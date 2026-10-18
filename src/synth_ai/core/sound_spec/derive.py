"""AudioAnalysis（観測値）から機種非依存の SoundSpec（目標と合成の仮説）を作る。

ラベルの閾値と仮説の確信度は経験則。実験データが溜まった段階で見直す。
"""

from __future__ import annotations

import math

import numpy as np

from synth_ai.core.sound_spec.features import UNITS, Feature
from synth_ai.core.sound_spec.models import (
    AudioAnalysis,
    EnvelopeSpec,
    HarmonicFeatures,
    Level,
    PitchTarget,
    QuantTarget,
    SoundSpec,
    Speed,
    SynthesisHypothesis,
    SynthesisMethod,
    TimbreSpec,
)

DECIMALS = 3

ISSUE_UNCERTAINTIES = {
    "pitch_unreliable": (
        "ピッチが確定できず、倍音に関する目標の信頼度が低い（和音・ノイズ・非調和音の可能性）"
    ),
    "truncated_tail": "音の終わりが切れているため、リリースは測定できていない",
    "low_snr": "背景ノイズが大きく、ノイズ感・減衰の目標は過大になっている可能性がある",
    "clipping": "クリップしているため、倍音（明るさ）が実際より強く測定されている可能性がある",
    "unstable_pitch": (
        "ピッチが揺れており、ビブラートやグライドを別途再現する必要があるかもしれない"
    ),
    "low_harmonicity": "整数倍音以外の成分が多く、単純な波形だけでは再現しにくい可能性がある",
    "wide_stereo": "左右差が大きく、モノラル化した音色を目標にしている",
}


# --- ラベル --------------------------------------------------------------------


def _speed(value_ms: float | None, fast: float, slow: float) -> Speed | None:
    if value_ms is None:
        return None
    if value_ms < fast:
        return Speed.FAST
    return Speed.MEDIUM if value_ms < slow else Speed.SLOW


def _level(value: float | None, bounds: tuple[float, float, float, float]) -> Level | None:
    """bounds を昇順の 4 つの境界として 5 段階に分ける。"""
    if value is None:
        return None
    levels = (Level.VERY_LOW, Level.LOW, Level.MEDIUM, Level.HIGH, Level.VERY_HIGH)
    return levels[sum(value >= b for b in bounds)]


def _harmonicity_level(h: HarmonicFeatures | None) -> Level | None:
    if h is None:
        return None
    if h.harmonic_energy_ratio > 0.95 and h.inharmonicity_cents < 5:
        return Level.VERY_HIGH
    return _level(h.harmonic_energy_ratio, (0.5, 0.7, 0.85, 0.95))


def _sustain_level(a: AudioAnalysis) -> Level | None:
    env = a.envelope
    if env is None:
        return None
    if not env.sustained or env.sustain_level_db is None:
        return Level.VERY_LOW
    return _level(env.sustain_level_db, (-30.0, -10.0, -3.0, 0.5))


# --- 派生特徴 ------------------------------------------------------------------


def harmonic_slope_db_per_octave(h: HarmonicFeatures) -> float | None:
    """倍音レベルを log2(倍音番号) に対して直線近似した傾き（16 次まで）。"""
    points = [(math.log2(p.number), p.level_db) for p in h.partials if p.number <= 16]
    if len(points) < 3:
        return None
    x, y = np.array(points).T
    return float(np.polyfit(x, y, 1)[0])


def brightness_decay_time_ms(a: AudioAnalysis) -> float | None:
    """スペクトル重心が、発音直後と終盤の中間（対数）まで下がる時間。暗くならない音は None。"""
    s, ts, env = a.spectral, a.timeseries, a.envelope
    if s is None or ts is None or env is None or s.brightness_change_ratio > 0.85:
        return None
    mid = math.sqrt(s.centroid_hz_start * s.centroid_hz_end)
    for i, c in enumerate(ts.centroid_hz):
        t = i * ts.hop_s
        if t > env.onset_s and c is not None and c <= mid:
            return (t - env.onset_s) * 1000
    return None


# --- 定量目標 ------------------------------------------------------------------


def _target(
    feature: Feature, value: float | None, tolerance: float, confidence: float
) -> QuantTarget | None:
    if value is None or not math.isfinite(value):
        return None
    return QuantTarget(
        feature=feature.value,
        value=round(value, DECIMALS),
        unit=UNITS[feature],
        tolerance=round(abs(tolerance), DECIMALS),
        confidence=round(confidence, DECIMALS),
    )


def quantitative_targets(a: AudioAnalysis) -> tuple[QuantTarget, ...]:
    targets: list[QuantTarget | None] = []
    env = a.envelope
    if env is not None:
        c = env.confidence
        targets += [
            _target(
                Feature.ATTACK_TIME,
                env.attack_ms,
                max(3.0, 0.3 * (env.attack_ms or 0)),
                c,
            ),
            _target(Feature.DECAY_TIME, env.decay_ms, 0.3 * (env.decay_ms or 0), c),
            _target(Feature.SUSTAIN_LEVEL, env.sustain_level_db, 2.0, c),
            _target(Feature.RELEASE_TIME, env.release_ms, 0.3 * (env.release_ms or 0), c),
            _target(
                Feature.DECAY_RATE,
                env.decay_rate_db_per_s,
                0.3 * abs(env.decay_rate_db_per_s or 0),
                c,
            ),
        ]
    s, f0 = a.spectral, a.pitch.f0_hz if a.pitch else None
    if s is not None:
        c = s.confidence * (a.pitch.confidence if a.pitch else 0.3)
        if f0:
            targets += [
                _target(
                    Feature.BRIGHTNESS, s.centroid_hz_mean / f0, 0.2 * s.centroid_hz_mean / f0, c
                ),
                _target(
                    Feature.BRIGHTNESS_START,
                    s.centroid_hz_start / f0,
                    0.2 * s.centroid_hz_start / f0,
                    c,
                ),
                _target(
                    Feature.BRIGHTNESS_END, s.centroid_hz_end / f0, 0.2 * s.centroid_hz_end / f0, c
                ),
            ]
        decay_ms = brightness_decay_time_ms(a)
        targets += [
            _target(
                Feature.BRIGHTNESS_CHANGE,
                s.brightness_change_ratio,
                0.15 * s.brightness_change_ratio,
                s.confidence,
            ),
            _target(Feature.BRIGHTNESS_DECAY_TIME, decay_ms, 0.3 * (decay_ms or 0), s.confidence),
            _target(
                Feature.NOISINESS, s.flatness_mean, max(0.002, 0.3 * s.flatness_mean), s.confidence
            ),
        ]
    h = a.harmonics
    if h is not None:
        targets += [
            _target(Feature.HARMONICITY, h.harmonic_energy_ratio, 0.05, h.confidence),
            _target(
                Feature.INHARMONICITY,
                h.inharmonicity_cents,
                max(2.0, 0.3 * h.inharmonicity_cents),
                h.confidence,
            ),
            _target(Feature.HARMONIC_SLOPE, harmonic_slope_db_per_octave(h), 1.5, h.confidence),
            _target(Feature.ODD_EVEN_RATIO, h.odd_even_ratio_db, 3.0, h.confidence),
        ]
    return tuple(t for t in targets if t is not None)


# --- 合成の仮説 ----------------------------------------------------------------


def synthesis_hypotheses(
    timbre: TimbreSpec, envelope: EnvelopeSpec, a: AudioAnalysis
) -> tuple[SynthesisHypothesis, ...]:
    ranked = (Level.VERY_LOW, Level.LOW, Level.MEDIUM, Level.HIGH, Level.VERY_HIGH)

    def at_least(level: Level | None, threshold: Level) -> bool:
        return level is not None and ranked.index(level) >= ranked.index(threshold)

    harmonic = at_least(timbre.harmonicity, Level.HIGH)
    noisy = at_least(timbre.noisiness, Level.MEDIUM)
    darkening = timbre.brightness_decay is not None
    pitch_ok = a.pitch is not None and a.pitch.confidence >= 0.5
    hypotheses: list[SynthesisHypothesis] = []

    def add(method: SynthesisMethod, confidence: float, reasons: list[str]) -> None:
        if confidence >= 0.2:
            hypotheses.append(
                SynthesisHypothesis(
                    method=method,
                    rationale="、".join(reasons),
                    confidence=round(min(confidence, 0.95), 2),
                )
            )

    # 減算合成: 整数倍音が豊富で、明るさの変化がフィルターで説明できる
    sub, reasons = 0.0, []
    if harmonic:
        sub += 0.55
        reasons.append("整数倍音が明瞭")
    if darkening:
        sub += 0.15
        reasons.append("時間とともに暗くなる（フィルターの変化で説明できる）")
    if not noisy:
        sub += 0.1
        reasons.append("ノイズ成分が少ない")
    if not pitch_ok:
        sub *= 0.5
        reasons.append("ただしピッチが確定できない")
    add(SynthesisMethod.SUBTRACTIVE, sub, reasons)

    # FM: 非整数倍音や金属的な響き、速い明るさの減衰
    fm, reasons = 0.0, []
    if not harmonic:
        fm += 0.5
        reasons.append("整数倍音以外の成分が多い")
    if a.harmonics is not None and a.harmonics.inharmonicity_cents > 20:
        fm += 0.2
        reasons.append(
            f"倍音が整数倍から平均 {a.harmonics.inharmonicity_cents:.0f} セントずれている"
        )
    if timbre.brightness_decay is Speed.FAST:
        fm += 0.1
        reasons.append("明るさが速く減衰する（変調指数の減衰で説明できる）")
    add(SynthesisMethod.FM, fm, reasons)

    # 物理モデル（撥弦・打撃）: 速い立ち上がり、サステインなし、高域から先に減衰
    pm, reasons = 0.0, []
    if envelope.attack is Speed.FAST and envelope.sustain is Level.VERY_LOW and darkening:
        pm = 0.45
        reasons = ["立ち上がりが速くサステインがなく、高域から先に減衰する（撥弦・打撃的）"]
    add(SynthesisMethod.PHYSICAL_MODEL, pm, reasons)

    # サンプル再生: ノイズや複雑な成分が多い、またはピッチ・倍音で説明しにくい
    smp, reasons = 0.15, ["元の音の質感をそのまま使える"]
    if noisy:
        smp += 0.25
        reasons.append("ノイズ成分が多い")
    if not pitch_ok:
        smp += 0.2
        reasons.append("ピッチや倍音構造で説明しにくい")
    add(SynthesisMethod.SAMPLE_BASED, smp, reasons)

    return tuple(sorted(hypotheses, key=lambda h: h.confidence, reverse=True))


# --- 組み立て ------------------------------------------------------------------


def derive_sound_spec(a: AudioAnalysis, spec_id: str | None = None) -> SoundSpec:
    env, s = a.envelope, a.spectral
    brightness_ratio = s.centroid_ratio_to_f0 if s else None
    change = s.brightness_change_ratio if s else None
    timbre = TimbreSpec(
        harmonicity=_harmonicity_level(a.harmonics),
        brightness=_level(brightness_ratio, (2.0, 4.0, 8.0, 16.0)),
        brightness_decay=None
        if change is None or change > 0.85
        else (Speed.FAST if change < 0.4 else Speed.MEDIUM if change < 0.7 else Speed.SLOW),
        noisiness=_level(s.flatness_mean if s else None, (0.001, 0.01, 0.05, 0.2)),
    )
    envelope = EnvelopeSpec(
        attack=_speed(env.attack_ms if env else None, 15.0, 100.0),
        decay=_speed(env.decay_ms if env else None, 150.0, 600.0),
        sustain=_sustain_level(a),
        release=_speed(env.release_ms if env else None, 100.0, 500.0),
    )
    pitch = (
        PitchTarget(note=a.pitch.note, f0_hz=a.pitch.f0_hz, confidence=a.pitch.confidence)
        if a.pitch
        else None
    )
    uncertainties = [ISSUE_UNCERTAINTIES[i.code] for i in a.issues if i.code in ISSUE_UNCERTAINTIES]
    if change is not None and change > 1.15:
        uncertainties.append("時間とともに明るくなる（フィルターが開く、または高域ノイズの増加）")
    if env is not None and not env.sustained:
        uncertainties.append("サステインがないため、ノートオフ後のリリースは参照音から分からない")

    return SoundSpec(
        spec_id=spec_id or f"{a.analysis_id}-spec",
        reference_id=a.analysis_id,
        analysis_id=a.analysis_id,
        pitch=pitch,
        timbre=timbre,
        envelope=envelope,
        targets=quantitative_targets(a),
        hypotheses=synthesis_hypotheses(timbre, envelope, a),
        uncertainties=tuple(uncertainties),
    )


def target_of(spec: SoundSpec, feature: Feature) -> QuantTarget | None:
    return next((t for t in spec.targets if t.feature == feature.value), None)
