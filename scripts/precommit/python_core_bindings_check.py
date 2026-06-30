#!/usr/bin/env python3
"""
Check that the citry_core Python package correctly uses the citry_core_py Rust crate bindings.

These two packages are tightly coupled, but defined in different places.

This script checks that they are in sync.

This script:
1. Reads `manifest-path` from `packages/py/citry_core/pyproject.toml` to locate the Rust crate
2. Reads `module-name` from `packages/py/citry_core/pyproject.toml` and verifies:
   - The Python package directory exists (checks both `src/<package_name>/` and `<package_name>/` layouts)
   - The Rust `#[pymodule]` function name matches the `<rust_module_name>` part of module-name
   - The type stub file `<rust_module_name>.pyi` exists in the Python package directory
3. Extracts module names from `PyModule::new()` calls in the Rust crate's `src/lib.rs`
4. Checks `<rust_module_name>.pyi` for class definitions like `class module_name:`
5. Verifies that all Rust modules have corresponding class definitions in the type stub file
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
        log.exception("[python_core_bindings_check] tomllib (Python 3.11+) or tomli package required")
        log.exception("[python_core_bindings_check] Install with: pip install tomli")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that Python package correctly uses Rust crate bindings")
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


def extract_pymodule_names(lib_rs_content: str) -> set[str]:
    """Extract module names from PyModule::new() calls in lib.rs."""
    modules = set()

    # Pattern to match PyModule::new(m.py(), "module_name")
    # We want to capture the string literal (module name) inside PyModule::new
    pattern = r'PyModule::new\([^,]+,\s*["\']([^"\']+)["\']\)'

    for match in re.finditer(pattern, lib_rs_content):
        module_name = match.group(1)
        modules.add(module_name)
        log.debug(f"[python_core_bindings_check] Found PyModule: {module_name}")

    return modules


def extract_rust_pyi_classes(rust_pyi_content: str) -> set[str]:
    """
    Extract class names from rust.pyi like `class module_name:`.
    Returns a set of class names.
    """
    classes = set()

    # Pattern to match: `class module_name:`
    # Handles various whitespace and optional type hints
    pattern = r"^class\s+(\w+)\s*[:\(]"

    for line_num, line in enumerate(rust_pyi_content.splitlines(), 1):
        match = re.search(pattern, line)
        if match:
            class_name = match.group(1)
            classes.add(class_name)
            log.debug(f"[python_core_bindings_check] Found class: {class_name} (line {line_num})")

    return classes


def extract_pymodule_function_name(lib_rs_content: str) -> str | None:
    """
    Extract the function name from `#[pymodule]` followed by `fn function_name`.
    Returns the function name or None if not found.
    """
    # Pattern to match: #[pymodule] followed by fn function_name
    # This handles multi-line cases and various whitespace
    pattern = r"#\[pymodule\]\s*\n\s*fn\s+(\w+)"

    match = re.search(pattern, lib_rs_content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def main() -> int:
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
            f"[python_core_bindings_check] Could not find repository root. Expected Cargo.toml or .git in {repo_root}"
        )
        sys.exit(1)

    # Read packages/py/citry_core/pyproject.toml
    pyproject_toml_file = repo_root / "packages" / "py" / "citry_core" / "pyproject.toml"
    if not pyproject_toml_file.exists():
        log.error(f"[python_core_bindings_check] {pyproject_toml_file} not found")
        sys.exit(1)

    log.debug(f"[python_core_bindings_check] Reading {pyproject_toml_file}...")
    pyproject_toml_content = pyproject_toml_file.read_bytes()
    pyproject_toml = tomllib.loads(pyproject_toml_content.decode("utf-8"))

    # Extract manifest-path from tool.maturin
    maturin_config = pyproject_toml.get("tool", {}).get("maturin", {})
    manifest_path = maturin_config.get("manifest-path", ".")
    module_name = maturin_config.get("module-name")

    if not module_name:
        log.error("[python_core_bindings_check] 'module-name' not found in [tool.maturin] section of pyproject.toml")
        sys.exit(1)

    # Split module-name into python_package_name.rust_module_name
    if "." not in module_name:
        log.error(
            f"[python_core_bindings_check] 'module-name' must be in format '<python_package_name>.<rust_module_name>',"
            f" got: {module_name}"
        )
        sys.exit(1)

    python_package_name, rust_module_name = module_name.split(".", 1)
    log.debug(
        f"[python_core_bindings_check] Parsed module-name: python_package='{python_package_name}',"
        f" rust_module='{rust_module_name}'"
    )

    # Check that the Python package directory exists
    # Try src layout first, then fall back to non-src layout
    python_package_dir_src = repo_root / "packages" / "py" / "citry_core" / "src" / python_package_name
    python_package_dir_non_src = repo_root / "packages" / "py" / "citry_core" / python_package_name

    if python_package_dir_src.exists():
        python_package_dir = python_package_dir_src
        log.debug(f"[python_core_bindings_check] Found Python package in src layout: {python_package_dir}")
    elif python_package_dir_non_src.exists():
        python_package_dir = python_package_dir_non_src
        log.debug(f"[python_core_bindings_check] Found Python package in non-src layout: {python_package_dir}")
    else:
        log.error("[python_core_bindings_check] Python package directory not found. Checked:")
        log.error(f"[python_core_bindings_check]   - {python_package_dir_src}")
        log.error(f"[python_core_bindings_check]   - {python_package_dir_non_src}")
        log.error(
            f"[python_core_bindings_check] Expected directory matching module-name '{module_name}'"
            f" (package: '{python_package_name}')"
        )
        sys.exit(1)

    # Resolve the Rust crate's Cargo.toml path
    # manifest-path is relative to pyproject.toml's directory
    pyproject_dir = pyproject_toml_file.parent
    cargo_toml_file = (pyproject_dir / manifest_path).resolve()

    if not cargo_toml_file.exists():
        log.error(f"[python_core_bindings_check] Rust crate Cargo.toml not found: {cargo_toml_file}")
        log.error(f"[python_core_bindings_check] Checked manifest-path '{manifest_path}' relative to {pyproject_dir}")
        sys.exit(1)

    # Find lib.rs relative to the Cargo.toml directory
    cargo_toml_dir = cargo_toml_file.parent
    lib_rs_file = cargo_toml_dir / "src" / "lib.rs"

    if not lib_rs_file.exists():
        log.error(f"[python_core_bindings_check] {lib_rs_file} not found")
        sys.exit(1)

    log.debug(f"[python_core_bindings_check] Reading {lib_rs_file}...")
    lib_rs_content = lib_rs_file.read_text()

    # Check that the pymodule function name matches the rust_module_name
    pymodule_function = extract_pymodule_function_name(lib_rs_content)
    if not pymodule_function:
        log.error(f"[python_core_bindings_check] Could not find #[pymodule] function in {lib_rs_file}")
        sys.exit(1)

    if pymodule_function != rust_module_name:
        log.error(
            f"[python_core_bindings_check] Mismatch: module-name specifies rust_module='{rust_module_name}',"
            f" but Rust #[pymodule] function is named '{pymodule_function}'"
        )
        log.error(
            f"[python_core_bindings_check] Either update module-name in pyproject.toml to "
            f"'{python_package_name}.{pymodule_function}' or rename the Rust function to '{rust_module_name}'"
        )
        sys.exit(1)

    log.debug(
        f"[python_core_bindings_check] Verified pymodule function name '{pymodule_function}' matches module-name"
    )

    # Check that the type stub file exists (filename must match rust_module_name)
    rust_pyi_file = python_package_dir / f"{rust_module_name}.pyi"
    if not rust_pyi_file.exists():
        log.error(f"[python_core_bindings_check] Type stub file not found: {rust_pyi_file}")
        log.error(
            f"[python_core_bindings_check] Expected file '{rust_module_name}.pyi' to match module-name '{module_name}'"
        )
        sys.exit(1)

    log.debug(f"[python_core_bindings_check] Reading {rust_pyi_file}...")
    rust_pyi_content = rust_pyi_file.read_text()

    # Extract module names from Rust code
    rust_modules = extract_pymodule_names(lib_rs_content)
    log.debug(f"[python_core_bindings_check] Found {len(rust_modules)} PyModule definitions in Rust")

    # Extract class definitions from type stubs
    rust_pyi_classes = extract_rust_pyi_classes(rust_pyi_content)
    log.debug(f"[python_core_bindings_check] Found {len(rust_pyi_classes)} class definitions in rust.pyi")

    # Check for issues
    errors = []

    # 1. Check that all Rust modules have corresponding class definitions in the type stub file
    missing_pyi_classes = rust_modules - rust_pyi_classes
    if missing_pyi_classes:
        for module in sorted(missing_pyi_classes):
            errors.append(
                f"Rust module '{module}' is defined in lib.rs but missing class definition in {rust_pyi_file.name}"
            )

    # 2. Check that all class definitions in the type stub file correspond to actual Rust modules
    orphaned_pyi_classes = rust_pyi_classes - rust_modules
    if orphaned_pyi_classes:
        for class_name in sorted(orphaned_pyi_classes):
            errors.append(
                f"Class '{class_name}' is defined in {rust_pyi_file.name} but module '{class_name}'"
                f" is not defined in Rust (lib.rs)"
            )

    # Report errors
    if errors:
        log.error("[python_core_bindings_check] Python-Rust bindings mismatch detected:")
        for error in errors:
            log.error(f"[python_core_bindings_check]   - {error}")
        log.error(f"[python_core_bindings_check] Fix the mismatches in {rust_pyi_file}")
        sys.exit(1)

    log.info(
        f"[python_core_bindings_check] ✓ All {len(rust_modules)} Rust modules are correctly bound in Python"
        f" ({rust_pyi_file.name})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
