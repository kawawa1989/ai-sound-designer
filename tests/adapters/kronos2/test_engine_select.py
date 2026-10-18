from collections.abc import Callable

import numpy as np

from synth_ai.adapters.kronos2.engine_select import AL1, HD1, MOD7, rank_engines
from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.sound_spec.derive import derive_sound_spec
from synth_ai.core.synthesis import test_signals as ts

Analyze = Callable[[str, np.ndarray], AnalysisResult]


def ranking(analyze_signal: Analyze, name: str, samples: np.ndarray) -> list[str]:
    spec = derive_sound_spec(analyze_signal(name, samples).analysis)
    return [e.engine for e in rank_engines(spec)]


def test_harmonic_sounds_prefer_al1(analyze_signal: Analyze) -> None:
    assert ranking(analyze_signal, "eng_saw", ts.saw())[0] == AL1
    assert ranking(analyze_signal, "eng_sweep", ts.saw_filter_sweep())[0] == AL1
    assert ranking(analyze_signal, "eng_pluck", ts.pluck())[0] == AL1


def test_inharmonic_bell_prefers_mod7(analyze_signal: Analyze) -> None:
    assert ranking(analyze_signal, "eng_bell", ts.fm_bell())[0] == MOD7


def test_chord_prefers_sample_playback(analyze_signal: Analyze) -> None:
    assert ranking(analyze_signal, "eng_chord", ts.chord())[0] == HD1


def test_scores_and_reasons(analyze_signal: Analyze) -> None:
    spec = derive_sound_spec(analyze_signal("eng_saw", ts.saw()).analysis)
    scores = rank_engines(spec)
    assert {e.engine for e in scores} == {AL1, MOD7, HD1}
    assert all(0 <= e.score <= 1 and e.reasons for e in scores)
    assert scores == sorted(scores, key=lambda e: e.score, reverse=True)
