# ruff: noqa: T201
"""
Check whether a stable Ruff release changed crates Citry vendors.

The Ruff crates are path dependencies inside a git submodule, so Dependabot
cannot see new upstream releases. This script reads the monitored crate paths
from the root ``Cargo.toml``, fetches Ruff's latest stable release tag, and
reports changes limited to those paths.

Exit codes:
    0: No monitored crate changed.
    10: A stable release changed at least one monitored crate.
    2: The check could not complete.
    3: The checker crashed unexpectedly.

Usage:
    python scripts/ruff_submodule_updates.py check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
RUFF_ROOT = REPO_ROOT / "third_party" / "rust" / "ruff"
CARGO_TOML = REPO_ROOT / "Cargo.toml"
LATEST_RELEASE_URL = "https://api.github.com/repos/astral-sh/ruff/releases/latest"
COMPARE_API_URL = "https://api.github.com/repos/astral-sh/ruff/compare"
COMPARE_URL = "https://github.com/astral-sh/ruff/compare"

_RUFF_PATH_RE = re.compile(r'path\s*=\s*"third_party/rust/ruff/(?P<path>crates/[^"]+)"')


class CheckError(RuntimeError):
    """The upstream check could not produce a trustworthy result."""


PinRelation = Literal["behind", "equal", "ahead"]


def monitored_paths(cargo_toml: Path = CARGO_TOML) -> tuple[str, ...]:
    """Return Ruff crate paths declared by the root Cargo workspace."""
    try:
        cargo_source = cargo_toml.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CheckError(f"could not read {cargo_toml}: {exc}") from exc
    paths = {match.group("path") for match in _RUFF_PATH_RE.finditer(cargo_source)}
    if not paths:
        raise CheckError(f"no Ruff crate paths found in {cargo_toml}")
    return tuple(sorted(paths))


def _fetch_json(url: str, description: str) -> object:
    """Fetch one GitHub API response and decode its JSON body."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "citry-ruff-submodule-check",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)  # noqa: S310 - fixed GitHub API URL
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub API URL
            return json.loads(response.read())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"could not fetch {description}: {exc}") from exc


def fetch_latest_tag() -> str:
    """Return the tag name of Ruff's latest stable GitHub release."""
    payload = _fetch_json(LATEST_RELEASE_URL, "Ruff release data")

    tag = payload.get("tag_name") if isinstance(payload, dict) else None
    if not isinstance(tag, str) or not tag:
        raise CheckError("Ruff's latest release response has no tag_name")
    return tag


def _parse_comparison(payload: object) -> PinRelation:
    """Return how Citry's pin relates to the release."""
    if not isinstance(payload, dict):
        raise CheckError("Ruff comparison response is not an object")

    status = payload.get("status")
    # GitHub describes the head (the release tag) relative to the base (our
    # pin), so its status is the inverse of the pin relation returned here.
    if status == "ahead":
        return "behind"
    if status == "identical":
        return "equal"
    if status == "behind":
        return "ahead"
    if status == "diverged":
        raise CheckError("Citry's Ruff pin and the latest stable release have diverged")
    raise CheckError(f"unknown Ruff comparison status: {status!r}")


def fetch_pin_relation(current_sha: str, tag: str) -> PinRelation:
    """Return how Citry's Ruff pin relates to the latest stable release."""
    base = quote(current_sha, safe="")
    head = quote(tag, safe="")
    payload = _fetch_json(
        f"{COMPARE_API_URL}/{base}...{head}",
        "Ruff comparison data",
    )
    return _parse_comparison(payload)


def _git(*args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise CheckError("git is not installed")
    try:
        result = subprocess.run(
            [executable, "-C", str(RUFF_ROOT), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise CheckError(f"git {' '.join(args)} could not complete: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CheckError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def changed_files(
    tag: str,
    paths: tuple[str, ...],
) -> tuple[str, str, PinRelation, list[str]]:
    """Return the pin, release, their relation, and monitored changes."""
    if not RUFF_ROOT.is_dir():
        raise CheckError(f"Ruff submodule is missing: {RUFF_ROOT}")

    current_sha = _git("rev-parse", "HEAD^{commit}")
    relation = fetch_pin_relation(current_sha, tag)
    if relation == "equal":
        return current_sha, current_sha, relation, []
    if relation == "ahead":
        return current_sha, "", relation, []

    _git("fetch", "--quiet", "--depth=1", "origin", f"refs/tags/{tag}")
    release_sha = _git("rev-parse", "FETCH_HEAD^{commit}")
    output = _git("diff", "--name-only", current_sha, release_sha, "--", *paths)
    files = [line for line in output.splitlines() if line]
    return current_sha, release_sha, relation, files


def format_report(tag: str, current_sha: str, release_sha: str, files: list[str]) -> str:
    """Build the tracking issue body for a relevant Ruff release."""
    shown = files[:100]
    lines = [
        "Ruff's latest stable release changes internal crates used by Citry.",
        "",
        f"- Current submodule commit: `{current_sha}`",
        f"- Latest stable release: `{tag}` (`{release_sha}`)",
        f"- Compare: {COMPARE_URL}/{current_sha}...{tag}",
        "",
        "Changed files in monitored crates:",
        "",
        *[f"- `{path}`" for path in shown],
    ]
    if len(files) > len(shown):
        lines.append(f"- ... and {len(files) - len(shown)} more")
    lines += [
        "",
        "Review the internal API changes, update the submodule and mirrored",
        "workspace dependencies together, then run the full repository gate.",
    ]
    return "\n".join(lines)


def cmd_check() -> int:
    try:
        tag = fetch_latest_tag()
        current_sha, release_sha, relation, files = changed_files(
            tag,
            monitored_paths(),
        )
    except CheckError as exc:
        print(f"error: {exc}")
        return 2
    except Exception:  # noqa: BLE001 - never report a crash as an update
        traceback.print_exc()
        return 3

    if relation == "ahead":
        print(f"In sync: Citry's Ruff pin is newer than stable release {tag}.")
        return 0
    if relation == "equal":
        print(f"In sync: Citry already pins stable release {tag}.")
        return 0
    if not files:
        print(f"In sync: {tag} has no changes in Citry's monitored Ruff crates.")
        return 0

    print(format_report(tag, current_sha, release_sha, files))
    return 10


def main() -> int:
    parser = argparse.ArgumentParser(description="Track stable Ruff changes used by Citry.")
    parser.add_argument("command", choices=["check"])
    parser.parse_args()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
