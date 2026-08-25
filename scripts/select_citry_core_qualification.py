"""Select a successful exact-commit workflow run and its artifact when required."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

API_VERSION: Final = "2022-11-28"
ARTIFACT_NAME: Final = "verified-citry-core-distributions"


class QualificationSelectionError(RuntimeError):
    """A matching successful workflow run cannot be selected safely."""


def _request_json(url: str, *, token: str) -> dict[str, Any]:
    request = urllib.request.Request(  # noqa: S310 - the caller constructs an HTTPS GitHub API URL
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub API origin
            payload: Any = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise QualificationSelectionError(f"GitHub API request failed: {error}") from error
    if not isinstance(payload, dict):
        raise QualificationSelectionError("GitHub API returned a non-object response")
    return payload


def select_run(
    payload: Mapping[str, Any],
    *,
    repository: str,
    commit: str,
    branch: str = "main",
    event: str = "workflow_dispatch",
) -> dict[str, Any]:
    """Choose the newest successful workflow run for one main commit."""
    raw_runs = payload.get("workflow_runs")
    if not isinstance(raw_runs, list):
        raise QualificationSelectionError("workflow-runs response has no workflow_runs list")
    matches: list[dict[str, Any]] = []
    for raw in raw_runs:
        if not isinstance(raw, dict):
            continue
        head_repository = raw.get("head_repository")
        head_name = head_repository.get("full_name") if isinstance(head_repository, dict) else None
        if (
            raw.get("event") == event
            and raw.get("status") == "completed"
            and raw.get("conclusion") == "success"
            and raw.get("head_sha") == commit
            and raw.get("head_branch") == branch
            and head_name == repository
        ):
            matches.append(raw)
    if not matches:
        run_kind = "manual qualification" if event == "workflow_dispatch" else f"{event} workflow run"
        raise QualificationSelectionError(f"no successful {run_kind} exists for {repository}@{commit} on {branch}")
    matches.sort(
        key=lambda run: (
            int(run.get("run_number", 0)),
            int(run.get("run_attempt", 0)),
            int(run.get("id", 0)),
        )
    )
    selected = matches[-1]
    if not isinstance(selected.get("id"), int) or not isinstance(selected.get("html_url"), str):
        raise QualificationSelectionError("selected qualification run has incomplete identity metadata")
    return selected


def select_artifact(
    payload: Mapping[str, Any],
    *,
    commit: str,
    run_id: int | None = None,
    artifact_name: str = ARTIFACT_NAME,
) -> dict[str, Any]:
    """Require one live verified bundle whose provenance names the same commit."""
    raw_artifacts = payload.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise QualificationSelectionError("artifacts response has no artifacts list")
    matches = [
        artifact
        for artifact in raw_artifacts
        if isinstance(artifact, dict) and artifact.get("name") == artifact_name and artifact.get("expired") is False
    ]
    if len(matches) != 1:
        raise QualificationSelectionError(
            f"qualification run must have one live {artifact_name!r} artifact; found {len(matches)}"
        )
    selected = matches[0]
    workflow_run = selected.get("workflow_run")
    artifact_commit = workflow_run.get("head_sha") if isinstance(workflow_run, dict) else None
    artifact_run_id = workflow_run.get("id") if isinstance(workflow_run, dict) else None
    if artifact_commit != commit:
        raise QualificationSelectionError(
            f"qualification artifact names commit {artifact_commit!r}, expected {commit!r}"
        )
    if run_id is not None and artifact_run_id != run_id:
        raise QualificationSelectionError(f"qualification artifact names run {artifact_run_id!r}, expected {run_id!r}")
    digest = selected.get("digest")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise QualificationSelectionError("qualification artifact has no valid SHA-256 digest")
    if not isinstance(selected.get("id"), int):
        raise QualificationSelectionError("qualification artifact has no numeric ID")
    return selected


def select_qualification(
    *,
    repository: str,
    commit: str,
    workflow: str,
    token: str,
    artifact_name: str | None = ARTIFACT_NAME,
    event: str = "workflow_dispatch",
) -> dict[str, str]:
    """Find an exact-commit workflow run and optional immutable artifact."""
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise QualificationSelectionError(f"expected a full commit SHA, found {commit!r}")
    workflow_id = urllib.parse.quote(workflow, safe="")
    api_root = f"https://api.github.com/repos/{repository}"
    query = urllib.parse.urlencode(
        {
            "branch": "main",
            "event": event,
            "head_sha": commit,
            "per_page": 100,
            "status": "success",
        }
    )
    runs_url = f"{api_root}/actions/workflows/{workflow_id}/runs?{query}"
    run = select_run(
        _request_json(runs_url, token=token),
        repository=repository,
        commit=commit,
        event=event,
    )
    run_id = int(run["id"])
    if artifact_name is None:
        return {
            "run_id": str(run_id),
            "run_url": str(run["html_url"]),
            "head_sha": commit,
        }
    artifacts_url = f"{api_root}/actions/runs/{run_id}/artifacts?per_page=100"
    artifact = select_artifact(
        _request_json(artifacts_url, token=token),
        commit=commit,
        run_id=run_id,
        artifact_name=artifact_name,
    )
    return {
        "run_id": str(run_id),
        "run_url": str(run["html_url"]),
        "artifact_id": str(artifact["id"]),
        "artifact_digest": str(artifact["digest"]),
        "head_sha": commit,
    }


def _write_github_output(path: Path, values: Mapping[str, str]) -> None:
    # These identifiers contain no newlines, so GitHub's simple key=value form
    # is sufficient and keeps the promotion step easy to audit.
    with path.open("a", encoding="utf-8") as stream:
        for name, value in values.items():
            stream.write(f"{name}={value}\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Select one exact-commit workflow run and expose its identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workflow", default="py--citry-core--publish.yml")
    parser.add_argument("--artifact-name", default=ARTIFACT_NAME)
    parser.add_argument("--event", choices=("push", "workflow_dispatch"), default="workflow_dispatch")
    parser.add_argument("--no-artifact", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        parser.error("GH_TOKEN is required")
    try:
        report = select_qualification(
            repository=args.repository,
            commit=args.commit,
            workflow=args.workflow,
            token=token,
            artifact_name=None if args.no_artifact else args.artifact_name,
            event=args.event,
        )
    except QualificationSelectionError as error:
        parser.exit(1, f"qualification selection failed: {error}\n")
    if args.github_output is not None:
        _write_github_output(args.github_output, report)
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
