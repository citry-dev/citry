#!/usr/bin/env python3
"""
Warn at session start when a code intelligence plugin cannot start its server.

The project enables the `rust-analyzer-lsp` and `pyright-lsp` plugins in
.claude/settings.json. Claude Code installs those plugins, but not the
language servers they start, and a missing server only shows up under
`/plugin` > Errors. Claude then falls back to grep and whole-file reads
without anyone noticing. This SessionStart hook checks both servers and,
when one is missing or broken, shows the user a warning with the command
that fixes it and tells Claude that the `LSP` tool will not work.

Checks:
- rust-analyzer: `rust-analyzer --version` must succeed in the project
  directory. The rustup proxy exists on every machine with rustup, so
  finding the binary on PATH is not enough; the proxy fails until the
  component is installed for the toolchain in rust-toolchain.toml.
- pyright: `pyright-langserver` must be on PATH, and `pyright --version`
  must match the version package.json pins for the check gate, so the
  language server and the gate report the same type errors.

Prints nothing and exits 0 when both servers work. A check that cannot run
counts as a problem: a server that times out on `--version` will not serve
Claude either, and without the package.json pin the hook cannot tell whether
pyright matches the gate.
"""

# The hook runs under whatever `python3` is on PATH, which can be as old as
# the 3.9 that macOS ships, so newer annotation syntax must not be evaluated.
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Claude's first reply waits for SessionStart hooks. Each version check takes
# well under a second on a working machine, so a slow answer usually means a
# broken install, though the pip `pyright` wrapper's first-run download can
# also take longer.
TIMEOUT_SECONDS = 10

# The rustup proxy would otherwise download a missing toolchain (for example
# right after the nightly date moves) while the session waits. With this set
# it fails at once and says which toolchain to install.
RUSTUP_ENV = {**os.environ, "RUSTUP_AUTO_INSTALL": "0"}

# A pin such as "1.1.414"; a range like "^1.1.414" cannot be compared with
# the installed version.
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def run_version(executable: str, cwd: Path, env: dict[str, str] | None = None) -> tuple[bool, str]:
    """Run `<executable> --version` and return (succeeded, first output line).

    `executable` is the full path `shutil.which` returned. Running that path
    also works for a Windows `.cmd` shim, which a bare name without a shell
    cannot start.
    """
    try:
        result = subprocess.run(  # noqa: S603 - fixed arguments, no shell
            [executable, "--version"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    output = (result.stdout or result.stderr).strip().splitlines()
    return result.returncode == 0, output[0] if output else ""


def check_rust_analyzer(root: Path) -> str | None:
    """Return a problem description, or None when rust-analyzer works."""
    fix = "Run `rustup component add rust-analyzer` in the repository."
    executable = shutil.which("rust-analyzer")
    if executable is None:
        return f"rust-analyzer is not on PATH. {fix}"
    works, detail = run_version(executable, root, RUSTUP_ENV)
    if not works:
        # The rustup proxy answers "Unknown binary 'rust-analyzer' in
        # official toolchain ..." until the component is installed.
        if "is not installed" in detail:
            # The pinned toolchain itself is missing, so the component add
            # alone would fail too.
            fix = "Run `rustup toolchain install`, then `rustup component add rust-analyzer`, in the repository."
        return f"rust-analyzer does not start ({detail}). {fix}"
    return None


def pinned_pyright(root: Path) -> str | None:
    """Return the pyright version package.json pins, or None if unreadable."""
    try:
        manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return manifest.get("devDependencies", {}).get("pyright")


def check_pyright(root: Path) -> str | None:
    """Return a problem description, or None when pyright works."""
    pin = pinned_pyright(root)
    if pin is None:
        return "Cannot read the pyright pin from package.json `devDependencies`."
    fix = f'Run `npm install -g "pyright@{pin}"`.'
    server = shutil.which("pyright-langserver")
    if server is None:
        return f"pyright-langserver is not on PATH. {fix}"
    # Ask the `pyright` installed next to the server the plugin starts, so the
    # version belongs to that install even when PATH holds a second pyright.
    sibling = Path(server).with_name(Path(server).name.replace("pyright-langserver", "pyright"))
    cli = str(sibling) if sibling.exists() else shutil.which("pyright")
    if cli is None:
        return f"pyright is not on PATH next to pyright-langserver. {fix}"
    works, detail = run_version(cli, root)
    if not works:
        return f"pyright does not start ({detail}). {fix}"
    if not EXACT_VERSION.match(pin):
        # The gate resolves a range itself; only an exact pin can be compared.
        return None
    # `pyright --version` prints "pyright 1.1.414".
    installed = detail.split()[-1] if detail else ""
    if installed != pin:
        return f"pyright {installed or '(unknown)'} is installed, but package.json pins {pin}. {fix}"
    return None


def main() -> int:
    # Claude Code sets CLAUDE_PROJECT_DIR for hooks; the fallback (this file is
    # .claude/hooks/<name>) keeps a manual run from a subdirectory working.
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
    problems = [p for p in (check_rust_analyzer(root), check_pyright(root)) if p]
    if not problems:
        return 0
    details = "\n".join(f"- {p}" for p in problems)
    print(
        json.dumps(
            {
                # Shown to the user at the start of the session.
                "systemMessage": (
                    "Code intelligence is not fully working in this repository:\n"
                    f"{details}\nSee 'Setting up Claude Code' in docs/codebase.md."
                ),
                # Tells Claude why the LSP tool fails, so it says so instead of
                # silently falling back to grep.
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        "A language server for this repository is missing or broken, so the "
                        "LSP tool will fail for the affected language:\n"
                        f"{details}\nTell the user once, then use Grep and ranged reads "
                        "for that language."
                    ),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
