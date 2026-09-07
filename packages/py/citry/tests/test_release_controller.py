from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
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
