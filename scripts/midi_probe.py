"""MIDI で 1 音鳴らす確認用スクリプト（`synth-ai midi-probe` と同じ）。"""

import sys

from synth_ai.cli import app

if __name__ == "__main__":
    app(["midi-probe", *sys.argv[1:]])
