#!/usr/bin/env python
"""
The project gate: run every check in one pass and report all results.

Phases: uv lock, cargo fmt, cargo clippy, cargo test, ruff check, ruff format,
mypy, pyright, the private protocol packages, citry-client (tsc, biome, and the
canary over the events client package), the generated docs playground bundle,
the VS Code language extension, pytest, and the custom validators
(scripts/validate.py). Every phase runs even after an earlier one fails, so a
single invocation surfaces every problem at once instead of one-at-a-time.

This only CHECKS; it never edits files. Fix the reported issues yourself, then
re-run. It assumes the workspace is already set up (`uv sync --all-packages`,
plus `pnpm install` for the pinned Node tools and package-local checks) and that
`cargo`, `uv`, `node`, `pnpm`, and a Rust toolchain are on PATH.

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
        # Runs first because it is instant and because a stale lockfile stops CI
        # before any other check gets to run: the workflows install with
        # `uv sync --locked`, which refuses a lockfile that no longer matches the
        # pyproject files. Raising a package's version without re-locking is the
        # easy way to hit that, so catch it here rather than after a push.
        ("uv lock", ["uv", "lock", "--check"]),
        ("cargo fmt", ["cargo", "fmt", "--check", *crates]),
        ("cargo clippy", ["cargo", "clippy", "--no-deps", *crates, "--all-targets", "--", "-D", "warnings"]),
        ("cargo test", ["cargo", "test", *crates]),
        ("ruff check", [*uvr, "ruff", "check", "."]),
        ("ruff format", [*uvr, "ruff", "format", "--check", "."]),
        (
            "mypy",
            [
                *uvr,
                "mypy",
                "packages/py/citry/citry",
                # the typed-base contract test runs under mypy, not pytest
                "packages/py/citry/tests/test_events_typing.py",
                "packages/py/citry/tests/test_library_component_typing.py",
                "packages/py/citry_lsp/citry_lsp",
                "packages/py/citry_ui/citry_ui",
                "packages/py/citry_ui/tests/typing_contract.py",
                "packages/py/citry_core/citry_core",
                "packages/py/pygments_citry/pygments_citry",
                "scripts",
            ],
        ),
        # pyright type-checks the same typed Events base contract that mypy covers
        # above, so the two checkers sit together. It runs the LOCAL, pinned pyright
        # (node_modules/.bin/pyright), never a global one, so the version is
        # reproducible; this assumes `pnpm install` has run, the way the rest of
        # the gate assumes `uv sync`. The flags reproduce the pinned
        # invocation verified in docs/design/events_research/typing-lab-report.md
        # (pyright 1.1.411, --pythonversion 3.13, and --pythonpath at the repo venv
        # python so pyright resolves citry from the same environment mypy uses).
        # Scoped to the typing contract test only; whole-package pyright is a
        # separate decision.
        # The paths here follow the POSIX layout (node_modules/.bin/pyright and
        # .venv/bin/python), which matches where this gate runs: Linux CI and macOS
        # development. A local Windows run would need the Windows Scripts directory
        # and its .cmd launcher instead.
        (
            "pyright",
            [
                str(_REPO_ROOT / "node_modules" / ".bin" / "pyright"),
                "--pythonversion",
                "3.13",
                "--pythonpath",
                str(_REPO_ROOT / ".venv" / "bin" / "python"),
                "packages/py/citry/tests/test_events_typing.py",
                "packages/py/citry/tests/test_library_component_typing.py",
                "packages/py/citry_ui/tests/typing_contract.py",
            ],
        ),
        # The events client package's own gate (packages/js/citry-client):
        # tsc --noEmit over the TypeScript runtime source, biome check (lint
        # plus format), and the pinned-version canary (node --test). Sits by
        # pyright as the other Node-based phase: both run pinned local tools
        # and assume `pnpm install` has run, the way the rest of the gate
        # assumes `uv sync`. pnpm resolves from PATH (CI sets it up before
        # the gate; see repo--check.yml).
        (
            "citry-client",
            ["pnpm", "--dir", "packages/js/citry-client", "run", "check"],
        ),
        (
            "protocol contracts",
            [
                *uvr,
                "python",
                "-m",
                "packages.protocol._tooling.check",
                "packages/protocol/events/v1",
                "packages/protocol/client_graph/v1",
            ],
        ),
        (
            "protocol Python copies",
            [*uvr, "python", "scripts/sync_protocol_python.py", "--check"],
        ),
        (
            "events protocol JavaScript",
            ["pnpm", "--dir", "packages/protocol/events/v1/js", "run", "check"],
        ),
        (
            "client graph protocol JavaScript",
            ["pnpm", "--dir", "packages/protocol/client_graph/v1/js", "run", "check"],
        ),
        (
            "docs-playground",
            ["pnpm", "--dir", "docs_site/_internal/frontend", "run", "check"],
        ),
        (
            "vscode-extension",
            ["pnpm", "--dir", "packages/editors/vscode", "run", "check"],
        ),
        # `--cov` (no target) uses [tool.coverage.run] source; pytest-cov enforces
        # `fail_under` from [tool.coverage.report] (docs/design/migration_djc_tests.md).
        ("pytest", [*uvr, "pytest", "--cov", "--cov-report=term-missing:skip-covered"]),
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
