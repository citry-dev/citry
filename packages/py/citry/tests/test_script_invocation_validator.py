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
        ".github/workflows/release.yml runs scripts/tool.py as a file, but it imports scripts.* "
        "without an ImportError fallback; run it with `python -m scripts.tool` from the repository root"
    ]


@pytest.mark.parametrize(
    ("command", "script"),
    [
        # Started as a module, the repository root is on the import path.
        ("python -m scripts.tool out", "from scripts.helper import run\n"),
        # A script that imports nothing from the package runs fine as a file.
        ("python scripts/tool.py out", "import json\n"),
        # Run as a file, the failed package import falls back to the sibling module.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper\nexcept ImportError:\n    import helper\n",
        ),
        # A tuple of exception types and an alias in both branches still bind the same name.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper as h\nexcept (KeyError, ModuleNotFoundError):\n"
            "    import helper as h\n",
        ),
        # A bare except catches the failed import too.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper\nexcept:\n    import helper\n",
        ),
    ],
)
def test_commands_that_can_import_their_script_pass(tmp_path, monkeypatch, command: str, script: str) -> None:
    assert _repo(tmp_path, monkeypatch, command, script) == []


@pytest.mark.parametrize(
    "script",
    [
        # The handler swallows the failure, so the script still has no helper module.
        "try:\n    from scripts import helper\nexcept ImportError:\n    helper = None\n",
        # Running as a file raises ImportError, which this handler does not catch.
        "try:\n    from scripts import helper\nexcept KeyError:\n    import helper\n",
        # The fallback imports something, but not the name the script goes on to use.
        "try:\n    from scripts import helper\nexcept ImportError:\n    import json\n",
        # A guarded import does not excuse a second, unguarded one.
        "try:\n    from scripts import helper\nexcept ImportError:\n    import helper\nimport scripts.other\n",
    ],
)
def test_a_package_import_without_a_working_fallback_is_reported(tmp_path, monkeypatch, script: str) -> None:
    assert len(_repo(tmp_path, monkeypatch, "python scripts/tool.py out", script)) == 1
