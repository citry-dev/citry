# Provider runtime exploration environment

Run from the repository root after installing Citry's e2e dependency group and
the three Playwright browsers:

```bash
uv sync --frozen --package citry --group e2e
uv run --frozen --package citry --group e2e \
  playwright install chromium firefox webkit
```

Reproduce the checked evidence:

```bash
provider_evidence="$(mktemp)"
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/provider_runtime/run_provider_runtime_spike.py \
  --output "$provider_evidence"
diff -u docs/design/i18n_research/provider_runtime/evidence.json \
  "$provider_evidence"
```

Repeat with Python optimization enabled:

```bash
provider_evidence_optimized="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/provider_runtime/run_provider_runtime_spike.py \
  --output "$provider_evidence_optimized"
diff -u docs/design/i18n_research/provider_runtime/evidence.json \
  "$provider_evidence_optimized"
```

Both diffs must be empty.
