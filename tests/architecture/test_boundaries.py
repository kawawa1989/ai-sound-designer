from pathlib import Path

import pytest

from tests.architecture.import_rules import find_violations

SRC = Path(__file__).resolve().parents[2] / "src"


def test_project_has_no_boundary_violations() -> None:
    violations = find_violations(SRC)
    assert not violations, "\n".join(map(str, violations))


def _make_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, body in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (
            {"synth_ai/core/audio/x.py": "from synth_ai.adapters.kronos2 import Kronos2Adapter\n"},
            "core must not import synth_ai.adapters.kronos2",
        ),
        (
            {"synth_ai/core/audio/x.py": "from ...adapters import kronos2\n"},
            "core must not import synth_ai.adapters.kronos2",
        ),
        (
            {"synth_ai/core/x.py": "import synth_ai.cli\n"},
            "core must not import synth_ai.cli",
        ),
        (
            {"synth_ai/core/workflow/x.py": 'if synth == "kronos2":\n    pass\n'},
            "synth-specific name",
        ),
        (
            {"synth_ai/adapters/pc3a8/x.py": "from synth_ai.adapters.kronos2 import adapter\n"},
            "adapter must not import synth_ai.adapters.kronos2",
        ),
        (
            {"synth_ai/infrastructure/midi/x.py": "from synth_ai.adapters import fake\n"},
            "infrastructure must not import synth_ai.adapters",
        ),
    ],
)
def test_checker_detects_violations(tmp_path: Path, files: dict[str, str], expected: str) -> None:
    violations = find_violations(_make_tree(tmp_path, files))
    assert any(expected in v.message for v in violations), violations


def test_checker_allows_core_to_use_contract(tmp_path: Path) -> None:
    root = _make_tree(
        tmp_path,
        {
            "synth_ai/core/workflow/x.py": "from synth_ai.adapters.base import SynthAdapter\n",
            "synth_ai/adapters/kronos2/x.py": "from synth_ai.adapters.base import Capabilities\n"
            "from synth_ai.adapters.kronos2 import adapter\n",
        },
    )
    assert find_violations(root) == []
