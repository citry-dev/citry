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

# One name an import binds: the dotted module it loads (relative to
# `scripts/` for a package import), the attribute it takes from that module
# (None for a plain `import`), and the local name it binds.
_Binding = tuple[str, str | None, str]


def _is_package_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.level == 0 and (node.module == "scripts" or (node.module or "").startswith("scripts."))
    if isinstance(node, ast.Import):
        return any(alias.name == "scripts" or alias.name.startswith("scripts.") for alias in node.names)
    return False


def _bindings(statement: ast.stmt) -> list[_Binding]:
    """Return what an import binds, e.g. `("helper", None, "helper")` for `import helper`."""
    if isinstance(statement, ast.ImportFrom):
        # Only absolute imports can name a sibling file of the script.
        if statement.level or statement.module is None:
            return []
        return [(statement.module, alias.name, alias.asname or alias.name) for alias in statement.names]
    if isinstance(statement, ast.Import):
        return [(alias.name, None, alias.asname or alias.name.split(".")[0]) for alias in statement.names]
    return []


def _file_run_bindings(statement: ast.stmt) -> list[_Binding | None]:
    """
    Return what the ImportError fallback must import for each name a `scripts.*` import binds.

    `from scripts import helper` becomes `import helper`, and
    `from scripts.a import X` becomes `from a import X`, because a script
    started as `python scripts/name.py` has `scripts/` itself first on the
    import path. None marks a name no fallback can bind, such as the
    `scripts` that `import scripts.a` binds.
    """
    if isinstance(statement, ast.ImportFrom):
        module = statement.module or ""
        if module == "scripts":
            return [(alias.name, None, alias.asname or alias.name) for alias in statement.names]
        return [(module.removeprefix("scripts."), alias.name, alias.asname or alias.name) for alias in statement.names]
    if isinstance(statement, ast.Import):
        return [
            (alias.name.removeprefix("scripts."), None, alias.asname)
            if alias.asname and alias.name.startswith("scripts.")
            else None
            for alias in statement.names
        ]
    return []


def _fallback_bindings(node: ast.Try) -> set[_Binding]:
    """Return what the ImportError handlers of `node` import."""
    bindings: set[_Binding] = set()
    for handler in node.handlers:
        if handler.type is None:
            # A bare `except:` catches the failed import too.
            caught = _IMPORT_ERRORS
        else:
            types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
            caught = {name.id for name in types if isinstance(name, ast.Name)}
        if caught & _IMPORT_ERRORS:
            for statement in handler.body:
                bindings.update(_bindings(statement))
    return bindings


def _module_exists(scripts_dir: Path, module: str) -> bool:
    # A fallback that names a missing file raises its own ImportError when the
    # script runs as a file, so the guard only counts when the sibling is there.
    path = scripts_dir.joinpath(*module.split("."))
    return path.with_suffix(".py").is_file() or (path / "__init__.py").is_file()


def imports_package_unguarded(source: str, scripts_dir: Path) -> bool:
    """
    Return whether the script imports `scripts.*` without a working fallback for running as a file.

    A guarded import sits in a `try` whose ImportError handler imports the
    same module from `scripts_dir` without the `scripts.` prefix, under the
    same names, and that module must exist there.
    """
    guarded: set[int] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        fallback = _fallback_bindings(node)
        for statement in node.body:
            if not _is_package_import(statement):
                continue
            expected = _file_run_bindings(statement)
            # Every name must come back from the same sibling module, or the
            # script run as a file fails later with a NameError or uses the
            # wrong object.
            if all(
                binding is not None and binding in fallback and _module_exists(scripts_dir, binding[0])
                for binding in expected
            ):
                guarded.add(id(statement))
    return any(_is_package_import(node) and id(node) not in guarded for node in ast.walk(tree))


def check() -> list[str]:
    """Report each workflow that runs a script as a file when the script imports `scripts.*`."""
    problems: list[str] = []
    scripts_dir = ROOT / "scripts"
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for name in sorted(set(FILE_COMMAND.findall(text))):
            script = scripts_dir / f"{name}.py"
            if script.is_file() and imports_package_unguarded(script.read_text(encoding="utf-8"), scripts_dir):
                problems.append(
                    f"{workflow.relative_to(ROOT).as_posix()} runs scripts/{name}.py as a file, but it imports "
                    "scripts.* without an ImportError fallback that imports the same scripts/ module "
                    "under the same names (`from scripts import x` -> `import x`, "
                    "`from scripts.a import x` -> `from a import x`); "
                    f"add that fallback or run it with `python -m scripts.{name}` from the repository root"
                )
    return problems
