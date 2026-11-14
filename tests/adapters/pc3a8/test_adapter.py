from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from synth_ai.adapters.base import AdjustmentAdvisor, CapabilityStatus, ParameterCatalog
from synth_ai.adapters.pc3a8 import Pc3a8Adapter
from synth_ai.adapters.pc3a8.adapter import PAGE_ORDER
from synth_ai.adapters.pc3a8.parameters import load_table
from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.comparison.models import Difference, DifferenceKind
from synth_ai.core.sound_spec.derive import derive_sound_spec
from synth_ai.core.sound_spec.models import SoundSpec, StepAction, StepStatus
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.workflow.recipe import generate_recipe

Analyze = Callable[[str, np.ndarray], AnalysisResult]
TABLE_DIR = Path(__file__).resolve().parents[3] / "data" / "pc3a8_parameters"

SIGNALS: dict[str, Callable[[], np.ndarray]] = {
    "lead": lambda: ts.saw(),
    "bass": lambda: ts.saw_filter_sweep(),
    "pluck": lambda: ts.pluck(),
    "square": lambda: ts.square(),
}


def spec_for(analyze_signal: Analyze, name: str) -> SoundSpec:
    return derive_sound_spec(analyze_signal(f"pc3a8_{name}", SIGNALS[name]()).analysis)


@pytest.fixture
def adapter() -> Pc3a8Adapter:
    return Pc3a8Adapter(parameter_dir=TABLE_DIR)


def test_capabilities() -> None:
    caps = Pc3a8Adapter().capabilities()
    assert caps.user_sample_import is CapabilityStatus.UNSUPPORTED
    assert caps.midi_notes is CapabilityStatus.SUPPORTED
    assert caps.parameter_read is CapabilityStatus.UNVERIFIED
    assert caps.parameter_write is CapabilityStatus.UNVERIFIED
    assert caps.available_engines == ("KVA",)
    assert isinstance(Pc3a8Adapter(), ParameterCatalog)
    assert isinstance(Pc3a8Adapter(), AdjustmentAdvisor)


def test_without_table_no_parameters_are_invented(analyze_signal: Analyze) -> None:
    recipe = Pc3a8Adapter().create_recipe(spec_for(analyze_signal, "lead"))
    assert recipe.steps == ()
    assert any("パラメータ表" in u for u in recipe.uncertainties)


@pytest.mark.parametrize("name", sorted(SIGNALS))
def test_recipe_values_are_in_range(
    analyze_signal: Analyze, adapter: Pc3a8Adapter, name: str
) -> None:
    """代表的な音から、表にある項目だけを、範囲内の値で、ページの順に並べる。"""
    spec = spec_for(analyze_signal, name)
    recipe = generate_recipe(spec, adapter)
    table = load_table(TABLE_DIR, "KVA")
    assert table is not None and recipe.steps
    for step in recipe.steps:
        param = table.by_id(step.parameter_id or "")
        assert param is not None and param.usable, step.parameter_id
        assert step.status is StepStatus.VERIFIED
        assert step.page == param.location
        if param.is_choice:
            assert step.value in {c.value for c in param.choices}
        elif step.value is not None:
            assert param.min is not None and param.max is not None
            assert param.min <= float(step.value) <= param.max
            assert param.clamp(float(step.value)) == step.value  # 本体で選べる値
    pages = [PAGE_ORDER.index(s.page.split(" › ")[0]) for s in recipe.steps]
    assert pages == sorted(pages)
    assert [s.order for s in recipe.steps] == list(range(1, len(recipe.steps) + 1))
    text = adapter.manual_instructions(recipe)
    assert "⚠" not in text  # 確かめていない項目を手順にしない
    assert "1025 KVA BASIC SAW" in text and "1026 以降" in text
    if "kva.alg.block2" in {s.parameter_id for s in recipe.steps}:
        assert "→ **LOPASS**" in text


def test_manual_shows_units(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    text = adapter.manual_instructions(adapter.create_recipe(spec_for(analyze_signal, "bass")))
    assert "**ENV2 › Att1** › Level → **100 %**" in text
    assert "（本体で選べるいちばん近い値）" in text  # 刻みが分からない時間の項目


def test_lead_recipe(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    recipe = adapter.create_recipe(spec_for(analyze_signal, "lead"))
    values = {s.parameter_id: s.value for s in recipe.steps}
    assert values["kva.alg.block1"] == "SAW"
    assert values["kva.alg.block2"] == "LOPASS"
    # 明るさが変わらない音では、ENV2 でカットオフを動かさない
    assert values["kva.dspmod.lp_frq.depth"] == 0
    assert not any(pid.startswith("kva.env2.") for pid in values)
    # 時間の目標（ms）は、秒の項目の初期値になる（Adsr の既定: アタック 5 ms）
    attack = values["kva.ampenv.att1.time"]
    assert isinstance(attack, float | int) and 0 < attack < 0.05
    assert any("換算して初期値" in u for u in recipe.uncertainties)
    # カットオフはキャリブレーションがないので目標だけ
    cutoff = next(s for s in recipe.steps if s.parameter_id == "kva.dspctl.lp_frq")
    assert cutoff.value is None and cutoff.target is not None


def test_darkening_sound_uses_env2(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    recipe = adapter.create_recipe(spec_for(analyze_signal, "bass"))
    values = {s.parameter_id: s.value for s in recipe.steps}
    assert values["kva.dspmod.lp_frq.src1"] == "ENV2"
    assert values["kva.env2.att1.level"] == 100
    assert values["kva.env2.att1.time"] == 0
    assert values["kva.env2.decay.level"] == 0  # 両極性なので「効果なし」は 0


def test_unavailable_waveform_keeps_base(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    """三角波は一覧にないので、選ばずに基準音の SAW のままにする。"""
    spec = spec_for(analyze_signal, "square")
    recipe = adapter.create_recipe(spec)
    wave = next((s for s in recipe.steps if s.parameter_id == "kva.alg.block1"), None)
    if wave is None:
        assert any("SAW のまま" in u for u in recipe.uncertainties)
    else:
        assert wave.value in ("SQUARE", "SAW", "SINE")


def test_no_sample_import(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    recipe = adapter.create_recipe(spec_for(analyze_signal, "pluck"))
    assert all(s.action is not StepAction.IMPORT_SAMPLE for s in recipe.steps)


def test_spec_is_not_modified(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    spec = spec_for(analyze_signal, "bass")
    before = spec.model_dump_json()
    adapter.create_recipe(spec)
    assert spec.model_dump_json() == before


def test_calibratable_parameters(adapter: Pc3a8Adapter) -> None:
    infos = {i.parameter_id: i for i in adapter.calibratable_parameters()}
    assert infos["kva.dspctl.lp_frq"].calibration_feature == "brightness_end"
    assert infos["kva.ampenv.rel1.time"].calibration_feature == "release_time"
    assert infos["kva.ampenv.decay.time"].label == "AMPENV › Dec1 › Time"
    assert "kva.alg.block1" not in infos  # 選択式は測らない
    assert adapter.parameter_info("kva.alg.block1") is not None
    assert adapter.parameter_info("no.such.id") is None


def test_adjustment_suggestion(analyze_signal: Analyze, adapter: Pc3a8Adapter) -> None:
    spec = spec_for(analyze_signal, "lead")
    recipe = adapter.create_recipe(spec)
    diff = Difference(
        feature="release_time",
        kind=DifferenceKind.FEATURE,
        reference=300.0,
        recording=100.0,
        delta=-200.0,
        unit="ms",
        severity=5.0,
        message="リリースが短い",
    )
    (suggestion,) = adapter.suggest_adjustments(spec, (diff,), recipe)
    assert suggestion.parameter_id == "kva.ampenv.rel1.time"
    assert suggestion.action is StepAction.INCREASE
