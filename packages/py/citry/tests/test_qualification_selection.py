import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts import select_citry_core_qualification as selection  # noqa: E402

COMMIT = "a" * 40
REPOSITORY = "citry-dev/citry"


def _run(*, event: str, run_id: int) -> dict[str, Any]:
    return {
        "id": run_id,
        "run_number": run_id,
        "run_attempt": 1,
        "html_url": f"https://github.example/runs/{run_id}",
        "event": event,
        "status": "completed",
        "conclusion": "success",
        "head_sha": COMMIT,
        "head_branch": "main",
        "head_repository": {"full_name": REPOSITORY},
    }


def test_select_run_can_require_a_push_gate() -> None:
    payload = {"workflow_runs": [_run(event="workflow_dispatch", run_id=1), _run(event="push", run_id=2)]}

    selected = selection.select_run(
        payload,
        repository=REPOSITORY,
        commit=COMMIT,
        event="push",
    )

    assert selected["id"] == 2


def test_select_workflow_run_without_an_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: list[str] = []

    def request(url: str, *, token: str) -> dict[str, Any]:
        assert token == ""
        requested.append(url)
        return {"workflow_runs": [_run(event="push", run_id=7)]}

    monkeypatch.setattr(selection, "_request_json", request)

    result = selection.select_qualification(
        repository=REPOSITORY,
        commit=COMMIT,
        workflow="repo--docs-check.yml",
        token="",
        artifact_name=None,
        event="push",
    )

    assert result == {
        "run_id": "7",
        "run_url": "https://github.example/runs/7",
        "head_sha": COMMIT,
    }
    assert len(requested) == 1
    assert "event=push" in requested[0]
