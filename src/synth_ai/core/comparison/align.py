"""録音を参照音に合わせる: 発音開始・長さ・音量。音程は補正せず差として報告する。"""

from __future__ import annotations

import math
from dataclasses import dataclass

import librosa
import numpy as np

from synth_ai.core.audio import features as F
from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.comparison.models import Alignment


@dataclass(frozen=True)
class AlignedPair:
    reference: np.ndarray
    recording: np.ndarray  # 発音開始を揃え、音量を合わせた録音
    sample_rate: int
    onset_s: float  # 揃えた後の発音開始位置（両方共通）
    alignment: Alignment


def align(reference: AnalysisResult, recording: AnalysisResult) -> AlignedPair:
    ref, rec = reference.audio.samples, recording.audio.samples
    sr = reference.audio.sample_rate
    if recording.audio.sample_rate != sr:
        raise ValueError("sample rates differ after loading")
    ref_env, rec_env = reference.analysis.envelope, recording.analysis.envelope
    ref_onset = ref_env.onset_s if ref_env else 0.0
    rec_onset = rec_env.onset_s if rec_env else 0.0

    # 発音開始を揃える。録音の発音前を詰めるか、無音を足す
    shift = int(round((rec_onset - ref_onset) * sr))
    shift += _refine_shift(ref, rec, shift, sr, ref_onset)
    rec_aligned = rec[shift:] if shift >= 0 else np.concatenate([np.zeros(-shift), rec])
    n = min(len(ref), len(rec_aligned))

    # 音量は RMS 包絡のピークで合わせる（音色・包絡の形を比べるため）
    ref_peak = _envelope_peak(ref[:n], sr)
    rec_peak = _envelope_peak(rec_aligned[:n], sr)
    gain = ref_peak / max(rec_peak, 1e-12)

    pitch_offset = None
    if reference.analysis.pitch and recording.analysis.pitch:
        pitch_offset = 1200 * math.log2(
            recording.analysis.pitch.f0_hz / reference.analysis.pitch.f0_hz
        )

    alignment = Alignment(
        offset_s=round(shift / sr, 4),
        gain_db=round(20 * math.log10(gain), 2),
        pitch_offset_cents=None if pitch_offset is None else round(pitch_offset, 1),
        compared_duration_s=round(n / sr, 4),
        reference_duration_s=round(len(ref) / sr, 4),
        recording_duration_s=round(len(rec_aligned) / sr, 4),
    )
    return AlignedPair(ref[:n], rec_aligned[:n] * gain, sr, ref_onset, alignment)


def _refine_shift(
    ref: np.ndarray, rec: np.ndarray, shift: int, sr: int, onset_s: float, search_s: float = 0.02
) -> int:
    """発音直後 0.3 秒の振幅包絡の相互相関で、ずれを ±search_s の範囲で補正する（サンプル数）。"""
    hop = int(F.ENV_HOP_S * sr)
    frame = int(0.005 * sr)
    start = max(int(onset_s * sr) - int(search_s * sr), 0)
    length = int(0.3 * sr)

    def env(x: np.ndarray, offset: int) -> np.ndarray:
        seg = x[max(offset, 0) : max(offset, 0) + length + 2 * int(search_s * sr)]
        if offset < 0:
            seg = np.concatenate([np.zeros(-offset), seg])
        rms: np.ndarray = librosa.feature.rms(
            y=seg, frame_length=frame, hop_length=hop, center=False
        )[0]
        return rms

    ref_env = env(ref, start)
    rec_env = env(rec, start + shift)
    max_lag = int(search_s / F.ENV_HOP_S)
    n = min(len(ref_env), len(rec_env)) - max_lag
    if n <= max_lag:
        return 0
    a = ref_env[:n] / (np.linalg.norm(ref_env[:n]) + 1e-12)
    best_lag, best = 0, -np.inf
    for lag in range(-max_lag, max_lag + 1):
        b = rec_env[max(lag, 0) : max(lag, 0) + n]
        if lag < 0:
            b = np.concatenate([np.zeros(-lag), rec_env[: n + lag]])
        score = float(np.dot(a, b / (np.linalg.norm(b) + 1e-12)))
        if score > best:
            best_lag, best = lag, score
    return best_lag * hop


def _envelope_peak(x: np.ndarray, sr: int) -> float:
    """RMS 包絡（20 ms 窓）の最大値。"""
    frame, hop = int(0.02 * sr), int(F.ENV_HOP_S * sr)
    if len(x) < frame:
        return float(np.sqrt(np.mean(x**2))) if len(x) else 0.0
    rms = librosa.feature.rms(y=x, frame_length=frame, hop_length=hop, center=False)[0]
    return float(rms.max())
