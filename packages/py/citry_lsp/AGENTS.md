# AGENTS.md - packages/py/citry_lsp

The pure-Python Citry language server. It owns its dependencies, release
version, and changelog separately from the `citry` runtime package.

Read [`/CLAUDE.md`](../../../CLAUDE.md) and
[`/docs/design/ide_integration.md`](../../../docs/design/ide_integration.md)
before changing protocol or capability behavior.
Before adding a component source body, embedded language, or language island,
also follow the complete vertical checklist in
[`/docs/design/embedded_language_ide.md`](../../../docs/design/embedded_language_ide.md).

Project code must never be imported in the LSP stdio process. Keep app loading
in `citry_lsp.app_worker`, preserve the registry/static confidence boundary,
and bump the declared protocol version for incompatible client changes.

TypeScript diagnostics: `engine.type_check_projections` builds the checked
files, `citry_lsp/typescript.py` runs `tsc` and maps and filters findings,
and the server asks a client that offers it (`typeCheckClient`) through
`citry/typeCheck`. Fix a false positive in the projection types or
`citry_lsp/citry-dom.d.ts`, never by matching TypeScript's message text, which
VS Code may show in another language.

`citry check --types` reuses the editor's code through
`citry_lsp/project_check.py`: `project_documents` reads the component files
once, `typescript.check_project_types` runs `tsc`, and
`check_project_python_types` runs the editor's `semantic.semantic_diagnostics`
with one ty child. Change the shared functions, not a CLI-only copy.

When the rules in `citry/_json_wire.py` cannot type part of a `js_data()`
value, ty types it: `semantic.infer_js_data_value_types` wraps each unknown
part in `reveal_type()` in a copy of the module and stores the answers on
the `ProjectState` for that exact source. The server runs it before each
document's checks, and `check_project_python_types` runs it before the
CLI's TypeScript check, so the TypeScript projections read the answers. A
project reload copies the answers as stale ones, used until ty answers
again (`adopt_js_data_inferred_types`).
