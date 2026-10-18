"""解析結果のグラフ（PNG）。各図は 1 本の縦軸に 1 つの量だけを描く。"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from synth_ai.core.audio import features as F  # noqa: E402
from synth_ai.core.audio.analyze import AnalysisResult  # noqa: E402

__all__ = [
    "SERIES",
    "SURFACE",
    "TEXT",
    "TEXT_SECONDARY",
    "plot_all",
    "plt",
    "save_figure",
]

JAPANESE_FONTS = ("Hiragino Sans", "BIZ UDGothic", "Noto Sans CJK JP", "IPAexGothic", "Yu Gothic")


def _japanese_font() -> list[str]:
    """インストール済みの日本語フォントを 1 つ選ぶ（なければ空）。"""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    return [name for name in JAPANESE_FONTS if name in installed][:1]


SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
MARKER = "#52514e"
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "seq_blue", [SURFACE, "#9cc3ee", "#2a78d6", "#0d2f5c"]
)

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.titlecolor": TEXT,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "font.size": 9,
        "font.family": [*_japanese_font(), "DejaVu Sans"],
        "lines.linewidth": 1.5,
        "legend.frameon": False,
        "legend.labelcolor": TEXT_SECONDARY,
        "savefig.dpi": 130,
    }
)


def _mark_segments(ax: Axes, result: AnalysisResult) -> None:
    env = result.analysis.envelope
    if env is None:
        return
    marks: list[tuple[str, float | None]] = [("onset", env.onset_s), ("peak", env.peak_s)]
    if env.sustained:
        marks += [("sustain", env.sustain_start_s), ("release", env.release_start_s)]
    for i, (label, t) in enumerate(marks):
        if t is None:
            continue
        ax.axvline(t, color=MARKER, linewidth=0.8, linestyle=(0, (3, 3)))
        ax.annotate(
            label,
            (t, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(3, -10 - 11 * (i % 2)),  # 近接するラベルが重ならないよう上下にずらす
            textcoords="offset points",
            color=TEXT_SECONDARY,
            fontsize=8,
        )


def plot_envelope(result: AnalysisResult, path: Path) -> Path:
    x, sr = result.audio.samples, result.audio.sample_rate
    env = result.envelope
    fig, (ax_wave, ax_env) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    # 1 周期ずつ描くとモアレになるため、短い区間ごとの最小・最大を帯で描く
    block = max(len(x) // 2000, 1)
    n = len(x) // block * block
    blocks = x[:n].reshape(-1, block)
    t = (np.arange(len(blocks)) + 0.5) * block / sr
    ax_wave.fill_between(t, blocks.min(axis=1), blocks.max(axis=1), color=SERIES[0], linewidth=0)
    ax_wave.set_title("波形")
    ax_wave.set_ylabel("振幅")
    ax_env.plot(env.times, env.db, color=SERIES[0])
    ax_env.set_ylim(max(float(env.db.min()), -80.0) - 3, 3)
    ax_env.set_title("RMS 包絡（ピーク基準）")
    ax_env.set_ylabel("dB")
    ax_env.set_xlabel("時間 [s]")
    for ax in (ax_wave, ax_env):
        _mark_segments(ax, result)
    return save_figure(fig, path)


def plot_spectrogram(result: AnalysisResult, path: Path) -> Path:
    spec = result.spectrogram
    db = F.to_db(spec.magnitude)
    db -= db.max()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    mesh = ax.pcolormesh(
        spec.times, spec.freqs[1:], db[1:], cmap=SEQUENTIAL, vmin=-90, vmax=0, shading="auto"
    )
    series = result.analysis.timeseries
    if series is not None:
        centroid = np.array([np.nan if v is None else v for v in series.centroid_hz])
        ax.plot(np.arange(len(centroid)) * series.hop_s, centroid, color=SERIES[1], label="重心")
        ax.legend(loc="upper right")
    ax.set_yscale("log")
    ax.set_ylim(20, result.audio.sample_rate / 2)
    ax.set_title("スペクトログラムとスペクトル重心")
    ax.set_xlabel("時間 [s]")
    ax.set_ylabel("周波数 [Hz]")
    ax.grid(False)
    fig.colorbar(mesh, ax=ax, label="dB（最大 0）", pad=0.01)
    return save_figure(fig, path)


def plot_spectrum(result: AnalysisResult, path: Path) -> Path:
    """定常区間のスペクトルと検出した倍音。"""
    x, sr = result.audio.samples, result.audio.sample_rate
    harmonics = result.analysis.harmonics
    fig, ax = plt.subplots(figsize=(9, 4))
    if harmonics is None:
        start, end = 0.0, min(len(x) / sr, 0.3)
    else:
        start, end = harmonics.window_start_s, harmonics.window_end_s
    seg = x[int(start * sr) : int(end * sr)]
    spectrum = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n=1 << 16))
    freqs = np.fft.rfftfreq(1 << 16, 1 / sr)
    db = F.to_db(spectrum)
    db -= db.max()
    ax.plot(freqs[1:], db[1:], color=SERIES[0], linewidth=0.8)
    if harmonics is not None:
        for p in harmonics.partials:
            ax.plot(p.freq_hz, p.level_db, "o", color=SERIES[1], markersize=4)
        ax.plot([], [], "o", color=SERIES[1], markersize=4, label="検出した倍音")
        ax.legend(loc="upper right")
    ax.set_xscale("log")
    ax.set_xlim(20, sr / 2)
    ax.set_ylim(-100, 5)
    ax.set_title(f"スペクトル（{start:.2f}〜{end:.2f} s の定常区間）")
    ax.set_xlabel("周波数 [Hz]")
    ax.set_ylabel("dB（最大 0）")
    return save_figure(fig, path)


def plot_harmonics(result: AnalysisResult, path: Path) -> Path:
    """倍音ごとのレベルの時間変化。"""
    series = result.analysis.timeseries
    fig, ax = plt.subplots(figsize=(9, 4))
    if series is not None and series.harmonic_levels_db:
        t = np.arange(len(series.harmonic_levels_db[0])) * series.hop_s
        for k, row in enumerate(series.harmonic_levels_db, start=1):
            values = np.array([np.nan if v is None else v for v in row])
            ax.plot(t, values, color=SERIES[(k - 1) % len(SERIES)], label=f"{k} 次")
        ax.legend(loc="lower left", ncol=4)
    else:
        ax.text(
            0.5, 0.5, "ピッチ未確定のため倍音を追跡できません", ha="center", transform=ax.transAxes
        )
    ax.set_ylim(-80, 3)
    ax.set_title("倍音レベルの時間変化")
    ax.set_xlabel("時間 [s]")
    ax.set_ylabel("dB（最大 0）")
    return save_figure(fig, path)


def save_figure(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_all(result: AnalysisResult, out_dir: Path) -> list[Path]:
    return [
        plot_envelope(result, out_dir / "envelope.png"),
        plot_spectrogram(result, out_dir / "spectrogram.png"),
        plot_spectrum(result, out_dir / "spectrum.png"),
        plot_harmonics(result, out_dir / "harmonics.png"),
    ]
