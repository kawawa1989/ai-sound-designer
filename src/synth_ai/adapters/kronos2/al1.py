"""SoundSpec から AL-1（減算合成）で調整する項目を決める。"""

from __future__ import annotations

from synth_ai.adapters.kronos2.intents import Intent
from synth_ai.adapters.kronos2.roles import ChoiceTag, Role
from synth_ai.core.sound_spec.derive import target_of
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import Level, SoundSpec, StepAction

NOISY = (Level.MEDIUM, Level.HIGH, Level.VERY_HIGH)


def choose_waveform(spec: SoundSpec) -> tuple[ChoiceTag, str]:
    slope = target_of(spec, Feature.HARMONIC_SLOPE)
    odd_even = target_of(spec, Feature.ODD_EVEN_RATIO)
    if slope is None or odd_even is None:
        return ChoiceTag.SAW, "倍音の情報がないため、倍音を最も多く含むノコギリ波から始める"
    if spec.timbre.harmonicity in (Level.VERY_LOW, Level.LOW, Level.MEDIUM):
        return ChoiceTag.SAW, (
            "整数倍音以外の成分が多く、波形の選択だけでは再現できない。"
            "倍音を最も多く含むノコギリ波から近似する"
        )
    if spec.timbre.brightness is Level.VERY_LOW and slope.value < -15:
        return ChoiceTag.SINE, "倍音がほとんどなく、基音が中心"
    if odd_even.value > 15:
        if slope.value < -9:
            return ChoiceTag.TRIANGLE, (
                f"奇数次の倍音が中心で、急に減衰する（{slope.value:.1f} dB/oct）"
            )
        return ChoiceTag.SQUARE, (f"奇数次の倍音が偶数次より {odd_even.value:.0f} dB 以上強い")
    return ChoiceTag.SAW, (
        f"奇数次・偶数次の倍音がそろっていて、{slope.value:.1f} dB/oct で減衰する"
        "（ノコギリ波は約 -6 dB/oct）"
    )


def al1_intents(spec: SoundSpec) -> list[Intent]:
    intents: list[Intent] = []
    wave, reason = choose_waveform(spec)
    intents.append(Intent(Role.OSCILLATOR_WAVEFORM, StepAction.SELECT, reason, choice=wave))

    noise = target_of(spec, Feature.NOISINESS)
    if spec.timbre.noisiness in NOISY and noise is not None:
        intents.append(
            Intent(Role.NOISE_LEVEL, StepAction.SET, "倍音の間にノイズ成分がある", target=noise)
        )

    intents.append(
        Intent(
            Role.FILTER_TYPE,
            StepAction.SELECT,
            "高域を削って明るさを調整する",
            choice=ChoiceTag.LOWPASS,
        )
    )

    darkening = spec.timbre.brightness_decay is not None
    cutoff_target = target_of(spec, Feature.BRIGHTNESS_END if darkening else Feature.BRIGHTNESS)
    if cutoff_target is not None:
        reason = (
            "鳴り終わりに近い部分の明るさに合わせる（発音直後の明るさはフィルター EG で足す）"
            if darkening
            else "音全体の明るさに合わせる"
        )
        intents.append(Intent(Role.FILTER_CUTOFF, StepAction.SET, reason, target=cutoff_target))

    if darkening:
        change = target_of(spec, Feature.BRIGHTNESS_CHANGE)
        if change is not None:
            intents.append(
                Intent(
                    Role.FILTER_EG_INTENSITY,
                    StepAction.SET,
                    "発音直後が明るく、時間とともに暗くなる"
                    f"（終盤は発音直後の {change.value:.2f} 倍）",
                    target=change,
                )
            )
        intents.append(
            Intent(
                Role.FILTER_EG_ATTACK,
                StepAction.SET,
                "発音した瞬間がいちばん明るい",
                extreme="min",
            )
        )
        decay = target_of(spec, Feature.BRIGHTNESS_DECAY_TIME)
        if decay is not None:
            intents.append(
                Intent(
                    Role.FILTER_EG_DECAY,
                    StepAction.SET,
                    "明るさが下がる速さに合わせる",
                    target=decay,
                )
            )
        intents.append(
            Intent(
                Role.FILTER_EG_SUSTAIN,
                StepAction.SET,
                "持続部の明るさはカットオフで決めるため、EG は最後まで閉じる",
                extreme="min",
            )
        )

    attack = target_of(spec, Feature.ATTACK_TIME)
    if attack is not None:
        intents.append(
            Intent(Role.AMP_EG_ATTACK, StepAction.SET, "音量の立ち上がりに合わせる", target=attack)
        )
    decay = target_of(spec, Feature.DECAY_TIME)
    if decay is not None:
        intents.append(
            Intent(
                Role.AMP_EG_DECAY,
                StepAction.SET,
                "ピーク後の音量の下がり方に合わせる",
                target=decay,
            )
        )
    sustain = target_of(spec, Feature.SUSTAIN_LEVEL)
    if spec.envelope.sustain is Level.VERY_LOW or sustain is None:
        intents.append(
            Intent(
                Role.AMP_EG_SUSTAIN,
                StepAction.SET,
                "鍵盤を押し続けても音量が保たれない（減衰していく）",
                extreme="min",
            )
        )
    else:
        intents.append(
            Intent(Role.AMP_EG_SUSTAIN, StepAction.SET, "持続部の音量に合わせる", target=sustain)
        )
    release = target_of(spec, Feature.RELEASE_TIME)
    if release is not None:
        intents.append(
            Intent(
                Role.AMP_EG_RELEASE,
                StepAction.SET,
                "鍵盤を離した後の余韻に合わせる",
                target=release,
            )
        )
    return intents
