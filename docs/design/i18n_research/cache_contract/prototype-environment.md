# Cache contract exploration environment

Run from the repository root.

Reproduce the checked evidence:

```bash
cache_evidence="$(mktemp)"
uv run --frozen --package citry \
  python docs/design/i18n_research/cache_contract/run_cache_contract_spike.py \
  --output "$cache_evidence"
diff -u docs/design/i18n_research/cache_contract/evidence.json \
  "$cache_evidence"
```

Repeat with Python optimization enabled:

```bash
cache_evidence_optimized="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry \
  python docs/design/i18n_research/cache_contract/run_cache_contract_spike.py \
  --output "$cache_evidence_optimized"
diff -u docs/design/i18n_research/cache_contract/evidence.json \
  "$cache_evidence_optimized"
```

Both diffs must be empty.

Run the focused existing replay baselines:

```bash
uv run --frozen --package citry pytest -q \
  packages/py/citry/tests/test_ext_cache_replay.py::TestCoreArtifactReplay::test_transparent_descendant_dependencies_are_replayed \
  packages/py/citry/tests/test_ext_cache_replay.py::TestCoreArtifactReplay::test_dependencies_replay_repairs_evicted_variable_script
```

Both tests must pass.
