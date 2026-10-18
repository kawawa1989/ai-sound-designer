"""AudioAnalysis の人間向け要約（観測値と、その読み方）。"""

from __future__ import annotations

from synth_ai.core.sound_spec.models import AudioAnalysis, Severity

_SEVERITY_MARK = {Severity.INFO: "i", Severity.WARNING: "!", Severity.ERROR: "x"}


def _fmt(value: float | None, unit: str, digits: int = 0) -> str:
    return "—" if value is None else f"{value:.{digits}f} {unit}"


def summarize(a: AudioAnalysis) -> str:
    lines = [f"解析: {a.analysis_id}  ({a.source.path})"]
    lines.append(
        f"  長さ {a.source.analyzed_duration_s:.2f} s / ピーク {a.levels.peak_dbfs:.1f} dBFS / "
        f"S/N {'≥' if a.levels.snr_is_lower_bound else ''}{a.levels.snr_db:.0f} dB"
    )
    if a.pitch:
        p = a.pitch
        lines.append(
            f"ピッチ: {p.note} {round(p.cents_offset, 1) + 0.0:+.1f} セント"
            f"（{p.f0_hz:.2f} Hz、確信度 {p.confidence:.2f}）"
        )
    else:
        lines.append("ピッチ: 推定できず")
    if a.envelope:
        e = a.envelope
        sustain = (
            f"サステイン {_fmt(e.sustain_level_db, 'dB', 1)} / リリース {_fmt(e.release_ms, 'ms')}"
            if e.sustained
            else f"サステインなし（減衰 {_fmt(e.decay_rate_db_per_s, 'dB/s', 1)}）"
        )
        lines.append(
            f"包絡: アタック {_fmt(e.attack_ms, 'ms', 1)} / "
            f"ディケイ {_fmt(e.decay_ms, 'ms')} / {sustain}"
        )
    if a.spectral:
        s = a.spectral
        ratio = (
            "" if s.centroid_ratio_to_f0 is None else f"（基音の {s.centroid_ratio_to_f0:.1f} 倍）"
        )
        lines.append(
            f"明るさ: 重心 {s.centroid_hz_mean:.0f} Hz{ratio}、"
            f"発音直後 {s.centroid_hz_start:.0f} → 終盤 {s.centroid_hz_end:.0f} Hz"
            f"（×{s.brightness_change_ratio:.2f}）、平坦度 {s.flatness_mean:.3f}"
        )
    if a.harmonics:
        h = a.harmonics
        top = "、".join(f"{p.number}次 {p.level_db:.1f}" for p in h.partials[:6])
        odd_even = (
            "" if h.odd_even_ratio_db is None else f"、奇数/偶数 {h.odd_even_ratio_db:+.1f} dB"
        )
        lines.append(
            f"倍音: 整数倍音率 {h.harmonic_energy_ratio:.2f}、"
            f"非調和 {h.inharmonicity_cents:.1f} セント"
            f"{odd_even}"
        )
        lines.append(f"  レベル(dB): {top}")
    if a.issues:
        lines.append("注意:")
        lines += [f"  [{_SEVERITY_MARK[i.severity]}] {i.code}: {i.message}" for i in a.issues]
    return "\n".join(lines)
