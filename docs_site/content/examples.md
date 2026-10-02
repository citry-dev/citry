---
title: Examples
description: Runnable Citry components, each rendered live with its source.
---

# Examples

Each example is a small, working Citry component that solves one common
task. Find the task you have, copy the code, and adapt it.

Every example page has three tabs: **Component** shows the component,
**Page** shows a complete page that uses it, and **Live demo** shows the
result. The docs build runs and tests each example, so the code works as
shown.

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

## Try an example live { #try-an-example }

This module uses component State and a Python event handler. Select
**Try live** to edit it, run it in your browser, and use the result.

<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card with State and Events"
/>

## Start a full project { #start-from-a-complete-project }

The examples above are small so they fit on a docs page. To start an
application, copy one of the
[starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples){: target="_blank" rel="noopener"}
instead. Each has its own `pyproject.toml`, lockfile, server command, and
tests.

There are starters for standalone rendering, FastAPI, Django, Flask, bare
ASGI, and bare WSGI. Every web starter builds the same page, so you can
compare how each framework connects to Citry.

Two larger demos sit beside them. Project Board is a task board where
components, Vue, and Python handlers work together. The HTMX demo shows
an existing HTMX application that keeps HTMX for requests and page
updates, while Citry renders the HTML, CSS, and JavaScript that each
route returns.
