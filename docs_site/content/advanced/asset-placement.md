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
JavaScript before the last `</body>`, in any letter case. Only real tags
count: `</head>` written inside an attribute value, a comment, or a
script is text, not a tag. When the HTML has no `</head>` or `</body>`,
CSS goes at the start of the output and JavaScript at the end.

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
  [Combine several renders](#combine-several-renders).

!!! note "A page that repeats a placement tag"

    When the page has more than one CSS or JavaScript placement tag, only
    the first of each kind receives the tags. The others insert nothing.

## Combine several renders { #combine-several-renders }

!!! warning "Experimental"

    This section's API may change in a minor release.

An app sometimes builds one page from several Citry renders, for
example a Django page with a Citry component in a few places. Each
render that needs Citry's browser runtime becomes its own Vue app.
Serialized one by one in the usual way, each render brings its own copy
of the runtime script and of the CSS and JavaScript files it shares with
the others.

With `deps_position="separate"`, Citry leaves the tags out of the HTML
and [`serialize_result()`][citry.CitryRender.serialize_result] returns
them on the result. Your code then writes each shared tag once. Use
`serialize_result()`: `serialize()` returns only the HTML and drops the
tags.

The result holds three groups of tags, each a
[`SerializedAssets`][citry.SerializedAssets]. A group's `css` tuple
holds the tags for `<head>`, and its `js` tuple the scripts for the end
of `<body>`:

| Field | What it holds |
|---|---|
| `runtime_assets` | Citry's browser runtime and preload hints |
| `app_assets` | this render's Vue app: its stylesheets, its data and its start script |
| `component_assets` | every other tag, such as component CSS and dependency files |

[`combine_assets()`][citry.combine_assets] (Experimental) takes the
same group from several renders and returns it with each shared tag
written once. Stylesheets that several apps load from the same file
become one tag that every one of those apps uses. Each app keeps its
own data and start script. Call it once per group, so no tag moves into
another group.

This example serializes two renders and writes their tags once each:

```python
from citry import combine_assets

results = [
    Widget().render().serialize_result(
        deps_position="separate",
    ),
    Chart().render().serialize_result(
        deps_position="separate",
    ),
]
groups = [
    combine_assets(r.runtime_assets for r in results),
    combine_assets(r.component_assets for r in results),
    combine_assets(r.app_assets for r in results),
]
head = "".join(tag for g in groups for tag in g.css)
end_of_body = "".join(tag for g in groups for tag in g.js)
```

Write the groups in this order: `runtime_assets`, then
`component_assets`, then `app_assets`. `combine_assets()` keeps the
tags in the order of the renders you pass, so the same renders, passed
in the same order, give the same tags. A tag several renders share
stays where it first appears, so a later render's stylesheets can end
up in a different order than that render alone would write them.

If you combine the tags yourself, keep every `app_assets` tag, even
when two apps load the same stylesheet. Each app uses only a stylesheet
tag that names it. An app whose tag is missing loads the file again on
a page served with Citry's routes mounted, and does not start on a
standalone page.

Each tag is exactly the tag Citry would have written into the HTML. It
carries the `nonce` you passed as `csp_nonce` and its `integrity`
attribute, `security_csp` and `security_javascript` check it, and
`result.security` covers it. When you combine several renders, your
page needs the `security` of every result, such as each result's
`csp_script_hashes`. Vue adopts the server HTML instead of
building it again, as it does with `"smart"`.

`"separate"` works with the `"document"` and `"simple"` strategies.
With `"ignore"`, every group is empty, and with `"fragment"` it raises
`ValueError`. Tags that another extension's `on_serialize()` hook adds
stay in the HTML, and a hook that changes one of the returned tags
makes serialize raise `RuntimeError`.

### Find a tag's components { #find-a-tags-components }

Code that bundles or caches tags, such as a tool that compresses them
into one file, needs to know where each tag came from. Each group's
`css_entries` and `js_entries` (Experimental) hold the same tags as
`css` and `js`, in the same order, each as a
[`SerializedAssetEntry`][citry.SerializedAssetEntry]:

- `class_ids` names the components that declared the tag, by their
  [`class_id`][citry.Component.class_id]. It is empty for Citry's own
  tags, such as the runtime, preload hints and each app's data and
  start script, and usually for a Vue app's stylesheets. A tag that an
  `on_dependencies()` hook adds or rebuilds names a component only
  when the hook sets the tag's `origin_class_id`.
- `instance` is `True` when the tag may hold data from one render: a
  stylesheet with one component's `css_data()` values, every
  `app_assets` tag, and any tag Citry cannot show is the same on every
  render, such as one a hook adds or rebuilds. Keep such a tag out of a
  file that other pages share. It is `False` only for `runtime_assets`
  tags and for a component's own or `Dependencies` tags.

Citry fills both from what it recorded while it rendered each
component, so your code does not need to read the tags' attributes.
This example keeps the component tags that every page can share, with
the components that declared them:

```python
result = Page().render().serialize_result(
    deps_position="separate",
)
shareable = [
    (entry.tag, entry.class_ids)
    for entry in result.component_assets.css_entries
    if not entry.instance
]
```

`combine_assets()` combines the entries too. A merged tag lists the
components of every tag it replaced, and has `instance=True` when any
of them does. When you pass a group that has tags but no entries, such
as one you built yourself, the result has no entries for that kind of
tag. Creating a `SerializedAssets` whose entries name other tags than
its `css` or `js` raises `ValueError`.

### Split into several apps

[`needs_browser_runtime()`][citry.CitryRender.needs_browser_runtime]
returns whether a render needs Citry's browser runtime, so whether it
becomes a Vue app when serialized. Code that mixes Citry renders with
HTML from another template engine can use it to make only the
interactive children of a render into their own apps.

A child component's render may be serialized on its own before its
parent is serialized. The child becomes a separate Vue app with its own
assets, and the parent's render does not change. Components in
different apps do not share state, so keep components that work
together inside one child.

This works only when the child holds no slot content that a component
outside it wrote, such as text the parent passed between the child's
tags. Serializing such a child on its own raises
[`OutsideSlotContentError`][citry.OutsideSlotContentError]
(Experimental). Catch it to serialize the parent instead. It subclasses
`TypeError`, so code that catches `TypeError` also catches it.

This example serializes each interactive direct child of a render on
its own:

```python
from citry import CitryRender

rendered = List().render()
child_results = [
    part.serialize_result(deps_position="separate")
    for part in rendered.parts
    if isinstance(part, CitryRender)
    and part.is_component_root
    and part.needs_browser_runtime()
]
```

## Next steps

- [Component JS and CSS](/advanced/js-and-css-dependencies/) adds
  code and styles to one component.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files.
- [Component hooks](/advanced/hooks/) changes the tags one component adds.
- [Extensions](/advanced/extensions/) changes the tags for every page in an
  application.
