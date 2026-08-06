# Design: test migration from django-components

This document tracks the migration of the `django-components` test suite into
citry, test file by test file and test group by test group. It is the sibling
of [`migration_djc.md`](migration_djc.md) (which tracks the engine-source
migration) and follows the same "review by file" model.

A deliberate byproduct: triaging tests this carefully surfaces every
user-observable difference between the two frameworks, so the migration
accumulates a [Divergences for djc users](#divergences-for-djc-users-migration-guide-seed)
catalogue at the end, the seed of a djc-to-citry upgrade guide.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For current project
state see [`/TODO/project_status_june_2026.md`](../../TODO/project_status_june_2026.md).

The migration was completed on 2026-07-23. All 54 upstream files received a
test-by-test disposition, every applicable Citry behavior has native regression
coverage, and the temporary `_djc_tests/` staging snapshot was retired with
maintainer approval. The pinned upstream commit and source/docs reference
snapshots remain reproducible via
[`scripts/vendor_djc_reference.sh`](#vendor_djc_referencesh).

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
[`migration_djc.md`](migration_djc.md) so the two docs read as siblings:

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

**Deferred features are not migration gaps.** Cache and Debug/highlight landed
with their applicable replacements. Named cache backends and other optional
capabilities that Citry deliberately omitted from V1 are recorded as
divergences or future work, not as unported tests.

**Target layer** (where the surviving test lives):

- `citry` - the framework-agnostic engine ([`packages/py/citry/`](../../packages/py/citry/)).
- `core` - the Rust parser/compiler
  ([`crates/citry_template_parser/`](../../crates/citry_template_parser/)) and
  HTML transformer
  ([`crates/citry_html_transform/`](../../crates/citry_html_transform/)). The
  djc tag/template-parser tests map to the former; `test_html_parser.py` maps
  to the latter and its Python wrapper tests. Verify these against the core
  tests rather than porting Django parser mechanics into `citry`.
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
pass), `✔` confirmed test-by-test against real assertions with every applicable
Citry regression landed. Deliberately omitted or future features are classified
as drops, replacements, or explicit divergences rather than pending ports.

As of 2026-07-23, all 54 files and approximately 955 source cases are complete.
There is no remaining test-migration implementation backlog.

### Component logic

<details open>
<summary><b> Component logic items (21/21): </b></summary>

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_attributes.py` | 38 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_cache.py` | 3 | citry | ✅ / ♻️ | ✔ |
| `test_component.py` | 67 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_component_cache.py` | 13 | citry | ✅ / ♻️ | ✔ |
| `test_component_css.py` | 9 | citry | ✅ / ♻️ | ✔ |
| `test_component_css_e2e.py` | 5 | citry | ✅ / ♻️ | ✔ |
| `test_component_defaults.py` | 15 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_component_dynamic.py` | 13 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_component_error_fallback.py` | 8 | citry | ✅ / ♻️ | ✔ |
| `test_component_js.py` | 15 | citry | ✅ / ♻️ | ✔ |
| `test_component_js_e2e.py` | 5 | citry | ✅ / ♻️ | ✔ |
| `test_component_media.py` | 50 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_component_typing.py` | 13 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_dependencies.py` | 28 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_dependency_manager_e2e.py` | 12 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_dependency_rendering.py` | 18 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_dependency_rendering_e2e.py` | 15 | citry | ✅ / ♻️ | ✔ |
| `test_expression.py` | 31 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_extension.py` | 25 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_registry.py` | 18 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_slots.py` | 22 | citry | ✅ / ♻️ / ❌ | ✔ |

</details>

### Primarily Django

<details open>
<summary><b> Django items (21/21): </b></summary>

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_autodiscover.py` | 4 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_context.py` | 47 | wrapper | ⏭️ / ♻️ / ❌ | ✔ |
| `test_django_cache_tag.py` | 12 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_finders.py` | 6 | wrapper | ⏭️ | ✔ |
| `test_hotreload.py` | 24 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_html_parser.py` | 7 | core | ✅ | ✔ |
| `test_integration_template_partials.py` | 1 | wrapper | ⏭️ | ✔ |
| `test_loader.py` | 15 | citry | ✅ / ⏭️ / ❌ | ✔ |
| `test_node.py` | 32 | citry | ♻️ / ❌ | ✔ |
| `test_settings.py` | 6 | citry | ♻️ / ❌ | ✔ |
| `test_signals.py` | 3 | wrapper | ⏭️ | ✔ |
| `test_tag_formatter.py` | 11 | core | ❌ | ✔ |
| `test_tag_parser.py` | 121 | core | ✅ / ♻️ / ❌ | ✔ |
| `test_template.py` | 4 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_template_parser.py` | 13 | core | ✅ / ♻️ / ❌ | ✔ |
| `test_templatetags.py` | 6 | core | ✅ / ♻️ / ❌ | ✔ |
| `test_templatetags_component.py` | 19 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_templatetags_extends.py` | 25 | wrapper | ⏭️ | ✔ |
| `test_templatetags_provide.py` | 35 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_templatetags_slot_fill.py` | 67 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_templatetags_templating.py` | 22 | citry | ✅ / ♻️ | ✔ |

</details>

### Utilities

<details open>
<summary><b> Utilities items (2/2): </b></summary>

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_util_weakref.py` | 3 | citry | ✅ / ♻️ | ✔ |
| `test_utils.py` | 1 | citry | ❌ | ✔ |

</details>

### Extensions and commands

<details open>
<summary><b> Extensions and commands items (6/6): </b></summary>

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_component_highlight.py` | 7 | citry | ✅ ported and expanded | ✔ |
| `test_component_view.py` | 14 | citry | ✅ / ♻️ / ❌ / ⏭️ | ✔ |
| `test_command_components.py` | 1 | citry | ✅ | ✔ |
| `test_command_create.py` | 7 | citry | ✅ / ♻️ / ❌ | ✔ |
| `test_command_ext.py` | 11 | citry | ✅ / ❌ | ✔ |
| `test_command_list.py` | 4 | citry | ♻️ / ❌ | ✔ |

</details>

### Benchmarks (scenario code preserved; pytest harness adapted)

<details>
<summary><b> Benchmarks items (4/4): </b></summary>

| Upstream file | ~Tests | Layer | Verdict | Triaged |
|---|---|---|---|---|
| `test_benchmark_django.py` | 1 | citry | ✅ | ✔ |
| `test_benchmark_django_small.py` | 1 | citry | ✅ | ✔ |
| `test_benchmark_djc.py` | 1 | citry | ✅ | ✔ |
| `test_benchmark_djc_small.py` | 1 | citry | ✅ | ✔ |

The four benchmark files preserve the upstream benchmarked scenario code under
[`packages/py/citry/tests/`](../../packages/py/citry/tests/) alongside citry
and Jinja2 variants. Their code below `TESTS START` is adapted from syrupy to
Citry's exact-output or structural-smoke pytest style. They are timed scenario
files, not a source of further migration work. See
[`benchmarking.md`](benchmarking.md).

</details>

---

## Test tooling parity

Removing tox (issue [#8](https://github.com/citry-dev/citry/issues/8), the uv
workspace conversion) also removed the test lanes tox defined for
django-components. Most of those lanes do not apply to citry. The one that
did, the coverage gate, was restored on 2026-07-02.

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

### What citry keeps, drops, and has restored

| Upstream lane | citry status | Action |
|---|---|---|
| Coverage gate (`--cov-fail-under`) | **Restored.** `pytest-cov` is a dev dependency, `scripts/check.py` runs `pytest --cov --cov-report=term-missing:skip-covered`, and root `pyproject.toml` currently enforces `fail_under = 93` at `precision = 2`. | Treat 93% as the current ratchet floor and raise it as coverage recovers. |
| Python x Django matrix | citry dropped Django as a runtime dependency; `django` appears only as a benchmark baseline pin. There is no Django axis to test. | No action. citry's CI matrix is Python x OS only. |
| `e2e` marker + browser lane | At parity: the `e2e` marker is registered in [`tests/e2e/conftest.py`](../../packages/py/citry/tests/e2e/conftest.py), with a chromium PR lane and a weekly three-browser lane in CI. | No action. |
| `benchmark_snapshot` marker | citry gates benchmarks by import in `conftest.py` (the optional `benchmark` / `jinja2` groups) rather than by marker. | No action. Different mechanism, same effect. |
| `syrupy` snapshots | citry locks exact strings and ASTs inline (see the "observe, then lock" rule in `/CLAUDE.md`). | No action. Do not adopt syrupy. |
| `xdist` + provide-isolation lane | citry uses no xdist; `provide`/`inject` travel on a render context, not process globals. | No action. Re-check when porting `test_templatetags_provide.py`; the isolation lane should be unnecessary. |

### Coverage gate (restored; 93% ratchet floor)

The gate started at the measured baseline. The maintainer temporarily lowered
the floor to 91% on 2026-07-22 and made two-decimal enforcement explicit so
the displayed result and process exit status cannot disagree. The completed
test-migration and transport hardening work raised the ratchet to 93% on
2026-07-23, below the current 94.01% measurement.

1. `pytest-cov` lives in citry's `[dependency-groups].dev`; the uv workspace
   installs it for the shared development and CI environment.
2. Root `[tool.coverage.run]` measures line and branch coverage for `citry`,
   the `citry_core` Python wrapper, `citry_ui`, and `pygments_citry`. The Rust
   code remains covered separately by `cargo test`.
3. `scripts/check.py` runs `pytest --cov --cov-report=term-missing:skip-covered`;
   pytest-cov reads the source list, `fail_under = 93`, and `precision = 2`
   from root config.
4. Raise `fail_under` as migration tests lift measured coverage; record each
   change in the implementation log. The historical two-package baseline is
   recorded below and must not be presented as a fresh four-package measure.

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

### `test_attributes.py` (38 tests) - triaged `✔`

Fully accounted for: 22 already-covered (each with a confirmed, quoted citry
assertion), 9 replaced by citry's element-level attribute tests, 7 dropped as
Django `{% html_attrs %}`-tag internals. No new test needed. Verified 2026-07-02
by reading every citry assertion, not by name-matching.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestFormatAttributes` (8): simple, multiple, escapes special chars, trusted markup not escaped, result is `Markup`, None/False omit, True renders bare | ✅ Already-covered | [`test_attrs.py`](../../packages/py/citry/tests/test_attrs.py) `TestFormatAttrs::{test_simple_attribute, test_multiple_attributes, test_escapes_special_characters, test_does_not_escape_markup, test_result_is_markup, test_none_value_omits_attribute, test_false_value_omits_attribute, test_true_value_renders_bare_attribute}`. Same guarantees; citry escapes `'` as the numeric entity `&#39;` where djc emits `&#x27;` (same character, different codec, not a behavior gap). |
| `TestMergeAttributes` classes and styles (single dict, append, empty, nested list/dict class values, style None-keeps / False-removes / later-wins, first-seen order) | ✅ Already-covered | [`test_attrs.py`](../../packages/py/citry/tests/test_attrs.py) `TestMergeAttrs::{test_single_dict, test_appends_classes_across_dicts, test_merge_with_empty_dict, test_merge_classes, test_merge_styles, test_merge_class_with_none_values, test_merge_class_with_false_values, test_merge_style_with_none_values, test_merge_style_with_false_values}`. `test_merge_classes` and `test_merge_styles` assert the identical inputs and byte-for-byte the djc expected output. |
| `TestMergeAttributes` overlapping plain (non class/style) keys: djc space-joins (`foo="bar baz"`) | ♻️ Replace (deliberate divergence) | citry resolves plain keys **last-one-wins** (`foo="baz"`); [`test_attrs.py`](../../packages/py/citry/tests/test_attrs.py) `TestMergeAttrs::test_overlapping_keys_last_one_wins` asserts and documents this. Catalogued as [Divergences for djc users](#divergences-for-djc-users-migration-guide-seed) #2. |
| `TestParseStringStyle` (7): single, multiple, comments, whitespace, empty, no-delimiter, incomplete | ✅ Already-covered | [`test_attrs.py`](../../packages/py/citry/tests/test_attrs.py) `TestParseStringStyle::{test_single_style, test_multiple_styles, test_with_comments, test_with_whitespace, test_empty_string, test_no_delimiters, test_incomplete_style}`. |
| `TestHtmlAttrs` merge semantics via the `{% html_attrs %}` tag: spread a mapping onto an element, merge class/style across sources, duplicate class/style from variable + literal, None attrs are a no-op | ♻️ Replace | citry has no `{% html_attrs %}` tag; the same merge guarantees live on plain elements: [`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py) `TestCBindSpread::{test_spreads_mapping_onto_element, test_none_contributes_nothing}` and `TestClassAndStyleMerging::{test_class_merges_across_sources, test_style_merges_none_skips_false_removes, test_interlacing_example}`. |
| `TestHtmlAttrs` tag internals: positional/aggregate arg parsing, `attrs:`/`defaults:` prefix keys, arg-collision `TypeError`/`TemplateSyntaxError`, tag kwarg-vs-positional class ordering, `data-djc-id` injection | ❌ Drop | These are django-components template-tag mechanics (argument parsing, the `defaults` fallback concept, the Django component-id attribute). citry attributes are element-level `c-*` with no positional/aggregate arg forms and a `data-cid` marker; nothing to port. |

</details>

### `test_component.py` (67) - triaged `✔`

djc's largest component file. 68 entries: 67 collected methods plus one
upstream never collects (`request_context_ignores_context_when_already_a_context`
lacks the `test_` prefix). The heart of the file maps onto citry's reshaped
lifecycle: `Component(...)` returns a `CitryElement`, `render()` a
`CitryRender`, and djc's three render hooks became the single `on_render`
generator. Surfaces divergences #50-#53.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Empty component renders; inline `template` string; `template_file`; `get_component_by_class_id` (hit and miss); typed kwargs accessors; parent/root/ancestors basics (root has none, nested chains nearest-first incl. root, isinstance checks); render-error component-path prefix; `on_render` returning content replaces output; unhandled hook error bubbles (14) | ✅ Already-covered | [`test_render.py`](../../packages/py/citry/tests/test_render.py) `TestContext::test_no_template_yields_empty_render`; [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestTemplateData` / `TestInputNormalization` / `TestAncestors`; [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestTemplateFile::test_template_file_renders_end_to_end`; [`test_class_id.py`](../../packages/py/citry/tests/test_class_id.py) `TestClassIdLookup`; [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeBoundary::test_child_parent_and_root_linkage`; [`test_error_trace.py`](../../packages/py/citry/tests/test_error_trace.py) `TestComponentPath::test_nested_component_failure`; [`test_on_render.py`](../../packages/py/citry/tests/test_on_render.py) `TestOnRenderPlainForm::test_str_replaces_output_and_skips_template`, `TestOnRenderGeneratorForm::test_unhandled_error_keeps_bubbling_past_generator`. |
| `template_data` returning `None` renders with no variables (1) | ✅ Ported this session | `test_component.py` `TestTemplateDataNormalization::{test_none_template_data_renders, test_none_template_data_means_no_variables_not_kwargs}` (the second pins that `None` yields an empty variable set, not a kwargs passthrough). |
| The render-id contract: `self.id` readable during the render, interpolates, equals the serialized `data-cid` marker (2: `test_component_render_id` and `test_render_can_access_instance`) | ✅ Ported this session | `TestRenderId::test_id_readable_during_render_and_equals_the_marker` covers both djc methods (readable during the render, interpolated, equal to the marker). |
| Untyped `self.kwargs` / `self.slots` are the raw dicts (identity), slots invocable (1) | ✅ Ported this session | `TestInputNormalization::test_untyped_accessors_are_the_raw_dicts`. The `self.args` third of the djc method drops (kwargs-only, divergence #20). |
| Accessors readable after the render; root/parent during the render; three-level tree resolves `.root` to the outermost instance (3) | ✅ Ported this session | `TestParentRoot::{test_root_component_has_parent_none_and_root_self, test_accessors_stay_readable_after_the_render, test_three_level_tree_resolves_root_to_outermost}`. |
| `ancestors` with the same class at two levels: distinct instances, nearest-first (1) | ✅ Ported this session | `TestAncestors::test_same_class_at_two_levels_keeps_distinct_instances`. |
| Template parse/compile error carries the component path and template origin (2) | ✅ Ported this session | `test_error_trace.py` `TestComponentPath::test_child_template_parse_error_carries_path_and_origin` (both djc flavors, unclosed and mismatched tags, share one citry code path). |
| Special-character input names on a component tag (1, reclassified from replace once tested) | ✅ Ported this session | `test_component_node.py` `TestComponentNodeAttrs::{test_special_character_attr_names_become_kwargs, test_at_prefixed_attrs_are_events_not_kwargs}`: hyphenated keys and bare `#`-attrs reach `raw_kwargs`; `@`-prefixed attrs are client event directives and never do (divergence #51). |
| Generator `on_render` on a template-less component: bare yield receives an empty settled render; returned string replaces it (0: citry-native hardening of the template-less slice, no standalone djc method) | ✅ Added alongside the port | `test_on_render.py` `TestOnRenderGeneratorForm::{test_component_without_template_yield_receives_empty_render, test_component_without_template_return_replaces_empty_output}`. |
| Legacy template caching (`get_template_is_cached`, cached-loader per-class copies) (2) | ♻️ Replace | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py): same-class caching (`TestTemplateFile`), reset locality, and two unrelated classes naming one `template_file` each getting their own copy (`test_unrelated_classes_sharing_a_template_file_get_own_copies`). |
| Template-syntax input values: filters, spreads, translations, nested tags inside kwargs (1) | ♻️ Replace | Every `c-` value is one Python expression; divergences #18/#19/#20/#34/#37. |
| `self.input` bundle's raw view (`raw_input`) (1) | ♻️ Replace | `raw_kwargs`/`raw_slots` keep djc's guarantees, incl. defensive copying (`test_component.py` `TestInputNormalization`). |
| Python metadata entry point (render options passed per call) (1) | ♻️ Replace | `render(template_globals=...)` + `serialize(deps_strategy=..., deps_position=...)` ([`test_render.py`](../../packages/py/citry/tests/test_render.py), [`test_template_globals.py`](../../packages/py/citry/tests/test_template_globals.py)). |
| The `component_vars` family: args/kwargs/slots readable in templates and fills, `is_filled` conditionals (5) | ♻️ Replace | No `component_vars` object (divergence #11). Inputs reach the template through the `template_data` mapping (`TestTemplateData::{test_default_returns_kwargs, test_kwargs_resolve_in_template_without_template_data}`); fill bodies resolve the writer's scope (`test_slot_fills.py::test_fill_body_renders_in_parent_scope`). |
| `render()` minimal and full call shapes (2) | ♻️ Replace | Kwargs-only with empty-dict defaults (`TestInputNormalization::test_none_inputs_default_to_empty_dicts`); the `context` argument becomes `template_globals`. Positional args drop (divergence #20). |
| Pydantic input-validation error timing (1) | ♻️ Replace | A missing required kwarg written in a template fails at parse time with a path-prefixed error ([`test_pydantic.py`](../../packages/py/citry/tests/test_pydantic.py)). |
| The three-hook lifecycle: `order`, lambda yields, yield errors, multiple yields, result interception (5) | ♻️ Replace | Divergence #50: one `on_render` generator ([`test_on_render.py`](../../packages/py/citry/tests/test_on_render.py)). Bare yield receives the settled result; each `yield content` replaces the output and receives the new result; errors return to the same yield; cross-component ordering locked by `test_hook_order_across_a_tree_with_siblings`. |
| `all_components()` inventory (1) | ♻️ Replace | Class creation IS registration: `Citry.components` ([`test_citry.py`](../../packages/py/citry/tests/test_citry.py)). |
| Legacy djc API: `get_template_string`, `get_context_data`, constructor/`registered_name`, `get_template_name`, `get_template` (string and Template), the `input` bundle, positional args, `template_name` alias, template/component metadata on a context object, hook mutation of `context`/`template` (13) | ❌ Drop | All marked TODO_V1/V2 upstream or deliberately not carried: citry defines templates only via `template`/`template_file`, inputs live directly on the instance, components are kwargs-only (divergence #20), and there is no mutable render context or nodelist (divergence #8; templates compile once per class). |
| `render_to_response` family, `response_class`, `{% include %}`/`{% extends %}` interplay, request/`RequestContext`/context-processor family (11, incl. the uncollected upstream method) | ⏭️ Skip (Django) | No HTTP coupling on `Component` (the pipeline ends at `serialize()`/`str`/`bytes`); Django template inheritance and request plumbing are divergences #8/#10/#14. |

**Accounting: 68/68 entries** (67 collected + 1 uncollected upstream; 14 already-covered, 11 ported this session via 12 tests, 19 replace, 13 drop, 11 skip-Django).

</details>

### `test_component_cache.py` (13 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Enabled / disabled and TTL | ✅ ported | `test_ext_cache_component.py::TestComponentCacheLookup::test_positive_ttl_expires_through_public_component_rendering` deterministically proves a hit before expiry and a miss at the deadline; adjacent tests cover disabled, `None`, and zero TTL. `test_cache.py::TestInMemoryCache::test_positive_ttl_expires_at_its_monotonic_deadline` locks the backend contract. |
| Custom cache name | ♻️ replaced | V1 intentionally has one engine-owned backend. Named backend aliases are a future feature, not a missing migration test. |
| Cache by input and input hashing | ✅ replaced | Canonical typed variation covers type distinctions, defaults/factories, `Const`, post-input-hook values, and exact deletion. |
| Override hash | ✅ replaced | The instance `Cache.vary()` method receives read-only effective input snapshots; Citry owns hashing and the physical key format. |
| Cached component inside include | ✅ replaced | Public nested component caching works under different current parents and does not archive the original outer parent. |
| Cache fills, string Slots, and callable Slot rejection | ✅ replaced | Every effective content-producing Slot source requires explicit variation; optional `None` and in-template fallback content remain cacheable. |
| Render error does not cache | ✅ ported | Unrecovered and recovered errors skip publication through the render-local finalize plan. |
| Short-circuit key lifetime | ✅ replaced | Finalize-local plans and detached artifacts retain no component instance or class; unregister plus collection is covered. |
| Deferred here from [`test_templatetags_provide.py`](#test_templatetags_providepy-35): djc's global `provide_cache` lifecycle, inject-outside-render "not persisted", and provide outside/inside a component with and without mid-render errors (5) | ♻️ Replace | Citry has no global provide cache. The portable lifetime lesson is covered by the artifact-lifetime acceptance tests above; the upstream cache-population and cleanup mechanics do not become Cache extension behavior. |

**Accounting: 13/13 methods** (3 enabled/disabled/TTL ports, 1 deferred
backend alias, 8 replacement behaviors, and 1 render-error port). The Phase 3
ports and replacements are complete in `test_ext_cache_component.py`.

</details>

### `test_component_css.py` (9 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestCssFunctionDetection` (1) | ♻️ Replace | Citry carries the same public helper. [`test_deps_vars.py`](../../packages/py/citry/tests/test_deps_vars.py) `TestCssVars::test_css_function_detection` locks all eight positive and five negative source cases, including leading whitespace and hyphenated functions. |
| Multiple variables plus numeric, color, spaced-string, and function values (5) | ✅ / ♻️ | `TestCssVars::{test_serialize_css_var_value, test_multiple_values_share_one_scoped_stylesheet}` cover the value branches and prove all entries land together in the hash-scoped stylesheet selected by the root marker. Exact djc hashes and `data-djc-css-*` names are replaced by Citry's `data-ccss-*` contract. |
| Same component class with different per-instance values (1) | ♻️ Replace | `TestCssVars::test_distinct_css_data_gets_distinct_scoped_stylesheets` locks two distinct 32-hex SHA-256 prefixes, matching root markers and scoped stylesheets, while the class stylesheet emits once. |
| Empty mapping and `None` (2) | ♻️ Replace | `TestCssVars::test_empty_css_data_emits_no_variables` covers both results and asserts there is no variables hash or `data-ccss-*` marker while the component's static CSS still emits. |

**Count: 9/9.** No Django-only behavior remains: context-behavior
parametrization, `{% component_css_dependencies %}`, and exact
`data-djc-*` marker/hash bytes are harness details replaced by Citry's
dependency emission and `data-ccss-*` markers.

</details>

### `test_component_js.py` (15 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Basic JS data delivery and typed kwargs (2) | ✅ / ♻️ | [`test_deps_vars.py`](../../packages/py/citry/tests/test_deps_vars.py) `TestJsVars::{test_vars_script_registers_the_data, test_distinct_data_gets_distinct_scripts}` cover serialization and typed prop access; `TestOnComponentTransform::test_sugar_expands_to_register_component`, manifest tests, and the document browser test complete the callback path. Citry's callback receives `{id, els, data}` rather than djc's direct data object. |
| Same class with distinct per-instance values (1) | ♻️ Replace | `TestJsVars::test_distinct_data_gets_distinct_scripts` binds each ordered instance call to its own 32-hex SHA-256 prefix and decoded payload, while sharing one class callback. |
| Nested lists/dicts/floats (1) | ♻️ Replace | `TestJsVars::test_data_round_trips_through_base64` now locks the complex source shape together with the hostile `</script>` string, proving both JSON fidelity and base64 armoring. |
| Empty mapping and `None` (1) | ♻️ Replace | `TestJsVars::test_empty_js_data_emits_call_without_variables` covers both normalized empty results: no variables script/hash, but an instance call with a null hash. [`e2e/test_runtime_e2e.py`](../../packages/py/citry/tests/e2e/test_runtime_e2e.py) `test_call_with_null_vars_hash_passes_null_data` locks the consumer's `data === null`. |
| No `type`, `text/javascript`, `module`, `wrap=False`, and `src` (5) | ✅ Already-covered | [`test_deps_types.py`](../../packages/py/citry/tests/test_deps_types.py) `TestScript::{test_inline_content_is_wrapped_by_default, test_js_mime_type_is_wrapped, test_module_type_is_never_wrapped, test_wrap_false_keeps_content_as_is, test_url_renders_script_src}`. |
| Empty `type`, `application/javascript`, `importmap`, `speculationrules`, and `application/json` (5) | ♻️ Replace | `TestScript::test_additional_script_type_wrap_rules` locks the two classic-script types as wrapped and the three data/declarative types as byte-preserved and unwrapped. |

**Count: 15/15.** Django `Context`/`Template`, registration tags, exact cache
URLs/hashes, and `data-djc-*` markers are harness details replaced by Citry's
component tags, manifest, and `Citry.manager` callback protocol.

</details>

### `test_component_css_e2e.py` (5 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Full document: static CSS without data, three differently scoped instances, and several properties (3) | ✅ / ♻️ | [`e2e/test_document_e2e.py`](../../packages/py/citry/tests/e2e/test_document_e2e.py) `test_component_css_is_static_and_scoped_per_instance` asserts computed static CSS with no variables marker, red/green/blue per-instance computed values, width/height variables, 32-hex SHA-256-prefix markers, and pairwise-distinct hashes. `test_component_css_applies_with_injected_vars` remains the single-instance smoke test. |
| Fresh fragment: static CSS without data and CSS variables (2) | ♻️ Replace | [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py) `test_fragment_static_and_scoped_css_load_on_demand` inserts both component shapes through the live fragment runtime, then asserts their computed background/border values, the scoped root marker, and the three fetched class/variables stylesheet links. |

**Count: 5/5.** The two combined Citry browser tests preserve all five
portable guarantees while using Citry's document/fragment serializer and
dependency runtime instead of Django response views.

</details>

### `test_component_js_e2e.py` (5 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Document without JS data plus global isolation (2) | ♻️ Replace | [`e2e/test_document_e2e.py`](../../packages/py/citry/tests/e2e/test_document_e2e.py) `test_component_js_without_data_runs_immediately_and_stays_scoped` proves immediate class JS runs, the null-data callback installs a working click handler, and a top-level `var` does not become a `window` property. Using `var` deliberately strengthens the upstream `const` assertion, which would pass even without an IIFE. This isolation claim is scoped to inline document emission. |
| Document with simultaneous distinct/complex data (1) | ♻️ Replace | `test_component_js_data_is_isolated_per_document_instance` renders three siblings, proves each callback receives its own nested payload, and exercises the callback-installed interaction for all three. `test_component_js_runs_and_receives_data` remains the single-instance smoke test. |
| Fragment without JS data (1) | ✅ / ♻️ | [`e2e/test_runtime_e2e.py`](../../packages/py/citry/tests/e2e/test_runtime_e2e.py) `_serve_fragment` plus `test_manifest_nested_in_inserted_subtree_is_processed` runs a real no-data component through fragment insertion; `test_call_with_null_vars_hash_passes_null_data` locks the null payload. The CSS half of the source test is covered by the completed CSS E2E batch above. |
| Fragment with JS data (1) | ✅ Already-covered | [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py) `test_fragment_scripts_load_on_demand` fetches the fragment and its cached class/data scripts, then asserts the callback's data-driven DOM mutation. |

**Count: 5/5.** Citry's tests preserve the document/fragment guarantees
through its serializer and runtime rather than Django response views.

</details>

### `test_component_defaults.py` (15 tests) - triaged `✔`

djc's defaults machinery: an inner `Defaults` class, the `Default(...)`
factory wrapper, and the `get_component_defaults()` helper. citry has one
defaults surface instead: ordinary field defaults on the declared `Kwargs`
dataclass, with `dataclasses.field(default_factory=...)` for mutable values.
Divergences #71-#73 carry the user-facing changes, including the trap that a
leftover `Defaults` class is silently ignored.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `Defaults` class resolution and `Default(...)` factories: plain values, factory from a callable, factory via dataclass `field` value / `default_factory` (4) | ♻️ Replace | Replaced by field defaults on `Kwargs`. The replacement contract locked this session: [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestKwargsDefaults::{test_default_factory_gives_a_fresh_value_per_render, test_mutable_class_level_default_fails_at_class_definition}` (a factory runs per render and gives a fresh object, the first `default_factory` lock in the suite; a mutable class-level default fails loudly at class definition, steering to `default_factory`). Divergence #71. |
| Defaults declared on the typed `Kwargs` itself (namedtuple and dataclass forms) apply through a render (2) | ✅ Ported this session | Dataclass form: `TestKwargsDefaults::{test_default_applies_when_omitted_and_supplied_value_wins, test_default_applies_on_the_template_tag_path}` (the default applies on both the direct Python call and the template-tag path, a supplied value wins, and `raw_kwargs` holds only what the caller passed, divergence #73). NamedTuple form: `TestKwargsDefaults::test_default_on_a_namedtuple_kwargs_applies_too` (same guarantees with the class kept unconverted; added after review caught the form being cited without its own lock). Previously only omission-is-accepted was locked (`test_tag_rules.py`), not the value flow. |
| A nested dataclass input value stays an instance (1) | ✅ Ported this session | `TestInputNormalization::test_dataclass_value_inside_kwargs_stays_the_same_instance`: the same object arrives in the typed kwargs and in `raw_kwargs` (input normalization is shallow by design, `util/misc.py:37-46`). |
| Defaults on a plain (neither dataclass nor NamedTuple) `Kwargs` class; `Defaults` combined with each `Kwargs` form (4) | ❌ Drop | There is no second defaults schema to combine with: the declared `Kwargs` is the single source of defaults (#71), and #68 records what bare inner classes become. |
| The `get_component_defaults()` introspection helper (4) | ❌ Drop | No defaults-reading helper exists; defaults are visible on the class itself via `dataclasses.fields(MyComp.Kwargs)` (#71 shows the migration). |

</details>

**Accounting: 15/15 methods** (3 ported this session, 4 replace, 8 drop, 0
already-covered: the nearest existing locks each asserted a nearby guarantee,
not the djc one).

### `test_component_dynamic.py` (13 tests) - triaged `✔`

djc's DynamicComponent (`{% component "dynamic" is=... %}`). citry's
counterpart is the built-in `<c-component>` tag (implemented, with
`<c-element>` as its plain-HTML sibling), and citry's own
[`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py)
already exercises it well beyond the djc file (41 test functions).
Divergences #76-#78; no gaps.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Template-path selection and pass-through: literal name, variable name, spread-supplied `is`, class-as-value; default and named fills through the wrapper, a fill the target lacks stays unused; the target's own validation raises on a bad input; an unknown name raises `NotRegistered`; registering over the built-in name raises `AlreadyRegistered` (10) | ✅ Already-covered | `TestDynamicComponent::{test_static_is_renders_component, test_dynamic_is_with_name_variable, test_is_via_c_bind_spread, test_dynamic_is_with_component_class, test_named_slots_pass_through, test_fills_the_target_lacks_stay_unused, test_unexpected_kwarg_raises_from_target, test_unknown_name_raises_with_element_hint}` plus `TestRegistryReservation::{test_component_name_is_reserved, test_element_class_name_is_reserved}`. citry additionally locks spread-vs-static source ordering, which djc has no analogue for. Unknown-name message wording is divergence #78. |
| Python-side entry point: `DynamicComponent.render(kwargs={"is": ...})` (1) | ♻️ Replace | No importable wrapper class (divergence #76); the replacement is resolving the class and rendering it: `c.get(name)(...)`. Locked: `test_component_registry.py` `TestGet::{test_get_returns_class, test_get_not_registered_raises}`; rendering a class held in Python is asserted throughout the suite. |
| `{% dynamic %}` shorthand via `tag_formatter` (1) | ❌ Drop | No pluggable tag formatter; the syntax is the fixed `<c-*>` form (divergence #15). |
| The `dynamic_component_name` rename setting (1) | ❌ Drop | The built-in names are reserved (`component_registry.py:44`), so the collision the setting solved cannot arise; the setting is deliberately absent (divergences #76, #77). |

</details>

**Accounting: 13/13 methods** (10 already-covered, 1 replace, 2 drop; 0
gaps to port).

### `test_component_error_fallback.py` (8 tests) - triaged `✔`

djc's error boundary (`{% component "error_fallback" %}`). citry's
counterpart is the built-in `<c-error-fallback>` tag, built on the
`on_render` generator hook, with its own suite in
[`test_error_fallback.py`](../../packages/py/citry/tests/test_error_fallback.py)
(19 tests after this batch). Divergences #79 and #80.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| The fallback-kwarg template method (safe and broken content); the nested-boundaries method (inner wins, surrounding page unaffected, a failing inner fallback cascades to the outer boundary, the fill reads the error); and one method that only exercises the dynamic component despite sitting in this file (3) | ✅ Already-covered | `test_error_fallback.py` `test_no_error_renders_content`, `test_fallback_attribute_on_child_component_error`, `test_nested_boundaries_inner_wins`, `test_rest_of_page_renders_around_caught_error`, `test_failing_fallback_bubbles_to_outer_boundary`, `test_fallback_slot_receives_error_as_data`; the dynamic-component method is covered by `test_component_dynamic.py` (kwarg pass-through, implicit body fill). |
| Python-call matrix across seven cells: the fallback kwarg and the fallback slot each honored on safe and raising content, no fallback renders empty, fallback-only renders empty (2) | ✅ Ported this session | New: `TestErrorFallback::{test_fallback_kwarg_from_python, test_no_fallback_from_python_renders_empty_on_error, test_fallback_slot_only_from_python_renders_empty, test_fallback_slot_suppressed_from_python_when_content_is_safe}` (the last added after review found the safe-content slot cell unlocked). The raising-content slot cell was already locked by the pre-existing `test_fallback_slot_from_python_gets_error_object`. |
| Template basic matrix (1) | ✅ Ported this session | Three of its five cells were already locked; two landed this session: the fallback-with-no-guarded-content cell in both forms (`test_fallback_attribute_without_content_renders_nothing`, `test_fallback_fill_without_content_renders_nothing`) and the safe-content-with-a-fallback-fill cell (`test_fallback_fill_suppressed_when_content_is_safe`, added after review found only the attribute form locked). |
| Boundaries inside a loop catch per iteration, the fallback reads the loop variable, source order kept (1) | ✅ Ported this session | `TestErrorFallback::test_boundaries_inside_loop_catch_independently` (4 items, 2 broken, exact interleaved output locked). |
| Giving the fallback as both the kwarg and the slot raises (1) | ♻️ Replace | djc raises `TemplateSyntaxError`; citry raises `RuntimeError` at render ("give only one"), already locked in `test_error_fallback.py`. Assertion-level change, part of divergence #79. |

</details>

**Accounting: 8/8 methods** (3 already-covered, 4 ported this session, 1
replace).

### `test_component_media.py` (50) - triaged `✔`, three bugs fixed

djc's `Media` splits across citry's two asset tiers: the primary
`template`/`js`/`css` pair ([`test_assets.py`](../../packages/py/citry/tests/test_assets.py))
and the `Dependencies` class ([`test_deps.py`](../../packages/py/citry/tests/test_deps.py)).
Triaging this file surfaced three real bugs, all fixed with regressions before
the port: an inherited asset file resolved against the subclass's directory
instead of the declaring class's, an absolute `Path` in `Dependencies` was
emitted as a URL instead of inlined, and the dead-slot check could be bypassed
by rendering twice. The earlier seeded row was wrong in both directions: it
called inheritance/merge covered (only single-base leaf cases were) and lumped
trusted markup/`PathLike` into Drop (citry supports both).

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Inline js/css rendering (IIFE wrap, style tag); file assets via `Citry(dirs=...)`; list/string/dict-by-media shapes; glob via dirs (sorted); non-glob entries untouched (incl. unresolvable); `Script`/`Style` identity pass-through; pair validation (both-`None` legal, both-set raises, child `None` erases); two-level `Dependencies` merge; `extend=False` on a leaf (14) | ✅ Already-covered | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestDocumentEmission`; [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestTemplateFile` / `TestJsCssFiles` / `TestPairValidation` / `TestInheritance`; [`test_deps.py`](../../packages/py/citry/tests/test_deps.py) `TestShapes` / `TestInheritanceAndMerge`; [`test_deps_types.py`](../../packages/py/citry/tests/test_deps_types.py). |
| Glob searches the component's module dir before the `Citry` dirs; URL-shaped entries with glob characters pass through unexpanded (2) | ✅ Ported this session | `test_deps.py` `TestModuleRelativeEntries::test_glob_searches_the_module_dir_before_citry_dirs`, `TestShapes::test_url_forms_pass_through_glob_expansion`. |
| Entry forms: `os.PathLike`, str subclass, str subclass with `__html__`, callables returning any entry form (or an unsupported one), and nothing touches an entry at class-definition time (djc #522) (5) | ✅ Ported this session | `test_deps.py` `TestShapes::{test_pathlike_entry_resolves_like_its_string_form, test_str_subclass_resolves_like_a_plain_string, test_prerendered_str_subclass_passes_through, test_callable_entries_may_return_any_entry_form, test_callable_returning_an_unsupported_type_raises, test_entries_stay_untouched_until_first_resolve}`. The #522 guarantee (no `__html__`/`__str__`/`__fspath__` call until first resolve) is counted-and-asserted. |
| Relative `Dependencies` entries anchor to the defining module, including when first resolved from a nested render in another directory (2, folded) | ✅ Ported this session | `test_deps.py` `TestModuleRelativeEntries::test_relative_entries_anchor_to_the_defining_module` (beats a same-named decoy in the `Citry` dirs). |
| Primary-asset inheritance matrix: 3-level chains where each level declares, nulls, or passes through the pair; pass-through subclasses get their own per-class template whose origin names that class; an inherited file declaration resolves against the declaring class's directory (8) | ✅ Ported this session | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestInheritance::{test_three_level_chain_resolves_each_pair_per_class, test_pass_through_subclasses_get_their_own_template_objects, test_explicit_none_on_the_file_member_also_erases}` plus the bug-fix regression `test_inherited_files_resolve_relative_to_declaring_module` (the behavior was broken before this batch, so it counts as ported, not pre-existing). Per-class origin is citry's analogue of djc's `origin.component_cls`. |
| `Dependencies` across 3-level chains and multiple bases: grandparent through an undeclared middle, two declaring ancestors (farthest first), `None` on a middle class or one base, `extend=False` / `extend` list on a parent (6) | ✅ Ported this session | `test_deps.py` `TestInheritanceAndMerge::{test_grandparent_reaches_child_through_undeclared_middle, test_undeclared_leaf_inherits_ancestors_farthest_first, test_dependencies_none_on_a_middle_class_cuts_ancestors_above_it, test_dependencies_none_on_one_base_drops_only_that_branch, test_extend_false_on_a_parent_cuts_only_above_that_parent, test_extend_list_on_a_parent_replaces_only_that_parents_bases}`. |
| Lazy-loading mechanism (`ComponentMedia` holder, `UNSET`, path rewriting); empty `Media`; `bytes` paths; mixing `None` with a set member; multi-base with a non-`Component` base; `extend` list on the leaf (incl. a plain listed class); the threading race (7) | ♻️ Replace | No `ComponentMedia`/`UNSET` mechanism survives, but the laziness guarantee itself is asserted (`test_assets.py` `TestLazyLoading::test_nothing_is_read_from_disk_at_class_definition_time`, plus reset locality in `TestFileIndexAndResets`). Declared-but-empty `Dependencies` contributes nothing (`test_deps.py` `TestShapes::test_declared_but_empty_dependencies_contribute_nothing`; the runtime is on-demand, divergence #6). `bytes`/`bytearray` in every shape raises `TypeError` naming the component and the entry (`TestShapes::test_bytes_entries_raise_naming_component_and_entry`, divergence #47; the dict-value shape previously decayed into integer bytes, fixed this batch). One-member-`None` is legal (`test_assets.py` `TestPairValidation::test_one_member_none_is_allowed`, divergence #48). A reusable plain definition base or a plain class named in `extend` contributes its preserved `Dependencies` declaration (`test_deps.py` `TestInheritanceAndMerge::test_plain_definition_assets_follow_the_same_branch_rules`); relative entries stay anchored to that definition's module. The leaf `extend` list replaces the bases (`test_extend_list_inherits_from_named_classes_only`) in written order (`test_extend_list_merges_in_written_order`, divergence #46). djc's threading race (#1587) is structurally impossible (the cache attribute is the value, published in one assignment); that design is the guarantee, and `test_assets.py` `TestConcurrentLoading::test_concurrent_first_render_never_sees_a_half_resolved_template` (8 barrier-synchronized threads) is its smoke check. |
| `media_class` custom render_js/render_css; Django staticfiles finder path; staticfiles storage backends (default and manifest) (5) | ❌ Drop | Django forms-`Media` extension points citry does not have. Tag output is controlled by `Script`/`Style` entries and the `on_dependencies` hooks; asset delivery is divergence #12. |
| Django template filters inside a component template (1) | ⏭️ Skip (Django) | Divergence #18; `|` is bitwise-or in citry. |

**Accounting: 50/50 methods** (14 already-covered, 23 ported this session, 7 replace, 5 drop, 1 skip-Django). The three bug-fix regressions (`test_inherited_files_resolve_relative_to_declaring_module`, `test_absolute_path_entries_are_inlined_as_local_files` + glob variant, `test_dead_slot_error_repeats_after_failed_compile`) landed with the fixes.

</details>

### `test_component_typing.py` (13 tests) - triaged `✔`

djc's typed input/output classes (`Args`/`Kwargs`/`Slots` in,
`TemplateData`/`JsData`/`CssData` out). citry keeps the same declared-class
idea but with three structural differences, each now a catalogued divergence:
the data methods are named `template_data`/`js_data`/`css_data` with a
`(self, kwargs, slots)` signature (#67), bare inner classes are rebuilt as
dataclasses rather than NamedTuples (#68), and the `Empty` marker type is
replaced by an empty `class Kwargs: pass` (#69). `Args` does not exist
(kwargs-only components, #20).

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Data methods see typed inputs and return typed outputs: custom input classes, untyped-by-default inputs, default output classes, custom output classes, output instances reused unrevalidated, custom `Kwargs` carried through (6) | ✅ Already-covered | Distributed: [`test_pydantic.py`](../../packages/py/citry/tests/test_pydantic.py) `TestPydanticKwargs::test_typed_view_is_validated_model`; [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestInputNormalization::test_untyped_accessors_are_the_raw_dicts`, `TestTemplateDataValidation::{test_missing_required_field_raises, test_unexpected_field_raises, test_template_data_instance_skips_revalidation}`; [`test_js_css_data.py`](../../packages/py/citry/tests/test_js_css_data.py) `TestJsCssDataSchemas::test_schemas_auto_convert_to_dataclasses`; [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py) `TestNonDataclassDeclarations::test_namedtuple_kwargs_validated_and_render`. |
| Bare inner classes are rebuilt as NamedTuples (the djc test asserts the tuple subclass and keyword construction) (1) | ♻️ Replace | citry rebuilds them as `dataclass(slots=True)`: attribute access only. Divergence #68; the conversion itself is locked by the already-covered rows above. |
| Callers construct and pass `Kwargs` instances; invalid instances raise (1) | ♻️ Replace | citry callers never build `Kwargs` instances: the call shape is plain kwargs (#20) and the framework constructs the declared class, so the validation lives in the render-time rows below. |
| `Kwargs = Empty` declares a no-inputs component (1) | ♻️ Replace | The replacement (`class Kwargs: pass`) locked this session: `test_tag_rules.py` `TestKwargsValidation::{test_empty_kwargs_class_rejects_all_attrs, test_empty_kwargs_class_rejects_python_kwargs_at_render, test_empty_kwargs_class_allows_bare_use}`. Divergence #69. |
| Builtin dataclass `Kwargs` validates the Python-call path (1) | ✅ Ported this session | `test_component.py` `TestKwargsRenderValidation::{test_missing_required_kwarg_raises, test_unexpected_kwarg_raises}`. djc's matrix locks the missing-required failure on the input path (its unexpected-input case fires while constructing an output class); the port locks both failure modes, missing-required and unexpected kwarg, on the Python-call input path. The template-tag path was already locked (`test_tag_rules.py`). |
| A subclass redeclaring `Kwargs` revalidates with its own class; an un-redeclared `Kwargs` is inherited by identity (1) | ✅ Ported this session | `test_component.py` `TestSubclassTypedInputs::{test_redeclared_kwargs_revalidates_with_the_subclass, test_unredeclared_kwargs_is_inherited_by_identity}`. The identity test also locks that the parent's class does the validating (the error message names `Button.Kwargs`). The `Args` half of djc's test drops (#20). |
| Custom `Args` classes: invalid instances raise; custom class carried through (2) | ❌ Drop | citry is kwargs-only; `Args` does not exist (divergence #20). |

</details>

**Accounting: 13/13 methods** (6 already-covered, 2 ported this session, 3
replace, 2 drop).

### `test_dependencies.py` (28 tests) - triaged `✔`, all ports resolved

Fully triaged 2026-07-02 against citry source and the real deps tests. citry's
strategy model differs structurally: djc has strategies
`document/simple/prepend/append/raw` plus a legacy `type=` alias; citry splits
this into `deps_strategy` (`document/simple/fragment/ignore`) x `deps_position`
(`smart/prepend/append`). Citry emits the client runtime when a component uses
`$component`, or when a mounted page has assets a later fragment must
deduplicate, so djc's "a dependency-manager script always appears" assumption
does not port.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Default document emission (CSS to `<head>`, JS to `<body>`), child deps bubble, same component emits once, resolve dedupes records | ✅ Already-covered | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestDocumentEmission::{test_js_and_css_land_in_default_locations, test_child_component_deps_bubble_to_the_page, test_same_component_rendered_twice_emits_once, test_resolve_records_dedupes_duplicate_records}`. |
| Explicit dependency-tag placement overrides default (djc `{% component_js/css_dependencies %}` to citry `<c-js>` / `<c-css>`) | ✅ Already-covered | `TestPlaceholders::{test_c_js_and_c_css_mark_the_spots, test_first_placeholder_wins_later_ones_render_nothing, test_placeholders_removed_even_without_deps}`. |
| `deps_strategy='ignore'` opts out; invalid strategy/position raise `ValueError` | ✅ Already-covered | `TestStrategiesAndPositions::{test_ignore_inserts_nothing_and_drops_placeholders, test_invalid_values_raise}`. |
| `Media`/`Dependencies` url + inline entries, `Script`/`Style` objects, pre-rendered `Markup` tags, deps load before component JS | ✅ Already-covered | `TestDependenciesEntries` (6 methods). |
| Component-id marker on the root element (single/multiroot/nested/loops) | ✅ Already-covered | [`test_markers.py`](../../packages/py/citry/tests/test_markers.py). |
| Component inline JS/CSS containing its own end tag raises, naming the component | ✅ Ported this session | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestComponentAssetEndTagGuard::{test_component_js_containing_its_end_tag_raises, test_component_css_containing_its_end_tag_raises}`. Divergence: citry raises `ValueError` where djc raised `RuntimeError` (catalog #4). |
| `on_dependencies` hook returning `None` is a no-op (component assets survive) | ✅ Ported this session | `TestOnDependenciesHooks::test_returning_none_keeps_the_component_assets`. |
| djc `prepend`/`append`/`raw` strategies and legacy `type=` map to citry `deps_position` + `deps_strategy='ignore'` | ♻️ Replace | `TestStrategiesAndPositions::{test_prepend_and_append_positions, test_simple_matches_document_for_now}`. citry has no `raw` strategy or `type=` alias (catalog #4). |
| Nested Python-side `render()` defaulting deps to `ignore` | ♻️ Replace | citry bubbles dependency records up and resolves once at the outermost `serialize()`, so there is no per-render `deps_strategy` default to test (`emission.py` `emit_dependencies`). |
| `on_dependencies` classmethod adding an extra `kind='extra'`, `wrap=False` entry (unwrapped) | ✅ Ported this session | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestOnDependenciesHooks::test_component_classmethod_can_add_an_extra_entry`. |
| Nested multi-component tree dedupes and orders class-level assets first-seen (djc's four `*_multiple_components_dependencies`) | ✅ Ported this session | `TestDocumentEmission::test_nested_components_dedupe_and_keep_first_seen_order` (one test covers dedup, first-seen order, and `simple == document`). |
| Fragment strategy returns malformed/unclosed HTML byte-for-byte (no auto-close) | ♻️ Replace | Not portable: citry's V3 parser rejects a malformed component template at parse time (`SyntaxError: Unclosed tag`), and there is no standalone `render_dependencies()` fed arbitrary HTML, so the djc premise cannot exist. The "fragment mode does not mangle the rendered body" guarantee is covered by [`test_deps_fragments.py`](../../packages/py/citry/tests/test_deps_fragments.py) `TestFragmentStrategy`. Surfaced divergence #7. |
| `render_dependencies()` as a standalone function + the two-phase `_RENDERED` / `CSS_PLACEHOLDER` / `JS_PLACEHOLDER` contract | ❌ Drop | citry has no separate `render_dependencies` step or `_RENDERED` marker; deps resolve inside `serialize()`. |
| Legacy `type=` argument (alias for `append`) | ❌ Drop | djc `TODO_v1`; citry uses `deps_strategy` / `deps_position`. |
| Unconditional dependency-manager script (`django_components.min.js`) on every document render | ❌ Drop | citry ships the runtime on demand: when a component uses `$component`, or when a mounted page carries assets a later fragment must dedup against (`emission.py:145`). A djc test that counts the manager script on every render would not port; the on-demand emission and fragment dedup are covered by [`test_deps_fragments.py`](../../packages/py/citry/tests/test_deps_fragments.py) `TestMountedDocumentFlow` and [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py). |
| `render_to_response()` resolves deps | ⏭️ Skip (Django) | citry's HTTP surface is the WSGI/route layer ([`test_deps_urls.py`](../../packages/py/citry/tests/test_deps_urls.py)); no `render_to_response` wrapper. The deps guarantee is the `serialize()` default, already covered. |

</details>

### `test_dependency_rendering.py` (18 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| No rendered components, including multiple registered asset-bearing classes (4) | ✅ / ♻️ | [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `TestPlaceholders::{test_placeholders_removed_even_without_deps, test_registered_but_unrendered_components_emit_no_assets}` prove that only rendered instances contribute records. Unlike djc's direct template-tag output, Citry resolves and removes empty internal placeholders. [`test_deps_fragments.py`](../../packages/py/citry/tests/test_deps_fragments.py) `TestMountedDocumentFlow::test_component_less_mounted_page_stays_lean` also locks the no-runtime/no-manifest result. |
| Single component dependencies and internal placeholder cleanup (2) | ✅ Already-covered | `TestDocumentEmission::{test_js_and_css_land_in_default_locations, test_child_component_deps_bubble_to_the_page}`, `TestDependenciesEntries::test_url_entries_emit_src_and_href_tags`, and `TestPlaceholders::test_c_js_and_c_css_mark_the_spots` cover the rendered tags and placement; `test_deps_vars.py::TestManifestAndRuntime::test_manifest_marks_url_dependencies_as_loaded` covers the mounted-document manifest. |
| Only the CSS or JS placement tag is present (2) | ♻️ Replace | `TestPlaceholders::test_one_placeholder_does_not_suppress_the_other_asset_kind` locks Citry's deliberate contract: `<c-css />` and `<c-js />` position their own category, while the other category uses its default location. djc's tags instead select which category is emitted; divergence #23. |
| Multiple URL entries and a nested multi-component tree (2) | ✅ Ported | `TestDocumentEmission::test_nested_url_dependencies_emit_once_in_first_seen_order` proves every JS/CSS URL emits once, shared URLs dedupe across classes, dependency entries precede component assets, and parent/child/sibling first-seen order survives within each bucket. Existing `test_nested_components_dedupe_and_keep_first_seen_order` independently covers class-level inline assets. |
| Multiple placeholders are all removed (1) | ✅ Already-covered | `TestPlaceholders::{test_first_placeholder_wins_later_ones_render_nothing, test_placeholders_removed_even_without_deps}`. |
| Dash or slash in the registered component name (1) | ✅ / ❌ | Dash names are covered by [`test_component_registry.py`](../../packages/py/citry/tests/test_component_registry.py) `TestNameNormalization` / `TestManualRegister` / `TestNameValidation`. Forward slashes are intentionally invalid because Citry component names must be HTML-tag-compatible; divergence #24. Dependency cache URLs use `Component.class_id`, not the authored registry name. |
| Component root markers: single, multiroot, nested stacking, loop instances (4) | ✅ Already-covered | [`test_markers.py`](../../packages/py/citry/tests/test_markers.py) covers single/multiroot/nested root stamping. [`test_deferred_render.py`](../../packages/py/citry/tests/test_deferred_render.py) `TestLoopVarKwargs::test_loop_variable_resolved_eagerly_per_iteration` proves loop-created instances receive fresh `c2`/`c3`/`c4` markers. |
| Component inside a Django inclusion tag, including a tag returning `None` (2) | ⏭️ Skip (Django) | Citry has no Django template `Library` or `inclusion_tag`; divergence #14. The portable guarantee that an externally nested child's dependencies bubble to the page is covered by `TestDocumentEmission::test_child_component_deps_bubble_to_the_page`. |

</details>

### `test_dependency_manager_e2e.py` (12 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Runtime bootstrap/API and the legacy global alias (2) | ♻️ Replace / ❌ Drop | [`e2e/test_runtime_e2e.py`](../../packages/py/citry/tests/e2e/test_runtime_e2e.py) `test_manager_api_surface_is_locked`, `test_second_runtime_load_keeps_existing_manager_and_state`, and `test_runtime_preserves_a_preexisting_citry_namespace` lock Citry's singleton `globalThis.Citry.manager`. The old `DjangoComponents` namespace, `createComponentsManager()` factory, `unescapeJs`, and legacy `Components` alias are not carried; divergence #85. |
| Load JS, load CSS, and skip URLs marked as loaded (3) | ✅ Already-covered | `test_load_js_appends_once_per_url_and_marks_loaded` and `test_load_css_appends_once_per_url_to_head` assert placement, repeated and in-flight URL dedupe, distinct URLs, `markScriptLoaded`, loaded bookkeeping, inline assets, and failed-load retry. |
| Successful synchronous call: callback payload and return value (1) | ♻️ Replace / ✅ Ported this session | `test_call_payload_shape_and_els_in_document_order` locks the one-object `{id, els, data}` payload and document-order roots. `test_call_is_fire_and_forget_and_numeric_return_is_ignored` now locks the other half: the callback runs, an ordinary return is ignored, and `callComponent()` returns `undefined`. Divergences #22 and #86. |
| Promise-returning callback (1) | ♻️ Replace | Component initialization is synchronous. `test_callback_non_function_return_is_not_treated_as_cleanup` proves a Promise is not mistaken for cleanup; [`e2e/test_alpine_lifecycle_e2e.py`](../../packages/py/citry/tests/e2e/test_alpine_lifecycle_e2e.py) `test_unsupported_async_parent_settles_descendant_and_independent_branch` proves the unsupported Promise and its rejection are reported without blocking descendants or an independent branch. Divergence #86. |
| Synchronous throw and asynchronous rejection (2) | ♻️ Replace | `test_throwing_callback_does_not_break_later_classes` proves a synchronous failure is logged with its original error and a later class still initializes. `test_unsupported_async_parent_settles_descendant_and_independent_branch` does the same for a rejected Promise. Citry logs and isolates these failures rather than rejecting a `callComponent()` Promise; divergence #86. |
| No DOM root for the requested instance (1) | ♻️ Replace (opposite contract) | `test_callback_fires_with_empty_els_when_marker_absent` locks that the callback still runs with `els=[]`; Citry does not reject the call. Divergence #87. |
| Call waits for component data or callback registration (2) | ♻️ Replace (existing coverage) | `test_call_waits_for_component_data` and `test_call_waits_for_callback_registration` lock both queue directions. Readiness is observed through the callback's effects because Citry's call itself is fire-and-forget. |

</details>

**Accounting: 12/12 methods** (3 already covered, 8 replaced by Citry's
runtime contract, 1 dropped compatibility alias). No production defect was
found in the dependency manager.

### `test_dependency_rendering_e2e.py` (15 tests) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Single and nested multiple components load Component.js/css plus Dependencies.js/css (2) | ✅ / ♻️ | [`e2e/test_document_e2e.py`](../../packages/py/citry/tests/e2e/test_document_e2e.py) `test_component_and_dependency_assets_execute_in_bucket_order` combines two component classes, inline `Dependencies` entries, class JS/CSS, and applied browser styles. Existing `test_component_js_runs_and_receives_data`, `test_component_css_applies_with_injected_vars`, and unit-level child bubbling complete the data/nesting paths. |
| Component and Dependencies CSS with browser JavaScript disabled (1) | ✅ Ported | `test_component_and_dependency_css_apply_without_javascript` creates a real JS-disabled browser context and proves both server-emitted stylesheets still apply while neither script runs. |
| Component/Dependencies script ordering: class probe last, dependency probe last, dependency probe first (3) | ✅ Ported | The three cases of `test_component_and_dependency_assets_execute_in_bucket_order` prove dependencies execute before component code, first-seen order is kept within each bucket, a late component probe sees everything, a late dependency probe sees dependencies only, and an early dependency probe sees no later globals. |
| Fragment Component.js/css load and apply (1) | ✅ Already-covered | [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py) `test_fragment_scripts_load_on_demand` and `test_fragment_static_and_scoped_css_load_on_demand`. |
| Fragment local Dependencies JS/CSS load and apply (1) | ✅ Ported | `test_fragment_local_dependency_assets_load_on_demand` exercises the real fragment serializer, manifest observer, inline descriptor materialization, JS execution, and computed CSS through the live mounted routes. |
| Fragment inserted by Alpine `x-html` or HTMX (2) | ♻️ Replace | Citry locks the framework-independent contract instead of downloading third-party CDN scripts: [`e2e/test_runtime_e2e.py`](../../packages/py/citry/tests/e2e/test_runtime_e2e.py) `test_manifest_nested_in_inserted_subtree_is_processed` models an HTMX-style wrapped insertion, while [`e2e/test_events_client_e2e.py`](../../packages/py/citry/tests/e2e/test_events_client_e2e.py) `test_fragment_inserted_into_live_x_data_region_stays_isolated` inserts after Citry's Alpine runtime has initialized inside a live `x-data` region. These prove DOM-insertion compatibility, not a promise about a particular third-party release. |
| Fragment bootstraps a page without the document runtime (1) | ✅ Already-covered | `e2e/test_runtime_e2e.py::test_fragment_bootstraps_runtime_on_page_without_it` is the exact Citry replacement. |
| External Alpine placement in head/body and the too-late listener case (4) | ♻️ Replace | Citry Events owns and starts its pinned Alpine runtime. `test_head_placed_c_js_still_isolates_nested_instances`, `test_page_boots_seeds_state_and_stays_error_free`, the bootstrap-order tests, and `test_second_alpine_instance_warns_and_is_not_clobbered` cover Citry's lifecycle. Plain Alpine attributes remain untouched by the binding rewrite. The djc contract of arranging an external Alpine copy relative to component JS is replaced by divergence #25. |

</details>

### `test_expression.py` (31)

In citry every `c-*` value and every `{{ }}` is *already* a Python expression, so
djc's "python expression" and "literal container" halves are covered end to end
by the Rust safe-eval suite. The Django-syntax half (filters, `{% %}` blocks,
`{# #}` inside arguments, colon-prefixed aggregate kwargs, positional/iterable
spreads) is a genuine drop, each confirmed absent from citry source.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Python expressions: `not`, and/or conditional with short-circuit, method calls, arithmetic (4) | ✅ Already-covered | [`test_safe_eval.py`](../../packages/py/citry_core/tests/test_safe_eval.py) `TestSyntax::{test_allow_unary_not, test_allow_boolean_mixed_operators, test_transform_method_call}`; the template layer via [`test_nodes.py`](../../packages/py/citry/tests/test_nodes.py) `TestExprNodeEval::test_evaluates_expression` (`{{ a + b }}` renders `5`). |
| Literal containers: list, list with variables, dict, dict with variables, nested structures, list/dict holding python expressions (7) | ✅ Already-covered | `test_safe_eval.py` `TestSyntax::{test_allow_list_with_literals, test_transform_variable_in_list, test_allow_dict_with_literals, test_transform_variable_in_dict, test_allow_nested_data_structures, test_allow_computed_dict_key_and_starred_list_unpack}`. |
| Spread validation: raises on a value-less spread, raises on a non-mapping (2) | ✅ Already-covered | Parse-time in Rust: `crates/citry_template_parser/tests/tag_parser_spreads.rs::test_c_bind_no_value` ("must have a non-empty value"); render-time in [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeAttrs::test_c_bind_non_mapping_raises`. |
| The expression object resolves to a raw, untouched Python value (1) | ✅ Ported this session | [`test_nodes.py`](../../packages/py/citry/tests/test_nodes.py) `TestExprRawValue` (11 tests): `ExprNode.evaluate` / `ExprHtmlAttr.resolve` return the identical object with no escaping and no `str()`, the escaping contrast against `render()`, the extension-built boolean attr short-circuiting to `True` without evaluating, and compile-once reuse (asserted with a counting wrapper and a control probe proving it is not vacuous). |
| A component tag nested inside an argument (1) | ✅ Ported this session | `TestComponentNodeAttrs::test_template_attr_can_hold_a_component_tag`: a `c-*` nested-template attribute may hold a component tag, which resolves in the parent's scope. Observed and locked: it renders **last**, not first: the attribute yields a `CitryRender` still holding a `DeferredComponent` (cid order `main=c1`, `span=c2`, `i=c3`). |
| A multi-line argument value (1) | ✅ Ported this session | [`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py) `TestMultilineAndSpecialCharValues` (5 tests): values spanning lines, square brackets, `!=`, and nested quotes. citry's equivalent of the django-components #1255 regression. There is no backslash escape inside a quoted value, so nested quotes must be the opposite kind. |
| Later spreads overwrite earlier ones (1) | ✅ Ported this session | `TestComponentNodeAttrs::test_kwarg_contributions_apply_left_to_right`. The element path was already covered, but a component tag runs through a different function (`ComponentNode._resolve_inputs`, plain last-one-wins) than an element (`merge_attrs`, which merges class/style), so the element tests did not transfer. |
| `{{ }}` variable inside a quoted argument; mixed literal text plus expression in one value (2) | ♻️ Replace | A plain attribute reaches the child verbatim, so `{{ }}` there is not interpolated: [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeAttrs::test_static_input_is_literal_while_c_form_computes` asserts both halves on one page. For mixed text, a `c-` value is one whole expression, so the string is built on purpose rather than by accident: [`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py) `TestBuildingValuesWithExpressions` (`c-label="f' {flag} '"` renders `label=" True "`, the same result djc produced by downgrading a typed value). Divergences #33 and #39. |
| Debug-mode error wrapping preserves the original error (1) | ♻️ Replace | citry has no `engine.debug` toggle: error annotation is always on and the original exception type and message survive, asserted throughout [`test_error_trace.py`](../../packages/py/citry/tests/test_error_trace.py). |
| Malformed tag-like text is passed through as literal text (1) | ♻️ Replace | Text that looks like a Django tag stays text; covered by the Rust parser tests (`crates/citry_template_parser/tests/tag_parser_expressions.rs`) rather than a Python render test. |
| `{% %}` block tags inside arguments; `{# #}` comments inside argument values (2) | ❌ Drop | citry has no `{% %}` language at all (divergence #37). `{# #}` works between elements and between attributes, but not inside an attribute value: in a plain attribute it renders as visible text, and in a `c-` attribute it is a parse error (divergence #40). Verified by probe. |
| Django filters: inside an expression, inside a list literal, and a `slice` filter on a list (3) | ❌ Drop | citry has no filters; `\|` is Python bitwise-or (divergence #18). Verified by probe: `safe_eval('a\|lower')` looks `lower` up as a variable. |
| Spreading a list or other non-mapping iterable (1) | ❌ Drop | Components are kwargs-only, so an iterable spread has nowhere to land (divergence #20). |
| Colon-prefixed aggregate kwargs, and the `is_aggregate_key` helper (2) | ❌ Drop | No aggregate-key feature exists: zero hits for `aggregate` across citry source and crates. Write the nested dict as one expression instead (divergences #1 and #34). |
| Django `Origin` / `Parser` / `StringifiedNode` internals and the debug-origin fallback (2) | ⏭️ Skip (Django) | White-box tests of Django template-engine internals and a django-components class; none of these types exist in citry. |

**Accounting: 31/31 methods** (13 already-covered, 4 replace, 4 ported this session, 8 drop, 2 skip-Django). Two further citry-native gaps were found while triaging and closed in the same pass, though they port no djc method: `TestStaticAttrValuesAreNotInterpolated` in `test_attrs_template.py` (a `{{ }}` written into a *static* attribute renders verbatim, the highest-risk silent change for a djc user, divergence #33) and `TestTemplatePosition::test_component_input_expression_error_shows_template_lines` in `test_error_trace.py` (an error in a `c-*` input surfaces with the **parent's** path and the whole component tag underlined, because the input is evaluated before the child is queued).

</details>

### `test_extension.py` (25) - triaged `✔`

The extension system: registration, config, hooks, defaults, and URL routes.
The earlier seeded row called "extension views" Django-only; that was wrong:
they are extension-declared URL routes, and citry has the same surface
(`Extension.urls`, mounted into `Citry.urls`), so two of the three route tests
are ports against it. Surfaces divergences #55-#59 and #90.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Extension roster and ordering; config attached to components; `Config(None)` instantiation; name conflicts with Component API; duplicate names; registration/unregistration hooks; `on_slot_rendered` (payload and override); `on_component_rendered` raising and returning html; asset hooks (inline and file); `on_dependencies` modifications propagating (13) | ✅ Already-covered | [`test_extension.py`](../../packages/py/citry/tests/test_extension.py) (roster, conflicts, registration hooks, rendered-hook raise/return in `test_rendered_replace_with_string` / `test_rendered_raise_propagates`, template hooks in `TestTemplateHooks`); [`test_slot_node.py`](../../packages/py/citry/tests/test_slot_node.py) `TestOnSlotRenderedHook`; [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestLoadingHooks` (file template through the hook, and the js/css loaded hooks); [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) :431 (extension-appended script emitted). |
| Nested config class inheriting a plain parent merges all three sources (1) | ✅ Ported this session | `TestComponentConfig::test_nested_config_inherits_plain_parent_class` (extension factory attrs + nested class's own + plain parent's, incl. a classmethod). |
| GC-time component-class extension callback (1) | ❌ Drop | Python may run finalizers while arbitrary locks are held, so garbage collection executes no user hooks. `on_component_class_deleted` and `OnComponentClassDeletedContext` are absent from Citry; extensions release deterministic resources through `on_component_unregistered` (divergence #90). |
| Render-hook payload completeness: fills arrive as normalized `Slot` instances; `js_data`/`css_data` reach a user extension verbatim; the success payload (component instance, its id matching the marker, the result, error `None`) (1, via 2 tests) | ✅ Ported this session | `TestRenderHooks::{test_input_slots_and_data_payloads, test_rendered_success_payload}`. Observed and locked: `ctx.component` is the rendered instance (a fresh one carrying the render id), not the object the caller constructed. |
| `extensions_defaults`: empty entry is a no-op; defaults override attrs and classmethods; unlisted keys kept; unknown names silently ignored (2) | ✅ Ported this session | `TestComponentConfig::{test_empty_defaults_entry_is_no_op, test_defaults_override_attrs_and_classmethods}`. |
| Extension URL routes: `{param}` values reach the handler; a parent path holding only children stays unmatched (2, the corrected "extension views") | ✅ Ported this session | [`test_deps_urls.py`](../../packages/py/citry/tests/test_deps_urls.py) `TestCitryUrls::{test_user_extension_route_params_passed_to_handler, test_user_extension_parent_route_serves_children_not_itself}`. Params are always strings (djc's `<int:id>` converted; divergence #57). |
| `on_component_rendered` on a failed render; reading hook-processed assets via attribute access (2) | ♻️ Replace | Deliberate divergences, equivalently tested: ancestors receive the bubbling error and the failing component's own hook does not fire ([`test_error_trace.py`](../../packages/py/citry/tests/test_error_trace.py) :437-:472, divergence #56); loaded, hook-processed content is read via `get_template()`/`get_js()`/`get_css()` while the class attributes keep the authored strings (`test_assets.py` `TestLoadingHooks` and `TestJsCssFiles::test_fields_stay_raw_declarations`; divergence #59). |
| Registry lifecycle hooks (`on_registry_created`/`deleted`); the legacy `ExtensionClass` nested-class alias (2) | ❌ Drop | No standalone registry object (it is part of each `Citry` instance; observe engine creation with `on_extension_created`, divergence #55); exactly one config spelling, the `Config` class attribute (divergence #58). |
| Django URL-resolver population mechanics (1) | ⏭️ Skip (Django) | `get_resolver()._populated` is Django internals; citry builds its route table lazily on property access. |

**Accounting: 25/25 methods** (13 already-covered, 6 ported this session via 7 tests, 2 replace, 3 drop, 1 skip-Django).

</details>

### `test_registry.py` (18)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Decorator/custom-registry registration, simple register, two components (4) | ✅ / ♻️ | [`test_component_registry.py`](../../packages/py/citry/tests/test_component_registry.py) `TestRegistration` / `TestManualRegister`; [`test_citry.py`](../../packages/py/citry/tests/test_citry.py) `TestCitryComponentAssignment`. Citry replaces `@register(..., registry=...)` with class-level `citry = app` or `app.register(...)`. |
| Duplicate name, repeated same-class registration, live class-ID collision (3) | ✅ Ported | Existing duplicate/no-op coverage plus [`test_class_id.py`](../../packages/py/citry/tests/test_class_id.py) `TestClassIdLookup::test_live_class_id_collision_is_rejected`. A rejected collision leaves both the name registry and reverse index pointing at the original class. |
| Unregister leaves unrelated registrations intact, simple unregister, failed unregister (3) | ✅ Ported | [`test_component_registry.py`](../../packages/py/citry/tests/test_component_registry.py) `TestUnregister`; Django `Library.tags` bookkeeping itself drops. |
| Unregister then register a re-imported replacement (1) | ✅ Ported | [`test_class_id.py`](../../packages/py/citry/tests/test_class_id.py) proves the class-ID reverse index survives one alias, is removed with the final alias, and accepts a replacement class with the same stable ID. |
| Registration weakref finalizer bookkeeping (1) | ❌ Drop | Citry's registry holds explicit strong registrations; unregister/`Citry.clear()` control their lifetime. There is no `_finalizers` implementation to detach. |
| Node-subclass cache ownership/population (3) | ♻️ Replaced | V3 has no generated Django `Node` subclass cache. [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py) `TestBuildTagRules::test_template_parsing_populates_separate_instance_caches` exercises the analogous derived parser state and proves real parsing populates separate per-`Citry` tag-rule caches. |
| Per-registry context/formatter settings (1) | ♻️ Replaced | Settings are owned by each `Citry` instance; [`test_citry.py`](../../packages/py/citry/tests/test_citry.py) covers independent instances and settings. `context_behavior` and tag formatters drop under divergences #9 and #15. |
| Protected framework/structural tag names (1) | ✅ Ported | Existing built-in-name guards plus the parametrized `TestDuplicateDetection::test_structural_tag_name_raises` cover all V3 parser-reserved names: `if`, `elif`, `else`, `for`, `empty`, `raw`, `fill`, and `slot`. Divergence #28. |
| Global weak `all_registries()` inventory (1) | ❌ Drop | Citry deliberately scopes state to explicit `Citry` objects and exposes no process-global registry tracker. Divergence #26. |

**Accounting: 18/18 methods.**

</details>

### `test_slots.py` (22)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Construction, required fills, standalone calls, positional/keyword data + fallback, escaping (7) | ✅ Ported / ♻️ Replaced | [`test_slots.py`](../../packages/py/citry/tests/test_slots.py) covers the value API and now passes a Python callable through a real `<c-slot>` site. Citry deliberately omits Django `Context` from `SlotContext`; divergences #8, #9, and #31. |
| Stable contents/function identity for strings, callables, Slots, and template fills (5) | ✅ Ported | `TestNormalizeSlotFills` now asserts callable identity and copied-Slot identity directly; template-fill bodies remain stable compiled node lists. |
| Metadata for Python and template fills (6) | ✅ Ported / ♻️ Replaced | `TestNormalizeSlotFills`, `TestImplicitDefaultSlot::test_implicit_fill_slot_metadata`, and `TestNamedFills::test_fill_slot_metadata` cover names, contents, source positions, and the copied `extra` bag. Citry's `source_position` replaces Django `nodelist` / `fill_node` backreferences. |
| DJC `{% fill body=... %}` shortcut (3) | ♻️ Replaced / ❌ Drop | Citry renders an existing Slot normally inside a fill body: `<c-fill name="x">{{ my_slot }}</c-fill>`. Supplying both a shortcut and body cannot arise because there is no shortcut. Divergence #31. |
| Template-created Slot called after its originating component render (1) | ✅ Ported | `TestSlotStr::test_template_fill_with_component_can_render_after_page` exposed and locks the deferred-descendant case: `str(slot)` settles nested components through the iterative queue before serialization and remains repeatable. |

**Accounting: 22/22 methods.**

</details>

### `test_cache.py` (3 tests) - triaged `✔`

djc's two caching layers in one file: the LRU store utility and the cache of
processed component JS/CSS. citry keeps the same LRU semantics on its
per-instance store and moves the script cache into the dependencies
extension (per instance, filled at first render). Divergences #74 and #75.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| LRU store: reads refresh recency, overflow evicts the stalest entries, `clear()` empties (1) | ✅ Already-covered | [`test_cache.py`](../../packages/py/citry/tests/test_cache.py) `TestInMemoryCache::{test_max_entries_drops_least_recently_used, test_get_set_has_delete, test_clear}` assert the guarantees, more strictly than djc's own file: djc's assertions also pass on a store that never refreshes recency on reads (its gets happen in insertion order), while citry's eviction test catches that. Implementation: `cache.py:77-94` (ordered store, refresh on get and set, oldest-first eviction). |
| `maxsize=0` / `maxsize=-1` construct fine and silently store nothing (1) | ♻️ Replace | citry rejects the construction instead: `max_entries <= 0` raises `ValueError` (`cache.py:68-70`), locked by `TestInMemoryCache::test_max_entries_must_be_positive` (the `-1` case shares the same guard, probe-confirmed). A store that silently drops everything looks like a working cache and hides misconfiguration. |
| The processed-JS/CSS cache: keys present right after class definition, the exact cached JSON payload, vars scripts cached after a render (1) | ♻️ Replace | citry's dependencies extension writes to the per-instance cache at first render, not at class definition, under `citry:<class_id>:js\|css` keys plus content-addressed and vars keys. Variable payloads use canonical JSON and a 32-hex prefix of SHA-256; this is Citry's own content-addressing contract, not a byte-identical djc format. Locks are distributed: [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) `gen_cache_key` assertions plus `TestScriptCacheLifecycle::test_component_without_assets_writes_no_cache_entries`; [`test_deps_urls.py`](../../packages/py/citry/tests/test_deps_urls.py) (served-from-cache, repopulation on miss, content-addressed overlap); [`test_deps_vars.py`](../../packages/py/citry/tests/test_deps_vars.py) (base64 round-trip, identical data shares one script) plus `TestJsVars::test_js_data_with_plain_js_is_not_delivered`; [`test_deps_types.py`](../../packages/py/citry/tests/test_deps_types.py) (JSON round-trip). Divergences #74, #75. |

</details>

**Accounting: 3/3 methods** (1 already-covered, 2 replace; the 2 tests ported
this session lock replacement sub-guarantees inside the third row, 0 djc
methods of their own).

---

## Test review by file (primarily Django)

Same status legend as above. These files exercise the Django-facing surface;
many are ⏭️ Skip (they belong in the `django-components` wrapper) or ♻️ Replace
(the parser tests move to the Rust crate).

### `test_autodiscover.py` (4) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `autodiscover()` imports component modules under the configured dirs, registers their components, returns module names, and repeat scans do not raise (1) | ✅ Already-covered | [`test_autodiscovery.py`](../../packages/py/citry/tests/test_autodiscovery.py) `TestAutodiscoverMethod::{test_returns_imported_module_names, test_is_idempotent}`, `TestLazyDiscovery::test_first_lookup_triggers_discovery`, `TestEndToEnd::test_walk_registers_a_pre_imported_module`; built-ins registered internally (`TestInitialize`). |
| The `libraries` setting and `import_libraries()` (with `map_module`) (2) | ❌ Drop | Deliberately not carried (recorded in [`migration_djc.md`](migration_djc.md), and being dropped upstream); `CitrySettings` has no such field. Modules are found via the `Citry(dirs=...)` scan or imported like any Python module (divergence #64). |
| The `@djc_test` harness's `sys.modules` teardown not re-importing pre-loaded modules (1) | ♻️ Replace | The harness premise is djc-only: citry ships no testing harness, and the one process-wide piece of state is the default `Citry` instance, which a test avoids by passing its own instance (divergence #66). The guarantee the harness guarded is now locked directly: `TestAutodiscoverMethod::test_rescan_does_not_reexecute_loaded_modules` (an already-imported module is not replaced or re-run by a second scan, added this session). |

**Accounting: 4/4 methods** (1 already-covered, 2 drop, 1 replace with the guarantee it guarded ported).

</details>

### `test_context.py` (47 tests) - triaged `✔`

Confirmed 2026-07-02: every group is Django `Context` machinery citry lacks, or
a dropped setting. The engine-level guarantees that do survive (child variables
isolated per component, slot/fill body rendering in the parent's scope,
provide/inject downward flow) are already covered by citry's own tests, so
nothing needs porting. Surfaces divergences #8-#11.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestContext` / `TestComponentsCanAccessOuterContext` / `TestOuterContextProperty` (nested `Context` shadowing, ambient outer-context access, `self.outer_context`) | ⏭️ Skip (Django) | citry has no `Context` object and never reads an ambient template context (`citry/citry_context.py`: a child gets fresh variables from its own `template_data`). The surviving guarantee (child variables isolated) is covered by [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py). |
| `TestParentArgs` (parent kwargs; slot content sees the parent scope) | ♻️ Replace | Portable core covered by [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py) `TestScopedSlotData::test_fill_data_combines_with_parent_scope` and `test_fill_body_renders_in_parent_scope`. The Django-`Context` and `context_behavior` axes do not port. |
| `TestContextCalledOnce` (`template_data` runs once per instance) | ♻️ Replace | Engine invariant citry keeps (one `template_data` call per `ComponentNode` render). An explicit call-count regression test is optional: citry has no context-flatten pass that could double-invoke. |
| `TestIsolatedContext` / `TestIsolatedContextSetting` (`only`, `context_behavior='isolated'`) | ❌ Drop | citry is always isolated / `only`-like; the `context_behavior` setting is deliberately not carried. |
| `TestContextProcessors` (Django `RequestContext`, context processors, `self.request`, CSRF, `#1569`) | ⏭️ Skip (Django) | None of these exist in citry (grep: `RequestContext` / `context_processors` / `csrf` appear only in the vendored snapshot). Belongs in the `django-components` wrapper. |
| `TestContextVarsIsFilled` (`{{ component_vars.is_filled.<slot> }}`) | ♻️ Replace | Dropped magic variable (djc `TODO_v1`); check `slots.get(name)` in `template_data` + `<c-if>`. Control-flow-gated fills: [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py) `TestFillsUnderControlFlow`. |

</details>

### `test_django_cache_tag.py` (12 tests)

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Top-level and nested miss/hit | ✅ Ported | Public `<c-cache>` tests cover misses, hits, nested fragments, cross-kind nesting with `Component.Cache`, and outer-hit suppression. The upstream standalone Django-template case is adapted as a root Citry component template rather than claimed as a literal one-for-one port. See [`test_ext_cache_fragment.py`](../../packages/py/citry/tests/test_ext_cache_fragment.py). |
| Explicit `{% load cache %}` | ❌ Drop | Django template-library loading has no Citry equivalent. |
| Slot/component inside cached body | ✅ Ported | `test_ext_cache_fragment.py::TestFragmentCacheOwnershipAndNesting::test_literal_slot_replays_the_current_callers_fill` covers a literal `<c-slot>` inside `<c-cache>` with a caller fill containing a component, proving one miss, one hit, fresh replay IDs, and current-writer ownership. Replay of Dependencies and Events is covered by `e2e/test_cache_replay_e2e.py`. |
| `expire_time` and `vary_on` | ✅ Replaced | `c-ttl` covers engine defaults, positive values, and `None`; `test_ext_cache_fragment.py::TestFragmentCacheLookup::test_each_field_in_structured_variation_misses_independently` proves both fields of one structured `c-vary` independently select entries. |
| Named backend | ♻️ replaced | V1 intentionally uses the one cache backend owned by the `Citry` instance. |
| Frozen inner render ID | ✅ Reversed assertion | Every component archived inside `<c-cache>` gets a fresh ID on replay; two uses of one artifact in a page have disjoint descendant IDs. |
| Error in body | ✅ Ported | Propagated and recovered body errors never publish a poisoned entry; later successful renders can still populate it. |

**Accounting: 12/12 methods** (4 direct ports, 1 Django-only drop, 4 syntax/API
replacements, 1 deferred backend alias, 1 reversed identity assertion, and 1
error-path port). All applicable V1 replacements are complete.

</details>

### `test_finders.py` (6), `test_signals.py` (3), `test_integration_template_partials.py` (1), `test_templatetags_extends.py` (25) - all triaged `✔`

Confirmed 2026-07-02: all four are Django integration citry does not have; every
"portable-looking" behavior resolved to an existing citry test. Surfaces
divergences #12-#14 and #16.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `test_finders.py`: Django staticfiles finder, `static_files_allowed`/`forbidden`, refusing to serve `.py`/`.html` source | ⏭️ Skip (Django) | citry serves only generated assets via its own routes (`citry/ext/dependencies/routes.py` serves stable compatibility and content-addressed `cache/` paths; [`test_deps_urls.py`](../../packages/py/citry/tests/test_deps_urls.py)), never component source. |
| `test_signals.py`: Django `template_rendered` signal, `instrumented_test_render` | ⏭️ Skip (Django) | citry observes renders through extension hooks (`on_component_rendered`, [`test_extension.py`](../../packages/py/citry/tests/test_extension.py)) and logger tracing ([`test_logger.py`](../../packages/py/citry/tests/test_logger.py)). |
| `test_integration_template_partials.py`: `django-template-partials` integration | ⏭️ Skip (Django) | Third-party Django library; no citry equivalent. The "component CSS/JS lands in the output" guarantee underneath is owned by the deps tests. |
| `test_templatetags_extends.py`: `{% extends %}` / `{% block %}` / `{% include %}` compat (16 groups) | ⏭️ Skip (Django) | citry has no Django template inheritance. Portable bits (nested-component deps default to `ignore`, provide/inject through the tree) are already covered by [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py) and [`test_provide.py`](../../packages/py/citry/tests/test_provide.py). |

</details>

### `test_hotreload.py` (24) - triaged `✔`

djc's autoreload integration. The seeded row was wrong in both directions: its
one flagged gap (weakref pruning) is real but a djc-shaped port would fail
(citry auto-registers classes and the registry holds strong references, so the
class must be unregistered first), and the blanket coverage claim hid four more
gaps, including that `test_reset_files_rereads_js_and_css` asserted JS only.
Surfaces divergences #60-#61. The rendered-class lifetime issue found during
the triage is fixed: after final unregistration, render-cache ownership is weak
and the class plus its file-index entry can be collected.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| File index: register and look up, unknown file empty, multiple classes per file, clear-all; `reset_template` serves stale until reset (the `reset_files` method itself is counted under Ported); hot and restart signal handling plus untracked-file pass-through; template and JS end-to-end reload (10) | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestFileIndexAndResets`; [`test_contrib_django.py`](../../packages/py/citry/tests/test_contrib_django.py) (real `file_changed` signals through `enable_hot_reload`); [`test_reload.py`](../../packages/py/citry/tests/test_reload.py) `TestInvalidateFile`. |
| Dead classes pruned from the index; the CSS half of `reset_files`; one invalidation resets both template and JS/CSS caches; every class sharing a file is reset; inline-only components never indexed; CSS end-to-end reload (6) | ✅ Ported this session | `test_assets.py` `TestFileIndexAndResets::{test_unregistered_class_is_pruned_from_the_index, test_reset_files_rereads_js_and_css (extended to genuinely cover css)}`; `test_reload.py` `TestInvalidateFile::{test_resets_css_files_too, test_one_call_resets_both_template_and_files, test_resets_every_class_sharing_the_file}`, `TestInvalidateAll::test_inline_assets_are_never_indexed`. The pruning test unregisters first: citry's registry holds strong references (divergence #61). |
| The `reload_on_file_change` mode strings (`hot`, `restart`) and invalid-value rejection (3) | ♻️ Replace | The setting is replaced by the explicit call: `enable_hot_reload(engine, mode="hot"\|"restart")` with call-time validation, all asserted in [`test_contrib_django.py`](../../packages/py/citry/tests/test_contrib_django.py) (divergence #60). |
| The `resolved_relative_paths` flag surviving resets (2); `True`/`False`/`"off"` setting normalization (3) | ❌ Drop | No such flag exists (relative paths re-resolve on load), and there is no `reload_on_file_change` setting or `off` mode: hot reload is off unless explicitly enabled (divergence #60). |

**Accounting: 24/24 methods** (10 already-covered, 6 ported this session via 6 tests with one extended, 3 replace, 5 drop).

</details>

### `test_html_parser.py` (7 tests) - triaged `✔`

Confirmed 2026-07-17: all seven upstream behaviors have exact Python-core
equivalents, backed by the Rust HTML-transform suite. This file maps to
`citry_html_transform`, not `citry_template_parser`; no port remains.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Basic transformation, multiple roots, complex nested HTML, void elements, `<head>` metadata, watched-attribute capture, whitespace preservation | ✅ Already-covered | [`test_html_transformer.py`](../../packages/py/citry_core/tests/test_html_transformer.py) carries the same seven named cases and exact output assertions. [`crates/citry_html_transform/tests/transformer.rs`](../../crates/citry_html_transform/tests/transformer.rs) independently covers the Rust implementation (the Python suite owns the exact whitespace assertion). |

</details>

### `test_template_parser.py` (13 tests) - triaged `✔`

Confirmed 2026-07-17 against the V3 Rust parser. The portable tokenizer
guarantees are covered; Django block-tag mechanics are deliberately absent.
The audit added explicit V3 policies for unterminated delimiters and surfaces
divergence #17.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Plain text, `{{ expression }}`, and template comments | ✅ Already-covered | [`tag_parser_expressions.rs`](../../crates/citry_template_parser/tests/tag_parser_expressions.rs) and [`tag_parser_comments.rs`](../../crates/citry_template_parser/tests/tag_parser_comments.rs) assert AST content, positions, variables, and comments. |
| Unterminated `{{` and `{#` delimiters | ♻️ Replace (deliberate divergence) | Django falls back to visible text. V3 reports a syntax error, now locked by `test_unterminated_expression_errors` and `test_unterminated_template_comment_errors`. An unterminated `{%` opener stays literal because V3 has no DTL block syntax (`test_django_block_delimiter_is_literal_text`). |
| Django `{% verbatim %}` and named verbatim blocks | ♻️ Replace / ❌ Drop | [`tag_parser_raw.rs`](../../crates/citry_template_parser/tests/tag_parser_raw.rs) and [`test_raw.py`](../../packages/py/citry/tests/test_raw.py) cover the surviving `<c-raw>` guarantee. Named Django verbatim blocks and their tokenizer tokens do not port. |
| Nested DTL tags, percent/bracket handling, and mixed DTL token streams | ❌ Drop / ♻️ Replace | V3 does not tokenize `{% ... %}`. Its corresponding mixed HTML/component/expression/comment/raw behavior is covered across `tag_parser_composition.rs`, `tag_parser_nested_templates.rs`, `tag_parser_comments.rs`, and `tag_parser_raw.rs`. |

</details>

### `test_templatetags.py` (6 tests) - triaged `✔`

Confirmed 2026-07-17. The file's portable guarantees are multiline component
tags and quote-safe dynamic component inputs; its nested Django tag and
translation syntax does not port.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Component invocation split across lines | ✅ Ported | [`tag_compiler.rs`](../../crates/citry_template_parser/tests/tag_compiler.rs) `test_multiline_component_tag` locks the V3 parse-and-compile contract, including dynamic inputs on separate lines. |
| Apostrophes and double quotes nested inside dynamic component inputs | ✅ Ported | [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `test_dynamic_attr_with_escaped_apostrophe_literal` and `test_dynamic_attr_with_escaped_double_quote_literal` render the values end to end; ordinary closing/self-closing component forms are already covered in Rust structure/compiler tests. |
| A Django `{% lorem %}` or translation call nested inside `{% component %}` | ❌ Drop / ♻️ Replace | Citry has no Django block-tag or translation parser. Use a Python expression/global for computed values; V3 nested HTML templates are covered by `tag_parser_nested_templates.rs`. |

</details>

### `test_tag_parser.py` (121 tests) - triaged `✔`

Confirmed 2026-07-17 in four count-complete groups. V3 replaces the reusable
DTL tag-value parser with HTML attributes whose `c-*` values are Python
expressions; positional inputs, template filters/translations, registered tag
flags, and DTL template-string resolvers deliberately do not port. Every
surviving gap found by the audit now has a focused regression.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `TestResolvers`: variable and expression callbacks (2) | ♻️ Replace | The injectable `compile_tag(variable=..., expr=...)` callbacks do not port. Native variable/expression behavior is covered by [`test_nodes.py`](../../packages/py/citry/tests/test_nodes.py) `TestExprNodeEval`, [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `test_dynamic_attr_is_evaluated`, and `tag_compiler.rs` `test_component_with_expr_attr`. |
| `TestResolvers::test_template_string_resolver` (1) | ♻️ Replace | Arbitrary nested DTL and its resolver callback are absent. V3 makes HTML-valued inputs first-class nested templates: `tag_parser_dynamic_attrs.rs` `test_c_attr_with_template`, `tag_compiler.rs` `test_component_with_template_attr`, and `test_component_node.py` `test_template_attr_becomes_rendered_kwarg`. |
| Translation/filter resolver callbacks (2), `TestTranslation` (6), `TestFilter` (3) | ❌ Drop | Citry has no translation token, filter registry, or DTL `value|filter:arg` grammar. Use ordinary Python methods/calls/conditionals and expose application helpers through template data or globals. `|` in a Citry expression is Python bitwise-or. Divergences #18-#19. **DTL-only subtotal: 14/14 (3 Replace, 11 Drop).** |
| `TestEndTag` (7) | ✅ / ♻️ / ❌ | V3 closing tags, comments, attribute rejection, matching, and invalid `</tag />` are covered by `tag_parser_structure.rs`, `tag_parser_comments.rs`, and `tag_parser_composition.rs`. The djc `end*` name-classification heuristic has no V3 equivalent. |
| `TestForLoopTag` (8) | ♻️ / ❌ | `<c-for>` parsing, multiple targets, Python iterable expressions, malformed clauses, and self-closing loops are covered by `tag_parser_control_flow_for.rs` plus [`test_control_flow.py`](../../packages/py/citry/tests/test_control_flow.py). Django filter syntax on the iterable drops. |
| `TestComments` (3) | ♻️ Replace | Template comments between attributes and Python comments inside multiline dynamic list/dict expressions are covered by `tag_parser_comments.rs`; the collection cases were added by this audit. |
| `TestFlags` (6) | ♻️ / ❌ | Ordinary attrs, duplicate rejection, and boolean inputs survive. Parser-registered flags that disappear before invocation do not; bare V3 attrs become boolean kwargs. Divergence #21. |
| `TestSelfClosing` (3) | ♻️ Replace | `tag_parser_structure.rs` covers compact/self-closing tags with attrs and now rejects a slash before later attributes. **Structural/control subtotal: 27/27 (21 Replace-covered, 6 Drop).** |
| `TestSpread` (11) | ♻️ / ❌ | V3 uses `c-bind` for a top-level mapping spread and ordinary Python `*`/`**` inside expressions. Covered by `tag_parser_spreads.rs`, [`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py) `TestCBindSpread` (including `test_python_dict_unpack_inside_bind`), and safe-eval container tests. DTL filter interactions, ellipsis syntax, and positional list spreads drop. |
| `TestTemplateString` (5) | ❌ / ♻️ | DTL strings recursively rendered through a template/filter resolver do not port. Citry nested HTML-valued attributes are the separate first-class template path covered by `tag_parser_nested_templates.rs` and component-node render tests. |
| `TestParamsOrder` (11) | ♻️ / ❌ | Two mapping-order guarantees map to source-ordered/repeated `c-bind`; the nine cases involving positional or list-spread component inputs drop because Citry is kwargs-only. Divergence #20. **Spread/template/order subtotal: 27/27.** |
| Basic tag/quote cases (6) | ♻️ / ❌ | Keyed attrs and nested quotes map to `tag_parser_kwargs.rs` and the two quote-safe `test_component_node.py` regressions. Positional and stray-quote DTL forms drop. New Rust tests lock unclosed HTML attribute quotes and unclosed Python strings inside `c-*` values. |
| Float/int/string/variable/Python-expression matrix (30) | ♻️ / ❌ | Positional and DTL-filter shells drop; Python literals, variables, calls, lists, and dicts are covered by `tag_parser_dynamic_attrs.rs`, `test_safe_eval.py`, `test_const.py`, and component-node rendering. The audit added `+2.` and `.2e-02` coverage. |
| `TestDict` (11) | ♻️ / ❌ | Python dict syntax replaces the DTL value grammar; generic syntax errors replace DTL-specific colon diagnostics. Safe-eval and `TestCBindSpread` cover literals, nesting, computed keys, trailing commas, and `**` unpack. DTL filters drop. |
| `TestList` (6) | ♻️ / ❌ | Safe-eval and const/container tests cover literals, nesting, trailing commas, and starred unpack. DTL filters and the positional shell drop. **Values/attributes subtotal: 53/53.** |
| Total | ✅ Audited | **121/121 accounted for: no open port or new-test item remains.** |

</details>

### `test_loader.py` (15 tests) - triaged `✔`

djc's directory-and-file discovery layer: where component dirs come from
(Django settings and the app registry) and how found files map to import
names. In citry the dirs come from one place (`Citry(dirs=...)`), so the
settings matrix skips; the file-to-module mapping is real and now locked.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Django settings-driven dirs resolution: `BASE_DIR` fallback and complex forms, `COMPONENTS.dirs`, empty dirs, relative-path rejection of the `(alias, path)` tuple settings form, `app_dirs` on/empty, nested apps (8) | ⏭️ Skip (Django) | citry has no settings module or app registry; the whole input surface is `Citry(dirs=...)`. Divergences #27 (settings) and #64 (`libraries`) already record the shape. |
| Relative dir entries raise (the plain string entry form); a missing dir contributes nothing; str and `Path` entries both work (4) | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestDirsValidation::{test_relative_dir_raises, test_dirs_land_on_settings}`; [`test_autodiscovery.py`](../../packages/py/citry/tests/test_autodiscovery.py) `TestFindComponentModules::test_nonexistent_dir_contributes_nothing`; the mapping function is exercised end-to-end by `TestFindComponentModules` (the pipeline is `Path`-native throughout). A supplementary lock added this session, `test_assets.py` `TestDirsValidation::test_str_dir_entries_convert_to_paths` (0 djc methods), pins that a str entry on the happy path is stored as a `Path`. |
| Only `.py` files become component modules, and nested subpackages map to their full dotted path (1) | ✅ Ported this session | `test_autodiscovery.py` `TestFindComponentModules::{test_ignores_non_python_files, test_maps_nested_subpackages}`: sibling `.html`/`.js`/`.css` files never become import candidates; `comps/sub/widget.py` maps to `pkg.comps.sub.widget`. |
| Enumerating arbitrary-suffix files (`test_get_files__js`); flipping path separators by `os.name` (2) | ❌ Drop | citry has no API for listing non-Python files under its dirs (asset delivery goes through `Dependencies`, divergence #12), and deliberately no OS-name branch in the path-to-module mapping (it works on path parts, so there is nothing to flip; the djc test technique does not transfer). |

</details>

**Accounting: 15/15 methods** (4 already-covered, 1 ported this session as 2
tests, 8 skip-Django, 2 drop). The gap the triage surfaced (djc silently
ignores dot-prefixed files and directories during discovery, while citry's
first scan crashed on them) was fixed the same day: discovery now skips any
path with a dot in its name (beyond the `.py` suffix), locked by
`TestFindComponentModules::{test_skips_dot_prefixed_files_and_dirs,
test_skips_files_and_dirs_with_dots_in_their_names,
test_skips_symlinks_that_resolve_to_dotted_or_missing_paths}` and
`TestAutodiscoverMethod::test_scans_cleanly_past_dot_prefixed_junk`
(regressions landed with the fix, divergence #70).

### `test_node.py` (32) - triaged `✔`

djc's user-facing tag-authoring API (`BaseNode`, `@template_tag`, and
signature-driven input validation). The decision is already recorded in
[`migration_djc.md`](migration_djc.md) (the `node.py` review): **citry's
user-defined tag is the component**. Any non-control `<c-*>` tag resolves
through the registry, render logic is component logic, and input validation
comes from the declared `Kwargs` via parse-time tag rules. There is no API to
bind a tag name to a custom node class (compiled templates run against a fixed
set of built-in nodes). Surfaces divergence #54.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Tag usage forms: paired and self-closing, unclosed-tag error; signature-driven input validation (unknown input, missing required, extra kwargs, special-key rejection); kwargs-only and catch-all acceptance (9, spanning the three near-identical djc classes) | ♻️ Replace | Paired/self-closing/unclosed are grammar-level, locked in `crates/citry_template_parser/tests/tag_parser_structure.rs`. Validation maps onto parse-time tag rules from declared `Kwargs` ([`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py) `TestKwargsValidation`; an undeclared component is unrestricted, `TestBuildTagRules::test_undeclared_component_gets_no_rules`). Positional sub-cases drop (divergence #20). |
| Unregistered tag fails at render, naming the tag with a caret snippet (supplements the tag-usage replace row; 0 djc methods) | ✅ Added alongside the triage | [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeBasic::test_unregistered_tag_raises_not_registered_at_render` (`NotRegistered`, "No component registered as 'totally-unknown-tag'", underline covering the whole tag). |
| The `**kwargs` catch-all guarantee: names special elsewhere (`data-id`, `v-if`) reach `raw_kwargs` verbatim (supplements the same replace row; 0 djc methods) | ✅ Added alongside the triage | `TestComponentNodeAttrs::test_special_character_attr_names_become_kwargs` (extended). Note: a static `data-id="123"` arrives as the string `'123'` (djc parsed numeric literals; divergence #33's literal-value rule), and `@`-keys are consumed by the events layer (divergence #51). |
| All required inputs omitted fails at the parent's first render, one group at a time in declaration order (supplements the validation replace row; 0 djc methods) | ✅ Added alongside the triage | [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py) `TestKwargsValidation::{test_all_required_kwargs_omitted_reports_first_declared_group, test_error_names_next_missing_group_when_first_is_supplied}`. citry never emits a combined all-missing listing (confirmed in the Rust parser: required groups checked in order, immediate return). |
| The `BaseNode` authoring API: `tag` required, `end_tag` optional, `allowed_flags`/`flags`/`active_flags`, flag-name conflicts, the render-signature contract (`self, context, ...`), the live `Context` argument, node instance introspection (`params`/`nodelist`/`node_id`/`contents`) (14) | ❌ Drop | No `BaseNode` exists; a tag is a component, its inputs are `Kwargs` fields, and there is no ambient context (divergences #8, #21, #54). |
| The `@template_tag` decorator family: registration at decoration, `_node` back-reference, decorator-form validation (7) | ❌ Drop | The decorator is the API named in the recorded drop decision; no such symbol exists in either package (divergence #54). |
| CPython-style error-message patterns for positional arity (`takes from X to Y positional arguments`, multiple-missing-positional listings) (2) | ❌ Drop | Positional inputs do not exist (kwargs-only grammar, divergence #20), so the arity messages have no analogue; the missing-required family is the parse-time error ported above. |

**Accounting: 32/32 methods** (9 replace, 23 drop). The 3 tests added this session (plus one extended) are supplementary engine locks attached to the replace rows; they own no djc methods, so they do not enter the partition. On the duplication across the three djc classes: `TestSignatureBasedValidation` repeats 8 of `TestNode`'s 10 methods verbatim, drops two, and adds the node-introspection and error-pattern tests; `TestDecorator` re-runs the contract through the decorator. The drop rows account for each duplicated form once.

</details>

### `test_settings.py` (6)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Valid and invalid `context_behavior` (2) | ❌ Drop | Django-specific setting; citry is always isolated. Divergence #9. |
| String/`Path` `BASE_DIR` implies `BASE_DIR/components` (2) | ♻️ Replaced | Citry has no implicit Django `BASE_DIR` fallback. Callers pass explicit absolute `dirs`; [`test_citry.py`](../../packages/py/citry/tests/test_citry.py) `TestSettingsNormalizedAtDirectConstruction::{test_dirs_coerced_to_paths_and_copied_into_a_tuple,test_dirs_absolute_handling_matches_citry}` and [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestTemplateFile::test_template_file_via_citry_dirs` cover normalization and resolution. Divergence #27. |
| Settings supplied as dict or `ComponentsSettings` instance (2) | ♻️ Replaced | Per-instance `Citry(...)` constructor arguments and direct typed `CitrySettings(...)` replace process-global `COMPONENTS`; [`test_citry.py`](../../packages/py/citry/tests/test_citry.py) `TestCitryInstance::test_settings_stored` and `TestSettingsNormalizedAtDirectConstruction::test_citry_and_direct_settings_normalize_equally`. Divergence #27. |

**Accounting: 6/6 methods. No duplicate `test_settings.py` is needed.**

</details>

### `test_template.py` (4) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| A component's template is cached: repeated retrieval returns the identical object until reset (1) | ✅ Already-covered | [`test_assets.py`](../../packages/py/citry/tests/test_assets.py) `TestTemplateFile::test_loaded_template_is_cached_per_class`; [`test_component.py`](../../packages/py/citry/tests/test_component.py) `TestGeneratorCaching`. |
| The public `cached_template()` helper (string-keyed shared cache) (1) | ♻️ Replace | djc marks the helper TODO_v1; citry has no string-keyed cache: caching is per class, and even identical inline source yields per-class template objects with their own origins, locked this session by `test_assets.py` `TestTemplateFile::test_unrelated_classes_with_identical_inline_source_get_own_copies`. |
| `cached_template()` accepting a custom Template subclass (1) | ❌ Drop | The injected class is a Django `Template` subclass; citry has exactly one internal template type. |
| Django `Template` monkeypatched when rendering a component (1) | ⏭️ Skip (Django) | citry is its own engine and never patches Django's `Template`. |

**Accounting: 4/4 methods** (1 already-covered, 1 replace, 1 drop, 1 skip-Django).

</details>

### `test_tag_formatter.py` (11) - triaged `✔`

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Pluggable `TagFormatter` / `ShorthandComponentFormatter`, custom start/end tags, formatter-invalid-tag error (8 groups, 11 methods) | ❌ Drop | citry's component syntax is the fixed `<c-*>` form with no pluggable formatter and no formatter-error class. Divergence #15. |

</details>

### `test_templatetags_component.py` (19) - triaged `✔`

The `{% component %}` invocation file. Both seeded thin spots resolved: deep
self-recursion existed but only the leaf was asserted, and the Python
parse-error surface was solid while the Rust unclosed-tag test matched only the
substring `error` (strengthened this session). Surfaces divergences #62-#63.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Single component (block and self-closing equivalence); unknown name fails at render; several kwargs with defaults; sibling component calls not interfering (same class side by side, different classes via [`test_deferred_render.py`](../../packages/py/citry/tests/test_deferred_render.py) `test_siblings_finalize_in_source_order`, and the fills matrix below); the syntax-error family (variable and text next to fills, unclosed component tag) (11) | ✅ Already-covered | [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeBasic` / `TestComponentNodeAttrs` / `TestComponentNodeBody`; [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py); text-beside-fills guarded at both layers (Rust `tag_parser_fills.rs` and the Python compile error, divergence #63); the unclosed-tag Rust test now locks the full message (`tag_parser_structure.rs::test_unclosed_tag_errors`, strengthened this session from matching only `error`, incl. the mismatched-tags diagnosis for the nested shape). |
| Sibling fill isolation: three calls of one slotted component each filling a different slot, each showing only its own fill, identical markup with fresh ids on a second render (3) | ✅ Ported this session | `test_slot_fills.py` `TestSiblingFillIsolation::test_sibling_calls_do_not_share_fills` (one test folds djc's only-first, only-second, and isolation methods, incl. the render-twice assertion). |
| Self-recursion emits every level's own markup, not just the leaf (1) | ✅ Ported this session | [`test_deferred_render.py`](../../packages/py/citry/tests/test_deferred_render.py) `TestSelfRecursion::test_guarded_self_recursion_renders_every_level_once` (exact serialized output of 7 levels, parents wrapping children). |
| Variable as the component name (1) | ♻️ Replace | A tag name is always literal; the dynamic path is `<c-component c-is="...">` ([`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py); divergence #62). |
| Aggregate colon-prefix inputs (1) | ❌ Drop | Divergences #1/#34. The leftover-syntax trap is now locked: `attrs:class="pad-8"` arrives as the LITERAL kwarg key (`test_component_node.py::test_colon_named_attr_is_a_literal_kwarg`, a supplementary lock owning no djc method). |
| Positional vs keyword name; single-quoted name literal (2) | ⏭️ Skip (Django) | Artifacts of the `{% component %}` string-argument syntax; in citry the name IS the tag. |

**Accounting: 19/19 methods** (11 already-covered, 4 ported this session via 2 tests, 1 replace, 1 drop, 2 skip-Django). The colon-attr lock and the Rust message strengthening are supplementary, owning no djc methods.

</details>

### `test_templatetags_templating.py` (22) - triaged `✔`

The interaction file: slots under control flow, loops, and deep component
nesting. No new divergence rows: every difference met here is an instance of
existing rows (#6, #8/#9, #11, #18, #29, #30).

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| Nested-slot override matrix (defaults, inner-only, outer-only removes inner, both with inner dropped); no-branch-taken with surplus fills; component nesting without fill, slot inside a fill, deep slot in a fill (8) | ✅ Already-covered | [`test_slot_node.py`](../../packages/py/citry/tests/test_slot_node.py) `TestSlotComposition::{test_three_level_nested_slot_override_matrix, test_passthrough_slot}`, `TestDefaultSlot::test_implicit_body_is_ignored_when_default_slot_branch_is_not_taken` plus the `no-branch` row of `TestFillOrFallback::test_slots_in_conditional_branches` (the exact surplus-named-fills case); [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py) `TestFillsUnderControlFlow::test_loop_variable_captured_per_component`. |
| Same-named fills at two nesting depths stay separate; nested fill bodies resolve the outermost writer's scope (2) | ✅ Ported this session | `test_slot_fills.py` `TestComponentsInsideSlotContent::{test_same_fill_names_at_two_nesting_depths_stay_separate, test_inner_component_slot_left_unfilled_keeps_its_own_default}`. Locked: citry matches djc's isolated mode (the fill printed the page's variable, never the inner card's kwarg), and a fill never falls through to an inner component of the same class. |
| Child-side conditional slots: taken branch resolves fill/default, fill for an untaken branch is a silent no-op, both-filled renders only the active branch (3) | ✅ Ported this session | `test_slot_node.py` `TestFillOrFallback::test_slots_in_conditional_branches` (one parametrized test, 7 rows, folds all four djc methods). |
| An outer-scope variable resolves in the fill body on every child-side loop iteration, alongside per-iteration slot data (1) | ✅ Ported this session | `test_slot_fills.py` `TestScopedSlotData::test_outer_scope_variable_resolves_on_every_slot_iteration`. |
| `fallback=` re-evaluates per loop iteration; `fallback=` chains through a passthrough slot to the forwarding site's own default (2) | ✅ Ported this session | `test_slot_node.py` `TestFallbackAccess::test_fallback_reevaluated_per_loop_iteration` (four distinct per-iteration values), `TestSlotComposition::test_fallback_through_passthrough_slot`. |
| The django-vs-isolated leak family: child loop variables reaching fill bodies, leak chains through nested loops, silent-empty renders on undefined names, `component_vars.is_filled` branching (6) | ♻️ Replace | The ambient-context model is dropped: fills close over the writer's scope only (divergences #8/#9), an undefined name raises a positioned `KeyError` instead of rendering empty (divergence #30), per-iteration data flows through explicit scoped slot data (`c-obj=` on the site, `data=` on the fill), and slot presence is computed in `template_data` (divergence #11). The surviving guarantees are the ported tests above. |

**Accounting: 22/22 methods** (8 already-covered, 8 ported this session via 5 tests, 6 replace).

</details>

### `test_templatetags_provide.py` (35)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `{% provide %}` basics: single-field payload renders, self-closing (no output), multi-field payload attribute access, does-not-leak past the block, keyword-less empty payload, provide-without-inject is harmless (6) | ✅ Already-covered | [`test_provide.py`](../../packages/py/citry/tests/test_provide.py) `TestProvideComponent::{test_basic, test_self_closing_renders_empty, test_payload_attribute_access, test_not_visible_after_closing_tag, test_empty_data_still_injectable, test_no_inject_is_fine}` (exact-HTML assertions; the multi-field aggregate payload is the one asserted by `test_payload_attribute_access`, `payload.text`/`payload.num`). |
| Payload fields via Django `{{ payload.field }}` dot-access (1) | ♻️ Replace | citry has no Django template dot-traversal; the "fields are real dot-accessible attributes" guarantee is `TestProvideComponent::test_payload_attribute_access` (`payload.text == "hi"`). |
| Dynamic name from a variable / from a spread dict (2) | ✅ Already-covered | `TestProvideComponent::test_dynamic_key` (`<c-provide c-key="key_var">`), `test_key_via_bind_spread` (`<c-provide c-bind="props">`, `props={"key": ...}`). |
| Name required / must be non-empty / must be a valid identifier (3) | ✅ Already-covered | `TestProvideComponent::{test_missing_key_raises, test_non_string_key_raises, test_non_identifier_key_raises}`. Error type is `ValueError`, not djc's `TypeError`/`TemplateSyntaxError` (divergence #36). |
| provide does not expose its kwargs into template variables (1) | ✅ Already-covered | `TestProvideComponent::test_data_does_not_enter_template_variables`. |
| Nested provides: same key shadows wholesale, different keys compose (2) | ✅ Already-covered | `TestProvideComponent::{test_nested_same_key_inner_shadows_wholesale, test_nested_different_keys_compose}`. |
| provide across a slot boundary (1) | ✅ Already-covered | `TestProvideAcrossSlots::test_slot_in_provide`. |
| One provide reaching every child a `<c-for>` generates: single loop and nested loops (2) | ✅ Ported this session | `TestProvideComponent::test_provide_wrapping_for_loops_reaches_every_child` (outer provide, one shared value to every child of nested `<c-for>` loops; the single-loop case is the same mechanism). `component_render.py:631-634` rebuilds `context.provides` per render. citry additionally strengthens this with per-iteration tests (`test_provide_inside_for_loop`, `test_provide_inside_nested_for_loop`) proving a provide INSIDE a loop re-scopes to each iteration's own value, guarding against cross-iteration leaks. |
| `inject()`: basic, missing raises (KeyError), default when missing, empty-string key raises, reachable after render, in a fill, in a slot in a fill (7) | ✅ Already-covered | `TestInject::{test_missing_key_raises_keyerror, test_default_returned_when_missing, test_empty_string_key_raises, test_inject_after_render}`; `TestProvideAcrossSlots::{test_inject_in_fill, test_inject_in_slot_in_fill}`; basic via `TestProvideComponent::test_basic`. |
| Reaches descendants through deep and repeated rendering (1) | ♻️ Replace | djc asserted it via its `provide_cache` staying populated while active; citry proves the observable guarantee with `TestDeepNesting::test_provide_survives_deep_component_chains` (depth) plus the loop tests `test_provide_wrapping_for_loops_reaches_every_child` / `test_provide_inside_for_loop` (repeated/wide rendering under one provide). |
| Single-quote literal name; colon-prefix aggregate kwargs; `{% include %}` body; mid-loop error cache cleanup (4) | ❌ Drop | Django-tag mechanics: the key is a `key="..."` HTML attribute (quote style is not provide-specific), no colon-prefix aggregate kwargs (use a `c-<group>` dict attribute or `c-bind`, divergence #34), no `{% include %}` (use a child component; provide still reaches it, divergence #14), and no provide cache to clean. The error-cleanup test's only portable half (an error mid-render propagates without corrupting provide state) is a general guarantee: citry's provide path has no try/finally or shared state to corrupt (`component_render.py:631-634`), and error propagation is covered by [`test_exception.py`](../../packages/py/citry/tests/test_exception.py) / [`test_error_trace.py`](../../packages/py/citry/tests/test_error_trace.py). |
| inject-outside-render "not persisted"; `TestProvideCache` provide-outside/inside-a-component (with and without mid-render errors) (5) | ♻️ Replace | Citry has no global provide cache or bare-template provide. The portable lifetime guarantee belongs to [`caching.md`](caching.md): a detached cache artifact retains no provide payload, context, component instance, or class. Provide remains a `Component` method or the `<c-provide>` component. |

**Accounting: 35/35 methods** (22 already-covered, 7 replace, 4 drop, 2 ported this session). citry additionally tests provide/inject behavior djc's file never had: the did-you-mean inject hint, transparent no-marker rendering, Python-channel provide inheritance, 300-level deep nesting, builtin name reservation, `validate_provide_key` / `make_provided`, payload immutability, and own-provide-not-visible-to-own-inject.

</details>

### `test_templatetags_slot_fill.py` (67)

<details>
<summary>Test groups</summary>

| Upstream class / behavior | Status | Notes |
|---|---|---|
| `TestComponentSlot`: core named/default/empty/dynamic/required/duplicate behavior (12) | ✅ Ported / ♻️ Replaced | End-to-end coverage is split across [`test_slot_node.py`](../../packages/py/citry/tests/test_slot_node.py), [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py), and Rust `tag_parser_fills.rs`. The batch added an explicit-empty-fill regression. Arbitrary named `default` declarations map to Citry's literal `default` slot; divergence #29. |
| `TestComponentSlot`: Django context modes (2) | ♻️ Replaced / ❌ Drop | Fill bodies close over the writer's explicit template scope; there is no ambient Django Context or `context_behavior`. Divergences #8 and #9. |
| `TestComponentSlot`: `{% include %}` interaction (2) | ⏭️ Skip (Django) | Replace the included partial with a component composed through slots; divergence #14. |
| `TestComponentSlotDefault` (10) | ✅ Ported / ♻️ Replaced / ❌ Drop | The batch locks empty/implicit fills, an unused implicit body, an untaken default-slot branch, comments, nested components, mixed-content rejection, and required behavior. DJC's ability to mark arbitrary named slots as default has no direct Citry flag; divergence #29. |
| `TestPassthroughSlots` (6) | ✅ Ported / ♻️ Replaced | `TestFillsUnderControlFlow` plus `TestSlotComposition::test_dynamic_passthrough_ignores_unknown_fills` cover conditional/loop collection, dynamic names, fallback, passthrough, and ignored surplus fills using Python expressions instead of DTL `{% with %}`. |
| `TestNestedSlots` (5) | ✅ Ported | `TestSlotComposition::test_three_level_nested_slot_override_matrix` locks the unfilled, outer, middle, inner, and all-filled precedence matrix. |
| Missing Django template variable regression (1) | ♻️ Replaced | Citry raises `KeyError` pointing at the line and column, instead of rendering an absent expression as empty. Divergence #30. |
| `TestSlotFallback` (5) | ✅ Ported / ❌ Drop | Fallback access, repetition, control flow, and nesting are covered; the legacy `default=` alias is intentionally absent in favor of `fallback=`. Divergence #32. |
| `TestScopedSlot` (13) | ✅ Ported / ♻️ Replaced | `TestScopedSlotData`, `TestFallbackAccess`, and repeated slot-site tests cover static/dynamic/spread data, fallback bindings, no-fill paths, parent variables, repetition, and nested fills. DJC filters/DTL variable syntax map to Python expressions. |
| `TestDuplicateSlot` (4) | ✅ Ported | Repeated slot sites may share a name and retain distinct fallbacks; nested fallback behavior is covered in Python. |
| `TestSlotFillTemplateSyntaxError` (3) | ✅ Ported | Rust `tag_parser_fills.rs` covers fill placement and static/dynamic duplicate identities; Python `FillSink` retains the runtime duplicate guard. |
| `TestSlotBehavior`: Django/isolated context modes (2) | ♻️ Replaced / ❌ Drop | Citry has one lexical fill-scope rule and explicit props/provides; divergences #8 and #9. |
| `TestSlotInput` (2) | ✅ Ported | `TestPythonSlotsChannel` and fill metadata tests assert that received fills are callable normalized `Slot` instances. |

**Accounting: 67/67 methods.**

</details>

---

## Test review by file (utilities)

Same status legend as above.

### `test_util_weakref.py` (3), `test_utils.py` (1) - triaged `✔`

djc-internal utilities (`util.weakref`, `util.misc`). None of the four
behaviors is user-observable on its own, so this section adds no divergence
rows; the user-visible ends of these stories are already catalogued (#61 for
collectability of dropped classes, #15 for the tag formatter's removal
taking quoted component names with it).

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `cached_ref` returns the identical reference object on repeated calls (1) | ♻️ Replace | The shared-reference cache backed djc's global weak rosters, which citry does not have: each site owns its weak structure (the class-id map, per-registry owner refs, the weak file index). The reason the cache existed, weak bookkeeping must not keep classes alive, is locked at citry's real surfaces: `test_assets.py` `test_unregistered_class_is_pruned_from_the_index` and `test_const.py` `test_collected_component_removes_all_weakly_owned_entries`. The reference-identity contract itself has no citry API to assert against. |
| Repeated `cached_ref` calls do not stack finalizers (1) | ✅ Ported this session | The same leak class exists at citry's analogous site: every asset resolution re-registers the class for its file, and the index dedupes (`citry.py:841`). The guard was only incidentally covered before (three reset-scoping and invalidate tests fail on duplicate entries when it is removed, none of them about the dedup itself). Now locked directly: `test_assets.py` `TestFileIndexAndResets::test_reload_cycles_do_not_stack_index_entries` (5 load/reset cycles, two classes sharing one file, each listed exactly once by `get_components_for_file` and `invalidate_file`). |
| The weak-roster entry disappears when its referent is collected (1) | ✅ Already-covered | Same guarantee at citry's surfaces: `test_assets.py` `test_unregistered_class_is_pruned_from_the_index` and `test_render_after_unregister_does_not_retain_the_class`, `test_const.py` `test_collected_component_removes_all_weakly_owned_entries`. |
| `is_str_wrapped_in_quotes` (10-case boolean matrix) (1) | ❌ Drop | The helper's sole caller was the tag formatter's quoted-name validation, and that surface is gone (divergence #15). Quoting in templates is the Rust grammar's job: an unterminated quote is a parse error (`tag_parser_kwargs.rs` `test_unterminated_quoted_attribute_values_error`), while unquoted attribute values are legal and locked as parsing successfully (`test_kwarg_unquoted_value`, `test_kwarg_unquoted_value_stops_at_whitespace`). Nothing replaces the boolean contract because the feature it validated does not exist. |

</details>

**Accounting: 4/4 methods** (`test_util_weakref.py` 3 = 1 replace + 1
ported this session + 1 already-covered; `test_utils.py` 1 = 1 drop).

---

## Test review by file (extensions and commands)

Same status legend as above.

### `test_component_highlight.py` (7 tests)

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| `test_component_highlight_fn`: helper keeps the component label and original HTML and uses the component palette (1) | ♻️ Replace | Citry exposes highlighting through `Debug`, not a standalone HTML-rewriting helper. `TestComponentHighlighting::test_nested_components_are_highlighted_and_authored_roots_keep_markers` asserts the public output keeps the authored roots, component labels, blue border, and `#2f14bb` label color. |
| `test_slot_highlight_fn`: helper keeps the slot label and original HTML and uses the slot palette (1) | ♻️ Replace | `TestSlotHighlighting::test_passed_and_fallback_slots_use_receiver_label` asserts passed and fallback content, the receiver/slot label, red border, and `#bb1414` label color through the public extension. |
| `test_component_highlight_extension`: engine default highlights nested components across repeated component instances (1) | ✅ Ported | `TestComponentHighlighting::{test_nested_components_are_highlighted_and_authored_roots_keep_markers,test_sibling_instances_and_repeated_slots_have_independent_boundaries}` cover nesting, repeated sibling instances, labels, original output, and independent complete boundaries. |
| `test_component_highlight_extension__legacy`: core `debug_highlight_components` setting (1) | ❌ Drop | Citry keeps extension settings under `extensions_defaults["debug"]`; it has no legacy core setting. This is the Debug-specific instance of divergence #58's extension-owned configuration contract. |
| `test_slot_highlight_extension`: engine default highlights repeated slots across repeated component instances (1) | ✅ Ported | `TestSlotHighlighting::test_repeated_slot_sites_get_distinct_complete_boundaries` covers repeated sites, and `TestComponentHighlighting::test_sibling_instances_and_repeated_slots_have_independent_boundaries` repeats those sites across two component instances. |
| `test_slot_highlight_extension__legacy`: core `debug_highlight_slots` setting (1) | ❌ Drop | Citry keeps extension settings under `extensions_defaults["debug"]`; it has no legacy core setting. |
| `test_highlight_on_component_class`: component-owned config enables both boundary kinds (1) | ✅ Ported | `TestConfiguration::test_component_config_can_enable_factory_default` enables both fields in the component's nested `Debug` class and asserts both wrapper kinds. Override precedence is separately locked by `test_component_config_overrides_engine_default`. |

</details>

**Accounting: 7/7 methods** (3 ported, 2 replaced through the public extension,
2 dropped legacy settings). Citry-specific document, transparent, serializer,
dependency, ownership, cross-engine, browser, and lifetime contracts are
covered in `test_ext_debug.py` and `e2e/test_ext_debug_e2e.py`; see
[`extensions_debug.md`](extensions_debug.md).

### `test_component_view.py` (14 tests) - triaged `✔`

<details open>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| A component invoked inside a Django template and served by a host view (1) | ♻️ Replace / ⏭️ Skip (Django) | The portable composition half is covered by [`test_component_node.py`](../../packages/py/citry/tests/test_component_node.py) `TestComponentNodeBasic::test_renders_child_component` and `TestComponentNodeAttrs::test_static_attr_becomes_kwarg`. Django `Template`, `Context`, `HttpResponse`, and URLconf mechanics stay in the wrapper. |
| Nested `View.get` and `View.post` dispatch (2) | ♻️ Replace | [`test_events_view_events.py`](../../packages/py/citry/tests/test_events_view_events.py) locks verb stamping, GET query binding, and form POST dispatch through `class Events(ViewEvents)`. The real-browser native and runtime form paths are covered by [`e2e/test_events_form_submission_port_e2e.py`](../../packages/py/citry/tests/e2e/test_events_form_submission_port_e2e.py). |
| Direct `Component.get` / `Component.post` shortcuts (2) | ❌ Drop | Event handlers live only inside the nested `Events` class. A method left directly on the component is not exposed; divergence #88. |
| `as_view()` creates an HTTP-bound component instance for the handler (1) | ❌ Drop / ♻️ Replace | Citry creates a per-call Events config, not a live component instance. The handler returns a fresh component element and can inspect `self.component_class`, but cannot read an HTTP-bound component through `self.component`; divergence #88. |
| Props, slot fallback/fill, and unsafe prop/slot escaping in served HTML (4) | ✅ Ported this session | `test_events_view_events.py::TestVerbRoute::test_classic_post_can_return_component_html_with_props_slots_and_escaping` drives the instance-less compatibility route through a real ASGI app. It returns a fresh component with an explicit prop and Python slot, asserts the unfilled fallback, and proves both unsafe strings escape. `test_events_django.py::TestDjangoParity::test_view_events_compat_post_can_return_an_unaddressed_component` locks the sync-host path. This exposed and fixed the targetless compatibility-render defect while the ordinary wire invariant remains locked by `test_events_actions.py::test_a_render_without_instance_or_target_is_refused`. |
| Component URL building, encoding, and custom route arguments (1) | ♻️ Replace / ❌ Drop | [`test_events_routes.py`](../../packages/py/citry/tests/test_events_routes.py) `TestEventUrls` covers module-level and component-bound builders, including the ported exact unsafe query-key/value/fragment case; [`test_misc.py`](../../packages/py/citry/tests/test_misc.py) covers merging, overrides, boolean flags, and omitted `False`/`None`. Citry uses fixed named-event routes and does not reverse per-component custom paths with `args` / `kwargs`; divergence #89. |
| Explicit, implicit, and disabled public component URLs (3) | ♻️ Replace / ❌ Drop | Placement is the allowlist: every public method in `Events` is exposed, and omission (or `Events = None`) removes it. `test_events.py::TestHandlerEnumeration::test_public_defs_are_handlers_in_definition_order`, `test_events_view_events.py::test_method_without_a_handler_answers_unknown_event`, and `test_events_routes.py::test_unknown_event_fails_at_build_time` lock the replacement. There is no `public` flag, per-class URL registration, or dedicated builder for the method-only compatibility route; divergence #89. |

</details>

**Accounting: 14/14 methods** (4 ported, 7 replaced, 3 dropped; the Django
host mechanics inside one replacement are explicitly skipped). The
definition-before-`django.setup()` fixture is non-method setup for Django's
per-class URL queue; Citry mounts fixed routes and resolves class ids at
request time, so it owns no additional case.

### `test_command_components.py` (1), `test_command_create.py` (7), `test_command_ext.py` (11), `test_command_list.py` (4) - triaged `✔`

djc's management-command suite (`python manage.py components ...`). citry's
counterpart is the standalone `citry` console script (`list`, `create`,
`watch`, `ext list`, `ext run`, `--version`), with its own tests in
[`test_cli.py`](../../packages/py/citry/tests/test_cli.py) and
[`test_command.py`](../../packages/py/citry/tests/test_command.py). The CLI
surface is deliberately minimal. The alias, scaffold-shape, and `manage.py`
drops are recorded decisions in
[`extensions_commands.md`](extensions_commands.md); the listing-format flag
drops rest on the flags' evident absence from that minimal surface, with no
flag-level decision recorded. Divergences #81-#84.

<details>
<summary>Test groups</summary>

| Test group / behavior | Status | Notes |
|---|---|---|
| The umbrella command's help lists every offered command (`test_command_components.py`, 1) | ✅ Ported this session | `test_cli.py` `TestHelpListings::{test_bare_citry_lists_subcommands_and_version, test_help_flag_prints_the_same_root_listing}`. The djc assertion's Django-global-options half is `manage.py` plumbing with no citry counterpart, and `upgrade` is deliberately not carried over (divergence #81). |
| `create`: default scaffold file names; `--force` overwrite (2) | ♻️ Replace | citry scaffolds one Python file with an inline template instead of a directory of assets (`test_cli.py` `test_writes_component_file`), and never overwrites: no `--force`, refusal locked by `test_refuses_to_overwrite`. Divergence #82. |
| `create`: existing target errors without `--force` (1) | ✅ Already-covered | `test_cli.py` `test_refuses_to_overwrite` (SystemExit, existing file untouched). |
| `create`: reports where it wrote the component (1) | ✅ Ported this session | `TestCreateComponent::test_reports_created_file_path` (the exact `Created <path>` message; citry always prints it, djc gated it behind `--verbose`). |
| `create`: `--js`/`--css`/`--template` renames, `--dry-run`, the `startcomponent` alias (3) | ❌ Drop | The renames are meaningless for the single-file scaffold, previewing is replaced by never-overwrite (there is nothing destructive to preview), and the `startcomponent` alias is not carried over (its job is done by `citry create`; divergences #81, #82). The scaffold shape and the alias decisions are recorded in `extensions_commands.md`; no compatibility aliases per the standing decision. |
| `ext`: the group's help lists `list`/`run`; `ext run` offers only extensions that declare commands; an unknown command under a known extension is a usage error (3) | ✅ Ported this session | `TestHelpListings::{test_ext_lists_its_subcommands, test_ext_run_lists_only_extensions_with_commands}`, `TestCommandTree::test_ext_run_unknown_command_under_known_extension_raises` (invalid-choice on stderr, exit 2; the unknown-extension sibling was already locked). |
| `ext list`: built-in and user extensions listed, user ones after built-ins (2) | ✅ Already-covered | `test_cli.py` `test_ext_list_lists_extensions` (built-in `dependencies` plus user `greeter` in one output). The listing iterates the extension manager's list directly, so the built-ins-first order comes from manager construction (`extension.py:651`), locked by the order-sensitive asserts at `test_extension.py:67` and `:827`. `test_command.py` locks the table's trailing-whitespace and header-less modes; the header/separator shape itself is unasserted. djc's exact built-in roster is engine content, not command behavior. |
| `ext run`: bare extension prints its command list (two byte-identical djc methods); a command's `handle` runs with parsed options as kwargs (3) | ✅ Already-covered | `test_cli.py` `test_ext_run_extension_without_command_lists_its_commands`, `test_ext_run_dispatches_to_extension_command`. citry's `handle` receives only declared options, nothing to pop (divergence #84). |
| `ext list` / `list` formatting flags: `--all`, `--columns`, `--simple` (6: 3 per file) | ❌ Drop | The output is a fixed table in citry and the flags do not exist (passing one is a usage error). Header-less rendering exists internally but is not surfaced. This is the one drop set in the batch resting on evident intent rather than a recorded decision: `extensions_commands.md` never mentions listing columns or formatting flags. Divergence #83. |
| `list`: default columns (1) | ♻️ Replace | citry prints one row per component with all its registered names, the class name, and the defining file (the path column and the alias merge added on maintainer request right after triage) instead of djc's `full_name` dotted path + path pair; running `list` triggers autodiscovery first. Locked in `test_cli.py` `TestListComponents`. Divergence #83. |

</details>

**Accounting: 23/23 methods** across the four files (6 already-covered, 3
replace, 9 drop, 5 ported this session as 6 tests). Per file:
`components` 1 = 1 ported; `create` 7 = 1 covered + 2 replace + 1 ported +
3 drop; `ext` 11 = 5 covered + 3 ported + 3 drop; `list` 4 = 1 replace +
3 drop.

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
- Dependencies subsystem: `test_deps_emission.py`, `test_deps_fragments.py`, `test_deps_types.py`, `test_deps_urls.py`, `test_deps_vars.py`, `test_js_css_data.py`, `test_deps.py`
- Events: `test_events.py`, `test_events_actions.py`, `test_events_bindings.py`, `test_events_dispatch.py`, `test_events_django.py`, `test_events_emission.py`, `test_events_openapi.py`, `test_events_protocol_package.py`, `test_events_routes.py`, `test_events_schemas.py`, `test_events_tokens.py`, `test_events_typing.py`, `test_events_view_events.py`, `e2e/test_events_applier_e2e.py`, `e2e/test_events_client_e2e.py`
- Attributes and compiler metadata: `test_attrs_template.py`, `test_meta_attrs.py`
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
| Source-language attributes (`template_lang` / `js_lang` / `css_lang`) and the pluggable compiler registry | none | [`source_languages.md`](source_languages.md) | ❓ Designed, not built. Add tests when the feature lands. |
| Extension roadmap plugins (Scoped CSS, ColorLogger) | partial | [`extensions_roadmap.md`](extensions_roadmap.md) | ❓ Add tests as each extension is built. Cache is covered by `test_ext_cache*.py` and `e2e/test_cache_replay_e2e.py`; Debug is covered by `test_ext_debug.py` and `e2e/test_ext_debug_e2e.py`. |

Well-covered citry-native features (no action, listed so the audit is
complete): `Const()` precompute ([`test_const.py`](../../packages/py/citry/tests/test_const.py)),
template globals ([`test_template_globals.py`](../../packages/py/citry/tests/test_template_globals.py)),
the literal `c-` attribute escape ([`tag_compiler.rs`](../../crates/citry_template_parser/tests/tag_compiler.rs),
[`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py)),
the `sandbox_expressions` equivalence and access-control split
([`test_sandbox_setting.py`](../../packages/py/citry/tests/test_sandbox_setting.py)),
`<c-element>` dynamic element ([`test_component_dynamic.py`](../../packages/py/citry/tests/test_component_dynamic.py)),
structured element attributes ([`test_attrs_template.py`](../../packages/py/citry/tests/test_attrs_template.py)),
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

1. **Keep the restored coverage gate green** (the tooling section above). Its
   ratcheting floor makes migration coverage visible.
2. **Clear the `wrapper` / Drop files.** The ⏭️ Skip and ❌ Drop files
   (`test_context`, `test_finders`, `test_signals`,
   `test_integration_template_partials`, `test_templatetags_extends`,
   `test_tag_formatter`) carry no porting work; confirm the verdict, cite the
   reason, mark `✔`. This retires roughly a fifth of the list quickly. (The
   then-pending extension files, `test_component_cache`,
   `test_component_highlight`, and `test_django_cache_tag`, were not cleared in
   that historical batch; their applicable Debug and Cache replacements have
   since landed.)
3. **Core files confirmed.** `test_html_parser`, `test_template_parser`,
   `test_templatetags`, and the 121-case `test_tag_parser` are complete. Their
   surviving gaps landed as focused Rust/Python tests; Django-only parser
   mechanics are recorded as explicit drops and divergences.
4. **Verify the strong-overlap files.** Mostly ✅; the work is confirming each
   claimed citry test actually asserts the behavior and citing it. Any
   uncovered case becomes a 🚧 Port.
5. **Port surviving behavior from mixed-disposition files.** For each file,
   translate the guarantees Citry keeps from `@djc_test` + `{% ... %}` into a
   fresh `Citry()` + `<c-*>`, while recording Django-only mechanics as Drop or
   Skip. Land each surviving guarantee in the named Citry test file.
6. **Write the remaining net-new tests** as Citry-native features land. The
   first target, the `c-c-` escape, is complete; source-language attributes
   and roadmap extensions remain feature-gated.
7. **Retire `_djc_tests/` - complete.** Every dashboard row is `✔`; maintainer
   approval was given on 2026-07-23, so the snapshot, collection exclusion, and
   vendor-script test copy were removed.

**Record divergences as you go.** Whenever triaging a file proves a
user-observable difference between citry and django-components (a `♻️ Replace`,
a deliberate behavior change, a dropped API a user relied on), add a numbered
row to [Divergences for djc users](#divergences-for-djc-users-migration-guide-seed).
That catalogue is a first-class deliverable of this migration, not an
afterthought: by the end it is the djc-to-citry upgrade checklist.

**Deletion approval.** No file is removed without maintainer sign-off. The
maintainer explicitly approved retiring `_djc_tests/` after the Cache ports and
coverage hardening landed; no native Citry tests were deleted as part of that
retirement.

Batches 2-5 fan out well to parallel sub-agents (one file per agent producing
its section rows), with a verification pass that rejects any ✅ verdict whose
cited citry test does not actually assert the behavior.

---

## Implementation log

Chronological record of triage and porting work. Newest entries at the bottom.

<details>
<summary><b> Log entries: </b></summary>

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

### 2026-07-02 - reclassified pending-extension files

- On maintainer feedback: `test_component_view.py`, `test_component_highlight.py`,
  `test_django_cache_tag.py`, and `test_component_cache.py` were classified as
  `🚧 pending`, not Skip/Drop. Debug/highlight was subsequently ported on
  2026-07-21; the applicable Cache and `<c-cache>` replacements subsequently
  landed under the contract in [`caching.md`](caching.md). Added a "pending"
  convention to the legend.
- Recorded that the coverage gate runs on every PR via the `Check` workflow,
  and that no file is deleted without maintainer sign-off.

### 2026-07-02 - first triaged file: `test_attributes.py`

- Sample run to validate the porting loop. A workflow enumerated all 38 djc
  behaviors and adversarially confirmed each against citry's real assertions
  (opening `test_attrs.py`, `test_attrs_template.py`, and `citry/attrs.py`).
- Result: 22 already-covered (quoted citations), 9 replaced by citry's
  element-level `c-bind`/`c-class`/`c-style` tests, 7 dropped as
  `{% html_attrs %}`-tag internals. No gap, so no new test was written.
- Recorded one deliberate divergence: overlapping plain attribute keys are
  last-one-wins in citry, not space-joined as in django-components. Row marked
  `✔`. Added the first entries to "Divergences for djc users" below.

### 2026-07-02 - second triaged file: `test_dependencies.py`

- First file with real porting work. Adversarial cross-map verified all 28 djc
  behaviors against citry source: 10+ already-covered (cited), several
  `♻️ Replace` (citry's `deps_strategy` x `deps_position` model), 3 `❌ Drop`
  (standalone `render_dependencies()`, `_RENDERED` placeholder contract, legacy
  `type=`), 1 `⏭️ Skip` (`render_to_response`).
- Wrote 3 new tests in [`test_deps_emission.py`](../../packages/py/citry/tests/test_deps_emission.py):
  the component inline-JS/CSS end-tag guard (2) and the `on_dependencies`-returns-`None`
  no-op (1). Suite 1285 -> 1288 passing; coverage 92.72% -> 92.76%.
- Corrected an agent claim by reading source and running a probe: citry's
  end-tag guard matches the substring `</script` (so `</script  >` is caught),
  and raises `ValueError`, not djc's `RuntimeError`. Cataloged divergences
  #4-#6 (strategy model, error type, on-demand client runtime).
- Left 3 source-verified ports queued (`🚧` in the section): `on_dependencies`
  adding an unwrapped extra, fragment no-HTML-fixup, and nested multi-component
  dedup/order. Row marked `✔` (analysis complete) with `🚧` ports outstanding.

### 2026-07-02 - closed `test_dependencies.py` ports

- Resolved the 3 queued ports. Probed each against real citry behavior first:
  - `on_dependencies` adding an unwrapped `kind='extra'` entry: real, ported as
    `TestOnDependenciesHooks::test_component_classmethod_can_add_an_extra_entry`.
  - Nested multi-component dedup + first-seen order: real, ported as one test,
    `TestDocumentEmission::test_nested_components_dedupe_and_keep_first_seen_order`.
  - Fragment "no HTML fixup on an unclosed tag": **not portable**. The V3 parser
    rejects a malformed component template at parse time, so the djc premise
    cannot exist. Reclassified `♻️ Replace`; added divergence #7 (component
    templates must be well-formed).
- Suite 1288 -> 1290 passing; coverage 92.76%. `test_dependencies.py` now has
  no outstanding `🚧`.
- At that stage, excluded the temporary `_djc_tests/` snapshot from ruff so
  re-vendoring could not reintroduce lint failures. The snapshot and exclusion
  were later retired at migration closeout.

### 2026-07-02 - confirmation batch: 6 wrapper/Drop files

- Adversarially confirmed the six no-porting files (`test_context`,
  `test_finders`, `test_signals`, `test_integration_template_partials`,
  `test_templatetags_extends`, `test_tag_formatter`): one agent per file, each
  told to hunt for a hidden portable behavior before accepting Skip/Drop.
- Every "portable-looking" behavior resolved to an existing citry test (child
  variable isolation, parent-scope slot rendering, provide/inject, nested-deps
  default, asset routes), so no new tests were needed. All six marked `✔`.
- The batch's real yield was the migration guide: added divergences #8-#16
  (ambient context, `context_behavior`/`only`, request/CSRF, `is_filled`,
  static asset delivery, render-observation signal, template inheritance,
  component syntax/`TagFormatter`, template-partials). No code changed; docs
  only.

### 2026-07-02 - fragment-dedup bug surfaced (from divergence #6)

- Tracing the `test_dependencies.py` divergence "runtime only emitted when
  `$component` is used" revealed a real correctness gap, not an optimization.
- `_resolve_records` computes `mark_css_urls`/`mark_js_urls` (the cache URLs of
  a mounted page's inlined component assets) precisely so a later fragment can
  dedup against them (comment at `emission.py:177-179`). But
  `emit_dependencies` ships the `markLoaded` manifest only under
  `if with_client_js and calls:` (`emission.py:141`), and the client runtime
  seeds its loaded-set only from `markLoaded` (`client/citry.js:167-172`), never
  from the DOM.
- Consequence: a **mounted** document with component CSS/CSS-vars but **no
  `$component`** ships no runtime and no `markLoaded`. A fragment inserted
  later that reuses one of those components re-fetches its CSS, duplicating it
  in the DOM (the document's inline `<style>` plus the fragment's fetched
  `<link>`).
- Proposed fix: gate on `calls or mark_js_urls or mark_css_urls` (emit the
  runtime + `markLoaded` whenever the mounted page has assets a fragment must
  dedup against), staying lean on unmounted or component-less pages. This is a
  change to the dependency-emission contract, so it needs a plan and updates to
  any test that asserted the old "no runtime without `$component`" output,
  plus a regression test (emission-level: the mounted no-`$component`
  document must emit a `markLoaded` listing its component cache URLs). Awaiting
  maintainer go-ahead.

### 2026-07-02 - fragment-dedup bug fixed

- Approved and shipped. `emit_dependencies` now gates on
  `calls or resolved.mark_js_urls or resolved.mark_css_urls` (`emission.py:145`),
  so a mounted page with component assets emits the runtime + `markLoaded` even
  without `$component`. No existing test asserted the old output, so none
  needed changing.
- Added two regression tests in [`test_deps_fragments.py`](../../packages/py/citry/tests/test_deps_fragments.py)
  `TestMountedDocumentFlow`: `test_content_only_mounted_page_still_marks_its_assets`
  (the fix) and `test_component_less_mounted_page_stays_lean` (the leanness
  guard). Suite 1290 -> 1292; coverage 92.76%.
- Swept the design docs for the old condition and corrected it in
  [`dependencies.md`](dependencies.md) (the section 15 decision and the section
  16 phasing note) and [`migration_djc.md`](migration_djc.md) (the manifest
  bullet). Divergence #6 updated to the corrected behavior.
- Added two browser-level regressions in [`e2e/test_fragment_e2e.py`](../../packages/py/citry/tests/e2e/test_fragment_e2e.py):
  `test_content_page_dedupes_a_reused_components_css` and its JS counterpart
  `test_content_page_dedupes_a_reused_components_js`. Each renders a content-only
  mounted page, then inserts a fragment reusing the component, and asserts (1)
  the runtime registered the asset's cache URL as loaded from `markLoaded` and
  (2) no duplicate `<link>` / `<script src>` is added; the JS test also asserts
  the component's JS did not run a second time. Verified in a live chromium via
  the e2e harness; runs in the e2e CI lane (chromium PR + weekly cross-browser).
  Without the fix, no runtime ships and signal (1) never becomes true, so the
  tests fail.

### 2026-07-17 - core parser and Citry-native regression batch

- Reconciled the user-organized test names (`test_attrs_template.py`,
  `test_deps.py`, and `test_events_*`) and added the Events suite to the
  Citry-only inventory. No stale pre-rename reference remains outside the
  deliberately untouched upstream snapshot.
- Closed `test_html_parser.py` seven-for-seven against the exact
  `citry_core/tests/test_html_transformer.py` cases and corrected ownership
  from `citry_template_parser` to `citry_html_transform`. Closed the four
  benchmark rows after confirming their benchmarked scenario code is
  preserved and only their pytest harness is adapted.
- Triaged `test_template_parser.py` and `test_templatetags.py`. Added Rust
  regressions for unterminated expressions/comments, literal DTL delimiters,
  and multiline component tags, plus Python component-render regressions for
  nested apostrophe/double-quote expressions. Divergence #17 records V3's
  strict unterminated-delimiter policy.
- Triaged all 121 `test_tag_parser.py` cases in four count-complete groups.
  Added focused regressions for misplaced self-closing slashes, Python comments
  inside dynamic collections, malformed static/dynamic quotes, Python dict
  unpack in `c-bind`, additional float spellings, trailing-comma containers,
  computed dict keys, and starred list unpack. Divergences #18-#21 record the
  filter, translation, positional-input, and registered-flag drops.
- Closed the highest-priority Citry-native gap. Rust compilation now locks
  authored `c-c-foo`, `c-c-c-foo`, `c-c-bind`, and `c-:class` keys; Python
  rendering locks exact-one-prefix removal, the Vue/Alpine colon bridge, and
  literal keys supplied through `c-bind`.
- Reconciled claims made stale by later work: the coverage gate is active,
  sandbox equivalence/access-control coverage is complete, Alpine compatibility
  has Events browser coverage, `ViewEvents` has landed, and djc Defaults and
  the two legacy utility helpers are superseded rather than pending ports.
- That batch brought the dashboard to 16 of 54 files fully triaged,
  representing about 310 of 955 approximate upstream cases.
- This batch changes tests and docs only; no production behavior changed.

### 2026-07-17 - component CSS unit and browser batch

- Triaged all nine `test_component_css.py` cases. Added direct coverage for
  CSS-function classification, multi-value scoped stylesheets, empty/`None`
  data, and distinct per-instance hashes/markers/stylesheets. Numeric, color,
  spaced-string, and function serialization remain covered by the shared
  serializer plus the new integration case.
- Triaged all five `test_component_css_e2e.py` cases. A document test now
  proves static CSS without variables and three same-class instances with
  distinct computed values and hashes. A live-fragment test fetches and
  applies both static-only and variables-backed component CSS, asserting
  computed styles, marker placement, and the fetched stylesheet URLs.
- Verified the affected browser files in Chromium: seven tests passed. That
  batch brought the dashboard to 18 of 54 files and about 324 of 955 cases
  fully triaged.
- This batch changes tests and docs only; no production behavior changed.

### 2026-07-17 - component JS unit and browser batch

- Triaged all fifteen `test_component_js.py` cases. Strengthened the JS-data
  tests to bind sibling calls to decoded payloads, round-trip nested data, and
  lock empty/`None` results as null-hash calls. Added the five missing Script
  `type` cases: empty, `application/javascript`, `importmap`,
  `speculationrules`, and `application/json`.
- Triaged all five `test_component_js_e2e.py` cases. New Chromium document
  regressions prove immediate/no-data callback behavior and meaningful IIFE
  isolation with top-level `var`, plus three simultaneous instances receiving
  and using their own complex payloads. Existing runtime/fragment tests cover
  both fragment cases, so no duplicate fragment test was added.
- Added divergence #22 for the `$component` callback shape: djc passes JS
  data directly, while Citry passes one `{id, els, data}` context object.
- That batch brought the dashboard to 20 of 54 files and about 344 of 955 cases fully
  triaged. This batch changes tests and docs only; no production behavior
  changed.

### 2026-07-17 - dependency rendering unit and browser batch

- Triaged all eighteen `test_dependency_rendering.py` cases. Added regressions
  proving unused registered classes emit nothing, nested URL dependencies emit
  once in first-seen bucket order, and a lone `<c-js />` or `<c-css />` does
  not suppress the other asset category.
- Triaged all fifteen `test_dependency_rendering_e2e.py` cases. New Chromium
  coverage combines Component and Dependencies assets across multiple
  instances, locks all three dependency/component probe orderings, proves CSS
  works with browser JavaScript disabled, and exercises local Dependencies JS
  and CSS through the live fragment path.
- Alpine `x-html` and HTMX are mapped to Citry's framework-independent DOM
  insertion contract instead of adding CDN-dependent tests. The four external
  Alpine placement cases map to Citry Events' owned Alpine lifecycle.
- Added divergences #23-#25 for placement tags versus category filters,
  HTML-compatible component names, and the Events extension's Alpine
  ownership. The dashboard is now 22 of 54 files and about 377 of 955 cases
  fully triaged. This batch changes tests and docs only; no production
  behavior changed.

### 2026-07-17 - registry and settings batch

- Triaged all eighteen `test_registry.py` methods. Existing Citry tests covered
  the ordinary name registry, while the audit added exact regressions for
  unrelated-component unregister, stable class-ID collision/replacement,
  alias-sensitive reverse-index lifetime, protected V3 structural names, and
  real-parse population of per-instance tag-rule caches.
- Fixed the two registry defects exposed by those tests: distinct live classes
  may no longer overwrite one class-ID entry, and removing a class's final
  registry alias now releases that reverse-index entry for a re-imported
  replacement. Registration also rejects every name consumed structurally by
  the V3 parser, rather than accepting unreachable components.
- Triaged all six `test_settings.py` methods without adding a duplicate native
  settings file. The two `context_behavior` cases drop; the two Django
  `BASE_DIR/components` cases map to explicit absolute `Citry(dirs=...)`; and
  dict/schema loading maps to per-instance constructor fields plus direct
  `CitrySettings` normalization.
- Added divergences #26-#28 for registry ownership/global inventory, settings
  scope and directory defaults, and parser-reserved component names. The
  dashboard is now 24 of 54 files and about 401 of 955 cases fully triaged.

### 2026-07-17 - slots and slot-template batch

- Triaged all 22 `test_slots.py` methods and all 67
  `test_templatetags_slot_fill.py` methods against the Python runtime tests,
  the Rust fill/tag-rule parser tests, and the built slot design.
- Added focused regressions for Python-callable slot-site data/fallback,
  positional-versus-keyword Slot calls, contents/function identity and copied
  metadata, implicit/named fill metadata, explicit empty fills, unused
  implicit fills, comments, repeated-site fallbacks, dynamic loop and
  passthrough slots, ignored unknown fills, and the full three-level nested
  override matrix.
- Fixed the one runtime defect the audit exposed: stringifying a captured
  template fill after its originating page render now settles deferred nested
  components through the same iterative queue used by ordinary rendering,
  without finalizing the already-rendered owner a second time. The regression
  also proves the captured Slot remains repeatable.
- Added divergences #29-#32 for default-slot selection, missing template
  variables, the Slot callback/forwarding API, and the removed legacy
  `default=` fallback alias. The dashboard is now 26 of 54 files and about 490
  of 955 cases fully triaged.

### 2026-07-19 - provide/inject batch

- Triaged all 35 `test_templatetags_provide.py` methods against citry's
  `test_provide.py` and the provide/inject source. 22 already-covered (each
  cited to a quoted assertion), 7 replace (Django `{{ payload.field }}`
  dot-access, the observable deep/repeated-render guarantee, and five global
  `provide_cache` lifecycle mechanics represented by detached-artifact lifetime
  tests), 4 drop (Django `{% provide %}` / `{% include %}` / colon-prefix
  aggregate-kwargs syntax, grep-confirmed absent from citry), and 2 ports.
- Ported the forloop gap: `test_provide_wrapping_for_loops_reaches_every_child`
  (one outer provide reaches every child a nested `<c-for>` generates, the
  faithful djc shape) and `test_provide_inside_nested_for_loop` (a citry
  strengthening: a provide INSIDE nested loops re-scopes per `(outer, inner)`
  pair). `component_render.py:631-634` rebuilds `context.provides` per render.
  Probed first: an f-string `c-val` works, but `str(i)` does not (the safe-eval
  sandbox omits `str`). `test_provide.py` 46 -> 48 passing.
- Added divergences #33-#36: the general `c-`-prefix "evaluate this attribute"
  rule (the biggest trap), the `{% provide %}` tag rewrite, the `DepInject` ->
  `Provided` payload type, and the provide/inject error-type changes. Split the
  provide section out of the combined templatetags section and marked it `✔`.
- Ran a two-lens adversarial review workflow (Mechanism 6): citation verifier +
  drop/port/divergence auditor. Both returned "fundamentally sound, no
  blocker/major". Folded back the minor findings: added the faithful
  outer-provide-around-`<c-for>` test (the cited tests had asserted per-iteration
  re-scoping, not djc's shared-outer shape), fixed the forloop docstring count,
  re-cited the repeated-render replace, added the error-propagation clause to the
  drops, made divergence #34 lead with the idiomatic `c-<group>` form, and
  corrected the `Provided` NamedTuple wording.
- Dashboard now 27 of 54 files, about 525 of 955 cases fully triaged.

### 2026-07-19 - expression batch

- Triaged all 31 `test_expression.py` methods: 13 already-covered, 4 replace,
  4 ported, 8 drop, 2 skip-Django, 0 pending. The python-expression and
  literal-container halves are genuinely covered end to end by
  `citry_core/tests/test_safe_eval.py`, because in citry every `c-*` value and
  every `{{ }}` is already a Python expression. The Django-syntax half (filters,
  `{% %}` blocks, `{# #}` in argument values, aggregate kwargs, positional and
  iterable spreads) is a real drop. The `{# #}` case is not simply absent: in a
  plain attribute the comment renders as text, and in a `c-` attribute it is a
  parse error.
- Ported the four gaps across four files, one agent per file so the edits could
  not collide, each required to probe the real behavior before locking it. That
  discipline overturned four wrong hypotheses: a component nested in a `c-*`
  template attribute renders **last** (a deferred `CitryRender`), not first;
  there is no backslash escape inside a quoted attribute value, so nested quotes
  must be the opposite kind; a `c-*` input error reports the **parent's**
  component path (`Root`, not `Root > Leaf`) and underlines the whole component
  tag; and `ExprHtmlAttr` takes `key` before `expr`.
- Closed two further citry-native gaps found while triaging:
  `TestStaticAttrValuesAreNotInterpolated` (a `{{ }}` in a *static* attribute
  renders verbatim, the highest-risk silent change for a djc user) and a
  component-input error-trace test. 24 new tests; suite 2192 -> 2216 passing,
  coverage 92.88%.
- Added divergences #37-#43 (no `{% %}` language, parentheses no longer needed,
  mixed text-plus-expression values, comment placement, no builtins in either
  sandbox mode, nesting a component in an input, and the same input given in
  both forms) and extended #33 with the verbatim-`{{ }}`-in-a-static-attribute
  consequence. Filters, positional/iterable spreads and aggregate kwargs were
  already covered by #18, #20, #1 and #34, so they were referenced rather than
  duplicated.
- Dashboard now 28 of 54 files, about 556 of 955 cases fully triaged.

### 2026-07-21 - component media batch: three bugs, then the port

- Triaged all 50 `test_component_media.py` methods: 15 already-covered, 22
  ported, 7 replace, 5 drop, 1 skip-Django. The earlier seeded row was wrong in
  both directions (inheritance/merge was only covered for single-base leaf
  cases; trusted markup/`PathLike` are supported, not Django-only).
- The audit surfaced three real bugs, each independently probe-confirmed and
  handed to a fixer agent before any porting: an inherited
  `template_file`/`js_file`/`css_file` resolved against the subclass's
  directory instead of the declaring class's (`FileNotFoundError` for a
  subclass in another package); an absolute `Path` in `Dependencies` was
  classified as a URL and emitted as `href` instead of inlined; and the
  dead-slot check ran after the compiled template was published, so the error
  fired once and a retry silently passed. All three fixes verified by re-probe;
  regressions landed with the fixes.
- Ported the 22 gaps as 23 tests across two files (one agent per file):
  `test_deps.py` gained the entry-form matrix (PathLike, str subclass,
  `__html__` pass-through, callables returning any form, wrong-type errors
  naming the component, the djc #522 no-touch-at-class-creation guarantee,
  module-dir-first globs, URL-glob safety, module-anchored relative entries)
  and the 3-level/multi-base `Dependencies` chains (`None`/`extend` on middle
  classes, parents, and single bases). `test_assets.py` gained the
  parametrized 3-level primary-asset matrix, per-class template identity
  (citry's analogue of djc's `origin.component_cls`), pair erasure via the
  file member, reset locality, definition-time laziness, and an
  8-thread concurrent-first-render lock (djc #1587's analogue, structurally
  safe in citry).
- Probe discipline again overturned a brief hypothesis: pass-through
  subclasses each get their own template object whose origin names that
  class, rather than one owned by the declaring class.
- Added divergences #44-#48 (plain-definition asset semantics, bases-first merge
  order, `extend` written order, `bytes` paths raise, one-member-`None` pair
  legal), each verified by probe; folded the `media_class` note into #12.
- The three-lens adversarial review (Mechanism 6) then caught: the #47 bytes
  claim held only for the list shape (a dict-value `bytes` decayed into
  integer bytes and a bare one raised a different error; fixed in
  `_is_single_entry` so every shape, `bytearray` included, raises the naming
  `TypeError`, locked by a parametrized regression); four probe-only claims
  with no locking test (extend written order, plain-definition assets,
  one-member-`None` pair, declared-but-empty `Dependencies`; all four now
  tested); the bug-fix regression miscounted as pre-existing coverage
  (accounting corrected to 14 already-covered / 23 ported); #44 broadened to
  classes named in `extend`; #46 raised to 🟡; #49 added for djc's `%3A//`
  URL escaping; and two overstated test comments reworded.
  Suite 2351 -> 2382 passing; coverage held.

### 2026-07-21 - component batch

- Triaged all 68 `test_component.py` entries (67 collected + 1 upstream never
  collects): 14 already-covered, 11 ported via 12 tests, 19 replace (the
  special-character entry moved to ported once tested), 13 drop, 11
  skip-Django, 0 pending. The seeded section had missed `TestComponentHook`
  (~700 lines) entirely; its three-hook lifecycle maps behavior-by-behavior
  onto the `on_render` generator contract already asserted in
  `test_on_render.py`.
- Ported 12 tests across four files (one agent per file, probe-first):
  `template_data` returning `None`; the render-id contract; untyped accessors
  are the raw dicts; parent/root during and after the render plus the
  three-level tree; same-class-at-two-levels ancestors; the compile-error
  component path (both djc flavors share one citry code path); special
  character input names, locking that `@`-prefixed attributes are consumed as
  client event directives; and the template-less generator `on_render`
  contract.
- Added divergences #50-#53 (the hook merge, the `@`-input trap, the
  `data-cid` marker rename, slot-less error paths), #51 verified by my own
  probe before the port. The events-layer consumption rule behind divergence
  #51 is being reworked in a separate effort; when that lands, update the #51
  row and `test_component_node.py::test_at_prefixed_attrs_are_events_not_kwargs`
  (which locks today's behavior) together. Suite +12 from this batch (2414 total, which also
  includes parallel work landing in `test_autodiscovery.py`); coverage 92.71%.

### 2026-07-21 - templating interaction batch

- Triaged all 22 `test_templatetags_templating.py` methods in parallel with
  the component batch: 8 already-covered, 8 ported via 5 tests, 6 replace,
  and no new divergence rows (every difference is an instance of existing
  rows #6, #8/#9, #11, #18, #29, #30).
- The ports lock the interaction guarantees: same-named fills at two nesting
  depths stay separate with the nested fill body resolving the outermost
  writer's scope (citry matches djc's isolated mode); the child-side
  conditional-slot matrix (one parametrized test folding four djc methods,
  including fill-for-untaken-branch as a silent no-op); an outer-scope
  variable resolving on every loop iteration of a slot site; `fallback=`
  re-evaluating per iteration; and `fallback=` chaining through a passthrough
  slot to the forwarding site's own default.
- Suite +5 from this batch; dashboard 31 of 54 files, about 695 of 955 cases.

### 2026-07-21 - node and extension batch

- Triaged `test_node.py` (32/32: 9 replace, 23 drop, plus 3 supplementary
  engine locks owning no djc methods) and
  `test_extension.py` (25/25: 13 covered, 6 ported via 7 tests, 2 replace,
  3 drop, 1 skip) in parallel.
- `test_node.py` settled the authoring-surface question from the recorded
  decision (`migration_djc.md`, the `node.py` review): citry's user-defined
  tag IS the component; no `BaseNode`/`@template_tag` analogue exists, and the
  compiled-template node set is fixed. The three ports lock the engine
  guarantees that survive: the unregistered-tag error with its caret snippet,
  the verbatim catch-all for special attribute names, and the
  one-group-at-a-time missing-required parse errors (confirmed down to the
  Rust parser's iteration order). Divergence #54.
- `test_extension.py` corrected the seeded "extension views: Skip" verdict:
  djc's extension views are URL routes, and citry has the same surface
  (`Extension.urls`), so two of the three became ports against it. The other
  ports: nested-config inheritance from a plain parent and render-hook payloads
  (fills arrive as `Slot` instances;
  `ctx.component` is observed to be the instance the render created; callers hold a `CitryElement`, never a `Component` instance), and the
  `extensions_defaults` edge cases. Divergences #55-#59 and #90.
- Suite +10 tests from this batch across four files, all probe-first.

### 2026-07-21 - hotreload and component-invocation batch

- Triaged `test_hotreload.py` (24/24: 10 covered, 6 ported, 3 replace, 5 drop)
  and `test_templatetags_component.py` (19/19: 11 covered, 4 ported via 2
  tests, 1 replace, 1 drop, 2 skip) after resuming the session-limit-killed
  cross-maps from their cached enumerations.
- Hotreload's seeded row was wrong in both directions: the weakref-pruning
  port needs unregister-first (strong-ref registry), and the blanket coverage
  hid four gaps, among them `test_reset_files_rereads_js_and_css` asserting JS
  only despite its name (now extended to genuinely cover css). The ports also
  locked one-call-resets-both, multi-class fan-out, inline-never-indexed, and
  css end-to-end reload.
- Component-invocation ports: one sibling-fill-isolation matrix folding three
  djc methods (with the render-twice assertion), a per-level self-recursion
  lock (7 levels, exact output), the colon-attr literal-kwarg trap lock, and
  the Rust `test_unclosed_tag_errors` strengthened from matching `error` to
  the full diagnoses.
- Resolved the rendered-class lifetime finding from divergence #61: const-body
  cache keys now hold component classes weakly, final-alias unregistration
  evicts current render bodies, and the rendered class plus its weak file-index
  entry disappear after the caller releases the class.
- Folded back the node/extension review: the node accounting restated honestly
  (9 replace + 23 drop; the 3 new tests are supplementary locks owning no djc
  methods), a phantom test-name citation fixed, stale line anchors replaced
  with test names, the TSBV-duplication claim corrected, and three test
  hardenings landed (gc-checkpoint before collect, defaults factory-untouched
  assert, plus the softened ctx.component wording).
- Added divergences #60-#63. Suite +9 Python tests (7 method-owning ports
  plus the colon-attr lock and the render-after-unregister lifetime
  regression) and one strengthened Rust test from this batch.
- Resolved with the maintainer: `django>=5.2; python_version >= '3.12'` added
  to citry's dev group (a range, not the benchmark group's exact pin, so no
  version mirroring), making `test_contrib_django.py` genuinely execute in the
  shared venv and CI (8/8). The benchmark suites stay inactive (they key on
  `django_components`, not django).

### 2026-07-21 - autodiscover and template batch

- Triaged `test_autodiscover.py` (4/4: 1 covered, 2 drop, 1 replace) and
  `test_template.py` (4/4: 1 covered, 1 replace, 1 drop, 1 skip) with the new
  right-sized shape: one full-triage agent per small file at xhigh, no
  separate enumeration stage. `test_tag_formatter.py` got its own section in
  the split (content unchanged, already `✔`).
- Two small locks added: `test_rescan_does_not_reexecute_loaded_modules`
  (an already-imported module survives a second scan untouched, the guarantee
  at the center of djc #1598) and
  `test_unrelated_classes_with_identical_inline_source_get_own_copies` (djc's
  string-keyed `cached_template` shared identical sources; citry is strictly
  per class).
- Added divergences #64-#66 (the `libraries` setting, the autodiscovery API
  shape, and the absent `@djc_test` harness). `test_template.py` contributed
  none: its differences all belong to already-catalogued rows.

### 2026-07-21 - loader and typing batch

- Triaged `test_loader.py` (15/15: 4 covered, 1 port, 8 skip-Django, 2 drop)
  and `test_component_typing.py` (13/13: 6 covered, 2 port, 3 replace, 2
  drop). Two enumerate-and-map agents at xhigh, then a two-agent port
  workflow over disjoint file pairs (autodiscovery+assets vs
  component+tag_rules), probe-first throughout.
- 10 tests added across four files: `TestFindComponentModules` gains the
  only-`.py`-files and nested-subpackage locks plus the supplementary
  str-dirs lock (`test_autodiscovery.py` / `test_assets.py` side);
  `TestKwargsRenderValidation` and `TestSubclassTypedInputs` lock the
  Python-call validation path and subclass `Kwargs` semantics
  (`test_component.py`); `TestKwargsValidation` locks the empty-`Kwargs`
  no-inputs contract, both rejection paths and the bare-use happy path
  (`test_tag_rules.py`).
- One genuine bug surfaced: a dot-prefixed `.py` file under `Citry(dirs=...)`
  crashed the first discovery scan with `ModuleNotFoundError` (djc silently
  skips such paths). Fixed the same day by a dedicated workflow (next entry);
  divergence #70 carries the user-facing row.
- Added divergences #67-#70: the data-method rename (`get_template_data` to
  `template_data`, the one silent-wrong-output rename in the catalogue so
  far, 🔴), dataclass-not-NamedTuple typed inputs, the `Empty` marker
  replacement, and the dot-prefix crash.

### 2026-07-21 - dot-prefix discovery fix and loader/typing review fold

- Fixed the discovery crash: `_iter_py_files` now skips any path with a dot
  in its name beyond the `.py` suffix (dot-prefixed files and directories,
  backup copies like `card.old.py`, dotted directory names, symlinks
  resolving to such paths), mirroring the underscore filter. Written
  regression-first (both new tests observed failing with the exact
  `ModuleNotFoundError` before the fix); an adversarial review round then
  surfaced two escapes (dotted stems, clean-named symlinks to hidden
  targets), fixed and locked in the same pass. Four regression tests landed
  with the fix, plus a CHANGELOG entry.
- Same-class sweep: the hot-reload polling watcher walks the same trees with
  no junk filter (`reload.py:125`), so it stats junk on every poll and editor
  lock-file churn can trigger spurious reloads; no crash. Left out of scope,
  noted here for a follow-up.
- Folded the loader/typing review panel (19 confirmed findings, 0 refuted):
  a wrong divergence citation (#35 corrected to #27), `TestDirsValidation`
  attributed to the wrong file, stale dashboard section headers recounted
  mechanically, and one wrong factual claim ("no process-global state": the
  default `Citry` instance is process-wide, and #66 plus the autodiscover
  section now say so). Test hardening from the panel: the tag-rules
  rejection tests now pin the offending attribute name, the rescan lock
  holds the module and one top-level name (catching both replacement and
  re-execution), and the non-Python-files fixture uses unique stems so a
  suffix-filter regression cannot hide by deduplicating into an existing
  module name. One finding was rejected after a probe: the str-dirs
  supplementary lock is not duplicate coverage (low findings skip
  adversarial verification by design).
- Rewrote divergence #70 to the fixed contract: citry silently skips every
  dotted name, a strict superset of djc's skip (djc crashes on dotted names
  that are not dot-prefixed). A later review probe found one skipped case
  that djc imported successfully (a clean-named symlink to a dot-hidden
  target), so the row carries that exception at yellow.

### 2026-07-21 - cache and defaults batch

- Triaged `test_cache.py` (3/3: 1 covered, 2 replace) and
  `test_component_defaults.py` (15/15: 3 ported, 4 replace, 8 drop); one
  full-triage agent per file at xhigh, then a two-agent port workflow over
  disjoint file sets.
- 7 tests added. Cache side: a plain-JS component's `js_data()` is never
  cached or shipped while its css side still is (with a `$component` control
  component in the same test proving the assertion bites), and a no-assets
  component writes no cache entries at all. Defaults side: the new
  `TestKwargsDefaults` class locks the default value flowing through both
  call paths with `raw_kwargs` untouched, `default_factory` giving a fresh
  object per render (the first `default_factory` lock in the suite), and the
  loud class-definition failure for a mutable class-level default; the
  nested-dataclass pass-through lock landed in `TestInputNormalization`.
- Boundary with the pending component-cache extension held: djc's media-cache
  method exercises the live dependencies script cache, so it was triaged now;
  the extension rows (caching rendered output by input) stay pending.
- Added divergences #71-#75. The sharpest is #71: a leftover `Defaults` inner
  class is silently ignored, failing only at render with nothing pointing at
  the cause. Maintainer decision: no definition-time warning, and no other
  django-components compatibility code in citry; the divergence catalogue is
  the migration aid, so the row carries the full rewrite recipe instead.

### 2026-07-21 - cache/defaults review fold

- Panel result: 12 confirmed findings, 0 refuted. Ledger corrections: the
  summary recounted to 42/856 (a parallel agent's highlight flip had not
  been absorbed into the arithmetic); djc's unset-cache destination
  corrected in #75 (a private in-memory store of its own, never Django's
  default cache, per the vendored source); #71's rejected-input consequence
  scoped to components that declare `Kwargs`; the #70/loader/CHANGELOG
  skip-set wording made mechanical ("a dot in the name": hyphen and digit
  names are discovered and executed, so "cannot form a valid import name"
  overstated); the LRU row now says citry's lock is stricter than djc's own
  (djc's assertions pass on a store with no refresh-on-read); the
  `test_cache.py` dashboard row moved to its alphabetical spot.
- #70 bumped to yellow: a review probe against the vendored djc loader
  showed a clean-named symlink pointing into a dot-prefixed directory is
  imported by djc but silently skipped by citry; the row now carries that
  exception and its workaround.
- Test corrections: a NamedTuple `Kwargs` default value-flow lock added
  (`test_default_on_a_namedtuple_kwargs_applies_too`; the row had cited
  dataclass-form tests for the namedtuple-form djc method), the rescan
  comment now describes the real failure modes (a body re-run raises
  `AlreadyRegistered` before the asserts fire), and the stem-filter
  comment's case-sensitivity claim fixed (glob matching follows the
  platform, not the filesystem).

### 2026-07-21 - dynamic and error-fallback batch

- Triaged `test_component_dynamic.py` (13/13: 10 covered, 1 replace, 2 drop,
  0 gaps) and `test_component_error_fallback.py` (8/8: 3 covered, 4 ported,
  1 replace); one full-triage agent per file at xhigh. Both features are
  fully built in citry (`<c-component>` since 2026-06-12 with its own
  41-function test file; `<c-error-fallback>` on the `on_render` generator
  hook), so the dynamic side needed no new tests at all.
- 6 tests added to `test_error_fallback.py` by a single port agent: the
  kwarg cells of the Python-call matrix (honored on safe and raising
  content, no fallback renders empty, fallback-only renders empty; the
  slot-form cells followed in the review fold),
  the fallback-with-no-content cell in both template forms, and boundaries
  inside a `<c-for>` catching per iteration with the fallback reading the
  loop variable (exact interleaved output locked).
- Added divergences #76-#80: the dynamic-component shape (no importable
  class, no rename setting), the reserved built-in names (a class simply
  named `Element` fails at definition), the unknown-name message wording,
  the error-boundary shape (body-as-content, `fallback` attribute or fill,
  `RuntimeError` on both forms), and the then-current requirement for dict
  values to use subscripts in expressions. The slot-data part of that last
  divergence was superseded on 2026-07-24: fills now receive `SlotData`, whose
  identifier keys support attribute access such as `{{ d.error }}`.

### 2026-07-21 - dynamic/error-fallback review fold

- Panel result: 16 confirmed findings collapsing to 8 distinct issues, 0
  refuted. The substantive one: the safe-content-with-a-fill-form-fallback
  cell was locked nowhere (the section had counted the attribute-form test
  for it). Two locks added
  (`test_fallback_fill_suppressed_when_content_is_safe`,
  `test_fallback_slot_suppressed_from_python_when_content_is_safe`) and the
  two matrix rows now account for all seven Python cells and five template
  cells explicitly, crediting the pre-existing slot-error lock they had
  silently leaned on.
- Ledger corrections: a typo'd node id fixed
  (`test_rest_of_page_renders_around_caught_error`), the nested-method row
  now cites its cascade and error-data locks, #77's djc column corrected
  (djc registers `error_fallback` at startup too, so two names are taken
  there, not one), #79's failure timing corrected to first render (the
  class defines without error), and the `<c-component>` implementation
  date fixed to 2026-06-12.
- Pre-existing dead code fixed while there:
  `test_escaped_error_names_guarded_child` defined a guarded page it never
  rendered; the guarded half now asserts the boundary swallows the error
  and the page serializes.

### 2026-07-21 - command files batch

- Triaged the four command files in one pass (23/23: `components` 1 ported;
  `create` 1 covered + 2 replace + 1 ported + 3 drop; `ext` 5 covered +
  3 ported + 3 drop; `list` 1 replace + 3 drop); one triage agent at xhigh
  over the whole set, since they share the one CLI surface. Two of djc's
  ext-run methods are byte-identical duplicates upstream.
- The alias, scaffold-shape, and `manage.py` drops cite recorded decisions
  in `extensions_commands.md`; the six listing-format-flag drops rest on
  the flags' evident absence from the minimal surface (passing one is a
  usage error), with no flag-level decision recorded - the one
  drop-by-absence set in the batch. No compatibility aliases per the
  standing decision.
- 6 tests added to `test_cli.py` by a single port agent, all assertion gaps
  over probed-working behavior: the help listings printed at the three
  command-tree levels that only route to subcommands (bare `citry` and
  `--help`, `citry ext`, and `citry ext run`, which offers only
  command-bearing extensions), the `Created <path>` success message, and
  the invalid-choice rejection for an unknown command under a known
  extension.
- Added divergences #81-#84: the `manage.py`-to-binary shift (with
  `--app module:attribute` for owned engines), the single-file `create`
  scaffold, the fixed listing columns, and the `ExtensionCommand` authoring
  rebase (`handle` receives only declared options; the engine is
  `self.citry`).
- Follow-up on maintainer request, same day: `citry list` gained a `path`
  column showing the file that defines each component (relative to the
  working directory when inside it; a component with no source file leaves
  the cell empty). Locked by `TestListComponents` (including the empty-cell
  case); #83, the section row, and the CHANGELOG CLI bullet updated. A
  dedicated adversarial review then hardened it: a file reached through a
  symlinked directory inside the project keeps its project-relative
  spelling (the as-imported path is tried before the physical one), the
  empty-cell test now asserts the ghost row is exactly name plus class (a
  placeholder fallback would have passed the old asserts), and the
  CHANGELOG claim gained its "when it has one" qualifier. The review also
  surfaced a pre-existing CLI roundtrip gap, noted below. A second
  maintainer request followed: the listing merges aliases, printing one row
  per component with all its registered names (a class auto-registers under
  its lowercased and kebab-case forms, which previously produced two rows).
- Two observations from that review's end-to-end probe (both pre-existing,
  neither caused by the change). First, the `citry create` scaffold binds
  to no engine; maintainer-confirmed as intended: the scaffold is a
  starting template, and the flow is create, open the file, edit (binding
  an engine yourself as needed), not create-then-list. Second, `--app
  module:attr` could not resolve a module that only exists in the working
  directory (console scripts do not put the working directory on
  `sys.path`), so `citry --app app:engine list` from a plain project root
  failed with "No module named 'app'". Maintainer decision, same day:
  follow the convention of the ASGI/WSGI servers the `module:attribute`
  syntax is borrowed from. The console entry now inserts the absolute
  working directory at the front of `sys.path` (once, skipped when already
  present, so `python -m citry` keeps identical semantics), fixed
  test-first by a dedicated workflow: the regression was observed failing
  with the no-module error, an adversarial review round added a `sys.path`
  leak guard for the in-process test calls plus a front-position lock, and
  a fresh-interpreter test pins that plain `import citry` never mutates
  `sys.path`. CHANGELOG updated.

### 2026-07-21 - command-files review fold

- Panel result: 15 confirmed findings collapsing to 10 distinct issues, 0
  refuted. The three highs: the "every drop is backed by a recorded
  decision" claim was false for the six listing-format-flag drops (the
  triage cited `extensions_commands.md` for a decision it never records;
  the panel read the doc end to end); #81 misdescribed `startcomponent` as
  a syntax migrator when it is djc's deprecated alias of `create`, so the
  row told `startcomponent` users they had nothing to run when `citry
  create` is the direct equivalent; and the pre-existing bare-extension
  help test asserted `"greet" in out`, which the word "greeter" in the
  usage line satisfies even with the command roster gone.
- Fixes: the intro, flags row, and log bullet now state plainly which drops
  are recorded decisions and which rest on evident intent; #81's citry and
  action cells corrected; the help test now locks the `{greet}` braces
  roster; the root and ext help tests also lock the subcommand description
  lines (djc locked them; the ports had silently narrowed that away); the
  `--help` test now asserts byte-equality with the bare invocation's
  output instead of one shared substring; the `ext list` ordering citation
  now points at the real mechanism (manager construction order,
  `extension.py:651`) and the real order-sensitive locks
  (`test_extension.py:67`, `:827`); #83 bumped to yellow (scripts parsing
  the listing or passing the old flags break) with both surfacing files
  cited.
- Maintainer decision, same day: the minimal-CLI-surface /
  no-formatting-flags decision stays unrecorded in
  `extensions_commands.md`; the evident-intent framing in the section and
  rows above is the record.

### 2026-07-22 - utility files batch

- Triaged `test_util_weakref.py` (3/3: 1 replace, 1 ported, 1 covered) and
  `test_utils.py` (1/1: drop); one triage agent at xhigh over both. No new
  divergence rows: these are djc-internal utilities, and the user-visible
  ends of their stories were already catalogued (#61 collectability, #15
  the tag formatter's death taking quoted names with it).
- The triage's find: djc's finalizer-stacking regression test maps to
  citry's file-index dedup guard (`citry.py:841`, re-registered on every
  asset resolution), which had no direct lock. Locked probe-first as
  `test_assets.py`
  `TestFileIndexAndResets::test_reload_cycles_do_not_stack_index_entries`
  (5 load/reset cycles, two classes sharing one file, each listed exactly
  once on both public surfaces).
- Review fold: the reviewer's guard-deletion run over the full suite
  refuted the triage's stronger no-coverage claim (three pre-existing
  reset-scoping and invalidate tests fail on duplicate entries when the
  guard is removed), so the section records incidental-vs-direct coverage
  instead. Two citation fixes: the Rust quoting sentence now says what the
  tests actually lock (unterminated quotes error; unquoted values are legal
  and parse), and the intro's catalogue references were trimmed to the apt
  pair (#61, #15).
- The old blanket "Replace (superseded)" verdicts for these files were
  refined: one of the three weakref methods was a port in disguise, and the
  `is_str_wrapped_in_quotes` method is a drop (nothing replaces the boolean
  contract; the feature it validated does not exist), with the Rust
  grammar's quoting errors cited as the surviving guarantee.

### 2026-07-22 - render-cache design baseline

- Recorded the approved [`caching.md`](caching.md) dispositions for all
  `test_component_cache.py` and `test_django_cache_tag.py` behaviors. Their
  replacement tests and public features landed in the following Cache phases.
- Reclassified the five global `provide_cache` lifecycle methods as
  replacements. Citry's portable guarantee is that a detached render-cache
  artifact retains no provide payload, context, component instance, or class.
- Strengthened `test_render.py` so the live-render boundary is explicit:
  serializing one `CitryRender` twice preserves its ID, while rendering the
  same `CitryElement` again mints a new ID.

### 2026-07-23 - dependency-manager and Component.View batch

- Triaged all 12 `test_dependency_manager_e2e.py` methods. Added the direct
  fire-and-forget/non-function-return lock and strengthened the synchronous
  throw and rejected-Promise tests to preserve their original error details.
  The Citry manager contract is now explicit: one `Citry.manager`, synchronous
  initialization, cleanup functions as the only meaningful callback return,
  isolated failures, and `els=[]` for an instance with no roots.
- Triaged all 14 `test_component_view.py` methods against the completed Events
  extension. Added exact event-URL encoding coverage and an end-to-end
  ViewEvents return path covering props, slot fallback/fill, and escaping on
  both ASGI and sync Django hosts.
- The ViewEvents port exposed a production defect: an instance-less classic
  request could not return the component promised by the compatibility API.
  Compatibility dispatch now gives that render a schema-valid internal target
  for result hooks, then translates its HTML into the whole response. JSON/wire
  dispatch remains strict, and the ViewEvents route now carries the same
  async-host twin as the ordinary Events routes and rejects components that did
  not opt into `ViewEvents`.
- At that point the dashboard reached 54/54 files and about 955/955 source
  cases, completing source-test triage while the separately marked Cache ports
  remained untouched. Those Cache replacements landed later on 2026-07-23.

### 2026-07-23 - reload/watch coverage hardening

- Added deterministic default-suite coverage for all three watcher adapters:
  real-filesystem polling with synchronized baseline and unchanged scans,
  prompt interruption of a long polling interval, scan races, `watchfiles`
  batch translation, and `watchdog` event/lifecycle translation. The native
  optional-backend tests remain as smoke tests when their extras are installed;
  the adapter tests need neither extra and avoid native-event timing in the
  default CI matrix.
- Locked the public watcher-handle state and the CLI's Ctrl-C cleanup path. A
  regression exposed that `watch()` invalidated aliases correctly only because
  `invalidate_file()` resolved them internally, while `on_reload` still received
  raw duplicate spellings. Changed paths are now resolved and de-duplicated once
  before both invalidation and notification.
- Reconciled [`hot_reload.md`](hot_reload.md) with the built behavior: polling
  and `watchfiles` emit batches, while `watchdog` intentionally forwards its
  one-at-a-time events. The separate editor-junk filtering follow-up above
  remains a product-policy question and was not folded into this coverage pass.

### 2026-07-23 - Dependencies coverage hardening

- Added public contract coverage for callable declarations, string and `Path`
  glob fallbacks (including a class with no module file), cross-kind entry
  errors, pre-rendered JS/CSS entries, served local JavaScript, missing-asset
  responses, strict variables JSON, identical CSS-data de-duplication,
  extension-added fragment dependencies, and quoted runtime URLs.
- Fixed four user-visible edge cases found during the branch audit:
  whitespace-only component assets produced dead fragment URLs and false CSS
  state, mixed-case closing tags bypassed the inline-content guard, valid
  unhashable `__html__` entries failed during de-duplication, and an invalid CSS
  media value leaked an incidental iteration error.
- Kept Cache artifact staging/replay and Events history/download work outside
  this batch. Private defensive branches with no public input path remain
  intentionally uncovered.
- Focused verification passes 208 tests and brings dependency delivery
  (`emission.py`, `scripts.py`, and `routes.py`) from 92.49% to 95.55%
  line-and-branch coverage. The repository gate passes all phases at 92.69%,
  up from the 92.43% pre-batch measurement.

### 2026-07-23 - Events schema-publication coverage hardening

- Added public OpenAPI coverage for the complete supported request annotation
  table, defaults and non-input fields, integer and mixed-value enums,
  recursive and colliding schema names, reserved error-schema names,
  deterministic operation ID collisions, typed return unions, empty GET
  inputs, and shared or conflicting nested Pydantic definitions.
- Added runtime-schema and Events-introspection parity coverage for
  parameterized `Mapping` fields, exact `None`, unsupported annotations,
  readable union errors, prebuilt nested and temporal values, inherited plain
  fields, every dataclass default form, and deferred `ClassVar` spellings.
  Defaults and factories remain unexecuted during document and metadata
  generation.
- Fixed two user-visible discrepancies exposed by the tests: parameterized
  `Mapping` fields now validate as object shapes, and the exact deferred
  `typing.ClassVar` spelling no longer appears as a request field in component
  introspection. A subclass `ClassVar` override also removes the inherited
  field from the published schema, matching runtime validation.
- Kept Cache, Events tokens, history/download actions, transport code, and
  Pydantic-v1 emulation outside this batch. Unsupported OpenAPI annotation
  fallbacks remain unpinned because their permissive schema does not match the
  runtime's rejection. Parameterized mapping values remain typed in OpenAPI
  while runtime validation checks only the object shape; aligning those
  without weakening typed return schemas remains a separate follow-up, as does
  conversion of inherited plain schemas that combine base fields with
  dataclass `field()` markers.
- Focused verification passes 515 tests. OpenAPI rises from 77.87% to 97.60%,
  runtime schemas from 94.97% to 98.33%, and Events introspection from 83.53%
  to 100.00% line-and-branch coverage, recovering 104 of their original 121
  uncovered obligations. The repository gate passes all phases at 93.27%, up
  from 92.69%.

### 2026-07-23 - Cache ports and test-migration closeout

- Completed the remaining Cache mappings with deterministic public TTL expiry,
  a genuine two-field `c-vary` matrix, and a literal `<c-slot>` inside
  `<c-cache>` whose caller fill contains a component and replays under the
  current lexical writer.
- Hardened untrusted artifact UTF-8 and size validation, stale dependency replay
  rejection, transitive Slot-writer anchors, staging-revision races, and repair
  rollback. Added focused key, artifact, transaction, and multi-Slot coverage.
- Reclassified the one-engine backend decision as an intentional replacement,
  not a pending port. All 54 files and approximately 955 source cases now have
  final dispositions and all applicable native tests are present.
- With explicit maintainer approval, retired `_djc_tests/`, its pytest and Ruff
  exclusions, and the vendor script's test-snapshot path. Pinned upstream links
  preserve provenance without keeping a second test tree.

### 2026-07-23 - Events history and download coverage hardening

- Added server coverage for usable ASCII download filenames, raw GET downloads,
  and the shared rule that request updates which change State prohibit
  `Download` and `RouteResponse` answers because a raw response cannot carry
  the refreshed State token.
- Added browser coverage for late responses attempting history changes, native
  Back and Forward traversal, malformed and path-shaped attachment filenames,
  the filename-less `download` fallback, and browser-save failures. The tests
  lock lifecycle settlement, temporary-link cleanup, and object-URL release as
  well as the visible result.
- Fixed Unicode-only basenames losing their useful ASCII stem. The fallback now
  synthesizes `download`, preserves an intentional dotfile prefix and a usable
  extension, and removes terminal dots while the exact original remains in the
  UTF-8 `filename*` parameter.
- Kept generic transport hardening and the three schema-publication follow-ups
  outside this batch. The completed Cache migration and its closeout status are
  unchanged.
- Focused verification passes 283 server tests, 38 Chromium tests, and the full
  client typecheck, lint, and unit suite. Events actions reach 100% line-and-
  branch coverage; Events routes rise from 93.80% to 94.63%. The repository
  gate passes all phases at 93.67% overall coverage.

### 2026-07-23 - Events transport and codec coverage hardening

- Added public route and codec coverage for malformed UTF-8 forms across both
  hosts, reserved GET metadata, registered-codec ordering, per-event multicall
  rejection, unknown components, explicit GET cache policies, and the pointed
  `Events.url()` misuse diagnostic. Compatibility responses now turn finite
  non-JSON values such as `Decimal` into the same controlled `handler_error`
  response as other strict-JSON failures instead of leaking a host exception.
- Completed the dispatcher rejection, async, CSRF, context, rolling-State, and
  capability matrices. Final `on_event_result` output is validated and checked
  against the advertised client capabilities after the State refresh is
  generated, while retaining the documented hook-before-State ordering.
  Exceptions and malformed replacements from `on_event_error` retain the
  original generic 500 result and valid replacements echo the call epoch.
- Added atomic browser preflight for the complete result envelope before any
  result slot applies. It checks protocol and request correlation, cardinality,
  success and error shapes, and exact epoch echoes; the deliberate pre-decode
  `id: "-"` edge error is propagated to every queued caller. The browser matrix
  also covers malformed HTTP responses, invalid local GET encoding, synchronous
  and asynchronous custom-transport failures, and response arrival before a
  slow action finishes. Existing client payload budgets remain green.
- Kept the three schema-publication follow-ups outside this batch. The private
  `_resolve_handler(citry, None, ...)` guard remains intentionally uncovered;
  public routing always supplies both URL parameters. Cache and the completed
  history/download behavior are unchanged.
- Focused verification passes 257 server tests, 140 Events Chromium tests, and
  the full client typecheck, lint, and unit suite. Events codecs and dispatcher
  reach 100.00% line-and-branch coverage, and Events routes reach 99.10% with
  every public path covered. The repository gate passes at 94.01% overall
  coverage. Its enforced floor is raised from 91% to 93% so the gate retains
  most of that gain.

</details>

---

## Divergences for djc users (migration guide seed)

Migrating the tests one at a time surfaces every place citry behaves
differently from django-components. This section is the running catalogue of
those differences, framed as **what a django-components user must change to
move a project to citry**. It grows one entry per divergence as files are
triaged; by the end of the test migration it is the raw material for a
published djc-to-citry migration guide.

Scope is the concrete, user-observable differences that test triage proves.
Broader architectural changes (kwargs-only components, `<c-*>` syntax instead
of `{% component %}`, no `context_behavior`, slots as explicit inputs) are
catalogued in [`migration_djc.md`](migration_djc.md); they are pulled in
here as the tests that exercise them are triaged, so this stays a single
checklist a user can work through.

Standing maintainer decision (2026-07-21): citry ships **no
django-components compatibility code**, no legacy aliases, no
definition-time warnings for leftover djc idioms (such as a `Defaults` inner
class that citry ignores). This catalogue is the migration aid; a djc-shaped
trap is handled by making its row here complete, not by a shim or warning in
the engine. Do not re-propose such shims when triage surfaces a new trap.

Impact legend: 🔴 breaks a project until changed; 🟡 changes output or
behavior a project may rely on; 🟢 cosmetic or assertion-only (affects
exact-HTML snapshot tests, not what a browser renders).

Two notes for whoever turns this into the published guide. The **Surfaced by**
column is a triage aid that records which upstream test file exposed the
difference; it points at files a reader cannot open, so drop it on the way out.
And publish the rows grouped by area (templates, inputs and expressions, slots,
provide and inject, assets, settings and registry) rather than in the order
triage happened to reach them, with a short "getting started" step before the
first row: install, create a `Citry` instance, register components.

| # | Area | django-components | citry | What to change | Impact | Surfaced by |
|---|---|---|---|---|---|---|
| 1 | Merging HTML attributes | The `{% html_attrs %}` tag (positional args, `attrs:` / `defaults:` aggregate keys, spread) | Element-level attributes: `c-bind="mapping"` to spread, plus `c-class` and `c-style` | Rewrite `{% html_attrs attrs defaults class=... %}` as `<div c-bind="defaults" c-bind="attrs" c-class="...">`. Attributes apply left to right and the later one wins, so put the fallback mapping first and the caller's mapping after it. `class` and `style` merge instead of overwriting. A leftover `attrs:foo=` is not rejected: it arrives as an input literally named `attrs:foo`, so search for `:` in attribute names. | 🔴 | `test_attributes.py` |
| 2 | Repeated non-`class`/`style` attribute keys | The same key supplied twice is space-joined (`foo="bar baz"`) | Last-one-wins (`foo="baz"`) | If you relied on a repeated plain attribute concatenating, combine the value yourself. `class` and `style` still merge. | 🟡 | `test_attributes.py` |
| 3 | Single-quote HTML escaping | Escaped as `&#x27;` | Escaped as `&#39;` (the same character, numeric-decimal entity) | Nothing for rendered pages; browsers treat the two entities identically. Update only tests that assert the literal `&#x27;` bytes. | 🟢 | `test_attributes.py` |
| 4 | Dependency rendering strategy | `render_dependencies(html, strategy=...)` / `DJC_DEPS_STRATEGY` with strategies `document`/`simple`/`prepend`/`append`/`raw` and a legacy `type=` alias | One `serialize(deps_strategy=..., deps_position=...)` call: `deps_strategy` is `document`/`simple`/`fragment`/`ignore`, `deps_position` is `smart`/`prepend`/`append` | Call `serialize()` on the render result and pass the strategy there: `MyComp(...).render().serialize(deps_strategy="document", deps_position="append")`. Map `prepend`/`append` to `deps_position`, map `raw` to `deps_strategy="ignore"`, and drop `type=`. A project-wide default goes on the `Citry(...)` instance rather than in settings. | 🟡 | `test_dependencies.py` |
| 5 | Error when a component's inline JS/CSS contains its own end tag | Raises `RuntimeError`, message `...contains '</script>' end tag.` | Raises `ValueError`, message `...contains a '</script>' end tag. This is not allowed.` | If you catch this error or assert its message, switch to `ValueError` and the new wording. | 🟢 | `test_dependencies.py` |
| 6 | The citry runtime script | A dependency-manager script is emitted on every document render | Citry adds its runtime script (`citry.js`) only when a page needs it: when a component uses `$component`, or when the page must stay in step with HTML fragments loaded later | Nothing changes in your templates. In tests, drop assertions that the runtime `<script>` is present on every rendered document. | 🟢 | `test_dependencies.py` |
| 7 | Component template must be well-formed | A component's `template` is arbitrary text passed to the Django template engine; unclosed tags are tolerated | An unclosed or mismatched tag is an error: loading the component fails with `SyntaxError: Unclosed tag <thead>` | Close every tag in a component `template`. A partial that was a bare `<thead>` fragment has to become a complete unit, for example by including its `<table>` wrapper and passing the rows in as a slot. | 🟡 | `test_dependencies.py` |
| 8 | Ambient template context | A component can read variables that are simply in the surrounding `Context`, and exposes `self.outer_context` | A component receives only its explicit props (kwargs) and slots; there is no ambient context and no `outer_context` | Pass every value a component needs as an explicit prop. For caller state that must reach deep descendants, use `provide` / `inject`. | 🔴 | `test_context.py` |
| 9 | `context_behavior` setting and `only` | `context_behavior` chooses `django` (child sees outer context) vs `isolated`, and `only` forces isolation per call | citry is always isolated, as if `only` were always on | Remove `context_behavior` from settings and drop `only`; behavior already matches djc's `isolated`. A project that ran in `django` mode must also rewrite fills that read the child's variables (loop items and friends): pass them explicitly as scoped slot data (`c-name=` on the slot site, `data=` on the fill). | 🟡 | `test_context.py` |
| 10 | Request, context processors, CSRF | `self.request`, context-processor variables, and `csrf_token` are injected into the template context | citry injects no ambient request-derived variables | Read the request in your view and pass what each component needs (CSRF token, current user, locale) as ordinary props. There is no per-request ambient context, so a value many components need is best provided once near the top of the page with `<c-provide>` and read with `inject()`. | 🔴 | `test_context.py` |
| 11 | Slot-filled introspection | `{% if component_vars.is_filled.title %}` branches on whether a slot was filled | The `component_vars.is_filled` magic variable is gone | In `template_data` compute `{'has_title': slots.get('title') is not None}`, then branch with `<c-if>`. | 🟡 | `test_context.py` |
| 12 | Static asset delivery | Component assets are served through `ComponentsFileSystemFinder` / `collectstatic`, gated by `static_files_allowed` / `static_files_forbidden` | citry serves only generated component scripts/styles through its own mounted WSGI/ASGI routes; component source (`.py`/`.html`) is never served | Remove the finder from `STATICFILES_FINDERS`, drop `collectstatic` for components and the `static_files_*` settings, and mount citry's asset routes. A custom `media_class` (overridden `render_js`/`render_css`) has no hook either: control tag output with `Script`/`Style` entries and the `on_dependencies` hooks. | 🔴 | `test_finders.py`, `test_component_media.py` |
| 13 | Observing which components rendered | The Django `template_rendered` signal and `assertTemplateUsed` report what rendered | citry has no template signal | Replace signal receivers / `assertTemplateUsed` checks with a test extension that records `on_component_rendered`. | 🟡 | `test_signals.py` |
| 14 | Django template inheritance | Component templates use `{% extends %}` / `{% block %}`, and `{% include %}` pulls in partials | citry has no template inheritance or `{% include %}` | Restructure an `{% extends %}` template into a base component composed via slots; replace `{% include 'p.html' %}` with a `<c-p />` component. | 🔴 | `test_templatetags_extends.py` |
| 15 | Component invocation syntax | A pluggable `TagFormatter` / `ShorthandComponentFormatter` customizes the `{% component %}` tag form | citry's syntax is the fixed `<c-*>` form; there is no formatter to configure | Remove any `tag_formatter` setting and custom formatter subclasses; write components as `<c-name />`. | 🔴 | `test_tag_formatter.py` |
| 16 | django-template-partials integration | Rendering `template.html#partial_name` where the partial contains components | No direct equivalent | Compose the partial as a citry component and render it directly. | 🔴 | `test_integration_template_partials.py` |
| 17 | Unterminated expression/comment delimiters | An opened `{{` or `{#` with no closing delimiter falls back to visible text | Citry raises `SyntaxError` when the component is loaded, before anything renders | Close the expression/comment delimiter; do not rely on malformed template syntax rendering literally. | 🟡 | `test_template_parser.py` |
| 18 | Django template filters | Tag values use `value|filter:arg`, filter registries, chaining, and filter-specific whitespace/arity rules | Citry has no template filters; `|` inside an expression is Python bitwise-or | Rewrite filters as Python expressions, for example `value.upper()`, `'yes' if value else 'no'`, or an explicitly supplied helper callable. | 🔴 | `test_tag_parser.py` |
| 19 | Translation shorthand in component inputs | `_('text')` is a special translation value inside arguments, filter arguments, lists, and dicts | Citry has no translation token/backend; the default sandbox also rejects the variable name `_` | Translate in `template_data`, or expose a non-underscore callable such as `translate` through template globals and use `c-label="translate('Hello')"`. | 🔴 | `test_tag_parser.py` |
| 20 | Positional component inputs and list spreads | Tags accept positional values and `...list`, with Python-like positional/keyword ordering rules | Component invocations are kwargs-only; `c-bind` spreads mappings, not positional lists | Give every input a name. Replace a positional list spread with a mapping and `c-bind`, or model the list as one named prop. | 🔴 | `test_tag_parser.py` |
| 21 | Parser-registered tag flags | A `TagSpec` can declare flags that affect parsing but are omitted from the component's args/kwargs | There are no parser flags. A bare attribute is a normal input with the value `True` | Convert each custom flag into an explicit boolean prop and handle it in the component. | 🔴 | `test_tag_parser.py` |
| 22 | `$component` callback payload | The first callback argument is the component's JS-data object, with a separate context argument | One object is passed: `{id, els, data}`. Extensions may add more members to it | Rewrite the django-components callback as `$component(({data, els, id}) => { const {message} = data; ... })`. Handle `data === null` when `js_data()` returns no values. | 🔴 | `test_component_js.py` |
| 23 | Dependency placement tags | `{% component_css_dependencies %}` emits CSS only; `{% component_js_dependencies %}` emits JS only | `<c-css />` and `<c-js />` only choose *where* the styles or scripts go. Leave one out and those assets still land on the page, in their usual place | Use the tags for placement only. If you left `{% component_css_dependencies %}` out of a page to keep its CSS off, that no longer works. To keep an asset off the page, remove it from the component or filter it in `on_dependencies`. | 🟡 | `test_dependency_rendering.py` |
| 24 | Component names containing `/` | The string-form component tag can address a registry name such as `te-s/t` | Component names are HTML-tag-compatible: they start with a letter and contain only letters, digits, hyphens, underscores, or dots | Rename a slash-delimited registry key, for example `te-s/t` to `te-s-t` or `te.s.t`, and update the `<c-*>` invocation. | 🔴 | `test_dependency_rendering.py` |
| 25 | Alpine ownership and load order | Alpine is an external dependency; placing it before component JS can make an `alpine:init` listener miss the event | Citry Events loads and starts its own copy of Alpine. If the page has already loaded Alpine, citry leaves yours running and logs a warning | On pages that use Citry Events, delete your own Alpine `<script>` and stop ordering it against component JS; an `alpine:init` listener will no longer miss the event. Your existing `x-` attributes keep working untouched. | 🔴 | `test_dependency_rendering_e2e.py` |
| 26 | Registry ownership and discovery | Standalone registries, `@register(..., registry=...)`, and global `all_registries()` support custom scopes and process-wide enumeration | Each `Citry` instance owns its registry; classes declare `citry = app` or use `app.register(...)`, and there is no global registry inventory | Create and retain a `Citry` instance for each component scope. Replace decorators with class assignment or `app.register`, and retain any registry/app references your own tooling needs instead of calling `all_registries()`. | 🔴 | `test_registry.py` |
| 27 | Settings scope and component directories | Django's global `COMPONENTS` accepts a dict or `ComponentsSettings`; absent `dirs` defaults to `BASE_DIR/components` | Settings are typed and per `Citry` instance; component directories are explicit absolute `dirs` and no Django `BASE_DIR` is consulted | Move `COMPONENTS` values into `Citry(...)` arguments or `CitrySettings(...)`. Pass every component directory explicitly as an absolute path. | 🔴 | `test_settings.py`, `test_registry.py` |
| 28 | Parser-reserved component names | Protected names follow django-components' registered Django tags and selected formatter | `if`, `elif`, `else`, `for`, `empty`, `raw`, `fill`, and `slot` are citry's own tag names, so no component can use them | Rename a colliding component and update its `<c-*>` uses; for example, rename `Empty` to `EmptyState`. | 🔴 | `test_registry.py` |
| 29 | Choosing the implicit/default slot | A `default` flag can mark an arbitrary named `{% slot "main" default %}` as the target of implicit component-body content | Implicit body content always fills the literal slot name `default`, rendered by a bare `<c-slot />` (or `<c-slot name="default" />`) | Rename the receiving slot to `default`, or keep its name and wrap caller content in an explicit `<c-fill name="main">`. | 🔴 | `test_templatetags_slot_fill.py` |
| 30 | Missing template variables | An absent Django template variable renders as an empty string | A name that is not defined raises `KeyError`, pointing at the line and column where it is used, so a typo fails loudly instead of rendering an empty string | Supply every referenced name, guard the expression/branch, or compute an explicit default in `template_data`. | 🟡 | `test_templatetags_slot_fill.py` |
| 31 | Slot callbacks and forwarding existing Slots | `SlotContext` exposes a Django `Context`, fallback uses `SlotFallback`, and `{% fill body=my_slot %}` forwards a Slot | `SlotContext` exposes `data`, `fallback: Slot \| None`, and `provides`; there is no Django Context or `body=` shortcut | Remove callback reads from `ctx.context`, treat `ctx.fallback` as an ordinary optional Slot, and forward with `<c-fill name="x">{{ my_slot }}</c-fill>`. | 🔴 | `test_slots.py` |
| 32 | Legacy fill fallback alias | `{% fill "x" default="fallback_var" %}` remains as a deprecated alias | Only the explicit `fallback="fallback_var"` attribute is accepted | Rename `default=` to `fallback=` on every fill that binds the receiving slot's fallback. | 🔴 | `test_templatetags_slot_fill.py` |
| 33 | Attribute evaluation (the biggest trap) | An attribute value is evaluated by the template engine, and `{{ }}` interpolates inside a quoted value | A plain attribute value is taken literally: only a `c-`-prefixed attribute is evaluated, and `{{ }}` written into a static value renders **literally** (`class="{{ kind }}"` outputs `class="{{ kind }}"`, with no error) | Add a `c-` prefix to any attribute whose value must be evaluated. `key="hi"` passes the string `"hi"`; `c-key="hi"` evaluates `hi`. Rewrite `class="{{ x }}"` as `c-class="x"`. This one fails silently, so grep your templates for `{{` inside an attribute. | 🔴 | `test_templatetags_provide.py`, `test_expression.py` |
| 34 | The `{% provide %}` tag | `{% provide name key=val var:field=... %}...{% endprovide %}`: a positional `name`, and `var:field=` colon-prefix aggregate kwargs | `<c-provide key="name" ...>...</c-provide>`: the name is the `key` attribute (`c-key` for a computed one). Each `var:field=` group becomes one attribute holding a dict | Rewrite the block as `<c-provide>` and move the positional name to `key=`. Turn each group into one dict attribute: `{% provide "x" var1:key="hi" %}` becomes `<c-provide key="x" c-var1="{'key': 'hi'}">`. | 🟡 | `test_templatetags_provide.py` |
| 35 | Injected payload type | `inject(...)` returns a `DepInject` NamedTuple | `inject(...)` returns a `Provided` NamedTuple | Field access (`payload.field`) and tuple behaviour are unchanged; the only observable difference is the type name in the `repr`. Update any assertion or logging that matches the payload's type name or repr. | 🟡 | `test_templatetags_provide.py` |
| 36 | provide / inject key errors | A missing/empty/invalid provide name raises `TypeError` / `TemplateSyntaxError`; a missing inject key raises `KeyError` | An invalid provide key raises `ValueError`. A missing inject key still raises `KeyError`, now with a suggestion of the closest key that was provided | Update `except` clauses and assertions that match the old exception types or message text. | 🟡 | `test_templatetags_provide.py` |
| 37 | The `{% %}` tag language | Values and bodies may contain any registered block tag, for example `{% lorem n w %}` or a custom tag, including inside a component argument | There is no `{% %}` tag language. Text written that way is not executed; it renders to the page exactly as typed | Compute the value in Python and pass it as an expression attribute (`c-flag="is_active"`), or move the logic into `template_data`. Control flow is `<c-if>` / `<c-for>`. | 🔴 | `test_expression.py` |
| 38 | Parentheses around expressions | Python-expression mode is opt-in per value: `disabled=(not editable)` | A `c-` value is always an expression, so the parentheses are not what makes it one. Keeping them still works | Nothing has to change. When tidying, drop them: `c-disabled="not editable"`. What matters is the `c-` prefix, not the parentheses. | 🟢 | `test_expression.py` |
| 39 | Mixed literal text plus expression in one value | `bool_var=" {% noop is_active %} "` yields the string `" True "`: stray whitespace silently turns a typed value into a string | A `c-` value is one expression, so you get exactly the type the expression returns. (A value holding a whole `<c-*>` tag is a nested component instead, see #42) | Build the string yourself where you want one: `c-label="f' {is_active} '"`. The accidental downgrade cannot happen. | 🟡 | `test_expression.py` |
| 40 | Template comment placement | `{# #}` works anywhere, including inside a component argument, where it collapses to `""` | A comment can sit between tags or between attributes (`<a {# note #} class="x">`), but not inside an attribute value: in a plain attribute it renders as visible text, and in a `c-` attribute it is an error | Move every `{# #}` out of attribute values: put it before the attribute, or on its own line above the tag. `title="{# note #}Hi"` would ship the comment to the browser. | 🟡 | `test_expression.py` |
| 41 | Builtins in expressions | Helpers such as `len` are commonly added to the render context per call | Python builtins are not available inside expressions: `len(...)`, `str(...)` and friends raise `NameError` unless you supply the name yourself | Not a behavior change, but there is a better home for them: register helpers once with `Citry(template_globals={"len": len})` instead of passing them on every render. | 🟢 | `test_expression.py` |
| 42 | Passing markup as an input | A whole `{% component 'card' ... / %}` written inside an argument renders to HTML, and that HTML becomes the outer input | A `c-` value that starts with an HTML tag and ends with its closing tag is a **nested template** rather than an expression: real markup, rendered with the same data, so `{{ }}` works inside it. It is the one place a `c-` value is not a Python expression | Write the markup straight into the value: `c-body="<span>Hello {{ name }}</span>"`. Any HTML works, including several roots (`<em>a</em><em>b</em>`), a self-closing tag (`<br/>`), or a component (`<c-badge c-label='name' />`). Anything else is still an expression, so plain text needs quotes: `c-body="'hello'"`. Write tags complete: a half-open tag is an error. A nested component renders after the outer one, so its finished HTML is not available inside the outer component's `template_data`. | 🟡 | `test_expression.py` |
| 43 | The same input given in both forms | No such concept; there is one argument syntax | Writing `title="x"` and `c-title="y"` on one tag is always a parse-time error because both explicitly provide the same logical input. Plain-element `class`/`c-class` and `style`/`c-style` are the accumulating exceptions. A `c-bind` spread may interlace with one explicit spelling because the key may be absent at render time. Repeating the *same* spelling twice is always an error | Pick one explicit form per input. Preserve intentional class/style accumulation on elements; move conditional overrides into `c-bind`. | 🟡 | `test_expression.py` |
| 44 | Assets on a plain definition class | A non-component base class carrying a `Media` class contributes its entries | Reusable definition bases and plain classes named in `extend` contribute preserved `Dependencies`; relative paths resolve from the declaring module and files are registered to the consuming component | Keep reusable assets on the definition that owns them. Use `Dependencies = None`, `extend = False`, or an explicit `extend` list to cut or select branches. | 🟢 | `test_component_media.py` |
| 45 | Order of inherited JS/CSS | A subclass's `Media` entries come before its parent's, so the parent's CSS wins equal-specificity ties | The parent's entries come first and the subclass's last, so the subclass's CSS wins the tie | Usually nothing: the new order is the one that lets a subclass override its parent's styles. If you relied on the parent winning, restate the parent's rule in the subclass. | 🟡 | `test_component_media.py` |
| 46 | Order of classes named in `extend` | The listed classes' assets merge in reverse order | They merge in the order you wrote them (`extend = [A, B]` gives A's assets before B's) | Only matters when two listed classes ship conflicting styles: if you relied on the reversed order, reverse your list. | 🟡 | `test_component_media.py` |
| 47 | `bytes` asset paths | A `bytes` path in `Media` is accepted | Raises `TypeError` naming the component and the offending value | Decode `bytes` paths to `str` (or use a `pathlib.Path`). The error tells you exactly which component and entry to fix. | 🟡 | `test_component_media.py` |
| 48 | Declaring one member of an asset pair as `None` | Setting `js = ...` while `js_file = None` (or the reverse) raises | Legal: only two values that are both set conflict; the set member is used | Nothing required. If you deleted an explicit `= None` to satisfy djc, you can put it back. | 🟢 | `test_component_media.py` |
| 49 | Protocol-relative asset URLs (`://example.com/x.js`) | The emitted tag escapes the leading colon (`href="%3A//example.com/..."`) | The entry is emitted exactly as written | Nothing for rendered pages. Update only tests that assert the escaped `%3A//` bytes. | 🟢 | `test_component_media.py` |
| 50 | Render lifecycle hooks | Three hooks: `on_render_before`, `on_render` (with a lambda-yield protocol), `on_render_after` | One hook: `on_render(self)`. Return content (or `None` to keep the template), or write it as a generator: code before `yield` runs before the template renders, the `yield` receives the finished result, and code after it can inspect or replace the output | Merge the three bodies into one `on_render`: the before-hook code goes before the `yield`, the after-hook code after it. Each `yield content` replaces the output and receives the new result; errors arrive at the same `yield`. Note the yield hands back a render object, not a string: to append to the output, `return str(result) + "..."`. Code that added template variables in `on_render_before` moves into `template_data`. | 🔴 | `test_component.py` |
| 51 | Inputs named with a leading `@` | `@lol=2` arrives in the component's kwargs like any other input | An `@`-prefixed attribute with a string value is a client-side event instruction (for the events layer); it never reaches the component's inputs, and nothing warns you. A bare `@`-flag or a non-string value fails loudly with a `TypeError` naming the attribute | Rename data inputs that start with `@` (for example `at_lol` or `on_lol`). Audit templates for `@`-prefixed attributes that were meant as data, not events. | 🔴 | `test_component.py` |
| 52 | The render marker attribute | Each rendered root carries `data-djc-id-<id>` | Each rendered root carries `data-cid-<id>=""` (a fresh id per render) | Update CSS selectors, JS lookups, and snapshot assertions that match `data-djc-id-*`. | 🟡 | `test_component.py` |
| 53 | Error paths for components placed via a fill | The error trace includes a slot segment for content rendered through a slot | Content failing inside a fill or fallback still shows a slot segment, as `Card(slot:body)` (djc wrote `provider(slot:content)`). Only a *component* placed via a fill loses the frame: its path is the authorship chain alone (`Page > Failing`) | Update slot-marker assertions to the `Card(slot:body)` spelling, and drop the slot expectation only for component-failure paths. | 🟢 | `test_component.py` |
| 54 | Authoring custom template tags | Subclass `BaseNode` (tag, end_tag, allowed_flags) or decorate a function with `@template_tag`; inputs follow the render function's Python signature | There is no tag-registration API. The one user-defined tag is a registered component: `<c-my-tag />` looks the name up in the registry, and an unknown name fails at render naming the tag | Rewrite each custom tag as a component: the render function's body moves into `template_data` or `on_render`, its parameters become `Kwargs` fields, the tag body arrives as the default slot, and flags convert as in #21. | 🔴 | `test_node.py` |
| 55 | Registry lifecycle extension hooks | `on_registry_created` / `on_registry_deleted` fire when a standalone registry is constructed or collected | There is no standalone registry: it is part of each `Citry` engine, and no such hooks exist | Observe engine creation with `on_extension_created` (its context carries the engine); registry-deletion logic has nothing to attach to, since per-engine state dies with the engine. | 🟡 | `test_extension.py` |
| 56 | `on_component_rendered` when a render fails | Fires once on the failing component itself, with the error message wrapped in the components-path prefix | The failing component's own hook does not fire; each *enclosing* component's hook fires as the error bubbles, receiving the original exception | Move per-component error handling (logging, boundaries) to an ancestor's hook or wrap the component; match the original exception, not the wrapped djc string. | 🟡 | `test_extension.py` |
| 57 | Extension URL routes | Auto-served by Django under `/components/ext/<name>/`, Django path syntax with typed converters (`<int:id>` hands the handler an int) | A framework-neutral route table the host app mounts (via a `citry.contrib` adapter) under `<prefix>/ext/<name>/`; params are `{name}` segments, always captured as strings | Rewrite `<int:id>` as `{id}` and convert inside the handler (`int(id)`); return a `RouteResponse` instead of an `HttpResponse`; mount `Citry.urls` in the host app. | 🔴 | `test_extension.py` |
| 58 | Declaring an extension's per-component config | A nested class named `ComponentConfig` (legacy alias `ExtensionClass` still accepted) | A `Config` class attribute subclassing `Extension.Config`; there is no legacy alias | Rename `ComponentConfig` (or `ExtensionClass`) to `Config` and its base to `Extension.Config`; update hook bodies for the renamed context fields (`ctx.component_class` and friends). | 🔴 | `test_extension.py` |
| 59 | Reading hook-processed assets | `Component.template` / `.js` / `.css` return content with the loaded-hooks applied | The class attributes keep exactly what you wrote; the hook-processed, cached content comes from `get_template().source` / `get_js()` / `get_css()` | Switch introspection and tests that read the class attributes expecting processed content to the accessor methods. | 🟡 | `test_extension.py` |
| 60 | Turning on hot reload | The `reload_on_file_change` setting (`True`/`False`/`"hot"`/`"restart"`/`"off"`) | An explicit call: `enable_hot_reload(engine, mode="hot")` (or `"restart"`); nothing watches until you call it, and there is no `off` value | Delete the setting; call `enable_hot_reload` where your dev server starts. An invalid mode fails at the call, not at settings load. | 🟡 | `test_hotreload.py` |
| 61 | Dropping a component class at runtime | Classes are not registered at definition, and the file index tracks them weakly, so an unregistered class dies with your last reference | Defining a class registers it, and the engine holds it strongly: call `engine.unregister(cls)` before dropping the last reference; render caches then release it normally | Unregister classes you replace at runtime (hot-swap tooling, plugin unload), then drop your own references. A fully rendered class is collectable and its weak file-index entry is pruned. | 🟡 | `test_hotreload.py` |
| 62 | Choosing a component by a variable | `{% component name_var %}` is rejected with "Component name must be a string 'literal', got: ...", steering you to other patterns | A tag name is always literal (`<c-{{ name }}` will not interpolate); the dynamic path is the built-in dynamic component: `<c-component c-is="name_var" />` | Rewrite variable-name calls as `<c-component c-is="..." />`. | 🔴 | `test_templatetags_component.py` |
| 63 | Text next to explicit fills | Text or variables beside `{% fill %}` tags raise `TemplateSyntaxError` when fills are used | Same protection, different reporter: the parent's first render raises `SyntaxError`, worded "Text cannot appear next to '<c-fill>'" for literal text and "Expression cannot appear..." for a variable | Update assertions that match the djc error type or message. | 🟢 | `test_templatetags_component.py` |
| 64 | The `libraries` setting | `COMPONENTS["libraries"]` lists module paths that `import_libraries()` loads at startup | No such setting or helper; component modules are found by scanning `Citry(dirs=...)` or by ordinary imports | Delete the `libraries` entry: move those modules under a scanned directory, or import them plainly where your app starts. | 🔴 | `test_autodiscover.py` |
| 65 | Running autodiscovery | The module-level `autodiscover(map_module=...)` function, anchored to Django apps | An instance method: `app.autodiscover()` (or the default lazy scan on first lookup); no `map_module` hook; paths anchor to `sys.path` | Call `autodiscover()` on your `Citry` instance or rely on the lazy default; delete `map_module` usage. | 🟡 | `test_autodiscover.py` |
| 66 | The `@djc_test` testing harness | Wraps tests to reset djc's process-global state (registries, caches, `sys.modules` snapshots) | No harness ships. Each `Citry` instance owns its registry and caches; the one process-wide piece of state is the default instance, which components fall back to when they do not set `citry=` | Remove `@djc_test`; create a fresh `Citry()` per test and pass it to the components under test (`citry = c`) instead of relying on the default instance. | 🟡 | `test_autodiscover.py` |
| 67 | Data-method names and signatures | Template/JS/CSS data come from `get_template_data(self, args, kwargs, slots, context)` (and `get_js_data`, `get_css_data`) | The methods are `template_data(self, kwargs, slots)`, `js_data(self, kwargs, slots)`, `css_data(self, kwargs, slots)`. A ported component that still defines `get_template_data` renders without any error, but the method is never called: the template sees only the raw kwargs, so the output is silently wrong. | Rename the three methods and drop the `args` and `context` parameters (values read from the Django context become explicit props, `provide`/`inject`, or `template_globals`; see #8 and #20 for those parameters). After porting, grep the project for `def get_template_data`, `def get_js_data`, `def get_css_data`: any hit is a dead method. | 🔴 | `test_component_typing.py` |
| 68 | What a bare typed-input class becomes | A bare inner `Kwargs`/`Slots`/`TemplateData` (etc.) class is rebuilt as a NamedTuple: instances are tuples, so `kwargs[0]`, `a, b = kwargs`, iteration, and `_asdict()`/`_replace()` all work | The same class is rebuilt as a dataclass with fixed attributes: attribute access works, tuple behavior does not (indexing, unpacking, and `_asdict()` raise), and setting an undeclared attribute on an instance also raises | Replace tuple-style access on typed instances with attribute access (or `self.raw_kwargs` for a plain dict). Classes declared with an explicit base (NamedTuple, `@dataclass`, pydantic model) are left untouched by both frameworks, so those need no change. | 🟡 | `test_component_typing.py` |
| 69 | Declaring a no-inputs component | `Kwargs = Empty` (imported from django-components) declares the component takes no inputs; violations raise `TypeError` at render | There is no `Empty` type (the import itself fails). The same contract is an empty `class Kwargs: pass`: a template attribute then fails at parse ("can only have the following attributes ..."), and a Python-call kwarg raises `TypeError` at render | Replace `Kwargs = Empty` with `class Kwargs: pass`, and delete `Args = Empty` entirely (components are kwargs-only, #20). | 🟡 | `test_component_typing.py` |
| 70 | Files with dots in their names in component dirs | Dot-prefixed files and directories are silently skipped during discovery, but other dotted names (a `card.old.py` backup, an `assets.v2/` directory) crash the scan | Any file or directory with a dot in its name (beyond the `.py` suffix) is silently skipped: dot-prefixed junk (`.#card.py` editor locks, `._card.py` macOS copies, `.cache/` trees), backup copies like `card.old.py`, directories with a dotted name (hiding their whole subtree), and symlinks resolving to such paths | Files that crashed djc's scan are now skipped, and every regular file djc discovered is still discovered. One exception: a clean-named symlink pointing at a file inside a dot-prefixed directory was imported by djc but is skipped by citry; point the symlink at a dot-free path or replace it with the real file. If a skipped file should be discovered, rename it to a plain dot-free name. | 🟡 | `test_loader.py` |
| 71 | Declaring default input values | Defaults live in a separate inner `Defaults` class; `Default(...)` wraps a factory for mutable values; `get_component_defaults(MyComponent)` reads the resolved defaults | Defaults are ordinary field defaults on the declared `Kwargs` class (`size: int = 10`); a factory is `dataclasses.field(default_factory=...)`; there is no defaults-reading helper. An inner class still named `Defaults` is silently ignored: nothing errors, the defaults just stop applying (a template reading the value fails with a missing-name error; if a `Kwargs` class is declared, passing the input is rejected as unexpected, and without one the input is simply accepted untyped) | Move each `Defaults` attribute onto the `Kwargs` class as an annotated field: `variable = "test"` becomes `variable: str = "test"`. The annotation is required, an unannotated `name = value` declares nothing. Rewrite `Default(fn)` as `field(default_factory=fn)`, and a mutable default like `items = []` as `field(default_factory=list)` (writing `items: list = []` fails at class definition with "mutable default ... use default_factory"). Replace `get_component_defaults(...)` with `dataclasses.fields(MyComp.Kwargs)`. Then delete the `Defaults` class: leaving it behind fails silently. | 🔴 | `test_component_defaults.py` |
| 72 | Passing `None` to get the default | An input explicitly given as `None` still receives its declared default (`None` is treated as "missing") | `None` is a value like any other: the default applies only when the input is omitted, so a template that used to show the default now shows `None` | Omit the input where you meant "use the default". If a caller may legitimately hold `None`, resolve it yourself in `template_data` (`value if value is not None else fallback`). This changes output silently, so audit call sites that pass `None` on purpose. | 🟡 | `test_component_defaults.py` |
| 73 | Defaults in the raw kwargs dict | `self.raw_kwargs` includes the defaults for inputs the caller omitted | `self.raw_kwargs` holds exactly what the caller passed; defaults appear only on the typed kwargs (the `kwargs` argument of `template_data`). Reading an omitted input from the raw dict raises `KeyError` | Read defaulted inputs through the typed kwargs (`kwargs.size`), not the raw dict. Where code iterates `self.raw_kwargs` expecting the complete set of inputs, switch it to the typed instance. | 🟡 | `test_component_defaults.py` |
| 74 | Delivery of `js_data()` values to the browser | The script carrying `get_js_data()` values is generated, cached, and shipped whenever the component has any JS at all, even a plain script that never reads the data | The `js_data()` script reaches the page only when the component's JS registers a `$component` callback. With a plain script the data is never shipped, and nothing warns. (`css_data()` is unaffected: its stylesheet ships whenever the component has CSS) | JS that consumes `js_data()` values must read them inside a `$component` callback (row #22 shows the shape). After porting, check every component that pairs a plain script with `js_data()`: either convert the script to the callback form or delete the unused `js_data()`. If a test only asserted the data script's presence, drop that assertion for plain-script components. | 🟡 | `test_cache.py` |
| 75 | Where processed component JS/CSS is cached | Processed JS/CSS is written to the Django cache named by the components `cache` setting (a private in-memory cache of its own when unset, never Django's default cache), under `__components:...` keys, as soon as the component class is defined | Each `Citry` instance writes to its own pluggable cache (`Citry(cache=...)`, a per-instance in-memory store by default), under `citry:...` keys, when the component first renders | Multi-worker setups that shared processed assets through a configured Django cache must pass a shared store to `Citry(cache=...)`; ready adapters exist for the Django cache framework (`citry.contrib.django.DjangoCache`), Redis, and diskcache (`citry.contrib.caches`). Update monitoring or warm-up jobs that looked for `__components:*` keys or expected the cache to fill at import time: keys start with `citry:` and appear at first render. | 🟡 | `test_cache.py` |
| 76 | Dynamic components | The dynamic component is a Python class you can import and render directly (`DynamicComponent.render(kwargs={"is": ...})`), registered under the tag name `dynamic`, and renameable with the `dynamic_component_name` setting | The dynamic component is the fixed built-in `<c-component>` tag. There is no importable wrapper class and no rename setting; the tag name cannot be changed | Rewrite `{% component "dynamic" is=x %}` (and any renamed shorthand) as `<c-component c-is="x" />` (row #62 shows the invocation shape). Delete the `dynamic_component_name` setting. In Python, drop the `DynamicComponent` import and resolve the target yourself: `app.get(name)(**kwargs)` when you hold a name, or call the component class you already hold. | 🔴 | `test_component_dynamic.py` |
| 77 | Reserved component names (built-in tags) | Two built-in names are taken at startup, `dynamic` (or your configured rename) and `error_fallback`; registering another component under either raises `AlreadyRegistered` | The built-in tag names `component`, `element`, `provide`, `cache`, `error-fallback`, `js`, and `css` are all reserved. Because a component class auto-registers under its lowercased class name, a class simply named `Element` fails at class definition with `AlreadyRegistered` naming the built-in it collides with | Rename a colliding class (for example `Element` to `ElementView`) or give it an explicit non-reserved `name` attribute, then update its `<c-*>` uses. Row #28 lists the parser tag names reserved for the same reason; this row adds the built-in component names. | 🔴 | `test_component_dynamic.py` |
| 78 | Unknown component name error message | Rendering an unknown component name raises `NotRegistered` with the message "The component 'x' was not found" | Still `NotRegistered`, now worded "No component registered as 'x'." When it is `<c-component>` that cannot resolve the name, the message additionally suggests using `<c-element>` for a plain HTML element | Update except clauses and test assertions that match the old wording; the exception class name is unchanged. Nothing changes for code that only catches the exception type. | 🟢 | `test_component_dynamic.py` |
| 79 | The built-in error boundary component | `{% component "error_fallback" %}` with the guarded content in a `content` slot (also fillable as `default`) and the fallback as a `fallback` slot or kwarg; the `ErrorFallback` class is importable; giving the fallback as both slot and kwarg raises `TemplateSyntaxError` | `<c-error-fallback>`: the guarded content is the tag body; the fallback is the `fallback="..."` attribute, or a `fallback` fill that receives the error as slot data (the guarded content then goes in the `default` fill, since fills cannot mix with other content). There is no importable class. A leftover `<c-fill name="content">` fails on the component's first render, with a parse error naming the fill (the class itself defines without error). Giving both fallback forms raises `RuntimeError` ("give only one") | Rewrite the invocation as `<c-error-fallback>` with the guarded content directly in the body. When you use the fallback fill, rename the `content` fill to `default` and read the error as `d.error`. Delete `ErrorFallback` imports; Python-side, call `app.get("error-fallback")(fallback="...", slots={"default": ...})`. Update any except clause or test that matched `TemplateSyntaxError` or the old both-forms message. | 🔴 | `test_component_error_fallback.py` |
| 80 | Reading mapping and slot-data keys with a dot in expressions | The Django template dot resolves dict keys too: `{{ data.error }}` shows the `error` entry of a dict, and slot data is habitually read that way | Expressions use Python attribute access. Fill data is Citry's immutable `SlotData`, so identifier keys support `{{ d.error }}`; unusual keys and names colliding with mapping methods use brackets or fill destructuring. Ordinary dict values still require subscripts. | Keep dot access for identifier-like slot-data keys. Rewrite dot access only when the value is an ordinary dict, or use brackets/destructuring for an unusual slot-data key such as `aria-label`. Dot access on real object attributes is unchanged. | 🟡 | `test_component_error_fallback.py` |
| 81 | Running component commands | Component commands run through Django: `python manage.py components create\|upgrade\|ext\|list`, carrying Django's global options (`--settings`, `--pythonpath`, `--traceback`, `--no-color`, `--skip-checks`, `-v`) | Installing citry puts a standalone `citry` command on your PATH: `citry list`, `citry inspect --json`, `citry create <name>`, `citry watch`, `citry ext list`, `citry ext run <extension> <command>`, plus `--version`. `inspect --json` emits the successfully loaded engine's versioned runtime component catalog and has no static-analysis fallback. There is no `manage.py` integration and Django's global options do not exist; a project that builds its own `Citry` instance points the CLI at it with a leading `--app module:attribute` (the same convention ASGI/WSGI servers use). The `upgrade` and `startcomponent` commands do not exist: `upgrade` migrated legacy Django-template syntax that citry does not use, and `startcomponent` was djc's deprecated alias of `create` | Replace every `manage.py components ...` invocation in scripts, docs, and CI with the `citry` binary; add `--app your.module:engine` as the first argument if your project constructs its own engine. Remove Django global options from those invocations. Anything that ran `upgrade` has nothing left to migrate; replace `startcomponent X` with `citry create X` (row #82). | 🔴 | command files |
| 82 | The `create` scaffold | `components create X` scaffolds a directory `X/` with `template.html`, `script.js`, `style.css` (and `X.py`), customizable via `--js`/`--css`/`--template`, previewable with `--dry-run`, overwritable with `--force`, chatty with `--verbose` | `citry create MyButton` writes a single `my_button.py` containing the component class with an inline multiline template (no separate HTML/JS/CSS files), takes only `--path`, always prints the created file path, and refuses to touch an existing file; there is no `--force`, `--dry-run`, `--js`/`--css`/`--template`, or `--verbose` | Expect one Python file per scaffold instead of a directory of assets, and drop the removed flags from any wrapper scripts (they now fail with a usage error). To redo a scaffold, delete the file first; the command will never overwrite it for you. | 🟡 | `test_command_create.py` |
| 83 | Listing output and its flags | `components list` prints `full_name` and `path` columns (dotted class path plus source file), and `list` / `ext list` accept `--all`, `--columns`, and `--simple` to add columns, pick columns, or drop the header row | `citry list` prints one row per component: all its registered names (the lowercased and kebab-case forms share the row), the class name, and the file defining the component (relative to the working directory when inside it; a component with no source file leaves the cell empty); `citry ext list` prints the extension names. The columns are fixed and there are no `--all`/`--columns`/`--simple` flags (passing one is a usage error) | Update anything that parses the listing output to the new fixed columns; strip the formatting flags from saved invocations (they now fail with a usage error). | 🟡 | `test_command_list.py`, `test_command_ext.py` |
| 84 | Extensions: authoring CLI commands | An extension declares CLI commands as `ComponentCommand` subclasses; the command's `handle` receives Django's global options (`settings`, `pythonpath`, `skip_checks`, ...) and underscore-prefixed parser internals in its kwargs, which authors had to pop out | The same declarative shape lives on citry's `ExtensionCommand` (imported from `citry`): `name`, `help`, arguments built from `CommandArg`/`CommandArgGroup`, nested subcommands, and a `handle(**kwargs)`. `handle` receives only the options the command tree declares, nothing needs popping, and the engine the CLI resolved is available as `self.citry`. Users run it as `citry ext run <extension> <command>` | Rebase command classes onto citry's `ExtensionCommand` and update the imports (`CommandArg`/`CommandArgGroup` keep their argparse-matching fields). Delete any code that pops parser internals or reads Django global options from kwargs; reach the engine through `self.citry` instead of Django settings. | 🔴 | `test_command_ext.py` |
| 85 | Browser dependency-manager namespace | The runtime exposes `DjangoComponents`, the legacy `Components` alias, `createComponentsManager()`, and `registerComponentData(..., factory)` | One load-safe singleton lives at `globalThis.Citry.manager`; there are no django-components aliases or manager factory, and `registerComponentData` takes the data value itself | Replace both old globals with `Citry.manager`, delete calls that construct private managers, and pass the JS-data object rather than a factory when registering data manually. | 🔴 | `test_dependency_manager_e2e.py` |
| 86 | Component initialization completion and failures | `callComponent()` returns a Promise for the callback's synchronous or asynchronous result; callback errors reject it | `callComponent()` is synchronous fire-and-forget and returns `undefined`. A returned function is the instance cleanup; other values are ignored. Returned Promises are unsupported, and synchronous throws or Promise rejections are logged and isolated so later initialization continues | Move asynchronous server work to an Events handler and await the client `sendEvent()` promise. Keep `$component` initialization synchronous, return only an optional cleanup function, and do not await `callComponent()` or use callback return values as results. | 🔴 | `test_dependency_manager_e2e.py` |
| 87 | Component initialization with no DOM roots | A component call rejects when no element carries its instance marker | The callback still runs with `els=[]`; rootless components and temporarily absent roots are valid lifecycle states | Handle an empty `els` array when initialization needs a root. Do not use rejection from `callComponent()` as a missing-root signal. | 🟡 | `test_dependency_manager_e2e.py` |
| 88 | Component HTTP handlers and their `self` | `Component.as_view()` dispatches `get` / `post` either from `Component.View` or directly from the component, and the handler can use a live component instance plus `render_to_response(context=..., slots=...)` | Put verb-shaped handlers in `class Events(ViewEvents):`. Their inputs are typed `data` and the neutral `request`; `self` is the per-call Events config, not a rendered component. Return a fresh component element or an Events action | Move each direct or nested view handler under `Events(ViewEvents)`, replace host request parsing with a data class, and replace `render_to_response` with a returned component or action. Move values formerly read from the live component into explicit data, context, State, or application services. | 🔴 | `test_component_view.py` |
| 89 | Component endpoint URLs and exposure | `get_component_url()` builds one optional public URL per component, `public=False` disables it, and `get_route_path()` plus `args` / `kwargs` define custom paths | Public methods placed in `Events` are exposed on fixed routes. Named handlers use `events.url(name, query=..., fragment=...)` or `get_event_url(...)`; there is no `public` flag or custom per-component route reversal, and the method-only ViewEvents route has no dedicated public builder | Replace public flags with handler placement or omission. Use named handlers and the event URL builders for durable call sites; keep query and fragment inputs, but move route parameters into typed event data. Treat `ViewEvents` as the initial method-shaped bridge, not a custom routing API. | 🔴 | `test_component_view.py` |
| 90 | Component-class deletion extension hook | `on_component_class_deleted(ctx)` receives `OnComponentClassDeletedContext` from a class finalizer | Citry exposes neither the hook nor the context because Python can run finalizers while arbitrary application locks are held | Move explicit-removal cleanup to `on_component_unregistered`. Use weak containers for memory-only indexes that should disappear with an unregistered class. `Citry.clear()` is a bulk teardown and emits no per-component hooks. | 🔴 | `test_extension.py` |
| 91 | Selecting a render-cache backend per component | `Component.Cache.cache_name` selects one named Django cache backend | A `Citry` instance owns one cache backend; component and fragment output caching use it | Pass the intended shared or local backend once as `Citry(cache=...)`. Split components across Citry instances only when they truly require different engine ownership; there is no per-component backend alias in V1. | 🟡 | `test_component_cache.py`, `test_django_cache_tag.py` |
| 92 | Component cache key customization and Slots | `Cache.hash()` can replace key generation, while `include_slots` attempts to add Slot values automatically | `Cache.vary(self, kwargs, slots)` returns typed semantic variation and Citry owns canonical hashing. Every content-producing Slot requires an explicit variation; Citry never guesses from closures or source text | Replace `hash()` and `include_slots` with a `vary()` result containing only the values that can change output, including explicit Slot-presence or caller-controlled dimensions where relevant. | 🔴 | `test_component_cache.py` |
| 93 | Template fragment cache syntax | Django's `{% cache timeout key *vary_on using=... %}...{% endcache %}` can run in a standalone Django template | Citry uses the transparent component `<c-cache key="..." c-ttl="..." c-vary="...">...</c-cache>` inside a component template, with the engine-owned backend | Move standalone cached markup into a root component template, translate timeout and variation to typed attributes, and remove `{% load cache %}` / `using=`. | 🔴 | `test_django_cache_tag.py` |
| 94 | IDs inside cached rendered output | Django's fragment cache reuses frozen rendered HTML, including the original component ID | Citry caches a detached artifact and mints fresh descendant IDs on every replay while reusing only the current boundary ID | Do not persist or compare a descendant `data-cid-*` across renders. Bind browser state to the current render; Citry remaps ownership, dependency, and Events records to those fresh IDs. | 🟡 | `test_django_cache_tag.py` |

New rows are appended as triage proceeds; keep them numbered so the eventual
guide can link to a stable id.

## `vendor_djc_reference.sh`

```sh
#!/usr/bin/env bash
#
# Vendor the django-components reference snapshots used during the citry
# migration. These snapshots are gitignored (they are a large third-party
# copy); this script is the tracked, reproducible record of WHAT was vendored
# and from WHERE.
#
# Two snapshots are produced under packages/py/citry/ :
#   _djc_reference/             <- upstream src/django_components/ (engine source)
#   _djc_reference_docs_site/   <- upstream docs_site/ (the docs-site port basis)
#
# The engine snapshot is cited by file:line across docs/design/*.md, so its
# contents must be reproducible. Re-running this script against the pinned
# commit reproduces the exact snapshot the design docs were written against.
# The completed test migration records pinned upstream test links directly in
# docs/design/migration_djc_tests.md; it no longer keeps a local test copy.
#
# Usage:
#   scripts/vendor_djc_reference.sh [path-to-django-components-checkout]
#
# Default checkout path is $DJC_CHECKOUT or /Users/mac/repos/django-components.

set -euo pipefail

# --- Provenance -------------------------------------------------------------
# Upstream: https://github.com/django-components/django-components
# Branch at vendor time: jo-docs-mkdocs-migrate (PR #1664, the docs-site work)
# Pinned commit:
DJC_COMMIT="5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75"  # 2026-06-20
# When PR #1664 merges to master, re-pin this to the merge commit on master.

CHECKOUT="${1:-${DJC_CHECKOUT:-/Users/mac/repos/django-components}}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$REPO_ROOT/packages/py/citry"

if [[ ! -d "$CHECKOUT/.git" ]]; then
  echo "error: '$CHECKOUT' is not a git checkout. Clone django-components there," >&2
  echo "       or pass the path / set DJC_CHECKOUT." >&2
  exit 1
fi

have="$(git -C "$CHECKOUT" rev-parse HEAD)"
if [[ "$have" != "$DJC_COMMIT" ]]; then
  echo "warning: checkout is at $have, expected pinned $DJC_COMMIT." >&2
  echo "         Run: git -C '$CHECKOUT' fetch && git -C '$CHECKOUT' checkout $DJC_COMMIT" >&2
  echo "         Continuing anyway (Ctrl-C to abort)..." >&2
fi

# Excludes: generated output and the 1 GB versions/ history are not part of the
# reference (they are regenerated by the citry builder, not ported from).
COMMON_EXCLUDES=(--exclude='__pycache__/' --exclude='*.pyc'
                 --exclude='.pytest_cache/' --exclude='.ruff_cache/'
                 --exclude='.mypy_cache/')

echo "Vendoring engine source -> _djc_reference/"
rsync -a --delete "${COMMON_EXCLUDES[@]}" \
  "$CHECKOUT/src/django_components/" "$DST/_djc_reference/"

echo "Vendoring docs site     -> _djc_reference_docs_site/"
# versions/ is 1 GB of built HTML history; staticfiles/ is collectstatic output;
# .cache/ is the generated OpenGraph social-card image cache. All regenerated,
# none are part of the source to port from.
rsync -a --delete "${COMMON_EXCLUDES[@]}" \
  --exclude='versions/' --exclude='staticfiles/' --exclude='.cache/' \
  "$CHECKOUT/docs_site/" "$DST/_djc_reference_docs_site/"

echo "Done. Engine: $(find "$DST/_djc_reference" -name '*.py' | wc -l | tr -d ' ') py files."
echo "      Docs:   $(du -sh "$DST/_djc_reference_docs_site" | cut -f1) (versions/ excluded)."
```