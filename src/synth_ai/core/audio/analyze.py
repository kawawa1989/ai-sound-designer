"""参照音声を解析して AudioAnalysis を組み立てる。"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from synth_ai.core.audio import features as F
from synth_ai.core.audio.load import LoadedAudio, load_audio
from synth_ai.core.sound_spec.models import (
    AnalysisSettings,
    AudioAnalysis,
    Issue,
    LevelInfo,
    Severity,
    TimeSeries,
)

ANALYZER_VERSION = "0.1.0"
DECIMALS = 4
PITCH_CONFIDENCE_MIN = 0.5
HARMONIC_RATIO_MIN = 0.7
UNSTABLE_PITCH_CENTS = 30.0
LOW_SNR_DB = 30.0
TRUNCATION_DB = -40.0


@dataclass(frozen=True)
class AnalysisResult:
    """保存用の AudioAnalysis と、グラフ描画に使う中間データ。"""

    analysis: AudioAnalysis
    audio: LoadedAudio
    envelope: F.Envelope
    spectrogram: F.Spectrogram


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, DECIMALS)
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_round(v) for v in value]
    return value


def _optional(values: Iterable[float], valid: Iterable[bool]) -> tuple[float | None, ...]:
    return tuple(
        float(v) if ok and np.isfinite(v) else None for v, ok in zip(values, valid, strict=True)
    )


def _quality_issues(
    audio: LoadedAudio, env: F.Envelope, analysis_parts: dict[str, Any], levels: LevelInfo
) -> list[Issue]:
    issues: list[Issue] = []
    snr_db = levels.snr_db
    if not levels.snr_is_lower_bound and snr_db < LOW_SNR_DB:
        issues.append(
            Issue(
                code="low_snr",
                message=f"背景ノイズが大きい（S/N 約 {snr_db:.0f} dB）。解析値の信頼度が下がります",
            )
        )
    if audio.end_level_db > TRUNCATION_DB and not F.tail_state(env).is_noise:
        issues.append(
            Issue(
                code="truncated_tail",
                message="音が鳴り終わる前にファイルが終わっています。リリースを測定できません",
            )
        )
    pitch = analysis_parts.get("pitch")
    if pitch is None or pitch.confidence < PITCH_CONFIDENCE_MIN:
        issues.append(
            Issue(
                code="pitch_unreliable",
                message="ピッチを確定できません。和音・ノイズ・非調和音の可能性があります",
            )
        )
    elif pitch.stability_cents > UNSTABLE_PITCH_CENTS:
        issues.append(
            Issue(
                code="unstable_pitch",
                message=f"ピッチが揺れています（±{pitch.stability_cents:.0f} セント）。"
                "ビブラートやグライドの可能性があります",
                severity=Severity.INFO,
            )
        )
    harmonics = analysis_parts.get("harmonics")
    if harmonics is not None and harmonics.harmonic_energy_ratio < HARMONIC_RATIO_MIN:
        issues.append(
            Issue(
                code="low_harmonicity",
                message="整数倍音以外の成分が多い（ノイズ、非調和音、または複数の音）",
                severity=Severity.INFO,
            )
        )
    return issues


def analyze_audio(audio: LoadedAudio, analysis_id: str) -> AnalysisResult:
    x, sr = audio.samples, audio.sample_rate

    track = F.pitch_track(x, sr)
    pitch = F.estimate_pitch(track)
    f0 = pitch.f0_hz if pitch else None

    env = F.rms_envelope(x, sr, f0)
    envelope = F.envelope_features(env)
    spec = F.spectrogram(x, sr)
    tail = F.tail_state(env)
    # 末尾が背景ノイズなら、ノイズより 10 dB 以上大きいフレームだけで音色を測る
    series = F.spectral_series(spec, tail.level_db + 10.0 if tail.is_noise else F.ACTIVE_DB)

    harmonics = None
    if pitch is not None and f0 is not None:
        window = F.steady_window(envelope, len(x) / sr)
        result = F.harmonic_features(x, sr, f0, window, confidence=pitch.confidence)
        if result is not None:
            harmonics, f0 = result
            pitch = F.with_harmonic_evidence(pitch, f0, harmonics)

    spectral = F.spectral_features(series, spec, envelope.onset_s, f0)

    peak = float(np.max(np.abs(x)))
    noise_measured = tail.is_noise
    floor = tail.level_db if noise_measured else F.noise_floor_db(env)
    levels = LevelInfo(
        peak_dbfs=float(F.to_db(peak)),
        rms_dbfs=float(F.to_db(np.sqrt(np.mean(x**2)))),
        noise_floor_db=floor,
        snr_db=-floor,
        snr_is_lower_bound=not noise_measured,
        clip_ratio=audio.clip_ratio,
        dc_offset=audio.dc_offset,
    )

    step = int(round(spec.hop_s / env.hop_s))
    n = min(spec.magnitude.shape[1], len(env.db[::step]))
    active = series.weight[:n] > 0
    harm = F.harmonic_levels(spec, f0) if f0 is not None else np.empty((0, n))
    timeseries = TimeSeries(
        hop_s=spec.hop_s,
        rms_db=tuple(float(v) for v in np.maximum(env.db[::step][:n], -100.0)),
        centroid_hz=_optional(series.centroid_hz[:n], active),
        flatness=_optional(series.flatness[:n], active),
        harmonic_levels_db=tuple(_optional(row[:n], active & (row[:n] > -80)) for row in harm),
    )

    parts: dict[str, Any] = {"pitch": pitch, "harmonics": harmonics}
    issues = list(audio.issues) + _quality_issues(audio, env, parts, levels)

    analysis = AudioAnalysis(
        analysis_id=analysis_id,
        source=audio.source,
        settings=AnalysisSettings(
            analyzer_version=ANALYZER_VERSION,
            sample_rate=sr,
            hop_s=spec.hop_s,
            n_fft=F.STFT_N_FFT,
        ),
        levels=levels,
        pitch=pitch,
        envelope=envelope,
        spectral=spectral,
        harmonics=harmonics,
        timeseries=timeseries,
        issues=tuple(issues),
    )
    rounded = AudioAnalysis.model_validate(_round(analysis.model_dump()))
    return AnalysisResult(analysis=rounded, audio=audio, envelope=env, spectrogram=spec)


def analyze_file(path: Path, analysis_id: str | None = None) -> AnalysisResult:
    audio = load_audio(path)
    return analyze_audio(audio, analysis_id or f"ref-{audio.source.sha256[:8]}")
