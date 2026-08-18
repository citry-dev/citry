"""Keep development, minimum, release, and browser Rust toolchains aligned."""

import json
import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[import-untyped, no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLCHAIN_FILE = REPO_ROOT / "rust-toolchain.toml"
_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "rust--tests.yml"
_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-core--publish.yml"
_ROOT_CARGO = REPO_ROOT / "Cargo.toml"
_PYODIDE_CONFIG = REPO_ROOT / "packages" / "py" / "citry_core" / "pyodide-build.json"
_CORE_PYPROJECT = REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml"
_PLAYGROUND_RUNTIME = REPO_ROOT / "docs_site" / "static" / "playground" / "runtime.json"
_CORE_CRATES = (
    "citry_core_py",
    "citry_html_transform",
    "citry_i18n",
    "citry_template_formatter",
    "citry_template_parser",
    "python_safe_eval",
)
_MATURIN_ACTION = "PyO3/maturin-action@e83996d129638aa358a18fbd1dfb82f0b0fb5d3b"
_RUST_ACTION = "dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772"
_PYPI_ACTION = "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
_UV_ACTION = "astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78"


def check() -> list[str]:
    required = (
        _TOOLCHAIN_FILE,
        _WORKFLOW_FILE,
        _PUBLISH_WORKFLOW,
        _ROOT_CARGO,
        _PYODIDE_CONFIG,
        _CORE_PYPROJECT,
        _PLAYGROUND_RUNTIME,
    )
    missing = [f"{path} not found" for path in required if not path.exists()]
    if missing:
        return missing

    errors: list[str] = []

    channel = tomllib.loads(_TOOLCHAIN_FILE.read_text(encoding="utf-8")).get("toolchain", {}).get("channel", "")

    content = _WORKFLOW_FILE.read_text(encoding="utf-8")
    action = re.search(r"dtolnay/rust-toolchain", content)
    if action is None:
        errors.append("could not find 'dtolnay/rust-toolchain' in rust--tests.yml")
    else:
        pinned = re.search(r"toolchain:\s*(\S+)", content[action.end() :])
        if pinned is None:
            errors.append("could not find a 'toolchain:' value after 'dtolnay/rust-toolchain' in rust--tests.yml")
        else:
            workflow_toolchain = pinned.group(1).strip("\"'")
            if channel != workflow_toolchain:
                errors.append(
                    f"toolchain mismatch: rust-toolchain.toml='{channel}', rust--tests.yml='{workflow_toolchain}'"
                )

    root_manifest = tomllib.loads(_ROOT_CARGO.read_text(encoding="utf-8"))
    minimum = root_manifest.get("workspace", {}).get("package", {}).get("rust-version")
    if minimum != "1.95":
        errors.append(f"Cargo workspace rust-version must be '1.95', found {minimum!r}")
    for crate in _CORE_CRATES:
        manifest_path = REPO_ROOT / "crates" / crate / "Cargo.toml"
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("package", {}).get("rust-version") != {"workspace": True}:
            errors.append(f"{manifest_path.relative_to(REPO_ROOT)} must inherit workspace rust-version")

    pyodide: dict[str, object] = json.loads(_PYODIDE_CONFIG.read_text(encoding="utf-8"))
    if pyodide.get("rust") != f"{minimum}.0":
        errors.append(f"Pyodide Rust pin {pyodide.get('rust')!r} does not match Cargo minimum {minimum!r}")
    runtime: dict[str, object] = json.loads(_PLAYGROUND_RUNTIME.read_text(encoding="utf-8"))
    runtime_pyodide = runtime.get("pyodide", {})
    if isinstance(runtime_pyodide, dict):
        for name in ("version", "python"):
            config_name = "pyodide" if name == "version" else name
            if pyodide.get(config_name) != runtime_pyodide.get(name):
                errors.append(
                    f"Pyodide build {config_name}={pyodide.get(config_name)!r} does not match "
                    f"playground {name}={runtime_pyodide.get(name)!r}"
                )

    publish = _PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    expected_env = {
        "CITRY_CORE_RUST_TOOLCHAIN": f"{minimum}.0",
        "CITRY_CORE_EMSCRIPTEN_VERSION": str(pyodide.get("emscripten")),
        "MATURIN_VERSION": str(pyodide.get("maturin")),
    }
    for name, value in expected_env.items():
        if not re.search(rf"^  {name}: [\"']?{re.escape(value)}[\"']?$", publish, re.MULTILINE):
            errors.append(f"citry-core publish workflow must set {name}={value}")
    workflow_pins = {
        f'node-version: "{pyodide.get("node")}"': "Node",
        f'version: "{pyodide.get("uv")}"': "uv",
        f"pyodide-cli=={pyodide.get('pyodide_cli')}": "pyodide-cli",
        f"pyodide-build=={pyodide.get('pyodide_build')}": "pyodide-build",
        f"pyodide xbuildenv install {pyodide.get('pyodide')}": "Pyodide xbuild environment",
        f"twine=={pyodide.get('twine')}": "Twine",
    }
    for text, label in workflow_pins.items():
        if text not in publish:
            errors.append(f"citry-core publish workflow does not use the configured {label} pin")
    release_guard = "if: ${{ github.event_name == 'push' && startsWith(github.ref, 'refs/tags/') }}"
    if release_guard not in publish:
        errors.append("citry-core release job must reject every workflow_dispatch ref, including tags")
    action_count = publish.count(f"uses: {_MATURIN_ACTION}")
    if action_count != len(re.findall(r"uses:\s+PyO3/maturin-action@", publish)):
        errors.append("every citry-core Maturin action must use the reviewed immutable commit")
    if publish.count(f"uses: {_RUST_ACTION}") != len(re.findall(r"uses:\s+dtolnay/rust-toolchain@", publish)):
        errors.append("every citry-core Rust action must use the reviewed immutable commit")
    if publish.count(f"uses: {_PYPI_ACTION}") != 1:
        errors.append("citry-core Trusted Publishing must use the reviewed immutable action commit")
    if publish.count(f"uses: {_UV_ACTION}") != len(re.findall(r"uses:\s+astral-sh/setup-uv@", publish)):
        errors.append("every citry-core uv action must use the reviewed immutable commit")
    for setting in (
        "rust-toolchain: ${{ env.CITRY_CORE_RUST_TOOLCHAIN }}",
        "maturin-version: ${{ env.MATURIN_VERSION }}",
    ):
        if publish.count(setting) != action_count:
            errors.append(f"all {action_count} citry-core maturin actions must set {setting!r}")
    core_pyproject = tomllib.loads(_CORE_PYPROJECT.read_text(encoding="utf-8"))
    if core_pyproject.get("build-system", {}).get("requires") != [f"maturin=={pyodide.get('maturin')}"]:
        errors.append("citry-core build-system must pin the release-owned Maturin version")
    if core_pyproject.get("tool", {}).get("maturin", {}).get("locked") is not True:
        errors.append("citry-core tool.maturin.locked must be true for wheel and sdist builds")
    if core_pyproject.get("tool", {}).get("maturin", {}).get("strip") is not True:
        errors.append("citry-core tool.maturin.strip must be true for release-size artifacts")
    if publish.count("--locked") != action_count - 1:
        errors.append("every citry-core wheel action must pass --locked")
    if "skip-existing" in publish or "--clobber" in publish:
        errors.append("citry-core release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "Require a new PyPI version and GitHub Release",
        "https://pypi.org/pypi/citry-core/${CITRY_CORE_VERSION}/json",
        'gh release view "$GITHUB_REF_NAME"',
    ):
        if marker not in publish:
            errors.append(f"citry-core release immutability preflight is missing {marker!r}")
    return errors
