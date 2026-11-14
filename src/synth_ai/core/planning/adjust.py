"""比較の差分から、減算合成のどのパラメータをどちらに動かすかを提案する。

特徴とパラメータの向きは一般的な減算合成の傾向（例: アタックの値を上げると
立ち上がりが遅くなる）。キャリブレーション曲線があれば、向きと量はそちらを優先する。

特徴どうしが重なって効く場面（#44）は、特徴ごとの提案の前に見る:
- フィルターの EG が効いていない（録音の明るさが時間で変わらない）なら、カットオフや
  EG の量を動かす提案は出さず、EG の設定を確かめる提案を出す
- 録音でフィルターが閉じていくなら、音量も一緒に下がる。アンプのディケイが長い・
  サステインが小さい差の一部はフィルターによるので、アンプの提案は値を出さず後ろに回す
"""

from __future__ import annotations

from synth_ai.core.calibration.models import CalibrationSet
from synth_ai.core.comparison.models import AdjustmentSuggestion, Difference
from synth_ai.core.comparison.suggest import MAX_SUGGESTIONS, significant_features
from synth_ai.core.comparison.wording import as_feature, fix_word, fmt
from synth_ai.core.planning.protocols import P, RecipeTable
from synth_ai.core.planning.render import pitch_shift
from synth_ai.core.planning.roles import ROLE_LABELS, Role
from synth_ai.core.planning.subtractive import choose_waveform
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

# 明るさの変化（終盤 ÷ 発音直後）がこれ以上なら、明るさは時間で変わっていない
EG_STATIC_CHANGE = 0.95
# 明るさの変化がこれ以下なら、明るさは時間で下がっている（フィルターが閉じていく）
EG_MOVING_CHANGE = 0.7
# EG が効いていないとき、出さない提案（明るさの特徴。原因は EG の設定）
BRIGHTNESS_FEATURES = frozenset(
    {
        Feature.BRIGHTNESS,
        Feature.BRIGHTNESS_END,
        Feature.HARMONIC_SLOPE,
        Feature.BRIGHTNESS_START,
        Feature.BRIGHTNESS_CHANGE,
        Feature.BRIGHTNESS_DECAY_TIME,
    }
)
# 確かめる EG の設定（この順に手順に書く）
EG_CHECK_ROLES = (Role.FILTER_EG_SUSTAIN, Role.FILTER_EG_SOURCE, Role.FILTER_EG_INTENSITY)
# フィルターが閉じると、録音でこちら向きにずれて見えるアンプの特徴（delta の符号）
FILTER_MASKED_AMP: dict[Feature, int] = {
    Feature.DECAY_TIME: +1,  # ディケイが長く見える
    Feature.DECAY_RATE: +1,  # 減衰の傾きが緩やかに見える
    Feature.SUSTAIN_LEVEL: -1,  # サステインが小さく見える
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
    table: RecipeTable[P] | None,
    calibrations: CalibrationSet,
) -> tuple[AdjustmentSuggestion, ...]:
    out: list[AdjustmentSuggestion] = []
    later: list[AdjustmentSuggestion] = []  # 先に出す提案が足りなければ使う
    used: set[Role] = set()
    change = _feature_difference(differences, Feature.BRIGHTNESS_CHANGE)
    eg_static = (
        change is not None
        and change.severity >= 1.0
        and change.recording >= EG_STATIC_CHANGE
        and change.reference <= EG_MOVING_CHANGE
    )
    if eg_static:
        assert change is not None
        out.append(_eg_check_suggestion(change, recipe, table))
    filter_closing = change is not None and change.recording <= EG_MOVING_CHANGE
    for d in significant_features(differences):
        if len(out) >= MAX_SUGGESTIONS:
            break
        feature = as_feature(d.feature)
        assert feature is not None
        if eg_static and feature in BRIGHTNESS_FEATURES:
            continue
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
        f0 = spec.pitch.f0_hz if spec.pitch else None
        direction = FILTER_MASKED_AMP.get(feature)
        if filter_closing and direction is not None and d.delta * direction > 0:
            later.append(
                _numeric_suggestion(
                    feature, role, sign, d, recipe, table, calibrations, f0, masked=True
                )
            )
            continue
        out.append(_numeric_suggestion(feature, role, sign, d, recipe, table, calibrations, f0))
    return tuple((out + later)[:MAX_SUGGESTIONS])


def _feature_difference(differences: tuple[Difference, ...], feature: Feature) -> Difference | None:
    return next((d for d in differences if as_feature(d.feature) is feature), None)


def _eg_check_suggestion(
    change: Difference, recipe: PatchRecipe | None, table: RecipeTable[P] | None
) -> AdjustmentSuggestion:
    """明るさが時間で変わらないとき、フィルター EG の設定を確かめる提案。"""
    checks = []
    first = None
    for role in EG_CHECK_ROLES:
        param = table.by_role(role) if table else None
        if param is None:
            checks.append(ROLE_LABELS[role])
            continue
        first = first or param
        value = _recipe_value(recipe, param.id)
        checks.append(f"{param.location} › {param.name}" + (f" が {value}" if value else ""))
    return AdjustmentSuggestion(
        priority=1,
        message="フィルター EG が効いているか確かめる: "
        + "、".join(checks)
        + " — 明るさを時間で変える",
        feature=Feature.BRIGHTNESS_CHANGE.value,
        parameter_id=first.id if first else None,
        parameter=first.name if first else None,
        page=first.page if first else None,
        action=StepAction.VERIFY,
        reason=f"{change.message}。録音の明るさが時間で変わっていない。"
        "EG が下がらない（サステインが最大のまま）か、EG がカットオフにつながっていないと起きる。"
        "このままカットオフや EG の効きを動かしても直らない",
    )


def _recipe_value(recipe: PatchRecipe | None, parameter_id: str) -> str | None:
    if recipe is None:
        return None
    step = next((s for s in recipe.steps if s.parameter_id == parameter_id), None)
    if step is None or step.value is None:
        return None
    return fmt(step.value) if isinstance(step.value, int | float) else step.value


def _numeric_suggestion(
    feature: Feature,
    role: Role,
    sign: int,
    d: Difference,
    recipe: PatchRecipe | None,
    table: RecipeTable[P] | None,
    calibrations: CalibrationSet,
    f0_hz: float | None = None,
    masked: bool = False,
) -> AdjustmentSuggestion:
    """masked: フィルターで音量が下がる録音のアンプの提案。値を出さず、注意を添える。"""
    param = table.by_role(role) if table else None
    curve = None
    if param is not None and table is not None:
        curve = next(
            (
                c
                for pid in table.curve_ids(param)
                if (c := calibrations.get(pid, feature.value)) is not None
            ),
            None,
        )
    calibrated = False
    if curve is not None and curve.is_monotonic and param and param.min is not None:
        assert param.max is not None
        sign = 1 if curve.predict(param.max) > curve.predict(param.min) else -1
        calibrated = True
    need_increase = d.delta < 0  # 録音の値が小さい → 特徴を大きくしたい
    action = StepAction.INCREASE if need_increase == (sign > 0) else StepAction.DECREASE
    verb = "上げる" if action is StepAction.INCREASE else "下げる"

    value: float | int | None = None
    shift_note = ""
    if curve is not None and param is not None and not param.is_choice and not masked:
        target, measured = curve.inverse(d.reference), curve.inverse(d.recording)
        current = _current_value(recipe, param.id)
        if target is not None and measured is not None and current is not None:
            # 曲線と実際の録音のずれを補うため、現在値から差分だけ動かす
            # （音程による曲線のずれは、差を取ると打ち消し合う）
            value = param.clamp(current + target - measured)
        elif target is not None:
            shift = pitch_shift(param, curve, f0_hz)
            value = param.clamp(param.shift_octaves(target, shift.octaves) if shift else target)
            shift_note = shift.describe() if shift else ""

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
        reason=f"{d.message}。{basis}{shift_note}"
        + (
            "。ただし録音ではフィルターが閉じて音量も下がっており、差の一部はフィルターによる。"
            "値は出さない。明るさを合わせたあとで、少しずつ動かして確かめる"
            if masked
            else ""
        ),
    )


def _waveform_suggestion(
    spec: SoundSpec, d: Difference, table: RecipeTable[P] | None
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
