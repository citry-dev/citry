---
title: Troubleshooting
description: Debug citry: read the component path in render errors, turn on trace logging, and inspect a component's rendered HTML.
---

# Troubleshooting

As a project grows, a bug can hide deep inside a tree of components. Citry gives
you four things to work with when that happens: render errors that name the
failing component, verbose logs of the render walk, visual component and slot
boundaries, and a way to capture the exact HTML a component produced.

## Debug the editor integration

The VS Code status bar shows the active Citry analysis level for each workspace
folder. `registry` means the server loaded the configured Citry instance or
component library and can check component names, inputs, and slots. A selected
component library has its library-only scope named in status. `syntax only`
means parser diagnostics still run, but registry-backed checks and component
intelligence are disabled.

If the status is `syntax only` unexpectedly:

1. Install `citry-lsp` in the Python environment selected for the workspace:

   ```console
   python -m pip install citry-lsp
   ```

2. Set `citry.app` to the same `module:attribute` Citry instance the application
   starts, for example `myproject.app:engine`. A component-library author can
   select its manifest, such as `acme_ui:__citry_library__`; status then reports
   that host-app components, configuration, and host-provided extensions are
   outside that registry.
3. Run **Citry: Show Language Server Status**. Check the reported interpreter,
   app spec, Citry version, protocol version, and discovery message.
4. If the interpreter is wrong, select the intended Python environment or set
   `citry.python` to its executable. Then run **Citry: Restart Language Server**.

Registry discovery has a 15-second startup limit and runs in a child process. An
import exception, `SystemExit`, process crash, startup timeout, unsupported
Citry version, or catalog mismatch therefore degrades that workspace to syntax
only without breaking the editor's language-server connection. Fix the first
reported discovery error, then restart the server. Output printed by project
imports is captured and included in status instead of entering the LSP stream.

Ordinary HTML files are not claimed globally because Citry permits any
`template_file` name. Registry mode analyzes files resolved from the component
catalog. For an unassociated standalone template, select the **Citry Template**
language mode or add a project-specific `files.associations` rule.

## Read browser diagnostics first

Client failures start with a `[Citry]` message in the browser console. Use the
first error in the chain:

| Symptom | Likely cause | Fix |
|---|---|---|
| A second or foreign Alpine warning | The page or a dependency loads Alpine separately | Remove that script and use [Citry's plugin hook](/advanced/alpine-runtime/#add-an-alpine-plugin) |
| Props initialization was skipped | `$c-props` is missing, invalid, asynchronous, or has the wrong declared type | Return a synchronous plain object and follow the named prop diagnostic |
| Missing or changed ownership marker | A minifier, CDN, sanitizer, or DOM update changed ownership comments | Preserve all [client-active HTML](/advanced/alpine-runtime/#preserve-client-active-html) |
| Fragment graph or asset adoption failed | Citry routes are not mounted, or one manifest or asset is incomplete | Mount the integration and inspect the first network or graph error |
| Native `x-for`, `x-if`, or `x-teleport` clone was rejected | The template tries to clone a server-rendered active Citry component | Render component lists on the server or keep the structural directive inside the component |

Citry fails a damaged graph before callbacks can observe partial ownership. Do
not suppress the diagnostic and continue with only the visible HTML.

## Read the component path in errors

When a component fails to render, the bare exception (say `KeyError: 'name'`)
does not say which component was rendering. Citry rewrites the message to name
the path from the root component down to the one that failed.

Take a `Page` that renders a `Card`, which renders an `Avatar` that expects a
`name` it never receives:

```citry
from citry import Component

class Avatar(Component):
    template = """
      <img c-alt="name" />
    """

    def template_data(self, kwargs, slots):
        return {"name": kwargs["name"]}

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

str(Page())
```

Rendering `Page` raises, and the message names the chain that led to the
failure:

```text
An error occurred while rendering components Page > Card > Avatar:
name
```

The path reads root first and failing component last, so `Avatar` is where to
look. It travels with the exception itself, so it survives being caught and
re-raised: a `try`/`except` in your own code still sees the annotated message.

When the failure happens inside slot content, the path also carries a frame for
the slot that was being filled, for example
`Page > Layout > Layout(slot:body)`.

## Find the failing line in a template

The path above points at Python code (`Avatar.template_data`). When the error is
in a template expression instead, citry adds an underlined snippet of the
template, so you see the exact expression and the lines around it.

Here `Profile` reads `user_name` in its template but never defines it:

```citry
from citry import Component

class Profile(Component):
    template = """
      <p>Welcome, {{ user_name }}</p>
    """
```

Rendering it points straight at the offending expression:

```text
An error occurred while rendering components Profile:
Error in variable: KeyError: 'user_name'

     1 | user_name
         ^^^^^^^^^

In template of 'Profile' (/path/to/profile.py::Profile):

     2 |       <p>Welcome, {{ user_name }}</p>
                           ^^^^^^^^^^^^^^^
```

The header names the component whose template failed and the file it lives in,
and the `^^^` underline marks the expression that raised.

## Turn on debug and trace logging

Everything citry logs goes through the standard library logger named `citry`, so
you configure it the usual way with Python's `logging` module. Citry uses two
levels:

- `DEBUG`: loading a component's associated HTML, JS, and CSS files, and
  autodiscovery of component modules.
- `TRACE`: a detailed view of the render walk. Logs when components, slots, and
  nodes start and finish rendering, and which fills a slot received.

`TRACE` is a level citry adds below `DEBUG`, with the numeric value `5`. To see
trace logs, set the level to `5` (there is no named constant for it):

```python
import logging

logging.basicConfig(level=5, format="%(levelname)s %(name)s %(message)s")
```

Rendering a small page (a `HomePage` that renders a `Hello` greeting) then logs
each step of the walk:

```text
TRACE citry RENDER COMPONENT: 'HomePage' ID cz9kert00 PATH: HomePage
TRACE citry RENDER NODE ComponentNode @22:44
TRACE citry RENDER COMPONENT: 'Hello' ID cz9keru00 PATH: HomePage > Hello
```

Each line shows the component (or node) and its `PATH` in the tree. The `ID` and
the `@start:end` span identify one instance and its place in the template source.

`basicConfig` turns on logging for the whole program. To keep the rest of your
app quiet and raise only citry's level, target the named logger:

```python
import logging

logging.getLogger("citry").setLevel(5)
```

Trace logging is nearly free when it is off (the render path only checks whether
the level is enabled), but with it on a render is roughly twice as slow, plus the
cost of whatever handler writes each line. Use it while debugging, not in
production.

## Visualize component and slot boundaries

Install the opt-in [Debug][citry.ext.debug.Debug] extension when you need to see which component or slot produced each region of a page. Component boundaries are blue and carry the component class and render ID. Slot boundaries are red and carry the receiving component class and slot name.

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

The engine defaults apply to every component. Override either switch on one component with its nested config:

```citry
class Layout(Component):
    citry = app
    template = """
      <main><c-slot /></main>
    """

    class Debug:
        highlight_components = False
        highlight_slots = True
```

Debug keeps Citry's `data-cid-*`, key, event, and CSS-variable markers on the elements authored by the component. Full-document component or slot boundaries and transparent structural components are skipped automatically.

The boundaries themselves are real `<div>` elements. They can change flex or grid children, direct-child selectors, exact element identity, and restricted table or select content. Use Debug for development inspection, not in production or for layout-sensitive behavioral tests. Place it after an output-rewriting extension if you want to inspect that extension's final result.

## Inspect the rendered output

Rendering a component gives you back a plain HTML string, so you can write it to
a file and read exactly what came out. Calling a component builds a
[CitryElement][citry.CitryElement]; `str()` on it runs the full render and
returns the HTML:

```python
html = str(HomePage())
with open("result.html", "w", encoding="utf-8") as f:
    f.write(html)
```

If you need to serialize with specific options, render first and call
`serialize()` on the result: `HomePage().render().serialize()` returns the same
string and lets you choose how JavaScript and CSS are placed (see
[Asset placement](/advanced/asset-placement/)).

## Debug with an AI coding agent

The features above make citry work well with AI coding agents. To debug a render
with one, give it three things: the component source (already in your repo), the
HTML that was produced, and a log of how it was produced.

Capture the rendered output to a file as shown above, and send trace logs to
their own file with a file handler:

```python
import logging

handler = logging.FileHandler("citry.log", mode="w")
citry_logger = logging.getLogger("citry")
citry_logger.setLevel(5)
citry_logger.addHandler(handler)
```

Then prompt the agent with both files attached:

> I have a citry project. Citry is component-based web rendering for Python, in
> the style of Vue or React.
>
> I am rendering the `HomePage` component, but the output is missing the
> greeting. The trace log is in `citry.log` and the rendered HTML is in
> `result.html`.
>
> Tell me what you would look for in the log and why, whether it is there, and
> how you would fix the issue.
