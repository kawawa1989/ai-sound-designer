"""録音と、発音に同期した 1 音の収録。

録音を始めてから発音し、リリースが鳴り終わるまで録ってから止める。
MIDI がなければ、合図を出して人が鍵盤を弾く。
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np
import soundfile as sf

from synth_ai.infrastructure.midi.sender import NoteSender

CLIP_LEVEL = 0.999


class CaptureError(Exception):
    pass


class Recorder(Protocol):
    sample_rate: int

    def start(self) -> None: ...

    def stop(self) -> np.ndarray:
        """録音を止め、(フレーム数, チャンネル数) の float32 配列を返す。"""
        ...


@dataclass(frozen=True)
class InputDevice:
    index: int
    name: str
    channels: int
    default_sample_rate: float


def input_devices() -> list[InputDevice]:
    import sounddevice as sd

    return [
        InputDevice(i, d["name"], d["max_input_channels"], d["default_samplerate"])
        for i, d in enumerate(sd.query_devices())
        if d["max_input_channels"] > 0
    ]


def resolve_input_device(wanted: str, devices: list[InputDevice]) -> InputDevice:
    exact = [d for d in devices if d.name == wanted]
    matches = exact or [d for d in devices if wanted.lower() in d.name.lower()]
    if len(matches) == 1:
        return matches[0]
    listed = "、".join(d.name for d in devices) or "（なし）"
    if not matches:
        raise CaptureError(f"録音デバイス「{wanted}」が見つかりません。接続中: {listed}")
    raise CaptureError(f"「{wanted}」に一致するデバイスが複数あります: {listed}")


class SoundDeviceRecorder:
    """sounddevice の入力ストリームで録音する。"""

    def __init__(self, device: str | None, sample_rate: int, channels: int) -> None:
        self.sample_rate = sample_rate
        self._channels = channels
        self._device: int | None = None
        if device is not None:
            info = resolve_input_device(device, input_devices())
            if info.channels < channels:
                raise CaptureError(
                    f"「{info.name}」の入力は {info.channels} ch です（設定は {channels} ch）"
                )
            self._device = info.index
        self._blocks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Any = None
        self.overflowed = False

    def _callback(self, indata: np.ndarray, frames: int, t: Any, status: Any) -> None:
        if status:
            self.overflowed = True
        with self._lock:
            self._blocks.append(indata.copy())

    def start(self) -> None:
        import sounddevice as sd

        try:
            self._stream = sd.InputStream(
                device=self._device,
                samplerate=self.sample_rate,
                channels=self._channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
        except sd.PortAudioError as exc:
            raise CaptureError(
                f"録音を開始できません: {exc}\n"
                "macOS では「システム設定 > プライバシーとセキュリティ > マイク」で、"
                "実行しているアプリ（ターミナル等）を許可してください"
            ) from exc

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            blocks, self._blocks = self._blocks, []
        if not blocks:
            return np.zeros((0, self._channels), dtype=np.float32)
        return np.concatenate(blocks, axis=0)


@dataclass(frozen=True)
class CaptureSettings:
    note: int
    velocity: int
    hold_s: float
    release_tail_s: float
    pre_roll_s: float = 0.3
    fade_ms: float = 5.0
    peak_warn_dbfs: float = -1.0
    quiet_warn_dbfs: float = -40.0


@dataclass
class CaptureResult:
    samples: np.ndarray  # (フレーム数, チャンネル数)
    sample_rate: int
    played_by: Literal["midi", "manual"]
    peak_dbfs: float
    warnings: list[str] = field(default_factory=list)


def _fade(x: np.ndarray, sample_rate: int, fade_ms: float) -> np.ndarray:
    n = min(int(sample_rate * fade_ms / 1000), len(x) // 2)
    if n <= 0:
        return x
    ramp = np.linspace(0.0, 1.0, n, dtype=x.dtype)[:, None]
    out = x.copy()
    out[:n] *= ramp
    out[-n:] *= ramp[::-1]
    return out


def capture_note(
    recorder: Recorder,
    sender: NoteSender | None,
    settings: CaptureSettings,
    prompt: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
) -> CaptureResult:
    """録音しながら 1 音鳴らす。sender が None なら人が弾く（合図は prompt で出す）。"""
    if sender is None:
        prompt(
            f"録音を始めます。合図のあと、ノート番号 {settings.note} の鍵盤を"
            f"約 {settings.hold_s:.1f} 秒押さえて離してください"
        )
    recorder.start()
    try:
        sleep(settings.pre_roll_s)
        if sender is not None:
            sender.play(settings.note, settings.velocity, settings.hold_s)
        else:
            prompt("▶ 今弾いてください")
            sleep(settings.hold_s)
            prompt("■ 離してください")
        sleep(settings.release_tail_s)
    finally:
        data = recorder.stop()

    if len(data) == 0:
        raise CaptureError("録音データが空です。入力デバイスを確認してください")
    data = data.astype(np.float64)
    peak = float(np.max(np.abs(data)))
    peak_dbfs = 20 * np.log10(max(peak, 1e-12))
    warnings = []
    if getattr(recorder, "overflowed", False):
        warnings.append("録音中に取りこぼし（オーバーフロー）がありました。録り直しを推奨します")
    if peak >= CLIP_LEVEL:
        warnings.append(
            "クリップしています。KRONOS の出力音量か入力ゲインを下げて録り直してください"
        )
    elif peak_dbfs > settings.peak_warn_dbfs:
        warnings.append(f"ピークが {peak_dbfs:.1f} dBFS と大きく、クリップの恐れがあります")
    if peak_dbfs < settings.quiet_warn_dbfs:
        warnings.append(
            f"ピークが {peak_dbfs:.1f} dBFS とほぼ無音です。"
            "入力デバイスの選択・接続・音量を確認してください"
        )
    return CaptureResult(
        samples=_fade(data, recorder.sample_rate, settings.fade_ms),
        sample_rate=recorder.sample_rate,
        played_by="midi" if sender is not None else "manual",
        peak_dbfs=round(peak_dbfs, 2),
        warnings=warnings,
    )


def write_capture(path: Path, result: CaptureResult) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, result.samples, result.sample_rate, subtype="PCM_24")
    return path
