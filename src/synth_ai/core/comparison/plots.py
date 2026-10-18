"""比較のグラフ（difference.png）。各段は 1 本の縦軸に 1 つの量だけを描く。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from synth_ai.core.audio import features as F

# plt は Agg バックエンドを設定済みの audio.plots から使う
from synth_ai.core.audio.plots import SERIES, SURFACE, TEXT, TEXT_SECONDARY, plt, save_figure
from synth_ai.core.comparison.align import AlignedPair
from synth_ai.core.comparison.compare import BANDS
from synth_ai.core.comparison.models import SEGMENT_LABELS, Comparison, DifferenceKind, Segment

# 2 色の発散配色。中央（差なし）は無彩色
DIVERGING = LinearSegmentedColormap.from_list(
    "diverging", ["#2a78d6", "#a9c8ee", "#e4e3df", "#f2b394", "#eb6834"]
)
REFERENCE_COLOR, RECORDING_COLOR = SERIES[0], SERIES[1]


def _long_term_spectrum(x: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    n_fft = 8192
    freqs = np.fft.rfftfreq(n_fft, 1 / sr)
    frames = [
        np.abs(np.fft.rfft(x[i : i + n_fft] * np.hanning(n_fft))) ** 2
        for i in range(0, max(len(x) - n_fft, 1), n_fft // 2)
    ]
    power = np.mean(frames, axis=0) if frames else np.zeros_like(freqs)
    db = 10 * np.log10(np.maximum(power, F.EPS))
    return freqs, db - db.max()


def plot_difference(pair: AlignedPair, comparison: Comparison, path: Path) -> Path:
    sr = pair.sample_rate
    fig, (ax_env, ax_spec, ax_band) = plt.subplots(3, 1, figsize=(9, 10))

    # 録音は破線にして、参照と重なっても両方が見えるようにする
    for x, color, label, style in (
        (pair.reference, REFERENCE_COLOR, "参照", "-"),
        (pair.recording, RECORDING_COLOR, "録音", (0, (4, 2))),
    ):
        env = F.rms_envelope(x, sr)
        ax_env.plot(env.times, np.maximum(env.db, -80), color=color, label=label, linestyle=style)
        freqs, db = _long_term_spectrum(x, sr)
        ax_spec.plot(freqs[1:], db[1:], color=color, linewidth=0.9, label=label, linestyle=style)
    ax_env.set_title("音量の包絡（それぞれのピーク基準、発音開始をそろえて表示）")
    ax_env.set_xlabel("時間 [s]")
    ax_env.set_ylabel("dB")
    ax_env.set_ylim(-80, 3)
    ax_env.legend(loc="upper right")

    ax_spec.set_title("平均スペクトル")
    ax_spec.set_xscale("log")
    ax_spec.set_xlim(20, sr / 2)
    ax_spec.set_ylim(-100, 5)
    ax_spec.set_xlabel("周波数 [Hz]")
    ax_spec.set_ylabel("dB（最大 0）")
    ax_spec.legend(loc="upper right")

    band_names = [b[0] for b in BANDS]
    seg_order = [s for s in Segment]
    grid = np.full((len(seg_order), len(band_names)), np.nan)
    for d in comparison.differences:
        if d.kind is DifferenceKind.BAND and d.segment is not None and d.band in band_names:
            grid[seg_order.index(d.segment), band_names.index(d.band)] = d.delta
    limit = max(6.0, float(np.nanmax(np.abs(grid))) if np.isfinite(grid).any() else 6.0)
    limit = min(limit, 24.0)
    mesh = ax_band.imshow(grid, cmap=DIVERGING, vmin=-limit, vmax=limit, aspect="auto")
    for i in range(len(seg_order)):
        for j in range(len(band_names)):
            if np.isfinite(grid[i, j]):
                ax_band.text(
                    j,
                    i,
                    f"{round(float(grid[i, j]), 1) + 0.0:+.1f}",
                    ha="center",
                    va="center",
                    color=TEXT,
                    fontsize=9,
                )
    ax_band.set_xticks(range(len(band_names)), [f"{b} Hz" for b in band_names])
    ax_band.set_yticks(range(len(seg_order)), [SEGMENT_LABELS[s] for s in seg_order])
    ax_band.set_title("区間 × 周波数帯の音色の差（録音 − 参照、区間の音量差を除く）")
    ax_band.grid(False)
    ax_band.set_facecolor(SURFACE)
    bar = fig.colorbar(mesh, ax=ax_band, pad=0.01)
    bar.set_label("dB（+ は録音が強い）", color=TEXT_SECONDARY)
    return save_figure(fig, path)
