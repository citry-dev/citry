---
title: Place JavaScript and CSS
description: Choose where Citry inserts collected assets and which dependency strategy a render uses.
---

# Place JavaScript and CSS

When a page renders, Citry collects the JavaScript and CSS that its
components need. By default it puts the CSS at the end of `<head>` and the
JavaScript at the end of `<body>`, which suits most pages.

Read on when you need the tags somewhere else, or when the HTML is not a
whole page: an email, a piece of HTML that another system places, or a page
whose scripts you load yourself.

## Mark where the tags go

Put `<c-css />` where the CSS should go and `<c-js />` where the JavaScript
should go:

```citry
from citry import Component


class Page(Component):
    template = """
      <html>
        <head>
          <c-css />
          <link rel="stylesheet" href="/static/overrides.css">
        </head>
        <body>
          <c-Chart c-points="[1, 2, 3]" />
          <c-js />
        </body>
      </html>
    """
```

Here the component styles come before `overrides.css`, so the overrides
win. Each tag takes no attributes and no content.

Without these tags, Citry inserts CSS before the first `</head>` and
JavaScript before the last `</body>`. When the HTML has no `</head>` or
`</body>`, CSS goes at the start of the output and JavaScript at the end.

## Choose a dependency strategy

The dependency strategy decides which tags Citry inserts. `str(component)`
uses `"document"`. To choose another, render first and pass
`deps_strategy` to `serialize()`:

```python
rendered = Page().render()
html = rendered.serialize(deps_strategy="simple")
```

[`DepsStrategy`][citry.DepsStrategy] accepts four values:

- `"document"` inserts every tag the page needs. When a component needs
  Citry's browser runtime (the JavaScript that runs Vue and server events),
  it adds that too.
- `"simple"` inserts the components' JavaScript and CSS and their
  [dependency files](/advanced/dependency-files/), but not the browser
  runtime. Use it for output with no Citry browser behavior:
  `$component()`, server events, and `js_data()` do not work, while
  `css_data()` does, because it is ordinary CSS.
- `"fragment"` is for HTML that you insert into a page that is already
  open. See [HTML fragments](/advanced/html-fragments/).
- `"ignore"` inserts no tags. Use it when something else adds every file
  the components need.

With `"ignore"`, the HTML can look right in tests but have no styles or
browser behavior if nothing else adds the files.

## Put the tags before or after the output

Use `deps_position` when the output is not a whole HTML page and the code
that receives it decides where it goes. It works with the `"document"` and
`"simple"` strategies:

```python
html = Page().render().serialize(
    deps_strategy="document",
    deps_position="append",
)
```

[`DepsPosition`][citry.DepsPosition] accepts three values:

- `"smart"`, the default, uses `<c-css />` and `<c-js />`, or the locations
  described in [Mark where the tags go](#mark-where-the-tags-go);
- `"prepend"` puts all the tags before the HTML;
- `"append"` puts all the tags after the HTML.

!!! note "A page that repeats a placement tag"

    When the page has more than one CSS or JavaScript placement tag, only
    the first of each kind receives the tags. The others insert nothing.

## Next steps

- [Component JavaScript and CSS](/advanced/js-and-css-dependencies/) adds
  code and styles to one component.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [Extensions](/advanced/extensions/) changes the tags for every page in an
  application.
