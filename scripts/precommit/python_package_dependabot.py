#!/usr/bin/env python3
"""
Check that each Python package in `packages/py/` has a corresponding entry
in `.github/dependabot.yml`, and that all dependabot entries point to existing packages.
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check that Python packages in `packages/py/` have corresponding Dependabot entries"
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


def extract_dependabot_directories(dependabot_content: str) -> set[str]:
    """Extract all 'directory' values from `dependabot.yml` that point to `packages/py/`"""
    directories = set()

    # Pattern to match directory entries that point to packages/py/
    # We want to capture the directory value after "directory:"
    pattern = r'directory:\s*["\']?(packages/py/[^"\'\s]+)["\']?'

    for match in re.finditer(pattern, dependabot_content):
        directory = match.group(1)
        directories.add(directory)
        log.debug(f"[python_package_dependabot] Found Dependabot entry: {directory}")

    return directories


def find_python_packages(packages_dir: Path) -> set[str]:
    """Find all Python packages in packages/py/ directory."""
    packages = set()

    if not packages_dir.exists():
        log.error(f"[python_package_dependabot] Directory not found: {packages_dir}")
        return packages

    for item in packages_dir.iterdir():
        if item.is_dir():
            # Check if it looks like a Python package (has pyproject.toml or __init__.py)
            if (item / "pyproject.toml").exists() or (item / "__init__.py").exists():
                package_path = f"packages/py/{item.name}"
                packages.add(package_path)
                log.debug(
                    f"[python_package_dependabot] Found Python package: {package_path}"
                )

    return packages


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
            f"[python_package_dependabot] Could not find repository root. Expected Cargo.toml or .git in {repo_root}"
        )
        sys.exit(1)

    # Read .github/dependabot.yml
    dependabot_file = repo_root / ".github" / "dependabot.yml"
    if not dependabot_file.exists():
        log.error(f"[python_package_dependabot] {dependabot_file} not found")
        sys.exit(1)

    log.debug(f"[python_package_dependabot] Reading {dependabot_file}...")
    dependabot_content = dependabot_file.read_text()

    # Extract directories from dependabot.yml
    dependabot_directories = extract_dependabot_directories(dependabot_content)
    log.debug(
        f"[python_package_dependabot] Found {len(dependabot_directories)} Dependabot entries for `packages/py/`"
    )

    # Find all Python packages in packages/py/
    packages_dir = repo_root / "packages" / "py"
    python_packages = find_python_packages(packages_dir)
    log.debug(
        f"[python_package_dependabot] Found {len(python_packages)} Python packages in `packages/py/`"
    )

    # Check for missing entries: packages without Dependabot entries
    missing_entries = python_packages - dependabot_directories
    if missing_entries:
        log.error(
            "[python_package_dependabot] Python packages missing from Dependabot configuration:"
        )
        for package in sorted(missing_entries):
            log.error(f"[python_package_dependabot]   - {package}")
        log.error(
            "[python_package_dependabot] Add entries to .github/dependabot.yml like:"
        )
        log.error('[python_package_dependabot]   - package-ecosystem: "pip"')
        for package in sorted(missing_entries):
            log.error(f'[python_package_dependabot]     directory: "{package}"')

    # Check for orphaned entries: Dependabot entries pointing to non-existent packages
    orphaned_entries = dependabot_directories - python_packages
    if orphaned_entries:
        log.error(
            "[python_package_dependabot] Dependabot entries pointing to non-existent packages:"
        )
        for entry in sorted(orphaned_entries):
            log.error(f"[python_package_dependabot]   - {entry}")
        log.error(
            "[python_package_dependabot] Remove these entries from .github/dependabot.yml"
        )

    # If there are any issues, exit with error
    if missing_entries or orphaned_entries:
        sys.exit(1)

    log.info(
        f"[python_package_dependabot] ✓ All {len(python_packages)} Python packages have Dependabot entries"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
