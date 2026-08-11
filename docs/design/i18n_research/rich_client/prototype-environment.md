# Rich-message browser exploration environment

This Phase 0 slice answers one question: can repeated rich Slots move, appear,
and disappear during an in-page locale switch without losing application DOM
state, focus, ownership, cleanup, or language and direction semantics?

It uses the exact browser Fluent and esbuild versions already pinned by the
runtime-backend exploration. It runs the same semantic probe in Chromium,
Firefox, and WebKit through the repository's locked Playwright dependency.

## Prepare

From the repository root:

```bash
pnpm --dir docs/design/i18n_research/runtime_backend/browser install --frozen-lockfile
uv sync --frozen --package citry --group e2e
```

Install the matching browser binaries if they are not already present:

```bash
uv run --frozen --package citry --group e2e playwright install chromium firefox webkit
```

## Run and reproduce

```bash
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client/run_rich_client_spike.py
```

Compare a new result with the checked evidence:

```bash
probe_output="$(mktemp)"
uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client/run_rich_client_spike.py \
  --output "$probe_output"
diff -u docs/design/i18n_research/rich_client/evidence.json "$probe_output"
```

Run once with Python optimization to prove that no Python `assert` statement
can disappear and leave a false pass:

```bash
probe_output="$(mktemp)"
PYTHONOPTIMIZE=1 uv run --frozen --package citry --group e2e \
  python docs/design/i18n_research/rich_client/run_rich_client_spike.py \
  --output "$probe_output"
diff -u docs/design/i18n_research/rich_client/evidence.json "$probe_output"
```

The harness records hashes for itself, the browser code, every FTL fixture, the
generated browser bundle, and the shared package manifest and lockfile. It also
checks the active Fluent, esbuild, pnpm, uv, and Playwright versions before it
runs. The evidence records the Python, Node, operating-system, machine, browser,
and Playwright dependency versions used for the checked result.
