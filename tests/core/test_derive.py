"""AudioAnalysis → SoundSpec の変換を、正解の分かる合成音で確かめる。"""

from collections.abc import Callable

import numpy as np
import pytest

from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.sound_spec.derive import derive_sound_spec, target_of
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import Level, SoundSpec, Speed, SynthesisMethod
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.synthesis.test_signals import Adsr

Analyze = Callable[[str, np.ndarray], AnalysisResult]


def spec_of(analyze_signal: Analyze, name: str, samples: np.ndarray) -> SoundSpec:
    return derive_sound_spec(analyze_signal(name, samples).analysis)


def top_method(spec: SoundSpec) -> SynthesisMethod:
    return spec.hypotheses[0].method


def test_sustained_saw(analyze_signal: Analyze) -> None:
    adsr = Adsr(attack_s=0.005, decay_s=0.2, sustain=0.5, release_s=0.3, note_s=1.2)
    spec = spec_of(analyze_signal, "spec_saw", ts.saw(adsr=adsr))
    assert spec.timbre.harmonicity is Level.VERY_HIGH
    assert spec.timbre.brightness_decay is None
    assert spec.envelope.attack is Speed.FAST
    assert spec.envelope.sustain is Level.MEDIUM
    assert top_method(spec) is SynthesisMethod.SUBTRACTIVE
    slope = target_of(spec, Feature.HARMONIC_SLOPE)
    assert slope is not None and slope.value == pytest.approx(-6.02, abs=0.3)
    sustain = target_of(spec, Feature.SUSTAIN_LEVEL)
    assert sustain is not None and sustain.value == pytest.approx(-6.0, abs=1.0)
    assert sustain.unit == "dB"


def test_ids_link_back_to_analysis(analyze_signal: Analyze) -> None:
    result = analyze_signal("spec_saw_ids", ts.saw())
    spec = derive_sound_spec(result.analysis)
    assert spec.reference_id == result.analysis.analysis_id
    assert spec.analysis_id == result.analysis.analysis_id
    assert spec.spec_id == f"{result.analysis.analysis_id}-spec"
    assert derive_sound_spec(result.analysis, "custom").spec_id == "custom"


def test_filter_sweep_darkens(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_sweep", ts.saw_filter_sweep())
    assert spec.timbre.brightness_decay is Speed.FAST
    decay = target_of(spec, Feature.BRIGHTNESS_DECAY_TIME)
    assert decay is not None and 300 < decay.value < 1500
    start, end = target_of(spec, Feature.BRIGHTNESS_START), target_of(spec, Feature.BRIGHTNESS_END)
    assert start is not None and end is not None and end.value < start.value / 3


def test_square_is_odd_only(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_square", ts.square())
    odd_even = target_of(spec, Feature.ODD_EVEN_RATIO)
    assert odd_even is not None and odd_even.value > 40
    slope = target_of(spec, Feature.HARMONIC_SLOPE)
    assert slope is not None and slope.value == pytest.approx(-6.0, abs=0.5)


def test_fm_bell_is_fm(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_bell", ts.fm_bell())
    assert top_method(spec) is SynthesisMethod.FM
    assert spec.envelope.sustain is Level.VERY_LOW
    assert any("リリース" in u for u in spec.uncertainties)


def test_pluck_has_physical_hypothesis(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_pluck", ts.pluck())
    methods = {h.method for h in spec.hypotheses}
    assert SynthesisMethod.PHYSICAL_MODEL in methods
    assert target_of(spec, Feature.SUSTAIN_LEVEL) is None


def test_chord_is_not_confidently_subtractive(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_chord", ts.chord())
    assert top_method(spec) is SynthesisMethod.SAMPLE_BASED
    assert any("ピッチ" in u for u in spec.uncertainties)


def test_targets_have_units_and_tolerances(analyze_signal: Analyze) -> None:
    spec = spec_of(analyze_signal, "spec_saw", ts.saw())
    features = {t.feature for t in spec.targets}
    assert {Feature.ATTACK_TIME, Feature.BRIGHTNESS, Feature.HARMONICITY} <= features
    assert all(t.unit and t.tolerance >= 0 for t in spec.targets)


def test_deterministic(analyze_signal: Analyze) -> None:
    analysis = analyze_signal("spec_saw", ts.saw()).analysis
    assert derive_sound_spec(analysis) == derive_sound_spec(analysis)
