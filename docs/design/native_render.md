# Design: the native render path

Citry renders a page with a lot of `simple = "vue"` rows (one component
placed hundreds of times by a `<c-for>` loop) faster on standard CPython
by doing part of each row's work in Rust. The output is the same, byte
for byte, and the user's callbacks run in the same order and the same
number of times. This document says what the Rust code does, when Citry
uses it, and what happens when it meets an input it cannot handle.

The work ships in levels, one pull request each. This document describes
the levels that have shipped:

| Level | What Rust does |
|---|---|
| A | Reads each `simple = "vue"` row, checks its values and writes its prepared data as JSON; computes the two ids of every row of a call run |

Terms used below:

- **Row**: one occurrence of a `simple = "vue"` component. It renders
  without a Python component object.
- **Call run**: the components one `<c-for>` places at one call site,
  whether `simple = "vue"` rows or ordinary components. Assembly names
  each of them with two SHA-256 ids, its placement key and its child
  occurrence id.
- **Assembly**: the step (`assemble_typed_render` in
  `citry/_vue/direct_capture.py`) that turns a finished render into the
  manifest's occurrences and component definitions.
- **Prepared data**: the values a row sends to its Vue instance in the
  page's manifest (the JSON block the browser reads).
- **Leaf**: the Python object (`PreparedLeafProgram`) that holds a row's
  recorded template values.
- **Decline**: Rust returns `None` instead of a result, and Python then
  handles that row the way it always has.
- **Rebuild**: Python builds a Rust-read row's leaf by running its
  evaluator over a copy of the values Rust read, when an output needs the
  row's HTML or a Python copy of its data.
- **The precompile path**: when no browser hook can change the components
  the page sends to the browser, serialize runs assembly before writing
  the page (`precompile_selected_tree_for_serialization` in
  `citry/_vue/events.py`).

The research that measured these levels is on the branch
`research/rust-render-stage0` (tag `research/rust-render-stage2-done`),
including its notes in `docs/design/rust_rendering_exploration.md` and its
timing harness. Nothing here depends on it.

## 1. What happens to one row

Without Rust, each row runs its data callbacks (`template_data`,
`js_data`, `css_data`), then a Python function generated from its
template (the evaluator) checks that every value the template reads is
plain data (the read-set check) and records the template's values. Serialize later copies
those values into the manifest and writes them as JSON.

With level A:

1. The callbacks run exactly as before.
2. If the row calls no child components and its `js_data` and `css_data`
   are empty, Citry asks Rust to read it
   (`LeafProgramNode.read_native_row`). Rust applies the same checks as
   the Python evaluator, copies every value the template reads, evaluates
   the template over the copy and writes the row's prepared data as JSON.
3. If Rust declines, the Python evaluator runs on the same variables, so
   any error is the one Python has always raised, after the same
   callbacks.
4. The row's record (`SimpleVueRecord`) holds the Rust row
   (`native`) and no Python leaf. Code that only needs to know whether the
   row called children, its template fragment or its Vue errors reads the
   record's properties, which answer without a leaf. Reading `leaf`
   rebuilds it once.
5. On the precompile path, assembly records the row's occurrence without
   copying any of its values (`native_rows=True` in
   `assemble_typed_render`), and the manifest writer
   (`_manifest_json` in `citry/_vue/serialization.py`) asks Rust to write
   the occurrence list with each Rust row's JSON in place. Every other
   caller of assembly, including Events updates, rebuilds the row's leaf.

Rust also computes the two ids of each row of every call run, for
ordinary components too, from the same leading JSON text Python's
`_DigestPrefix` hashes. A key with no UTF-8 form (a lone surrogate) gets
its ids from Python, inside a run whose other ids come from Rust.

Python owns every rule. Rust receives the template's operations and the
paths it reads as plain tuples built from the same structures the Python
evaluator is built from (`native_row_plan_tuples` in
`citry/_vue/leaf_program.py`), asks Python through a callback for the
layout of each new root `c-bind` key set (how its keys merge with the
element's own attributes), and is told the size of
Python's layout cache. Nothing in the Rust crate copies a Python
constant.

## 2. When Rust runs

`citry/_vue/native_render.py` decides once, when it is first imported:

- `SUPPORTED` is true on CPython built with the GIL, outside Pyodide,
  when the installed `citry-core` has every name the native path calls.
  It never changes. Template nodes build their Rust plans only when it is
  true.
- `ACTIVE` is `SUPPORTED`, unless the environment variable
  `CITRY_NATIVE_RENDER` is `0`. Each call site reads it when it runs.

| Situation | Result |
|---|---|
| PyPy | Python path, no warning. PyPy reads every object through a slow emulation layer, so Rust would lose there. |
| Pyodide (`sys.platform == "emscripten"`) | Python path, no warning. |
| Free-threaded CPython (`Py_GIL_DISABLED` set at build time) | Python path, no warning. Rust reads dicts and lists without locking them, which is safe only under the GIL. The check reads the build setting, so it holds even when importing an extension turned the GIL back on. |
| CPython with `citry_core._rust.native_render` missing or older | Python path and one `RuntimeWarning` naming the missing name. citry pins citry-core exactly, so this means an inconsistent install or a stale development build. |
| `CITRY_NATIVE_RENDER=0` | Python path, no warning. This is the workaround for a bug only the Rust path has. |
| `CITRY_NATIVE_RENDER` set to anything but `0` or `1` | One `RuntimeWarning`; the value is ignored. |
| The component's `Citry` instance has `mode="development"` | Rows are not read in Rust. A development page checks every element id it writes, so the serializer needs every row's HTML, and reading the row in Rust first would only add work. The check runs at the row read, because mode belongs to each `Citry` instance. Call-run ids still come from Rust; they need no rebuild. |

Every step after a Rust object exists follows that object (`record.native`,
`PreparedOccurrence._native`), not the flag, so a render serializes
correctly even if the flag changed in between. The Rust module stays
declared as needing the GIL (`#[pymodule(gil_used = true)]` in
`crates/citry_core_py/src/lib.rs`).

## 3. Rows rebuilt in Python

A page Vue hydrates, or one it mounts in the browser (`ssr=False`),
writes a Rust-read row from its JSON alone, as long as the serializer
leaves out the root's body (`_can_skip_vue_document_body` in
`citry/serialize.py`). When it cannot, it writes every frame of the body,
so every Rust-read row on the page, in a child component or in the root
template, is rebuilt once. The serializer keeps the body for:

- static HTML, fragments and pages that decline hydration, which need the
  rows' HTML anyway;
- a root template that is not one `<html><head><body>` document;
- any CSP mode other than `"off"`, or a nonce;
- a JavaScript or script-integrity policy;
- a `deps_position` other than `"smart"`;
- an `on_serialize` hook other than the built-in one;
- a placeholder or trusted HTML value written directly in the root body,
  or a child component whose root marker is not one of Citry's own
  (`data-cid-*`, `data-citry*`).

Two other cases rebuild each row for its data rather than its HTML:
Events update responses, and pages kept off the precompile path (a custom
component tag callback or a browser hook). Their assembly copies each
row's values from its leaf.

A row's leaf is built at most once per render, so serializing the same
render as several outputs rebuilds each row once.

## 4. Error modes

| Input or event | What happens |
|---|---|
| A row value that is not plain data (a `dict` subclass, `Markup`, a `Secret`, a tuple where Python checks a list), NaN or infinity, an int outside the 64-bit range, a str with a lone surrogate, a row variable named like a loop target | Rust declines; the Python evaluator renders the row or raises its own error. |
| A root `c-bind` key set Python merges per row (an event handler or `style` attribute, names that differ only in case), a key that is not a str, or more key sets than Python's layout cache holds | Rust declines that row. |
| The layout callback raises | Rust declines; Python's own path calls the same function and raises there with the template position. |
| User code raises while Rust looks a value up (a dict key's `__eq__`) | Raised inside a value, Rust declines and Python's evaluator meets the same error; raised while looking up a template variable itself, the error propagates from the read, as Python's check would raise it. |
| A template shape Rust does not evaluate (a child call, a literal outside `None`, `bool` and `str`, a data key named `calls`) | No plan is built; every row of the template stays in Python. |
| Building the plan raises anything but `ValueError` | The error propagates and nothing is cached, so every render fails loudly; `CITRY_NATIVE_RENDER=0` works around it. |
| A call-run key with no UTF-8 form | Python computes that row's ids. |
| A `str` subclass render id | Written from its text, as `json.dumps` does. |
| `ComponentLike.register(...)` or a lower `sys.set_int_max_str_digits` between render and serialize | A rebuild skips the read-set check and Rust only copies ints inside the 64-bit range, so values the render accepted stay accepted. |
| A row's dicts changed after the render | The output keeps the values each row had when Rust read it, as the Python leaf does. |
| A Rust panic | `RuntimeError` through `without_panics`; a panic during the row read fails the render with Citry's component path in the message. Rust's panic hook also prints the message to stderr. |
| The occurrence list holds an item assembly never makes for a Rust row | `ValueError` from `_encode_occurrences`; this is a Citry bug, never user input. |

Accepted differences, none of which changes output:

- A user dict key whose hash equals a template variable's name sees fewer
  `__eq__` calls, because Rust looks each variable up once.
- A row's call-run component tag is looked up once per class per
  assembly instead of once per row. The precompile path accepts only the
  built-in tag callback, which gives the same answer for every row.
- A Rust-read row's record and occurrence carry private fields
  (`native`, `_leaf_node`, `_native`) that are not part of their
  equality.

## 5. Where the code lives

| Piece | File |
|---|---|
| The pure-Rust plan, value copy, evaluation, JSON writer and digests | `crates/citry_native_render/` |
| The PyO3 classes `_RowPlan`, `_NativeRow`, `_RunDigests` and `_encode_occurrences` | `crates/citry_core_py/src/native_render/` |
| Their type stub | `class native_render` in `packages/py/citry_core/citry_core/_rust.pyi` |
| The decision | `citry/_vue/native_render.py` |
| The plan tuples, the row read and the rebuild | `citry/_vue/leaf_program.py` |
| The row read's call site | `_render_simple_vue_leaf` in `citry/component_render.py` |
| The record properties | `SimpleVueRecord` in `citry/citry_render.py` |
| Assembly (`start_occurrence`, `native_definition`, `register_native_member`, the call-run ids) | `citry/_vue/direct_capture.py` |
| The manifest writer | `_manifest_json` in `citry/_vue/serialization.py` |

## 6. Testing both paths

- `tests/_render_paths.py` has `render_both(run)`, which calls `run` on
  each path in one process, pins render ids, the Vue app id and the
  Events token clock, compares the results, and counts the rows Rust read
  and the rows Python rebuilt, so a case cannot pass because both
  runs took the Python path.
- The `render_path` fixture runs a test once per path; `python_render_path`
  forces the Python path for a test that checks the Python evaluator's own
  internals. Both live in `packages/py/citry/tests/conftest.py`.
- `pytest --python-render-path` runs a whole session on the Python path,
  except the tests that ask for `render_path` or call `render_both`,
  which still run both.
  The ubuntu / Python 3.10 cell of `py--tests.yml` uses it, because no CI
  job runs the suite on PyPy, Pyodide or free-threaded builds.
- `tests/test_call_run_order.py` locks the order of user callbacks and
  extension hooks, and runs on both paths.
- The Rust crate's tests compare against fixtures that
  `scripts/native_render_fixtures.py` writes from the Python code;
  `--check` (run by a Python test) fails when a fixture no longer matches.

## 7. Adding a level

A new level follows the same rules:

1. Python owns every rule. Pass a Python constant or callback into Rust;
   never copy it.
2. When Rust cannot reproduce an input exactly, decline and let Python
   handle it, so the error and its timing are Python's own.
3. Read `native_render.ACTIVE` at the call site, build plans from
   `SUPPORTED`, and after that follow the Rust object, not the flag.
4. Add a `render_both` case with expected counts, so a silent decline
   cannot pass, and keep `tests/test_call_run_order.py` passing on both
   paths.
5. Add each new name to `_REQUIRED_NAMES`, the stub and this document.
