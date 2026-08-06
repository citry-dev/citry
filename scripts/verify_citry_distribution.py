"""Build and verify the citry wheel and source distribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "py" / "citry"
SOURCE_ROOT: Final = PACKAGE_ROOT / "citry"


class DistributionVerificationError(RuntimeError):
    """A built distribution differs from the checked source or cannot run."""


def sha256_bytes(value: bytes) -> str:
    """Return one lowercase SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def source_inventory(root: Path = SOURCE_ROOT) -> dict[str, str]:
    """Hash every source file that belongs inside the installed package."""
    inventory: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        inventory[path.relative_to(root).as_posix()] = sha256_bytes(path.read_bytes())
    return inventory


def wheel_inventory(path: Path) -> dict[str, str]:
    """Hash every regular member of a wheel and reject duplicate names."""
    with zipfile.ZipFile(path) as archive:
        names = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
        if len(names) != len(set(names)):
            raise DistributionVerificationError(f"{path.name} contains duplicate member names")
        return {name: sha256_bytes(archive.read(name)) for name in sorted(names)}


def sdist_inventory(path: Path) -> dict[str, str]:
    """Hash every regular member of a gzipped source distribution."""
    inventory: dict[str, str] = {}
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            if member.name in inventory:
                raise DistributionVerificationError(f"{path.name} contains duplicate member {member.name!r}")
            file = archive.extractfile(member)
            if file is None:
                raise DistributionVerificationError(f"cannot read {member.name!r} from {path.name}")
            inventory[member.name] = sha256_bytes(file.read())
    return dict(sorted(inventory.items()))


def package_payload(inventory: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Return installed-package paths below one archive prefix."""
    normalized = prefix.rstrip("/") + "/"
    return {name.removeprefix(normalized): digest for name, digest in inventory.items() if name.startswith(normalized)}


def inventory_fingerprint(inventory: Mapping[str, str]) -> str:
    """Hash a stable path-to-content inventory."""
    encoded = json.dumps(dict(sorted(inventory.items())), separators=(",", ":"), sort_keys=True).encode()
    return sha256_bytes(encoded)


def require_equal(label: str, expected: Mapping[str, str], actual: Mapping[str, str]) -> None:
    """Raise with a bounded path diff when two inventories differ."""
    if expected == actual:
        return
    names = sorted(set(expected) | set(actual))
    differences = [name for name in names if expected.get(name) != actual.get(name)]
    shown = ", ".join(differences[:20])
    suffix = "" if len(differences) <= 20 else f" and {len(differences) - 20} more"
    raise DistributionVerificationError(f"{label} differs at {shown}{suffix}")


def verify_artifacts(source_wheel: Path, sdist: Path, rebuilt_wheel: Path) -> dict[str, Any]:
    """Compare checkout, wheel, sdist, and rebuilt-wheel content."""
    source_files = source_inventory()
    source_wheel_files = wheel_inventory(source_wheel)
    rebuilt_wheel_files = wheel_inventory(rebuilt_wheel)
    sdist_files = sdist_inventory(sdist)

    require_equal(
        "source and source-built wheel package payload",
        source_files,
        package_payload(source_wheel_files, "citry"),
    )
    require_equal("source-built and sdist-built wheels", source_wheel_files, rebuilt_wheel_files)

    roots = {name.split("/", 1)[0] for name in sdist_files}
    if len(roots) != 1:
        raise DistributionVerificationError(f"{sdist.name} must contain exactly one top-level directory")
    sdist_root = roots.pop()
    require_equal(
        "source and sdist package payload",
        source_files,
        package_payload(sdist_files, f"{sdist_root}/citry"),
    )

    return {
        "sourceWheel": _artifact_report(source_wheel, source_wheel_files),
        "sdist": _artifact_report(sdist, sdist_files),
        "sdistWheel": _artifact_report(rebuilt_wheel, rebuilt_wheel_files),
        "installedPayload": {
            "files": len(source_files),
            "sha256": inventory_fingerprint(source_files),
        },
    }


def _artifact_report(path: Path, inventory: Mapping[str, str]) -> dict[str, Any]:
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "archiveSha256": sha256_bytes(path.read_bytes()),
        "files": len(inventory),
        "contentSha256": inventory_fingerprint(inventory),
    }


def _run(command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        output = (completed.stdout + completed.stderr).strip()
        raise DistributionVerificationError(f"command failed ({' '.join(command)}):\n{output}")
    return completed.stdout


def _unique(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise DistributionVerificationError(f"expected one {pattern!r} in {directory}, found {len(matches)}")
    return matches[0]


def _build_checkout_distribution(directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    _run(
        ["uv", "build", "--package", "citry", "--out-dir", str(directory), "--clear", "--no-build-logs"],
        cwd=REPO_ROOT,
    )
    return _unique(directory, "*.whl"), _unique(directory, "*.tar.gz")


def _build_sdist_wheel(sdist: Path, directory: Path, *, cwd: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "uv",
            "build",
            str(sdist),
            "--wheel",
            "--out-dir",
            str(directory),
            "--clear",
            "--no-config",
            "--no-build-logs",
        ],
        cwd=cwd,
    )
    return _unique(directory, "*.whl")


_SMOKE = r"""
import importlib.resources
import importlib.util
import shutil

assert shutil.which("node") is None
assert importlib.util.find_spec("jsonschema") is None

import citry
from citry._protocol import client_graph, events

descriptor = events.build_descriptor("Page_1", {})
instance = events.build_component_instance("page_1", "Page_1", None, {})
events_manifest = events.build_manifest(None, [descriptor], [instance])
assert events.validate_manifest(events_manifest) is None

component_class = client_graph.build_component_class("Page_1", "Page")
component_instance = client_graph.build_component_instance(
    instance_id=1,
    render_id="page_1",
    class_id="Page_1",
    invocation_id=None,
    parent_render_id=None,
    transparent=False,
)
graph = client_graph.build_graph(
    graph_id=0,
    component_classes=[component_class],
    component_instances=[component_instance],
    source_locations=[],
    nested_components=[],
    component_execution_order_constraints=[],
    fills=[],
    slot_regions=[],
)
graph_manifest = client_graph.build_manifest("production", [graph])
assert client_graph.validate_manifest(graph_manifest) is None

root = importlib.resources.files("citry")
assert root.joinpath("ext/dependencies/client/citry.js").is_file()
assert root.joinpath("ext/events/client/citry-events.js").is_file()
assert root.joinpath("py.typed").is_file()
print(citry.__file__)
"""


def _smoke_install(wheel: Path, directory: Path, *, core_wheel: Path | None) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    venv = directory / "venv"
    _run(["uv", "venv", str(venv), "--python", sys.executable], cwd=directory)
    executable = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    cli = venv / ("Scripts/citry.exe" if os.name == "nt" else "bin/citry")
    if core_wheel is not None:
        _run(["uv", "pip", "install", "--python", str(executable), str(core_wheel)], cwd=directory)
    _run(["uv", "pip", "install", "--python", str(executable), str(wheel)], cwd=directory)
    smoke_env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        smoke_env.pop(name, None)
    bin_dir = executable.parent
    system_path = os.pathsep.join((str(bin_dir), "/usr/bin", "/bin"))
    smoke_env["PATH"] = system_path
    imported_from = _run([str(executable), "-I", "-c", _SMOKE], cwd=directory, env=smoke_env).strip()
    _run([str(cli), "--help"], cwd=directory, env=smoke_env)
    return {
        "wheel": wheel.name,
        "python": str(executable),
        "importedFrom": imported_from,
        "coreSource": "companion wheel" if core_wheel is not None else "package index",
        "nodeAvailable": False,
        "jsonschemaInstalled": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the complete distribution proof and print one JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dist-dir",
        type=Path,
        help="Use one existing directory containing exactly one wheel and one sdist.",
    )
    parser.add_argument(
        "--core-wheel",
        type=Path,
        help="Install this pre-release citry-core wheel before each citry wheel.",
    )
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="citry-distribution-") as temporary:
            workspace = Path(temporary).resolve()
            if args.dist_dir is None:
                source_wheel, sdist = _build_checkout_distribution(workspace / "dist")
            else:
                dist = args.dist_dir.resolve()
                source_wheel = _unique(dist, "*.whl")
                sdist = _unique(dist, "*.tar.gz")
            rebuilt_wheel = _build_sdist_wheel(sdist, workspace / "rebuilt", cwd=workspace)
            report = verify_artifacts(source_wheel, sdist, rebuilt_wheel)
            core_wheel = args.core_wheel.resolve() if args.core_wheel is not None else None
            if core_wheel is not None and not core_wheel.is_file():
                raise DistributionVerificationError(f"companion core wheel does not exist: {core_wheel}")
            report["smoke"] = [
                _smoke_install(source_wheel, workspace / "smoke-source", core_wheel=core_wheel),
                _smoke_install(rebuilt_wheel, workspace / "smoke-sdist", core_wheel=core_wheel),
            ]
    except DistributionVerificationError as error:
        sys.stderr.write(f"citry distribution verification failed: {error}\n")
        return 1
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
