"""The script invocation validator catches workflow commands that cannot import their script."""

from pathlib import Path

import pytest
from scripts.validators import script_invocation


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str, script: str) -> list[str]:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(f"run: {command}\n", encoding="utf-8")
    (tmp_path / "scripts" / "tool.py").write_text(script, encoding="utf-8")
    monkeypatch.setattr(script_invocation, "ROOT", tmp_path)
    return script_invocation.check()


def test_a_file_command_for_a_script_that_imports_the_package_is_reported(tmp_path, monkeypatch) -> None:
    # This is the shape that broke the 0.6.0 docs release at its commit step.
    problems = _repo(tmp_path, monkeypatch, "python scripts/tool.py out", "from scripts.helper import run\n")
    assert problems == [
        ".github/workflows/release.yml runs scripts/tool.py as a file, but it imports scripts.*; "
        "run it with `python -m scripts.tool` from the repository root"
    ]


@pytest.mark.parametrize(
    ("command", "script"),
    [
        # Started as a module, the repository root is on the import path.
        ("python -m scripts.tool out", "from scripts.helper import run\n"),
        # A script that imports nothing from the package runs fine as a file.
        ("python scripts/tool.py out", "import json\n"),
    ],
)
def test_commands_that_can_import_their_script_pass(tmp_path, monkeypatch, command: str, script: str) -> None:
    assert _repo(tmp_path, monkeypatch, command, script) == []
