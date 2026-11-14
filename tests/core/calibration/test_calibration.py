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


def test_log_scale_interpolates_in_octaves() -> None:
    """周波数の値は比で効くので、測定点の間を対数で補間する。"""
    points = (
        CalibrationPoint(parameter_value=1000, feature_value=2.0),
        CalibrationPoint(parameter_value=4000, feature_value=6.0),
    )
    c = CalibrationCurve(
        synth_id="s",
        parameter_id="p",
        feature="brightness_end",
        unit="x f0",
        parameter_scale="log",
        points=points,
    )
    assert c.predict(2000) == pytest.approx(4.0)  # 1 オクターブ上（線形なら 3.33）
    assert c.inverse(4.0) == pytest.approx(2000)
    assert c.predict(0) == pytest.approx(2.0)
    linear = c.model_copy(update={"parameter_scale": "linear"})
    assert linear.predict(2000) == pytest.approx(2.0 + 4.0 / 3)
    with pytest.raises(ValidationError, match="positive"):
        CalibrationCurve.model_validate(
            c.model_dump()
            | {"points": [{"parameter_value": 0, "feature_value": 1}, *c.model_dump()["points"]]}
        )


def test_physical_unit_values() -> None:
    """秒のような小数のパラメータ値でも曲線を作り、逆引きできる。"""
    c = curve([(0, 8.5), (0.02, 15.0), (0.1, 60.0), (0.4, 230.0)])
    assert c.is_monotonic
    assert c.inverse(60.0) == pytest.approx(0.1)
    assert c.inverse(37.5) == pytest.approx(0.06)


def test_kronos_curves_load_unchanged() -> None:
    """既存の KRONOS の曲線（parameter_scale なし）は線形のまま読める。"""
    directory = Path(__file__).resolve().parents[3] / "data" / "kronos_calibration"
    curves = CalibrationSet.load(directory, "kronos2")
    assert len(curves) == 5
    attack = curves.get("al1.amp_eg.time.attack", "attack_time")
    assert attack is not None and attack.parameter_scale == "linear"
