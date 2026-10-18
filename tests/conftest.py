import pytest

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
