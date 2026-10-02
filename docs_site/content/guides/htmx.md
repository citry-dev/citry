---
title: Use Citry with HTMX
description: Keep HTMX for requests and page updates while Citry renders the HTML, CSS, and JavaScript.
---

# Use Citry with HTMX

Already using HTMX? You can keep it and let Citry render the HTML that your
HTMX endpoints return, together with each component's CSS and JavaScript.
This suits a project that already has HTMX endpoints, or one that wants to
move to Citry one component at a time.

Each part keeps one job:

- your Python web framework handles routes, data, login, permissions, and
  request security;
- HTMX sends requests and replaces parts of the page;
- Citry renders each response and supplies the components' CSS and
  JavaScript.

For a new Citry app, try [Citry Events](/events/) first. It is built into
Citry and is usually simpler. Do not attach both HTMX and Citry Events to
the same button, input, or form.

## Return a component from an HTMX route

Render the component in a normal route and serialize it with
`deps_strategy="fragment"`:

```python
from fastapi.responses import HTMLResponse


@app.get(
    "/fragments/contacts/{contact_id}",
    response_class=HTMLResponse,
)
def contact_detail(contact_id: int) -> HTMLResponse:
    component = ContactDetail(contact=get_contact(contact_id))
    html = component.render().serialize(deps_strategy="fragment")
    return HTMLResponse(html)
```

The response holds the component's HTML plus what the browser needs to
load its CSS and JavaScript. Citry must be
[mounted on your web framework](/web-frameworks/) so it can serve those
files.

## Load HTMX and Citry on the page

Load a pinned copy of HTMX and Citry's browser runtime once, on the full
page:

```html
<script src="/static/htmx.min.js"></script>
<script src="/citry/citry.js"></script>

<main>
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

When HTMX inserts a Citry response, Citry's runtime notices it, loads its
CSS and JavaScript, and starts its components. HTMX needs no extension or
helper script for this.

In a Citry template, write a fixed HTMX attribute as plain HTML, such as
`hx-target="#results"`. When the value comes from component data, add
Citry's `c-` prefix: `c-hx-get="edit_url"`.

## Swap the response into a plain wrapper

Citry starts each inserted response as its own Vue app: a separate part of
the page that Vue controls. To update it, replace the whole response at
once.

Put a plain `<div>` or `<section>` on the page around the place where the
response goes, and target it with `hx-swap="innerHTML"`. Keep that wrapper
out of the HTML your route returns. HTMX then replaces the old response,
including the data Citry uses to start it, and the wrapper stays. A Citry
component can render several elements, only text, or nothing at all, so do
not rely on it having one outer element to replace.

These common HTMX patterns lose the data Citry needs to start the
component, so the component shows up but does nothing:

- `hx-select`, which keeps only part of the response;
- splitting one response into several out-of-band swaps;
- inserting the response directly into `<tbody>` or `<select>`. Replace a
  plain wrapper around the table or select instead.

For a list, render the list's wrapper on the server and serialize each
interactive row on its own. Insert those strings into the page as HTML; do
not use serialized fragment HTML as the source of a Vue template.

## Serve full pages and HTMX responses from one URL safely

Use separate URLs for full pages and HTMX responses when you can. If one URL
returns different HTML depending on the `HX-Request` header, add
`Vary: HX-Request` to the response. Otherwise a cache may return the HTMX
response when the browser asked for a full page, or the other way around.

If you use `hx-push-url`, check that every URL it adds to the browser
history also works when opened directly.

## Use HTMX attributes inside an interactive component

HTMX does not see `hx-*` attributes on elements that Vue creates after the
page loads. Give the element a `ref` and pass it to `htmx.process()` once
Vue has mounted the component:

```citry-html
<article ref="root">
  <button hx-get="/fragments/contacts/1/edit">Edit</button>
</article>
```

```javascript
$component({
  mounted() {
    window.htmx.process(this.$refs.root);
  },
});
```

Do not let HTMX rewrite elements inside a Vue app that stays on the page.
To change what it shows, replace the whole app through its wrapper, as
described above.

## Test the integration in a browser

Checking the response text is not enough. Run browser tests against the
same HTMX file you deploy, and check that:

- a slow search cannot overwrite a newer result;
- valid forms, invalid forms, empty results, and missing records behave as
  expected;
- changes that need a login reject bad CSRF tokens and users without
  permission;
- a component inserted later gets its CSS and JavaScript;
- a replaced component removes the styles it loaded;
- repeated requests for the same CSS and JavaScript come from the browser
  cache;
- the browser console and network log show no unexpected errors.

The
[HTMX patterns demo]({{ repo_url }}/tree/main/examples/demos/htmx){: target="_blank" rel="noopener"}
has search-as-you-type, an editable contact form, and a department picker
that refreshes the team list, with FastAPI routes, a pinned HTMX file, and
browser tests. [HTML fragments](/advanced/html-fragments/) explains
fragments in more detail.
