---
title: Component JavaScript and CSS
description: Give a Citry component its own JavaScript, CSS, and per-render browser data.
---

# Component JavaScript and CSS

A component often needs a little browser code or a few styles of its own: a
search box that takes focus, a chart that draws itself, a banner in a color
the page chooses. Put that code on the component, in `js` and `css`. Citry
adds it to every page that renders the component, once per page however many
times the component appears.

This page covers code that belongs to one component. To add a library or a
shared file, see [Dependency files](/advanced/dependency-files/). To choose
where the tags go in the page, see
[Place JavaScript and CSS](/advanced/asset-placement/).

## Add JavaScript and CSS to a component

```citry
from citry import Component


class SearchBox(Component):
    template = """
      <input
        ref="input"
        class="search-box"
        type="search"
      />
    """

    js = """
      $component({
        onServerRender({ component }) {
          component.$refs.input.focus();
        },
      });
    """

    css = """
      .search-box {
        width: 100%;
      }
    """
```

[`$component()`][$component] registers the browser code for each rendered
`SearchBox`. Its `onServerRender` callback runs when the component appears
on the page, and again each time a server event renders it again.
`component` is that rendered component, and `component.$refs.input` is the
element marked with `ref="input"` in the template.

`onServerRender` may return a function. Citry calls it before the next
`onServerRender` call and when the component is removed, so you can undo
what the callback set up. Here the search box takes focus when the user
presses `/`, and stops listening when it goes away:

```javascript
$component({
  onServerRender({ component }) {
    const onKey = (event) => {
      if (event.key !== "/") return;
      // Keep the "/" out of the search box.
      event.preventDefault();
      component.$refs.input.focus();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  },
});
```

Code outside `$component()` runs once, when the script loads. Use it for
setup that the whole page shares. Code inside `onServerRender` runs for each
rendered component.

Each component's script runs inside its own function, so its top-level
variables do not clash with other scripts on the page.
[Browser APIs](/reference/browser-apis/#component) lists everything that
`$component()` and `onServerRender` accept.

## Send data from Python to JavaScript

Return a mapping from [`js_data()`][citry.Component.js_data] to give one
render's values to its JavaScript. Each key becomes a field on `component`:

```citry
from citry import Component


class Sparkline(Component):
    class Kwargs:
        points: list[int]

    def js_data(self, kwargs: Kwargs, slots):
        return {"points": kwargs.points}

    template = """
      <canvas
        ref="canvas"
        width="120"
        height="30"
      ></canvas>
    """

    js = """
      $component({
        onServerRender({ component }) {
          // drawSparkline comes from a charting library.
          drawSparkline(component.$refs.canvas, component.points);
        },
      });
    """
```

Two sparklines on one page each get their own `points`. Vue expressions in
the template can read the same fields.

Citry sends the data to the browser as JSON, so the mapping must follow
these rules:

- every key is a `str`;
- no key starts with `$` or `_`, and no key is `citryId`, because Vue and
  Citry already use those names on `component`;
- every value can be turned into JSON, and numbers are finite (`NaN` and
  infinity are rejected).

## Send values from Python to CSS

Return a mapping from [`css_data()`][citry.Component.css_data] to give one
render's values to its CSS. Each key becomes a CSS custom property that
you read with `var(--<key>)`:

```citry
from citry import Component


class Banner(Component):
    class Kwargs:
        color: str = "#fde68a"

    def css_data(self, kwargs: Kwargs, slots):
        return {"banner_color": kwargs.color}

    template = """
      <div class="banner">
        <c-slot />
      </div>
    """

    css = """
      .banner {
        background: var(--banner_color);
      }
    """
```

The property applies only to that render's elements, so two banners with
different colors show different colors. The component needs its own `css`
for this to work; without it, Citry does not emit the values.

Each value must be a string, a finite number (not a boolean), or
`None`. A key must be a
string that is valid as the name of a custom property, without the leading
`--`. Citry quotes a string that contains spaces, unless it starts with a
CSS function such as `calc(...)` or `rgba(...)`. It raises `ValueError` for
a value that could break out of the generated CSS, such as one with a
top-level `;` or a `</style` end tag.

!!! warning "Keep secrets out of CSS data"

    Citry delivers these values as a stylesheet at a URL. Anyone who has
    the URL can download it, so never put a secret in `css_data()`.

## Check the data that a data method returns

Declare a nested `JsData` or `CssData` class to have Citry check the names
that `js_data()` or `css_data()` returns. A missing or unexpected name then
raises `TypeError` when the component renders. Return either an instance of
the class or a plain dictionary:

```citry
class Sparkline(Component):
    class JsData:
        points: list[int]

    def js_data(self, kwargs: Kwargs, slots) -> JsData:
        return self.JsData(points=kwargs.points)
```

A plain annotated class checks names, not the type of each value. See
[Inputs and validation](/concepts/inputs-and-validation/) for schema styles
that also check types.

## Keep the code in separate files

Use `js_file` and `css_file` to keep the code in files next to the
component:

```citry
from citry import Component


class Calendar(Component):
    template_file = "calendar.html"
    js_file = "calendar.js"
    css_file = "calendar.css"
```

Citry finds these files the same way it finds `template_file`. Set either
`js` or `js_file`, not both, and either `css` or `css_file`. Setting both
raises `ValueError` when the class is defined.

## Highlight inline code in your editor

JetBrains editors highlight a string in the language named by a comment
just above it:

```citry
class Calendar(Component):
    # language=HTML
    template = """
      <div class="calendar">Today</div>
    """

    # language=CSS
    css = """
      .calendar {
        width: 12rem;
      }
    """
```

Some VS Code extensions read type annotations instead, such as
`template: "html"`, `css: "css"`, and `js: "js"`. These hints change only
how the editor shows the code.

## Next steps

- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files that several components use.
- [Place JavaScript and CSS](/advanced/asset-placement/) chooses where the
  tags go in the page.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [HTML fragments](/advanced/html-fragments/) adds the JavaScript and CSS
  of new components to a page that is already open.
