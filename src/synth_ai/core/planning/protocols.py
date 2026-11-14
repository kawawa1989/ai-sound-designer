"""レシピの組み立てが、機種別のパラメータ表に求める形。

各 Adapter のパラメータ表（pydantic のモデル）は、この Protocol を満たせばよい。
継承は要らない。
"""

from __future__ import annotations

from typing import Protocol, TypeVar


class ChoiceOption(Protocol):
    @property
    def value(self) -> str:
        """本体の表示どおりの選択肢名。"""
        ...


class RecipeParameter(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def name(self) -> str:
        """本体の表示どおりのパラメータ名。"""
        ...

    @property
    def page(self) -> str:
        """本体の画面（ページ）名。"""
        ...

    @property
    def location(self) -> str:
        """手順に書く場所（ページとその中の位置）。"""
        ...

    @property
    def is_choice(self) -> bool: ...
    @property
    def min(self) -> float | None: ...
    @property
    def max(self) -> float | None: ...
    @property
    def steps_per_octave(self) -> float | None: ...
    @property
    def source_ref(self) -> str: ...
    @property
    def verified(self) -> bool: ...
    @property
    def notes(self) -> str: ...

    def clamp(self, value: float) -> float | int:
        """範囲と刻みに合わせた、本体で設定できる値。"""
        ...

    def shift_octaves(self, value: float, octaves: float) -> float:
        """音程が octaves だけ違う参照音に合わせて、周波数を決める値をずらす。"""
        ...

    def choice_with(self, tag: str) -> ChoiceOption | None:
        """このタグが付いた選択肢。"""
        ...


P = TypeVar("P", bound=RecipeParameter)


class RecipeTable(Protocol[P]):
    def by_role(self, role: str) -> P | None:
        """レシピで使える、この役割のパラメータ。"""
        ...

    def curve_ids(self, param: P) -> tuple[str, ...]:
        """キャリブレーション曲線を探すパラメータ ID の順番。"""
        ...
