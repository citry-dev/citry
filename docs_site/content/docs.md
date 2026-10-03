---
title: Citry documentation
description: Learn to build fully typed web interfaces in Python with reusable components, server events, and Vue browser behavior.
---

# Build with Citry

Citry is a fully typed frontend framework for Python with server events and
Vue. One component holds its server-rendered HTML, browser behavior, CSS,
translations, and Python event handlers. No second frontend application or
separate build. It is inspired by Vue and Livewire.

New to Citry? [Install Citry](/getting-started/installation/), then
[build your first component](/getting-started/your-first-component/). The
first component runs with plain Python, without a web framework.

This documentation site is built with Citry too.

## Follow the tutorial

<c-youtube-video
  video_id="d3nPqvDdNB0"
  title="50-minute Citry and Django code-along"
/>

The tutorial starts with reusable HTML rendered in Python. Each step adds one
thing: browser behavior, a FastAPI server, Python event handlers, values
kept between calls, and forms. By the end, you have an admin page that
lists items and lets you edit each row.

Follow it in order, or start with the part you need:

1. **Render components from Python:**
   [install Citry](/getting-started/installation/),
   [build a component](/getting-started/your-first-component/), and
   [give it Python data](/getting-started/data-in-components/).
2. **Build a page from smaller pieces:**
   [compose components](/getting-started/build-page/) and
   [add slots for flexible content](/getting-started/add-slots/).
3. **Add behavior in the browser:**
   [use Vue](/getting-started/browser-interactivity/) and
   [connect parent and child components](/getting-started/client-props-and-handlers/).
4. **Connect the browser to Python:**
   [serve the page with FastAPI](/getting-started/fastapi/),
   [call Python from a click](/getting-started/call-python/),
   [keep values between calls](/getting-started/state/), and
   [handle forms](/getting-started/forms/).
5. **Update the page from Python:**
   [replace a component with new HTML](/getting-started/server-rendered-updates/)
   and [combine the patterns in a CRUD
   page](/getting-started/build-crud-pages/).

The server steps use FastAPI so they can show complete, runnable code.
Citry also works with Django, Flask, Starlette, and other
[ASGI and WSGI applications](/web-frameworks/).

## Try it in the browser

- [Playground](/playground/): write Python components and render them in
  the browser.
- [Examples](/examples/): copy a working recipe or run it in the browser.

## Learn in depth

- [Template syntax](/syntax/) explains how to insert Python values, set HTML
  attributes from Python, show or repeat content, use built-in tags, and add
  Vue behavior.
- [Components](/concepts/components/) explains how a component accepts
  inputs, computes the values its template uses, uses other components, and
  renders HTML.
- [Registration](/concepts/registration/) explains how Citry finds the
  Python class behind a component tag.
- [Slots](/concepts/slots/) shows how a component can accept whole pieces of
  HTML as content.
- [Client interactivity](/concepts/client-interactivity/) shows how to give
  a component data and methods in the browser, and how parent and child
  components talk to each other there.
- [Server events](/events/) shows how a click or form submit calls Python,
  and covers values kept between calls, forms, loading and error feedback,
  and page updates.
- [Web frameworks](/web-frameworks/) shows how to mount Citry in FastAPI,
  Starlette, Django, Flask, ASGI, or WSGI applications.
- [Troubleshooting](/guides/troubleshooting/) starts from what went wrong and
  helps you find the likely cause.

When a project needs more control, read how to ship
[component JS and CSS](/advanced/js-and-css-dependencies/), return
[HTML fragments](/advanced/html-fragments/),
[make rendering faster](/performance/), including
[caching rendered output](/performance/caching/), and
[test components](/advanced/testing/).

## Use Citry UI

[Citry UI](/ui-library/) is Citry's own library of styled components. It
provides accessible buttons, fields, forms, tabs, dialogs, comboboxes, tables,
and a theme you can adapt to your application.

Install the separate package:

```console
uv add citry-ui
```

Then [register Citry UI](/ui-library/installation/) and choose a component
from its catalog.

## Set up VS Code

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

Follow the [VS Code setup guide](/ide/vscode/) to connect the extension to your
application. You can also run `citry check` from a terminal or CI, whatever
editor you use.

## Find reference and help

- [Reference](/reference/): Python, template, and browser APIs.
- [Getting help](/community/help/): ask questions or report a problem.
- [Release notes](/releases/): what changed, and migration guides.
- [Compatibility](/about/compatibility/): supported Python versions,
  operating systems, and more.
- [Security](/security/): template expressions, State, browser data,
  and what you must secure when you deploy.
- [Benchmarks](/about/benchmarks/): how fast Citry renders.

Ready to build something? [Install Citry](/getting-started/installation/) and
render your first component.
