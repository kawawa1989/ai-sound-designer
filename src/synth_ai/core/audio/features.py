"""音響特徴量の純粋関数群。入力は前処理済みのモノラル信号（float64）。"""

from __future__ import annotations

import math
from dataclasses import dataclass

import librosa
import numpy as np
from scipy.ndimage import uniform_filter1d

from synth_ai.core.audio.notes import hz_to_note
from synth_ai.core.sound_spec.models import (
    EnvelopeFeatures,
    HarmonicFeatures,
    Partial,
    PitchEstimate,
    SpectralFeatures,
)

EPS = 1e-12
PYIN_FMIN = 30.0
PYIN_FMAX = 4200.0
PYIN_FRAME = 4096
STFT_N_FFT = 4096
STFT_HOP_S = 0.01
ENV_HOP_S = 0.0025
ACTIVE_DB = -40.0  # スペクトル特徴を計算するフレームの下限（ピーク基準）
PLATEAU_SLOPE_DB_S = 4.0  # これより緩い傾きを「サステイン」とみなす
PLATEAU_MIN_S = 0.15
RELEASE_DROP_DB = 20.0
MAX_PARTIALS = 40
N_TRACKED_HARMONICS = 8


def to_db(x: np.ndarray | float) -> np.ndarray:
    return 20.0 * np.log10(np.maximum(np.asarray(x, dtype=np.float64), EPS))


# --- 包絡 ----------------------------------------------------------------------


@dataclass(frozen=True)
class Envelope:
    hop_s: float
    frame_s: float
    db: np.ndarray  # ピーク基準 dB（最大値 0）

    @property
    def times(self) -> np.ndarray:
        return np.arange(len(self.db)) * self.hop_s


def rms_envelope(x: np.ndarray, sr: int, f0_hz: float | None = None) -> Envelope:
    """RMS 包絡。窓長を基音周期の整数倍（5〜25 ms）にして周期によるうねりを抑える。"""
    hop = int(round(ENV_HOP_S * sr))
    if f0_hz is None:
        frame = int(round(0.02 * sr))
    else:
        periods = max(math.ceil(0.005 * f0_hz), 1)
        while (periods + 1) / f0_hz <= 0.025 and periods / f0_hz < 0.01:
            periods += 1
        frame = int(round(periods * sr / f0_hz))
    frame = max(frame, hop)
    rms = librosa.feature.rms(y=x, frame_length=frame, hop_length=hop, center=True)[0]
    db = to_db(rms)
    return Envelope(hop_s=hop / sr, frame_s=frame / sr, db=db - float(db.max()))


def noise_floor_db(env: Envelope) -> float:
    """20 ms 平均した包絡の最小値。トリム済みの減衰しきった音なら -60 dB 付近になる。"""
    size = max(int(0.02 / env.hop_s), 1)
    return float(np.min(uniform_filter1d(env.db, size=size, mode="nearest")))


@dataclass(frozen=True)
class TailState:
    """末尾 0.5 秒（短い音は全体の 1/4）の中央値レベルと傾き。

    傾きがほぼ 0 で十分小さければ、末尾は背景ノイズとみなせる。
    """

    level_db: float
    slope_db_per_s: float

    @property
    def is_noise(self) -> bool:
        return abs(self.slope_db_per_s) < 3.0 and self.level_db < -15.0


def tail_state(env: Envelope) -> TailState:
    duration = len(env.db) * env.hop_s
    n = max(int(min(0.5, duration / 4) / env.hop_s), 3)
    tail_t, tail_db = env.times[-n:], env.db[-n:]
    slope = float(np.polyfit(tail_t, tail_db, 1)[0]) if len(tail_db) >= 3 else 0.0
    return TailState(level_db=float(np.median(tail_db)), slope_db_per_s=slope)


def _first_crossing(
    times: np.ndarray, db: np.ndarray, level: float, start: int = 0
) -> float | None:
    """start 以降で db が初めて level 以上になる時刻（フレーム間は線形補間）。"""
    idx = np.flatnonzero(db[start:] >= level)
    if len(idx) == 0:
        return None
    i = start + int(idx[0])
    if i == 0 or db[i - 1] >= level:
        return float(times[i])
    frac = (level - db[i - 1]) / (db[i] - db[i - 1])
    return float(times[i - 1] + frac * (times[i] - times[i - 1]))


def _first_drop(times: np.ndarray, db: np.ndarray, level: float, start: int) -> float | None:
    """start 以降で db が初めて level 未満になる時刻。"""
    idx = np.flatnonzero(db[start:] < level)
    if len(idx) == 0:
        return None
    i = start + int(idx[0])
    if i == 0:
        return float(times[i])
    frac = (db[i - 1] - level) / (db[i - 1] - db[i])
    return float(times[i - 1] + frac * (times[i] - times[i - 1]))


def _longest_run(mask: np.ndarray) -> tuple[int, int] | None:
    """mask が True の最長区間 [start, end)。"""
    best: tuple[int, int] | None = None
    start = None
    for i, value in enumerate(np.append(mask, False)):
        if value and start is None:
            start = i
        elif not value and start is not None:
            if best is None or i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    return best


def envelope_features(env: Envelope) -> EnvelopeFeatures:
    times, db = env.times, env.db
    floor = noise_floor_db(env)
    onset = _first_crossing(times, db, max(-40.0, floor + 10.0)) or 0.0
    peak_i = int(np.argmax(db))
    peak_s = float(times[peak_i])

    t10 = _first_crossing(times, db, to_db(0.1).item())
    t90 = _first_crossing(times, db, to_db(0.9).item())
    attack_ms = None if t10 is None or t90 is None else max(t90 - t10, 0.0) * 1000

    smooth = uniform_filter1d(db, size=max(int(0.05 / env.hop_s), 1), mode="nearest")
    w = max(int(0.025 / env.hop_s), 1)
    padded = np.pad(smooth, w, mode="edge")
    slope = (padded[2 * w :] - padded[: -2 * w]) / (2 * w * env.hop_s)
    flat = (np.abs(slope) < PLATEAU_SLOPE_DB_S) & (db > -40.0)
    flat[:peak_i] = False
    run = _longest_run(flat)
    sustained = False
    if run is not None and (run[1] - run[0]) * env.hop_s >= PLATEAU_MIN_S:
        # 局所的に平坦でも、区間全体でゆっくり減衰していればサステインとみなさない（撥弦など）
        fit = np.polyfit(times[run[0] : run[1]], db[run[0] : run[1]], 1)[0]
        sustained = abs(float(fit)) < PLATEAU_SLOPE_DB_S / 2

    sustain_level = sustain_start = release_start = release_ms = decay_ms = None
    if sustained and run is not None:
        sustain_start = float(times[run[0]])
        sustain_level = float(np.median(db[run[0] : run[1]]))
        # 平滑化で前にずれた区間終端を、サステインから 0.5 dB 以内の最後のフレームまで延ばす
        last = run[1] - 1
        while last + 1 < len(db) and db[last + 1] >= sustain_level - 0.5:
            last += 1
        release_start = float(times[last])
        decay_ms = (sustain_start - peak_s) * 1000
        end = _first_drop(times, db, sustain_level - RELEASE_DROP_DB, last)
        release_ms = None if end is None else (end - release_start) * 1000
        rate_end = sustain_start
    else:
        drop20 = _first_drop(times, db, -20.0, peak_i)
        decay_ms = None if drop20 is None else (drop20 - peak_s) * 1000
        rate_end = _first_drop(times, db, -30.0, peak_i) or float(times[-1])

    rate = None
    seg = (times >= peak_s) & (times <= rate_end)
    if seg.sum() >= max(int(0.02 / env.hop_s), 3):
        rate = float(np.polyfit(times[seg], db[seg], 1)[0])

    confidence = 0.9 if floor < -40 else 0.6
    return EnvelopeFeatures(
        onset_s=onset,
        peak_s=peak_s,
        attack_ms=attack_ms,
        decay_ms=decay_ms,
        sustained=sustained,
        sustain_level_db=sustain_level,
        sustain_start_s=sustain_start,
        release_start_s=release_start,
        release_ms=release_ms,
        decay_rate_db_per_s=rate,
        confidence=confidence,
    )


# --- ピッチ --------------------------------------------------------------------


@dataclass(frozen=True)
class PitchTrack:
    f0_hz: np.ndarray  # 無声フレームは NaN
    voiced: np.ndarray
    voiced_prob: np.ndarray
    active: np.ndarray  # 音量が十分なフレーム


def pitch_track(x: np.ndarray, sr: int) -> PitchTrack:
    hop = int(round(STFT_HOP_S * sr))
    f0, voiced, prob = librosa.pyin(
        x,
        fmin=PYIN_FMIN,
        fmax=min(PYIN_FMAX, sr / 4),
        sr=sr,
        frame_length=PYIN_FRAME,
        hop_length=hop,
    )
    rms = librosa.feature.rms(y=x, frame_length=PYIN_FRAME, hop_length=hop)[0]
    rms_db = to_db(rms)
    active = rms_db > rms_db.max() - 30.0
    n = min(len(f0), len(active))
    return PitchTrack(f0[:n], voiced[:n], np.nan_to_num(prob[:n]), active[:n])


def estimate_pitch(track: PitchTrack) -> PitchEstimate | None:
    if not track.active.any():
        return None
    voiced = track.voiced & track.active & np.isfinite(track.f0_hz)
    voiced_ratio = float(voiced.sum() / track.active.sum())
    if voiced.sum() == 0:
        return None
    f0 = float(np.median(track.f0_hz[voiced]))
    cents = 1200 * np.log2(track.f0_hz[voiced] / f0)
    note, offset = hz_to_note(f0)
    return PitchEstimate(
        f0_hz=f0,
        note=note,
        cents_offset=offset,
        stability_cents=min(float(np.std(cents)), 1200.0),
        voiced_ratio=voiced_ratio,
        confidence=float(np.mean(track.voiced_prob[track.active])),
    )


def with_harmonic_evidence(
    pitch: PitchEstimate, f0_hz: float, harmonics: HarmonicFeatures
) -> PitchEstimate:
    """倍音から精密化した f0 を反映し、倍音構造が明瞭なら確信度を引き上げる。

    pyin の有声確率は低音で低く出やすい。基音が存在し（最大倍音から -30 dB 以内）、
    エネルギーのほとんどが整数倍音にある場合は、単音である根拠として扱う。
    基音が欠けている場合（和音を共通の低い基音で説明している等）は引き上げない。
    """
    note, offset = hz_to_note(f0_hz)
    fundamental = next((p for p in harmonics.partials if p.number == 1), None)
    confidence = pitch.confidence
    if (
        fundamental is not None
        and fundamental.level_db > -30.0
        and harmonics.harmonic_energy_ratio > 0.9
        and harmonics.inharmonicity_cents < 5.0
    ):
        evidence = 0.9 * harmonics.harmonic_energy_ratio * pitch.voiced_ratio
        confidence = max(confidence, evidence)
    return pitch.model_copy(
        update={"f0_hz": f0_hz, "note": note, "cents_offset": offset, "confidence": confidence}
    )


# --- スペクトル ----------------------------------------------------------------


@dataclass(frozen=True)
class Spectrogram:
    magnitude: np.ndarray  # [周波数, フレーム]
    freqs: np.ndarray
    hop_s: float
    frame_db: np.ndarray  # フレームのエネルギー（ピーク基準 dB）

    @property
    def times(self) -> np.ndarray:
        return np.arange(self.magnitude.shape[1]) * self.hop_s

    @property
    def active(self) -> np.ndarray:
        return self.frame_db > ACTIVE_DB


def spectrogram(x: np.ndarray, sr: int) -> Spectrogram:
    hop = int(round(STFT_HOP_S * sr))
    mag = np.abs(librosa.stft(x, n_fft=STFT_N_FFT, hop_length=hop, window="hann"))
    energy = 10 * np.log10(np.maximum((mag**2).sum(axis=0), EPS))
    return Spectrogram(
        magnitude=mag,
        freqs=librosa.fft_frequencies(sr=sr, n_fft=STFT_N_FFT),
        hop_s=hop / sr,
        frame_db=energy - energy.max(),
    )


@dataclass(frozen=True)
class SpectralSeries:
    centroid_hz: np.ndarray
    rolloff_hz: np.ndarray
    flatness: np.ndarray
    weight: np.ndarray  # フレームのエネルギー（線形）。無効フレームは 0


def spectral_series(spec: Spectrogram, min_db: float = ACTIVE_DB) -> SpectralSeries:
    """min_db より小さいフレーム（背景ノイズのみの区間など）は重み 0 にする。"""
    S = spec.magnitude
    centroid = librosa.feature.spectral_centroid(S=S, freq=spec.freqs)[0]
    rolloff = librosa.feature.spectral_rolloff(S=S, freq=spec.freqs, roll_percent=0.85)[0]
    flatness = librosa.feature.spectral_flatness(S=S, amin=1e-6)[0]
    weight = np.where(spec.frame_db > max(min_db, ACTIVE_DB), 10 ** (spec.frame_db / 10), 0.0)
    return SpectralSeries(centroid, rolloff, flatness, weight)


def _weighted_mean(values: np.ndarray, weight: np.ndarray, mask: np.ndarray) -> float | None:
    w = weight * mask
    return None if w.sum() <= 0 else float(np.sum(values * w) / w.sum())


def spectral_features(
    series: SpectralSeries, spec: Spectrogram, onset_s: float, f0_hz: float | None
) -> SpectralFeatures | None:
    times = spec.times
    active = series.weight > 0
    if not active.any():
        return None
    all_frames = np.ones_like(active)
    mean = _weighted_mean(series.centroid_hz, series.weight, all_frames)
    last_active = float(times[np.flatnonzero(active)[-1]])
    start_mask = (times >= onset_s) & (times <= onset_s + 0.1)
    end_mask = times >= onset_s + 0.75 * max(last_active - onset_s, 0.0)
    start = _weighted_mean(series.centroid_hz, series.weight, start_mask) or mean
    end = _weighted_mean(series.centroid_hz, series.weight, end_mask) or mean
    rolloff = _weighted_mean(series.rolloff_hz, series.weight, all_frames)
    flatness = _weighted_mean(series.flatness, series.weight, all_frames)
    assert mean is not None and start is not None and end is not None
    return SpectralFeatures(
        centroid_hz_mean=mean,
        centroid_hz_start=start,
        centroid_hz_end=end,
        centroid_ratio_to_f0=None if f0_hz is None else mean / f0_hz,
        brightness_change_ratio=end / max(start, EPS),
        rolloff_hz_mean=rolloff or 0.0,
        flatness_mean=flatness or 0.0,
        confidence=min(1.0, float(active.sum()) / 20.0),
    )


# --- 倍音 ----------------------------------------------------------------------


def steady_window(env: EnvelopeFeatures, duration_s: float) -> tuple[float, float]:
    """倍音を測る区間。サステインがあればその先頭 0.5 秒、なければアタック直後の 0.3 秒。"""
    if env.sustained and env.sustain_start_s is not None and env.release_start_s is not None:
        return env.sustain_start_s, min(env.sustain_start_s + 0.5, env.release_start_s)
    start = env.peak_s + 0.02
    return start, min(start + 0.3, duration_s)


def _segment_spectrum(x: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    n_fft = max(1 << math.ceil(math.log2(len(x) * 4)), 1 << 16)
    power = np.abs(np.fft.rfft(x * np.hanning(len(x)), n=n_fft)) ** 2
    return np.fft.rfftfreq(n_fft, 1 / sr), power


def _find_partials(
    freqs: np.ndarray, power: np.ndarray, f0: float, nyquist: float
) -> list[tuple[int, float, float]]:
    """(倍音番号, 周波数, パワー) のリスト。ノイズフロアより 12 dB 以上のピークのみ。"""
    db = 10 * np.log10(np.maximum(power, EPS))
    band = (freqs > 20) & (freqs < nyquist)
    floor = float(np.median(db[band]))
    df = freqs[1] - freqs[0]
    found = []
    for k in range(1, MAX_PARTIALS + 1):
        center = k * f0
        if center + 0.25 * f0 >= nyquist:
            break
        lo, hi = int((center - 0.25 * f0) / df), int((center + 0.25 * f0) / df) + 1
        i = lo + int(np.argmax(db[lo:hi]))
        if db[i] < floor + 12 or i in (lo, hi - 1):
            continue
        a, b, c = db[i - 1], db[i], db[i + 1]
        denom = a - 2 * b + c
        shift = 0.5 * (a - c) / denom if denom != 0 else 0.0
        freq = freqs[i] + shift * df
        peak_db = b - 0.25 * (a - c) * shift
        found.append((k, float(freq), float(10 ** (peak_db / 10))))
    return found


def _refine_f0(partials: list[tuple[int, float, float]], f0: float) -> float:
    candidates = [
        (freq / k, power)
        for k, freq, power in partials
        if k <= 10 and abs(1200 * math.log2(freq / (k * f0))) < 30
    ]
    if not candidates:
        return f0
    values, weights = np.array(candidates).T
    return float(np.sum(values * weights) / np.sum(weights))


def harmonic_features(
    x: np.ndarray, sr: int, f0_hz: float, window: tuple[float, float], confidence: float
) -> tuple[HarmonicFeatures, float] | None:
    """定常区間の倍音構造と、倍音から精密化した f0 を返す。"""
    start, end = window
    seg = x[int(start * sr) : int(end * sr)]
    if len(seg) < max(int(0.05 * sr), int(4 * sr / f0_hz)):
        return None
    nyquist = min(sr / 2 * 0.95, 20_000.0)
    freqs, power = _segment_spectrum(seg, sr)
    f0 = _refine_f0(_find_partials(freqs, power, f0_hz, nyquist), f0_hz)
    raw = _find_partials(freqs, power, f0, nyquist)
    if not raw:
        return None

    max_power = max(p for _, _, p in raw)
    partials = tuple(
        Partial(
            number=k,
            freq_hz=freq,
            level_db=10 * math.log10(p / max_power),
            deviation_cents=1200 * math.log2(freq / (k * f0)),
        )
        for k, freq, p in raw
    )

    half_width = 3 * sr / len(seg)
    band = (freqs > 20) & (freqs < nyquist)
    near = np.zeros_like(band)
    found = {k: freq for k, freq, _ in raw}
    for k in range(1, int(nyquist / f0) + 1):
        center = found.get(k, k * f0)
        near |= np.abs(freqs - center) <= half_width
    ratio = float(power[band & near].sum() / max(power[band].sum(), EPS))

    upper = [(p.deviation_cents, 10 ** (p.level_db / 10)) for p in partials if p.number >= 2]
    inharm = sum(abs(d) * w for d, w in upper) / sum(w for _, w in upper) if upper else 0.0
    odd = sum(p for k, _, p in raw if k >= 3 and k % 2 == 1)
    even = sum(p for k, _, p in raw if k >= 2 and k % 2 == 0)
    odd_even = None
    if odd > 0 or even > 0:
        odd_even = float(np.clip(10 * math.log10((odd + EPS) / (even + EPS)), -60, 60))

    features = HarmonicFeatures(
        window_start_s=start,
        window_end_s=end,
        partials=partials,
        harmonic_energy_ratio=min(ratio, 1.0),
        inharmonicity_cents=inharm,
        odd_even_ratio_db=odd_even,
        confidence=confidence,
    )
    return features, f0


def harmonic_levels(spec: Spectrogram, f0_hz: float, n: int = N_TRACKED_HARMONICS) -> np.ndarray:
    """フレームごとの k 次倍音のレベル（dB、全体の最大を 0）。形状 [n, フレーム]。"""
    df = spec.freqs[1] - spec.freqs[0]
    rows = []
    for k in range(1, n + 1):
        i = int(round(k * f0_hz / df))
        if i + 2 >= len(spec.freqs):
            break
        rows.append(spec.magnitude[i - 2 : i + 3].max(axis=0))
    if not rows:
        return np.empty((0, spec.magnitude.shape[1]))
    levels = to_db(np.array(rows))
    relative: np.ndarray = levels - levels.max()
    return relative
