"""SoundSpec の定量目標で使う、機種非依存の特徴名と単位。"""

from __future__ import annotations

from enum import StrEnum


class Feature(StrEnum):
    ATTACK_TIME = "attack_time"  # ms: ピーク振幅の 10%→90%
    DECAY_TIME = "decay_time"  # ms: ピーク→サステインの dB 差の 90%（なしなら -20 dB 到達）
    SUSTAIN_LEVEL = "sustain_level"  # dB: ピーク基準
    RELEASE_TIME = "release_time"  # ms: サステインから 20 dB 下がるまで
    DECAY_RATE = "decay_rate"  # dB/s: ピーク後の減衰の傾き
    BRIGHTNESS = "brightness"  # ×f0: スペクトル重心 / 基音（全体平均）
    BRIGHTNESS_START = "brightness_start"  # ×f0: 発音直後 100 ms
    BRIGHTNESS_END = "brightness_end"  # ×f0: 発音区間の最後の 25%
    BRIGHTNESS_CHANGE = "brightness_change"  # 比: end / start
    BRIGHTNESS_DECAY_TIME = (
        "brightness_decay_time"  # ms: 重心が start と end の中間（対数）に下がるまで
    )
    NOISINESS = "noisiness"  # 0〜1: スペクトル平坦度
    HARMONICITY = "harmonicity"  # 0〜1: 整数倍音に集まるエネルギーの割合
    INHARMONICITY = "inharmonicity"  # cents: 倍音の整数倍からのずれ
    HARMONIC_SLOPE = "harmonic_slope"  # dB/oct: 倍音レベルの傾き（ノコギリ波 ≈ -6）
    ODD_EVEN_RATIO = "odd_even_ratio"  # dB: 奇数次 / 偶数次（矩形波で大きい）


UNITS: dict[Feature, str] = {
    Feature.ATTACK_TIME: "ms",
    Feature.DECAY_TIME: "ms",
    Feature.SUSTAIN_LEVEL: "dB",
    Feature.RELEASE_TIME: "ms",
    Feature.DECAY_RATE: "dB/s",
    Feature.BRIGHTNESS: "x f0",
    Feature.BRIGHTNESS_START: "x f0",
    Feature.BRIGHTNESS_END: "x f0",
    Feature.BRIGHTNESS_CHANGE: "ratio",
    Feature.BRIGHTNESS_DECAY_TIME: "ms",
    Feature.NOISINESS: "flatness",
    Feature.HARMONICITY: "ratio",
    Feature.INHARMONICITY: "cents",
    Feature.HARMONIC_SLOPE: "dB/oct",
    Feature.ODD_EVEN_RATIO: "dB",
}

LABELS: dict[Feature, str] = {
    Feature.ATTACK_TIME: "アタック",
    Feature.DECAY_TIME: "ディケイ",
    Feature.SUSTAIN_LEVEL: "サステインレベル",
    Feature.RELEASE_TIME: "リリース",
    Feature.DECAY_RATE: "減衰の速さ",
    Feature.BRIGHTNESS: "明るさ",
    Feature.BRIGHTNESS_START: "発音直後の明るさ",
    Feature.BRIGHTNESS_END: "持続部の明るさ",
    Feature.BRIGHTNESS_CHANGE: "明るさの変化",
    Feature.BRIGHTNESS_DECAY_TIME: "暗くなるまでの時間",
    Feature.NOISINESS: "ノイズ感",
    Feature.HARMONICITY: "整数倍音率",
    Feature.INHARMONICITY: "非調和性",
    Feature.HARMONIC_SLOPE: "倍音の傾き",
    Feature.ODD_EVEN_RATIO: "奇数/偶数倍音比",
}
