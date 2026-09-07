"""Verify that a playground package pin matches its qualified wheel bytes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

VERSION_FIELDS: Final = {
    "citry-core": "core_version",
    "citry": "version",
    "citry-ui": "ui_version",
}


class PlaygroundReleaseError(ValueError):
    """The committed runtime pin differs from the qualified release."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PlaygroundReleaseError(f"could not read {path}: {error}") from error
    if not isinstance(value, dict):
        raise PlaygroundReleaseError(f"{path} must contain an object")
    return value


def verify_runtime_pin(
    *,
    runtime: Mapping[str, Any],
    inventory: Mapping[str, Any],
    package_name: str,
    wheel_pattern: str,
) -> bool:
    """Return whether this candidate is the runtime pin and verify it when so."""
    packages = runtime.get("packages")
    if not isinstance(packages, list):
        raise PlaygroundReleaseError("playground runtime has no package list")
    matches = [item for item in packages if isinstance(item, dict) and item.get("name") == package_name]
    if len(matches) != 1:
        raise PlaygroundReleaseError(f"playground runtime must contain one {package_name!r} package")
    package = matches[0]
    package_version = package.get("version")
    versions = runtime.get("citry")
    version_field = VERSION_FIELDS.get(package_name)
    if (
        not isinstance(package_version, str)
        or version_field is None
        or not isinstance(versions, dict)
        or versions.get(version_field) != package_version
    ):
        raise PlaygroundReleaseError(f"playground runtime has inconsistent {package_name} versions")

    release_version = inventory.get("version")
    if not isinstance(release_version, str):
        raise PlaygroundReleaseError("release inventory has no version")
    if package_version != release_version:
        return False
    if package.get("source") != "pypi":
        raise PlaygroundReleaseError(f"playground release package {package_name} must use the PyPI source")

    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise PlaygroundReleaseError("release inventory has no artifact list")
    wheels = [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict)
        and isinstance(artifact.get("name"), str)
        and fnmatch.fnmatchcase(artifact["name"], wheel_pattern)
    ]
    if len(wheels) != 1:
        raise PlaygroundReleaseError(
            f"release inventory must contain one {package_name} wheel matching {wheel_pattern!r}"
        )
    wheel = wheels[0]
    if package.get("filename") != wheel.get("name") or package.get("sha256") != wheel.get("sha256"):
        raise PlaygroundReleaseError(f"playground {package_name} filename or SHA-256 differs from the qualified wheel")
    return True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--package-name", choices=sorted(VERSION_FIELDS), required=True)
    parser.add_argument("--wheel-pattern", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check one release inventory against the committed browser runtime."""
    args = _parser().parse_args(argv)
    try:
        pinned = verify_runtime_pin(
            runtime=_load(args.runtime),
            inventory=_load(args.inventory),
            package_name=args.package_name,
            wheel_pattern=args.wheel_pattern,
        )
    except PlaygroundReleaseError as error:
        sys.stderr.write(f"playground release error: {error}\n")
        return 1
    state = "matches the qualified wheel" if pinned else "remains on another compatible version"
    sys.stdout.write(f"playground {args.package_name} {state}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
