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
# 時間はすべて解析対象（トリム後）の先頭からの秒。レベルの dB は特記なければピーク基準。


class SourceInfo(FrozenModel):
    path: str
    sha256: str
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    duration_s: float = Field(ge=0)
    trim_start_s: float = Field(ge=0, default=0.0)  # 元ファイル上で解析対象が始まる位置
    analyzed_duration_s: float = Field(ge=0, default=0.0)


class AnalysisSettings(FrozenModel):
    """再現性のための解析条件。"""

    analyzer_version: str
    sample_rate: int
    hop_s: float
    n_fft: int


class LevelInfo(FrozenModel):
    peak_dbfs: float
    rms_dbfs: float
    noise_floor_db: float  # ピーク基準
    snr_db: float
    snr_is_lower_bound: bool  # 末尾まで減衰しきっていて背景ノイズを直接測れない場合 True
    clip_ratio: float = Field(ge=0, le=1)
    dc_offset: float


class PitchEstimate(FrozenModel):
    f0_hz: float = Field(gt=0)
    note: str
    cents_offset: float
    stability_cents: float = Field(ge=0)  # 有声区間の f0 の標準偏差
    voiced_ratio: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class EnvelopeFeatures(FrozenModel):
    """RMS 包絡から求めた発音の時間構造。

    attack_ms: ピーク振幅の 10%→90% の立ち上がり時間
    decay_ms: ピークからサステイン到達まで（サステインなしなら -20 dB 到達まで）
    sustain_level_db: サステイン区間の中央値（ピーク基準、サステインなしなら None）
    release_ms: サステイン終了から 20 dB 減衰するまで（未到達なら None）
    decay_rate_db_per_s: ピーク後の減衰の傾き（負の値ほど速く減衰）
    """

    onset_s: float
    peak_s: float
    attack_ms: float | None = None
    decay_ms: float | None = None
    sustained: bool
    sustain_level_db: float | None = None
    sustain_start_s: float | None = None
    release_start_s: float | None = None
    release_ms: float | None = None
    decay_rate_db_per_s: float | None = None
    confidence: float = Field(ge=0, le=1)


class SpectralFeatures(FrozenModel):
    """発音区間のスペクトル特徴。start は発音直後 100 ms、end は発音区間の最後の 25%。"""

    centroid_hz_mean: float
    centroid_hz_start: float
    centroid_hz_end: float
    centroid_ratio_to_f0: float | None = None  # ピッチによらない明るさの目安
    brightness_change_ratio: float  # end / start（1 未満なら時間とともに暗くなる）
    rolloff_hz_mean: float
    flatness_mean: float  # 0（純音的）〜 1（ノイズ的）
    confidence: float = Field(ge=0, le=1)


class Partial(FrozenModel):
    number: int = Field(ge=1)
    freq_hz: float
    level_db: float  # 最大の倍音を 0 dB とする
    deviation_cents: float  # number × f0 からのずれ


class HarmonicFeatures(FrozenModel):
    window_start_s: float
    window_end_s: float
    partials: tuple[Partial, ...]
    harmonic_energy_ratio: float = Field(ge=0, le=1)  # 倍音位置に集まるエネルギーの割合
    inharmonicity_cents: float = Field(ge=0)  # 倍音のずれのエネルギー加重平均
    odd_even_ratio_db: float | None = None  # 奇数次と偶数次（基音除く）のエネルギー比
    confidence: float = Field(ge=0, le=1)


class TimeSeries(FrozenModel):
    """フレームごとの値。None は音量が小さく信頼できないフレーム。"""

    hop_s: float
    rms_db: tuple[float | None, ...]
    centroid_hz: tuple[float | None, ...]
    flatness: tuple[float | None, ...]
    harmonic_levels_db: tuple[tuple[float | None, ...], ...] = ()  # [倍音番号-1][フレーム]


class AudioAnalysis(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    analysis_id: str
    source: SourceInfo
    settings: AnalysisSettings
    levels: LevelInfo
    pitch: PitchEstimate | None = None
    envelope: EnvelopeFeatures | None = None
    spectral: SpectralFeatures | None = None
    harmonics: HarmonicFeatures | None = None
    timeseries: TimeSeries | None = None
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
