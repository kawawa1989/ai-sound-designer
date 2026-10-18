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
    choice: ChoiceTag | None = None  # 選択式: この タグの選択肢を選ぶ
    extreme: Literal["min", "max"] | None = None  # 数値: 最小・最大にする
    target: QuantTarget | None = None  # 数値: この音響目標に合わせる
