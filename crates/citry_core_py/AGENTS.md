# AGENTS.md - crates/citry_core_py

The PyO3 glue crate. It is a single `_rust` Python extension module that brings
the other Rust crates together and exposes them to Python as submodules. This
crate defines exactly what Python sees.

For repo-level rules see [`/CLAUDE.md`](../../CLAUDE.md). For cross-crate facts
see [`/docs/agent/INDEX.md`](../../docs/agent/INDEX.md).

## Where to look

- `src/lib.rs` - the `#[pymodule] fn _rust(...)`. Registers each submodule and
  its functions / classes. This is the registration point for everything Python
  can import. It also sets `BUILD_PROFILE` (`"release"` or `"debug"`), which the
  benchmark runners read to refuse an unoptimized build.
- `src/html_transform.rs` - wraps `citry_html_transform`, including the
  private output checks: `_check_output_html`, plus
  `_script_type_is_executable`, `_classify_dependency_attribute`,
  `_is_javascript_url` and `_JAVASCRIPT_MIME_TYPES`, which `citry` also uses
  on structured `Script` and `Style` values. Only the `citry` package calls
  them.
- `src/i18n.rs` - exposes ICU4X locale canonicalization and direction lookup,
  and wraps the language-neutral `citry_i18n` catalog runtime.
- `src/safe_eval.rs` - wraps `python_safe_eval`.
- `src/template_formatter.rs` - wraps `citry_template_formatter` and attaches
  stable formatter codes, ranges, and parser diagnostics to Python errors.
- `src/vue.rs` - wraps `citry_vue_compiler`: `_compile_vue`, and the
  render programs the server runs to write HTML Vue hydrates
  (`ServerRenderProgram`, `_read_server_render_program`,
  `_render_for_hydration`).
- `src/native_render/` - wraps `citry_native_render` for the native render
  path (`docs/design/native_render.md`): `rows.rs` holds `_RowPlan`,
  `_NativeRow`, `_RunDigests` and `_encode_occurrences`, the code that reads
  Python values through the C API, and `without_panics`; `runs.rs` holds
  `_NativeRun`, the object that records a whole call run of Rust-read rows
  during serialize, and `_NativeOccurrence`, one row of it in the view;
  `walk.rs` holds `_CallRunWalkPlan`, which walks a call run's loop and
  reads each row's inputs (level C2); `leaf_json.rs` holds level B2:
  `_leaf_values_json`, which writes an ordinary component's leaf data (the
  values its leaf program sends to the browser) as JSON into a `_LeafJson`,
  and the function `_encode_occurrences` calls to write such an
  occurrence's item; `mod.rs` registers them. Every name is private;
  `citry/_vue/native_render.py` decides whether Citry calls them.
- `src/template_parser.rs` - wraps `citry_template_parser`: `parse_template`
  / `compile_template`, the V3 AST classes, `TagRules`, and the browser
  analysis functions. `analyze_browser_source` and
  `analyze_component_source` return the `#[pyclass]` record structs from
  `citry_template_parser::browser` directly, so their fields are defined
  once, in that crate, and `lib.rs` registers each record class.
- `src/panics.rs` - `catch_panic`, which turns a Rust panic into an
  error message, so a binding can raise an ordinary Python exception
  instead of PyO3's `PanicException` (a `BaseException`).
- `Cargo.toml` - depends on the sibling crates by path; `crate-type =
  ["cdylib"]`.

## Gotchas

- **The Python module name comes from the `#[pymodule]` function name** (`_rust`)
  and must match the `module-name` setting in the Python package's
  `pyproject.toml`. See [`packages/py/citry_core/AGENTS.md`](../../packages/py/citry_core/AGENTS.md).
- **Every `#[pyclass]` / `#[pyfunction]` exposed here must be mirrored** in
  [`packages/py/citry_core/citry_core/_rust.pyi`](../../packages/py/citry_core/citry_core/_rust.pyi).
  The stub is hand-written and is the IDE/type-check contract.
- **An entry point that does deep work starts with a stack guard.** Wrap its
  Rust work, after the arguments are converted, in
  `citry_template_parser::stack::with_enough_stack`. CPython lets a call
  through with only about 20 KiB of stack left, so the work's first frames
  need the guard. An entry point that runs on every render uses
  `with_enough_stack_where_measurable`, which skips the guard on wasm32. The
  work inside must not touch Python objects, because it may run on a stack
  segment taken from the heap. The native render entry points call Python as
  they go, so they cannot be wrapped (see `src/native_render/mod.rs`).

## Verifying changes

Build the Python extension and run the Python tests from the package directory:

```bash
cd packages/py/citry_core && uv run maturin develop && cd -
uv run pytest
```
