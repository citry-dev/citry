"""Build the pinned Next production application without using system Node."""

import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario"
if not (SCENARIO / "canonical_project.json").is_file():
    SCENARIO = HERE.parents[1] / "scenarios/project_board"
TOOLCHAIN = json.loads((HERE / "toolchain.json").read_text())
NODE_SPEC = TOOLCHAIN["node"]
NODE_VERSION = NODE_SPEC["version"]
NODE_DIR = HERE / ".toolchain" / f"node-v{NODE_VERSION}-darwin-arm64"
NODE = NODE_DIR / "bin/node"


def download() -> bytes:
    with urllib.request.urlopen(NODE_SPEC["url"], timeout=120) as response:  # noqa: S310 - pinned HTTPS archive
        data = response.read()
    if hashlib.sha256(data).hexdigest() != NODE_SPEC["sha256"]:
        raise ValueError("Node archive checksum differs from the pinned release")
    return data


def ensure_node() -> None:
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise RuntimeError("The Next adapter currently requires macOS ARM64")
    if not NODE.exists():
        NODE_DIR.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(download()), mode="r:gz") as archive:
            root = f"node-v{NODE_VERSION}-darwin-arm64/"
            for member in archive.getmembers():
                relative = member.name.removeprefix(root)
                if relative == "bin/node" or relative.startswith("lib/node_modules/npm/"):
                    archive.extract(member, NODE_DIR.parent)
    if hashlib.sha256(NODE.read_bytes()).hexdigest() != NODE_SPEC["executable_sha256"]:
        raise ValueError("Node executable differs from the pinned release")
    version = subprocess.check_output([str(NODE), "--version"], text=True).strip().removeprefix("v")
    if version != NODE_VERSION:
        raise ValueError(f"Unexpected Node version: {version}")


def materialize_sources(destination: Path = HERE, source: Path = SCENARIO) -> None:
    generated = destination / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    data = json.loads((source / "canonical_project.json").read_text(encoding="utf-8"))["data"]
    (generated / "data.mjs").write_text(
        "export default " + json.dumps(data, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    scenario = destination / "scenario"
    scenario.mkdir(parents=True, exist_ok=True)
    model = scenario / "node_model.mjs"
    if source.joinpath("node_model.mjs").resolve() != model.resolve():
        shutil.copyfile(source / "node_model.mjs", model)
    public_assets = destination / "public" / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "board.css", public_assets / "board.css")


def main() -> None:
    ensure_node()
    materialize_sources()
    package_lock = HERE / "package-lock.json"
    before = hashlib.sha256(package_lock.read_bytes()).hexdigest()
    npm = NODE_DIR / "lib/node_modules/npm/bin/npm-cli.js"
    env = {key: value for key, value in os.environ.items() if not key.startswith(("NPM_CONFIG_", "npm_config_"))}
    env.pop("NODE_OPTIONS", None)
    subprocess.run([str(NODE), str(npm), "ci", "--ignore-scripts"], cwd=HERE, env=env, check=True)
    subprocess.run([str(NODE), str(npm), "run", "build"], cwd=HERE, env=env, check=True)
    if hashlib.sha256(package_lock.read_bytes()).hexdigest() != before:
        raise ValueError("Next build changed the frozen npm lock")


if __name__ == "__main__":
    main()
