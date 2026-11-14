"""アプリケーション層: 機種IDから Adapter を選んで注入する。"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from synth_ai.adapters.base import SynthAdapter
from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.adapters.kronos2 import Kronos2Adapter
from synth_ai.adapters.pc3a8 import Pc3a8Adapter

# パラメータ表・キャリブレーション表の置き場所。SYNTH_AI_DATA_DIR で変更できる
DATA_DIR = Path(os.environ.get("SYNTH_AI_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))


def _kronos2() -> SynthAdapter:
    return Kronos2Adapter(
        parameter_dir=DATA_DIR / "kronos_parameters",
        calibration_dir=DATA_DIR / "kronos_calibration",
    )


def _pc3a8() -> SynthAdapter:
    return Pc3a8Adapter(
        parameter_dir=DATA_DIR / "pc3a8_parameters",
        calibration_dir=DATA_DIR / "pc3a8_calibration",
    )


# 機種ごとのキャリブレーション表の置き場所
CALIBRATION_DIRS: dict[str, Path] = {
    "kronos2": DATA_DIR / "kronos_calibration",
    "pc3a8": DATA_DIR / "pc3a8_calibration",
}

# 機種ごとに送ってよい CC 番号（docs/safety.md「CC を送る条件」。calibrate の CC モードだけで使う）
# CC 15 は本体全体の音程を動かすことが分かったので外した（2026-11-14、#40。docs/safety.md）
ALLOWED_CONTROLS: dict[str, frozenset[int]] = {"pc3a8": frozenset({14})}

ADAPTER_FACTORIES: dict[str, Callable[[], SynthAdapter]] = {
    "fake": FakeSynthAdapter,
    "kronos2": _kronos2,
    "pc3a8": _pc3a8,
}


def get_adapter(synth_id: str) -> SynthAdapter:
    try:
        return ADAPTER_FACTORIES[synth_id]()
    except KeyError:
        known = ", ".join(sorted(ADAPTER_FACTORIES))
        raise ValueError(f"unknown synth {synth_id!r} (known: {known})") from None
