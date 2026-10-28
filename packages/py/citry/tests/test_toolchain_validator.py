"""The toolchain validator catches a workflow that leaves the reviewed Rust, uv or PyPI upload setup."""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from scripts.validators import toolchain
from scripts.validators.toolchain import nightly_pin_errors, pinned_action_errors

_REPO = Path(__file__).resolve().parents[4]
_UV_PIN = json.loads((_REPO / "packages/py/citry_core/pyodide-build.json").read_text())["uv"]


@pytest.fixture
def root(tmp_path):
    shutil.copytree(_REPO / ".github/workflows", tmp_path / ".github/workflows")
    shutil.copytree(_REPO / ".github/actions", tmp_path / ".github/actions")
    shutil.copy(_REPO / "rust-toolchain.toml", tmp_path / "rust-toolchain.toml")
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
        # Neither may an ordinary test workflow.
        (".github/workflows/py--tests.yml", f'version: "{_UV_PIN}"', 'version: "latest"'),
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


def test_a_floating_setup_uv_tag_fails(root):
    # A tag can point at any setup-uv release, including one that skips the checksum.
    _replace_once(root / ".github/workflows/py--tests.yml", toolchain._UV_ACTION, "astral-sh/setup-uv@v7")
    errors = pinned_action_errors(root, _UV_PIN)
    assert any("must use" in error and "py--tests.yml" in error for error in errors)


def test_a_setup_uv_step_without_cache_pruning_fails(root):
    _replace_once(root / ".github/workflows/py--tests.yml", "prune-cache: true", "prune-cache: false")
    errors = pinned_action_errors(root, _UV_PIN)
    assert len(errors) == 1
    assert "py--tests.yml" in errors[0]
    assert "must set prune-cache: true" in errors[0]


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        ({"uses": "astral-sh/setup-uv@v7", "with": {"version": _UV_PIN, "prune-cache": True}}, "must use"),
        ({"uses": toolchain._UV_ACTION, "with": {"version": "latest", "prune-cache": True}}, "set version:"),
        ({"uses": toolchain._UV_ACTION, "with": {"version": _UV_PIN}}, "must set prune-cache: true"),
        ({"uses": "pypa/gh-action-pypi-publish@release/v1"}, "must upload with"),
    ],
)
def test_a_composite_action_follows_the_same_pins(root, step, expected):
    action = root / ".github/actions/setup/action.yml"
    action.parent.mkdir(parents=True)
    action.write_text(yaml.safe_dump({"name": "Setup", "runs": {"using": "composite", "steps": [step]}}))
    errors = pinned_action_errors(root, _UV_PIN)
    assert len(errors) == 1
    assert errors[0].startswith(".github/actions/setup/action.yml composite action")
    assert expected in errors[0]


def test_a_composite_action_with_the_reviewed_pins_passes(root):
    action = root / ".github/actions/setup/action.yml"
    action.parent.mkdir(parents=True)
    step = {"uses": toolchain._UV_ACTION, "with": {"version": _UV_PIN, "prune-cache": True}}
    action.write_text(yaml.safe_dump({"name": "Setup", "runs": {"using": "composite", "steps": [step]}}))
    assert pinned_action_errors(root, _UV_PIN) == []


def test_the_dated_nightly_and_current_workflows_pass(root):
    assert nightly_pin_errors(root) == []


@pytest.mark.parametrize("channel", ["nightly", "stable", "nightly-2026-10"])
def test_a_channel_that_is_not_a_dated_nightly_fails(root, channel):
    toolchain_file = root / "rust-toolchain.toml"
    text = toolchain_file.read_text()
    current = next(line for line in text.splitlines() if line.startswith("channel = "))
    toolchain_file.write_text(text.replace(current, f'channel = "{channel}"'))
    assert [error for error in nightly_pin_errors(root) if "rust-toolchain.toml channel" in error]


@pytest.mark.parametrize(
    "line",
    [
        # A setup action given the undated channel, in any quoting.
        "          toolchain: nightly",
        "          toolchain: 'nightly'",
        # A dated nightly in a workflow would still drift from the file.
        "          toolchain: nightly-2026-01-01",
        # The action ref its README suggests.
        "      - uses: dtolnay/rust-toolchain@nightly",
        "          rust-toolchain: nightly",
        "      - run: cargo +nightly clippy",
        "      - run: rustup toolchain install --profile minimal nightly",
        "      - run: rustup update nightly",
        '      - run: echo RUSTUP_TOOLCHAIN=nightly >> "$GITHUB_ENV"',
        "      RUSTUP_TOOLCHAIN: nightly  # for the audit",
    ],
)
def test_a_workflow_that_names_its_own_nightly_fails(root, line):
    workflow = root / ".github/workflows/rust--tests.yml"
    workflow.write_text(workflow.read_text() + line + "\n")
    errors = nightly_pin_errors(root)
    assert errors
    assert all("rust--tests.yml" in error for error in errors)


def test_a_composite_action_that_names_its_own_nightly_fails(root):
    action = root / ".github/actions/install-rust/action.yml"
    action.parent.mkdir(parents=True, exist_ok=True)
    action.write_text("runs:\n  using: composite\n  steps:\n    - run: rustup default nightly\n")
    assert [error for error in nightly_pin_errors(root) if "install-rust/action.yml" in error]


@pytest.mark.parametrize(
    "line",
    [
        "      # Do not run rustup update nightly here.",
        "      - run: cargo test  # works on the pinned nightly",
    ],
)
def test_a_comment_that_mentions_nightly_passes(root, line):
    workflow = root / ".github/workflows/rust--tests.yml"
    workflow.write_text(workflow.read_text() + line + "\n")
    assert nightly_pin_errors(root) == []
