"""Validate targets, cache Citry Core wheels, and install dependencies for Python diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path, PurePosixPath
from typing import Final

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WHEEL_CACHE_VERSION: Final = "v1"
_NATIVE_PATHS: Final = (
    ".cargo",
    ".github/workflows/py--diagnostic.yml",
    "Cargo.lock",
    "Cargo.toml",
    "crates",
    "packages/py/citry_core",
    "rust-toolchain.toml",
    "scripts/python_diagnostic.py",
    "third_party/rust/ruff",
    "uv.lock",
)
_PROFILE_ROOTS: Final = {
    "citry": (PurePosixPath("packages/py/citry/tests"),),
    "citry-core": (PurePosixPath("packages/py/citry_core/tests"),),
    "citry-lsp": (PurePosixPath("packages/py/citry_lsp/tests"),),
    "citry-ui": (PurePosixPath("packages/py/citry_ui"),),
    "pygments-citry": (PurePosixPath("packages/py/pygments_citry/tests"),),
}
_SYNC_ARGUMENTS: Final = {
    # Citry owns several repository-policy tests that import root dev tools
    # such as PyYAML, so its narrow profile selects both owners.
    "citry": ("--package", "citry-monorepo", "--package", "citry"),
    "citry-core": ("--package", "citry-core"),
    "citry-lsp": ("--package", "citry-lsp"),
    "citry-ui": ("--package", "citry-ui"),
    "pygments-citry": ("--package", "pygments-citry"),
    "full-workspace": ("--all-packages",),
}
_NO_CORE_PROFILE: Final = "pygments-citry"


def _profile_roots(profile: str) -> tuple[PurePosixPath, ...]:
    if profile == "full-workspace":
        return tuple(root for roots in _PROFILE_ROOTS.values() for root in roots)
    try:
        return _PROFILE_ROOTS[profile]
    except KeyError as error:
        msg = f"unknown diagnostic profile: {profile}"
        raise ValueError(msg) from error


def validate_pytest_target(profile: str, target: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Validate one non-browser test file or node ID within the selected profile."""
    if not target or target.startswith("-") or "\\" in target or any(char in target for char in "\0\r\n"):
        msg = "pytest target must be one repository-relative POSIX test file or node ID"
        raise ValueError(msg)

    file_text, separator, node_text = target.partition("::")
    if separator and (not node_text or any(not part for part in node_text.split("::"))):
        msg = "pytest node ID segments must not be empty"
        raise ValueError(msg)

    relative = PurePosixPath(file_text)
    if relative.is_absolute() or "." in relative.parts or ".." in relative.parts:
        msg = "pytest target must stay within the selected package"
        raise ValueError(msg)
    if relative.suffix != ".py" or not relative.name.startswith("test_"):
        msg = "pytest target must name a test_*.py file"
        raise ValueError(msg)
    if "e2e" in relative.parts or "benchmark" in relative.name:
        msg = "browser and benchmark tests are outside the diagnostic workflow"
        raise ValueError(msg)
    if not any(relative.is_relative_to(root) for root in _profile_roots(profile)):
        msg = f"pytest target is outside the {profile} diagnostic profile"
        raise ValueError(msg)

    resolved_root = repo_root.resolve()
    resolved_target = (resolved_root / Path(*relative.parts)).resolve()
    if not resolved_target.is_relative_to(resolved_root) or not resolved_target.is_file():
        msg = "pytest target must be an existing repository file"
        raise ValueError(msg)
    return resolved_target


def _git_index_records(repo_root: Path) -> bytes:
    command = [_executable("git"), "ls-files", "--stage", "-z", "--", *_NATIVE_PATHS]
    result = subprocess.run(command, cwd=repo_root, check=True, capture_output=True)
    selected = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        if not separator:
            msg = "unexpected Git index record while identifying native inputs"
            raise RuntimeError(msg)
        path = PurePosixPath(raw_path.decode("utf-8"))
        if _is_native_wheel_input(path):
            selected.append(metadata + separator + raw_path + b"\0")
    if not selected:
        msg = "native cache inputs were not found in the Git index"
        raise RuntimeError(msg)
    return b"".join(selected)


def _is_native_wheel_input(path: PurePosixPath) -> bool:
    if path.as_posix() in {
        ".github/workflows/py--diagnostic.yml",
        "Cargo.lock",
        "Cargo.toml",
        "rust-toolchain.toml",
        "scripts/python_diagnostic.py",
        "uv.lock",
    }:
        return True
    if path.parts[:1] == (".cargo",):
        return True
    if path.as_posix() == "third_party/rust/ruff":
        return True
    if path.parts[:1] == ("crates",):
        return path.name in {"Cargo.toml", "build.rs"} or "src" in path.parts[2:]
    if path.parts[:3] == ("packages", "py", "citry_core"):
        return path.name in {"pyproject.toml", "README.md", "LICENSE"} or path.parts[3:4] == ("citry_core",)
    return False


def native_source_digest(*, repo_root: Path = _REPO_ROOT) -> str:
    """Hash tracked native build inputs, including the Ruff submodule commit."""
    digest = hashlib.sha256()
    digest.update(_WHEEL_CACHE_VERSION.encode())
    digest.update(b"\0")
    digest.update(_git_index_records(repo_root))
    return digest.hexdigest()


def _rustc_identity() -> tuple[str, str]:
    result = subprocess.run([_executable("rustc"), "-Vv"], check=True, capture_output=True, text=True)
    verbose = result.stdout.strip()
    commit = next(
        (line.partition(":")[2].strip() for line in verbose.splitlines() if line.startswith("commit-hash:")),
        "unknown",
    )
    return verbose, commit


def _uv_identity() -> str:
    result = subprocess.run([_executable("uv"), "--version"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _safe_key_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        msg = f"required executable is unavailable: {name}"
        raise RuntimeError(msg)
    return executable


def cache_identity(
    runner_os: str,
    runner_arch: str,
    runner_image: str,
    *,
    repo_root: Path = _REPO_ROOT,
) -> dict[str, str]:
    """Return the exact native-wheel cache identity for this runner."""
    rustc_verbose, rustc_commit = _rustc_identity()
    python_abi = str(sysconfig.get_config_var("SOABI") or sys.implementation.cache_tag)
    python_runtime = f"{platform.python_implementation()}-{platform.python_version()}-{python_abi}"
    source_digest = native_source_digest(repo_root=repo_root)
    uv_version = _uv_identity()

    identity = hashlib.sha256()
    for value in (runner_os, runner_arch, runner_image, python_runtime, rustc_verbose, uv_version, source_digest):
        identity.update(value.encode())
        identity.update(b"\0")

    readable_prefix = "-".join(
        _safe_key_part(value) for value in (runner_os, runner_arch, sys.implementation.cache_tag or "python")
    )
    return {
        "cache_key": f"diagnostic-citry-core-wheel-{_WHEEL_CACHE_VERSION}-{readable_prefix}-{identity.hexdigest()}",
        "python_abi": python_abi,
        "rustc_commit": rustc_commit,
        "source_digest": source_digest,
        "uv_version": uv_version,
    }


def _one_wheel(wheel_dir: Path) -> Path:
    wheels = sorted(wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        msg = f"expected exactly one cached citry-core wheel, found {len(wheels)}"
        raise RuntimeError(msg)
    return wheels[0]


def record_wheel(wheel_dir: Path, cache_key: str) -> Path:
    """Record the cache identity and wheel digest beside a newly built wheel."""
    wheel = _one_wheel(wheel_dir)
    manifest = {
        "cache_key": cache_key,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "wheel": wheel.name,
    }
    (wheel_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return wheel


def verified_wheel(wheel_dir: Path, expected_cache_key: str) -> Path:
    """Reject incomplete, misplaced, or modified wheel-cache contents."""
    wheel = _one_wheel(wheel_dir)
    manifest_path = wheel_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        msg = "cached citry-core wheel has no valid manifest"
        raise RuntimeError(msg) from error
    expected_digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if manifest != {"cache_key": expected_cache_key, "sha256": expected_digest, "wheel": wheel.name}:
        msg = "cached citry-core wheel does not match its cache identity or digest"
        raise RuntimeError(msg)
    return wheel


def install_profile(profile: str, wheel_dir: Path, expected_cache_key: str) -> None:
    """Install only the selected package's test environment and its exact Core wheel."""
    try:
        profile_arguments = _SYNC_ARGUMENTS[profile]
    except KeyError as error:
        msg = f"unknown diagnostic profile: {profile}"
        raise ValueError(msg) from error

    sync_command = [_executable("uv"), "sync", "--locked", *profile_arguments]
    if profile != _NO_CORE_PROFILE:
        sync_command.extend(("--no-install-package", "citry-core"))
    subprocess.run(sync_command, cwd=_REPO_ROOT, check=True)

    if profile != _NO_CORE_PROFILE:
        wheel = verified_wheel(wheel_dir, expected_cache_key)
        install_command = [
            _executable("uv"),
            "pip",
            "install",
            "--python",
            ".venv",
            "--no-deps",
            "--reinstall",
            str(wheel),
        ]
        subprocess.run(install_command, cwd=_REPO_ROOT, check=True)
        # Loading the extension catches incompatible or incomplete wheels before
        # the workflow saves an immutable entry under the exact cache key.
        smoke_command = [
            _executable("uv"),
            "run",
            "--no-sync",
            "python",
            "-c",
            "import citry_core._rust as rust; print(rust.__file__)",
        ]
        subprocess.run(smoke_command, cwd=_REPO_ROOT, check=True)


def _write_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                msg = f"GitHub output {key} must fit on one line"
                raise ValueError(msg)
            output.write(f"{key}={value}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-target")
    validate.add_argument("--profile", required=True, choices=tuple(_SYNC_ARGUMENTS))
    validate.add_argument("--target", required=True)

    identity = subparsers.add_parser("cache-identity")
    identity.add_argument("--runner-os", required=True)
    identity.add_argument("--runner-arch", required=True)
    identity.add_argument("--runner-image", required=True)
    identity.add_argument("--github-output", required=True, type=Path)

    record = subparsers.add_parser("record-wheel")
    record.add_argument("--wheel-dir", required=True, type=Path)
    record.add_argument("--cache-key", required=True)

    install = subparsers.add_parser("install-profile")
    install.add_argument("--profile", required=True, choices=tuple(_SYNC_ARGUMENTS))
    install.add_argument("--wheel-dir", required=True, type=Path)
    install.add_argument("--cache-key", default="")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate-target":
        path = validate_pytest_target(args.profile, args.target)
        sys.stdout.write(f"Validated diagnostic target: {path.relative_to(_REPO_ROOT)}\n")
    elif args.command == "cache-identity":
        values = cache_identity(args.runner_os, args.runner_arch, args.runner_image)
        _write_github_outputs(args.github_output, values)
        sys.stdout.write(
            "Citry Core wheel identity: "
            f"Python ABI {values['python_abi']}, rustc {values['rustc_commit'][:12]}, "
            f"{values['uv_version']}, sources {values['source_digest'][:12]}\n"
        )
    elif args.command == "record-wheel":
        wheel = record_wheel(args.wheel_dir, args.cache_key)
        sys.stdout.write(f"Recorded Citry Core wheel: {wheel.name}\n")
    elif args.command == "install-profile":
        install_profile(args.profile, args.wheel_dir, args.cache_key)
        sys.stdout.write(f"Installed diagnostic profile: {args.profile}\n")


if __name__ == "__main__":
    main()
