# Fluent semantic-span probe environment

The checked [evidence](evidence.json) was produced on 2026-08-10 from the
standalone Rust crate in this directory. The crate depends on
`fluent-syntax` 0.12.0 and parses the checked adversarial fixture through the
crate's public generic `Slice` interface.

No upstream issue, pull request, branch, comment, or other external state was
created or changed during this exploration.

## Versions

- Python 3.13.12
- Rust 1.98.0-nightly (2026-05-31)
- Cargo 1.98.0-nightly (2026-05-26)
- `fluent-syntax` 0.12.0
- macOS 26.6 on arm64

The exact Rust dependency closure is in [Cargo.lock](Cargo.lock). The evidence
records the digest of the lock, manifest, fixture, Rust probe, and Python
orchestrator. It intentionally contains no Git commit identifier, so committing
the evidence does not make it self-invalidating.

## Upstream snapshot

The read-only upstream audit inspected `projectfluent/fluent-rs` main at commit
`b822cfe0ac5f35099ee71d3cf6f43b7c01d5fc6d`. At that revision:

- the successful AST remains spanless;
- the parser's `Slice` trait remains public and generic;
- [issue 270](https://github.com/projectfluent/fluent-rs/issues/270) is the open
  request for parser spans; and
- [issue 346](https://github.com/projectfluent/fluent-rs/issues/346) is closed
  as a duplicate of issue 270.

These observations are recorded research context, not inputs fetched during a
normal evidence replay.

## Reproduction

From the repository root:

```console
uv run --frozen python \
  docs/design/i18n_research/span_parser/run_span_parser_spike.py \
  --output /tmp/citry-i18n-span-evidence.json

diff -u \
  docs/design/i18n_research/span_parser/evidence.json \
  /tmp/citry-i18n-span-evidence.json
```

The same command is run with `PYTHONOPTIMIZE=1`. After normalizing only
`environment.python_optimize` from `1` to `0`, it must remain byte-identical to
the checked evidence. The Python runner contains no `assert` statement; the
Rust probe uses always-on result gates.

Rust checks:

```console
cargo fmt \
  --manifest-path docs/design/i18n_research/span_parser/Cargo.toml \
  -- --check

cargo clippy \
  --manifest-path docs/design/i18n_research/span_parser/Cargo.toml \
  --locked --all-targets -- -D warnings

cargo test \
  --manifest-path docs/design/i18n_research/span_parser/Cargo.toml \
  --locked
```

Python checks:

```console
uv run --frozen ruff check \
  docs/design/i18n_research/span_parser/run_span_parser_spike.py
uv run --frozen ruff format --check \
  docs/design/i18n_research/span_parser/run_span_parser_spike.py
```

The generated `target` directory is not an evidence input and must not be
committed.
