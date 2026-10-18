import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from synth_ai.adapters.kronos2.parameters import ParameterTable, load_table
from synth_ai.adapters.kronos2.roles import ChoiceTag, Role
from tests.adapters.kronos2.conftest import full_table, numeric


def test_load_and_lookup(parameter_dir: Path) -> None:
    table = load_table(parameter_dir, "AL-1")
    assert table is not None
    cutoff = table.by_role(Role.FILTER_CUTOFF)
    assert cutoff is not None and cutoff.id == "test.filter_cutoff"
    wave = table.by_role(Role.OSCILLATOR_WAVEFORM)
    assert wave is not None
    choice = wave.choice_with(ChoiceTag.PULSE)
    assert choice is not None and choice.value == "W-Square"
    assert table.by_id("missing") is None


def test_missing_file_is_none(tmp_path: Path) -> None:
    assert load_table(tmp_path, "AL-1") is None
    assert load_table(None, "AL-1") is None


def test_engine_mismatch(tmp_path: Path) -> None:
    data = full_table() | {"engine": "MOD-7"}
    (tmp_path / "al1.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="engine"):
        load_table(tmp_path, "AL-1")


@pytest.mark.parametrize(
    "bad",
    [
        numeric(Role.FILTER_CUTOFF, min=10, max=5),
        numeric(Role.FILTER_CUTOFF, default=200),
        numeric(Role.FILTER_CUTOFF, roles=["no_such_role"]),
        numeric(Role.FILTER_CUTOFF, kind="choice"),
        {k: v for k, v in numeric(Role.FILTER_CUTOFF).items() if k != "source_ref"},
    ],
)
def test_rejects_invalid_parameters(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ParameterTable.model_validate(full_table() | {"parameters": [bad]})


def test_rejects_duplicate_ids() -> None:
    p = numeric(Role.FILTER_CUTOFF)
    with pytest.raises(ValidationError, match="duplicated"):
        ParameterTable.model_validate(full_table() | {"parameters": [p, p]})


def test_clamp_and_step() -> None:
    table = ParameterTable.model_validate(
        full_table() | {"parameters": [numeric(Role.FILTER_CUTOFF, step=5)]}
    )
    p = table.parameters[0]
    assert p.clamp(150) == 95  # 上限 99 を超えない刻みの最大値
    assert p.clamp(-3) == 0
    assert p.clamp(12.4) == 10


def test_docs_example_is_valid() -> None:
    doc = (Path(__file__).resolve().parents[3] / "docs" / "kronos_parameter_table.md").read_text()
    block = doc.split("```json")[1].split("```")[0]
    data = json.loads(block)
    # 例のページ番号・名前は伏せ字なので、構造だけを確認する
    ParameterTable.model_validate(data)
