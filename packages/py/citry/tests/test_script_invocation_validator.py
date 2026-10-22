"""The script invocation validator catches workflow commands that cannot import their script."""

from pathlib import Path

import pytest
from scripts.validators import script_invocation


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    script: str,
    siblings: tuple[str, ...] = ("helper.py",),
) -> list[str]:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".github" / "workflows" / "release.yml").write_text(f"run: {command}\n", encoding="utf-8")
    (tmp_path / "scripts" / "tool.py").write_text(script, encoding="utf-8")
    # A fallback only works when the module it names sits beside the script.
    for sibling in siblings:
        path = tmp_path / "scripts" / sibling
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    monkeypatch.setattr(script_invocation, "ROOT", tmp_path)
    return script_invocation.check()


def test_a_file_command_for_a_script_that_imports_the_package_is_reported(tmp_path, monkeypatch) -> None:
    # This is the shape that broke the 0.6.0 docs release at its commit step.
    problems = _repo(tmp_path, monkeypatch, "python scripts/tool.py out", "from scripts.helper import run\n")
    assert problems == [
        ".github/workflows/release.yml runs scripts/tool.py as a file, but it imports scripts.* "
        "without an ImportError fallback that imports the same scripts/ module under the same names "
        "(`from scripts import x` -> `import x`, `from scripts.a import x` -> `from a import x`); "
        "add that fallback or run it with `python -m scripts.tool` from the repository root"
    ]


@pytest.mark.parametrize(
    ("command", "script", "siblings"),
    [
        # Started as a module, the repository root is on the import path.
        ("python -m scripts.tool out", "from scripts.helper import run\n", ()),
        # A script that imports nothing from the package runs fine as a file.
        ("python scripts/tool.py out", "import json\n", ()),
        # Run as a file, the failed package import falls back to the sibling module.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper\nexcept ImportError:\n    import helper\n",
            ("helper.py",),
        ),
        # A name taken from a sibling module falls back to the same name from it.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts.helper import run\nexcept ImportError:\n    from helper import run\n",
            ("helper.py",),
        ),
        # A sibling package works the same way as a sibling file.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts.tools.a import run\nexcept ImportError:\n    from tools.a import run\n",
            ("tools/__init__.py", "tools/a.py"),
        ),
        # A tuple of exception types and an alias in both branches still bind the same name.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper as h\nexcept (KeyError, ModuleNotFoundError):\n"
            "    import helper as h\n",
            ("helper.py",),
        ),
        # A bare except catches the failed import too.
        (
            "python scripts/tool.py out",
            "try:\n    from scripts import helper\nexcept:\n    import helper\n",
            ("helper.py",),
        ),
    ],
)
def test_commands_that_can_import_their_script_pass(
    tmp_path, monkeypatch, command: str, script: str, siblings: tuple[str, ...]
) -> None:
    assert _repo(tmp_path, monkeypatch, command, script, siblings) == []


@pytest.mark.parametrize(
    ("script", "siblings"),
    [
        # The handler swallows the failure, so the script still has no helper module.
        ("try:\n    from scripts import helper\nexcept ImportError:\n    helper = None\n", ("helper.py",)),
        # Running as a file raises ImportError, which this handler does not catch.
        ("try:\n    from scripts import helper\nexcept KeyError:\n    import helper\n", ("helper.py",)),
        # The fallback imports something, but not the name the script goes on to use.
        ("try:\n    from scripts import helper\nexcept ImportError:\n    import json\n", ("helper.py",)),
        # The fallback binds the right name, but from a different module.
        (
            "try:\n    from scripts import helper\nexcept ImportError:\n    import other as helper\n",
            ("helper.py", "other.py"),
        ),
        (
            "try:\n    from scripts.helper import run\nexcept ImportError:\n    from other import run\n",
            ("helper.py", "other.py"),
        ),
        # The fallback names the right module, but no such file sits beside the script.
        ("try:\n    from scripts import helper\nexcept ImportError:\n    import helper\n", ()),
        # `import scripts.helper` binds `scripts`, which no file-run import can provide.
        ("try:\n    import scripts.helper\nexcept ImportError:\n    import helper\n", ("helper.py",)),
        # A guarded import does not excuse a second, unguarded one.
        (
            "try:\n    from scripts import helper\nexcept ImportError:\n    import helper\nimport scripts.other\n",
            ("helper.py", "other.py"),
        ),
    ],
)
def test_a_package_import_without_a_working_fallback_is_reported(
    tmp_path, monkeypatch, script: str, siblings: tuple[str, ...]
) -> None:
    assert len(_repo(tmp_path, monkeypatch, "python scripts/tool.py out", script, siblings)) == 1
