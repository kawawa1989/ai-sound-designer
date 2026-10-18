"""WAV の読み込み・検証・前処理（モノ化、リサンプル、無音トリム）。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from synth_ai.core.sound_spec.models import Issue, Severity, SourceInfo

TARGET_SR = 48_000
SILENCE_DB = -60.0  # ピーク基準。これより小さい先頭・末尾を削る
PRE_ROLL_S = 0.01  # 発音の立ち上がりを残すため、トリム位置の手前に残す長さ
MIN_DURATION_S = 0.1
SHORT_DURATION_S = 0.3
LONG_DURATION_S = 30.0
CLIP_LEVEL = 0.999
CLIP_RATIO_WARN = 1e-4


class AudioLoadError(Exception):
    """解析できない入力（存在しない、読めない、無音、短すぎる）。"""


@dataclass(frozen=True)
class LoadedAudio:
    samples: np.ndarray  # モノラル float64、TARGET_SR、トリム済み
    sample_rate: int
    source: SourceInfo
    clip_ratio: float
    dc_offset: float
    end_level_db: float  # ファイル末尾 2 ms のピーク（全体ピーク基準）。高ければ途中で切れている
    issues: tuple[Issue, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resample(x: np.ndarray, sr: int, target_sr: int) -> np.ndarray:
    if sr == target_sr:
        return x
    g = gcd(sr, target_sr)
    return np.asarray(resample_poly(x, target_sr // g, sr // g), dtype=np.float64)


def trim_silence(x: np.ndarray, sr: int, threshold_db: float = SILENCE_DB) -> tuple[int, int]:
    """ピーク基準 threshold_db 以下の先頭・末尾を除いた範囲 [start, end) を返す。"""
    peak = float(np.max(np.abs(x)))
    if peak == 0:
        return 0, 0
    above = np.flatnonzero(np.abs(x) > peak * 10 ** (threshold_db / 20))
    start = max(int(above[0]) - int(PRE_ROLL_S * sr), 0)
    end = min(int(above[-1]) + 1, len(x))
    return start, end


def load_audio(path: Path, target_sr: int = TARGET_SR) -> LoadedAudio:
    if not path.is_file():
        raise AudioLoadError(f"ファイルが見つかりません: {path}")
    try:
        data, sr = sf.read(path, dtype="float64", always_2d=True)
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise AudioLoadError(f"音声ファイルとして読み込めません: {path} ({exc})") from exc

    n_frames, channels = data.shape
    duration = n_frames / sr if sr else 0.0
    issues: list[Issue] = []

    if n_frames == 0:
        raise AudioLoadError(f"音声データが空です: {path}")

    clip_ratio = float(np.mean(np.abs(data) >= CLIP_LEVEL))
    if clip_ratio > CLIP_RATIO_WARN:
        issues.append(
            Issue(
                code="clipping",
                message=f"クリップの可能性があります（{clip_ratio:.2%} のサンプルが最大値付近）",
            )
        )

    mono = data.mean(axis=1)
    if channels > 1:
        side = (data[:, 0] - data[:, 1]) / 2 if channels == 2 else data - mono[:, None]
        if float(np.sqrt(np.mean(side**2))) > 0.5 * float(np.sqrt(np.mean(mono**2)) + 1e-12):
            issues.append(
                Issue(
                    code="wide_stereo",
                    message="左右の差が大きいため、モノラル化で音色が変わる可能性があります",
                )
            )

    dc_offset = float(np.mean(mono))
    mono = mono - dc_offset
    if abs(dc_offset) > 0.01:
        issues.append(Issue(code="dc_offset", message=f"直流成分 {dc_offset:+.3f} を除去しました"))

    mono = _resample(mono, sr, target_sr)
    peak = float(np.max(np.abs(mono)))
    if peak < 10 ** (-60 / 20):
        raise AudioLoadError(f"無音、または音量が小さすぎます（ピーク -60 dBFS 未満）: {path}")

    end_level_db = float(
        20 * np.log10(max(float(np.max(np.abs(mono[-int(0.002 * target_sr) :]))), 1e-12) / peak)
    )
    start, end = trim_silence(mono, target_sr)
    trimmed = mono[start:end]
    # 先頭から音が鳴っている場合も、発音前に PRE_ROLL_S の無音があるようにそろえる
    # （包絡の先頭フレームが欠けて、アタックの測定が素材によってぶれるのを防ぐ）
    peak_t = float(np.max(np.abs(trimmed)))
    first = int(np.flatnonzero(np.abs(trimmed) > peak_t * 10 ** (SILENCE_DB / 20))[0])
    missing = int(PRE_ROLL_S * target_sr) - first
    if missing > 0:
        trimmed = np.concatenate([np.zeros(missing), trimmed])
    analyzed = len(trimmed) / target_sr
    if analyzed < MIN_DURATION_S:
        raise AudioLoadError(f"音が短すぎます（{analyzed * 1000:.0f} ms、100 ms 以上が必要）")
    if analyzed < SHORT_DURATION_S:
        issues.append(Issue(code="short", message="音が短いため、包絡の推定精度が下がります"))
    if analyzed > LONG_DURATION_S:
        issues.append(
            Issue(
                code="long",
                message="30 秒を超えています。単音のみを切り出した素材を推奨します",
                severity=Severity.INFO,
            )
        )

    source = SourceInfo(
        path=str(path),
        sha256=_sha256(path),
        sample_rate=sr,
        channels=channels,
        duration_s=round(duration, 6),
        trim_start_s=round(start / target_sr, 6),
        analyzed_duration_s=round(analyzed, 6),
    )
    return LoadedAudio(
        samples=trimmed,
        sample_rate=target_sr,
        source=source,
        clip_ratio=clip_ratio,
        dc_offset=dc_offset,
        end_level_db=end_level_db,
        issues=tuple(issues),
    )
