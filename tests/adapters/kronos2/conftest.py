"""テスト専用のパラメータ表。名前・ページは架空で、実機の値ではない。"""

import json
from pathlib import Path
from typing import Any

import pytest

from synth_ai.adapters.kronos2.roles import Role


def numeric(role: Role, **extra: Any) -> dict[str, Any]:
    entry = {
        "id": f"test.{role.value}",
        "page": "TestPage",
        "name": f"Test {role.value}",
        "kind": "int",
        "min": 0,
        "max": 99,
        "roles": [role.value],
        "source_ref": "test fixture",
        "verified": True,
    }
    entry.update(extra)
    return entry


def full_table(skip: tuple[Role, ...] = ()) -> dict[str, Any]:
    params: list[dict[str, Any]] = [
        {
            "id": "test.wave",
            "page": "TestPage",
            "tab": "Osc",
            "name": "Test Wave",
            "kind": "choice",
            "choices": [
                {"value": "W-Saw", "tags": ["saw"]},
                {"value": "W-Square", "tags": ["square", "pulse"]},
                {"value": "W-Tri", "tags": ["triangle"]},
                {"value": "W-Sine", "tags": ["sine"]},
            ],
            "roles": [Role.OSCILLATOR_WAVEFORM.value],
            "source_ref": "test fixture",
            "verified": True,
        },
        {
            "id": "test.filter_type",
            "page": "TestPage",
            "name": "Test Filter Type",
            "kind": "choice",
            "choices": [{"value": "F-LPF", "tags": ["lowpass"]}],
            "roles": [Role.FILTER_TYPE.value],
            "source_ref": "test fixture",
            "verified": False,
        },
    ]
    params.append(
        {
            "id": "test.eg_select",
            "page": "TestPage",
            "name": "Test EG Select",
            "kind": "choice",
            "choices": [{"value": "E-1", "tags": ["filter_eg"]}, {"value": "E-Amp"}],
            "roles": [Role.FILTER_EG_SOURCE.value],
            "source_ref": "test fixture",
            "verified": True,
        }
    )
    choice_roles = (Role.OSCILLATOR_WAVEFORM, Role.FILTER_TYPE, Role.FILTER_EG_SOURCE)
    bipolar = (
        Role.FILTER_EG_INTENSITY,
        Role.FILTER_EG_START_LEVEL,
        Role.FILTER_EG_ATTACK_LEVEL,
        Role.FILTER_EG_BREAK_LEVEL,
        Role.FILTER_EG_SUSTAIN,
    )
    params += [
        numeric(r, min=-99) if r in bipolar else numeric(r) for r in Role if r not in choice_roles
    ]
    params = [p for p in params if not set(p["roles"]) & {r.value for r in skip}]
    return {
        "schema_version": "1.0",
        "synth_id": "kronos2",
        "engine": "AL-1",
        "source": {"document": "test"},
        "parameters": params,
    }


@pytest.fixture
def parameter_dir(tmp_path: Path) -> Path:
    d = tmp_path / "params"
    d.mkdir()
    (d / "al1.json").write_text(json.dumps(full_table()))
    return d


@pytest.fixture
def calibration_dir(tmp_path: Path) -> Path:
    d = tmp_path / "calibration"
    d.mkdir()
    curve = {
        "synth_id": "kronos2",
        "parameter_id": f"test.{Role.AMP_EG_ATTACK.value}",
        "feature": "attack_time",
        "unit": "ms",
        "points": [
            {"parameter_value": 0, "feature_value": 1.0},
            {"parameter_value": 50, "feature_value": 100.0},
            {"parameter_value": 99, "feature_value": 2000.0},
        ],
    }
    (d / "attack.json").write_text(json.dumps(curve))
    return d
