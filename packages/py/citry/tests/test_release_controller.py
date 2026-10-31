from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from scripts import release
from scripts.release import (
    GitHubClient,
    ReleaseError,
    _plan_layers,
    build_plan,
    publish_candidate,
    verify_producer_run,
    verify_qualification,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_python_manifest(path: Path, *, name: str, version: str, dependencies: tuple[str, ...] = ()) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dependency_lines = ", ".join(json.dumps(item) for item in dependencies)
    path.write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\ndependencies = [{dependency_lines}]\n',
        encoding="utf-8",
    )


def _repo(tmp_path: Path, *, lsp_floor: str = "0.4.5", extension_lsp: str = "0.1.4") -> Path:
    _write_python_manifest(tmp_path / "packages/py/citry_core/pyproject.toml", name="citry-core", version="1.7.0")
    _write_python_manifest(
        tmp_path / "packages/py/citry/pyproject.toml",
        name="citry",
        version="0.4.7",
        dependencies=("citry-core==1.7.0",),
    )
    _write_python_manifest(
        tmp_path / "packages/py/citry_lsp/pyproject.toml",
        name="citry-lsp",
        version="0.1.4",
        dependencies=(f"citry>={lsp_floor},<0.5",),
    )
    _write_python_manifest(
        tmp_path / "packages/py/citry_ui/pyproject.toml",
        name="citry-ui",
        version="0.2.1",
        dependencies=("citry>=0.4.2,<0.5",),
    )
    _write_python_manifest(
        tmp_path / "packages/py/pygments_citry/pyproject.toml",
        name="pygments-citry",
        version="0.2.1",
    )
    extension = tmp_path / "packages/editors/vscode/package.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps({"name": "citry", "version": "0.1.3", "citry": {"lspVersion": extension_lsp}}),
        encoding="utf-8",
    )
    return tmp_path


def test_plan_builds_only_real_dependency_layers(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    plan = build_plan(
        root,
        commit="a" * 40,
        selected=("citry-core", "citry", "citry-lsp", "vscode-citry"),
        existing_tags=frozenset(),
    )

    assert plan["layers"] == [["citry-core", "citry-lsp"], ["citry", "vscode-citry"]]
    packages = {item["key"]: item for item in plan["packages"]}
    assert packages["citry"]["dependencies"] == ["citry-core"]
    assert packages["citry"]["qualification_dependencies"] == ["citry-core"]
    assert packages["citry-lsp"]["dependencies"] == []
    assert packages["vscode-citry"]["dependencies"] == ["citry-lsp"]
    assert packages["vscode-citry"]["qualification_dependencies"] == ["citry-lsp"]


def test_raised_lsp_floor_waits_for_selected_citry(tmp_path: Path) -> None:
    root = _repo(tmp_path, lsp_floor="0.4.7")

    plan = build_plan(
        root,
        commit="a" * 40,
        selected=("citry", "citry-lsp"),
        existing_tags=frozenset(),
    )

    assert plan["layers"] == [["citry"], ["citry-lsp"]]
    packages = {item["key"]: item for item in plan["packages"]}
    assert packages["citry-lsp"]["qualification_dependencies"] == ["citry"]


def test_qualification_dependency_closure_includes_selected_core(tmp_path: Path) -> None:
    root = _repo(tmp_path, lsp_floor="0.4.7")

    plan = build_plan(
        root,
        commit="a" * 40,
        selected=("citry-core", "citry", "citry-lsp"),
        existing_tags=frozenset(),
    )

    packages = {item["key"]: item for item in plan["packages"]}
    assert packages["citry-lsp"]["qualification_dependencies"] == ["citry-core", "citry"]


def test_auto_plan_selects_only_versions_without_tags(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    plan = build_plan(
        root,
        commit="a" * 40,
        selected=None,
        existing_tags=frozenset(
            {
                "citry-core@1.7.0",
                "citry-lsp@0.1.4",
                "citry-ui@0.2.1",
                "pygments-citry@0.2.1",
                "vscode-citry@0.1.3",
            }
        ),
    )

    assert [item["key"] for item in plan["packages"]] == ["citry"]
    assert plan["layers"] == [["citry"]]


def test_plan_rejects_a_mismatched_selected_lsp_pin(tmp_path: Path) -> None:
    root = _repo(tmp_path, extension_lsp="0.1.3")

    with pytest.raises(ReleaseError, match="does not pin the selected citry-lsp"):
        build_plan(
            root,
            commit="a" * 40,
            selected=("citry-lsp", "vscode-citry"),
            existing_tags=frozenset(),
        )


def test_explicit_plan_rejects_an_existing_release_tag(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    with pytest.raises(ReleaseError, match=r"citry@0\.4\.7 already exists"):
        build_plan(
            root,
            commit="a" * 40,
            selected=("citry",),
            existing_tags=frozenset({"citry@0.4.7"}),
        )


def test_publication_layers_cannot_start_a_dependent_first(tmp_path: Path) -> None:
    plan = build_plan(
        _repo(tmp_path),
        commit="a" * 40,
        selected=("citry-core", "citry"),
        existing_tags=frozenset(),
    )
    plan["layers"] = [["citry"], ["citry-core"]]
    packages = {package["key"]: package for package in plan["packages"]}

    with pytest.raises(ReleaseError, match="before its dependencies"):
        _plan_layers(plan, packages)


def _producer_run() -> dict[str, object]:
    return {
        "path": ".github/workflows/py--citry--publish.yml",
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "head_repository": {"full_name": "citry-dev/citry"},
    }


def test_producer_run_accepts_the_exact_trusted_source() -> None:
    verify_producer_run(
        _producer_run(),
        repository="citry-dev/citry",
        workflow="py--citry--publish.yml",
        commit="a" * 40,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", ".github/workflows/untrusted.yml"),
        ("event", "pull_request"),
        ("head_branch", "review"),
        ("head_sha", "b" * 40),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("head_repository", {"full_name": "fork/citry"}),
        ("head_repository", None),
    ],
)
def test_producer_run_rejects_untrusted_or_unqualified_evidence(field: str, value: object) -> None:
    run = {**_producer_run(), field: value}

    with pytest.raises(ReleaseError, match="not a successful"):
        verify_producer_run(
            run,
            repository="citry-dev/citry",
            workflow="py--citry--publish.yml",
            commit="a" * 40,
        )


@pytest.mark.parametrize("wrong_identity", [None, "run", "commit", "digest", "name", "expired"])
def test_retained_qualification_requires_the_exact_producer_and_artifact(
    monkeypatch: pytest.MonkeyPatch,
    wrong_identity: str | None,
) -> None:
    client = GitHubClient(repository="citry-dev/citry", token="test-token")  # noqa: S106 - synthetic credential
    artifact: dict[str, object] = {
        "id": 2,
        "name": "verified-citry-distributions",
        "expired": False,
        "digest": "sha256:" + "c" * 64,
        "workflow_run": {"id": 1, "head_sha": "a" * 40},
    }
    if wrong_identity == "run":
        artifact["workflow_run"] = {"id": 3, "head_sha": "a" * 40}
    elif wrong_identity == "commit":
        artifact["workflow_run"] = {"id": 1, "head_sha": "b" * 40}
    elif wrong_identity == "digest":
        artifact["digest"] = "sha256:" + "d" * 64
    elif wrong_identity == "name":
        artifact["name"] = "raw-citry-distributions"
    elif wrong_identity == "expired":
        artifact["expired"] = True
    monkeypatch.setattr(client, "request", lambda *_args: _producer_run())
    monkeypatch.setattr(client, "artifacts", lambda _run_id: [artifact])

    def verify() -> None:
        verify_qualification(
            client,
            package="citry",
            commit="a" * 40,
            run_id=1,
            artifact_id=2,
            artifact_digest="sha256:" + "c" * 64,
        )

    if wrong_identity is None:
        verify()
    else:
        with pytest.raises(ReleaseError, match="different source or identity"):
            verify()


def test_publication_rejects_a_bundle_from_another_workflow_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client = GitHubClient(repository="citry-dev/citry", token="test-token")  # noqa: S106 - synthetic credential
    monkeypatch.setattr(client, "request", lambda *_args: _producer_run())
    candidate = build_plan(_repo(tmp_path), commit="a" * 40, selected=("citry",), existing_tags=frozenset())

    # Even a valid package graph cannot authorize publication from another producer.
    with pytest.raises(ReleaseError, match=r"repo--release-candidate\.yml"):
        publish_candidate(candidate, client=client, ref="main", publication_id="3", candidate_run_id=1)


@pytest.mark.parametrize("event", ["push", "workflow_dispatch"])
def test_candidate_accepts_both_supported_preparation_events(event: str) -> None:
    run = {**_producer_run(), "path": ".github/workflows/repo--release-candidate.yml", "event": event}
    verify_producer_run(
        run,
        repository="citry-dev/citry",
        workflow="repo--release-candidate.yml",
        commit="a" * 40,
        events=("push", "workflow_dispatch"),
    )


class _ScriptedRuns:
    """Serve one workflow run whose state advances on each poll."""

    def __init__(
        self,
        states: list[tuple[str, str | None]],
        jobs: list[dict[str, object]] | None = None,
        *,
        jobs_error: Exception | None = None,
    ) -> None:
        self.states = states
        self.jobs = jobs or []
        self.jobs_error = jobs_error
        self.requested: list[str] = []

    def workflow_runs(self, _workflow: str) -> list[dict[str, object]]:
        status, conclusion = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return [
            {
                "id": 7,
                "display_title": "Qualify citry for candidate 1",
                "created_at": "2026-01-01T00:00:00Z",
                "status": status,
                "conclusion": conclusion,
                "html_url": "https://example.test/runs/7",
            }
        ]

    def request(self, _method: str, path: str) -> dict[str, object]:
        self.requested.append(path)
        if self.jobs_error is not None:
            raise self.jobs_error
        return {"jobs": self.jobs}


def _wait(monkeypatch: pytest.MonkeyPatch, client: _ScriptedRuns) -> dict[str, dict[str, object]]:
    monkeypatch.setattr(release, "POLL_SECONDS", 0)
    return release._wait_for_runs(
        client,  # type: ignore[arg-type]
        {"citry": ("py--citry--publish.yml", "Qualify citry for candidate 1")},
        started_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        timeout_seconds=60,
    )


def test_waiting_logs_each_state_change_once_with_the_run_link(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Repeated polls of an unchanged run must not flood the log, and the first
    # line must carry the URL so a reader can open the run being waited on.
    client = _ScriptedRuns([("queued", None), ("queued", None), ("in_progress", None), ("completed", "success")])

    assert _wait(monkeypatch, client)["citry"]["id"] == 7
    assert capsys.readouterr().err.splitlines() == [
        "Qualify citry for candidate 1: queued: https://example.test/runs/7",
        "Qualify citry for candidate 1: in_progress",
        "Qualify citry for candidate 1: completed/success",
    ]


def test_waiting_repeats_unfinished_states_on_the_progress_interval(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A zero interval makes the still-waiting line due on the first unfinished
    # poll, without the test waiting five minutes.
    monkeypatch.setattr(release, "PROGRESS_SECONDS", 0)
    client = _ScriptedRuns([("in_progress", None), ("completed", "success")])

    _wait(monkeypatch, client)
    assert "Still waiting after 0 min on: citry (in_progress)" in capsys.readouterr().err


def test_a_failed_run_names_its_failed_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _ScriptedRuns(
        [("completed", "failure")],
        jobs=[
            {"name": "build", "conclusion": "success"},
            {"name": "smoke-python (3.14)", "conclusion": "failure"},
        ],
    )

    with pytest.raises(ReleaseError, match=r"failed in jobs smoke-python \(3\.14\): https://example"):
        _wait(monkeypatch, client)
    assert client.requested == ["/actions/runs/7/jobs?per_page=100"]


def test_a_failed_job_stops_the_wait_before_the_run_finishes(monkeypatch: pytest.MonkeyPatch) -> None:
    # The run would finish only after its slowest job, so the wait must stop
    # as soon as one job has failed. A zero interval reads jobs on every poll.
    monkeypatch.setattr(release, "JOB_CHECK_SECONDS", 0)
    client = _ScriptedRuns(
        [("in_progress", None)],
        jobs=[
            {"name": "sdist", "conclusion": "failure"},
            {"name": "linux (x86)", "conclusion": None},
        ],
    )

    with pytest.raises(ReleaseError, match=r"failed in jobs sdist while its other jobs were still running"):
        _wait(monkeypatch, client)


def test_running_jobs_without_a_failure_keep_the_wait_going(monkeypatch: pytest.MonkeyPatch) -> None:
    # A job that is still running has no conclusion, so the wait goes on. With
    # a zero interval it reads jobs once for each poll of the unfinished run.
    monkeypatch.setattr(release, "JOB_CHECK_SECONDS", 0)
    client = _ScriptedRuns(
        [("in_progress", None), ("in_progress", None), ("completed", "success")],
        jobs=[{"name": "linux (x86)", "conclusion": None}],
    )

    assert _wait(monkeypatch, client)["citry"]["id"] == 7
    assert client.requested == ["/actions/runs/7/jobs?per_page=100"] * 2


def test_jobs_of_a_running_run_wait_for_the_check_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    # Polls come every 10 seconds, so reading jobs on each one would spend the
    # API budget; the first read waits for the full interval.
    client = _ScriptedRuns([("queued", None), ("in_progress", None), ("completed", "success")])

    _wait(monkeypatch, client)
    assert client.requested == []


def test_a_failed_job_lookup_still_reports_the_run_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # The job names are extra detail, so a lookup error of any kind must leave
    # the original failure message in place.
    client = _ScriptedRuns([("completed", "failure")], jobs_error=ConnectionResetError("reset"))

    with pytest.raises(ReleaseError) as raised:
        _wait(monkeypatch, client)
    assert str(raised.value) == "Qualify citry for candidate 1 failed: https://example.test/runs/7"
