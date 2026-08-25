---
title: Examples
description: Runnable Citry components, each rendered live with its source.
---

# Examples

Each recipe is executable Citry code. The component source opens first; switch
tabs to see the complete page and its live result.

## Start from a complete project

The recipes below are optimized for the documentation renderer. For an
independently copyable application with its own `pyproject.toml`, lockfile,
server command, and tests, use the
[complete starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples){: target="_blank" rel="noopener"}.
The collection includes standalone rendering, FastAPI, Django, Flask, bare
ASGI, and bare WSGI, plus the larger Project Board and HTMX integration demos.
Every web starter shows the same Alpine and server Events behavior so the
framework wiring is easy to compare. The HTMX demo instead shows how an
existing application can keep using HTMX for requests and page updates while
Citry renders the HTML, CSS, and JavaScript returned by each route.

## Try an example

This complete module uses component State and a Python event handler. Select
**Try live** to edit it in the page, run it in your browser, and interact with
the rendered result.

<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card with State and Events"
/>

## Components

- [Card](/examples/card/) - accept an input, render content, and add CSS.
- [Slots](/examples/slots/) - offer named areas with fallback content.
- [Provide and inject](/examples/provide-inject/) - share data with a subtree.
- [Error boundary](/examples/error-fallback/) - show a safe fallback after an
  error.
- [Recursion](/examples/recursion/) - let a component render itself.

## Template syntax

- [Control flow](/examples/control-flow/) - use conditions, loops, and an empty
  state.

## Browser and server

- [Tabs](/examples/tabs/) - ship JavaScript with a component.
- [Form submission](/examples/form-submission/) - handle a form in the browser.
- [Fragments](/examples/fragments/) - load rendered HTML and its assets on
  demand.
