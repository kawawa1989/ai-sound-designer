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


def test_sample_suited_sound_gets_alternatives(
    adapter: Pc3a8Adapter, sample_spec: SoundSpec
) -> None:
    """取り込みは提案せず、KVA・Layer の重ね合わせ・ROM の Keymap を代わりに示す（#21）。"""
    recipe = generate_recipe(sample_spec, adapter)
    alt = recipe.sample_alternative
    assert alt is not None
    assert alt.limitation is not None and "本文 E-1" in alt.limitation
    text = "\n".join(alt.approaches)
    assert "KVA" in text and "RES NOISE" in text and "Keymap" in text
    assert "名前は挙げない" in text  # 実機で確かめていない Keymap 名は出さない
    # 再現の限界: 非整数倍音とノイズ
    assert any("整数倍音以外" in x for x in recipe.limitations)
    assert any("ノイズ成分" in x for x in recipe.limitations)
    manual = adapter.manual_instructions(recipe)
    assert "## サンプルの代わりに" in manual and "## 再現の限界" in manual
    for word in ("WAV", "インポート", "取り込"):
        assert word not in manual


def test_no_alternative_for_synth_friendly_sound(
    analyze_signal: Analyze, adapter: Pc3a8Adapter
) -> None:
    recipe = adapter.create_recipe(spec_for(analyze_signal, "lead"))
    assert recipe.sample_alternative is None and recipe.limitations == ()


def test_cutoff_curve_shifts_by_octave(adapter: Pc3a8Adapter, tmp_path: Path) -> None:
    """C4 で測った LP Frq の曲線を 1 オクターブ上の参照音に使うと、Hz は 2 倍になる。"""
    from synth_ai.core.calibration.models import CalibrationCurve, CalibrationPoint
    from synth_ai.core.sound_spec.models import PitchTarget, QuantTarget, TimbreSpec

    curve = CalibrationCurve(
        synth_id="pc3a8",
        parameter_id="kva.dspctl.lp_frq",
        feature="brightness_end",
        unit="x f0",
        reference_note="C4",
        parameter_scale="log",
        points=(
            CalibrationPoint(parameter_value=523, feature_value=2.0),
            CalibrationPoint(parameter_value=2093, feature_value=6.0),
        ),
    )
    (tmp_path / "lp.json").write_text(curve.model_dump_json())
    calibrated = Pc3a8Adapter(parameter_dir=TABLE_DIR, calibration_dir=tmp_path)

    def cutoff(note: str, f0: float) -> float:
        spec = SoundSpec(
            spec_id="s",
            reference_id="r",
            pitch=PitchTarget(note=note, f0_hz=f0, confidence=0.9),
            timbre=TimbreSpec(),
            targets=(
                QuantTarget(
                    feature="brightness_end", value=4.0, unit="x f0", tolerance=0.5, confidence=0.8
                ),
            ),
        )
        step = next(
            s for s in calibrated.create_recipe(spec).steps if s.parameter_id == "kva.dspctl.lp_frq"
        )
        assert isinstance(step.value, float | int)
        return float(step.value)

    assert cutoff("C4", 261.63) == pytest.approx(1046, rel=0.01)  # 523 と 2093 の対数の中点
    assert cutoff("C5", 523.25) == pytest.approx(2093, rel=0.01)


def test_project_curves_reproduce_base_sound() -> None:
    """data/pc3a8_calibration/ の曲線で、基準音 1025 を録って解析した値を逆引きすると、
    基準音の設定に戻る（#22 の受け入れ条件）。目標は 2026-11-14 の録音の解析結果。"""
    from synth_ai.core.sound_spec.models import (
        EnvelopeSpec,
        Level,
        PitchTarget,
        QuantTarget,
        TimbreSpec,
    )

    data = TABLE_DIR.parent
    calibrated = Pc3a8Adapter(parameter_dir=TABLE_DIR, calibration_dir=data / "pc3a8_calibration")
    measured = {
        "attack_time": (8.5, "ms"),
        "decay_time": (95.0, "ms"),
        "sustain_level": (-7.9, "dB"),
        "release_time": (21.0, "ms"),
        "brightness_end": (13.2, "x f0"),
    }
    spec = SoundSpec(
        spec_id="base-1025",
        reference_id="pc3a8_1025_c4",
        pitch=PitchTarget(note="C4", f0_hz=261.66, confidence=0.94),
        timbre=TimbreSpec(harmonicity=Level.VERY_HIGH),
        envelope=EnvelopeSpec(sustain=Level.MEDIUM),
        targets=tuple(
            QuantTarget(feature=f, value=v, unit=u, tolerance=1.0, confidence=0.9)
            for f, (v, u) in measured.items()
        ),
    )
    values = {s.parameter_id: s.value for s in calibrated.create_recipe(spec).steps}
    assert values["kva.ampenv.att1.time"] == 0
    assert values["kva.ampenv.decay.time"] == pytest.approx(0.1, abs=0.005)  # 刻みは未確認
    assert values["kva.ampenv.rel1.time"] == pytest.approx(0.06)
    assert values["kva.dspctl.lp_frq"] == pytest.approx(25088, rel=0.02)
    sustain = values["kva.ampenv.decay.level"]
    assert isinstance(sustain, float | int) and abs(sustain - 75) < 2


def test_env2_depth_from_cutoff_curve() -> None:
    """ENV2 の Depth の初期値は、LP Frq の曲線で発音直後と終盤のカットオフの差（セント）。"""
    from synth_ai.core.sound_spec.models import PitchTarget, QuantTarget, Speed, TimbreSpec

    def target(feature: str, value: float, unit: str) -> QuantTarget:
        return QuantTarget(feature=feature, value=value, unit=unit, tolerance=0.1, confidence=0.9)

    spec = SoundSpec(
        spec_id="bass",
        reference_id="r",
        pitch=PitchTarget(note="C4", f0_hz=261.63, confidence=0.9),
        timbre=TimbreSpec(brightness_decay=Speed.MEDIUM),
        targets=(
            target("brightness_start", 7.589, "x f0"),  # 曲線で 4186 Hz
            target("brightness_end", 3.304, "x f0"),  # 曲線で 523 Hz
            target("brightness_change", 0.435, "ratio"),
        ),
    )
    calibrated = Pc3a8Adapter(
        parameter_dir=TABLE_DIR, calibration_dir=TABLE_DIR.parent / "pc3a8_calibration"
    )
    steps = {s.parameter_id: s for s in calibrated.create_recipe(spec).steps}
    depth = steps["kva.dspmod.lp_frq.depth"].value
    assert isinstance(depth, float | int)
    assert depth == pytest.approx(3600, abs=30)  # 523 → 4186 Hz は 3 オクターブ
    assert steps["kva.dspctl.lp_frq"].value == 523
    # 曲線がなければ値は出さず、目標だけを示す
    plain = {
        s.parameter_id: s for s in Pc3a8Adapter(parameter_dir=TABLE_DIR).create_recipe(spec).steps
    }
    assert plain["kva.dspmod.lp_frq.depth"].value is None


def test_cc_curves_are_not_used_for_recipes() -> None:
    """CC で測った曲線（cc/）は比較用。レシピには data/pc3a8_calibration/ 直下の曲線だけを使う。"""
    from synth_ai.core.calibration.models import CalibrationSet

    directory = TABLE_DIR.parent / "pc3a8_calibration"
    curves = CalibrationSet.load(directory, "pc3a8")
    assert len(curves) == 5
    lp = curves.get("kva.dspctl.lp_frq", "brightness_end")
    assert lp is not None and "CC 14" not in lp.conditions
    cc = CalibrationSet.load(directory / "cc", "pc3a8").get("kva.dspctl.lp_frq", "brightness_end")
    assert cc is not None and "CC 14 で設定" in cc.conditions
    # 手動の曲線と 2% 以内で合う（2026-11-14）
    for p in cc.points:
        assert p.feature_value == pytest.approx(lp.predict(p.parameter_value), rel=0.02)
