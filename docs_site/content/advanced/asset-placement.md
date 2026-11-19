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

## `<c-css />` and `<c-js />` { #mark-where-the-tags-go }

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

## Choose a strategy { #choose-a-dependency-strategy }

The dependency strategy decides which tags Citry inserts. `str(component)`
uses `"document"`. To choose another, render first and pass
`deps_strategy` to `serialize()`:

```python
page = Page()
rendered = page.render()
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

## Placement options

Use `deps_position` when the output is not a whole HTML page and the code
that receives it decides where it goes. It works with the `"document"` and
`"simple"` strategies:

```python
page = Page()
html = page.render().serialize(
    deps_strategy="document",
    deps_position="append",
)
```

[`DepsPosition`][citry.DepsPosition] accepts four values:

- `"smart"`, the default, uses `<c-css />` and `<c-js />`, or the locations
  described in [`<c-css />` and `<c-js />`](#mark-where-the-tags-go);
- `"prepend"` puts all the tags before the HTML;
- `"append"` puts all the tags after the HTML;
- `"separate"` (Experimental) leaves the tags out of the HTML and returns
  them grouped, for code that puts several renders on one page. See
  [Combine several renders on one page](#combine-several-renders).

!!! note "A page that repeats a placement tag"

    When the page has more than one CSS or JavaScript placement tag, only
    the first of each kind receives the tags. The others insert nothing.

## Combine several renders on one page { #combine-several-renders }

!!! warning "Experimental"

    `deps_position="separate"`, [`SerializedAssets`][citry.SerializedAssets],
    the asset fields of [`SerializedRender`][citry.SerializedRender] and
    [`CitryRender.needs_browser_runtime()`][citry.CitryRender.needs_browser_runtime]
    may change in a minor release.

Some code builds one page from several Citry renders, for example a
Django page with a Citry component in a few places. Each render that
needs Citry's browser runtime becomes its own Vue app. Serialized one
by one with the default position, each render would bring its own copy
of the runtime script and of every shared file.

With `deps_position="separate"`, Citry leaves the tags out of the HTML.
[`serialize_result()`][citry.CitryRender.serialize_result] returns them
on the result instead, so your code can write each shared tag once:

```python
result = Widget().render().serialize_result(
    deps_position="separate",
)
html = result.html  # the HTML, with no asset tags
```

The tags come in three groups. Each group is a
[`SerializedAssets`][citry.SerializedAssets] with a `css` tuple, for
the tags that go where `<c-css />` would put them, and a `js` tuple, for
the scripts that go where `<c-js />` would put them:

| Field | What it holds | On a page with several renders |
|---|---|---|
| `runtime_assets` | Citry's browser runtime, the browser plugin scripts of extensions, and preload hints | write the first of identical tags once |
| `app_assets` | this render's Vue app: its stylesheet links, its configuration data and its start script | write every tag |
| `component_assets` | component CSS and JavaScript on a page without Vue, dependency files, and tags from `on_dependencies` hooks | write the first of identical tags once |

Write every tag of `app_assets`, even when two apps link the same
stylesheet. Each link names its own app, and the runtime loads the file
again for an app whose link is missing. The browser fetches the file
once either way.

Write the `css` tuples in `<head>` and the `js` tuples at the end of
`<body>`, in the order `runtime_assets`, `component_assets`,
`app_assets`. The start script in `app_assets` waits until the browser
has read the whole page, so it runs after the runtime even when your
page puts it earlier.

Each tag keeps what Citry would have written: the `nonce` you passed as
`csp_nonce`, its `integrity` attribute, and the same checks under
`security_csp` and `security_javascript`. Vue adopts the HTML the server
wrote, as it does with `"smart"`.

`"separate"` works with the `"document"` and `"simple"` strategies. With
`"ignore"`, every group is empty. With `"fragment"`, it raises
`ValueError`, because a fragment writes its own loader script. Tags that
another extension's `on_serialize()` hook adds stay in the HTML.

### Make some child components their own apps

[`needs_browser_runtime()`][citry.CitryRender.needs_browser_runtime]
tells whether a render would become a Vue app when serialized on its
own. A host that mixes Citry renders with HTML from another template
engine can use it to turn only the interactive children of a render
into their own apps, and serialize the rest as plain HTML.

A child component's render may be serialized on its own before its
parent is serialized. Each child becomes a separate Vue app with its
own assets, and the parent's render does not change:

```python
rendered = List().render()
for part in rendered.parts:
    if (
        isinstance(part, CitryRender)
        and part.is_component_root
        and part.needs_browser_runtime()
    ):
        island = part.serialize_result(
            deps_position="separate",
        )
```

Each app is separate, so a server event handler in one app can update
only components in that app.

## Next steps

- [Component JS and CSS](/advanced/js-and-css-dependencies/) adds
  code and styles to one component.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [Extensions](/advanced/extensions/) changes the tags for every page in an
  application.
