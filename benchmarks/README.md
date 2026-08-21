# Benchmarks

Rendering-performance comparison between citry, django-components (DJC),
vanilla Django templates, and Jinja2. The design, scope, and roadmap live in
[`docs/design/benchmarking.md`](../docs/design/benchmarking.md); this README
covers running the comparison and reading its output.

Citry's graph-first browser workload has a separate runner because browser
startup, fragment adoption, morph, heap, and client payloads are not comparable
to server render time. Run it with:

```bash
uv run --no-sync python benchmarks/client.py \
  --browser chromium --counts 10 100 325 --rounds 9 --memory
```

It discards one cold round, reports median and p95, and rejects samples with
browser errors, incomplete runtime resources, or wrong initializer and
cleanup counts. `--json` emits the complete measurement record, including a
Git description whose `-dirty` suffix preserves uncommitted-run provenance.
Deterministic payload limits are enforced by
`packages/py/citry/tests/test_client_performance_payload.py`; browser timings
are informational. The exact workload, interpretation rules, and budgets are
recorded in
[`docs/design/alpinejs/a10_performance.md`](../docs/design/alpinejs/a10_performance.md).

The final i18n server gate has its own short bounded runner:

```bash
uv run --no-sync python benchmarks/i18n.py --json
```

It compares an equivalent literal tree with 100 warm message resolutions and
20 named ICU4X format calls. It also compiles 10,000 messages in each of three
locales and checks compile time, raw and compressed artifact size, and peak
memory. Five warmups and 30 render samples enforce the release limits in
`docs/design/i18n.md` section 14.3. Build `citry-core` in release mode first; a
debug native extension invalidates the timing result.

## How it works

The benchmarked code lives in `packages/py/citry/tests/` as self-contained
`test_benchmark_*.py` scenario files (one per engine and size), each exposing
`gen_render_data()` and `render(data)` entrypoints and verified by the normal
pytest suite. The runner never imports them: it reads each file as a source
string, slices out the pytest section at the file's markers (the upstream
django-components convention from
[PR #999](https://github.com/django-components/django-components/pull/999)),
and times the result in a fresh subprocess per round so no state leaks
between cells.

Engines:

| Row | What it is |
|---|---|
| `django` | Vanilla Django templates (vendored DJC scenario; it still imports django-components for `{% html_attrs %}`, so read it as "the relative cost of components", not pure Django) |
| `django-components` | The DJC component scenario, vendored byte-close to upstream |
| `citry` | The citry port of the same UI, plain inputs |
| `citry-const` | The same port with each component's render-invariant literals marked `Const` (the opt-in render-caching optimization, see `docs/design/component_constness.md`); large scenario only |
| `jinja2` | The same UI in Jinja2, the first engine beyond the Django family. Jinja2 has no component model, so each citry component becomes a macro; provide/inject is threaded as macro arguments, and each component's inline JS is collected by a per-render registry and injected at the `<c-js>` marker. Its `html_attrs` global stands in for Django's `{% html_attrs %}` tag. Both scenarios |

Test types, mirroring upstream so the methodology stays comparable:

| Column | What is timed |
|---|---|
| `startup` | Running the whole scenario script: imports, class and template definitions, no render. Citry also completes its documented post-registration `initialize()` step. |
| `import` | Running only the scenario's import section |
| `first` | One render, template parse/compile included |
| `subsequent` | One render, after a warmup render in the same process |

## Running

From the repository root:

```bash
# 1. Install the baseline engines (not part of the default dev install)
uv pip install django==6.0.6 django-components==0.151.1 jinja2==3.1.6

# 2. REQUIRED: build the Rust extension in release mode. The default debug
#    build makes citry's Rust-backed paths many times slower and invalidates
#    every citry number. The runner cannot detect which build is installed.
cd packages/py/citry_core && ../../../.venv/bin/maturin develop --release && cd ../../..

# 3. Run the comparison
.venv/bin/python benchmarks/compare.py            # full: 5 rounds per cell
.venv/bin/python benchmarks/compare.py --quick    # smoke: 2 rounds, no import column
```

One more trap: the very first run after rebuilding the extension loads the
fresh `.so` cold (disk cache, macOS code signing), which can inflate the first
engine's numbers severalfold. Run once, discard, run again.

## Reading the results

The results are RELATIVE values, never absolute (the same rule as upstream
django-components):

- "citry renders this scenario N times faster than DJC on this machine" is a
  valid reading.
- "a render takes X microseconds, so my page will take X" is not: a real page
  has a different mix of templates, components, and data.
- Never compare numbers across machines, runs, or build profiles.

## Results (small scenario)

Measured 2026-08-20 on an Apple M4, macOS 26.6.2, Python 3.14.3, median of 5
fresh-process rounds per cell. Versions: django 6.0.6, django-components
0.151.1, jinja2 3.1.6, and the current Citry source declared as 0.4.1 with
citry-core 1.5.0 built in release mode. Ratios are vs the `django` row.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 81.80 ms (1.00x) | 90.06 ms (1.00x) | 1.10 ms (1.00x) | 42.5 us (1.00x) |
| django-components | 76.54 ms (0.94x) | 76.02 ms (0.84x) | 1.43 ms (1.29x) | 211.6 us (4.98x) |
| citry | 102.69 ms (1.26x) | 100.32 ms (1.11x) | 7.42 ms (6.73x) | 216.8 us (5.11x) |
| jinja2 | 13.09 ms (0.16x) | 12.83 ms (0.14x) | 1.15 ms (1.05x) | 25.3 us (0.60x) |

Highlights, with the relative-only caveat above:

- The two bare template engines (django, jinja2) do no per-render component
  work, so they lead the component engines (django-components, citry) on
  render time; the meaningful reading is within each pair.
- Citry is currently about 1.3x slower than django-components to start/import,
  about 5.2x slower on the first render, and effectively even once warm. The
  small scenario has only one component, so fixed application, extension, and
  template-analysis work dominates its first render.
- Jinja2 starts and imports about 5.9x faster than the Django stack. Its repeat
  render is about 1.7x faster than bare Django and about 8.4x faster than
  django-components.
- There is no `citry-const` row here. The single Button computes every value
  it renders from its inputs (the classes, the attributes), so nothing it
  returns is a render-invariant literal to mark constant. Const has a fair
  test in the large scenario, where there are static literals to mark.

The small scenario also has older dated tables in the results log
([`docs/design/benchmarking.md`](../docs/design/benchmarking.md) section 11),
measured on earlier code; compare rows within this run, never numbers across the
dated tables.

## Results (large scenario)

Measured 2026-08-21 on an Apple M4, macOS 26.6.2, Python 3.14.3, median of 5
fresh-process rounds per cell. Versions: django 6.0.6, django-components
0.151.1, jinja2 3.1.6, and the current Citry source declared as 0.4.1 with
citry-core 1.5.0 built in release mode. Ratios are vs the `django` row. The
large scenario is the full project-management page: 35 authored component
classes, about 350 rendered Citry component markers, JS dependency collection,
provide/inject, slots/fills, and dynamic elements. The current Citry render is
980,643 bytes, including its client dependency manager, Events/Alpine runtime,
and ownership graph. The Citry scenarios declare their repeated `HeroIcon` and
`ProjectOutputBadge` leaves pure; every engine still renders the same page.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 88.51 ms (1.00x) | 78.98 ms (1.00x) | 18.96 ms (1.00x) | 10.95 ms (1.00x) |
| django-components | 82.95 ms (0.94x) | 76.14 ms (0.96x) | 68.39 ms (3.61x) | 50.65 ms (4.63x) |
| citry | 116.03 ms (1.31x) | 99.04 ms (1.25x) | 76.59 ms (4.04x) | 38.65 ms (3.53x) |
| citry-const | 118.64 ms (1.34x) | 96.78 ms (1.23x) | 80.52 ms (4.25x) | 43.74 ms (3.99x) |
| jinja2 | 16.59 ms (0.19x) | 13.59 ms (0.17x) | 62.26 ms (3.28x) | 6.91 ms (0.63x) |

Highlights, with the relative-only caveat above:

- Against django-components (the fair component-to-component comparison),
  Citry is currently about 1.4x slower to start, 1.3x slower to import, and
  12% slower on the first render, but about 24% faster once warm.
- The result includes Citry's current ownership graph, client lifecycle,
  extension hooks, security-aware serialization, and much larger browser
  runtime. Those features are real shipped work, so this table does not
  disable them to preserve the older result.
- Jinja2 has no component model: each component is a macro. It starts/imports
  about 5x faster than the Django stack and repeats about 1.6x faster than bare
  Django and 7.2x faster than django-components. Its first render compiles the
  whole macro library and lands near django-components.
- `citry-const` did not help this page and was about 14% slower than the plain
  Citry row once warm in this run. Both Citry rows use the same explicit pure
  leaves; the const variant
  (`test_benchmark_citry_const.py`) marks each component's genuinely
  render-invariant values constant (literal attribute dicts, the theme, icon
  paths) and nothing else, which is the correct way to use Const. It folds
  almost nothing extra on this page because a real project page is mostly
  loops over per-render data, and a value marked constant stops being
  constant the moment it is iterated over or indexed into. Const pays off on
  templates with large blocks that are the same every render; a data-driven
  page is the opposite; its cache-key bookkeeping outweighs the little work
  it can fold here.

Historical note: the first large-scenario run had citry ~37x slower
than Django, which turned out to be a real O(n*depth) bug in citry's
dependency emission (a component's record was re-counted once per ancestor as
nested renders merged, so a 325-instance page resolved ~154,000 records).
Collapsing duplicate records before resolution fixed it (~32x faster repeat
renders) and is what the numbers above reflect. This is the large benchmark
doing its job: surfacing a real scaling bug that the small scenario could not.

The 2026-08-20 refresh did the same again: its first current-tree run took
about 912 ms warm because no-op render hooks repeatedly scanned every captured
ownership region. The first guard reduced that to 87.31 ms; indexed ownership
selection/retirement, exact-class asset derivation, dormant i18n paths,
single-pass manifest serialization, and the bounded traversal follow-ups then
reduced the latest authoritative rerun to 45.78 ms without changing its
986,021-byte output. See
[`docs/design/performance.md`](../docs/design/performance.md) section 10.

The follow-up allocation and specialization pass removed render-local cycles,
directly resolved compiler-proven component inputs, skipped dormant Events and
i18n work, and added conservative render-local pure-body plans. It moved the
  same five-process warm result to 38.65 ms with byte-identical 980,643-byte
output; section 10.8 records the staged evidence and the narrower pure-only
A/B.

## What's here

```
benchmarks/
    README.md    this file
    client.py    graph-first browser startup, adoption, morph, and heap runner
    client_scenario.py reusable production-shaped browser workload and payload sizing
    compare.py   the comparison runner (one table per scenario size)
    utils.py     marker slicing shared by runners
    plot.py      draws the project README chart from the large-scenario table
```

`plot.py` renders the charts shown in the project README and docs site from the
large-scenario numbers above. After re-measuring that table, update the data in
`plot.py` to match and re-run it:
`uv run --no-project --with matplotlib python benchmarks/plot.py`.

Still ahead: asv adoption (per-commit tracking, dashboards, memory
benchmarks), and more engines beyond the Django family (MiniJinja, JinjaX,
django-cotton, ...); see the design doc's section 8. Jinja2 is the first
beyond-Django-family engine, ported for both scenarios
(`test_benchmark_jinja2_small.py` and `test_benchmark_jinja2.py`).
