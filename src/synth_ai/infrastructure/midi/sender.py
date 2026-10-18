"""MIDI のノート送信。送るのは Note On / Note Off / All Notes Off（CC 123）だけ。

SysEx・プログラムチェンジ・その他のコントロールチェンジは送らない（実機の設定や音色を
書き換えないため）。例外や中断があっても、開いているノートは必ず止める。
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

import mido

ALL_NOTES_OFF = 123


class MidiError(Exception):
    pass


class MidiPort(Protocol):
    def send(self, msg: mido.Message) -> None: ...

    def close(self) -> None: ...


def output_port_names() -> list[str]:
    return list(mido.get_output_names())


def resolve_port_name(wanted: str, available: list[str]) -> str:
    """完全一致、なければ大文字小文字を無視した部分一致がちょうど 1 つの名前。"""
    if wanted in available:
        return wanted
    matches = [name for name in available if wanted.lower() in name.lower()]
    if len(matches) == 1:
        return matches[0]
    listed = "、".join(available) or "（なし）"
    if not matches:
        raise MidiError(f"MIDI 出力ポート「{wanted}」が見つかりません。接続中: {listed}")
    raise MidiError(f"「{wanted}」に一致するポートが複数あります: {'、'.join(matches)}")


class NoteSender:
    """1 つのチャンネルにノートを送る。チャンネルは 1〜16 で指定する。"""

    _ALLOWED = {"note_on", "note_off", "control_change"}

    def __init__(self, port: MidiPort, channel: int) -> None:
        if not 1 <= channel <= 16:
            raise MidiError(f"MIDI チャンネルは 1〜16: {channel}")
        self._port = port
        self._channel = channel - 1
        self._sounding: set[int] = set()

    def _send(self, msg: mido.Message) -> None:
        if msg.type not in self._ALLOWED or (
            msg.type == "control_change" and msg.control != ALL_NOTES_OFF
        ):
            raise MidiError(f"許可していない MIDI メッセージです: {msg.type}")
        self._port.send(msg)

    def note_on(self, note: int, velocity: int) -> None:
        if not (0 <= note <= 127 and 1 <= velocity <= 127):
            raise MidiError(
                f"ノート番号 0〜127、ベロシティ 1〜127: note={note} velocity={velocity}"
            )
        self._send(mido.Message("note_on", note=note, velocity=velocity, channel=self._channel))
        self._sounding.add(note)

    def note_off(self, note: int) -> None:
        self._send(mido.Message("note_off", note=note, velocity=0, channel=self._channel))
        self._sounding.discard(note)

    def all_notes_off(self) -> None:
        for note in sorted(self._sounding):
            self.note_off(note)
        self._send(
            mido.Message("control_change", control=ALL_NOTES_OFF, value=0, channel=self._channel)
        )

    def play(self, note: int, velocity: int, hold_s: float) -> None:
        """Note On → hold_s 秒 → Note Off。途中で例外が起きてもノートを止める。"""
        try:
            self.note_on(note, velocity)
            time.sleep(hold_s)
        finally:
            self.all_notes_off()


@contextmanager
def open_sender(port_name: str, channel: int) -> Iterator[NoteSender]:
    name = resolve_port_name(port_name, output_port_names())
    try:
        port = mido.open_output(name)
    except (OSError, ValueError) as exc:
        raise MidiError(f"MIDI 出力ポート「{name}」を開けません: {exc}") from exc
    sender = NoteSender(port, channel)
    try:
        yield sender
    finally:
        try:
            sender.all_notes_off()
        finally:
            port.close()
