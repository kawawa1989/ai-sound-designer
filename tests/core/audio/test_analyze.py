"""正解が分かっている合成音で、解析値が期待どおりに振る舞うことを確かめる。"""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from synth_ai.core.audio import features as F
from synth_ai.core.audio.analyze import AnalysisResult, analyze_file
from synth_ai.core.synthesis import test_signals as ts
from synth_ai.core.synthesis.test_signals import Adsr

Analyze = Callable[[str, np.ndarray], AnalysisResult]


def issue_codes(result: AnalysisResult) -> set[str]:
    return {i.code for i in result.analysis.issues}


# --- ピッチ --------------------------------------------------------------------


@pytest.mark.parametrize(("note", "f0"), [("A1", 55.0), ("C4", 261.6256), ("A5", 880.0)])
def test_pitch_of_saw(analyze_signal: Analyze, note: str, f0: float) -> None:
    pitch = analyze_signal(f"saw_{note}", ts.saw(f0)).analysis.pitch
    assert pitch is not None
    assert pitch.note == note
    assert abs(pitch.cents_offset) < 2.0
    assert pitch.confidence > 0.7


def test_detuned_pitch_reports_cents(analyze_signal: Analyze) -> None:
    pitch = analyze_signal("saw_a4_plus25", ts.saw(440.0 * 2 ** (25 / 1200))).analysis.pitch
    assert pitch is not None and pitch.note == "A4"
    assert pitch.cents_offset == pytest.approx(25.0, abs=2.0)


def test_pluck_pitch(analyze_signal: Analyze) -> None:
    pitch = analyze_signal("pluck", ts.pluck(220.0)).analysis.pitch
    assert pitch is not None and pitch.note == "A3"
    assert abs(pitch.cents_offset) < 10.0  # Karplus-Strong の遅延は整数サンプルに丸められる


def test_chord_is_flagged(analyze_signal: Analyze) -> None:
    result = analyze_signal("chord", ts.chord())
    assert "pitch_unreliable" in issue_codes(result)


# --- 包絡 ----------------------------------------------------------------------


def test_fast_and_slow_attack(analyze_signal: Analyze) -> None:
    fast = analyze_signal("attack_fast", ts.saw(adsr=Adsr(attack_s=0.002))).analysis.envelope
    slow = analyze_signal("attack_slow", ts.saw(adsr=Adsr(attack_s=0.3))).analysis.envelope
    assert fast is not None and slow is not None
    assert fast.attack_ms is not None and fast.attack_ms < 15
    # 線形ランプの 10%→90% は全体の 80%
    assert slow.attack_ms == pytest.approx(0.8 * 300, rel=0.15)


def test_sustained_note(analyze_signal: Analyze) -> None:
    adsr = Adsr(attack_s=0.01, decay_s=0.2, sustain=0.5, release_s=0.4, note_s=1.2)
    env = analyze_signal("sustained", ts.saw(adsr=adsr)).analysis.envelope
    assert env is not None and env.sustained
    assert env.sustain_level_db == pytest.approx(20 * np.log10(0.5), abs=1.0)
    assert env.decay_ms == pytest.approx(200, abs=60)
    # release_ms はサステインから 20 dB 下がるまで。線形ランプでは長さの 90%
    assert env.release_ms == pytest.approx(0.9 * 400, rel=0.1)


def test_pluck_has_no_sustain(analyze_signal: Analyze) -> None:
    env = analyze_signal("pluck", ts.pluck(220.0)).analysis.envelope
    assert env is not None and not env.sustained
    assert env.decay_rate_db_per_s is not None and env.decay_rate_db_per_s < -3


def test_reverb_lengthens_release(analyze_signal: Analyze) -> None:
    dry_adsr = Adsr(release_s=0.1)
    dry = analyze_signal("dry", ts.saw(adsr=dry_adsr)).analysis.envelope
    wet = analyze_signal("wet", ts.with_reverb(ts.saw(adsr=dry_adsr))).analysis.envelope
    assert dry is not None and wet is not None
    assert dry.release_ms is not None and wet.release_ms is not None
    assert wet.release_ms > dry.release_ms * 2


# --- スペクトル・倍音 ----------------------------------------------------------


def test_saw_harmonic_levels(analyze_signal: Analyze) -> None:
    harmonics = analyze_signal("saw_C4", ts.saw(261.6256)).analysis.harmonics
    assert harmonics is not None
    levels = {p.number: p.level_db for p in harmonics.partials}
    for k in (2, 3, 4, 8):  # 1/k 振幅 → -20·log10(k) dB
        assert levels[k] == pytest.approx(-20 * np.log10(k), abs=0.3)
    assert harmonics.harmonic_energy_ratio > 0.98
    assert harmonics.inharmonicity_cents < 1.0


def test_square_has_odd_harmonics_only(analyze_signal: Analyze) -> None:
    harmonics = analyze_signal("square", ts.square()).analysis.harmonics
    assert harmonics is not None
    assert harmonics.odd_even_ratio_db is not None and harmonics.odd_even_ratio_db > 40


def test_fm_bell_is_inharmonic(analyze_signal: Analyze) -> None:
    result = analyze_signal("fm_bell", ts.fm_bell())
    saw = analyze_signal("saw_C4", ts.saw(261.6256)).analysis.harmonics
    bell = result.analysis.harmonics
    assert bell is not None and saw is not None
    assert bell.harmonic_energy_ratio < saw.harmonic_energy_ratio - 0.2
    assert "low_harmonicity" in issue_codes(result)


def test_brightness_order(analyze_signal: Analyze) -> None:
    sine = analyze_signal("sine", ts.sine()).analysis.spectral
    saw = analyze_signal("saw_C4", ts.saw(261.6256)).analysis.spectral
    assert sine is not None and saw is not None
    assert sine.centroid_ratio_to_f0 == pytest.approx(1.0, abs=0.1)
    assert saw.centroid_hz_mean > 5 * sine.centroid_hz_mean


def test_filter_sweep_gets_darker(analyze_signal: Analyze) -> None:
    spectral = analyze_signal("sweep", ts.saw_filter_sweep()).analysis.spectral
    assert spectral is not None
    assert spectral.brightness_change_ratio < 0.5


def test_noise_raises_flatness_and_is_flagged(analyze_signal: Analyze) -> None:
    clean = analyze_signal("saw_C4", ts.saw(261.6256))
    noisy = analyze_signal("noisy", ts.with_noise(ts.with_silence(ts.saw(), 0.2, 0.5)))
    assert noisy.analysis.spectral is not None and clean.analysis.spectral is not None
    assert noisy.analysis.spectral.flatness_mean > 10 * clean.analysis.spectral.flatness_mean
    assert "low_snr" in issue_codes(noisy)
    assert not noisy.analysis.levels.snr_is_lower_bound
    assert "low_snr" not in issue_codes(clean)
    # ノイズだけの末尾は音色の計算から除かれる
    assert noisy.analysis.spectral.brightness_change_ratio < 1.2


# --- 品質チェックと再現性 ------------------------------------------------------


def test_truncated_tail(analyze_signal: Analyze) -> None:
    assert "truncated_tail" in issue_codes(analyze_signal("cut", ts.saw()[:30_000]))
    assert "truncated_tail" not in issue_codes(analyze_signal("saw_C4", ts.saw(261.6256)))


def test_clean_signal_has_no_issues(analyze_signal: Analyze) -> None:
    assert issue_codes(analyze_signal("saw_C4", ts.saw(261.6256))) == set()


def test_timeseries_shapes(analyze_signal: Analyze) -> None:
    series = analyze_signal("saw_C4", ts.saw(261.6256)).analysis.timeseries
    assert series is not None
    n = len(series.rms_db)
    assert len(series.centroid_hz) == n and len(series.flatness) == n
    assert len(series.harmonic_levels_db) == F.N_TRACKED_HARMONICS
    assert all(len(row) == n for row in series.harmonic_levels_db)


def test_same_input_gives_same_json(tmp_path: Path) -> None:
    path = ts.write_wav(tmp_path / "a.wav", ts.saw_filter_sweep())
    first = analyze_file(path, "x").analysis.model_dump_json()
    second = analyze_file(path, "x").analysis.model_dump_json()
    assert first == second


def test_default_id_from_hash(tmp_path: Path) -> None:
    analysis = analyze_file(ts.write_wav(tmp_path / "a.wav", ts.saw())).analysis
    assert analysis.analysis_id == f"ref-{analysis.source.sha256[:8]}"


def test_quiet_dark_sound_is_not_brightened_by_noise_floor(analyze_signal: Analyze) -> None:
    """フィルターを閉じた小さな音でも、録音系の背景ノイズで明るさが上がって見えない。"""
    dark = ts.saw_filter_sweep(f0=261.63, cutoff_start_hz=300.0, cutoff_end_hz=300.0)
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1e-5, len(dark) + 48_000)  # 約 -100 dBFS の背景ノイズ
    loud = ts.with_silence(dark, 0.0, 1.0) + noise
    quiet = ts.with_silence(dark * 0.02, 0.0, 1.0) + noise  # 約 -40 dBFS
    loud_s = analyze_signal("dark_loud", loud).analysis.spectral
    quiet_s = analyze_signal("dark_quiet", quiet).analysis.spectral
    assert loud_s is not None and quiet_s is not None
    assert quiet_s.centroid_hz_end == pytest.approx(loud_s.centroid_hz_end, rel=0.15)
