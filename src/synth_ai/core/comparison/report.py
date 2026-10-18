"""比較結果の Markdown レポート（comparison.md）。"""

from __future__ import annotations

from synth_ai.core.comparison.models import Comparison
from synth_ai.core.comparison.wording import as_feature
from synth_ai.core.sound_spec.features import LABELS
from synth_ai.core.sound_spec.models import Severity

MAX_LISTED = 10


def render_markdown(c: Comparison, trial: int, previous_distance_db: float | None) -> str:
    a = c.alignment
    pitch = "—" if a.pitch_offset_cents is None else f"{a.pitch_offset_cents:+.1f} セント"
    lines = [
        f"# 比較レポート: 試行 {trial:03d}",
        "",
        f"- 参照: `{c.reference_analysis_id}` / 録音: `{c.recording_analysis_id}`",
        f"- 機種: {c.synth_id or '—'} / レシピ: {c.recipe_id or '—'}",
        "",
        "## 比較条件",
        "",
        f"- 発音開始のずれ {a.offset_s * 1000:+.1f} ms、音量補正 {a.gain_db:+.1f} dB、"
        f"音程の差 {pitch}",
        f"- 比較した長さ {a.compared_duration_s:.2f} s"
        f"（参照 {a.reference_duration_s:.2f} s / 録音 {a.recording_duration_s:.2f} s）",
    ]
    marks = {Severity.INFO: "i", Severity.WARNING: "!", Severity.ERROR: "x"}
    lines += [f"- [{marks[i.severity]}] {i.message}" for i in c.issues]

    lines += ["", "## 次の調整案", ""]
    if c.suggestions:
        for s in c.suggestions:
            lines.append(f"{s.priority}. **{s.message}**")
            if s.reason:
                lines.append(f"   - 根拠: {s.reason}")
    else:
        lines.append("有意な差がないため、調整案はありません。聴き比べて好みで判断してください。")

    lines += ["", "## 主な違い", ""]
    significant = c.significant
    if significant:
        lines += [f"- {d.message}" for d in significant[:MAX_LISTED]]
        if len(significant) > MAX_LISTED:
            lines.append(f"- ほか {len(significant) - MAX_LISTED} 件（comparison.json を参照）")
    else:
        lines.append("許容幅を超える差はありません。")

    if c.progress or previous_distance_db is not None:
        lines += ["", "## 前回からの変化", ""]
        for p in c.progress:
            feature = as_feature(p.feature)
            label = LABELS[feature] if feature else p.feature
            state = (
                "改善"
                if p.improved
                else "悪化"
                if p.current_severity > p.previous_severity
                else "同じ"
            )
            lines.append(
                f"- {label}: {state}"
                f"（差の大きさ {p.previous_severity:.1f} → {p.current_severity:.1f}）"
            )
        if previous_distance_db is not None:
            lines.append(
                f"- スペクトル距離: {previous_distance_db:.1f} → {c.distance.mean_db:.1f} dB"
            )

    resolutions = ", ".join(f"{n}: {v:.1f}" for n, v in c.distance.per_resolution_db.items())
    lines += [
        "",
        "## 参考値",
        "",
        f"- スペクトル距離（平均）{c.distance.mean_db:.1f} dB（解像度別 {resolutions}）",
        "  - 録音条件や音の種類で変わるため、成功の判定には使わない",
        "",
        "## 聴いた感想を記録する",
        "",
        "```bash",
        f'synth-ai trial note <run_dir> {trial} --closeness 1-5 --preference 1-5 --memo "…"',
        "```",
    ]
    return "\n".join(lines) + "\n"
