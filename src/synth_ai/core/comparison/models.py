"""参照音と録音（シンセで作った音）の比較結果。機種非依存。"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from synth_ai.core.sound_spec.models import FrozenModel, Issue, StepAction


class DifferenceKind(StrEnum):
    FEATURE = "feature"  # SoundSpec の定量特徴（アタック時間、明るさなど）
    BAND = "band"  # 区間 × 周波数帯のエネルギー（区間全体の音量差を除いた音色の差）
    ENVELOPE = "envelope"  # 区間ごとの音量差
    HARMONIC = "harmonic"  # 倍音ごとのレベル差


class Segment(StrEnum):
    ATTACK = "attack"
    BODY = "body"
    TAIL = "tail"


SEGMENT_LABELS = {Segment.ATTACK: "アタック", Segment.BODY: "持続部", Segment.TAIL: "減衰・余韻"}


class Alignment(FrozenModel):
    """録音を参照音に合わせた方法。gain_db は録音に掛けた補正量。"""

    offset_s: float  # 録音の発音開始を参照に合わせるために動かした量（正: 録音を前に詰めた）
    gain_db: float
    pitch_offset_cents: float | None  # 録音の音程 - 参照の音程
    compared_duration_s: float
    reference_duration_s: float
    recording_duration_s: float


class Difference(FrozenModel):
    kind: DifferenceKind
    feature: str | None = None
    segment: Segment | None = None
    band: str | None = None  # 例: "1k-4k"
    harmonic: int | None = None
    reference: float
    recording: float
    delta: float  # recording - reference
    unit: str
    severity: float = Field(ge=0)  # 許容幅に対する差の大きさ（1 以上を有意とみなす）
    message: str


class SpectralDistance(FrozenModel):
    """マルチ解像度 STFT の対数振幅の平均差（dB）。参考値で、成功判定には使わない。"""

    per_resolution_db: dict[int, float]
    mean_db: float


class AdjustmentSuggestion(FrozenModel):
    priority: int = Field(ge=1)
    message: str
    feature: str | None = None  # 改善したい音響特徴
    parameter_id: str | None = None  # Adapter が具体化できた場合のみ
    parameter: str | None = None
    page: str | None = None
    action: StepAction | None = None
    value: str | float | int | None = None
    reason: str = ""


class FeatureProgress(FrozenModel):
    feature: str
    previous_severity: float
    current_severity: float

    @property
    def improved(self) -> bool:
        return self.current_severity < self.previous_severity


class Comparison(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    comparison_id: str
    reference_analysis_id: str
    recording_analysis_id: str
    synth_id: str | None = None
    recipe_id: str | None = None
    alignment: Alignment
    differences: tuple[Difference, ...]  # severity の大きい順
    distance: SpectralDistance
    suggestions: tuple[AdjustmentSuggestion, ...] = ()
    progress: tuple[FeatureProgress, ...] = ()  # 前回の試行からの変化
    issues: tuple[Issue, ...] = ()  # 比較条件の問題（音程違い、録音の品質など）

    @property
    def significant(self) -> tuple[Difference, ...]:
        return tuple(d for d in self.differences if d.severity >= 1.0)
