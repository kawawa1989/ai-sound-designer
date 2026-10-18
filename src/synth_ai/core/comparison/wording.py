"""差分の言葉づかい。「録音が参照より大きい／小さい」をどう言うか、どう直すか。"""

from __future__ import annotations

from synth_ai.core.sound_spec.features import Feature

# (録音のほうが大きいとき, 小さいとき)
DIFFERENCE_WORDS: dict[Feature, tuple[str, str]] = {
    Feature.ATTACK_TIME: ("アタックが遅い", "アタックが速い"),
    Feature.DECAY_TIME: ("ディケイが長い", "ディケイが短い"),
    Feature.SUSTAIN_LEVEL: ("サステインが大きい", "サステインが小さい"),
    Feature.RELEASE_TIME: ("リリースが長い", "リリースが短い"),
    Feature.DECAY_RATE: ("減衰が遅い", "減衰が速い"),  # 値は負。大きい = 緩やか
    Feature.BRIGHTNESS: ("全体が明るい", "全体が暗い"),
    Feature.BRIGHTNESS_START: ("発音直後が明るい", "発音直後が暗い"),
    Feature.BRIGHTNESS_END: ("持続部が明るい", "持続部が暗い"),
    Feature.BRIGHTNESS_CHANGE: ("暗くなり方が弱い", "暗くなり方が強い"),  # end/start の比
    Feature.BRIGHTNESS_DECAY_TIME: ("暗くなるのが遅い", "暗くなるのが速い"),
    Feature.NOISINESS: ("ノイズが多い", "ノイズが少ない"),
    Feature.HARMONICITY: ("整数倍音の割合が高い", "整数倍音の割合が低い"),
    Feature.INHARMONICITY: ("倍音のずれが大きい", "倍音のずれが小さい"),
    Feature.HARMONIC_SLOPE: ("高次倍音が強い", "高次倍音が弱い"),
    Feature.ODD_EVEN_RATIO: ("奇数次倍音が強い（偶数次が弱い）", "偶数次倍音が強い"),
}

# 参照に近づけるための言い方: (特徴を大きくする, 小さくする)
FIX_WORDS: dict[Feature, tuple[str, str]] = {
    Feature.ATTACK_TIME: ("立ち上がりを遅くする", "立ち上がりを速くする"),
    Feature.DECAY_TIME: ("ディケイを長くする", "ディケイを短くする"),
    Feature.SUSTAIN_LEVEL: ("サステインを上げる", "サステインを下げる"),
    Feature.RELEASE_TIME: ("リリースを長くする", "リリースを短くする"),
    Feature.DECAY_RATE: ("減衰を緩やかにする", "減衰を速くする"),
    Feature.BRIGHTNESS: ("全体を明るくする", "全体を暗くする"),
    Feature.BRIGHTNESS_START: ("発音直後を明るくする", "発音直後を暗くする"),
    Feature.BRIGHTNESS_END: ("持続部を明るくする", "持続部を暗くする"),
    Feature.BRIGHTNESS_CHANGE: ("暗くなり方を弱める", "暗くなり方を強める"),
    Feature.BRIGHTNESS_DECAY_TIME: ("暗くなるのを遅くする", "暗くなるのを速くする"),
    Feature.NOISINESS: ("ノイズを足す", "ノイズを減らす"),
    Feature.HARMONICITY: ("整数倍音以外の成分を減らす", "整数倍音以外の成分を足す"),
    Feature.INHARMONICITY: ("倍音をずらす", "倍音を整数倍にそろえる"),
    Feature.HARMONIC_SLOPE: ("高次倍音を強める", "高次倍音を弱める"),
    Feature.ODD_EVEN_RATIO: (
        "偶数次倍音を減らす（矩形波寄りにする）",
        "偶数次倍音を足す（ノコギリ波寄りにする）",
    ),
}


def as_feature(name: str | None) -> Feature | None:
    if name is None:
        return None
    try:
        return Feature(name)
    except ValueError:
        return None


def difference_word(feature: Feature, delta: float) -> str:
    more, less = DIFFERENCE_WORDS[feature]
    return more if delta > 0 else less


def fix_word(feature: Feature, delta: float) -> str:
    """録音と参照の差 delta を打ち消す方向の言い方。"""
    increase, decrease = FIX_WORDS[feature]
    return decrease if delta > 0 else increase


def fmt(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.3g}"
