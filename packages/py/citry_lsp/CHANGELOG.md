# Changelog

All notable changes to `citry-lsp` are documented here.

## Unreleased

### Added

- The editor reports TypeScript's errors in component JavaScript and Vue
  template expressions, such as a method assigned a boolean, an `$emit`
  payload that fails its validator, a wrong argument count, or an unknown
  member of `this.$el`. They show as `citry.typescript.*` errors with the
  source `Citry (ts)`, and a mistake Citry already reports keeps only
  Citry's finding. VS Code uses its own TypeScript; other editors use the
  project's `tsc`. Set the `typeCheck` initialization option to `false` to
  turn it off.
- The editor warns about a static HTML attribute value that the attribute
  does not accept, such as `draggable="treu"` or `<input type="datetime">`,
  and suggests the closest valid keyword.

### Changed

- A value Citry cannot type, such as an injection or a server event's
  result, is `any` in completion and hover.
- A `js_data()` value types its key by the value's general type, such as
  `boolean` for `False`.
- A `js_data()` value that reads attributes of a Kwargs field, such as
  `kwargs.task.lane`, types its key from the annotations of the classes
  it passes through, so `lane: str` makes `this.laneKey` a `string`
  instead of `any`.
- `$event` on an HTML element is the DOM event of that name, such as
  `KeyboardEvent` for `@keydown`, and a name the DOM does not define is a
  `CustomEvent`.
- A selector query such as `querySelector('#name')` returns `any`.

- citry-lsp 0.2.0 understands Vue templates and component JavaScript.
  It requires Citry 0.6.0 or newer, with no upper bound, so upgrade
  `citry` and `citry-lsp` together. Keep citry-lsp 0.1.x for a project
  that stays on Citry 0.5.x.
- Hovers and type checks cover every field of the `onServerRender`
  context, including `state`, `sendEvent`, `loading`, `error`, `i18n`,
  `els`, and `id`, and `$component({ init })` is checked like
  `onServerRender`.

### Fixed

- In VS Code, `this` inside `$component({ ... })` now completes and hovers
  every member of the component: props, injections, `data()`, `setup()`,
  computed values, methods, `js_data()` keys, and Citry's helpers such as
  `$sendEvent`. Vue expressions in the template get the same types, and Go
  to Definition from either place opens the member's declaration, or the
  Python field for a `js_data()` key.
- `$el` is typed from the component template's top-level node, such as
  `HTMLButtonElement` for a `<button>` root, instead of `any` in component
  JavaScript and `Element` in templates.
- `$emit` follows the component's `emits` option like Vue's
  `defineComponent()`: completion offers the declared names, hover shows
  each event's values, and a listener on a child component tag types
  `$event` from the child's `emits`. The editor also marks an event name
  that `emits` does not declare.
- Hovering `$state` explains that it is Citry's Events State, typed from
  the component's `State` class, not Vue's `data()` or a Pinia store.
- Completion, hover, go-to-definition, and unknown-variable diagnostics now
  work for keys returned by a `template_data`, `js_data`, or `css_data`
  written as a `@staticmethod` or `@classmethod`, not only for instance
  methods.
- In an app without i18n settings, the editor no longer reports "Unknown
  i18n format profile" for a `self.i18n.format.number(..., format=...)`
  call guarded by `self.i18n.configured`, as `citry check` does.

## [0.1.7] - 2026-09-11

### Added

- Complete public State fields after `:c-` and report unknown binding fields
  ([#99](https://github.com/citry-dev/citry/issues/99)).
- Navigate JavaScript callback parameters to their authored declarations and
  report unknown `data` members for declared or fully inferred data schemas
  ([#113](https://github.com/citry-dev/citry/issues/113)).

### Fixed

- Report State bindings on unsupported elements and input types, including in
  syntax-only mode.
- Preserve authored positions for JavaScript suggestions inside indented
  Python strings.

## [0.1.4] - 2026-09-09

### Changed

- Accept Citry 0.4.5 and newer without a dependency upper bound; project checks
  accept later versions with compatible catalog and protocol schemas.
- Export `MINIMUM_CITRY_SERIES` in place of `SUPPORTED_CITRY_SERIES` to describe
  the project version check.


## [0.1.3] - 2026-08-30

### Added

- Complete and document core Alpine directive names and common event and
  attribute shorthands in standalone, inline, and nested templates.
- Complete and explain channel-specific `@c-*` and `:c-*` modifiers, link
  State keys to their Python fields, and navigate two-way binding values to
  their server handlers.

### Fixed

- Keep Citry `:c-*` State-binding handler names out of Alpine unknown-variable
  diagnostics and browser-expression completion routing.
- Check and complete two-way `:c-*` handler values through the same server
  event contract as `@c-*` values.

## [0.1.2] - 2026-08-29

### Added

- Load app-discovery environment variables from an optional `envFile`, reread
  the file on registry reload, and report missing or malformed files without
  changing the language server or type analyzer environment.

### Changed

- Pin the supported `ty` analyzer directly so a clean `citry-lsp` install does
  not depend on optional-extra metadata from a separate Citry release.
- Allow 15 seconds for isolated app discovery so cold environments do not
  degrade prematurely while keeping the editor event loop free.

### Fixed

- Keep isolated app discovery responsive on Windows by isolating worker stdin
  from LSP stdio and owning startup, communication, and reaping in one bounded
  background transaction with cancellation-safe cleanup.
- Keep analyzer shadows inside the edited workspace when installed component
  source and the project occupy different Windows drives, and serve Citry-owned
  i18n formatter completions and signatures from the canonical API contract
  instead of depending on cross-drive analyzer traversal.
- Recognize the Windows `ty` cache layout when filtering unsafe Python runtime
  members from template completions.

## [0.1.1] - 2026-08-20

### Fixed

- Formatted triple-quoted component assets now keep ordinary quotes and use
  readable, host-relative multiline JavaScript and CSS framing.

### Changed

- Python expression analysis now uses `ty` 0.0.71.

## [0.1.0] - 2026-08-19

### Added

- Analyze inline Python templates, `citry-html` documents, and registered template files with Citry diagnostics, completion, hover, symbols, references, and precise navigation.
- Load a configured `Citry` app or `ComponentLibrary` in an isolated worker for component, input, slot, template-data, and asset knowledge, with an explicit syntax-only fallback when registry discovery is unavailable.
- Use the supported `ty` analyzer for Python expression diagnostics, member and call completion, narrowed hover types, definitions, and signature help.
- Check Alpine expressions, component JavaScript, Events handlers, `$c-props`, `JsData`, and `CssData` against their Python declarations and navigate between them.
- Check Fluent messages and `tr()`, formatter, `<c-trans>`, `$c-tr`, and `i18n.bind()` uses with key, argument, type, completion, hover, and navigation support.
- Format standalone and inline Citry templates through the shared structural formatter, with protocol-v1 requests for document, cursor, JavaScript, and CSS asset formatting.
- Provide protocol v1, conservative HTML projections, responsive cancellation, portable file-URI handling, and formatter registration compatible with VS Code, PyCharm's native LSP client, and LSP4IJ.
