# Production-shaped Phase 0 slice environment

The checked [evidence](evidence.json) was produced on 2026-08-10 from the
standalone PyO3 crate in [`rust`](rust), the checked fixtures, and the current
Citry source tree. The evidence includes hashes for the harness, every fixture,
the Rust manifest, lock, source, Python package initializer, and actual compiled
extension. It also hashes the Citry files and loaded `citry_core._rust` binary
used by the integration proof.

The slice deliberately builds a wheel and imports its compiled extension. It
does not load Rust code through a test-only executable or Python reimplementation.

## Versions

- Python 3.13.12
- Rust 1.98.0-nightly (2026-05-31)
- Cargo 1.98.0-nightly (2026-05-26)
- maturin 1.14.1
- PyO3 0.27.1
- `fluent-syntax` 0.12.0
- `fluent-bundle` 0.16.0
- macOS 26.6 on arm64

The exact Rust transitive dependency closure is in
[`rust/Cargo.lock`](rust/Cargo.lock). Python and maturin run from the repository
`uv.lock`; the evidence records that lock's digest.

## Reproduction

From the repository root:

```console
uv run --frozen python \
  docs/design/i18n_research/production_slice/run_production_slice.py \
  --benchmark-iterations 25 \
  --output /tmp/i18n-production-slice-evidence.json \
  --benchmark-output /tmp/i18n-production-slice-benchmark.json

diff -u \
  docs/design/i18n_research/production_slice/evidence.json \
  /tmp/i18n-production-slice-evidence.json
```

The same evidence path was also run with `PYTHONOPTIMIZE=1`. After normalizing
only `environment.python_optimize` from `1` to `0`, it was byte-identical to the
checked evidence. The runner uses always-on `require()` gates and contains no
load-bearing Python `assert` statements.

Rust checks:

```console
cargo fmt \
  --manifest-path docs/design/i18n_research/production_slice/rust/Cargo.toml \
  -- --check

cargo clippy \
  --manifest-path docs/design/i18n_research/production_slice/rust/Cargo.toml \
  --locked --all-targets -- -D warnings

cargo test \
  --manifest-path docs/design/i18n_research/production_slice/rust/Cargo.toml \
  --locked
```

Python checks:

```console
uv run --frozen ruff check \
  docs/design/i18n_research/production_slice/run_production_slice.py
uv run --frozen ruff format --check \
  docs/design/i18n_research/production_slice/run_production_slice.py
```

## Benchmark scope

The checked [benchmark](benchmark.json) is host-specific and is intentionally
separate from deterministic evidence. It measured the four-catalog fixture,
including selectors, formatter calls, typed interfaces, and exact source maps:

- cold compile: 4.824 ms;
- mean of 25 warm compiles: 4.123 ms;
- one-catalog edit and relink: 4.279 ms;
- 100 message resolutions plus 20 named format calls added 1.483 ms at
  median and 1.508 ms at p95 over 30 samples; and
- the unconfigured literal tree stayed inside the configured literal tree's
  95% mean confidence interval.

These numbers show that the prototype is not obviously pathological. They do
not cover the final ICU4X adapter, large real catalogs, Linux and wheel targets,
or browser budgets. The separate Phase 0 completion slice measures the browser
payload and loaded switch gates.
