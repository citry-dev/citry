"""Verify that a playground package pin matches its qualified wheel bytes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Sequence

VERSION_FIELDS: Final = {
    "citry-core": "core_version",
    "citry": "version",
    "citry-ui": "ui_version",
}
PYPI_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}\Z")
PYODIDE_VERSION_PATTERN: Final = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
PYTHON_VERSION_PATTERN: Final = PYODIDE_VERSION_PATTERN
# Keep this origin in sync with runtime_packages.js. Published direct URLs are
# accepted by origin because Pyodide publishes no registry digest for them.
APPROVED_DIRECT_URL_HOST: Final = "cdn.jsdelivr.net"
REQUIRED_PACKAGES: Final = frozenset(VERSION_FIELDS)


class PlaygroundReleaseError(ValueError):
    """The committed runtime pin differs from the qualified release."""


def _normalized_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


def validate_published_runtime(runtime: Mapping[str, Any]) -> None:
    """Reject incomplete, workspace, or unsafe package coordinates at release boundary."""
    if (
        type(runtime.get("schema_version")) is not int
        or runtime["schema_version"] != 1
        or type(runtime.get("protocol_version")) is not int
        or runtime["protocol_version"] != 1
    ):
        raise PlaygroundReleaseError("published playground runtime must use schema and protocol version 1")
    if runtime.get("source") != "published":
        raise PlaygroundReleaseError("published playground runtime must use source 'published'")

    pyodide = runtime.get("pyodide")
    if not isinstance(pyodide, Mapping):
        raise PlaygroundReleaseError("published playground runtime has no Pyodide configuration")
    pyodide_version = pyodide.get("version")
    if not isinstance(pyodide_version, str) or PYODIDE_VERSION_PATTERN.fullmatch(pyodide_version) is None:
        raise PlaygroundReleaseError("published playground runtime has an invalid Pyodide version")
    python_version = pyodide.get("python")
    if not isinstance(python_version, str) or PYTHON_VERSION_PATTERN.fullmatch(python_version) is None:
        raise PlaygroundReleaseError("published playground runtime has an invalid Python version")
    pyodide_base = f"https://{APPROVED_DIRECT_URL_HOST}/pyodide/v{pyodide_version}/full/"
    if pyodide.get("index_url") != pyodide_base or pyodide.get("module_url") != f"{pyodide_base}pyodide.mjs":
        raise PlaygroundReleaseError("published playground runtime has invalid Pyodide CDN URLs")

    citry = runtime.get("citry")
    if not isinstance(citry, Mapping):
        raise PlaygroundReleaseError("published playground runtime has no Citry version configuration")
    citry_versions: dict[str, str] = {}
    for package_name, field in VERSION_FIELDS.items():
        version = citry.get(field)
        if not isinstance(version, str) or not version:
            raise PlaygroundReleaseError(f"published playground runtime has no Citry {field}")
        citry_versions[package_name] = version

    packages = runtime.get("packages")
    if not isinstance(packages, list):
        raise PlaygroundReleaseError("published playground runtime has no package list")
    names: set[str] = set()
    required_packages: dict[str, Mapping[str, Any]] = {}
    for package in packages:
        if not isinstance(package, Mapping):
            raise PlaygroundReleaseError("published playground runtime contains an invalid package entry")
        raw_name = package.get("name")
        name = raw_name if isinstance(raw_name, str) else "unknown package"
        version = package.get("version")
        if not isinstance(raw_name, str) or not raw_name or not isinstance(version, str) or not version:
            raise PlaygroundReleaseError("published playground runtime contains a package without a name and version")
        normalized_name = _normalized_package_name(raw_name)
        if normalized_name in names:
            raise PlaygroundReleaseError(f"published playground runtime contains duplicate package {raw_name!r}")
        names.add(normalized_name)
        if normalized_name in REQUIRED_PACKAGES:
            required_packages[normalized_name] = package
        source = package.get("source")
        if source == "pypi":
            filename = package.get("filename")
            sha256 = package.get("sha256")
            if (
                not isinstance(filename, str)
                or not filename
                or "/" in filename
                or "\\" in filename
                or "url" in package
                or not isinstance(sha256, str)
                or PYPI_SHA256_PATTERN.fullmatch(sha256) is None
            ):
                raise PlaygroundReleaseError(f"published package {name!r} has an invalid PyPI filename or SHA-256")
            continue
        if source == "url":
            url_value = package.get("url")
            if isinstance(url_value, str):
                url = url_value
                invalid_url = False
            else:
                url = ""
                invalid_url = True
            try:
                parsed = urlsplit(url) if not invalid_url else None
            except ValueError:
                invalid_url = True
                parsed = None
            invalid_port = False
            try:
                port = parsed.port if parsed is not None else None
            except ValueError:
                invalid_port = True
                port = None
            expected_path = f"/pyodide/v{pyodide_version}/full/"
            path = parsed.path if parsed is not None else ""
            direct_filename = path.removeprefix(expected_path)
            if (
                parsed is None
                or invalid_url
                or parsed.scheme != "https"
                or parsed.hostname != APPROVED_DIRECT_URL_HOST
                or parsed.username is not None
                or parsed.password is not None
                or port not in (None, 443)
                or invalid_port
                or "\\" in url
                or "@" in url
                or not parsed.netloc
                or not direct_filename
                or "/" in direct_filename
                or not path.startswith(expected_path)
                or parsed.query
                or parsed.fragment
            ):
                raise PlaygroundReleaseError(
                    f"published package {name!r} must use an approved absolute HTTPS URL without credentials or query"
                )
            continue
        raise PlaygroundReleaseError(f"published package {name!r} has unsupported source {source!r}")

    missing = sorted(REQUIRED_PACKAGES - required_packages.keys())
    if missing:
        raise PlaygroundReleaseError("published playground runtime is missing package(s): " + ", ".join(missing))
    for package_name, package in required_packages.items():
        if package.get("source") != "pypi":
            raise PlaygroundReleaseError(f"published package {package_name!r} must use the PyPI source")
        if package.get("version") != citry_versions[package_name]:
            raise PlaygroundReleaseError(f"published runtime version for {package_name!r} disagrees with citry config")


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
    validate_published_runtime(runtime)
    packages = runtime.get("packages")
    if not isinstance(packages, list):
        raise PlaygroundReleaseError("playground runtime has no package list")
    expected_name = _normalized_package_name(package_name)
    matches = [
        item
        for item in packages
        if isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and _normalized_package_name(item["name"]) == expected_name
    ]
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
