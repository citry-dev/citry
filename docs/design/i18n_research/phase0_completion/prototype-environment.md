# Phase 0 completion environment

The checked [evidence](evidence.json) was produced on 2026-08-10 on arm64
macOS. Timing values are in the separate host-specific
[performance file](performance.json).

## Versions

- Python 3.13.12
- Node 26.5.0
- Playwright 1.62.0
- Chromium 151.0.7922.34
- Firefox 153.0
- WebKit 26.5
- esbuild 0.28.1
- `@fluent/bundle` 0.19.1

The browser dependency versions are locked in the runtime comparison's
[`pnpm-lock.yaml`](../runtime_backend/browser/pnpm-lock.yaml). The Citry and
Playwright dependencies come from the repository `uv.lock`.

## Prepare

From the repository root:

```bash
uv sync --frozen --package citry --group e2e
uv run --frozen --package citry --group e2e \
  playwright install chromium firefox webkit
cd docs/design/i18n_research/runtime_backend/browser
pnpm install --ignore-workspace --frozen-lockfile
cd ../../../../..
```

Regenerate the production-shaped server evidence and benchmark first:

```bash
uv run --frozen python \
  docs/design/i18n_research/production_slice/run_production_slice.py \
  --benchmark-iterations 25 \
  --output docs/design/i18n_research/production_slice/evidence.json \
  --benchmark-output docs/design/i18n_research/production_slice/benchmark.json
```

Then reproduce this slice:

```bash
tmp_evidence="$(mktemp)"
tmp_performance="$(mktemp)"
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/phase0_completion/run_phase0_completion.py \
  --output "$tmp_evidence" \
  --measurements "$tmp_performance"
diff -u docs/design/i18n_research/phase0_completion/evidence.json \
  "$tmp_evidence"
```

The evidence diff must be empty. Actual timing values may vary, so compare the
new performance file to the recorded thresholds rather than expecting a byte-
for-byte match.

Repeat the deterministic evidence check with optimized Python:

```bash
tmp_evidence_optimized="$(mktemp)"
tmp_performance_optimized="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/phase0_completion/run_phase0_completion.py \
  --output "$tmp_evidence_optimized" \
  --measurements "$tmp_performance_optimized"
diff -u docs/design/i18n_research/phase0_completion/evidence.json \
  "$tmp_evidence_optimized"
```

## Static checks

```bash
uv run --frozen ruff check \
  docs/design/i18n_research/phase0_completion/run_phase0_completion.py
uv run --frozen ruff format --check \
  docs/design/i18n_research/phase0_completion/run_phase0_completion.py
node --check \
  docs/design/i18n_research/phase0_completion/browser/complete_payload.mjs
node --check \
  docs/design/i18n_research/phase0_completion/browser/switch_benchmark.js
python -m json.tool \
  docs/design/i18n_research/phase0_completion/evidence.json >/dev/null
```

The Python harness has an AST guard against optimization-sensitive `assert`
statements. It also rejects JavaScript `console.assert` before it runs.
