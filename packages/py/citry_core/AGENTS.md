# AGENTS.md - packages/py/citry_core

The Python package (`citry_core` on PyPI). A mixed Rust/Python package: maturin
builds the Rust `_rust` extension from `crates/citry_core_py`, and the
hand-written Python modules here wrap it in a language-native API.

For repo-level rules see [`/CLAUDE.md`](../../../CLAUDE.md). For cross-crate
facts see [`/docs/agent/INDEX.md`](../../../docs/agent/INDEX.md).

## Where to look

- `citry_core/_rust.pyi` - **hand-written type stub** mirroring everything the
  Rust `_rust` module exposes. This is the IDE / type-check contract; keep it in
  sync with `crates/citry_core_py/src/lib.rs`.
- `citry_core/html_transform/` - wraps the `html_transform` submodule.
- `citry_core/safe_eval/` - sandboxed expression eval (`eval.py`, `sandbox.py`,
  `error.py`); wraps the `safe_eval` submodule.
- `citry_core/template_formatter/` - typed wrapper for the pure authored
  template formatter and its structured error.
- `citry_core/template_parser/` - the V3 parser/compiler wrapper (`parse.py`,
  `compile.py`); wraps the `template_parser` submodule. The generated code it
  returns instantiates the runtime node classes that live in the `citry`
  package (`citry.nodes`), not here.
- `pyproject.toml` - `[tool.maturin]` config. `module-name = "citry_core._rust"`
  and `manifest-path` point maturin at `crates/citry_core_py`. The long comment
  there explains why the module name mapping is necessary.
- `tests/` - binding tests for HTML transformation, safe evaluation, template
  parsing, and template formatting run in CI; the `benchmark_*.py` files are
  manual helpers, not collected.

## Gotchas

- **The package name (`citry_core`) and the Rust extension name (`_rust`)
  differ from the Rust crate name (`citry_core_py`).** The maturin
  `module-name` setting bridges them; do not "fix" the mismatch by renaming.
- **`_rust.pyi` is the contract** consumers and the type checker see. When the
  Rust surface changes, update the stub in the same change.

## Verifying changes

```bash
# from this directory: build the extension, then run tests from the repo root
uv run maturin develop
cd ../../.. && uv run pytest && uv run mypy packages/py/citry_core
```
