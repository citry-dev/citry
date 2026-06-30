"""
Bindings consistency: the citry_core Python package and the citry_core_py Rust
crate must stay in step. The maturin module-name in the package's pyproject names
the Rust extension module; that name must match the #[pymodule] function, a
matching <rust_module>.pyi stub must exist, and every PyModule::new submodule
registered in the crate's lib.rs must have a `class <name>:` in the stub (and
vice versa).
"""

import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml"

_PYMODULE_FN_RE = re.compile(r"#\[pymodule\]\s*\n\s*fn\s+(\w+)")
_PYMODULE_NEW_RE = re.compile(r'PyModule::new\([^,]+,\s*["\']([^"\']+)["\']\)')
# Top-level `class <name>:` only (the submodule namespaces); the AST classes are
# nested inside them and intentionally not matched.
_STUB_CLASS_RE = re.compile(r"^class\s+(\w+)\s*[:(]", re.MULTILINE)


def check() -> list[str]:
    if not _PYPROJECT.exists():
        return [f"{_PYPROJECT} not found"]

    maturin = tomllib.loads(_PYPROJECT.read_text()).get("tool", {}).get("maturin", {})
    module_name = maturin.get("module-name")
    manifest_path = maturin.get("manifest-path", ".")
    if not module_name:
        return ["[tool.maturin] module-name is missing in packages/py/citry_core/pyproject.toml"]
    if "." not in module_name:
        return [f"module-name must be '<package>.<rust_module>', got '{module_name}'"]

    package_name, rust_module = module_name.split(".", 1)

    candidates = (_PYPROJECT.parent / "src" / package_name, _PYPROJECT.parent / package_name)
    package_dir = next((d for d in candidates if d.exists()), None)
    if package_dir is None:
        return [f"Python package directory for '{package_name}' not found next to {_PYPROJECT.name}"]

    lib_rs = (_PYPROJECT.parent / manifest_path).resolve().parent / "src" / "lib.rs"
    if not lib_rs.exists():
        return [f"Rust crate lib.rs not found at {lib_rs} (from manifest-path '{manifest_path}')"]

    lib_src = lib_rs.read_text()
    problems: list[str] = []

    pymodule_fn = _PYMODULE_FN_RE.search(lib_src)
    if pymodule_fn is None:
        return [f"could not find a #[pymodule] function in {lib_rs}"]
    if pymodule_fn.group(1) != rust_module:
        problems.append(
            f"module-name expects the #[pymodule] function to be '{rust_module}', but it is '{pymodule_fn.group(1)}'",
        )

    stub = package_dir / f"{rust_module}.pyi"
    if not stub.exists():
        problems.append(f"type stub '{stub.name}' not found in {package_dir}")
        return problems

    rust_modules = set(_PYMODULE_NEW_RE.findall(lib_src))
    stub_classes = set(_STUB_CLASS_RE.findall(stub.read_text()))
    for module in sorted(rust_modules - stub_classes):
        problems.append(
            f"Rust submodule '{module}' is registered in lib.rs but has no `class {module}:` in {stub.name}"
        )
    for klass in sorted(stub_classes - rust_modules):
        problems.append(f"`class {klass}:` in {stub.name} has no matching PyModule submodule in lib.rs")
    return problems
