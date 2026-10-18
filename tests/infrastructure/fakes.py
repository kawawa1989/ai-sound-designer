"""実機なしで MIDI 送信と録音を試すための代用品。"""

from collections.abc import Callable

import mido
import numpy as np


class FakePort:
    def __init__(self) -> None:
        self.messages: list[mido.Message] = []
        self.closed = False

    def send(self, msg: mido.Message) -> None:
        self.messages.append(msg)

    def close(self) -> None:
        self.closed = True


class FakeRecorder:
    """stop() で、与えた信号を (フレーム, チャンネル) で返す。"""

    def __init__(self, make: Callable[[], np.ndarray], sample_rate: int = 48_000) -> None:
        self.sample_rate = sample_rate
        self._make = make
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> np.ndarray:
        self.stopped = True
        x = self._make()
        return np.stack([x, x], axis=1).astype(np.float32)
