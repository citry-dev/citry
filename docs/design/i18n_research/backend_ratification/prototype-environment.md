# Backend ratification environment

Run from the repository root. The Rust workspace has its own exact lock file.

Reproduce the checked evidence:

```bash
backend_evidence="$(mktemp)"
uv run --frozen --package citry \
  python docs/design/i18n_research/backend_ratification/run_backend_ratification_spike.py \
  --output "$backend_evidence"
diff -u docs/design/i18n_research/backend_ratification/evidence.json \
  "$backend_evidence"
```

Repeat with Python optimization enabled:

```bash
backend_evidence_optimized="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry \
  python docs/design/i18n_research/backend_ratification/run_backend_ratification_spike.py \
  --output "$backend_evidence_optimized"
diff -u docs/design/i18n_research/backend_ratification/evidence.json \
  "$backend_evidence_optimized"
```

Both diffs must be empty. The runner also performs Rust formatting and Clippy
checks, builds both release binaries with `--locked`, checks its own source for
optimization-sensitive `assert` statements, and runs the Node `Intl`
comparison.
