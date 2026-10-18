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
