# Fluent runtime comparison environment

## Purpose

This is the second bounded i18n design probe. It compares released Python,
browser, and Rust Fluent runtimes without adding a dependency to a production
Citry package.

The exact candidate versions are:

- `fluent.runtime==0.4.0` and all of its resolved Python transitive packages,
  pinned in [python-requirements.txt](python-requirements.txt);
- `@fluent/bundle==0.19.1` and `esbuild==0.28.1`, locked by the local
  [browser lockfile](browser/pnpm-lock.yaml); and
- `fluent-bundle==0.16.0`, locked by the isolated
  [Rust lockfile](rust/Cargo.lock).

The Python requirements file provides exact version pins, not hash-enforced
artifact locking. The evidence records its digest, the active `uv` version, and
every pinned Fluent-runtime dependency version. A future release-ratification run must
add artifact hashes if reproducibility across package-index or wheel changes is
required.

The checked [evidence](evidence.json) records the exact Python, Node, pnpm,
`uv`, Rust, Cargo, operating-system, fixture, harness-source, package, and
lock/pin identities used on 2026-08-10. The browser candidate reports the
actually resolved `@fluent/bundle` version, and the orchestrator independently
checks the installed `esbuild` executable version.

## Reproduction

Install only the isolated browser dependencies:

```sh
cd docs/design/i18n_research/runtime_backend/browser
pnpm install --ignore-workspace --frozen-lockfile
cd ../../../../..
```

Then run the comparison from the repository root:

```sh
uv run --isolated --no-project \
  --with-requirements docs/design/i18n_research/runtime_backend/python-requirements.txt \
  python docs/design/i18n_research/runtime_backend/run_runtime_backend_spike.py
```

The runner invokes the browser and isolated Rust candidates, performs every
cross-runtime check with always-on validation, builds a minified ES2020 browser
artifact with 100 embedded messages, and prints deterministic JSON. Compare it
with the checked evidence:

```sh
diff -u \
  docs/design/i18n_research/runtime_backend/evidence.json \
  <(uv run --isolated --no-project \
    --with-requirements docs/design/i18n_research/runtime_backend/python-requirements.txt \
    python docs/design/i18n_research/runtime_backend/run_runtime_backend_spike.py)
```

Run the optimization compatibility check. The runner's separate Python AST
guard rejects `assert` statements in both Python harness files, so this smoke
run cannot silently rely on a stripped assertion:

```sh
PYTHONOPTIMIZE=1 uv run --isolated --no-project \
  --with-requirements docs/design/i18n_research/runtime_backend/python-requirements.txt \
  python docs/design/i18n_research/runtime_backend/run_runtime_backend_spike.py >/dev/null
```

The Rust crate uses the repository's Rust 2024 edition but contains its own
empty `[workspace]` table, so it does not alter Citry's root Cargo graph. The
browser directory is outside Citry's pnpm workspace. Generated Rust build
output and browser `node_modules` are disposable and are not evidence inputs.

## Fixed scope

The probe covers two locales; terms with literal grammatical parameters;
attributes; exact, cardinal, and ordinal selection through a Citry-owned
operation; Citry-owned number/date/scalar operations; strict resolution errors;
hostile scalar and catalog bidi controls; one typed rich placeholder; an
illustrative already-generated public reference/private-term artifact; a
malformed variable-valued term argument; and an upstream browser payload
baseline. The bidi matrix includes literal and Fluent-escaped catalog controls,
all seven Unicode bidi paragraph boundaries in scalar sinks, CRLF, and
per-paragraph wrapping of multiline catalog output.

It does not cover the complete locale matrix, real CLDR formatting, exact
Decimal or large-integer wire behavior, the authored-to-generated compiler,
production source maps, actual layer precedence/linking, fallback, production
PyO3 bindings, locale switching, structural Slot direction, a complete Citry
browser adapter, catalogs compiled to a public browser artifact, or concurrent
runtime benchmarks.
