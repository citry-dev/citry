---
title: Citry documentation
url: https://citry.dev/v/0.6.0/docs/
description: "Learn to build fully typed web interfaces in Python with reusable components, server events, and Vue browser behavior."
---
# Build with Citry

Citry is a fully typed frontend framework for Python with server events and
Vue. One component holds its server-rendered HTML, browser behavior, CSS,
translations, and Python event handlers. No second frontend application or
separate build. It is inspired by Vue and Livewire.

New to Citry? [Install Citry](/v/0.6.0/getting-started/installation/), then
[build your first component](/v/0.6.0/getting-started/your-first-component/). The
first component runs with plain Python, without a web framework.

This documentation site is built with Citry too.

## Follow the tutorial


<figure class="youtube-video" data-youtube-embed-url="https://www.youtube-nocookie.com/embed/d3nPqvDdNB0" data-youtube-title="50-minute Citry and Django code-along">
  <button type="button" class="youtube-video__facade" data-youtube-load aria-label="Play 50-minute Citry and Django code-along on YouTube">
    <span class="youtube-video__play" aria-hidden="true">▶</span>
    <span>Play 50-minute Citry and Django code-along</span>
  </button>
  <figcaption class="youtube-video__caption">
    <a href="https://www.youtube.com/watch?v=d3nPqvDdNB0" target="_blank" rel="noopener">
      Watch the 50-minute Citry and Django code-along on YouTube
    </a>
  </figcaption>
</figure>


The tutorial starts with reusable HTML rendered in Python. Each step adds one
thing: browser behavior, a FastAPI server, Python event handlers, values
kept between calls, and forms. By the end, you have an admin page that
lists items and lets you edit each row.

Follow it in order, or start with the part you need:

1. **Render components from Python:**
   [install Citry](/v/0.6.0/getting-started/installation/),
   [build a component](/v/0.6.0/getting-started/your-first-component/), and
   [give it Python data](/v/0.6.0/getting-started/data-in-components/).
2. **Build a page from smaller pieces:**
   [compose components](/v/0.6.0/getting-started/build-page/) and
   [add slots for flexible content](/v/0.6.0/getting-started/add-slots/).
3. **Add behavior in the browser:**
   [use Vue](/v/0.6.0/getting-started/browser-interactivity/) and
   [connect parent and child components](/v/0.6.0/getting-started/client-props-and-handlers/).
4. **Connect the browser to Python:**
   [serve the page with FastAPI](/v/0.6.0/getting-started/fastapi/),
   [call Python from a click](/v/0.6.0/getting-started/call-python/),
   [keep values between calls](/v/0.6.0/getting-started/state/), and
   [handle forms](/v/0.6.0/getting-started/forms/).
5. **Update the page from Python:**
   [replace a component with new HTML](/v/0.6.0/getting-started/server-rendered-updates/)
   and [combine the patterns in a CRUD
   page](/getting-started/build-crud-pages/).

The server steps use FastAPI so they can show complete, runnable code.
Citry also works with Django, Flask, Starlette, and other
[ASGI and WSGI applications](/v/0.6.0/advanced/web-frameworks/).

## Try it in the browser

- [Playground](/playground/): write Python components and render them in
  the browser.
- [Examples](/v/0.6.0/examples/): copy a working recipe or run it in the browser.

## Learn in depth

- [Template syntax](/v/0.6.0/syntax/) explains how to insert Python values, set HTML
  attributes from Python, show or repeat content, use built-in tags, and add
  Vue behavior.
- [Components](/v/0.6.0/concepts/components/) explains how a component accepts
  inputs, computes the values its template uses, uses other components, and
  renders HTML.
- [Registration](/v/0.6.0/concepts/registration/) explains how Citry finds the
  Python class behind a component tag.
- [Slots](/v/0.6.0/concepts/slots/) shows how a component can accept whole pieces of
  HTML as content.
- [Vue in Citry](/v/0.6.0/vue/) shows how to give a component data and methods in
  the browser, and how parent and child components talk to each other
  there.
- [Server events](/v/0.6.0/events/) shows how a click or form submit calls Python,
  and covers values kept between calls, forms, loading and error feedback,
  and page updates.
- [Web frameworks](/v/0.6.0/advanced/web-frameworks/) shows how to mount Citry in FastAPI,
  Starlette, Django, Flask, ASGI, or WSGI applications.
- [Troubleshooting](/v/0.6.0/guides/troubleshooting/) starts from what went wrong and
  helps you find the likely cause.

When a project needs more control, read how to ship
[component JS and CSS](/v/0.6.0/advanced/js-and-css-dependencies/), return
[HTML fragments](/v/0.6.0/advanced/html-fragments/),
[make rendering faster](/v/0.6.0/performance/), including
[caching rendered output](/v/0.6.0/performance/caching/), and
[test components](/v/0.6.0/advanced/testing/).

## Use Citry UI

[Citry UI](/v/0.6.0/ui-library/) is Citry's own library of styled components. It
provides accessible buttons, fields, forms, tabs, dialogs, comboboxes, tables,
and a theme you can adapt to your application.

Install the separate package:


```console
uv add citry-ui
```


Then [register Citry UI](/v/0.6.0/ui-library/installation/) and choose a component
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


Follow the [VS Code setup guide](/v/0.6.0/ide/vscode/) to connect the extension to your
application. You can also run `citry check` from a terminal or CI, whatever
editor you use.

## Find reference and help

- [Reference](/v/0.6.0/reference/): Python, template, and browser APIs.
- [Getting help](/community/help/): ask questions or report a problem.
- [Release notes](/v/0.6.0/releases/): what changed, and migration guides.
- [Compatibility](/v/0.6.0/about/compatibility/): supported Python versions,
  operating systems, and more.
- [Security](/v/0.6.0/security/): template expressions, State, browser data,
  and what you must secure when you deploy.
- [Benchmarks](/v/0.6.0/about/benchmarks/): how fast Citry renders.

Ready to build something? [Install Citry](/v/0.6.0/getting-started/installation/) and
render your first component.