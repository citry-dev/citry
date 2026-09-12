"""Contracts for pull-request cancellation and focused Python diagnostics."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"


def _load_workflow(name: str) -> dict[str, Any]:
    content = yaml.safe_load((_WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(content, dict)
    # PyYAML applies YAML 1.1 booleans, where the Actions key `on` becomes True.
    if True in content:
        content["on"] = content.pop(True)
    return content


def test_pull_request_workflows_cancel_only_stale_pull_request_runs() -> None:
    checked: set[str] = set()
    workflow_paths = [*_WORKFLOWS.glob("*.yml"), *_WORKFLOWS.glob("*.yaml")]
    for path in workflow_paths:
        workflow = _load_workflow(path.name)
        events = workflow.get("on", {})
        if not isinstance(events, dict) or not {"pull_request", "pull_request_target"}.intersection(events):
            continue

        assert workflow.get("concurrency") == {
            "group": "${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}",
            "cancel-in-progress": (
                "${{ github.event_name == 'pull_request' || github.event_name == 'pull_request_target' }}"
            ),
        }, path.name
        checked.add(path.name)

    assert checked == {
        "py--examples--tests.yml",
        "py--tests.yml",
        "repo--check.yml",
        "repo--dependabot-relock.yml",
        "repo--discord-pr.yml",
        "repo--docs-check.yml",
        "repo--docs-lighthouse.yml",
        "rust--tests.yml",
    }


def test_python_diagnostic_constrains_setup_and_passes_one_literal_target() -> None:
    workflow = _load_workflow("py--diagnostic.yml")
    dispatch = workflow["on"]["workflow_dispatch"]
    inputs = dispatch["inputs"]

    runner = inputs["runner_os"]
    assert runner["type"] == "choice"
    assert runner["required"] is True
    assert runner["default"] == "ubuntu-latest"
    assert runner["options"] == ["ubuntu-latest", "macos-latest", "windows-latest"]

    python = inputs["python_version"]
    assert python["type"] == "choice"
    assert python["required"] is True
    assert python["default"] == "3.14"
    assert python["options"] == ["3.10", "3.11", "3.12", "3.13", "3.14"]

    profile = inputs["install_profile"]
    assert profile["type"] == "choice"
    assert profile["required"] is True
    assert profile["default"] == "citry"
    assert profile["options"] == [
        "citry",
        "citry-core",
        "citry-lsp",
        "citry-ui",
        "pygments-citry",
        "full-workspace",
    ]

    wheel_mode = inputs["core_wheel_mode"]
    assert wheel_mode["type"] == "choice"
    assert wheel_mode["required"] is True
    assert wheel_mode["default"] == "reuse"
    assert wheel_mode["options"] == ["reuse", "rebuild"]

    target = inputs["pytest_target"]
    assert target == {
        "description": "One ordinary non-browser Python test file or node ID",
        "required": True,
        "default": "packages/py/citry/tests/test_server_reload.py",
        "type": "string",
    }

    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {"test"}
    job = workflow["jobs"]["test"]
    assert job["runs-on"] == "${{ inputs.runner_os }}"
    assert job["timeout-minutes"] == 45
    steps = {step.get("name", step.get("uses")): step for step in job["steps"]}
    assert "with" not in steps["actions/checkout@v7"]
    assert steps["Set up Python"]["with"]["python-version"] == "${{ inputs.python_version }}"

    validate_step = steps["Validate the selected pytest target"]
    assert validate_step["shell"] == "bash"
    assert validate_step["env"] == {
        "INSTALL_PROFILE": "${{ inputs.install_profile }}",
        "PYTEST_TARGET": "${{ inputs.pytest_target }}",
    }
    assert "inputs.pytest_target" not in validate_step["run"]
    assert 'validate-target --profile "$INSTALL_PROFILE" --target "$PYTEST_TARGET"' in validate_step["run"]

    restore = steps["Restore exact Citry Core wheel"]
    assert restore["uses"] == "actions/cache/restore@v6"
    assert restore["with"] == {
        "path": ".diagnostic-cache/citry-core",
        "key": "${{ steps.core-identity.outputs.cache_key }}",
    }
    assert "restore-keys" not in restore["with"]
    identity = steps["Resolve Citry Core wheel identity"]
    runner_image_argument = (
        'runner-image "${ImageOS:?missing hosted image OS}/${ImageVersion:?missing hosted image version}"'
    )
    assert runner_image_argument in identity["run"]

    build = steps["Build Citry Core wheel"]
    assert build["env"] == {
        "CARGO_INCREMENTAL": "0",
        "RUSTC_WRAPPER": "sccache",
        "SCCACHE_GHA_ENABLED": "true",
    }
    assert build["run"].splitlines() == [
        "uv lock --check",
        "uv build --package citry-core --wheel \\",
        "  --out-dir .diagnostic-cache/citry-core",
    ]
    assert steps["Set up sccache for a Core wheel cache miss"]["uses"] == (
        "mozilla-actions/sccache-action@fc920bf0ec8de6ee65d409111f7ec508035751ba"
    )
    assert steps["Enable GitHub Actions-backed sccache"]["run"].splitlines() == [
        'echo "RUSTC_WRAPPER=sccache" >> "$GITHUB_ENV"',
        'echo "SCCACHE_GHA_ENABLED=true" >> "$GITHUB_ENV"',
    ]
    assert steps["Initialize native submodules"]["run"] == "git submodule update --init --recursive"

    uv = shutil.which("uv")
    assert uv is not None
    uv_build_help = subprocess.run([uv, "build", "--help"], check=True, capture_output=True, text=True).stdout
    supported_build_options = set(
        re.findall(r"(?m)^\s+(?:-[A-Za-z],\s+)?(--[a-z][a-z-]*)\b", uv_build_help)
    )
    build_command = " ".join(build["run"].splitlines()[1:]).replace("\\", "")
    requested_build_options = {token for token in shlex.split(build_command) if token.startswith("--")}
    assert requested_build_options <= supported_build_options

    core_pyproject = tomllib.loads(
        (_REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert core_pyproject["tool"]["maturin"]["locked"] is True

    save = steps["Save exact Citry Core wheel"]
    assert save["uses"] == "actions/cache/save@v6"
    assert save["with"] == restore["with"]
    assert "core_wheel_mode == 'reuse'" in save["if"]
    assert "cache-hit != 'true'" in save["if"]
    step_names = [step.get("name", step.get("uses")) for step in job["steps"]]
    assert step_names.index("Install selected diagnostic profile") < step_names.index("Save exact Citry Core wheel")
    assert step_names.index("Save exact Citry Core wheel") < step_names.index("Run selected pytest target serially")

    install = steps["Install selected diagnostic profile"]
    assert install["env"] == {
        "CORE_WHEEL_CACHE_KEY": "${{ steps.core-identity.outputs.cache_key }}",
        "INSTALL_PROFILE": "${{ inputs.install_profile }}",
    }
    assert "inputs.install_profile" not in install["run"]
    assert 'install-profile --profile "$INSTALL_PROFILE"' in install["run"]

    run_step = steps["Run selected pytest target serially"]
    assert run_step["shell"] == "bash"
    assert run_step["env"] == {"PYTEST_TARGET": "${{ inputs.pytest_target }}"}
    assert "inputs.pytest_target" not in run_step["run"]
    assert run_step["run"] == 'uv run --no-sync python -m pytest -m "not e2e" --durations 30 -- "$PYTEST_TARGET"'
    assert "-n" not in run_step["run"].split()
