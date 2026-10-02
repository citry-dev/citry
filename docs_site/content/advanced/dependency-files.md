---
title: Dependency files
description: Add libraries and shared JavaScript or CSS files to a Citry component.
---

# Dependency files

Sometimes a component needs code that it does not own: a charting library,
a shared theme stylesheet, or a script file in your project. List those
files in a nested `Dependencies` class on the component. Citry then adds
them to every page that renders the component, once per page, and loads
them before any component's own JavaScript, so the component can use the
library.

Code that belongs to the component itself goes in its `js` and `css`. See
[Component JavaScript and CSS](/advanced/js-and-css-dependencies/).

## Add a library from a URL

List JavaScript URLs in `js` and stylesheet URLs in `css`:

```citry
from citry import Component


class PriceChart(Component):
    class Dependencies:
        js = ["https://cdn.example.com/chart.js"]
        css = ["https://cdn.example.com/chart.css"]

    template = """
      <div class="price-chart"></div>
    """
```

A JavaScript URL becomes a `<script src="...">` tag, and a CSS URL becomes
a `<link rel="stylesheet">` tag. Files load in the order you list them.
When several components on a page list the same URL, Citry adds it once.

## Add a file from your project

A string that does not start with `http://`, `https://`, or `/` can name a
file. Citry looks for it next to the Python module that declares the
component, then in the directories passed to
[`Citry(dirs=...)`][citry.Citry]. If it finds no file, it uses the string
as a URL:

```citry
from pathlib import Path

from citry import Component


class Report(Component):
    class Dependencies:
        js = [Path("libs/report.js")]
        css = ["report.css"]

    template = """
      <article class="report"></article>
    """
```

Use a
[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path){: target="_blank" rel="noopener"}
when the entry must be a file. A missing `Path` raises `FileNotFoundError`,
while a missing string quietly becomes a URL.

Citry puts the content of a project file directly into the page. A
JavaScript file runs as written, so a library's top-level variables stay
global as the library expects.

To serve project files at their own URLs instead, so the browser can cache
them, set `local_files = "serve"`:

```python
class Dependencies:
    local_files = "serve"
    js = ["report.js"]
```

Each URL contains a hash of the file's content, so a changed file gets a
new URL. Serving needs Citry's routes added to your web app (see
[Web frameworks](/web-frameworks/)); without them, Citry puts the content
into the page as before. `local_files` accepts only `"inline"` (the
default) and `"serve"`. Any other value raises `ValueError` when a page
that includes one of the component's project files is serialized.

To serve project files for every component, set the default on your
`Citry` instance:

```python
c = Citry(
    extensions_defaults={
        "dependencies": {"local_files": "serve"},
    },
)
```

## Add attributes or inline code to a tag

Use [`Script`][citry.ext.dependencies.Script] or
[`Style`][citry.ext.dependencies.Style] when the tag needs HTML attributes,
or when the code is short enough to write inline:

```citry
from citry import Component
from citry.ext.dependencies import Script, Style


class Editor(Component):
    class Dependencies:
        js = [
            Script(
                url="https://cdn.example.com/editor.js",
                attrs={"crossorigin": "anonymous"},
            ),
            Script(
                content="window.EDITOR_THEME = 'dark';",
            ),
        ]
        css = [
            Style(
                content=".editor { border: 1px solid #ccc; }",
            ),
        ]

    template = """
      <div class="editor"></div>
    """
```

Give each object either `url` or `content`, not both. `attrs` adds HTML
attributes to the tag.

Citry runs inline JavaScript inside its own function, so its top-level
variables do not leak to other scripts. Set `wrap=False` when a script must
run exactly as written, for example to define a global variable with
`var`:

```python
Script(
    content="var EDITOR_READY = true;",
    wrap=False,
)
```

A script with a `type` such as `module` or `importmap` is never wrapped.

## Load a stylesheet only for print or another media type

Use a mapping to give stylesheets a `media` attribute:

```python
class Dependencies:
    css = {
        "all": ["base.css"],
        "print": ["print.css"],
    }
```

Each key other than `"all"` becomes the `media` value of its stylesheets.
Stylesheets under `"all"` get no `media` attribute.

## Use plain scripts on interactive pages

A page is interactive when one of its components needs Citry's browser
runtime, the JavaScript that Citry adds to run Vue and server events. That
happens, for example, when a component has its own `js` or uses Vue syntax
such as `@click`. On an interactive page, Citry loads every dependency
script itself, one after another, so each must be a plain script that can
run in that order:

```python
# Fails as soon as any component on the page is interactive.
Script(
    url="https://cdn.example.com/editor.js",
    attrs={"type": "module"},
)

# Works on every page.
Script(url="https://cdn.example.com/editor.umd.js")
```

When you turn an interactive page's render into HTML with `str()` or
`serialize()`, Citry raises `ValueError` for a `Script` that has:

- an `async`, `defer`, or `nomodule` attribute;
- a `type` other than JavaScript, such as `type="module"`;
- a `nonce` attribute, when you pass no `csp_nonce` to `serialize()`.

Pages without the runtime, and the `"simple"` strategy described in
[Place JavaScript and CSS](/advanced/asset-placement/#choose-a-dependency-strategy),
write ordinary tags, so these attributes work there. On every page, a
`nonce` that differs from the `csp_nonce` you pass raises `ValueError`.

Use `Script` and `Style` themselves, not subclasses of them. A subclass
raises `TypeError` on an interactive page.

## Order files and handle duplicates

Entries from a base component come first, then the child's own entries.
[Subclassing components](/advanced/subclassing/) shows how to extend or
replace inherited entries.

Citry treats two scripts or two stylesheets as the same file when they have
the same URL or the same inline content, and adds that file once:

- For scripts, the first one wins, attributes included. To change a
  script's attributes, change the first declaration rather than adding a
  second one.
- For stylesheets, every copy must have the same attributes. Within one
  component, including what it inherits, the first copy wins. When two
  components declare the same stylesheet with different attributes, or one
  component lists it under two `media` keys, serialization raises
  `ValueError`. Give such stylesheets different URLs.

## Use other kinds of entries

Besides URLs, file paths, `Script`, and `Style`, an entry can be one of
these:

### A glob pattern

A string such as `"widgets/*.js"` adds every matching file, sorted by
path. Citry searches the same places as for a single file, and uses only
the first place that has matches. A string glob that matches nothing is
kept as a URL.

### A function

Citry calls a callable entry the first time it needs the component's
files, not when the class is defined, and uses what it returns as the
entry. It keeps that result for later renders.

### A ready-made tag

An object with an `__html__()` method is inserted as the tag it returns.
Citry does not escape that HTML, so accept such objects only from code you
trust.

Prefer `Script` and `Style`: Citry's browser runtime cannot load a
ready-made tag. Serialization raises `TypeError` for one on an interactive
page, in an [HTML fragment](/advanced/html-fragments/), or when you serialize
with a CSP nonce or script integrity checks.
