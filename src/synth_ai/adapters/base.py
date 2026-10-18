"""SynthAdapter 契約と Capabilities。

Core が参照してよい adapters 配下のモジュールはこのファイルだけ。
MIDI 制御やパラメータ書き込みは必須インターフェースに含めない（DeviceController として別に扱う）。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec


class CapabilityStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNVERIFIED = "unverified"  # 未検証。使用可能として扱わない


class Capabilities(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    synth_id: str
    display_name: str
    user_sample_import: CapabilityStatus
    midi_notes: CapabilityStatus
    parameter_read: CapabilityStatus
    parameter_write: CapabilityStatus
    available_engines: tuple[str, ...]

    def is_supported(self, name: str) -> bool:
        """supported のときだけ True。unverified は使用不可として扱う。"""
        status = getattr(self, name)
        if not isinstance(status, CapabilityStatus):
            raise AttributeError(f"{name} is not a capability")
        return status is CapabilityStatus.SUPPORTED


@runtime_checkable
class SynthAdapter(Protocol):
    synth_id: str

    def capabilities(self) -> Capabilities: ...

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe: ...

    def manual_instructions(self, recipe: PatchRecipe) -> str: ...
