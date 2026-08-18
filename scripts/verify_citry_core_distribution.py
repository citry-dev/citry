"""Verify, stage, rebuild, and smoke-test citry-core release artifacts."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from email.parser import BytesParser
from itertools import product
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final

import tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from email.message import Message

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
PACKAGE_ROOT: Final = REPO_ROOT / "packages" / "py" / "citry_core"
SOURCE_ROOT: Final = PACKAGE_ROOT / "citry_core"
PYODIDE_CONFIG: Final = PACKAGE_ROOT / "pyodide-build.json"
SMOKE_SCRIPT: Final = REPO_ROOT / "scripts" / "smoke_citry_core.py"
MAX_WHEEL_BYTES: Final = 10 * 1024 * 1024
SUPPORTED_CPYTHON: Final = ("310", "311", "312", "313", "314")
LINUX_PLATFORMS: Final = {
    "x86_64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
    "i686": "manylinux_2_5_i686.manylinux1_i686",
    "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "armv7l": "manylinux_2_17_armv7l.manylinux2014_armv7l",
    "s390x": "manylinux_2_17_s390x.manylinux2014_s390x",
    "ppc64le": "manylinux_2_17_ppc64le.manylinux2014_ppc64le",
}
MUSL_PLATFORMS: Final = {arch: f"musllinux_1_2_{arch}" for arch in ("x86_64", "i686", "aarch64", "armv7l")}
WINDOWS_PLATFORMS: Final = ("win32", "win_amd64")
MACOS_PLATFORMS: Final = ("macosx_10_12_x86_64", "macosx_11_0_arm64")


class DistributionVerificationError(RuntimeError):
    """A release artifact is missing, unexpected, malformed, or cannot run."""


def sha256_bytes(payload: bytes) -> str:
    """Return a URL-safe RECORD digest without padding."""
    return base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")


def hex_sha256(payload: bytes) -> str:
    """Return a lowercase hexadecimal SHA-256 digest."""
    return hashlib.sha256(payload).hexdigest()


def package_version() -> str:
    """Read the release version from the package metadata."""
    project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version: Any = project.get("version")
    if not isinstance(version, str) or not version:
        raise DistributionVerificationError("citry-core has no project version")
    return version


def expected_release_filenames(version: str) -> set[str]:
    """Return the closed artifact set for the support matrix."""
    wheels: set[str] = set()
    for platform in (*LINUX_PLATFORMS.values(), *MUSL_PLATFORMS.values()):
        wheels.update(f"citry_core-{version}-cp{py}-cp{py}-{platform}.whl" for py in SUPPORTED_CPYTHON)
        wheels.add(f"citry_core-{version}-cp314-cp314t-{platform}.whl")
        wheels.add(f"citry_core-{version}-pp311-pypy311_pp73-{platform}.whl")
    for platform in (*WINDOWS_PLATFORMS, *MACOS_PLATFORMS):
        wheels.update(f"citry_core-{version}-cp{py}-cp{py}-{platform}.whl" for py in SUPPORTED_CPYTHON)
    config: Any = json.loads(PYODIDE_CONFIG.read_text(encoding="utf-8"))
    wheels.add(f"citry_core-{version}-{config['python_tag']}-{config['abi_tag']}-{config['platform_tag']}.whl")
    wheels.add(f"citry_core-{version}.tar.gz")
    return wheels


def source_inventory() -> dict[str, str]:
    """Hash the platform-independent Python payload that every wheel must carry."""
    result: dict[str, str] = {}
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.suffix not in {".py", ".pyi"} and path.name != "py.typed":
            continue
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        result[relative] = hex_sha256(path.read_bytes())
    return result


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
    if metadata.get("Name", "").lower().replace("_", "-") != "citry-core":
        raise DistributionVerificationError(f"{artifact.name} has unexpected Name metadata")
    if metadata.get("Version") != version:
        raise DistributionVerificationError(f"{artifact.name} has unexpected Version metadata")
    if metadata.get("Requires-Python") != ">=3.10, <4.0":
        raise DistributionVerificationError(f"{artifact.name} has unexpected Requires-Python metadata")
    if metadata.get("Requires-Dist") is not None:
        raise DistributionVerificationError(f"{artifact.name} unexpectedly declares a runtime dependency")


def _wheel_filename_parts(path: Path) -> tuple[str, str, str]:
    try:
        _distribution, _version, python, abi, platform = path.name.removesuffix(".whl").split("-", 4)
    except ValueError as error:
        raise DistributionVerificationError(f"cannot parse wheel filename {path.name}") from error
    return python, abi, platform


def _wheel_filename_tags(path: Path) -> set[str]:
    python, abi, platform = _wheel_filename_parts(path)
    return {"-".join(parts) for parts in product(python.split("."), abi.split("."), platform.split("."))}


def verify_wheel(path: Path, *, version: str) -> dict[str, Any]:
    """Validate one wheel's metadata, RECORD, tags, and package contents."""
    if path.stat().st_size > MAX_WHEEL_BYTES:
        raise DistributionVerificationError(
            f"{path.name} is {path.stat().st_size} bytes; the release cap is {MAX_WHEEL_BYTES} bytes"
        )
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise DistributionVerificationError(f"{path.name} has a corrupt member {bad_member!r}")
            entries = [entry for entry in archive.infolist() if not entry.is_dir()]
            names = [entry.filename for entry in entries]
            for name in names:
                _safe_archive_name(name, artifact=path)
            if len(names) != len(set(names)):
                raise DistributionVerificationError(f"{path.name} contains duplicate member names")
            metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
            wheel_names = [name for name in names if name.endswith(".dist-info/WHEEL")]
            record_names = [name for name in names if name.endswith(".dist-info/RECORD")]
            if not (len(metadata_names) == len(wheel_names) == len(record_names) == 1):
                raise DistributionVerificationError(f"{path.name} must contain one METADATA, WHEEL, and RECORD")
            dist_info = f"citry_core-{version}.dist-info/"
            expected_control_files = {
                f"{dist_info}METADATA",
                f"{dist_info}WHEEL",
                f"{dist_info}RECORD",
            }
            if {*metadata_names, *wheel_names, *record_names} != expected_control_files:
                raise DistributionVerificationError(
                    f"{path.name} must use the canonical {dist_info!r} metadata directory"
                )
            metadata = _parse_metadata(archive.read(metadata_names[0]), artifact=path)
            _require_metadata(metadata, artifact=path, version=version)

            wheel_metadata = _parse_metadata(archive.read(wheel_names[0]), artifact=path)
            filename_tags = _wheel_filename_tags(path)
            wheel_tags = set(wheel_metadata.get_all("Tag", []))  # type: ignore[attr-defined]
            if not wheel_tags or not wheel_tags.issubset(filename_tags):
                raise DistributionVerificationError(
                    f"{path.name} WHEEL tags {sorted(wheel_tags)!r} disagree with its filename"
                )
            if wheel_metadata.get("Root-Is-Purelib") != "false":
                raise DistributionVerificationError(f"{path.name} must be a platform wheel")

            actual_payload = {
                name: hex_sha256(archive.read(name))
                for name in names
                if name.startswith("citry_core/") and name.endswith((".py", ".pyi", "/py.typed"))
            }
            expected_payload = source_inventory()
            if actual_payload != expected_payload:
                changed = sorted(set(actual_payload) ^ set(expected_payload))
                changed.extend(
                    name
                    for name in sorted(set(actual_payload) & set(expected_payload))
                    if actual_payload[name] != expected_payload[name]
                )
                raise DistributionVerificationError(
                    f"{path.name} Python payload differs from checkout at {', '.join(changed[:20])}"
                )
            extensions = [
                name for name in names if name.startswith("citry_core/_rust.") and name.endswith((".so", ".pyd"))
            ]
            if len(extensions) != 1:
                raise DistributionVerificationError(
                    f"{path.name} must contain exactly one native extension; found {extensions!r}"
                )
            package_members = {name for name in names if name.startswith("citry_core/")}
            unexpected_package_members = sorted(package_members - set(expected_payload) - set(extensions))
            if unexpected_package_members:
                raise DistributionVerificationError(
                    f"{path.name} contains unexpected package files: {', '.join(unexpected_package_members[:20])}"
                )
            python_tag, _abi_tag, platform_tag = _wheel_filename_parts(path)
            if platform_tag == "pyemscripten_2026_0_wasm32":
                expected_extension = "citry_core/_rust.cpython-314-wasm32-emscripten.so"
                extension_matches = extensions[0] == expected_extension
            elif platform_tag.startswith("win"):
                extension_matches = f"/_rust.{python_tag}-" in f"/{extensions[0]}"
            elif python_tag.startswith("cp"):
                extension_matches = f"cpython-{python_tag.removeprefix('cp')}" in extensions[0]
            else:
                extension_matches = "pypy311" in extensions[0]
            if not extension_matches:
                raise DistributionVerificationError(
                    f"{path.name} extension {extensions[0]!r} does not match interpreter tag {python_tag!r}"
                )
            if any("__pycache__" in name or name.endswith((".pyc", ".pyo")) for name in names):
                raise DistributionVerificationError(f"{path.name} contains Python cache artifacts")
            licenses = [name for name in names if ".dist-info/licenses/" in name and name.endswith("/LICENSE")]
            if len(licenses) != 1 or archive.read(licenses[0]) != (PACKAGE_ROOT / "LICENSE").read_bytes():
                raise DistributionVerificationError(f"{path.name} does not contain the checked MIT license")
            expected_members = package_members | {
                f"{dist_info}METADATA",
                f"{dist_info}WHEEL",
                f"{dist_info}RECORD",
                f"{dist_info}licenses/LICENSE",
                f"{dist_info}sboms/citry_core_py.cyclonedx.json",
            }
            unexpected_members = sorted(set(names) - expected_members)
            missing_members = sorted(expected_members - set(names))
            if unexpected_members or missing_members:
                raise DistributionVerificationError(
                    f"{path.name} member inventory mismatch; missing={missing_members!r}; "
                    f"unexpected={unexpected_members!r}"
                )

            rows = list(csv.reader(io.StringIO(archive.read(record_names[0]).decode("utf-8"))))
            if len(rows) != len(names) or {row[0] for row in rows} != set(names):
                raise DistributionVerificationError(f"{path.name} RECORD does not cover every member exactly once")
            for name, digest, size in rows:
                if name == record_names[0]:
                    if digest or size:
                        raise DistributionVerificationError(f"{path.name} RECORD must leave its own hash empty")
                    continue
                payload = archive.read(name)
                if digest != f"sha256={sha256_bytes(payload)}" or size != str(len(payload)):
                    raise DistributionVerificationError(f"{path.name} RECORD entry for {name!r} is invalid")
    except zipfile.BadZipFile as error:
        raise DistributionVerificationError(f"{path.name} is not a valid wheel: {error}") from error
    payload = path.read_bytes()
    return {
        "name": path.name,
        "bytes": len(payload),
        "sha256": hex_sha256(payload),
        "extension": extensions[0],
        "tags": sorted(wheel_tags),
    }


def verify_sdist(path: Path, *, version: str) -> dict[str, Any]:
    """Validate one source distribution without extracting it."""
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
    expected_root = f"citry_core-{version}"
    if roots != {expected_root}:
        raise DistributionVerificationError(f"{path.name} must have only the root {expected_root!r}")
    relative = {name.removeprefix(f"{expected_root}/"): payload for name, payload in files.items()}
    required = {
        "PKG-INFO",
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "Cargo.toml",
        "Cargo.lock",
        "crates/citry_core_py/Cargo.toml",
        "crates/citry_i18n/Cargo.toml",
        "crates/citry_html_transform/Cargo.toml",
        "crates/citry_template_formatter/Cargo.toml",
        "crates/citry_template_parser/Cargo.toml",
        "crates/python_safe_eval/Cargo.toml",
        "third_party/rust/ruff/crates/ruff_python_parser/Cargo.toml",
    }
    missing = sorted(required - relative.keys())
    if missing:
        raise DistributionVerificationError(f"{path.name} is missing required source files: {', '.join(missing)}")
    _require_metadata(_parse_metadata(relative["PKG-INFO"], artifact=path), artifact=path, version=version)
    if relative["LICENSE"] != (PACKAGE_ROOT / "LICENSE").read_bytes():
        raise DistributionVerificationError(f"{path.name} does not contain the checked MIT license")
    expected_source = source_inventory()
    actual_source = {
        name: hex_sha256(payload)
        for name, payload in relative.items()
        if name.startswith("citry_core/") and name.endswith((".py", ".pyi", "/py.typed"))
    }
    if actual_source != expected_source:
        raise DistributionVerificationError(f"{path.name} Python payload differs from the checkout")
    for name, payload in relative.items():
        if name == "PKG-INFO":
            continue
        if name == "pyproject.toml":
            expected_manifest = tomllib.loads((PACKAGE_ROOT / name).read_text(encoding="utf-8"))
            expected_manifest["tool"]["maturin"]["manifest-path"] = "crates/citry_core_py/Cargo.toml"
            if tomllib.loads(payload.decode("utf-8")) != expected_manifest:
                raise DistributionVerificationError(f"{path.name} contains an unexpected generated pyproject.toml")
            continue
        if name in {"LICENSE", "README.md"} or name.startswith("citry_core/"):
            source_path = PACKAGE_ROOT / name
        else:
            source_path = REPO_ROOT / name
        if not source_path.is_file():
            raise DistributionVerificationError(f"{path.name} contains unchecked source member {name!r}")
        if name.endswith("Cargo.toml"):
            expected_manifest = tomllib.loads(source_path.read_text(encoding="utf-8"))
            actual_manifest = tomllib.loads(payload.decode("utf-8"))
            expected_package = expected_manifest.get("package", {})
            actual_package = actual_manifest.get("package", {})
            if (
                isinstance(expected_package, dict)
                and isinstance(actual_package, dict)
                and "readme" not in expected_package
                and actual_package.get("readme") == "README.md"
                and source_path.with_name("README.md").is_file()
            ):
                actual_package.pop("readme")
            if actual_manifest != expected_manifest:
                raise DistributionVerificationError(f"{path.name} contains changed Cargo metadata in {name}")
        elif payload != source_path.read_bytes():
            raise DistributionVerificationError(f"{path.name} contains changed source bytes in {name}")
    workspace = tomllib.loads(relative["Cargo.toml"].decode("utf-8"))
    if workspace.get("workspace", {}).get("package", {}).get("rust-version") != "1.95":
        raise DistributionVerificationError(f"{path.name} does not declare the Rust 1.95 minimum")
    for crate in required:
        if not crate.startswith("crates/") or not crate.endswith("/Cargo.toml"):
            continue
        manifest = tomllib.loads(relative[crate].decode("utf-8"))
        if manifest.get("package", {}).get("rust-version") != {"workspace": True}:
            raise DistributionVerificationError(f"{path.name} does not carry MSRV inheritance in {crate}")
    if any(
        part in {".git", "target", "__pycache__", ".pytest_cache", ".mypy_cache"}
        for name in relative
        for part in PurePosixPath(name).parts
    ):
        raise DistributionVerificationError(f"{path.name} contains repository or build artifacts")
    payload = path.read_bytes()
    return {"name": path.name, "bytes": len(payload), "sha256": hex_sha256(payload), "files": len(files)}


def stage_and_verify(raw_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Reject collisions, verify the closed release set, and stage safe copies."""
    candidates = sorted(path for path in raw_dir.rglob("*") if path.is_file())
    by_name: dict[str, list[Path]] = {}
    for path in candidates:
        by_name.setdefault(path.name, []).append(path)
    duplicates = sorted(name for name, paths in by_name.items() if len(paths) != 1)
    if duplicates:
        raise DistributionVerificationError(f"duplicate artifact basenames: {', '.join(duplicates)}")
    version = package_version()
    expected = expected_release_filenames(version)
    actual = set(by_name)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise DistributionVerificationError(
            f"release inventory mismatch; missing={missing!r}; unexpected={unexpected!r}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        raise DistributionVerificationError(f"verified output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, Any]] = []
    for name in sorted(expected):
        source = by_name[name][0]
        report = (
            verify_wheel(source, version=version) if name.endswith(".whl") else verify_sdist(source, version=version)
        )
        shutil.copy2(source, output_dir / name)
        artifacts.append(report)
    report = {"version": version, "artifacts": artifacts}
    (output_dir / "release-inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _run(command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> str:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        output = (completed.stdout + completed.stderr).strip()
        raise DistributionVerificationError(f"command failed ({' '.join(command)}):\n{output}")
    return completed.stdout


def smoke_wheel(wheel: Path, *, python: str = sys.executable) -> dict[str, str]:
    """Install and exercise one wheel in an isolated environment outside the checkout."""
    version = package_version()
    verify_wheel(wheel, version=version)
    with tempfile.TemporaryDirectory(prefix="citry-core-wheel-smoke-") as temporary:
        root = Path(temporary).resolve()
        venv = root / "venv"
        _run(["uv", "venv", str(venv), "--python", python], cwd=root)
        executable = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        _run(["uv", "pip", "install", "--python", str(executable), str(wheel.resolve())], cwd=root)
        env = dict(os.environ)
        for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
            env.pop(name, None)
        env["CITRY_CORE_EXPECTED_VERSION"] = version
        output = _run([str(executable), "-I", str(SMOKE_SCRIPT)], cwd=root, env=env)
        smoke: Any = json.loads(output)
        extension = Path(smoke["extension"]).resolve()
        if venv not in extension.parents:
            raise DistributionVerificationError(f"citry-core imported outside the smoke venv: {extension}")
        return {"wheel": wheel.name, "python": str(executable), "extension": str(extension)}


def smoke_sdist(sdist: Path, *, rust_toolchain: str) -> dict[str, Any]:
    """Rebuild the sdist with its declared MSRV and smoke the rebuilt wheel."""
    version = package_version()
    verify_sdist(sdist, version=version)
    with tempfile.TemporaryDirectory(prefix="citry-core-sdist-smoke-") as temporary:
        root = Path(temporary).resolve()
        output_dir = root / "dist"
        env = dict(os.environ)
        env["RUSTUP_TOOLCHAIN"] = rust_toolchain
        _run(
            [
                "uv",
                "build",
                str(sdist.resolve()),
                "--wheel",
                "--out-dir",
                str(output_dir),
                "--no-config",
                "--no-build-logs",
            ],
            cwd=root,
            env=env,
        )
        wheels = sorted(output_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise DistributionVerificationError(f"sdist rebuild produced {len(wheels)} wheels")
        return {
            "sdist": sdist.name,
            "rebuilt": verify_wheel(wheels[0], version=version),
            "smoke": smoke_wheel(wheels[0]),
        }


def _one(path_or_glob: str) -> Path:
    path = Path(path_or_glob)
    if path.is_file():
        return path.resolve()
    anchor = Path(path.anchor) if path.anchor else Path()
    matches = sorted(anchor.glob(str(path.relative_to(anchor))))
    if len(matches) != 1:
        raise DistributionVerificationError(f"expected one match for {path_or_glob!r}, found {len(matches)}")
    return matches[0].resolve()


def main(argv: Sequence[str] | None = None) -> int:
    """Run one distribution proof and print a machine-readable report."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--raw-dir", type=Path, required=True)
    inventory.add_argument("--output-dir", type=Path, required=True)
    wheel = subparsers.add_parser("smoke-wheel")
    wheel.add_argument("--wheel", required=True)
    wheel.add_argument("--python", default=sys.executable)
    check_wheel = subparsers.add_parser("check-wheel")
    check_wheel.add_argument("--wheel", required=True)
    sdist = subparsers.add_parser("smoke-sdist")
    sdist.add_argument("--sdist", required=True)
    sdist.add_argument("--rust-toolchain", default="1.95.0")
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            report = stage_and_verify(args.raw_dir.resolve(), args.output_dir.resolve())
        elif args.command == "smoke-wheel":
            report = smoke_wheel(_one(args.wheel), python=args.python)
        elif args.command == "check-wheel":
            report = verify_wheel(_one(args.wheel), version=package_version())
        else:
            report = smoke_sdist(_one(args.sdist), rust_toolchain=args.rust_toolchain)
    except DistributionVerificationError as error:
        parser.exit(1, f"citry-core distribution verification failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
