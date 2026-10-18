"""synth-ai コマンドラインインターフェース。"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from synth_ai import __version__
from synth_ai.registry import ADAPTER_FACTORIES, get_adapter

app = typer.Typer(no_args_is_help=True, help="AI Sound Designer")


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
    if plots:
        written += plot_all(result, out)
    typer.echo(summarize(result.analysis))
    typer.echo("\n出力:")
    for path in written:
        typer.echo(f"  {path}")


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
