"""試行（参照音に対して 1 回録音して比較したもの）の記録。"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from synth_ai.core.sound_spec.models import FrozenModel


class TrialNote(FrozenModel):
    """人の評価。「目標に近いか」と「好きか」は別に記録する。"""

    closeness: int | None = Field(default=None, ge=1, le=5)  # 目標への近さ 1〜5
    preference: int | None = Field(default=None, ge=1, le=5)  # 好み 1〜5
    memo: str = ""
    changes: tuple[str, ...] = ()  # この試行で実機に加えた変更
    updated_at: str = ""


class TrialMeta(FrozenModel):
    trial: int = Field(ge=1)
    created_at: str
    recording_source: str  # 比較に使った元のファイル
    recording_sha256: str
    synth_id: str | None = None
    recipe_id: str | None = None


class TrialRecord(FrozenModel):
    """history.json の 1 行。試行ディレクトリの内容から作り直せる。"""

    trial: int
    created_at: str
    synth_id: str | None
    recipe_id: str | None
    recording_source: str
    distance_db: float
    significant_differences: int
    top_differences: tuple[str, ...]
    suggestions: tuple[str, ...]
    note: TrialNote | None = None


class History(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    reference_analysis_id: str
    trials: tuple[TrialRecord, ...] = ()
