from pathlib import Path

import pytest

from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.core.audio.analyze import analyze_file
from synth_ai.core.history.store import load_note, rebuild_history, save_note
from synth_ai.core.sound_spec.io import save_json
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.synthesis.test_signals import Adsr
from synth_ai.core.workflow.files import MissingRunFileError, write_recipe
from synth_ai.core.workflow.trial import ReferenceMismatchError, run_trial


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    ref = ts.write_wav(tmp_path / "ref.wav", ts.with_silence(ts.saw_filter_sweep(), 0.1, 0.2))
    out = tmp_path / "run"
    save_json(analyze_file(ref, "ref-t").analysis, out / "analysis.json")
    (out / "reference.wav").write_bytes(ref.read_bytes())
    return out


def test_two_trials(run_dir: Path, tmp_path: Path) -> None:
    adapter = Kronos2Adapter()
    write_recipe(run_dir, adapter)
    take1 = ts.write_wav(tmp_path / "t1.wav", ts.saw(130.81, adsr=Adsr(attack_s=0.08, note_s=1.5)))
    take2 = ts.write_wav(tmp_path / "t2.wav", ts.saw_filter_sweep(cutoff_end_hz=600))

    first = run_trial(run_dir, take1, adapter, plots=False)
    assert first.trial == 1
    assert first.comparison.recipe_id is not None
    assert 1 <= len(first.comparison.suggestions) <= 3
    for name in (
        "recording.wav",
        "analysis.json",
        "recipe.json",
        "comparison.json",
        "comparison.md",
        "trial.json",
    ):
        assert (first.directory / name).is_file()
    assert first.comparison.progress == ()

    save_note(run_dir, 1, closeness=2, preference=4, memo="明るすぎ", changes=("cutoff 上げ",))
    save_note(run_dir, 1, memo="明るすぎる", changes=("EG 調整",))
    note = load_note(run_dir, 1)
    assert note is not None and note.closeness == 2 and note.memo == "明るすぎる"
    assert note.changes == ("cutoff 上げ", "EG 調整")

    second = run_trial(run_dir, take2, adapter, plots=True)
    assert second.trial == 2
    assert (second.directory / "difference.png").is_file()
    assert second.comparison.distance.mean_db < first.comparison.distance.mean_db
    assert any(p.improved for p in second.comparison.progress)
    assert "前回からの変化" in second.markdown

    history = rebuild_history(run_dir)
    assert [t.trial for t in history.trials] == [1, 2]
    assert history.trials[0].note is not None and history.trials[0].note.preference == 4
    assert history.reference_analysis_id == "ref-t"


def test_pitch_mismatch_is_reported(run_dir: Path, tmp_path: Path) -> None:
    take = ts.write_wav(tmp_path / "t.wav", ts.saw_filter_sweep(f0=196.0))
    result = run_trial(run_dir, take, None, plots=False)
    assert "pitch_mismatch" in {i.code for i in result.comparison.issues}
    assert result.comparison.synth_id is None


def test_reference_changed(run_dir: Path, tmp_path: Path) -> None:
    ts.write_wav(run_dir / "reference.wav", ts.saw())
    take = ts.write_wav(tmp_path / "t.wav", ts.saw())
    with pytest.raises(ReferenceMismatchError):
        run_trial(run_dir, take, None, plots=False)


def test_missing_analysis(tmp_path: Path) -> None:
    with pytest.raises(MissingRunFileError):
        run_trial(tmp_path, tmp_path / "x.wav", None)
