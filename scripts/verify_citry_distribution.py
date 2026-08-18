"""Build and verify the citry wheel and source distribution."""

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
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "py" / "citry"
SOURCE_ROOT: Final = PACKAGE_ROOT / "citry"
MAX_WHEEL_BYTES: Final = 1_100 * 1024
EXPECTED_REQUIRES_DIST: Final = {
    "citry-core==1.5.0",
    "wrapt>=1.16",
    "markupsafe>=2.1",
    "typing-extensions>=4.10",
    'tomli>=2.0; python_version < "3.11"',
    "tzdata>=2026.3",
    'ty==0.0.69; extra == "analysis-ty"',
    'watchfiles>=1.0; extra == "watcher-watchfiles"',
    'watchdog>=4.0; extra == "watcher-watchdog"',
}
EXPECTED_EXTRAS: Final = {"analysis-ty", "watcher-watchfiles", "watcher-watchdog"}


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
        raise DistributionVerificationError("citry has no project version")
    return version


def expected_release_filenames(version: str) -> set[str]:
    """Return the complete, closed Citry release set."""
    return {f"citry-{version}-py3-none-any.whl", f"citry-{version}.tar.gz"}


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
    if metadata.get("Name", "").lower().replace("_", "-") != "citry":
        raise DistributionVerificationError(f"{artifact.name} has unexpected Name metadata")
    if metadata.get("Version") != version:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Version metadata")
    if metadata.get("Requires-Python") not in {">=3.10, <4.0", "<4.0,>=3.10"}:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Requires-Python metadata")
    if set(metadata.get_all("Requires-Dist", [])) != EXPECTED_REQUIRES_DIST:  # type: ignore[attr-defined]
        raise DistributionVerificationError(f"{artifact.name} has unexpected runtime dependencies")
    if set(metadata.get_all("Provides-Extra", [])) != EXPECTED_EXTRAS:  # type: ignore[attr-defined]
        raise DistributionVerificationError(f"{artifact.name} has unexpected optional extras")


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


def verify_wheel(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the wheel filename, metadata, RECORD, and closed member set."""
    expected_name = f"citry-{version}-py3-none-any.whl"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected wheel {expected_name!r}, found {path.name!r}")
    if path.stat().st_size > MAX_WHEEL_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {path.stat().st_size} bytes; the release cap is {MAX_WHEEL_BYTES} bytes"
        )
    dist_info = f"citry-{version}.dist-info/"
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
            expected_members = {f"citry/{name}" for name in source_inventory()} | controls
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
            if archive.read(f"{dist_info}entry_points.txt") != b"[console_scripts]\ncitry = citry.__main__:main\n":
                raise DistributionVerificationError(f"{path.name} has an unexpected console entry point")
            if archive.read(f"{dist_info}top_level.txt") != b"citry\n":
                raise DistributionVerificationError(f"{path.name} has an unexpected top-level package")
            if archive.read(f"{dist_info}licenses/LICENSE") != (PACKAGE_ROOT / "LICENSE").read_bytes():
                raise DistributionVerificationError(f"{path.name} does not contain the checked MIT license")

            actual_payload = {
                name.removeprefix("citry/"): sha256_bytes(archive.read(name))
                for name in names
                if name.startswith("citry/")
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
    """Return every reviewed checkout file setuptools may place in the sdist."""
    result = {name: (PACKAGE_ROOT / name).read_bytes() for name in ("LICENSE", "README.md", "pyproject.toml")}
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        result[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    # Setuptools' default sdist contract includes top-level test_*.py modules,
    # but not conftest, helper modules, fixtures, or the browser e2e subtree.
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        result[path.relative_to(PACKAGE_ROOT).as_posix()] = path.read_bytes()
    return result


def verify_sdist(path: Path, *, version: str) -> dict[str, Any]:
    """Validate the source archive without extracting or executing it."""
    expected_name = f"citry-{version}.tar.gz"
    if path.name != expected_name:
        raise DistributionVerificationError(f"expected sdist {expected_name!r}, found {path.name!r}")
    expected_root = f"citry-{version}"
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
        "citry.egg-info/PKG-INFO",
        "citry.egg-info/SOURCES.txt",
        "citry.egg-info/dependency_links.txt",
        "citry.egg-info/entry_points.txt",
        "citry.egg-info/requires.txt",
        "citry.egg-info/top_level.txt",
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
    if relative["citry.egg-info/PKG-INFO"] != relative["PKG-INFO"]:
        raise DistributionVerificationError(f"{path.name} contains inconsistent PKG-INFO files")
    if relative["setup.cfg"] != b"[egg_info]\ntag_build = \ntag_date = 0\n\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected generated setup.cfg")
    if relative["citry.egg-info/dependency_links.txt"] != b"\n":
        raise DistributionVerificationError(f"{path.name} contains unexpected dependency links")
    if relative["citry.egg-info/entry_points.txt"] != b"[console_scripts]\ncitry = citry.__main__:main\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected console entry point")
    if relative["citry.egg-info/top_level.txt"] != b"citry\n":
        raise DistributionVerificationError(f"{path.name} contains an unexpected top-level package")
    sources = relative["citry.egg-info/SOURCES.txt"].decode("utf-8").splitlines()
    expected_sources = set(checkout) | {name for name in generated if name.startswith("citry.egg-info/")}
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


def _release_artifact_report(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "name": path.name,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


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
    wheel = by_name[f"citry-{version}-py3-none-any.whl"]
    sdist = by_name[f"citry-{version}.tar.gz"]
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
    """Check GitHub's digest, extract its flat bundle safely, and verify it again."""
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
from citry import Citry, Component
from citry._protocol import client_graph, events
from citry.ext.i18n import make_context

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
assert root.joinpath("ext/events/client/citry-events-csp.js").is_file()
assert root.joinpath("ext/i18n/client/citry-i18n.js").is_file()
assert root.joinpath("py.typed").is_file()

i18n_app = Citry(
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
        }
    },
)

class I18nPage(Component):
    citry = i18n_app
    template = '{{ tr("wheel-greeting", name=name) }}'

    class Kwargs:
        name: str

    messages = '''
    # @param {str} $name - User name.
    wheel-greeting = Hello, { $name }.
    '''

context = make_context(i18n_app, locale="en-US")
assert str(I18nPage(name="Ada").render(provides={"citry_i18n": context})) == "Hello, \u2068Ada\u2069."
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
    parser.add_argument(
        "--stage-output-dir",
        type=Path,
        help="After the complete proof, stage the exact wheel, sdist, and byte inventory here.",
    )
    parser.add_argument(
        "--promote-archive",
        type=Path,
        help="Instead of building, promote this immutable GitHub qualification archive.",
    )
    parser.add_argument("--artifact-digest", help="GitHub's sha256:<hex> digest for --promote-archive.")
    parser.add_argument("--promotion-output-dir", type=Path, help="Safe extraction target for --promote-archive.")
    args = parser.parse_args(argv)
    try:
        if args.promote_archive is not None:
            if args.artifact_digest is None or args.promotion_output_dir is None:
                raise DistributionVerificationError(
                    "--promote-archive requires --artifact-digest and --promotion-output-dir"
                )
            if args.dist_dir is not None or args.core_wheel is not None or args.stage_output_dir is not None:
                raise DistributionVerificationError("promotion mode cannot build or stage another qualification")
            report = promote_qualification_archive(
                args.promote_archive.resolve(),
                expected_digest=args.artifact_digest,
                output_dir=args.promotion_output_dir.resolve(),
            )
            sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
            return 0
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
            if args.stage_output_dir is not None:
                report["qualification"] = stage_qualification(
                    source_wheel,
                    sdist,
                    args.stage_output_dir.resolve(),
                )
    except DistributionVerificationError as error:
        sys.stderr.write(f"citry distribution verification failed: {error}\n")
        return 1
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
