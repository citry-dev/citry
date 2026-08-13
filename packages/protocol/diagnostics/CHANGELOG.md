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
- Added `citry.csp.incompatible-browser-code` for version-pinned Alpine CSP
  compatibility findings in `citry check` and the language server.
- Added stable i18n diagnostics for invalid catalogs, unknown messages, bad
  arguments, unsafe cross-language fallback, and invalid client-message
  declarations in the checker and language server.
- Extended the i18n argument and unknown-message contracts to checked `$c-tr`
  syntax, message outputs, and typed browser named values.
