from datetime import date
from pathlib import Path

import pytest

from synth_ai.core.audio.analyze import analyze_file
from synth_ai.core.calibration.session import (
    CalibrationPlan,
    Measurement,
    NotEnoughPointsError,
    Step,
    Verdict,
    build_curve,
    curve_filename,
    measure_feature,
    run_session,
)
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import AudioAnalysis
from synth_ai.core.synthesis import test_signals as ts

PLAN = CalibrationPlan(
    synth_id="s",
    parameter_id="p.attack",
    parameter_label="Attack",
    feature=Feature.ATTACK_TIME,
    values=(0.0, 50.0, 99.0),
    conditions="test",
)
ATTACKS = {0.0: 0.005, 50.0: 0.1, 99.0: 0.4}


@pytest.fixture
def recorder(tmp_path: Path):  # type: ignore[no-untyped-def]
    calls: list[tuple[float, int]] = []

    def record(value: float, attempt: int) -> Path:
        calls.append((value, attempt))
        adsr = ts.Adsr(attack_s=ATTACKS[value], note_s=1.5)
        return ts.write_wav(tmp_path / f"{value}_{attempt}.wav", ts.saw(adsr=adsr))

    record.calls = calls  # type: ignore[attr-defined]
    return record


def analyze(path: Path) -> AudioAnalysis:
    return analyze_file(path).analysis


def test_full_session_builds_increasing_curve(recorder) -> None:  # type: ignore[no-untyped-def]
    result = run_session(PLAN, lambda i, v: Step.GO, recorder, analyze, lambda m: Verdict.ACCEPT)
    assert [m.parameter_value for m in result.points] == [0.0, 50.0, 99.0]
    curve = build_curve(result, measured_at=date(2026, 10, 25))
    assert curve.is_monotonic
    assert curve.unit == "ms" and curve.feature == "attack_time"
    assert curve.measured_at == "2026-10-25"
    values = [p.feature_value for p in curve.points]
    assert values[0] < 15 and values[2] == pytest.approx(0.8 * 400, rel=0.15)


def test_retry_skip_and_quit(recorder) -> None:  # type: ignore[no-untyped-def]
    steps = iter([Step.GO, Step.SKIP, Step.QUIT])
    verdicts = iter([Verdict.RETRY, Verdict.ACCEPT])
    result = run_session(
        PLAN, lambda i, v: next(steps), recorder, analyze, lambda m: next(verdicts)
    )
    assert recorder.calls == [(0.0, 1), (0.0, 2)]
    assert [m.parameter_value for m in result.points] == [0.0]
    assert result.skipped == [50.0]
    assert result.quit_early
    with pytest.raises(NotEnoughPointsError):
        build_curve(result)


def test_unmeasurable_feature_is_skipped(tmp_path: Path) -> None:
    plan = CalibrationPlan("s", "p", "P", Feature.SUSTAIN_LEVEL, (1.0,), "")
    pluck = ts.write_wav(tmp_path / "pluck.wav", ts.pluck())
    seen: list[Measurement] = []

    def confirm(m: Measurement) -> Verdict:
        seen.append(m)
        return Verdict.ACCEPT

    result = run_session(plan, lambda i, v: Step.GO, lambda v, a: pluck, analyze, confirm)
    assert seen[0].feature_value is None  # 撥弦音にはサステインがない
    assert result.points == [] and result.skipped == [1.0]


def test_measure_feature(tmp_path: Path) -> None:
    analysis = analyze(ts.write_wav(tmp_path / "s.wav", ts.saw()))
    assert measure_feature(analysis, Feature.HARMONIC_SLOPE) == pytest.approx(-6.0, abs=0.3)


def test_curve_filename() -> None:
    assert curve_filename("al1.amp_eg.time.attack", Feature.ATTACK_TIME) == (
        "al1.amp_eg.time.attack__attack_time.json"
    )
