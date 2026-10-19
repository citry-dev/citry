# Changelog

## v1 - Unreleased

- Added the schema-validated source catalog for Citry-owned diagnostic codes,
  message variants, trigger conditions, examples, severities, reporting
  surfaces, and documentation links.
- Added generated Python, Rust, and TypeScript bindings plus drift validation.
- Added an optional `fix` field that tells the reader how to resolve a
  diagnostic. The public reference shows it after the message and examples.
- Recorded `citry.python.*` as a provider-owned family whose suffixes and
  messages are not copied into the Citry catalog.
- Added stable Vue-variable, server-event, and component-prop diagnostics
  that `citry check` and the language server report for browser expressions.
- Added stable i18n diagnostics for invalid catalogs, unknown messages, bad
  arguments, unsafe cross-language fallback, and invalid client-message
  declarations in the checker and language server.
- Extended the i18n argument and unknown-message contracts to checked `$c-tr`
  syntax, message outputs, and typed browser named values.
- Added `citry.i18n.missing-param-type`, the configurable `citry check`
  warning for a message variable without a `# @param` type, which the i18n
  compiler already reported.
