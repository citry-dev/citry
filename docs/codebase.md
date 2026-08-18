# Codebase & Development

This document outlines the architectural and organizational decisions made for the citry monorepo.

## Monorepo Structure

### Overview

This repository follows a **monorepo pattern** where:

1. **Rust as source of truth** - Core logic lives in Rust [`crates/`](../crates/)
2. **Language bindings** - Rust functionality is exposed to multiple languages - Python, PHP, JS, Go...

   Each language has one package to define language-specific API. E.g. [`packages/py/citry_core`](../packages/py/citry_core/) exposed Rust code to Python.

3. **Packages** - The actual packages for developers are defined as separate packages, e.g. [`packages/py/citry`](../packages/py/citry/).

4. **Third party git modules** - In some cases, like for Ruff, we have to include them as git module.
   These are stored inside [`third_party/`](../third_party/).

### Directory Structure

```
citry/
├── crates/              # Rust workspace crates (core + internal crates)
│   ├── citry_core_py/   # Main Rust crate exposed to Python
│   ├── citry_html_transform/
│   ├── citry_i18n/     # Language-neutral Fluent catalog runtime
│   ├── citry_template_formatter/
│   ├── python_safe_eval/
│   └── citry_template_parser/
├── packages/            # Shipping products per language
│   └── py/              # Python packages
│       └── citry/       # Main Python package
│       └── citry_core/  # Expose citry_core_py to Python
├── tests/               # Integration tests
├── pyproject.toml       # Root tooling configuration (NOT releasable)
└── Cargo.toml           # Rust workspace configuration
```

### Rationale

The architecture is designed to support multiple language bindings:

- **Python**: Via PyO3/maturin
- **JS/TS**: Via wasm-bindgen
- **Go**: Via stable C ABI/FFI
- **PHP**: Via stable C ABI/FFI

As such, the Rust crates are ideal for:

- Text transformation - e.g. template parser, or HTML/code modification
- Shared component logic with string interfaces - Instead of re-implementing it for each language, we define it one in Rust.

<!-- TODO - THE REST IS NOT VERIFIED!!! -->
<!-- TODO - THE REST IS NOT VERIFIED!!! -->
<!-- TODO - THE REST IS NOT VERIFIED!!! -->

## Getting Started / Development Setup

### Prerequisites

- **Rust**: Install via [rustup](https://rustup.rs/). Vendored Ruff requires
  Rust 1.95 or higher, and this repository selects the nightly channel.
- **Python**: 3.10 or higher
- **UV**: Fast Python package installer (recommended)
- **Node.js and [pnpm](https://pnpm.io/)**: needed for the gate's Node-based
  phases: the pinned `pyright`, the `citry-client` TypeScript package, the docs
  playground bundle, and the VS Code language extension. A current LTS Node is
  fine; run `pnpm install` once after cloning. pnpm is the repo's Node package
  manager: the committed lockfile is `pnpm-lock.yaml`, CI installs from it with
  `pnpm install --frozen-lockfile`, and one root install covers every member in
  `pnpm-workspace.yaml`, including `docs_site/_internal/frontend`, `packages/editors/*`,
  and `packages/js/*`. npm is not a substitute here because it does not read
  the pnpm workspace or run those package-local gates.

### Installing and Managing Rust

This codebase uses **Rust edition 2024**, and vendored Ruff requires Rust 1.95
or higher. The edition and minimum version are both available on stable Rust;
the repository separately chooses to track nightly in
[`rust-toolchain.toml`](../rust-toolchain.toml) so local and CI builds use one
development channel.

**Check your Rust version:**

```bash
# Check current Rust version
rustc --version
cargo --version

# Verify the toolchain for this project
cd citry
rustup show
```

**Install or update Rust:**

```bash
# Install rustup (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install the nightly toolchain selected by this repository
rustup toolchain install nightly

# Update to the latest nightly
rustup update nightly

# The rust-toolchain.toml file will automatically select the correct toolchain
# when you run cargo commands in this directory
```

**Verify the correct toolchain is active:**

```bash
# From the repository root
cd citry
cargo --version  # Should show nightly version
rustc --version  # Should show nightly version
```

If you need to manually override the toolchain for this directory:

```bash
rustup override set nightly
```

### Installing UV

Install [UV](https://astral.sh/uv) using one of these methods:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip (if you have Python already)
pip install uv
```

### Setting Up the Development Environment

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd citry
   git submodule update --init --recursive  # Initialize Ruff submodule
   ```

2. **Verify Rust toolchain** (required before building):

   ```bash
   # Check that nightly is installed and active
   rustc --version  # Should show nightly version
   cargo --version  # Should show nightly version

   # If not using nightly, install it:
   rustup toolchain install nightly
   rustup override set nightly
   ```

   The [`rust-toolchain.toml`](../rust-toolchain.toml) file automatically
   selects the repository's nightly development channel when you run cargo
   commands in this directory. Rust edition 2024 itself does not require
   nightly.

3. **Install the workspace** (from the repository root):

   ```bash
   cd citry
   uv sync --all-packages
   ```

   This is the one-step bootstrap. From the root [`pyproject.toml`](../pyproject.toml) and the locked workspace it: builds the `citry_core` Rust extension through the maturin backend, installs the pure-Python `citry` package in editable mode, and installs every package's dev dependencies (pytest, ruff, mypy, maturin, and each package's own test deps). Because the lockfile now knows every package, a later `uv sync` or `uv run` is safe and will not remove the editable installs.

4. **Rebuilding the Rust extension during development**:

   `uv sync` rebuilds `citry_core` when the Rust sources change (the `cache-keys` in its [`pyproject.toml`](../packages/py/citry_core/pyproject.toml) cover `crates/**`). For a tighter inner loop while working on Rust, build it directly:

   ```bash
   cd packages/py/citry_core
   uv run maturin develop
   ```

   Note: both `maturin develop` and the `uv sync` build produce a **debug** (unoptimized) extension. That is fine for tests, but it makes the Rust-backed paths ~10x or more slower, so pass `--release` (for example `uv run maturin develop --release`) before running any benchmark.

5. **Run tests**:

   ```bash
   # From the root directory
   uv run pytest

   # Or run Rust tests first (scoped to our crates, see "Running tests" below)
   cargo test -p citry_core_py -p citry_html_transform -p citry_i18n -p citry_template_formatter -p citry_template_parser -p python_safe_eval
   ```

## Common Development Tasks

**Note**: Codebase-wide tools (like `uv sync`, `uv run pytest`, `uv run ruff`) should be run from the **repository root directory**, as they read the root [`pyproject.toml`](../pyproject.toml) for configuration.

### Building the package

```bash
# From the package directory
cd packages/py/citry_core
uv run maturin develop
```

### Running tests

Rust tests are scoped to the crates under `crates/`, one `-p` flag per crate.
The vendored ruff submodule's crates are auto-included in the cargo workspace
(path dependencies inside the workspace directory), so a bare `cargo test`
would also run ruff's own test suite. CI scopes the run the same way
(see `rust--tests.yml`).

```bash
# From the root directory
# Python tests
uv run pytest

# Rust tests (our crates only)
cargo test -p citry_core_py -p citry_html_transform -p citry_i18n -p citry_template_formatter -p citry_template_parser -p python_safe_eval

# Both (Rust first, then Python)
cargo test -p citry_core_py -p citry_html_transform -p citry_i18n -p citry_template_formatter -p citry_template_parser -p python_safe_eval && uv run pytest
```

#### Browser end-to-end tests

Install the browser-test dependencies and Chromium before running the E2E
suite locally:

```bash
uv sync --all-packages --group e2e
uv run playwright install chromium
```

The Citry and Citry UI browser suites run by file across four pytest workers,
matching the four CPUs on the standard public GitHub Linux runner. Each worker
owns its own browser process and test servers; `loadfile` keeps all tests from
one file on the same worker so file-local fixtures are not split across
processes:

```bash
uv run --no-sync pytest \
  packages/py/citry/tests/e2e \
  packages/py/citry_ui/citry_ui/components \
  packages/py/citry_ui/citry_ui/quality/tests/e2e \
  -m e2e \
  --browser chromium \
  -n 4 \
  --dist loadfile \
  --durations 30
```

The pull-request Chromium job and the scheduled Chromium, Firefox, and WebKit
jobs use this same distribution. The browser matrix still assigns each browser
to a separate GitHub job; the four workers run inside that browser's one job
and do not request four GitHub runners. `--durations 30` reports the slowest
tests so an oversized file that limits parallelism remains visible.

Do not put the worker flags in pytest's global `addopts`. Small focused runs,
the ordinary Python matrix, and the docs-site E2E suite stay serial. In
particular, distributing the docs-site suite would repeat its session-scoped
site build once per worker. On a machine with fewer than four CPUs or limited
memory, lower `-n`; four is the CI default, not a correctness requirement.

### Formatting and linting code

```bash
# From the root directory
# Python (ruff - replaces black, isort, flake8)
uv run ruff format .          # Format code
uv run ruff check .           # Lint code
uv run ruff check --fix .     # Auto-fix linting issues

# Rust (rustfmt)
cargo fmt
```

### Type checking

```bash
# From the root directory
uv run mypy packages/py/citry_core
```

### Linting (Rust)

```bash
# From the root directory
cargo clippy
```

### Checks and validators

Quality is enforced by explicit commands, not a commit-time hook. Nothing runs
automatically on `git commit`, so the tools never change files behind your
back; run the appropriate check when you choose and fix what it reports.

#### Testing practices in a shared worktree

Tests provide evidence at three different boundaries. Use the narrowest one
that answers the question at hand:

1. **While implementing, run focused checks.** Run the affected test file,
   package check, formatter, type checker, or a small falsifier suite. Repeat
   these freely because they should complete in seconds. A reviewer should
   likewise run the cases that could disprove the change, not the entire
   repository.
2. **When the touched surfaces settle, run the fast repository profile.** It
   runs every static, type, package, and validator phase plus the portable
   non-browser Python tests, distributed by file across four workers. It omits
   coverage and the small `qualification` stress slice so routine integration
   feedback is not dominated by instrumentation or deliberately deep boundary
   proofs.
3. **At an integration boundary, one owner runs the full profile.** An
   integration boundary is when a substantial piece of work is settled and
   ready for handoff, a pull request, or release. In a shared worktree, the
   primary integration owner waits for other edits to finish and runs the full
   coverage profile once. Subagents and reviewers report their focused checks;
   they do not each repeat the full gate. If files change after that run, the
   integration owner decides which evidence must be refreshed.

Browser E2E is a separate fourth lane because it requires Playwright and a
browser binary. The repository profiles always pass `-m "not e2e"`, so their
behavior does not change merely because someone installed the optional E2E
group. Use the dedicated four-worker command in
[Browser end-to-end tests](#browser-end-to-end-tests), and let its Chromium and
cross-browser CI jobs provide the final browser evidence.

This ownership rule avoids concurrent full gates by practice rather than by a
workspace lock. A full result belongs to the source generation it checked; it
is not evidence for edits made while or after it ran.

#### Writing tests that stay fast

Test fidelity comes first, but setup cost should match the boundary under test:

- Reuse immutable, module-scoped applications, registries, catalogs, and
  library installations when a test is checking many inputs against the same
  configuration. Create a fresh instance when isolation, registration,
  lifecycle, cache invalidation, or failure cleanup is the behavior under test.
- Batch homogeneous render cases through one small test component instead of
  defining and registering a new component class for every row. Keep each row
  separately identified so failures remain local.
- Test source mapping and response joining with fake analyzer responses. Keep a
  smaller acceptance matrix against the real `ty` subprocess for transport,
  protocol, environment, and lifecycle boundaries. Cache immutable executable
  validation within one server process; never share analyzer state across
  unrelated temporary workspaces.
- Inject short shutdown/request bounds into lifecycle tests. Production timeout
  values are user-safety policy, not a duration that every unit test must sleep
  through.
- In Playwright, wait for the state that proves success. For debounce,
  throttle, polling, and timer behavior, use Playwright's clock rather than
  sleeping through wall time. A fixed sleep is appropriate only when elapsed
  real time is itself the contract.
- Mark an unusually expensive stress or depth proof with `qualification` only
  when a cheaper test already covers the ordinary behavior. The fast profile
  omits that marker. The full profile runs it in a separate two-worker phase
  without coverage instrumentation, and the Python version matrix retains it.

When a file becomes a load-balancing outlier under `--dist loadfile`, first
remove avoidable waits and repeated setup. Split the file only when it still
contains independent fixture groups large enough to schedule separately.

#### Running the checks

```bash
# Routine integration: all repository phases and non-browser tests, without
# coverage. This is the profile agents normally run after focused checks.
python scripts/check.py --profile fast

# Final integration: the same non-browser phases with the coverage threshold.
# With no --profile argument, `full` remains the backward-compatible default.
python scripts/check.py --profile full

# Machine-readable: progress and 30-second heartbeats go to stderr; stdout ends
# with one JSON object containing the profile, phase status and duration, and
# the tail of any failing phase's output.
python scripts/check.py --profile fast --reporter agent

# Run only the custom validators (fast; no compiling or tests).
python scripts/validate.py
```

`check.py` only checks; it never edits files. It assumes the workspace is set
up (`uv sync --all-packages`, plus `pnpm install` for the pinned Node tools)
and that `cargo`, `uv`, `node`, `pnpm`, and the Rust toolchain are on PATH. The
human and JSON reports include each phase's elapsed time and the total. In
agent mode, phase starts, finishes, and a heartbeat every 30 seconds go to
stderr while stdout remains a single parseable JSON result. Both profiles run
the non-browser pytest suite with `-n 4 --dist loadfile --durations 30`. The
main pytest phase selects `not e2e and not qualification`; the full profile
enables pytest-cov there, enforces the repository threshold, and then runs the
`qualification and not e2e` stress slice separately without coverage.
Coverage measures shipped runtime modules. It omits tests, repository-only
qualification helpers, subprocess adapters whose execution belongs to child
processes, and Citry UI's public demo `snippets/`, which are excluded from the
wheel and verified through the docs and UI scenario suites. The threshold is a
ratchet immediately below the current measured runtime coverage; raise it as
focused tests recover headroom.
The `pyright` phase runs the pinned pyright from `node_modules` alongside mypy.
The package-local Node phases run `pnpm run check` for `citry-client`, the docs
playground, and the VS Code language extension. One root `pnpm install` covers
all of them, the same way `uv sync` installs the Python tools.

#### Custom validators

The repo-specific invariants (every Python package has a Dependabot entry, the Rust bindings match the Python stub, the toolchain pins agree, every crate is a workspace member) live as small modules in `scripts/validators/`. They are **auto-discovered**: `scripts/validate.py` runs every `<name>.py` in that directory, so adding a check is just dropping in a new file (names starting with `_` are skipped).

Each validator exports a `check()` function that returns a list of problem descriptions; an empty list means the invariant holds:

```python
"""One line on what this invariant protects."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def check() -> list[str]:
    problems: list[str] = []
    # ... read files under REPO_ROOT; append a message for each violation ...
    return problems
```

The runner prints `PASS`/`FAIL` per validator and exits non-zero if any returns problems (or raises). There is no registration, argparse, or logging boilerplate to write: keep the module to the check logic and let `validate.py` (and `check.py`) handle running and reporting. If a validator needs an extra Python dependency, add it to the root `[dependency-groups].dev`.

#### CI integration

The gate runs in CI via the [`repo--check.yml`](../.github/workflows/repo--check.yml)
workflow, which builds the workspace and explicitly runs
`python scripts/check.py --profile full` on every change (no path filters).
The per-language matrix workflows ([`rust--tests.yml`](../.github/workflows/rust--tests.yml),
[`py--tests.yml`](../.github/workflows/py--tests.yml)) add cross-version,
cross-OS, and dedicated browser breadth on top of that single-environment gate.

### Protocol packages and shipped copies

Citry has two private server/browser wire contracts:

- [`packages/protocol/events/v1/`](../packages/protocol/events/v1/) owns
  Events calls, results, actions, and browser manifests.
- [`packages/protocol/client_graph/v1/`](../packages/protocol/client_graph/v1/)
  owns the rendered component graph and its ownership comments.

Each directory contains the prose spec, JSON Schemas, worked examples, a
standard-library-only Python package, and a TypeScript package. The protocol
directories are the editable sources. Citry ships byte-identical Python copies
under `citry._protocol`; refresh or check them with:

```bash
uv run python scripts/sync_protocol_python.py
uv run python scripts/sync_protocol_python.py --check
```

The Events TypeScript package builds into `citry-events.js`. The client-graph
TypeScript package builds one marked generated block inside `citry.js`.
Package-local `pnpm run check` commands type-check the sources, replay shared
cases, and reject stale generated files:

```bash
pnpm --dir packages/protocol/events/v1/js run check
pnpm --dir packages/protocol/client_graph/v1/js run check
pnpm --dir packages/js/citry-client run check
```

`tests/conformance-cases.json` holds surgical mutations that require matching
Python and JavaScript issue paths and categories. A schema constraint means one
concrete structural rule at one schema location. The companion
`tests/constraint-ownership.json` groups every such rule under named Python
and JavaScript validator functions and supporting test files. Counts and
content fingerprints make a schema edit fail until its validator assignment
is reviewed. Run both protocol audits with:

```bash
uv run python -m packages.protocol._tooling.check \
  packages/protocol/events/v1 \
  packages/protocol/client_graph/v1
```

The report deliberately keeps complete ownership assignment separate from the
smaller exact-mutation count. Relationship rules such as reference integrity
and cycle rejection live in the named valid/invalid fixture corpora because
JSON Schema does not express them.

### Verifying the citry distribution

The publish workflow builds one wheel and one source distribution. Its smoke
job then builds a second wheel from the source distribution in a temporary
directory outside the checkout and runs:

```bash
python scripts/verify_citry_distribution.py --dist-dir dist
```

The verifier compares every installed `citry/` source file with both wheels
and the source distribution, compares the two wheels member by member, and
installs each wheel into its own fresh environment. The installed checks run
outside the repository with Node absent from `PATH` and without `jsonschema`.
They exercise both embedded protocol packages, both browser data files, the
typing marker, the top-level import, and `citry --help`. Both wheels must also
stay below the checked 1.1 MiB release cap.

The main test workflow has a separate i18n release-qualification job. It builds
the native extension in release mode, runs `benchmarks/i18n.py`, checks the
browser i18n payload, and uploads the machine-readable result. The Citry UI
wheel job also builds a source distribution, rebuilds the wheel from it, and
requires both wheels to contain the same checked catalog package. Its installed
production smoke resolves a real Citry UI message without parsing package FTL.

During active development, `citry` can need an unreleased companion
`citry-core` change. Build that wheel explicitly and pass it to the same
isolated proof:

```bash
uv build --package citry-core --wheel --out-dir dist/core
python scripts/verify_citry_distribution.py \
  --dist-dir dist \
  --core-wheel dist/core/citry_core-*.whl
```

The tag-triggered publish workflow does not pass `--core-wheel`. It resolves
the exact `citry-core` pin from PyPI, so the smoke job still enforces the
documented release order: publish the compatible core first, wait for it to be
available, then tag `citry`.

### Adding a codebase-wide tooling package

To add a new tooling dependency (like a linter, formatter, or test utility) that should be available across the entire codebase:

1. Edit the root [`pyproject.toml`](../pyproject.toml) file
2. Add the package to the root `dev` dependency-group. Use this only for
   repo-wide tooling; a dependency used by a single package belongs in that
   package's own `[dependency-groups]` instead:

   ```toml
   [dependency-groups]
   dev = ["maturin>=1.10.2", "ruff>=0.10.0", "mypy>=1.0.0", "your-new-tool>=1.0.0"]
   ```

3. Install the new dependency:

   ```bash
   # From the root directory
   uv sync --all-packages
   ```

4. Use the tool:

   ```bash
   # From the root directory
   uv run your-new-tool
   ```

### Runtime optional-dependency extras (`citry[...]`)

Runtime extras on the `citry` package (the `pip install citry[...]` surface, as
opposed to the root `dev`/`ci` tooling extras above) are namespaced
`citry[<category>-<name>]` so the extras namespace stays collision-free and has
room to grow. Two categories exist so far:

- `watcher-<backend>`: a file-watcher backend for hot reload, e.g.
  `citry[watcher-watchfiles]`, `citry[watcher-watchdog]`. See
  [`docs/design/hot_reload.md`](design/hot_reload.md).
- `ext-<name>`: an optional or bundled extension and its dependencies, e.g. a
  future `citry[ext-storybook]`.

Rules:

1. **Always include the category prefix.** Do not add a bare `citry[watcher]` or
   `citry[storybook]`: an unprefixed token reads ambiguously (is `watcher` a
   backend name or a category?) and risks colliding with a future package or
   extension of the same name.
2. **Import the optional dependency lazily**, inside the module that needs it, so
   plain `import citry` never requires it (the contrib adapters and
   [`docs_site/_internal/cli.py`](../docs_site/_internal/cli.py) are the precedent).
3. **Declare each dependency once, at its owner.** Runtime extras stay on the
   `citry` package. A dependency imported only by that package's tests belongs
   in its `[dependency-groups].dev`. Only repo-wide tools belong in the root
   dev group. The uv workspace installs every member's selected groups into the
   shared environment with `uv sync --all-packages`, so no root mirror is
   needed. Refresh `uv.lock`, and grep CI workflows before changing a pin
   because jobs may select groups or extras explicitly. This is the landed
   workspace model from [#8](https://github.com/citry-dev/citry/issues/8).

### Adding a git submodule

To add a new third-party dependency as a git submodule:

1. **Determine the location**: Submodules are organized by language in [`third_party/`](../third_party/):

   - Rust - `third_party/rust/`
   - Python - `third_party/py/`
   - ect..

2. **Add the submodule**:

   ```bash
   # From the root directory
   # Example: Adding a Rust crate
   git submodule add https://github.com/example/upstream-repo.git third_party/rust/upstream-repo

   # Or for a specific tag/branch
   git submodule add -b v1.0.0 https://github.com/example/upstream-repo.git third_party/rust/upstream-repo
   ```

3. **Update documentation**: Add an entry to [`third_party/README.md`](../third_party/README.md) documenting:

   - What the dependency is for
   - Where it's used
   - License information
   - Update policy

4. **Update references**: If the submodule is used in code (e.g., `Cargo.toml` for Rust), update path references to point to the new location.

5. **Commit the changes**:

   ```bash
   git add .gitmodules third_party/rust/upstream-repo third_party/README.md
   git commit -m "Add upstream-repo as submodule"
   ```

**Initializing submodules** (for new clones):

```bash
# Initialize all submodules
git submodule update --init --recursive

# Or initialize a specific submodule
git submodule update --init third_party/rust/upstream-repo
```

**Updating a submodule**:

```bash
# Navigate to the submodule
cd third_party/rust/upstream-repo

# Fetch latest changes
git fetch origin --tags

# Checkout a specific tag/commit
git checkout v1.2.0

# Return to root and commit the update
cd ../../..
git add .gitmodules third_party/rust/upstream-repo
git commit -m "Update upstream-repo submodule to v1.2.0"
```

To keep track of the current version, update the comment in the `.gitmodules` file.

**Verifying builds after updating a submodule**:

After updating an upstream submodule, **always verify that everything still builds**. Upstream packages may introduce new dependencies that need to be added to the workspace `Cargo.toml`.

For example, when I upgraded `ruff` from v0.14.0 to v0.14.10, they added `datatest-stable` as a Rust dependency. So it had to be added to our root `Cargo.toml`:

### Adding Rust Dependencies

When adding a new Rust dependency to any crate in the workspace, follow these guidelines to ensure version consistency across the entire workspace:

1. **Add the dependency to the root `Cargo.toml`**: All dependency versions should be specified and pinned in the root [`Cargo.toml`](../Cargo.toml) under the `[workspace.dependencies]` section.

   ```toml
   [workspace.dependencies]
   your_new_dependency = { version = "1.2.3" }
   ```

2. **Use `workspace = true` in individual crates**: Individual crates should reference the workspace dependency using `workspace = true`, not specify versions directly:

   ```toml
   # In crates/your-crate/Cargo.toml
   [dependencies]
   your_new_dependency = { workspace = true }
   ```

   This ensures the entire workspace uses the same version of the dependency, preventing version conflicts and reducing binary size.

3. **Document upstream dependencies**: If the dependency was introduced because it's required by an upstream third-party package (like `ruff`), add a comment in the root `Cargo.toml` to document this:

   ```toml
   # Used by ruff_python_parser
   datatest-stable = { version = "0.3.3" }
   ```

   This helps track which dependencies are direct requirements vs. transitive requirements from upstream packages.

**Example**: Adding a new dependency to `python_safe_eval`:

1. Add to root `Cargo.toml`:

   ```toml
   [workspace.dependencies]
   # Used by python_safe_eval
   serde_json = { version = "1.0.113" }
   ```

2. Add to `crates/python_safe_eval/Cargo.toml`:

   ```toml
   [dependencies]
   serde_json = { workspace = true }
   ```

3. Run `cargo build` to verify it works.

### Adding a new package

When adding a new package to the monorepo (either a new Rust crate or a new Python package), you need to ensure that Dependabot is configured to watch its dependencies.

#### Rust packages

**No additional Dependabot configuration needed** for Rust crates. All Rust dependencies are centralized in the root [`Cargo.toml`](../Cargo.toml) under `[workspace.dependencies]`, so Dependabot automatically monitors all Rust dependencies when configured for the root directory.

The existing Dependabot entry for `package-ecosystem: "cargo"` at the root directory will cover all Rust crates in the workspace.

#### Python packages

**You must add a Dependabot entry** for each new Python package that has its own `pyproject.toml` with dependencies.

1. **Create the new Python package** in `packages/py/your-package/` with its own `pyproject.toml`

2. **Add a Dependabot entry** in [`.github/dependabot.yml`](../.github/dependabot.yml):

   ```yaml
   # Python - your-package
   - package-ecosystem: "pip"
     directory: "/packages/py/your-package"
     schedule:
       interval: "weekly"
   ```

3. **Verify the configuration** by checking that Dependabot can detect the package's dependencies.

**Note**: The root `pyproject.toml` already has a Dependabot entry for tooling dependencies (ruff, pytest, mypy, etc.). Each Python package with its own dependencies needs its own entry.

**Example**: If you add a new Python package `packages/py/citry/`, you would add:

```yaml
- package-ecosystem: "pip"
  directory: "/packages/py/citry"
  schedule:
    interval: "weekly"
```

**Why `pip` and not the `uv` ecosystem, and how `uv.lock` stays in sync.** The
entries use `package-ecosystem: "pip"` on purpose. Dependabot's newer `uv`
ecosystem would update `uv.lock` for you, but its uv-workspace support is still
immature, and the root `pyproject.toml` uses `[tool.uv.sources]` with
`{ workspace = true }`, which trips a known Dependabot uv parse bug. `pip` bumps
each package's `pyproject.toml` correctly but does not touch `uv.lock`, so the
`Check` gate would otherwise fail at `uv sync --locked`. The
[`repo--dependabot-relock.yml`](../.github/workflows/repo--dependabot-relock.yml)
workflow closes that gap: on a Dependabot PR it runs `uv lock` and commits the
refreshed `uv.lock` back to the PR branch. If no token is configured it instead
comments on the PR with the manual `uv lock` command and fails, so a missing or
expired token never silently blocks a PR.

**Setting up the relock token.** The push has to use a token that is *not* the
default `GITHUB_TOKEN` (a `GITHUB_TOKEN` push does not re-trigger the `Check`
gate, so it would stay red). Store it as a **Dependabot secret** (repo `Settings`
-> `Secrets and variables` -> `Dependabot`, *not* the Actions tab), because a
Dependabot-triggered run can only read Dependabot secrets. Two options:

- **Org GitHub App (recommended, not tied to one person).** An org-owned App is
  free on any plan and does not depend on one person's account. The mental model
  to hold: **ownership and installation are two separate things, and you need
  both.** *Owning* the App lets the org control it (its settings and key) but
  grants access to no repositories; *installing* it is what gives it repo access
  and creates the installation the workflow mints a token from. Set it up once:

  1. **Register it under the org** at
     `https://github.com/organizations/citry-dev/settings/apps/new`
     (`Organization citry-dev` -> `Settings` -> `Developer settings` ->
     `GitHub Apps` -> `New GitHub App`; you must be an org owner). Already made it
     under your *personal* account? Do not recreate it, transfer it: your account
     `Settings` -> `Developer settings` -> `GitHub Apps` -> the App ->
     `Advanced` -> `Transfer ownership` -> `citry-dev`.
  2. **Give it write access to code.** In the App's permissions set
     `Repository permissions` -> `Contents: Read and write`; that is what lets it
     push the `uv.lock` commit.
  3. **Install it on the repo** (owning it is not enough, and this is the step
     people miss). App page -> `Install App` -> install on `citry-dev` ->
     `Only select repositories` -> `citry` (or all). If a personal App showed no
     org to install on, that was its `Where can this GitHub App be installed?`
     setting defaulting to "Only on this account".
  4. **Approve any pending permission change.** If you set or changed
     `Contents: Read and write` *after* installing, GitHub holds it as a request
     an org owner must approve, or the token will not actually have write access.
  5. **Store the credentials as Dependabot secrets.** Copy the numeric `App ID`
     and `Generate a private key` (downloads a `.pem`); add them as the Dependabot
     secrets `RELOCK_APP_ID` and `RELOCK_APP_PRIVATE_KEY`. The workflow mints a
     short-lived installation token from these on each run
     (`actions/create-github-app-token`), so no long-lived token is stored.
- **Fine-grained PAT (simpler, but personal and expiring).** Create it on *your
  own* account at `Settings` -> `Developer settings` -> `Personal access tokens`
  -> `Fine-grained tokens`, with `Resource owner: citry-dev`, `Repository: citry`,
  and `Repository permissions` -> `Contents: Read and write`. The org must allow
  fine-grained PATs (`Organization citry-dev` -> `Settings` -> `Personal access
  tokens`). Add it as the Dependabot secret `RELOCK_TOKEN`. Prefer the App for
  anything long-lived, since a PAT stops working when its owner leaves or it
  expires.

If neither is set, the workflow still runs: it posts a PR comment with the exact
`uv lock` command and fails, so the fix is one copy-paste away.

### Working with Multiple Python Versions

UV can manage multiple Python versions automatically:

```bash
# Install a specific Python version
uv python install 3.11

# Use a specific version for this project
uv python pin 3.11

# Sync with that version
uv sync --all-packages
```

### CI Dependencies

CI installs the whole workspace from the lockfile, so it builds citry_core and installs every package's dev group reproducibly:

```bash
uv sync --locked --all-packages
```

### Brand assets: the C3 logo, favicons, and icons

The logo is the characters **C3**, which is how the name sounds read aloud: say
the `ci` of *citry* as the English letter C and what is left is `tri`, Slovak for
three. It is a pun on the name, not a version number.

Everything that shows the logo is cut from **two SVG files**, and nothing else is
drawn by hand:

| File | What it is |
|---|---|
| [`docs_site/static/img/citry-icon.svg`](../docs_site/static/img/citry-icon.svg) | The mark on a square frame, for anything sitting in a square slot |
| [`docs_site/static/img/citry-mark.svg`](../docs_site/static/img/citry-mark.svg) | The same two paths on a wide frame, for anything sitting beside text |

Both take their colour from the surrounding CSS through `currentColor`, except
the square one, which sets its own and flips with the reader's theme because a
favicon loads as its own document with no stylesheet around it.

#### Regenerating the rasters

Every PNG is a screenshot of one of those two SVGs. After changing the artwork,
run:

```bash
uv run --no-sync python docs_site/scripts/icons.py
```

That writes the browser and phone icons into `docs_site/static/img/`
(`favicon.svg`, `favicon-16.png`, `favicon-32.png`, `favicon.png`,
`apple-touch-icon.png`), the README wordmark and the profile picture into
`docs/assets/`, and the VS Code Marketplace icon into
`packages/editors/vscode/images/`. It needs Playwright and a Chromium binary
(`uv sync --extra social-cards`, then `playwright install chromium`). Do not
hand-export a PNG or edit one in an image editor: the next run overwrites it,
and the file drifts from the drawing in the meantime.

Three of the outputs are drawn on a white ground rather than a transparent one,
because their host fills transparency with something unpredictable: iOS paints a
home-screen icon's transparency black, a chat client composites a link preview
against its own theme, and GitHub shows a profile picture on both. The rest are
transparent.

#### Placing the logo in a page

In the docs site, do not paste the path data. The
[`<c-citry-mark />`](../docs_site/_internal/components/brand.py) component holds
it, and both the site header and the social-share card render through it. Pass
`css_class` when a stylesheet sizes and colours it, or `color` with `width` and
`height` when there is no stylesheet to read (the card is screenshotted on its
own, so it states both).

**When the mark stands beside the name, it sits slightly shorter than the
letters.** The site header is the reference: a `1rem` mark against a `1.05rem`
name, spaced `0.5rem` apart (`.djc-logo` in `docs_site/static/css/site.css`).
The README wordmark and the card footer are built from those same two
proportions, so all three read as one lockup. They do not follow the stylesheet
automatically, so retuning the header means retuning
`MARK_TO_NAME` and `GAP_TO_NAME` in `docs_site/scripts/icons.py` and the mark
size in `og_card.py`.

#### Images and links in a published README

A README that ships outside the repository (PyPI, the VS Code Marketplace) is
rendered on that host's own domain, where a repo-relative path such as
`docs/assets/benchmark.png` or `./LICENSE` resolves against *their* site and
404s. GitHub resolves the same path fine, so the breakage is invisible until
someone opens the package page. Every reference in those files therefore has to
be absolute: images at `https://raw.githubusercontent.com/...`, repository files
at `https://github.com/citry-dev/citry/blob/main/...`. The
`published_readme_links` validator enforces this, so a relative path fails the
gate rather than shipping.

#### The parts that are not in the repository

A GitHub organisation profile picture and a repository social-preview image can
only be uploaded through the web interface; there is no API for either.
`docs/assets/citry-avatar.png` is the file to upload for the profile picture.

## Rust-First Architecture

### Core Principle

**Rust is the source of truth** for all core functionality. Language bindings are thin wrappers that expose Rust functionality to other languages.

### Rust Workspace

The top-level `Cargo.toml` defines a workspace that includes:

- Core crates (`citry_core_py`, `citry_html_transform`, `citry_i18n`,
  `citry_template_formatter`, `python_safe_eval`, `citry_template_parser`)
- Shared dependencies and toolchain configuration
- Unified linting, formatting, and testing

### One binary, hand-owned Python API

All the Rust crates are exposed to Python through a single binding crate,
`citry_core_py`, compiled to one extension module, `citry_core._rust`. A
Rust-to-Python binary is large (on the order of ~100 MB), so bundling every
crate into one module ships one binary instead of one per crate.

The Python-facing API is written by hand rather than left as maturin's
auto-generated re-exports. The maturin-built binary is only a Python *module*
(`citry_core._rust`); the `citry_core` *package* wraps it with a thin Python
layer that unwraps union-returning Rust calls, adds Python-side error context,
and keeps a stable public surface (mirrored in the `_rust.pyi` stubs). That
layer is why the package can hold Python code beyond the raw bindings.

### Future Language Bindings

The architecture is designed to support multiple language bindings:

- **Python**: Via PyO3/maturin (current)
- **JavaScript/TypeScript**: Via wasm-bindgen (planned)
- **Go**: Via stable C ABI/FFI (planned)
- **PHP**: Via stable C ABI/FFI (planned)

## Python Packaging

### Package Structure

The Python package lives in `packages/py/citry_core/`.

**Key Files:**

- `packages/py/citry_core/pyproject.toml` - Package metadata and build configuration
- `packages/py/citry_core/__init__.py` - Public Python API
- Rust extension module built via maturin

### Build Configuration

The `pyproject.toml` in `packages/py/citry_core/`:

- Uses `maturin` as the build backend
- References the Rust crate at `../../../crates/citry_core_py/Cargo.toml`
- Includes Python source files via `[tool.maturin]` include paths

### Package vs Bindings

Currently, we have a single Python distribution (`citry_core`) that includes both:

- The Rust extension module (bindings)
- Python-side SDK code (helpers, types, error handling)

**Future consideration**: Split into two distributions:

- `citry_core` (thin): Only bindings + minimal shims
- `citry` (fat SDK): Full Python SDK that depends on `citry_core`

This would reduce verbosity in the package directory and allow independent versioning if needed.

## Dependency Management

### UV for Tooling

The root `pyproject.toml` uses **UV** for dependency management instead of traditional `requirements.txt` files.

**Why UV?**

- 10-100x faster than pip
- Better dependency resolution
- Built-in virtual environment management
- Lock files for reproducible builds

**Structure:** the root is a uv workspace; `packages/py/*` are members, and repo-wide tooling lives in a dependency-group:

```toml
[tool.uv.workspace]
members = ["packages/py/*"]

[dependency-groups]
dev = ["maturin>=1.10.2", "ruff>=0.10.0", "mypy>=1.0.0"]
```

**Usage:**

```bash
# Install the whole workspace (builds citry_core, installs citry editable,
# and pulls every package's dev group)
uv sync --all-packages

# Run tools
uv run pytest
uv run maturin develop
```

### Root pyproject.toml Protection

The root `pyproject.toml` is **explicitly marked as non-releasable**:

- No `[build-system]` section (prevents building)
- `"Private :: Do Not Upload"` classifier
- Version `0.0.0` with descriptive name

This prevents accidental releases while still allowing tooling configuration.

## Tooling Configuration

### Codebase-Wide Tools

The root `pyproject.toml` contains tool configurations that apply to the entire codebase:

- **Black**: Code formatting (119 char line length)
- **isort**: Import sorting (black-compatible)
- **flake8**: Linting (E302, W503 ignored)
- **mypy**: Type checking
- **pytest**: Test configuration

**Important**: These tools are **not** excluded from the `packages/` directory. They apply codebase-wide, including to all Python packages.

### Tool Exclusions

Tools exclude standard build artifacts and caches:

- `.venv`, `.tox`, `build`, `dist`
- `__pycache__`, `.mypy_cache`
- But **NOT** `packages/` - tools should run on package code

## Versioning strategy

### Current approach

- Published distributions are independently versioned and released.
- Each Python distribution declares its version in its own `pyproject.toml`.
- The `citry` distribution pins its compatible `citry-core` version exactly;
  the release-order rule below keeps that pair coherent.
- Rust crates declare their versions in their `Cargo.toml` files.

## Changelog management

### Package-owned changelogs

Each published package owns one changelog. The root
[`CHANGELOG.md`](../CHANGELOG.md) belongs only to the Python `citry` package.
Auxiliary distributions keep release notes in their package directories, for
example:

- [`packages/py/citry_core/CHANGELOG.md`](../packages/py/citry_core/CHANGELOG.md)
  for `citry-core`
- [`packages/py/pygments_citry/CHANGELOG.md`](../packages/py/pygments_citry/CHANGELOG.md)
  for `pygments-citry`
- [`packages/py/citry_lsp/CHANGELOG.md`](../packages/py/citry_lsp/CHANGELOG.md)
  for `citry-lsp`
- [`packages/editors/vscode/CHANGELOG.md`](../packages/editors/vscode/CHANGELOG.md)
  for the VS Code extension

This matches the independently versioned and tagged distributions. Users see
the release history for the package they are deciding whether to upgrade, and
one change is not duplicated across unrelated release streams. Internal crates
and monorepo infrastructure do not need user-facing release notes.

Use clear user-facing language, include migration instructions for breaking
changes, and link relevant issues when helpful. Record each release exactly
once in its owning changelog. The content test and exclusions are defined in
[`CLAUDE.md`](../CLAUDE.md#what-belongs-in-the-changelog).

Write each item as one outcome-first sentence when practical. Group related
implementation work, keep only the API names and keywords users need, and use
a small before/after example when it is faster to understand than prose.
Breaking migrations may be longer. The complete writing rules live in
[`CLAUDE.md`](../CLAUDE.md#how-to-write-a-changelog-entry).

## Versioning, tags and releases

### Package-specific tags

This monorepo uses **package-specific git tags** to distinguish versions of different packages.

**Tag format:**

Tags follow the format: `<package-name>@<version>`. A tag with no language prefix means the Python package.

**Examples:**

- `citry-core@1.3.0` - the citry-core Python package
- `citry@0.2.0` - the citry Python package
- `citry-lsp@0.1.0` - the Citry language server
- `pygments-citry@0.1.0` - the Citry Pygments lexer
- `vscode-citry@0.1.0` - the Citry VS Code extension

Editor-extension tags include the editor name so they cannot collide with a
Python distribution. The VS Code extension uses `vscode-citry@<version>`.

**Note:** When a second host language (JS/PHP/Go) is published, we will revisit how to disambiguate its tags from the Python ones (likely a `<language>@` prefix on the non-default languages); until then the prefix would be noise. The version after `@` must match the package's `pyproject.toml` version: the publish workflow checks this and fails the release on a mismatch.

**Rationale:**

- **Clarity**: Each tag clearly identifies which package it refers to
- **Independent versioning**: Supports packages versioning independently
- **Filtering**: Easy to list tags for a specific package: `git tag -l "citry-core@*"`
- **Scalability**: Works well as the monorepo grows with multiple major projects and language bindings

### Current Release Process

Currently, releases are managed manually:

1. **Update version** in the package's `pyproject.toml` (or equivalent for other languages)
2. **Re-lock**: run `uv lock` so `uv.lock` picks up the new version, and commit
   `uv.lock` alongside `pyproject.toml`. The lockfile pins every workspace
   package's version, so a bumped `pyproject.toml` without a matching `uv.lock`
   makes CI fail its `uv sync --locked --all-packages` step (in `repo--check` and
   the test workflows), not only at publish time.
3. **Update the package's owning changelog** with release notes. Use the root
   `CHANGELOG.md` only for `citry`; auxiliary packages use the `CHANGELOG.md`
   in their own package directory.
4. **Qualify Citry Core, Citry, or citry-lsp** when releasing one of those
   packages: manually run its publish workflow on the exact release commit on
   `main` and wait for the complete distribution gate. The tag promotes that
   run's exact bytes; packages without a qualify-then-promote workflow skip
   this step.
5. **Create the git tag** matching that version: `git tag -a citry-core@1.3.0 -m "Release citry-core@1.3.0"` (use the matching `citry@...` or `pygments-citry@...` name for another package)
6. **Push the tag**: `git push origin citry-core@1.3.0`

Pushing the tag triggers the package's publish workflow and verifies that the
tag matches the package version. Citry Core, Citry, and citry-lsp promote exact
qualified bytes; the remaining package workflows build and smoke-test from the
tag. A
`citry@X.Y.Z` tag also triggers the documentation release workflow that builds,
validates, commits, and deploys a version snapshot; sibling package tags do not.
Review the snapshot procedure and first-release blockers in
[`docs_site/README.md`](../docs_site/README.md#release-version-snapshots) before
pushing a Citry release tag. **Release ordering**: citry depends on
`citry-core`, so when bumping both, publish `citry-core` first and let it reach
PyPI before tagging `citry`.

The packages are versioned and released **independently on purpose**, so each
can ship on its own cadence. The ordering rule applies when `citry` and
`citry-core` both change. A `citry-lsp` release whose minimum Citry version is
new must likewise wait for that Citry release to reach PyPI. `pygments-citry`
has no cross-package release ordering requirement.

**`citry` pins one exact `citry-core` version** (`citry-core==1.5.0`, not a
range). The runtime node classes in `citry.nodes` read the source that
citry-core's compiler emits, so a citry-core release that changes that output
would otherwise reach an already-published `citry` that cannot read it. Raise
the pin in the same change that bumps citry-core's version, before tagging
either. That makes the two releases a pair: publish `citry-core` first, wait
for PyPI, then tag `citry`.

### The `review` branch holds work that has not been read yet

Releases go out from `main`, but not everything committed has been read line by
line. The `review` branch is where that unread work waits, so the editor's
source-control panel doubles as the worklist:

- **`main` is the reviewed baseline.** Local `main` tracks `origin/main`, so it
  never reports as diverged and never prompts to sync.
- **`review` carries everything not yet read**, branched at the commit `main`
  held when the ledger was last reset. The `reviewed-baseline` tag names that
  commit as a recovery point.
- **Reading a file through means committing it on `review`.** The commit is the
  audit record of what has been read.
- **Do not pull generated commits into `review`.** The docs release pushes a
  `docs: build <version> [skip ci]` commit to `main` carrying the version
  snapshot. Let local `main` fetch those and leave `review` alone; nobody
  reviews generated output.

**`review` never merges into `main`, in either direction.** The gate works by
having `HEAD` point at an old tree, so the two branches diverging is what makes
it function, not damage to repair. The editor's "N behind, M ahead" indicator is
cosmetic and stays lit; `review` has no upstream configured, so the editor is
just comparing against `origin/main`. Merging `main` into `review` would refuse
to run anyway, because it would have to overwrite hundreds of locally-modified
files, and `git merge -s ours` is worse: it records "deliberately discard main's
changes", so a later merge the other way would revert content on `main` to
`review`'s older copies.

A release therefore never comes from `review`. Assemble it in a throwaway
worktree of `main` instead:

```bash
git worktree add ../citry-release main
# copy the named files this release needs into the worktree, then
# commit, tag, and push from there
git worktree remove ../citry-release
```

Two rules that came out of doing this five times:

- **Copy named files, never whole trees.** A wholesale copy drags in whatever
  other work is in progress on disk, and `main` may not be able to run it. Diff
  each file into place and read the diff.
- **Land any fix you make during the release in the working tree too**, not
  only in the worktree. Otherwise the disk copy stays stale and committing the
  tree later silently reverts the fix. The change then shows up in the panel as
  an ordinary unread entry, which is accurate.

Releasing straight from `review` looks tempting because publish workflows
accept a manual `workflow_dispatch`. That is not a supported release route:
Citry Core and Citry treat every manual dispatch (even one targeting a tag
ref) as a qualification-only run; it cannot enter Trusted Publishing. A tag
push from `main` is the supported release route for every package.

The throwaway `main` worktree preserves the arrangement automatically. Keep the
original `review` worktree's branch pointer, index, and files unchanged before,
during, and after the promotion; `review` continues to point at its recorded
pre-promotion baseline, so every unread modification and untracked file remains
visible in the editor. Do not reset `review` to the new `main`: that makes the
same bytes appear reviewed and hides newly tracked files from the worklist. If
recovery is ever required, restore `review` to its recorded pre-promotion SHA
(normally the `reviewed-baseline` recovery point) with a mixed reset so the disk
contents remain intact.

A tag cannot rebuild this arrangement: it only names a commit, while the panel
is populated from the original worktree relative to `review`'s `HEAD`.

### Chronological Ordering

Git tags are ordered by the commit date they point to, not the date they were created. When packages version independently:

- Tags may appear out of chronological order in the tag list
- To list tags chronologically for a specific package: `git tag -l "citry-core@*" --sort=-version:refname`
- This is expected behavior and acceptable for independent versioning

### Future Tooling

As the monorepo grows, we may adopt automated tooling for versioning and releases:

**Potential Tools:**

- **Changesets**: Popular for npm/pnpm monorepos, supports independent versioning with `package-name@version` tags (can be configured for custom tag formats)
- **Lerna**: JavaScript-focused monorepo tool with flexible versioning strategies
- **Cocogitto**: Rust-focused tool that automates versioning based on conventional commits
- **Semantic Release**: Automated versioning based on commit messages
- **Release Please**: Google's tool that works with multiple languages and package managers

**Benefits of automation:**

- Automatic version bumping based on commit messages
- Automatic changelog generation
- Automatic tag creation
- Dependency version updates
- Coordinated releases across packages

**When to adopt:**

Consider adopting automated tooling when:

- Manual release process becomes error-prone or time-consuming
- Multiple packages are released frequently
- Coordinating releases across packages becomes complex
- Team size grows and release process needs standardization

### Workflow management

**Workflow file naming convention:**

Since GitHub Actions workflows cannot be nested in subdirectories (all workflow files must be in `.github/workflows/` at the root), we use a consistent naming convention to organize workflows by language and package:

**Format:** `<language>--<package-name>--<workflow-type>.yml`

**Examples:**

- `py--citry-core--publish.yml` - Publish Python citry-core package
- `py--pygments-citry--publish.yml` - Publish the Citry Pygments lexer
- `py--citry-core--test.yml` - Test Python citry-core package (future)
- `js--citry-core--publish.yml` - Publish JavaScript citry-core package (future)
- `go--citry-core--publish.yml` - Publish Go citry-core package (future)

**Rationale:**

- **Double dashes (`--`)** clearly separate language → package → workflow type
- **Language prefix** (`py--`, `js--`, `go--`) namespaces the workflow file by language; release *tags* drop the prefix (a bare tag means Python), so the file naming is a separate scheme that still leaves room for other languages
- **Scalable** as the monorepo grows with multiple packages and languages
- **Easy to filter**: `ls .github/workflows/py--*` shows all Python workflows

**Package-Specific Workflow Triggers:**

Each publish workflow is configured to trigger only on tags for its specific package:

```yaml
on:
  push:
    tags:
      - "citry-core@*" # Only triggers for citry-core@1.3.0, etc.
```

This ensures:

- Workflows only run when their specific package is released
- No unnecessary workflow runs for unrelated package tags
- Clear separation of concerns per package

**Workflow Organization:**

- **Test workflows** use descriptive names: `repo--check.yml`, `rust--tests.yml`, `py--tests.yml`
- **Package-specific workflows** use the `language--package--type.yml` convention (e.g., `py--citry-core--publish.yml`)
- All workflows are in `.github/workflows/` (no subdirectories supported by GitHub)

## CI/CD Strategy

### Test Workflows

The repository uses **three separate test workflows** to optimize CI performance and only run tests when relevant code changes:

#### 1. `repo--check.yml` - The full gate

**Purpose**: Runs the full non-browser check profile
(`python scripts/check.py --profile full`) on all changes: formatting, lints,
types, coverage, the custom validators, and a single-environment test pass.

**Triggers**: Runs on all pushes and pull requests (no path filters).

**What it runs**:

- `python scripts/check.py --profile full`: lock validation, cargo
  fmt/clippy/test, Ruff,
  mypy, Pyright, the client/docs-playground/VS Code package checks, pytest, and
  the custom validators, every phase followed by a combined report
- The single source of truth for "does everything pass"

**Configuration**:

- Python 3.14 on ubuntu-latest, with the Rust nightly toolchain and Node 22
- `uv sync --locked --all-packages` and `pnpm install --frozen-lockfile` to
  build both workspaces, then `python scripts/check.py --profile full`

#### 2. `rust--tests.yml` - Rust Tests

**Purpose**: Tests all Rust crates in the workspace.

**Triggers**: Runs when changes are made to:

- `crates/**` - Rust crate code
- `.github/**` - Workflow changes that might affect test execution
- `third_party/**` - Third-party dependencies (e.g., Ruff submodule)
- `.gitmodules` - Submodule configuration changes

**What it tests**:

- All Rust crates via `cargo test -p <package>` for each crate
- Tests only our crates (excludes Ruff submodule crates)

**Configuration**:

- Rust nightly toolchain (matching `rust-toolchain.toml`)
- Tests on ubuntu-latest and windows-latest
- Uses Rust dependency caching for faster builds

**Why path filters**: Avoids running Rust tests when only Python code, documentation, or unrelated files change.

#### 3. `py--tests.yml` - Python Tests

**Purpose**: Tests all Python packages.

**Triggers**: Runs when changes are made to:

- `packages/py/**` - Python package code
- `crates/**` - Rust code (Python packages depend on Rust via PyO3 bindings)
- `third_party/**` - Third-party dependencies used by both Rust and Python
- `.github/**` - Workflow changes
- `.gitmodules` - Submodule configuration changes

**What it tests**:

- Installs the whole workspace with `uv sync --locked --all-packages`, which builds the `citry_core` extension through maturin and installs `citry` editable, so both packages' suites run (`citry` did not run in CI before the uv workspace)
- Runs the portable Python tests via
  `uv run --no-sync pytest -m "not e2e" -n 4 --dist loadfile --durations 30`;
  four file-level workers share one GitHub runner

**Configuration**:

- Python versions: 3.10, 3.11, 3.12, 3.13, 3.14
- OS: ubuntu-latest and windows-latest, plus a macOS smoke pair (oldest and newest Python)
- Requires Rust toolchain (`uv sync` builds the citry_core extension via maturin)
- Uses Rust dependency caching

**Why path filters**: Avoids running Python tests when only documentation, scripts, or unrelated files change. Includes `crates/**` because Python packages depend on Rust code via PyO3 bindings.

### Docs workflow Rust cache

The docs workflows build the local `citry_core` extension because the rendered
site imports Citry. They use the workspace MSRV (`RUSTUP_TOOLCHAIN=1.95.0`), not
the repository's moving development nightly, and share the
`docs-citry-core-py314` Rust cache across Ubuntu/CPython 3.14 jobs. The cache
deliberately omits the GitHub job ID and is saved even if a later docs guard,
browser audit, link check, or deployment step fails. This prevents an unrelated
docs failure from throwing away the expensive Cargo build and lets the next
docs job reuse it. The same jobs use `sccache`'s GitHub Actions backend for
content-addressed compiler outputs, so concurrently-started cold jobs can share
crate compilation before any one job has saved its complete Cargo target tree.
Keep the toolchain, Python ABI, shared key, compiler-cache settings, and cache policy
aligned across `repo--docs-check.yml`, `repo--docs-deploy.yml`,
`repo--docs-external-links.yml`, `repo--docs-lighthouse.yml`,
and `repo--docs-release.yml`; the toolchain validator enforces that contract.
Those workflows select only the root, Citry, and Citry UI workspace packages,
because the rendered site does not import the LSP. The people-data refresh does
not render the site or import Citry at all, so it syncs only the root package and
the `docs` extra and avoids the Rust build entirely.

### Testing

- **Rust tests**: Run via `rust--tests.yml` workflow using `cargo test`
- **Python tests**: Run via `py--tests.yml`, which installs the uv workspace
  (`uv sync --locked --all-packages`) and distributes the non-browser suite by
  file across four workers on each matrix runner
- **The full non-browser gate**: Run via `repo--check.yml`, which runs
  `python scripts/check.py --profile full` (lint, types, coverage, validators,
  and single-environment portable tests)
- **Dependencies**: Installed from the uv workspace lockfile; `--locked` keeps CI reproducible
- **Matrix testing**: Python tests run across Python versions (3.10-3.14) and OSes

### Publishing

Each published Python package has its own tag-triggered workflow:
`py--citry-core--publish.yml`, `py--citry--publish.yml`,
`py--citry-lsp--publish.yml`, or
`py--pygments-citry--publish.yml`. Most package workflows build and test from
the `<package>@<version>` tag, publish to PyPI, and create a matching GitHub
Release. Citry Core, Citry, and citry-lsp use qualify-then-promote: the tag can
publish only the exact bytes already qualified for its `main` commit.

**PyPI auth is Trusted Publishing (OIDC), not a stored API token.** The release jobs carry `id-token: write` and target a GitHub environment named `pypi`; PyPI verifies the workflow's OIDC identity, so there is no secret to keep. Before a package's first publish, configure a PyPI **publisher** (a *pending publisher* if the project does not exist yet) with:

- PyPI project name (`citry-core`, `citry`, `citry-lsp`, or `pygments-citry`)
- Owner and repository (`citry-dev/citry`)
- Matching workflow filename under `.github/workflows/`
- Environment name (`pypi`)

The first publish from a configured pending publisher creates the project. The GitHub `pypi` environment is also where you can add a manual-approval gate on releases.

### Citry Core distribution qualification

Run `py--citry-core--publish.yml` manually on the exact `main` commit that will
receive the release tag. That qualification run builds one source distribution
and 34 native wheels. Fourteen `cp310-abi3` wheels cover GIL-enabled CPython
3.10 and newer across every supported platform. Linux and musllinux also carry
one CPython 3.14 free-threaded wheel and one PyPy 3.11 wheel per architecture.
The workflow also builds one
`cp314-cp314-pyemscripten_2026_0_wasm32` wheel for the exact Pyodide runtime
pinned by the playground. That browser wheel is another build of
`citry-core`, not a package dependency.

The qualification uses Rust 1.95.0, Maturin 1.14.1, and Cargo's
performance-qualified `release-wheel` profile: fat LTO, one codegen unit, and
no debug information in the stripped distribution build. The four-way
profile/ABI comparison and keep/drop decision are recorded in
[`docs/design/performance.md`](design/performance.md#9-citry-core-release-wheel-profile-and-abi-decision-2026-08-18).
Builders select the three supported interpreter families explicitly, so a
runner-image change cannot silently add or remove a wheel. Runnable wheels are
installed and exercised in their build jobs: every supported interpreter on
Linux x86_64 and Windows, plus the oldest and newest CPython on macOS. The
remaining cross-architecture wheels receive the same static inspection. The
sdist job rebuilds outside the checkout with the declared Rust 1.95 minimum and
exercises the resulting wheel before uploading the sdist.

Each builder keeps its output in a separate directory. The final qualification
job rejects duplicate filenames and requires the complete 36-file set before
it creates `verified-citry-core-distributions`. Every wheel is checked against
the checkout for metadata, tags, Python payload, extension module, license,
`RECORD`, and size. `release-inventory.json` records every filename, byte size,
and SHA-256 hash. GitHub retains this promotion bundle for 14 days.
The qualification run records build provenance for the verified set; the tag
run records a second attestation for promoting those bytes to the registries.

Two separate runners build the PyEmscripten wheel from clean source trees with
the pinned Pyodide/Emscripten tuple. The workflow requires byte-identical
normalized outputs and checks the actual SDK-reported Emscripten version. It
uses that SDK's `wasm-opt` to remove the workspace's profiler-only DWARF/debug
payload before regenerating `RECORD`, then exercises build A in that exact
Pyodide runtime.

After qualification succeeds, add and push `citry-core@<version>` at that same
commit. The tag run searches for the newest successful manual qualification
whose source repository, branch (`main`), and full commit SHA match the peeled
tag. It downloads that run's immutable bundle by artifact ID, verifies
GitHub's archive SHA-256, safely extracts it, and repeats the complete static
and source-byte verification against the tagged checkout. It publishes those
qualified bytes without compiling them again. The GitHub Release includes
`qualification-provenance.json`, which records the qualification run, commit,
and artifact digest.

The tag run fails before entering Trusted Publishing when no exact
qualification exists, its artifact expired, its digest differs, the tag commit
is absent from `main`, or any file differs from the recorded inventory. Run a
fresh manual qualification for that exact commit; do not substitute artifacts
from another commit. Release-critical third-party actions are pinned to
reviewed commits.

The version must be absent from both PyPI and GitHub Releases before publishing.
The workflow never skips existing PyPI files or overwrites release assets: a
partial publication requires deliberate hash reconciliation and manual
recovery, not an automatic rerun that could associate different bytes.

The permanent browser build tuple lives in
`packages/py/citry_core/pyodide-build.json`. Its Pyodide and Python versions
must match `docs_site/static/playground/runtime.json`. Do not update the
playground to a new Citry Core version until PyPI provides the immutable wheel
URL and the whole compatible runtime tuple can be promoted and browser-tested
together.

### Citry distribution qualification

Run `py--citry--publish.yml` manually on the exact `main` commit that will
receive the Citry tag. The workflow builds the one universal wheel and one
source distribution, requires that closed pair and its package/metadata/
license/entry-point/`RECORD` inventories, rebuilds the sdist outside the
checkout, and install-smokes both wheels on CPython 3.10 through 3.14. Its
`verified-citry-distributions` bundle and `release-inventory.json` are retained
for 14 days.

Pushing `citry@<version>` at that commit selects the successful manual run by
repository, `main` branch, and full commit SHA. The tag run checks the GitHub
artifact digest, safely extracts and re-verifies the pair against the tagged
checkout, requires the commit to remain on `main`, and fails closed if the
PyPI version or GitHub Release already exists. It never rebuilds, skips an
existing PyPI file, or overwrites a release asset.

### citry-lsp distribution qualification

Run `py--citry-lsp--publish.yml` manually on the exact `main` commit that will
receive the `citry-lsp@<version>` tag. The workflow builds one universal wheel
and one source distribution, then requires that closed pair and its package,
metadata, license, console-entry-point, and `RECORD` inventories. It rebuilds
the source distribution outside the checkout and installs the wheel with only
public binary dependencies on CPython 3.10 through 3.14.

The installed-wheel smoke imports every shipped module, verifies Citry 0.4.x,
`pygls` 2.1.1, and `ty` 0.0.69, checks `citry-lsp --help`, and starts the stdio
server with closed input. This proves that a clean install resolves the public
`citry[analysis-ty]` dependency without reading another workspace package.

The manual run retains `verified-citry-lsp-distributions` and its exact byte
inventory for 14 days. Pushing the matching tag at that same commit selects the
successful manual run by repository, `main` branch, and full commit SHA. The tag
run checks GitHub's artifact digest, safely extracts and re-verifies the pair
against the tagged checkout, requires the commit to remain on `main`, and fails
closed if the PyPI version or GitHub Release already exists. It never rebuilds,
skips an existing PyPI file, or overwrites a release asset.

For the first release, create a pending PyPI Trusted Publisher with this exact
identity: project `citry-lsp`, owner `citry-dev`, repository `citry`, workflow
`py--citry-lsp--publish.yml`, and environment `pypi`. The workflow file and the
tagged commit must be on `main` before publication. Configure the GitHub `pypi`
environment to permit `citry-lsp@*` tags as well as any existing package tag
rules.

- Rust crates are not published to crates.io; they are an internal implementation detail surfaced through the Python packages.
- The root `pyproject.toml` is never published (no build-system; `Private :: Do Not Upload`).

## Future Architecture

### Planned Expansions

1. **JavaScript/TypeScript Bindings**

   - WASM build via wasm-bindgen
   - Package in `packages/js/citry/`
   - Native Node.js addon as alternative

2. **Go Bindings**

   - Stable C ABI from `crates/ffi/`
   - Go wrapper in `packages/go/citry/`
   - Generated header file in `include/citry.h`

3. **PHP Bindings**
   - Same C ABI as Go
   - PHP extension in `packages/php/citry/`

### FFI Crate

A future `crates/ffi/` crate will provide:

- Stable C ABI boundary
- Language-agnostic interface
- Used by Go, PHP, and potentially other languages
- Generated headers committed to repo

## Design Principles

1. **Rust First**: Core logic always in Rust
2. **Thin Bindings**: Language bindings are minimal wrappers
3. **Idiomatic APIs**: Packages provide language-native interfaces
4. **Single Source of Truth**: One implementation, multiple interfaces
5. **Tooling at Root**: Shared configuration, not duplicated
6. **Explicit Non-Releasable**: Root config clearly marked as tooling-only

## Migration Notes

### From Single Package to Monorepo

The codebase was migrated from a single-package structure to a monorepo:

- **Before**: Root `pyproject.toml` for both tooling and package
- **After**:
  - Root `pyproject.toml` for tooling only
  - `packages/py/citry_core/pyproject.toml` for package

### Path Updates

When moving the package `pyproject.toml`:

- `manifest-path` updated to `"../../../crates/citry_core_py/Cargo.toml"`
- `readme` updated to `"../../../README.md"`
- Maturin include paths remain relative to package directory
