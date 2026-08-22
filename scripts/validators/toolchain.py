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
_CITRY_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry--publish.yml"
_CITRY_LSP_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-lsp--publish.yml"
_CITRY_UI_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-ui--publish.yml"
_PYTHON_TEST_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--tests.yml"
_ROOT_CARGO = REPO_ROOT / "Cargo.toml"
_CORE_BINDING_CARGO = REPO_ROOT / "crates" / "citry_core_py" / "Cargo.toml"
_PYODIDE_CONFIG = REPO_ROOT / "packages" / "py" / "citry_core" / "pyodide-build.json"
_CORE_PYPROJECT = REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml"
_PLAYGROUND_RUNTIME = REPO_ROOT / "docs_site" / "static" / "playground" / "runtime.json"
_PYODIDE_BUILDER = REPO_ROOT / "scripts" / "build_citry_core_pyodide_wheel.py"
_DISTRIBUTION_VERIFIER = REPO_ROOT / "scripts" / "verify_citry_core_distribution.py"
_DOCS_RUST_WORKFLOWS = tuple(
    REPO_ROOT / ".github" / "workflows" / name
    for name in (
        "repo--docs-check.yml",
        "repo--docs-deploy.yml",
        "repo--docs-external-links.yml",
        "repo--docs-lighthouse.yml",
        "repo--docs-release.yml",
    )
)
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
_SCCACHE_ACTION = "mozilla-actions/sccache-action@7d986dd989559c6ecdb630a3fd2557667be217ad"
_RUST_CACHE_ACTION = "Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6"


def check() -> list[str]:
    required = (
        _TOOLCHAIN_FILE,
        _WORKFLOW_FILE,
        _PUBLISH_WORKFLOW,
        _CITRY_PUBLISH_WORKFLOW,
        _CITRY_LSP_PUBLISH_WORKFLOW,
        _CITRY_UI_PUBLISH_WORKFLOW,
        _PYTHON_TEST_WORKFLOW,
        _ROOT_CARGO,
        _CORE_BINDING_CARGO,
        _PYODIDE_CONFIG,
        _CORE_PYPROJECT,
        _PLAYGROUND_RUNTIME,
        _PYODIDE_BUILDER,
        _DISTRIBUTION_VERIFIER,
        *_DOCS_RUST_WORKFLOWS,
    )
    missing = [f"{path} not found" for path in required if not path.exists()]
    if missing:
        return missing

    errors: list[str] = []

    # Each event owns its path list, so a duplicate in one list cannot hide an omission in the other.
    python_test_workflow = _PYTHON_TEST_WORKFLOW.read_text(encoding="utf-8")
    _, pull_request_marker, after_push = python_test_workflow.partition("  pull_request:\n")
    pull_request_section, workflow_dispatch_marker, _ = after_push.partition("  workflow_dispatch:\n")
    event_sections = {
        "push": python_test_workflow.partition("  push:\n")[2].partition("  pull_request:\n")[0],
        "pull_request": pull_request_section if pull_request_marker and workflow_dispatch_marker else "",
    }
    event_path_lists = {
        event: (
            match.group(1).splitlines()
            if (match := re.search(r"(?m)^    paths:\n((?:      - .*\n)+)", section))
            else []
        )
        for event, section in event_sections.items()
    }
    for path in (
        "scripts/verify_citry_ui_distribution.py",
        ".github/workflows/py--citry-ui--publish.yml",
    ):
        marker = f'      - "{path}"'
        for event, path_list in event_path_lists.items():
            if marker not in path_list:
                errors.append(f"py--tests.yml {event} path filters must include {path!r}")

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
    wheel_profile = root_manifest.get("profile", {}).get("release-wheel")
    expected_wheel_profile = {
        "inherits": "release",
        "debug": False,
        "lto": True,
        "codegen-units": 1,
    }
    if wheel_profile != expected_wheel_profile:
        errors.append(f"Cargo release-wheel profile must be {expected_wheel_profile!r}, found {wheel_profile!r}")
    binding_manifest = tomllib.loads(_CORE_BINDING_CARGO.read_text(encoding="utf-8"))
    abi3_feature = binding_manifest.get("features", {}).get("abi3-py310")
    if abi3_feature != ["pyo3/abi3-py310", "pyo3/extension-module"]:
        errors.append("citry_core_py abi3-py310 feature must enable PyO3's stable ABI and extension module")

    docs_toolchain = f"{minimum}.0"
    docs_cache_settings = (
        "shared-key: docs-citry-core-py314",
        "add-job-id-key: false",
        "cache-on-failure: true",
    )
    for workflow_path in _DOCS_RUST_WORKFLOWS:
        workflow = workflow_path.read_text(encoding="utf-8")
        label = workflow_path.relative_to(REPO_ROOT)
        if not re.search(rf'^  RUSTUP_TOOLCHAIN: ["\']{re.escape(docs_toolchain)}["\']$', workflow, re.MULTILINE):
            errors.append(f"{label} must pin docs Rust to the workspace MSRV {docs_toolchain}")
        rust_actions = len(re.findall(r"uses:\s+dtolnay/rust-toolchain@", workflow))
        if workflow.count(f"uses: {_RUST_ACTION}") != rust_actions:
            errors.append(f"every Rust setup in {label} must use the reviewed immutable action commit")
        if workflow.count("toolchain: ${{ env.RUSTUP_TOOLCHAIN }}") != rust_actions:
            errors.append(f"every Rust setup in {label} must select the pinned docs toolchain")
        if workflow.count(f"uses: {_SCCACHE_ACTION}") != rust_actions:
            errors.append(f"every Rust setup in {label} must use the reviewed immutable sccache action")
        for setting in ('SCCACHE_GHA_ENABLED: "true"', 'RUSTC_WRAPPER: "sccache"'):
            if workflow.count(setting) != 1:
                errors.append(f"{label} must set {setting!r} once at workflow scope")
        rust_caches = workflow.count(f"uses: {_RUST_CACHE_ACTION}")
        if rust_caches != rust_actions:
            errors.append(f"every Rust setup in {label} must use the reviewed immutable Rust cache action")
        for setting in docs_cache_settings:
            if workflow.count(setting) != rust_caches:
                errors.append(f"every Rust cache in {label} must set {setting!r}")

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
    for text, pin_label in workflow_pins.items():
        if text not in publish:
            errors.append(f"citry-core publish workflow does not use the configured {pin_label} pin")
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
    if publish.count("--profile release-wheel") != action_count - 1:
        errors.append("every native citry-core wheel action must use the release-wheel Cargo profile")
    if publish.count("--features abi3-py310") != action_count - 1:
        errors.append("every native citry-core wheel action must select the reviewed ABI3 release feature")
    if "--find-interpreter" in publish:
        errors.append("citry-core release builders must select the closed interpreter families explicitly")
    if "/opt/python/" in publish:
        errors.append(
            "containerized citry-core builders must select interpreters by "
            "versioned command name, not architecture-specific /opt/python paths"
        )
    for interpreter_args in (
        "--features abi3-py310 --interpreter python3.10",
        "--features abi3-py310 --interpreter python3.14t pypy3.11",
    ):
        if publish.count(interpreter_args) != 2:
            errors.append(f"Linux and musllinux citry-core builders must each select {interpreter_args!r}")
    profile_setting = "maturin.build-args=--profile release-wheel"
    for script_path in (_PYODIDE_BUILDER, _DISTRIBUTION_VERIFIER):
        if script_path.read_text(encoding="utf-8").count(profile_setting) != 1:
            errors.append(f"{script_path.relative_to(REPO_ROOT)} must select the release-wheel profile once")
    if "skip-existing" in publish or "--clobber" in publish:
        errors.append("citry-core release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "select-qualification:",
        "scripts/select_citry_core_qualification.py",
        "needs: [verify-version, select-qualification]",
        "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
        "verify_citry_core_distribution.py promote",
        "retention-days: 14",
        "PyEmscripten reproducibility build ${{ matrix.copy }}",
        "Require a new PyPI version and GitHub Release",
        "https://pypi.org/pypi/citry-core/${CITRY_CORE_VERSION}/json",
        "releases/tags/$GITHUB_REF_NAME",
    ):
        if marker not in publish:
            errors.append(f"citry-core release immutability preflight is missing {marker!r}")

    citry_publish = _CITRY_PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    if citry_publish.count(release_guard) != 2:
        errors.append("citry publish selection and release jobs must both reject workflow_dispatch refs")
    if citry_publish.count(f"uses: {_PYPI_ACTION}") != 1:
        errors.append("citry Trusted Publishing must use the reviewed immutable action commit")
    if citry_publish.count(f"uses: {_UV_ACTION}") != len(re.findall(r"uses:\s+astral-sh/setup-uv@", citry_publish)):
        errors.append("every citry publish uv action must use the reviewed immutable commit")
    if "skip-existing" in citry_publish or "--clobber" in citry_publish:
        errors.append("citry release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "select-qualification:",
        "--workflow py--citry--publish.yml",
        "--artifact-name verified-citry-distributions",
        "needs: [verify-version, select-qualification]",
        "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
        "--promote-archive qualification.zip",
        "retention-days: 14",
        "Require a new PyPI version and GitHub Release",
        "https://pypi.org/pypi/citry/${CITRY_VERSION}/json",
        "releases/tags/$GITHUB_REF_NAME",
    ):
        if marker not in citry_publish:
            errors.append(f"citry release immutability preflight is missing {marker!r}")

    citry_lsp_publish = _CITRY_LSP_PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    if citry_lsp_publish.count(release_guard) != 2:
        errors.append("citry-lsp publish selection and release jobs must both reject workflow_dispatch refs")
    if citry_lsp_publish.count(f"uses: {_PYPI_ACTION}") != 1:
        errors.append("citry-lsp Trusted Publishing must use the reviewed immutable action commit")
    if citry_lsp_publish.count(f"uses: {_UV_ACTION}") != len(
        re.findall(r"uses:\s+astral-sh/setup-uv@", citry_lsp_publish)
    ):
        errors.append("every citry-lsp publish uv action must use the reviewed immutable commit")
    if "skip-existing" in citry_lsp_publish or "--clobber" in citry_lsp_publish:
        errors.append("citry-lsp release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "select-qualification:",
        "--workflow py--citry-lsp--publish.yml",
        "--artifact-name verified-citry-lsp-distributions",
        "needs: [verify-version, select-qualification]",
        "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
        "--promote-archive qualification.zip",
        "retention-days: 14",
        "Require a new PyPI version and GitHub Release",
        "https://pypi.org/pypi/citry-lsp/${CITRY_LSP_VERSION}/json",
        "releases/tags/$GITHUB_REF_NAME",
    ):
        if marker not in citry_lsp_publish:
            errors.append(f"citry-lsp release immutability preflight is missing {marker!r}")

    citry_ui_publish = _CITRY_UI_PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    if citry_ui_publish.count(release_guard) != 2:
        errors.append("citry-ui publish selection and release jobs must both reject workflow_dispatch refs")
    if citry_ui_publish.count(f"uses: {_PYPI_ACTION}") != 1:
        errors.append("citry-ui Trusted Publishing must use the reviewed immutable action commit")
    if citry_ui_publish.count(f"uses: {_UV_ACTION}") != len(
        re.findall(r"uses:\s+astral-sh/setup-uv@", citry_ui_publish)
    ):
        errors.append("every citry-ui publish uv action must use the reviewed immutable commit")
    if "skip-existing" in citry_ui_publish or "--clobber" in citry_ui_publish:
        errors.append("citry-ui release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "select-qualification:",
        "--workflow py--citry-ui--publish.yml",
        "--artifact-name verified-citry-ui-distributions",
        "needs: [verify-version, select-qualification]",
        "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
        "--promote-archive qualification.zip",
        "retention-days: 14",
        "Require a new PyPI version and GitHub Release",
        "https://pypi.org/pypi/citry-ui/${CITRY_UI_VERSION}/json",
        "releases/tags/$GITHUB_REF_NAME",
    ):
        if marker not in citry_ui_publish:
            errors.append(f"citry-ui release immutability preflight is missing {marker!r}")
    return errors
