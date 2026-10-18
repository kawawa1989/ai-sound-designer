import json
from pathlib import Path

from typer.testing import CliRunner

from synth_ai.cli import app
from synth_ai.core.sound_spec.models import AudioAnalysis
from synth_ai.core.synthesis.test_signals import saw, write_wav


def test_adapters_command_lists_capabilities() -> None:
    result = CliRunner().invoke(app, ["adapters"])
    assert result.exit_code == 0
    assert '"synth_id": "kronos2"' in result.output
    assert '"parameter_write": "unverified"' in result.output


def test_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert json.loads(f'"{result.output.strip()}"')


def test_analyze_writes_outputs(tmp_path: Path) -> None:
    wav = write_wav(tmp_path / "saw.wav", saw())
    out = tmp_path / "run"
    result = CliRunner().invoke(app, ["analyze", str(wav), "--out", str(out), "--id", "ref-x"])
    assert result.exit_code == 0, result.output
    assert "ピッチ: C4" in result.output
    analysis = AudioAnalysis.model_validate_json((out / "analysis.json").read_text())
    assert analysis.analysis_id == "ref-x"
    for name in ("envelope", "spectrogram", "spectrum", "harmonics"):
        assert (out / f"{name}.png").stat().st_size > 0


def test_analyze_reports_missing_file(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["analyze", str(tmp_path / "x.wav"), "-o", str(tmp_path)])
    assert result.exit_code == 2
    assert "見つかりません" in result.output


def test_test_signals_command(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["test-signals", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "saw_c4.wav").exists()


def test_spec_and_recipe_commands(tmp_path: Path) -> None:
    wav = write_wav(tmp_path / "saw.wav", saw())
    out = tmp_path / "run"
    runner = CliRunner()
    assert runner.invoke(app, ["analyze", str(wav), "-o", str(out), "--no-plots"]).exit_code == 0
    result = runner.invoke(app, ["spec", str(out)])
    assert result.exit_code == 0, result.output
    assert "subtractive" in result.output
    result = runner.invoke(app, ["recipe", str(out), "--synth", "kronos2"])
    assert result.exit_code == 0, result.output
    assert "AL-1" in result.output
    assert (out / "recipes" / "kronos2" / "recipe.md").exists()


def test_recipe_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["spec", str(tmp_path)]).exit_code == 2
    result = runner.invoke(app, ["recipe", str(tmp_path), "--synth", "nope"])
    assert result.exit_code == 2
