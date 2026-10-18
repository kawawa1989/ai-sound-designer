from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from synth_ai.core.audio.analyze import AnalysisResult, analyze_file
from synth_ai.core.synthesis import test_signals as ts


@pytest.fixture(scope="session")
def wav_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("wav")


@pytest.fixture(scope="session")
def analyze_signal(wav_dir: Path) -> Callable[[str, np.ndarray], AnalysisResult]:
    """信号を WAV に書き出して解析する（名前ごとにキャッシュ）。"""
    cache: dict[str, AnalysisResult] = {}

    def run(name: str, samples: np.ndarray) -> AnalysisResult:
        if name not in cache:
            cache[name] = analyze_file(ts.write_wav(wav_dir / f"{name}.wav", samples))
        return cache[name]

    return run
