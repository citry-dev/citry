"""Keep development, minimum, release, and browser Rust toolchains aligned."""

import json
import re
from pathlib import Path

import tomllib
import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLCHAIN_FILE = REPO_ROOT / "rust-toolchain.toml"
_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-core--publish.yml"
_CITRY_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry--publish.yml"
_CITRY_LSP_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-lsp--publish.yml"
_CITRY_UI_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--citry-ui--publish.yml"
_PYGMENTS_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--pygments-citry--publish.yml"
_VSCODE_PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "vscode--citry--publish.yml"
_EXAMPLES_TEST_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--examples--tests.yml"
_PYTHON_TEST_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "py--tests.yml"
_ROOT_CARGO = REPO_ROOT / "Cargo.toml"
_CORE_BINDING_CARGO = REPO_ROOT / "crates" / "citry_core_py" / "Cargo.toml"
_PYODIDE_CONFIG = REPO_ROOT / "packages" / "py" / "citry_core" / "pyodide-build.json"
_CORE_PYPROJECT = REPO_ROOT / "packages" / "py" / "citry_core" / "pyproject.toml"
_PLAYGROUND_RUNTIME = REPO_ROOT / "docs_site" / "static" / "playground" / "runtime.json"
_PYODIDE_BUILDER = REPO_ROOT / "scripts" / "build_citry_core_pyodide_wheel.py"
_DISTRIBUTION_VERIFIER = REPO_ROOT / "scripts" / "verify_citry_core_distribution.py"
_PLAYGROUND_RELEASE_VERIFIER = REPO_ROOT / "scripts" / "verify_playground_release.py"
_DOCS_RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "repo--docs-release.yml"
_RELEASE_CANDIDATE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "repo--release-candidate.yml"
_RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "repo--release.yml"
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
_RUST_ACTION = "dtolnay/rust-toolchain@683b588c487a69d01f6c6ddf40f036ff682cc2c8"
_PYPI_ACTION = "pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086"
_UV_ACTION = "astral-sh/setup-uv@07a047e608db84b3d8c06cd9a7c7dcc9c355c18e"
_SCCACHE_ACTION = "mozilla-actions/sccache-action@fc920bf0ec8de6ee65d409111f7ec508035751ba"
_RUST_CACHE_ACTION = "Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6"
_PNPM_ACTION = "pnpm/action-setup@0977fd99725f1db4007ccb2928dbb4e90d06cc86"


def check() -> list[str]:
    required = (
        _TOOLCHAIN_FILE,
        _PUBLISH_WORKFLOW,
        _CITRY_PUBLISH_WORKFLOW,
        _CITRY_LSP_PUBLISH_WORKFLOW,
        _CITRY_UI_PUBLISH_WORKFLOW,
        _PYGMENTS_PUBLISH_WORKFLOW,
        _VSCODE_PUBLISH_WORKFLOW,
        _EXAMPLES_TEST_WORKFLOW,
        _PYTHON_TEST_WORKFLOW,
        _ROOT_CARGO,
        _CORE_BINDING_CARGO,
        _PYODIDE_CONFIG,
        _CORE_PYPROJECT,
        _PLAYGROUND_RUNTIME,
        _PYODIDE_BUILDER,
        _DISTRIBUTION_VERIFIER,
        _PLAYGROUND_RELEASE_VERIFIER,
        _RELEASE_CANDIDATE_WORKFLOW,
        _RELEASE_WORKFLOW,
        *_DOCS_RUST_WORKFLOWS,
    )
    missing = [f"{path} not found" for path in required if not path.exists()]
    if missing:
        return missing

    errors: list[str] = []

    # A push is filtered by the trigger's path list, and a pull request by the
    # `changes` job's PYTHON_INPUTS list, so each list is checked on its own:
    # a duplicate in one cannot hide an omission in the other.
    python_test_workflow = yaml.safe_load(_PYTHON_TEST_WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML reads the Actions key `on` as the boolean True.
    triggers = python_test_workflow.get(True) or python_test_workflow.get("on") or {}
    changes_steps = python_test_workflow.get("jobs", {}).get("changes", {}).get("steps", [])
    event_path_lists = {
        "on.push.paths": (triggers.get("push") or {}).get("paths", []),
        "jobs.changes PYTHON_INPUTS": [
            line.strip()
            for step in changes_steps
            for line in step.get("env", {}).get("PYTHON_INPUTS", "").splitlines()
            if line.strip()
        ],
    }
    for path in (
        "scripts/verify_citry_ui_distribution.py",
        ".github/workflows/py--citry-ui--publish.yml",
    ):
        for label, path_list in event_path_lists.items():
            if path not in path_list:
                errors.append(f"py--tests.yml {label} must include {path!r}")

    errors.extend(nightly_pin_errors(REPO_ROOT))
    errors.extend(selected_toolchain_errors(REPO_ROOT))

    root_manifest = tomllib.loads(_ROOT_CARGO.read_text(encoding="utf-8"))
    minimum = root_manifest.get("workspace", {}).get("package", {}).get("rust-version")
    if minimum != "1.96":
        errors.append(f"Cargo workspace rust-version must be '1.96', found {minimum!r}")
    for crate in _CORE_CRATES:
        manifest_path = REPO_ROOT / "crates" / crate / "Cargo.toml"
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("package", {}).get("rust-version") != {"workspace": True}:
            errors.append(f"{manifest_path.relative_to(REPO_ROOT).as_posix()} must inherit workspace rust-version")
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
    abi3_feature = binding_manifest.get("features", {}).get("abi3-py311")
    if abi3_feature != ["pyo3/abi3-py311", "pyo3/extension-module"]:
        errors.append("citry_core_py abi3-py311 feature must enable PyO3's stable ABI and extension module")

    docs_toolchain = f"{minimum}.0"
    docs_cache_settings = (
        "shared-key: docs-citry-core-py314",
        "add-job-id-key: false",
        "cache-on-failure: true",
    )
    for workflow_path in _DOCS_RUST_WORKFLOWS:
        workflow = workflow_path.read_text(encoding="utf-8")
        label = workflow_path.relative_to(REPO_ROOT).as_posix()
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
    # The citry-core build settings already record the uv release, so every
    # other pin is compared with that one value and moves in the same change.
    uv_pin = pyodide.get("uv")
    # Without a recorded version there is nothing to compare the pins with.
    if not isinstance(uv_pin, str):
        errors.append(f"{_PYODIDE_CONFIG.relative_to(REPO_ROOT).as_posix()} must record the uv version under 'uv'")
    # The example projects ship their CI workflow to users who copy them, so
    # they use the same reviewed setup-uv commit as the release workflows.
    example_workflows = sorted(REPO_ROOT.glob("examples/*/*/.github/workflows/check.yml"))
    for workflow_path in (
        _EXAMPLES_TEST_WORKFLOW,
        _DOCS_RELEASE_WORKFLOW.parent / "repo--docs-check.yml",
        _DOCS_RELEASE_WORKFLOW,
        *example_workflows,
    ):
        workflow = workflow_path.read_text(encoding="utf-8")
        label = workflow_path.relative_to(REPO_ROOT).as_posix()
        uv_actions = len(re.findall(r"uses:\s+astral-sh/setup-uv@", workflow))
        if workflow.count(f"uses: {_UV_ACTION}") != uv_actions:
            errors.append(f"every uv setup in {label} must use {_UV_ACTION}")
        pnpm_actions = len(re.findall(r"uses:\s+pnpm/action-setup@", workflow))
        if workflow.count(f"uses: {_PNPM_ACTION}") != pnpm_actions:
            errors.append(f"every pnpm setup in {label} must use {_PNPM_ACTION}")
    if isinstance(uv_pin, str):
        errors.extend(pinned_action_errors(REPO_ROOT, uv_pin))

    examples_workflow = _EXAMPLES_TEST_WORKFLOW.read_text(encoding="utf-8")
    examples_rust_actions = len(re.findall(r"uses:\s+dtolnay/rust-toolchain@", examples_workflow))
    if examples_workflow.count(f"uses: {_RUST_ACTION}") != examples_rust_actions:
        errors.append("every examples evidence Rust setup must use the reviewed immutable action commit")
    if not re.search(rf'^  RUSTUP_TOOLCHAIN: ["\']{re.escape(docs_toolchain)}["\']$', examples_workflow, re.MULTILINE):
        errors.append(f"{_EXAMPLES_TEST_WORKFLOW.name} must pin examples Rust to the workspace MSRV {docs_toolchain}")
    if examples_workflow.count("toolchain: ${{ env.RUSTUP_TOOLCHAIN }}") != examples_rust_actions:
        errors.append("every examples evidence Rust setup must select the pinned RUSTUP_TOOLCHAIN")
    examples_rust_caches = len(re.findall(r"uses:\s+Swatinem/rust-cache@", examples_workflow))
    if examples_workflow.count(f"uses: {_RUST_CACHE_ACTION}") != examples_rust_caches:
        errors.append("every examples evidence Rust cache must use the reviewed immutable action commit")

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
    if publish.count('SOURCE_DATE_EPOCH: "315532800"') != 1:
        errors.append("citry-core qualification must normalize release archive timestamps")
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
    if "  push:\n    tags:" in publish:
        errors.append("package publishers must not accept release tags as an entry point")
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
    if publish.count("--features abi3-py311") != action_count - 1:
        errors.append("every native citry-core wheel action must select the reviewed ABI3 release feature")
    if "--find-interpreter" in publish:
        errors.append("citry-core release builders must select the closed interpreter families explicitly")
    if "/opt/python/" in publish:
        errors.append(
            "containerized citry-core builders must select interpreters by "
            "versioned command name, not architecture-specific /opt/python paths"
        )
    for interpreter_args in (
        "--features abi3-py311 --interpreter python3.11",
        "--features abi3-py311 --interpreter python3.14t python3.15t pypy3.11",
    ):
        if publish.count(interpreter_args) != 2:
            errors.append(f"Linux and musllinux citry-core builders must each select {interpreter_args!r}")
    profile_setting = "maturin.build-args=--profile release-wheel"
    for script_path in (_PYODIDE_BUILDER, _DISTRIBUTION_VERIFIER):
        if script_path.read_text(encoding="utf-8").count(profile_setting) != 1:
            script_label = script_path.relative_to(REPO_ROOT).as_posix()
            errors.append(f"{script_label} must select the release-wheel profile once")
    if "skip-existing" in publish or "--clobber" in publish:
        errors.append("citry-core release retries must fail closed instead of replacing or skipping artifacts")
    for marker in (
        "operation:",
        "if: ${{ inputs.operation == 'promote' }}",
        "verified-citry-core-distributions",
        "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
        "verify_citry_core_distribution.py promote",
        "retention-days: 30",
        "PyEmscripten reproducibility build ${{ matrix.copy }}",
        "scripts/pypi_release.py",
        "scripts/verify_playground_release.py",
        "if: steps.public-state.outputs.publish == 'true'",
        "RELEASE_TAG: citry-core@${{ needs.verify-version.outputs.version }}",
    ):
        if marker not in publish:
            errors.append(f"citry-core controller release contract is missing {marker!r}")

    publish_workflows = {
        "citry": _CITRY_PUBLISH_WORKFLOW.read_text(encoding="utf-8"),
        "citry-lsp": _CITRY_LSP_PUBLISH_WORKFLOW.read_text(encoding="utf-8"),
        "citry-ui": _CITRY_UI_PUBLISH_WORKFLOW.read_text(encoding="utf-8"),
    }
    for package, workflow in publish_workflows.items():
        if workflow.count('SOURCE_DATE_EPOCH: "315532800"') != 1:
            errors.append(f"{package} qualification must normalize release archive timestamps")
        if "  push:\n    tags:" in workflow:
            errors.append(f"{package} publisher must not accept release tags as an entry point")
        if workflow.count(f"uses: {_PYPI_ACTION}") != 1:
            errors.append(f"{package} Trusted Publishing must use the reviewed immutable action commit")
        if workflow.count(f"uses: {_UV_ACTION}") != len(re.findall(r"uses:\s+astral-sh/setup-uv@", workflow)):
            errors.append(f"every {package} publish uv action must use the reviewed immutable commit")
        for marker in (
            "operation:",
            "if: ${{ inputs.operation == 'qualify' }}",
            "if: ${{ inputs.operation == 'promote' }}",
            "qualification_artifact_digest:",
            "actions/artifacts/${{ needs.select-qualification.outputs.artifact_id }}/zip",
            "--promote-archive qualification.zip",
            "retention-days: 30",
            "scripts/pypi_release.py",
            "if: steps.public-state.outputs.publish == 'true'",
            "Create or verify the final annotated tag",
        ):
            if marker not in workflow:
                errors.append(f"{package} controller release contract is missing {marker!r}")

    for package, workflow_path in (
        ("pygments-citry", _PYGMENTS_PUBLISH_WORKFLOW),
        ("vscode-citry", _VSCODE_PUBLISH_WORKFLOW),
    ):
        workflow = workflow_path.read_text(encoding="utf-8")
        if package == "pygments-citry" and workflow.count('SOURCE_DATE_EPOCH: "315532800"') != 1:
            errors.append("pygments-citry qualification must normalize release archive timestamps")
        if "  push:\n    tags:" in workflow:
            errors.append(f"{package} publisher must not accept release tags as an entry point")
        for marker in (
            "operation:",
            "if: ${{ inputs.operation == 'qualify' }}",
            "if: ${{ inputs.operation == 'promote' }}",
            "qualification_artifact_digest:",
            "retention-days: 30",
            "Create or verify the final annotated tag",
        ):
            if marker not in workflow:
                errors.append(f"{package} controller release contract is missing {marker!r}")

    citry_publish = publish_workflows["citry"]
    for marker in (
        "candidate-citry-core-wheel",
        "contains(inputs.workspace_dependencies, 'citry-core')",
        "RELEASE_TAG: citry@${{ needs.verify-version.outputs.version }}",
        "scripts/verify_playground_release.py",
    ):
        if marker not in citry_publish:
            errors.append(f"citry candidate dependency or closeout contract is missing {marker!r}")
    if "scripts/verify_playground_release.py" not in publish_workflows["citry-ui"]:
        errors.append("citry-ui qualification must verify its selected playground wheel")

    docs_release = _DOCS_RELEASE_WORKFLOW.read_text(encoding="utf-8")
    if "  push:\n    tags:" in docs_release:
        errors.append("Citry docs release must be dispatched by the Citry publisher, not by a manually pushed tag")
    release_gate = "Require the completed Citry GitHub Release"
    snapshot = "Build the version snapshot"
    for marker in (
        release_gate,
        'gh api "repos/$GITHUB_REPOSITORY/releases/tags/$REF_NAME"',
        snapshot,
    ):
        if marker not in docs_release:
            errors.append(f"Citry docs release gate is missing {marker!r}")
    if docs_release.find(release_gate) > docs_release.find(snapshot):
        errors.append("Citry docs must require the final GitHub Release before committing its version snapshot")

    candidate_workflow = _RELEASE_CANDIDATE_WORKFLOW.read_text(encoding="utf-8")
    release_workflow = _RELEASE_WORKFLOW.read_text(encoding="utf-8")
    if "gh workflow run repo--docs-release.yml" not in release_workflow:
        errors.append("The release controller must start site updates after publishing all packages")
    for marker in (
        "python scripts/release.py plan",
        "python scripts/release.py qualify",
        "name: release-candidate",
    ):
        if marker not in candidate_workflow:
            errors.append(f"release candidate workflow is missing {marker!r}")
    for marker in (
        "candidate_run_id:",
        "name: release-candidate",
        "python scripts/release.py publish",
    ):
        if marker not in release_workflow:
            errors.append(f"mandatory release workflow is missing {marker!r}")
    return errors


# A dated nightly such as `nightly-2026-10-27`. An undated `nightly` would
# give every build a new compiler each time a nightly is published.
_DATED_NIGHTLY = re.compile(r"nightly-\d{4}-\d{2}-\d{2}")
# Any mention of a nightly in CI configuration: an action input
# (`toolchain: nightly`), an action ref (`dtolnay/rust-toolchain@nightly`),
# `RUSTUP_TOOLCHAIN`, `cargo +nightly`, or a rustup command. Each one would
# pick a compiler other than the one rust-toolchain.toml names.
_NIGHTLY_WORD = re.compile(r"(?<![\w-])nightly(?![\w])")


def nightly_pin_errors(root: Path) -> list[str]:
    """
    Report an undated development nightly, or CI configuration that picks its own nightly.

    `rust-toolchain.toml` must name a dated nightly, so every machine and CI
    job builds with the same compiler until the date is moved on purpose. CI
    installs that toolchain through the `install-rust` composite action,
    which reads the file, so no workflow, composite action or example
    workflow may name a nightly itself. YAML comments are skipped, and jobs
    that pin a stable release on purpose, such as the docs and release
    builds, pass.
    """
    errors: list[str] = []
    toolchain_file = root / "rust-toolchain.toml"
    channel = tomllib.loads(toolchain_file.read_text(encoding="utf-8")).get("toolchain", {}).get("channel", "")
    if not _DATED_NIGHTLY.fullmatch(str(channel)):
        errors.append(
            f"rust-toolchain.toml channel must be a dated nightly such as 'nightly-YYYY-MM-DD', found {channel!r}"
        )
    paths = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    paths += sorted((root / ".github" / "actions").glob("*/action.y*ml"))
    # Users copy the example workflows, so they follow the same rule.
    paths += sorted(root.glob("examples/*/*/.github/workflows/*.y*ml"))
    for path in paths:
        label = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            # A comment may mention nightly freely; only the YAML before it counts.
            code = line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
            if _NIGHTLY_WORD.search(code):
                errors.append(
                    f"{label}:{number} names its own nightly ({code.strip()!r}); install Rust with "
                    "the ./.github/actions/install-rust action, which reads rust-toolchain.toml"
                )
    return errors


def selected_toolchain_errors(root: Path) -> list[str]:
    """
    Report a job that installs a specific Rust toolchain but would build with another.

    Installing a toolchain with `dtolnay/rust-toolchain` does not select it
    inside the checkout: there, `rust-toolchain.toml` wins and every cargo
    run uses the development nightly. So a job that installs a toolchain,
    such as the workspace minimum, must also set `RUSTUP_TOOLCHAIN` to the
    same value in its workflow or job env. Only those two count: a step's
    env reaches that step alone, not the cargo steps after it. A
    `${{ env.NAME }}` setup input is resolved against the workflow and job
    env, with the job env winning, as GitHub does. A setup with no
    `toolchain` input takes the toolchain from its ref (`@1.96.0`), unless
    the ref is a commit SHA, which then installs nothing specific.
    """
    errors: list[str] = []
    paths = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    paths += sorted(root.glob("examples/*/*/.github/workflows/*.y*ml"))
    for path in paths:
        workflow = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        label = path.relative_to(root).as_posix()
        workflow_env = _env_mapping(workflow.get("env"))
        for job_name, job in (workflow.get("jobs") or {}).items():
            job_env = _env_mapping(job.get("env"))
            env = {**workflow_env, **job_env}
            for step in job.get("steps") or []:
                uses = str(step.get("uses", ""))
                if not uses.lower().startswith("dtolnay/rust-toolchain@"):
                    continue
                settings = step.get("with")
                requested = str((settings if isinstance(settings, dict) else {}).get("toolchain", "")).strip()
                ref = uses.partition("@")[2]
                # Without an input, the action installs the toolchain its ref names.
                if not requested and not re.fullmatch(r"[0-9a-f]{40}", ref):
                    requested = ref
                installed = _resolve_env(requested, env)
                selected = _resolve_env(env.get("RUSTUP_TOOLCHAIN", ""), workflow_env)
                # An input that names an unset variable installs nothing the job can rely on.
                if requested and not installed:
                    errors.append(f"{label} job {job_name} installs Rust {requested!r}, which is not set")
                    continue
                # nightly_pin_errors already reports a setup that names a nightly, so skip it here.
                if not installed or _NIGHTLY_WORD.search(installed):
                    continue
                if not selected:
                    errors.append(
                        f"{label} job {job_name} installs Rust {installed!r} but does not set "
                        "RUSTUP_TOOLCHAIN, so cargo in the checkout would use rust-toolchain.toml; "
                        "set it in the workflow or job env"
                    )
                elif selected != installed:
                    errors.append(
                        f"{label} job {job_name} installs Rust {installed!r} but sets "
                        f"RUSTUP_TOOLCHAIN={selected!r}, so cargo in the checkout would build with "
                        f"{selected!r} instead"
                    )
    return errors


def _env_mapping(value: object) -> dict[str, str]:
    """Read an `env:` block as strings; an expression such as `${{ fromJSON(...) }}` reads as empty."""
    return {str(key): str(item) for key, item in value.items()} if isinstance(value, dict) else {}


def _resolve_env(value: str, env: dict[str, str]) -> str:
    """Resolve a whole-value `${{ env.NAME }}` reference, as GitHub does for workflow env."""
    reference = re.fullmatch(r"\$\{\{\s*env\.(\w+)\s*\}\}", value.strip())
    return env.get(reference.group(1), "") if reference else value.strip().strip("\"'")


def pinned_action_errors(root: Path, uv_pin: str) -> list[str]:
    """
    Report steps that leave the reviewed setup-uv or PyPI upload setup.

    Every workflow, example workflow, and composite action under
    `.github/actions/` is read as YAML. Each setup-uv step must use the
    reviewed commit, install exactly `uv_pin` (resolved through
    ``${{ env.NAME }}`` references at workflow, job, and step level), and set
    `prune-cache: true`.
    """
    errors: list[str] = []
    # GitHub runs both spellings of the YAML extension.
    paths = sorted(path for path in (root / ".github" / "workflows").glob("*.y*ml"))
    # Users copy the example workflows, so they follow the same pins.
    paths += sorted(root.glob("examples/*/*/.github/workflows/*.y*ml"))
    for path in paths:
        workflow = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        # Messages name files with forward slashes on every OS, as the repository does.
        label = path.relative_to(root).as_posix()
        workflow_env = workflow.get("env") or {}
        for job_name, job in (workflow.get("jobs") or {}).items():
            env = {**workflow_env, **(job.get("env") or {})}
            where = f"{label} job {job_name}"
            for step in job.get("steps") or []:
                errors.extend(_action_pin_errors(where, step, env, uv_pin))
    # A composite action can install uv or upload to PyPI on behalf of any
    # job that uses it, so its steps follow the same pins.
    for path in sorted((root / ".github" / "actions").glob("*/action.y*ml")):
        action = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        where = f"{path.relative_to(root).as_posix()} composite action"
        for step in (action.get("runs") or {}).get("steps") or []:
            errors.extend(_action_pin_errors(where, step, {}, uv_pin))
    return errors


def _action_pin_errors(where: str, step: dict[str, object], env: dict[str, object], uv_pin: str) -> list[str]:
    """Report a setup-uv or PyPI upload step that leaves the reviewed commit or settings."""
    errors: list[str] = []
    # GitHub matches action owners and names without regard to case.
    uses = str(step.get("uses", "")).lower()
    if uses.startswith("pypa/gh-action-pypi-publish@") and uses != _PYPI_ACTION.lower():
        errors.append(f"{where} must upload with {_PYPI_ACTION}")
    if not uses.startswith("astral-sh/setup-uv@"):
        return errors
    # Only the reviewed commit is known to check the uv download against a
    # checksum, so every job uses it.
    if uses != _UV_ACTION.lower():
        errors.append(f"{where} must use {_UV_ACTION}")
    settings = step.get("with")
    settings = settings if isinstance(settings, dict) else {}
    version = str(settings.get("version", ""))
    # A `${{ env.NAME }}` reference pins whatever that env value holds.
    reference = re.fullmatch(r"\$\{\{\s*env\.(\w+)\s*\}\}", version)
    if reference:
        step_env = step.get("env")
        version = str({**env, **(step_env if isinstance(step_env, dict) else {})}.get(reference.group(1), ""))
    # Every job runs the uv release the citry-core build settings record, so a
    # new uv reaches CI only through a reviewed change to that one pin.
    if version != uv_pin:
        found = f"sets uv {version!r}" if version else "does not set a uv version"
        errors.append(f'{where} {found}; set version: "{uv_pin}"')
    # Since setup-uv 9, prune-cache is off by default; turning it on keeps the
    # saved cache small and pruned, as it was before that release.
    if str(settings.get("prune-cache")).lower() != "true":
        errors.append(f"{where} must set prune-cache: true on {_UV_ACTION}")
    return errors
