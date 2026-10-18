"""KORG KRONOS 2（System 3.1.3）用Adapter。

Sprint 0 時点では雛形。AL-1パラメータ表（data/kronos_parameters/）と
キャリブレーション表が整うまでは具体的なパラメータ手順を生成しない。
"""

from __future__ import annotations

from synth_ai.adapters.base import Capabilities, CapabilityStatus
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec

ENGINES = ("AL-1", "MOD-7", "HD-1")


class Kronos2Adapter:
    synth_id = "kronos2"

    def capabilities(self) -> Capabilities:
        # 実機で検証するまでは unverified。未検証を対応済みに見せない。
        return Capabilities(
            synth_id=self.synth_id,
            display_name="KORG KRONOS 2 (System 3.1.3)",
            user_sample_import=CapabilityStatus.UNVERIFIED,
            midi_notes=CapabilityStatus.UNVERIFIED,
            parameter_read=CapabilityStatus.UNVERIFIED,
            parameter_write=CapabilityStatus.UNVERIFIED,
            available_engines=ENGINES,
        )

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe:
        return PatchRecipe(
            recipe_id=f"{spec.spec_id}-{self.synth_id}",
            sound_spec_id=spec.spec_id,
            synth_id=self.synth_id,
            engine=None,
            rationale="エンジン選定ルールとパラメータ表が未整備のため、具体的な手順は保留。",
            uncertainties=(
                "AL-1パラメータ表（公式Parameter Guide照合済み）が未作成",
                "パラメータ値と音響特徴の対応（キャリブレーション）が未測定",
            ),
        )

    def manual_instructions(self, recipe: PatchRecipe) -> str:
        lines = [
            f"# KRONOS 2 レシピ: {recipe.recipe_id}",
            "",
            f"- エンジン: {recipe.engine or '未決定'}",
        ]
        lines.append(f"- 理由: {recipe.rationale}")
        if recipe.steps:
            lines += ["", "## 手順", ""]
            for s in recipe.steps:
                value = "" if s.value is None else f" = {s.value}"
                ref = f"（{s.source_ref}）" if s.source_ref else ""
                lines.append(f"{s.order}. **{s.page}** › {s.parameter}{value} — {s.reason}{ref}")
        if recipe.uncertainties:
            lines += ["", "## 未確定事項", ""]
            lines += [f"- {u}" for u in recipe.uncertainties]
        return "\n".join(lines) + "\n"
