"""Core のワークフローは FakeSynthAdapter だけでテストする。"""

import pytest

from synth_ai.adapters.base import CapabilityStatus
from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec, StepAction
from synth_ai.core.workflow.recipe import RecipeContractError, generate_recipe


def test_generate_recipe_with_injected_adapter(lead_spec: SoundSpec) -> None:
    recipe = generate_recipe(lead_spec, FakeSynthAdapter())
    assert recipe.synth_id == "fake"
    assert recipe.engine == "fake-sub"
    assert recipe.alternatives  # サンプル不可の代替案を説明している


def test_sample_import_used_only_when_supported(lead_spec: SoundSpec) -> None:
    recipe = generate_recipe(lead_spec, FakeSynthAdapter(sample_import=CapabilityStatus.SUPPORTED))
    assert any(s.action is StepAction.IMPORT_SAMPLE for s in recipe.steps)


def test_unverified_capability_is_not_supported(lead_spec: SoundSpec) -> None:
    recipe = generate_recipe(lead_spec, FakeSynthAdapter(sample_import=CapabilityStatus.UNVERIFIED))
    assert all(s.action is not StepAction.IMPORT_SAMPLE for s in recipe.steps)


class _BrokenAdapter(FakeSynthAdapter):
    def __init__(self, recipe_update: dict[str, object]) -> None:
        super().__init__()
        self._update = recipe_update

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe:
        return super().create_recipe(spec).model_copy(update=self._update)


@pytest.mark.parametrize(
    "update",
    [
        {"synth_id": "other"},
        {"sound_spec_id": "other"},
        {"engine": "not-an-engine"},
    ],
)
def test_contract_violations_are_rejected(lead_spec: SoundSpec, update: dict[str, object]) -> None:
    with pytest.raises(RecipeContractError):
        generate_recipe(lead_spec, _BrokenAdapter(update))


def test_sample_import_on_unsupported_synth_is_rejected(lead_spec: SoundSpec) -> None:
    sampler = FakeSynthAdapter(sample_import=CapabilityStatus.SUPPORTED)
    steps = sampler.create_recipe(lead_spec).steps
    with pytest.raises(RecipeContractError):
        generate_recipe(lead_spec, _BrokenAdapter({"steps": steps}))
