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
- `citry.template.invalid-attribute-value` defaults to `error`. It stays a
  warning where no setting chooses its severity, such as
  `citry check --static` for a component whose `Lint` class does not set it.
- Added `citry.template.misspelled-directive`, the configurable error for a
  `c-*` attribute that looks like a misspelled Citry directive, or a `v-*`
  attribute that looks like a misspelled Vue directive (message variant
  `vue-directive`).
- Added configurable diagnostics for template HTML:
  `citry.template.misspelled-attribute`,
  `citry.template.misspelled-element`,
  `citry.template.unknown-aria-attribute`,
  `citry.template.invalid-nesting`, and `citry.template.duplicate-id`,
  all errors by default, and `citry.template.missing-image-alt`, a warning
  by default.
- Added configurable diagnostics for Vue code: `citry.vue.invalid-expression`
  and `citry.browser.invalid-model-target`, errors by default, and
  `citry.vue.misspelled-event`, a warning by default.
- `citry.template.invalid-attribute-value` also covers a boolean attribute
  with a value other than empty or its own name, with the message variant
  `boolean`.
- `citry.browser.undeclared-component-event` is configurable
  (`configurableSeverity: true`), also covers plain lowercase listener
  names that are not DOM events, and has the message variant `suggestion`
  that names a declared event one typing slip away.
