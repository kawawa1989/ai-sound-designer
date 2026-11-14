from pathlib import Path

import pytest

from synth_ai.config import ConfigError, LocalConfig, load_config

ROOT = Path(__file__).resolve().parents[1]


def test_missing_file_gives_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "none.yaml")
    assert cfg == LocalConfig()
    assert cfg.midi.output_port is None


def test_example_is_valid() -> None:
    cfg = load_config(ROOT / "config" / "local.example.yaml")
    assert cfg.capture.sample_rate == 48_000
    assert cfg.test_note.note == "C4"


@pytest.mark.parametrize(
    "text", ["midi:\n  channel: 17\n", "capture:\n  unknown: 1\n", "midi: [unclosed\n"]
)
def test_invalid(tmp_path: Path, text: str) -> None:
    path = tmp_path / "local.yaml"
    path.write_text(text)
    with pytest.raises(ConfigError):
        load_config(path)


MULTI = """\
synth: kronos2
midi:
  output_port: UR22mkII
  channel: 1
capture:
  input_device: UR22mkII
test_note:
  note: C4
synths:
  pc3a8:
    midi:
      output_port: PC3A
      channel: 2
"""


def test_legacy_single_synth(tmp_path: Path) -> None:
    path = tmp_path / "local.yaml"
    path.write_text("midi:\n  output_port: KRONOS\n")
    cfg = load_config(path).for_synth()
    assert cfg.synth == "kronos2"
    assert cfg.midi.output_port == "KRONOS"
    assert load_config(path).for_synth("kronos2") == cfg


def test_multi_synth_profiles(tmp_path: Path) -> None:
    path = tmp_path / "local.yaml"
    path.write_text(MULTI)
    local = load_config(path)
    assert local.known_synths() == ["kronos2", "pc3a8"]
    kronos = local.for_synth()
    assert (kronos.synth, kronos.midi.output_port) == ("kronos2", "UR22mkII")
    assert kronos.midi.channel == 1
    pc3 = local.for_synth("pc3a8")
    assert (pc3.synth, pc3.midi.output_port, pc3.midi.channel) == ("pc3a8", "PC3A", 2)
    # 書かなかった項目は先頭の項目を使う
    assert pc3.capture.input_device == "UR22mkII"
    assert pc3.test_note == kronos.test_note


def test_profile_overrides_default_synth(tmp_path: Path) -> None:
    path = tmp_path / "local.yaml"
    path.write_text(MULTI + "  kronos2:\n    midi:\n      output_port: KRONOS\n")
    assert load_config(path).for_synth().midi.output_port == "KRONOS"


def test_unknown_synth(tmp_path: Path) -> None:
    path = tmp_path / "local.yaml"
    path.write_text(MULTI)
    with pytest.raises(ConfigError, match="nope.*kronos2, pc3a8"):
        load_config(path).for_synth("nope")
    # synths が無い従来形式でも、既定以外の機種はエラー
    with pytest.raises(ConfigError, match="pc3a8"):
        LocalConfig().for_synth("pc3a8")


def test_invalid_profile(tmp_path: Path) -> None:
    path = tmp_path / "local.yaml"
    path.write_text("synths:\n  pc3a8:\n    midi:\n      channel: 0\n")
    with pytest.raises(ConfigError):
        load_config(path)
    path.write_text("synths:\n  pc3a8:\n    unknown: 1\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_example_has_pc3a8() -> None:
    local = load_config(ROOT / "config" / "local.example.yaml")
    assert local.for_synth("pc3a8").synth == "pc3a8"
