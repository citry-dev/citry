# Release notes

## v1.6.0

_Unreleased_

### Added

- Expose Citry's language-neutral Fluent compiler and runtime through PyO3,
  including typed message interfaces, deterministic artifacts, locale fallback,
  structured rich-message segments, source diagnostics, ICU4X plural rules,
  and the checked number, currency, date, relative-time, and list profiles.
  Parameter metadata includes descriptions and exact declaration spans, and
  currency formatting applies CLDR fraction digits and half-expand rounding.
- Expose OXC-backed JavaScript expression analysis and conservative
  `$component` initializer facts for Citry's batch and editor tooling,
  including exact context bindings, free references, and synchronous scope
  writes.

## v1.5.0

_7 Aug 2026_

### Changed

- Plain-element `#c-key` now compiles to an `ElementKeyNode` wrapping the key
  expression. This lets a host runtime omit the complete `data-citry-key`
  attribute when the value is `None`; host runtimes that execute generated
  source must provide this node class.

### Added

- Expose immutable parser-owned directive and context-qualified structural
  attribute inventories for language tools that need exhaustive Citry syntax
  coverage.
- Added `citry_core.template_formatter.format_template()` and the structured
  `TemplateFormatError` for parser-backed structural formatting of authored
  Citry template text without application discovery or global state. The
  structural formatter preserves sensitive, verbatim, and suppressed bytes while
  formatting proven block structure and nested template attributes.
- Add built-in Python expression formatting backed by the vendored Ruff
  0.16.2 pin. Ordinary expressions and `c-for` clauses are accepted only
  after AST and anchored-comment equivalence checks; direct `c-fill data`
  patterns use Citry's own formatter. The new
  `python_expression_provider()` function reports the authoritative provider
  identity.
- Add the typed two-pass embedded-formatting API under
  `citry_core.template_formatter`. `prepare_embedded_format()` exposes
  immutable JavaScript/CSS requests and capability notices, while
  `finish_embedded_format()` validates source-bound provider results and
  composes them atomically. Invalid, stale, missing, duplicate, or unsafe
  provider output raises `TemplateFormatError` with the stable
  `citry.format.provider-invalid` code.
- Template parse failures expose a stable diagnostic code and root-template
  UTF-8 byte range through `parse_diagnostic()`. They retain their existing
  `SyntaxError` or `ValueError` class and rendered message. Parsed
  `HtmlAttr.kind` values are also readable and comparable from Python.

### Fixed

- Recognize omitted, bare, empty, module, and standard JavaScript MIME
  `script` types when preparing embedded formatter requests, while retaining
  data-block and parameterized-type exclusions. Embedded result statuses now
  reject contradictory output fields.
- Treat quotes and braces inside Python `#` comments as comment text while
  finding a `{{ ... }}` interpolation boundary, and keep the host `}}`
  delimiter outside the compiled expression.
- Return the parser's validation error for unsupported Python expression kinds
  such as `await` instead of allowing the safe-expression transformer to
  panic.

## v1.4.0

_27 Jul 2026_

### Breaking changes

Some templates that parsed under v1.3.0 now raise a parse error. In each case
the old template had two readings, and the parser now asks you to pick one.

- **A loop or fill variable may no longer reuse a name already in scope.**
  Reusing an outer name used to be accepted, and the inner value quietly
  replaced the outer one for the rest of the block. Rename the inner variable.

  ```html
  <!-- error: 'x' is already in scope -->
  {{ x }}
  <c-for each="x in items">{{ x }}</c-for>
  ```

  This covers a loop shadowing a template variable, a loop nested inside
  another loop of the same name, a `<c-fill data="x">` inside a `<c-for
  each="x in items">`, and a loop that binds one name twice
  (`each="x, x in pairs"`).

- **Giving one attribute both a static and a dynamic value is now rejected.**
  `<form id="form" c-id="my_var">` used to parse, with the last one silently
  winning. Write only the dynamic form, or supply the value through `c-bind`.
  Two exceptions still accumulate as before: `class` and `style` on plain HTML
  elements, and event handlers on a component tag.

  ```html
  <!-- error: 'id' and 'c-id' set the same attribute -->
  <form id="form" c-id="my_var">
  <!-- write this instead -->
  <form c-id="my_var">
  ```

- **The `#c-*` prefix is reserved for Citry.** `#c-key` and `#c-ignore` are the
  only names it accepts; any other `#c-*` attribute is an error rather than a
  plain static attribute. A `#` name that does not start with `#c-` (such as
  `#foo`) is untouched.

- **`$c-props` and `c-$c-props` are reserved names** and belong on a component
  tag. On a plain HTML element, on `<c-element>`, or on any structural `<c-*>`
  tag they are now an error instead of an ordinary attribute. Only those exact
  names are reserved, so `$c-props-extra` still parses as before.

- **`c-bind` belongs on a component or element tag.** Spreading attributes onto
  a structural tag (`<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`,
  `<c-raw>`) is now an error; those tags take their own attributes directly.

- **`c-bind` takes an expression, not a template.** A value written as a
  template fragment, `c-bind="<>attrs</>"`, is now rejected; the expression has
  to resolve to a mapping.

- **`<c-component>` and `<c-element>` require a non-empty `is`, and any tag
  with a static `name` requires a non-empty value.** `<c-component is="" />`,
  `<c-slot name="" />`, `<c-slot name />`, and `<c-fill name>` used to be
  accepted, whitespace-only values included. Use `c-is` or `c-name` when the
  value is computed. Writing both `is` and `c-is` is also reported when the
  template is parsed rather than when it is compiled, so a caller that only
  wrapped `compile_template` now sees the error earlier.

- **`<c-fill data="...">` accepts an identifier or a destructuring pattern**,
  not an arbitrary expression. Values such as `data="{x: y}"`, `data="{x.y}"`,
  and `data="{*rest}"` are now rejected. See the new destructuring syntax below.

- **`<c-component>` and `<c-element>` with both `is` and `c-bind` resolve the
  target at render time.** `<c-component is="Alpha" c-bind="props" />` used to
  settle on `Alpha` while parsing and ignore an `is` supplied by the spread; the
  spread now decides. If you want the fixed target, drop the `c-bind`.

- **A template-valued attribute no longer passes its `<>` markers to the
  child.** `<c-card c-body="<><p>A</p></>" />` used to hand the child the
  literal `<>` and `</>` text, and an empty `c-body="<></>"` arrived as `True`
  rather than an empty string.

### Added

- **Fill data destructuring.** `<c-fill data="...">` accepts a pattern, so a
  fill can name the individual pieces of the data a slot exposes instead of
  reaching through one object. Renaming uses `as`, and a final `**rest`
  collects the remainder. Trailing commas and multi-line patterns are fine.

  ```html
  <c-fill
      name="row"
      data="{ item, index as i, **rest }"
  >
      {{ item }} at {{ i }}
  </c-fill>
  ```

  The parsed pattern is available as `HtmlAttr.fill_data_pattern`, with the new
  `FillDataPattern` and `FillDataField` AST types.

- **Slot data field validation.** `TagRules` accepts `slot_data_fields`, a
  mapping from slot name to the fields that slot exposes. Destructuring a field
  the slot does not offer now reports the mistake at parse time and lists the
  fields that are available. A fill whose name is computed is checked at render
  time instead.

- **`#c-key` and `#c-ignore` attributes** for telling the browser how to treat
  an element across updates. `#c-key="item.id"` gives an element a stable
  identity and takes an expression, so a bare `#c-key` is an error. It is valid
  on plain HTML elements and on component tags. `#c-ignore` leaves a subtree
  alone and is valid on plain HTML elements only, since a component tag has no
  element of its own to opt out. Neither has to appear in a component's
  `allowed_attrs`.

  ```html
  <li #c-key="item.id">{{ item.name }}</li>
  ```

- **`$c-props` and `c-$c-props` attributes** for passing props to a component's
  browser-side code. `$c-props` holds a browser expression evaluated in the
  page; `c-$c-props` holds a Python expression whose result is sent instead.
  Like event handlers, `$c-props` passes through a component's `allowed_attrs`
  without being listed, and it does not satisfy a required attribute.

- **`HtmlAttrKind.Meta`**, the kind reported for `#c-key` and `#c-ignore`. Code
  that branches over every `HtmlAttrKind` member needs an arm for it.

- **`RESERVED_TAG_NAMES`**, the set of structural `<c-*>` tags the parser
  handles itself, is now exported from `citry_core.template_parser`.

### Changed

- **Two `<c-fill>` tags with the same computed name now parse.** Whether they
  actually collide depends on values only known at render time, so the check
  belongs there.

- **Event handlers written on a component tag pass through that component's
  `allowed_attrs`** without being listed, in both their static and `c-` forms
  (`@click`, `c-@change`, `x-on:focus`, `c-x-on:blur`, `@c-save`).

### Fixed

- A template containing non-ASCII text reported parse errors at the wrong
  column, so the caret pointed into the middle of a character rather than at
  the mistake.
- A `{# ... #}` comment spanning several lines, or containing non-ASCII text,
  could crash the parser or report a position far from the comment.
- A loop over a variable of its own name, `<c-for each="x in x">`, did not
  record that it reads the outer `x`, so the loop could render stale values
  after that variable changed. Reusing a name this way is now rejected outright
  (see Breaking changes above).
- With `c-if` or `c-for` written directly on an element, the variables each
  node reported reading were attributed to the wrong node, and with both on one
  element the loop variable landed on whichever wrapper was built first.
- Two identifiers that look identical but use different Unicode spellings were
  treated as separate variables in the generated code.
- An unclosed or mismatched tag now says which tag it expected and which it
  found, instead of reporting a generic parse failure, and an error inside a
  template-valued attribute is reported at its real line and column in the
  original template.

## v1.3.0

_30 Jun 2026_

Initial release. citry-core provides the Rust-backed bindings for citry: the V3 template parser and compiler, the sandboxed `safe_eval`, and the HTML transform.

It was forked from [django-components/djc-core](https://github.com/django-components/djc-core) at commit [49e20dc](https://github.com/django-components/djc-core/commit/49e20dc); the version continues the djc-core lineage it was forked from.
