# Benchmarks

Rendering-performance comparison between citry, django-components (DJC),
vanilla Django templates, and Jinja2. The design, scope, and roadmap live in
[`docs/design/benchmarking.md`](../docs/design/benchmarking.md); this README
covers running the comparison and reading its output.

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
| `citry-const` | The same port with each component's render-invariant literals marked `Const` (the opt-in render-caching optimization, see `docs/design/constness.md`); large scenario only |
| `jinja2` | The same UI in Jinja2, the first engine beyond the Django family. Jinja2 has no component model, so each citry component becomes a macro; provide/inject is threaded as macro arguments, and each component's inline JS is collected by a per-render registry and injected at the `<c-js>` marker. Its `html_attrs` global stands in for Django's `{% html_attrs %}` tag. Both scenarios |

Test types, mirroring upstream so the methodology stays comparable:

| Column | What is timed |
|---|---|
| `startup` | Running the whole scenario script: imports, class and template definitions, no render |
| `import` | Running only the scenario's import section |
| `first` | One render, template parse/compile included |
| `subsequent` | One render, after a warmup render in the same process |

## Running

From the repository root:

```bash
# 1. Install the baseline engines (not part of the default dev install)
uv pip install django==6.0.6 django-components==0.151.0 jinja2==3.1.6

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

Measured 2026-06-25 on an Apple M4, Python 3.13.12, median of 5 fresh-process
rounds per cell. Versions: django 6.0.6, django-components 0.151.0, jinja2
3.1.6, citry 0.1.0 (citry_core 1.3.0, release build). Ratios are vs the
`django` row.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 79.21 ms (1.00x) | 77.37 ms (1.00x) | 1.06 ms (1.00x) | 41.0 us (1.00x) |
| django-components | 78.86 ms (1.00x) | 77.28 ms (1.00x) | 1.41 ms (1.33x) | 199.4 us (4.86x) |
| citry | 29.80 ms (0.38x) | 29.20 ms (0.38x) | 1.53 ms (1.45x) | 71.5 us (1.74x) |
| jinja2 | 14.68 ms (0.19x) | 14.26 ms (0.18x) | 1.21 ms (1.15x) | 23.2 us (0.57x) |

Highlights, with the relative-only caveat above:

- The two bare template engines (django, jinja2) do no per-render component
  work, so they lead the component engines (django-components, citry) on
  render time; the meaningful reading is within each pair.
- jinja2 is the fast no-component baseline it is known for: it imports and
  starts up about 5x faster than the Django stack, and its repeat render is
  about 1.8x faster than a bare Django template (and ~8.6x faster than
  django-components). It pays for that on first render (1.15x), where
  compiling the template to Python bytecode costs a little more than Django's
  parse; the speed shows up on every render after.
- citry imports and starts up about 2.6x faster than the Django stack.
- On repeat renders citry is about 2.8x faster than django-components, the
  fair component-to-component comparison. It trails the two bare template
  engines, which skip the component lifecycle citry runs each render
  (component construction, slot resolution, id marking).
- There is no `citry-const` row here. The single Button computes every value
  it renders from its inputs (the classes, the attributes), so nothing it
  returns is a render-invariant literal to mark constant. Const has a fair
  test in the large scenario, where there are static literals to mark.

The small table was last measured 2026-06-12, before the phase-3 feature and
render-path work landed, so its citry numbers differ from that older table;
compare rows within this run, never numbers across the dated tables.

## Results (large scenario)

Measured 2026-06-25 on an Apple M4, Python 3.13.12, median of 5 fresh-process
rounds per cell. Versions: django 6.0.6, django-components 0.151.0, jinja2
3.1.6, citry 0.1.0 (citry_core 1.3.0, release build). Ratios are vs the
`django` row. The large scenario is the full project-management page: 35
components, ~325 component instances rendered, JS dependency collection,
provide/inject, slots/fills, and dynamic elements.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 81.90 ms (1.00x) | 76.78 ms (1.00x) | 17.82 ms (1.00x) | 10.78 ms (1.00x) |
| django-components | 82.25 ms (1.00x) | 76.73 ms (1.00x) | 65.45 ms (3.67x) | 46.02 ms (4.27x) |
| citry | 38.36 ms (0.47x) | 28.64 ms (0.37x) | 37.79 ms (2.12x) | 13.65 ms (1.27x) |
| citry-const | 38.02 ms (0.46x) | 29.19 ms (0.38x) | 38.44 ms (2.16x) | 14.82 ms (1.37x) |
| jinja2 | 18.16 ms (0.22x) | 14.54 ms (0.19x) | 58.93 ms (3.31x) | 6.06 ms (0.56x) |

Highlights, with the relative-only caveat above:

- citry imports and starts up about 2x faster than the Django stack.
- Against django-components (the fair comparison, since both pay the
  component-machinery cost) citry is about 1.7x faster on first render and
  about 3.4x faster on repeat renders.
- Both component engines are slower than a bare Django template, which does
  none of the per-render component work (construction, slots, dependency
  collection, id marking); the relevant question is the relative cost of
  using components, and there citry wins. After a round of render-path
  optimization (see the section 11 log in `docs/design/benchmarking.md`),
  citry's repeat render is about 1.3x a bare Django template, down from 1.85x.
- jinja2 (no component model: each component is a macro) is the fastest engine
  to start up and import (about 5x the Django stack, about 2x citry) and has
  the fastest repeat render of any engine here (0.56x a bare Django template,
  about 7.6x faster than django-components), because each render just runs
  pre-compiled macro bytecode. It pays for that on first render (3.31x), where
  the whole macro library compiles at once. The classic compiled-template
  trade-off, at page scale: slowest to warm up, fastest once warm.
- `citry-const` is within noise of plain citry here. The const variant
  (`test_benchmark_citry_const.py`) marks each component's genuinely
  render-invariant values constant (literal attribute dicts, the theme, icon
  paths) and nothing else, which is the correct way to use Const. It folds
  almost nothing extra on this page because a real project page is mostly
  loops over per-render data, and a value marked constant stops being
  constant the moment it is iterated over or indexed into. Const pays off on
  templates with large blocks that are the same every render; a data-driven
  page is the opposite, so the honest result here is "no speedup."

A note on getting here: the first large-scenario run had citry ~37x slower
than Django, which turned out to be a real O(n*depth) bug in citry's
dependency emission (a component's record was re-counted once per ancestor as
nested renders merged, so a 325-instance page resolved ~154,000 records).
Collapsing duplicate records before resolution fixed it (~32x faster repeat
renders) and is what the numbers above reflect. This is the large benchmark
doing its job: surfacing a real scaling bug that the small scenario could not.

## What's here

```
benchmarks/
    README.md    this file
    compare.py   the comparison runner (one table per scenario size)
    utils.py     marker slicing shared by runners
    plot.py      draws the project README chart from the large-scenario table
```

`plot.py` renders the chart shown in the project README from the large-scenario
numbers above. After re-measuring that table, update the data in `plot.py` to
match and re-run it: `uv run --no-project --with matplotlib python benchmarks/plot.py`.

Still ahead: asv adoption (per-commit tracking, dashboards, memory
benchmarks), and more engines beyond the Django family (MiniJinja, JinjaX,
django-cotton, ...); see the design doc's section 8. Jinja2 is the first
beyond-Django-family engine, ported for both scenarios
(`test_benchmark_jinja2_small.py` and `test_benchmark_jinja2.py`).
