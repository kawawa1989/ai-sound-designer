"""パラメータ表で使う「役割」と「選択肢タグ」の語彙。

レシピ生成コードは KRONOS のパラメータ名を直接書かず、この役割でパラメータ表を引く。
どのパラメータがどの役割を担うかは、公式資料を確認した人がパラメータ表に記入する。
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    OSCILLATOR_WAVEFORM = "oscillator_waveform"
    NOISE_LEVEL = "noise_level"
    FILTER_TYPE = "filter_type"
    FILTER_CUTOFF = "filter_cutoff"
    FILTER_RESONANCE = "filter_resonance"
    FILTER_EG_INTENSITY = "filter_eg_intensity"  # フィルター EG がカットオフを動かす量
    FILTER_EG_ATTACK = "filter_eg_attack"
    FILTER_EG_DECAY = "filter_eg_decay"
    FILTER_EG_SUSTAIN = "filter_eg_sustain"
    FILTER_EG_RELEASE = "filter_eg_release"
    AMP_EG_ATTACK = "amp_eg_attack"
    AMP_EG_DECAY = "amp_eg_decay"
    AMP_EG_SUSTAIN = "amp_eg_sustain"
    AMP_EG_RELEASE = "amp_eg_release"


class ChoiceTag(StrEnum):
    """選択式パラメータの選択肢に付けるタグ（例: 波形の選択肢「Saw」に saw）。"""

    SAW = "saw"
    SQUARE = "square"
    PULSE = "pulse"
    TRIANGLE = "triangle"
    SINE = "sine"
    NOISE = "noise"
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"


ROLE_LABELS: dict[Role, str] = {
    Role.OSCILLATOR_WAVEFORM: "オシレーターの波形",
    Role.NOISE_LEVEL: "ノイズの量",
    Role.FILTER_TYPE: "フィルターの種類",
    Role.FILTER_CUTOFF: "フィルターのカットオフ",
    Role.FILTER_RESONANCE: "フィルターのレゾナンス",
    Role.FILTER_EG_INTENSITY: "フィルター EG の効き（カットオフを動かす量）",
    Role.FILTER_EG_ATTACK: "フィルター EG のアタック",
    Role.FILTER_EG_DECAY: "フィルター EG のディケイ",
    Role.FILTER_EG_SUSTAIN: "フィルター EG のサステイン",
    Role.FILTER_EG_RELEASE: "フィルター EG のリリース",
    Role.AMP_EG_ATTACK: "アンプ EG のアタック",
    Role.AMP_EG_DECAY: "アンプ EG のディケイ",
    Role.AMP_EG_SUSTAIN: "アンプ EG のサステイン",
    Role.AMP_EG_RELEASE: "アンプ EG のリリース",
}
