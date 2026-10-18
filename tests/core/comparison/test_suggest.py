from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.core.comparison.models import (
    AdjustmentSuggestion,
    Difference,
    DifferenceKind,
    Segment,
)
from synth_ai.core.comparison.suggest import generic_suggestions, suggest
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec


def fdiff(feature: str, ref: float, rec: float, severity: float) -> Difference:
    return Difference(
        kind=DifferenceKind.FEATURE,
        feature=feature,
        reference=ref,
        recording=rec,
        delta=rec - ref,
        unit="u",
        severity=severity,
        message=f"{feature} differs",
    )


DIFFS = (
    fdiff("brightness_end", 2.5, 30.0, 50.0),
    fdiff("harmonic_slope", -20.0, -6.0, 9.0),  # brightness_end と同じグループ
    fdiff("attack_time", 8.0, 60.0, 12.0),
    fdiff("release_time", 300.0, 250.0, 0.5),  # 有意でない
    fdiff("noisiness", 0.001, 0.05, 3.0),
    fdiff("sustain_level", -4.0, -10.0, 2.0),
)


def test_generic_suggestions_pick_top_groups() -> None:
    out = generic_suggestions(DIFFS)
    assert [s.feature for s in out] == ["brightness_end", "attack_time", "noisiness"]
    assert out[0].message.startswith("持続部を暗くする")
    assert out[1].message.startswith("立ち上がりを速くする")
    assert [s.priority for s in out] == [1, 2, 3]
    assert all(s.parameter_id is None for s in out)


def test_band_fallback_when_no_feature_differs() -> None:
    band = Difference(
        kind=DifferenceKind.BAND,
        segment=Segment.ATTACK,
        band="4k-10k",
        reference=-20,
        recording=-10,
        delta=10,
        unit="dB",
        severity=3.3,
        message="band",
    )
    out = generic_suggestions((band,))
    assert len(out) == 1 and "弱める" in out[0].message


def test_no_suggestions_without_significant_differences() -> None:
    assert generic_suggestions((fdiff("attack_time", 8, 9, 0.3),)) == ()


class Advisor(FakeSynthAdapter):
    def __init__(self, supported: bool) -> None:
        from synth_ai.adapters.base import CapabilityStatus

        super().__init__()
        status = CapabilityStatus.SUPPORTED if supported else CapabilityStatus.UNVERIFIED
        self._capabilities = self._capabilities.model_copy(
            update={"adjustment_suggestions": status}
        )

    def suggest_adjustments(
        self, spec: SoundSpec, differences: tuple[Difference, ...], recipe: PatchRecipe | None
    ) -> tuple[AdjustmentSuggestion, ...]:
        return tuple(AdjustmentSuggestion(priority=9, message=f"advisor {i}") for i in range(5))


def test_advisor_used_only_when_supported(lead_spec: SoundSpec) -> None:
    used = suggest(lead_spec, DIFFS, None, Advisor(supported=True))
    assert [s.message for s in used] == ["advisor 0", "advisor 1", "advisor 2"]
    assert [s.priority for s in used] == [1, 2, 3]
    fallback = suggest(lead_spec, DIFFS, None, Advisor(supported=False))
    assert fallback[0].feature == "brightness_end"
    assert suggest(lead_spec, DIFFS, None, FakeSynthAdapter())[0].feature == "brightness_end"
    assert suggest(lead_spec, DIFFS, None, None)[0].feature == "brightness_end"
