# Contributing to Citry

Thanks for your interest in improving Citry. This guide covers the practical
setup; how the codebase fits together lives in
[`docs/codebase.md`](docs/codebase.md), and the rules AI agents follow are in
[`CLAUDE.md`](CLAUDE.md).

Citry is a Rust + Python monorepo: the core lives in Rust crates under
[`crates/`](crates/), is exposed to Python through the `citry-core` bindings,
and the pure-Python `citry` package sits on top.

## Getting set up

You need a recent [uv](https://docs.astral.sh/uv/) and the Rust toolchain
pinned in [`rust-toolchain.toml`](rust-toolchain.toml). The Ruff parser is a git
submodule, so clone with submodules:

```sh
git clone --recurse-submodules https://github.com/citry-dev/citry
cd citry
# if you already cloned without --recurse-submodules:
git submodule update --init --recursive
uv sync --all-packages
```

`uv sync --all-packages` builds the Rust extension and installs both Python
packages into a shared virtual environment.

## Running the checks

One command runs the whole gate the way CI does (cargo fmt, clippy, and tests;
Ruff lint and format; mypy; pytest; and the custom validators) and reports every
failure at once:

```sh
python scripts/check.py
```

Pass `--reporter agent` for machine-readable JSON. Please make sure this passes
before opening a pull request. There is no pre-commit hook by design: the check
is an explicit command you run, not something that rewrites your files on commit.

When you work on the Rust core, `maturin develop` (inside the venv) is the fast
inner loop for rebuilding the extension.

## Making a change

- **Write tests.** New or changed behavior comes with tests; they are the
  evidence the change works and the guard against regressions.
- **Keep the CHANGELOG honest.** Add a `CHANGELOG.md` entry only when the change
  is observable to a user of the package (see the CHANGELOG section in
  [`CLAUDE.md`](CLAUDE.md)); skip it for internal refactors and tooling.
- **Mind the cross-language contract.** The grammar, the AST, and the compiler
  output are a contract shared across host-language bindings. If you touch one of
  them, read the high-risk notes in [`CLAUDE.md`](CLAUDE.md) first.

## Opening a pull request

Fill in the pull request template, make sure `python scripts/check.py` passes,
and link any related issue. Reviews route through the maintainer (see
[`.github/CODEOWNERS`](.github/CODEOWNERS)).

## Releases

Releases are per-package, triggered by pushing a git tag named for the package
and version: `citry@X.Y.Z` for the Python package and `citry-core@X.Y.Z` for the
Rust-backed bindings (a tag with no language prefix means the Python package).
The tagged version must match the package's `pyproject.toml`. See
[`docs/codebase.md`](docs/codebase.md) for the full release flow.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating
you agree to uphold it.
