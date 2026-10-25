"""Intent をパラメータ表とキャリブレーション表で具体的な手順（RecipeStep）にする。

- 表にない役割は手順にしない（未登録として不確実性に記録する）
- 値はキャリブレーション曲線から逆引きする。曲線がなければ値を空にして音響目標を示す
- ×f0 で測った曲線を、測定時と違う音程の参照音に使うときは、パラメータの
  steps_per_octave（1 オクターブあたりの段数）で音程差のぶんだけ値をずらす
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from synth_ai.adapters.kronos2.intents import Intent
from synth_ai.adapters.kronos2.parameters import ParameterDef, ParameterKind, ParameterTable
from synth_ai.adapters.kronos2.roles import ROLE_LABELS
from synth_ai.core.audio.notes import hz_to_note, note_to_hz
from synth_ai.core.calibration.models import CalibrationCurve, CalibrationSet
from synth_ai.core.sound_spec.features import LABELS, Feature
from synth_ai.core.sound_spec.models import QuantTarget, RecipeStep, StepStatus


@dataclass
class RenderResult:
    steps: list[RecipeStep] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    unregistered: list[Intent] = field(default_factory=list)
    uncalibrated: int = 0


# 基音に対する比で表す特徴。音程が変わると、同じ値でも必要なパラメータ値が変わる
PITCH_RELATIVE_UNITS = {"x f0"}
MIN_SHIFT_STEPS = 0.5


@dataclass(frozen=True)
class PitchShift:
    steps: float  # 逆引きした値に足す段数
    measured_note: str  # 曲線を測った音
    target_note: str  # 参照音

    def describe(self) -> str:
        return (
            f"（参照音 {self.target_note} と測定音 {self.measured_note} の音程差で"
            f" {self.steps:+.0f} 段補正）"
        )


def pitch_shift(
    param: ParameterDef, curve: CalibrationCurve, f0_hz: float | None
) -> PitchShift | None:
    """音程の違う参照音に曲線を使うときのずれ。補正できない・不要なら None。

    カットオフのように周波数を決めるパラメータは、同じ「×f0 の明るさ」を得るのに
    音程が 1 オクターブ上がれば 1 オクターブ分（steps_per_octave 段）上げる必要がある。
    """
    if (
        param.steps_per_octave is None
        or curve.reference_note is None
        or curve.unit not in PITCH_RELATIVE_UNITS
        or not f0_hz
    ):
        return None
    try:
        measured_hz = note_to_hz(curve.reference_note)
    except ValueError:
        return None
    steps = param.steps_per_octave * math.log2(f0_hz / measured_hz)
    if abs(steps) < MIN_SHIFT_STEPS:
        return None
    return PitchShift(steps, curve.reference_note, hz_to_note(f0_hz)[0])


def _num(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.3g}"


def describe_target(target: QuantTarget) -> str:
    try:
        label = LABELS[Feature(target.feature)]
    except ValueError:
        label = target.feature
    unit = "×f0" if target.unit == "x f0" else target.unit
    return f"{label} {_num(target.value)} {unit}（±{_num(target.tolerance)}）"


def describe_intent(intent: Intent) -> str:
    what = ROLE_LABELS[intent.role]
    if intent.choice is not None:
        how = f"「{intent.choice.value}」系を選ぶ"
    elif intent.extreme is not None:
        how = {"min": "最小にする", "max": "最大にする", "zero": "0（効果なし）にする"}[
            intent.extreme
        ]
    elif intent.target is not None:
        how = f"{describe_target(intent.target)} に合わせる"
    else:
        how = "調整する"
    return f"{what}: {how} — {intent.reason}"


def render_steps(
    intents: list[Intent],
    table: ParameterTable | None,
    calibrations: CalibrationSet,
    f0_hz: float | None = None,
) -> RenderResult:
    """f0_hz は参照音の基音（音程の補正に使う）。"""
    result = RenderResult()
    for intent in intents:
        param = table.by_role(intent.role) if table else None
        if param is None:
            if not intent.optional:
                result.unregistered.append(intent)
            continue

        value: str | float | int | None = None
        reason = intent.reason
        if intent.choice is not None:
            choice = param.choice_with(intent.choice)
            if choice is None:
                result.uncertainties.append(
                    f"{param.name} の選択肢に「{intent.choice.value}」のタグが"
                    "付いていないため選べない"
                )
                continue
            value = choice.value
        elif intent.extreme is not None:
            if param.kind is ParameterKind.CHOICE:
                result.uncertainties.append(f"{param.name} は選択式のため最小・最大を指定できない")
                continue
            assert param.min is not None and param.max is not None
            bound = {"min": param.min, "max": param.max}.get(intent.extreme)
            if bound is None:  # zero
                bound = 0.0 if param.min <= 0 <= param.max else param.min
            value = param.clamp(bound)
        elif intent.target is not None and param.kind is not ParameterKind.CHOICE:
            curve = calibrations.get(param.id, intent.target.feature)
            estimate = curve.inverse(intent.target.value) if curve else None
            if curve is not None and estimate is not None:
                shift = pitch_shift(param, curve, f0_hz)
                value = param.clamp(estimate + (shift.steps if shift else 0.0))
                if not curve.covers(intent.target.value):
                    reason += "（目標が測定範囲外のため、測定した端の値）"
                else:
                    reason += "（キャリブレーション表から算出）"
                if shift:
                    reason += shift.describe()
            else:
                result.uncalibrated += 1

        if param.notes:
            reason += f"（注: {param.notes}）"
        result.steps.append(
            RecipeStep(
                order=len(result.steps) + 1,
                action=intent.action,
                page=param.page if param.tab is None else f"{param.page} › {param.tab}",
                parameter_id=param.id,
                parameter=param.name,
                value=value,
                reason=reason,
                source_ref=param.source_ref,
                status=StepStatus.VERIFIED if param.verified else StepStatus.NEEDS_CONFIRMATION,
                target=intent.target,
            )
        )

    if result.uncalibrated:
        result.uncertainties.append(
            f"{result.uncalibrated} 項目はキャリブレーション未測定のため値を決めていない。"
            "示した音響目標に合わせて、耳と analyze の結果で調整する"
        )
    return result
