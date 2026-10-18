"""全Adapterが満たすべき契約。新しいAdapterは ADAPTERS に追加する。"""

from collections.abc import Callable

import pytest

from synth_ai.adapters.base import CapabilityStatus, SynthAdapter
from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec, StepAction
from synth_ai.core.workflow.recipe import validate_recipe

ADAPTERS: dict[str, Callable[[], SynthAdapter]] = {
    "fake": FakeSynthAdapter,
    "fake-with-sampler": lambda: FakeSynthAdapter(sample_import=CapabilityStatus.SUPPORTED),
    "kronos2": Kronos2Adapter,
}


@pytest.fixture(params=sorted(ADAPTERS))
def adapter(request: pytest.FixtureRequest) -> SynthAdapter:
    return ADAPTERS[request.param]()


def test_implements_protocol(adapter: SynthAdapter) -> None:
    assert isinstance(adapter, SynthAdapter)


def test_capabilities_match_synth_id(adapter: SynthAdapter) -> None:
    caps = adapter.capabilities()
    assert caps.synth_id == adapter.synth_id
    assert caps.available_engines


def test_recipe_is_bound_to_spec_and_synth(adapter: SynthAdapter, lead_spec: SoundSpec) -> None:
    recipe = adapter.create_recipe(lead_spec)
    assert recipe.synth_id == adapter.synth_id
    assert recipe.sound_spec_id == lead_spec.spec_id
    assert recipe.schema_version == "1.0"
    validate_recipe(recipe, lead_spec, adapter)


def test_spec_is_not_modified(adapter: SynthAdapter, lead_spec: SoundSpec) -> None:
    before = lead_spec.model_dump_json()
    adapter.create_recipe(lead_spec)
    assert lead_spec.model_dump_json() == before


def test_no_sample_import_without_capability(adapter: SynthAdapter, lead_spec: SoundSpec) -> None:
    recipe = adapter.create_recipe(lead_spec)
    if not adapter.capabilities().is_supported("user_sample_import"):
        assert all(step.action is not StepAction.IMPORT_SAMPLE for step in recipe.steps)


def test_recipe_round_trips_json(adapter: SynthAdapter, lead_spec: SoundSpec) -> None:
    recipe = adapter.create_recipe(lead_spec)
    assert PatchRecipe.model_validate_json(recipe.model_dump_json()) == recipe


def test_manual_instructions_not_empty(adapter: SynthAdapter, lead_spec: SoundSpec) -> None:
    text = adapter.manual_instructions(adapter.create_recipe(lead_spec))
    assert text.strip()
