# Changelog

## v1 - Unreleased

- Added `citry.template.csp-incompatible`, reported by `citry check` and the
  language server when the application's `security_csp` is `"warn"` (a
  warning) or `"strict"` (an error). It is off by default, because
  `security_csp` is.
- Added `citry.template.undeclared-template-data-key`, the `citry check`
  warning for a key that `template_data()` writes as a literal but the
  component's `Lint.template_data_keys` leaves out.
- Added `citry.parse.too-deep` for a template that nests tags more than 512
  levels deep, or more than 256 Citry logic levels deep.
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
- `citry.vue.invalid-expression` has the message variant `parser`, whose
  `detail` parameter carries the JavaScript parser's message, such as
  `Unexpected token`.
- Added `citry.vue.compile-error`, the configurable error for a template that
  Vue's compiler rejects. Its one parameter, `detail`, carries the
  compiler's message.
- `citry.template.invalid-attribute-value` also covers a boolean attribute
  with a value other than empty or its own name, with the message variant
  `boolean`.
- `citry.browser.undeclared-component-event` is configurable
  (`configurableSeverity: true`), also covers plain lowercase listener
  names that are not DOM events, and has the message variant `suggestion`
  that names a declared event one typing slip away.
- Added configurable diagnostics that `citry check` reports with the
  application loaded: `citry.browser.missing-component-key`,
  `citry.browser.prop-assignment` (also reported by the language server,
  with the message variant `v-model`),
  `citry.browser.unknown-server-event-field` (variants `suggestion` and
  `no-data`), `citry.browser.missing-server-event-field`, and
  `citry.browser.incompatible-server-event-field`, all errors by default,
  and `citry.css.misspelled-variable`, a warning by default. The language
  server reports the three server-event field diagnostics too.
- Added `citry.browser.unknown-form-field` (variants `suggestion` and
  `no-data`) and `citry.browser.missing-form-field`, configurable errors
  that `citry check` and the language server report with the application
  loaded, for the control names of a form whose `@c-submit` sends its
  fields to a server event.
- Added `citry.template.unknown-url` (variant `suggestion`), a configurable
  warning that `citry check` and the language server report with the
  application loaded, for a literal link path the host app does not serve.
  Added `citry.check.url-checker-missing` and
  `citry.check.url-checker-failed` (message variant `several`), information
  diagnostics that `citry check` lists as notes when no web framework
  integration can answer for the links, or when its answer raises an error.
- Added `citry.template.unknown-inject-key` (variants `suggestion`,
  `nowhere`, and `nowhereSuggestion`), a configurable warning that
  `citry check` and the language server report with the application
  loaded, for a `self.inject()` key that no provider above the component
  gives.
- Added `citry.check.template-not-checked`, an information diagnostic for a
  class whose template `citry check --static` and the language server skip
  because its base class comes from another module and Citry has not
  loaded the application or does not find the class in it.
- `citry.browser.incompatible-component-prop` also covers a string for a
  Boolean prop and both results of a condition whose results are literals.
- `citry.js-data.unsupported-type` also covers a module constant that
  `js_data()` returns and a value that ty types as a standard type JSON
  cannot carry.
- `citry.js-data.unsupported-type` also covers a `citry.Secret` in
  `js_data()` or a `JsData` field.
- Added `citry.css.misspelled-class` (a warning), and
  `citry.css.undeclared-class` and `citry.css.undeclared-variable`, both
  off by default; `citry check` reports them with the application loaded.
- `defaultSeverity` now accepts `ignore` for a rule that is off until the
  application turns it on. It requires `configurableSeverity: true`, and
  the public reference shows such a rule as off.
- `citry.js-data.unsupported-type` adds the message variant `secret`,
  used when the value is a `citry.Secret`.
- The `citry.css.misspelled-variable` and `citry.css.undeclared-variable`
  messages now say the property gets its initial or inherited value.
