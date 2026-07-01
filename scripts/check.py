#!/usr/bin/env python
"""
The project gate: run every check in one pass and report all results.

Phases: cargo fmt, cargo clippy, cargo test, ruff check, ruff format, mypy,
pytest, and the custom validators (scripts/validate.py). Every phase runs even
after an earlier one fails, so a single invocation surfaces every problem at
once instead of one-at-a-time.

This only CHECKS; it never edits files. Fix the reported issues yourself, then
re-run. It assumes the workspace is already set up (`uv sync --all-packages`)
and that `cargo`, `uv`, and a Rust toolchain are on PATH.

Usage:
    python scripts/check.py                    # human-readable, streamed output
    python scripts/check.py --reporter agent   # one JSON object for tools/agents
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CRATES_DIR = _REPO_ROOT / "crates"
_TAIL_LINES = 60


def _crate_flags() -> list[str]:
    """One `-p <crate>` per first-party crate, so cargo skips the vendored ruff submodule."""
    flags: list[str] = []
    for item in sorted(_CRATES_DIR.iterdir()):
        if item.is_dir() and (item / "Cargo.toml").exists():
            flags += ["-p", item.name]
    return flags


def _phases() -> list[tuple[str, list[str]]]:
    crates = _crate_flags()
    uvr = ["uv", "run", "--no-sync"]
    return [
        ("cargo fmt", ["cargo", "fmt", "--check", *crates]),
        ("cargo clippy", ["cargo", "clippy", "--no-deps", *crates, "--all-targets", "--", "-D", "warnings"]),
        ("cargo test", ["cargo", "test", *crates]),
        ("ruff check", [*uvr, "ruff", "check", "."]),
        ("ruff format", [*uvr, "ruff", "format", "--check", "."]),
        ("mypy", [*uvr, "mypy", "packages/py/citry/citry", "packages/py/citry_core/citry_core", "scripts"]),
        ("pytest", [*uvr, "pytest"]),
        ("validators", [sys.executable, "scripts/validate.py"]),
    ]


def _run(cmd: list[str], *, capture: bool) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=_REPO_ROOT, capture_output=capture, text=True, check=False)
    except FileNotFoundError as exc:
        return 127, str(exc)
    output = (proc.stdout or "") + (proc.stderr or "") if capture else ""
    return proc.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full check suite (lint, types, tests, custom validators).")
    parser.add_argument("--reporter", choices=["agent"], help="Emit one JSON object instead of streaming output.")
    args = parser.parse_args()
    agent = args.reporter == "agent"

    results: list[dict[str, object]] = []
    for name, cmd in _phases():
        if not agent:
            print(f"\n=== {name} ===")
        code, output = _run(cmd, capture=agent)
        result: dict[str, object] = {
            "name": name,
            "command": " ".join(cmd),
            "status": "PASSED" if code == 0 else "FAILED",
        }
        if code != 0:
            result["exitCode"] = code
            if agent:
                result["details"] = "\n".join(output.splitlines()[-_TAIL_LINES:]).strip() or "(no output)"
        results.append(result)
        if not agent:
            print(f"{'PASS' if code == 0 else 'FAIL'}: {name}")

    failed = [str(r["name"]) for r in results if r["status"] == "FAILED"]
    if agent:
        print(json.dumps({"status": "FAILED" if failed else "PASSED", "phases": results}))
    elif failed:
        print(f"\n{len(failed)} of {len(results)} checks failed: {', '.join(failed)}", file=sys.stderr)
    else:
        print(f"\nAll {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
