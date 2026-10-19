"""Bundle locked production browser dependencies before measurements."""

import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build() -> None:
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise RuntimeError("This native frontend build currently requires macOS ARM64")
    output = HERE / "generated"
    output.mkdir(exist_ok=True)
    spec = json.loads((HERE / "toolchain.json").read_text())
    bun = output / "bun"
    if not bun.exists():
        with urllib.request.urlopen(spec["url"], timeout=60) as response:  # noqa: S310 - pinned HTTPS release
            archive = response.read()
        if hashlib.sha256(archive).hexdigest() != spec["sha256"]:
            raise ValueError("Bun archive checksum differs from the pinned release")
        with zipfile.ZipFile(io.BytesIO(archive)) as source:
            bun.write_bytes(source.read("bun-darwin-aarch64/bun"))
        bun.chmod(0o755)
    if hashlib.sha256(bun.read_bytes()).hexdigest() != spec["executable_sha256"]:
        raise ValueError("Bun executable differs from the pinned release")
    env = {
        key: value for key, value in os.environ.items() if not key.startswith(("BUN_", "NPM_CONFIG_", "npm_config_"))
    }
    env.pop("NODE_OPTIONS", None)
    env["BUN_INSTALL_CACHE_DIR"] = str(output / "cache")
    shutil.copyfile(HERE / "package.json", output / "package.json")
    shutil.copyfile(HERE / "bun.lock", output / "bun.lock")
    shutil.copytree(HERE / "src", output / "src", dirs_exist_ok=True)
    subprocess.run([str(bun), "install", "--frozen-lockfile", "--ignore-scripts"], cwd=output, env=env, check=True)
    source = "src/client.jsx" if (output / "src/client.jsx").exists() else "src/client.js"
    subprocess.run(
        [
            str(bun),
            "build",
            source,
            "--outfile",
            "client.js",
            "--target",
            "browser",
            "--minify",
            "--define",
            'process.env.NODE_ENV="production"',
            "--define",
            "__VUE_OPTIONS_API__=true",
            "--define",
            "__VUE_PROD_DEVTOOLS__=false",
            "--define",
            "__VUE_PROD_HYDRATION_MISMATCH_DETAILS__=false",
        ],
        cwd=output,
        env=env,
        check=True,
    )
    if (output / "bun.lock").read_bytes() != (HERE / "bun.lock").read_bytes():
        raise ValueError("Frontend build changed the frozen dependency lock")


if __name__ == "__main__":
    build()
