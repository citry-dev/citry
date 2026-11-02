from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
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


# Restart and retry. Every registry answer below is a synthetic payload; no
# test reaches PyPI, the Marketplace, Open VSX, or GitHub.

_COMMIT = "a" * 40
_WHEEL = "citry_core-1.7.0-cp311-abi3-manylinux_2_17_x86_64.whl"
_SDIST = "citry_core-1.7.0.tar.gz"
_VSIX = "citry-0.1.3.vsix"


def _qualification_archive(path: Path, files: dict[str, bytes], *, inventory: dict[str, str] | None = None) -> str:
    """Write a qualification zip like the workers retain, and return its artifact digest."""
    recorded = inventory or {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
    with zipfile.ZipFile(path, "w") as bundle:
        for name, body in files.items():
            bundle.writestr(name, body)
        bundle.writestr(
            "release-inventory.json",
            json.dumps({"artifacts": [{"name": name, "sha256": digest} for name, digest in recorded.items()]}),
        )
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _pypi_json(files: dict[str, bytes]) -> bytes:
    urls = [
        {"filename": name, "digests": {"sha256": hashlib.sha256(body).hexdigest()}} for name, body in files.items()
    ]
    return json.dumps({"urls": urls}).encode()


class _Registry:
    """Answer registry URLs from a fixed table; any other URL is a 404."""

    def __init__(self, answers: dict[str, bytes]) -> None:
        self.answers = answers
        self.requested: list[str] = []

    def get(self, url: str) -> tuple[int, bytes]:
        self.requested.append(url)
        return (200, self.answers[url]) if url in self.answers else (404, b"")


class _ReleaseGitHub:
    """Serve the GitHub calls `publish_candidate` makes, from fixed state."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        tags: dict[str, str],
        releases: set[str],
        archives: dict[int, bytes],
    ) -> None:
        self.repository = "citry-dev/citry"
        self.tmp_path = tmp_path
        self.tags = tags
        self.releases = releases
        self.archives = archives
        self.dispatched: list[str] = []

    def request(self, _method: str, path: str) -> dict[str, object]:
        if path.endswith("/jobs?per_page=100"):
            return {"jobs": []}
        return {**_producer_run(), "path": ".github/workflows/repo--release-candidate.yml"}

    def tag_commit(self, tag: str) -> str | None:
        return self.tags.get(tag)

    def release_exists(self, tag: str) -> bool:
        return tag in self.releases

    def download_artifact(self, artifact_id: int, destination: Path) -> None:
        destination.write_bytes(self.archives[artifact_id])

    def dispatch(self, *, workflow: str, ref: str, inputs: dict[str, str]) -> None:
        assert ref == "main"
        assert inputs["operation"] == "promote"
        self.dispatched.append(workflow)

    def workflow_runs(self, workflow: str) -> list[dict[str, object]]:
        # Each dispatched worker finishes at once, so the layer can advance.
        key = next(spec.key for spec in release.PACKAGE_SPECS if spec.workflow == workflow)
        return [
            {
                "id": 50,
                "display_title": f"Publish {key} for candidate 3",
                "created_at": "2999-01-01T00:00:00Z",
                "status": "completed",
                "conclusion": "success",
                "html_url": "https://example.test/runs/50",
            }
        ]


def _core_candidate(tmp_path: Path, core_files: dict[str, bytes]) -> tuple[dict[str, object], dict[int, bytes]]:
    """Build a two-layer candidate (citry-core, then citry) with a real core archive."""
    candidate = build_plan(
        _repo(tmp_path / "repo"),
        commit=_COMMIT,
        selected=("citry-core", "citry"),
        existing_tags=frozenset(),
    )
    archive = tmp_path / "core.zip"
    digest = _qualification_archive(archive, core_files)
    candidate["candidate_id"] = "1"
    candidate["qualifications"] = [
        {"package": "citry-core", "run_id": 10, "artifact_id": 11, "artifact_digest": digest},
        {"package": "citry", "run_id": 20, "artifact_id": 21, "artifact_digest": "sha256:" + "e" * 64},
    ]
    return candidate, {11: archive.read_bytes()}


_CORE_FILES = {_WHEEL: b"wheel bytes", _SDIST: b"sdist bytes"}
_CORE_PYPI = "https://pypi.org/pypi/citry-core/1.7.0/json"


def _publish(client: _ReleaseGitHub, registry: _Registry, candidate: dict[str, object]) -> None:
    publish_candidate(
        candidate,
        client=client,  # type: ignore[arg-type]
        ref="main",
        publication_id="3",
        candidate_run_id=1,
        registry=registry,  # type: ignore[arg-type]
    )


def test_restart_skips_a_package_already_published_from_the_same_bytes(tmp_path: Path) -> None:
    # The first run published citry-core and stopped later. A restart must not
    # send citry-core to its worker again, and must go on to the next layer.
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(
        tmp_path, tags={"citry-core@1.7.0": _COMMIT}, releases={"citry-core@1.7.0"}, archives=archives
    )
    registry = _Registry({_CORE_PYPI: _pypi_json(_CORE_FILES)})

    _publish(client, registry, candidate)

    assert client.dispatched == ["py--citry--publish.yml"]
    assert registry.requested == [_CORE_PYPI]


def test_restart_stops_when_the_registry_holds_different_bytes(tmp_path: Path) -> None:
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(
        tmp_path, tags={"citry-core@1.7.0": _COMMIT}, releases={"citry-core@1.7.0"}, archives=archives
    )
    registry = _Registry({_CORE_PYPI: _pypi_json({**_CORE_FILES, _WHEEL: b"other wheel bytes"})})

    with pytest.raises(ReleaseError, match=rf"citry-core 1\.7\.0 on PyPI: .*changed=\['{re.escape(_WHEEL)}'\]"):
        _publish(client, registry, candidate)
    # Nothing is dispatched once a public file is known to be wrong.
    assert client.dispatched == []


def test_restart_sends_a_partly_uploaded_package_back_to_its_worker(tmp_path: Path) -> None:
    # Only the sdist reached PyPI. The worker uploads the wheel with
    # skip-existing and then checks every file, so the controller must not
    # count the package as published.
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(
        tmp_path, tags={"citry-core@1.7.0": _COMMIT}, releases={"citry-core@1.7.0"}, archives=archives
    )
    registry = _Registry({_CORE_PYPI: _pypi_json({_SDIST: _CORE_FILES[_SDIST]})})

    _publish(client, registry, candidate)

    assert client.dispatched == ["py--citry-core--publish.yml", "py--citry--publish.yml"]


def test_restart_sends_a_package_without_its_tag_to_the_worker_that_creates_it(tmp_path: Path) -> None:
    # PyPI already serves the files, but the tag job failed. Only the worker
    # holds the release App's write access, so it must run again; it skips
    # the upload and creates the tag and GitHub Release. The controller does
    # not read the registry or the archive on this path.
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(tmp_path, tags={}, releases=set(), archives=archives)
    registry = _Registry({_CORE_PYPI: _pypi_json(_CORE_FILES)})

    _publish(client, registry, candidate)

    assert client.dispatched == ["py--citry-core--publish.yml", "py--citry--publish.yml"]
    assert registry.requested == []


def test_restart_sends_a_tag_without_its_github_release_back_to_the_worker(tmp_path: Path) -> None:
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(tmp_path, tags={"citry-core@1.7.0": _COMMIT}, releases=set(), archives=archives)

    _publish(client, _Registry({_CORE_PYPI: _pypi_json(_CORE_FILES)}), candidate)

    assert client.dispatched == ["py--citry-core--publish.yml", "py--citry--publish.yml"]


def test_restart_rejects_a_tag_on_another_commit(tmp_path: Path) -> None:
    candidate, archives = _core_candidate(tmp_path, _CORE_FILES)
    client = _ReleaseGitHub(
        tmp_path, tags={"citry-core@1.7.0": "b" * 40}, releases={"citry-core@1.7.0"}, archives=archives
    )

    with pytest.raises(ReleaseError, match=r"citry-core@1\.7\.0 names commit b+, not the candidate commit"):
        _publish(client, _Registry({}), candidate)


def test_qualified_files_rejects_an_archive_with_another_digest(tmp_path: Path) -> None:
    archive = tmp_path / "core.zip"
    _qualification_archive(archive, _CORE_FILES)

    with pytest.raises(ReleaseError, match="does not match digest"):
        release.qualified_files(archive, "sha256:" + "0" * 64)


def test_qualified_files_rejects_an_inventory_that_does_not_match_its_files(tmp_path: Path) -> None:
    # The inventory claims a hash the archived wheel does not have, so it
    # cannot be used to vouch for the registry's copy.
    archive = tmp_path / "core.zip"
    digest = _qualification_archive(
        archive, _CORE_FILES, inventory={_WHEEL: "f" * 64, _SDIST: hashlib.sha256(b"sdist bytes").hexdigest()}
    )

    with pytest.raises(ReleaseError, match=rf"qualified file {re.escape(_WHEEL)} does not match"):
        release.qualified_files(archive, digest)


_MARKETPLACE = (
    "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/citry-dev/vsextensions/citry/0.1.3/vspackage"
)
_OPEN_VSX = "https://open-vsx.org/api/citry-dev/citry/0.1.3"
_OPEN_VSX_FILE = "https://open-vsx.org/api/citry-dev/citry/0.1.3/file/citry-dev.citry-0.1.3.vsix"


def _vscode_answers(*, marketplace: bytes | None, open_vsx: bytes | None) -> dict[str, bytes]:
    answers: dict[str, bytes] = {}
    if marketplace is not None:
        answers[_MARKETPLACE] = marketplace
    if open_vsx is not None:
        answers[_OPEN_VSX] = json.dumps({"files": {"download": _OPEN_VSX_FILE}}).encode()
        answers[_OPEN_VSX_FILE] = open_vsx
    return answers


@pytest.mark.parametrize(
    ("marketplace", "open_vsx", "state"),
    [
        (b"vsix", b"vsix", "complete"),
        # Open VSX answers 404 while it reviews a new version.
        (b"vsix", None, "partial"),
        (None, None, "absent"),
    ],
)
def test_extension_state_needs_both_registries_to_serve_the_qualified_vsix(
    marketplace: bytes | None, open_vsx: bytes | None, state: str
) -> None:
    registry = _Registry(_vscode_answers(marketplace=marketplace, open_vsx=open_vsx))
    expected = {_VSIX: hashlib.sha256(b"vsix").hexdigest()}

    assert release.registry_state("vscode-citry", "0.1.3", expected, registry) == state  # type: ignore[arg-type]


def test_extension_state_names_the_registry_that_serves_other_bytes() -> None:
    registry = _Registry(_vscode_answers(marketplace=b"vsix", open_vsx=b"other"))
    expected = {_VSIX: hashlib.sha256(b"vsix").hexdigest()}

    with pytest.raises(ReleaseError, match=rf"vscode-citry 0\.1\.3 on Open VSX: .*changed=\['{re.escape(_VSIX)}'\]"):
        release.registry_state("vscode-citry", "0.1.3", expected, registry)  # type: ignore[arg-type]


def _job(conclusion: str, *failed_steps: str) -> dict[str, object]:
    return {
        "name": "Promote qualified bytes and release",
        "conclusion": conclusion,
        "steps": [{"name": "Download the immutable qualification archive", "conclusion": "success"}]
        + [{"name": step, "conclusion": "failure"} for step in failed_steps],
    }


@pytest.mark.parametrize(
    ("jobs", "retries_used", "retry"),
    [
        # The 0.7.0 failure: sigstore answered 502 inside the publish action.
        ([_job("failure", "Publish to PyPI")], 0, True),
        ([_job("failure", "Attest the promotion of the qualified bytes")], 1, True),
        ([_job("failure", "Publish the same VSIX to Open VSX")], 0, True),
        # Every retry is spent.
        ([_job("failure", "Publish to PyPI")], 2, False),
        # A hash check gives the same answer every time.
        ([_job("failure", "Accept only absent, partly uploaded, or byte-identical public state")], 0, False),
        ([_job("failure", "Publish to PyPI"), _job("failure", "Create or verify the final annotated tag")], 0, False),
        # Someone cancelled the run, or a job ran out of time.
        ([_job("cancelled")], 0, False),
        ([_job("timed_out", "Publish to PyPI")], 0, False),
        # A failed job without step details is not understood well enough.
        ([{"name": "release", "conclusion": "failure"}], 0, False),
        ([], 0, False),
    ],
)
def test_retry_decision(jobs: list[dict[str, object]], retries_used: int, retry: bool) -> None:
    assert release.should_retry(jobs, retries_used=retries_used, max_retries=2) is retry


def test_every_retryable_step_is_a_step_of_a_publish_workflow() -> None:
    # A renamed step would silently turn its retry off, so tie the names to
    # the workflows.
    workflows = Path(release.__file__).resolve().parents[1] / ".github/workflows"
    steps: set[str] = set()
    for spec in release.PACKAGE_SPECS:
        for job in yaml.safe_load((workflows / spec.workflow).read_text(encoding="utf-8"))["jobs"].values():
            steps.update(str(step.get("name")) for step in job.get("steps", []))
    assert steps >= release.RETRYABLE_STEPS


class _RetriedRun:
    """Serve one publish run that fails in a retryable step, then succeeds on its second attempt."""

    def __init__(self) -> None:
        # Attempt 1 fails. Right after the rerun request GitHub still shows
        # attempt 1, then attempt 2 runs and succeeds.
        self.states: list[tuple[int, str, str | None]] = [
            (1, "completed", "failure"),
            (1, "completed", "failure"),
            (2, "in_progress", None),
            (2, "completed", "success"),
        ]
        self.reruns: list[int] = []

    def workflow_runs(self, _workflow: str) -> list[dict[str, object]]:
        attempt, status, conclusion = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return [
            {
                "id": 7,
                "run_attempt": attempt,
                "display_title": "Publish citry-lsp for candidate 3",
                "created_at": "2026-01-01T00:00:00Z",
                "status": status,
                "conclusion": conclusion,
                "html_url": "https://example.test/runs/7",
            }
        ]

    def request(self, _method: str, _path: str) -> dict[str, object]:
        return {"jobs": [_job("failure", "Publish to PyPI")]}

    def rerun_failed_jobs(self, run_id: int) -> None:
        self.reruns.append(run_id)


def test_a_failed_publish_step_is_retried_and_the_old_attempt_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release, "POLL_SECONDS", 0)
    monkeypatch.setattr(release, "RETRY_DELAY_SECONDS", 0)
    client = _RetriedRun()

    runs = release._wait_for_runs(
        client,  # type: ignore[arg-type]
        {"citry-lsp": ("py--citry-lsp--publish.yml", "Publish citry-lsp for candidate 3")},
        started_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        timeout_seconds=60,
        max_retries=2,
    )

    assert client.reruns == [7]
    assert runs["citry-lsp"]["run_attempt"] == 2


def test_qualification_waits_do_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    # Only publication passes `max_retries`; a failed qualification is a
    # result to read, not an outage to wait out.
    monkeypatch.setattr(release, "POLL_SECONDS", 0)
    client = _RetriedRun()

    with pytest.raises(ReleaseError, match="failed in jobs Promote qualified bytes and release"):
        release._wait_for_runs(
            client,  # type: ignore[arg-type]
            {"citry-lsp": ("py--citry-lsp--publish.yml", "Publish citry-lsp for candidate 3")},
            started_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            timeout_seconds=60,
        )
    assert client.reruns == []
