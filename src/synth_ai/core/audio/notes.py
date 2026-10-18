"""音名と周波数の変換（A4 = 440 Hz、C4 = 中央のド）。"""

from __future__ import annotations

import math
import re

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")
_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz_to_midi(freq_hz: float) -> float:
    return 69.0 + 12.0 * math.log2(freq_hz / 440.0)


def midi_to_hz(midi: float) -> float:
    return float(440.0 * 2.0 ** ((midi - 69.0) / 12.0))


def hz_to_note(freq_hz: float) -> tuple[str, float]:
    """最も近い音名と、その音からのずれ（セント）を返す。"""
    midi = hz_to_midi(freq_hz)
    nearest = round(midi)
    name = f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}"
    return name, (midi - nearest) * 100.0


def note_to_midi(note: str) -> int:
    match = _NOTE_RE.match(note.strip())
    if not match:
        raise ValueError(f"invalid note name: {note!r}")
    letter, accidental, octave = match.groups()
    semitone = _OFFSETS[letter.upper()] + {"#": 1, "b": -1, "": 0}[accidental]
    return (int(octave) + 1) * 12 + semitone


def note_to_hz(note: str) -> float:
    return midi_to_hz(note_to_midi(note))
