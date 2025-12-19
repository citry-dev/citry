#!/usr/bin/env python3
"""
Check that the Rust toolchain version in rust-toolchain.toml matches
the version specified in .github/workflows/tests.yml
"""

import argparse
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger(__name__)

# Add handler to output to stderr (pre-commit expects errors on stderr)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(handler)

# For Python < 3.11, use tomli instead
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-untyped]
    except ImportError:
        log.error(
            "[rust_toolchain_check] tomllib (Python 3.11+) or tomli package required"
        )
        log.error("[rust_toolchain_check] Install with: pip install tomli pyyaml")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check that Rust toolchain versions match between rust-toolchain.toml and .github/workflows/tests.yml"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress debug and info messages, only show errors",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show debug messages in addition to info, warnings, and errors",
    )
    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    # Set log level based on flags (quiet takes precedence over verbose)
    if args.quiet:
        # -q: Only show WARNING and ERROR
        log.setLevel(logging.WARNING)
    elif args.verbose:
        # -v: Show DEBUG, INFO, WARNING, and ERROR
        log.setLevel(logging.DEBUG)
    else:
        # Default: Show INFO, WARNING, and ERROR
        log.setLevel(logging.INFO)

    repo_root = Path(__file__).parent.parent.parent

    # Verify we're in the right directory by checking for a marker file
    if not (repo_root / "Cargo.toml").exists() and not (repo_root / ".git").exists():
        log.error(
            f"[rust_toolchain_check] Could not find repository root. Expected Cargo.toml or .git in {repo_root}"
        )
        sys.exit(1)

    # Read rust-toolchain.toml
    rust_toolchain_file = repo_root / "rust-toolchain.toml"
    if not rust_toolchain_file.exists():
        log.error(f"[rust_toolchain_check] {rust_toolchain_file} not found")
        sys.exit(1)

    log.debug(f"[rust_toolchain_check] Reading {rust_toolchain_file}...")
    rust_toolchain_content = rust_toolchain_file.read_text()
    log.debug(f"[rust_toolchain_check] Parsing {rust_toolchain_file}...")
    rust_toolchain_data = tomllib.loads(rust_toolchain_content)
    toolchain_channel = rust_toolchain_data.get("toolchain", {}).get("channel", "")
    log.debug(f"[rust_toolchain_check] toolchain_channel = {toolchain_channel}")

    # Read .github/workflows/tests.yml
    workflow_file = repo_root / ".github" / "workflows" / "tests.yml"
    if not workflow_file.exists():
        log.error(f"[rust_toolchain_check] {workflow_file} not found")
        sys.exit(1)

    log.debug(f"[rust_toolchain_check] Reading workflow file {workflow_file}...")
    workflow_content = workflow_file.read_text()

    # Extract toolchain value from the workflow using regex
    # Look for "dtolnay/rust-toolchain" and then find the closest "toolchain:" after it
    workflow_toolchain = None
    log.debug("[rust_toolchain_check] Searching for 'dtolnay/rust-toolchain'...")

    # Find the position of dtolnay/rust-toolchain
    dtolnay_match = re.search(r"dtolnay/rust-toolchain", workflow_content)
    if not dtolnay_match:
        log.error(
            "[rust_toolchain_check] Could not find 'dtolnay/rust-toolchain' in workflow"
        )
        sys.exit(1)

    # From that position, search forward for the next "toolchain:" line
    # Look for "toolchain:" followed by whitespace and a value
    remaining_content = workflow_content[dtolnay_match.end() :]
    toolchain_match = re.search(r"toolchain:\s*(\S+)", remaining_content)

    if toolchain_match:
        workflow_toolchain = toolchain_match.group(1).strip("\"'")
        log.debug(
            f"[rust_toolchain_check] Found workflow_toolchain = {workflow_toolchain}"
        )
    else:
        log.error(
            "[rust_toolchain_check] Could not find 'toolchain:' value after 'dtolnay/rust-toolchain'"
        )
        sys.exit(1)

    # Compare values
    if toolchain_channel != workflow_toolchain:
        log.error("[rust_toolchain_check] Rust toolchain version mismatch!")
        log.error(f"[rust_toolchain_check]   rust-toolchain.toml: {toolchain_channel}")
        log.error(
            f"[rust_toolchain_check]   .github/workflows/tests.yml: {workflow_toolchain}"
        )
        sys.exit(1)

    log.info(
        f"[rust_toolchain_check] ✓ Rust toolchain versions match: {toolchain_channel}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
