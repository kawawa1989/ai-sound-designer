"""キャリブレーション表: 実機のパラメータ値と、録音から測った音響特徴の対応。

テスト用の音色で 1 つのパラメータだけを数段階変えて録音・解析し、
「この値にするとアタックが何 ms になるか」を記録する。レシピは目標値から逆引きする。
機種・パラメータは文字列 ID で扱い、Core は個別の機種を知らない。
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalibrationPoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter_value: float
    feature_value: float


class CalibrationCurve(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    synth_id: str
    parameter_id: str
    feature: str  # synth_ai.core.sound_spec.features.Feature の値
    unit: str
    conditions: str = ""  # 測定条件（他のパラメータの設定、音程など）
    measured_at: str = ""  # 測定日（YYYY-MM-DD）
    # 測定した音の音名（例: "C4"）。×f0 のように音程で意味が変わる特徴の補正に使う
    reference_note: str | None = None
    points: tuple[CalibrationPoint, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def _distinct_parameter_values(self) -> CalibrationCurve:
        values = [p.parameter_value for p in self.points]
        if len(set(values)) != len(values):
            raise ValueError("parameter_value must be unique within a curve")
        return self

    def _sorted(self) -> tuple[np.ndarray, np.ndarray]:
        pts = sorted(self.points, key=lambda p: p.parameter_value)
        return (
            np.array([p.parameter_value for p in pts]),
            np.array([p.feature_value for p in pts]),
        )

    @property
    def is_monotonic(self) -> bool:
        _, y = self._sorted()
        d = np.diff(y)
        return bool(np.all(d > 0) or np.all(d < 0))

    @property
    def feature_range(self) -> tuple[float, float]:
        _, y = self._sorted()
        return float(y.min()), float(y.max())

    def predict(self, parameter_value: float) -> float:
        """パラメータ値から特徴値を推定する（測定点の間を線形補間、範囲外は端の値）。"""
        x, y = self._sorted()
        return float(np.interp(parameter_value, x, y))

    def inverse(self, feature_value: float) -> float | None:
        """目標の特徴値になるパラメータ値。単調でない曲線では一意に決まらないため None。

        測定範囲外の目標は、最も近い端の測定点のパラメータ値を返す。
        """
        if not self.is_monotonic:
            return None
        x, y = self._sorted()
        if y[0] > y[-1]:
            x, y = x[::-1], y[::-1]
        return float(np.interp(feature_value, y, x))

    def covers(self, feature_value: float) -> bool:
        lo, hi = self.feature_range
        return lo <= feature_value <= hi


class CalibrationSet:
    """ある機種のキャリブレーション曲線の集まり。(parameter_id, feature) で引く。"""

    def __init__(self, curves: list[CalibrationCurve] | None = None) -> None:
        self._curves = {(c.parameter_id, c.feature): c for c in curves or []}

    def __len__(self) -> int:
        return len(self._curves)

    def get(self, parameter_id: str, feature: str) -> CalibrationCurve | None:
        return self._curves.get((parameter_id, feature))

    @classmethod
    def load(cls, directory: Path | None, synth_id: str) -> CalibrationSet:
        """directory 内の *.json を読み、synth_id が一致する曲線だけを集める。"""
        if directory is None or not directory.is_dir():
            return cls()
        curves = []
        for path in sorted(directory.glob("*.json")):
            curve = CalibrationCurve.model_validate_json(path.read_text(encoding="utf-8"))
            if curve.synth_id == synth_id:
                curves.append(curve)
        return cls(curves)
