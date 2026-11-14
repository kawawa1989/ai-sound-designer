"""ローカル設定（config/local.yaml）。MIDI の送信先と録音入力を機種ごとに固定する。

書き方は 2 通り。

- 1 台だけ: 先頭の `synth` と、`midi` / `capture` / `test_note` をそのまま書く（従来の形式）
- 複数台: `synths:` の下に機種 ID ごとの `midi` / `capture` / `test_note` を書く。
  書かなかった項目は先頭の同名の項目（なければ既定値）を使う。
  先頭の `synth` は既定の機種で、`synths` にその機種がなければ先頭の項目がその機種の設定になる
"""

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


class SynthProfile(_Section):
    """1 台分の接続設定。書かなかった項目は LocalConfig の先頭の項目を使う。"""

    midi: MidiConfig | None = None
    capture: CaptureConfig | None = None
    test_note: NoteConfig | None = None


class SynthConfig(_Section):
    """機種を決めたあとの設定。コマンドはこれだけを見る。"""

    synth: str
    midi: MidiConfig
    capture: CaptureConfig
    test_note: NoteConfig


class ConfigError(Exception):
    pass


class LocalConfig(_Section):
    synth: str = "kronos2"  # 既定の機種
    midi: MidiConfig = MidiConfig()
    capture: CaptureConfig = CaptureConfig()
    test_note: NoteConfig = NoteConfig()
    synths: dict[str, SynthProfile] = Field(default_factory=dict)

    def known_synths(self) -> list[str]:
        return sorted({self.synth, *self.synths})

    def for_synth(self, synth_id: str | None = None) -> SynthConfig:
        """機種の設定を返す。synth_id を省略すると既定の機種。"""
        synth = synth_id or self.synth
        profile = self.synths.get(synth)
        if profile is None:
            if synth != self.synth:
                known = ", ".join(self.known_synths())
                raise ConfigError(
                    f"「{synth}」の接続設定がありません（設定済み: {known}）。"
                    f"config/local.yaml の synths: に {synth} を追加してください"
                )
            profile = SynthProfile()
        return SynthConfig(
            synth=synth,
            midi=profile.midi or self.midi,
            capture=profile.capture or self.capture,
            test_note=profile.test_note or self.test_note,
        )


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
