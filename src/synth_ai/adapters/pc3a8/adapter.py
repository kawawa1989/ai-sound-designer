"""Kurzweil PC3A8 用 Adapter。

PC3A8 のパラメータを読み書きする SysEx の形式は公開されていないため、このツールは音色を
変えない。レシピは、人が本体の Program Editor で設定するための手順書として出す。

レシピは基準音 1025（パラメータ表の layout）を呼び出し、そこから変える項目だけを並べる。
パラメータ表（data/pc3a8_parameters/）とキャリブレーション表（data/pc3a8_calibration/）は
コンストラクタで受け取る。表がなければ具体的な手順は出さず、調整する項目と音響目標だけを示す。
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from synth_ai.adapters.base import Capabilities, CapabilityStatus, ParameterInfo
from synth_ai.adapters.pc3a8.parameters import Layout, ParameterDef, ParameterTable, load_table
from synth_ai.core.audio.notes import hz_to_note
from synth_ai.core.calibration.models import CalibrationCurve, CalibrationSet
from synth_ai.core.comparison.models import AdjustmentSuggestion, Difference
from synth_ai.core.planning.adjust import suggest_adjustments
from synth_ai.core.planning.render import (
    describe_intent,
    describe_target,
    limitation_sections,
    pitch_shift,
    render_steps,
)
from synth_ai.core.planning.roles import CALIBRATION_FEATURES, Role
from synth_ai.core.planning.subtractive import NOISY, subtractive_intents
from synth_ai.core.sound_spec.derive import target_of
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import (
    Level,
    PatchRecipe,
    QuantTarget,
    RecipeStep,
    SampleAlternative,
    SoundSpec,
    StepAction,
    StepStatus,
)

ENGINE = "KVA"
# 設定を確かめる提案に添える、本体での確かめ方
VERIFY_MANUAL = "docs/manuals/pc3a8/run_trial.md の「確認」"

# Program Editor で設定する順番（ページ名。本文 6-12 のソフトボタン）
PAGE_ORDER = ("KEYMAP", "ALG", "DSPCTL", "DSPMOD", "ENV2", "AMPENV", "COMMON")

# 時間の目標（ms）を、秒の項目の初期値にするときの換算
TIME_UNITS = {("ms", "s"): 0.001, ("s", "s"): 1.0}


def _time_value(param: ParameterDef, target: QuantTarget) -> float | None:
    """単位がそろう時間の項目は、目標の時間をそのまま初期値にする。"""
    factor = TIME_UNITS.get((target.unit, param.unit or ""))
    return target.value * factor if factor is not None else None


def _cutoff_for(
    cutoff: ParameterDef, curve: CalibrationCurve, brightness: float, f0_hz: float | None
) -> float | None:
    """LP Frq の曲線から、この明るさ（×f0）になるカットオフ（Hz）。参照音の音程でずらす。"""
    value = curve.inverse(brightness)
    if value is None:
        return None
    shift = pitch_shift(cutoff, curve, f0_hz)
    return cutoff.shift_octaves(value, shift.octaves) if shift else value


# ENV2 Dec1 Time を「暗くなるまでの時間」から出すときの、解析の遅れ（ms）。
# 1028 で ENV2 Dec1 Time を 0.1〜3.2 s に変えて測った 6 点の、計算との差の平均（74〜89 ms、#40）。
# 解析が発音直後の明るさを最初の 100 ms の平均で取るためと考えている
FILTER_DECAY_OFFSET_MS = 80.0


def _filter_decay_seconds(
    curve: CalibrationCurve, hz_start: float, hz_end: float, target_ms: float
) -> float | None:
    """暗くなるまでの時間を target_ms にする ENV2 Dec1 Time（秒）。

    hz_start / hz_end は発音直後と終盤のカットオフ（曲線を測った C4 のときの値）。
    ENV2 は Dec1 Time をかけて 100% から 0% まで一定の速さで下がり、Depth（セント）を掛けると、
    カットオフは対数で一定の速さで下がる。暗くなるまでの時間は、明るさが発音直後と終盤の中間
    （対数）になるまでなので、LP Frq の曲線でその明るさになるカットオフが、対数で何割下がった
    ところかを求め、Dec1 Time = (目標 − 解析の遅れ) ÷ その割合 とする。
    """
    if hz_start <= hz_end or hz_end <= 0:
        return None
    middle = math.sqrt(curve.predict(hz_start) * curve.predict(hz_end))
    hz_middle = curve.inverse(middle)
    if not hz_middle:
        return None
    remaining = math.log2(max(hz_middle, hz_end) / hz_end) / math.log2(hz_start / hz_end)
    fraction = 1.0 - remaining
    if fraction <= 0:
        return None
    return max(target_ms - FILTER_DECAY_OFFSET_MS, 0.0) / fraction / 1000.0


def _initial_value_fn(
    spec: SoundSpec, table: ParameterTable | None, calibrations: CalibrationSet
) -> Callable[[ParameterDef, QuantTarget], float | None]:
    """曲線がない項目の初期値を決める関数。

    - 時間の項目: 目標の時間（ms → 秒）
    - DSPMOD の Depth（ENV2 が LP Frq を動かす量、ct）: LP Frq の曲線で、発音直後と終盤の
      明るさに当たるカットオフを求め、その差をセントにする（ENV2 は発音直後 100%、終盤 0%）
      （1028 で、ENV2 が 100% のときに Depth の分だけ上がることを確かめた。#40）
    - ENV2 Dec1 Time: LP Frq の曲線から計算する（_filter_decay_seconds）。暗くなるまでの
      時間は LP Frq と Depth でも変わるため、1028 で測った曲線（reference/）は計算の確認に使う
    """
    f0 = spec.pitch.f0_hz if spec.pitch else None
    cutoff = table.by_role(Role.FILTER_CUTOFF) if table else None
    curve = None
    if cutoff is not None:
        curve = calibrations.get(cutoff.id, Feature.BRIGHTNESS_END.value)

    def initial(param: ParameterDef, target: QuantTarget) -> float | None:
        if Role.FILTER_EG_INTENSITY.value in param.roles and param.unit == "ct":
            start = target_of(spec, Feature.BRIGHTNESS_START)
            end = target_of(spec, Feature.BRIGHTNESS_END)
            if cutoff is None or curve is None or start is None or end is None:
                return None
            hz_start = _cutoff_for(cutoff, curve, start.value, f0)
            hz_end = _cutoff_for(cutoff, curve, end.value, f0)
            if not hz_start or not hz_end:
                return None
            return 1200 * math.log2(cutoff.clamp(hz_start) / cutoff.clamp(hz_end))
        if Role.FILTER_EG_DECAY.value in param.roles and param.unit == "s" and curve is not None:
            start = target_of(spec, Feature.BRIGHTNESS_START)
            end = target_of(spec, Feature.BRIGHTNESS_END)
            if start is not None and end is not None and target.unit == "ms":
                hz_start, hz_end = curve.inverse(start.value), curve.inverse(end.value)
                seconds = (
                    _filter_decay_seconds(curve, hz_start, hz_end, target.value)
                    if hz_start and hz_end
                    else None
                )
                if seconds is not None:
                    return seconds
        return _time_value(param, target)

    return initial


def _page_rank(step: RecipeStep) -> int:
    page = step.page.split(" › ")[0]
    return PAGE_ORDER.index(page) if page in PAGE_ORDER else len(PAGE_ORDER)


def _blocks(layout: Layout) -> str:
    return " → ".join(layout.blocks)


def _preparation(layout: Layout | None) -> list[str]:
    if layout is None:
        return [
            "テスト用の Program（docs/safety.md の「テスト用の領域」）を選ぶ。"
            "既存の Program を上書きしない",
        ]
    return [
        f"Program モードで基準音 **{layout.program}** を選ぶ"
        "（設定は docs/safety.md の「基準音 1025 の設定」）",
        "**Edit** で Program Editor に入る。編集中は Program を切り替えない"
        "（保存していない編集は警告なしで消える。本文 6-3）",
        f"**KEYMAP** が {layout.keymap}、**ALG** が Algorithm {layout.algorithm}"
        f"（{_blocks(layout)}）、**AMPENV** のモードが User であることを確かめる"
        "（本文 6-22〜6-23, 6-42, 6-53）",
        "Effect モードの Master Cmpr. が Out のままか確かめる"
        "（docs/pc3a8_setup.md の「マスターエフェクト」）",
    ]


SAVE_NOTES = (
    "残す音は、空いているテスト用の ID（1026 以降）に保存する。基準音 1025 には上書きしない。"
    "保存先の ID を声に出して確かめ、docs/safety.md の「テスト用の領域」の表に追記する"
    "（本文 5-2〜5-4）",
    "残さないときは、Exit で「保存しますか」に No を選ぶ（本文 5-3）",
)


def _with_unit(value: str | float | int, param: ParameterDef | None) -> str:
    if param is None or isinstance(value, str):
        return str(value)
    text = f"{value:g} {param.unit}" if param.unit else f"{value:g}"
    if param.is_semitone_hz and value > 0:
        return f"{text}（{hz_to_note(float(value))[0]}）"  # 画面は音名と Hz
    if not param.step and not param.grid() and value not in (0, param.min, param.max):
        # 刻みを確かめていない項目は、本体で選べる値に丸められない（端と 0 は選べる）
        text += "（本体で選べるいちばん近い値）"
    return text


def _short_value(value: str | float | int, param: ParameterDef | None) -> str:
    """一覧の表に書く短い値。本体で選べる値に丸めていない値は「約」を付ける。"""
    if param is None or isinstance(value, str):
        return str(value)
    unit = f" {param.unit}" if param.unit else ""
    if param.is_semitone_hz and value > 0:
        return f"{value:g}{unit}（{hz_to_note(float(value))[0]}）"
    if not param.step and not param.grid() and value not in (0, param.min, param.max):
        return f"約 {float(value):.3g}{unit}" if abs(value) < 1000 else f"約 {value:.0f}{unit}"
    return f"{value:g}{unit}"


def _same_as_base(value: str | float | int, param: ParameterDef | None) -> bool:
    if param is None or param.base_value is None:
        return False
    if isinstance(value, str) or isinstance(param.base_value, str):
        return str(value) == str(param.base_value)
    return abs(float(value) - float(param.base_value)) < 1e-9


def _value_table(recipe: PatchRecipe, table: ParameterTable | None) -> list[str]:
    """設定する値だけを並べた表（理由と出典は「手順」に書く）。"""
    base = table.layout.program if table else "基準音"
    lines = [
        "## 設定する値",
        "",
        f"{base} から、上から順に変える。「{base.split()[0]} のまま」の項目は触らなくてよい。"
        "「約」の値は、本体で選べるいちばん近い値にする",
        "",
        "| # | ページ | 項目 | 値 |",
        "| --- | --- | --- | --- |",
    ]
    for s in recipe.steps:
        param = table.by_id(s.parameter_id) if table and s.parameter_id else None
        if s.value is not None:
            value = f"**{_short_value(s.value, param)}**"
            if _same_as_base(s.value, param):
                value = f"{_short_value(s.value, param)}（{base.split()[0]} のまま）"
        elif s.target is not None:
            value = f"目標 {describe_target(s.target)} に合わせて調整"
        else:
            value = "—"
        lines.append(f"| {s.order} | {s.page} | {s.parameter} | {value} |")
    return [*lines, ""]


INHARMONIC = (Level.VERY_LOW, Level.LOW, Level.MEDIUM)


def _limitations(spec: SoundSpec) -> list[str]:
    """基準音の配置（KVA の発振器 1 つ → LOPASS）では再現しきれない点。"""
    out = []
    if spec.timbre.harmonicity in INHARMONIC:
        out.append(
            "整数倍音以外の成分が多い。KVA の発振器 1 つでは作れないため、"
            "ノコギリ波からの近似になる"
        )
    if spec.timbre.noisiness in NOISY:
        out.append("ノイズ成分は、基準音の配置（発振器 1 つ → LOPASS）では足せない")
    return out


def _sample_alternative(spec: SoundSpec) -> SampleAlternative | None:
    """サンプルの再生が向く音でも、取り込みは提案しない（本文 E-1）。代わりにできることを示す。"""
    hypothesis = spec.sample_hypothesis
    if hypothesis is None:
        return None
    approaches = ["KVA の発振器で近似する（この手順書の手順。基準音 1025 から作る）"]
    if spec.timbre.noisiness in NOISY:
        approaches.append(
            "ノイズ成分は、別の Layer に発振器 RES NOISE（ノイズ + レゾナンス付きローパス）を置いて"
            "重ねる。1 つの Layer に発振器を複数置くと、最後の発振器の音しか聞こえない"
            "（本文 6-4, 6-54, 6-57〜6-58）。Layer を足す操作の手順書はまだない"
        )
    approaches.append(
        "ROM の Keymap（内蔵のサンプル）を音源にした Layer を使う。近い Keymap は本体で聴いて選ぶ。"
        "このツールは Keymap の一覧を持っていないので、名前は挙げない（本文 6-4）"
    )
    return SampleAlternative(
        reason=hypothesis.rationale,
        approaches=tuple(approaches),
        limitation=(
            "PC3A8 はユーザーサンプルを読み込めないため、参照音そのものは鳴らせない（本文 E-1）"
        ),
    )


class Pc3a8Adapter:
    synth_id = "pc3a8"

    def __init__(
        self, parameter_dir: Path | None = None, calibration_dir: Path | None = None
    ) -> None:
        self._parameter_dir = parameter_dir
        self._calibration_dir = calibration_dir

    def capabilities(self) -> Capabilities:
        return Capabilities(
            synth_id=self.synth_id,
            display_name="Kurzweil PC3A8 (OS 2.41)",
            # "The PC3A does not load samples"（本文 E-1）
            user_sample_import=CapabilityStatus.UNSUPPORTED,
            midi_notes=CapabilityStatus.SUPPORTED,  # 5 ピン MIDI で確認（docs/pc3a8_setup.md）
            # SysEx の形式が公開されていない（本文 A-1）。このツールは SysEx を送らない
            parameter_read=CapabilityStatus.UNVERIFIED,
            parameter_write=CapabilityStatus.UNVERIFIED,
            adjustment_suggestions=CapabilityStatus.SUPPORTED,  # 実機を操作しない提案のみ
            available_engines=(ENGINE,),
        )

    def _table(self) -> ParameterTable | None:
        return load_table(self._parameter_dir, ENGINE)

    def _calibrations(self) -> CalibrationSet:
        return CalibrationSet.load(self._calibration_dir, self.synth_id)

    def create_recipe(self, spec: SoundSpec) -> PatchRecipe:
        table = self._table()
        rendered = render_steps(
            subtractive_intents(spec),
            table,
            self._calibrations(),
            spec.pitch.f0_hz if spec.pitch else None,
            initial_value=_initial_value_fn(spec, table, self._calibrations()),
        )
        ordered = sorted(rendered.steps, key=_page_rank)
        steps = tuple(s.model_copy(update={"order": i}) for i, s in enumerate(ordered, 1))

        uncertainties: list[str] = []
        if table is None:
            uncertainties.append(
                f"{ENGINE} のパラメータ表が見つからないため、具体的なパラメータ手順は保留。"
                "次の項目を設定する:"
            )
        elif rendered.unregistered:
            uncertainties.append(
                f"基準音の配置（{_blocks(table.layout)}）に対応する項目がないため、"
                "次の項目は手順にしていない:"
            )
        uncertainties += [f"  - {describe_intent(i)}" for i in rendered.unregistered]
        uncertainties += rendered.uncertainties
        if table is not None:
            wave = table.by_role(Role.OSCILLATOR_WAVEFORM)
            if wave is not None and all(s.parameter_id != wave.id for s in steps):
                uncertainties.append(f"波形は基準音の {wave.base_value} のままにする")
            uncertainties.append(
                "ブロック 2 の LOPASS（1 ブロック）にはレゾナンスの項目がないため、"
                "レゾナンスは設定しない（本文 6-24）"
            )
        uncertainties += [f"参照音: {u}" for u in spec.uncertainties]

        rationale = "KVA の発振器・フィルター・AMPENV・ENV2 で減算合成する"
        if table is not None:
            rationale = (
                f"基準音 {table.layout.program}（{_blocks(table.layout)}）から、"
                "発振器・LOPASS・ENV2・AMPENV を変えて減算合成する"
            )
        return PatchRecipe(
            recipe_id=f"{spec.spec_id}-{self.synth_id}-{ENGINE.lower()}",
            sound_spec_id=spec.spec_id,
            synth_id=self.synth_id,
            engine=ENGINE,
            rationale=rationale,
            steps=steps,
            sample_alternative=_sample_alternative(spec),
            limitations=tuple(_limitations(spec)),
            uncertainties=tuple(uncertainties),
        )

    def suggest_adjustments(
        self,
        spec: SoundSpec,
        differences: tuple[Difference, ...],
        recipe: PatchRecipe | None,
    ) -> tuple[AdjustmentSuggestion, ...]:
        suggestions = suggest_adjustments(
            spec, differences, recipe, self._table(), self._calibrations()
        )
        # 設定を確かめる提案には、本体での確かめ方（手順書）を添える
        return tuple(
            s.model_copy(update={"reason": f"{s.reason}。確かめ方: {VERIFY_MANUAL}"})
            if s.action is StepAction.VERIFY
            else s
            for s in suggestions
        )

    @staticmethod
    def _info(param: ParameterDef) -> ParameterInfo:
        feature = next(
            (CALIBRATION_FEATURES[Role(r)] for r in param.roles if Role(r) in CALIBRATION_FEATURES),
            None,
        )
        return ParameterInfo(
            parameter_id=param.id,
            label=f"{param.location} › {param.name}",
            min=param.min,
            max=param.max,
            is_numeric=not param.is_choice,
            calibration_feature=feature,
            source_ref=param.source_ref,
            unit=param.unit,
            calibration_values=param.calibration_values,
            log_scale=param.unit == "Hz",
            cc_control=param.cc_calibration,
        )

    def parameter_info(self, parameter_id: str) -> ParameterInfo | None:
        table = self._table()
        param = table.by_id(parameter_id) if table else None
        return self._info(param) if param is not None else None

    def calibratable_parameters(self) -> tuple[ParameterInfo, ...]:
        table = self._table()
        if table is None:
            return ()
        infos = (self._info(p) for p in table.parameters if p.usable)
        return tuple(i for i in infos if i.is_numeric and i.calibration_feature)

    def manual_instructions(self, recipe: PatchRecipe) -> str:
        table = self._table()
        lines = [
            f"# PC3A8 レシピ: {recipe.recipe_id}",
            "",
            f"- エンジン: **{recipe.engine or ENGINE}**（V.A.S.T. の KVA 発振器）",
            f"- 理由: {recipe.rationale}",
            "- このツールは本体の設定を変えない。次の手順を本体の Program Editor で行う",
            "",
        ]
        if recipe.steps:
            lines += _value_table(recipe, table)
        lines += ["## 準備", ""]
        lines += [f"1. {p}" for p in _preparation(table.layout if table else None)]
        if recipe.steps:
            lines += [
                "",
                "## 手順（理由と出典）",
                "",
                "ページ（ソフトボタン）の順に設定する。"
                "ボタンが見当たらなければ **more** で切り替える（本文 6-12）。"
                "DSPCTL・DSPMOD は左の列で機能を選び、▶ でサブページに移る"
                "（本文 6-29〜6-31）",
                "",
            ]
            for s in recipe.steps:
                param = table.by_id(s.parameter_id) if table and s.parameter_id else None
                if s.value is not None:
                    setting = f" → **{_with_unit(s.value, param)}**"
                elif s.target is not None:
                    setting = f" → 目標 {describe_target(s.target)} に合わせて調整"
                else:
                    setting = ""
                check = "" if s.status is StepStatus.VERIFIED else " ⚠ 資料で要確認"
                lines.append(f"{s.order}. **{s.page}** › {s.parameter}{setting}")
                lines.append(f"   - 理由: {s.reason}")
                lines.append(f"   - 出典: {s.source_ref or '—'}{check}")
        lines += ["", "## 保存", ""]
        lines += [f"- {n}" for n in SAVE_NOTES]
        lines += limitation_sections(recipe)
        if recipe.uncertainties:
            lines += ["", "## 未確定事項・注意", ""]
            lines += [u if u.startswith("  - ") else f"- {u}" for u in recipe.uncertainties]
        return "\n".join(lines) + "\n"
