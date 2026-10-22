"""Keep workflow commands able to import the scripts they run."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `python scripts/name.py` puts `scripts/` itself on the import path, so an
# unguarded `scripts.*` import fails as soon as the script starts.
FILE_COMMAND = re.compile(r"\bpython[0-9.]*\s+(?:\./)?scripts/([A-Za-z0-9_]+)\.py\b")
_IMPORT_ERRORS = {"ImportError", "ModuleNotFoundError"}


def _is_package_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.level == 0 and (node.module == "scripts" or (node.module or "").startswith("scripts."))
    if isinstance(node, ast.Import):
        return any(alias.name == "scripts" or alias.name.startswith("scripts.") for alias in node.names)
    return False


def _bound_names(statements: list[ast.stmt]) -> set[str]:
    # The names an import statement makes available, e.g. `helper` for both
    # `from scripts import helper` and `import helper`.
    names: set[str] = set()
    for statement in statements:
        if isinstance(statement, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in statement.names)
        elif isinstance(statement, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in statement.names)
    return names


def _fallback_names(node: ast.Try) -> set[str]:
    """Return the names that an ImportError handler of `node` imports again."""
    names: set[str] = set()
    for handler in node.handlers:
        if handler.type is None:
            # A bare `except:` catches the failed import too.
            caught = _IMPORT_ERRORS
        else:
            types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
            caught = {name.id for name in types if isinstance(name, ast.Name)}
        if caught & _IMPORT_ERRORS:
            names |= _bound_names(handler.body)
    return names


def imports_package_unguarded(source: str) -> bool:
    """Return whether the script imports `scripts.*` without a fallback for running as a file."""
    guarded: set[int] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        fallback = _fallback_names(node)
        # The fallback must bind every name the package import binds, or the
        # file-run script would fail later with a NameError instead.
        guarded.update(
            id(statement)
            for statement in node.body
            if _is_package_import(statement) and _bound_names([statement]) <= fallback
        )
    return any(_is_package_import(node) and id(node) not in guarded for node in ast.walk(tree))


def check() -> list[str]:
    """Report each workflow that runs a script as a file when the script imports `scripts.*`."""
    problems: list[str] = []
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for name in sorted(set(FILE_COMMAND.findall(text))):
            script = ROOT / "scripts" / f"{name}.py"
            if script.is_file() and imports_package_unguarded(script.read_text(encoding="utf-8")):
                problems.append(
                    f"{workflow.relative_to(ROOT).as_posix()} runs scripts/{name}.py as a file, but it imports "
                    "scripts.* without an ImportError fallback; "
                    f"run it with `python -m scripts.{name}` from the repository root"
                )
    return problems
