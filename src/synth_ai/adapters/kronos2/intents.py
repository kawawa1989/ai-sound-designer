"""レシピの中間表現。「どの役割のパラメータを、どの音響目標に向けて動かすか」。

パラメータ表とキャリブレーション表を引く前の段階なので、KRONOS の具体的な
パラメータ名・値は含まない。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from synth_ai.adapters.kronos2.roles import ChoiceTag, Role
from synth_ai.core.sound_spec.models import QuantTarget, StepAction


@dataclass(frozen=True)
class Intent:
    role: Role
    action: StepAction
    reason: str
    choice: ChoiceTag | None = None  # 選択式: このタグの選択肢を選ぶ
    # 数値: 最小・最大にする。zero は「効果なし」の 0（範囲に 0 がなければ最小）
    extreme: Literal["min", "max", "zero"] | None = None
    target: QuantTarget | None = None  # 数値: この音響目標に合わせる
    # True なら、パラメータ表にこの役割がなくても未登録として報告しない
    # （多段 EG のレベルなど、機種によっては存在しない項目）
    optional: bool = False
