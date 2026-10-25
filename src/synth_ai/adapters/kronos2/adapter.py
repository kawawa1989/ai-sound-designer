"""KORG KRONOS 2（System 3.1.3）用 Adapter。

パラメータ表（data/kronos_parameters/）とキャリブレーション表（data/kronos_calibration/）を
コンストラクタで受け取る。表がなければ具体的なパラメータ手順は出さず、
調整すべき項目と音響目標だけを不確実性として示す。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from synth_ai.adapters.base import Capabilities, CapabilityStatus, ParameterInfo
from synth_ai.adapters.kronos2.adjust import suggest_adjustments
from synth_ai.adapters.kronos2.al1 import al1_intents
from synth_ai.adapters.kronos2.engine_select import (
    AL1,
    ENGINE_DESCRIPTIONS,
    HD1,
    MOD7,
    rank_engines,
)
from synth_ai.adapters.kronos2.intents import Intent
from synth_ai.adapters.kronos2.parameters import (
    ParameterDef,
    ParameterKind,
    ParameterTable,
    load_table,
    table_path,
)
from synth_ai.adapters.kronos2.recipe import describe_intent, describe_target, render_steps
from synth_ai.adapters.kronos2.roles import CALIBRATION_FEATURES
from synth_ai.core.calibration.models import CalibrationSet
from synth_ai.core.comparison.models import AdjustmentSuggestion, Difference
from synth_ai.core.sound_spec.models import (
    AlternativeApproach,
    PatchRecipe,
    SoundSpec,
    StepStatus,
)

ENGINES = (AL1, MOD7, HD1)

# レシピ生成に対応済みのエンジン。MOD-7 / HD-1 は順位付けのみ
INTENT_BUILDERS: dict[str, Callable[[SoundSpec], list[Intent]]] = {AL1: al1_intents}

PREPARATION = (
    "テスト用に決めた Program 番号を選ぶ（既存の音色を上書きしない）",
    "対象エンジンの Program を初期状態から作る（初期化の操作は公式マニュアルに従う）",
    "エフェクトはオフ（ドライ）にして、参照音と同じ音程で確認する",
)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


class Kronos2Adapter:
    synth_id = "kronos2"

    def __init__(
        self, parameter_dir: Path | None = None, calibration_dir: Path | None = None
    ) -> None:
        self._parameter_dir = parameter_dir
        self._calibration_dir = calibration_dir

    def capabilities(self) -> Capabilities:
        # 実機で検証するまでは unverified。未検証を対応済みに見せない。
        return Capabilities(
            synth_id=self.synth_id,
            display_name="KORG KRONOS 2 (System 3.1.3)",
            user_sample_import=CapabilityStatus.UNVERIFIED,
            midi_notes=CapabilityStatus.UNVERIFIED,
            parameter_read=CapabilityStatus.UNVERIFIED,
            parameter_write=CapabilityStatus.UNVERIFIED,
            adjustment_suggestions=CapabilityStatus.SUPPORTED,  # 実機を操作しない提案のみ
            available_engines=ENGINES,
        )

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe:
        ranking = rank_engines(spec)
        chosen = next(e for e in ranking if e.engine in INTENT_BUILDERS)
        uncertainties: list[str] = []
        if ranking[0].engine != chosen.engine and ranking[0].score > chosen.score:
            top = ranking[0]
            uncertainties.append(
                f"解析上は {top.engine}（{top.score:.2f}）のほうが適している可能性がある。"
                f"{top.engine} のレシピは未対応のため、{chosen.engine} で近似する"
            )

        intents = INTENT_BUILDERS[chosen.engine](spec)
        table = load_table(self._parameter_dir, chosen.engine)
        calibrations = CalibrationSet.load(self._calibration_dir, self.synth_id)
        rendered = render_steps(intents, table, calibrations)

        if table is None:
            location = (
                _display_path(table_path(self._parameter_dir, chosen.engine))
                if self._parameter_dir
                else f"{chosen.engine} のパラメータ表"
            )
            uncertainties.append(
                f"{location} が未作成のため、具体的なパラメータ手順は保留。"
                "公式資料で確認した表ができたら、次の項目を設定する:"
            )
        elif rendered.unregistered:
            uncertainties.append("パラメータ表に役割が未登録のため、次の項目は手順にしていない:")
        uncertainties += [f"  - {describe_intent(i)}" for i in rendered.unregistered]
        uncertainties += rendered.uncertainties
        uncertainties.append("フィルターのレゾナンスは解析していないため、初期値のままにする")
        uncertainties += [f"参照音: {u}" for u in spec.uncertainties]

        return PatchRecipe(
            recipe_id=f"{spec.spec_id}-{self.synth_id}-{chosen.engine.lower().replace('-', '')}",
            sound_spec_id=spec.spec_id,
            synth_id=self.synth_id,
            engine=chosen.engine,
            rationale=chosen.summary,
            steps=tuple(rendered.steps),
            alternatives=tuple(
                AlternativeApproach(engine=e.engine, summary=e.summary, score=e.score)
                for e in ranking
                if e.engine != chosen.engine and e.score > 0
            ),
            uncertainties=tuple(uncertainties),
        )

    def suggest_adjustments(
        self,
        spec: SoundSpec,
        differences: tuple[Difference, ...],
        recipe: PatchRecipe | None,
    ) -> tuple[AdjustmentSuggestion, ...]:
        engine = recipe.engine if recipe and recipe.engine in INTENT_BUILDERS else AL1
        return suggest_adjustments(
            spec,
            differences,
            recipe,
            load_table(self._parameter_dir, engine),
            CalibrationSet.load(self._calibration_dir, self.synth_id),
        )

    def _tables(self) -> list[ParameterTable]:
        tables = (load_table(self._parameter_dir, engine) for engine in ENGINES)
        return [t for t in tables if t is not None]

    @staticmethod
    def _info(param: ParameterDef) -> ParameterInfo:
        tab = f" › {param.tab}" if param.tab else ""
        feature = next(
            (CALIBRATION_FEATURES[r] for r in param.roles if r in CALIBRATION_FEATURES), None
        )
        return ParameterInfo(
            parameter_id=param.id,
            label=f"{param.page}{tab} › {param.name}",
            min=param.min,
            max=param.max,
            is_numeric=param.kind is not ParameterKind.CHOICE,
            calibration_feature=feature,
            source_ref=param.source_ref,
        )

    def parameter_info(self, parameter_id: str) -> ParameterInfo | None:
        for table in self._tables():
            param = table.by_id(parameter_id)
            if param is not None:
                return self._info(param)
        return None

    def calibratable_parameters(self) -> tuple[ParameterInfo, ...]:
        infos = (self._info(p) for t in self._tables() for p in t.parameters)
        return tuple(i for i in infos if i.is_numeric and i.calibration_feature)

    def manual_instructions(self, recipe: PatchRecipe) -> str:
        lines = [
            f"# KRONOS 2 レシピ: {recipe.recipe_id}",
            "",
            f"- エンジン: **{recipe.engine or '未決定'}**"
            + (
                f"（{ENGINE_DESCRIPTIONS[recipe.engine]}）"
                if recipe.engine in ENGINE_DESCRIPTIONS
                else ""
            ),
            f"- 理由: {recipe.rationale}",
            "",
            "## 準備",
            "",
        ]
        lines += [f"1. {p}" for p in PREPARATION]
        if recipe.steps:
            lines += ["", "## 手順", ""]
            for s in recipe.steps:
                if s.value is not None:
                    setting = f" → **{s.value}**"
                elif s.target is not None:
                    setting = f" → 目標 {describe_target(s.target)} に合わせて調整"
                else:
                    setting = ""
                check = "" if s.status is StepStatus.VERIFIED else " ⚠ 資料で要確認"
                lines.append(f"{s.order}. **{s.page}** › {s.parameter}{setting}")
                lines.append(f"   - 理由: {s.reason}")
                lines.append(f"   - 出典: {s.source_ref or '—'}{check}")
        if recipe.alternatives:
            lines += ["", "## 他の候補", ""]
            for alt in recipe.alternatives:
                score = "" if alt.score is None else f"（スコア {alt.score:.2f}）"
                lines.append(f"- **{alt.engine}**{score}: {alt.summary}")
        if recipe.uncertainties:
            lines += ["", "## 未確定事項・注意", ""]
            lines += [u if u.startswith("  - ") else f"- {u}" for u in recipe.uncertainties]
        return "\n".join(lines) + "\n"
