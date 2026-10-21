# Changelog

All notable changes to `citry-lsp` are documented here.

## Unreleased

### Added

- The editor reports a misspelled directive, such as `c-iff` for `c-if`,
  with the severity your application's `rule_misspelled_directive` sets.
- Before your application loads, the editor uses the severity a
  component's own `Lint` class sets as a plain string, such as
  `rule_misspelled_directive = "ignore"`.
- The editor reports a misspelled attribute, tag, `aria-*` name, or DOM
  event (`titel`, `<dvi>`, `aria-expandd`, `@clik`), a `<div>` or other
  block inside a `<p>`, a repeated `id`, an `<img>` without alt text, a
  Vue expression that is not valid JavaScript, and `v-model` on an
  element that holds no value. Each follows its `rule_*` setting, and
  each works before your application loads.
- The editor runs Vue's compiler over each template and underlines what it
  rejects, such as a `<div>` directly inside a `<table>` or a `v-else` with
  no `v-if` before it, at the severity `rule_vue_compile_error` sets. It
  works before your application loads.
- The editor reports a typo in a Vue directive, such as `v-iff`, a
  boolean attribute with a value such as `disabled="false"`, and, once
  your application loads, a lowercase listener on a component for an
  event the child does not declare, such as `@hdie`.
- Once your application loads, the editor reports a component that
  assigns to its own prop, such as `@click="open = false"`, at the
  severity `rule_prop_assignment` sets.
- Once your application loads, the editor reports `@c-*` arguments the
  server would reject, such as `save({amont: 1})` or `save({amount: '1'})`
  for an `int` field, and a control in a submitted form whose `name` the
  handler does not accept, such as `<input name="qeury">`, as
  `citry check` does. It skips a handler while the handler or its data
  class has unsaved changes, and every handler of an application on an
  older Citry, which does not say how the server checks the arguments.
- Once your application loads, the editor and `citry check --types`
  check a fill's `data` name, such as `card` in `<c-fill data="card">`,
  against the slot's `SlotInput[T]`, so
  `card.titel` or `card.count + " tasks"` is reported when `T` declares
  `title: str` and `count: int`.
- Once your application loads, the editor and `citry check --types` check
  a bound prop value on a child component tag against the prop's `type` in
  the child's `$component` call, so `:open="count"` is an error for a
  Boolean prop when `count` is a number.
- Once your application loads, the editor warns about a link to a page or
  file your app does not serve, such as `<a href="/abuot">`, when your app
  mounts Citry with `citry.contrib.flask.mount()`,
  `citry.contrib.fastapi.mount()`, or `citry.contrib.django.urlpatterns()`
  (`rule_unknown_url`). A link you add is checked at the next reload,
  which saving a Python file starts.
- The editor and `citry check --types` warn about a `js_data()` value that
  ty types as a standard type JSON cannot carry, such as a
  `PurePosixPath`, a `datetime`, or a set.
- Once it has loaded your application, the editor checks the template,
  JavaScript, and CSS of a component whose base class comes from another
  module of your project, and `citry check --types` type-checks them.
  Without the application, or for a class added or renamed since it
  loaded, the editor marks the class with an information message.

### Changed

- `citry check --types` no longer checks components installed in a `.venv`
  or `site-packages` folder inside your project; their authors check them.

### Fixed

- `citry check --types` and the editor now report type errors in a
  component that has no `template_data()` of its own, or whose
  `template_data()` or `js_data()` comes from a class in an installed
  package, an editable install, or a `.venv` inside the project. An inline
  template is checked when its class subclasses `Component` directly.

## [0.2.0] - 2026-10-19

### Added

- The editor reports TypeScript's errors in component JavaScript and Vue
  template expressions, such as a method assigned a boolean, an `$emit`
  payload that fails its validator, a wrong argument count, or an unknown
  member of `this.$el`. They show as `citry.typescript.*` errors with the
  source `Citry (ts)`, and a mistake Citry already reports keeps only
  Citry's finding. VS Code uses its own TypeScript; other editors use the
  project's `tsc`. Set the `typeCheck` initialization option to `false` to
  turn it off.
- The editor checks a bound attribute on an HTML element, such as
  `:draggable` or `:style`, against Vue's types for that attribute, so
  `:style="1"` is a TypeScript error. This can report existing bindings
  such as `:aria-expanded="String(open)"`; bind the boolean instead.
- The editor checks each `c-*` value on a component tag against the
  child's `Kwargs` annotation, so `<c-TaskCard c-task="1">` is an error
  when `task` is a `Task`. A static attribute is checked as the string
  it passes, so `<c-TaskCard size="xl">` is an error when `size` only
  takes `"sm"`, `"md"`, or `"lg"`. It also checks that `c-class` and
  `c-style` on an HTML element get a string, a dict, a list or tuple of
  those, or `None`.
- The editor warns about a static HTML attribute value that the attribute
  does not accept, such as `draggable="treu"` or `<input type="datetime">`,
  and suggests the closest valid keyword. A Vue binding to one string,
  such as `:dir="'rlt'"`, is checked the same way, and TypeScript does
  not report the same value again, so such a value is now a warning
  rather than a TypeScript error.
- The editor asks ty for the type of a `js_data()` value Citry has no
  rule for, such as `self.labels()` or a list comprehension, so when
  `labels()` returns `list[str]`, completion, hover, and TypeScript checks
  type `this.labels` as `string[]` instead of `any`.

### Changed

- A value Citry cannot type, such as an injection or a server event's
  result, is `any` in completion and hover.
- A `js_data()` constant types its key by the value's general type, such
  as `boolean` for `False`, while a Kwargs field annotated with a
  `Literal`, or an `Enum` member's `.value`, keeps its values, such as
  `"sm" | "md"`.
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
- On a subclassed component, completion, hover, and template checks
  follow Citry 0.6.0's rule for nested data classes such as `TemplateData`
  and `JsData`: a plain `class TemplateData:` on the subclass replaces the
  parent's class and drops its fields, while
  `class TemplateData(Parent.TemplateData):` keeps them.
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
- A template loop variable now has its own type in hover and type checks
  when `template_data()` has a local of the same name. Before, `c-for="row
  in rows"` next to a local `row: list[Row]` typed the loop variable as
  the list.
- Hover and type checks keep each key's own type in the dict
  `template_data()` returns, also when the method ends with `return data`
  or when only some returns include the key. Before, such a key could show
  the union of every value in the dict.

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
