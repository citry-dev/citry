---
title: Component previews
description: Keep named examples beside components, browse their gallery, and capture PNGs from the CLI.
---

# Component previews

To check how a component looks in each of its states, you would normally
build a page that renders it with different inputs. Previews let you write
those examples on the component itself. Citry then shows them all in a
gallery in your browser, or saves a screenshot of each one, for example to
review visual changes. The idea is similar to
[Storybook](https://storybook.js.org/){: target="_blank" rel="noopener"},
but simpler.

The preview extension adds two commands:

- `serve` runs a local web server with a gallery of your previews.
- `render` saves a PNG screenshot of each preview with Playwright.

## Add examples

Install the extra dependencies:

```sh
pip install 'citry[ext-preview]'
```

Add `PreviewExtension` when you create your `Citry` instance, before any
component is defined or discovered. Then give a component a nested
`Preview` class whose `variants()` method lists its examples. A variant is
one named example: a set of inputs plus a label for the gallery.

```citry
# myproject/components.py
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
                    description="Paused while saving.",
                    params={"label": "Saving...", "disabled": True},
                ),
            ]

    template = """
      <button c-disabled="disabled">{{ label }}</button>
    """
```

Each variant takes:

- `slug`, a short name for URLs and file names. It uses lowercase
  letters, digits, and single hyphens, and must be unique within the
  component.
- `label`, the title shown in the gallery. It is not passed to the
  component; the button text above comes from `params["label"]`.
- `params`, the inputs to render the component with.
- `description`, optional text shown with the example.

`group` is a label that the gallery shows next to the component's name.

To preview a component with its default inputs only, write
`class Preview:` with `enabled = True` and no variants. A component with
no `Preview` content gets no preview. Set `enabled = False` to turn off
previews that a component inherits from its base class.

## Browse the gallery

Start the preview server:

```sh
citry --app myproject.components:app ext run preview serve
```

Open the URL it prints. The server runs until you press Ctrl-C. It uses
port 8001 by default; pass `--port 0` to pick any free port. Refresh the
page to see changes to preview template files. Restart the command after
changing Python code.

The gallery shows each example in its own frame (an iframe), sized to the
example's viewport (the frame's width and height). Each frame is a separate
page, so one example's styles and teleported content stay inside its
frame. An example wider than the window
scrolls rather than shrinking. All frames share one server, and may share
browser storage such as cookies.

To show only some components, name them, choose variants, or filter by
directory:

```sh
citry --app myproject.components:app ext run preview serve Button
citry --app myproject.components:app ext run preview serve \
  Button --variant disabled
citry --app myproject.components:app ext run preview serve \
  --dir 'myproject/components/**'
```

Separate several names with commas. A name can be a component's
registered name or an alias. A directory filter is relative to the current
directory, and `**` includes subdirectories. Repeat `--dir` to include
several directories. When you give both names and
directories, a named component must also be inside one of the directories.
The command fails when a filter matches nothing, a named component has no
previews, or a named variant does not exist.

## Save screenshots

Install Chromium for Playwright once, then run `render`:

```sh
playwright install chromium
citry --app myproject.components:app ext run preview render \
  --outdir ./preview_imgs
```

The command starts its own preview server and opens each variant in a
fresh browser. It writes one `<component_id>/<slug>.png` per variant, plus
a `manifest.json` file that lists the result of each one. If any variant
fails, the command exits with an error, and the images that succeeded stay
on disk. Pass `--overwrite` to replace existing images; other files in the
directory are left alone.

To take screenshots from a `preview serve` that is already running, pass
its address:

```sh
citry --app myproject.components:app ext run preview render \
  --base-url http://127.0.0.1:8001/citry
```

The command checks that the server has the variants you asked for, and
leaves it running afterward.

Each screenshot waits for the page, its fonts, and its images to load, and
CSS animations are turned off. If the component loads data on its own
after that, add `--ready-selector '[data-ready="true"]'` and make the
component show that element only when it is ready. `--timeout 30` limits
each screenshot to 30 seconds.

The preview server does not run your web app. Middleware, static file
routes, sessions, and test data setup are not there, so each example must
supply what it needs. Fixed clocks, random values, and outside data are
also up to you, if you want the same screenshot on every run.

## Wrap an example

By default a variant renders the component alone with its `params`. Give
`Preview` a `template` to build the example yourself, for example to place
the component in a section or fill its slots:

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

The template can read `params` and `preview`, which describes the current
variant. It renders only the example; the page around it comes from the
page layout (see below).

To keep the template in a file, set
`template_file = "button.preview.citry-html"` instead. A relative path
starts from the file that declares the `Preview` class, also when a
subclass inherits it. Set `template` or `template_file`, not both. A
missing or unreadable file makes that preview fail.

## Set size and frame

Import `Viewport` and `Layout` from `citry.ext.preview`. A viewport sets the
width and height an example renders at. Set one for the component, or pass
`viewport=` to a single `variant()`:

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

A layout is the markup around an example. The example goes into its
`content` slot. There are two kinds:

- `variant_layout` wraps one example.
- `page_layout` is the full HTML page around the examples. It receives a
  `PreviewPage` as `preview`.

Give a layout exactly one source: `template`, `template_file`, or
`component=YourLayoutComponent`. A layout component must use the same
`Citry` instance, accept `preview` in its `Kwargs`, and accept a `content`
slot.

## Share defaults

Set defaults for every component on the `Citry` instance:

```python
app = Citry(
    extensions=[PreviewExtension],
    extensions_defaults={
        "preview": {
            "viewport": Viewport(width=1024, height=768),
        },
    },
)
```

The defaults accept `group`, `viewport`, `variant_layout`, and
`page_layout`. They do not turn on previews for components that have none.
A relative layout file set here starts from the working directory at the
time the extension is created, so use an absolute path if you run the
command from different directories.

## Build a custom gallery

A custom `page_layout` can list the examples itself. `preview.components`
holds one group per component, with `component` details and `items`. Each
item has `variant` details and `content`; write `{{ item.content }}` to
place it. On a gallery page, `content` is a frame; on a page for one
variant, it is the example itself. `preview.selection` is `"variant"`,
`"component"`, or `"all"`, depending on which page is shown.

A component's `page_layout` applies to its own preview pages and its own
gallery. The gallery of all components uses the default from the `Citry`
instance, but the frames inside it still use each component's page
layout. If your layout leaves out `{{ item.content }}` or writes it
twice, the page shows exactly that.

## Preview a simple component

A component with `simple = True` cannot have its own `Preview` class. To
preview one, write an ordinary component with previews that uses the
simple component in its template. A layout component must also be an
ordinary component, because it receives the example in a named `content`
slot, and a simple component accepts only default content.

!!! note "When `variants()` runs"

    Citry calls `variants()` each time it lists the examples, without
    rendering the component. It can read `self.component_class` but not
    `self.component`. Return a list or tuple, with new mutable values on
    each call when the component may change them. Do not create database
    records or other test data in `variants()`.
