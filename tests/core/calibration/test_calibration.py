import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from synth_ai.core.calibration.models import CalibrationCurve, CalibrationPoint, CalibrationSet


def curve(points: list[tuple[float, float]], **kw: str) -> CalibrationCurve:
    return CalibrationCurve(
        synth_id=kw.get("synth_id", "s"),
        parameter_id=kw.get("parameter_id", "p"),
        feature=kw.get("feature", "attack_time"),
        unit="ms",
        points=tuple(CalibrationPoint(parameter_value=x, feature_value=y) for x, y in points),
    )


def test_inverse_increasing() -> None:
    c = curve([(0, 2.0), (50, 20.0), (100, 200.0)])
    assert c.inverse(20.0) == pytest.approx(50)
    assert c.inverse(11.0) == pytest.approx(25)
    assert c.predict(25) == pytest.approx(11.0)


def test_inverse_decreasing_and_unsorted() -> None:
    c = curve([(100, 1.0), (0, 30.0), (50, 10.0)])
    assert c.inverse(10.0) == pytest.approx(50)
    assert c.inverse(20.0) == pytest.approx(25)


def test_out_of_range_clamps_to_end() -> None:
    c = curve([(0, 2.0), (100, 200.0)])
    assert c.inverse(500.0) == pytest.approx(100)
    assert not c.covers(500.0)
    assert c.covers(100.0)


def test_non_monotonic_has_no_inverse() -> None:
    c = curve([(0, 1.0), (50, 5.0), (100, 3.0)])
    assert not c.is_monotonic
    assert c.inverse(2.0) is None


def test_rejects_bad_curves() -> None:
    with pytest.raises(ValidationError):
        curve([(0, 1.0)])
    with pytest.raises(ValidationError):
        curve([(0, 1.0), (0, 2.0)])


def test_load_filters_by_synth(tmp_path: Path) -> None:
    for i, synth in enumerate(("a", "a", "b")):
        c = curve([(0, 1.0), (1, 2.0)], synth_id=synth, parameter_id=f"p{i}")
        (tmp_path / f"{i}.json").write_text(c.model_dump_json())
    loaded = CalibrationSet.load(tmp_path, "a")
    assert len(loaded) == 2
    assert loaded.get("p0", "attack_time") is not None
    assert loaded.get("p2", "attack_time") is None
    assert len(CalibrationSet.load(tmp_path / "missing", "a")) == 0
    assert len(CalibrationSet.load(None, "a")) == 0


def test_json_example_in_docs_is_valid() -> None:
    doc = (Path(__file__).resolve().parents[3] / "docs" / "kronos_parameter_table.md").read_text()
    block = doc.split("`data/kronos_calibration/*.json`")[1].split("```json")[1].split("```")[0]
    CalibrationCurve.model_validate(json.loads(block))
