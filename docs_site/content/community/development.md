---
title: Development
description: Set up citry locally, run the full check gate, rebuild the Rust extension, preview the docs site, and see how CI is layered.
---

# Development

Citry is a Rust and Python monorepo. The core lives in Rust crates under
`crates/`, is exposed to Python through the `citry-core` bindings. The
pure-Python `citry` package sits on top.

This page is the hands-on setup: how to get the workspace building,
run the checks the way CI does, and preview the docs.

For how the pieces fit together, see `docs/codebase.md` in the repository. For a
shorter contributor overview, see the [contributing guide](/community/contributing/).

## Getting set up

You need four things on your machine:

- [uv](https://docs.astral.sh/uv/){: target="_blank" rel="noopener"} -
  Python dependency manager.
- [Rust via rustup](https://rustup.rs/){: target="_blank" rel="noopener"} -
  Installs `cargo` and manages Rust toolchains. The repository's
  `rust-toolchain.toml` selects the required nightly toolchain automatically
  when you run `cargo` here.
- [Node.js](https://nodejs.org/){: target="_blank" rel="noopener"} - Used for dev tools:
  [pyright](https://github.com/microsoft/pyright){: target="_blank" rel="noopener"},
  [TypeScript](https://www.typescriptlang.org/){: target="_blank" rel="noopener"},
  and [Biome](https://biomejs.dev/){: target="_blank" rel="noopener"}.
  Current LTS Node works.
- [pnpm](https://pnpm.io/){: target="_blank" rel="noopener"} - Node dependency manager.

Citry also uses
[Ruff](https://github.com/astral-sh/ruff){: target="_blank" rel="noopener"}'s
internal packages to parse Python code inside Citry templates. Because these
packages are unpublished, the Ruff project is included as a [git
submodule](https://www.youtube.com/watch?v=gSlXo2iLBro){: target="_blank" rel="noopener"}.

When you download `citry` project, use `--recurse-submodules` to include the Ruff submodule:

```sh
# Clone fresh
git clone --recurse-submodules https://github.com/citry-dev/citry
cd citry

# Or if you already cloned without --recurse-submodules:
git submodule update --init --recursive
```

Then run `uv sync` from the repository root to install all Python dependencies
for all packages:

```sh
uv sync --all-packages
```

`uv sync --all-packages` is the one-step bootstrap:

1. Builds the `citry_core` Rust extension through the [maturin](https://github.com/pyo3/maturin){: target="_blank" rel="noopener"} backend,
2. Installs the `citry` package in editable mode,
3. Installs every package's dev dependencies (pytest, ruff, mypy, maturin, and each package's own test deps).

Because the lockfile knows every package, a later `uv sync` will not remove the editable installs.

Lastly, install the Node dependencies:

```sh
pnpm install
```

This installs the dependencies from `pnpm-lock.yaml`.

[`npm`](http://npmjs.com/){: target="_blank" rel="noopener"} is not a substitute: `pnpm` is used also for managing monorepo dependencies (`pnpm-workspace.yaml`).


## Confirm your setup works

Run codebase-wide commands (`uv sync`, `uv run`, `python scripts/check.py`) from
the repository root, since they read the root `pyproject.toml` for configuration.

A quick way to check that the Rust extension built and the packages installed is
to render a component. Save this as `confirm_setup.py`:

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

Then run it from the repository root:

```sh
uv run python confirm_setup.py
```

Calling `Greeting(...)` returns a [`CitryElement`][citry.CitryElement], a
lightweight description of what to render, and `str()` runs the full render and
serializes it to HTML. If your setup is working, the script prints a
`<p>Hello, citry!</p>` element.

## Running the checks

One command runs the whole gate the way CI does, and it is the single source of
truth for "does everything pass":

```sh
python scripts/check.py
```

It runs every phase, then reports all results together:

- Cargo - `cargo fmt`, `cargo clippy`, `cargo test`
- Ruff - `ruff check`, `ruff format`
- Python type checks - `mypy`, `pyright`
- JS type checks - TypeScript, Biome lint and format
- Python Test - pytest
- Custom validators

Every phase runs even after an earlier one fails, so you see all the failures in
one pass instead of one at a time. Pass `--reporter agent` for a single JSON
object you can parse:

```sh
python scripts/check.py --reporter agent
```

There is no pre-commit hook by design. Nothing runs on `git commit`, so the
tools never rewrite your files behind your back; you run the gate when you
choose and fix what it reports. Please make sure it passes before opening a pull
request.

While iterating you can run a single tool instead of the whole gate:

```sh
# Python tests
uv run pytest

# Rust tests
# Use `-p <crate_name>`, so cargo skips Ruff's crates
cargo test -p citry_core_py -p citry_html_transform \
           -p citry_template_parser -p python_safe_eval

# Formatting and linting
cargo fmt
cargo clippy
uv run ruff format .
uv run ruff check .
uv run mypy packages/py/citry_core

# Just the custom validators (fast; no compiling or tests)
python scripts/validate.py
```

The custom validators are small modules under `scripts/validators/` that guard
repo-specific rules. Usually cross-language or cross-package constraints that other tools can't cover:

- Every Python package has an entry in `dependabot.yml`,
- That, for the Rust code exposed to Python, the Rust-side API matches the Python-side,
- That every Rust crate is captured in `Cargo.toml`.

They are auto-discovered, so adding a check is just dropping
a new file into that directory.

## Working on the Rust core

`uv sync` rebuilds `citry_core` when the Rust sources change, but for a tighter
inner loop while working on Rust, build the extension directly:

```sh
cd packages/py/citry_core
uv run maturin develop
```

Both `maturin develop` and the `uv sync` build produce a debug (unoptimized)
extension. That is fine for tests, but it makes the Rust-backed paths several
times slower, so pass `--release` before running any [benchmark](/advanced/performance/):

```sh
uv run maturin develop --release
```

## Working on the docs site

The documentation site lives under `docs_site/` and renders these markdown pages
through citry itself. Run every command with `python -m docs_site <command>`
from the repository root.

While editing, run the dev server for a live preview. It renders each page on
the fly through the same pipeline as the build, so you edit a markdown file and
reload:

```sh
python -m docs_site serve   # http://127.0.0.1:8000/
```

Build the whole static site to disk (defaults to `<repo>/site`):

```sh
python -m docs_site build
```

The gate that CI runs on every change builds the site and runs the post-build
guards (links, anchors, fences, navigation drift). Pass `--strict` to also fail
on warnings, not just errors:

```sh
python -m docs_site build-check --strict
```

To preview the site exactly as it deploys, build it with `docs_site build`, then serve it over plain
HTTP:

```sh
python -m docs_site serve-built
```

## Writing docstrings

Most API Reference pages under `/reference/` are generated from the docstrings
on Citry's public Python API. The build introspects the `citry` package with
[griffe](https://mkdocstrings.github.io/griffe/){: target="_blank" rel="noopener"} and renders one entry per public symbol (the names exported
from `citry`), so the docstring you put on a public class, function, or
attribute is exactly what a reader sees on its reference page.

The [Built-in tags](/reference/builtins/) page is the exception. Not all Citry `<c-*` tags have a Python equivalent. That's why their reference has to be managed manually in `docs_site/content/reference/builtins.md`:

- Tags that are Python components (inherit `Component`) - their source of truth is their `Component` subclass:
    - `<c-component>`, `<c-element>`
    - `<c-provide>`
    - `<c-cache>`
    - `<c-error-fallback>`
    - `<c-css>`, `<c-js>`
- Tags with no Python equivalent - source of truth is in `builtins.md`:
    - `<c-if>`, `<c-elif>`, `<c-else>`
    - `<c-for>`, `<c-empty>`
    - `<c-slot>`, `<c-fill>`
    - `<c-raw>`

Write the docstrings for the reader: someone meeting the symbol for the first time, in plain language,
not for a contributor reading the source.

A few conventions keep the generated pages consistent:

- **Open with a one-sentence summary.** The first line is a short description of
  what the symbol is or does. Keep it to a single sentence and leave any detail
  for the paragraphs below it.
- **Use Google-style sections.** citry's docstrings are parsed in Google style,
  and the reference turns these sections into their own labelled fields: `Args:`
  (shown as Parameters), `Returns:`, `Raises:`, and `Attributes:`. An `Example:`
  (or `Examples:`) section renders as a titled example block, so a usage snippet
  in the docstring shows up on the reference page too.
- **Link other symbols with a bracket cross-reference.** In the prose, write a
  reference link to another symbol's entry like this:

  ```text
  [`CitryElement`][citry.CitryElement]
  ```

  The text in the first brackets is what the reader sees; the second brackets
  hold the full dotted path of a real citry symbol (a member such as
  `citry.Component.template_data` works too).
  
  Only symbols that actually exist resolve; an unknown key falls back to plain text with no link, so reference
  only names that are really there.

Putting it together, a documented method reads like this:

```python
def render(
    self, *,
    template_globals: Mapping[str, Any] | None = None
) -> CitryRender:
    """
    Render this element to a [`CitryRender`][citry.CitryRender].

    Args:
        template_globals: Extra global names to expose to the template
            while it renders.

    Returns:
        The rendered output, ready to serialize to HTML.
    """
    ...
```

## Making a change

- **Write tests.** New or changed behavior comes with tests. They are the
  evidence the change works and the guard against regressions.
- **Keep the changelog honest.** Add a `CHANGELOG.md` entry only when the change
  is observable to a user of the package (a fixed behavior, a new or changed
  public API, a default change). Skip it for internal refactors and tooling.
- **Mind the cross-language contract.** The grammar, the AST, and the compiler
  output are a contract shared across the host-language bindings. If you touch
  one of them, read the high-risk notes in `CLAUDE.md` first.

## Releases

Releases are per-package and triggered by pushing a git tag named for the
package and version:

- `citry@X.Y.Z` for the Python package
- `citry-core@X.Y.Z` for the Rust-backed bindings
- `pygments-citry@X.Y.Z` for the Pygments lexer package

The tagged version must match the package's `pyproject.toml`;
the publish workflow checks this and fails the release on a
mismatch.

The packages version and release independently. Because `citry` depends on
`citry-core`, when you bump both, publish `citry-core` first and let it reach
PyPI before tagging `citry`. `pygments-citry` has no cross-package release
ordering requirement.

Publishing uses
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/){: target="_blank" rel="noopener"} (OIDC),
so there is no stored API token. See `docs/codebase.md` for the full release flow.

## How CI is layered

CI is a single-environment gate plus per-language matrices that add cross-version
and cross-OS breadth on top of it.

| Workflow | What it runs | When |
| --- | --- | --- |
| `repo--check.yml` | The full gate (`python scripts/check.py`) on Python 3.13 with the Rust nightly toolchain and Node for the pyright and citry-client phases | Every push and pull request, no path filters |
| `rust--tests.yml` | Rust crate tests (`cargo test -p ...`) on Ubuntu and Windows | Changes under `crates/`, `third_party/`, `.github/`, or `.gitmodules` |
| `py--tests.yml` | Python tests: `uv sync --locked --all-packages`, then `uv run --no-sync pytest`, across Python 3.10 to 3.14 on Ubuntu and Windows plus a macOS smoke pair | Changes under `packages/py/`, `crates/`, `third_party/`, `.github/`, or `.gitmodules` |
| `repo--docs-check.yml` | The docs gate (`python -m docs_site build-check`) plus the docs-site unit tests | Changes under `docs_site/`, `packages/py/`, `crates/`, and related paths |
| `repo--docs-deploy.yml` | Builds and publishes the docs site to GitHub Pages | Pushes to `main` |
| `repo--ruff-upstream.yml` | Checks stable Ruff releases for changes in the internal crates Citry uses, then opens one tracking issue | Monthly or manual |

Running `python scripts/check.py` locally is the same gate `repo--check.yml`
runs, so a clean local run is the best predictor of a green pull request.
