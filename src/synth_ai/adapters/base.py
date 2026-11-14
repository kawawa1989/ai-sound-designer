"""SynthAdapter 契約と Capabilities。

Core が参照してよい adapters 配下のモジュールはこのファイルだけ。
MIDI 制御やパラメータ書き込みは必須インターフェースに含めない（DeviceController として別に扱う）。
"""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class CcControl(BaseModel):
    """キャリブレーション用の Program で、このパラメータを CC で動かす設定。

    x = CC / divisor として、
    - depth_cents のとき: 値 = base × 2^(depth_cents × x / 1200)（周波数など、セントで上がる値）
    - rate_depth のとき: 値 = base ÷ rate_depth^x（時間など、速さの倍率で縮む値）
    途中の CC で比例して動くと仮定している（測った曲線と手動の曲線を比べて確かめる）。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    control: int = Field(ge=1, le=119)  # CC 番号
    base: float = Field(gt=0)  # CC 0 のときの値（パラメータの単位）
    depth_cents: float | None = Field(default=None, gt=0)
    rate_depth: float | None = Field(default=None, gt=1)  # CC が最大のときの速さの倍率
    divisor: Literal[127, 128] = 127  # CC を何で割って 0〜1 にするか
    program: str  # 人が本体で選んでおく Program（例: "1026 KVA CC CAL"）

    @model_validator(mode="after")
    def _one_depth(self) -> CcControl:
        if (self.depth_cents is None) == (self.rate_depth is None):
            raise ValueError("set exactly one of depth_cents or rate_depth")
        return self

    def _octaves(self, x: float) -> float:
        """値が CC 0 から何オクターブ動くか（rate_depth のときは下がる）。"""
        if self.depth_cents is not None:
            return self.depth_cents * x / 1200
        assert self.rate_depth is not None
        return -math.log2(self.rate_depth) * x

    def value_at(self, cc: int) -> float:
        return float(self.base * 2.0 ** self._octaves(cc / self.divisor))

    def cc_for(self, value: float) -> int:
        """この値にいちばん近い CC。"""
        full = self._octaves(1.0)
        cc = round(self.divisor * math.log2(value / self.base) / full)
        return min(max(cc, 0), 127)

    def describe(self) -> str:
        """測定条件に残す換算の説明。"""
        if self.depth_cents is not None:
            formula = f"{self.base:g} × 2^({self.depth_cents:g} ct × CC/{self.divisor})"
        else:
            formula = f"{self.base:g} ÷ {self.rate_depth:g}^(CC/{self.divisor})"
        return f"値 = {formula}、比例を仮定"


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
    unit: str | None = None  # 値の単位（例: "s"、"Hz"）
    calibration_values: tuple[float, ...] = ()  # 測る値（本体で選べる値）。空なら範囲から決める
    log_scale: bool = False  # 比で効く値（周波数など）。曲線を対数で補間する
    cc_control: CcControl | None = None  # CC で動かして測れるとき


@runtime_checkable
class ParameterCatalog(Protocol):
    """任意の契約。機種のパラメータ表を引ける Adapter が実装する。"""

    def parameter_info(self, parameter_id: str) -> ParameterInfo | None: ...

    def calibratable_parameters(self) -> tuple[ParameterInfo, ...]: ...
