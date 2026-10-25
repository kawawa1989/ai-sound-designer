"""Intent をパラメータ表とキャリブレーション表で具体的な手順（RecipeStep）にする。

- 表にない役割は手順にしない（未登録として不確実性に記録する）
- 値はキャリブレーション曲線から逆引きする。曲線がなければ値を空にして音響目標を示す
"""

from __future__ import annotations

from dataclasses import dataclass, field

from synth_ai.adapters.kronos2.intents import Intent
from synth_ai.adapters.kronos2.parameters import ParameterKind, ParameterTable
from synth_ai.adapters.kronos2.roles import ROLE_LABELS
from synth_ai.core.calibration.models import CalibrationSet
from synth_ai.core.sound_spec.features import LABELS, Feature
from synth_ai.core.sound_spec.models import QuantTarget, RecipeStep, StepStatus


@dataclass
class RenderResult:
    steps: list[RecipeStep] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    unregistered: list[Intent] = field(default_factory=list)
    uncalibrated: int = 0


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
    intents: list[Intent], table: ParameterTable | None, calibrations: CalibrationSet
) -> RenderResult:
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
                value = param.clamp(estimate)
                if not curve.covers(intent.target.value):
                    reason += "（目標が測定範囲外のため、測定した端の値）"
                else:
                    reason += "（キャリブレーション表から算出）"
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
