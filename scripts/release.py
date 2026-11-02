"""Plan, qualify, and publish a Citry monorepo release as one operation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import tomllib

from scripts.pypi_release import PyPIReleaseError, compare_public, public_state

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

SCHEMA_VERSION: Final = 1
API_VERSION: Final = "2022-11-28"
POLL_SECONDS: Final = 10
# While runs are still going, repeat their states this often, so a long wait
# keeps adding lines to the Actions log.
PROGRESS_SECONDS: Final = 5 * 60
# How often the waiter reads a running run's jobs to catch a failed one early.
JOB_CHECK_SECONDS: Final = 60
# On 2026-10-28 some citry-core qualification jobs waited about 40 minutes for
# a runner, and the run took 65 minutes. Two hours leaves room for a slower day.
QUALIFICATION_TIMEOUT_SECONDS: Final = 2 * 60 * 60
PUBLICATION_TIMEOUT_SECONDS: Final = 20 * 60
# The VS Code worker waits up to 45 minutes for the Open VSX review on top of
# its usual work, so its publish run gets a longer limit.
VSCODE_PUBLICATION_TIMEOUT_SECONDS: Final = 75 * 60
# A publish step that fails during a passing registry or signing outage is
# started again this many times, this long after the failure. On 2026-11-02
# sigstore's signing log answered 502 for a few minutes; three tries spread
# over ten minutes cover an outage like that without stalling a real failure
# for long.
PUBLISH_RETRIES: Final = 2
RETRY_DELAY_SECONDS: Final = 5 * 60
# The publish workers' steps that talk to a registry or to sigstore, which can
# fail for a few minutes and then work again. A failure in any other step
# (a hash check, a tag check) is not retried, because running it again gives
# the same answer. packages/py/citry/tests/test_release_controller.py checks that every name here
# is still a step in a publish workflow.
RETRYABLE_STEPS: Final = frozenset(
    {
        "Attest the promotion of the qualified bytes",
        "Publish to PyPI",
        "Publish the qualified VSIX to Visual Studio Marketplace",
        "Publish the same VSIX to Open VSX",
    }
)
FAILED_CONCLUSIONS: Final = frozenset({"failure", "cancelled", "timed_out"})
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
    publish_timeout_seconds: int = PUBLICATION_TIMEOUT_SECONDS


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
        VSCODE_PUBLICATION_TIMEOUT_SECONDS,
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

    def _headers(self, request: urllib.request.Request) -> None:
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Content-Type", "application/json")
        request.add_header("X-GitHub-Api-Version", API_VERSION)
        # An artifact download redirects to blob storage, which rejects a
        # second credential; an unredirected header stays with GitHub.
        request.add_unredirected_header("Authorization", f"Bearer {self.token}")

    def _call(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None,
        *,
        missing_ok: bool,
    ) -> dict[str, Any] | None:
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(f"{self.api_root}{path}", data=body, method=method)  # noqa: S310 - fixed GitHub API origin
        self._headers(request)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub API origin
                raw = response.read()
        except urllib.error.HTTPError as error:
            # A missing tag or GitHub Release is an answer, not a failure, when
            # the caller asks whether it exists.
            if missing_ok and error.code == 404:
                return None
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

    def request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = self._call(method, path, payload, missing_ok=False)
        # `_call` returns None only for a 404 that the caller allowed.
        return {} if value is None else value

    def request_if_present(self, path: str) -> dict[str, Any] | None:
        """GET one resource, returning None when GitHub answers 404."""
        return self._call("GET", path, None, missing_ok=True)

    def tag_commit(self, tag: str) -> str | None:
        """Return the commit a tag names, or None when the tag does not exist."""
        ref = self.request_if_present(f"/git/ref/tags/{urllib.parse.quote(tag, safe='')}")
        if ref is None:
            return None
        target = ref.get("object")
        if not isinstance(target, dict):
            raise ReleaseError(f"GitHub returned no object for tag {tag}")
        # Release tags are annotated, so the ref names a tag object that in
        # turn names the commit.
        if target.get("type") == "tag":
            tag_object = self.request("GET", f"/git/tags/{target.get('sha')}")
            target = tag_object.get("object")
            if not isinstance(target, dict):
                raise ReleaseError(f"GitHub returned no commit for tag {tag}")
        if target.get("type") != "commit" or not isinstance(target.get("sha"), str):
            raise ReleaseError(f"tag {tag} does not name a commit")
        return str(target["sha"])

    def release_exists(self, tag: str) -> bool:
        """Return whether a GitHub Release exists for the tag."""
        return self.request_if_present(f"/releases/tags/{urllib.parse.quote(tag, safe='')}") is not None

    def download_artifact(self, artifact_id: int, destination: Path) -> None:
        """Save one workflow artifact's zip archive to a file."""
        request = urllib.request.Request(  # noqa: S310 - fixed GitHub API origin
            f"{self.api_root}/actions/artifacts/{artifact_id}/zip"
        )
        self._headers(request)
        try:
            with (
                urllib.request.urlopen(request, timeout=120) as response,  # noqa: S310 - fixed GitHub API origin
                destination.open("wb") as stream,
            ):
                # The citry-core archive is about 400 MB, so copy it in pieces
                # rather than holding it in memory.
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
        except (OSError, urllib.error.URLError) as error:
            raise ReleaseError(f"could not download artifact {artifact_id}: {error}") from error

    def rerun_failed_jobs(self, run_id: int) -> None:
        """Start the failed jobs of a finished run again, with the jobs that depend on them."""
        self.request("POST", f"/actions/runs/{run_id}/rerun-failed-jobs")

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


class RegistryClient:
    """Read public package registries over HTTPS without credentials."""

    def get(self, url: str) -> tuple[int, bytes]:
        """Return the HTTP status and body for one URL; a 404 is an answer, not an error."""
        if not url.startswith("https://"):
            raise ReleaseError(f"registry URL must use HTTPS: {url}")
        request = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})  # noqa: S310 - HTTPS checked above
        try:
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - HTTPS checked above
                body = response.read()
                encoding = response.headers.get("Content-Encoding", "")
                status = int(response.status)
        except urllib.error.HTTPError as error:
            return error.code, b""
        except (OSError, urllib.error.URLError) as error:
            raise ReleaseError(f"could not read {url}: {error}") from error
        # The Marketplace compresses its VSIX download; the hash must be of
        # the VSIX itself, as the worker's `curl --compressed` sees it.
        return status, gzip.decompress(body) if encoding == "gzip" else body


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def qualified_files(archive: Path, artifact_digest: str) -> dict[str, str]:
    """
    Return each qualified file's name and SHA-256 from a retained qualification archive.

    The archive must hash to the digest the candidate recorded, and every file
    named in its `release-inventory.json` must be in the archive with that
    hash, so the result describes exactly the bytes qualification approved.
    """
    match = re.fullmatch(r"sha256:([0-9a-f]{64})", artifact_digest)
    if match is None or _sha256_file(archive) != match.group(1):
        raise ReleaseError(f"qualification archive does not match digest {artifact_digest}")
    try:
        with zipfile.ZipFile(archive) as bundle:
            inventory = json.loads(bundle.read("release-inventory.json"))
            entries = inventory.get("artifacts") if isinstance(inventory, dict) else None
            if not isinstance(entries, list) or not entries:
                raise ReleaseError("qualification inventory has no artifacts")
            files: dict[str, str] = {}
            for entry in entries:
                name = entry.get("name") if isinstance(entry, dict) else None
                recorded = entry.get("sha256") if isinstance(entry, dict) else None
                if not isinstance(name, str) or not isinstance(recorded, str) or name in files:
                    raise ReleaseError("qualification inventory has an invalid or repeated artifact")
                digest = hashlib.sha256()
                with bundle.open(name) as stream:
                    while chunk := stream.read(1024 * 1024):
                        digest.update(chunk)
                # The inventory is only a list of claims; hash the archived
                # file itself so a wrong entry cannot vouch for other bytes.
                if digest.hexdigest() != recorded:
                    raise ReleaseError(f"qualified file {name} does not match its inventory hash")
                files[name] = recorded
    except (KeyError, OSError, ValueError, zipfile.BadZipFile) as error:
        raise ReleaseError(f"could not read the qualification archive: {error}") from error
    return files


def _vscode_registry_files(registry: RegistryClient, version: str, name: str) -> dict[str, dict[str, str]]:
    """Download the VSIX from both extension registries and hash what each one serves."""
    found: dict[str, dict[str, str]] = {}
    marketplace_url = (
        "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/citry-dev/"
        f"vsextensions/citry/{version}/vspackage"
    )
    status, body = registry.get(marketplace_url)
    if status not in {200, 404}:
        raise ReleaseError(f"could not read the Marketplace version {version}; HTTP {status}")
    found["Visual Studio Marketplace"] = {name: hashlib.sha256(body).hexdigest()} if status == 200 else {}

    status, body = registry.get(f"https://open-vsx.org/api/citry-dev/citry/{version}")
    if status not in {200, 404}:
        raise ReleaseError(f"could not read the Open VSX version {version}; HTTP {status}")
    found["Open VSX"] = {}
    if status == 200:
        try:
            download = json.loads(body)["files"]["download"]
        except (KeyError, TypeError, ValueError) as error:
            raise ReleaseError(f"Open VSX returned no download link for {version}") from error
        status, vsix = registry.get(str(download))
        if status != 200:
            raise ReleaseError(f"could not download the Open VSX VSIX {version}; HTTP {status}")
        found["Open VSX"] = {name: hashlib.sha256(vsix).hexdigest()}
    return found


def registry_state(
    package: str,
    version: str,
    expected: Mapping[str, str],
    registry: RegistryClient,
) -> str:
    """
    Compare a package's public files with the qualified ones by SHA-256.

    Returns:
        "absent" when no registry has the version, "partial" when some files
        or registries are still missing, and "complete" when every registry
        serves every qualified file.

    Raises:
        ReleaseError: A registry serves a file whose bytes differ from the
            qualified file, or a file qualification never produced. The
            message names the registry and the file.

    """
    if PACKAGE_BY_KEY[package].manifest_kind == "json":
        if len(expected) != 1:
            raise ReleaseError("the VS Code qualification must contain exactly one VSIX")
        public_by_registry = _vscode_registry_files(registry, version, next(iter(expected)))
        states = []
        for name, public in public_by_registry.items():
            try:
                states.append(compare_public(expected, public))
            except PyPIReleaseError as error:
                raise ReleaseError(f"{package} {version} on {name}: {error}") from error
        if all(state == "complete" for state in states):
            return "complete"
        return "absent" if all(state == "absent" for state in states) else "partial"

    status, body = registry.get(f"https://pypi.org/pypi/{package}/{version}/json")
    try:
        payload = json.loads(body) if status == 200 else None
        inventory = {"artifacts": [{"name": name, "sha256": digest} for name, digest in expected.items()]}
        # One comparison serves this controller and the publish workers, so
        # both accept and reject exactly the same public state.
        return public_state(status=status, inventory=inventory, payload=payload)
    except (PyPIReleaseError, ValueError) as error:
        raise ReleaseError(f"{package} {version} on PyPI: {error}") from error


def already_published(
    client: GitHubClient,
    registry: RegistryClient,
    *,
    package: Mapping[str, Any],
    qualification: Mapping[str, Any],
    commit: str,
) -> bool:
    """
    Return whether an earlier release run already finished this package from the same bytes.

    A package counts as finished only when its tag names the candidate commit,
    its GitHub Release exists, and every registry serves exactly the qualified
    files. Anything less returns False, and the publish worker finishes the
    rest: it uploads only missing files and creates a missing tag or Release.
    """
    key = str(package["key"])
    tag = str(package["tag"])
    tagged = client.tag_commit(tag)
    # The tag is the last thing a worker creates before its GitHub Release,
    # so a first release run, where no tag exists yet, costs one API call.
    if tagged is None:
        return False
    if tagged != commit:
        raise ReleaseError(f"{tag} names commit {tagged}, not the candidate commit {commit}")
    if not client.release_exists(tag):
        _log(f"{tag} exists without a GitHub Release; its publish worker will finish it")
        return False
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "qualification.zip"
        client.download_artifact(int(qualification["artifact_id"]), archive)
        expected = qualified_files(archive, str(qualification["artifact_digest"]))
    state = registry_state(key, str(package["version"]), expected, registry)
    if state != "complete":
        _log(f"{tag} is {state} on its registries; its publish worker will upload the rest")
        return False
    _log(f"{tag} is already published from the qualified bytes; skipping it")
    return True


def _log(message: str) -> None:
    """Report one progress line in the Actions log as it happens."""
    # Progress goes to stderr beside the `release error:` line, which keeps
    # stdout for the JSON that `plan` prints.
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()


def _run_state(run: Mapping[str, Any] | None) -> str:
    if run is None:
        return "no run found yet"
    status = str(run.get("status", "unknown"))
    return f"{status}/{run.get('conclusion')}" if status == "completed" else status


def _jobs(client: GitHubClient, run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read a run's jobs, with their steps, for the latest attempt of the run."""
    try:
        payload = client.request("GET", f"/actions/runs/{run.get('id')}/jobs?per_page=100")
    except Exception:  # noqa: BLE001 - the job details are optional
        # The caller still raises the run failure; a failed job lookup only
        # drops the job names and turns off a retry, whatever went wrong.
        return []
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return []
    return [job for job in jobs if isinstance(job, dict)]


def _failed_job_names(jobs: Iterable[Mapping[str, Any]]) -> list[str]:
    return [str(job.get("name")) for job in jobs if job.get("conclusion") in FAILED_CONCLUSIONS]


def _failed_jobs(client: GitHubClient, run: Mapping[str, Any]) -> list[str]:
    """List the jobs that made a run fail, so the error message points at the cause."""
    return _failed_job_names(_jobs(client, run))


def should_retry(jobs: Sequence[Mapping[str, Any]], *, retries_used: int, max_retries: int) -> bool:
    """
    Decide whether a failed publish run is worth starting again.

    A retry is worth it only when every failed job failed in a step that talks
    to a registry or to sigstore (`RETRYABLE_STEPS`). A cancelled or timed-out
    job, a job without a failed step, or a failed check step would fail the
    same way again, so those stop the release at once.
    """
    if retries_used >= max_retries:
        return False
    failed = [job for job in jobs if job.get("conclusion") in FAILED_CONCLUSIONS]
    if not failed:
        return False
    for job in failed:
        if job.get("conclusion") != "failure":
            return False
        steps = job.get("steps")
        failed_steps = [
            str(step.get("name"))
            for step in (steps if isinstance(steps, list) else [])
            if isinstance(step, dict) and step.get("conclusion") == "failure"
        ]
        if not failed_steps or not set(failed_steps) <= RETRYABLE_STEPS:
            return False
    return True


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


def _run_attempt(run: Mapping[str, Any]) -> int:
    attempt = run.get("run_attempt", 1)
    return attempt if isinstance(attempt, int) else 1


def _wait_for_runs(
    client: GitHubClient,
    pending: Mapping[str, tuple[str, str]],
    *,
    started_at: datetime,
    timeout_seconds: int,
    max_retries: int = 0,
) -> dict[str, dict[str, Any]]:
    started = time.monotonic()
    deadline = started + timeout_seconds
    next_progress = started + PROGRESS_SECONDS
    # Reading jobs costs one API call per run, so the waiter reads each run's
    # jobs every `JOB_CHECK_SECONDS`, not on every poll.
    next_job_check = dict.fromkeys(pending, started + JOB_CHECK_SECONDS)
    completed: dict[str, dict[str, Any]] = {}
    # The run id and state last logged for each package, so only a change
    # prints a line.
    states: dict[str, tuple[object, str]] = {}
    # The newest run seen for each package, listed in the still-waiting line.
    latest: dict[str, dict[str, Any] | None] = dict.fromkeys(pending)
    # Retries already started for each package, and when a scheduled retry is
    # due. A retry waits `RETRY_DELAY_SECONDS` so a passing outage can end.
    retries_used = dict.fromkeys(pending, 0)
    retry_due: dict[str, float] = {}
    # After a retry starts, GitHub can still report the failed attempt for a
    # few polls; states from attempts below this number are old news.
    current_attempt = dict.fromkeys(pending, 1)
    while len(completed) != len(pending):
        if time.monotonic() >= deadline:
            missing = ", ".join(sorted(set(pending) - completed.keys()))
            raise ReleaseError(f"timed out waiting for workflows: {missing}")
        for package, (workflow, title) in pending.items():
            if package in completed:
                continue
            run = _find_run(client, workflow=workflow, title=title, started_at=started_at)
            latest[package] = run
            if run is None:
                continue
            if package in retry_due:
                if time.monotonic() < retry_due[package]:
                    continue
                del retry_due[package]
                current_attempt[package] = _run_attempt(run) + 1
                client.rerun_failed_jobs(int(run["id"]))
                # The new attempt gets the same time limit as the first one.
                deadline = max(deadline, time.monotonic() + timeout_seconds)
                _log(f"{title}: started attempt {current_attempt[package]}: {run.get('html_url', 'unknown run URL')}")
                continue
            if _run_attempt(run) < current_attempt[package]:
                continue
            state = _run_state(run)
            if states.get(package) != (run.get("id"), state):
                # A newly seen run carries its URL, so the log links to every run,
                # including one dispatched again by hand under the same title.
                is_new_run = states.get(package, (None, ""))[0] != run.get("id")
                link = f": {run.get('html_url', 'unknown run URL')}" if is_new_run else ""
                _log(f"{title}: {state}{link}")
                states[package] = (run.get("id"), state)
            if run.get("status") != "completed":
                # A run reports its failure only after its slowest job ends,
                # so stop at the first failed job and name it, unless the job
                # can be retried; a retry can start only once the run ends.
                if time.monotonic() >= next_job_check[package]:
                    next_job_check[package] = time.monotonic() + JOB_CHECK_SECONDS
                    jobs = _jobs(client, run)
                    names = _failed_job_names(jobs)
                    if names and not should_retry(jobs, retries_used=retries_used[package], max_retries=max_retries):
                        raise ReleaseError(
                            f"{title} failed in jobs {', '.join(names)} while its other jobs were still running: "
                            f"{run.get('html_url', 'unknown run URL')}"
                        )
                continue
            if run.get("conclusion") != "success":
                jobs = _jobs(client, run)
                names = _failed_job_names(jobs)
                if should_retry(jobs, retries_used=retries_used[package], max_retries=max_retries):
                    retries_used[package] += 1
                    retry_due[package] = time.monotonic() + RETRY_DELAY_SECONDS
                    _log(
                        f"{title} failed in jobs {', '.join(names)}; retry {retries_used[package]}/{max_retries} "
                        f"starts in {RETRY_DELAY_SECONDS // 60} min and skips files the registry already holds"
                    )
                    continue
                detail = f" in jobs {', '.join(names)}" if names else ""
                raise ReleaseError(f"{title} failed{detail}: {run.get('html_url', 'unknown run URL')}")
            completed[package] = run
        if len(completed) != len(pending):
            if time.monotonic() >= next_progress:
                minutes = int((time.monotonic() - started) // 60)
                waiting = ", ".join(
                    f"{package} ({_run_state(latest[package])})" for package in pending if package not in completed
                )
                _log(f"Still waiting after {minutes} min on: {waiting}")
                next_progress += PROGRESS_SECONDS
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
    _log(
        f"Qualifying {len(packages)} package(s) at {plan['commit']} for candidate {candidate_id}: "
        + ", ".join(f"{package['key']} {package['version']}" for package in packages)
    )
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
        _log(f"Dispatched {title} ({package['workflow']})")
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
        _log(f"Retained {package['key']} artifact {artifact_id} ({digest}) from run {run_id}")
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
    registry: RegistryClient | None = None,
) -> None:
    """
    Publish each dependency layer concurrently from retained candidate bytes.

    The run can be started again for the same candidate after any failure. A
    package an earlier run already finished from the same bytes is skipped,
    and every other package is sent to its publish worker, which uploads only
    the files its registry is missing.
    """
    registry = RegistryClient() if registry is None else registry
    # A correctly shaped JSON bundle alone does not prove who qualified it.
    run = client.request("GET", f"/actions/runs/{candidate_run_id}")
    verify_producer_run(
        run,
        repository=client.repository,
        workflow="repo--release-candidate.yml",
        commit=str(candidate.get("commit", "")),
        events=("push", "workflow_dispatch"),
    )
    _log(f"Verified candidate run {candidate_run_id} for {candidate.get('commit')}")
    packages = {package["key"]: package for package in _plan_packages(candidate)}
    qualifications = _candidate_qualifications(candidate, packages.keys())
    layers = _plan_layers(candidate, packages)
    for number, layer in enumerate(layers, start=1):
        # Name the layer before dispatching it, so the log shows which packages
        # are publishing now. The publish runs are titled with this release
        # run's id, which differs from the candidate run id.
        _log(
            f"Publishing layer {number}/{len(layers)} (publication {publication_id}): "
            + ", ".join(f"{key} {packages[key]['version']}" for key in layer)
        )
        # GitHub timestamps runs to whole seconds, so include the dispatch second.
        started_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        pending: dict[str, tuple[str, str]] = {}
        for key in layer:
            if key not in packages:
                raise ReleaseError(f"publication layer names unknown package {key!r}")
            package = packages[key]
            qualification = qualifications[key]
            if already_published(
                client,
                registry,
                package=package,
                qualification=qualification,
                commit=str(candidate["commit"]),
            ):
                continue
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
            _log(f"Dispatched {title} from qualification run {qualification['run_id']}")
        if pending:
            _wait_for_runs(
                client,
                pending,
                started_at=started_at,
                # The slowest worker in the layer sets the limit for the layer.
                timeout_seconds=max(PACKAGE_BY_KEY[key].publish_timeout_seconds for key in pending),
                max_retries=PUBLISH_RETRIES,
            )
        _log(f"Layer {number}/{len(layers)} published: {', '.join(layer)}")
    _log(f"Published every package in candidate run {candidate_run_id}")


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
