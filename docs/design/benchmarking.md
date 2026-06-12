# Design: rendering benchmarks (citry vs django-components vs Django)

**Status (2026-06-12): phases 1 and 2 built.** Phase 1: small scenario
(vendored Django/DJC files + citry port with the `CONST_MODE` switch,
`benchmark` dependency group), verified by pytest. Phase 2: the
`benchmarks/compare.py` runner, `benchmarks/utils.py` slicing helpers, and
`benchmarks/README.md` with the first published numbers (citry ~3x faster
startup/import, ~3.5x faster repeat renders than DJC on the small scenario).
Features A and B from section 6.3 landed separately (commits `8b80c66`,
`39824bb`); feature C still gates phase 3. Phases 4 and 5 not started.
This document
specifies how citry measures its template-rendering performance against
django-components (DJC) and vanilla Django templates: where the benchmark code
lives, how the harness runs it, what the two benchmark scenarios contain, and
which citry features are still missing to port them fully. Engines beyond the
Django family (Jinja2, MiniJinja, and others) are catalogued as future
additions in section 2.1.

For the migration context (what citry keeps and drops from DJC) see
[`citry_migration.md`](citry_migration.md). For the Const optimization that
the `citry-const` variant exercises see [`constness.md`](constness.md).
For the JS/CSS dependency rendering that gates the large scenario see
[`asset_loading.md`](asset_loading.md) section 7.4. For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: django-components
[PR #999](https://github.com/django-components/django-components/pull/999)
(the benchmark suite and the "benchmarked code doubles as a pytest test"
convention this design reuses).

---

## 1. Prior art (what was searched)

In `~/repos/django-components` (the upstream repo, source of the scenarios):

- **`benchmarks/benchmark_templating.py`** (442 lines) is the whole asv
  benchmark suite. Two parametrized groups ("Components vs Django",
  "isolated vs django modes"), each measured across sizes (`sm`/`lg`),
  test types (`first` render, `subsequent` render, `startup`), and metrics
  (`timeraw_` wall time, `peakmem_` peak memory), plus one import-time test.
- **`benchmarks/utils.py:15`**: the `@benchmark(...)` decorator that maps
  friendly names, groups, and params onto asv's function-attribute
  conventions. `utils.py:71` `create_virtual_module` execs a source string as
  an importable module (needed for `peakmem_` tests, which run in-process).
- **`tests/test_benchmark_{django,djc}{,_small}.py`**: the benchmarked code
  itself, four fully self-contained scripts (inline `settings.configure`, all
  components, all data, a `gen_render_data()` and `render(data)` entrypoint
  at the top). Each ends with a pytest snapshot test, so the benchmark code
  is verified by the normal test suite.
- **The slicing trick** (`benchmark_templating.py:52-79`): the runner never
  imports the test files. It reads them as source strings, cuts at the
  `# ----------- TESTS START ------------ #` marker (dropping the pytest
  part), optionally cuts at `# ----------- IMPORTS END ------------ #` (for
  the import-time test), and regex-overrides the `CONTEXT_MODE` constant.
  `timeraw_` benchmarks return that string to be executed in a fresh process;
  `peakmem_` benchmarks exec it as a virtual module in-process.
- **`asv.conf.json`**: `virtualenv` environments, per-commit install via
  `pip install ./project`, results committed to the repo, HTML dashboard
  published with the docs site.
- **CI**: `pr-benchmark-generate.yml` + `pr-benchmark-comment.yml` run
  `asv continuous` between master and the PR head and post the comparison as
  a PR comment. `DJC_BENCHMARK_QUICK=1` trims the suite to the single test
  flagged `include_in_quick_benchmark` (`benchmark_templating.py:224`),
  because the full suite takes ~10 minutes. Release tags run the full suite
  and publish the dashboard.
- **Interpretation rules** (`benchmarks/README.md`): results are relative
  only, never absolute. Their "Django" variant still imports
  django-components and uses `{% html_attrs %}`, so it measures "the relative
  cost of using components", not pure vanilla Django. Citry inherits both
  caveats.

In this repo:

- **`packages/py/citry/tests/benchmark_const.py`**: the existing script-style
  benchmark (Const optimization). Establishes local conventions this design
  follows: plain script not collected by pytest, warmup render, output
  equality assert before timing, and the release-build warning (a debug
  `citry_core` build makes serialization ~12x slower and invalidates every
  number).
- **`packages/py/citry_core/tests/benchmark.py`** and **`benchmark_eval.py`**:
  micro-benchmarks of the Rust HTML transformer and of `safe_eval` dispatch.
  Different layer (citry_core primitives, not component rendering); they stay
  as they are.
- **`old_djccore_benchmark_eval.py`** (repo root): the djc-core ancestor of
  `benchmark_eval.py`, kept for reference.
- **The vendoring pattern**: `packages/py/citry/_djc_reference/` and
  `packages/py/citry/tests/_djc_tests/` already hold DJC material copied into
  this repo for porting work. Vendoring the DJC benchmark files continues an
  established pattern.
- **`docs/codebase.md`** "Running tests" and the root `pyproject.toml`:
  Python dev deps are mirrored between each package's
  `[dependency-groups].dev` and the root extras; any new benchmark deps must
  follow the same mirroring (until the uv workspace conversion,
  [#8](https://github.com/JuroOravec/citry/issues/8)).

---

## 2. Goal and scope

Two distinct uses, one set of benchmark files:

1. **Cross-engine comparison**: how does rendering the same UI compare across
   citry, django-components, and vanilla Django templates? This is a
   marketing-grade and sanity-grade number ("is the Rust-parser architecture
   paying off?") measured at one point in time.
2. **Longitudinal tracking**: how does citry's own rendering performance move
   commit to commit? This is what asv is for, and it only makes sense for
   citry's history (Django and DJC are pinned baselines that do not change).

Micro-benchmarks of citry_core primitives stay out of scope (they already
exist, section 1). Engines beyond the Django family are in scope as future
additions, below.

### 2.1 Future comparison targets beyond the Django family

The engine axis is open-ended by design: each engine is one self-contained
scenario file (section 5.2), so adding an engine never touches the others.
The Django family ships first because the scenarios come from DJC and stay
byte-comparable there. Candidates for follow-up engines, from a June 2026
scan of the Python HTML-rendering landscape (a maintained index to re-run
the scan later:
[awesome-python-html](https://github.com/hasansezertasan/awesome-python-html)):

| Candidate | What it is | Comparability |
|---|---|---|
| [Jinja2](https://jinja.palletsprojects.com/) | The de-facto Python template engine; compiles templates to Python bytecode (reportedly 10-20x faster than Django templates) | High. Macros approximate components, `{% call %}` blocks approximate slots. The baseline every reader knows. |
| [MiniJinja](https://github.com/mitsuhiko/minijinja) | Jinja2-compatible engine written in Rust, official Python bindings via PyO3/maturin | High, and the most interesting control group: the same Rust-core-plus-PyO3 architecture as citry, so it separates "Rust core" from "citry's design" in the numbers. |
| [JinjaX](https://jinjax.scaletti.dev/) | Component syntax (`<Component attr=...>`) on top of Jinja2 | High. The closest syntax peer in the Jinja world. |
| [django-cotton](https://django-cotton.com/) | HTML-like `<c-*>` component tags for Django templates | High. The closest syntax peer in the Django world (same `<c-` prefix), and a natural fourth row in the Django-family table. |
| [Mako](https://www.makotemplates.org/) | Compiled template engine, speed comparable to Jinja2 | Medium. Classical engine, no component model; `<%def>` blocks approximate components. |
| [Chameleon](https://chameleon.readthedocs.io/) | ZPT/XML-attribute templates, compiles to Python | Medium. Attribute-driven syntax is structurally close to `c-*` attributes, but no component model. |
| [htpy](https://htpy.dev/) / [Dominate](https://github.com/Knio/dominate) | HTML built by Python function calls / context managers | Medium. There is no template to parse or compile, so the `startup` and `first` columns measure something different; the `subsequent` column is the honest comparison. |
| [FastHTML](https://fastht.ml/) | Web framework over fastcore FT components (HTML-as-Python) | Medium. Same caveat as htpy, plus framework overhead; benchmark its component render path, not its server. |
| [Ludic](https://github.com/getludic/ludic) | Type-safe HTML components with htmx integration | Medium. Same HTML-in-Python caveat. |
| [Reflex](https://reflex.dev/) | Full-stack framework; Python compiles to a React/Next.js frontend | Low. There is no server-side HTML render to time, so this harness's metrics do not map; comparing it needs a different metric (e.g. time-to-first-byte of a served page). Listed for completeness, not planned. |

Suggested order when the time comes: Jinja2 first, MiniJinja second (the
architectural control group), then JinjaX / django-cotton (component-syntax
peers). Each addition is phase 5 work (section 8) and follows the same
scenario-file contract, including its own snapshot test.

---

## 3. Decisions that shaped the design

Decisions made with the maintainer:

1. **The benchmarks live in citry, not in django-components.** Three reasons:
   - Installability is one-directional. `django` and `django-components` are
     on PyPI; adding them to citry is a dev-dependency line. The `citry`
     package is unpublished (0.1.0) and sits on a locally-built `citry_core`
     via maturin, so installing it into the DJC repo would need path hacks
     plus a Rust toolchain in DJC's CI.
   - The longitudinal axis that matters is citry's commit history
     (section 2), and asv tracks the repo it lives in.
   - The vendoring direction already exists here (`_djc_reference/`,
     `tests/_djc_tests/`).
2. **Two-stage harness.** Stage one is a plain comparison script (the
   `benchmark_const.py` style) that runs all engine variants at HEAD and
   prints a table; stage two adopts asv for per-commit tracking and
   dashboards. The benchmark *files* follow the DJC marker convention from
   day one so stage two reuses them unchanged (section 5).
3. **Small scenario first; large scenario gated.** The small scenario needs
   one small citry feature (class/style attribute values, section 6.3
   feature A); the large scenario additionally needs dynamic tag names and
   JS/CSS dependency rendering (features B and C), so its citry port waits
   for those rather than shipping a lopsided comparison.
4. **Citry runs as two variants**: plain inputs, and `Const`-marked inputs
   where the optimization applies (section 6.4). The plain row is the
   cross-engine comparison; the Const row shows opt-in headroom.
5. **Missing citry features get implemented, not worked around.** Where the
   scenarios exercise something citry lacks (class/style value forms,
   dynamic tag names), the feature is built as a real, user-facing citry
   feature with its own design, and the benchmark port uses it. The one
   exception is Django forms, which are hand-written in the citry port
   (section 6.2).

---

## 4. The two scenarios

Both come from DJC and are kept byte-comparable on the DJC/Django side
(vendored nearly verbatim), with a citry reimplementation added as a third
variant.

- **Small** (`sm`): a single Button component (~340 lines). One component,
  kwargs with defaults, a computed CSS class, an if/else branch, attribute
  spreading, one default slot. Renders a button from
  `gen_render_data()` kwargs plus a `"content"` slot fill.
- **Large** (`lg`): a realistic project-management page (~6,000 lines):
  35 registered components (layout, navbar, sidebar, dialog, tabs, tables,
  forms, breadcrumbs, bookmarks...), a JSON data blob, custom filters,
  Alpine.js attributes throughout, provide/inject, 13 components with inline
  JS, and JS/CSS dependency rendering in the base layout.

Each scenario file exposes the same two entrypoints the harness calls:
`gen_render_data() -> data` and `render(data) -> str`.

Measured dimensions (mirroring DJC so numbers are methodologically
comparable):

| Dimension | Values |
|---|---|
| Engine | `django`, `django-components`, `citry`, `citry-const` (section 6.4) |
| Size | `sm`, `lg` |
| Test type | `startup` (class + template definition), `first` render, `subsequent` render |
| Metric | wall time (fresh process), peak memory, import time |

The DJC-only `isolated` vs `django` context-mode axis stays in the vendored
DJC files (it is one regex override) but is not part of the cross-engine
table; citry has no equivalent mode split. The `citry-const` row is the
mirror image: a citry-only axis with no DJC/Django equivalent.

---

## 5. File layout and harness

### 5.1 Layout

```
benchmarks/                         # repo root, mirrors DJC's layout
    README.md                       # how to run, how to read results
    compare.py                      # stage-one runner (section 5.3)
    utils.py                        # marker slicing + (later) asv helpers
packages/py/citry/tests/
    test_benchmark_citry_small.py   # citry port of the small scenario
    test_benchmark_citry.py         # citry port of the large scenario (phase 3)
    test_benchmark_djc_small.py     # vendored from DJC
    test_benchmark_djc.py           # vendored from DJC (phase 3)
    test_benchmark_django_small.py  # vendored from DJC
    test_benchmark_django.py        # vendored from DJC (phase 3)
```

The benchmarked files sit in `tests/` so pytest verifies them (section 5.2),
exactly as in DJC. The runner lives at the repo root because it spans
engines and (in stage two) hosts the asv suite. Future engines (section 2.1)
each add one `test_benchmark_<engine>{,_small}.py` file to the same
directory.

### 5.2 The scenario file contract

Each `test_benchmark_*.py` is self-contained and follows the DJC marker
convention:

- All imports first, ending with `# ----------- IMPORTS END ------------ #`
  (enables the import-time benchmark).
- Engine setup (for Django/DJC: inline `settings.configure`; for citry:
  `Citry()` instantiation), component definitions, data, and the two
  entrypoints `gen_render_data()` / `render(data)`.
- `# ----------- TESTS START ------------ #` followed by a pytest snapshot
  test that calls both entrypoints. Everything below the marker is invisible
  to the harness.

The harness reads the file as a source string and slices at the markers; it
never imports the module. This keeps the benchmark process free of pytest
and of the citry test venv's import state, and it is what lets the same file
serve asv's `timeraw_` (run string in fresh process) and `peakmem_` (exec
string as virtual module) modes later.

Mode constants follow the DJC `CONTEXT_MODE` trick: a module-level constant
near the top of the file that the runner overrides by regex. The vendored
DJC files keep `CONTEXT_MODE`; the citry files get `CONST_MODE`
(section 6.4).

The vendored DJC/Django files require `django` and `django-components` at
test time. When those are absent (the default dev install), `tests/conftest.py`
skips collecting the files entirely. The skip lives in conftest rather than
as an importorskip inside the files so the vendored import section stays
byte-identical to upstream; the import-time benchmark slices and times that
section, and a test-infra import inside it would pollute the measurement.

### 5.3 Stage one: the comparison script

`benchmarks/compare.py`, in the style of `benchmark_const.py`:

- For each (engine, size, test type) cell: build the script by slicing the
  scenario file, append the setup lines (`gen_render_data()`, plus one warmup
  `render()` for the `subsequent` type), and time `render(render_data)` in a
  **fresh subprocess** (so startup state never leaks between cells, matching
  asv's `timeraw_` semantics). The `citry-const` engine value is the citry
  scenario file with `CONST_MODE` flipped to `True`.
- Print one table per size: engine rows (including `citry-const`),
  test-type columns, with ratios against the Django baseline.
- Refuse to run (or warn loudly) when `citry_core` is a debug build, the
  same trap `benchmark_const.py` documents. How to detect the build profile
  cheaply is an open question (section 9); worst case the README warning is
  the guard.
- Not collected by pytest; run as
  `.venv/bin/python benchmarks/compare.py [--size sm|lg] [--quick]`.

### 5.4 Stage two: asv

Adopt asv once the files exist and stage one has produced first numbers:

- `asv.conf.json` at the repo root, results in `.asv/results/` (or committed,
  matching DJC, once there is a docs site to publish to).
- The suite file ports DJC's `benchmark_templating.py` structure: same
  decorator, same slicing helpers, with `renderer` gaining the `citry` and
  `citry-const` values.
- **The build step is the citry-specific work**: asv installs the project per
  commit, and citry needs a maturin release build of `citry_core` per
  benchmarked commit. This means a custom `build_command` (maturin build
  `--release`, then install the wheel plus the `citry` package) and a Rust
  toolchain wherever benchmarks run. Per-commit Rust builds are slow; the
  DJC-style quick subset (one flagged benchmark) is what makes PR runs
  viable.

Stage two is deliberately last: it adds tracking and dashboards, not new
information about citry vs DJC.

### 5.5 Dependencies

`django` and `django-components` go into a `benchmark` dependency group of
`packages/py/citry/pyproject.toml`, mirrored in the root `pyproject.toml`
extras with the usual cross-comments (the mirrored-deps gotcha in
`/CLAUDE.md`). They are not runtime deps and not part of the default dev
install. Future engines add their packages to the same group.

No snapshot plugin: upstream's syrupy snapshot asserts are replaced with
the observed output locked directly into the assert (the "observe, then
lock" rule in `/CLAUDE.md`), so the scenario tests use plain asserts like
the rest of the suite. DJC's random per-render `data-djc-id-*` marker is
regex-stripped inside the DJC file's assert only (upstream's `djc_test`
fixture played that role); citry's `data-cid-*` markers are deterministic
under the suite's conftest fixture and are asserted as-is.

---

## 6. Can citry express the scenarios? (feature audit)

Audited against the current `packages/py/citry/` runtime, June 2026. The
audit surfaced three citry features that the scenarios exercise and citry
does not have yet. Per decision 5 (section 3) they get built as real,
user-facing features, each with its own design; section 6.3 holds the
sketch-level specs and section 8 maps them onto phases.

### 6.1 Small scenario

| DJC construct in the Button file | citry equivalent | Status |
|---|---|---|
| `get_context_data(...)` with kwarg defaults | `Kwargs` class + `template_data()` | Ported as-is |
| `{% if %}` / `{% else %}` | `<c-if>` / `<c-else>` | Ported as-is |
| `{% html_attrs attrs class=x class="y" %}` | `c-bind` spread + class/style value forms | Needs feature A (section 6.3) |
| `{% if disabled %} disabled {% endif %}` (bare attribute) | `disabled: True` in the `c-bind` dict renders as a boolean attribute | Ported as-is |
| `{% slot "content" default / %}` | `<c-slot name="content">` filled via `slots={"content": ...}` | Ported as-is |
| `Button.render(kwargs=..., slots=...)` | `str(Button(**kwargs, slots=...))` | Ported as-is |

DJC's `{% html_attrs %}` *appends* duplicate `class` values where `c-bind`
is last-one-wins, so the honest port needs class values that merge. That is
exactly feature A; the citry port uses it rather than hand-merging strings
in `template_data()`, so the benchmark exercises the engine, not a
component author's workaround.

### 6.2 Large scenario

Three constructs need citry features (A, B, C in section 6.3), and one is a
deliberate hand-port:

**Django forms.** The scenario defines real Django forms
(`ProjectAddUserForm` with `ChoiceField`s, `test_benchmark_djc.py:5127`) and
renders their fields. Django form widgets render through Django's own
template engine, which would smuggle Django's renderer into the "citry"
measurement. The citry port hand-writes the equivalent field HTML; Django
stays a data-generation dependency only (like `HttpRequest` and `csrf`
already are). The vendored DJC/Django variants keep the real forms.

Everything else maps mechanically:

| DJC construct (large scenario) | citry equivalent |
|---|---|
| `{% component "Name" %}` (35 registered components) | `<c-Name>` via the registry |
| `{% for %}` / `{% empty %}` / `{% elif %}` | `<c-for>` / `<c-empty>` / `<c-elif>` |
| `{% fill %}` incl. conditional and in-loop fills | `<c-fill>` (already tested in `test_slot_fills.py`) |
| `{% provide %}` | `<c-provide>` |
| `{% html_attrs %}` (47 uses) | `c-bind` + feature A |
| `<{{ form_content_tag }}>` dynamic tag (`:3775`) | feature B |
| `{% component_js_dependencies %}` / `{% component_css_dependencies %}` (`:2763`) | feature C |
| Filters: `json`, `alpine`, `js`, `get_item`, `escape`, `title`, `linebreaksbr`, `default_if_none` | plain function calls in expressions; helpers passed via template data (V3 has no filter syntax by design) |
| `{% define expr as var %}` (used once, `:1932`) | inline the expression at the use site |
| `{% static 'js/htmx.js' %}` (used once, `:2757`) | a `static()` helper passed via template data |
| Alpine attributes (`@click`, `:class`, `x-data`) | parse as-is (the grammar allows any non-delimiter chars in attribute names) |
| `mark_safe` | markupsafe / `mark_html()` |
| `naturaltime` (django.contrib.humanize) | small local reimplementation, so the citry file does not import Django at module level and the import-time benchmark stays honest |

### 6.3 New citry features this work drives

These are user-facing citry features that happen to be surfaced by the
benchmark port; each needs its own design before building, and they outlive
the benchmarks.

**Feature A - class/style attribute values (Vue/React style).** `class` and
`style` values, wherever they appear (static attribute, `c-class`/`c-style`
dynamic attribute, or an entry inside a `c-bind` dict), accept structured
forms that the engine normalizes at render time:

- `class`: a plain string, a list of strings, a dict of
  `{class_name: enabled_bool}` (falsy values drop the class), or a list
  mixing any of those (nested lists flatten).
- `style`: a plain string, a dict of `{css_property: css_value}`, or a list
  of those.
- Unlike all other attributes, where duplicates are last-one-wins (README
  "Attribute spreading"), multiple `class`/`style` sources on one element
  **merge**. This is a deliberate special case, matching Vue's class/style
  bindings.

Designed in [`html_attrs.md`](html_attrs.md). The audit there found the
scope is larger than value normalization: the compiler currently flattens
plain-element attributes into string chunks, so the feature also covers
`c-bind` spreading and boolean attribute semantics, and it includes a
compiler-output change (a structured element-attrs node). No grammar or
AST change. Needed by both scenario sizes.

**Feature B - dynamic HTML tag names.** The large scenario picks a tag at
render time (`<{{ form_content_tag }}>` resolving to div/table/ul,
`test_benchmark_djc.py:3775`). V3 tag names are static in the grammar. The
design adds a `<c-element is="...">` built-in (sibling of `<c-component>`,
which stays components-only) that renders a plain HTML element named at
render time; the Form case becomes `<c-element c-is="form_content_tag">`.
Designed in [`dynamic_component.md`](dynamic_component.md). Needed by the
large scenario only.

**Feature C - JS/CSS dependency rendering.** Already designed at the
boundary level: asset loading covers declare/resolve/load
([`asset_loading.md`](asset_loading.md)), emission belongs to the future
dependency extension (asset_loading.md section 7.4) with `<c-js>`/`<c-css>`
as the planned built-ins (`citry/component_registry.py:241`). The large
scenario renders the collected, deduped assets of 13 components
(`test_benchmark_djc.py:2763`); porting it without this would silently skip
that work and skew the comparison in citry's favor, so the large port waits
for it.

### 6.4 The two citry variants: plain and Const

The citry scenario files run as two engine rows:

- **`citry`**: plain inputs, matching what a naive user writes in every
  engine. This is the cross-engine comparable row.
- **`citry-const`**: the same file with inputs `Const`-marked where the
  optimization applies ([`constness.md`](constness.md)). This row shows the
  headroom an opted-in user gets; it has no DJC/Django equivalent, so within
  the table it reads as "citry vs itself".

Mechanism: one set of component definitions per file, plus a module constant
(`CONST_MODE = False`) that the runner flips by regex, the same trick DJC
uses for `CONTEXT_MODE` (section 5.2). The constant switches whether
`gen_render_data()` wraps the relevant inputs in `Const`.
`benchmark_const.py` remains the micro-level Const benchmark; this is the
scenario-level view of the same optimization.

### 6.5 Fairness notes

- **Release builds only.** All citry numbers require
  `uv run maturin develop --release` in `packages/py/citry_core` first; a
  debug build invalidates everything (the `benchmark_const.py` precedent).
- **Per-render ID attributes.** Citry output carries `data-cid-*` markers
  that DJC/Django output does not. They are part of citry's real cost, so
  the benchmarks never strip them; output is timed and snapshotted as
  rendered.
- **Outputs are not byte-identical across engines** (markers, attribute
  ordering, whitespace), so there is no cross-engine equality assert. Each
  scenario file carries its own snapshot test instead, same as DJC.

---

## 7. What gets vendored, and how it stays honest

The four DJC files are copied nearly verbatim (they were designed as
self-contained single files precisely so they could be lifted), with only:

- a header comment naming the upstream commit they were copied from,
- the pytest section adapted to citry's test conventions (locked-string
  asserts instead of syrupy snapshots; see section 5.5),
- no behavior edits. If an edit is ever needed, it goes in as a clearly
  marked, commented divergence.

The vendored files are excluded from ruff (root `pyproject.toml` excludes);
linting them would force edits that defeat the byte-close-to-upstream rule.

Pinning: the `benchmark` dependency group pins `django` and
`django-components` to exact versions, and the benchmark README records which
versions the published numbers refer to. Bumping the pins is a deliberate
act that re-baselines the comparison.

---

## 8. Implementation phases

**Phase 1 - small scenario, three engines. Done (2026-06-12).**

1. Design and implement feature A (class/style attribute values,
   section 6.3), with its own design note and tests. Standalone value even
   if benchmarks stalled here.
2. Add the `benchmark` dependency group (package + root mirror).
3. Vendor `test_benchmark_django_small.py` and `test_benchmark_djc_small.py`
   into `packages/py/citry/tests/`, adapt their pytest sections.
4. Write `test_benchmark_citry_small.py` per the section 6.1 mapping, using
   feature A, with the `CONST_MODE` switch (section 6.4) and its snapshot
   test.
5. Verify all variants render correctly via pytest.

**Phase 2 - the comparison runner. Done (2026-06-12).**

6. `benchmarks/utils.py` (marker slicing) and `benchmarks/compare.py`
   (subprocess timing, table output, baseline ratios, the `citry-const`
   row), per section 5.3.
7. `benchmarks/README.md`: how to run, release-build requirement,
   relative-results-only interpretation rules (adapted from DJC's).
8. First published numbers (small scenario) land in the README.

**Phase 3 - large scenario. Gated on features B and C** (section 6.3;
feature C ships with the dependency extension tracked in
[`extensions.md`](extensions.md) / [`asset_loading.md`](asset_loading.md),
feature B is its own design + implementation in the high-risk areas).

9. Design and implement feature B (dynamic HTML tag names; the `/CLAUDE.md`
   high-risk-area process applies).
10. Vendor `test_benchmark_django.py` and `test_benchmark_djc.py`.
11. Port `test_benchmark_citry.py` per the section 6.2 mapping (forms
    hand-written, helpers local, features A/B/C exercised), with
    `CONST_MODE`.
12. Extend `compare.py` defaults to both sizes.

**Phase 4 - asv adoption (optional, after phases 1-3 prove out).**

13. `asv.conf.json` + suite file with the custom maturin `build_command`
    (section 5.4).
14. CI: a PR quick-compare job and a full run on release tags, modeled on
    DJC's `pr-benchmark-generate.yml` / `pr-benchmark-comment.yml`.

**Phase 5 - additional engines (section 2.1).**

15. One scenario file per engine, starting with Jinja2 and MiniJinja, then
    the component-syntax peers (JinjaX, django-cotton). Each lands with its
    own snapshot test and a README note on its comparability caveats.

Phases 1-2 give the first citry-vs-DJC-vs-Django numbers; feature A is the
only feature work on that path. Phase 3's gates (features B and C) are the
only cross-project dependencies.

---

## 9. Open questions

- **Detecting a debug `citry_core` build** from the runner, so `compare.py`
  can refuse to produce garbage numbers instead of relying on a README
  warning. (Possible angle: a build-profile flag exposed from the Rust crate;
  needs its own small design if pursued.)
- **Where published numbers live** once a docs site exists (DJC publishes the
  asv dashboard with its docs). Until then, the benchmarks README holds a
  dated results table.
- **Whether the citry large port should exist in a draft before the phase 3
  gates lift** (skipping features B/C), purely to shake out parser/runtime
  issues on a 6,000-line real-world template. If yes, it must not be used
  for published comparisons.
- **How far `CONST_MODE` reaches in the large scenario**: marking only
  `gen_render_data()` inputs is mechanical, but some of the headroom may sit
  in per-component `template_data()` outputs. Decide when porting; start
  with inputs only.

---

## 10. Interactions

- **Class/style attribute values (feature A)** and **dynamic tag names
  (feature B)**: standalone user-facing features that this work surfaces;
  their designs land separately and they outlive the benchmarks. Feature B
  is a high-risk-area change (grammar/parser/compiler contract).
- **Dependency extension (feature C)** (asset_loading.md section 7.4,
  extensions.md phasing): phase 3's gate. The large scenario becomes its
  first integration-scale consumer and benchmark.
- **Const optimization** (constness.md): exercised at scenario level by the
  `citry-const` variant (section 6.4); `benchmark_const.py` remains the
  micro-level benchmark of the same machinery.
- **V3 parser work** (`crates/citry_template_parser/`): the large scenario is
  the biggest real-world template the parser will have seen; expect it to
  surface grammar and runtime edge cases (Alpine attribute names, deeply
  nested fills). That is a feature, not a risk: the pytest section catches
  breakage in the normal suite.
- **citry_core micro-benchmarks** (`packages/py/citry_core/tests/`):
  unaffected; different layer.

---

## 11. Results log

Dated snapshots of published numbers; `benchmarks/README.md` always carries
the latest table with the full how-to-reproduce context. Results are
relative values only (section 1, "Interpretation rules"): compare rows
within one run, never numbers across machines, runs, or build profiles.

### 2026-06-12 - small scenario, first numbers

Apple M4, Python 3.13.12, median of 5 fresh-process rounds per cell.
django 6.0.6, django-components 0.151.0, citry 0.1.0 (citry_core 1.3.0,
release build). Ratios vs the `django` row.

| engine | startup | import | first | subsequent |
|---|---|---|---|---|
| django | 75.35 ms (1.00x) | 71.45 ms (1.00x) | 1.11 ms (1.00x) | 39.5 us (1.00x) |
| django-components | 72.47 ms (0.96x) | 72.05 ms (1.01x) | 1.44 ms (1.29x) | 206.6 us (5.23x) |
| citry | 25.96 ms (0.34x) | 26.08 ms (0.37x) | 866.6 us (0.78x) | 58.9 us (1.49x) |
| citry-const | 26.05 ms (0.35x) | 25.80 ms (0.36x) | 849.7 us (0.76x) | 64.4 us (1.63x) |

Reading:

- citry imports and starts up about 3x faster than the Django stack, and
  beats even vanilla Django on first render.
- On repeat renders citry is about 3.5x faster than django-components,
  though ~1.5x slower than a bare Django template; the gap is the component
  machinery itself (per-render component construction, slot resolution, id
  marking).
- `citry-const` shows no benefit on this scenario: the Button template is a
  single element, so almost nothing is left to fold, while computing the
  fold-cache key still costs a little per render. Expected, not a bug; the
  optimization targets templates with large constant regions, so the large
  scenario (phase 3) is its fair test.
