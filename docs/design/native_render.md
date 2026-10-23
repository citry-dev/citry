# Design: the native render path

Citry renders a page with a lot of `simple = "vue"` rows (one component
placed hundreds of times by a `<c-for>` loop) faster on standard CPython
by doing part of each row's work in Rust. The output is the same, byte
for byte, and the user's callbacks run in the same order and the same
number of times. This document says what the Rust code does, when Citry
uses it, and what happens when it meets an input it cannot handle.

The work ships in levels, one pull request each. This document describes
the levels that have shipped:

| Level | What it does |
|---|---|
| A | Rust reads each `simple = "vue"` row, checks its values and writes its prepared data as JSON; it also computes the two ids of every row of a call run |
| B1 | When Rust read every row of a call run, one Rust object records the whole run during serialize and writes its rows' manifest items |
| C1 | The render queue renders the rows of a `<c-for>` loop in one task, in the order one task per row would. This level is Python only and runs on every interpreter, with or without Rust |

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
  handles that row or call run the way it always has.
- **Rebuild**: Python builds a Rust-read row's leaf by running its
  evaluator over a copy of the values Rust read, when an output needs the
  row's HTML or a Python copy of its data.
- **The precompile path**: when no browser hook can change the components
  the page sends to the browser, serialize runs assembly before writing
  the page (`precompile_selected_tree_for_serialization` in
  `citry/_vue/events.py`).
- **Run object**: one Rust object (`_NativeRun`) that records every row of
  a call run in assembly, in place of one Python record per row (level B1).
- **Render queue**: the loop in `_settle_render`
  (`citry/component_render.py`) that renders each deferred child
  component after its parent's template has run. It keeps its tasks on a
  stack and always runs the top one next, so a task pushed under another
  runs after it (see
  [`component_rendering_defer.md`](component_rendering_defer.md)).
- **Parts list**: the `parts` of a `CitryRender`, the list of pieces a
  template rendered. A loop's parts list holds one entry per row until
  the render queue puts each row's record in its place.
- **Run task**: the one render-queue task (`_RunTask`) that renders the
  rows of a call run in order (level C1).

The research that measured these levels is on the branch
`research/rust-render-stage0` (tag `research/rust-render-stage2-done`),
including its notes in `docs/design/rust_rendering_exploration.md` and its
timing harness. Nothing here depends on it.

## 1. What happens to one row

Without Rust, each row runs its data callbacks (`template_data`,
`js_data`, `css_data`), then a Python function generated from its
template (the evaluator) checks that every value the template reads is
plain data (the read-set check) and records the template's values.
Serialize later copies those values into the manifest and writes them as
JSON.

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

Python passes Rust every rule it can. Rust receives the template's
operations and the paths it reads as plain tuples built from the same
structures the Python evaluator is built from (`native_row_plan_tuples` in
`citry/_vue/leaf_program.py`), asks Python through a callback for the
layout of each new root `c-bind` key set (how its keys merge with the
element's own attributes), and is told the size of
Python's layout cache and the largest int an attribute sends as a number.
The fixed text of the manifest format (the `"calls"` key, the
`"explicit"` id tag) and the value rules (how a text or attribute value
is written) are locked by fixtures that `scripts/native_render_fixtures.py`
writes from Python.

## 2. What happens to one call run

Assembly names and records each row of a call run in a Python loop
(`run_members` in `citry/_vue/direct_capture.py`, "the per-row loop"
below): it computes the row's two ids, checks them against what assembly
has already seen, writes the row into about a dozen sets and maps, and
records one occurrence. For a run of rows Rust read, that work is the
same for every row.

With level B1, on the precompile path only:

1. Before the per-row loop, `take_native_run` checks what depends only on
   the class, once per run: the registry lookup, the component tag, and
   that the class is the one registered for this engine and not the
   built-in `mark` component. It then asks Rust for a run object
   (`_NativeRun.try_new`). Rust reads every row's record, checks that level
   A would record each row through `register_native_member` (a Rust-read
   row with no `js_data` and no root markers) and that every row shares the
   first row's class, template fragment and call site, and computes both
   ids of each row. It changes nothing in assembly.
2. `commit` checks every row against assembly's live state (the render ids
   and occurrence ids already seen, the keys already used at this call
   site, fills addressed to a row), and only when every row passes writes
   the rows into the maps, in row order.
3. Assembly then registers the rows' definition, at the point where the
   per-row loop would first register it, and adds the run's rows to the
   call site's count in one step (a later ordinary call at the same call
   site under the same owner reads that count). The order in which
   definitions are first registered is the order the manifest lists them
   in, so assembly registers the definition only once the run object has
   committed.
4. One entry in assembly's occurrence list stands for every row of the
   run. After the whole tree, `check_invariants` makes the run's share of
   the final checks: no other call references a row, and no other
   occurrence shares a row's parent and placement key. The view then lists
   one `_NativeOccurrence` per row, where the per-row loop would have put
   each row's occurrence.
5. The manifest's occurrence list holds the run object once, at its first
   row's place, and `_encode_occurrences` writes each of its rows' items
   from Rust, with the compiled definition id serialize passes in
   (`_PreparedResult.run_definition_ids`).

If `try_new` declines or `commit` refuses, the per-row loop records the
whole run, exactly as it does without level B1, and raises any error at
the row it belongs to. So every error message stays Python's.

Between them, `commit` and `take_native_run` write every entry the per-row
loop writes, except in three maps. `reference_parents` is covered by
`check_invariants`. `native_occurrences` is not needed, because each
`_NativeOccurrence` carries its `_NativeRow`. `prepared_by_occurrence` is
read only for the occurrence `transform_component` is building and for
occurrences that own calls, fills or markers, and a run row is none of
these; it is a plain dict, so a reader that looked one up would raise
`KeyError` rather than read a wrong value.

Code that reads the view or the manifest handles the run objects:
`prepared_manifest` checks each run's definition once for opaque HTML
(a row Rust read writes none), the Events preparation skips run objects in
its opaque HTML and `renderId` loops (no Events instance can be a
`simple = "vue"` row; one that matched would raise `AssertionError`), and
serialize reads a run's `type_key` for its component tags. A
`_NativeOccurrence` has the attributes an occurrence's readers use, and
its `server_data` and `prepared_data` are read-only mappings shared by
every row, so a reader that tried to change them would fail at once.

## 3. One task per call run

Each deferred component normally gets its own render-queue task. A loop
of hundreds of `simple = "vue"` rows then builds a `CitryElement` and a
`DeferredComponent` per row while the parent's template runs, and the
queue later pops one task per row. Each task checks the depth, sets the
row's execution frame (the slot fill or nested template Citry was
rendering when it reached the row; Citry uses it to link any slot the
row's callbacks call), runs the admission checks (the per-class checks
that decide whether a row can render without a component object) and the
row's callbacks (`_render_simple_vue_leaf`), and puts the row's record in
its place. Level C1 gives the loop's rows one task instead, which does
the same work for every row, in the same order:

1. Before the loop runs, `ForNode._call_run_class` checks that the loop
   can record its rows as one run. These are the checks `ForNode.render`
   makes after the loop to treat it as a call run (the render is a Vue
   render, the loop has no `<c-empty>` branch, its body is one keyed
   component call with no body, no browser bindings and no special input
   keys, and the class is registered, not transparent and not a dynamic
   selector),
   plus three more: the class is `simple = "vue"`, the call's inputs are
   plain, and its metadata does not target an element. The checks after
   the loop still run and decide whether the loop's output is marked as a
   call run.
2. The loop walk (`ForNode._render_call_run`) makes each row's template
   steps in their usual order and records the row's kwargs and call
   metadata in one `_DeferredRun`, without building its element. Each
   row's position in the parts list gets its own small `_DeferredRunRow`,
   so code that sees the list still finds one object per row. A row whose
   looked-up class no longer fits the run (another class under the name,
   or one that became a dynamic selector) or whose execution frame
   differs gets its own
   deferred component and its own task, as in a loop that is not a run,
   and so does every later row of the loop.
3. When the queue scans a parts list (`_scan_deferred_parts`), rows of
   one run that sit next to each other get one `_RunTask`. One task per
   row would put their tasks next to each other on the stack, so one task
   that renders them in list order does the same. If an extension hook
   or user code reordered, dropped or repeated entries, the scan sees that
   list, so the same rows render in the same order. A list scanned again
   later gets tasks only for the rows still in it.
4. `_run_rows` renders the task's rows in order. For each row it makes the
   depth check a row's own task makes, sets the row's execution frame,
   repeats the admission checks that can change between rows
   (`_run_row`), and then runs the same steps as `_render_simple_vue_leaf`
   (both call `_simple_vue_record`, where level A's row read happens). It
   puts each record at its row's position.
5. Four things stop the task early at row k:

| The task stops at row k when | The queue then |
|---|---|
| Row k sits deeper than `max_component_depth` | Raises the nesting-depth error, which no `on_render` boundary can catch |
| Row k's checks choose the ordinary component path (for example the i18n extension needs it) | Builds row k's `DeferredComponent`, renders it as an ordinary component, and pushes a run task for the remaining rows under it |
| Row k called child components | Pushes a run task for the remaining rows, with the children's tasks on top, so they render before row k+1 |
| Row k's position is gone from the parts list | Raises the `RuntimeError` a row's own task raises then. Row k's callbacks have already run, and no `on_render` boundary can catch it |

The order of every user callback and extension hook is the same as with
one task per row. `tests/test_call_run_order.py` locks it on both paths.

## 4. When Rust runs

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
`PreparedOccurrence._native`, a `_NativeRun` in the manifest), not the
flag, so a render serializes correctly even if the flag changed in
between. Level B1 reads the flag once per call run, when assembly decides
whether to ask for a run object; with the flag off, the per-row loop
records the run's Rust-read rows as level A does. The Rust module stays
declared as needing the GIL (`#[pymodule(gil_used = true)]` in
`crates/citry_core_py/src/lib.rs`).

Level C1 does not read these flags. It runs on every interpreter; on the
Python path its run task runs the Python evaluator for each row, as a
row's own task does. So every interpreter has one render queue to test.

## 5. Rows rebuilt in Python

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

## 6. Error modes

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
| A call run holds an ordinary component or a row Python evaluated, a row with `js_data` or root markers, another class, class id, fragment, source or span, a key or render id that is not an exact `str` with a UTF-8 form, or a repeated key, render id or child id | `try_new` declines before assembly changes; the per-row loop records the run and raises its own error for any of these that Python refuses. |
| A row's render id or occurrence id was already seen, its key was already used at this call site under the same owner (another run of the same loop), or fills are addressed to it | `commit` refuses and writes nothing. The per-row loop then records the run: it raises the same `UnsupportedPreparedView` for an id or key already used, and writes one call per row when fills are addressed to a row. |
| The final check fails for a run row | `check_invariants` names the row and the check; assembly raises the message the per-row check raises. Reaching it from a page needs two ids whose SHA-256 digests share their first 24 hex digits. |
| The registry lookup or the tag lookup raises | The run is declined; the per-row loop makes the same lookup and raises there. |
| A manifest with a run object reaches `_encode_occurrences` without the compiled definition ids, or a run's rows are not next to each other in the view | `ValueError` or `AssertionError`; both are Citry bugs, never user input. |
| Events updates, pages kept off the precompile path, and development mode | No run object; the per-row loop records every run, as for level A's rows. Development mode reads no row in Rust, so its runs never qualify. |

Accepted differences, none of which changes output:

- A user dict key whose hash equals a template variable's name sees fewer
  `__eq__` calls, because Rust looks each variable up once.
- A row's call-run component tag is looked up once per class per
  assembly instead of once per row. The precompile path accepts only the
  built-in tag callback, which gives the same answer for every row.
- A Rust-read row's record and occurrence carry private fields
  (`native`, `_leaf_node`, `_native`) that are not part of their
  equality. A record still compares its leaf, which a Rust-read record
  builds on first read, so its equality to a copy can change then.
  Nothing in Citry compares records.
- Assembly looks up a call run's component tag once per class, not once
  per row, so it also checks only once whether that class was replaced. If
  another thread replaces the class while serialize runs, the later check
  that the class is still registered fails instead, with a different
  message.
- With a run object, the registry lookup that checks a row's class runs
  once per run instead of once per row, with the same thread consequence.
- Serialize asks the component tag callback for a run's class once per run
  instead of once per row when the built-in metadata has no tag for it. The
  answer is the same for every row, so no output can show it.

Level C1 adds these error modes. Every error a row raises is the one its
own task raises, with the same message, component path and chain of
causes:

| Input or event | What happens |
|---|---|
| A row's callback, `Kwargs` construction or id generator raises, or the id is invalid | The run task stops at that row; the error carries the row's component path and reaches the nearest `on_render` boundary, and later rows do not run, as with one task per row. |
| `KeyboardInterrupt` or another `BaseException` in a row | It propagates unchanged, with no component path; the row's execution frame is reset first. |
| A row sits deeper than `max_component_depth`, including after an earlier row lowered the limit | The nesting-depth error ends the render; no `on_render` boundary can swallow it. |
| A row's callback changes what later rows do (registers a component with messages, makes the class transparent or makes it fail admission, unregisters it, replaces the id generator) | Each row repeats the admission checks that can change, so later rows take the ordinary path or raise the rejection they raise with one task per row. |
| A row's class is replaced under its name, or becomes a dynamic selector, while the loop walks | That row and every later row get their own deferred components and tasks. Rows already in the run raise the call-shape rejection when they render, before their callbacks, as their own tasks would. |
| An extension hook or user code reorders, drops or repeats a loop's unplaced rows | The same rows render in the same order as with one task per row. |
| An extension hook or user code removes a row's position after the scan | The `RuntimeError` a row's own task raises in that case. |
| A list of rows is printed again after some rows were placed | The later scan gives the rows still unplaced their own task, which renders them. The earlier task then renders its next row again and raises the position-gone `RuntimeError`, as with one task per row. |

Accepted differences, none of which changes output:

- A row in a run shows `_run_rows` and `_run_row` in its traceback; a row
  with its own task shows `_render_simple_vue_leaf`. The innermost frame,
  where user code raised, is the same.
- Reads of class attributes and of Citry's own frozen records (the
  admission record, the call metadata) differ in count, and some in
  timing: the call's shape is checked once for the loop instead of once
  per row, and `ForNode._call_run_class` reads the class's `simple`,
  `transparent` and selector flags before the loop runs. None of these
  has a read hook on Citry's own classes; only a user metaclass with a
  read hook could see the difference.
- `ComponentNode.render` makes one more method call (`_finish_render`)
  for every component call, and `_render_simple_vue_leaf` one more
  (`_simple_vue_record`), run or not.
- `CitryRender.parts` (public) can hold a `_DeferredRunRow` at each row's
  position until the render queue places the rows. Neither it nor
  `DeferredComponent` is exported from `citry`.
- Three public routes hand user code such a render before the queue
  reaches it: calling a template-defined slot (from `template_data` or
  another callback), the `on_slot_rendered` extension hook, and a nested
  template passed as a kwarg. In each, the list has one object per row,
  and `str()` raises the error an unplaced deferred component raises.
  The `on_render` generator and `on_component_rendered` see a render
  only after its rows are placed. `tests/test_call_run_tasks.py` checks
  the three routes.

## 7. Where the code lives

| Piece | File |
|---|---|
| The pure-Rust plan, value copy, evaluation, JSON writer and digests | `crates/citry_native_render/` |
| A call run's ids (levels A and B1), repeat checks and manifest items (level B1) | `crates/citry_native_render/src/run.rs` |
| The PyO3 classes `_RowPlan`, `_NativeRow` and `_RunDigests`, and `_encode_occurrences` | `crates/citry_core_py/src/native_render/rows.rs` |
| The run object (`_NativeRun`) and its rows (`_NativeOccurrence`) | `crates/citry_core_py/src/native_render/runs.rs` |
| Their type stub | `class native_render` in `packages/py/citry_core/citry_core/_rust.pyi` |
| The decision | `citry/_vue/native_render.py` |
| The plan tuples, the row read and the rebuild | `citry/_vue/leaf_program.py` |
| The row read's call site | `_simple_vue_record` in `citry/component_render.py` |
| The call run's walk (level C1) | `ForNode._call_run_class` and `ForNode._render_call_run`, and `ComponentNode._render_run_row` and `_finish_render`, in `citry/nodes/__init__.py` |
| The rows a loop recorded, and their places in the parts list (level C1) | `_DeferredRun` and `_DeferredRunRow` in `citry/citry_render.py` |
| The run task (level C1) | `_RunTask`, `_run_rows`, `_run_row` and the run branch of `_settle_render` in `citry/component_render.py` |
| The record properties | `SimpleVueRecord` in `citry/citry_render.py` |
| Assembly (`start_occurrence`, `native_definition`, `register_native_member`, the call-run ids, `take_native_run`, `run_members`) | `citry/_vue/direct_capture.py` |
| The manifest's occurrence list with run objects | `_occurrence_items_with_runs` in `citry/_vue/protocol.py` |
| The manifest writer | `_manifest_json` in `citry/_vue/serialization.py` |

## 8. Testing both paths

- `tests/_render_paths.py` has `render_both(run)`, which calls `run` on
  each path in one process, pins render ids, the Vue app id and the
  Events token clock, compares the results, and counts the rows Rust read,
  the rows Python rebuilt, the run objects Rust built, the call runs it
  declined, and the run objects the page manifests held, so a case cannot
  pass because both runs took the Python path.
- The `render_path` fixture runs a test once per path; `python_render_path`
  forces the Python path for a test that checks the Python evaluator's own
  internals. Both live in `packages/py/citry/tests/conftest.py`.
- `pytest --python-render-path` runs a whole session on the Python path,
  except the tests that ask for `render_path` or call `render_both`,
  which still run both. `packages/py/citry/tests/conftest.py` defines the
  option, so the run must include that directory; a run from the
  repository root does.
  The ubuntu / Python 3.10 cell of `py--tests.yml` uses it, because no CI
  job runs the suite on PyPy, Pyodide or free-threaded builds.
- `tests/test_call_run_order.py` locks the order of user callbacks and
  extension hooks, and runs on both paths.
- `tests/test_call_run_tasks.py` covers level C1, on both paths: run
  tasks place every row of a 140-row board (one task per loop, no row in
  a task of its own); both ways a row's position can be gone; a hook that
  reorders, drops or repeats the unplaced rows; a rows list printed again
  after its first row; rows that change what later rows do; a parts list
  edited before its rows are placed; and the three public routes that can
  see a render whose rows are not placed yet. Citry has no switch for run
  tasks, so the cases that compare with one task per row render the page
  again in the same process with no loop qualifying for a run
  (`ForNode._call_run_class` returns None). One more check, which does
  not depend on the path, gives a leftover row in a prepared render the
  unresolved-part error.
- `tests/test_native_render_runs.py` covers level B1: page cases with the
  run objects each must build and write, a check that every call run of a
  140-row board reaches a run object, a field-by-field comparison of the
  run object's assembly with the per-row loop's, and the binding's
  refusals against synthetic maps, which pages cannot reach.
- The Rust crate's tests compare against fixtures that
  `scripts/native_render_fixtures.py` writes from the Python code;
  `--check` (run by a Python test) fails when a fixture no longer matches.

## 9. Adding a level

A new level follows the same rules:

1. Pass every Python rule, constant or callback into Rust that can be
   passed. Lock what cannot be passed, such as fixed key names, with a
   fixture generated from Python.
2. When Rust cannot reproduce an input exactly, decline and let Python
   handle it, so the error and its timing are Python's own.
3. Read `native_render.ACTIVE` at the call site, build plans from
   `SUPPORTED`, and after that follow the Rust object, not the flag.
4. Add a `render_both` case with expected counts, so a silent decline
   cannot pass, and keep `tests/test_call_run_order.py` passing on both
   paths.
5. Add each new name to `_REQUIRED_NAMES`, the stub and this document.
