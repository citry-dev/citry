---
title: HTML fragments
url: https://citry.dev/v/0.4.0/advanced/html-fragments/
description: "Render a component for insertion into an existing page, including its client behavior and dependencies."
---
# HTML fragments

Return an HTML fragment when one request should replace only part of a page.
This works well for search results, modal contents, and HTMX-style swaps. The
server renders a component, while the browser keeps the rest of the document
in place.

There is one important choice on the receiving page:

- If the page already loaded Citry's runtime, a normal DOM insertion is
  enough. Citry discovers the new fragment and activates it.
- If the page did not load Citry, the insertion method must execute the
  fragment's loader script. Assigning a string to `innerHTML` does not execute
  inserted `<script>` elements.

## Render the fragment

Render a component, then serialize it with the `"fragment"`
[`DepsStrategy`](/v/0.4.0/reference/rendering/#citry-depsstrategy):


```python
html = Card(title="Welcome").render().serialize(
    deps_strategy="fragment",
)
```


The calls produce three different values:

1. `Card(...)` creates a [`CitryElement`](/v/0.4.0/reference/rendering/#citry-citryelement).
2. `.render()` creates a [`CitryRender`](/v/0.4.0/reference/rendering/#citry-citryrender).
3. `.serialize(...)` returns the HTML string sent to the browser.

The fragment contains the component markup plus the manifests needed for its
browser behavior and dependencies. If the component is entirely server-side,
Citry can return plain HTML without those additions.

## Make asset routes available

A client-active fragment refers to Citry's runtime and generated assets by
URL. Mount one of Citry's [web framework integrations](/v/0.4.0/web-frameworks/) so
those URLs can be served.

Client-active output includes components that use normal Alpine attributes,
[`$component`](/v/0.4.0/reference/browser-apis/#component), client props, browser or server event handlers, or
Events state. If such a fragment has no mounted integration or recorded route
prefix, serialization raises `RuntimeError` instead of returning broken URLs.

A worker that only renders fragments can record the prefix used by the
serving process with
[`Citry.set_mounted_prefix`](/v/0.4.0/reference/citry/#citry-citry-set-mounted-prefix):


```citry
from citry import Citry, Component

app = Citry()
app.set_mounted_prefix("/citry")


class Notice(Component):
    citry = app

    def js_data(self, kwargs, slots):
        return {"message": "Ready"}

    template = """
      <p class="notice">Loading...</p>
    """

    js = """
      $component(({ els, data }) => {
        els[0].textContent = data.message;
      });
    """


html = Notice().render().serialize(
    deps_strategy="fragment",
)
```


Set the prefix before serialization. The generated URLs are fixed when Citry
turns the render into a string.

## Insert into a page that already uses Citry

Load Citry once in the host document, then insert the response:


```html
<script src="/citry/citry.js"></script>
<div id="results"></div>
<script>
  fetch('/search-fragment')
    .then((response) => response.text())
    .then((html) => {
      document.getElementById('results').innerHTML = html;
    });
</script>
```


The existing runtime notices the fragment manifest, fetches missing assets,
and activates the complete fragment. Each dependency is loaded once per page.

## Insert into a page without Citry

A fragment can include a small loader for Citry's runtime. The browser still
has to execute that loader. Scripts inserted through `innerHTML` stay inert,
so the example in the previous section only works because Citry was already
loaded.

For a runtime-free host, use a swap library that executes response scripts, or
parse the response and recreate its `<script>` elements as live DOM nodes.
The loader can then start Citry and adopt the manifests that arrived with the
fragment.

Whichever insertion method you choose, insert the fragment as one transaction.
Do not split its markup, manifests, and ownership markers into separate swaps.

## Deliver component dependencies

Fragment serialization handles dependency declarations according to their
form:

- URL dependencies remain URLs and are fetched by the browser.
- Local files are included as script or style descriptors by default.
- With `Dependencies.local_files = "serve"`, mounted applications turn local
  files into fingerprinted URLs instead.
- Objects that only provide opaque pre-rendered HTML through `__html__` cannot
  be decomposed into a fragment dependency. Serialization raises `TypeError`;
  declare a `Script`, `Style`, or URL instead.

The [`deps_position`](/v/0.4.0/reference/rendering/#citry-depsposition) option applies to document and simple
serialization. A fragment always appends the information needed for adoption,
so that option is ignored.

## Run fragments across several workers

The request for a generated asset may reach a different worker from the one
that rendered the fragment. Configure a shared cache backend so every worker
can serve the generated values. See
[Cache backends](/v/0.4.0/advanced/cache-backends/) for Redis, DiskCache, Django, and
deployment generations.

Use the same mounted prefix and cache configuration in the rendering and
serving processes.

## Keep fragments intact in production

HTML optimizers and sanitizers must preserve Citry's ownership comments,
manifest scripts, and client attributes. See
[Preserve client-active HTML](/v/0.4.0/advanced/alpine-runtime/#preserve-client-active-html)
for the exact list.

## See also

- [Component JavaScript and CSS](/v/0.4.0/advanced/js-and-css-dependencies/) for a
  component's own browser behavior and styles.
- [Dependency files](/v/0.4.0/advanced/dependency-files/) for URLs and local files.
- [Client interactivity](/v/0.4.0/concepts/client-interactivity/) for browser scope
  and component lifecycles.
- [Event actions](/v/0.4.0/events/actions/) for returning rendered updates from a
  Python handler.
- [Rendering](/v/0.4.0/concepts/rendering/) for render and serialization choices.