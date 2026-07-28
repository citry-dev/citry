---
title: Rendering
description: How a citry component becomes HTML: the compose, render, and serialize phases, and when to reach past str() for finer control.
---

# Rendering

Turning a component into HTML happens in three explicit steps. Most of the time you never see them: you call `str(component)` and get a string back. When you need more control, such as choosing how JS and CSS dependencies are placed, you drive the steps yourself.

## The short version

The everyday path is one line:

```citry
from citry import Component

class Card(Component):
    template = """
      <p>hi</p>
    """

html = str(Card())
```

`str(...)` runs the whole pipeline with default options and hands you the final HTML string. If that is all you need, you can stop here and use it everywhere.

## The three phases

Under `str()` are three phases, each producing its own object.

```python
el = Card()                  # 1. compose  -> CitryElement
rendered = el.render()       # 2. render   -> CitryRender
html = rendered.serialize()  # 3. serialize -> str

assert str(rendered) == html
```

### Compose

Calling a component class does not render anything and does not build a component instance. It returns a [CitryElement][citry.CitryElement], a small record of "what to render": the class, the keyword arguments, and any slots.

```python
from citry import CitryElement

el = Card()
assert isinstance(el, CitryElement)
```

Because a [CitryElement][citry.CitryElement] is just a description, you can render it on its own or pass it into another component and render it there. See [Build a page from components](/getting-started/build-page/) for how one component embeds another.

### Render

`render()` on the element runs the pipeline for the element and everything inside it, and returns a [CitryRender][citry.CitryRender]. This is deliberately an object, not a string. Keeping it as an object means an already-rendered subtree can be reused, passed into another component, or embedded in a `{{ ... }}` expression, carrying its collected JS and CSS with it.

Each call to `render()` mints fresh state, so two calls are not the same render:

```python
el = Card()
assert el.render() is not el.render()
```

If you need a stable identity, hold on to the [CitryElement][citry.CitryElement] or the [CitryRender][citry.CitryRender], not something you read off one of them.

### Serialize

`serialize()` on the render joins the parts into the final HTML string. It stamps a marker attribute on each component's root element and places the collected JS and CSS. Serializing the same render more than once gives the same result each time:

```python
rendered = Card().render()
assert rendered.serialize() == rendered.serialize()  # repeatable
```

The marker it adds is a `data-cid-<id>` attribute on each root element, so the output differs from the raw template even for a static component. The id is different on every render, so check for the marker rather than matching the whole string:

```python
html = str(Card())
assert "data-cid-" in html
```

## Where the methods live

The rendering methods live on the element and the render, not on [Component][citry.Component]:

- `render()` and `__str__` are on [CitryElement][citry.CitryElement].
- `serialize()`, `__str__`, and `__bytes__` are on [CitryRender][citry.CitryRender].

Calling a [Component][citry.Component] subclass gives you a [CitryElement][citry.CitryElement], so you never call `render()` on a component yourself. Real component instances are created only inside the render pipeline.

## Controlling dependency placement

`str()` uses the default options. To choose how JS and CSS dependencies are handled, call `serialize()` directly and pass a strategy. The strategies are `document`, `simple`, `fragment`, and `ignore`, and the position can be `smart`, `prepend`, or `append`:

```python
rendered = Card().render()

# Skip dependency handling entirely.
html = rendered.serialize(deps_strategy="ignore")
```

Each strategy suits a different context: a full HTML document, a smaller standalone piece, an HTML fragment for a live web integration, or no handling at all. For the full picture of how JS and CSS are collected and placed, see [JS and CSS dependencies](/advanced/js-and-css-dependencies/) and [HTML fragments](/advanced/html-fragments/). The [DepsStrategy][citry.DepsStrategy] and [DepsPosition][citry.DepsPosition] symbols name these choices.

## Returning a component from a web route

Because a render comes out as a plain string, putting a component on the web is just returning that string from a route. Citry does not tie a route to a component, so you keep the web framework you already use and hand its HTML response the result of `str(...)`.

Here is a FastAPI route that renders a component and returns it:

```citry
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from citry import Component

app = FastAPI()

class Greeting(Component):
    template = """
      <p>Hello, {{ name }}!</p>
    """

    def template_data(self, kwargs, slots):
        return {"name": kwargs["name"]}

@app.get("/hello")
def hello(name: str = "world") -> HTMLResponse:
    return HTMLResponse(str(Greeting(name=name)))
```

The same one line fits any framework: Flask sends a returned string as HTML, so `return str(Greeting(name=name))` is enough, and Django wraps it with `HttpResponse(str(Greeting(name=name)))`. Only the response type is your framework's; the component code does not change.

For HTMX-style updates, where the browser swaps a chunk of HTML into a page that is already loaded and citry wires up the component's JavaScript and CSS, serialize with the `"fragment"` strategy instead and return that string the same way. Fragments that carry JavaScript or CSS need citry mounted on your app so it can build the script URLs. See [HTML fragments](/advanced/html-fragments/) for the browser side and [Web frameworks](/web-frameworks/) for mounting.

## The render context

A [CitryRender][citry.CitryRender] carries the [CitryContext][citry.CitryContext] it was produced with. The context is render-scoped state for one render pass. Its `variables` hold the template variables a component's `template_data` produced, and those do not cross into child components: each child gets its own variables from its own `template_data`. Values provided for injection flow down the tree, and extension scratch space merges up. Provide and inject is covered in [Provide and inject](/concepts/provide-and-inject/).

```python
rendered = Card().render()
assert isinstance(rendered.context, CitryContext)
```

## Components are always isolated

A citry component sees only what is given to it. Its template reads the variables its own `template_data` returns, and `template_data` can pull in values shared from an ancestor through provide and inject. What a component never receives is the variables of the template or component that renders it, not even the one wrapped right around it.

This is the boundary the render context describes above: each child gets its own variables from its own `template_data`, and they do not cross between components. Isolation is the only mode, so there is nothing to switch on or off. If you come from a template engine where an inner scope inherits the variables around it, the citry rule is shorter: what a component needs, you give it.

You give a component data in three ways:

- As props, the keyword arguments you call it with (`Greeting(name="Ada")`).
- Through provide and inject, for values shared down a whole subtree without threading them through every call. See [Provide and inject](/concepts/provide-and-inject/).
- As slot content, markup the parent fills in. Slots have their own page under [Slots](/concepts/slots/).

## Building a render by hand

Since a [CitryRender][citry.CitryRender] is a plain object, you can construct one from ordered parts, where each part is a string or another nested [CitryRender][citry.CitryRender]. Serializing joins them in order and recurses into nested renders:

```python
from citry import CitryContext, CitryRender

ctx = CitryContext()
inner = CitryRender(parts=["<span>inner</span>"], context=ctx)
outer = CitryRender(parts=["<p>", inner, "</p>"], context=ctx)

assert outer.serialize() == "<p><span>inner</span></p>"
```

This is the mechanism behind embedding one pre-rendered subtree inside another: the nested render inlines its own HTML.

## Reference

For the full API of every object named here, see the Rendering reference category, including [CitryElement][citry.CitryElement], [CitryRender][citry.CitryRender], and [CitryContext][citry.CitryContext].
