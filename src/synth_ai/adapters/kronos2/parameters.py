"""KRONOS 2 のパラメータ表（data/kronos_parameters/<engine>.json）の型と読み込み。

表は公式 Parameter Guide を確認しながら人が作る。コードは表にないパラメータを生成しない。
記入方法は docs/kronos_parameter_table.md を参照。
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from synth_ai.adapters.kronos2.roles import ChoiceTag, Role


class ParameterKind(StrEnum):
    INT = "int"
    FLOAT = "float"
    CHOICE = "choice"


class Choice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    value: str  # 本体の表示どおりの選択肢名
    tags: tuple[ChoiceTag, ...] = ()


class ParameterDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str  # 表の中で一意な ID（例: "al1.<ページ>.<名前>"）
    page: str  # 本体の画面（ページ）名
    tab: str | None = None
    name: str  # 本体の表示どおりのパラメータ名
    kind: ParameterKind
    min: float | None = None
    max: float | None = None
    step: float | None = None
    default: float | str | None = None  # 初期化した Program での値（分かる場合）
    unit: str | None = None
    choices: tuple[Choice, ...] = ()
    roles: tuple[Role, ...] = ()
    source_ref: str  # 公式資料の該当箇所（例: "Parameter Guide p.123"）
    verified: bool = False  # 公式資料と照合済みなら true
    notes: str = ""

    @model_validator(mode="after")
    def _check_kind(self) -> ParameterDef:
        if self.kind is ParameterKind.CHOICE:
            if not self.choices:
                raise ValueError(f"{self.id}: choice parameter needs choices")
        else:
            if self.min is None or self.max is None or self.min >= self.max:
                raise ValueError(f"{self.id}: numeric parameter needs min < max")
            if isinstance(self.default, int | float) and not self.min <= self.default <= self.max:
                raise ValueError(f"{self.id}: default is out of range")
        return self

    def clamp(self, value: float) -> float | int:
        assert self.min is not None and self.max is not None
        value = min(max(value, self.min), self.max)
        if self.step:
            value = self.min + round((value - self.min) / self.step) * self.step
            if value > self.max:  # 刻みに丸めた結果が上限を超えたら 1 刻み戻す
                value -= self.step
        return int(round(value)) if self.kind is ParameterKind.INT else round(value, 4)

    def choice_with(self, tag: ChoiceTag) -> Choice | None:
        return next((c for c in self.choices if tag in c.tags), None)


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str  # 例: "KRONOS Parameter Guide"
    version: str = ""
    notes: str = ""


class ParameterTable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    synth_id: Literal["kronos2"] = "kronos2"
    engine: str
    source: SourceDocument
    parameters: tuple[ParameterDef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_ids(self) -> ParameterTable:
        ids = [p.id for p in self.parameters]
        duplicated = sorted({i for i in ids if ids.count(i) > 1})
        if duplicated:
            raise ValueError(f"duplicated parameter ids: {duplicated}")
        return self

    def by_role(self, role: Role) -> ParameterDef | None:
        """役割を担うパラメータ。複数あれば表の先頭のもの。"""
        return next((p for p in self.parameters if role in p.roles), None)

    def by_id(self, parameter_id: str) -> ParameterDef | None:
        return next((p for p in self.parameters if p.id == parameter_id), None)


def table_path(directory: Path, engine: str) -> Path:
    return directory / f"{engine.lower().replace('-', '')}.json"


def load_table(directory: Path | None, engine: str) -> ParameterTable | None:
    """directory/<engine>.json（例: al1.json）を読む。ファイルがなければ None。"""
    if directory is None:
        return None
    path = table_path(directory, engine)
    if not path.is_file():
        return None
    table = ParameterTable.model_validate_json(path.read_text(encoding="utf-8"))
    if table.engine != engine:
        raise ValueError(f"{path}: engine is {table.engine!r}, expected {engine!r}")
    return table
