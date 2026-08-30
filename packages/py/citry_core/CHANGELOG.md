# Release notes

## Unreleased

## v1.6.1

_30 Aug 2026_

### Fixed

- Installed Citry packages can resolve plain-text Fluent messages together
  with their selected locale and fallback status through the compiled catalog.

## v1.6.0

_22 Aug 2026_

### Added

- Template hosts can declare validated, provider-owned UTF-8 byte spans through
  `ParseOptions`; the parser preserves those claims as ordered foreign body,
  attribute-value, and start-tag source parts.
- The low-level template formatter accepts the same parser options, preserves
  claimed bytes as unknown syntax, and safely rebases their positions while it
  formats Citry-owned source around them.

## v1.5.1

_21 Aug 2026_

### Added

- Detect Alpine attributes across multiple HTML fragments with
  `scan_alpine_html()`.

### Performance

- Large Citry pages canonicalize client graphs and scan Alpine-bearing HTML in
  Rust, while sandboxed built-in attribute access skips redundant checks.

### Fixed

- Source-free Fluent link units retain the punctuation needed to validate and
  run formatter calls.

## v1.5.0

_18 Aug 2026_

### Changed

- Compiled nodes now use `ElementKeyNode` for plain-element `#c-key` and tagged
  `ComponentNode` metadata for component `#c-key`/`#c-ignore`; source-executing
  host runtimes must support both contracts.

### Added

- Compile and analyze Fluent catalogs, with typed messages, locale fallback,
  rich text, exact diagnostics, locale-aware formatting, and strict number,
  percent, date, time, and datetime input.
- Analyze browser expressions and `$component` initializers for exact bindings,
  free references, and synchronous scope writes.
- Format template structure and Python expressions in-process, with a validated
  two-pass hand-off for JavaScript and CSS.
- Read stable parse diagnostics, attribute kinds, and parser-owned directive and
  structural-attribute inventories from Python.

### Fixed

- Embedded formatting now recognizes common `<script>` type forms and rejects
  contradictory provider results.
- Python comments no longer confuse `{{ ... }}` boundaries, and unsupported
  expressions such as `await` return validation errors instead of panicking.
- Parser/compiler fixes: preserve tag-shaped raw text, match HTML tag identity
  case-insensitively, allow template comments between branches and trailing
  `c-for` comments, and keep extension-owned bindings structured.

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
