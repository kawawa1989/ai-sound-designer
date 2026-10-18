import json

from typer.testing import CliRunner

from synth_ai.cli import app


def test_adapters_command_lists_capabilities() -> None:
    result = CliRunner().invoke(app, ["adapters"])
    assert result.exit_code == 0
    assert '"synth_id": "kronos2"' in result.output
    assert '"parameter_write": "unverified"' in result.output


def test_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert json.loads(f'"{result.output.strip()}"')
