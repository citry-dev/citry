# Percent, unit, and date-editing exploration environment

This is a design probe. It adds no production dependency and does not implement
a formatter profile.

## Checked versions

- ICU4X 2.2.0
- `icu_experimental` 0.5.0
- Node 26.5.0, ICU 78.3, CLDR 48
- Playwright 1.62.0
- Chromium 151.0.7922.34
- Firefox 153.0
- WebKit 26.5
- Rust 1.98.0-nightly

The exact Rust dependency closure is in [`rust/Cargo.lock`](rust/Cargo.lock).
The browser versions come from the repository's frozen `uv.lock` and installed
Playwright binaries.

## Reproduce the server comparison

From the repository root:

```bash
cargo run \
  --locked \
  --manifest-path docs/design/i18n_research/formatting_followup/rust/Cargo.toml
```

The probe formats Arabic metres and percentages from exact `fixed_decimal`
values. It also prints the plural operands and category used by ICU4X.

## Reproduce Node `Intl`

```bash
node docs/design/i18n_research/formatting_followup/browser/probe.mjs
```

The output records Node, V8, ICU, CLDR, Unicode, and tzdb versions and includes
`formatToParts()` so invisible separators and bidi literals remain visible.

## Reproduce the three-browser result

Install the repository's existing browser test group and matching browsers if
needed:

```bash
uv sync --frozen --package citry --group e2e
uv run --frozen --package citry --group e2e \
  playwright install chromium firefox webkit
```

Then run:

```bash
uv run --frozen --package citry --group e2e \
  python \
  docs/design/i18n_research/formatting_followup/browser/probe_playwright.py
```

The script prints each browser's user agent and the same Arabic percent, unit,
and exact-decimal plural cases.

## Scope limits

This probe does not implement or ratify a Citry profile. It does not measure
payload size, every CLDR unit, grammatical case, compound units, unit
conversion, percent parsing, or a date control. It answers the narrower design
questions recorded in the report and identifies the standards and upstream
work that the production design must follow.
