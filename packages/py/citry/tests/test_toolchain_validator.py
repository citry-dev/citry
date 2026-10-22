"""The toolchain validator catches a workflow that leaves the reviewed uv or PyPI upload pins."""

import json
import shutil
from pathlib import Path

import pytest
from scripts.validators import toolchain
from scripts.validators.toolchain import pinned_action_errors

_REPO = Path(__file__).resolve().parents[4]
_UV_PIN = json.loads((_REPO / "packages/py/citry_core/pyodide-build.json").read_text())["uv"]


@pytest.fixture
def root(tmp_path):
    shutil.copytree(_REPO / ".github/workflows", tmp_path / ".github/workflows")
    # Only the example CI workflows matter to the check, so copy just those.
    for workflow in _REPO.glob("examples/*/*/.github/workflows/check.yml"):
        target = tmp_path / workflow.relative_to(_REPO)
        target.parent.mkdir(parents=True)
        shutil.copy(workflow, target)
    return tmp_path


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    # Replacing exactly one occurrence proves a single stray pin is enough to fail.
    assert old in text
    path.write_text(text.replace(old, new, 1))


def test_current_workflows_pass(root):
    assert pinned_action_errors(root, _UV_PIN) == []


@pytest.mark.parametrize(
    ("relative_path", "old", "new"),
    [
        # A pin kept in the workflow env reaches setup-uv through `${{ env.UV_VERSION }}`.
        (".github/workflows/py--citry--publish.yml", f'UV_VERSION: "{_UV_PIN}"', 'UV_VERSION: "0.10.12"'),
        # One wrong pin among the several citry-core setups.
        (".github/workflows/py--citry-core--publish.yml", f'version: "{_UV_PIN}"', 'version: "0.10.12"'),
        # A publish workflow may not float to the newest uv.
        (".github/workflows/vscode--citry--publish.yml", f'version: "{_UV_PIN}"', 'version: "latest"'),
        # The starters ship this file to users.
        ("examples/starters/flask/.github/workflows/check.yml", f'version: "{_UV_PIN}"', 'version: "0.10.12"'),
        # A release workflow that leaves the version out gets whatever uv is newest.
        (".github/workflows/repo--docs-release.yml", f'version: "{_UV_PIN}"', 'cache-dependency-glob: "uv.lock"'),
    ],
)
def test_a_stray_uv_pin_fails(root, relative_path, old, new):
    _replace_once(root / relative_path, old, new)
    errors = pinned_action_errors(root, _UV_PIN)
    # An env pin reaches every setup that reads it, so one change can fail several steps.
    assert errors
    assert all(relative_path in error for error in errors)


@pytest.mark.parametrize(
    "stale",
    [
        "pypa/gh-action-pypi-publish@" + "0" * 40,
        # GitHub ignores case in the owner, so a recased old pin still runs.
        "PyPA/gh-action-pypi-publish@" + "0" * 40,
    ],
)
def test_an_old_pypi_upload_action_fails(root, stale):
    workflow = root / ".github/workflows/py--pygments-citry--publish.yml"
    _replace_once(workflow, toolchain._PYPI_ACTION, stale)
    assert any("must upload with" in error for error in pinned_action_errors(root, _UV_PIN))
