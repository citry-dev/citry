---
title: Citry
description: A fast, simple, and smart frontend framework for Python that brings the best of Vue, React, Django, and Jinja.
---

# Citry

Citry is a **fast**, **simple**, and **smart** frontend framework for Python
that brings the best of **Vue**, **React**, **Django**, and **Jinja**. You write
HTML with `<c-*>` tags, and citry renders it. The engine is a single Rust core
with Python bindings today, and JavaScript, PHP, Go, and Rust to follow.

This very page is rendered by Citry (version {{ version }}): the docs site
dogfoods the engine it documents.

## Two simple rules

Citry extends HTML with two rules. If you know HTML, you already know most of it.

1. `<c-*>` tags are components. A `<c-Welcome />` tag renders the `Welcome` class.
2. `c-*` attributes are dynamic. Their value is evaluated as an expression, and
   the `c-` prefix is stripped from the rendered attribute.

## A small example

A component pairs a `template` with the data it needs, and can ship its own `js`
and `css` too. Each part reads values prepared in plain Python by `template_data`,
`js_data`, and `css_data`:

```citry
from typing import Any

from citry import Component


class Welcome(Component):
    class Kwargs:
        title: str
        messages: list[str]

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {
            "title": kwargs.title,
            "count": len(kwargs.messages),
        }

    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p>You have {{ count }} new messages.</p>
      </div>
    """

    # js_data values reach the script as `data.*`.
    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"count": len(kwargs.messages)}

    js = """
      $component(({ els, data }) => {
        els[0].title = `${data.count} new messages`;
      });
    """

    # css_data values reach the styles as `var(--*)`.
    def css_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"accent": "tomato"}

    css = """
      .card {
        border-top: 3px solid var(--accent);
      }
    """

component = Welcome(
    title="Welcome back",
    messages=["a", "b", "c"],
)
html = str(component)
```

Only the `template` is required. `js` and `css` are there when a component needs
them, and citry collects each rendered component's scripts and styles for you.

## Highlights

Beyond a single component, citry ships the pieces you need to build a whole
interface. Each highlight links to a page with the details.

### Template syntax

Templates are HTML with a little Python. Drop a value into the output with
`{{ }}`, compute an attribute by prefixing its name with `c-`, and branch or
loop with `<c-if>` and `<c-for>`.

```html
<h1>{{ user.name }}</h1>
<button c-disabled="is_loading">Save</button>
<ul>
  <li c-for="tag in tags">{{ tag }}</li>
  <li c-empty>No tags yet</li>
</ul>
```

See [Expressions](/syntax/expressions/),
[Dynamic attributes](/syntax/dynamic-attributes/),
[Control flow](/syntax/control-flow/), and
[Nested templates](/syntax/nested-templates/).

### Slots

Let a component accept content from its caller. It marks insertion points with
`<c-slot>`; the caller fills them with `<c-fill>` (or passes plain body content
for the default slot). An unfilled slot renders its own fallback.

```html
<c-Modal>
  <c-fill name="default">
    <p>Are you sure?</p>
  </c-fill>
  <c-fill name="actions">
    <button>Confirm</button>
  </c-fill>
</c-Modal>
```

More in [Slots](/concepts/slots/).

### Typing and validation

Declare what a component accepts with a `Kwargs` class. A typo like
`<c-Button lable="Save" />` then stands out against the contract instead of
surfacing as a blank button for a visitor later.

```citry
from citry import Component

class Button(Component):
    class Kwargs:
        label: str                # required
        variant: str = "primary"  # optional

    template = """
      <button c-class="'btn btn-' + variant">
        {{ label }}
      </button>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"label": kwargs.label, "variant": kwargs.variant}
```

More in [Typing and validation](/concepts/typing-and-validation/).

### HTML attributes

Write `class` and `style` as lists and dicts, Vue-style, and citry merges the
pieces into the final string. Spread a whole dict onto a tag with `c-bind`, or
assemble attributes in Python with [format_attrs][citry.format_attrs] and
[merge_attrs][citry.merge_attrs].

```html
<!-- is_active = True -->
<div c-class="['btn', { 'active': is_active }]"></div>
<!-- -> <div class="btn active"></div> -->
```

More in [HTML attributes](/concepts/html-attributes/).

### Client interactivity

Citry owns one Alpine runtime and gives each client-active component an
isolated scope. Pass reactive values down with `$c-props`, author Alpine and
server event handlers on component tags, and keep call-site scope through
slots without adding wrapper elements.

```html
<section x-data="{ selected: false }">
  <c-action-button
    $c-props="{ active: selected }"
    @click="selected = true"
    @c-save="saveSelection({ selected })"
  />
</section>
```

More in [Client interactivity](/concepts/client-interactivity/) and
[Alpine runtime](/advanced/alpine-runtime/).

### Server events

Call typed Python handlers from clicks, forms, State bindings, or polling. A
handler can re-render its component, update another page region, dispatch a
browser event, return JSON, or redirect, all through one ordered return value.

```citry
class ContactIn:
    email: str


class ContactForm(Component):
    class Events:
        def submit(self, data: ContactIn):
            create_account(data.email)
            return ThankYou()

    template = """
      <form @c-submit.prevent="submit">
        <input name="email">
        <button type="submit">Sign up</button>
      </form>
    """
```

More in [Server events](/events/).

### Provide and inject

Pass data to a whole subtree without threading it through every level in
between. A provider sets data under a key with `<c-provide>`, and any descendant
reads it with `self.inject(...)`.

```html
<c-provide key="theme" mode="dark">
  <c-Themed />
</c-provide>
```

`<c-Themed>` never received `mode` as a prop; it reached up the tree for it.
More in [Provide and inject](/concepts/provide-and-inject/).

### HTML fragments

Render a component as a fragment for an HTMX-style swap or a plain `fetch()`
that sets `innerHTML`. Served through a mounted web framework, citry loads the
component's JS and CSS in the browser for you.

```python
card = Card(title="Welcome")
card.render().serialize(deps_strategy="fragment")
```

The chain runs [CitryElement][citry.CitryElement] to
[CitryRender][citry.CitryRender] to an HTML string, with the
[DepsStrategy][citry.DepsStrategy] choosing how the assets ship. More in
[HTML fragments](/advanced/html-fragments/).

### Extensions

Hook into the component lifecycle to watch or change what happens when a
component takes input, computes its data, or renders. Extensions install per
[Citry][citry.Citry] instance and can also add per-component config and their
own CLI commands.

```python
from citry import Citry, Extension

class Timing(Extension):
    name = "timing"

    def on_component_rendered(self, ctx):
        print(f"{type(ctx.component).__name__} rendered")

app = Citry(extensions=[Timing])
```

More in [Extensions](/advanced/extensions/).

### Caching

Cache a complete component subtree with its nested `Cache` policy:

```citry
class ProductCard(Component):
    class Cache:
        enabled = True
        ttl = 300
        version = 1
```

Or cache one transparent template region and vary it on every value that can
change its output:

```html
<c-cache key="account-menu" c-vary="[current_user.id, locale]">
  <c-account-menu c-user="current_user" c-locale="locale" />
</c-cache>
```

Both surfaces use the backend configured on your [Citry][citry.Citry]
instance. The default is process-local; Redis, disk, and Django adapters support
shared deployments. More in [Caching](/advanced/caching/).

### Performance

Most of a template is the same on every render. Promise which inputs stay the
same with [Const][citry.Const], and citry renders those parts once and reuses
the result on later renders.

```python
from citry import Const

Card(cols=Const(3))
```

More in [Performance](/advanced/performance/).

## Where to go next

- [Installation](/getting-started/installation/): install citry and render your
  first component.
- [Template syntax](/syntax/expressions/): expressions, dynamic attributes, and
  control flow.
- [Components](/concepts/components/) and [Slots](/concepts/slots/): the core
  building blocks.
- [Examples](/examples/): real citry components, rendered live.
- [API reference](/reference/): every public class and function.
