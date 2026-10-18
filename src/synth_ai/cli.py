"""synth-ai コマンドラインインターフェース。"""

from __future__ import annotations

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


if __name__ == "__main__":
    app()
