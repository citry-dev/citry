# Vue slot props (#445)

- **Pull request:** [#445](https://github.com/citry-dev/citry/pull/445),
  merged 2026-10-27 (7347b21fb)
- **Reviewer:** a separate reviewing agent, helped by a second agent that
  ran the browser checks. A third agent reran the report's main checks and
  tried more routes. Two later review rounds, also by separate agents,
  checked the fixes from the earlier rounds.
- **Code:** the parser checks for `<c-slot>` props and the `<c-fill>`
  `v-slot` pattern (`validate_slot_prop` and `validate_fill_slot_pattern`
  in `crates/citry_template_parser/src/parser.rs`,
  `browser_slot_pattern_problem` in
  `crates/citry_template_parser/src/browser.rs`); the code that reads them
  from the template (`_slot_vue_props` and `_fill_vue_pattern` in
  `packages/py/citry/citry/nodes/__init__.py`); the code that writes the
  pattern into the fill's slot function (`fill_binding_pattern` in
  `packages/py/citry/citry/_vue/direct_capture.py`); the cache entry
  checks in `packages/py/citry/citry/ext/cache/artifact.py`; tests in
  `packages/py/citry/tests/test_vue_slot_props.py` and
  `packages/py/citry/tests/e2e/test_vue_slot_props_e2e.py`

## Who controls the input

A component can now pass its browser data to the content a caller puts in
its slot. The component writes `<c-slot name="item" :row="row" />`, and
the caller's fill reads it with `<c-fill name="item" v-slot="{ row }">`.
Citry writes both into the components' Vue templates, which it compiles
on the server into code the browser runs:

- **The prop name and its expression** (`:row="row"`) come from the
  template author. The browser runs the expression as JavaScript in the
  component that has the slot.
- **The `v-slot` pattern** (`{ row }`) comes from the template author. The
  browser uses it as the parameters of the function Vue calls to render
  the fill (the fill's slot function).
- **The prop values** come from that component's browser data, such as
  `js_data()`, which can hold request data or stored data. The browser does
  whatever the fill does with them: shows them as text, sets an attribute,
  follows a URL, or parses HTML with `v-html`.
- **Cached copies** of the props and the pattern come from the render
  cache store.

So data must never choose the prop name, the expression, or the pattern.
It may fill in values, and the fill's own code decides where they land.

## How it was checked

The reviewer read the parser checks and the Python code that writes the
outlet (the Vue `<slot>` element Citry generates for `<c-slot>`) and the
fill. Then it tried to get data, rather than the author, to choose the
code:

- Python data through `c-bind` on both tags, with keys such as `:row`,
  `v-bind:row` and `v-slot`, in many spellings (capitals, leading spaces,
  tabs, zero-width spaces, `c-` prefixes).
- A Python `{{ ... }}` expression inside a prop or a pattern.
- A value that another template language fills in (a part of the template
  an extension marks as belonging to that language), in plain and Vue
  modes, inside nested template attributes, and through
  `render_template()`.
- Authored values with quote characters, encoded quotes, `>` or
  `</slot>`, and JavaScript escapes in names.
- Names like Citry's internal ones, and names such as `__proto__` and
  `constructor`.
- Changed cache entries for the stored props and pattern.
- Fills passed on by a middle component, such as `CTabs`.

A second agent ran 11 cases in Chromium. Values from `js_data()` tried
markup and attribute breakouts, `{{ ... }}`, `javascript:` URLs, and
`style` breakouts. They were bound through `v-text`, `:title`, `:href`,
`:src`, `:style` and `v-html` inside a scoped fill. Python slot text with
`{{ ... }}` was shown beside them. Each page was loaded three ways:

- hydrated, where Vue takes over the server's HTML;
- rebuilt by Vue in the browser (what happens when `serialize()` gets a
  CSP nonce), without a CSP header;
- rebuilt the same way, with a CSP header.

It also loaded each page's server HTML with the scripts removed and
checked it for event attributes and `javascript:` URLs. For the first
five cases, it built the same slot in a plain Vue 3.5.44 page to compare.

## Ruled out

- **Python data choosing code:** `c-bind` keys that name a Vue prop or
  `v-slot` fail at render. Spellings close to these, such as one with a
  leading space, stay ordinary Python slot data that never reaches the
  outlet. The props and the pattern are read once, from the attributes
  written in the template.
- **Extensions:** hooks that change a tag's attributes at render run
  after Citry has read the props and the pattern, so they cannot change
  them.
- **Template text choosing code:** a Python `{{ ... }}` expression, or a
  value another template language fills in, inside a prop or a pattern
  fails when the template is parsed.
- **Breaking out of the generated Vue template:** the parser refuses prop
  names that hold `=`, `<`, `>` or `/`, so a name cannot end the tag.
  Citry writes each expression between the quote character it does not
  contain, so it cannot end its attribute. `v-slot` accepts only one
  object pattern or one name, so the pattern cannot close the slot
  function's parameters early.
- **Prop values becoming markup or code:** text and attributes stayed
  escaped in all three ways. A `:style` string could not end its
  attribute. Python text inside a scoped fill stayed text, `{{ ... }}`
  included. A data key named `__proto__` changed no object's prototype.
  `v-html` and `javascript:` URLs ran only where the author bound them,
  exactly as in plain Vue, and the CSP header blocked them. Binding data
  there is the app author's choice, as in plain Vue.
- **Data reaching the server HTML:** in the reviewed code, the server
  wrote no slot prop value into the page. Values reached the browser only
  inside the page's JSON data, where `<` was seen escaped as `<`.
- **Fills passed on by a middle component:** the middle component passes
  the fill only the props of the outlet that renders the fill. Those hold
  author-written props and the names Citry adds to every fill.
- **Template text built from request data:** if an app passes request
  text to `render_template()`, that text chooses Vue code, as it would
  through any Vue attribute. This is author-only by design; the
  `render_template()` docstring says its source must be trusted.
- **Changed cache entries:** anyone who can write to the cache store can
  already inject HTML that Citry trusts, and the caching docs say to
  protect the store like a database. A changed slot entry does not widen
  that.

## Fixed during the review

- **Character references in `v-slot`:** the parser checked the pattern as
  written, while Vue decodes character references such as `&#39;` first.
  So an author could hide a reserved name from the parser's checks. Only
  the template author writes the pattern, so this was not a route for
  data. The parser now refuses an `&` in `v-slot`.
- **Another template language, checked in Rust:** a value from another
  template language inside a prop or a pattern was refused only by the
  Python code. The Rust parser now refuses it too, so every host language
  gets the check.
- **Cache entry checks:** the check's comment overstated what it
  protects. It now says only that an entry the parser would not accept
  becomes a cache miss, and that the expressions are stored like any other
  compiled template text. The check parses all stored props on one
  `<c-slot>` and the pattern on a `<c-fill>`, and refuses a pattern with
  spaces around it.

## Not tested

- The security browser checks ran on an earlier commit of the pull
  request (22c5ae030). The later rounds checked the fixes by reading the
  code, with server-side checks and the feature's tests, plus a few
  correctness checks in Chromium. They did not repeat the security browser
  checks. The last cache check changes were checked by tests only.
- A value holding `</script>` in the page's JSON data.
- Other ways Vue rebuilds the page in the browser
  (`security_javascript="warn"`, `ssr=False`, a custom `deps_position`).
- A changed cache entry under a CSP header.
- An `on_slot_rendered` hook that returns a different fill.
- Firefox and WebKit.
- Server HTML that holds slot prop values. The server started writing
  these in [#447](https://github.com/citry-dev/citry/pull/447), after this
  review.

## Follow-ups

- On `<c-slot>` and `<c-fill>`, a refused `c-bind` key raises a plain
  `RuntimeError`, while the same refusal on an element raises
  `citry.VueCodeError`. Code that catches `VueCodeError` misses it.
- Done in [#562](https://github.com/citry-dev/citry/pull/562): the
  "Scoped slots" docs (`docs_site/content/vue/slots.md`) now say that the
  `:` binding on `<c-slot>` and the `v-slot` value on `<c-fill>` are part
  of the template, so only the template author writes them.
- Done in [#562](https://github.com/citry-dev/citry/pull/562): the Vue
  slots page now warns against binding request data with `v-html`,
  `:href` or `:src`.
- `v-slot` refuses names that start with `$`, `_` or `citry`, which Citry
  uses for its own values, but a `v-for` alias accepts them, so an author
  can reuse one by mistake. Only the template author writes either one.
