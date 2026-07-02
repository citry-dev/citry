# Design: test migration from django-components

This document tracks the migration of the `django-components` test suite into
citry, test file by test file and test group by test group. It is the sibling
of [`citry_migration.md`](citry_migration.md) (which tracks the engine-source
migration) and follows the same "review by file" model.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For current project
state see [`/TODO/project_status_june_2026.md`](../../TODO/project_status_june_2026.md).

The upstream tests are staged under
[`packages/py/citry/tests/_djc_tests/`](../../packages/py/citry/tests/_djc_tests/)
(a raw snapshot of `django-components/tests/`, currently excluded from
collection by `collect_ignore_glob = ["_djc_*"]` in
[`packages/py/citry/tests/conftest.py`](../../packages/py/citry/tests/conftest.py)).
That snapshot is a **staging area**: once every file below has a completed
verdict, the snapshot can be retired (with maintainer sign-off, see the
Migration approach). Until then it stays reproducible via
[`scripts/vendor_djc_reference.sh`](../../scripts/vendor_djc_reference.sh).

---

## Why the suite is not ported one-for-one

citry's public surface is roughly 90-95% the same as django-components, but the
tests are written against a different world. A djc test and its citry
equivalent differ on five axes:

| Axis | django-components test | citry test |
|---|---|---|
| Template syntax | Django Template Language: `{% component %}`, `{% slot %}`, `{% fill %}`, `{% load %}` | V3 `<c-*>` HTML-like tags |
| Harness | `@djc_test` decorator + `setup_test_config()` (Django settings, DB, template loaders) | plain pytest + fixtures in [`tests/conftest.py`](../../packages/py/citry/tests/conftest.py) |
| Imports | `django_components.*` | `citry.*` / `citry_core.*` |
| Django-only concepts | `context_behavior` (django vs isolated), `Context`, `assertHTMLEqual`, staticfiles | none: citry is framework-agnostic |
| Assertions | `assertHTMLEqual` on rendered HTML | exact serialized output with `data-cid-<id>` markers (the `_deterministic_render_ids` fixture makes ids `c1`, `c2`, ...) |

So a test cannot simply be copied. Each is classified on **two axes**.

**Disposition** (what happens to the test), reusing the same six symbols as
[`citry_migration.md`](citry_migration.md) so the two docs read as siblings:

- ✅ **Already-covered** - the behavior is already asserted by an existing
  citry test. The Notes name the exact test (e.g. `test_slots.py::TestSlotCall`)
  so the claim is auditable.
- 🚧 **Port** - the behavior is one citry keeps but nothing asserts it yet.
  Rewrite the test against the citry API (fresh `Citry()`, `<c-*>` syntax) and
  land it. The Notes name the target citry test file.
- ♻️ **Replace** - the same guarantee survives but the djc test's shape is
  Django-specific; a differently-shaped citry test covers it (named in Notes),
  or it moves to a different layer (e.g. the Rust parser crate).
- ❓ **New-citry-test-needed** - citry behavior with no djc analogue, or a gap
  the djc test surfaces, that needs a brand-new test. Do not port as-is.
- ❌ **Drop** - tests a feature citry deliberately does not carry
  (`@djc_test`, tag formatters, positional `Args`, `context_behavior`,
  registered names). Drops are flagged here, not silently skipped.
- ⏭️ **Skip (Django)** - asserts Django integration (finders, loaders,
  `{% extends %}`, `{% include %}`, template `Library`, the `template_rendered`
  signal) that stays in the `django-components` wrapper and is out of scope for
  this repo.

**Pending a feature or extension.** Some 🚧 items are not portable *yet*
because the citry feature they cover is itself still being migrated, chiefly
the built-in extensions tracked in
[`citry_migration.md`](citry_migration.md) and [`extensions_roadmap.md`](extensions_roadmap.md)
(Cache, Debug/highlight, View). These are marked **🚧 pending** in the
dashboard and stay `~` (not `✔`): their fate is decided (port when the feature
lands) but the port cannot be written until then. The Django `{% cache %}`
tag is one of these, not a Skip: citry may grow a `<c-cache>` component, so its
tests wait on that decision rather than being dropped.

**Target layer** (where the surviving test lives):

- `citry` - the framework-agnostic engine ([`packages/py/citry/`](../../packages/py/citry/)).
- `core` - the Rust parser/compiler ([`crates/citry_template_parser/`](../../crates/citry_template_parser/)).
  The djc Python-side parser tests (`test_tag_parser`, `test_template_parser`,
  `test_html_parser`) map here; verify against the crate's own tests rather
  than porting to Python.
- `wrapper` - the Django integration package (`django-components`). Tests here
  are **out of scope**; they are recorded as ⏭️ so nothing is lost track of.

**Verification rule.** An ✅ "already-covered" verdict is only valid when the
Notes cite the citry test that actually asserts the behavior. The overlap
figures below come from name-sampling the two suites, not from reading every
assertion, so every ✅ must be confirmed against the real test during triage.

---

## Progress dashboard

One row per upstream test file. `~Tests` is the approximate case count.
`Layer` is the dominant target. `Verdict` is the dominant disposition (a file
usually mixes a few; the per-file section carries the detail). `Triaged` is
the tracking flag: `-` not started, `~` seeded from survey (this doc's initial
pass), `✔` confirmed test-by-test against real assertions.

### Component logic

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_attributes.py` | 38 | citry | ✅ / ♻️ | ~ |
| `test_component.py` | 67 | citry | ✅ / ⏭️ | ~ |
| `test_component_cache.py` | 13 | citry | 🚧 pending | ~ |
| `test_component_css.py` | 9 | citry | ✅ | ~ |
| `test_component_css_e2e.py` | 5 | citry | ✅ | ~ |
| `test_component_defaults.py` | 15 | citry | 🚧 / ✅ | ~ |
| `test_component_dynamic.py` | 13 | citry | ✅ | ~ |
| `test_component_error_fallback.py` | 8 | citry | ✅ | ~ |
| `test_component_js.py` | 15 | citry | ✅ | ~ |
| `test_component_js_e2e.py` | 5 | citry | ✅ | ~ |
| `test_component_media.py` | 50 | citry | 🚧 / ⏭️ | ~ |
| `test_component_typing.py` | 13 | citry | 🚧 / ✅ | ~ |
| `test_dependencies.py` | 28 | citry | ✅ | ~ |
| `test_dependency_manager_e2e.py` | 12 | citry | ✅ / 🚧 | ~ |
| `test_dependency_rendering.py` | 18 | citry | ✅ | ~ |
| `test_dependency_rendering_e2e.py` | 15 | citry | ✅ / 🚧 | ~ |
| `test_expression.py` | 31 | citry | ✅ / 🚧 | ~ |
| `test_extension.py` | 25 | citry | ✅ / ⏭️ | ~ |
| `test_registry.py` | 18 | citry | ✅ | ~ |
| `test_slots.py` | 22 | citry | ✅ | ~ |
| `test_cache.py` | 3 | citry | ✅ | ~ |

### Primarily Django

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_autodiscover.py` | 4 | citry | ✅ | ~ |
| `test_context.py` | 47 | wrapper | ⏭️ / ♻️ | ~ |
| `test_django_cache_tag.py` | 12 | citry | 🚧 pending | ~ |
| `test_finders.py` | 6 | wrapper | ⏭️ | ~ |
| `test_hotreload.py` | 24 | citry | ✅ | ~ |
| `test_html_parser.py` | 7 | core | ♻️ | ~ |
| `test_integration_template_partials.py` | 1 | wrapper | ⏭️ | ~ |
| `test_loader.py` | 15 | citry | ✅ / ⏭️ | ~ |
| `test_node.py` | 32 | citry | 🚧 / ♻️ | ~ |
| `test_settings.py` | 6 | citry | 🚧 / ✅ | ~ |
| `test_signals.py` | 3 | wrapper | ⏭️ | ~ |
| `test_tag_formatter.py` | 11 | core | ❌ | ~ |
| `test_tag_parser.py` | 121 | core | ♻️ | ~ |
| `test_template.py` | 4 | citry | ✅ / ⏭️ | ~ |
| `test_template_parser.py` | 13 | core | ♻️ | ~ |
| `test_templatetags.py` | 6 | core | ♻️ | ~ |
| `test_templatetags_component.py` | 19 | citry | ✅ / 🚧 | ~ |
| `test_templatetags_extends.py` | 25 | wrapper | ⏭️ | ~ |
| `test_templatetags_provide.py` | 35 | citry | ✅ | ~ |
| `test_templatetags_slot_fill.py` | 67 | citry | ✅ | ~ |
| `test_templatetags_templating.py` | 22 | citry | ✅ / ⏭️ | ~ |

### Utilities

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_util_weakref.py` | 3 | citry | 🚧 / ❓ | ~ |
| `test_utils.py` | 1 | citry | 🚧 / ❌ | ~ |

### Extensions and commands

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_component_highlight.py` | 7 | citry | 🚧 pending | ~ |
| `test_component_view.py` | 14 | citry | 🚧 pending | ~ |
| `test_command_components.py` | 1 | citry | ✅ / 🚧 | ~ |
| `test_command_create.py` | 7 | citry | ✅ / 🚧 | ~ |
| `test_command_ext.py` | 11 | citry | ✅ / 🚧 | ~ |
| `test_command_list.py` | 4 | citry | ✅ / 🚧 | ~ |

### Benchmarks (present verbatim, not behavioral)

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_benchmark_django.py` | 1 | citry | ✅ | ~ |
| `test_benchmark_django_small.py` | 1 | citry | ✅ | ~ |
| `test_benchmark_djc.py` | 1 | citry | ✅ | ~ |
| `test_benchmark_djc_small.py` | 1 | citry | ✅ | ~ |

The four benchmark files are already present verbatim under
[`packages/py/citry/tests/`](../../packages/py/citry/tests/) alongside citry
and Jinja2 variants; they are timed scenario files, not behavioral tests, and
need no porting. See [`benchmarking.md`](benchmarking.md).

---

## Test tooling parity

Removing tox (issue [#8](https://github.com/citry-dev/citry/issues/8), the uv
workspace conversion) also removed the test lanes tox defined for
django-components. Most of those lanes do not apply to citry, but one does and
must be restored.

### What upstream had

Upstream drives everything through tox (`tox.ini`):

- A `py3.10-3.14` x `Django 5.2 / 6.0` interpreter matrix.
- A `coverage` lane: `pytest --cov=django_components --cov-fail-under=75 --cov-branch`.
- Markers `e2e` and `benchmark_snapshot`, with the default lane running
  `-m "not e2e and not benchmark_snapshot"`.
- `pytest-xdist` (`-n auto`) in the default lane, with
  `test_templatetags_provide.py` split into its own single-process lane
  because `provide`/`inject` leaned on process-global state that xdist
  parallelism corrupted.
- `syrupy` snapshots for the four benchmark render tests.
- Playwright e2e, with `DJC_TEST_BROWSERS` selecting one or all three browsers.

### What citry keeps, drops, and must restore

| Upstream lane | citry status | Action |
|---|---|---|
| Coverage gate (`--cov-fail-under`) | **Missing.** `scripts/check.py` runs a bare `pytest`; there is no `pytest-cov`, no `[tool.coverage.*]`, no threshold. | **Restore** (below). |
| Python x Django matrix | citry dropped Django as a runtime dependency; `django` appears only as a benchmark baseline pin. There is no Django axis to test. | No action. citry's CI matrix is Python x OS only. |
| `e2e` marker + browser lane | At parity: the `e2e` marker is registered in [`tests/e2e/conftest.py`](../../packages/py/citry/tests/e2e/conftest.py), with a chromium PR lane and a weekly three-browser lane in CI. | No action. |
| `benchmark_snapshot` marker | citry gates benchmarks by import in `conftest.py` (the optional `benchmark` / `jinja2` groups) rather than by marker. | No action. Different mechanism, same effect. |
| `syrupy` snapshots | citry locks exact strings and ASTs inline (see the "observe, then lock" rule in `/CLAUDE.md`). | No action. Do not adopt syrupy. |
| `xdist` + provide-isolation lane | citry uses no xdist; `provide`/`inject` travel on a render context, not process globals. | No action. Re-check when porting `test_templatetags_provide.py`; the isolation lane should be unnecessary. |

### Coverage restoration plan (ratchet from baseline)

The gate must never fail a build that was previously green, so the threshold
starts at the current measured coverage and only ever rises.

1. Measure the current line-and-branch coverage of the two Python packages
   (`citry` and the `citry_core` Python wrapper; the Rust half of `citry_core`
   is covered separately by `cargo test`). Record the baseline in the
   implementation log below.
2. Add `pytest-cov` to citry's `[dependency-groups].dev`. The uv workspace
   installs every member's dev group on `uv sync --all-packages`, so the
   shared venv and CI get it from that one declaration (no root-level copy to
   keep in step).
3. Add a `[tool.coverage.run]` section (`source = ["citry", "citry_core"]`,
   `branch = true`, and an `omit` for tests and the generated `_rust`
   extension) plus `[tool.coverage.report]` with `fail_under = <floor(baseline)>`.
4. Fold coverage into the `check.py` pytest phase (citry runs one gate,
   `scripts/check.py`, not a tox matrix), passing
   `--cov --cov-report=term-missing:skip-covered`. `pytest-cov` reads
   `--cov`'s source and enforces `fail_under` from the config.
5. Raise `fail_under` as the test migration lands real coverage; each raise is
   a one-line implementation-log entry.

**Where the gate runs.** `scripts/check.py` is invoked by the `Check`
workflow ([`.github/workflows/repo--check.yml`](../../.github/workflows/repo--check.yml)),
which triggers on **every push and pull request**. So the coverage gate runs
on every PR, in one deterministic environment (Ubuntu, Python 3.13, the full
`dev` deps). It is enforced once there rather than in each cell of the
`Python tests` version-and-OS matrix, because the ratchet floor is
env-specific: version-gated code paths and optional deps would make a
per-cell threshold flaky.

Deliberately out of scope: a *dedicated* coverage-only CI job (the existing
PR-triggered `Check` gate already enforces it), coverage upload/reporting
services, and Rust coverage tooling (the Rust half is covered by `cargo test`).

---

## Test review by file (component logic)

Per-file verdicts for the tests that exercise citry's engine. Seeded from the
survey; rows marked "triage pending" still need per-assertion confirmation.
The status legend is the six-symbol disposition axis defined
[above](#why-the-suite-is-not-ported-one-for-one).

### `test_attributes.py` (38 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestFormatAttributes`, `TestMergeAttributes`, `TestParseStringStyle` | ✅ Already-covered | Near-direct rename to [`test_attrs.py`](../../packages/py/citry/tests/test_attrs.py) `TestFormatAttrs` / `TestMergeAttrs` / `TestParseStringStyle`; citry adds `TestNormalizeClass` / `TestNormalizeStyle` / `TestConstMarkedValues`. Confirm names line up. |
| `TestHtmlAttrs` (the `{% html_attrs %}` tag: positional/kwargs/spread/aggregate) | ♻️ Replace | No template tag in citry; spread and class/style merge are covered on plain elements by [`test_element_attrs.py`](../../packages/py/citry/tests/test_element_attrs.py) `TestCBindSpread` / `TestClassAndStyleMerging`. |

</details>

### `test_component.py` (67 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Component fields, template-string vs file, empty component, parent/root/ancestors | ✅ Already-covered | [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestComponentFields` / `TestCreateInstance` / `TestAncestors`. |
| `Component(...)` returns a renderable | ♻️ Replace | citry returns a `CitryElement`; `TestComponentCall`. |
| Typed input normalization and validation | ✅ Already-covered | `TestTemplateData(+Normalization+Validation)`, `TestInputNormalization`. |
| Generator/template caching per class | ✅ Already-covered | `TestGeneratorCaching`. |
| `render_to_response`, request, context-processor data | ⏭️ Skip (Django) | Django render pipeline; stays in the `django-components` wrapper. |
| `as_view` | 🚧 pending | The View extension is still being migrated; tracked under `test_component_view.py`. |
| Legacy `get_context_data` / `get_template*` API | ❌ Drop | Deprecated in djc; citry uses `template` / `template_data()`. |
| Triage pending | 🚧 Port | Confirm the ~67 cases split cleanly into the rows above; port any engine-behavior case with no citry assertion. |

</details>

### `test_component_cache.py` (13 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestComponentCache` (cache enabled/disabled, ttl, cache-by-input, input hashing, override hash, cache slots) | 🚧 pending | citry has the cache backend ([`test_cache.py`](../../packages/py/citry/tests/test_cache.py)) and const-body caching ([`test_const.py`](../../packages/py/citry/tests/test_const.py) `TestConstBodyCache`), but no per-component cache-by-input test. Pending the Cache extension migration ([`extensions_roadmap.md`](extensions_roadmap.md)); port when it lands. |
| `TestCacheRenderKeyLifecycle` (error does not cache, short-circuit leak) | 🚧 pending | Same target. |

</details>

### `test_component_css.py` (9 tests) and `test_component_js.py` (15 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| CSS variables in stylesheets, numeric/color values, css functions | ✅ Already-covered | [`test_deps_vars.py`](../../packages/py/citry/tests/test_deps_vars.py) `TestCssVars`; djc's per-value `is_css_func` detection is less granular in citry, confirm no gap. |
| JS variables (basic/multiple/complex/type-hints) | ✅ Already-covered | `test_deps_vars.py` `TestJsVars`. |
| Script wrap rules (module/importmap/json/src/`wrap=false`) | ✅ Already-covered | [`test_deps_types.py`](../../packages/py/citry/tests/test_deps_types.py) `TestScript`. |

</details>

### `test_component_css_e2e.py` (5) and `test_component_js_e2e.py` (5)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| CSS variables applied in a real browser | ✅ Already-covered | [`e2e/test_document_e2e.py`](../../packages/py/citry/tests/e2e/test_document_e2e.py) `test_component_css_applies_with_injected_vars`. |
| JS runs and receives data in a real browser | ✅ Already-covered | `e2e/test_document_e2e.py` `test_component_js_runs_and_receives_data`; fragment loading in `e2e/test_fragment_e2e.py`. |

</details>

### `test_component_defaults.py` (15 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Typed kwargs defaults (namedtuple/dataclass) | ✅ Already-covered | [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestInputNormalization`; const default on typed field in [`test_const.py`](../../packages/py/citry/tests/test_const.py) `TestConstThroughTypedKwargs`. |
| `Defaults` class, `factory_from_dataclass`, nested dataclass | 🚧 Port | No dedicated citry defaults test; confirm the `Defaults` object semantics exist in citry and port. |

</details>

### `test_component_dynamic.py` (13 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Dynamic component (python/template, variable-as-name, as-class, default/named slots, invalid input) | ✅ Already-covered | [`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py) `TestDynamicComponent`; citry adds `TestDynamicElement`, `TestAttributeParity`, `TestRegistryReservation`. |
| `shorthand_formatter` | ❌ Drop | citry has no pluggable tag formatter (fixed `<c-*>` syntax). |

</details>

### `test_component_error_fallback.py` (8 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Error boundary: basic, default slot, fallback-as-kwarg, raises on both, inside loop, nested | ✅ Already-covered | [`test_error_fallback.py`](../../packages/py/citry/tests/test_error_fallback.py) `TestErrorFallback`; citry adds page-around-error and escaped-error-name cases. |

</details>

### `test_component_media.py` (50 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Media shapes (js/css as list/dict-by-media/urls/callable/glob), inheritance/merge rules | ✅ Already-covered | [`test_ext_dependencies.py`](../../packages/py/citry/tests/test_ext_dependencies.py) `TestShapes` / `TestInheritanceAndMerge`. |
| Django `Media` staticfiles storage, `SafeString`/`PathLike` paths, `media_class` | ❌ Drop | Django forms-`Media` specifics; citry does not use Django staticfiles. |
| Subclassing `Media`, threading race | 🚧 Port | Confirm citry's extend rules cover subclassing; port the threading-race guard if citry has an equivalent. |

</details>

### `test_component_typing.py` (13 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Typed input/output classes, builtin classes, subclass overrides parent type | ✅ Already-covered | Distributed: [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestTemplateDataValidation` / `TestInputNormalization`, [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py) `TestFieldIntrospection`, [`test_pydantic.py`](../../packages/py/citry/tests/test_pydantic.py). |
| Custom `Args` class raises | ❌ Drop | citry is kwargs-only. |
| Full `Args`/`Kwargs`/`Slots` typed-class matrix | 🚧 Port | No single citry file mirrors the matrix; confirm coverage and port the gaps. |

</details>

### `test_dependencies.py` (28) and `test_dependency_rendering.py` (18)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `render_dependencies`, strategy matrix (document/simple/prepend/append/raw/default), invalid values raise | ✅ Already-covered | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestDocumentEmission` / `TestStrategiesAndPositions`; fragments in [`test_deps_fragments.py`](../../packages/py/citry/tests/test_deps_fragments.py). |
| `adds_component_id_html_attr` (single/multiroot/nested/loops) | ✅ Already-covered | [`test_markers.py`](../../packages/py/citry/tests/test_markers.py). |
| Script-end-tag-inside-js/css raises | 🚧 Port | Confirm citry guards this; port if absent. |

</details>

### `test_dependency_manager_e2e.py` (12) and `test_dependency_rendering_e2e.py` (15)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Client-side dependency manager: load script, call component | ✅ Already-covered | [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py) `test_fragment_scripts_load_on_demand`; unit-level manifest/runtime in `test_deps_vars.py` `TestManifestAndRuntime`. |
| Alpine compatibility in browser | ❓ New-citry-test-needed | No Alpine-compat e2e in citry; decide whether citry claims Alpine compat and add if so. |

</details>

### `test_expression.py` (31 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Python expressions (negate/conditional/method/arithmetic), spread operator | ✅ Already-covered | [`test_nodes.py`](../../packages/py/citry/tests/test_nodes.py) `TestExprNodeEval`, [`test_control_flow.py`](../../packages/py/citry/tests/test_control_flow.py), [`test_element_attrs.py`](../../packages/py/citry/tests/test_element_attrs.py) `TestCBindSpread`. |
| Literal lists/dicts with Django filters | ❌ Drop | citry has no Django template filters (`|` is bitwise-or, per [`grammar.md`](grammar.md)). |
| Aggregate kwargs, literal-with-vars | 🚧 Port | Confirm citry's expression engine covers these; port gaps. |

</details>

### `test_extension.py` (25 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Hook lifecycle, registration, config inheritance, render hooks | ✅ Already-covered | [`test_extension.py`](../../packages/py/citry/tests/test_extension.py) `TestClassAndRegistrationHooks` / `TestRenderHooks` / `TestComponentConfig`; citry adds template hooks and smart-dispatch. |
| `on_slot_rendered`, asset hooks | ✅ Already-covered | [`test_slot_node.py`](../../packages/py/citry/tests/test_slot_node.py) `TestOnSlotRenderedHook`, `test_deps_emission.py`. |
| Extension views | ⏭️ Skip (Django) | Django extension-view surface. |

</details>

### `test_registry.py` (18) and `test_slots.py` (22)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Register/unregister/get, duplicate detection, per-registry node cache | ✅ Already-covered | [`test_component_registry.py`](../../packages/py/citry/tests/test_component_registry.py); class-id conflicts in [`test_class_id.py`](../../packages/py/citry/tests/test_class_id.py). citry adds pascal/kebab name normalization. |
| `Slot` object semantics (escaping, func slots, `str()`, metadata, same-contents) | ✅ Already-covered | [`test_slots.py`](../../packages/py/citry/tests/test_slots.py); fill/render-site behavior in `test_slot_node.py` + `test_slot_fills.py`. |

</details>

### `test_cache.py` (3 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `LRUCache` utility, `maxsize_zero` | ✅ Already-covered | [`test_cache.py`](../../packages/py/citry/tests/test_cache.py) `TestInMemoryCache` (ttl, LRU eviction, protocol) + `TestCitryCacheWiring`. |

</details>

---

## Test review by file (primarily Django)

Same status legend as above. These files exercise the Django-facing surface;
many are ⏭️ Skip (they belong in the `django-components` wrapper) or ♻️ Replace
(the parser tests move to the Rust crate).

### `test_autodiscover.py` (4 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Autodiscovery across dirs, import libraries | ✅ Already-covered | [`test_autodiscovery.py`](../../packages/py/citry/tests/test_autodiscovery.py) is larger (`TestFindComponentModules` / `TestLazyDiscovery` / `TestAutodiscoverMethod` / `TestEndToEnd`). |
| `sys.modules` isolation | ❌ Drop | djc-specific import machinery. |

</details>

### `test_context.py` (47 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestContext` / `TestParentArgs` / `TestIsolatedContext` / `TestContextProcessors` | ⏭️ Skip (Django) | Built on Django `Context` / `RequestContext` / context-processors / `context_behavior`, none of which citry has. |
| `TestContextVarsIsFilled` (`{{ component_vars.is_filled }}`) | ♻️ Replace | citry checks fill presence via `slots.get(...)` in `template_data`; echoed by declared-slot checks in [`test_slots.py`](../../packages/py/citry/tests/test_slots.py). |

</details>

### `test_django_cache_tag.py` (12 tests)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestCacheTagCompatibility` (cache miss/hit, nested, slot inside cache, `expire_time`, `vary_on`, named backend, error in body) | 🚧 pending | Not a plain Django skip: citry may grow a `<c-cache>` component covering the same "cache a rendered region" need. Pending that decision; port the applicable cases (drop the Django `{% cache %}`-tag-specific ones) when it lands. |

</details>

### `test_finders.py` (6), `test_signals.py` (3), `test_integration_template_partials.py` (1), `test_templatetags_extends.py` (25)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Django staticfiles finder | ⏭️ Skip (Django) | citry serves assets via its own endpoints, not Django staticfiles. |
| Django `template_rendered` signal | ⏭️ Skip (Django) | citry uses extension hooks + logger tracing; nearest echo is [`test_logger.py`](../../packages/py/citry/tests/test_logger.py). |
| `django-template-partials` integration | ⏭️ Skip (Django) | Third-party Django library. |
| `{% extends %}` / `{% block %}` / `{% include %}` compat | ⏭️ Skip (Django) | citry has no Django template inheritance. |

</details>

### `test_hotreload.py` (24 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| File-to-component index, reset template/files clears caches | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestFileIndexAndResets`, [`test_ext_dependencies.py`](../../packages/py/citry/tests/test_ext_dependencies.py) `TestResets`. |
| Watcher backends (watchfiles/watchdog/polling), invalidate-on-change | ✅ Already-covered | [`test_reload.py`](../../packages/py/citry/tests/test_reload.py) `TestInvalidateFile` / `TestWatch` / `TestPollingWatcher` / `TestDefaultWatcher`. |
| Hot/restart/off mode mapping | ✅ Already-covered | [`test_contrib_django.py`](../../packages/py/citry/tests/test_contrib_django.py). |
| Dead-weakref pruning | 🚧 Port | Confirm citry prunes; port if there is a gap. |

</details>

### `test_html_parser.py` (7), `test_tag_parser.py` (121), `test_template_parser.py` (13), `test_templatetags.py` (6)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| HTML transform (multiple roots, void elements, whitespace preservation) | ♻️ Replace (`core`) | citry's HTML transform lives in [`crates/citry_template_parser/`](../../crates/citry_template_parser/); verify against the crate's Rust tests. Behavioral echoes: [`test_markers.py`](../../packages/py/citry/tests/test_markers.py), `test_deps_emission.py`. |
| Django DTL tag parser (args/kwargs, filters, translations, typed literals, spread) | ♻️ Replace (`core`) | citry's parser is the Rust crate. Python-visible parse behavior: [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py), [`test_const.py`](../../packages/py/citry/tests/test_const.py). Django filters/translations are not ported. |
| DTL tokenizer (verbatim, nested tags, unterminated) | ♻️ Replace (`core`) | Rust crate; verbatim analogue is [`test_raw.py`](../../packages/py/citry/tests/test_raw.py). |
| Triage note | ❓ New-citry-test-needed | `test_tag_parser.py` is the single largest file (121 cases). Confirm the Rust crate's tests cover the equivalents; anything the crate misses becomes a new Rust test, not a Python port. |

</details>

### `test_loader.py` (15 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Component dirs resolution, filepath-to-module, relative-path raises | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestDirsValidation` / `TestTemplateFile`; module mapping in [`test_autodiscovery.py`](../../packages/py/citry/tests/test_autodiscovery.py) `TestFindComponentModules`. |
| Django app-dirs / nested-apps discovery | ⏭️ Skip (Django) | No Django app registry in citry. |

</details>

### `test_node.py` (32 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `@template_tag` decorator, signature-based validation, flags | 🚧 Port / ♻️ Replace | djc's user-facing Django tag-authoring API. citry's node surface differs ([`test_nodes.py`](../../packages/py/citry/tests/test_nodes.py) tests runtime render nodes). Custom-node registration is [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py) `test_custom_node_can_register_fills`. Decide which authoring API citry exposes, then port or drop. |

</details>

### `test_settings.py` (6), `test_template.py` (4), `test_tag_formatter.py` (11)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Settings validation (base_dir, dict/instance) | 🚧 Port | Scattered across [`test_citry.py`](../../packages/py/citry/tests/test_citry.py), `test_cache.py`, `test_assets.py`, [`test_sandbox_setting.py`](../../packages/py/citry/tests/test_sandbox_setting.py); consider a dedicated `test_settings.py`. |
| `context_behavior` validation | ❌ Drop | Django-specific setting. |
| Template caching | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestTemplateFile`, `test_component.py` `TestGeneratorCaching`. |
| Django `Template` monkeypatch | ⏭️ Skip (Django) | citry does not subclass or patch Django `Template`. |
| Pluggable tag formatter (`{% component %}` vs shorthand) | ❌ Drop | citry syntax is fixed `<c-*>`. |

</details>

### `test_templatetags_component.py` (19), `test_templatetags_provide.py` (35), `test_templatetags_slot_fill.py` (67), `test_templatetags_templating.py` (22)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `{% component %}` render (self-closing, variable name, spread) | ✅ Already-covered | [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py), [`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py). |
| Recursive component, unclosed-tag syntax error | 🚧 Port / ♻️ Replace | Parser errors are Rust-side; confirm citry has a recursion test and a parse-error surface, add where thin. |
| `{% provide %}` / `inject` (basic, dynamic key, spread, nested, forloop, defaults) | ✅ Already-covered | [`test_provide.py`](../../packages/py/citry/tests/test_provide.py) `TestProvideComponent` / `TestInject` / `TestProvideAcrossSlots`; citry adds Python `provide()` API, transparent marker, reserved-name guards. |
| `{% provide %}` inside `{% include %}` | ⏭️ Skip (Django) | Django `{% include %}` interplay. |
| Slot/fill: default/named/scoped, required, doubly-filled raises, passthrough, nested | ✅ Already-covered | [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py) + [`test_slot_node.py`](../../packages/py/citry/tests/test_slot_node.py); near-complete port. |
| Conditional/iterated slots | ✅ Already-covered | `test_slot_fills.py` `TestFillsUnderControlFlow`. |

</details>

---

## Test review by file (utilities)

Same status legend as above.

### `test_util_weakref.py` (3), `test_utils.py` (1)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `cached_ref` / `GLOBAL_REFS` weakref utility | 🚧 Port | No citry weakref util test; confirm citry has the utility (`citry/util/`) and add a focused test, or ❌ Drop if the utility does not exist. |
| `is_str_wrapped_in_quotes` helper | 🚧 Port | Confirm the helper exists in citry (`citry/util/`); if so port the one case into [`test_misc.py`](../../packages/py/citry/tests/test_misc.py), else ❌ Drop. |

</details>

---

## Test review by file (extensions and commands)

Same status legend as above.

### `test_component_highlight.py` (7 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Component/slot debug-highlight extension | 🚧 pending | The Debug/highlight extension is still being migrated ([`extensions_roadmap.md`](extensions_roadmap.md), [`citry_migration.md`](citry_migration.md) `extensions/debug_highlight.py`). Port these tests when the extension lands; a tracked gap, not a drop. |

</details>

### `test_component_view.py` (14 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestComponentAsView` (`as_view`, get/post request, `component_url` / `public_url`, view disabled) | 🚧 pending | The View extension is still being migrated ([`citry_migration.md`](citry_migration.md) `extensions/view.py`). Port the framework-agnostic parts when it lands; the Django `as_view`/URL-conf specifics stay in the `django-components` wrapper. |
| Serving a component over HTTP | ♻️ Replace | citry already serves via its own host adapters ([`test_contrib_fastapi.py`](../../packages/py/citry/tests/test_contrib_fastapi.py), [`test_contrib_hosts.py`](../../packages/py/citry/tests/test_contrib_hosts.py)); confirm the endpoint behavior is covered there and note any gap. |

</details>

### `test_command_components.py` (1), `test_command_create.py` (7), `test_command_ext.py` (11), `test_command_list.py` (4)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Management commands (create/list/ext, dispatch) | ✅ Already-covered / 🚧 Port | citry has a CLI ([`test_cli.py`](../../packages/py/citry/tests/test_cli.py)) and command tests ([`test_command.py`](../../packages/py/citry/tests/test_command.py)). Confirm parity per subcommand; port the create-scaffolding and ext-subcommand cases that citry's CLI supports, ⏭️ Skip the Django `manage.py` integration. |

</details>

---

## citry-only tests (no upstream source)

These citry test files have no django-components ancestor. They cover
citry-native subsystems and are recorded here so no djc-file section is
expected to "own" them. They are **not** part of the migration; they are the
net-new tests the fork already added.

- Identity and ids: `test_class_id.py`, `test_component_id.py`, `test_id_generator.py`, `test_markers.py`
- V3 engine: `test_control_flow.py`, `test_nodes.py`, `test_raw.py`, `test_tag_rules.py`, `test_component_node.py`, `test_render.py`, `test_citry.py`
- Const precompute: `test_const.py`, `benchmark_const.py`
- Deferred rendering and errors: `test_deferred_render.py`, `test_on_render.py`, `test_error_trace.py`, `test_exception.py`
- Dependencies subsystem: `test_deps_emission.py`, `test_deps_fragments.py`, `test_deps_types.py`, `test_deps_urls.py`, `test_deps_vars.py`, `test_js_css_data.py`, `test_ext_dependencies.py`
- Attributes: `test_element_attrs.py`
- Globals and sandbox: `test_template_globals.py`, `test_sandbox_setting.py`
- Reload and logging: `test_reload.py`, `test_logger.py`, `test_misc.py`
- Hosting: `test_contrib_django.py`, `test_contrib_fastapi.py`, `test_contrib_hosts.py`
- Pydantic support: `test_pydantic.py`
- citry benchmarks and e2e: `test_benchmark_citry*.py`, `test_benchmark_jinja2*.py`, `e2e/test_document_e2e.py`, `e2e/test_fragment_e2e.py`

---

## citry-native features needing net-new tests

Features that exist in citry but not in django-components, so no ported test
covers them. A djc-test migration would miss these entirely; they need tests
written from scratch. Ranked most-urgent first.

| Feature | Coverage | Source | Action |
|---|---|---|---|
| Literal `c-` attribute escape (`c-c-foo` renders `c-foo`; the `c-:class` Vue/Alpine bridge) | none | [`html_attrs.md`](html_attrs.md) section 3.4 | ❓ Highest-value gap: the feature is built but has zero tests in Rust or Python. Add tests (Rust parser level and Python render level). |
| `sandbox_expressions` toggle: byte-identical output on/off, and the sandbox rejecting an expression plain `eval` allows | partial | [`/docs/agent/INDEX.md`](../agent/INDEX.md) (safe_eval) | ❓ [`test_sandbox_setting.py`](../../packages/py/citry/tests/test_sandbox_setting.py) is thin; broaden to the byte-identical promise and a rejected-expression case. |
| Source-language attributes (`template_lang` / `js_lang` / `css_lang`) and the pluggable compiler registry | none | [`source_languages.md`](source_languages.md) | ❓ Designed, not built. Add tests when the feature lands. |
| Extension roadmap plugins (Cache, Scoped CSS, Debug, ColorLogger) | partial | [`extensions_roadmap.md`](extensions_roadmap.md) | ❓ Add tests as each extension is built; ties into `test_component_cache.py` and `test_component_highlight.py` above. |

Well-covered citry-native features (no action, listed so the audit is
complete): `Const()` precompute ([`test_const.py`](../../packages/py/citry/tests/test_const.py)),
template globals ([`test_template_globals.py`](../../packages/py/citry/tests/test_template_globals.py)),
`<c-element>` dynamic element ([`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py)),
structured element attributes ([`test_element_attrs.py`](../../packages/py/citry/tests/test_element_attrs.py)),
`data-cid` markers ([`test_markers.py`](../../packages/py/citry/tests/test_markers.py)),
deferred render queue ([`test_deferred_render.py`](../../packages/py/citry/tests/test_deferred_render.py)),
the `on_render` generator and error tracing ([`test_on_render.py`](../../packages/py/citry/tests/test_on_render.py),
[`test_error_trace.py`](../../packages/py/citry/tests/test_error_trace.py)),
and the V3 `<c-*>` grammar ([`test_control_flow.py`](../../packages/py/citry/tests/test_control_flow.py),
[`test_raw.py`](../../packages/py/citry/tests/test_raw.py)).

---

## Migration approach

The suite is worked in batches, cheapest-clearing first, each batch tracked by
flipping `Triaged` in the dashboard and filling the file's section.

1. **Restore coverage first** (the tooling section above). A ratcheting gate
   means every ported test visibly raises the floor.
2. **Clear the `wrapper` / Drop files.** The ⏭️ Skip and ❌ Drop files
   (`test_context`, `test_finders`, `test_signals`,
   `test_integration_template_partials`, `test_templatetags_extends`,
   `test_tag_formatter`) carry no porting work; confirm the verdict, cite the
   reason, mark `✔`. This retires roughly a fifth of the list quickly. (The
   pending-extension files, `test_component_cache`, `test_component_highlight`,
   `test_component_view`, `test_django_cache_tag`, are not cleared here; they
   wait on the feature migration.)
3. **Confirm the `core` files.** The parser files (`test_tag_parser`,
   `test_template_parser`, `test_html_parser`, `test_templatetags`) are ♻️
   Replace; verify the Rust crate's tests cover the equivalents and note any
   gap as a new Rust test.
4. **Verify the strong-overlap files.** Mostly ✅; the work is confirming each
   claimed citry test actually asserts the behavior and citing it. Any
   uncovered case becomes a 🚧 Port.
5. **Port the partial-overlap files.** The real rewriting work: translate
   `@djc_test` + `{% ... %}` into a fresh `Citry()` + `<c-*>`, drop
   Django-only assertions, land in the named citry test file.
6. **Write the net-new tests** for citry-native features, starting with the
   `c-c-` escape.
7. **Retire `_djc_tests/`** once every dashboard row is `✔`: remove the
   snapshot, the `collect_ignore_glob` entry, and the vendor-script `tests/`
   snapshot.

**Confirm before deleting.** No file is removed without maintainer sign-off.
That includes retiring `_djc_tests/` in step 7 and deleting any citry test that
a port supersedes: propose the deletion, get confirmation, then act. This
matches the `/CLAUDE.md` rule on hard-to-reverse, outward-facing actions.

Batches 2-5 fan out well to parallel sub-agents (one file per agent producing
its section rows), with a verification pass that rejects any ✅ verdict whose
cited citry test does not actually assert the behavior.

---

## Implementation log

Chronological record of triage and porting work. Newest entries at the bottom.

### 2026-07-02 - ledger created

- Surveyed the upstream suite (54 files, ~1000 cases), citry's own suite
  (~65 files), the tooling gap left by the tox removal, and citry-native
  features with no djc analogue. Seeded the dashboard and per-file sections
  from that survey (all rows `~`, none `✔` yet).
- Identified the one real tooling gap: coverage measurement, lost with tox.
  The Django-version matrix, syrupy snapshots, and the xdist provide-isolation
  lane are deliberately not restored.
- Identified the highest-value net-new test target: the literal `c-c-`
  attribute escape, built but untested.

### 2026-07-02 - coverage gate restored

- Added `pytest-cov` to citry's dev group, a `[tool.coverage.run]` +
  `[tool.coverage.report]` block to the root `pyproject.toml`, and `--cov` to
  the `scripts/check.py` pytest phase.
- Measured baseline: **92.72%** line-and-branch coverage over the `citry` and
  `citry_core` Python packages (1285 tests, 11 skipped for the absent
  e2e/benchmark groups). Set `fail_under = 92` as the initial ratchet floor.
  Raise it as ported tests lift real coverage.
