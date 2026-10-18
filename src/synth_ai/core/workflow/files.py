"""試行ディレクトリ（runs/<id>/）のファイル配置と、解析→SoundSpec→レシピの保存。

runs/<id>/
  analysis.json, *.png       参照音の解析
  sound_spec.json            機種非依存の目標
  recipes/<synth_id>/        機種ごとのレシピ（recipe.json, recipe.md）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from synth_ai.adapters.base import SynthAdapter
from synth_ai.core.sound_spec.derive import derive_sound_spec
from synth_ai.core.sound_spec.io import load_json, save_json
from synth_ai.core.sound_spec.models import AudioAnalysis, PatchRecipe, SoundSpec
from synth_ai.core.workflow.recipe import generate_recipe

ANALYSIS = "analysis.json"
SOUND_SPEC = "sound_spec.json"


class MissingRunFileError(FileNotFoundError):
    """前の段階の出力がまだない。"""


@dataclass(frozen=True)
class RecipeFiles:
    recipe: PatchRecipe
    json_path: Path
    markdown_path: Path


def _require(path: Path, hint: str) -> Path:
    if not path.is_file():
        raise MissingRunFileError(f"{path} がありません。先に {hint} を実行してください")
    return path


def recipe_dir(run_dir: Path, synth_id: str) -> Path:
    return run_dir / "recipes" / synth_id


def write_sound_spec(run_dir: Path) -> tuple[SoundSpec, Path]:
    analysis = load_json(AudioAnalysis, _require(run_dir / ANALYSIS, "analyze"))
    spec = derive_sound_spec(analysis)
    path = run_dir / SOUND_SPEC
    save_json(spec, path)
    return spec, path


def load_or_derive_spec(run_dir: Path) -> SoundSpec:
    path = run_dir / SOUND_SPEC
    if path.is_file():
        return load_json(SoundSpec, path)
    return write_sound_spec(run_dir)[0]


def write_recipe(run_dir: Path, adapter: SynthAdapter) -> RecipeFiles:
    """保存済みの SoundSpec（なければ解析から作る）を変更せずに、機種別レシピを書き出す。"""
    spec = load_or_derive_spec(run_dir)
    recipe = generate_recipe(spec, adapter)
    out = recipe_dir(run_dir, adapter.synth_id)
    json_path, markdown_path = out / "recipe.json", out / "recipe.md"
    save_json(recipe, json_path)
    markdown_path.write_text(adapter.manual_instructions(recipe), encoding="utf-8")
    return RecipeFiles(recipe, json_path, markdown_path)
