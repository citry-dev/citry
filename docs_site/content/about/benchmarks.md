---
title: Benchmarks
description: How fast Citry and eleven other frameworks make a 1,400-entry page usable, and how early Citry and eleven others report the same 63 developer mistakes.
---

# Benchmarks

- [Performance](#performance): how long a page with 1,400 entries
  takes to become usable.
- [Catching errors](#catching-errors): how early each framework
  reports the same 63 developer mistakes.

## Performance

These charts show how long a page with 1,400 rendered entries takes to
become usable in Citry and eleven other frameworks. Shorter bars are
faster.

<c-benchmark-chart
  load="first"
  title="First load: time until usable, 1,400 entries"
/>

<c-benchmark-chart
  load="second"
  title="Second load: time until usable, 1,400 entries"
/>

### What the charts show

- Every framework serves the same project page with 1,400 entries:
  repeated blocks of content, each with its own data.
- A bar runs from the moment the browser asks for the page until the
  page's scripts respond to input and the browser has laid the page out.
- The first chart times the first request for the page. The second
  chart times the next request for the same page, after the server has
  handled it once. The browser cache is empty both times.
- Green is the server building the page. Blue is the browser loading and
  running scripts after the page arrives. The remaining parts of each bar
  are short: the wait for the next layout takes up to about 35 ms, and
  the other phases a few milliseconds each.
- The dashed line marks Citry's total.
- "Rusty" is
  [Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
  an experimental Rust version of Django's template engine.

### Where Citry stands

- First load: Citry takes 400 ms. Nuxt, Rusty + HTMX + Alpine, and
  Jinja + HTMX + Alpine are about 100 ms faster. Django + HTMX + Alpine,
  Tetra, and Next.js are 30 to 70 ms faster.
- Second load: Citry takes 323 ms. Nuxt is about 95 ms faster. The
  HTMX + Alpine stacks, Tetra, and Next.js are within 30 ms of Citry, on
  either side.
- Reflex, django-components, django-unicorn, FastHTML, and ReactPy are
  slower on both loads.
- Citry spends more time on the server than most frameworks here, and,
  with Nuxt, the least time in the browser.

### How we measured { #how-the-numbers-were-taken }

Measured on 2026-10-19 with Citry 0.6.0 and citry-core 1.8.0 from PyPI,
using Citry's Vue runtime and
[`simple="vue"`](/performance/simple-components/), on an Apple M4 Mac
with Chromium 151, an empty browser cache, and a local connection. All
twelve frameworks were measured in the same run. Each framework reports
its own server time, so the work it covers can differ a little. Each bar
is a single measurement, so treat a gap of a few tens of milliseconds as
noise.

## Catching errors

The earlier a mistake is reported, the less time it costs you.

We wrote the same small app in Citry and eleven other frameworks, made
the same 63 mistakes in each (a misspelled component name, a
wrong-typed input, an unclosed tag, and so on), and recorded **where
each mistake was first reported**. Rusty is the Django app with its
templates rendered by
[Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
an experimental Rust version of Django's template engine.
django-components is the Django app with its page, cards, counter and
status line rewritten as components of
[django-components](https://github.com/django-components/django-components),
the Django library Citry grew out of.
[ReactPy](https://github.com/reactive-python/reactpy) lets you write
React-style components in Python: the server runs them and sends the
browser the page to show.
django-unicorn is the Django app with its cards, counter, details and
search form rewritten as components of
[django-unicorn](https://www.django-unicorn.com/). Each click goes to
the server, which sends back the component's new HTML.
Tetra is the Django app with its interactive parts rewritten as
components of [Tetra](https://www.tetraframework.com/): the server
renders each component, and the component's Alpine code in the browser
calls its Python methods on the server.
[Reflex](https://reflex.dev/) compiles components written in Python into
a React app, which sends each click to a Python backend.

<c-error-benchmark-chart
  title="How the 63 mistakes ended in each framework"
/>

### Read the error chart { #errors-what-the-chart-shows }

- **Static/IDE error** (best): the editor, a command-line check, or
  the production build, before the app runs.
- **Static/IDE warning**: the same, but only a warning. Easy to miss.
- **Runtime error**: only once the app runs, from the server, an error
  response, or the browser.
- **Runtime warning**: the running app only prints a warning.
- **N/A or prevented**: no equivalent in this framework, or its
  design prevents the mistake.
- **Missed** (worst): nothing reports it, whether or not the page
  looks different.
- **Number on the right**: static/IDE errors plus warnings.
- **Dashed line**: Citry's number.

### Where Citry stands { #errors-where-citry-stands }

- **Before the app runs: 54 of 61** (47 errors, 7 warnings),
  measured with Citry's code from after the 0.6.0 release. The 0.6.0
  release itself catches 29 of 61 (see
  [How we measured](#errors-how-we-measured)). Two of the 63 mistakes
  don't apply to Citry. Next.js 45 of 57, Nuxt 39 of
  58, Reflex 38 of 54, ReactPy 24 of 56, FastHTML 20 of 48, django-unicorn 12 of 55,
  Tetra 9 of 57, Django + HTMX + Alpine 6 of 52, Rusty + HTMX + Alpine 6 of 50,
  django-components + HTMX + Alpine 6 of 54, Jinja + HTMX + Alpine 5
  of 51.
- **What Citry checks**: when you point `citry check` at your app
  (`citry --app app.main:citry_app check`) and set the editor
  extension's `citry.app` setting to the same app, they check each
  template against your components, their slots and
  events, your server events and forms, the CSS variables the server
  sets, and the pages and files your app serves. They also run Vue's
  compiler and HTML checks over every template.
- **Warning only: 7**, reported before the app runs, but easy to miss:
    - a listener with a misspelled event name: a component event such
      as `@hdie`, or a browser event such as `@clik`
    - a CSS variable whose name differs from the one the server sets
    - a link to a page that doesn't exist, or an image with a
      misspelled path: if you ship it, the browser gets a 404
    - an image without alt text
    - the server passes browser code a value it can't receive, such as
      a path object. The warning points at the `js_data()` line that
      sends the value rather than the line that creates it
- **Only at runtime: 2**:
    - a link that passes a word, such as `/projects/alpha`, where the
      route takes a number: FastAPI answers with a 422 validation
      error. The check knows which pages the app serves, but not the
      type of a page's parameters
    - a component reads a value the page shares with `<c-provide>`
      under a misspelled key, such as `self.inject("bord")` where the
      page provides `board`: the server fails to render the page
- **Missed: 5**, nothing tells you:
    - a misspelled CSS class: the page looks wrong
    - the child's event sends a number where the parent expects text:
      clicking the child's button changes nothing
    - a handler that takes more arguments than the event sends: the
      extra argument is `undefined`
    - the server and browser render different content in a part that
      passes values to a child component: the page shows the browser's
      version with no error
    - a secret sent to the browser through `js_data()`: the page looks
      right, but the secret is in what the browser receives. No
      framework here reports this one, and in Next.js and Nuxt even
      reading a server-only value in browser code puts it in the page
      before an error appears.
- **Why Next.js and Nuxt come next**: TypeScript checks Next.js's HTML
  elements, attribute names and values, and event names. Its server
  actions take typed arguments, so a wrong or missing field in the data
  a button sends is caught too. Nuxt's template check, with its
  `strictTemplates` setting on, reports unknown components, elements, attributes,
  directives and component events. Both linters report a missing list
  key, and Next.js's also warns about accessibility mistakes such as a
  misspelled ARIA attribute.
- **Why Reflex is close behind Nuxt**: its components are typed Python functions
  and its state fields have types, so Pylance checks component inputs,
  reads of state fields and event arguments, and `reflex compile` checks
  prop values, event names and loops before the app runs.

### How we measured { #errors-how-we-measured }

- **When**: 2026-10-21. Every framework's versions are pinned in its
  app's lockfile; Citry's exception is below.
- **Which Citry**: Citry and its language server, citry-lsp, built from
  the repository at commit
  [bf935bc](https://github.com/citry-dev/citry/tree/bf935bc77fc3e868cb7c3915035c32f0ab7147ff),
  a commit made after the 0.6.0 release, with citry-core 1.8.0 from
  PyPI. The run's report names a later commit that changed only the
  benchmark, so the Citry code is the same. Citry 0.6.0, the release
  before that commit, reports 29 of the 61.
- **Citry**: a FastAPI app that adds Citry's routes with
  `citry.contrib.fastapi.mount()`, as Citry's FastAPI starter does. The
  editor extension's language server (measured with
  `citry check --types`) and `citry check` check it.
- **Every Python stack** (Citry, Django, Rusty, Jinja, Tetra,
  django-unicorn, django-components, FastHTML, ReactPy, Reflex):
  Pylance with type checking on (measured with pyright in standard mode), and
  ruff with its default rules.
- **Django, Rusty, Jinja, Tetra, django-unicorn and django-components**:
  djLint with the Django or Jinja profile, `manage.py check` for every
  app except Jinja's, and VS Code's JavaScript syntax check for the
  script files in every app except Jinja's and Tetra's. The Tetra app
  writes its components' templates and scripts inside Python classes, as
  Tetra's tutorial does, where djLint and the JavaScript check don't
  look; its build command,
  `manage.py tetrabuild`, reports a script's syntax error but still
  succeeds, so that counts as a warning.
- **Reflex**: `reflex compile --dry`, which builds every page without
  starting the app.
- **Next.js and Nuxt**: the editor's TypeScript checks (tsc for
  Next.js; vue-tsc and the Vue compiler's errors for Nuxt), ESLint, and
  the production build.
- **The running app**: each framework's server, started as its docs
  say, driven in Chromium through the same clicks. Server errors, error
  responses, and browser errors and warnings are recorded.
- **Stricter settings**: when a framework has a setting that turns on
  a stricter check, and other frameworks here have the same kind of
  check, the benchmark turns it on in that framework's app, so the
  frameworks are compared like for like:
    - **Jinja**: `StrictUndefined`, so printing a name the template
      wasn't given is an error, not empty text.
    - **django-components**: Pydantic models for component inputs with
      the djc-ext-pydantic extension, as its docs show, so a
      wrong-typed input is an error when the page renders.
    - **Nuxt**: vue-tsc's `strictTemplates`, which reports unknown
      components, elements, attributes, directives and component
      events, and `typedPages`, which checks links that name a route
      (the page links by path, so it doesn't change the link mistake).
    - **Next.js**: `typedRoutes`, which checks a link's path against
      the app's pages, and three stricter TypeScript options that Nuxt
      turns on by default; they change no result.
    - **ReactPy**: debug mode, which checks each element it sends and
      warns about a list item without a key, like the checks React
      makes in development.
    - **Tetra**: a type on every public attribute (the values it sends
      to the browser). Tetra has no setting for this; it checks a
      value's type only where the attribute declares one.
    - **Citry, Django, Rusty, FastHTML, django-unicorn and Reflex**:
      none of their settings adds a kind of check the others make, so
      they keep their defaults.
- **Setup**: the project layout from each framework's docs or starter,
  with default settings unless the
  [benchmark notes](https://github.com/citry-dev/citry/tree/main/benchmarks/errors)
  say otherwise.

### Every mistake

Each cell is a short code for where the mistake was first reported.
Cells in the five outcomes are tinted with their chart color. On a computer, hover over a cell to see
what the tools printed, or why the mistake doesn't apply.

<c-error-benchmark-table />

## Related pages

- [Performance overview](/performance/) compares the ways to make
  rendering faster.
- [Simple components](/performance/simple-components/) explains how to
  render repeated components with less overhead.
- The [error benchmark source](https://github.com/citry-dev/citry/tree/main/benchmarks/errors)
  has every mistake, every framework's app, and the notes on how each
  tool was set up.
