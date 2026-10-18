"""試行ディレクトリの読み書き。

runs/<id>/trials/<NNN>/
  trial.json          メタ情報（日時、録音の元ファイル、使ったレシピ）
  recording.wav       比較した録音のコピー
  analysis.json       録音の解析
  recipe.json         比較時点のレシピのコピー（あれば）
  comparison.json/md  比較結果
  difference.png      比較のグラフ
  note.json           人の評価（synth-ai trial note で記入）
runs/<id>/history.json  全試行の一覧（試行ディレクトリから作り直す）
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from synth_ai.core.comparison.models import Comparison
from synth_ai.core.history.models import History, TrialMeta, TrialNote, TrialRecord
from synth_ai.core.sound_spec.io import load_json, save_json

TRIALS = "trials"
HISTORY = "history.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def trial_dir(run_dir: Path, trial: int) -> Path:
    return run_dir / TRIALS / f"{trial:03d}"


def trial_numbers(run_dir: Path) -> list[int]:
    root = run_dir / TRIALS
    if not root.is_dir():
        return []
    return sorted(int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit())


def next_trial(run_dir: Path) -> int:
    numbers = trial_numbers(run_dir)
    return (numbers[-1] + 1) if numbers else 1


def load_comparison(run_dir: Path, trial: int) -> Comparison | None:
    path = trial_dir(run_dir, trial) / "comparison.json"
    return load_json(Comparison, path) if path.is_file() else None


def load_note(run_dir: Path, trial: int) -> TrialNote | None:
    path = trial_dir(run_dir, trial) / "note.json"
    return load_json(TrialNote, path) if path.is_file() else None


def save_note(
    run_dir: Path,
    trial: int,
    *,
    closeness: int | None = None,
    preference: int | None = None,
    memo: str | None = None,
    changes: tuple[str, ...] = (),
) -> TrialNote:
    """指定した項目だけを更新する（変更内容は追記）。"""
    if not (trial_dir(run_dir, trial) / "trial.json").is_file():
        raise FileNotFoundError(f"試行 {trial} がありません: {trial_dir(run_dir, trial)}")
    current = load_note(run_dir, trial) or TrialNote()
    note = TrialNote(
        closeness=closeness if closeness is not None else current.closeness,
        preference=preference if preference is not None else current.preference,
        memo=memo if memo is not None else current.memo,
        changes=current.changes + changes,
        updated_at=now_iso(),
    )
    save_json(note, trial_dir(run_dir, trial) / "note.json")
    rebuild_history(run_dir)
    return note


def rebuild_history(run_dir: Path) -> History:
    analysis_id = ""
    records = []
    for n in trial_numbers(run_dir):
        meta_path = trial_dir(run_dir, n) / "trial.json"
        comparison = load_comparison(run_dir, n)
        if not meta_path.is_file() or comparison is None:
            continue
        meta = load_json(TrialMeta, meta_path)
        analysis_id = comparison.reference_analysis_id
        records.append(
            TrialRecord(
                trial=n,
                created_at=meta.created_at,
                synth_id=meta.synth_id,
                recipe_id=meta.recipe_id,
                recording_source=meta.recording_source,
                distance_db=comparison.distance.mean_db,
                significant_differences=len(comparison.significant),
                top_differences=tuple(d.message for d in comparison.significant[:3]),
                suggestions=tuple(s.message for s in comparison.suggestions),
                note=load_note(run_dir, n),
            )
        )
    history = History(reference_analysis_id=analysis_id, trials=tuple(records))
    save_json(history, run_dir / HISTORY)
    return history
