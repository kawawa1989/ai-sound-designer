"""境界を越えるデータ形式: AudioAnalysis → SoundSpec → PatchRecipe。

- AudioAnalysis: 解析器が観測した値。推測は含めない。
- SoundSpec: 目標とする音響特徴と合成の仮説。機種非依存。
- PatchRecipe: 機種固有の設定手順。synth_id で機種を区別する。

すべてのモデルは不変（frozen、シーケンスは tuple）にして、Adapter に渡した
SoundSpec が書き換えられないことを型レベルで保証する。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION: Final = "1.0"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --- 共通の部品 ---------------------------------------------------------------


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Issue(FrozenModel):
    """解析条件の問題や警告（クリップ、多重音、残響など）。"""

    code: str
    message: str
    severity: Severity = Severity.WARNING


class Level(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Speed(StrEnum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


# --- AudioAnalysis -------------------------------------------------------------


class SourceInfo(FrozenModel):
    path: str
    sha256: str
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    duration_s: float = Field(ge=0)


class PitchEstimate(FrozenModel):
    f0_hz: float = Field(gt=0)
    note: str
    cents_offset: float
    confidence: float = Field(ge=0, le=1)


class EnvelopeFeatures(FrozenModel):
    attack_ms: float | None = None
    decay_ms: float | None = None
    sustain_level_db: float | None = None
    release_ms: float | None = None
    confidence: float = Field(ge=0, le=1)


class SpectralFeatures(FrozenModel):
    centroid_hz_mean: float | None = None
    centroid_hz_start: float | None = None
    centroid_hz_end: float | None = None
    flatness_mean: float | None = None
    inharmonicity: float | None = None
    confidence: float = Field(ge=0, le=1)


class AudioAnalysis(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    analysis_id: str
    source: SourceInfo
    pitch: PitchEstimate | None = None
    envelope: EnvelopeFeatures | None = None
    spectral: SpectralFeatures | None = None
    issues: tuple[Issue, ...] = ()


# --- SoundSpec（機種非依存） ----------------------------------------------------


class SynthesisMethod(StrEnum):
    SUBTRACTIVE = "subtractive"
    FM = "fm"
    ADDITIVE = "additive"
    WAVETABLE = "wavetable"
    SAMPLE_BASED = "sample_based"
    PHYSICAL_MODEL = "physical_model"


class QuantTarget(FrozenModel):
    """単位付きの定量目標。feature は機種非依存の特徴名（例: attack_time）。"""

    feature: str
    value: float
    unit: str
    tolerance: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)


class PitchTarget(FrozenModel):
    note: str
    f0_hz: float | None = None
    confidence: float = Field(ge=0, le=1)


class TimbreSpec(FrozenModel):
    harmonicity: Level | None = None
    brightness: Level | None = None
    brightness_decay: Speed | None = None
    noisiness: Level | None = None


class EnvelopeSpec(FrozenModel):
    attack: Speed | None = None
    decay: Speed | None = None
    sustain: Level | None = None
    release: Speed | None = None


class SynthesisHypothesis(FrozenModel):
    method: SynthesisMethod
    rationale: str
    confidence: float = Field(ge=0, le=1)


class SoundSpec(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    spec_id: str
    reference_id: str
    analysis_id: str | None = None
    pitch: PitchTarget | None = None
    timbre: TimbreSpec = TimbreSpec()
    envelope: EnvelopeSpec = EnvelopeSpec()
    targets: tuple[QuantTarget, ...] = ()
    hypotheses: tuple[SynthesisHypothesis, ...] = ()
    uncertainties: tuple[str, ...] = ()


# --- PatchRecipe（機種固有） ----------------------------------------------------


class StepAction(StrEnum):
    SET = "set"
    INCREASE = "increase"
    DECREASE = "decrease"
    SELECT = "select"
    IMPORT_SAMPLE = "import_sample"
    VERIFY = "verify"


class StepStatus(StrEnum):
    VERIFIED = "verified"  # 公式資料と照合済み
    NEEDS_CONFIRMATION = "needs_confirmation"  # 資料・実機で要確認


class RecipeStep(FrozenModel):
    order: int = Field(ge=1)
    action: StepAction
    page: str
    parameter_id: str
    parameter: str
    value: str | float | int | None = None
    reason: str
    source_ref: str | None = None  # 公式資料の該当箇所（例: "Parameter Guide p.123"）
    status: StepStatus = StepStatus.NEEDS_CONFIRMATION


class AlternativeApproach(FrozenModel):
    engine: str
    summary: str


class PatchRecipe(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    recipe_id: str
    sound_spec_id: str
    synth_id: str
    engine: str | None = None
    rationale: str
    steps: tuple[RecipeStep, ...] = ()
    alternatives: tuple[AlternativeApproach, ...] = ()
    uncertainties: tuple[str, ...] = ()
