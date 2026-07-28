# Component-first `$c-*` syntax spike

Status: research evidence only. This spike changes no production grammar,
compiler, renderer, or client runtime.

## Conclusion

`$c-*` is a viable HTML namespace for directives owned by the Citry client
runtime. In particular, `$c-props` has the useful property that stock Alpine
3.15.12 ignores it while Citry's current V3 pipeline can carry it from source
to a component kwarg or rendered HTML attribute.

It is not transparent to every adjacent syntax:

- A raw CSS selector such as `[$c-props]` is invalid. Code must use
  `[${CSS.escape("$c-props")}]`, `getAttribute`, or attribute iteration.
- Alpine `x-bind:$c-props` and an `$c-props` key inside an Alpine `x-bind`
  object do not work on Alpine 3.15.12. Both forms misparse the binding name
  and emit numeric attributes for characters in the value string. Citry must
  own `$c-props` evaluation. Server-side `c-bind` remains a working way to
  emit or omit the directive dynamically.
- HTML parsing lowercases the name. The authoring contract should require the
  canonical lowercase spelling.
- The name works in HTML-parsed SVG but is not a valid XML attribute name.
  XHTML and standalone XML/SVG serialization therefore need a different
  encoding if Citry ever supports them.

None of these findings decides whether the component-first runtime should use
this spelling. They show that the spelling itself is practical for Citry's
current HTML delivery model.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it.

## Prior art checked

- The V3 attribute rule accepts `$` because it excludes delimiters rather than
  using an identifier grammar
  ([`grammar.pest:219`](../../../crates/citry_template_parser/src/grammar.pest#L219),
  [`grammar.pest:231`](../../../crates/citry_template_parser/src/grammar.pest#L231)).
- Attribute classification is string-based: `c-*` is a Python expression and
  any other ordinary name is static
  ([`parser.rs:875`](../../../crates/citry_template_parser/src/parser.rs#L875),
  [`parser.rs:928`](../../../crates/citry_template_parser/src/parser.rs#L928),
  [`parser.rs:1014`](../../../crates/citry_template_parser/src/parser.rs#L1014)).
- Plain-element and component rendering both remove one leading `c-` from a
  dynamic attribute. Their `c-bind` mappings preserve arbitrary string keys
  ([`nodes/__init__.py:613`](../../../packages/py/citry/citry/nodes/__init__.py#L613),
  [`nodes/__init__.py:833`](../../../packages/py/citry/citry/nodes/__init__.py#L833)).
- Alpine filters for its configured `x-` prefix and parses directive arguments
  with a character class that excludes `$`
  (`packages/js/citry-client/node_modules/alpinejs/src/directives.js:177`,
  `packages/js/citry-client/node_modules/alpinejs/src/directives.js:189`,
  from the locally installed pinned package).
- Alpine object bindings rewrite an ordinary key to an `x-bind:<key>` virtual
  directive, which reaches the same argument parser
  (`packages/js/citry-client/node_modules/alpinejs/src/binds.js:37`).
- Alpine morph compares and patches arbitrary attribute names through the DOM
  attribute APIs
  (`packages/js/citry-client/node_modules/@alpinejs/morph/src/morph.js:160`).
- Existing parser tests for dynamic attributes and spreads were read before
  constructing the probes: `tag_parser_dynamic_attrs.rs`,
  `tag_parser_spreads.rs`, `tag_compiler_dynamic.rs`, and
  `tag_compiler_meta_attrs.rs`.

The old browser observation in the grammar comment at `grammar.pest:246` says
that a leading `$` was dropped by Chrome 142. That result did not reproduce in
any current pinned browser below. The checked-in harness is the stronger and
repeatable evidence for this design exploration.

## V3 parse, compile, and render results

The server harness uses the real `citry_core` V3 parser and compiler, then real
`Component`, `ComponentNode`, `ElementAttrsNode`, and serializer paths.

| Source form | Current classification | Current result |
|---|---|---|
| `$c-props="{ count: localCount }"` | Static HTML attribute | The value is carried literally and is not parsed as Python. On a component tag the child receives a `"$c-props"` kwarg. |
| `c-$c-props="props_source"` | Python expression attribute | V3 evaluates `props_source`, removes the leading `c-`, and produces the `"$c-props"` key. |
| `c-bind="attrs"`, where `attrs` contains `"$c-props"` | Python mapping spread | The key is preserved on both plain elements and component kwargs. A `None` value is omitted on a plain element. |

Observed component kwargs were:

```json
{
  "direct": {"$c-props": "{ count: localCount }"},
  "dynamic": {"$c-props": "{ count: 2 }"},
  "spread": {"$c-props": "{ count: 3 }"}
}
```

Observed plain-element HTML after removing unrelated Citry instance markers
was:

```html
<div $c-props="{ count: 1 }"></div>
<div $c-props="{ count: 2 }"></div>
<div $c-props="{ count: 3 }"></div>
<div></div>
```

The last element came from `c-bind={"$c-props": None}`.

Two generic-attribute behaviors need an explicit `$c-props` contract:

- `$c-props=""` currently compiles to a bare `$c-props` boolean attribute.
  Props probably require a non-empty expression, as the accepted `x-props`
  design does.
- The parser preserves authored case while the HTML parser lowercases it.
  Static validation should reject noncanonical casing before the browser can
  silently normalize it.

Exact duplicate `$c-props` attributes are already rejected by the generic V3
duplicate check. `$c-props`, `$c-on:click.once`, and `$c-model` all parse and
compile as ordinary static attributes today. That confirms namespace
transport, not semantics for those additional names.

## Browser and DOM results

The browser harness ran three identical passes on each engine:

| Engine | Version | Result |
|---|---:|---|
| Chromium | 149.0.7827.55 | Pass |
| Firefox | 151.0 | Pass |
| WebKit | 26.5 | Pass |

All three engines agreed on these results:

- HTML `innerHTML`, `DOMParser` with `text/html`, and `insertAdjacentHTML`
  preserve `$c-props`, `c-$c-props`, and `$c-on:click.once`.
- `getAttribute`, `setAttribute`, `removeAttribute`, `toggleAttribute`,
  `getAttributeNames`, and `NamedNodeMap.getNamedItem` accept the names.
- `outerHTML` serialization preserves the names.
- `cloneNode(true)`, template contents, and cloned template contents preserve
  the names and values.
- `MutationObserver` reports the exact `"$c-props"` attribute name for change,
  removal, and addition.
- Table foster-parenting, a contextual `tbody` fragment, `select` options,
  HTML-parsed SVG, and a contextual SVG fragment preserve the attribute.
- `setAttribute("$c-model", "state")` succeeds on an SVG element created in
  the SVG namespace.
- XML parsing of an SVG string containing `$c-props` produces a parser error.
  Firefox also writes that XML parse failure to the console.

The CSS selector result was equally consistent:

```js
document.querySelectorAll("[$c-props]")                 // SyntaxError
document.querySelectorAll(`[${CSS.escape("$c-props")}]`) // works
```

## Alpine coexistence and morph results

A page used real `x-data` and `x-text` beside `$c-props`. Alpine updated the
text reactively from `1` to `2`, left the `$c-props` expression unchanged, and
never invoked a registered Alpine directive named `c-props`. An Alpine
`interceptInit` callback could still inspect the ordinary attribute. This is
the desired division if Citry owns `$c-*` while Alpine continues to own `x-*`.

The Alpine binding forms are a concrete incompatibility:

```html
<div x-data="{ bag: { '$c-props': expression } }" x-bind="bag"></div>
<div x-bind:$c-props="expression"></div>
```

With a string directive value, both forms emitted attributes named `0`, `1`,
`2`, and so on for the string's character indexes. Neither emitted
`$c-props`. A component-first design must not advertise Alpine `x-bind` as a
way to create Citry directives. Reactive changes belong inside the
`$c-props` expression, and server-time conditional presence can use Citry's
`c-bind`.

Real `@alpinejs/morph` 3.15.12 changed `$c-props` from `v1` to `v2`, removed
it when absent from the new HTML, and added it back as `v3`. The root element
kept its identity and the mutation observer saw all three changes. No special
morph adapter is required for the attribute name itself.

## Selected directive contract

The maintainer selected `$c-props` and graph-first Alpine on 2026-07-20. The
production design specifies these points rather than inheriting generic
attributes by accident:

1. `$c-props` is a Citry client expression and must be non-empty.
2. It is valid on a Citry component call site and follows the same placement,
   relocation, source-scope, and `c-bind` rules already accepted for
   `x-props`.
3. `c-$c-props` is public syntax. It evaluates Python and returns the complete
   client expression string. `c-bind` is also allowed.
4. The runtime scans with attribute APIs or escaped selectors. It never
   interpolates `$c-*` directly into a CSS selector.
5. Stock Alpine ignores `$c-*`; Citry evaluates it. Alpine `x-bind` does not
   create or update Citry directives.
6. Authoring uses lowercase names. HTML is the supported serialization mode.

The existing static error for client props on a non-component tag would need
to move from the `x-props` spelling to `$c-props`. The server renderer would
also need to extract direct, `c-$c-props`, and `c-bind` contributions into the
same structured client binding record. This spike proves that all three forms reach
the extraction point; it does not implement extraction.

## Reproduction

Server parse, compile, and render harness:

```bash
uv run python docs/design/alpinejs/component_first_syntax_server.py
```

Post-A0 note: the server harness now treats the report's original generic
plain-element round trip as historical evidence and locks the accepted
component-only placement, non-empty value, and dynamic-key diagnostics. The
browser transport harness remains the evidence for HTML preserving the name.

Cross-browser DOM, Alpine, and morph harness:

```bash
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
    python docs/design/alpinejs/component_first_syntax_browser.py
```

Both commands assert every result before printing the observed JSON. The
browser command requires the repository's cached Playwright browsers and
local pinned Alpine packages.

## What this spike does not prove

This spike does not implement or validate `$c-props` expression evaluation,
component-boundary relocation, source-scope ownership, root groups, rootless
regions, cleanup, props declarations, or error reporting. It also does not
test third-party HTML sanitizers, minifiers, editor tooling, or XML delivery.
Those are separate acceptance concerns if the syntax is selected.
