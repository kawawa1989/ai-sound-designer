from collections.abc import Callable
from pathlib import Path

import numpy as np

from synth_ai.adapters.base import CapabilityStatus
from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.adapters.kronos2.roles import Role
from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.sound_spec.derive import derive_sound_spec
from synth_ai.core.sound_spec.models import SoundSpec, StepAction, StepStatus
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.workflow.recipe import generate_recipe
from tests.adapters.kronos2.conftest import full_table

Analyze = Callable[[str, np.ndarray], AnalysisResult]


def spec_for(analyze_signal: Analyze, name: str, samples: np.ndarray) -> SoundSpec:
    return derive_sound_spec(analyze_signal(name, samples).analysis)


def test_nothing_is_claimed_as_supported_before_verification() -> None:
    caps = Kronos2Adapter().capabilities()
    assert caps.parameter_write is CapabilityStatus.UNVERIFIED
    assert not caps.is_supported("parameter_write")
    assert caps.available_engines == ("AL-1", "MOD-7", "HD-1")


def test_without_table_no_parameters_are_invented(analyze_signal: Analyze) -> None:
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    recipe = generate_recipe(spec, Kronos2Adapter())
    assert recipe.engine == "AL-1"
    assert recipe.steps == ()
    text = "\n".join(recipe.uncertainties)
    assert "パラメータ表" in text and "フィルターのカットオフ" in text
    assert "未確定事項" in Kronos2Adapter().manual_instructions(recipe)


def test_recipe_from_table(analyze_signal: Analyze, parameter_dir: Path) -> None:
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    adapter = Kronos2Adapter(parameter_dir=parameter_dir)
    recipe = generate_recipe(spec, adapter)
    by_id = {s.parameter_id: s for s in recipe.steps}
    table_ids = {p["id"] for p in full_table()["parameters"]}
    assert set(by_id) <= table_ids
    assert by_id["test.wave"].value == "W-Saw"
    assert by_id["test.wave"].action is StepAction.SELECT
    assert by_id["test.filter_type"].status is StepStatus.NEEDS_CONFIRMATION
    assert by_id["test.wave"].status is StepStatus.VERIFIED
    # 明るさが下がる音なので、フィルター EG を使う
    assert f"test.{Role.FILTER_EG_INTENSITY.value}" in by_id
    assert by_id[f"test.{Role.FILTER_EG_ATTACK.value}"].value == 0
    # キャリブレーションがないので値は空、目標は示す
    cutoff = by_id[f"test.{Role.FILTER_CUTOFF.value}"]
    assert cutoff.value is None and cutoff.target is not None
    assert cutoff.target.feature == "brightness_end"
    assert f"test.{Role.FILTER_RESONANCE.value}" not in by_id
    assert [s.order for s in recipe.steps] == list(range(1, len(recipe.steps) + 1))
    assert any("キャリブレーション未測定" in u for u in recipe.uncertainties)


def test_waveform_follows_spectrum(analyze_signal: Analyze, parameter_dir: Path) -> None:
    spec = spec_for(analyze_signal, "ad_square", ts.square())
    recipe = Kronos2Adapter(parameter_dir=parameter_dir).create_recipe(spec)
    assert recipe.steps[0].value == "W-Square"
    # 明るさが変わらない音では、フィルター EG の効きを 0 にするだけ
    eg_steps = [s for s in recipe.steps if "filter_eg" in s.parameter_id]
    assert [(s.parameter_id, s.value) for s in eg_steps] == [
        (f"test.{Role.FILTER_EG_INTENSITY.value}", 0)
    ]


def test_multistage_eg_for_darkening_sound(analyze_signal: Analyze, parameter_dir: Path) -> None:
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    recipe = Kronos2Adapter(parameter_dir=parameter_dir).create_recipe(spec)
    values = {s.parameter_id: s.value for s in recipe.steps}
    assert values["test.eg_select"] == "E-1"
    assert values[f"test.{Role.FILTER_EG_START_LEVEL.value}"] == 99
    # 両極性のレベルでは「効果なし」は 0（最小の -99 ではない）
    assert values[f"test.{Role.FILTER_EG_SUSTAIN.value}"] == 0
    assert values[f"test.{Role.FILTER_EG_BREAK_LEVEL.value}"] == 0
    assert values[f"test.{Role.AMP_EG_START_LEVEL.value}"] == 0
    # サステインがある音: ブレイク・レベルもサステインと同じ目標
    break_step = next(
        s for s in recipe.steps if s.parameter_id == f"test.{Role.AMP_EG_BREAK_LEVEL.value}"
    )
    assert break_step.target is not None and break_step.target.feature == "sustain_level"


def test_optional_roles_are_not_reported_missing(analyze_signal: Analyze, tmp_path: Path) -> None:
    import json

    optional = (
        Role.FILTER_EG_SOURCE,
        Role.FILTER_EG_START_LEVEL,
        Role.FILTER_EG_ATTACK_LEVEL,
        Role.FILTER_EG_BREAK_LEVEL,
        Role.AMP_EG_START_LEVEL,
        Role.AMP_EG_ATTACK_LEVEL,
        Role.AMP_EG_BREAK_LEVEL,
    )
    (tmp_path / "al1.json").write_text(json.dumps(full_table(skip=optional)))
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    recipe = Kronos2Adapter(parameter_dir=tmp_path).create_recipe(spec)
    assert not any("未登録" in u for u in recipe.uncertainties)


def test_parameter_notes_are_shown(analyze_signal: Analyze, tmp_path: Path) -> None:
    import json

    table = full_table()
    for p in table["parameters"]:
        if p["id"] == "test.wave":
            p["notes"] = "矩形波は幅 50"
    (tmp_path / "al1.json").write_text(json.dumps(table))
    spec = spec_for(analyze_signal, "ad_saw", ts.saw())
    recipe = Kronos2Adapter(parameter_dir=tmp_path).create_recipe(spec)
    assert "（注: 矩形波は幅 50）" in recipe.steps[0].reason


def test_calibration_gives_values(
    analyze_signal: Analyze, parameter_dir: Path, calibration_dir: Path
) -> None:
    spec = spec_for(analyze_signal, "ad_attack", ts.saw(adsr=ts.Adsr(attack_s=0.125)))
    adapter = Kronos2Adapter(parameter_dir=parameter_dir, calibration_dir=calibration_dir)
    recipe = generate_recipe(spec, adapter)
    attack = next(s for s in recipe.steps if s.parameter_id == f"test.{Role.AMP_EG_ATTACK.value}")
    # 目標 ≈ 100 ms（線形 125 ms の 80%）→ 曲線上で 50
    assert isinstance(attack.value, int) and 45 <= attack.value <= 55
    assert "キャリブレーション表" in attack.reason


def test_missing_roles_are_reported(analyze_signal: Analyze, tmp_path: Path) -> None:
    import json

    (tmp_path / "al1.json").write_text(json.dumps(full_table(skip=(Role.FILTER_CUTOFF,))))
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    recipe = Kronos2Adapter(parameter_dir=tmp_path).create_recipe(spec)
    assert all(s.parameter_id != f"test.{Role.FILTER_CUTOFF.value}" for s in recipe.steps)
    assert any("フィルターのカットオフ" in u for u in recipe.uncertainties)


def test_bell_notes_that_mod7_fits_better(analyze_signal: Analyze) -> None:
    spec = spec_for(analyze_signal, "ad_bell", ts.fm_bell())
    recipe = Kronos2Adapter().create_recipe(spec)
    assert recipe.engine == "AL-1"
    assert recipe.alternatives[0].engine == "MOD-7"
    assert any("MOD-7" in u for u in recipe.uncertainties)


def test_manual_instructions(analyze_signal: Analyze, parameter_dir: Path) -> None:
    spec = spec_for(analyze_signal, "ad_sweep", ts.saw_filter_sweep())
    adapter = Kronos2Adapter(parameter_dir=parameter_dir)
    text = adapter.manual_instructions(adapter.create_recipe(spec))
    assert "## 準備" in text and "## 手順" in text
    assert "**TestPage › Osc** › Test Wave → **W-Saw**" in text
    assert "資料で要確認" in text  # verified=false のパラメータ
    assert "目標" in text


def test_parameter_catalog(parameter_dir: Path) -> None:
    from synth_ai.adapters.base import ParameterCatalog

    adapter = Kronos2Adapter(parameter_dir=parameter_dir)
    assert isinstance(adapter, ParameterCatalog)
    info = adapter.parameter_info(f"test.{Role.AMP_EG_ATTACK.value}")
    assert info is not None and info.calibration_feature == "attack_time"
    assert info.label == f"TestPage › Test {Role.AMP_EG_ATTACK.value}"
    wave = adapter.parameter_info("test.wave")
    assert wave is not None and not wave.is_numeric
    assert adapter.parameter_info("missing") is None
    ids = {p.parameter_id for p in adapter.calibratable_parameters()}
    assert f"test.{Role.FILTER_CUTOFF.value}" in ids
    assert "test.wave" not in ids and f"test.{Role.FILTER_RESONANCE.value}" not in ids
    assert Kronos2Adapter().calibratable_parameters() == ()


def test_break_level_uses_sustain_curve(analyze_signal: Analyze, tmp_path: Path) -> None:
    import json

    table = full_table()
    sustain_id = f"test.{Role.AMP_EG_SUSTAIN.value}"
    for p in table["parameters"]:
        if p["id"] == f"test.{Role.AMP_EG_BREAK_LEVEL.value}":
            p["calibration_source"] = sustain_id
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "al1.json").write_text(json.dumps(table))
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "sus.json").write_text(
        json.dumps(
            {
                "synth_id": "kronos2",
                "parameter_id": sustain_id,
                "feature": "sustain_level",
                "unit": "dB",
                "points": [
                    {"parameter_value": 10, "feature_value": -20},
                    {"parameter_value": 99, "feature_value": 0},
                ],
            }
        )
    )
    adsr = ts.Adsr(attack_s=0.005, decay_s=0.2, sustain=0.5, release_s=0.3, note_s=1.2)
    spec = spec_for(analyze_signal, "ad_sustain", ts.saw(adsr=adsr))
    recipe = Kronos2Adapter(
        parameter_dir=tmp_path / "p", calibration_dir=tmp_path / "c"
    ).create_recipe(spec)
    values = {s.parameter_id: s.value for s in recipe.steps}
    assert values[sustain_id] == values[f"test.{Role.AMP_EG_BREAK_LEVEL.value}"]
    assert isinstance(values[sustain_id], int)
