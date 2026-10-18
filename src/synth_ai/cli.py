"""synth-ai コマンドラインインターフェース。"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer

from synth_ai import __version__
from synth_ai.registry import ADAPTER_FACTORIES, get_adapter

app = typer.Typer(no_args_is_help=True, help="AI Sound Designer")
trial_app = typer.Typer(no_args_is_help=True, help="試行（録音と比較）の記録")
app.add_typer(trial_app, name="trial")


@app.command()
def version() -> None:
    """バージョンを表示する。"""
    typer.echo(__version__)


@app.command()
def adapters() -> None:
    """登録済みの機種と Capabilities を表示する。"""
    for synth_id in sorted(ADAPTER_FACTORIES):
        caps = get_adapter(synth_id).capabilities()
        typer.echo(caps.model_dump_json(indent=2))


@app.command()
def analyze(
    wav: Annotated[Path, typer.Argument(help="解析する参照WAV（単音）")],
    out: Annotated[Path, typer.Option("--out", "-o", help="出力先ディレクトリ")],
    analysis_id: Annotated[
        str | None, typer.Option("--id", help="解析ID（既定: ref-<sha256先頭8桁>）")
    ] = None,
    plots: Annotated[bool, typer.Option("--plots/--no-plots", help="グラフを出力する")] = True,
) -> None:
    """参照WAVを解析し、analysis.json とグラフを出力する。"""
    from synth_ai.core.audio.analyze import analyze_file
    from synth_ai.core.audio.load import AudioLoadError
    from synth_ai.core.audio.plots import plot_all
    from synth_ai.core.audio.summary import summarize
    from synth_ai.core.sound_spec.io import save_json

    try:
        result = analyze_file(wav, analysis_id)
    except AudioLoadError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    save_json(result.analysis, out / "analysis.json")
    written = [out / "analysis.json"]
    # 比較のときに同じ参照音を使えるよう、試行ディレクトリにコピーしておく
    reference_copy = out / "reference.wav"
    if wav.resolve() != reference_copy.resolve():
        shutil.copyfile(wav, reference_copy)
        written.append(reference_copy)
    if plots:
        written += plot_all(result, out)
    typer.echo(summarize(result.analysis))
    typer.echo("\n出力:")
    for path in written:
        typer.echo(f"  {path}")


@app.command()
def spec(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
) -> None:
    """analysis.json から機種非依存の sound_spec.json を作る。"""
    from synth_ai.core.workflow.files import MissingRunFileError, write_sound_spec

    try:
        sound_spec, path = write_sound_spec(run_dir)
    except MissingRunFileError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    t, e = sound_spec.timbre, sound_spec.envelope
    typer.echo(f"SoundSpec: {sound_spec.spec_id}")
    typer.echo(
        f"  音色: 倍音 {t.harmonicity} / 明るさ {t.brightness} / "
        f"明るさの減衰 {t.brightness_decay} / ノイズ {t.noisiness}"
    )
    typer.echo(f"  包絡: A {e.attack} / D {e.decay} / S {e.sustain} / R {e.release}")
    for h in sound_spec.hypotheses:
        typer.echo(f"  仮説: {h.method.value} ({h.confidence:.2f}) {h.rationale}")
    for u in sound_spec.uncertainties:
        typer.echo(f"  注意: {u}")
    typer.echo(f"\n出力: {path}")


@app.command()
def recipe(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    synth: Annotated[str, typer.Option("--synth", "-s", help="対象機種")] = "kronos2",
) -> None:
    """SoundSpec から機種別のレシピ（recipe.json / recipe.md）を作る。"""
    from synth_ai.core.workflow.files import MissingRunFileError, write_recipe
    from synth_ai.core.workflow.recipe import RecipeContractError

    try:
        files = write_recipe(run_dir, get_adapter(synth))
    except (MissingRunFileError, ValueError, RecipeContractError) as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(files.markdown_path.read_text(encoding="utf-8"))
    typer.echo(f"出力:\n  {files.json_path}\n  {files.markdown_path}")


@app.command()
def compare(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    recording: Annotated[Path, typer.Argument(help="シンセで鳴らして録音した WAV")],
    synth: Annotated[str | None, typer.Option("--synth", "-s", help="対象機種")] = "kronos2",
    plots: Annotated[bool, typer.Option("--plots/--no-plots", help="グラフを出力する")] = True,
) -> None:
    """録音を参照音と比べ、差分と次の調整案を試行として保存する。"""
    from synth_ai.core.audio.load import AudioLoadError
    from synth_ai.core.workflow.files import MissingRunFileError
    from synth_ai.core.workflow.trial import ReferenceMismatchError, run_trial

    try:
        adapter = get_adapter(synth) if synth else None
        result = run_trial(run_dir, recording, adapter, plots=plots)
    except (AudioLoadError, MissingRunFileError, ReferenceMismatchError, ValueError) as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(result.markdown)
    typer.echo(f"出力: {result.directory}")


@trial_app.command("list")
def trial_list(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
) -> None:
    """試行の一覧（距離、主な違い、評価）を表示する。"""
    from synth_ai.core.history.store import rebuild_history

    history = rebuild_history(run_dir)
    if not history.trials:
        typer.echo("試行はまだありません（synth-ai compare で追加）")
        return
    for t in history.trials:
        note = t.note
        rating = (
            f"近さ {note.closeness or '-'} / 好み {note.preference or '-'}" if note else "未評価"
        )
        typer.echo(
            f"[{t.trial:03d}] {t.created_at}  距離 {t.distance_db:.1f} dB  "
            f"有意な差 {t.significant_differences} 件  {rating}"
        )
        for d in t.top_differences:
            typer.echo(f"      - {d}")
        if note and note.memo:
            typer.echo(f"      メモ: {note.memo}")


@trial_app.command("note")
def trial_note(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    trial: Annotated[int, typer.Argument(help="試行番号")],
    closeness: Annotated[
        int | None, typer.Option(min=1, max=5, help="目標への近さ（1〜5）")
    ] = None,
    preference: Annotated[int | None, typer.Option(min=1, max=5, help="好み（1〜5）")] = None,
    memo: Annotated[str | None, typer.Option(help="感想・気づき")] = None,
    change: Annotated[
        list[str] | None, typer.Option(help="実機で変えた内容（複数回指定可）")
    ] = None,
) -> None:
    """試行に人の評価を記録する。近さと好みは別々に記録する。"""
    from synth_ai.core.history.store import save_note

    try:
        note = save_note(
            run_dir,
            trial,
            closeness=closeness,
            preference=preference,
            memo=memo,
            changes=tuple(change or ()),
        )
    except FileNotFoundError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(note.model_dump_json(indent=2))


@app.command("test-signals")
def test_signals(
    out: Annotated[Path, typer.Argument(help="出力先ディレクトリ")] = Path("assets/test"),
) -> None:
    """解析器の確認用に合成テスト音（WAV）を書き出す。"""
    from synth_ai.core.synthesis.test_signals import standard_set, write_wav

    for name, samples in standard_set().items():
        typer.echo(str(write_wav(out / f"{name}.wav", samples)))


if __name__ == "__main__":
    app()
