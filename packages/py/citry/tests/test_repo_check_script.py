"""Contracts for the repository check runner's profiles and progress output."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_RELOAD_TEST_PATH = "packages/py/citry/tests/test_server_reload.py"
_CHECK_SPEC = importlib.util.spec_from_file_location("_citry_repo_check", _REPO_ROOT / "scripts" / "check.py")
assert _CHECK_SPEC is not None
assert _CHECK_SPEC.loader is not None
check_script = importlib.util.module_from_spec(_CHECK_SPEC)
_CHECK_SPEC.loader.exec_module(check_script)


def test_fast_and_full_profiles_keep_browser_tests_outside_the_gate() -> None:
    fast_phases = dict(check_script._phases("fast"))
    full_phases = dict(check_script._phases("full"))
    default_phases = dict(check_script._phases())
    fast = fast_phases["pytest"]
    full = full_phases["pytest"]

    assert fast[fast.index("-m") + 1] == "not e2e and not qualification"
    assert full[full.index("-m") + 1] == "not e2e and not qualification"
    for command in (fast, full):
        assert command[command.index("--ignore") + 1] == _RELOAD_TEST_PATH
        assert command[command.index("-n") + 1] == "4"
        assert command[command.index("--dist") + 1] == "loadfile"
    reload_servers = fast_phases["pytest reload servers"]
    assert reload_servers[-3:] == [_RELOAD_TEST_PATH, "--durations", "10"]
    assert "-n" not in reload_servers
    assert full_phases["pytest reload servers"] == reload_servers
    assert "--cov" not in fast
    assert "--cov" in full
    assert "pytest qualification" not in fast_phases
    qualification = full_phases["pytest qualification"]
    assert qualification[qualification.index("-m") + 1] == "qualification and not e2e"
    assert qualification[qualification.index("-n") + 1] == "2"
    assert "--cov" not in qualification
    assert default_phases["pytest"] == full
    assert default_phases["pytest qualification"] == qualification


def test_python_test_workflow_runs_reload_once_outside_the_platform_matrix() -> None:
    workflow_path = _REPO_ROOT / ".github" / "workflows" / "py--tests.yml"
    jobs = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))["jobs"]

    reload_job = jobs["reload-servers"]
    assert reload_job["runs-on"] == "ubuntu-latest"
    reload_steps = {step.get("name"): step for step in reload_job["steps"]}
    assert reload_steps["Set up Python"]["with"]["python-version"] == "3.14"
    reload_command = reload_steps["Run real-server reload tests serially"]["run"]
    assert reload_command == f"uv run --no-sync pytest {_RELOAD_TEST_PATH} --durations 10"
    assert "-n" not in reload_command.split()

    matrix_steps = {step.get("name"): step for step in jobs["test"]["steps"]}
    matrix_command = matrix_steps["Run Python tests"]["run"]
    assert f"--ignore {_RELOAD_TEST_PATH}" in matrix_command
    assert "Run real-server reload tests serially" not in matrix_steps

    reload_invocations = [
        step["run"]
        for job in jobs.values()
        for step in job.get("steps", ())
        if f"pytest {_RELOAD_TEST_PATH}" in step.get("run", "")
    ]
    assert reload_invocations == [reload_command]


def test_agent_capture_emits_heartbeats_without_losing_child_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(check_script, "_HEARTBEAT_SECONDS", 0.01)

    code, output = check_script._run(
        [
            sys.executable,
            "-c",
            "import time; print('started', flush=True); time.sleep(0.05); print('finished')",
        ],
        capture=True,
        phase_name="slow example",
    )

    assert code == 0
    assert output.splitlines() == ["started", "finished"]
    assert "[check] slow example still running" in capsys.readouterr().err


def test_agent_report_keeps_progress_on_stderr_and_json_on_stdout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(check_script, "_phases", lambda profile: [(f"{profile} example", ["unused"])])

    def run_phase(command: list[str], *, capture: bool, phase_name: str) -> tuple[int, str]:
        assert command == ["unused"]
        assert capture is True
        assert phase_name == "fast example"
        return 0, ""

    monkeypatch.setattr(check_script, "_run", run_phase)

    assert check_script.main(["--profile", "fast", "--reporter", "agent"]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "PASSED"
    assert report["profile"] == "fast"
    assert isinstance(report["durationSeconds"], float)
    assert isinstance(report["phases"][0]["durationSeconds"], float)
    assert "[check] starting fast example" in captured.err
    assert "[check] PASS fast example" in captured.err
