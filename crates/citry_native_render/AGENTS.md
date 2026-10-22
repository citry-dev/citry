# AGENTS.md - crates/citry_native_render

The pure-Rust half of Citry's native render path: it evaluates one
`simple = "vue"` row template over values copied out of Python, writes the
row's prepared data as JSON, and hashes the ids of each row of a call run
(the components one `c-for` places). The PyO3 half, which reads the Python
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
- `tests/` - fixture tests. `scripts/native_render_fixtures.py` writes the
  fixtures from Python's own output; rerun it after a change to the Python
  evaluator, and `--check` tells you whether it is needed.

## Gotchas

- **Never copy a Python rule or constant into Rust.** Python passes it in
  (the spread layout callback, the layout cache size). A copied constant
  goes stale silently: a test that changes the Python value would then
  compare Rust with Rust.
- **Decline rather than guess.** When an input is outside what this crate
  reproduces exactly, the caller declines the row, and Python then
  produces the result or raises the error it always has. A new case gets a
  decline first and an exact implementation only with a fixture proving it.
- **The Python half shares one start for every occurrence.**
  `transform_component` and `register_native_member` in
  `citry/_vue/direct_capture.py` both begin with `start_occurrence`; a new
  check on occurrences belongs there, so Rust-read rows get it too.
- **The crate has no PyO3 dependency.** Keep it that way, so its tests run
  without Python and another binding could reuse it.
