---
title: Component previews
url: https://citry.dev/v/0.5.1/advanced/previews/
description: "Keep named examples beside components, browse their gallery, and capture PNGs from the CLI."
---
# Component previews

The Preview extension lets you define examples beside your components and open
them in a gallery. Similar idea to [Storybook](https://storybook.js.org/){: target="_blank" rel="noopener"},
but simpler.

It has two modes:

- `serve` - Run a web server where you can explore previews of all your components.
- `render` - Render the previews and save their screenshots with Playwright.

## Define an example

Install the dependencies:


```sh
pip install 'citry[ext-preview]'
```


Add `PreviewExtension` when constructing your Citry app, before defining or
discovering components. In `myproject/components.py`:


```citry
from citry import Citry, Component
from citry.ext.preview import PreviewExtension, variant

app = Citry(extensions=[PreviewExtension])

class Button(Component):
    citry = app

    class Kwargs:
        label: str = "Save"
        disabled: bool = False

    class Preview:
        group = "Actions"

        def variants(self):
            return [
                variant(
                    slug="default",
                    label="Ready to save",
                    params={"label": "Save"},
                ),
                variant(
                    slug="disabled",
                    label="Saving",
                    description="The action is temporarily unavailable.",
                    params={"label": "Saving...", "disabled": True},
                ),
            ]

    template = """
        <button c-disabled="disabled">{{ label }}</button>
    """
```


The variant's `label` describes the example. The button's visible text lives in
`params["label"]`. A `slug` is a stable lowercase name using letters, digits, and
single hyphens; it must be unique within that component.

For an example using only component defaults, declare `class Preview:` with
`enabled = True`. A component without preview content or variants is omitted.
Use `enabled = False` to opt out of inherited previews.

## Browse previews

Start a separate preview server:


```sh
citry --app myproject.components:app ext run preview serve
```


Open the printed gallery URL. The server stays running until Ctrl-C and does
not start Playwright or open a browser. Its default port is 8001; use
`--port 0` to choose a free port. Python changes require restarting the command;
preview template file changes take effect when you refresh the page.

The gallery shows all selected variants in separate iframes. Each frame uses
the variant's width and height, keeping component styles and teleport targets
inside that document. The surrounding page scrolls wide frames rather than
shrinking them. Frames share the server and may share browser storage.

Component names, variants, and source directories can narrow either command:


```sh
citry --app myproject.components:app ext run preview serve Button
citry --app myproject.components:app ext run preview serve \
  Button --variant disabled
citry --app myproject.components:app ext run preview serve \
  --dir 'myproject/components/**'
```


Names are comma-separated registered names or aliases. Directory filters use
paths relative to the working directory; `**` includes nested directories.
Multiple directory filters combine, and named components must also match any
directory filters. Explicit names without available previews, missing selected
variants, and filters matching nothing produce errors.

## Capture PNGs

Install Chromium once, then run a capture:


```sh
playwright install chromium
citry --app myproject.components:app ext run preview render \
  --outdir ./preview_imgs
```


The command starts a temporary preview server and captures each variant in a
fresh browser context. It writes `<component_id>/<slug>.png` and
`manifest.json`, which records each result. A failed variant makes the command
exit unsuccessfully, while completed images and diagnostics remain available.
Existing outputs require `--overwrite`; unrelated files are retained.

To reuse a running `preview serve` session:


```sh
citry --app myproject.components:app ext run preview render \
  --base-url http://127.0.0.1:8001/citry
```


The base URL identifies the preview server's mounted Citry root. The command
checks that its catalog contains the requested variants and leaves that server
running afterward.

Capture waits for document load, fonts, and images. For asynchronous application
work, use `--ready-selector '[data-ready="true"]'` with an element your component
shows only when ready. `--timeout 30` bounds each capture in seconds. Capture
disables CSS animations, but your fixtures still control clocks, randomness,
and external data. Ordinary application middleware, static routes, sessions,
and fixture setup are not created by the preview host.

## Compose an example with a template

A preview template owns the entire example, including child components and
slot content. Its variables are `params` and `preview` metadata:


```python
class Preview:
    template = """
        <section>
            <h2>{{ preview.variant.label }}</h2>
            <c-button c-label="params['label']" />
        </section>
    """

    def variants(self):
        return [
            variant(
                slug="default",
                label="Button in a section",
                params={"label": "Save"},
            ),
        ]
```


Place this nested class inside the component. You can use
`template_file = "button.preview.citry-html"` instead of inline source. Relative
paths resolve beside the declaration, including inherited declarations. Define
only one of `template` and `template_file`; missing or unreadable files fail the
preview. Templates are fragments; the page layout owns the HTML document.

`variants(self)` runs without a rendered component instance. It can refer to
`self.component_class`, but cannot access `self.component`. Return a list or
tuple of variants, with fresh mutable input values when needed. Keep database
mutation and fixture setup outside enumeration.

## Choose viewports and layouts

Import `Viewport` and `Layout` from `citry.ext.preview`. Set a component default
viewport or pass an override to `variant()`:


```python
class Preview:
    enabled = True
    viewport = Viewport(width=420, height=800)
    variant_layout = Layout(template="""
        <section>
            <h2>{{ preview.variant.label }}</h2>
            <c-slot name="content" />
        </section>
    """)
```


`variant_layout` wraps one example. `page_layout` supplies a complete HTML
page, receives a `PreviewPage` as `preview`, and places the same `content` slot.
Each layout accepts exactly one source: `template`, `template_file`, or
`component=YourLayoutComponent`. A layout component must belong to the same app,
accept `preview` in its `Kwargs`, and accept a `content` slot.

A custom page layout may iterate `preview.components`. Each group has
`component` metadata and `items`; each item has `variant` metadata and lazy
`content`. Render `{{ item.content }}` to place an item. On a gallery page that
content is an iframe; on a single-variant page it is the example. The page's
`selection` is `"variant"`, `"component"`, or `"all"`.

A component's page layout applies to individual previews and its single-component
gallery. The all-component gallery uses the engine default. Iframes retain
the component's own page layout. Custom layouts own any omitted or repeated
content, as with ordinary slots.

Share presentation defaults with the engine:


```python
app = Citry(
    extensions=[PreviewExtension],
    extensions_defaults={
        "preview": {"viewport": Viewport(width=1024, height=768)},
    },
)
```


Engine defaults accept `group`, `viewport`, `variant_layout`, and `page_layout`.
Relative layout files configured there resolve from the working directory when
the extension is attached; use absolute paths when running from different
locations. Engine defaults do not enable previews on every component.


## Preview simple components

A component with `simple = True` cannot declare its own `Preview` configuration.
Define an ordinary component with previews enabled and call the simple component
from its template to exercise it in a preview. Component-based preview layouts
must also be ordinary components: layouts receive a named `content` slot, while
simple components accept only default content.