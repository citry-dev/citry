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
