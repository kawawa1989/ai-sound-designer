"""SynthAdapter 契約と Capabilities。

Core が参照してよい adapters 配下のモジュールはこのファイルだけ。
MIDI 制御やパラメータ書き込みは必須インターフェースに含めない（DeviceController として別に扱う）。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from synth_ai.core.comparison.models import AdjustmentSuggestion, Difference
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
    adjustment_suggestions: CapabilityStatus  # 比較結果から具体的なパラメータ調整を提案できる
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


@runtime_checkable
class AdjustmentAdvisor(Protocol):
    """任意の契約。capabilities().adjustment_suggestions が supported の Adapter だけが使われる。"""

    def suggest_adjustments(
        self,
        spec: SoundSpec,
        differences: tuple[Difference, ...],
        recipe: PatchRecipe | None,
    ) -> tuple[AdjustmentSuggestion, ...]: ...


class ParameterInfo(BaseModel):
    """キャリブレーションなどで使う、機種のパラメータ 1 つの説明。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter_id: str
    label: str  # 本体で探すための表示（ページ › タブ › 名前）
    min: float | None = None
    max: float | None = None
    is_numeric: bool
    calibration_feature: str | None = None  # 測るとよい音響特徴（Feature の値）
    source_ref: str | None = None


@runtime_checkable
class ParameterCatalog(Protocol):
    """任意の契約。機種のパラメータ表を引ける Adapter が実装する。"""

    def parameter_info(self, parameter_id: str) -> ParameterInfo | None: ...

    def calibratable_parameters(self) -> tuple[ParameterInfo, ...]: ...
