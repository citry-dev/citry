# Source-aware rich-Slot relocation environment

This Phase 0 exploration uses Citry's real client graph and direct Slot-region
comments. A small research candidate performs the proposed preflight and
same-task relocation without changing the shipped runtime.

## Prepare

```bash
uv sync --frozen --package citry --group e2e
uv run --frozen --package citry --group e2e \
  playwright install chromium firefox webkit
```

## Reproduce the checked evidence

Run from the repository root:

```bash
tmp_evidence="$(mktemp)"
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client_relocation/run_rich_client_relocation_spike.py \
  --output "$tmp_evidence"
diff -u docs/design/i18n_research/rich_client_relocation/evidence.json \
  "$tmp_evidence"
```

The diff must be empty.

## Reproduce with Python optimization enabled

The harness rejects optimization-sensitive Python `assert` statements and
JavaScript `console.assert` calls before running its browser checks. Verify the
same evidence under optimized Python:

```bash
tmp_evidence_optimized="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client_relocation/run_rich_client_relocation_spike.py \
  --output "$tmp_evidence_optimized"
diff -u docs/design/i18n_research/rich_client_relocation/evidence.json \
  "$tmp_evidence_optimized"
```

The optimized diff must also be empty.

## Static checks

```bash
uv run --frozen --package citry ruff check \
  docs/design/i18n_research/rich_client_relocation/run_rich_client_relocation_spike.py
uv run --frozen --package citry ruff format --check \
  docs/design/i18n_research/rich_client_relocation/run_rich_client_relocation_spike.py
node --check docs/design/i18n_research/rich_client_relocation/browser/candidate.js
node --check docs/design/i18n_research/rich_client_relocation/browser/probe.js
python -m json.tool \
  docs/design/i18n_research/rich_client_relocation/evidence.json >/dev/null
```
