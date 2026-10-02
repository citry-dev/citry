---
title: Development
description: Set up citry locally, run the full check gate, rebuild the Rust extension, preview the docs site, and see how CI is layered.
---

# Development

You want to change Citry's code or its documentation. This page gets the
project building on your machine, shows how to check your change the way CI
does, and how to preview the docs.

Citry is a Rust and Python monorepo. The core lives in Rust crates under
`crates/`. The `citry-core` package exposes them to Python, and the
pure-Python `citry` package sits on top.

For how the pieces fit together, see `docs/codebase.md` in the repository.
For a shorter overview of ways to help, see the
[contributing guide](/community/contributing/).

## Set up your machine { #getting-set-up }

Install these four tools:

- [uv](https://docs.astral.sh/uv/){: target="_blank" rel="noopener"} -
  the Python dependency manager.
- [Rust via rustup](https://rustup.rs/){: target="_blank" rel="noopener"} -
  installs `cargo`. The repository's `rust-toolchain.toml` picks the
  required nightly toolchain when you run `cargo` inside it.
- [Node.js](https://nodejs.org/){: target="_blank" rel="noopener"}, current
  LTS - runs the dev tools
  [pyright](https://github.com/microsoft/pyright){: target="_blank" rel="noopener"},
  [TypeScript](https://www.typescriptlang.org/){: target="_blank" rel="noopener"},
  and [Biome](https://biomejs.dev/){: target="_blank" rel="noopener"}.
- [pnpm](https://pnpm.io/){: target="_blank" rel="noopener"} - the Node
  dependency manager.

Clone the repository with its submodules:

```sh
git clone --recurse-submodules {{ repo_url }}
cd citry

# If you already cloned without --recurse-submodules:
git submodule update --init --recursive
```

The submodule is
[Ruff](https://github.com/astral-sh/ruff){: target="_blank" rel="noopener"}.
Citry uses Ruff's internal packages to parse the Python code inside
templates. Ruff does not publish those packages, so the repository includes
the Ruff source as a
[git submodule](https://www.youtube.com/watch?v=gSlXo2iLBro){: target="_blank" rel="noopener"}.

Install the Python packages from the repository root:

```sh
uv sync --all-packages
```

This one command:

1. Builds the `citry_core` Rust extension through the
   [maturin](https://github.com/pyo3/maturin){: target="_blank" rel="noopener"}
   build backend.
2. Installs the `citry` package in editable mode.
3. Installs every package's dev dependencies (pytest, ruff, mypy, maturin,
   and each package's own test dependencies).

A later plain `uv sync` keeps these editable installs.

Then install the Node dependencies from `pnpm-lock.yaml`:

```sh
pnpm install
```

Use `pnpm`, not `npm`. The repository's Node packages form one pnpm
workspace, declared in `pnpm-workspace.yaml`.

Run repository-wide commands (`uv sync`, `uv run`,
`python scripts/check.py`) from the repository root. They read their
settings from the root `pyproject.toml`.

## Check your setup { #confirm-your-setup-works }

Render a component to confirm the Rust extension built and the packages
installed. Save this as `confirm_setup.py`:

```citry
from citry import Component

class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p>Hello, {{ name }}!</p>
    """

greet = Greeting(name="citry")
print(str(greet))
```

Run it from the repository root:

```sh
uv run python confirm_setup.py
```

`str()` renders the component to HTML. A working setup prints
`<p>Hello, citry!</p>`.

## Run the checks { #running-the-checks }

One command runs every check CI runs and reports all the results together:

```sh
python scripts/check.py
```

It runs these phases:

- `uv lock --check`, which fails when `uv.lock` no longer matches the
  `pyproject.toml` files.
- Rust: `cargo fmt`, `cargo clippy`, `cargo test`.
- Python lint and format: `ruff check`, `ruff format`.
- Python types: `mypy`, plus `pyright` on the typing tests.
- JavaScript and TypeScript: the TypeScript and Biome checks of each Node
  package, and a check that Citry UI's minified files match their source.
- Python tests: pytest, then a check that the server-rendered Vue pages match
  Vue's own renderer.
- The custom validators (see below).

Every phase runs even after an earlier one fails, so you see all the
failures in one pass. The command only checks; it never edits files.

Two profiles control how much the tests do:

```sh
# While you work: no coverage, skips the slow stress tests
python scripts/check.py --profile fast

# Before a pull request: adds the coverage threshold and
# the stress tests. This is the default, and what CI runs.
python scripts/check.py --profile full
```

Add `--reporter agent` to get one JSON object you can parse:

```sh
python scripts/check.py --reporter agent
```

There is no pre-commit hook. Nothing runs on `git commit`, so no tool
rewrites your files behind your back. Run the checks yourself and make sure
they pass before you open a pull request.

### Run a single tool

While you work, you can run one tool instead of the whole set:

```sh
# Python tests
uv run pytest

# Rust tests. List the crates with -p so cargo
# skips Ruff's crates.
cargo test -p citry_core_py -p citry_html_transform \
           -p citry_i18n -p citry_template_formatter \
           -p citry_template_parser -p citry_vue_compiler \
           -p python_safe_eval

# Formatting and linting
cargo fmt
cargo clippy
uv run ruff format .
uv run ruff check .
uv run mypy packages/py/citry_core

# Only the custom validators (fast; no compiling or tests)
python scripts/validate.py
```

### Custom validators

The custom validators check repository rules that no other tool covers,
often rules that span languages or packages. For example, they check that:

- Every Python package has an entry in `dependabot.yml`.
- The Rust functions exposed to Python match the Python type stub.
- Every Rust crate is listed in the root `Cargo.toml`.

Each validator is a small module in `scripts/validators/`. To add one, drop
a new file in that directory; `scripts/validate.py` finds and runs it.

## Make a change { #making-a-change }

- **Write tests.** New or changed behavior comes with tests. They show the
  change works and catch it if it breaks later.
- **Add a changelog entry only when users notice.** Add one for a fixed
  behavior, a new or changed public API, or a changed default. Skip it for
  internal refactors and tooling. Each package keeps its own changelog: the
  root `CHANGELOG.md` is for the `citry` package, and other packages keep
  theirs in their own directory.
- **Read `CLAUDE.md` before touching the template language.** The grammar,
  the parsed template structures, and the compiler output are shared by
  every host-language binding. `CLAUDE.md` lists the extra steps a change to
  them needs.

## Rebuild the Rust core { #working-on-the-rust-core }

`uv sync` rebuilds `citry_core` when the Rust sources change. For a faster
loop while you work on Rust, build the extension directly:

```sh
cd packages/py/citry_core
uv run maturin develop
```

Both commands build an unoptimized debug extension. That is fine for tests,
but the Rust-backed code runs several times slower. Before you run the
[repository benchmarks](https://github.com/citry-dev/citry/blob/main/benchmarks/README.md){: target="_blank" rel="noopener"},
build with `--release`:

```sh
uv run maturin develop --release
```

## Preview the docs { #working-on-the-docs-site }

The documentation site lives under `docs_site/` and renders these Markdown
pages with Citry itself. Run each command from the repository root.

While you edit, run the dev server. It renders each page when you load it,
so you edit a Markdown file and reload the browser:

```sh
python -m docs_site serve   # http://127.0.0.1:8000/
```

Before you open a pull request, build the site and run its checks for
broken links, anchors, code fences, and navigation. `--strict` also fails
on warnings:

```sh
python -m docs_site build-check --strict
```

CI runs `build-check` without `--strict` when the docs or the code they
document change.

To see the site exactly as it deploys, build it to disk (by default into
`<repo>/site`), then serve the built files:

```sh
python -m docs_site build
python -m docs_site serve-built
```

## Write docstrings { #writing-docstrings }

Most pages under the [API Reference](/reference/) are generated from
docstrings. The build reads the public names exported from `citry` with
[griffe](https://mkdocstrings.github.io/griffe/){: target="_blank" rel="noopener"}
and renders one entry for each. The docstring on a public class, function,
or attribute is exactly what a reader sees there.

Write it for someone meeting the symbol for the first time, not for a
contributor reading the source:

- **Start with a one-sentence summary.** The first line says what the
  symbol is or does. Put details in the paragraphs below it.
- **Use Google-style sections.** The reference shows `Args:` (as
  Parameters), `Returns:`, `Raises:`, and `Attributes:` as separate fields.
  An `Example:` (or `Examples:`) section becomes a titled example block.
- **Link other symbols with brackets.** Write a link to another entry like
  this:

  ```text
  [`CitryElement`][citry.CitryElement]
  ```

  The first brackets hold the text the reader sees. The second hold the
  full dotted path of a real `citry` symbol; a member such as
  `citry.Component.template_data` works too. An unknown path shows as plain
  text with no link.

A documented method looks like this:

```python
def render(
    self,
    *,
    template_globals: Mapping[str, Any] | None = None,
    provides: Mapping[str, Any] | None = None,
) -> CitryRender:
    """
    Render this element to a [`CitryRender`][citry.CitryRender].

    Args:
        template_globals: Extra global names to expose to the
            template while it renders.
        provides: Values the root and its rendered descendants
            may read with ``inject()``.

    Returns:
        The rendered output, ready to serialize to HTML.
    """
    ...
```

Each generated page lists its symbols in `docs_site/reference.yml`. When
you add a public export, add it to a page there; otherwise `build-check`
warns that no page documents it.

### Hand-written reference

Two reference pages are written by hand.

[Built-in tags](/reference/builtins/) lives in
`docs_site/content/reference/builtins.md`, because not every `<c-*>` tag has
a Python class:

- These tags are Python components, so their `Component` subclass is the
  source of truth: `<c-component>`, `<c-element>`, `<c-mark>`,
  `<c-provide>`, `<c-cache>`, `<c-error-fallback>`, `<c-i18n>`,
  `<c-trans>`, `<c-css>`, `<c-js>`.
- These tags have no Python class, so `builtins.md` is the source of truth:
  `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`, `<c-slot>`,
  `<c-fill>`, `<c-raw>`.

[Browser APIs](/reference/browser-apis/) covers everything that runs in the
browser: `$component` and its server-render callbacks, `Citry.vue`, and the
Events helpers such as `$sendEvent` and `Citry.events`. Declare each
linkable name and its anchor in `docs_site/reference.yml`, then document
that anchor in `docs_site/content/reference/browser-apis.md`. The build
check reports an anchor that is missing, duplicated, or not declared.

## How releases work { #releases }

Each package has its own version and its own git tag, named after the
package and version:

- `citry@X.Y.Z` for the Python package
- `citry-core@X.Y.Z` for the Rust-backed bindings
- `citry-lsp@X.Y.Z` for the language server
- `citry-ui@X.Y.Z` for the Citry UI component library
- `pygments-citry@X.Y.Z` for the Pygments lexer package
- `vscode-citry@X.Y.Z` for the VS Code extension

Maintainers do not push these tags by hand. A release goes like this:

1. A pull request that changes a package version is merged into `main`.
2. The **Prepare release candidate** workflow builds and tests every
   package whose version has no tag yet.
3. A maintainer inspects that run and passes its run ID to the **Release
   qualified packages** workflow.
4. That workflow publishes the packages in dependency order (for example,
   `citry-core` before `citry`), checks the published files, and creates
   the tags and GitHub Releases.

Publishing to PyPI uses
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/){: target="_blank" rel="noopener"}
(OIDC), so no API token is stored. The full release flow is in
`docs/codebase.md`.

## What CI runs { #how-ci-is-layered }

One workflow runs the full set of checks in a single environment. Other
workflows repeat the tests across Python versions and operating systems.

| Workflow | What it runs | When |
| --- | --- | --- |
| `repo--check.yml` | `python scripts/check.py --profile full` on Python 3.14 with nightly Rust and Node | Every pull request and every push to `main` or `dev` |
| `rust--tests.yml` | Rust crate tests on Ubuntu, Windows, and macOS | Changes under `crates/` or `third_party/`, to the Cargo files, `rust-toolchain.toml`, or `.gitmodules` |
| `py--tests.yml` | `uv sync --locked --all-packages`, then pytest, on Python 3.10 to 3.14 on Ubuntu and Windows, plus Python 3.10 and 3.14 on macOS | Changes under `packages/py/`, `packages/js/citry-client/`, `packages/protocol/`, `crates/`, or `third_party/`, and to the lockfiles and build scripts |
| `repo--docs-check.yml` | `python -m docs_site build-check` plus the docs site's own tests | Changes under `docs_site/`, `packages/py/`, `crates/`, and related paths |
| `repo--docs-deploy.yml` | Builds the docs site and publishes it to GitHub Pages | Pushes to `main` that change the docs or the code they document |
| `repo--ruff-upstream.yml` | Checks new stable Ruff releases for changes in the internal packages Citry uses, and opens one tracking issue | Monthly, or by hand |

`repo--check.yml` runs the same command as `python scripts/check.py`, so a
clean local run is the best sign your pull request will pass.
