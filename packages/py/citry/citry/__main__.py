"""
The ``citry`` command-line entry point.

Resolves which engine to run against, then builds and runs the command tree. A
leading ``--app module:attribute`` points engine-backed commands at an
explicitly constructed ``Citry`` (the same ``module:object`` convention
web-server entry points use). ``check`` defers that import until its own
arguments are validated. ``format`` rejects app selection without importing
the target because formatting is source-only. Registered as the ``citry``
console script in ``pyproject.toml``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from citry._app_selection import AppSelectionError, CheckAppSelection, load_app
from citry.citry import Citry
from citry.citry import citry as default_engine
from citry.command import run
from citry.commands import build_cli

if TYPE_CHECKING:
    from collections.abc import Sequence


def _fail(message: str) -> NoReturn:
    """Print a usage error to stderr and exit with code 2 (argparse's convention)."""
    sys.stderr.write(f"citry: error: {message}\n")
    raise SystemExit(2)


def _import_engine(spec: str) -> Citry:
    """Resolve a ``module:attribute`` spec to the ``Citry`` engine it names."""
    try:
        return load_app(spec)
    except AppSelectionError as exc:
        _fail(str(exc))


def _resolve_engine(argv: list[str]) -> tuple[Citry, list[str]]:
    """
    Pick the engine to run against, consuming a leading ``--app module:attribute``.

    ``--app`` is recognized only as the first argument (as ``--app VALUE`` or
    ``--app=VALUE``), so it cannot be mistaken for an option of a nested command
    further along the line. With no leading ``--app``, the default global engine
    is used and the arguments are passed through unchanged.
    """
    if argv and argv[0] == "--app":
        if len(argv) < 2:
            _fail("--app requires a value, e.g. --app myproject.app:engine")
        return _import_engine(argv[1]), argv[2:]
    if argv and argv[0].startswith("--app="):
        return _import_engine(argv[0][len("--app=") :]), argv[1:]
    return default_engine, argv


def _split_app(argv: list[str]) -> tuple[str | None, list[str]]:
    """Consume a leading app option without importing its target."""
    if argv and argv[0] == "--app":
        if len(argv) < 2:
            _fail("--app requires a value, e.g. --app myproject.app:engine")
        return argv[1], argv[2:]
    if argv and argv[0].startswith("--app="):
        return argv[0][len("--app=") :], argv[1:]
    return None, argv


def main(argv: Sequence[str] | None = None) -> int:
    """Run the citry CLI. Returns a process exit code."""
    # Resolve --app against the working directory, the way uvicorn, gunicorn,
    # and flask do: the console script (unlike 'python -m citry') starts
    # without the cwd on sys.path, so 'citry --app app:engine' would not find
    # a project-root app.py otherwise.
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    args = list(sys.argv[1:] if argv is None else argv)
    spec, rest = _split_app(args)
    is_check = bool(rest and rest[0] == "check")
    is_format = bool(rest and rest[0] == "format")
    selection: CheckAppSelection | None = None
    if spec is not None and is_format:
        _fail("--app is not accepted by citry format")
    if spec is not None and is_check:
        engine = default_engine
        selection = CheckAppSelection(spec=spec)
    elif spec is not None:
        engine = _import_engine(spec)
    else:
        engine = default_engine
        if is_check:
            selection = CheckAppSelection()
    root = build_cli(engine, check_selection=selection)
    return run(root, rest, citry=engine)


if __name__ == "__main__":
    sys.exit(main())
