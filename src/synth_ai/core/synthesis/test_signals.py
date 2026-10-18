"""正解が分かっている合成テスト音。解析器の検証と手元での試聴に使う。

すべて決定的（乱数は seed 固定）で、振幅は float64・ピーク 0.5 前後。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from synth_ai.core.audio.notes import note_to_hz

FloatArray = np.ndarray
DEFAULT_SR = 48_000


@dataclass(frozen=True)
class Adsr:
    attack_s: float = 0.005
    decay_s: float = 0.15
    sustain: float = 0.6  # 線形振幅
    release_s: float = 0.3
    note_s: float = 1.0  # Note On から Note Off まで


def adsr_envelope(adsr: Adsr, sr: int = DEFAULT_SR) -> FloatArray:
    """線形セグメントの ADSR。長さは note_s + release_s。"""
    n_note = int(round(adsr.note_s * sr))
    n_total = n_note + int(round(adsr.release_s * sr))
    t = np.arange(n_total) / sr
    a, d = adsr.attack_s, adsr.decay_s
    held = np.interp(t[:n_note], [0.0, a, a + d], [0.0, 1.0, adsr.sustain])
    level = held[-1] if n_note else 0.0
    rel_t = t[n_note:] - adsr.note_s
    release = level * np.clip(1.0 - rel_t / max(adsr.release_s, 1e-9), 0.0, None)
    return np.concatenate([held, release])


def additive(
    f0: float,
    duration_s: float,
    amplitude: Callable[[int, FloatArray], FloatArray],
    sr: int = DEFAULT_SR,
    max_partials: int = 200,
) -> FloatArray:
    """帯域制限された加算合成。amplitude(k, t) が k 次倍音の振幅（時間配列）を返す。"""
    t = np.arange(int(round(duration_s * sr))) / sr
    out = np.zeros_like(t)
    for k in range(1, max_partials + 1):
        if k * f0 >= sr / 2 * 0.95:
            break
        out += amplitude(k, t) * np.sin(2 * np.pi * k * f0 * t)
    return out


def normalize(x: FloatArray, peak: float = 0.5) -> FloatArray:
    m = float(np.max(np.abs(x)))
    return x if m == 0 else x * (peak / m)


def saw(f0: float = 261.63, adsr: Adsr | None = None, sr: int = DEFAULT_SR) -> FloatArray:
    """k 次倍音の振幅が 1/k の帯域制限ノコギリ波。"""
    adsr = adsr or Adsr()
    env = adsr_envelope(adsr, sr)
    tone = additive(f0, len(env) / sr, lambda k, t: np.full_like(t, 1.0 / k), sr)
    return normalize(tone * env)


def square(f0: float = 261.63, adsr: Adsr | None = None, sr: int = DEFAULT_SR) -> FloatArray:
    """奇数次のみ（振幅 1/k）の矩形波。"""
    adsr = adsr or Adsr()
    env = adsr_envelope(adsr, sr)
    tone = additive(f0, len(env) / sr, lambda k, t: np.full_like(t, (k % 2) / k), sr)
    return normalize(tone * env)


def sine(f0: float = 261.63, adsr: Adsr | None = None, sr: int = DEFAULT_SR) -> FloatArray:
    adsr = adsr or Adsr()
    env = adsr_envelope(adsr, sr)
    t = np.arange(len(env)) / sr
    return normalize(np.sin(2 * np.pi * f0 * t) * env)


def saw_filter_sweep(
    f0: float = 130.81,
    cutoff_start_hz: float = 8000.0,
    cutoff_end_hz: float = 400.0,
    adsr: Adsr | None = None,
    sr: int = DEFAULT_SR,
) -> FloatArray:
    """ローパスのカットオフが指数的に下がるノコギリ波（4次の振幅特性で近似）。"""
    adsr = adsr or Adsr(note_s=1.5)
    env = adsr_envelope(adsr, sr)
    duration = len(env) / sr

    def amp(k: int, t: FloatArray) -> FloatArray:
        fc = cutoff_start_hz * (cutoff_end_hz / cutoff_start_hz) ** (t / duration)
        return (1.0 / k) / np.sqrt(1.0 + (k * f0 / fc) ** 8)

    return normalize(additive(f0, duration, amp, sr) * env)


def pluck(
    f0: float = 220.0, duration_s: float = 2.0, sr: int = DEFAULT_SR, seed: int = 0
) -> FloatArray:
    """Karplus-Strong の撥弦音。高域ほど速く減衰する。"""
    rng = np.random.default_rng(seed)
    delay = int(round(sr / f0 + 0.5))  # ループの実効遅延は delay - 0.5 サンプル
    buf = rng.uniform(-1, 1, delay)
    n = int(round(duration_s * sr))
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % delay]
        buf[i % delay] = 0.996 * 0.5 * (buf[i % delay] + buf[(i + 1) % delay])
    return normalize(out - out.mean())


def fm_bell(
    f0: float = 440.0,
    ratio: float = 1.4,
    index: float = 4.0,
    duration_s: float = 2.5,
    sr: int = DEFAULT_SR,
) -> FloatArray:
    """非整数比の FM による金属的なベル音。"""
    t = np.arange(int(round(duration_s * sr))) / sr
    amp_env = np.exp(-t / 0.6) * np.minimum(t / 0.002, 1.0)
    index_env = index * np.exp(-t / 0.4)
    tone = np.sin(2 * np.pi * f0 * t + index_env * np.sin(2 * np.pi * f0 * ratio * t))
    return normalize(tone * amp_env)


def with_noise(x: FloatArray, level_db: float = -20.0, seed: int = 1) -> FloatArray:
    """信号ピーク基準 level_db のホワイトノイズを全体に加える。"""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, len(x))
    noise *= np.max(np.abs(x)) * 10 ** (level_db / 20) / np.max(np.abs(noise))
    return x + noise


def with_reverb(
    x: FloatArray, rt60_s: float = 1.5, wet: float = 0.5, sr: int = DEFAULT_SR, seed: int = 2
) -> FloatArray:
    """指数減衰ノイズのインパルス応答で残響を付ける。"""
    rng = np.random.default_rng(seed)
    n_ir = int(rt60_s * sr)
    t = np.arange(n_ir) / sr
    ir = rng.normal(0, 1, n_ir) * 10 ** (-3 * t / rt60_s)
    ir /= np.sqrt(np.sum(ir**2))
    padded = np.concatenate([x, np.zeros(n_ir)])
    reverb = np.convolve(padded, ir)[: len(padded)]
    return normalize((1 - wet) * padded + wet * reverb)


def chord(notes: tuple[str, ...] = ("C4", "E4", "G4"), adsr: Adsr | None = None) -> FloatArray:
    """複数の音を同時に鳴らす（単音でない入力の検証用）。"""
    return normalize(sum((saw(note_to_hz(n), adsr) for n in notes), np.zeros(1)))


def with_silence(
    x: FloatArray, before_s: float, after_s: float, sr: int = DEFAULT_SR
) -> FloatArray:
    return np.concatenate([np.zeros(int(before_s * sr)), x, np.zeros(int(after_s * sr))])


def write_wav(path: Path, x: FloatArray, sr: int = DEFAULT_SR, channels: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.tile(x[:, None], (1, channels)) if channels > 1 else x
    sf.write(path, data, sr, subtype="PCM_24")
    return path


def standard_set() -> dict[str, FloatArray]:
    """手元で試聴・解析するための代表的なテスト音。"""
    return {
        "saw_c4": saw(),
        "saw_filter_sweep_c3": saw_filter_sweep(),
        "square_c4": square(),
        "pluck_a3": pluck(),
        "fm_bell_a4": fm_bell(),
        "saw_noisy_c4": with_noise(with_silence(saw(), 0.2, 0.5)),
        "saw_reverb_c4": with_reverb(saw(adsr=Adsr(release_s=0.1))),
        "chord_c_major": chord(),
    }
