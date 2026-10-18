"""ローカル設定（config/local.yaml）。MIDI の送信先と録音入力を固定する。"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_PATH = Path("config/local.yaml")


class _Section(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MidiConfig(_Section):
    output_port: str | None = None
    channel: int = Field(default=1, ge=1, le=16)


class CaptureConfig(_Section):
    input_device: str | None = None
    sample_rate: int = Field(default=48_000, gt=0)
    channels: int = Field(default=2, ge=1, le=8)
    pre_roll_s: float = Field(default=0.3, ge=0, le=5)
    fade_ms: float = Field(default=5.0, ge=0, le=100)
    peak_warn_dbfs: float = Field(default=-1.0, le=0)
    quiet_warn_dbfs: float = Field(default=-40.0, le=0)


class NoteConfig(_Section):
    note: str = "C4"
    velocity: int = Field(default=100, ge=1, le=127)
    hold_s: float = Field(default=1.5, gt=0, le=30)
    release_tail_s: float = Field(default=2.0, ge=0, le=30)


class LocalConfig(_Section):
    synth: str = "kronos2"
    midi: MidiConfig = MidiConfig()
    capture: CaptureConfig = CaptureConfig()
    test_note: NoteConfig = NoteConfig()


class ConfigError(Exception):
    pass


def load_config(path: Path | None = None) -> LocalConfig:
    """設定を読む。ファイルがなければ既定値（MIDI なし・既定の入力）。"""
    path = path or DEFAULT_PATH
    if not path.is_file():
        return LocalConfig()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return LocalConfig.model_validate(data)
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"{path} の内容が正しくありません:\n{exc}") from exc
