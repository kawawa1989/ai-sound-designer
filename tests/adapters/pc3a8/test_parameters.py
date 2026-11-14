import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from synth_ai.adapters.pc3a8.parameters import ROLES, ParameterTable, load_table

ROOT = Path(__file__).resolve().parents[3]


def numeric(**extra: Any) -> dict[str, Any]:
    """テスト専用の項目。名前・ページは架空で、実機の値ではない。"""
    entry: dict[str, Any] = {
        "id": "test.time",
        "page": "TestPage",
        "name": "Test Time",
        "kind": "float",
        "min": 0,
        "max": 60,
        "unit": "s",
        "roles": ["amp_eg_attack"],
        "source_ref": "test fixture",
        "verified": True,
    }
    entry.update(extra)
    return entry


def table(*params: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine": "KVA",
        "source": {"document": "test"},
        "layout": {"program": "1 Test", "keymap": "1 Test", "algorithm": 1, "blocks": ["X"]},
        "parameters": list(params) or [numeric()],
    }


def test_load_and_lookup(tmp_path: Path) -> None:
    wave = {
        "id": "test.wave",
        "page": "ALG",
        "name": "Oscillator",
        "kind": "choice",
        "choices": [{"value": "W-SAW", "tags": ["saw"]}],
        "roles": ["oscillator_waveform"],
        "source_ref": "test fixture",
        "verified": True,
    }
    (tmp_path / "kva.json").write_text(json.dumps(table(numeric(), wave)))
    loaded = load_table(tmp_path, "KVA")
    assert loaded is not None
    assert loaded.by_role("amp_eg_attack") == loaded.by_id("test.time")
    choice = loaded.parameters[1].choice_with("saw")
    assert choice is not None and choice.value == "W-SAW"
    assert load_table(tmp_path, "OTHER") is None
    assert load_table(None, "KVA") is None


def test_engine_mismatch(tmp_path: Path) -> None:
    (tmp_path / "kva.json").write_text(json.dumps(table() | {"engine": "VAST"}))
    with pytest.raises(ValueError, match="engine"):
        load_table(tmp_path, "KVA")


def test_unverified_is_not_usable() -> None:
    unknown_range = numeric(id="test.unknown", min=None, max=None, verified=False)
    unverified = numeric(id="test.unverified", verified=False, roles=["amp_eg_release"])
    loaded = ParameterTable.model_validate(table(numeric(), unknown_range, unverified))
    assert [p.id for p in loaded.unverified()] == ["test.unknown", "test.unverified"]
    assert loaded.by_role("amp_eg_release") is None  # 確かめていないものはレシピに使わない
    assert loaded.by_role("amp_eg_release", usable_only=False) is not None
    with pytest.raises(ValueError, match="range"):
        loaded.parameters[1].clamp(1.0)


@pytest.mark.parametrize(
    "bad",
    [
        numeric(min=10, max=5),
        numeric(min=None),  # 確かめた数値の項目は範囲が必須
        numeric(default=99),
        numeric(base_value=-1),
        numeric(roles=["no_such_role"]),
        numeric(kind="choice"),
        numeric(step=0),
        numeric(kind="choice", choices=[{"value": "A", "tags": ["no_such_tag"]}]),
        numeric(kind="choice", choices=[{"value": "A"}], base_value="B"),
        {k: v for k, v in numeric().items() if k != "source_ref"},
        numeric(unknown_field=1),
    ],
)
def test_rejects_invalid_parameters(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ParameterTable.model_validate(table(bad))


def test_rejects_duplicate_ids_and_wrong_synth() -> None:
    with pytest.raises(ValidationError, match="duplicated"):
        ParameterTable.model_validate(table(numeric(), numeric()))
    with pytest.raises(ValidationError):
        ParameterTable.model_validate(table() | {"synth_id": "kronos2"})


def test_clamp_and_step() -> None:
    loaded = ParameterTable.model_validate(table(numeric(step=0.02, max=1)))
    p = loaded.parameters[0]
    assert p.clamp(0.065) == pytest.approx(0.06)  # 0.02 刻みのいちばん近い値
    assert p.clamp(5) == pytest.approx(1.0)
    assert p.clamp(-1) == 0


def test_uneven_grid() -> None:
    """刻みが一定でない値は、本体で選べるいちばん近い値に丸める。"""
    p = ParameterTable.model_validate(
        table(
            numeric(
                values=[0, 0.002, 0.005, 0.01],
                step_ranges=[
                    {"start": 0.02, "end": 2.0, "step": 0.02},
                    {"start": 2.0, "end": 5.0, "step": 0.04},
                ],
            )
        )
    ).parameters[0]
    grid = p.grid()
    assert grid[:6] == (0, 0.002, 0.005, 0.01, 0.02, 0.04)
    assert grid[-1] == 5.0 and grid.count(2.0) == 1
    assert p.clamp(0.004) == 0.005
    assert p.clamp(0.061) == pytest.approx(0.06)
    assert p.clamp(3.01) == pytest.approx(3.0)
    assert p.clamp(30.3) == pytest.approx(30.3)  # 確かめた範囲の外は丸めない
    assert p.clamp(99) == 60


@pytest.mark.parametrize(
    "bad",
    [
        numeric(step_ranges=[{"start": 2, "end": 1, "step": 0.1}]),
        numeric(step_ranges=[{"start": 50, "end": 70, "step": 1}]),
        numeric(values=[-1]),
        numeric(step=0.1, values=[0, 0.5]),
    ],
)
def test_rejects_invalid_grid(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ParameterTable.model_validate(table(bad))


def test_roles_match_kronos_vocabulary() -> None:
    """共通の概念は KRONOS と同じ役割名を使う（共通化は #20）。"""
    from synth_ai.adapters.kronos2.roles import Role

    assert ROLES.issubset({r.value for r in Role})


def test_project_kva_table_is_valid() -> None:
    """data/pc3a8_parameters/kva.json（公式資料と実機から作った表）がスキーマを満たす。"""
    loaded = load_table(ROOT / "data" / "pc3a8_parameters", "KVA")
    assert loaded is not None
    for p in loaded.parameters:
        assert p.source_ref.startswith("Musician's Guide 本文 ") or "実機" in p.source_ref, p.id
        if not p.usable:
            # 要確認の項目には、何が分かっていないかを書く
            assert "要確認" in p.notes, p.id
    # レシピで使う主要な役割は、確かめた値で表にある
    for role in (
        "oscillator_waveform",
        "filter_type",
        "amp_eg_attack",
        "amp_eg_decay",
        "amp_eg_sustain",
        "amp_eg_release",
    ):
        assert loaded.by_role(role) is not None, role
    # 実機で確かめた範囲（2026-11-14）
    cutoff = loaded.by_role("filter_cutoff")
    assert cutoff is not None
    assert (cutoff.min, cutoff.max, cutoff.steps_per_octave) == (16, 25088, 12)
    release = loaded.by_role("amp_eg_release")
    assert release is not None and release.clamp(0.05) in (0.04, 0.06)  # 0.05 は選べない
    # 基準音の値は、基準音の配置（layout）と一致する
    assert loaded.layout.blocks[:2] == (
        loaded.by_id("kva.alg.block1").base_value,  # type: ignore[union-attr]
        loaded.by_id("kva.alg.block2").base_value,  # type: ignore[union-attr]
    )
