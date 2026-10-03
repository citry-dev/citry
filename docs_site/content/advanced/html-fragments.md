---
title: HTML fragments
description: Render a component for insertion into an existing page, including its client behavior and dependencies.
---

# HTML fragments

Sometimes one request should update only part of a page that is already
open: search results below a search box, the contents of a modal, or an
htmx-style swap. Render a component as an HTML fragment, send it, and
insert it into the page. The rest of the page stays as it is, and the
fragment's styles and browser behavior work once it is inserted.

If the update comes from a Python [event handler](/events/), you do not need
this page: return the component from the handler and Citry updates the page
for you. See [Event actions](/events/actions/).

## Render a fragment

Render the component, then serialize it with `deps_strategy="fragment"`:

```python
card = Card(title="Welcome")
html = card.render().serialize(
    deps_strategy="fragment",
)
```

The result is the component's HTML plus what the browser needs to load its
JavaScript and CSS and start its Vue behavior. A component with no
JavaScript, CSS, or browser behavior comes back as plain HTML.

[`DepsStrategy`][citry.DepsStrategy] lists the other ways to place
JavaScript and CSS, and [Rendering](/concepts/rendering/) explains the
`render()` and `serialize()` steps.

## Insert into a Citry page

Load Citry's runtime once in the page, then insert the response wherever
you like:

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

The runtime notices the new fragment, loads the scripts and stylesheets it
is missing, and starts the fragment's components as their own Vue app. A
component script the page already loaded is not loaded or run again.
Removing the fragment's elements from the page stops its Vue app.

Each fragment adds its own stylesheet link, so its styles stay in place even
if the page's own Vue app is removed. The browser usually serves the
repeated link from its cache.

Insert the whole response in one step. Do not split it into separate swaps,
because the fragment's HTML and the data block that describes its
components must arrive together.

## Insert into other pages

When the page has not loaded Citry, the fragment brings a small script that
loads the runtime. That script must run, and a `<script>` added through
`innerHTML` does not run. The example above works only because Citry was
already on the page.

Use a swap library that runs scripts in the response, such as htmx, or
parse the response and create its `<script>` elements again as new DOM
nodes. The script then loads Citry, which starts the fragment.

## Serve Citry's files

A fragment with JavaScript or CSS loads it by URL, and an interactive
fragment loads Citry's runtime by URL too. Add one of Citry's
[web framework integrations](/advanced/web-frameworks/) to your app so those URLs
work.

This applies when the fragment has any of these:

- a component's `js` or `css`, or a `Dependencies` entry, even an inline
  `Script`;
- Vue bindings or [`$component`][$component] options;
- browser or server event handlers, or Events State;
- browser data from Python, such as `js_data()`.

Serializing such a fragment raises `RuntimeError` when no integration is
added and no prefix is recorded (below), so it never returns broken
URLs.

A worker that renders fragments but does not serve Citry's routes can
record the URL prefix the serving process uses, with
[`Citry.set_mounted_prefix`][citry.Citry.set_mounted_prefix]:

```citry
from citry import Citry, Component

app = Citry()
app.set_mounted_prefix("/citry")


class Notice(Component):
    citry = app

    def js_data(self, kwargs, slots):
        return {"message": "Ready"}

    template = """
      <p class="notice" v-text="message"></p>
    """


notice = Notice()
html = notice.render().serialize(
    deps_strategy="fragment",
)
```

Call it before serializing, because the URLs are written into the HTML at
that point.

## Render fresh each time

If a second insertion of the same fragment loses its styling or browser
behavior, check whether your endpoint returns HTML it serialized earlier.
An interactive fragment can be inserted only once per page, and Citry
rejects a second copy. Render a new fragment for each response, even when
the content has not changed:

```python
# Wrong: every request returns the same rendered fragment.
card = Card(title="Welcome")
saved_html = card.render().serialize(
    deps_strategy="fragment",
)


def card_fragment():
    return saved_html
```

```python
def card_fragment():
    # Right: render a new fragment for each request.
    card = Card(title="Welcome")
    return card.render().serialize(
        deps_strategy="fragment",
    )
```

A static demo that ships one pre-rendered fragment can insert it once, then
reload the page to let the reader try again.

## Keep fragments intact

HTML optimizers and sanitizers must not remove or change the data block a
fragment carries, or the Citry runtime on the page that reads it. See
[Preserve page HTML](/vue/server-rendering/#preserve-interactive-html).

## Use several workers

The browser's request for a fragment's JavaScript or CSS may reach a
different worker from the one that rendered the fragment. Configure a
shared cache backend so that every worker can serve those files. See
[Cache backends](/performance/cache-backends/).

Use the same URL prefix and cache configuration in the processes that
render and the processes that serve.

## How assets load

A fragment includes each [dependency](/advanced/dependency-files/)
according to how you declared it:

- A URL stays a URL, and the browser loads it.
- A local file is included in the fragment by default.
- With `Dependencies.local_files = "serve"`, a local file becomes a URL
  served by the web framework integration.
- An object that provides only finished HTML through `__html__` raises
  `TypeError`. Declare a `Script`, `Style`, or URL instead.

A fragment ignores [`deps_position`][citry.DepsPosition], which applies only
to the `document` and `simple` strategies.

## See also

- [Component JS and CSS](/advanced/js-and-css-dependencies/) for a
  component's own browser behavior and styles.
- [Dependency files](/advanced/dependency-files/) for URLs and local files.
- [Component options](/vue/component-options/) for browser state and
  component lifecycles.
- [Event actions](/events/actions/) for returning rendered updates from a
  Python handler.
- [Rendering](/concepts/rendering/) for render and serialization choices.
