import pytest

from synth_ai.core.audio.notes import hz_to_note, note_to_hz, note_to_midi


@pytest.mark.parametrize(
    ("note", "midi"), [("A4", 69), ("C4", 60), ("C#4", 61), ("Db4", 61), ("C-1", 0), ("B9", 131)]
)
def test_note_to_midi(note: str, midi: int) -> None:
    assert note_to_midi(note) == midi


def test_round_trip() -> None:
    for note in ("C2", "F#3", "A4", "G7"):
        name, cents = hz_to_note(note_to_hz(note))
        assert name == note
        assert abs(cents) < 1e-6


def test_cents_offset() -> None:
    name, cents = hz_to_note(440.0 * 2 ** (30 / 1200))
    assert name == "A4"
    assert cents == pytest.approx(30.0)


def test_invalid_note() -> None:
    with pytest.raises(ValueError):
        note_to_midi("H2")
