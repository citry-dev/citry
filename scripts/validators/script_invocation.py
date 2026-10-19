"""Keep workflow commands able to import the scripts they run."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# `python scripts/name.py` puts `scripts/` itself on the import path, so a
# script started that way cannot import `scripts.*` and fails on its first line.
FILE_COMMAND = re.compile(r"\bpython[0-9.]*\s+(?:\./)?scripts/([A-Za-z0-9_]+)\.py\b")
PACKAGE_IMPORT = re.compile(r"^\s*(?:from\s+scripts[.\s]|import\s+scripts\b)", re.MULTILINE)


def check() -> list[str]:
    """Report each workflow that runs a script as a file when the script imports `scripts.*`."""
    problems: list[str] = []
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for name in sorted(set(FILE_COMMAND.findall(text))):
            script = ROOT / "scripts" / f"{name}.py"
            if script.is_file() and PACKAGE_IMPORT.search(script.read_text(encoding="utf-8")):
                problems.append(
                    f"{workflow.relative_to(ROOT).as_posix()} runs scripts/{name}.py as a file, but it imports "
                    f"scripts.*; run it with `python -m scripts.{name}` from the repository root"
                )
    return problems
