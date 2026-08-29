"""Build, inspect, install, and promote the citry-lsp release pair."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final

_tomllib: Any
try:
    import tomllib as _stdlib_tomllib
except ModuleNotFoundError:  # Python 3.10 qualification runner
    _tomllib = None
else:
    _tomllib = _stdlib_tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from email.message import Message

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "py" / "citry_lsp"
SOURCE_ROOT: Final = PACKAGE_ROOT / "citry_lsp"
MAX_WHEEL_BYTES: Final = 512 * 1024
MAX_SDIST_BYTES: Final = 1024 * 1024
EXPECTED_REQUIRES_DIST: Final = {
    "citry<0.5,>=0.4.1",
    "pygls==2.1.1",
    "python-dotenv<2,>=1.2.3",
    "ty==0.0.73",
}


class DistributionVerificationError(RuntimeError):
    """A built distribution differs from the checked source or cannot run."""


def sha256_bytes(value: bytes) -> str:
    """Return one lowercase SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def record_sha256(value: bytes) -> str:
    """Return the URL-safe SHA-256 form used by wheel RECORD files."""
    return base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode("ascii")


def package_version() -> str:
    """Read the package version from the release manifest."""
    content = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if _tomllib is not None:
        version: Any = _tomllib.loads(content)["project"].get("version")
    else:
        project = re.search(r"(?ms)^\[project\][ \t]*\n(?P<body>.*?)(?=^\[|\Z)", content)
        version_line = (
            None
            if project is None
            else re.search(
                r"""(?m)^version\s*=\s*["'](?P<version>[^"']+)["']\s*(?:#.*)?$""",
                project.group("body"),
            )
        )
        version = None if version_line is None else version_line.group("version")
    if not isinstance(version, str) or not version:
        raise DistributionVerificationError("citry-lsp has no project version")
    return version


def expected_release_filenames(version: str) -> set[str]:
    """Return the complete, closed citry-lsp release set."""
    return {
        f"citry_lsp-{version}-py3-none-any.whl",
        f"citry_lsp-{version}.tar.gz",
    }


def _safe_archive_name(name: str, *, artifact: Path) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise DistributionVerificationError(f"{artifact.name} contains unsafe member {name!r}")
    return path


def _parse_metadata(payload: bytes, *, artifact: Path) -> Message:
    try:
        return BytesParser().parsebytes(payload)
    except Exception as error:
        raise DistributionVerificationError(f"cannot parse metadata in {artifact.name}: {error}") from error


def _require_metadata(metadata: Message, *, artifact: Path, version: str) -> None:
    if metadata.get("Name", "").lower().replace("_", "-") != "citry-lsp":
        raise DistributionVerificationError(f"{artifact.name} has unexpected Name metadata")
    if metadata.get("Version") != version:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Version metadata")
    if metadata.get("Requires-Python") not in {">=3.10, <4.0", "<4.0,>=3.10"}:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Requires-Python metadata")
    if set(metadata.get_all("Requires-Dist", [])) != EXPECTED_REQUIRES_DIST:  # type: ignore[attr-defined]
        raise DistributionVerificationError(f"{artifact.name} has unexpected runtime dependencies")
    if metadata.get_all("Provides-Extra", []):  # type: ignore[attr-defined]
        raise DistributionVerificationError(f"{artifact.name} has unexpected optional extras")


def source_inventory(root: Path = SOURCE_ROOT) -> dict[str, str]:
    """Hash every source file that belongs inside the installed package."""
    inventory: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
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


def verify_wheel(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the wheel filename, metadata, RECORD, and closed member set."""
    expected_name = f"citry_lsp-{version}-py3-none-any.whl"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected wheel {expected_name!r}, found {path.name!r}")
    if path.stat().st_size > MAX_WHEEL_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {path.stat().st_size} bytes; the release cap is {MAX_WHEEL_BYTES} bytes"
        )
    dist_info = f"citry_lsp-{version}.dist-info/"
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise DistributionVerificationError(f"{path.name} has a corrupt member {bad_member!r}")
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            names = [entry.filename for entry in entries]
            for entry in entries:
                _safe_archive_name(entry.filename, artifact=path)
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise DistributionVerificationError(f"{path.name} contains a symbolic link")
            if len(names) != len(set(names)):
                raise DistributionVerificationError(f"{path.name} contains duplicate member names")

            controls = {
                f"{dist_info}METADATA",
                f"{dist_info}WHEEL",
                f"{dist_info}RECORD",
                f"{dist_info}entry_points.txt",
                f"{dist_info}top_level.txt",
                f"{dist_info}licenses/LICENSE",
            }
            expected_members = {f"citry_lsp/{name}" for name in source_inventory()} | controls
            missing = sorted(expected_members - set(names))
            unexpected = sorted(set(names) - expected_members)
            if missing or unexpected:
                raise DistributionVerificationError(
                    f"{path.name} member inventory mismatch; missing={missing!r}; unexpected={unexpected!r}"
                )

            metadata = _parse_metadata(archive.read(f"{dist_info}METADATA"), artifact=path)
            _require_metadata(metadata, artifact=path, version=version)
            wheel_metadata = _parse_metadata(archive.read(f"{dist_info}WHEEL"), artifact=path)
            if wheel_metadata.get("Root-Is-Purelib") != "true" or set(wheel_metadata.get_all("Tag", [])) != {
                "py3-none-any"
            }:
                raise DistributionVerificationError(f"{path.name} has unexpected WHEEL compatibility metadata")
            if archive.read(f"{dist_info}entry_points.txt") != (
                b"[console_scripts]\ncitry-lsp = citry_lsp.__main__:main\n"
            ):
                raise DistributionVerificationError(f"{path.name} has an unexpected console entry point")
            if archive.read(f"{dist_info}top_level.txt") != b"citry_lsp\n":
                raise DistributionVerificationError(f"{path.name} has an unexpected top-level package")
            if archive.read(f"{dist_info}licenses/LICENSE") != (PACKAGE_ROOT / "LICENSE").read_bytes():
                raise DistributionVerificationError(f"{path.name} does not contain the checked MIT license")

            actual_payload = {
                name.removeprefix("citry_lsp/"): sha256_bytes(archive.read(name))
                for name in names
                if name.startswith("citry_lsp/")
            }
            require_equal("checkout and wheel package payload", source_inventory(), actual_payload)

            rows = list(csv.reader(io.StringIO(archive.read(f"{dist_info}RECORD").decode("utf-8"))))
            if len(rows) != len(names) or {row[0] for row in rows} != set(names):
                raise DistributionVerificationError(f"{path.name} RECORD does not cover every member exactly once")
            for name, digest, size in rows:
                if name == f"{dist_info}RECORD":
                    if digest or size:
                        raise DistributionVerificationError(f"{path.name} RECORD must leave its own hash empty")
                    continue
                payload = archive.read(name)
                if digest != f"sha256={record_sha256(payload)}" or size != str(len(payload)):
                    raise DistributionVerificationError(f"{path.name} RECORD entry for {name!r} is invalid")
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"{path.name} is not a valid wheel: {error}") from error
    return _release_artifact_report(path)


def _checkout_sdist_files() -> dict[str, bytes]:
    """Return every checkout file setuptools places in the source archive."""
    result = {name: (PACKAGE_ROOT / name).read_bytes() for name in ("LICENSE", "README.md", "pyproject.toml")}
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        result[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    # Setuptools includes top-level test modules in an sdist by default. Keep
    # that contract explicit so an unnoticed generated or executable file fails.
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        result[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    return result


def verify_sdist(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the source archive without extracting or executing it."""
    expected_name = f"citry_lsp-{version}.tar.gz"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected sdist {expected_name!r}, found {path.name!r}")
    if path.stat().st_size > MAX_SDIST_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {path.stat().st_size} bytes; the release cap is {MAX_SDIST_BYTES} bytes"
        )
    expected_root = f"citry_lsp-{version}"
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            for name in names:
                _safe_archive_name(name, artifact=path)
            if len(names) != len(set(names)):
                raise DistributionVerificationError(f"{path.name} contains duplicate member names")
            if any(member.issym() or member.islnk() or member.isdev() for member in members):
                raise DistributionVerificationError(f"{path.name} contains links or device members")
            files: dict[str, bytes] = {}
            for member in members:
                if not member.isfile():
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise DistributionVerificationError(f"cannot read {member.name!r} from {path.name}")
                files[member.name] = stream.read()
    except tarfile.TarError as error:
        raise DistributionVerificationError(f"{path.name} is not a valid sdist: {error}") from error

    roots = {PurePosixPath(name).parts[0] for name in files}
    if roots != {expected_root}:
        raise DistributionVerificationError(f"{path.name} must have only the root {expected_root!r}")
    relative = {name.removeprefix(f"{expected_root}/"): payload for name, payload in files.items()}
    generated = {
        "PKG-INFO",
        "setup.cfg",
        "citry_lsp.egg-info/PKG-INFO",
        "citry_lsp.egg-info/SOURCES.txt",
        "citry_lsp.egg-info/dependency_links.txt",
        "citry_lsp.egg-info/entry_points.txt",
        "citry_lsp.egg-info/requires.txt",
        "citry_lsp.egg-info/top_level.txt",
    }
    checkout = _checkout_sdist_files()
    expected = set(checkout) | generated
    missing = sorted(expected - set(relative))
    unexpected = sorted(set(relative) - expected)
    if missing or unexpected:
        raise DistributionVerificationError(
            f"{path.name} member inventory mismatch; missing={missing!r}; unexpected={unexpected!r}"
        )
    for name, payload in checkout.items():
        if relative[name] != payload:
            raise DistributionVerificationError(f"{path.name} contains changed source bytes in {name}")
    _require_metadata(_parse_metadata(relative["PKG-INFO"], artifact=path), artifact=path, version=version)
    if relative["citry_lsp.egg-info/PKG-INFO"] != relative["PKG-INFO"]:
        raise DistributionVerificationError(f"{path.name} contains inconsistent PKG-INFO files")
    if relative["setup.cfg"] != b"[egg_info]\ntag_build = \ntag_date = 0\n\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected generated setup.cfg")
    if relative["citry_lsp.egg-info/dependency_links.txt"] != b"\n":
        raise DistributionVerificationError(f"{path.name} contains unexpected dependency links")
    if relative["citry_lsp.egg-info/entry_points.txt"] != (
        b"[console_scripts]\ncitry-lsp = citry_lsp.__main__:main\n"
    ):
        raise DistributionVerificationError(f"{path.name} contains an unexpected console entry point")
    if relative["citry_lsp.egg-info/top_level.txt"] != b"citry_lsp\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected top-level package")
    sources = relative["citry_lsp.egg-info/SOURCES.txt"].decode("utf-8").splitlines()
    expected_sources = set(checkout) | {name for name in generated if name.startswith("citry_lsp.egg-info/")}
    if len(sources) != len(set(sources)) or set(sources) != expected_sources:
        raise DistributionVerificationError(f"{path.name} contains an inconsistent SOURCES.txt")
    return _release_artifact_report(path)


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


def _artifact_report(path: Path, inventory: Mapping[str, str]) -> dict[str, Any]:
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "archiveSha256": sha256_bytes(path.read_bytes()),
        "files": len(inventory),
        "contentSha256": inventory_fingerprint(inventory),
    }


def _release_artifact_report(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"name": path.name, "bytes": len(payload), "sha256": sha256_bytes(payload)}


def _release_report(wheel: Path, sdist: Path) -> dict[str, Any]:
    return {
        "version": package_version(),
        "artifacts": sorted(
            (_release_artifact_report(wheel), _release_artifact_report(sdist)),
            key=lambda artifact: artifact["name"],
        ),
    }


def _require_empty_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise DistributionVerificationError(f"output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def stage_qualification(wheel: Path, sdist: Path, output_dir: Path) -> dict[str, Any]:
    """Copy only the verified release pair and record their exact bytes."""
    version = package_version()
    actual = {wheel.name, sdist.name}
    expected = expected_release_filenames(version)
    if actual != expected:
        raise DistributionVerificationError(
            f"release inventory mismatch; missing={sorted(expected - actual)!r}; "
            f"unexpected={sorted(actual - expected)!r}"
        )
    _require_empty_output(output_dir)
    shutil.copy2(wheel, output_dir / wheel.name)
    shutil.copy2(sdist, output_dir / sdist.name)
    report = _release_report(wheel, sdist)
    (output_dir / "release-inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def verify_staged_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Re-verify a flat qualification bundle against the tagged checkout."""
    if not bundle_dir.is_dir():
        raise DistributionVerificationError(f"qualification bundle is not a directory: {bundle_dir}")
    entries = sorted(bundle_dir.iterdir())
    if any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise DistributionVerificationError("qualification bundle must contain only regular files at its root")
    version = package_version()
    expected_artifacts = expected_release_filenames(version)
    expected_names = expected_artifacts | {"release-inventory.json"}
    by_name = {entry.name: entry for entry in entries}
    if set(by_name) != expected_names:
        raise DistributionVerificationError(
            f"qualification bundle mismatch; missing={sorted(expected_names - set(by_name))!r}; "
            f"unexpected={sorted(set(by_name) - expected_names)!r}"
        )
    wheel = by_name[f"citry_lsp-{version}-py3-none-any.whl"]
    sdist = by_name[f"citry_lsp-{version}.tar.gz"]
    verify_wheel(wheel, version=version)
    verify_sdist(sdist, version=version)
    report = _release_report(wheel, sdist)
    try:
        recorded: Any = json.loads(by_name["release-inventory.json"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DistributionVerificationError(f"cannot read release-inventory.json: {error}") from error
    if recorded != report:
        raise DistributionVerificationError("release-inventory.json does not match the qualified artifact bytes")
    return report


def promote_qualification_archive(
    archive_path: Path,
    *,
    expected_digest: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Check GitHub's digest, extract its flat bundle safely, and verify it."""
    match = re.fullmatch(r"sha256:([0-9a-f]{64})", expected_digest)
    if match is None:
        raise DistributionVerificationError(f"invalid qualification artifact digest: {expected_digest!r}")
    if sha256_bytes(archive_path.read_bytes()) != match.group(1):
        raise DistributionVerificationError("qualification archive SHA-256 does not match GitHub's artifact digest")
    _require_empty_output(output_dir)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise DistributionVerificationError(f"qualification archive has a corrupt member {bad_member!r}")
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise DistributionVerificationError("qualification archive contains duplicate member names")
            for entry in entries:
                member = _safe_archive_name(entry.filename, artifact=archive_path)
                if len(member.parts) != 1:
                    raise DistributionVerificationError(
                        f"qualification archive member must be a root file: {entry.filename!r}"
                    )
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise DistributionVerificationError(
                        f"qualification archive contains a symbolic link: {entry.filename!r}"
                    )
                (output_dir / entry.filename).write_bytes(archive.read(entry))
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"qualification artifact is not a valid zip archive: {error}") from error
    return verify_staged_bundle(output_dir)


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


def _build_sdist_wheel(sdist: Path, directory: Path, *, cwd: Path) -> Path:
    # Resolve the artifact before changing the child process's working directory.
    # CI passes ``dist/<name>.tar.gz`` while rebuilding outside the checkout.
    sdist = sdist.resolve()
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
import importlib
import importlib.metadata
import importlib.resources
import importlib.util
import pathlib
import subprocess
import sys
import sysconfig

modules = (
    "citry_lsp",
    "citry_lsp.app_worker",
    "citry_lsp.catalog",
    "citry_lsp.engine",
    "citry_lsp.formatting",
    "citry_lsp.project",
    "citry_lsp.protocol",
    "citry_lsp.regions",
    "citry_lsp.semantic",
    "citry_lsp.server",
    "citry_lsp.type_analysis",
    "citry_lsp.uri",
)
for module in modules:
    importlib.import_module(module)

import citry_lsp

assert importlib.metadata.version("citry-lsp") == "__VERSION__"
assert importlib.metadata.version("pygls") == "2.1.1"
assert importlib.metadata.version("ty") == "0.0.73"
citry_version = tuple(int(part) for part in importlib.metadata.version("citry").split(".")[:3])
assert (0, 4, 1) <= citry_version < (0, 5, 0), citry_version
assert citry_lsp.SERVER_VERSION == "__VERSION__"
assert citry_lsp.PROTOCOL_VERSION == 1
assert citry_lsp.SUPPORTED_CITRY_SERIES == (0, 4)
assert importlib.resources.files("citry_lsp").joinpath("py.typed").is_file()
assert importlib.util.find_spec("pytest_lsp") is None
assert pathlib.Path(citry_lsp.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())

script_name = "citry-lsp.exe" if sys.platform == "win32" else "citry-lsp"
script = pathlib.Path(sysconfig.get_path("scripts")) / script_name
assert script.is_file(), script

help_result = subprocess.run(
    [str(script), "--help"],
    check=False,
    capture_output=True,
    timeout=10,
)
assert help_result.returncode == 0, help_result.stderr.decode(errors="replace")
assert b"usage: citry-lsp" in help_result.stdout

stdio_result = subprocess.run(
    [str(script)],
    input=b"",
    check=False,
    capture_output=True,
    timeout=10,
)
assert stdio_result.returncode == 0, stdio_result.stderr.decode(errors="replace")
assert stdio_result.stdout == b""
assert stdio_result.stderr == b""
"""


def _venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def smoke_wheel(wheel: Path, *, cwd: Path) -> None:
    """Install one wheel with public binary dependencies and start the server."""
    with tempfile.TemporaryDirectory(prefix="citry-lsp-install-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        _run(["uv", "venv", "--python", sys.executable, "--no-config", str(environment)], cwd=root)
        python = _venv_python(environment)
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-config",
                "--only-binary",
                ":all:",
                str(wheel),
            ],
            cwd=root,
        )
        smoke = _SMOKE.replace("__VERSION__", package_version())
        clean_env = {name: value for name, value in os.environ.items() if name != "PYTHONPATH"}
        _run([str(python), "-I", "-c", smoke], cwd=cwd, env=clean_env)


def verify_artifacts(source_wheel: Path, sdist: Path, rebuilt_wheel: Path) -> dict[str, Any]:
    """Compare checkout, wheel, sdist, and rebuilt-wheel content."""
    version = package_version()
    verify_wheel(source_wheel, version=version)
    verify_sdist(sdist, version=version)
    verify_wheel(rebuilt_wheel, version=version)
    source_files = source_inventory()
    source_wheel_files = wheel_inventory(source_wheel)
    rebuilt_wheel_files = wheel_inventory(rebuilt_wheel)
    sdist_files = sdist_inventory(sdist)

    require_equal(
        "source and source-built wheel package payload",
        source_files,
        package_payload(source_wheel_files, "citry_lsp"),
    )
    require_equal("source-built and sdist-built wheels", source_wheel_files, rebuilt_wheel_files)

    roots = {name.split("/", 1)[0] for name in sdist_files}
    if len(roots) != 1:
        raise DistributionVerificationError(f"{sdist.name} must contain exactly one top-level directory")
    sdist_root = roots.pop()
    require_equal(
        "source and sdist package payload",
        source_files,
        package_payload(sdist_files, f"{sdist_root}/citry_lsp"),
    )

    return {
        "sourceWheel": _artifact_report(source_wheel, source_wheel_files),
        "sdist": _artifact_report(sdist, sdist_files),
        "sdistWheel": _artifact_report(rebuilt_wheel, rebuilt_wheel_files),
        "installedPayload": {"files": len(source_files), "sha256": inventory_fingerprint(source_files)},
    }


def verify_dist_directory(dist_dir: Path, *, smoke: bool) -> tuple[Path, Path, dict[str, Any]]:
    """Verify one raw wheel/sdist pair and rebuild the sdist outside the checkout."""
    # Every later subprocess runs outside the checkout, so retain absolute
    # artifact paths even when the CLI receives the conventional relative
    # ``--dist-dir dist`` used by the release workflow.
    dist_dir = dist_dir.resolve()
    version = package_version()
    wheel = _unique(dist_dir, f"citry_lsp-{version}-py3-none-any.whl")
    sdist = _unique(dist_dir, f"citry_lsp-{version}.tar.gz")
    with tempfile.TemporaryDirectory(prefix="citry-lsp-sdist-") as temporary:
        root = Path(temporary)
        rebuilt_wheel = _build_sdist_wheel(sdist, root / "wheel", cwd=root)
        report = verify_artifacts(wheel, sdist, rebuilt_wheel)
        if smoke:
            smoke_wheel(wheel, cwd=root)
    return wheel, sdist, report


def main(argv: Sequence[str] | None = None) -> int:
    """Run qualification, stage a bundle, or promote one exact bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument("--stage-output-dir", type=Path)
    parser.add_argument("--skip-install-smoke", action="store_true")
    parser.add_argument("--promote-archive", type=Path)
    parser.add_argument("--artifact-digest")
    parser.add_argument("--promotion-output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.promote_archive is not None:
            if not args.artifact_digest or args.promotion_output_dir is None:
                parser.error("promotion requires --artifact-digest and --promotion-output-dir")
            report = promote_qualification_archive(
                args.promote_archive,
                expected_digest=args.artifact_digest,
                output_dir=args.promotion_output_dir,
            )
        else:
            if args.dist_dir is None:
                parser.error("qualification requires --dist-dir")
            wheel, sdist, report = verify_dist_directory(
                args.dist_dir,
                smoke=not args.skip_install_smoke,
            )
            if args.stage_output_dir is not None:
                report["release"] = stage_qualification(wheel, sdist, args.stage_output_dir)
    except DistributionVerificationError as error:
        parser.exit(1, f"citry-lsp distribution verification failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
