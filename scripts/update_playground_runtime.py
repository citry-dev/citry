"""Update browser package pins from the versions in an immutable Citry release."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 is part of the package test matrix.
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]


try:
    from scripts.verify_playground_release import PlaygroundReleaseError, verify_runtime_pin
except ModuleNotFoundError:
    from verify_playground_release import PlaygroundReleaseError, verify_runtime_pin

PACKAGES = {"citry-core": "citry_core", "citry": "citry", "citry-ui": "citry_ui"}
FIELDS = {"citry-core": "core_version", "citry": "version", "citry-ui": "ui_version"}


def _run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def source_versions(source_ref: str) -> dict[str, str]:
    """Read exact package versions from the selected Citry tag."""
    if not source_ref.startswith("citry@") or str(Version(source_ref[6:])) != source_ref[6:]:
        raise PlaygroundReleaseError("source ref must be a canonical citry@VERSION tag")
    commit = _run("git", "rev-parse", "--verify", f"refs/tags/{source_ref}^{{commit}}")
    versions = {
        name: tomllib.loads(_run("git", "show", f"{commit}:packages/py/{directory}/pyproject.toml"))["project"][
            "version"
        ]
        for name, directory in PACKAGES.items()
    }
    if versions["citry"] != source_ref[6:]:
        raise PlaygroundReleaseError("Citry source version differs from the release tag")
    return versions


def release_inventory(name: str, version: str) -> dict[str, Any]:
    """Read the inventory attached to the published package release."""
    tag = f"{name}@{version}"
    release = json.loads(_run("gh", "release", "view", tag, "--json", "isDraft,tagName"))
    if release["isDraft"] or release["tagName"] != tag:
        raise PlaygroundReleaseError(f"{tag} must be a published GitHub Release")
    with tempfile.TemporaryDirectory() as directory:
        _run("gh", "release", "download", tag, "--pattern", "release-inventory.json", "--dir", directory)
        inventory = json.loads((Path(directory) / "release-inventory.json").read_text())
    if inventory.get("version") != version:
        raise PlaygroundReleaseError(f"{tag} inventory has a different version")
    return inventory


def _download(url: str) -> bytes:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {"pypi.org", "files.pythonhosted.org"}:
        raise PlaygroundReleaseError("package downloads must use HTTPS on PyPI")
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - HTTPS PyPI hosts checked above
        final = urllib.parse.urlsplit(response.url)
        if final.scheme != "https" or final.hostname not in {"pypi.org", "files.pythonhosted.org"}:
            raise PlaygroundReleaseError("package download redirected outside PyPI")
        return response.read()


def public_wheel(name: str, version: str, artifact: dict[str, Any]) -> bytes:
    """Verify the public wheel against the release inventory before using it."""
    metadata = json.loads(_download(f"https://pypi.org/pypi/{name}/{version}/json"))
    matches = [item for item in metadata["urls"] if item["filename"] == artifact["name"]]
    if len(matches) != 1 or matches[0].get("yanked"):
        raise PlaygroundReleaseError(f"{name} has no unique non-yanked public wheel")
    published = matches[0]
    if published["digests"]["sha256"] != artifact["sha256"] or published["size"] != artifact["bytes"]:
        raise PlaygroundReleaseError(f"{name} PyPI metadata differs from the qualified wheel")
    wheel = _download(published["url"])
    if len(wheel) != artifact["bytes"] or hashlib.sha256(wheel).hexdigest() != artifact["sha256"]:
        raise PlaygroundReleaseError(f"{name} public bytes differ from the qualified wheel")
    return wheel


def verify_dependencies(runtime: dict[str, Any], wheels: dict[str, bytes]) -> None:
    """Check wheel identities and requirements against the complete pinned runtime."""
    pins = {canonicalize_name(item["name"]): item["version"] for item in runtime["packages"]}
    python = runtime["pyodide"]["python"]
    environment = default_environment()
    environment.update(
        python_full_version=python,
        python_version=".".join(python.split(".")[:2]),
        implementation_name="cpython",
        implementation_version=python,
        platform_python_implementation="CPython",
        os_name="posix",
        sys_platform="emscripten",
        platform_machine="wasm32",
        platform_system="Emscripten",
        platform_release="",
        platform_version="",
        extra="",
    )
    for name, content in wheels.items():
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            paths = [path for path in archive.namelist() if path.endswith(".dist-info/METADATA")]
            if len(paths) != 1:
                raise PlaygroundReleaseError(f"{name} wheel must have one METADATA file")
            metadata = BytesParser().parsebytes(archive.read(paths[0]))
        if canonicalize_name(metadata["Name"]) != name or metadata["Version"] != pins[name]:
            raise PlaygroundReleaseError(f"{name} wheel metadata differs from its pin")
        if not SpecifierSet(metadata.get("Requires-Python", "")).contains(python, prereleases=True):
            raise PlaygroundReleaseError(f"{name} does not support the pinned Python version")
        for text in metadata.get_all("Requires-Dist", []):
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate(environment):
                continue
            dependency = canonicalize_name(requirement.name)
            if (
                requirement.url
                or requirement.extras
                or dependency not in pins
                or not requirement.specifier.contains(pins[dependency], prereleases=True)
            ):
                raise PlaygroundReleaseError(f"{name} requirement {text!r} is not satisfied by the browser pins")


def update_runtime(runtime: dict[str, Any], versions: dict[str, str]) -> dict[str, Any]:
    """Return verified pins, preserving Pyodide and every unrelated package."""
    result = copy.deepcopy(runtime)
    packages = result["packages"]
    names = [canonicalize_name(item["name"]) for item in packages]
    if len(names) != len(set(names)):
        raise PlaygroundReleaseError("runtime contains duplicate package names")
    wheels = {}
    for name in PACKAGES:
        matches = [item for item in packages if item["name"] == name]
        if len(matches) != 1:
            raise PlaygroundReleaseError(f"runtime must contain one {name} package")
        package = matches[0]
        version = versions[name]
        if result["citry"][FIELDS[name]] != package["version"]:
            raise PlaygroundReleaseError(f"runtime has inconsistent {name} versions")
        if Version(version) < Version(package["version"]):
            raise PlaygroundReleaseError(f"refusing to downgrade {name}")
        _, _, _, expected_tags = parse_wheel_filename(package["filename"])
        inventory = release_inventory(name, version)
        artifacts = []
        for artifact in inventory["artifacts"]:
            if not artifact["name"].endswith(".whl"):
                continue
            distribution, wheel_version, _, tags = parse_wheel_filename(artifact["name"])
            if distribution == name and wheel_version == Version(version) and tags == expected_tags:
                artifacts.append(artifact)
        if len(artifacts) != 1:
            raise PlaygroundReleaseError(f"{name} release must have one wheel matching the current browser ABI")
        artifact = artifacts[0]
        wheels[name] = public_wheel(name, version, artifact)
        package.update(version=version, source="pypi", filename=artifact["name"], sha256=artifact["sha256"])
        result["citry"][FIELDS[name]] = version
        verify_runtime_pin(runtime=result, inventory=inventory, package_name=name, wheel_pattern=artifact["name"])
    verify_dependencies(result, wheels)
    return result


def main() -> int:
    """Write the runtime after verifying all three selected browser packages."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    try:
        original = json.loads(args.runtime.read_text())
        updated = update_runtime(original, source_versions(args.source_ref))
        if updated != original:
            args.runtime.write_text(json.dumps(updated, indent=2) + "\n")
            sys.stdout.write("Updated verified browser runtime pins\n")
        else:
            sys.stdout.write("Browser runtime already matches the verified release\n")
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        sys.stderr.write(f"playground update error: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
