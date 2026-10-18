"""録音を参照音と比べて試行として保存するユースケース。"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from synth_ai.adapters.base import SynthAdapter
from synth_ai.core.audio.analyze import AnalysisResult, analyze_file
from synth_ai.core.comparison.align import align
from synth_ai.core.comparison.compare import compute_differences, spectral_distance
from synth_ai.core.comparison.models import (
    Alignment,
    Comparison,
    Difference,
    DifferenceKind,
    FeatureProgress,
)
from synth_ai.core.comparison.plots import plot_difference
from synth_ai.core.comparison.report import render_markdown
from synth_ai.core.comparison.suggest import suggest
from synth_ai.core.history.models import TrialMeta
from synth_ai.core.history.store import (
    load_comparison,
    next_trial,
    now_iso,
    rebuild_history,
    trial_dir,
)
from synth_ai.core.sound_spec.io import load_json, save_json
from synth_ai.core.sound_spec.models import AudioAnalysis, Issue, PatchRecipe, Severity
from synth_ai.core.workflow.files import (
    ANALYSIS,
    MissingRunFileError,
    load_or_derive_spec,
    recipe_dir,
)

REFERENCE_WAV = "reference.wav"
PITCH_MISMATCH_CENTS = 50.0
DETUNE_CENTS = 10.0
RECORDING_ISSUES = {"clipping", "low_snr", "truncated_tail", "pitch_unreliable"}


class ReferenceMismatchError(RuntimeError):
    """参照WAVが解析時と異なる。"""


@dataclass(frozen=True)
class TrialResult:
    trial: int
    directory: Path
    comparison: Comparison
    markdown: str


def reference_wav(run_dir: Path, analysis: AudioAnalysis) -> Path:
    """run_dir/reference.wav、なければ解析時のパス。中身が解析時と同じことを確かめる。"""
    candidates = [run_dir / REFERENCE_WAV, Path(analysis.source.path)]
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        raise MissingRunFileError(
            f"参照WAVが見つかりません（{candidates[0]} または {candidates[1]}）"
        )
    return path


def _condition_issues(a: Alignment, recording: AnalysisResult) -> list[Issue]:
    issues: list[Issue] = []
    if a.pitch_offset_cents is not None:
        cents = a.pitch_offset_cents
        if abs(cents) > PITCH_MISMATCH_CENTS:
            issues.append(
                Issue(
                    code="pitch_mismatch",
                    message=f"音程が違う（{cents:+.0f} セント）。参照と同じ音程で録音し直す",
                )
            )
        elif abs(cents) > DETUNE_CENTS:
            issues.append(
                Issue(
                    code="detuned",
                    message=f"音程が {cents:+.0f} セントずれている"
                    "（チューニングやデチューンを確認）",
                    severity=Severity.INFO,
                )
            )
    if a.recording_duration_s < 0.8 * a.reference_duration_s:
        issues.append(
            Issue(
                code="short_recording",
                message="録音が参照より短い。ノートの長さと録音の長さを参照にそろえる",
                severity=Severity.INFO,
            )
        )
    if a.gain_db > 20:
        issues.append(
            Issue(
                code="quiet_recording",
                message=f"録音の音量が小さい（{a.gain_db:+.0f} dB 補正）。ノイズの影響を受けやすい",
                severity=Severity.INFO,
            )
        )
    issues += [
        Issue(code=f"recording_{i.code}", message=f"録音: {i.message}", severity=i.severity)
        for i in recording.analysis.issues
        if i.code in RECORDING_ISSUES
    ]
    return issues


def _progress(
    previous: Comparison | None, current: tuple[Difference, ...]
) -> tuple[FeatureProgress, ...]:
    if previous is None:
        return ()
    before = {
        d.feature: d.severity for d in previous.differences if d.kind is DifferenceKind.FEATURE
    }
    out = []
    for d in current:
        if d.kind is not DifferenceKind.FEATURE or d.feature not in before:
            continue
        prev = before[d.feature]
        if max(prev, d.severity) >= 1.0:
            out.append(
                FeatureProgress(
                    feature=d.feature, previous_severity=prev, current_severity=d.severity
                )
            )
    return tuple(sorted(out, key=lambda p: p.previous_severity, reverse=True))


def run_trial(
    run_dir: Path, recording_path: Path, adapter: SynthAdapter | None, plots: bool = True
) -> TrialResult:
    saved = load_json(AudioAnalysis, _require(run_dir / ANALYSIS))
    ref_path = reference_wav(run_dir, saved)
    reference = analyze_file(ref_path, saved.analysis_id)
    if reference.analysis.source.sha256 != saved.source.sha256:
        raise ReferenceMismatchError(f"{ref_path} の内容が解析時と異なります")

    trial = next_trial(run_dir)
    out = trial_dir(run_dir, trial)
    recording = analyze_file(recording_path, f"{saved.analysis_id}-trial-{trial:03d}")

    spec = load_or_derive_spec(run_dir)
    recipe = None
    if adapter is not None:
        recipe_path = recipe_dir(run_dir, adapter.synth_id) / "recipe.json"
        if recipe_path.is_file():
            recipe = load_json(PatchRecipe, recipe_path)

    pair = align(reference, recording)
    differences = tuple(compute_differences(pair, reference, recording))
    previous = load_comparison(run_dir, trial - 1) if trial > 1 else None
    comparison = Comparison(
        comparison_id=f"{saved.analysis_id}-trial-{trial:03d}",
        reference_analysis_id=saved.analysis_id,
        recording_analysis_id=recording.analysis.analysis_id,
        synth_id=adapter.synth_id if adapter else None,
        recipe_id=recipe.recipe_id if recipe else None,
        alignment=pair.alignment,
        differences=differences,
        distance=spectral_distance(pair),
        suggestions=suggest(spec, differences, recipe, adapter),
        progress=_progress(previous, differences),
        issues=tuple(_condition_issues(pair.alignment, recording)),
    )

    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(recording_path, out / "recording.wav")
    save_json(recording.analysis, out / "analysis.json")
    if recipe is not None:
        save_json(recipe, out / "recipe.json")
    save_json(comparison, out / "comparison.json")
    markdown = render_markdown(comparison, trial, previous.distance.mean_db if previous else None)
    (out / "comparison.md").write_text(markdown, encoding="utf-8")
    if plots:
        plot_difference(pair, comparison, out / "difference.png")
    save_json(
        TrialMeta(
            trial=trial,
            created_at=now_iso(),
            recording_source=str(recording_path),
            recording_sha256=recording.analysis.source.sha256,
            synth_id=comparison.synth_id,
            recipe_id=comparison.recipe_id,
        ),
        out / "trial.json",
    )
    rebuild_history(run_dir)
    return TrialResult(trial, out, comparison, markdown)


def _require(path: Path) -> Path:
    if not path.is_file():
        raise MissingRunFileError(f"{path} がありません。先に analyze を実行してください")
    return path
