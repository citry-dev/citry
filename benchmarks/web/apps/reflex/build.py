"""Prepare pinned local JavaScript tools and export Reflex before measurements."""

import hashlib
import io
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from configuration import configure_environment

HERE = Path(__file__).resolve().parent


def download(spec: dict) -> bytes:
    if not spec["url"].startswith("https://"):
        raise ValueError("Tool archives require HTTPS")
    with urllib.request.urlopen(spec["url"], timeout=120) as response:  # noqa: S310 - pinned HTTPS archive
        data = response.read()
    if hashlib.sha256(data).hexdigest() != spec["sha256"]:
        raise ValueError("Tool archive checksum differs from the pinned release")
    return data


def seed_frontend_resolution(directory: Path) -> None:
    """Seed Reflex's canonical resolution before it initializes the web directory."""
    persisted = directory / "reflex.lock"
    persisted.mkdir(exist_ok=True)
    for name in ("bun.lock", "package.json"):
        shutil.copyfile(directory / "frontend" / name, persisted / name)


def main() -> None:
    # This first native adapter pins the available macOS ARM64 toolchain only.
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise RuntimeError("The Reflex toolchain currently requires macOS ARM64")
    tools = json.loads((HERE / "toolchain.json").read_text())
    node_dir = HERE / ".toolchain" / "node-v22.22.0-darwin-arm64"
    if not node_dir.exists():
        with tarfile.open(fileobj=io.BytesIO(download(tools["node"])), mode="r:gz") as archive:
            archive.extractall(HERE / ".toolchain", filter="data")
    bun = HERE / ".reflex/bun/bin/bun"
    if not bun.exists():
        with zipfile.ZipFile(io.BytesIO(download(tools["bun"]))) as archive:
            data = archive.read("bun-darwin-aarch64/bun")
        bun.parent.mkdir(parents=True, exist_ok=True)
        bun.write_bytes(data)
        bun.chmod(0o755)
    for name, executable in (("node", node_dir / "bin/node"), ("bun", bun)):
        if hashlib.sha256(executable.read_bytes()).hexdigest() != tools[name]["executable_sha256"]:
            raise ValueError(f"Unexpected {name} executable bytes")
        version = subprocess.check_output([str(executable), "--version"], text=True).strip().removeprefix("v")
        if version != tools[name]["version"]:
            raise ValueError(f"Unexpected {name} version: {version}")
    web = HERE / ".web"
    web.mkdir(exist_ok=True)
    # Reflex mirrors this canonical pair into .web and prunes orphaned .web locks.
    seed_frontend_resolution(HERE)
    configure_environment(compile_frontend=True)
    # Ask Reflex which configuration and tools it selected before invoking the compiler.
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from configuration import validate_configuration; "
            "from reflex.config import get_config; "
            "from reflex.utils.path_ops import get_node_path, get_bun_path; "
            "validate_configuration(get_config(), get_node_path(), get_bun_path())",
        ],
        cwd=HERE,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "reflex", "export", "--frontend-only", "--no-zip", "--env", "prod"],
        cwd=HERE,
        check=True,
    )
    for name in ("bun.lock", "package.json"):
        if any(
            (directory / name).read_bytes() != (HERE / "frontend" / name).read_bytes()
            for directory in (web, HERE / "reflex.lock")
        ):
            raise ValueError(f"Compiled frontend changed the pinned {name}")
    if not (web / "build/client/index.html").is_file():
        raise RuntimeError("Reflex export did not produce a production document")


if __name__ == "__main__":
    main()
