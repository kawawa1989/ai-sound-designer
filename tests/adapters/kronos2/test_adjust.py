import json
from pathlib import Path

from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.adapters.kronos2.roles import Role
from synth_ai.core.comparison.models import Difference, DifferenceKind
from synth_ai.core.sound_spec.models import (
    PatchRecipe,
    RecipeStep,
    SoundSpec,
    StepAction,
)


def fdiff(feature: str, ref: float, rec: float, severity: float = 5.0) -> Difference:
    return Difference(
        kind=DifferenceKind.FEATURE,
        feature=feature,
        reference=ref,
        recording=rec,
        delta=rec - ref,
        unit="u",
        severity=severity,
        message=f"{feature} differs",
    )


def test_directions_without_table(lead_spec: SoundSpec) -> None:
    diffs = (
        fdiff("attack_time", 8, 60),  # 遅い → アタックを下げる
        fdiff("brightness_change", 0.2, 0.9),  # 暗くなり方が弱い → EG の効きを上げる
        fdiff("sustain_level", -4, -12),  # 小さい → サステインを上げる
    )
    out = Kronos2Adapter().suggest_adjustments(lead_spec, diffs, None)
    assert [s.action for s in out] == [
        StepAction.DECREASE,
        StepAction.INCREASE,
        StepAction.INCREASE,
    ]
    assert "アンプ EG のアタック" in out[0].message
    assert all(s.parameter_id is None for s in out)
    assert "一般的な傾向" in out[0].reason


def test_one_suggestion_per_role(lead_spec: SoundSpec) -> None:
    diffs = (
        fdiff("brightness_end", 2, 20, 9),
        fdiff("brightness", 3, 20, 8),
        fdiff("attack_time", 8, 60, 2),
    )
    out = Kronos2Adapter().suggest_adjustments(lead_spec, diffs, None)
    assert len(out) == 2


def test_with_table_and_calibration(
    lead_spec: SoundSpec, parameter_dir: Path, calibration_dir: Path
) -> None:
    adapter = Kronos2Adapter(parameter_dir=parameter_dir, calibration_dir=calibration_dir)
    param_id = f"test.{Role.AMP_EG_ATTACK.value}"
    recipe = PatchRecipe(
        recipe_id="r",
        sound_spec_id=lead_spec.spec_id,
        synth_id="kronos2",
        engine="AL-1",
        rationale="",
        steps=(
            RecipeStep(
                order=1,
                action=StepAction.SET,
                page="TestPage",
                parameter_id=param_id,
                parameter="Test",
                value=50,
                reason="",
            ),
        ),
    )
    # 曲線では 50 → 100 ms だが、実際の録音は 200 ms だった。目標は 100 ms
    out = adapter.suggest_adjustments(lead_spec, (fdiff("attack_time", 100.0, 200.0),), recipe)
    s = out[0]
    assert s.parameter_id == param_id and s.page == "TestPage"
    assert s.action is StepAction.DECREASE
    # 曲線上の差（100 ms → 50, 200 ms → 約 52.6）だけ現在値から動かす
    assert isinstance(s.value, int) and 45 <= s.value < 50
    assert "キャリブレーション表" in s.reason


def test_waveform_suggestion(lead_spec: SoundSpec, parameter_dir: Path) -> None:
    spec = lead_spec.model_copy(
        update={
            "targets": lead_spec.targets
            + (
                lead_spec.targets[0].model_copy(
                    update={"feature": "odd_even_ratio", "value": 40.0}
                ),
                lead_spec.targets[0].model_copy(
                    update={"feature": "harmonic_slope", "value": -6.0}
                ),
            )
        }
    )
    adapter = Kronos2Adapter(parameter_dir=parameter_dir)
    out = adapter.suggest_adjustments(spec, (fdiff("odd_even_ratio", 40, 0),), None)
    assert out[0].action is StepAction.SELECT
    assert out[0].value == "W-Square"


def test_capability_declared() -> None:
    assert Kronos2Adapter().capabilities().is_supported("adjustment_suggestions")
    json.dumps(Kronos2Adapter().capabilities().model_dump(mode="json"))
