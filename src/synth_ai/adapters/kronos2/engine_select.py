"""SoundSpec の合成仮説から、KRONOS 2 の音源エンジン候補を順位付けする。

Core が出す機種非依存の仮説（減算合成・FM・サンプル再生など）を、
対象エンジン（AL-1 / MOD-7 / HD-1）に対応付ける。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from synth_ai.core.sound_spec.models import Level, SoundSpec, SynthesisMethod

AL1, MOD7, HD1 = "AL-1", "MOD-7", "HD-1"

METHOD_TO_ENGINE: dict[SynthesisMethod, str] = {
    SynthesisMethod.SUBTRACTIVE: AL1,
    SynthesisMethod.FM: MOD7,
    SynthesisMethod.SAMPLE_BASED: HD1,
}

ENGINE_DESCRIPTIONS = {
    AL1: "アナログモデリング（減算合成）",
    MOD7: "VPM / FM などの変調合成",
    HD1: "PCM マルチサンプル再生",
}


@dataclass
class EngineScore:
    engine: str
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return f"{ENGINE_DESCRIPTIONS[self.engine]}: " + "、".join(self.reasons)


def rank_engines(spec: SoundSpec) -> list[EngineScore]:
    """対象エンジンすべてのスコア（0〜1）と理由を、高い順に返す。"""
    scores = {engine: EngineScore(engine) for engine in (AL1, MOD7, HD1)}
    for hypothesis in spec.hypotheses:
        engine = METHOD_TO_ENGINE.get(hypothesis.method)
        if engine is None:
            continue
        entry = scores[engine]
        if hypothesis.confidence > entry.score:
            entry.score = hypothesis.confidence
        entry.reasons.append(hypothesis.rationale)

    # 撥弦・打撃的な音は、AL-1 でもフィルター EG を速く閉じれば近づけられる
    physical = next(
        (h for h in spec.hypotheses if h.method is SynthesisMethod.PHYSICAL_MODEL), None
    )
    if physical is not None:
        al1 = scores[AL1]
        al1.score = max(al1.score, physical.confidence * 0.8)
        al1.reasons.append("撥弦・打撃的な減衰はフィルター EG とアンプ EG で近似できる")

    # 整数倍音が非常に明瞭な音は、FM より減算合成のほうが調整しやすい
    if spec.timbre.harmonicity is Level.VERY_HIGH and scores[MOD7].score > 0:
        scores[MOD7].score *= 0.7

    for entry in scores.values():
        entry.score = round(min(entry.score, 1.0), 2)
        if not entry.reasons:
            entry.reasons.append("解析結果からは積極的な根拠がない")
    return sorted(scores.values(), key=lambda e: e.score, reverse=True)
