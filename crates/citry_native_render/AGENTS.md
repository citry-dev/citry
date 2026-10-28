# AGENTS.md - crates/citry_native_render

The pure-Rust half of Citry's native render path: it evaluates one
`simple = "vue"` row template over values copied out of Python, writes the
row's prepared data as JSON, hashes the ids of each row of a call run
(the components one `c-for` places), writes a whole run's manifest
items when one object records the run, and reads every row of such a
run's loop when the loop reads only plain paths (a name and constant
subscripts). The PyO3 half, which reads the Python
values and exposes the classes to Python, is
[`crates/citry_core_py/src/native_render/`](../citry_core_py/src/native_render/).
The design, when Citry uses this code and every error mode are in
[`docs/design/native_render.md`](../../docs/design/native_render.md).

For repo-level rules see [`/CLAUDE.md`](../../CLAUDE.md). For cross-crate facts
see [`/docs/agent/INDEX.md`](../../docs/agent/INDEX.md).

## Where to look

- `src/plan.rs` - `Plan::new` turns Python's description of a template (its
  operations and the paths it reads, built by `native_row_plan_tuples` in
  `citry/_vue/leaf_program.py`) into a plan, and refuses any shape it cannot
  evaluate exactly. `SpreadLayout` is one root `c-bind` key set's layout.
- `src/value.rs` - `Value`, the copied tree of the values a row reads.
- `src/eval.rs` - `Plan::write_row`: evaluates the plan and writes the JSON.
- `src/json.rs` - the JSON string writer, with and without `script_json`'s
  `<` escape.
- `src/digest.rs` - `DigestPrefix`, the call-run ids.
- `src/run.rs` - `RunIds` (both ids of a run's rows, used by levels A and
  B1), and for level B1 `first_repeat` (the repeat checks) and
  `write_occurrence_item` (one row's manifest item).
- `src/walk.rs` - `WalkPlan` (level C2): checks the paths Python built
  from a loop's expressions (`citry/_vue/native_walk.py`) and reads every row through the
  `Tree` trait, which the PyO3 layer implements over Python objects, in the
  order Python's walk reads them, or names why it declines.
- `tests/` - fixture tests. `scripts/native_render_fixtures.py` writes the
  fixtures from Python's own output; rerun it after a change to the Python
  evaluator, and `--check` tells you whether it is needed.

## Gotchas

- **Pass Python rules and constants in; do not copy them.** Python passes
  them in (the spread layout callback, the layout cache size, the JavaScript int
  limit). A copied constant goes stale silently: a test that changes the
  Python value would then compare Rust with Rust. What cannot be passed
  in (the manifest's fixed key names, how a value is written) is locked
  by the fixtures.
- **Decline rather than guess.** When an input is outside what this crate
  reproduces exactly, the caller declines the row, and Python then
  produces the result or raises the error it always has. A new case gets a
  decline first and an exact implementation only with a fixture proving it.
- **A new occurrence check has more than one home.** `transform_component`
  and `register_native_member` in `citry/_vue/direct_capture.py` both
  begin with `start_occurrence`, so a check added there applies to
  Rust-read rows too. A call run that one run object records skips
  `start_occurrence`: `take_native_run` makes the class checks once per
  run, and `_NativeRun.try_new` and `commit` make the per-row ones. Add a
  new check there too, or make `try_new` decline the rows it concerns.
- **Code that calls itself once per nesting level counts the level.** The
  plan's walks run on the caller's own thread stack, so `MAX_BODY_DEPTH`
  and `MAX_READ_DEPTH` in `src/plan.rs` bound them, with a value for each
  build profile. A new recursive walk of the plan or of a row's values
  stays within those limits, or gets its own. After a change that makes a
  level's stack frame larger, rerun `tests/test_native_render_depth.py` in
  the `citry` package on a `maturin develop` build and on a release build.
- **The crate has no PyO3 dependency.** Keep it that way, so its tests run
  without Python and another binding could reuse it.
