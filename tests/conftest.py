from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from synth_ai.core.audio.analyze import AnalysisResult, analyze_file
from synth_ai.core.sound_spec.models import (
    EnvelopeSpec,
    Level,
    PitchTarget,
    QuantTarget,
    SoundSpec,
    Speed,
    SynthesisHypothesis,
    SynthesisMethod,
    TimbreSpec,
)
from synth_ai.core.synthesis import test_signals as ts


@pytest.fixture
def lead_spec() -> SoundSpec:
    return SoundSpec(
        spec_id="spec-001",
        reference_id="ref-001",
        pitch=PitchTarget(note="C4", f0_hz=261.6, confidence=0.9),
        timbre=TimbreSpec(
            harmonicity=Level.HIGH, brightness=Level.HIGH, brightness_decay=Speed.FAST
        ),
        envelope=EnvelopeSpec(attack=Speed.FAST, decay=Speed.MEDIUM, sustain=Level.MEDIUM),
        targets=(
            QuantTarget(feature="attack_time", value=8.0, unit="ms", tolerance=4.0, confidence=0.7),
        ),
        hypotheses=(
            SynthesisHypothesis(
                method=SynthesisMethod.SUBTRACTIVE, rationale="整数倍音", confidence=0.7
            ),
            SynthesisHypothesis(
                method=SynthesisMethod.SAMPLE_BASED, rationale="質感", confidence=0.3
            ),
        ),
    )


@pytest.fixture(scope="session")
def wav_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("wav")


@pytest.fixture(scope="session")
def analyze_signal(wav_dir: Path) -> Callable[[str, np.ndarray], AnalysisResult]:
    """信号を WAV に書き出して解析する（名前ごとにキャッシュ）。"""
    cache: dict[str, AnalysisResult] = {}

    def run(name: str, samples: np.ndarray) -> AnalysisResult:
        if name not in cache:
            cache[name] = analyze_file(ts.write_wav(wav_dir / f"{name}.wav", samples))
        return cache[name]

    return run
