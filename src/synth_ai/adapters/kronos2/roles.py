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
    FILTER_EG_SOURCE = "filter_eg_source"  # カットオフを動かす EG の選択
    FILTER_EG_INTENSITY = "filter_eg_intensity"  # フィルター EG がカットオフを動かす量
    # EG は「レベル」と「次のレベルまでの時間」で表す。4 段の ADSR しかない機種では
    # *_START_LEVEL / *_ATTACK_LEVEL / *_BREAK_LEVEL / *_SLOPE は表に書かなくてよい
    FILTER_EG_START_LEVEL = "filter_eg_start_level"
    FILTER_EG_ATTACK_LEVEL = "filter_eg_attack_level"
    FILTER_EG_BREAK_LEVEL = "filter_eg_break_level"
    FILTER_EG_ATTACK = "filter_eg_attack"  # 時間
    FILTER_EG_DECAY = "filter_eg_decay"  # 時間
    FILTER_EG_SLOPE = "filter_eg_slope"  # 時間
    FILTER_EG_SUSTAIN = "filter_eg_sustain"  # レベル
    FILTER_EG_RELEASE = "filter_eg_release"  # 時間
    AMP_EG_START_LEVEL = "amp_eg_start_level"
    AMP_EG_ATTACK_LEVEL = "amp_eg_attack_level"
    AMP_EG_BREAK_LEVEL = "amp_eg_break_level"
    AMP_EG_ATTACK = "amp_eg_attack"  # 時間
    AMP_EG_DECAY = "amp_eg_decay"  # 時間
    AMP_EG_SLOPE = "amp_eg_slope"  # 時間
    AMP_EG_SUSTAIN = "amp_eg_sustain"  # レベル
    AMP_EG_RELEASE = "amp_eg_release"  # 時間


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
    FILTER_EG = "filter_eg"  # EG の選択肢のうち、フィルター用の EG


ROLE_LABELS: dict[Role, str] = {
    Role.OSCILLATOR_WAVEFORM: "オシレーターの波形",
    Role.NOISE_LEVEL: "ノイズの量",
    Role.FILTER_TYPE: "フィルターの種類",
    Role.FILTER_CUTOFF: "フィルターのカットオフ",
    Role.FILTER_RESONANCE: "フィルターのレゾナンス",
    Role.FILTER_EG_SOURCE: "カットオフを動かす EG の選択",
    Role.FILTER_EG_INTENSITY: "フィルター EG の効き（カットオフを動かす量）",
    Role.FILTER_EG_START_LEVEL: "フィルター EG のスタート・レベル",
    Role.FILTER_EG_ATTACK_LEVEL: "フィルター EG のアタック・レベル",
    Role.FILTER_EG_BREAK_LEVEL: "フィルター EG のブレイク・レベル",
    Role.FILTER_EG_ATTACK: "フィルター EG のアタック・タイム",
    Role.FILTER_EG_DECAY: "フィルター EG のディケイ・タイム",
    Role.FILTER_EG_SLOPE: "フィルター EG のスロープ・タイム",
    Role.FILTER_EG_SUSTAIN: "フィルター EG のサステイン・レベル",
    Role.FILTER_EG_RELEASE: "フィルター EG のリリース・タイム",
    Role.AMP_EG_START_LEVEL: "アンプ EG のスタート・レベル",
    Role.AMP_EG_ATTACK_LEVEL: "アンプ EG のアタック・レベル",
    Role.AMP_EG_BREAK_LEVEL: "アンプ EG のブレイク・レベル",
    Role.AMP_EG_ATTACK: "アンプ EG のアタック・タイム",
    Role.AMP_EG_DECAY: "アンプ EG のディケイ・タイム",
    Role.AMP_EG_SLOPE: "アンプ EG のスロープ・タイム",
    Role.AMP_EG_SUSTAIN: "アンプ EG のサステイン・レベル",
    Role.AMP_EG_RELEASE: "アンプ EG のリリース・タイム",
}
