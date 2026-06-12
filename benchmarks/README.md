# Benchmarks

Rendering-performance comparison between citry, django-components (DJC), and
vanilla Django templates. The design, scope, and roadmap live in
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
| `citry-const` | The citry port with inputs `Const`-marked (the opt-in render-caching optimization, see `docs/design/constness.md`) |

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
uv pip install django==6.0.6 django-components==0.151.0

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

Measured 2026-06-12 on an Apple M4, Python 3.13.12, median of 5 fresh-process
rounds per cell. Versions: django 6.0.6, django-components 0.151.0, citry
0.1.0 (citry_core 1.3.0, release build). Ratios are vs the `django` row.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 75.35 ms (1.00x) | 71.45 ms (1.00x) | 1.11 ms (1.00x) | 39.5 us (1.00x) |
| django-components | 72.47 ms (0.96x) | 72.05 ms (1.01x) | 1.44 ms (1.29x) | 206.6 us (5.23x) |
| citry | 25.96 ms (0.34x) | 26.08 ms (0.37x) | 866.6 us (0.78x) | 58.9 us (1.49x) |
| citry-const | 26.05 ms (0.35x) | 25.80 ms (0.36x) | 849.7 us (0.76x) | 64.4 us (1.63x) |

Highlights, with the relative-only caveat above:

- citry imports and starts up about 3x faster than the Django stack.
- On repeat renders citry is about 3.5x faster than django-components,
  though still ~1.5x slower than a bare Django template (the gap is the
  component machinery: per-render component construction, slot resolution,
  and id marking).
- `citry-const` shows no benefit on this scenario, and its repeat renders sit
  within noise of (or slightly behind) plain citry: the Button template is
  one element, so almost nothing is left to fold, while computing the
  fold-cache key still costs a little per render. The optimization is built
  for templates with large constant regions; the large scenario (phase 3)
  is where it gets a fair test.

## What's here

```
benchmarks/
    README.md    this file
    compare.py   the comparison runner (one table per scenario size)
    utils.py     marker slicing shared by runners
```

The large (`lg`) scenario, asv adoption (per-commit tracking, dashboards,
memory benchmarks), and engines beyond the Django family (Jinja2, MiniJinja,
JinjaX, ...) are later phases; see the design doc's section 8.
