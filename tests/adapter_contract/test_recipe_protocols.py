"""各機種のパラメータ表が、Core のレシピ組み立て（core.planning）の Protocol を満たす。

代入の型は mypy が検査する。実行時は、表から引いたパラメータで最低限の動作を確かめる。
"""

from __future__ import annotations

from pathlib import Path

from synth_ai.adapters.kronos2.parameters import load_table as load_kronos
from synth_ai.adapters.pc3a8.parameters import load_table as load_pc3a8
from synth_ai.core.planning.protocols import P, RecipeTable
from synth_ai.core.planning.roles import ChoiceTag, Role

ROOT = Path(__file__).resolve().parents[2]


def check(table: RecipeTable[P]) -> None:
    wave = table.by_role(Role.OSCILLATOR_WAVEFORM)
    assert wave is not None and wave.is_choice
    assert wave.choice_with(ChoiceTag.SAW) is not None
    assert table.curve_ids(wave)[0] == wave.id
    assert wave.location.startswith(wave.page)


def test_tables_satisfy_recipe_protocol() -> None:
    kronos = load_kronos(ROOT / "data" / "kronos_parameters", "AL-1")
    pc3a8 = load_pc3a8(ROOT / "data" / "pc3a8_parameters", "KVA")
    assert kronos is not None and pc3a8 is not None
    check(kronos)
    check(pc3a8)
