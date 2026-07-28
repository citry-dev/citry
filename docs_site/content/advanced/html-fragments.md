---
title: HTML fragments
description: Render a component as an HTML fragment for HTMX-style swaps, and let citry load its JS and CSS in the browser.
---

# HTML fragments

A fragment is a rendered component prepared for insertion into a page that is
already loaded. This is the shape you want for HTMX swaps or a plain
`fetch()` that sets `innerHTML`: the server returns a chunk of HTML, the
browser drops it into the page, and citry wires up the component's JavaScript
and CSS for you.

## Render a component as a fragment

Build the component, render it, then serialize it with the `"fragment"`
strategy:

```python
card = Card(title="Welcome")
card.render().serialize(deps_strategy="fragment")
```

Each step in that chain does one thing. `Card(title="Welcome")` returns a
[`CitryElement`][citry.CitryElement]. `.render()` returns a
[`CitryRender`][citry.CitryRender]. Its `serialize` method returns the final
HTML string. The `deps_strategy` argument is a [`DepsStrategy`][citry.DepsStrategy]
value; `"fragment"` is the one meant for insertion into a live page.

Unlike the default `"document"` strategy, the fragment output does not inline
component asset bodies. It carries the markup, client ownership and Events
manifests when needed, a small pre-loader, and a dependency manifest. The
browser validates and adopts the complete transaction before component
callbacks observe it, and fetches each referenced asset once per page.

## Fragments need a mounted web framework

Because a client-active fragment refers to runtime and component assets by URL,
citry has to know where those assets are served from. Client activity includes
Alpine directives, `$component`, `$c-props`, component-tag handlers, Events,
and scoped template fills; it is not limited to a component declaring JS or
CSS. The routes come from a mounted web integration. See
[Web frameworks](/web-frameworks/) for the adapters (FastAPI, Flask, Django,
and the generic ASGI or WSGI apps).

If the fragment needs client activation or asset URLs and nothing is mounted,
`serialize(deps_strategy="fragment")` raises `RuntimeError` telling you to
mount an integration or set the prefix yourself. Only genuinely server-only
output emits plain HTML without a client graph.

In a worker process that renders fragments but does not serve them, record the
prefix directly with `set_mounted_prefix` (use the same prefix the serving
process mounts at):

```citry
from citry import Citry, Component

c = Citry()
c.set_mounted_prefix("/citry")

class Frag(Component):
    citry = c
    template = """
        <div class="frag">frag</div>
    """
    js = """
        $component(({ els, data }) => {
            els[0].setAttribute('data-n', String(data.n));
        });
    """

    def js_data(self, kwargs, slots):
        return {"n": 42}

# The prefix must be set before serializing: the fragment references
# its scripts by URL.
fragment_html = Frag().render().serialize(deps_strategy="fragment")
```

The rendered HTML holds the `<div class="frag">` markup plus a manifest of
`/citry/cache/...` URLs. The browser fetches and runs them on demand; the JS
and CSS bodies are never inlined into the fragment.

## Load a fragment in the browser

On the host page, load the citry runtime once, fetch a fragment, and set it as
`innerHTML`:

```html
<html>
  <head><script src="/citry/citry.js"></script></head>
  <body>
    <div id="target"></div>
    <script>
      fetch('/fragment')
        .then((r) => r.text())
        .then((html) => { document.getElementById('target').innerHTML = html; });
    </script>
  </body>
</html>
```

Once the fragment lands in the page, citry's runtime notices the inserted
manifest and fetches and runs the component's JS and CSS. A fragment dropped
into a page that has not loaded the runtime also ships a pre-loader for
`citry.js`, but the fragment consumer must execute inserted script elements.
Browsers do not execute `<script>` tags created by assigning `innerHTML`, so
the plain assignment above is sufficient only because that host page already
loads the runtime. For runtime-free hosts, use a swap library that executes
fragment scripts, or recreate each inserted script node after parsing it. The
pre-loader then starts Citry, which discovers the inert graph and dependency
manifests already present in the fragment.

## Good to know

- `set_mounted_prefix` must run before you serialize, because the fragment
  embeds its script URLs at serialize time.
- `deps_position` (the [`DepsPosition`][citry.DepsPosition] argument) only
  affects the `"document"` and `"simple"` strategies. A fragment always
  appends its manifest, so `deps_position` is ignored for `"fragment"`.
- If you run more than one worker, point them at a shared cache backend. The
  `/cache` endpoint may be served by a different process than the one that
  rendered the fragment, and it needs the shared store to serve the
  per-instance variables script. The Django adapter ships a
  `DjangoCache` for this; see [Caching](/advanced/caching/).
- A [`Dependency`][citry.ext.dependencies.Dependency] that points at a local file has no URL, so
  in a fragment it rides inline as a tag descriptor rather than as a fetch URL.
- Preserve Citry's ownership comments and manifest tags when an HTML minifier,
  CDN, sanitizer, or client DOM library handles the response. See
  [Alpine runtime](/advanced/alpine-runtime/#preserve-client-graph-markers).

## See also

- [JS and CSS dependencies](/advanced/js-and-css-dependencies/) for how a
  component declares its scripts and styles.
- [Client interactivity](/concepts/client-interactivity/) for activation and scope ownership.
- [Event actions](/events/actions/) for handlers that return and apply
  rendered updates.
- [Rendering](/concepts/rendering/) for the render and serialize model.
- [Web frameworks](/web-frameworks/) to mount the routes that serve fragment
  assets.
