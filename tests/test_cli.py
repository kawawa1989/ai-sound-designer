import json
from pathlib import Path

import pytest
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


def test_compare_and_trial_commands(tmp_path: Path) -> None:
    runner = CliRunner()
    ref = write_wav(tmp_path / "ref.wav", saw())
    take = write_wav(tmp_path / "take.wav", saw() * 0.5)
    out = tmp_path / "run"
    assert runner.invoke(app, ["analyze", str(ref), "-o", str(out), "--no-plots"]).exit_code == 0
    assert (out / "reference.wav").is_file()
    result = runner.invoke(app, ["compare", str(out), str(take), "--no-plots"])
    assert result.exit_code == 0, result.output
    assert "比較レポート: 試行 001" in result.output
    result = runner.invoke(
        app, ["trial", "note", str(out), "1", "--closeness", "4", "--memo", "近い"]
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["trial", "list", str(out)])
    assert "[001]" in result.output and "近さ 4" in result.output and "近い" in result.output
    assert runner.invoke(app, ["trial", "note", str(out), "9", "--memo", "x"]).exit_code == 2
    assert runner.invoke(app, ["trial", "note", str(out), "1", "--closeness", "7"]).exit_code != 0


def test_compare_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["compare", str(tmp_path), str(tmp_path / "x.wav")])
    assert result.exit_code == 2


def test_capture_with_run_compares(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from synth_ai.infrastructure.capture import recorder as rec_module
    from tests.infrastructure.fakes import FakePort, FakeRecorder

    runner = CliRunner()
    ref = write_wav(tmp_path / "ref.wav", saw(196.0))  # G3
    out = tmp_path / "run"
    assert runner.invoke(app, ["analyze", str(ref), "-o", str(out), "--no-plots"]).exit_code == 0

    port = FakePort()
    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    monkeypatch.setattr(
        rec_module, "SoundDeviceRecorder", lambda *a: FakeRecorder(lambda: saw(196.0))
    )
    config = tmp_path / "local.yaml"
    config.write_text(
        "midi:\n  output_port: KRONOS\n"
        "test_note:\n  hold_s: 0.01\n  release_tail_s: 0\n"
        "capture:\n  pre_roll_s: 0\n"
    )
    result = runner.invoke(app, ["capture", "--run", str(out), "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert "G3" in result.output  # 参照音の音程で鳴らす
    assert port.messages[0].note == 55
    assert "比較レポート: 試行 001" in result.output
    assert len(list((out / "takes").glob("take-*.wav"))) == 1


def test_capture_requires_destination(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["capture", "--config", str(tmp_path / "none.yaml")])
    assert result.exit_code == 2


def test_devices_lists_ports(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from synth_ai.infrastructure.capture import recorder as rec_module

    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD"])
    monkeypatch.setattr(
        rec_module, "input_devices", lambda: [rec_module.InputDevice(1, "KRONOS", 2, 48000)]
    )
    config = tmp_path / "c.yaml"
    config.write_text("midi:\n  output_port: kronos\ncapture:\n  input_device: KRONOS\n")
    result = CliRunner().invoke(app, ["devices", "--config", str(config)])
    assert result.exit_code == 0
    assert "* KRONOS KEYBOARD" in result.output and "* KRONOS（2 ch" in result.output
