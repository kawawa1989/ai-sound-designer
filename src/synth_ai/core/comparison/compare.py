"""揃えた参照音と録音の差を計算し、区間・周波数帯・特徴ごとの差分として並べる。"""

from __future__ import annotations

import librosa
import numpy as np

from synth_ai.core.audio import features as F
from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.comparison.align import AlignedPair
from synth_ai.core.comparison.models import (
    SEGMENT_LABELS,
    Difference,
    DifferenceKind,
    Segment,
    SpectralDistance,
)
from synth_ai.core.comparison.wording import as_feature, difference_word, fmt
from synth_ai.core.sound_spec.derive import quantitative_targets
from synth_ai.core.sound_spec.features import LABELS

BANDS: tuple[tuple[str, float, float], ...] = (
    ("<250", 20.0, 250.0),
    ("250-1k", 250.0, 1000.0),
    ("1k-4k", 1000.0, 4000.0),
    ("4k-10k", 4000.0, 10_000.0),
    (">10k", 10_000.0, 20_000.0),
)
BAND_LABELS = {
    "<250": "低域（250 Hz 未満）",
    "250-1k": "中低域（250 Hz〜1 kHz）",
    "1k-4k": "中域（1〜4 kHz）",
    "4k-10k": "高域（4〜10 kHz）",
    ">10k": "超高域（10 kHz 以上）",
}
BAND_TOLERANCE_DB = 3.0
ENVELOPE_TOLERANCE_DB = 2.0
HARMONIC_TOLERANCE_DB = 6.0
MAX_HARMONIC = 8
DISTANCE_RESOLUTIONS = (512, 2048, 8192)
# 比較から外す特徴（他の特徴と重複する、または平均で情報が薄いもの）
SKIPPED_FEATURES = {"brightness"}


def segments(pair: AlignedPair, reference: AnalysisResult) -> dict[Segment, tuple[float, float]]:
    """参照音の包絡から、アタック・持続部・減衰の区間（秒）を決める。"""
    env = reference.analysis.envelope
    end = len(pair.reference) / pair.sample_rate
    onset = pair.onset_s
    attack_ms = env.attack_ms if env and env.attack_ms else 10.0
    attack_end = min(onset + max(2 * attack_ms / 1000, 0.03), end)
    if env and env.sustained and env.release_start_s:
        body_end = min(env.release_start_s, end)
    else:
        body_end = onset + 0.75 * (end - onset)
    body_end = max(body_end, attack_end)
    spans = {
        Segment.ATTACK: (onset, attack_end),
        Segment.BODY: (attack_end, body_end),
        Segment.TAIL: (body_end, end),
    }
    return {k: v for k, v in spans.items() if v[1] - v[0] >= 0.02}


def _power_spectrogram(x: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, float]:
    hop = int(round(F.STFT_HOP_S * sr))
    power = np.abs(librosa.stft(x, n_fft=F.STFT_N_FFT, hop_length=hop)) ** 2
    return power, librosa.fft_frequencies(sr=sr, n_fft=F.STFT_N_FFT), hop / sr


def band_differences(
    pair: AlignedPair, spans: dict[Segment, tuple[float, float]]
) -> list[Difference]:
    """区間ごとに、周波数帯のエネルギー差から区間全体の音量差を引いた「音色の差」。"""
    ref_p, freqs, hop_s = _power_spectrogram(pair.reference, pair.sample_rate)
    rec_p, _, _ = _power_spectrogram(pair.recording, pair.sample_rate)
    n = min(ref_p.shape[1], rec_p.shape[1])
    times = np.arange(n) * hop_s
    ref_total_db = 10 * np.log10(np.maximum(ref_p[:, :n].sum(axis=0), F.EPS))
    loud = ref_total_db > ref_total_db.max() - 50
    out = []
    for segment, (start, end) in spans.items():
        frames = (times >= start) & (times < end) & loud
        if frames.sum() < 2:
            continue
        ref_seg, rec_seg = ref_p[:, :n][:, frames], rec_p[:, :n][:, frames]
        level_delta = 10 * np.log10(rec_seg.sum() / max(ref_seg.sum(), F.EPS))
        for name, lo, hi in BANDS:
            band = (freqs >= lo) & (freqs < hi)
            ref_e, rec_e = ref_seg[band].sum(), rec_seg[band].sum()
            # 参照・録音とも区間全体の 1/10000（-40 dB）未満の帯域は比較しない
            if max(ref_e / ref_seg.sum(), rec_e / max(rec_seg.sum(), F.EPS)) < 1e-4:
                continue
            ref_db = 10 * np.log10(max(ref_e / ref_seg.sum(), F.EPS))
            rec_db = 10 * np.log10(max(rec_e / max(rec_seg.sum(), F.EPS), F.EPS))
            delta = float(rec_db - ref_db)
            word = "強い" if delta > 0 else "弱い"
            out.append(
                Difference(
                    kind=DifferenceKind.BAND,
                    segment=segment,
                    band=name,
                    reference=round(float(ref_db), 2),
                    recording=round(float(rec_db), 2),
                    delta=round(delta, 2),
                    unit="dB",
                    severity=round(abs(delta) / BAND_TOLERANCE_DB, 3),
                    message=f"{SEGMENT_LABELS[segment]}の{BAND_LABELS[name]}が "
                    f"{delta:+.1f} dB {word}"
                    f"（区間の音量差 {level_delta:+.1f} dB を除いた音色の差）",
                )
            )
    return out


def envelope_differences(
    pair: AlignedPair, spans: dict[Segment, tuple[float, float]], reference: AnalysisResult
) -> list[Difference]:
    sr = pair.sample_rate
    f0 = reference.analysis.pitch.f0_hz if reference.analysis.pitch else None
    ref_env = F.rms_envelope(pair.reference, sr, f0)
    rec_env = F.rms_envelope(pair.recording, sr, f0)
    # どちらも自身のピーク基準（録音はピークを参照に合わせてある）。包絡の形を比べる
    ref_db, rec_db = ref_env.db, rec_env.db
    n = min(len(ref_db), len(rec_db))
    times = ref_env.times[:n]
    out = []
    for segment, (start, end) in spans.items():
        frames = (times >= start) & (times < end) & (ref_db[:n] > -50)
        if frames.sum() < 2:
            continue
        ref_mean = float(np.mean(ref_db[:n][frames]))
        rec_mean = float(np.mean(np.maximum(rec_db[:n][frames], -80)))
        delta = rec_mean - ref_mean
        word = "大きい" if delta > 0 else "小さい"
        out.append(
            Difference(
                kind=DifferenceKind.ENVELOPE,
                segment=segment,
                reference=round(ref_mean, 2),
                recording=round(rec_mean, 2),
                delta=round(delta, 2),
                unit="dB",
                severity=round(abs(delta) / ENVELOPE_TOLERANCE_DB, 3),
                message=f"{SEGMENT_LABELS[segment]}の音量が {delta:+.1f} dB {word}",
            )
        )
    return out


def feature_differences(reference: AnalysisResult, recording: AnalysisResult) -> list[Difference]:
    ref_targets = {t.feature: t for t in quantitative_targets(reference.analysis)}
    rec_targets = {t.feature: t for t in quantitative_targets(recording.analysis)}
    out = []
    for name, ref in ref_targets.items():
        feature = as_feature(name)
        rec = rec_targets.get(name)
        if feature is None or rec is None or name in SKIPPED_FEATURES:
            continue
        delta = rec.value - ref.value
        tolerance = ref.tolerance if ref.tolerance > 0 else max(abs(ref.value) * 0.1, 1e-6)
        out.append(
            Difference(
                kind=DifferenceKind.FEATURE,
                feature=name,
                reference=ref.value,
                recording=rec.value,
                delta=round(delta, 4),
                unit=ref.unit,
                severity=round(abs(delta) / tolerance, 3),
                message=f"{difference_word(feature, delta)}"
                f"（{LABELS[feature]}: 参照 {fmt(ref.value)} → 録音 {fmt(rec.value)} {ref.unit}）",
            )
        )
    return out


def harmonic_differences(reference: AnalysisResult, recording: AnalysisResult) -> list[Difference]:
    ref_h, rec_h = reference.analysis.harmonics, recording.analysis.harmonics
    if ref_h is None or rec_h is None:
        return []
    rec_levels = {p.number: p.level_db for p in rec_h.partials}
    out = []
    for p in ref_h.partials:
        if p.number > MAX_HARMONIC or p.number not in rec_levels or p.level_db < -40:
            continue
        delta = rec_levels[p.number] - p.level_db
        word = "強い" if delta > 0 else "弱い"
        out.append(
            Difference(
                kind=DifferenceKind.HARMONIC,
                harmonic=p.number,
                reference=round(p.level_db, 2),
                recording=round(rec_levels[p.number], 2),
                delta=round(delta, 2),
                unit="dB",
                severity=round(abs(delta) / HARMONIC_TOLERANCE_DB, 3),
                message=f"{p.number} 次倍音が {delta:+.1f} dB {word}（最大の倍音を 0 dB として）",
            )
        )
    return out


def spectral_distance(pair: AlignedPair) -> SpectralDistance:
    per = {}
    for n_fft in DISTANCE_RESOLUTIONS:
        hop = n_fft // 4
        ref = np.abs(librosa.stft(pair.reference, n_fft=n_fft, hop_length=hop))
        rec = np.abs(librosa.stft(pair.recording, n_fft=n_fft, hop_length=hop))
        ref_db, rec_db = F.to_db(ref), F.to_db(rec)
        floor = max(ref_db.max(), rec_db.max()) - 80
        mask = (ref_db > floor) | (rec_db > floor)
        diff = np.abs(np.maximum(ref_db, floor) - np.maximum(rec_db, floor))
        per[n_fft] = round(float(diff[mask].mean()) if mask.any() else 0.0, 2)
    return SpectralDistance(
        per_resolution_db=per, mean_db=round(float(np.mean(list(per.values()))), 2)
    )


def compute_differences(
    pair: AlignedPair, reference: AnalysisResult, recording: AnalysisResult
) -> list[Difference]:
    spans = segments(pair, reference)
    diffs = (
        feature_differences(reference, recording)
        + envelope_differences(pair, spans, reference)
        + band_differences(pair, spans)
        + harmonic_differences(reference, recording)
    )
    return sorted(diffs, key=lambda d: d.severity, reverse=True)
