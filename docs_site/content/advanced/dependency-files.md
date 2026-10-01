---
title: Dependency files
description: Add libraries and shared JavaScript or CSS files to a Citry component.
---

# Dependency files

A component may rely on code it does not own: a charting library, a shared
theme, or a third-party script copied into your project. Declare those assets
in a nested `Dependencies` class. Citry includes them only on pages that render
the component.

Keep code that belongs to the component in its own `js`, `css`, `js_file`, or
`css_file`. See
[Component JavaScript and CSS](/advanced/js-and-css-dependencies/).

## Add a URL

A JavaScript URL becomes a `<script src>` tag. A CSS URL becomes a stylesheet
link:

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

Lists keep their declared order. If several rendered components request the
same URL, Citry emits it once.

## Control the generated tag

Use [`Script`][citry.ext.dependencies.Script] or
[`Style`][citry.ext.dependencies.Style] to add attributes or inline content:

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

Each object accepts either `url` or `content`, never both. Its `attrs` mapping
adds HTML attributes to the generated tag.

Citry normally wraps inline classic scripts in a self-executing function so
their top-level variables stay private. Set `wrap=False` when a script must
run exactly as written:

```python
Script(
    content="window.EDITOR_READY = true;",
    wrap=False,
)
```

Module scripts, import maps, and other non-classic script types are never
wrapped, regardless of `wrap`.

## Use classic scripts on interactive pages

A page becomes interactive when one of its components needs Citry's browser
runtime, for example because it has its own `js` or uses Vue syntax such as
`@click`. Citry then loads every dependency script itself, one after another,
so each script must be a classic script that runs in order.

Citry checks dependencies when it serializes the render, that is, when you
call `serialize()` or `str()` on it. On an interactive page, serialization
raises `ValueError` for a `Script` with `async`, `defer`, or `nomodule`,
with a `type` other than JavaScript (such as `type="module"`), or with a
`nonce` when you pass no `csp_nonce`. A subclass of `Script` or `Style`
raises `TypeError` there; use the classes themselves:

```python
# Breaks once any component on the page is interactive.
Script(
    url="https://cdn.example.com/editor.js",
    attrs={"type": "module"},
)

# Works on every page.
Script(url="https://cdn.example.com/editor.umd.js")
```

Pages without the runtime, and the `"simple"` dependency strategy (see
[Place JavaScript and CSS](/advanced/asset-placement/)), write these scripts as
ordinary tags, so these attributes work there. One check applies on every
page: a `nonce` that differs from the `csp_nonce` you pass raises
`ValueError`.

## Add a local file

A string first looks for a file beside the Python module that declared it,
then in the directories configured on [`Citry`][citry.Citry]. When Citry finds
the file, it treats it as a local dependency. If it cannot find the string, it
keeps it as a URL or application static path.

Use
[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path){: target="_blank" rel="noopener"}
when the value must refer to a local file. A missing `Path` raises
`FileNotFoundError` instead of becoming a URL:

```citry
from pathlib import Path

from citry import Component


class Report(Component):
    class Dependencies:
        js = [Path("vendor/report.js")]
        css = ["report.css"]

    template = """
      <article class="report"></article>
    """
```

Local files are inline by default. To serve fingerprinted asset URLs from a
mounted Citry application, set `local_files = "serve"`:

```python
class Dependencies:
    local_files = "serve"
    js = ["report.js"]
```

Set the same default for every component on an engine:

```python
c = Citry(
    extensions_defaults={
        "dependencies": {"local_files": "serve"},
    },
)
```

Without a mounted web integration, `"serve"` safely falls back to inline
content. See [Web frameworks](/web-frameworks/) for mounting. If a component
that lists a local file sets any other value than `"inline"` or `"serve"`,
serialization raises `ValueError`.

## Group styles by media type

Use a mapping when stylesheets need different `media` attributes:

```python
class Dependencies:
    css = {
        "all": ["base.css"],
        "print": ["print.css"],
    }
```

The `"all"` group has no explicit `media` attribute. Other keys become the
attribute value.

## Load a calculated set of files

A dependency entry may also be:

- a glob string, expanded in sorted order;
- a callable, evaluated when Citry resolves the dependencies; or
- a trusted object with `__html__()`, inserted as a ready-made tag.

Prefer `Script` and `Style` when possible. Citry's browser runtime can load
`Script` and `Style` objects itself, but it cannot do that with a ready-made
tag. A ready-made tag works only where Citry writes dependencies as ordinary
tags. On an interactive page or
[HTML fragment](/advanced/html-fragments/), or when serialization uses a CSP
nonce or script integrity, serialization raises `TypeError`.
Citry trusts the HTML returned by `__html__()`, so accept these objects only
from code you trust.

## Understand ordering and duplicates

Dependencies from base components come first, followed by entries from the
child. [Subclassing components](/advanced/subclassing/) explains how to extend
or replace inherited declarations.

Citry considers two scripts or styles the same when they have the same URL or
the same inline content. For scripts, the first entry wins completely,
including its attributes. If a script needs different attributes, change the
first declaration rather than adding a duplicate later. Within one
component, including what it inherits from base classes, the first
stylesheet also wins. Two components that declare the same stylesheet with different attributes, or one
stylesheet listed under two `media` keys, make serialization raise
`ValueError`. Give the stylesheets distinct URLs instead.

After collection, Citry places the resulting tags according to the page's
dependency strategy. Continue with
[Place JavaScript and CSS](/advanced/asset-placement/).
