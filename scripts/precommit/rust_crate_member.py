#!/usr/bin/env python3
"""
Check that each Rust crate in `crates/` is listed in `workspace.members` in `Cargo.toml`,
and that all `workspace.members` entries point to existing crates.
"""

import argparse
import logging
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
            "[rust_crate_member] tomllib (Python 3.11+) or tomli package required"
        )
        log.error("[rust_crate_member] Install with: pip install tomli")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check that Rust crates in crates/ are listed in workspace.members"
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


def extract_workspace_members(cargo_toml_content: str) -> set[str]:
    """Extract workspace.members from Cargo.toml."""
    cargo_data = tomllib.loads(cargo_toml_content)
    workspace = cargo_data.get("workspace", {})
    members = workspace.get("members", [])

    # Convert to set and normalize paths
    members_set = set()
    for member in members:
        # Normalize the path (remove leading/trailing slashes, handle relative paths)
        normalized = member.strip("/")
        members_set.add(normalized)
        log.debug(f"[rust_crate_member] Found workspace member: {normalized}")

    return members_set


def find_rust_crates(crates_dir: Path) -> set[str]:
    """Find all Rust crates in crates/ directory."""
    crates = set()

    if not crates_dir.exists():
        log.error(f"[rust_crate_member] Directory not found: {crates_dir}")
        return crates

    for item in crates_dir.iterdir():
        if item.is_dir():
            # Check if it's a Rust crate (has Cargo.toml)
            if (item / "Cargo.toml").exists():
                crate_path = f"crates/{item.name}"
                crates.add(crate_path)
                log.debug(f"[rust_crate_member] Found Rust crate: {crate_path}")

    return crates


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

    # Verify we're in the right directory
    if not (repo_root / "Cargo.toml").exists() and not (repo_root / ".git").exists():
        log.error(
            f"[rust_crate_member] Could not find repository root. Expected Cargo.toml or .git in {repo_root}"
        )
        sys.exit(1)

    # Read Cargo.toml
    cargo_toml_file = repo_root / "Cargo.toml"
    if not cargo_toml_file.exists():
        log.error(f"[rust_crate_member] {cargo_toml_file} not found")
        sys.exit(1)

    log.debug(f"[rust_crate_member] Reading {cargo_toml_file}...")
    cargo_toml_content = cargo_toml_file.read_text()

    # Extract workspace.members from Cargo.toml
    workspace_members = extract_workspace_members(cargo_toml_content)
    log.debug(
        f"[rust_crate_member] Found {len(workspace_members)} workspace members in Cargo.toml"
    )

    # Find all Rust crates in crates/
    crates_dir = repo_root / "crates"
    rust_crates = find_rust_crates(crates_dir)
    log.debug(f"[rust_crate_member] Found {len(rust_crates)} Rust crates in crates/")

    # Check for missing entries: crates not in workspace.members
    missing_entries = rust_crates - workspace_members
    if missing_entries:
        log.error("[rust_crate_member] Rust crates missing from workspace.members:")
        for crate in sorted(missing_entries):
            log.error(f"[rust_crate_member]   - {crate}")
        log.error(
            "[rust_crate_member] Add entries to Cargo.toml under [workspace] members like:"
        )
        log.error("[rust_crate_member]   [workspace]")
        log.error("[rust_crate_member]   members = [")
        for crate in sorted(missing_entries):
            log.error(f'[rust_crate_member]       "{crate}",')
        log.error("[rust_crate_member]   ]")

    # Check for orphaned entries: workspace.members pointing to non-existent crates
    orphaned_entries = workspace_members - rust_crates
    if orphaned_entries:
        log.error(
            "[rust_crate_member] workspace.members entries pointing to non-existent crates:"
        )
        for entry in sorted(orphaned_entries):
            log.error(f"[rust_crate_member]   - {entry}")
        log.error(
            "[rust_crate_member] Remove these entries from Cargo.toml [workspace.members]"
        )

    # If there are any issues, exit with error
    if missing_entries or orphaned_entries:
        sys.exit(1)

    log.info(
        f"[rust_crate_member] ✓ All {len(rust_crates)} Rust crates are in workspace.members"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
