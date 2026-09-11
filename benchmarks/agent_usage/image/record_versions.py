"""Record the installed public tools so a run can identify its environment."""

import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

PACKAGES = ("citry", "citry_core", "fastapi", "uvicorn", "pytest", "httpx", "playwright")


def main() -> None:
    """Write versions into the image without consulting host configuration."""
    # Read the installed tools, so this report describes the resulting image.
    versions = {
        "python": platform.python_version(),
        "node": subprocess.check_output(["/usr/local/bin/node", "--version"], text=True).strip(),
        "npm": subprocess.check_output(["/usr/local/bin/npm", "--version"], text=True).strip(),
        "codex": subprocess.check_output(["/usr/local/bin/codex", "--version"], text=True).strip(),
        "packages": {package: version(package) for package in PACKAGES},
    }
    Path("/opt/agent-eval/versions.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
