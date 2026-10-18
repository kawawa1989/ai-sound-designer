"""Core / Adapter の依存境界を AST で検査する。

ルール:
- core は synth_ai.core と synth_ai.adapters.base 以外の synth_ai を import しない
- core のソースに機種名・エンジン名を書かない（機種別分岐の防止）
- 各 Adapter は他の Adapter を import しない（base は可）
- infrastructure は adapters を import しない
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

PACKAGE = "synth_ai"
CORE_ALLOWED = ("synth_ai.core", "synth_ai.adapters.base")
SYNTH_SPECIFIC_WORDS = re.compile(
    r"kronos|pc3a8|korg|kurzweil|v\.a\.s\.t|\bkva\b|\bal-1\b|\bmod-7\b|\bhd-1\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def module_name(src_root: Path, path: Path) -> str:
    parts = list(path.relative_to(src_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imported_modules(tree: ast.AST, module: str, is_package: bool) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = module.split(".")
                drop = node.level - 1 if is_package else node.level
                base = base[: len(base) - drop] if drop else base
                target = ".".join(base + ([node.module] if node.module else []))
            else:
                target = node.module or ""
            found.append((node.lineno, target))
            # from synth_ai.adapters import kronos2 のような形も拾う
            found += [(node.lineno, f"{target}.{alias.name}") for alias in node.names]
    return found


def _within(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def adapter_package(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) >= 3 and parts[:2] == [PACKAGE, "adapters"] and parts[2] != "base":
        return ".".join(parts[:3])
    return None


def find_violations(src_root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted((src_root / PACKAGE).rglob("*.py")):
        module = module_name(src_root, path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports = imported_modules(tree, module, path.name == "__init__.py")
        internal = [(line, name) for line, name in imports if _within(name, PACKAGE)]

        if _within(module, f"{PACKAGE}.core"):
            for line, name in internal:
                if not any(_within(name, allowed) for allowed in CORE_ALLOWED):
                    violations.append(Violation(path, line, f"core must not import {name}"))
            for lineno, text in enumerate(source.splitlines(), start=1):
                if match := SYNTH_SPECIFIC_WORDS.search(text):
                    violations.append(
                        Violation(path, lineno, f"synth-specific name {match.group()!r} in core")
                    )

        own_adapter = adapter_package(module)
        if own_adapter:
            for line, name in internal:
                other = adapter_package(name)
                if other and other != own_adapter:
                    violations.append(Violation(path, line, f"adapter must not import {name}"))

        if _within(module, f"{PACKAGE}.infrastructure"):
            for line, name in internal:
                if _within(name, f"{PACKAGE}.adapters"):
                    violations.append(
                        Violation(path, line, f"infrastructure must not import {name}")
                    )
    return violations
