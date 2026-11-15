"""
citry-lsp imports from Citry only through ``citry._lsp_support`` and a few covered public names.

``citry._lsp_support`` keeps its names and signatures for all of citry 1.x
(citry's ``test_lsp_support_module.py`` checks that), so an installed
citry-lsp keeps working next to a newer citry. Any other private Citry
module, or an experimental name, may change in a citry minor release.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import citry

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# Public names the 1.x promise already covers (they are in `citry.__all__`
# and not marked experimental), so importing them from `citry` is safe.
# Add a name here only when Citry's docs cover it; an experimental or
# private name goes through `citry._lsp_support` instead.
COVERED_CITRY_NAMES = frozenset(
    {
        "Citry",
        "Component",
        "ComponentCatalog",
        "ComponentLibrary",
        "LibraryComponent",
        "LintSeverity",
        "LspPosition",
        "LspRange",
        "SlotInput",
    }
)


def _python_files() -> list[Path]:
    """Every Python file of the package and its tests, the code a release check runs."""
    return sorted([*(PACKAGE_ROOT / "citry_lsp").rglob("*.py"), *(PACKAGE_ROOT / "tests").rglob("*.py")])


def _citry_imports(path: Path, root: Path = PACKAGE_ROOT) -> list[str]:
    """Describe each import of a Citry module or name in one file that the rule does not allow."""
    problems = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = path.relative_to(root)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # `import citry` alone gives only the covered top-level names;
            # `import citry.x` reaches a submodule.
            problems += [
                f"{relative}:{node.lineno}: import {alias.name}"
                for alias in node.names
                if alias.name.startswith("citry.")
            ]
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            if node.module == "citry":
                problems += [
                    f"{relative}:{node.lineno}: from citry import {alias.name}"
                    for alias in node.names
                    if alias.name not in COVERED_CITRY_NAMES
                ]
            elif node.module.startswith("citry.") and node.module != "citry._lsp_support":
                problems.append(f"{relative}:{node.lineno}: from {node.module} import ...")
    return problems


def test_citry_lsp_imports_citry_only_through_the_versioned_module() -> None:
    problems = [problem for path in _python_files() for problem in _citry_imports(path)]
    assert not problems, (
        "import these from citry._lsp_support (and add them there), or from citry when 1.x covers them:\n"
        + "\n".join(problems)
    )


@pytest.mark.parametrize("name", sorted(COVERED_CITRY_NAMES))
def test_covered_names_are_public(name: str) -> None:
    assert name in citry.__all__


def test_the_rule_reports_private_and_experimental_imports(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text(
        "from citry import Citry, TemplateAnalysis\n"
        "from citry._walk import run\n"
        "from citry._lsp_support import run\n"
        "import citry.analysis\n"
        "from citry_lsp import engine\n",
        encoding="utf-8",
    )
    assert _citry_imports(sample, tmp_path) == [
        "sample.py:1: from citry import TemplateAnalysis",
        "sample.py:2: from citry._walk import ...",
        "sample.py:4: import citry.analysis",
    ]
