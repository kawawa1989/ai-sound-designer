"""SoundSpec から注入された Adapter でレシピを作るユースケース。"""

from __future__ import annotations

from synth_ai.adapters.base import SynthAdapter
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec, StepAction


class RecipeContractError(RuntimeError):
    """Adapter が契約に反するレシピを返した。"""


def generate_recipe(spec: SoundSpec, adapter: SynthAdapter) -> PatchRecipe:
    recipe = adapter.create_recipe(spec)
    validate_recipe(recipe, spec, adapter)
    return recipe


def validate_recipe(recipe: PatchRecipe, spec: SoundSpec, adapter: SynthAdapter) -> None:
    if recipe.synth_id != adapter.synth_id:
        raise RecipeContractError(
            f"recipe.synth_id={recipe.synth_id!r} does not match adapter {adapter.synth_id!r}"
        )
    if recipe.sound_spec_id != spec.spec_id:
        raise RecipeContractError(
            f"recipe.sound_spec_id={recipe.sound_spec_id!r} does not match spec {spec.spec_id!r}"
        )
    orders = [step.order for step in recipe.steps]
    if orders != list(range(1, len(orders) + 1)):
        raise RecipeContractError(f"step order must be 1..n without gaps, got {orders}")

    capabilities = adapter.capabilities()
    if not capabilities.is_supported("user_sample_import") and any(
        step.action is StepAction.IMPORT_SAMPLE for step in recipe.steps
    ):
        raise RecipeContractError(
            "recipe proposes sample import on a synth that does not support it"
        )
    if recipe.engine is not None and recipe.engine not in capabilities.available_engines:
        raise RecipeContractError(f"engine {recipe.engine!r} is not in available_engines")
    vague = [
        step.order
        for step in recipe.steps
        if step.action in (StepAction.SET, StepAction.SELECT)
        and step.value is None
        and step.target is None
    ]
    if vague:
        raise RecipeContractError(f"steps {vague} have neither a value nor an acoustic target")
