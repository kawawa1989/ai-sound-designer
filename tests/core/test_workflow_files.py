from pathlib import Path

import pytest

from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.core.audio.analyze import analyze_file
from synth_ai.core.sound_spec.io import save_json
from synth_ai.core.sound_spec.models import SoundSpec
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.workflow.files import (
    MissingRunFileError,
    recipe_dir,
    write_recipe,
    write_sound_spec,
)


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    result = analyze_file(ts.write_wav(tmp_path / "ref.wav", ts.saw()), "ref-1")
    out = tmp_path / "run"
    save_json(result.analysis, out / "analysis.json")
    return out


def test_spec_then_recipe(run_dir: Path) -> None:
    spec, path = write_sound_spec(run_dir)
    assert path == run_dir / "sound_spec.json"
    files = write_recipe(run_dir, FakeSynthAdapter())
    assert files.json_path == recipe_dir(run_dir, "fake") / "recipe.json"
    assert files.markdown_path.read_text().startswith("# Fake recipe")
    assert files.recipe.sound_spec_id == spec.spec_id


def test_recipe_does_not_rewrite_saved_spec(run_dir: Path) -> None:
    write_sound_spec(run_dir)
    before = (run_dir / "sound_spec.json").read_text()
    write_recipe(run_dir, FakeSynthAdapter())
    assert (run_dir / "sound_spec.json").read_text() == before


def test_recipe_derives_spec_when_missing(run_dir: Path) -> None:
    write_recipe(run_dir, FakeSynthAdapter())
    assert SoundSpec.model_validate_json((run_dir / "sound_spec.json").read_text())


def test_missing_analysis(tmp_path: Path) -> None:
    with pytest.raises(MissingRunFileError, match="analyze"):
        write_sound_spec(tmp_path)
