"""モデルのJSON保存・読み込み。"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


def save_json(model: BaseModel, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")


def load_json[M: BaseModel](model_type: type[M], path: Path) -> M:
    return model_type.model_validate_json(path.read_text(encoding="utf-8"))
