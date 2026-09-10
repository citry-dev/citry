"""Create an immutable package tag after its publication job succeeds."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from scripts.release import FULL_SHA, PACKAGE_BY_KEY, tomllib


class ReleaseTagError(RuntimeError):
    """The package tag cannot be created safely."""


def _git(repo: Path, *args: str, authenticated: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if authenticated:
        token = env.get("RELEASE_APP_TOKEN", "")
        if not token:
            raise ReleaseTagError("RELEASE_APP_TOKEN is missing")
        # Keep the credential out of command arguments and repository configuration.
        authorization = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
            GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {authorization}",
        )
    return subprocess.run(
        [shutil.which("git") or "/usr/bin/git", *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _required(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode:
        raise ReleaseTagError(f"git {args[0]} failed")
    return result.stdout.strip()


def _validate_tag_object(repo: Path, ref: str, tag: str, commit: str) -> None:
    if _required(repo, "cat-file", "-t", ref) != "tag":
        raise ReleaseTagError("The existing release tag is not annotated")
    if _required(repo, "rev-parse", f"{ref}^{{commit}}") != commit:
        raise ReleaseTagError("The existing release tag names a different commit")
    # Ref aliases and nested tags must not disguise a different release identity.
    headers = _required(repo, "cat-file", "-p", ref).split("\n\n", maxsplit=1)[0].splitlines()
    if headers[:3] != [f"object {commit}", "type commit", f"tag {tag}"]:
        raise ReleaseTagError("The annotated tag has a different internal identity")


def _remote_tag(repo: Path, tag: str, commit: str) -> bool:
    result = _git(repo, "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}")
    if result.returncode == 2:
        return False
    if result.returncode:
        raise ReleaseTagError("Could not query the remote tag")
    # Fetch the exact remote object, independent of any existing local tag.
    _required(repo, "fetch", "--no-tags", "origin", f"refs/tags/{tag}")
    _validate_tag_object(repo, "FETCH_HEAD", tag, commit)
    return True


def validate(repo: Path, package: str, commit: str, tag: str) -> bool:
    """Validate the release identity and return whether its remote tag exists."""
    if FULL_SHA.fullmatch(commit) is None:
        raise ReleaseTagError("The release commit must be a full lowercase Git SHA")
    spec = PACKAGE_BY_KEY.get(package)
    if spec is None:
        raise ReleaseTagError("Unknown release package")
    # Historical source is data; privileged jobs execute only trusted main code.
    _required(repo, "fetch", "--no-tags", "origin", "main:refs/remotes/origin/main")
    if _required(repo, "cat-file", "-t", commit) != "commit":
        raise ReleaseTagError("The release SHA must name a commit object")
    _required(repo, "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main")
    raw = _required(repo, "show", f"{commit}:{spec.manifest}")
    try:
        manifest = json.loads(raw) if spec.manifest_kind == "json" else tomllib.loads(raw)
        project = manifest if spec.manifest_kind == "json" else manifest["project"]
        version = project["version"]
    except (ValueError, KeyError, TypeError) as error:
        raise ReleaseTagError("The release manifest has no valid version") from error
    if (
        not isinstance(version, str)
        or re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:[a-zA-Z0-9.+-]*)?", version) is None
    ):
        raise ReleaseTagError("The release manifest version is invalid")
    if tag != f"{spec.tag_prefix}{version}":
        raise ReleaseTagError("The requested tag does not match the source package version")
    _required(repo, "check-ref-format", f"refs/tags/{tag}")
    return _remote_tag(repo, tag, commit)


def create(repo: Path, package: str, commit: str, tag: str) -> None:
    """Create the validated annotated tag, accepting an identical concurrent creation."""
    if validate(repo, package, commit, tag):
        return
    local = _git(repo, "rev-parse", "--verify", f"refs/tags/{tag}")
    if local.returncode == 0:
        _validate_tag_object(repo, f"refs/tags/{tag}", tag, commit)
    else:
        _required(
            repo,
            "-c",
            "user.name=citry-release[bot]",
            "-c",
            "user.email=citry-release[bot]@users.noreply.github.com",
            "tag",
            "-a",
            tag,
            commit,
            "-m",
            f"Release {tag}",
        )
    pushed = _git(repo, "push", "origin", f"refs/tags/{tag}:refs/tags/{tag}", authenticated=True)
    # A concurrent successful publisher is safe only when its tag also agrees.
    exists = _remote_tag(repo, tag, commit)
    if pushed.returncode and not exists:
        raise ReleaseTagError("The release tag push failed")
    if not exists:
        raise ReleaseTagError("The pushed release tag is missing")


def main() -> None:
    """Validate or create the package tag requested by the trusted workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("validate", "create"))
    parser.add_argument("--package", required=True)
    parser.add_argument("--release-commit", required=True)
    parser.add_argument("--release-tag", required=True)
    args = parser.parse_args()
    try:
        operation = create if args.operation == "create" else validate
        operation(Path.cwd(), args.package, args.release_commit, args.release_tag)
    except ReleaseTagError as error:
        parser.exit(1, f"Release tag rejected: {error}\n")


if __name__ == "__main__":
    main()
