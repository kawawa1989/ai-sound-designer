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
    assert "## kronos2（SoundSpec: " in result.output
    # PC3A8 の試行は別の番号で、--synth で絞り込める
    result = runner.invoke(app, ["compare", str(out), str(take), "-s", "pc3a8", "--no-plots"])
    assert result.exit_code == 0 and "trials/pc3a8/001" in result.output
    result = runner.invoke(app, ["trial", "list", str(out), "-s", "pc3a8"])
    assert "## pc3a8" in result.output and "kronos2" not in result.output
    note = ["trial", "note", str(out), "1", "-s", "pc3a8", "--memo", "pc"]
    assert runner.invoke(app, note).exit_code == 0
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


def test_calibrate_interactive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from synth_ai import registry
    from synth_ai.core.calibration.models import CalibrationCurve
    from synth_ai.core.synthesis.test_signals import Adsr
    from synth_ai.infrastructure.capture import recorder as rec_module
    from tests.infrastructure.fakes import FakePort, FakeRecorder

    attacks = iter([0.005, 0.1, 0.1, 0.4])  # 2 つめは録り直し
    port = FakePort()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    monkeypatch.setattr(
        rec_module,
        "SoundDeviceRecorder",
        lambda *a: FakeRecorder(lambda: saw(adsr=Adsr(attack_s=next(attacks), note_s=1.5))),
    )
    monkeypatch.setitem(registry.CALIBRATION_DIRS, "kronos2", tmp_path / "cal")
    monkeypatch.setattr("time.sleep", lambda _: None)  # 押さえる時間（最低 3 秒）を待たない
    config = tmp_path / "local.yaml"
    config.write_text(
        "midi:\n  output_port: KRONOS\n"
        "test_note:\n  hold_s: 0.01\n  release_tail_s: 0\n"
        "capture:\n  pre_roll_s: 0\n"
    )
    # 値ごとに「Enter（設定した）」→「Enter（採用）」。2 つめは r で録り直す
    answers = "\n\n" + "\nr\n\n" + "\n\n"
    result = CliRunner().invoke(
        app,
        ["calibrate", "al1.amp_eg.time.attack", "--values", "0,30,60", "--config", str(config)],
        input=answers,
    )
    assert result.exit_code == 0, result.output
    assert "Amp EG Time Attack" in result.output
    path = tmp_path / "cal" / "al1.amp_eg.time.attack__attack_time.json"
    curve = CalibrationCurve.model_validate_json(path.read_text())
    assert [p.parameter_value for p in curve.points] == [0, 30, 60]
    assert curve.is_monotonic
    assert "hold 3s" in curve.conditions  # アタックの測定では最低 3 秒押さえる
    assert curve.reference_note == "C4"
    assert len(list((tmp_path / "runs" / "calibration").rglob("*.wav"))) == 4


def test_calibrate_lists_parameters() -> None:
    result = CliRunner().invoke(app, ["calibrate", "--config", "/nonexistent.yaml"])
    assert result.exit_code == 0
    assert "al1.filter_a.frequency" in result.output


def test_calibrate_from_recordings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from synth_ai import registry
    from synth_ai.core.calibration.models import CalibrationCurve
    from synth_ai.core.synthesis.test_signals import Adsr

    monkeypatch.setitem(registry.CALIBRATION_DIRS, "kronos2", tmp_path / "cal")
    session = tmp_path / "session"
    for value, attack in ((0, 0.005), (30, 0.1), (60, 0.4)):
        write_wav(session / f"v{value}_try1.wav", saw(adsr=Adsr(attack_s=attack, note_s=1.5)))
    path = tmp_path / "cal" / "al1.amp_eg.time.attack__attack_time.json"
    path.parent.mkdir()
    path.write_text(
        CalibrationCurve(
            synth_id="kronos2",
            parameter_id="al1.amp_eg.time.attack",
            feature="attack_time",
            unit="ms",
            conditions="元の条件",
            measured_at="2026-10-25",
            points=(
                {"parameter_value": 0, "feature_value": 1},
                {"parameter_value": 1, "feature_value": 2},
            ),
        ).model_dump_json()
    )
    result = CliRunner().invoke(
        app,
        [
            "calibrate",
            "al1.amp_eg.time.attack",
            "--from-recordings",
            str(session),
            "--overwrite",
            "--config",
            str(tmp_path / "none.yaml"),
        ],
    )
    assert result.exit_code == 0, result.output
    curve = CalibrationCurve.model_validate_json(path.read_text())
    assert [p.parameter_value for p in curve.points] == [0, 30, 60]
    assert curve.conditions == "元の条件" and curve.measured_at == "2026-10-25"
    # --values で使う録音を絞れる
    args = ["calibrate", "al1.amp_eg.time.attack", "--from-recordings", str(session)]
    args += ["--values", "30,60", "--overwrite", "--config", str(tmp_path / "none.yaml")]
    assert CliRunner().invoke(app, args).exit_code == 0
    curve = CalibrationCurve.model_validate_json(path.read_text())
    assert [p.parameter_value for p in curve.points] == [30, 60]


TWO_SYNTHS = (
    "synth: kronos2\n"
    "midi:\n  output_port: KRONOS\n"
    "test_note:\n  hold_s: 0.01\n  release_tail_s: 0\n"
    "capture:\n  pre_roll_s: 0\n  input_device: UR22\n"
    "synths:\n  pc3a8:\n    midi:\n      output_port: PC3A\n      channel: 3\n"
)


def test_midi_probe_selects_synth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.infrastructure.fakes import FakePort

    opened: list[str] = []
    port = FakePort()

    def open_output(name: str) -> FakePort:
        opened.append(name)
        return port

    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD", "PC3A USB"])
    monkeypatch.setattr("mido.open_output", open_output)
    config = tmp_path / "local.yaml"
    config.write_text(TWO_SYNTHS)
    result = CliRunner().invoke(
        app, ["midi-probe", "--synth", "pc3a8", "--hold", "0.01", "--config", str(config)]
    )
    assert result.exit_code == 0, result.output
    assert opened == ["PC3A USB"]
    assert "pc3a8" in result.output
    assert port.messages[0].channel == 2  # 設定のチャンネル 3（mido は 0 始まり）
    assert all(m.type in {"note_on", "note_off", "control_change"} for m in port.messages)


def test_capture_unregistered_synth_compares_without_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from synth_ai.infrastructure.capture import recorder as rec_module
    from tests.infrastructure.fakes import FakePort, FakeRecorder

    runner = CliRunner()
    ref = write_wav(tmp_path / "ref.wav", saw())
    out = tmp_path / "run"
    assert runner.invoke(app, ["analyze", str(ref), "-o", str(out), "--no-plots"]).exit_code == 0
    monkeypatch.setattr("mido.get_output_names", lambda: ["PC3A USB"])
    monkeypatch.setattr("mido.open_output", lambda name: FakePort())
    monkeypatch.setattr(rec_module, "SoundDeviceRecorder", lambda *a: FakeRecorder(saw))
    config = tmp_path / "local.yaml"
    config.write_text(TWO_SYNTHS)
    result = runner.invoke(
        app, ["capture", "--run", str(out), "-s", "pc3a8", "--config", str(config)]
    )
    assert result.exit_code == 0, result.output
    assert "録音（pc3a8）" in result.output
    assert "比較レポート: 試行 001" in result.output


def test_unknown_synth_is_error(tmp_path: Path) -> None:
    config = tmp_path / "local.yaml"
    config.write_text(TWO_SYNTHS)
    for command in (["devices"], ["midi-probe"], ["capture", "x.wav"], ["calibrate"]):
        result = CliRunner().invoke(app, [*command, "--synth", "nope", "--config", str(config)])
        assert result.exit_code == 2, command
        assert "nope" in result.output


def test_devices_shows_selected_synth(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from synth_ai.infrastructure.capture import recorder as rec_module

    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD", "PC3A USB"])
    monkeypatch.setattr(rec_module, "input_devices", lambda: [])
    config = tmp_path / "c.yaml"
    config.write_text(TWO_SYNTHS)
    result = CliRunner().invoke(app, ["devices", "-s", "pc3a8", "--config", str(config)])
    assert result.exit_code == 0
    assert "機種: pc3a8" in result.output
    assert "* PC3A USB" in result.output and "  KRONOS KEYBOARD" in result.output


def test_calibrate_pc3a8_physical_units(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PC3A8 では、表の測る値（秒）を既定にし、単位を付けて案内する。"""
    from synth_ai import registry
    from synth_ai.core.calibration.models import CalibrationCurve
    from synth_ai.core.synthesis.test_signals import Adsr
    from synth_ai.infrastructure.capture import recorder as rec_module
    from tests.infrastructure.fakes import FakePort, FakeRecorder

    attacks = iter([0.002, 0.02, 0.1])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mido.get_output_names", lambda: ["Steinberg UR22mkII Port1"])
    monkeypatch.setattr("mido.open_output", lambda name: FakePort())
    monkeypatch.setattr(
        rec_module,
        "SoundDeviceRecorder",
        lambda *a: FakeRecorder(lambda: saw(adsr=Adsr(attack_s=next(attacks), note_s=1.5))),
    )
    monkeypatch.setitem(registry.CALIBRATION_DIRS, "pc3a8", tmp_path / "cal")
    monkeypatch.setattr("time.sleep", lambda _: None)
    config = tmp_path / "local.yaml"
    config.write_text(
        "synth: pc3a8\nmidi:\n  output_port: UR22mkII\n"
        "test_note:\n  hold_s: 0.01\n  release_tail_s: 0\n"
        "capture:\n  pre_roll_s: 0\n"
    )
    args = ["calibrate", "kva.ampenv.att1.time", "--values", "0,0.02,0.1", "--config", str(config)]
    result = CliRunner().invoke(app, args, input="\n\n" * 3)
    assert result.exit_code == 0, result.output
    assert "AMPENV › Att1 › Time を 0.02 s にして" in result.output
    assert "U-CC000" not in result.output
    curve = CalibrationCurve.model_validate_json(
        (tmp_path / "cal" / "kva.ampenv.att1.time__attack_time.json").read_text()
    )
    assert [p.parameter_value for p in curve.points] == [0, 0.02, 0.1]
    assert curve.synth_id == "pc3a8" and curve.parameter_scale == "linear"


def test_calibrate_pc3a8_lists_units(tmp_path: Path) -> None:
    config = tmp_path / "local.yaml"
    config.write_text("synth: pc3a8\n")
    result = CliRunner().invoke(app, ["calibrate", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert "kva.dspctl.lp_frq  brightness_end  16〜25088 Hz" in result.output


def test_calibrate_pc3a8_cc_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CC モード: 値ごとに CC 14 を送って録音し、最後に 0 に戻す。曲線は cc/ に分けて保存する。"""
    from synth_ai import registry
    from synth_ai.core.calibration.models import CalibrationCurve
    from synth_ai.core.synthesis.test_signals import saw_filter_sweep
    from synth_ai.infrastructure.capture import recorder as rec_module
    from tests.infrastructure.fakes import FakePort, FakeRecorder

    port = FakePort()
    cutoffs = iter([300.0, 1200.0, 6000.0])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("mido.get_output_names", lambda: ["Steinberg UR22mkII Port1"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    monkeypatch.setattr(
        rec_module,
        "SoundDeviceRecorder",
        lambda *a: FakeRecorder(
            lambda: saw_filter_sweep(
                f0=261.63, cutoff_start_hz=(c := next(cutoffs)), cutoff_end_hz=c
            )
        ),
    )
    monkeypatch.setitem(registry.CALIBRATION_DIRS, "pc3a8", tmp_path / "cal")
    monkeypatch.setattr("time.sleep", lambda _: None)
    config = tmp_path / "local.yaml"
    config.write_text(
        "synth: pc3a8\nmidi:\n  output_port: UR22mkII\n"
        "test_note:\n  hold_s: 0.01\n  release_tail_s: 0\n"
        "capture:\n  pre_roll_s: 0\n"
    )
    args = ["calibrate", "kva.dspctl.lp_frq", "--cc", "--values", "262,1047,4186"]
    result = CliRunner().invoke(app, [*args, "--config", str(config)], input="y\n")
    assert result.exit_code == 0, result.output
    assert "1026 KVA CC CAL を選んでいますか" in result.output
    controls = [(m.control, m.value) for m in port.messages if m.type == "control_change"]
    sent = [v for c, v in controls if c == 14]
    assert sent[:3] == [34, 63, 91] and sent[-1] == 0  # 終わったら 0 に戻す
    assert {c for c, _ in controls} <= {14, 123}
    curve = CalibrationCurve.model_validate_json(
        (tmp_path / "cal" / "cc" / "kva.dspctl.lp_frq__brightness_end.json").read_text()
    )
    assert curve.parameter_scale == "log" and len(curve.points) == 3
    assert "CC 14 で設定" in curve.conditions
    assert not (tmp_path / "cal" / "kva.dspctl.lp_frq__brightness_end.json").exists()


def test_calibrate_cc_mode_requires_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.infrastructure.fakes import FakePort

    port = FakePort()
    monkeypatch.setattr("mido.get_output_names", lambda: ["UR22mkII"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    config = tmp_path / "local.yaml"
    config.write_text("synth: pc3a8\nmidi:\n  output_port: UR22mkII\n")
    args = ["calibrate", "kva.dspctl.lp_frq", "--cc", "--config", str(config)]
    result = CliRunner().invoke(app, args, input="n\n")
    assert result.exit_code == 2
    assert port.messages == []  # 確かめるまで何も送らない
    # CC の設定がないパラメータは CC モードで測れない
    args = ["calibrate", "kva.ampenv.att1.time", "--cc", "--config", str(config)]
    assert CliRunner().invoke(app, args).exit_code == 2


def test_calibrate_cc_mode_refuses_cc15(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CC 15 は本体全体の音程を動かすので送らない（#40）。1027 の Rel1 は CC モードで測れない。"""
    from synth_ai import registry
    from tests.infrastructure.fakes import FakePort

    assert 15 not in registry.ALLOWED_CONTROLS["pc3a8"]
    port = FakePort()
    monkeypatch.setattr("mido.get_output_names", lambda: ["UR22mkII"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    config = tmp_path / "local.yaml"
    config.write_text("synth: pc3a8\nmidi:\n  output_port: UR22mkII\n")
    args = ["calibrate", "kva.ampenv.rel1.time", "--cc", "--config", str(config)]
    result = CliRunner().invoke(app, args, input="y\n")
    assert result.exit_code == 2 and "CC 15" in result.output
    assert port.messages == []
