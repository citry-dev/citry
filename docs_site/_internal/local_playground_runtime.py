"""
Build and describe workspace Python wheels for the local docs playground.

The committed ``runtime.json`` pins published wheels. Two local variants
replace some of them with wheels built from this checkout:

- By default only Citry UI comes from the workspace, so docs authors can try
  unreleased UI components against the published Citry.
- When ``CITRY_PLAYGROUND_CORE_WHEEL`` names a Pyodide build of the workspace
  Citry Core, Citry and Citry UI also come from the workspace. The browser
  then runs this checkout's source end to end, which is what the browser tests
  need while Citry changes between releases.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from zipfile import BadZipFile, ZipFile

from packaging.requirements import Requirement
from packaging.version import Version

# A developer points this at a citry-core wheel compiled for the pinned
# Pyodide's Python version and platform (see
# docs_site/static/playground/README.md). Pure-Python packages are cheap to
# build on demand, but the Rust build needs Emscripten (the compiler that
# targets WebAssembly), so it stays a separate, explicitly requested step.
CORE_WHEEL_ENV = "CITRY_PLAYGROUND_CORE_WHEEL"


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


# The Citry distributions a local runtime may build from this checkout.
_WORKSPACE_PACKAGES = frozenset({"citry-core", "citry", "citry-ui"})
# Local wheels are served next to worker.js under this relative path.
_LOCAL_WHEEL_PREFIX = "./local/"


def _normalized_distribution(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def _inspect_wheel(path: Path, *, tag: str = "py3-none-any") -> _Wheel:
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

    # Pyodide installs any wheel it is given, so a native macOS or Linux build
    # would only fail later as a confusing import error inside the Worker.
    if f"Tag: {tag}" not in wheel_metadata.splitlines():
        raise LocalPlaygroundRuntimeError(f"local playground package must be a {tag} wheel: {path.name}")
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


def _local_package(wheel: _Wheel, *, name: str | None = None) -> dict[str, str]:
    return {
        "name": name or wheel.name,
        "version": wheel.version,
        "source": "url",
        "url": f"{_LOCAL_WHEEL_PREFIX}{wheel.path.name}",
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


def playground_core_wheel_from_environment() -> Path | None:
    """Return the workspace Citry Core Pyodide wheel a developer selected, if any."""
    value = os.environ.get(CORE_WHEEL_ENV, "").strip()
    if not value:
        return None
    path = Path(value).expanduser()
    # The variable is an explicit request, so a typo must not quietly fall
    # back to the published runtime and test the wrong Citry.
    if not path.is_file():
        raise LocalPlaygroundRuntimeError(f"{CORE_WHEEL_ENV} does not name a wheel file: {value}")
    return path


def _pyodide_wheel_tag(root: Path) -> str:
    """Read the one wheel tag the pinned Pyodide can load, from the release settings in pyodide-build.json."""
    config_path = root / "packages/py/citry_core/pyodide-build.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return f"{config['python_tag']}-{config['abi_tag']}-{config['platform_tag']}"
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise LocalPlaygroundRuntimeError(
            f"could not read the Pyodide wheel tag from {config_path}: {error}"
        ) from error


def _require_compatible(dependent: _Wheel, dependency: _Wheel) -> None:
    """Reject a pair where one wheel's requirement rejects the other's version, which would fail in the browser."""
    requirement = _requirement_for(dependent, dependency.name)
    if requirement is None or Version(dependency.version) not in requirement.specifier:
        raise LocalPlaygroundRuntimeError(
            f"local {dependent.name} {dependent.version} does not accept {dependency.name} {dependency.version}"
        )


def _replace_packages(packages: list[Any], replacements: list[_Wheel]) -> list[Any]:
    """Swap pinned entries for local wheels, keeping one entry per distribution."""
    by_name = {_normalized_distribution(wheel.name): wheel for wheel in replacements}
    placed: set[str] = set()
    result: list[Any] = []
    for package in packages:
        name = _normalized_distribution(str(package.get("name", ""))) if isinstance(package, dict) else ""
        wheel = by_name.get(name)
        if wheel is None:
            result.append(package)
        elif name not in placed:
            # Keep the pinned position and spelling: the analysis Worker looks
            # up citry-core by its exact committed name, while the wheel's
            # metadata spells it "citry_core".
            result.append(_local_package(wheel, name=str(package["name"])))
            placed.add(name)
    result.extend(_local_package(wheel) for name, wheel in by_name.items() if name not in placed)
    return result


def build_local_playground_runtime(
    *,
    repo_root: Path,
    output_dir: Path,
    core_wheel: Path | None = None,
) -> LocalPlaygroundRuntime:
    """
    Replace pinned browser wheels with wheels built from this checkout.

    Args:
        repo_root: The repository checkout that supplies the workspace packages.
        output_dir: A scratch directory that receives ``runtime.json`` and the
            ``local/`` wheels. The caller serves it and removes it afterwards.
        core_wheel: A Citry Core wheel built from this checkout for the pinned
            Pyodide ABI. Without it, only Citry UI comes from the workspace and
            the published Citry must satisfy its requirement. With it, Citry,
            Citry Core, and Citry UI all come from the workspace.

    Raises:
        LocalPlaygroundRuntimeError: A wheel could not be built or inspected,
            or the chosen wheels do not accept each other's versions.

    """
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
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LocalPlaygroundRuntimeError("the committed playground runtime has no package list")

    if core_wheel is not None:
        # Copy rather than link so the served directory stays valid even if
        # the developer rebuilds the core wheel while the server runs.
        core_copy = wheels_dir / core_wheel.name
        try:
            shutil.copyfile(core_wheel, core_copy)
        except OSError as error:
            raise LocalPlaygroundRuntimeError(f"could not copy {core_wheel}: {error}") from error
        core = _inspect_wheel(core_copy, tag=_pyodide_wheel_tag(root))
        if _normalized_distribution(core.name) != "citry-core":
            raise LocalPlaygroundRuntimeError(f"expected a citry-core wheel, got {core.name}")
        citry = _inspect_wheel(_build_workspace_wheel(root / "packages/py/citry", wheels_dir))
        if _normalized_distribution(citry.name) != "citry":
            raise LocalPlaygroundRuntimeError(f"expected a citry wheel, got {citry.name}")
        _require_compatible(citry, core)
        _require_compatible(citry_ui, citry)
        manifest["packages"] = _replace_packages(packages, [core, citry, citry_ui])
        # The Worker refuses to run unless the installed versions equal these.
        manifest["citry"] = {
            **citry_config,
            "version": citry.version,
            "core_version": core.version,
            "ui_version": citry_ui.version,
        }
    else:
        citry_version = str(citry_config.get("version", ""))
        ui_requirement = _requirement_for(citry_ui, "citry")
        if ui_requirement is None or Version(citry_version) not in ui_requirement.specifier:
            raise LocalPlaygroundRuntimeError(
                f"local Citry UI {citry_ui.version} does not accept the playground's Citry {citry_version}"
            )
        has_citry = any(
            isinstance(package, dict)
            and _normalized_distribution(str(package.get("name", ""))) == "citry"
            and package.get("version") == citry_version
            for package in packages
        )
        if not has_citry:
            raise LocalPlaygroundRuntimeError("the committed playground runtime has no Citry package")
        manifest["packages"] = _replace_packages(packages, [citry_ui])
        manifest["citry"] = {**citry_config, "ui_version": citry_ui.version}

    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "runtime.json"
    # The committed runtime says "published"; the playground's runtime label
    # reads this field, so a page running any workspace wheel must say so.
    manifest["source"] = "workspace"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return load_local_playground_runtime(destination)


def _local_wheel_filename(url: object) -> str | None:
    """Return the wheel file name a ``./local/`` URL names, or ``None`` for any other URL."""
    if not isinstance(url, str) or not url.startswith(_LOCAL_WHEEL_PREFIX):
        return None
    # The server maps this name onto a file in the runtime directory, so only a
    # plain basename is accepted; anything that could leave the directory or be
    # decoded differently by the browser is rejected.
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
    wheel_names: set[str] = set()
    local_versions: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise LocalPlaygroundRuntimeError("local playground runtime contains an invalid package entry")
        filename = _local_wheel_filename(package.get("url"))
        if filename is None:
            continue
        package_name = _normalized_distribution(str(package.get("name", "")))
        # Only Citry's own packages are ever built from the workspace, so any
        # other local entry means the directory was not produced by this module.
        if package_name not in _WORKSPACE_PACKAGES:
            raise LocalPlaygroundRuntimeError(
                f"local playground runtime contains an unexpected local package {package_name!r}"
            )
        # Pyodide would install both copies and the later one would win silently.
        if package_name in local_versions:
            raise LocalPlaygroundRuntimeError(f"local playground runtime contains duplicate {package_name} package")
        if not (root / "local" / filename).is_file():
            raise LocalPlaygroundRuntimeError(f"local wheel is missing: {filename}")
        wheel_names.add(filename)
        package_version = package.get("version")
        local_versions[package_name] = package_version if isinstance(package_version, str) else ""
    # Citry UI is always local. Citry and Citry Core are local only when a
    # workspace core wheel was requested; check whichever the manifest serves.
    expected_versions = {"citry-ui": citry_config.get("ui_version")}
    if "citry" in local_versions:
        expected_versions["citry"] = citry_config.get("version")
    if "citry-core" in local_versions:
        expected_versions["citry-core"] = citry_config.get("core_version")
    if not all(isinstance(version, str) and version for version in expected_versions.values()):
        raise LocalPlaygroundRuntimeError("local playground runtime has incomplete Citry package versions")
    for package_name, expected_version in expected_versions.items():
        if local_versions.get(package_name) != expected_version:
            raise LocalPlaygroundRuntimeError(f"local playground runtime is missing {package_name} {expected_version}")
    return LocalPlaygroundRuntime(
        directory=root,
        manifest_path=manifest_path,
        wheel_names=frozenset(wheel_names),
    )
