"""Build and describe workspace Python wheels for the local docs playground."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from email.parser import BytesParser
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit
from zipfile import BadZipFile, ZipFile

from packaging.requirements import Requirement
from packaging.version import Version

if TYPE_CHECKING:
    from pathlib import Path


class LocalPlaygroundRuntimeError(RuntimeError):
    """The local browser runtime could not be assembled safely."""


@dataclass(frozen=True)
class LocalPlaygroundRuntime:
    """Generated files served in place of the committed playground runtime."""

    directory: Path
    manifest_path: Path
    wheel_names: frozenset[str]


@dataclass(frozen=True)
class _Wheel:
    path: Path
    name: str
    version: str
    requirements: tuple[str, ...]


def _normalized_distribution(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def _inspect_wheel(path: Path) -> _Wheel:
    try:
        with ZipFile(path) as archive:
            metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            wheel_names = [name for name in archive.namelist() if name.endswith(".dist-info/WHEEL")]
            if len(metadata_names) != 1 or len(wheel_names) != 1:
                raise LocalPlaygroundRuntimeError(f"wheel has an invalid metadata layout: {path.name}")
            metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
            wheel_metadata = archive.read(wheel_names[0]).decode("utf-8")
    except (BadZipFile, OSError, UnicodeDecodeError) as error:
        raise LocalPlaygroundRuntimeError(f"could not inspect local wheel {path.name}: {error}") from error

    if "Tag: py3-none-any" not in wheel_metadata.splitlines():
        raise LocalPlaygroundRuntimeError(f"local playground package must be a py3-none-any wheel: {path.name}")
    name = metadata.get("Name")
    version = metadata.get("Version")
    if not name or not version:
        raise LocalPlaygroundRuntimeError(f"wheel metadata is missing Name or Version: {path.name}")
    return _Wheel(
        path=path,
        name=name,
        version=version,
        requirements=tuple(metadata.get_all("Requires-Dist", [])),
    )


def _build_workspace_wheel(package_dir: Path, output_dir: Path) -> Path:
    source_dir = output_dir.parent / "build-sources" / package_dir.name
    try:
        shutil.copytree(
            package_dir,
            source_dir,
            symlinks=False,
            ignore=shutil.ignore_patterns(
                "build",
                "dist",
                "*.egg-info",
                "__pycache__",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
            ),
        )
    except OSError as error:
        raise LocalPlaygroundRuntimeError(f"could not prepare {package_dir.name} for building: {error}") from error

    before = set(output_dir.glob("*.whl"))
    uv = shutil.which("uv")
    if uv is None:
        raise LocalPlaygroundRuntimeError("uv is required to build the local playground packages")
    try:
        subprocess.run(
            [uv, "build", "--wheel", str(source_dir), "--out-dir", str(output_dir)],
            cwd=package_dir.parents[2],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise LocalPlaygroundRuntimeError("uv is required to build the local playground packages") from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or "uv build failed").strip()
        raise LocalPlaygroundRuntimeError(f"could not build {package_dir.name}: {details}") from error
    built = set(output_dir.glob("*.whl")) - before
    if len(built) != 1:
        names = ", ".join(sorted(path.name for path in built)) or "none"
        raise LocalPlaygroundRuntimeError(f"expected one wheel for {package_dir.name}, found {names}")
    return built.pop()


def _requirement_for(wheel: _Wheel, distribution: str) -> Requirement | None:
    expected = _normalized_distribution(distribution)
    for raw in wheel.requirements:
        requirement = Requirement(raw)
        if _normalized_distribution(requirement.name) == expected:
            return requirement
    return None


def _local_package(wheel: _Wheel) -> dict[str, str]:
    return {
        "name": wheel.name,
        "version": wheel.version,
        "url": f"./local/{wheel.path.name}",
    }


def _validate_manifest_versions(manifest: Any, *, label: str) -> dict[str, Any]:
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
    ):
        raise LocalPlaygroundRuntimeError(f"{label} must use schema version 1")
    if type(manifest.get("protocol_version")) is not int or manifest["protocol_version"] != 1:
        raise LocalPlaygroundRuntimeError(f"{label} must use protocol version 1")
    return manifest


def build_local_playground_runtime(*, repo_root: Path, output_dir: Path) -> LocalPlaygroundRuntime:
    """Add the workspace Citry UI wheel to the pinned browser runtime."""
    root = repo_root.resolve()
    destination = output_dir.resolve()
    wheels_dir = destination / "local"
    wheels_dir.mkdir(parents=True, exist_ok=True)

    citry_ui = _inspect_wheel(_build_workspace_wheel(root / "packages/py/citry_ui", wheels_dir))
    if _normalized_distribution(citry_ui.name) != "citry-ui":
        raise LocalPlaygroundRuntimeError(f"expected a citry-ui wheel, got {citry_ui.name}")

    runtime_source = root / "docs_site/static/playground/runtime.json"
    try:
        manifest = _validate_manifest_versions(
            json.loads(runtime_source.read_text(encoding="utf-8")),
            label="the committed playground runtime",
        )
    except (OSError, ValueError) as error:
        raise LocalPlaygroundRuntimeError(f"could not read {runtime_source}: {error}") from error
    citry_config = manifest.get("citry")
    if not isinstance(citry_config, dict):
        raise LocalPlaygroundRuntimeError("the committed playground runtime has no Citry version configuration")
    citry_version = str(citry_config.get("version", ""))
    ui_requirement = _requirement_for(citry_ui, "citry")
    if ui_requirement is None or Version(citry_version) not in ui_requirement.specifier:
        raise LocalPlaygroundRuntimeError(
            f"local Citry UI {citry_ui.version} does not accept the playground's Citry {citry_version}"
        )

    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LocalPlaygroundRuntimeError("the committed playground runtime has no package list")
    has_citry = any(
        isinstance(package, dict)
        and _normalized_distribution(str(package.get("name", ""))) == "citry"
        and package.get("version") == citry_version
        for package in packages
    )
    if not has_citry:
        raise LocalPlaygroundRuntimeError("the committed playground runtime has no Citry package")
    next_packages = [
        package
        for package in packages
        if not isinstance(package, dict) or _normalized_distribution(str(package.get("name", ""))) != "citry-ui"
    ]
    next_packages.append(_local_package(citry_ui))
    manifest["packages"] = next_packages
    manifest["citry"] = {**citry_config, "ui_version": citry_ui.version}

    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "runtime.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return load_local_playground_runtime(destination)


def load_local_playground_runtime(directory: Path) -> LocalPlaygroundRuntime:
    """Validate and load a generated local runtime directory."""
    root = directory.resolve()
    manifest_path = root / "runtime.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LocalPlaygroundRuntimeError(f"could not load local playground runtime: {error}") from error
    manifest = _validate_manifest_versions(manifest, label="local playground runtime")
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LocalPlaygroundRuntimeError("local playground runtime has no package list")
    citry_config = manifest.get("citry")
    if not isinstance(citry_config, dict):
        raise LocalPlaygroundRuntimeError("local playground runtime has no Citry version configuration")
    expected_versions = {"citry-ui": citry_config.get("ui_version")}
    if not all(isinstance(version, str) and version for version in expected_versions.values()):
        raise LocalPlaygroundRuntimeError("local playground runtime has incomplete Citry package versions")
    wheel_names: set[str] = set()
    local_versions: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict) or not isinstance(package.get("url"), str):
            continue
        path = urlsplit(package["url"]).path
        prefix = "./local/"
        if not path.startswith(prefix):
            continue
        filename = path.removeprefix(prefix)
        if not filename or "/" in filename or not filename.endswith(".whl"):
            raise LocalPlaygroundRuntimeError(f"invalid local wheel URL: {package['url']}")
        if not (root / "local" / filename).is_file():
            raise LocalPlaygroundRuntimeError(f"local wheel is missing: {filename}")
        wheel_names.add(filename)
        package_name = _normalized_distribution(str(package.get("name", "")))
        package_version = package.get("version")
        if package_name in expected_versions and isinstance(package_version, str):
            local_versions[package_name] = package_version
    for package_name, expected_version in expected_versions.items():
        if local_versions.get(package_name) != expected_version:
            raise LocalPlaygroundRuntimeError(f"local playground runtime is missing {package_name} {expected_version}")
    return LocalPlaygroundRuntime(
        directory=root,
        manifest_path=manifest_path,
        wheel_names=frozenset(wheel_names),
    )
