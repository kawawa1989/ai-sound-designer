"""比較の差分から、AL-1 のどのパラメータをどちらに動かすかを提案する。

特徴とパラメータの向きは一般的な減算合成の傾向（例: アタックの値を上げると
立ち上がりが遅くなる）。キャリブレーション曲線があれば、向きと量はそちらを優先する。
"""

from __future__ import annotations

from synth_ai.adapters.kronos2.al1 import choose_waveform
from synth_ai.adapters.kronos2.parameters import ParameterKind, ParameterTable
from synth_ai.adapters.kronos2.roles import ROLE_LABELS, Role
from synth_ai.core.calibration.models import CalibrationSet
from synth_ai.core.comparison.models import AdjustmentSuggestion, Difference
from synth_ai.core.comparison.suggest import MAX_SUGGESTIONS, significant_features
from synth_ai.core.comparison.wording import as_feature, fix_word
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec, StepAction

# 特徴 → (役割, 向き)。向き +1 はパラメータを上げると特徴の値が大きくなる
ROLE_FOR_FEATURE: dict[Feature, tuple[Role, int]] = {
    Feature.ATTACK_TIME: (Role.AMP_EG_ATTACK, +1),
    Feature.DECAY_TIME: (Role.AMP_EG_DECAY, +1),
    Feature.DECAY_RATE: (Role.AMP_EG_DECAY, +1),  # ディケイが長いほど傾きは緩やか（値は大きい）
    Feature.SUSTAIN_LEVEL: (Role.AMP_EG_SUSTAIN, +1),
    Feature.RELEASE_TIME: (Role.AMP_EG_RELEASE, +1),
    Feature.BRIGHTNESS: (Role.FILTER_CUTOFF, +1),
    Feature.BRIGHTNESS_END: (Role.FILTER_CUTOFF, +1),
    Feature.HARMONIC_SLOPE: (Role.FILTER_CUTOFF, +1),
    Feature.BRIGHTNESS_START: (Role.FILTER_EG_INTENSITY, +1),
    Feature.BRIGHTNESS_CHANGE: (
        Role.FILTER_EG_INTENSITY,
        -1,
    ),  # 効きを強めるほど終盤/直後の比は小さい
    Feature.BRIGHTNESS_DECAY_TIME: (Role.FILTER_EG_DECAY, +1),
    Feature.NOISINESS: (Role.NOISE_LEVEL, +1),
}


def _current_value(recipe: PatchRecipe | None, parameter_id: str) -> float | None:
    if recipe is None:
        return None
    step = next((s for s in recipe.steps if s.parameter_id == parameter_id), None)
    return float(step.value) if step and isinstance(step.value, int | float) else None


def suggest_adjustments(
    spec: SoundSpec,
    differences: tuple[Difference, ...],
    recipe: PatchRecipe | None,
    table: ParameterTable | None,
    calibrations: CalibrationSet,
) -> tuple[AdjustmentSuggestion, ...]:
    out: list[AdjustmentSuggestion] = []
    used: set[Role] = set()
    for d in significant_features(differences):
        if len(out) >= MAX_SUGGESTIONS:
            break
        feature = as_feature(d.feature)
        assert feature is not None
        if feature is Feature.ODD_EVEN_RATIO and Role.OSCILLATOR_WAVEFORM not in used:
            used.add(Role.OSCILLATOR_WAVEFORM)
            out.append(_waveform_suggestion(spec, d, table))
            continue
        if feature not in ROLE_FOR_FEATURE:
            continue
        role, sign = ROLE_FOR_FEATURE[feature]
        if role in used:
            continue
        used.add(role)
        out.append(_numeric_suggestion(feature, role, sign, d, recipe, table, calibrations))
    return tuple(out)


def _numeric_suggestion(
    feature: Feature,
    role: Role,
    sign: int,
    d: Difference,
    recipe: PatchRecipe | None,
    table: ParameterTable | None,
    calibrations: CalibrationSet,
) -> AdjustmentSuggestion:
    param = table.by_role(role) if table else None
    curve = calibrations.get(param.id, feature.value) if param else None
    calibrated = False
    if curve is not None and curve.is_monotonic and param and param.min is not None:
        assert param.max is not None
        sign = 1 if curve.predict(param.max) > curve.predict(param.min) else -1
        calibrated = True
    need_increase = d.delta < 0  # 録音の値が小さい → 特徴を大きくしたい
    action = StepAction.INCREASE if need_increase == (sign > 0) else StepAction.DECREASE
    verb = "上げる" if action is StepAction.INCREASE else "下げる"

    value: float | int | None = None
    if curve is not None and param is not None and param.kind is not ParameterKind.CHOICE:
        target, measured = curve.inverse(d.reference), curve.inverse(d.recording)
        current = _current_value(recipe, param.id)
        if target is not None and measured is not None and current is not None:
            # 曲線と実際の録音のずれを補うため、現在値から差分だけ動かす
            value = param.clamp(current + target - measured)
        elif target is not None:
            value = param.clamp(target)

    name = f"{param.name}（{param.page}）" if param else ROLE_LABELS[role]
    message = f"{name}を{verb}" + (f": {value} にする" if value is not None else "")
    basis = (
        "キャリブレーション表から算出"
        if calibrated
        else "パラメータと音の関係は一般的な傾向。少しずつ動かして確認する"
    )
    return AdjustmentSuggestion(
        priority=1,
        message=f"{message} — {fix_word(feature, d.delta)}",
        feature=feature.value,
        parameter_id=param.id if param else None,
        parameter=param.name if param else None,
        page=param.page if param else None,
        action=action,
        value=value,
        reason=f"{d.message}。{basis}",
    )


def _waveform_suggestion(
    spec: SoundSpec, d: Difference, table: ParameterTable | None
) -> AdjustmentSuggestion:
    tag, why = choose_waveform(spec)
    param = table.by_role(Role.OSCILLATOR_WAVEFORM) if table else None
    choice = param.choice_with(tag) if param else None
    target = choice.value if choice else f"「{tag.value}」系"
    name = param.name if param else ROLE_LABELS[Role.OSCILLATOR_WAVEFORM]
    return AdjustmentSuggestion(
        priority=1,
        message=f"{name}を {target} にする — {fix_word(Feature.ODD_EVEN_RATIO, d.delta)}",
        feature=Feature.ODD_EVEN_RATIO.value,
        parameter_id=param.id if param else None,
        parameter=param.name if param else None,
        page=param.page if param else None,
        action=StepAction.SELECT,
        value=choice.value if choice else None,
        reason=f"{d.message}。参照音は{why}",
    )
