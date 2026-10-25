"""キャリブレーションの 1 セッション: 値を変える → 録音 → 解析 → 特徴を読む、を値ごとに繰り返す。

実機の操作（値を変える）と録音は呼び出し側から関数で渡す。Core は機種も録音手段も知らない。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path

from synth_ai.core.calibration.models import CalibrationCurve, CalibrationPoint
from synth_ai.core.sound_spec.derive import quantitative_targets
from synth_ai.core.sound_spec.features import UNITS, Feature
from synth_ai.core.sound_spec.models import AudioAnalysis, Issue

# 特徴の測定に影響する解析上の問題
RELEVANT_ISSUES = {"clipping", "truncated_tail", "pitch_unreliable", "low_snr"}


class Step(StrEnum):
    GO = "go"  # 値を設定した。録音する
    SKIP = "skip"  # この値は測らない
    QUIT = "quit"  # ここまでで終える


class Verdict(StrEnum):
    ACCEPT = "accept"
    RETRY = "retry"
    SKIP = "skip"


@dataclass(frozen=True)
class CalibrationPlan:
    synth_id: str
    parameter_id: str
    parameter_label: str  # 表示用（例: "P6: Amp › 6–3: Amp EG › Amp EG Time Attack"）
    feature: Feature
    values: tuple[float, ...]
    conditions: str


@dataclass(frozen=True)
class Measurement:
    parameter_value: float
    feature_value: float | None
    recording: Path
    issues: tuple[Issue, ...]


@dataclass
class SessionResult:
    plan: CalibrationPlan
    points: list[Measurement] = field(default_factory=list)
    skipped: list[float] = field(default_factory=list)
    quit_early: bool = False

    @property
    def usable(self) -> list[Measurement]:
        return [m for m in self.points if m.feature_value is not None]


def measure_feature(analysis: AudioAnalysis, feature: Feature) -> float | None:
    targets = {t.feature: t.value for t in quantitative_targets(analysis)}
    return targets.get(feature.value)


def relevant_issues(analysis: AudioAnalysis) -> tuple[Issue, ...]:
    return tuple(i for i in analysis.issues if i.code in RELEVANT_ISSUES)


def run_session(
    plan: CalibrationPlan,
    ask_to_set: Callable[[int, float], Step],
    record: Callable[[float, int], Path],
    analyze: Callable[[Path], AudioAnalysis],
    confirm: Callable[[Measurement], Verdict],
) -> SessionResult:
    """値ごとに「設定してもらう → 録音 → 解析 → 確認」を繰り返す。

    record(value, attempt) は録音した WAV のパスを返す。confirm で RETRY なら同じ値を録り直す。
    """
    result = SessionResult(plan)
    for index, value in enumerate(plan.values):
        step = ask_to_set(index, value)
        if step is Step.QUIT:
            result.quit_early = True
            break
        if step is Step.SKIP:
            result.skipped.append(value)
            continue
        attempt = 1
        while True:
            path = record(value, attempt)
            analysis = analyze(path)
            measurement = Measurement(
                parameter_value=value,
                feature_value=measure_feature(analysis, plan.feature),
                recording=path,
                issues=relevant_issues(analysis),
            )
            verdict = confirm(measurement)
            if verdict is Verdict.RETRY:
                attempt += 1
                continue
            if verdict is Verdict.ACCEPT and measurement.feature_value is not None:
                result.points.append(measurement)
            else:
                result.skipped.append(value)
            break
    return result


class NotEnoughPointsError(ValueError):
    pass


def build_curve(result: SessionResult, measured_at: date | None = None) -> CalibrationCurve:
    usable = result.usable
    if len(usable) < 2:
        raise NotEnoughPointsError(
            f"測定できた点が {len(usable)} 個です。曲線には 2 個以上必要です"
        )
    plan = result.plan
    return CalibrationCurve(
        synth_id=plan.synth_id,
        parameter_id=plan.parameter_id,
        feature=plan.feature.value,
        unit=UNITS[plan.feature],
        conditions=plan.conditions,
        measured_at=(measured_at or date.today()).isoformat(),
        points=tuple(
            CalibrationPoint(parameter_value=m.parameter_value, feature_value=m.feature_value)
            for m in sorted(usable, key=lambda m: m.parameter_value)
            if m.feature_value is not None
        ),
    )


def curve_filename(parameter_id: str, feature: Feature) -> str:
    return f"{parameter_id}__{feature.value}.json"


# 特徴を正しく測るための、押さえる時間・余韻の最低限（秒）
MIN_HOLD_S: dict[Feature, float] = {
    Feature.ATTACK_TIME: 3.0,
    Feature.DECAY_TIME: 3.0,
    Feature.SUSTAIN_LEVEL: 2.0,
    Feature.BRIGHTNESS_DECAY_TIME: 3.0,
    Feature.BRIGHTNESS_CHANGE: 2.0,
}
MIN_TAIL_S: dict[Feature, float] = {
    Feature.RELEASE_TIME: 4.0,
}
