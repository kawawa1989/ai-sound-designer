"""1 音を録音する確認用スクリプト（`synth-ai capture` と同じ）。

例: uv run python scripts/record_test.py assets/test/kronos_c4.wav --note C4
"""

import sys

from synth_ai.cli import app

if __name__ == "__main__":
    app(["capture", *sys.argv[1:]])
