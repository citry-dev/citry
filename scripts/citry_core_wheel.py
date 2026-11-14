"""
Name, build, verify, and install the citry-core wheel that CI jobs share.

Building the Rust extension takes minutes on every OS, so CI builds one
citry-core wheel per runner OS, caches it under a key derived from every file
that goes into it, and installs that wheel in each job instead of letting
`uv sync` compile the extension again. The key changes whenever a Rust source,
a Cargo manifest, the lockfile, the toolchain pin, the Python half of the
package, or this build recipe changes, so a job never installs a wheel built
from older sources.

Commands:

- `cache-key` prints the cache key for this runner as a GitHub output.
- `build` builds the wheel, imports it in a throwaway environment, and writes
  a manifest that ties the wheel's bytes to its cache key.
- `install` checks the manifest, syncs the workspace without the editable
  citry-core package, and installs the wheel in its place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

import tomllib

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# Raise this when the meaning of a cached wheel changes in a way the hashed
# files below cannot show, so every runner builds a fresh one.
_WHEEL_CACHE_VERSION: Final = "v1"

# The folders and files `git ls-files` reads. `_is_native_wheel_input` then
# keeps only the entries that can change the wheel.
_NATIVE_PATHS: Final = (
    ".cargo",
    "Cargo.lock",
    "Cargo.toml",
    "crates",
    "packages/py/citry_core",
    "rust-toolchain.toml",
    "third_party/rust",
)

# The recipe that builds the shared wheel. A change to either file changes the
# key, so a wheel built by an earlier recipe is never reused.
_RECIPE_PATHS: Final = (
    ".gitattributes",
    ".github/actions/citry-core-wheel/action.yml",
    ".github/actions/install-rust/action.yml",
    "scripts/citry_core_wheel.py",
)

# The feature and profile the release workflow uses for the CPython wheel:
# one limited-API wheel serves every supported GIL-enabled CPython, and the
# tests run the optimization settings users install. The compiler differs:
# this build uses the nightly that rust-toolchain.toml pins, while releases
# use the minimum supported Rust.
_MATURIN_BUILD_ARGS: Final = "--features abi3-py311 --profile release-wheel"

# Crate folders whose files never reach the compiled library.
_CRATE_NON_BUILD_DIRS: Final = frozenset({"benches", "docs", "examples", "tests"})


def _executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        msg = f"required executable is unavailable: {name}"
        raise RuntimeError(msg)
    return executable


def _is_native_wheel_input(path: PurePosixPath) -> bool:
    """Return whether a tracked file can change the citry-core wheel."""
    parts = path.parts
    if path.as_posix() in {"Cargo.lock", "Cargo.toml", "rust-toolchain.toml"}:
        return True
    # Cargo reads its configuration from here before every build.
    if parts[:1] == (".cargo",):
        return True
    # The Ruff submodule shows up as one entry carrying its commit, and the
    # patched vize crates as ordinary files; both are compiled into the wheel.
    if parts[:2] == ("third_party", "rust"):
        return True
    if parts[:1] == ("crates",):
        # Markdown never compiles in, and test, bench, example, and doc
        # folders are not part of the library build.
        return path.suffix != ".md" and (len(parts) < 3 or parts[2] not in _CRATE_NON_BUILD_DIRS)
    if parts[:3] == ("packages", "py", "citry_core"):
        # maturin packs the Python package, the metadata, the README, and the
        # license files. Tests and the changelog stay out of the wheel.
        if len(parts) == 4:
            return path.name in {"pyproject.toml", "README.md"} or path.name.startswith("LICENSE")
        return parts[3:4] == ("citry_core",)
    return False


def _git_index_records(repo_root: Path, paths: Iterable[str], *, select_all: Iterable[str] = ()) -> bytes:
    """
    Return the index records (mode, blob hash, path) for the selected files.

    Reading the index rather than the files makes the digest cheap even for the
    Ruff submodule, which appears as a single entry naming its commit, and
    works before the submodule is checked out.
    """
    always = set(select_all)
    command = [_executable("git"), "ls-files", "--stage", "-z", "--", *paths, *always]
    result = subprocess.run(command, cwd=repo_root, check=True, capture_output=True)
    selected = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        if not separator:
            msg = "unexpected Git index record while identifying native inputs"
            raise RuntimeError(msg)
        text = raw_path.decode("utf-8")
        if text in always or _is_native_wheel_input(PurePosixPath(text)):
            selected.append(metadata + separator + raw_path + b"\0")
    if not selected:
        msg = "native cache inputs were not found in the Git index"
        raise RuntimeError(msg)
    return b"".join(selected)


def _build_constraints(repo_root: Path) -> bytes:
    """Return the root build constraints, which pin the maturin that builds the wheel."""
    root = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    constraints = root.get("tool", {}).get("uv", {}).get("build-constraint-dependencies", [])
    # Hash only this table, so an unrelated edit to the root pyproject.toml
    # (a ruff rule, a dev tool) keeps the cached wheel.
    return json.dumps(constraints, sort_keys=True).encode()


def native_source_digest(
    *,
    repo_root: Path = _REPO_ROOT,
    version: str = _WHEEL_CACHE_VERSION,
    extra_paths: Sequence[str] = _RECIPE_PATHS,
) -> str:
    """
    Hash every tracked file that can change the wheel, plus the build recipe.

    `extra_paths` names files hashed in full whatever the selection rule says,
    such as the workflow or script that builds the wheel.
    """
    digest = hashlib.sha256()
    digest.update(version.encode())
    digest.update(b"\0")
    digest.update(_git_index_records(repo_root, _NATIVE_PATHS, select_all=extra_paths))
    digest.update(b"\0")
    digest.update(_build_constraints(repo_root))
    return digest.hexdigest()


def _safe_key_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def cache_key(runner_os: str, runner_arch: str, image_os: str, *, repo_root: Path = _REPO_ROOT) -> dict[str, str]:
    """
    Return the cache key of the shared wheel for this runner.

    The key leaves out the Python version, because the limited-API wheel works
    on every supported CPython, and the rustc version, because
    rust-toolchain.toml (hashed above) pins the compiler. Leaving both out lets
    a job look the wheel up before it installs Python tooling or Rust.
    """
    source_digest = native_source_digest(repo_root=repo_root)
    uv_version = subprocess.run([_executable("uv"), "--version"], check=True, capture_output=True, text=True)
    identity = hashlib.sha256()
    for value in (runner_os, runner_arch, image_os, uv_version.stdout.strip(), source_digest):
        identity.update(value.encode())
        identity.update(b"\0")
    prefix = "-".join(_safe_key_part(value) for value in (runner_os, runner_arch, image_os))
    return {
        "cache_key": f"citry-core-wheel-{_WHEEL_CACHE_VERSION}-{prefix}-{identity.hexdigest()}",
        "source_digest": source_digest,
    }


def _one_wheel(wheel_dir: Path) -> Path:
    wheels = sorted(wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        msg = f"expected exactly one citry-core wheel in {wheel_dir}, found {len(wheels)}"
        raise RuntimeError(msg)
    return wheels[0]


def record_wheel(wheel_dir: Path, cache_key: str) -> Path:
    """Write the manifest that ties the wheel's name and bytes to its cache key."""
    wheel = _one_wheel(wheel_dir)
    manifest = {
        "cache_key": cache_key,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "wheel": wheel.name,
    }
    (wheel_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return wheel


def verified_wheel(wheel_dir: Path, expected_cache_key: str | None) -> Path:
    """
    Return the wheel after checking it against its manifest.

    A wheel whose bytes or name differ from the manifest was changed after the
    build, so it is refused. With `expected_cache_key`, a wheel recorded under
    another key is refused too; a job that downloads the wheel from an earlier
    job in the same run passes None, because that job already checked the key.
    """
    wheel = _one_wheel(wheel_dir)
    try:
        manifest = json.loads((wheel_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        msg = "the citry-core wheel has no valid manifest"
        raise RuntimeError(msg) from error
    recorded_key = manifest.get("cache_key") if isinstance(manifest, dict) else None
    expected = {
        "cache_key": recorded_key if expected_cache_key is None else expected_cache_key,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "wheel": wheel.name,
    }
    if not isinstance(recorded_key, str) or manifest != expected:
        msg = "the citry-core wheel does not match its manifest or cache key"
        raise RuntimeError(msg)
    return wheel


def _venv_python(venv: Path) -> Path:
    return venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"


# Importing the extension proves the wheel loads on this runner; the profile
# check proves it was built optimized, which the timing benchmarks rely on.
_SMOKE_IMPORT: Final = (
    "import citry_core._rust as rust; assert rust.BUILD_PROFILE == 'release', rust.BUILD_PROFILE; print(rust.__file__)"
)


def _smoke_test(wheel: Path) -> None:
    """Install the wheel into a throwaway environment and import its extension."""
    uv = _executable("uv")
    with tempfile.TemporaryDirectory() as scratch:
        venv = Path(scratch) / "venv"
        subprocess.run([uv, "venv", "--python", sys.executable, str(venv)], check=True)
        subprocess.run([uv, "pip", "install", "--python", str(venv), "--no-deps", str(wheel)], check=True)
        # `-I` and a scratch working directory keep the checkout's citry_core
        # sources off sys.path, so the import can only find the installed wheel.
        subprocess.run([str(_venv_python(venv)), "-I", "-c", _SMOKE_IMPORT], cwd=scratch, check=True)


# Settings that would change the compiled code without changing any hashed
# file. A workflow may set them for its own builds (some pin the workspace's
# minimum Rust version through RUSTUP_TOOLCHAIN), so the shared build drops
# them and always uses the toolchain rust-toolchain.toml names and the flags
# Cargo.toml sets.
_UNHASHED_BUILD_VARIABLES: Final = frozenset(
    {
        "CARGO_BUILD_RUSTFLAGS",
        "CARGO_BUILD_TARGET",
        "CARGO_ENCODED_RUSTFLAGS",
        "MACOSX_DEPLOYMENT_TARGET",
        "MATURIN_PEP517_ARGS",
        "RUSTFLAGS",
        "RUSTUP_TOOLCHAIN",
    }
)
# Prefixes of the same kind: per-profile and per-target Cargo settings
# (CARGO_TARGET_DIR goes too, so the build writes to ./target, the folder
# rust-cache saves), and PyO3's interpreter overrides (maturin sets those it
# needs itself).
_UNHASHED_BUILD_PREFIXES: Final = ("CARGO_PROFILE_", "CARGO_TARGET_", "PYO3_")


def _build_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Return the environment for the wheel build without settings the key does not cover."""
    return {
        name: value
        for name, value in environment.items()
        if name not in _UNHASHED_BUILD_VARIABLES and not name.startswith(_UNHASHED_BUILD_PREFIXES)
    }


def build_wheel(wheel_dir: Path, cache_key: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Build the shared wheel, prove it imports, and record its manifest."""
    # A leftover wheel would make the directory ambiguous, so start empty.
    if wheel_dir.exists() and any(wheel_dir.iterdir()):
        msg = f"{wheel_dir} must be empty before a build"
        raise RuntimeError(msg)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    command = [
        _executable("uv"),
        "build",
        "--package",
        "citry-core",
        "--wheel",
        # The interpreter running this script, so the build does not depend
        # on which other Pythons the runner has.
        "--python",
        sys.executable,
        "--out-dir",
        str(wheel_dir),
        "--config-setting",
        f"maturin.build-args={_MATURIN_BUILD_ARGS}",
    ]
    subprocess.run(command, cwd=repo_root, check=True, env=_build_environment(os.environ))
    wheel = _one_wheel(wheel_dir)
    # Check before recording, so a broken wheel is never saved under the key.
    _smoke_test(wheel)
    record_wheel(wheel_dir, cache_key)
    return wheel


def install_wheel(
    wheel_dir: Path,
    sync_arguments: Sequence[str],
    *,
    expected_cache_key: str | None = None,
    repo_root: Path = _REPO_ROOT,
) -> Path:
    """
    Sync the workspace without editable citry-core, then install the shared wheel.

    `sync_arguments` are the job's own `uv sync` selections, such as
    `--all-packages` or `--group e2e`.
    """
    # Check the wheel before changing the environment, so a bad download
    # fails before the slow sync.
    wheel = verified_wheel(wheel_dir, expected_cache_key)
    uv = _executable("uv")
    # `--no-install-package` keeps uv from building the editable citry-core,
    # which is the compile this whole script exists to skip.
    subprocess.run(
        [uv, "sync", "--locked", *sync_arguments, "--no-install-package", "citry-core"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [uv, "pip", "install", "--python", ".venv", "--no-deps", "--reinstall", str(wheel)],
        cwd=repo_root,
        check=True,
    )
    subprocess.run([uv, "run", "--no-sync", "python", "-c", _SMOKE_IMPORT], cwd=repo_root, check=True)
    return wheel


def _write_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                msg = f"GitHub output {key} must fit on one line"
                raise ValueError(msg)
            output.write(f"{key}={value}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    key = subparsers.add_parser("cache-key", help="write the wheel's cache key as a GitHub output")
    key.add_argument("--runner-os", required=True)
    key.add_argument("--runner-arch", required=True)
    key.add_argument("--image-os", required=True, help="the hosted image family, such as ubuntu24")
    key.add_argument("--github-output", required=True, type=Path)

    build = subparsers.add_parser("build", help="build, smoke-test, and record the wheel")
    build.add_argument("--wheel-dir", required=True, type=Path)
    build.add_argument("--cache-key", required=True)

    install = subparsers.add_parser("install", help="sync the workspace and install the wheel")
    install.add_argument("--wheel-dir", required=True, type=Path)
    install.add_argument("--cache-key", default=None)
    install.add_argument("sync_arguments", nargs=argparse.REMAINDER, help="`uv sync` arguments after `--`")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "cache-key":
        values = cache_key(args.runner_os, args.runner_arch, args.image_os)
        _write_github_outputs(args.github_output, values)
        sys.stdout.write(f"citry-core wheel cache key: {values['cache_key']}\n")
    elif args.command == "build":
        wheel = build_wheel(args.wheel_dir, args.cache_key)
        sys.stdout.write(f"Built and recorded {wheel.name}\n")
    elif args.command == "install":
        sync_arguments = list(args.sync_arguments)
        if sync_arguments[:1] == ["--"]:
            sync_arguments = sync_arguments[1:]
        wheel = install_wheel(args.wheel_dir, sync_arguments, expected_cache_key=args.cache_key)
        sys.stdout.write(f"Installed {wheel.name} in place of the editable citry-core\n")


if __name__ == "__main__":
    main()
