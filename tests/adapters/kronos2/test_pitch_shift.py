"""×f0 で測ったカットオフの曲線を、音程の違う参照音に使うときの補正。"""

import json
from pathlib import Path

import pytest

from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.adapters.kronos2.parameters import ParameterTable
from synth_ai.adapters.kronos2.recipe import pitch_shift
from synth_ai.adapters.kronos2.roles import Role
from synth_ai.core.audio.notes import note_to_hz
from synth_ai.core.calibration.models import CalibrationCurve
from synth_ai.core.comparison.models import Difference, DifferenceKind
from synth_ai.core.sound_spec.models import (
    PitchTarget,
    QuantTarget,
    SoundSpec,
    Speed,
    TimbreSpec,
)
from tests.adapters.kronos2.conftest import full_table, numeric

CUTOFF_ID = f"test.{Role.FILTER_CUTOFF.value}"


def curve(reference_note: str | None = "C4", unit: str = "x f0") -> CalibrationCurve:
    return CalibrationCurve.model_validate(
        {
            "synth_id": "kronos2",
            "parameter_id": CUTOFF_ID,
            "feature": "brightness_end",
            "unit": unit,
            "reference_note": reference_note,
            "points": [
                {"parameter_value": 0, "feature_value": 1.0},
                {"parameter_value": 50, "feature_value": 4.0},
                {"parameter_value": 99, "feature_value": 16.0},
            ],
        }
    )


def cutoff_param(steps_per_octave: float | None = 10):  # type: ignore[no-untyped-def]
    extra = {} if steps_per_octave is None else {"steps_per_octave": steps_per_octave}
    table = ParameterTable.model_validate(
        full_table() | {"parameters": [numeric(Role.FILTER_CUTOFF, **extra)]}
    )
    return table.parameters[0]


def test_one_octave_lower_is_ten_steps_down() -> None:
    shift = pitch_shift(cutoff_param(), curve(), note_to_hz("C3"))
    assert shift is not None
    assert shift.steps == pytest.approx(-10.0)
    assert shift.measured_note == "C4" and shift.target_note == "C3"
    assert "-10 段補正" in shift.describe()


def test_half_octave_higher() -> None:
    shift = pitch_shift(cutoff_param(), curve(), note_to_hz("F#4"))
    assert shift is not None and shift.steps == pytest.approx(5.0)


@pytest.mark.parametrize(
    ("param_steps", "the_curve", "f0"),
    [
        (10, curve(), note_to_hz("C4")),  # 同じ音程
        (None, curve(), note_to_hz("C3")),  # 段数が分からない
        (10, curve(reference_note=None), note_to_hz("C3")),  # 測定音程が分からない
        (10, curve(unit="ms"), note_to_hz("C3")),  # 音程に依存しない特徴
        (10, curve(), None),  # 参照音のピッチ不明
    ],
)
def test_no_shift(param_steps: float | None, the_curve: CalibrationCurve, f0: float | None) -> None:
    assert pitch_shift(cutoff_param(param_steps), the_curve, f0) is None


def spec_at(note: str) -> SoundSpec:
    return SoundSpec(
        spec_id=f"spec-{note}",
        reference_id="ref",
        pitch=PitchTarget(note=note, f0_hz=note_to_hz(note), confidence=0.9),
        timbre=TimbreSpec(brightness_decay=Speed.MEDIUM),
        targets=(
            QuantTarget(
                feature="brightness_end", value=4.0, unit="x f0", tolerance=0.8, confidence=0.8
            ),
            QuantTarget(
                feature="brightness_change", value=0.5, unit="ratio", tolerance=0.1, confidence=0.8
            ),
        ),
    )


@pytest.fixture
def adapter(tmp_path: Path) -> Kronos2Adapter:
    table = full_table()
    for p in table["parameters"]:
        if p["id"] == CUTOFF_ID:
            p["steps_per_octave"] = 10
    (tmp_path / "params").mkdir()
    (tmp_path / "params" / "al1.json").write_text(json.dumps(table))
    (tmp_path / "cal").mkdir()
    (tmp_path / "cal" / "cutoff.json").write_text(curve().model_dump_json())
    return Kronos2Adapter(parameter_dir=tmp_path / "params", calibration_dir=tmp_path / "cal")


def cutoff_step_value(adapter: Kronos2Adapter, note: str) -> object:
    recipe = adapter.create_recipe(spec_at(note))
    return next(s for s in recipe.steps if s.parameter_id == CUTOFF_ID).value


def test_recipe_shifts_cutoff_by_pitch(adapter: Kronos2Adapter) -> None:
    assert cutoff_step_value(adapter, "C4") == 50
    assert cutoff_step_value(adapter, "C3") == 40
    assert cutoff_step_value(adapter, "C2") == 30
    recipe = adapter.create_recipe(spec_at("C3"))
    step = next(s for s in recipe.steps if s.parameter_id == CUTOFF_ID)
    assert "参照音 C3 と測定音 C4" in step.reason


def test_adjustment_without_current_value_is_shifted(adapter: Kronos2Adapter) -> None:
    diff = Difference(
        kind=DifferenceKind.FEATURE,
        feature="brightness_end",
        reference=4.0,
        recording=16.0,
        delta=12.0,
        unit="x f0",
        severity=10,
        message="持続部が明るい",
    )
    out = adapter.suggest_adjustments(spec_at("C3"), (diff,), None)
    assert out[0].parameter_id == CUTOFF_ID
    assert out[0].value == 40
    assert "-10 段補正" in out[0].reason
