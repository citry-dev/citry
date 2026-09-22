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
    tags: tuple[str, ...]


_WORKSPACE_PACKAGES = frozenset({"citry-core", "citry", "citry-ui"})
_LOCAL_WHEEL_PREFIX = "./local/"


def _normalized_distribution(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def _inspect_wheel(path: Path, *, python_only: bool = True) -> _Wheel:
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

    tags = tuple(
        line.partition(":")[2].strip()
        for line in wheel_metadata.splitlines()
        if line.startswith("Tag:") and line.partition(":")[2].strip()
    )
    if python_only and "py3-none-any" not in tags:
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
        tags=tags,
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
        "source": "url",
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


def _local_wheel_filename(url: object) -> str | None:
    """Return one safe local wheel basename, or ``None`` for another URL."""
    if not isinstance(url, str) or not url.startswith(_LOCAL_WHEEL_PREFIX):
        return None
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or parsed.path != url:
        raise LocalPlaygroundRuntimeError(f"invalid local wheel URL: {url}")
    filename = url.removeprefix(_LOCAL_WHEEL_PREFIX)
    if (
        not filename
        or "/" in filename
        or "\\" in filename
        or "%" in filename
        or filename in {".", ".."}
        or not filename.endswith(".whl")
    ):
        raise LocalPlaygroundRuntimeError(f"invalid local wheel URL: {url}")
    return filename


def _copy_workspace_core_wheel(core_wheel: Path, output_dir: Path) -> _Wheel:
    """Copy and inspect the one prebuilt PyEmscripten core wheel."""
    source = core_wheel.resolve()
    if not source.is_file():
        raise LocalPlaygroundRuntimeError(f"the workspace citry-core wheel is missing: {source}")
    destination = output_dir / source.name
    try:
        shutil.copy2(source, destination)
    except OSError as error:
        raise LocalPlaygroundRuntimeError(f"could not copy the workspace citry-core wheel: {error}") from error
    return _inspect_wheel(destination, python_only=False)


def build_local_playground_runtime(
    *,
    repo_root: Path,
    output_dir: Path,
    core_wheel: Path,
) -> LocalPlaygroundRuntime:
    """
    Assemble one workspace Citry/Citry Core/Citry UI browser tuple.

    The native core build is intentionally outside this function.  A docs
    server can be recreated many times by a reload, while the PyEmscripten
    build is expensive and must be the exact artifact selected by CI.
    """
    root = repo_root.resolve()
    destination = output_dir.resolve()
    wheels_dir = destination / "local"
    wheels_dir.mkdir(parents=True, exist_ok=True)

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
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LocalPlaygroundRuntimeError("the committed playground runtime has no package list")

    core = _copy_workspace_core_wheel(core_wheel, wheels_dir)
    if _normalized_distribution(core.name) != "citry-core":
        raise LocalPlaygroundRuntimeError(f"expected a citry-core wheel, got {core.name}")
    if not any("pyemscripten" in tag for tag in core.tags):
        raise LocalPlaygroundRuntimeError(f"workspace citry-core must be a PyEmscripten wheel, got {core.path.name}")
    published_core = next(
        (
            package
            for package in packages
            if isinstance(package, dict) and _normalized_distribution(str(package.get("name", ""))) == "citry-core"
        ),
        None,
    )
    expected_core_filename = published_core.get("filename") if isinstance(published_core, dict) else None
    if isinstance(expected_core_filename, str) and core.path.name != expected_core_filename:
        raise LocalPlaygroundRuntimeError(
            f"workspace citry-core wheel {core.path.name} does not match the pinned Pyodide ABI "
            f"{expected_core_filename}"
        )

    citry = _inspect_wheel(_build_workspace_wheel(root / "packages/py/citry", wheels_dir))
    if _normalized_distribution(citry.name) != "citry":
        raise LocalPlaygroundRuntimeError(f"expected a citry wheel, got {citry.name}")
    citry_ui = _inspect_wheel(_build_workspace_wheel(root / "packages/py/citry_ui", wheels_dir))
    if _normalized_distribution(citry_ui.name) != "citry-ui":
        raise LocalPlaygroundRuntimeError(f"expected a citry-ui wheel, got {citry_ui.name}")

    citry_version = citry.version
    core_version = core.version
    ui_version = citry_ui.version
    if citry_version != citry_config.get("version"):
        raise LocalPlaygroundRuntimeError(
            f"workspace Citry {citry_version} does not match the runtime's Citry {citry_config.get('version')}"
        )
    if core_version != citry_config.get("core_version"):
        raise LocalPlaygroundRuntimeError(
            f"workspace Citry Core {core_version} does not match the runtime's Citry Core "
            f"{citry_config.get('core_version')}"
        )
    ui_requirement = _requirement_for(citry_ui, "citry")
    if ui_requirement is None or Version(citry_version) not in ui_requirement.specifier:
        raise LocalPlaygroundRuntimeError(
            f"local Citry UI {citry_ui.version} does not accept the playground's Citry {citry_version}"
        )
    core_requirement = _requirement_for(citry, "citry-core")
    if core_requirement is None or Version(core_version) not in core_requirement.specifier:
        raise LocalPlaygroundRuntimeError(
            f"workspace Citry {citry_version} does not accept workspace Citry Core {core_version}"
        )

    replacements = {
        "citry-core": _local_package(core),
        "citry": _local_package(citry),
        "citry-ui": _local_package(citry_ui),
    }
    seen: set[str] = set()
    next_packages: list[Any] = []
    for package in packages:
        if not isinstance(package, dict):
            next_packages.append(package)
            continue
        package_name = _normalized_distribution(str(package.get("name", "")))
        replacement = replacements.get(package_name)
        if replacement is None:
            next_packages.append(package)
        else:
            next_packages.append(replacement)
            seen.add(package_name)
    missing = sorted(set(replacements) - seen)
    if missing:
        raise LocalPlaygroundRuntimeError(
            "the committed playground runtime is missing package entries: " + ", ".join(missing)
        )
    manifest["source"] = "workspace"
    manifest["packages"] = next_packages
    manifest["citry"] = {
        **citry_config,
        "version": citry_version,
        "core_version": core_version,
        "ui_version": ui_version,
    }

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
    if manifest.get("source") != "workspace":
        raise LocalPlaygroundRuntimeError("local playground runtime must identify itself as a workspace tuple")
    expected_versions = {
        "citry-core": citry_config.get("core_version"),
        "citry": citry_config.get("version"),
        "citry-ui": citry_config.get("ui_version"),
    }
    if not all(isinstance(version, str) and version for version in expected_versions.values()):
        raise LocalPlaygroundRuntimeError("local playground runtime has incomplete Citry package versions")
    wheel_names: set[str] = set()
    local_versions: dict[str, str] = {}
    local_package_names: set[str] = set()
    for package in packages:
        if not isinstance(package, dict):
            raise LocalPlaygroundRuntimeError("local playground runtime contains an invalid package entry")
        package_name = _normalized_distribution(str(package.get("name", "")))
        filename = _local_wheel_filename(package.get("url"))
        if filename is None:
            if package_name in expected_versions:
                raise LocalPlaygroundRuntimeError(
                    f"local playground runtime package {package_name} must use one local wheel URL"
                )
            continue
        if package_name not in expected_versions:
            raise LocalPlaygroundRuntimeError(
                f"local playground runtime contains an unexpected local package {package_name!r}"
            )
        if package_name in local_package_names:
            raise LocalPlaygroundRuntimeError(f"local playground runtime contains duplicate {package_name} package")
        local_package_names.add(package_name)
        if not (root / "local" / filename).is_file():
            raise LocalPlaygroundRuntimeError(f"local wheel is missing: {filename}")
        wheel_names.add(filename)
        package_version = package.get("version")
        if package_name in expected_versions and isinstance(package_version, str):
            local_versions[package_name] = package_version
    missing_names = sorted(_WORKSPACE_PACKAGES - local_package_names)
    if missing_names:
        missing_name = missing_names[0]
        raise LocalPlaygroundRuntimeError(
            f"local playground runtime is missing {missing_name} {expected_versions[missing_name]}"
        )
    if len(wheel_names) != len(_WORKSPACE_PACKAGES):
        raise LocalPlaygroundRuntimeError("local playground runtime must reference three distinct local wheels")
    for package_name, expected_version in expected_versions.items():
        if local_versions.get(package_name) != expected_version:
            raise LocalPlaygroundRuntimeError(f"local playground runtime is missing {package_name} {expected_version}")
    return LocalPlaygroundRuntime(
        directory=root,
        manifest_path=manifest_path,
        wheel_names=frozenset(wheel_names),
    )
