"""Plan, qualify, and publish a Citry monorepo release as one operation."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 is part of the package test matrix.
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

SCHEMA_VERSION: Final = 1
API_VERSION: Final = "2022-11-28"
POLL_SECONDS: Final = 10
QUALIFICATION_TIMEOUT_SECONDS: Final = 60 * 60
PUBLICATION_TIMEOUT_SECONDS: Final = 20 * 60
FULL_SHA: Final = re.compile(r"[0-9a-f]{40}")


class ReleaseError(RuntimeError):
    """The requested release cannot continue safely."""


@dataclass(frozen=True, slots=True)
class PackageSpec:
    """Describe one independently published package and its retained artifact."""

    key: str
    manifest: str
    workflow: str
    artifact: str
    tag_prefix: str
    manifest_kind: str = "python"


PACKAGE_SPECS: Final = (
    PackageSpec(
        "citry-core",
        "packages/py/citry_core/pyproject.toml",
        "py--citry-core--publish.yml",
        "verified-citry-core-distributions",
        "citry-core@",
    ),
    PackageSpec(
        "citry",
        "packages/py/citry/pyproject.toml",
        "py--citry--publish.yml",
        "verified-citry-distributions",
        "citry@",
    ),
    PackageSpec(
        "citry-lsp",
        "packages/py/citry_lsp/pyproject.toml",
        "py--citry-lsp--publish.yml",
        "verified-citry-lsp-distributions",
        "citry-lsp@",
    ),
    PackageSpec(
        "citry-ui",
        "packages/py/citry_ui/pyproject.toml",
        "py--citry-ui--publish.yml",
        "verified-citry-ui-distributions",
        "citry-ui@",
    ),
    PackageSpec(
        "pygments-citry",
        "packages/py/pygments_citry/pyproject.toml",
        "py--pygments-citry--publish.yml",
        "verified-pygments-citry-distributions",
        "pygments-citry@",
    ),
    PackageSpec(
        "vscode-citry",
        "packages/editors/vscode/package.json",
        "vscode--citry--publish.yml",
        "verified-vscode-citry-extension",
        "vscode-citry@",
        "json",
    ),
)
PACKAGE_BY_KEY: Final = {package.key: package for package in PACKAGE_SPECS}


def _manifest(spec: PackageSpec, repo_root: Path) -> dict[str, Any]:
    path = repo_root / spec.manifest
    try:
        if spec.manifest_kind == "json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReleaseError(f"could not read {spec.key} manifest: {error}") from error
    if not isinstance(payload, dict):
        raise ReleaseError(f"{spec.key} manifest must contain an object")
    return payload


def _version(spec: PackageSpec, manifest: Mapping[str, Any]) -> str:
    project = manifest.get("project")
    value = (
        manifest.get("version")
        if spec.manifest_kind == "json"
        else project.get("version")
        if isinstance(project, dict)
        else None
    )
    if not isinstance(value, str) or re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", value) is None:
        raise ReleaseError(f"{spec.key} manifest has no full package version")
    return value


def _python_dependencies(manifest: Mapping[str, Any]) -> tuple[str, ...]:
    project = manifest.get("project")
    dependencies = project.get("dependencies") if isinstance(project, dict) else None
    if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
        return ()
    return tuple(dependencies)


def _dependency(dependencies: Iterable[str], package: str) -> str | None:
    normalized = package.lower().replace("_", "-")
    matches = []
    for dependency in dependencies:
        name = re.split(r"[<>=!~;[ ]", dependency, maxsplit=1)[0].lower().replace("_", "-")
        if name == normalized:
            matches.append(dependency)
    if len(matches) > 1:
        raise ReleaseError(f"manifest declares {package} more than once")
    return matches[0] if matches else None


def _numeric_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    if match is None:
        raise ReleaseError(f"release dependency versions must use major.minor.patch, found {value!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def _minimum_version(requirement: str) -> str | None:
    match = re.search(r">=\s*(\d+\.\d+\.\d+)", requirement)
    return match.group(1) if match else None


def _exact_version(requirement: str) -> str | None:
    match = re.search(r"==\s*(\d+\.\d+\.\d+)(?:\s*(?:,|;|$))", requirement)
    return match.group(1) if match else None


def _existing_tags(repo_root: Path) -> frozenset[str]:
    completed = subprocess.run(
        ["git", "tag", "--list"],  # noqa: S607 - git is intentionally resolved from PATH
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return frozenset(completed.stdout.splitlines())


def _topological_layers(keys: Sequence[str], dependencies: Mapping[str, set[str]]) -> list[list[str]]:
    remaining = set(keys)
    emitted: set[str] = set()
    layers: list[list[str]] = []
    while remaining:
        # Stable package order keeps plans readable and reproducible.
        layer = [key for key in keys if key in remaining and dependencies[key] <= emitted]
        if not layer:
            blocked = ", ".join(sorted(remaining))
            raise ReleaseError(f"release dependency graph contains a cycle among: {blocked}")
        layers.append(layer)
        emitted.update(layer)
        remaining.difference_update(layer)
    return layers


def _dependency_closures(keys: Sequence[str], dependencies: Mapping[str, set[str]]) -> dict[str, list[str]]:
    def collect(current: str, found: set[str]) -> None:
        for dependency in dependencies[current]:
            if dependency in found:
                continue
            found.add(dependency)
            collect(dependency, found)

    closures: dict[str, list[str]] = {}
    for key in keys:
        found: set[str] = set()
        collect(key, found)
        closures[key] = [candidate for candidate in keys if candidate in found]
    return closures


def build_plan(
    repo_root: Path,
    *,
    commit: str,
    selected: Sequence[str] | None,
    existing_tags: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Build the exact package list and concurrent publication layers."""
    if FULL_SHA.fullmatch(commit) is None:
        raise ReleaseError(f"release commit must be a full SHA, found {commit!r}")
    tags = _existing_tags(repo_root) if existing_tags is None else existing_tags
    manifests = {spec.key: _manifest(spec, repo_root) for spec in PACKAGE_SPECS}
    versions = {spec.key: _version(spec, manifests[spec.key]) for spec in PACKAGE_SPECS}

    if selected is None:
        keys = [spec.key for spec in PACKAGE_SPECS if f"{spec.tag_prefix}{versions[spec.key]}" not in tags]
    else:
        unknown = sorted(set(selected) - PACKAGE_BY_KEY.keys())
        if unknown:
            raise ReleaseError(f"unknown release packages: {', '.join(unknown)}")
        if len(set(selected)) != len(selected):
            raise ReleaseError("release package list contains duplicates")
        # The registry order makes the same selection produce the same plan.
        keys = [spec.key for spec in PACKAGE_SPECS if spec.key in selected]

    dependencies: dict[str, set[str]] = {key: set() for key in keys}
    citry_dependencies = _python_dependencies(manifests["citry"])
    core_requirement = _dependency(citry_dependencies, "citry-core")
    if core_requirement is None:
        raise ReleaseError("citry must declare its citry-core dependency")
    if "citry-core" in keys and "citry" in keys:
        if _exact_version(core_requirement) != versions["citry-core"]:
            raise ReleaseError("selected Citry does not pin the selected citry-core version")
        dependencies["citry"].add("citry-core")

    for dependent in ("citry-lsp", "citry-ui"):
        if dependent not in keys or "citry" not in keys:
            continue
        requirement = _dependency(_python_dependencies(manifests[dependent]), "citry")
        minimum = _minimum_version(requirement or "")
        # A raised floor needs the selected Citry bytes to be public first.
        if minimum is not None and _numeric_version(minimum) >= _numeric_version(versions["citry"]):
            dependencies[dependent].add("citry")

    if "vscode-citry" in keys:
        extension_config = manifests["vscode-citry"].get("citry")
        lsp_version = extension_config.get("lspVersion") if isinstance(extension_config, dict) else None
        if not isinstance(lsp_version, str):
            raise ReleaseError("VS Code manifest must declare citry.lspVersion")
        if "citry-lsp" in keys:
            if lsp_version != versions["citry-lsp"]:
                raise ReleaseError("selected VS Code extension does not pin the selected citry-lsp version")
            dependencies["vscode-citry"].add("citry-lsp")

    qualification_dependencies = _dependency_closures(keys, dependencies)
    packages = []
    for key in keys:
        spec = PACKAGE_BY_KEY[key]
        tag = f"{spec.tag_prefix}{versions[key]}"
        if selected is not None and tag in tags:
            raise ReleaseError(f"{tag} already exists")
        packages.append(
            {
                "key": key,
                "version": versions[key],
                "tag": tag,
                "workflow": spec.workflow,
                "artifact": spec.artifact,
                "dependencies": sorted(dependencies[key]),
                "qualification_dependencies": qualification_dependencies[key],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "commit": commit,
        "packages": packages,
        "layers": _topological_layers(keys, dependencies),
    }


class GitHubClient:
    """Call the small GitHub Actions API surface used by the coordinator."""

    def __init__(self, *, repository: str, token: str) -> None:
        if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
            raise ReleaseError(f"invalid GitHub repository {repository!r}")
        if not token:
            raise ReleaseError("GH_TOKEN is required")
        self.api_root = f"https://api.github.com/repos/{repository}"
        self.repository = repository
        self.token = token

    def request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(  # noqa: S310 - fixed GitHub API origin
            f"{self.api_root}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub API origin
                raw = response.read()
        except urllib.error.HTTPError as error:
            details = error.read().decode(errors="replace")
            raise ReleaseError(f"GitHub API {method} {path} failed with HTTP {error.code}: {details}") from error
        except (OSError, urllib.error.URLError) as error:
            raise ReleaseError(f"GitHub API {method} {path} failed: {error}") from error
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ReleaseError(f"GitHub API {method} {path} returned invalid JSON") from error
        if not isinstance(value, dict):
            raise ReleaseError(f"GitHub API {method} {path} returned a non-object response")
        return value

    def dispatch(self, *, workflow: str, ref: str, inputs: Mapping[str, str]) -> None:
        workflow_id = urllib.parse.quote(workflow, safe="")
        self.request("POST", f"/actions/workflows/{workflow_id}/dispatches", {"ref": ref, "inputs": inputs})

    def workflow_runs(self, workflow: str) -> list[dict[str, Any]]:
        workflow_id = urllib.parse.quote(workflow, safe="")
        payload = self.request(
            "GET",
            f"/actions/workflows/{workflow_id}/runs?event=workflow_dispatch&branch=main&per_page=50",
        )
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise ReleaseError(f"GitHub returned no workflow runs for {workflow}")
        return [run for run in runs if isinstance(run, dict)]

    def artifacts(self, run_id: int) -> list[dict[str, Any]]:
        payload = self.request("GET", f"/actions/runs/{run_id}/artifacts?per_page=100")
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise ReleaseError(f"GitHub returned no artifacts for workflow run {run_id}")
        return [artifact for artifact in artifacts if isinstance(artifact, dict)]


def verify_producer_run(
    run: Mapping[str, Any],
    *,
    repository: str,
    workflow: str,
    commit: str,
    events: tuple[str, ...] = ("workflow_dispatch",),
) -> None:
    """Require successful evidence from the expected workflow and exact main commit."""
    head_repository = run.get("head_repository")
    if (
        FULL_SHA.fullmatch(commit) is None
        or run.get("path") != f".github/workflows/{workflow}"
        or run.get("event") not in events
        or run.get("head_branch") != "main"
        or run.get("head_sha") != commit
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or not isinstance(head_repository, dict)
        or head_repository.get("full_name") != repository
    ):
        raise ReleaseError(f"run is not a successful {workflow} qualification for {repository}@{commit} on main")


def verify_qualification(
    client: GitHubClient,
    *,
    package: str,
    commit: str,
    run_id: int,
    artifact_id: int,
    artifact_digest: str,
) -> None:
    """Bind retained bytes to their trusted qualification workflow and source."""
    spec = PACKAGE_BY_KEY[package]
    run = client.request("GET", f"/actions/runs/{run_id}")
    verify_producer_run(run, repository=client.repository, workflow=spec.workflow, commit=commit)
    matches = [artifact for artifact in client.artifacts(run_id) if artifact.get("id") == artifact_id]
    if len(matches) != 1:
        raise ReleaseError(f"{package} qualification does not own artifact {artifact_id}")
    artifact = matches[0]
    producer = artifact.get("workflow_run")
    if (
        artifact.get("name") != spec.artifact
        or artifact.get("expired") is not False
        or artifact.get("digest") != artifact_digest
        or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact_digest) is None
        or not isinstance(producer, dict)
        or producer.get("id") != run_id
        or producer.get("head_sha") != commit
    ):
        raise ReleaseError(f"{package} qualification artifact has different source or identity")


def _run_title(operation: str, package: str, candidate_id: str) -> str:
    verb = "Qualify" if operation == "qualify" else "Publish"
    return f"{verb} {package} for candidate {candidate_id}"


def _find_run(client: GitHubClient, *, workflow: str, title: str, started_at: datetime) -> dict[str, Any] | None:
    matches = []
    for run in client.workflow_runs(workflow):
        if run.get("display_title") != title:
            continue
        created_at = run.get("created_at")
        if not isinstance(created_at, str):
            continue
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created >= started_at:
            matches.append(run)
    return max(matches, key=lambda run: int(run.get("id", 0)), default=None)


def _wait_for_runs(
    client: GitHubClient,
    pending: Mapping[str, tuple[str, str]],
    *,
    started_at: datetime,
    timeout_seconds: int,
) -> dict[str, dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    completed: dict[str, dict[str, Any]] = {}
    while len(completed) != len(pending):
        if time.monotonic() >= deadline:
            missing = ", ".join(sorted(set(pending) - completed.keys()))
            raise ReleaseError(f"timed out waiting for workflows: {missing}")
        for package, (workflow, title) in pending.items():
            if package in completed:
                continue
            run = _find_run(client, workflow=workflow, title=title, started_at=started_at)
            if run is None or run.get("status") != "completed":
                continue
            if run.get("conclusion") != "success":
                raise ReleaseError(f"{title} failed: {run.get('html_url', 'unknown run URL')}")
            completed[package] = run
        if len(completed) != len(pending):
            time.sleep(POLL_SECONDS)
    return completed


def qualify_plan(
    plan: Mapping[str, Any],
    *,
    client: GitHubClient,
    ref: str,
    candidate_id: str,
) -> dict[str, Any]:
    """Run every selected qualification concurrently and retain its artifact identity."""
    packages = _plan_packages(plan)
    if not packages:
        raise ReleaseError("release plan selects no packages")
    # GitHub timestamps runs to whole seconds, so include the dispatch second.
    started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    pending: dict[str, tuple[str, str]] = {}
    for package in packages:
        key = package["key"]
        title = _run_title("qualify", key, candidate_id)
        client.dispatch(
            workflow=package["workflow"],
            ref=ref,
            inputs={
                "operation": "qualify",
                "release_commit": str(plan["commit"]),
                "candidate_id": candidate_id,
                "workspace_dependencies": ",".join(package["qualification_dependencies"]),
            },
        )
        pending[key] = (package["workflow"], title)
    runs = _wait_for_runs(
        client,
        pending,
        started_at=started_at,
        timeout_seconds=QUALIFICATION_TIMEOUT_SECONDS,
    )

    qualifications = []
    for package in packages:
        run = runs[package["key"]]
        verify_producer_run(
            run,
            repository=client.repository,
            workflow=package["workflow"],
            commit=str(plan["commit"]),
        )
        run_id = int(run["id"])
        matches = [
            artifact
            for artifact in client.artifacts(run_id)
            if artifact.get("name") == package["artifact"] and artifact.get("expired") is False
        ]
        if len(matches) != 1:
            raise ReleaseError(
                f"{package['key']} qualification must retain one {package['artifact']!r} artifact; "
                f"found {len(matches)}"
            )
        artifact = matches[0]
        artifact_id = artifact.get("id")
        digest = artifact.get("digest")
        if (
            not isinstance(artifact_id, int)
            or not isinstance(digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
        ):
            raise ReleaseError(f"{package['key']} qualification artifact has no valid identity")
        qualifications.append(
            {
                "package": package["key"],
                "run_id": run_id,
                "run_url": run.get("html_url"),
                "artifact_id": artifact_id,
                "artifact_digest": digest,
            }
        )
    return {**dict(plan), "candidate_id": candidate_id, "qualifications": qualifications}


def publish_candidate(
    candidate: Mapping[str, Any],
    *,
    client: GitHubClient,
    ref: str,
    publication_id: str,
    candidate_run_id: int,
) -> None:
    """Publish each dependency layer concurrently from retained candidate bytes."""
    # A correctly shaped JSON bundle alone does not prove who qualified it.
    run = client.request("GET", f"/actions/runs/{candidate_run_id}")
    verify_producer_run(
        run,
        repository=client.repository,
        workflow="repo--release-candidate.yml",
        commit=str(candidate.get("commit", "")),
        events=("push", "workflow_dispatch"),
    )
    packages = {package["key"]: package for package in _plan_packages(candidate)}
    qualifications = _candidate_qualifications(candidate, packages.keys())
    layers = _plan_layers(candidate, packages)
    for layer in layers:
        # GitHub timestamps runs to whole seconds, so include the dispatch second.
        started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        pending: dict[str, tuple[str, str]] = {}
        for key in layer:
            if key not in packages:
                raise ReleaseError(f"publication layer names unknown package {key!r}")
            package = packages[key]
            qualification = qualifications[key]
            title = _run_title("promote", key, publication_id)
            client.dispatch(
                workflow=package["workflow"],
                ref=ref,
                inputs={
                    "operation": "promote",
                    "release_commit": str(candidate["commit"]),
                    "candidate_id": publication_id,
                    "qualification_run_id": str(qualification["run_id"]),
                    "qualification_artifact_id": str(qualification["artifact_id"]),
                    "qualification_artifact_digest": qualification["artifact_digest"],
                },
            )
            pending[key] = (package["workflow"], title)
        _wait_for_runs(
            client,
            pending,
            started_at=started_at,
            timeout_seconds=PUBLICATION_TIMEOUT_SECONDS,
        )


def _plan_packages(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema_version") != SCHEMA_VERSION or FULL_SHA.fullmatch(str(plan.get("commit", ""))) is None:
        raise ReleaseError("release plan has an unsupported schema or commit")
    packages = plan.get("packages")
    if not isinstance(packages, list) or not all(isinstance(package, dict) for package in packages):
        raise ReleaseError("release plan has no package list")
    keys = [package.get("key") for package in packages]
    if len(set(keys)) != len(keys) or any(key not in PACKAGE_BY_KEY for key in keys):
        raise ReleaseError("release plan contains duplicate or unknown packages")
    package_keys = set(keys)
    for package in packages:
        key = package["key"]
        spec = PACKAGE_BY_KEY[key]
        direct = package.get("dependencies")
        closure = package.get("qualification_dependencies")
        version = package.get("version")
        if (
            not isinstance(version, str)
            or package.get("tag") != f"{spec.tag_prefix}{version}"
            or package.get("workflow") != spec.workflow
            or package.get("artifact") != spec.artifact
            or not isinstance(direct, list)
            or not isinstance(closure, list)
            or not all(isinstance(key, str) for key in [*direct, *closure])
            or not set(direct) <= set(closure) <= package_keys
        ):
            raise ReleaseError(f"release plan has invalid package metadata for {package.get('key')}")
    return packages


def _plan_layers(plan: Mapping[str, Any], packages: Mapping[str, Mapping[str, Any]]) -> list[list[str]]:
    layers = plan.get("layers")
    if not isinstance(layers, list) or not all(isinstance(layer, list) and layer for layer in layers):
        raise ReleaseError("candidate has no valid publication layers")
    emitted: set[str] = set()
    for layer in layers:
        if not all(isinstance(key, str) for key in layer) or len(set(layer)) != len(layer):
            raise ReleaseError("candidate publication layer contains duplicate or invalid packages")
        for key in layer:
            if key not in packages or key in emitted:
                raise ReleaseError(f"candidate publication layer names invalid package {key!r}")
            if not set(packages[key]["dependencies"]) <= emitted:
                raise ReleaseError(f"candidate publication layer starts {key!r} before its dependencies")
        emitted.update(layer)
    if emitted != set(packages):
        raise ReleaseError("candidate publication layers do not cover every selected package")
    return layers


def _candidate_qualifications(
    candidate: Mapping[str, Any],
    package_keys: Iterable[str],
) -> dict[str, dict[str, Any]]:
    raw = candidate.get("qualifications")
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ReleaseError("candidate has no qualification list")
    qualifications = {item.get("package"): item for item in raw}
    if set(qualifications) != set(package_keys):
        raise ReleaseError("candidate qualifications do not match its selected packages")
    for key, item in qualifications.items():
        if (
            not isinstance(item.get("run_id"), int)
            or not isinstance(item.get("artifact_id"), int)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", str(item.get("artifact_digest", ""))) is None
        ):
            raise ReleaseError(f"candidate qualification for {key} has invalid artifact identity")
    return qualifications


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReleaseError(f"could not read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ReleaseError(f"{path} must contain an object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _selected(value: str) -> Sequence[str] | None:
    if value == "auto":
        return None
    selected = [item.strip() for item in value.split(",") if item.strip()]
    if not selected:
        raise ReleaseError("--packages must be 'auto' or a comma-separated package list")
    return selected


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="write the exact package graph for one commit")
    plan.add_argument("--repo-root", type=Path, default=Path.cwd())
    plan.add_argument("--commit", required=True)
    plan.add_argument("--packages", default="auto")
    plan.add_argument("--output", type=Path, required=True)

    qualify = subparsers.add_parser("qualify", help="dispatch all qualifications and write a candidate bundle")
    qualify.add_argument("--plan", type=Path, required=True)
    qualify.add_argument("--repository", required=True)
    qualify.add_argument("--ref", default="main")
    qualify.add_argument("--candidate-id", required=True)
    qualify.add_argument("--output", type=Path, required=True)

    publish = subparsers.add_parser("publish", help="publish a candidate in dependency layers")
    publish.add_argument("--candidate", type=Path, required=True)
    publish.add_argument("--repository", required=True)
    publish.add_argument("--ref", default="main")
    publish.add_argument("--publication-id", required=True)
    publish.add_argument("--candidate-run-id", type=int, required=True)

    verify = subparsers.add_parser(
        "verify-qualification", help="verify the exact trusted producer of a retained bundle"
    )
    verify.add_argument("--repository", required=True)
    verify.add_argument("--package", choices=PACKAGE_BY_KEY, required=True)
    verify.add_argument("--commit", required=True)
    verify.add_argument("--run-id", type=int, required=True)
    verify.add_argument("--artifact-id", type=int, required=True)
    verify.add_argument("--artifact-digest", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the release controller."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            plan = build_plan(
                args.repo_root,
                commit=args.commit,
                selected=_selected(args.packages),
            )
            _write_json(args.output, plan)
            sys.stdout.write(json.dumps(plan, indent=2, sort_keys=True) + "\n")
            return 0

        token = os.environ.get("GH_TOKEN", "")
        client = GitHubClient(repository=args.repository, token=token)
        if args.command == "verify-qualification":
            verify_qualification(
                client,
                package=args.package,
                commit=args.commit,
                run_id=args.run_id,
                artifact_id=args.artifact_id,
                artifact_digest=args.artifact_digest,
            )
            return 0
        if args.command == "qualify":
            candidate = qualify_plan(
                _load_json(args.plan),
                client=client,
                ref=args.ref,
                candidate_id=args.candidate_id,
            )
            _write_json(args.output, candidate)
            return 0

        publish_candidate(
            _load_json(args.candidate),
            client=client,
            ref=args.ref,
            publication_id=args.publication_id,
            candidate_run_id=args.candidate_run_id,
        )
        return 0
    except ReleaseError as error:
        sys.stderr.write(f"release error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
