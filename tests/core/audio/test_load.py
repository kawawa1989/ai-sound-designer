from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from synth_ai.core.audio.load import TARGET_SR, AudioLoadError, load_audio
from synth_ai.core.synthesis import test_signals as ts


def codes(audio: object) -> set[str]:
    return {issue.code for issue in audio.issues}  # type: ignore[attr-defined]


def test_stereo_and_resample(tmp_path: Path) -> None:
    x = ts.saw(sr=44_100)
    path = ts.write_wav(tmp_path / "stereo.wav", x, sr=44_100, channels=2)
    audio = load_audio(path)
    assert audio.sample_rate == TARGET_SR
    assert audio.source.sample_rate == 44_100
    assert audio.source.channels == 2
    assert audio.samples.ndim == 1
    assert audio.source.analyzed_duration_s == pytest.approx(len(x) / 44_100, abs=0.02)
    assert "wide_stereo" not in codes(audio)


def test_wide_stereo_warning(tmp_path: Path) -> None:
    left, right = ts.saw(), -ts.saw()
    path = tmp_path / "wide.wav"
    sf.write(path, np.stack([left, right * 0.9], axis=1), TARGET_SR)
    assert "wide_stereo" in codes(load_audio(path))


def test_trims_leading_and_trailing_silence(tmp_path: Path) -> None:
    x = ts.with_silence(ts.saw(), before_s=0.5, after_s=1.0)
    audio = load_audio(ts.write_wav(tmp_path / "padded.wav", x))
    assert audio.source.trim_start_s == pytest.approx(0.49, abs=0.005)
    assert audio.source.analyzed_duration_s == pytest.approx(len(ts.saw()) / TARGET_SR, abs=0.02)


def test_clipping_detected(tmp_path: Path) -> None:
    x = np.clip(ts.saw() * 4, -1, 1)
    assert "clipping" in codes(load_audio(ts.write_wav(tmp_path / "clip.wav", x)))


def test_dc_offset_removed(tmp_path: Path) -> None:
    audio = load_audio(ts.write_wav(tmp_path / "dc.wav", ts.saw() * 0.8 + 0.05))
    assert "dc_offset" in codes(audio)
    assert abs(float(np.mean(audio.samples))) < 0.01


def test_end_level_detects_cut(tmp_path: Path) -> None:
    cut = load_audio(ts.write_wav(tmp_path / "cut.wav", ts.saw()[:24_000]))
    faded = load_audio(ts.write_wav(tmp_path / "faded.wav", ts.saw()))
    assert cut.end_level_db > -10
    assert faded.end_level_db < -40


def test_sha256_is_stable(tmp_path: Path) -> None:
    path = ts.write_wav(tmp_path / "a.wav", ts.saw())
    assert load_audio(path).source.sha256 == load_audio(path).source.sha256


@pytest.mark.parametrize(
    ("make", "message"),
    [
        (lambda p: p / "missing.wav", "見つかりません"),
        (lambda p: _write_text(p / "text.wav"), "読み込めません"),
        (lambda p: ts.write_wav(p / "silent.wav", np.zeros(48_000)), "無音"),
        (lambda p: ts.write_wav(p / "short.wav", ts.sine()[:2_400]), "短すぎ"),
    ],
)
def test_rejects_unusable_input(tmp_path: Path, make: object, message: str) -> None:
    with pytest.raises(AudioLoadError, match=message):
        load_audio(make(tmp_path))  # type: ignore[operator]


def _write_text(path: Path) -> Path:
    path.write_text("not audio")
    return path
