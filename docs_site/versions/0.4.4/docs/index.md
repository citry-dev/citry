---
title: Citry documentation
url: https://citry.dev/v/0.4.4/docs/
description: "Learn to build HTML-first components in Python, add browser behavior, and call Python without maintaining a separate frontend application."
---
# Build with Citry

Welcome to Citry documentation!

Citry is the complete frontend stack for Python.
From server-rendered HTML to browser behavior and back to a Python handler, one component holds all of it. No second application, no separate build.

New to Citry? [Install Citry](/v/0.4.4/getting-started/installation/), then
[build your first component](/v/0.4.4/getting-started/your-first-component/). The
first component runs with plain Python, without setting up a web framework.

This documentation site is built with Citry too.

## Getting started

Walk through this end-to-end tutorial.
You begin with reusable server-rendered HTML, then add browser behavior,
FastAPI, Python event handlers, server-side state, forms.

By the end of the tutorial you build an entire admin page containing a list
of items and CRUD actions per row.

Follow it in order, or start with the part you need:

1. **Render components from Python:**
   [install Citry](/v/0.4.4/getting-started/installation/),
   [build a component](/v/0.4.4/getting-started/your-first-component/), and
   [give it Python data](/v/0.4.4/getting-started/data-in-components/).
2. **Build a page from smaller pieces:**
   [compose components](/v/0.4.4/getting-started/build-page/) and
   [let them accept flexible content](/v/0.4.4/getting-started/add-slots/).
3. **Add behavior in the browser:**
   [use Alpine](/v/0.4.4/getting-started/browser-interactivity/) and
   [connect parent and child components](/v/0.4.4/getting-started/client-props-and-handlers/).
4. **Connect the browser to Python:**
   [serve the page with FastAPI](/v/0.4.4/getting-started/fastapi/),
   [call Python from a click](/v/0.4.4/getting-started/call-python/),
   [keep State between calls](/v/0.4.4/getting-started/state/), and
   [handle forms](/v/0.4.4/getting-started/forms/).
5. **Update the page from Python:**
   [render into one part of the page](/v/0.4.4/getting-started/server-rendered-updates/)
   and [combine the patterns in a CRUD
   page](/getting-started/build-crud-pages/).

The server-backed steps use FastAPI so they can show complete, runnable code.
Citry also integrates with Django, Flask, Starlette, and other
[ASGI and WSGI applications](/v/0.4.4/web-frameworks/).

## Try it live

- [Playground](/playground/) - Write and render Python components in the browser.
- [Examples](/v/0.4.4/examples/) - Code-first cookbook. Copy or run in the browser.

## Citry UI

[Citry UI](/v/0.4.4/ui-library/) is Citry's first-party styled component library. It
provides accessible buttons, fields, forms, tabs, dialogs, comboboxes, tables,
and a theme you can adapt to your application.

Install the separate package:


```console
uv add citry-ui
```


Then [register Citry UI](/v/0.4.4/ui-library/installation/) and choose a component
from its catalog.

## VS Code

[Install Citry from the Visual Studio
Marketplace](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry)
to add:

- Syntax highlighting for Citry templates
- Linting and diagnostics
- Completion, hover information, and navigation
- Safe formatting for inline templates, JavaScript, and CSS

Install the Citry extension, then add the language server to the same Python
environment as the project:


```console
python -m pip install citry-lsp
```


Follow the [VS Code setup guide](/v/0.4.4/ide/vscode/) to connect the extension to your
application. You can also run `citry check` from a terminal or CI, whether or
not your editor has a dedicated Citry integration.

## Learn more

- [Template syntax](/v/0.4.4/syntax/) explains how to insert Python values, set HTML
  attributes from Python, show or repeat content, use built-in tags, and add
  Alpine behavior.
- [Components](/v/0.4.4/concepts/components/) explains how component classes accept
  inputs, prepare template data, compose other components, and render HTML.
- [Registration](/v/0.4.4/concepts/registration/) explains how a component tag finds
  its Python class.
- [Slots](/v/0.4.4/concepts/slots/) shows how a component can accept whole pieces of
  HTML as content.
- [Client interactivity](/v/0.4.4/concepts/client-interactivity/) covers component
  browser data as Alpine variables, advanced setup with `$component`,
  `$c-props`, and browser communication between parents and children.
- [Server events](/v/0.4.4/events/) covers Python handlers, State, forms, loading and
  error feedback, browser events, and page updates.
- [Web frameworks](/v/0.4.4/web-frameworks/) shows how to mount Citry in FastAPI,
  Starlette, Django, Flask, ASGI, or WSGI applications.
- [Troubleshooting](/v/0.4.4/guides/troubleshooting/) starts from what went wrong and
  helps you find the likely cause.

When a project needs more control, read how to ship
[component JavaScript and CSS](/v/0.4.4/advanced/js-and-css-dependencies/), return
[HTML fragments](/v/0.4.4/advanced/html-fragments/),
[cache rendered output](/v/0.4.4/advanced/caching/), and
[test components](/v/0.4.4/advanced/testing/).

## Useful links

- [Reference](/v/0.4.4/reference/) - Python, template, and browser APIs.
- [Getting help](/community/help/) - Ask questions or report a
  problem.
- [Release notes](/v/0.4.4/releases/) - Read what changed, migration guides.
- [Compatibility](/v/0.4.4/about/compatibility/) - supported Python versions,
  OS, and more.
- [Security](/v/0.4.4/security/) - template expressions, State, browser data,
  and deployment responsibilities.
- [Benchmarks](/v/0.4.4/about/benchmarks/)

Ready to build something? [Install Citry](/v/0.4.4/getting-started/installation/) and
render your first component.