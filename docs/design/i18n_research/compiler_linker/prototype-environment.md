# Fluent compiler/linker spike environment

## Purpose

This is the fourth bounded i18n design probe. It starts from ordinary authored
Fluent catalogs, links the configured package and application layers, lowers
Citry-owned operations, and executes the generated artifacts in the same three
runtime candidates used by the runtime comparison.

It is research code under `docs/design`. It does not add a dependency to a
production Citry package and does not select the eventual implementation
language or PyO3 boundary.

The exact candidate versions are:

- `fluent.syntax==0.19.0`, `fluent.runtime==0.4.0`, and their exact Python
  transitive pins in [python-requirements.txt](python-requirements.txt);
- `@fluent/bundle==0.19.1`, installed from the existing runtime-spike
  [browser lockfile](../runtime_backend/browser/pnpm-lock.yaml); and
- `fluent-bundle==0.16.0`, locked by this spike's isolated
  [Rust lockfile](rust/Cargo.lock).

The Python requirements are exact version pins rather than hash-enforced
package artifacts. The runner requires an isolated environment whose complete
installed distribution inventory equals those pins. Its evidence also records
the active Python, uv, Node, pnpm, Rust, Cargo, operating-system, source,
fixture, manifest, and lockfile identities. The browser helper reports its
actually loaded `@fluent/bundle` version.

## Reproduction

Install the browser runtime used by both Fluent spikes:

```sh
cd docs/design/i18n_research/runtime_backend/browser
pnpm install --ignore-workspace --frozen-lockfile
cd ../../../../..
```

Run the compiler/linker comparison from the repository root:

```sh
uv run --isolated --no-project \
  --with-requirements docs/design/i18n_research/compiler_linker/python-requirements.txt \
  python docs/design/i18n_research/compiler_linker/run_compiler_linker_spike.py
```

Compare it with the checked evidence:

```sh
diff -u \
  docs/design/i18n_research/compiler_linker/evidence.json \
  <(uv run --isolated --no-project \
    --with-requirements docs/design/i18n_research/compiler_linker/python-requirements.txt \
    python docs/design/i18n_research/compiler_linker/run_compiler_linker_spike.py)
```

Run the optimization compatibility check:

```sh
PYTHONOPTIMIZE=1 uv run --isolated --no-project \
  --with-requirements docs/design/i18n_research/compiler_linker/python-requirements.txt \
  python docs/design/i18n_research/compiler_linker/run_compiler_linker_spike.py >/dev/null
```

The runner parses its own Python source and rejects any `assert` statement, so
the optimized run cannot silently remove a load-bearing Python check. The Rust
candidate uses the repository's Rust 2024 edition and an empty local
`[workspace]`, leaving the root Cargo graph unchanged. Generated Rust build
output and browser `node_modules` are disposable and are not evidence inputs.

## Fixed scope

The fixture topology has two active locales, two packages with different source
locales, a lower library layer, and a higher application layer. It exercises
per-owner source fallback, application overrides, independent attribute
fallback, public message references, layer-private terms, transitive typed
inputs, repeated rich Slots, exact/cardinal/ordinal selection, named number
profiles, deterministic discovery, source maps, and four negative compiler
canaries.

It does not cover the complete Fluent language, configurable intermediate
fallbacks, dynamic catalog loading, exact wire types, real CLDR formatting,
production diagnostic objects, a Rust/PyO3 compiler binding, browser artifact
loading, locale switching, structural Slot direction, DOM ownership, caching,
or performance.
