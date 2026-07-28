---
title: Built-in tags
description: The c-* tags Citry provides in every component template.
---

# Built-in tags

Citry provides these tags in every component template. You do not need to
register or import them.

- **Control flow:** [`<c-if>`](#c-if), [`<c-elif>`](#c-elif),
  [`<c-else>`](#c-else), [`<c-for>`](#c-for), and
  [`<c-empty>`](#c-empty)
- **Slots:** [`<c-slot>`](#c-slot) and [`<c-fill>`](#c-fill)
- **Dynamic output:** [`<c-component>`](#c-component) and
  [`<c-element>`](#c-element)
- **Data and resilience:** [`<c-provide>`](#c-provide),
  [`<c-cache>`](#c-cache), and
  [`<c-error-fallback>`](#c-error-fallback)
- **Page assets:** [`<c-css>`](#c-css) and [`<c-js>`](#c-js)
- **Literal template text:** [`<c-raw>`](#c-raw)

## Control flow

<h3 id="c-if"><code>&lt;c-if&gt;</code></h3>

Render a block when its `cond` expression is truthy. An `<c-if>` may be
followed by any number of `<c-elif>` branches and one `<c-else>` branch.

```citry
<c-if cond="is_admin">
  <p>Administrator tools</p>
</c-if>
```

The [control-flow guide](/syntax/control-flow/) covers inline `c-if`
attributes, truthiness, and branch ordering.

<h3 id="c-elif"><code>&lt;c-elif&gt;</code></h3>

Add another condition to an `<c-if>` chain. Citry renders this branch only
when every earlier condition was false and this branch's `cond` is truthy.

```citry
<c-if cond="is_admin">Admin</c-if>
<c-elif cond="is_editor">Editor</c-elif>
```

<h3 id="c-else"><code>&lt;c-else&gt;</code></h3>

Add the final fallback to an `<c-if>` chain. `<c-else>` has no `cond`
attribute.

```citry
<c-if cond="is_signed_in">Account</c-if>
<c-else>Sign in</c-else>
```

<h3 id="c-for"><code>&lt;c-for&gt;</code></h3>

Repeat a block for every value in an iterable. Its `each` attribute uses a
Python-style target and expression.

```citry
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
```

Read [Control flow](/syntax/control-flow/#loops) for unpacking, filtering,
and the `loop` helper.

<h3 id="c-empty"><code>&lt;c-empty&gt;</code></h3>

Show an empty state when the `<c-for>` immediately before it produces no
items.

```citry
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
<c-empty>No books yet.</c-empty>
```

## Slots

<h3 id="c-slot"><code>&lt;c-slot&gt;</code></h3>

Mark a place where another template can add content. Leave out `name` for the
default slot, or name the slot when a component has more than one. Content
inside the tag is its fallback.

```citry
<article>
  <c-slot />
  <footer>
    <c-slot name="footer">No footer supplied.</c-slot>
  </footer>
</article>
```

See [Slots](/concepts/slots/) for required slots, slot data, dynamic names,
and fallback details.

<h3 id="c-fill"><code>&lt;c-fill&gt;</code></h3>

Choose which named slot receives a block of content when you use a component.
You can pass plain body content when you only need the default slot.

```citry
<c-Panel>
  <c-fill name="footer">
    <a href="/help/">Get help</a>
  </c-fill>
</c-Panel>
```

## Dynamic output

<c-builtin tag="component" c-level="3" />

<c-builtin tag="element" c-level="3" />

Read [Dynamic components](/advanced/dynamic-components/) for complete examples
and the difference between component names and HTML tag names.

## Data and resilience

<c-builtin tag="provide" c-level="3" />

<c-builtin tag="cache" c-level="3" />

<c-builtin tag="error-fallback" c-level="3" />

## Page assets

<c-builtin tag="css" c-level="3" />

<c-builtin tag="js" c-level="3" />

The [JS and CSS dependencies guide][dependencies-guide] explains collection,
placement, and serialization strategies.

## Literal template text

<h3 id="c-raw"><code>&lt;c-raw&gt;</code></h3>

Keep template-looking text unchanged. Citry does not evaluate expressions or
component tags inside `<c-raw>`.

```citry
--8<-- "docs_site/snippets/builtin_raw.html"
```

[dependencies-guide]: /advanced/js-and-css-dependencies/
