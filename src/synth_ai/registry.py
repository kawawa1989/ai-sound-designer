"""アプリケーション層: 機種IDから Adapter を選んで注入する。"""

from __future__ import annotations

from collections.abc import Callable

from synth_ai.adapters.base import SynthAdapter
from synth_ai.adapters.fake import FakeSynthAdapter
from synth_ai.adapters.kronos2 import Kronos2Adapter

ADAPTER_FACTORIES: dict[str, Callable[[], SynthAdapter]] = {
    "fake": FakeSynthAdapter,
    "kronos2": Kronos2Adapter,
}


def get_adapter(synth_id: str) -> SynthAdapter:
    try:
        return ADAPTER_FACTORIES[synth_id]()
    except KeyError:
        known = ", ".join(sorted(ADAPTER_FACTORIES))
        raise ValueError(f"unknown synth {synth_id!r} (known: {known})") from None
