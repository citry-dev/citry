# Changelog

## v1 - Unreleased

- Added the schema-validated source catalog for Citry-owned diagnostic codes,
  message variants, trigger conditions, examples, severities, reporting
  surfaces, and documentation links.
- Added generated Python, Rust, and TypeScript bindings plus drift validation.
- Recorded `citry.python.*` as a provider-owned family whose suffixes and
  messages are not copied into the Citry catalog.
- Added stable Alpine-variable, server-event, and client-prop diagnostics for
  browser-expression analysis in `citry check` and the language server.
