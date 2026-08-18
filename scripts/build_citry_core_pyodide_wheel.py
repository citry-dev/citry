"""Build one reproducible citry-core wheel for the pinned Pyodide ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE: Final = REPO_ROOT / "packages" / "py" / "citry_core"
BUILD_CONFIG: Final = DEFAULT_SOURCE / "pyodide-build.json"
NORMALIZED_SOURCE_ROOT: Final = "/citry/source"


class PyodideBuildError(RuntimeError):
    """The pinned Pyodide wheel could not be built or normalized."""


def load_build_config(path: Path = BUILD_CONFIG) -> dict[str, str | int]:
    """Load and validate the release-owned Pyodide build tuple."""
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise PyodideBuildError(f"unsupported Pyodide build config in {path}")
    required = {
        "pyodide",
        "python",
        "pyodide_cli",
        "pyodide_build",
        "emscripten",
        "rust",
        "maturin",
        "wheel",
        "uv",
        "node",
        "twine",
        "python_tag",
        "abi_tag",
        "platform_tag",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise PyodideBuildError(f"Pyodide build config is missing: {', '.join(missing)}")
    for name in required:
        if not isinstance(data[name], str) or not data[name]:
            raise PyodideBuildError(f"Pyodide build config field {name!r} must be a non-empty string")
    return data


def package_version(source: Path) -> str:
    """Return the package version declared by the selected source tree."""
    pyproject = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    value: Any = pyproject.get("project", {}).get("version")
    if not isinstance(value, str) or not value:
        raise PyodideBuildError(f"{source / 'pyproject.toml'} has no project version")
    return value


def expected_wheel_name(version: str, config: Mapping[str, str | int]) -> str:
    """Return the only wheel filename accepted for the pinned ABI."""
    return f"citry_core-{version}-{config['python_tag']}-{config['abi_tag']}-{config['platform_tag']}.whl"


def _run(command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode:
        raise PyodideBuildError(f"command failed ({' '.join(command)})")


def _capture(command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> str:
    completed = subprocess.run(command, cwd=cwd, env=env, check=False, capture_output=True, text=True)
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if completed.returncode:
        raise PyodideBuildError(f"command failed ({' '.join(command)}): {output}")
    return output


def _verify_emscripten_version(emcc: Path, *, cwd: Path, expected: str) -> None:
    """Prove the installed SDK, rather than only its cache key, matches the tuple."""
    emcc_env = dict(os.environ)
    emcc_env["PATH"] = os.pathsep.join((str(Path(sys.executable).parent), emcc_env.get("PATH", "")))
    output = _capture([str(emcc), "--version"], cwd=cwd, env=emcc_env)
    match = re.search(r"\bemcc .*?\) (\d+\.\d+\.\d+)(?:\s|$)", output)
    actual = match.group(1) if match else None
    if actual != expected:
        raise PyodideBuildError(f"expected Emscripten {expected}, found {actual!r}: {output}")


def _ensure_clean_python_source(source: Path) -> None:
    for path in source.joinpath("citry_core").rglob("*"):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            raise PyodideBuildError(f"source contains a Python cache artifact: {path}")


def _normalize_wheel(
    wheel_path: Path,
    *,
    source_root: Path,
    forbidden_roots: Sequence[Path],
    wasm_opt: Path,
    source_date_epoch: int,
    config: Mapping[str, str | int],
) -> None:
    local_roots = [str(path) for path in dict.fromkeys(forbidden_roots)]
    with tempfile.TemporaryDirectory(prefix="citry-core-pyodide-normalize-") as temporary:
        root = Path(temporary)
        unpacked = root / "unpacked"
        packed = root / "packed"
        unpacked.mkdir()
        packed.mkdir()
        wheel_tool = [
            "uvx",
            "--python",
            str(config["python"]),
            "--from",
            f"wheel=={config['wheel']}",
            "wheel",
        ]
        _run([*wheel_tool, "unpack", str(wheel_path), "--dest", str(unpacked)], cwd=source_root)
        unpacked_roots = [path for path in unpacked.iterdir() if path.is_dir()]
        if len(unpacked_roots) != 1:
            raise PyodideBuildError(f"expected one unpacked wheel root, found {len(unpacked_roots)}")

        extensions = sorted(unpacked_roots[0].glob("citry_core/_rust*.so"))
        if len(extensions) != 1:
            raise PyodideBuildError(f"expected one PyEmscripten extension, found {len(extensions)}")
        stripped_extension = extensions[0].with_suffix(".stripped.so")
        _run(
            [
                str(wasm_opt),
                "--all-features",
                "--strip-debug",
                "--strip-dwarf",
                str(extensions[0]),
                "-o",
                str(stripped_extension),
            ],
            cwd=source_root,
        )
        stripped_extension.replace(extensions[0])

        replacements = 0
        sbom_files = sorted(unpacked_roots[0].glob("*.dist-info/sboms/*.json"))
        if not sbom_files:
            raise PyodideBuildError("the Pyodide wheel contains no generated JSON SBOM")
        for sbom_file in sbom_files:
            original = sbom_file.read_text(encoding="utf-8")
            replacements += original.count(str(source_root))
            normalized = original.replace(str(source_root), NORMALIZED_SOURCE_ROOT)
            json.loads(normalized)
            sbom_file.write_text(normalized, encoding="utf-8")
        if replacements == 0:
            raise PyodideBuildError("the generated SBOM did not contain the source root")

        for path in unpacked_roots[0].rglob("*"):
            if not path.is_file():
                continue
            payload = path.read_bytes()
            for local_root in local_roots:
                if local_root.encode() in payload:
                    raise PyodideBuildError(f"local source path remains in {path}")

        pack_env = dict(os.environ)
        pack_env["SOURCE_DATE_EPOCH"] = str(source_date_epoch)
        _run(
            [*wheel_tool, "pack", str(unpacked_roots[0]), "--dest-dir", str(packed)],
            cwd=source_root,
            env=pack_env,
        )
        packed_wheels = sorted(packed.glob("*.whl"))
        if len(packed_wheels) != 1 or packed_wheels[0].name != wheel_path.name:
            names = ", ".join(path.name for path in packed_wheels)
            raise PyodideBuildError(f"wheel repack produced unexpected artifacts: {names}")
        packed_wheels[0].replace(wheel_path)


def build_wheel(
    *,
    source: Path,
    out_dir: Path,
    xbuildenv_path: Path,
    cargo_target_dir: Path,
    source_date_epoch: int,
    cargo_home: Path,
) -> dict[str, int | str]:
    """Build, normalize, and report the pinned PyEmscripten wheel."""
    source = source.resolve()
    config = load_build_config(source / "pyodide-build.json")
    source_workspace = source.parents[2]
    out_dir = out_dir.resolve()
    xbuildenv_path = xbuildenv_path.resolve()
    cargo_target_dir = cargo_target_dir.resolve()
    cargo_home = cargo_home.resolve()
    if source_date_epoch <= 0:
        raise PyodideBuildError("SOURCE_DATE_EPOCH must be a positive integer")
    runtime_entry = xbuildenv_path / str(config["pyodide"]) / "xbuildenv" / "pyodide-root" / "dist" / "pyodide.mjs"
    if not runtime_entry.is_file():
        raise PyodideBuildError(f"the pinned Pyodide xbuild environment is missing {runtime_entry}")
    wasm_opt = xbuildenv_path / str(config["pyodide"]) / "emsdk" / "upstream" / "bin" / "wasm-opt"
    if not wasm_opt.is_file():
        raise PyodideBuildError(f"the pinned Emscripten optimizer is missing {wasm_opt}")
    emcc = xbuildenv_path / str(config["pyodide"]) / "emsdk" / "upstream" / "emscripten" / "emcc"
    if not emcc.is_file():
        raise PyodideBuildError(f"the pinned Emscripten compiler is missing {emcc}")
    if not (source / "pyproject.toml").is_file() or not (source_workspace / "Cargo.toml").is_file():
        raise PyodideBuildError("--source must point to packages/py/citry_core in this workspace")
    if not cargo_home.is_dir():
        raise PyodideBuildError(f"Cargo home does not exist: {cargo_home}")
    _ensure_clean_python_source(source)
    _verify_emscripten_version(emcc, cwd=source, expected=str(config["emscripten"]))

    version = package_version(source)
    expected_name = expected_wheel_name(version, config)
    out_dir.mkdir(parents=True, exist_ok=True)
    cargo_target_dir.mkdir(parents=True, exist_ok=True)

    rustflags = [
        f"--remap-path-prefix={source_workspace}={NORMALIZED_SOURCE_ROOT}",
        f"--remap-path-prefix={cargo_target_dir}=/citry/target",
        f"--remap-path-prefix={cargo_home}=/citry/cargo-home",
    ]
    build_env = dict(os.environ)
    build_env.update(
        {
            "CARGO_HOME": str(cargo_home),
            "CARGO_TARGET_DIR": str(cargo_target_dir),
            "PYODIDE_XBUILDENV_PATH": str(xbuildenv_path),
            "RUSTFLAGS": " ".join(rustflags),
            "RUSTUP_TOOLCHAIN": str(config["rust"]),
            "SOURCE_DATE_EPOCH": str(source_date_epoch),
        }
    )
    command = [
        "uvx",
        "--python",
        str(config["python"]),
        "--from",
        f"pyodide-cli=={config['pyodide_cli']}",
        "--with",
        f"pyodide-build=={config['pyodide_build']}",
        "--with",
        f"maturin=={config['maturin']}",
        "pyodide",
        "build",
        str(source),
        "--outdir",
        str(out_dir),
        "--config-setting",
        "maturin.build-args=--profile release-wheel",
        "-v",
    ]
    _run(command, cwd=source, env=build_env)
    wheels = sorted(out_dir.glob("citry_core-*.whl"))
    if len(wheels) != 1 or wheels[0].name != expected_name:
        names = ", ".join(path.name for path in wheels)
        raise PyodideBuildError(f"expected only {expected_name}, found: {names}")
    wheel_path = wheels[0]
    _normalize_wheel(
        wheel_path,
        source_root=source_workspace,
        forbidden_roots=(source_workspace, cargo_target_dir, cargo_home, xbuildenv_path),
        wasm_opt=wasm_opt,
        source_date_epoch=source_date_epoch,
        config=config,
    )
    payload = wheel_path.read_bytes()
    return {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "wheel": str(wheel_path),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Build one wheel and print its stable artifact record."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--xbuildenv-path", type=Path, required=True)
    parser.add_argument("--cargo-target-dir", type=Path, required=True)
    parser.add_argument("--cargo-home", type=Path, default=Path.home() / ".cargo")
    parser.add_argument("--source-date-epoch", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_wheel(
            source=args.source,
            out_dir=args.out_dir,
            xbuildenv_path=args.xbuildenv_path,
            cargo_target_dir=args.cargo_target_dir,
            source_date_epoch=args.source_date_epoch,
            cargo_home=args.cargo_home,
        )
    except PyodideBuildError as error:
        parser.exit(1, f"citry-core Pyodide build failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
