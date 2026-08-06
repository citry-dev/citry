---
title: Rendering
description: Compose components, render a fresh occurrence, and serialize it to HTML while keeping each component's data isolated.
---

# Rendering

Most pages only need `str(MyPage(...))`. That one call turns a component tree
into HTML with Citry's normal JavaScript and CSS handling.

Reach for the individual rendering steps when you need to add a per-request
template value, choose how dependencies are placed, or hold on to a composed
component for later.

## Use the short path for ordinary HTML

```citry
from citry import Component


class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p>Hello, {{ name }}!</p>
    """


html = str(Greeting(name="Ada"))
```

`str(...)` performs all three rendering steps with their default options.

## Follow the three steps when you need control

Citry separates composing a component, rendering one occurrence, and turning
the result into an HTML string:

```python
element = Greeting(name="Ada")
rendered = element.render()
html = rendered.serialize()
```

Each line has a different result:

1. Calling the class creates a [`CitryElement`][citry.CitryElement]. It
   remembers the component class, keyword arguments, and slots.
2. [`render()`][citry.CitryElement.render] creates a fresh
   [`CitryRender`][citry.CitryRender] for the element and everything inside
   it.
3. [`serialize()`][citry.CitryRender.serialize] produces the final string and
   places the collected JavaScript and CSS.

`render()` does not return a string. This distinction lets Citry keep the
component tree and its collected dependencies together until serialization.

## Reuse an element for more than one occurrence

A `CitryElement` is a description, so you can render it more than once. Each
call creates a separate occurrence with fresh render state:

```python
greeting = Greeting(name="Ada")

first = greeting.render()
second = greeting.render()

assert first is not second
```

You may also insert the same element into two expressions in a parent. Citry
renders it afresh at each position.

A `CitryRender` is different: it represents one already-rendered occurrence.
You may serialize that result repeatedly, and the result is repeatable:

```python
rendered = Greeting(name="Ada").render()

assert rendered.serialize() == rendered.serialize()
```

Do not insert the same `CitryRender` into two positions in one final tree.
One rendered occurrence belongs to one physical position, so serialization
raises a `RuntimeError` if it finds the same occurrence twice. Keep and reuse
the element when you need two occurrences; keep the render when you need to
serialize one occurrence again.

## Add values for one whole render

Pass `template_globals` to `render()` for values that every component in one
tree may read. This suits request-wide data such as the current user's name,
locale, or request ID:

```citry
from citry import Component


class PageFooter(Component):
    template = """
      <footer>{{ site_name }}</footer>
    """


class AccountPage(Component):
    template = """
      <main>Account</main>
      <c-page-footer />
    """


rendered = AccountPage().render(
    template_globals={"site_name": "Citry"},
)
html = rendered.serialize()
```

The value reaches `AccountPage`, `PageFooter`, nested elements, and slot
content in this render. It does not change later renders.

You can also set defaults for every render owned by a
[`Citry`][citry.Citry] instance through its `template_globals`. Values follow
this order, with later entries winning:

1. the Citry instance's global value;
2. the value passed to this `render()` call; and
3. the current component's own `template_data()` value.

The component therefore keeps control of names it returns itself. Render
globals add shared defaults; they do not overwrite component data.

## Pass ordinary component data explicitly

A child does not inherit the variables returned by its parent's
[`template_data()`][citry.Component.template_data]. Each component receives
its own keyword arguments and slots, then builds its own template data.

Pass a value as a prop when one child needs it:

```citry-html
<main>
  <h1>{{ account_name }}</h1>
  <c-account-summary c-name="account_name" />
</main>
```

Use [provide and inject](/concepts/provide-and-inject/) when many descendants
need the same value without threading it through every component. Use
[slots](/concepts/slots/) when a parent supplies content for a child to place.
Use `template_globals` only for a value that should truly be visible to the
whole render.

This isolation makes a component predictable: its surrounding template does
not silently change the names that resolve inside it.

## Choose dependency placement at serialization

`str(element)` uses the default dependency strategy. Call `serialize()`
yourself when the HTML is going into a different context:

```python
rendered = Greeting(name="Ada").render()

html = rendered.serialize(deps_strategy="ignore")
```

For a full document, a standalone piece, or a live fragment, choose the
strategy that matches where the HTML will be used. See
[Asset placement](/advanced/asset-placement/) for `document`, `simple`, and
`ignore`, and
[HTML fragments](/advanced/html-fragments/) for the `fragment` strategy.

Web frameworks only need the serialized string. The
[Web frameworks guide](/web-frameworks/) shows how to return it from a route
and how to mount Citry when browser features need supporting endpoints.
