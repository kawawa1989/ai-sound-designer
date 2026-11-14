"""PC3A8 のパラメータ表（data/pc3a8_parameters/<engine>.json）の型と読み込み。

表は公式 Musician's Guide と実機の画面を確認しながら人が作る。
コードは表にないパラメータを生成しない。記入方法は docs/pc3a8_parameter_table.md を参照。

KRONOS の表（adapters/kronos2/parameters.py）との違い:
- 値は物理単位（秒・%・dB・Hz・セント）の小数。KRONOS の 0〜99 の目盛りとは違う
- 音源やフィルターは「アルゴリズムのブロックに置く機能」なので、
  表は基準音（layout）の配置を前提にする
- 実機で確かめていない項目は verified: false にし、範囲が分からなければ min / max を空にできる

役割（roles）と選択肢タグは、機種共通の語彙（synth_ai.core.planning.roles）から選ぶ。
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from synth_ai.core.planning.roles import ChoiceTag, Role

# 表に書ける役割と選択肢のタグ（機種共通の語彙）
ROLES: frozenset[str] = frozenset(r.value for r in Role)
CHOICE_TAGS: frozenset[str] = frozenset(t.value for t in ChoiceTag)


class ParameterKind(StrEnum):
    INT = "int"
    FLOAT = "float"
    CHOICE = "choice"


class Choice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    value: str  # 本体の表示どおりの選択肢名
    tags: tuple[str, ...] = ()

    @field_validator("tags")
    @classmethod
    def _known_tags(cls, tags: tuple[str, ...]) -> tuple[str, ...]:
        unknown = sorted(set(tags) - CHOICE_TAGS)
        if unknown:
            raise ValueError(f"unknown choice tags: {unknown}")
        return tags


class StepRange(BaseModel):
    """start から end まで step 刻みの値（両端を含む）。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: float
    end: float
    step: float = Field(gt=0)

    @model_validator(mode="after")
    def _check(self) -> StepRange:
        if self.start >= self.end:
            raise ValueError("step range needs start < end")
        return self

    def values(self) -> list[float]:
        count = int(round((self.end - self.start) / self.step))
        return [round(self.start + i * self.step, 6) for i in range(count + 1)]


class ParameterDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str  # 表の中で一意な ID（例: "kva.ampenv.decay.time"）
    page: str  # Program Editor のページ名（例: "AMPENV"）
    section: str | None = None  # ページ内の位置（例: "Decay"、"ブロック 2"）
    name: str  # 本体の表示どおりのパラメータ名
    kind: ParameterKind
    min: float | None = None
    max: float | None = None
    step: float | None = Field(default=None, gt=0)
    # 刻みが一定でない値（AMPENV の時間など）。実機で確かめた範囲だけを書く
    values: tuple[float, ...] = ()  # 個別の値（例: 0, 0.002, 0.005, 0.01）
    step_ranges: tuple[StepRange, ...] = ()  # 一定の刻みの区間
    default: float | str | None = None  # Program 999 Default Program での値（分かる場合）
    base_value: float | str | None = None  # 基準音（layout の Program）での値
    unit: str | None = None  # "s"、"%"、"dB"、"Hz"、"ct" など
    # 値の 1 段が周波数で何分の 1 オクターブか（Hz の刻みが半音なら 12）
    steps_per_octave: float | None = Field(default=None, gt=0)
    # キャリブレーションで測る値（本体で選べる値。docs/manuals/pc3a8/calibrate.md）
    calibration_values: tuple[float, ...] = ()
    choices: tuple[Choice, ...] = ()
    roles: tuple[str, ...] = ()
    source_ref: str  # 例: "Musician's Guide 本文 6-43"、"実機の画面で確認（2026-11-14）"
    verified: bool = False  # 範囲・名前を公式資料か実機で確かめたら true
    notes: str = ""

    @field_validator("roles")
    @classmethod
    def _known_roles(cls, roles: tuple[str, ...]) -> tuple[str, ...]:
        unknown = sorted(set(roles) - ROLES)
        if unknown:
            raise ValueError(f"unknown roles: {unknown}")
        return roles

    @model_validator(mode="after")
    def _check_kind(self) -> ParameterDef:
        if self.kind is ParameterKind.CHOICE:
            if not self.choices:
                raise ValueError(f"{self.id}: choice parameter needs choices")
            names = [c.value for c in self.choices]
            for value in (self.default, self.base_value):
                if isinstance(value, str) and value not in names:
                    raise ValueError(f"{self.id}: {value!r} is not a choice")
            return self
        if self.min is None or self.max is None:
            if self.verified:
                raise ValueError(f"{self.id}: verified numeric parameter needs min and max")
            return self
        if self.min >= self.max:
            raise ValueError(f"{self.id}: numeric parameter needs min < max")
        for value in (self.default, self.base_value, *self.values):
            if isinstance(value, int | float) and not self.min <= value <= self.max:
                raise ValueError(f"{self.id}: {value} is out of range")
        for r in self.step_ranges:
            if not self.min <= r.start < r.end <= self.max:
                raise ValueError(f"{self.id}: step range {r.start}..{r.end} is out of range")
        if self.step and self.grid():
            raise ValueError(f"{self.id}: use either step or values/step_ranges")
        for value in self.calibration_values:
            if not self.min <= value <= self.max:
                raise ValueError(f"{self.id}: calibration value {value} is out of range")
            if (self.step or self.grid()) and abs(self.clamp(value) - value) > 1e-9:
                raise ValueError(f"{self.id}: calibration value {value} cannot be set")
        if len(set(self.calibration_values)) != len(self.calibration_values):
            raise ValueError(f"{self.id}: calibration values are duplicated")
        return self

    def grid(self) -> tuple[float, ...]:
        """values と step_ranges から作る、本体で選べる値の一覧（昇順）。"""
        points = set(self.values)
        for r in self.step_ranges:
            points.update(r.values())
        return tuple(sorted(points))

    @property
    def usable(self) -> bool:
        """レシピで使えるか（確かめた値で、範囲が分かっている）。"""
        if not self.verified:
            return False
        return self.kind is ParameterKind.CHOICE or (self.min is not None and self.max is not None)

    def clamp(self, value: float) -> float | int:
        if self.min is None or self.max is None:
            raise ValueError(f"{self.id}: range is unknown")
        value = min(max(value, self.min), self.max)
        grid = self.grid()
        if grid and grid[0] <= value <= grid[-1]:
            # 確かめた範囲では、本体で選べるいちばん近い値にする
            return min(grid, key=lambda g: (abs(g - value), g))
        if self.step:
            value = self.min + round((value - self.min) / self.step) * self.step
            if value > self.max:
                value -= self.step
        return int(round(value)) if self.kind is ParameterKind.INT else round(value, 4)

    @property
    def is_choice(self) -> bool:
        return self.kind is ParameterKind.CHOICE

    @property
    def location(self) -> str:
        return self.page if self.section is None else f"{self.page} › {self.section}"

    def shift_octaves(self, value: float, octaves: float) -> float:
        """Hz の値は 1 オクターブで 2 倍。それ以外は steps_per_octave 段ずつ変わる。"""
        if self.unit == "Hz":
            return float(value * 2.0**octaves)
        return value + (self.steps_per_octave or 0.0) * octaves

    def choice_with(self, tag: str) -> Choice | None:
        return next((c for c in self.choices if tag in c.tags), None)


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    version: str = ""
    notes: str = ""


class Layout(BaseModel):
    """表が前提にする基準音の配置（アルゴリズムとブロック）。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    program: str  # 例: "1025 KVA BASIC SAW"
    keymap: str  # 例: "999 Silence"
    algorithm: int
    blocks: tuple[str, ...]  # ブロックの機能（例: ("SAW", "LOPASS", "NONE")）
    notes: str = ""


class ParameterTable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    synth_id: Literal["pc3a8"] = "pc3a8"
    engine: str
    source: SourceDocument
    layout: Layout
    parameters: tuple[ParameterDef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_ids(self) -> ParameterTable:
        ids = [p.id for p in self.parameters]
        duplicated = sorted({i for i in ids if ids.count(i) > 1})
        if duplicated:
            raise ValueError(f"duplicated parameter ids: {duplicated}")
        return self

    def by_role(self, role: str, usable_only: bool = True) -> ParameterDef | None:
        """役割を担うパラメータ。usable_only なら、レシピで使えるものだけ。"""
        return next(
            (p for p in self.parameters if role in p.roles and (p.usable or not usable_only)),
            None,
        )

    def curve_ids(self, param: ParameterDef) -> tuple[str, ...]:
        """キャリブレーション曲線を探す ID（このパラメータ自身の曲線だけ）。"""
        return (param.id,)

    def by_id(self, parameter_id: str) -> ParameterDef | None:
        return next((p for p in self.parameters if p.id == parameter_id), None)

    def unverified(self) -> tuple[ParameterDef, ...]:
        return tuple(p for p in self.parameters if not p.usable)


def table_path(directory: Path, engine: str) -> Path:
    return directory / f"{engine.lower().replace('-', '')}.json"


def load_table(directory: Path | None, engine: str) -> ParameterTable | None:
    """directory/<engine>.json（例: kva.json）を読む。ファイルがなければ None。"""
    if directory is None:
        return None
    path = table_path(directory, engine)
    if not path.is_file():
        return None
    table = ParameterTable.model_validate_json(path.read_text(encoding="utf-8"))
    if table.engine != engine:
        raise ValueError(f"{path}: engine is {table.engine!r}, expected {engine!r}")
    return table
