"""Contracts for pull-request cancellation and focused Python diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

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
    steps = {step.get("name", step.get("uses")): step for step in job["steps"]}
    assert steps["actions/checkout@v7"]["with"]["submodules"] == "recursive"
    assert steps["Set up Python"]["with"]["python-version"] == "${{ inputs.python_version }}"
    assert steps["Install the workspace"]["run"] == "uv sync --locked --all-packages"

    run_step = steps["Run selected pytest target serially"]
    assert run_step["shell"] == "bash"
    assert run_step["env"] == {"PYTEST_TARGET": "${{ inputs.pytest_target }}"}
    assert "inputs.pytest_target" not in run_step["run"]
    assert run_step["run"] == 'uv run --no-sync pytest --durations 30 -- "$PYTEST_TARGET"'
    assert "-n" not in run_step["run"].split()
