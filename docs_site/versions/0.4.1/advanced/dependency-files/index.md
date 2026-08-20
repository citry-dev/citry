---
title: Dependency files
url: https://citry.dev/v/0.4.1/advanced/dependency-files/
description: "Add libraries and shared JavaScript or CSS files to a Citry component."
---
# Dependency files

A component may rely on code it does not own: a charting library, a shared
theme, or a vendored script. Declare those assets in a nested `Dependencies`
class. Citry includes them only on pages that render the component.

Keep code that belongs to the component in its own `js`, `css`, `js_file`, or
`css_file`. See
[Component JavaScript and CSS](/v/0.4.1/advanced/js-and-css-dependencies/).

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

Use [`Script`](/v/0.4.1/reference/dependencies/#citry-ext-dependencies-script) or
[`Style`](/v/0.4.1/reference/dependencies/#citry-ext-dependencies-style) to add attributes or inline content:


```citry
from citry import Component
from citry.ext.dependencies import Script, Style


class Editor(Component):
    class Dependencies:
        js = [
            Script(
                url="https://cdn.example.com/editor.js",
                attrs={"defer": True},
            ),
            Script(
                content="window.EDITOR_THEME = 'dark';",
                attrs={"type": "module"},
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

## Add a local file

A string first looks for a file beside the Python module that declared it,
then in the directories configured on [`Citry`](/v/0.4.1/reference/citry/#citry-citry). When Citry finds
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
content. See [Web frameworks](/v/0.4.1/web-frameworks/) for mounting.

## Group styles by media type

Use a mapping when stylesheets need different `media` attributes:


```citry
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

Prefer `Script` and `Style` when possible. Citry can describe those objects to
the browser during a fragment update, while it cannot safely decompose an
opaque ready-made tag for a fragment. Citry trusts the HTML returned by
`__html__()`, so accept these objects only from code you trust.

## Understand ordering and duplicates

Dependencies from base components come first, followed by entries from the
child. [Subclassing components](/v/0.4.1/advanced/subclassing/) explains how to extend
or replace inherited declarations.

Citry considers two scripts or styles the same when they have the same URL or
the same inline content. The first entry wins completely, including its
attributes. If a script needs different attributes, change the first
declaration rather than adding a duplicate later.

After collection, Citry places the resulting tags according to the page's
dependency strategy. Continue with
[Place JavaScript and CSS](/v/0.4.1/advanced/asset-placement/).