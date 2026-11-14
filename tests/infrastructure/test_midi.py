import mido
import pytest

from synth_ai.infrastructure.midi import sender as midi
from synth_ai.infrastructure.midi.sender import MidiError, NoteSender, resolve_port_name
from tests.infrastructure.fakes import FakePort


def kinds(port: FakePort) -> list[str]:
    return [m.type for m in port.messages]


def test_play_sends_on_off_and_all_notes_off() -> None:
    port = FakePort()
    NoteSender(port, channel=3).play(60, 100, hold_s=0.001)
    assert kinds(port) == ["note_on", "note_off", "control_change"]
    assert port.messages[0].channel == 2  # 1 始まり → 0 始まり
    assert port.messages[0].note == 60 and port.messages[0].velocity == 100
    assert port.messages[2].control == midi.ALL_NOTES_OFF


def test_notes_stop_even_on_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    port = FakePort()

    def interrupted(_: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("time.sleep", interrupted)
    with pytest.raises(KeyboardInterrupt):
        NoteSender(port, 1).play(60, 100, hold_s=1.0)
    assert kinds(port) == ["note_on", "note_off", "control_change"]


@pytest.mark.parametrize(
    "msg",
    [
        mido.Message("sysex", data=[0x42, 0x30]),
        mido.Message("program_change", program=5),
        mido.Message("control_change", control=7, value=127),
    ],
)
def test_other_messages_are_refused(msg: mido.Message) -> None:
    port = FakePort()
    with pytest.raises(MidiError, match="許可していない"):
        NoteSender(port, 1)._send(msg)
    assert port.messages == []


@pytest.mark.parametrize(("note", "velocity"), [(128, 100), (60, 0), (-1, 10)])
def test_rejects_out_of_range(note: int, velocity: int) -> None:
    with pytest.raises(MidiError):
        NoteSender(FakePort(), 1).note_on(note, velocity)


def test_rejects_bad_channel() -> None:
    with pytest.raises(MidiError):
        NoteSender(FakePort(), 17)


def test_resolve_port_name() -> None:
    ports = ["KRONOS KEYBOARD", "KRONOS SOUND", "IAC Driver Bus 1"]
    assert resolve_port_name("IAC Driver Bus 1", ports) == "IAC Driver Bus 1"
    assert resolve_port_name("keyboard", ports) == "KRONOS KEYBOARD"
    with pytest.raises(MidiError, match="複数"):
        resolve_port_name("kronos", ports)
    with pytest.raises(MidiError, match="見つかりません"):
        resolve_port_name("PC3A8", ports)


def test_open_sender_closes_port(monkeypatch: pytest.MonkeyPatch) -> None:
    port = FakePort()
    monkeypatch.setattr("mido.get_output_names", lambda: ["KRONOS KEYBOARD"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    with pytest.raises(RuntimeError), midi.open_sender("kronos", 1) as sender:
        sender.note_on(60, 90)
        raise RuntimeError("boom")
    assert port.closed
    assert kinds(port) == ["note_on", "note_off", "control_change"]


def test_allowed_controls_only() -> None:
    """許可した CC 番号だけを送り、閉じるときに 0 に戻す（docs/safety.md「CC を送る条件」）。"""
    port = FakePort()
    sender = NoteSender(port, 1, allowed_controls=frozenset({14, 15}))
    sender.control_change(14, 64)
    sender.control_change(15, 0)
    for control in (7, 13, 0):
        with pytest.raises(MidiError, match="許可していない"):
            sender.control_change(control, 10)
    with pytest.raises(MidiError):
        sender.control_change(14, 128)
    with pytest.raises(MidiError):
        sender.control_change(midi.ALL_NOTES_OFF, 1)
    sender.reset_controls()
    assert [(m.control, m.value) for m in port.messages] == [(14, 64), (15, 0), (14, 0)]
    # 許可していなければ、CC 14 も送れない
    with pytest.raises(MidiError):
        NoteSender(FakePort(), 1).control_change(14, 1)


@pytest.mark.parametrize("control", [0, 6, 7, 32, 38, 98, 101, 120, 121, 127, 128])
def test_unsafe_controls_cannot_be_allowed(control: int) -> None:
    with pytest.raises(MidiError, match="送れません"):
        NoteSender(FakePort(), 1, allowed_controls=frozenset({control}))


def test_open_sender_resets_controls(monkeypatch: pytest.MonkeyPatch) -> None:
    port = FakePort()
    monkeypatch.setattr("mido.get_output_names", lambda: ["UR22mkII"])
    monkeypatch.setattr("mido.open_output", lambda name: port)
    with pytest.raises(RuntimeError), midi.open_sender("UR22", 1, frozenset({14})) as sender:
        sender.control_change(14, 100)
        raise RuntimeError("中断")
    assert [
        (m.type, getattr(m, "control", None), getattr(m, "value", None)) for m in port.messages
    ][-1] == ("control_change", 14, 0)
    assert port.closed
