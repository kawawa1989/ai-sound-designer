from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from synth_ai.infrastructure.capture.recorder import (
    CaptureError,
    CaptureSettings,
    InputDevice,
    capture_note,
    resolve_input_device,
    write_capture,
)
from synth_ai.infrastructure.midi.sender import NoteSender
from tests.infrastructure.fakes import FakePort, FakeRecorder

SETTINGS = CaptureSettings(note=60, velocity=100, hold_s=0.001, release_tail_s=0.0, pre_roll_s=0.0)


def tone(level: float = 0.5) -> np.ndarray:
    t = np.arange(48_000) / 48_000
    return level * np.sin(2 * np.pi * 261.63 * t)


def test_midi_capture_plays_note_and_records() -> None:
    port, recorder = FakePort(), FakeRecorder(tone)
    result = capture_note(recorder, NoteSender(port, 1), SETTINGS, sleep=lambda _: None)
    assert recorder.started and recorder.stopped
    assert [m.type for m in port.messages][:2] == ["note_on", "note_off"]
    assert result.played_by == "midi"
    assert result.samples.shape == (48_000, 2)
    assert result.peak_dbfs == pytest.approx(-6.02, abs=0.05)
    assert result.warnings == []
    # 先頭・末尾にフェードが掛かっている
    assert result.samples[0, 0] == 0.0 and abs(result.samples[-1, 0]) < 1e-6


def test_manual_capture_prompts() -> None:
    prompts: list[str] = []
    waits: list[float] = []
    result = capture_note(
        FakeRecorder(tone), None, SETTINGS, prompt=prompts.append, sleep=waits.append
    )
    assert result.played_by == "manual"
    assert any("今弾いて" in p for p in prompts) and any("離して" in p for p in prompts)
    assert waits == [SETTINGS.pre_roll_s, SETTINGS.hold_s, SETTINGS.release_tail_s]


@pytest.mark.parametrize(
    ("level", "expected"), [(1.0, "クリップ"), (0.95, "クリップの恐れ"), (0.001, "ほぼ無音")]
)
def test_level_warnings(level: float, expected: str) -> None:
    result = capture_note(
        FakeRecorder(lambda: tone(level)),
        None,
        SETTINGS,
        prompt=lambda _: None,
        sleep=lambda _: None,
    )
    assert any(expected in w for w in result.warnings)


def test_recorder_stops_on_interrupt() -> None:
    recorder = FakeRecorder(tone)

    def interrupted(_: float) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        capture_note(recorder, None, SETTINGS, prompt=lambda _: None, sleep=interrupted)
    assert recorder.stopped


def test_empty_recording() -> None:
    recorder = FakeRecorder(lambda: np.zeros(0))
    with pytest.raises(CaptureError):
        capture_note(recorder, None, SETTINGS, prompt=lambda _: None, sleep=lambda _: None)


def test_write_capture_24bit(tmp_path: Path) -> None:
    result = capture_note(
        FakeRecorder(tone), None, SETTINGS, prompt=lambda _: None, sleep=lambda _: None
    )
    path = write_capture(tmp_path / "takes" / "a.wav", result)
    info = sf.info(path)
    assert info.subtype == "PCM_24" and info.channels == 2 and info.samplerate == 48_000


def test_resolve_input_device() -> None:
    devices = [
        InputDevice(0, "MacBook Air Microphone", 1, 44100),
        InputDevice(3, "KRONOS", 2, 48000),
    ]
    assert resolve_input_device("kronos", devices).index == 3
    with pytest.raises(CaptureError, match="見つかりません"):
        resolve_input_device("PC3A8", devices)
