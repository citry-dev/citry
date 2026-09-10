"""Keep package publication and release App credentials in separate jobs."""

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("citry-core", "citry", "citry-lsp", "citry-ui", "pygments-citry", "vscode-citry")
TAG_WORKFLOW = "repo--release-tag.yml"
APP_JOBS = {(TAG_WORKFLOW, "tag"), ("repo--docs-release.yml", "commit")}


def check(root: Path = ROOT) -> list[str]:
    """Check the reviewed workflow structure; GitHub environment rules enforce refs."""
    errors: list[str] = []
    directory = root / ".github/workflows"
    workflows: dict[str, Any] = {}
    for path in directory.glob("*.yml"):
        workflows[path.name] = yaml.safe_load(path.read_text())
    publishers = {
        ("vscode--citry--publish.yml" if package == "vscode-citry" else f"py--{package}--publish.yml"): package
        for package in PACKAGES
    }
    for filename, workflow in workflows.items():
        for name, job in workflow.get("jobs", {}).items():
            environment = job.get("environment")
            if isinstance(environment, dict):
                environment = environment.get("name")
            if job.get("uses") == f"./.github/workflows/{TAG_WORKFLOW}" and (
                filename not in publishers or name != "tag"
            ):
                errors.append(f"{filename}:{name} calls protected tag creation outside the package publishers")
            if environment in ("pypi", "vscode-marketplaces") and (filename not in publishers or name != "release"):
                errors.append(f"{filename}:{name} has a publishing environment outside its publication job")
            if environment == "release-maintenance" and (filename, name) not in APP_JOBS:
                errors.append(f"{filename}:{name} has unexpected release App access")
            if "RELEASE_APP_PRIVATE_KEY" in str(job) and (filename, name) not in APP_JOBS:
                errors.append(f"{filename}:{name} uses the release key outside its isolated write job")
    for filename, package in publishers.items():
        jobs = workflows.get(filename, {}).get("jobs", {})
        release, tag, closeout = (jobs.get(name, {}) for name in ("release", "tag", "closeout"))
        expected_environment = "vscode-marketplaces" if package == "vscode-citry" else "pypi"
        if release.get("environment") != expected_environment:
            errors.append(f"{filename} publication must use {expected_environment}")
        if release.get("permissions", {}).get("contents") != "read":
            errors.append(f"{filename} publication must not write repository contents")
        if tag.get("uses") != f"./.github/workflows/{TAG_WORKFLOW}" or "release" not in tag.get("needs", []):
            errors.append(f"{filename} must create its tag only after verified publication")
        if tag.get("if") or tag.get("secrets"):
            errors.append(f"{filename} tag creation must use successful dependencies and its own environment secrets")
        if (
            tag.get("with", {}).get("release_commit") != "${{ inputs.release_commit }}"
            or tag.get("with", {}).get("release_tag") != package + "@${{ needs.verify-version.outputs.version }}"
        ):
            errors.append(f"{filename} tag creation must use the published source identity")
        if tag.get("with", {}).get("package") != package:
            errors.append(f"{filename} must pass its fixed package identity to tag creation")
        if not {"release", "tag"}.issubset(closeout.get("needs", [])) or closeout.get("environment"):
            errors.append(
                f"{filename} closeout must follow publication and tag creation without publishing credentials"
            )
        checkouts = [
            step for step in closeout.get("steps", []) if str(step.get("uses", "")).startswith("actions/checkout@")
        ]
        if len(checkouts) != 1 or checkouts[0].get("with", {}).get("ref") != "${{ github.sha }}":
            errors.append(f"{filename} closeout must execute trusted workflow source")
        if "scripts.release_closeout" not in str(closeout) or "needs.release.outputs.closeout_digest" not in str(
            closeout
        ):
            errors.append(f"{filename} closeout must verify the transferred artifact digest")
        if str(closeout).count("scripts.verify_github_release") != 2 or "--require-existing" not in str(closeout):
            errors.append(f"{filename} must verify existing and newly created GitHub Release assets")
    workflow = workflows.get(TAG_WORKFLOW, {})
    events = workflow.get("on", workflow.get(True, {}))
    if not isinstance(events, dict) or set(events) != {"workflow_call"}:
        errors.append("Protected tag creation must expose only workflow_call")
    job = workflow.get("jobs", {}).get("tag", {})
    if job.get("environment") != "release-maintenance" or job.get("if") != "github.ref == 'refs/heads/main'":
        errors.append("Protected tag creation must use the main-only release environment")
    checkouts = [step for step in job.get("steps", []) if str(step.get("uses", "")).startswith("actions/checkout@")]
    if len(checkouts) != 1 or checkouts[0].get("with", {}).get("ref") != "${{ github.sha }}":
        errors.append("Protected tag creation must execute trusted workflow source")
    if "scripts.release_tag validate" not in str(job) or "scripts.release_tag create" not in str(job):
        errors.append("Protected tag creation must validate the immutable package identity")
    return errors
