---
title: Place JavaScript and CSS
url: https://citry.dev/v/0.4.1/advanced/asset-placement/
description: "Choose where Citry inserts collected assets and which dependency strategy a render uses."
---
# Place JavaScript and CSS

After a page renders, Citry has the JavaScript and CSS required by every
component that appeared. You can mark where those tags belong or let Citry
choose sensible document locations.

## Mark the positions in a page

Put `<c-css />` in `<head>` and `<c-js />` near the end of `<body>`:


```citry
from citry import Component


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


The tags are placeholders. They are self-closing and accept no attributes or
body. If a placeholder appears more than once, the first one in document
order receives the collected tags and the others insert nothing.

When the placeholders are absent, the default document strategy inserts CSS
before the first `</head>` and JavaScript before the last `</body>`. If those
end tags are absent too, Citry inserts CSS at the start and JavaScript at the
end.

## Choose a dependency strategy

Calling `str(component)` uses the default document strategy. For explicit
control, render first and pass `deps_strategy` to `serialize()`:


```python
rendered = Page().render()
html = rendered.serialize(deps_strategy="document")
```


[`DepsStrategy`](/v/0.4.1/reference/rendering/#citry-depsstrategy) accepts four values:

- `"document"` inserts all required tags. Citry also adds its browser runtime
  and initialization data when the rendered page needs them.
- `"simple"` inserts component and dependency tags without the Citry browser
  runtime or initialization calls.
- `"fragment"` describes new dependencies for insertion into a page that
  already loaded Citry. See [HTML fragments](/v/0.4.1/advanced/html-fragments/).
- `"ignore"` inserts no dependency tags.

The simple strategy is for output with no Citry browser behavior. It can still
insert ordinary component JavaScript, so do not use it with `$component()`,
server events, or anything else that expects the Citry runtime. It also skips
per-render JavaScript data. CSS data still works because its custom properties
are ordinary CSS.

The ignore strategy assumes something else supplies every required asset.
Components may look correct in the returned HTML but have no styles or browser
behavior.

## Override the position without placeholders

For the document and simple strategies, `deps_position` accepts
[`DepsPosition`](/v/0.4.1/reference/rendering/#citry-depsposition):


```python
html = Page().render().serialize(
    deps_strategy="document",
    deps_position="append",
)
```


The positions are:

- `"smart"`, the default, uses `<c-css />` and `<c-js />` when present and
  otherwise uses the document locations described above;
- `"prepend"` puts the collected tags before the rendered HTML; and
- `"append"` puts them after the rendered HTML.

Use smart placement for normal pages. Prepend and append are useful when the
rendered output is not a complete HTML document and its host decides where the
combined result will go.

## Keep each decision in the right place

Placement answers where the final tags go. Other pages cover the remaining
asset jobs:

- [Component JavaScript and CSS](/v/0.4.1/advanced/js-and-css-dependencies/) defines
  behavior, styles, and per-render browser data owned by a component.
- [Dependency files](/v/0.4.1/advanced/dependency-files/) adds libraries and shared
  files.
- [Component hooks](/v/0.4.1/advanced/hooks/) adjusts the tags contributed by one
  component.
- [Extensions](/v/0.4.1/advanced/extensions/) can adjust the collected component
  dependency lists across an application. Citry may still add required core
  runtime and initialization tags after that extension hook.