---
title: Troubleshooting
description: Fix common Citry problems: render errors, components that do nothing in the browser, editor checks that stop, and tools to trace a render.
---

# Troubleshooting

Use this page when something goes wrong: a render raises an error, a
component shows up in the browser but does nothing, or the editor stops
checking your components. Each entry starts with what you see, then the
cause and the fix. The tools at the end of the page help with bugs that
have no clear error.

## Which component failed

You see a bare exception such as `KeyError: 'name'`, and the page has many
components.

Read the first line of the message. Citry adds the path from the outermost
component down to the one that failed. Take a `Page` that renders a
`Card`, which renders an `Avatar` that never receives the `name` it reads:

```citry
from citry import Component


class Avatar(Component):
    def template_data(self, kwargs, slots):
        return {"name": kwargs["name"]}

    template = """
      <img c-alt="name" />
    """


class Card(Component):
    template = """
      <div class="card">
        <c-Avatar />
      </div>
    """


class Page(Component):
    template = """
      <main>
        <c-Card />
      </main>
    """


page = Page()
str(page)
```

The error names the whole chain:

```text
An error occurred while rendering components Page > Card > Avatar:
name
```

The last name, `Avatar`, is where the error happened. The path stays in the
exception's message, so your own `try`/`except` sees it too. When the
error happens inside slot content, the path also names the slot, for
example `Page > Layout > Layout(slot:body)`.

## Error in a template

You see `Error in variable: KeyError: 'user_name'`, followed by a snippet
of your template.

The template reads a name that the component never provides. Here
`Profile` reads `user_name` but never defines it:

```citry
from citry import Component


class Profile(Component):
    template = """
      <p>Welcome, {{ user_name }}</p>
    """
```

The error points at the exact expression, names the component, and shows
the file it lives in:

```text
An error occurred while rendering components Profile:
Error in variable: KeyError: 'user_name'

     1 | user_name
         ^^^^^^^^^

In template of 'Profile' (/path/to/profile.py::Profile):

     1 |
     2 | <p>Welcome, {{ user_name }}</p>
                     ^^^^^^^^^^^^^^^
     3 |
```

Return the missing name from `template_data()`, or fix its spelling in the
template.

## Component does nothing

The page looks right, but buttons, menus, and other browser behavior do
not work. Open the browser console and find the first message that starts
with `[Citry]`. Later errors are often caused by the first one, so fix
that one first.

| What the console shows | Cause | Fix |
|---|---|---|
| 404 responses for `citry.js`, component code, or stylesheets | Citry is not mounted on your web app, or another worker process answered without the stored files | [Mount Citry](/web-frameworks/), and [share the cache between worker processes](/web-frameworks/#share-the-cache-between-worker-processes) |
| `[Citry] discarded Vue fragment` | An inserted fragment arrived incomplete, or its files did not load | Insert the whole response, and fix the first network error |
| `[Citry] expected one configuration block for app ...` | A tool such as an HTML minifier, sanitizer, or your own script removed part of the HTML Citry wrote | [Keep Citry's elements and data blocks in the HTML](/advanced/vue-runtime/#preserve-interactive-html) |

Citry checks the data the server sends before it changes the page, so it
rejects a broken update as a whole. Fix the first error rather than
working around it.

## `v-for` on a component

The template fails to load, and the error says:

```text
Vue directive 'v-for' is not supported on the component tag
'<c-Card>'. A browser 'v-for' cannot create Citry components.
Repeat the component with '<c-for>'.
```

`v-for` is a Vue loop that runs in the browser, and the browser cannot run
your Python components. Repeat the component with
[`<c-for>`](/syntax/control-flow/), which loops on the server.

## Missing or wrong prop

`citry check` or the editor reports that a required Vue prop is missing,
for example:

```text
Required Vue prop 'open' is missing for <c-dialog>.
```

Or it reports that a Vue prop expects a different type than the binding
passes.

The child component declares the prop in its JavaScript `props`, and the
parent's tag does not pass it, or passes a value of the wrong type. Pass
the prop on the parent's tag with `:name="..."` or `v-bind`, or change the
child's `props` declaration.

## Editor: syntax only

The VS Code status bar shows `Citry: syntax only`, and the editor reports
template syntax errors but does not check component names, inputs, or
slots.

The Citry language server, the editor helper that runs these checks,
could not load your Citry app. When it works, the status bar shows `Citry`
with a check mark. To fix it:

1. Install `citry-lsp` in the Python environment the workspace uses:

   ```console
   python -m pip install citry-lsp
   ```

2. Set `citry.app` to the Citry instance your app starts, written as
   `module:attribute`, for example `myproject.app:engine`. A component
   library author can set it to the library's manifest instead, such as
   `acme_ui:__citry_library__`; the editor then checks only that
   library's components.
3. Run **Citry: Show Language Server Status**. It shows the Python
   interpreter, the app setting, the Citry version, and the error from
   loading your app, if any.
4. If the interpreter is wrong, select the right Python environment or set
   `citry.python` to its executable. Then run
   **Citry: Restart Language Server**.

The language server loads your app in a separate process and waits up to
15 seconds. If the import fails, exits, crashes, or takes too long, or the
installed `citry-lsp` does not support your Citry version, the editor
keeps working with syntax checks only. Fix the first error the
status shows, then restart the server. Anything your app prints while it
loads also appears in the status.

!!! note "A template file opens as plain HTML"

    The editor does not treat every `.html` file as a Citry template,
    because a template file can have any name. Once the editor has loaded
    your app, it checks the files your components name in
    `template_file`. For any other template, select the **Citry
    Template** language mode, or add a `files.associations` rule to your
    workspace settings.

## Trace a render

When the output is wrong but nothing raises, turn on Citry's logs. Citry
logs through the standard Python logger named `citry`, at two levels:

- `DEBUG`: loading a component's HTML, JS, and CSS files, and finding
  component modules;
- `TRACE`: each component, slot, and template part as it starts and
  finishes rendering, and which content each slot received.

`TRACE` is a level that Citry adds below `DEBUG`, with the number `5`.
Python's `logging` module has no name for it, so set the level to `5`:

```python
import logging

logging.basicConfig(
    level=5,
    format="%(levelname)s %(name)s %(message)s",
)
```

A small page that renders a `Hello` component inside `HomePage` then logs
lines like these (some `RENDER NODE` lines left out):

```text
TRACE citry RENDER COMPONENT: 'HomePage' ID ck52imnvf PATH: HomePage
TRACE citry RENDER NODE ComponentNode @7:18
TRACE citry RENDER COMPONENT: 'Hello' ID ck52imnvg PATH: HomePage > Hello
```

A `RENDER COMPONENT` line shows the component, its render ID, and its path
in the tree. A `RENDER NODE` line shows one part of the template; its
`@start:end` numbers, when present, mark where that part sits in the
template source.

`basicConfig` turns on logs for your whole program. To change only Citry's
logs, set the level on its logger:

```python
import logging

logging.getLogger("citry").setLevel(5)
```

With `TRACE` on, a render takes about twice as long, plus the time to
write each line. Use it while debugging, not in production. When it is
off, it costs almost nothing.

## Show component boxes { #visualize-component-and-slot-boundaries }

Add the [Debug][citry.ext.debug.Debug] extension to draw a box around each
component and slot on the page. Component boxes are blue and show the
component class and render ID. Slot boxes are red and show the component
that receives the slot and the slot name.

```citry
from citry import Citry, Component
from citry.ext.debug import Debug

app = Citry(
    extensions=[Debug],
    extensions_defaults={
        "debug": {
            "highlight_components": True,
            "highlight_slots": True,
        },
    },
)


class Card(Component):
    citry = app

    template = """
      <article><c-slot name="body" /></article>
    """
```

These settings apply to every component. To change them for one
component, add a nested `Debug` class:

```citry
class Layout(Component):
    citry = app

    class Debug:
        highlight_components = False
        highlight_slots = True

    template = """
      <main><c-slot /></main>
    """
```

Debug wraps each component's output and does not change the elements the
component writes. It draws no box around a component or slot that
renders a whole HTML document, or around a transparent component.

!!! warning "Debug boxes can change your layout"

    Each box is a real `<div>`. It can break flex and grid layouts, CSS
    rules that select direct children, and content that must sit directly
    inside a `<table>` or `<select>`. Use Debug while developing, not in
    production or in tests that depend on layout. To inspect what another
    extension changed in the output, list Debug after that extension.

## Save the HTML

To read exactly what a component produced, save it to a file. `str()` on a
component renders it and returns the HTML:

```python
page = HomePage()
html = str(page)
with open("result.html", "w", encoding="utf-8") as f:
    f.write(html)
```

To choose where JavaScript and CSS go, render and serialize in two steps:
`page.render().serialize()` returns the same HTML and takes the
options described in [Asset placement](/advanced/asset-placement/).

## Ask an AI agent

An AI coding agent can debug a render if you give it three things: the
component source, which is already in your repository, the HTML that was
produced, and the trace log.

Save the HTML as shown above, and write the trace log to its own file:

```python
import logging

handler = logging.FileHandler("citry.log", mode="w")
citry_logger = logging.getLogger("citry")
citry_logger.setLevel(5)
citry_logger.addHandler(handler)
```

Then attach both files and ask, for example:

> I have a citry project. Citry is component-based web rendering for
> Python, in the style of Vue or React.
>
> I am rendering the `HomePage` component, but the output is missing the
> greeting. The trace log is in `citry.log` and the rendered HTML is in
> `result.html`.
>
> Tell me what you would look for in the log and why, whether it is there,
> and how you would fix the issue.
