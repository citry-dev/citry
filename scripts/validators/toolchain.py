"""
Toolchain consistency: rust-toolchain.toml's channel must match the toolchain
the Rust CI workflow installs (.github/workflows/rust--tests.yml).
"""

import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLCHAIN_FILE = REPO_ROOT / "rust-toolchain.toml"
_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "rust--tests.yml"


def check() -> list[str]:
    if not _TOOLCHAIN_FILE.exists():
        return [f"{_TOOLCHAIN_FILE} not found"]
    if not _WORKFLOW_FILE.exists():
        return [f"{_WORKFLOW_FILE} not found"]

    channel = tomllib.loads(_TOOLCHAIN_FILE.read_text()).get("toolchain", {}).get("channel", "")

    content = _WORKFLOW_FILE.read_text()
    action = re.search(r"dtolnay/rust-toolchain", content)
    if action is None:
        return ["could not find 'dtolnay/rust-toolchain' in rust--tests.yml"]
    pinned = re.search(r"toolchain:\s*(\S+)", content[action.end() :])
    if pinned is None:
        return ["could not find a 'toolchain:' value after 'dtolnay/rust-toolchain' in rust--tests.yml"]

    workflow_toolchain = pinned.group(1).strip("\"'")
    if channel != workflow_toolchain:
        return [f"toolchain mismatch: rust-toolchain.toml='{channel}', rust--tests.yml='{workflow_toolchain}'"]
    return []
