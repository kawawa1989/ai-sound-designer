"""テスト・ドライラン用の疑似Adapter。実機も知識ベースも使わない。"""

from __future__ import annotations

from synth_ai.adapters.base import Capabilities, CapabilityStatus
from synth_ai.core.sound_spec.models import (
    AlternativeApproach,
    PatchRecipe,
    RecipeStep,
    SoundSpec,
    StepAction,
    SynthesisMethod,
)


class FakeSynthAdapter:
    synth_id = "fake"

    def __init__(self, *, sample_import: CapabilityStatus = CapabilityStatus.UNSUPPORTED) -> None:
        self._capabilities = Capabilities(
            synth_id=self.synth_id,
            display_name="Fake Synth",
            user_sample_import=sample_import,
            midi_notes=CapabilityStatus.UNSUPPORTED,
            parameter_read=CapabilityStatus.UNSUPPORTED,
            parameter_write=CapabilityStatus.UNSUPPORTED,
            adjustment_suggestions=CapabilityStatus.UNSUPPORTED,
            available_engines=("fake-sub", "fake-sampler"),
        )

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe:
        can_import = self._capabilities.is_supported("user_sample_import")
        wants_sample = any(h.method is SynthesisMethod.SAMPLE_BASED for h in spec.hypotheses)
        use_sampler = wants_sample and can_import

        steps = [
            RecipeStep(
                order=1,
                action=StepAction.SELECT,
                page="Engine",
                parameter_id="fake.engine",
                parameter="Engine",
                value="fake-sampler" if use_sampler else "fake-sub",
                reason="仮説に基づくエンジン選択",
            )
        ]
        if use_sampler:
            steps.append(
                RecipeStep(
                    order=2,
                    action=StepAction.IMPORT_SAMPLE,
                    page="Sample",
                    parameter_id="fake.sample",
                    parameter="Sample",
                    reason="元の質感を残すためにサンプルを取り込む",
                )
            )
        alternatives: tuple[AlternativeApproach, ...] = ()
        if wants_sample and not can_import:
            alternatives = (
                AlternativeApproach(
                    engine="fake-sub", summary="サンプル取り込み不可のため減算合成で近似"
                ),
            )
        return PatchRecipe(
            recipe_id=f"{spec.spec_id}-{self.synth_id}",
            sound_spec_id=spec.spec_id,
            synth_id=self.synth_id,
            engine=steps[0].value if isinstance(steps[0].value, str) else None,
            rationale="Fake adapter recipe",
            steps=tuple(steps),
            alternatives=alternatives,
        )

    def manual_instructions(self, recipe: PatchRecipe) -> str:
        lines = [f"# Fake recipe {recipe.recipe_id}"]
        lines += [
            f"{s.order}. [{s.page}] {s.parameter}: {s.value} — {s.reason}" for s in recipe.steps
        ]
        return "\n".join(lines) + "\n"
