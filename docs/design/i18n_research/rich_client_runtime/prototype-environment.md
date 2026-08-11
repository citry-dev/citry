# Rich-message ownership-runtime exploration environment

This Phase 0 slice checks the repeated rich-Slot protocol against Citry's real
browser ownership graph, Events fragment adoption, supplied-slot projection,
retained component ranges, and Alpine teleport behavior.

It runs four paths:

1. a browser-only switch that reorders an unchanged set of existing Slot
   occurrences in one task;
2. a server-backed Events fragment that adds and later removes an occurrence.
3. a keyed child that receives the original lazy Slot directly and checks
   caller-side Alpine scope;
4. a normal child Slot that forwards the original fill and is expected to hit
   the current ownership-manifest rejection.

It also runs Citry's existing native-component-clone rejection, supplied-Slot
teleport, and repeated-slot-mirror tests in all three browsers. The clone test
is the falsifier for creating a new Python Slot occurrence by copying its
server-rendered DOM. The other tests show that ordinary, unwrapped Slots still
keep their source ownership.

## Prepare

```bash
uv sync --frozen --package citry --group e2e
uv run --frozen --package citry --group e2e \
  playwright install chromium firefox webkit
```

## Run and reproduce

```bash
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client_runtime/run_rich_client_runtime_spike.py
```

```bash
probe_output="$(mktemp)"
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client_runtime/run_rich_client_runtime_spike.py \
  --output "$probe_output"
diff -u docs/design/i18n_research/rich_client_runtime/evidence.json "$probe_output"
```

```bash
probe_output="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client_runtime/run_rich_client_runtime_spike.py \
  --output "$probe_output"
diff -u docs/design/i18n_research/rich_client_runtime/evidence.json "$probe_output"
```
