---
title: Use Citry with HTMX
description: Keep HTMX for requests and page updates while Citry renders the HTML, CSS, and JavaScript.
---

# Use Citry with HTMX

Already using HTMX? You can keep it. Citry can render the HTML returned by your
existing endpoints and include the CSS and JavaScript used by each component.

Give each part of the application one clear job:

- your Python web framework handles routes, data, authentication,
  authorization, and request security;
- HTMX sends requests and replaces parts of the page; and
- Citry renders each response and supplies the component's CSS and JavaScript.

If you are starting a new Citry application, try [Citry Events](/events/)
first. It is built into Citry and is usually the simpler choice. Use the HTMX
approach when you already have HTMX endpoints or want to introduce Citry a
component at a time. Do not attach both HTMX and Citry Events to the same
button, input, or form. This demo uses HTMX for every server interaction.

## Return the HTML, CSS, and JavaScript together

Render the component in a framework route and serialize it with
`deps_strategy="fragment"`:

```python
from fastapi.responses import HTMLResponse


@app.get("/fragments/search", response_class=HTMLResponse)
def search(q: str = "") -> HTMLResponse:
    component = SearchResults(contacts=find_contacts(q), query=q)
    return HTMLResponse(
        component.render().serialize(deps_strategy="fragment")
    )
```

The response contains the component's HTML plus the information Citry needs to
load its CSS and JavaScript. Insert the whole response. If you extract only
the visible HTML, the component may appear but its behavior may not start.

## Let HTMX send the request and update the page

Load a pinned copy of HTMX and Citry's browser runtime on the full page. With
HTMX 2.0.8 or newer, also copy and load `citry-htmx.js` from the demo:

```html
<script src="/static/htmx.min.js"></script>
<script src="/static/citry-htmx.js"></script>
<script src="/citry/citry.js"></script>

<main hx-ext="citry-fragments">
  <label for="contact-search">Search contacts</label>
  <input
    id="contact-search"
    type="search"
    name="q"
    hx-get="/fragments/search"
    hx-trigger="input changed delay:300ms"
    hx-target="#search-results"
    hx-swap="innerHTML"
    hx-sync="this:replace"
  />
  <div id="search-results"></div>
</main>
```

Write literal HTMX attributes as ordinary HTML, such as
`hx-target="#results"`. When a value comes from component data, add Citry's
`c-` prefix: `c-hx-get="edit_url"`.

With HTMX 2.0.8 or newer, Chromium can remove markers that Citry needs while
parsing a response. The HTML still appears, but Citry may not load the
component's CSS or run its JavaScript.

The bundled `citry-htmx.js` extension preserves those markers during the
swap. Add `hx-ext="citry-fragments"` to the page, or to any section where HTMX
inserts Citry-rendered HTML.

Use the extension only with `hx-swap="innerHTML"` on a wrapper that stays on
the page. It raises an error for `outerHTML`, `beforebegin`, `afterbegin`,
`beforeend`, and `afterend`. After those swaps, the extension cannot reliably
find all the nodes HTMX just inserted. It does not support out-of-band swaps.

## Update a plain wrapper around the component

Put a plain `<div>` or `<section>` around the area HTMX will update. Keep the
wrapper outside the HTML returned by the route. `innerHTML` then replaces its
contents while leaving the wrapper on the page. A Citry component can render
several elements, only text, or even no HTML, so you cannot assume it always
has one outer element to replace.

Do not use `hx-select` to extract only the visible part of a Citry fragment.
Do not split one response into several out-of-band swaps. Both approaches can
discard the data Citry needs to start the component. Also avoid inserting
these responses directly into `<tbody>` or `<select>`; replace a plain wrapper
around the table or select instead.

Use separate URLs for full pages and HTMX responses when practical. If one URL
returns different HTML based on the `HX-Request` header, add
`Vary: HX-Request`. Otherwise, a cache may return the HTMX response when the
browser asked for a full page, or the other way around. If you use
`hx-push-url`, make sure every URL it adds to history also works when opened
directly.

## Test the actual integration

Checking the response text is not enough. Run browser tests against the same
HTMX file you deploy, and check that:

- a slow search cannot overwrite a newer result;
- valid forms, invalid forms, empty results, and missing records behave as
  expected;
- authenticated changes reject bad CSRF tokens and unauthorized users;
- a component inserted later receives its CSS and JavaScript;
- Citry avoids duplicate dependencies while components that use them remain;
- Citry removes a component's CSS after its last instance leaves and restores
  it when another instance appears; and
- the browser console and network log stay free of unexpected errors.

The complete
[HTMX patterns demo]({{ repo_url }}/tree/citry%400.4.4/examples/demos/htmx){: target="_blank" rel="noopener"}
contains search-as-you-type, an editable contact form, and a department picker
that refreshes the team list. It also includes FastAPI routes, a pinned HTMX
runtime, and browser tests. See
[HTML fragments](/advanced/html-fragments/) for the serialization contract.
