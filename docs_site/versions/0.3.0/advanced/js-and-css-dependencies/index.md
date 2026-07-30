---
title: JS and CSS dependencies
url: https://citry.dev/v/0.3.0/advanced/js-and-css-dependencies/
description: "How citry collects each rendered component's JS and CSS, passes per-instance data with js_data and css_data, and places it at c-css and c-js."
---
# JS and CSS dependencies

Every component can ship its own JavaScript and CSS. As a page renders, citry
collects the JS and CSS of each component that appeared, deduplicates it, and
places it where you asked. This page covers component-owned assets,
third-party dependencies, per-instance data, asset placement, and dependency
strategies.

## Declare JS and CSS on a component

A component's JS and CSS are class attributes, written as multiline strings.
Inside the JS, [`$component(...)`](/v/0.3.0/reference/browser-apis/#component) registers a callback that citry
runs once per rendered instance of the component.


```citry
from citry import Component

class Chart(Component):
    template = """
      <div class="chart"></div>
    """
    js = """
      $component(({ els, data }) => {
        draw(els[0], data.points);
      });
    """
    css = """
      .chart {
        height: var(--h);
      }
    """

    def js_data(self, kwargs, slots):
        return {"points": kwargs["points"]}   # reaches the JS as data.points

    def css_data(self, kwargs, slots):
        return {"h": "240px"}                  # reaches the CSS as var(--h)
```


Instead of inline strings you can point at external files with `js_file` and
`css_file`, resolved the same way as `template_file`. The inline `js`/`css` and
the `*_file` forms are mutually exclusive.

### Highlight inline source in your editor

Inline HTML, CSS, and JavaScript are Python strings, so an editor may show them
as plain text. JetBrains editors understand a `# language=` comment immediately
above the attribute:


```citry
from citry import Component


class Calendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

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

    # language=JS
    js = """
      $component(({ els }) => {
        console.log(els[0]);
      });
    """
```


In VS Code, the Python Inline Source extension can use string annotations:


```citry
class Calendar(Component):
    template: "html" = """
      <div class="calendar">Today</div>
    """

    css: "css" = """
      .calendar {
        width: 12rem;
      }
    """

    js: "js" = """
      $component(({ els }) => {
        console.log(els[0]);
      });
    """
```


These hints affect only editor highlighting.

### Know when component JavaScript runs

Code outside `$component` runs when the component's script loads. Code inside
the callback runs once for each rendered instance, after Citry has found that
instance and prepared its data:


```js
console.log("The component script loaded");

$component(({ els, data }) => {
  console.log("This rendered instance is ready", els[0], data);
});
```


Keep page-wide setup outside the callback. Put work that reads one component's
elements or `js_data()` inside it.

## Pass per-instance data with js_data and css_data

`js_data(self, kwargs, slots)` and `css_data(self, kwargs, slots)` return a dict
for the current render. Both take the same three arguments as `template_data`.

The `js_data` dict is JSON-serialized and delivered to the browser. Your
`$component` callback receives it as the `data` argument, so a returned
`{"points": [...]}` is readable as `data.points`. The callback also receives
`els`, the array of elements carrying this instance's `data-cid-<id>` marker, so
`els[0]` is the component's root element.

The `css_data` dict becomes CSS custom properties scoped to that instance. A
returned `{"h": "240px"}` makes `var(--h)` resolve to `240px` inside that
instance's CSS, and only for that instance. String values with spaces are quoted
automatically (so `"Helvetica Neue"` stays one value), while CSS function calls
like `calc(...)`, `var(...)`, and `rgba(...)` are left unquoted so they still
work. Pick key names that are valid after the `--` prefix.

Identical `js_data`/`css_data` results are hashed and sent to the browser only
once, however many instances share them.

### Optional typed schemas

You can declare an inner `JsData` or `CssData` class as a plain annotated class.
citry turns it into a dataclass, and your method may return either that instance
or a plain dict.


```citry
class Card(Component):
    template = """
      <p>x</p>
    """

    class JsData:
        rows: int

    def js_data(self, kwargs, slots):
        return Card.JsData(rows=5)   # or return {"rows": 5}
```


Declaring a schema is a promise: at render time, a missing required field or an
unexpected field raises `TypeError`.

## Add third-party and shared assets

Use a nested `Dependencies` class when a component needs a library or shared
asset it does not own. A URL string in `js` becomes a `<script src>` tag. A URL
string in `css` becomes a stylesheet link:


```citry
from citry import Component


class PriceChart(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    class Dependencies:
        js = [
            "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js",
        ]
        css = [
            "https://unpkg.com/normalize.css@8.0.1/normalize.css",
        ]

    template = """
      <div class="price-chart"></div>
    """
```


Citry keeps the declared order and emits the same URL only once, even when
several rendered components request it.

Use [`Script`](/v/0.3.0/reference/dependencies/#citry-ext-dependencies-script) or
[`Style`](/v/0.3.0/reference/dependencies/#citry-ext-dependencies-style) when an asset needs inline content or
extra tag attributes:


```citry
from citry import Component
from citry.ext.dependencies import Script, Style


class Editor(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    class Dependencies:
        js = [
            Script(
                url="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.js",
                attrs={"defer": True},
            ),
            Script(
                content="window.EDITOR_THEME = 'dark';",
                attrs={"type": "module"},
            ),
        ]
        css = [
            Style(content=".editor { border: 1px solid #ccc; }"),
        ]

    template = """
      <div class="editor"></div>
    """
```


An entry that is not a URL is read from a file beside the component module and
inlined. Set `local_files = "serve"` on `Dependencies` when a mounted web app
should serve local files from fingerprinted URLs instead.

Use a mapping when a stylesheet needs a media type:


```citry
class Invoice(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    class Dependencies:
        css = {
            "all": "base.css",
            "print": "print.css",
        }

    template = """
      <article class="invoice"></article>
    """
```


Dependencies are inherited and extended by default. [Subclassing
components](/concepts/subclassing/#dependencies-inheritance) covers the
inheritance order, `extend = False`, and selecting particular bases.

## Where the collected JS and CSS go

citry gathers every rendered component's JS and CSS and injects it at two
built-in placement tags. Put `<c-css />` where the stylesheets should go
(usually in `<head>`) and `<c-js />` where the scripts should go (usually at the
end of `<body>`).


```citry
class Page(Component):
    template = """
      <html>
        <head>
          <c-css />
        </head>
        <body>
          <c-Chart c-points="[1, 2, 3]" />
          <c-js />
        </body>
      </html>
    """
```


Both tags are self-closing and take no attributes and no body (passing either
raises `ValueError`). If the same tag appears more than once, the first in
document order receives the collected tags and the rest render nothing.

If you leave the tags out, nothing is dropped: CSS is inserted before the first
`</head>` and JS before the last `</body>`. If those are missing too, CSS is
prepended and JS appended to the output.

## Deps strategies control placement

`str(component)` is a shortcut for `component.render().serialize()`. The
`serialize` method takes a `deps_strategy` ([`DepsStrategy`](/v/0.3.0/reference/rendering/#citry-depsstrategy))
that decides how the collected assets are emitted:

- `"document"` (default): full-page output. Tags plus the client runtime and a
  data manifest when a component uses `$component`.
- `"simple"`: tags only, no JS runtime. Good for static pages and email. The
  per-instance JS variables and `$component` calls are skipped, so `js_data`
  is not delivered under this strategy. `css_data` still works because CSS
  variables are pure CSS and need no runtime.
- `"fragment"`: emits a URL manifest for insertion into an already-loaded page.
  See [HTML fragments](/v/0.3.0/advanced/html-fragments/).
- `"ignore"`: inserts no dependency tags at all.

A `deps_position` ([`DepsPosition`](/v/0.3.0/reference/rendering/#citry-depsposition)) of `"smart"` (the
default), `"prepend"`, or `"append"` picks where tags land for the `"document"`
and `"simple"` strategies. `"smart"` uses the `<c-css />` / `<c-js />`
placeholders when present and otherwise falls back to the default locations
above.


```python
# Static page with no client runtime:
html = Page().render().serialize(deps_strategy="simple")
```


Note that `js_data` reaches the browser only if the component's JS actually uses
`$component`; without a callback there is nothing for the data to reach.
Likewise `css_data` produces nothing if the component declares no CSS.

## Modifying the emitted JS and CSS

As the collected assets turn into `<script>`, `<style>`, and `<link>` elements,
citry gives you the final say over them. Each asset is a [`Script`](/v/0.3.0/reference/dependencies/#citry-ext-dependencies-script)
or [`Style`](/v/0.3.0/reference/dependencies/#citry-ext-dependencies-style) object holding either inline `content` or a `url`, plus
an `attrs` dict of extra HTML attributes. Two hooks let you edit these objects
before they render, and one flag controls how inline scripts are wrapped. Reach
for them to add an attribute (a CSP `nonce`, a `type`), reorder the tags, or drop
one the page already loads.

### Adjust one component's tags

`on_dependencies(cls, scripts, styles)` is a classmethod hook on a component.
citry calls it once per rendered instance with the tags that component
contributes (its own `js`/`css` and any `Dependencies` entries). Edit the
`Script`/`Style` objects in place and return nothing:


```citry
from citry import Component

class Chart(Component):
    template = """
      <div class="chart"></div>
    """
    js = """
      draw();
    """
    css = """
      .chart {
        height: 240px;
      }
    """

    @classmethod
    def on_dependencies(cls, scripts, styles):
        nonce = current_csp_nonce()  # your per-request CSP nonce
        for dep in [*scripts, *styles]:
            dep.attrs["nonce"] = nonce  # stamp this component's tags
```


To replace the lists instead, return a `(scripts, styles)` pair. For example,
`return (scripts, [])` keeps the scripts and drops this component's styles, which
is handy when they already ship in your site-wide stylesheet. Dropping a
component's own script can stop it working in the browser, so drop only entries
you know are loaded elsewhere.

### Adjust every component's tags

To change every component's tags at once, after duplicates are removed, put an
`on_dependencies` method on an [Extension](/v/0.3.0/reference/extensions/#citry-extension). It receives an
`OnDependenciesContext` whose `scripts` and `styles` are the final, page-wide
lists (and whose `citry` is the engine). Mutate those lists in place; a site-wide
CSP nonce is the usual reason:


```citry
from citry import Citry, Component, Extension
from citry.ext.dependencies import OnDependenciesContext

class CspNonce(Extension):
    name = "csp_nonce"

    def on_dependencies(self, ctx: OnDependenciesContext):
        nonce = current_csp_nonce()  # your per-request CSP nonce
        for dep in [*ctx.scripts, *ctx.styles]:
            if dep.content and "nonce" not in dep.attrs:
                dep.attrs["nonce"] = nonce  # only inline tags need it

app = Citry(extensions=[CspNonce])

class Widget(Component):
    citry = app
    template = """
      <div class="widget"></div>
    """
    js = """
      init();
    """
    css = """
      .widget {
        color: red;
      }
    """
```


The `dep.content` guard skips external `<script src>` and `<link>` tags, which
carry no inline content and take no nonce. The hook runs at serialize time for
every page the engine renders, so any component bound to `app` gets the nonce.
See [Extensions](/v/0.3.0/advanced/extensions/) for how extensions are written and
installed.

### Disable the self-executing wrapper

citry wraps a component's inline JavaScript in a self-executing function, so its
top-level variables stay private and never collide with another script on the
page:


```js
(function() {
init();
})();
```


When you build a [`Script`](/v/0.3.0/reference/dependencies/#citry-ext-dependencies-script) yourself, as a
`Dependencies` entry or through the hooks above, set `wrap=False` to emit the
content verbatim instead:


```citry
from citry import Component
from citry.ext.dependencies import Script

class Banner(Component):
    template = """
      <div class="banner"></div>
    """

    class Dependencies:
        js = [
            Script(content="window.BANNER = true;", wrap=False),
        ]
```


The tag then emits `<script>window.BANNER = true;</script>` with no wrapper. Only
classic scripts are wrapped in the first place: a `Script` with `type="module"`
(or any other non-JavaScript `type`) is left as-is whatever `wrap` says.

## Next steps

- [HTML fragments](/v/0.3.0/advanced/html-fragments/) covers the `"fragment"` strategy
  for HTMX-style page updates.
- [Add browser behavior](/v/0.3.0/getting-started/browser-interactivity/) introduces
  component JavaScript through one small interaction.
- [Web frameworks](/v/0.3.0/web-frameworks/) shows how to mount Citry so local assets
  and rendered fragments have URLs.