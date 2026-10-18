from synth_ai.adapters.base import CapabilityStatus
from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.core.sound_spec.models import SoundSpec


def test_nothing_is_claimed_as_supported_before_verification() -> None:
    caps = Kronos2Adapter().capabilities()
    assert caps.parameter_write is CapabilityStatus.UNVERIFIED
    assert not caps.is_supported("parameter_write")
    assert caps.available_engines == ("AL-1", "MOD-7", "HD-1")


def test_skeleton_recipe_does_not_invent_parameters(lead_spec: SoundSpec) -> None:
    recipe = Kronos2Adapter().create_recipe(lead_spec)
    assert recipe.steps == ()
    assert recipe.uncertainties
    assert "未確定事項" in Kronos2Adapter().manual_instructions(recipe)
