from pathlib import Path

import pytest

from synth_ai.core.history.store import (
    load_note,
    next_trial,
    rebuild_history,
    save_note,
    trial_dir,
    trial_numbers,
    trial_synths,
)


def test_numbering(tmp_path: Path) -> None:
    assert next_trial(tmp_path, "s") == 1
    trial_dir(tmp_path, "s", 1).mkdir(parents=True)
    trial_dir(tmp_path, "s", 3).mkdir(parents=True)
    (tmp_path / "trials" / "s" / "notes").mkdir()
    assert trial_numbers(tmp_path, "s") == [1, 3]
    assert next_trial(tmp_path, "s") == 4
    assert trial_dir(tmp_path, "s", 4).name == "004"
    # 機種ごとに番号を付ける
    assert next_trial(tmp_path, "other") == 1
    assert trial_dir(tmp_path, None, 1) == tmp_path / "trials" / "unknown" / "001"
    trial_dir(tmp_path, None, 1).mkdir(parents=True)
    assert trial_synths(tmp_path) == ["s", None]


def test_note_requires_trial(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        save_note(tmp_path, "s", 1, closeness=3)


def test_empty_history(tmp_path: Path) -> None:
    history = rebuild_history(tmp_path)
    assert history.trials == ()
    assert (tmp_path / "history.json").is_file()
    assert load_note(tmp_path, "s", 1) is None
