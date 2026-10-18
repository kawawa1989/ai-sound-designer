"""差分から次の調整案を最大 3 件選ぶ。

Adapter が具体的なパラメータを提案できればそれを使い、できなければ
機種に依存しない「どの音響特徴をどちらに動かすか」だけを提案する。
"""

from __future__ import annotations

from synth_ai.adapters.base import AdjustmentAdvisor, SynthAdapter
from synth_ai.core.comparison.models import (
    SEGMENT_LABELS,
    AdjustmentSuggestion,
    Difference,
    DifferenceKind,
)
from synth_ai.core.comparison.wording import as_feature, fix_word, fmt
from synth_ai.core.sound_spec.features import Feature
from synth_ai.core.sound_spec.models import PatchRecipe, SoundSpec

MAX_SUGGESTIONS = 3

# 同じ操作で直る特徴をまとめ、1 つの調整案にする
FEATURE_GROUPS: dict[Feature, str] = {
    Feature.ATTACK_TIME: "attack",
    Feature.DECAY_TIME: "decay",
    Feature.DECAY_RATE: "decay",
    Feature.SUSTAIN_LEVEL: "sustain",
    Feature.RELEASE_TIME: "release",
    Feature.BRIGHTNESS: "brightness",
    Feature.BRIGHTNESS_END: "brightness",
    Feature.HARMONIC_SLOPE: "brightness",
    Feature.BRIGHTNESS_START: "brightness_motion",
    Feature.BRIGHTNESS_CHANGE: "brightness_motion",
    Feature.BRIGHTNESS_DECAY_TIME: "brightness_time",
    Feature.NOISINESS: "noise",
    Feature.HARMONICITY: "partials",
    Feature.INHARMONICITY: "partials",
    Feature.ODD_EVEN_RATIO: "waveform",
}


def significant_features(differences: tuple[Difference, ...]) -> list[Difference]:
    """有意な特徴の差を、グループごとに最も大きいものだけ残して大きい順に返す。"""
    seen: set[str] = set()
    out = []
    for d in sorted(differences, key=lambda d: d.severity, reverse=True):
        feature = as_feature(d.feature)
        if d.kind is not DifferenceKind.FEATURE or feature is None or d.severity < 1.0:
            continue
        group = FEATURE_GROUPS.get(feature, feature.value)
        if group in seen:
            continue
        seen.add(group)
        out.append(d)
    return out


def generic_suggestions(differences: tuple[Difference, ...]) -> tuple[AdjustmentSuggestion, ...]:
    out: list[AdjustmentSuggestion] = []
    for d in significant_features(differences)[:MAX_SUGGESTIONS]:
        feature = as_feature(d.feature)
        assert feature is not None
        out.append(
            AdjustmentSuggestion(
                priority=len(out) + 1,
                message=f"{fix_word(feature, d.delta)}（目標 {fmt(d.reference)} {d.unit}、"
                f"現在 {fmt(d.recording)} {d.unit}）",
                feature=d.feature,
                reason=d.message,
            )
        )
    if not out:
        # 特徴量に有意差がなければ、区間 × 周波数帯の差から 1 件だけ示す
        band = next(
            (d for d in differences if d.kind is DifferenceKind.BAND and d.severity >= 1.0), None
        )
        if band is not None and band.segment is not None:
            verb = "弱める" if band.delta > 0 else "強める"
            out.append(
                AdjustmentSuggestion(
                    priority=1,
                    message=f"{SEGMENT_LABELS[band.segment]}の {band.band} Hz 付近を{verb}",
                    reason=band.message,
                )
            )
    return tuple(out)


def suggest(
    spec: SoundSpec,
    differences: tuple[Difference, ...],
    recipe: PatchRecipe | None,
    adapter: SynthAdapter | None,
) -> tuple[AdjustmentSuggestion, ...]:
    suggestions: tuple[AdjustmentSuggestion, ...] = ()
    if (
        adapter is not None
        and isinstance(adapter, AdjustmentAdvisor)
        and adapter.capabilities().is_supported("adjustment_suggestions")
    ):
        suggestions = adapter.suggest_adjustments(spec, differences, recipe)
    if not suggestions:
        suggestions = generic_suggestions(differences)
    return tuple(
        s.model_copy(update={"priority": i}) for i, s in enumerate(suggestions[:MAX_SUGGESTIONS], 1)
    )
