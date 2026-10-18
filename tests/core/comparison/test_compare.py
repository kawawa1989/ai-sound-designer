"""揃え方と差分計算を、違いが分かっている合成音の組で確かめる。"""

from collections.abc import Callable

import numpy as np
import pytest

from synth_ai.core.audio.analyze import AnalysisResult
from synth_ai.core.comparison.align import align
from synth_ai.core.comparison.compare import compute_differences, spectral_distance
from synth_ai.core.comparison.models import Difference, DifferenceKind, Segment
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.synthesis.test_signals import Adsr

Analyze = Callable[[str, np.ndarray], AnalysisResult]
REF = ts.with_silence(ts.saw_filter_sweep(), 0.1, 0.2)


def feature(diffs: list[Difference], name: str) -> Difference:
    return next(d for d in diffs if d.kind is DifferenceKind.FEATURE and d.feature == name)


def run(analyze_signal: Analyze, name: str, samples: np.ndarray) -> tuple[object, list[Difference]]:
    ref = analyze_signal("cmp_ref", REF)
    rec = analyze_signal(name, samples)
    pair = align(ref, rec)
    return pair, compute_differences(pair, ref, rec)


def test_identical_sound_has_no_differences(analyze_signal: Analyze) -> None:
    pair, diffs = run(
        analyze_signal, "cmp_same", ts.with_silence(0.5 * ts.saw_filter_sweep(), 0.3, 0.1)
    )
    assert pair.alignment.gain_db == pytest.approx(6.02, abs=0.1)  # type: ignore[attr-defined]
    assert pair.alignment.pitch_offset_cents == pytest.approx(0.0, abs=0.5)  # type: ignore[attr-defined]
    assert all(d.severity < 1.0 for d in diffs)
    assert spectral_distance(pair).mean_db < 0.5  # type: ignore[arg-type]


def test_alignment_reports_detune(analyze_signal: Analyze) -> None:
    detuned = ts.with_silence(ts.saw_filter_sweep(f0=130.81 * 2 ** (20 / 1200)), 0.1, 0.2)
    pair, _ = run(analyze_signal, "cmp_detune", detuned)
    assert pair.alignment.pitch_offset_cents == pytest.approx(20.0, abs=1.0)  # type: ignore[attr-defined]


def test_slow_attack_is_found(analyze_signal: Analyze) -> None:
    slow = ts.with_silence(ts.saw_filter_sweep(adsr=Adsr(attack_s=0.1, note_s=1.5)), 0.1, 0.2)
    _, diffs = run(analyze_signal, "cmp_slow", slow)
    attack = feature(diffs, "attack_time")
    assert attack.delta > 0 and attack.severity >= 1
    assert attack.message.startswith("アタックが遅い")
    envelope = next(
        d for d in diffs if d.kind is DifferenceKind.ENVELOPE and d.segment is Segment.ATTACK
    )
    assert envelope.delta < -3


def test_unfiltered_saw_is_too_bright(analyze_signal: Analyze) -> None:
    bright = ts.with_silence(ts.saw(130.81, adsr=Adsr(note_s=1.5)), 0.1, 0.2)
    _, diffs = run(analyze_signal, "cmp_bright", bright)
    assert diffs[0].severity > 5
    end = feature(diffs, "brightness_end")
    assert end.delta > 0 and "持続部が明るい" in end.message
    change = feature(diffs, "brightness_change")
    assert change.delta > 0 and "暗くなり方が弱い" in change.message
    high_tail = [
        d
        for d in diffs
        if d.kind is DifferenceKind.BAND
        and d.segment is Segment.TAIL
        and d.band in ("4k-10k", ">10k")
    ]
    assert high_tail and all(d.delta > 10 for d in high_tail)


def test_differences_sorted_by_severity(analyze_signal: Analyze) -> None:
    bright = ts.with_silence(ts.saw(130.81, adsr=Adsr(note_s=1.5)), 0.1, 0.2)
    _, diffs = run(analyze_signal, "cmp_bright", bright)
    severities = [d.severity for d in diffs]
    assert severities == sorted(severities, reverse=True)
