from pathlib import Path

import pytest

from synth_ai.core.history.store import (
    load_note,
    next_trial,
    rebuild_history,
    save_note,
    trial_dir,
    trial_numbers,
)


def test_numbering(tmp_path: Path) -> None:
    assert next_trial(tmp_path) == 1
    trial_dir(tmp_path, 1).mkdir(parents=True)
    trial_dir(tmp_path, 3).mkdir(parents=True)
    (tmp_path / "trials" / "notes").mkdir()
    assert trial_numbers(tmp_path) == [1, 3]
    assert next_trial(tmp_path) == 4
    assert trial_dir(tmp_path, 4).name == "004"


def test_note_requires_trial(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        save_note(tmp_path, 1, closeness=3)


def test_empty_history(tmp_path: Path) -> None:
    history = rebuild_history(tmp_path)
    assert history.trials == ()
    assert (tmp_path / "history.json").is_file()
    assert load_note(tmp_path, 1) is None
