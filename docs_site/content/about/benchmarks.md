---
title: Benchmarks
description: How fast Citry and eleven other frameworks make a 1,400-entry page usable, and how early Citry and five others report the same 44 developer mistakes.
---

# Benchmarks

- [Performance](#performance): how long a page with 1,400 entries
  takes to become usable.
- [Catching errors](#catching-errors): how early each framework
  reports the same 44 developer mistakes.

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

We wrote the same small app in Citry and five other frameworks, made
the same 44 mistakes in each (a misspelled component name, a
wrong-typed input, an unclosed tag, and so on), and recorded **where
each mistake was first reported**.

<c-error-benchmark-chart
  title="How the 44 mistakes ended in each framework"
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

- **Before the app runs: 24 of 42** (23 errors, 1 warning). Two of
  the 44 mistakes don't apply to Citry. Next.js 34 of 39, Nuxt 23 of
  40, FastHTML 17 of 32, Django + HTMX + Alpine 3 of 35, Jinja + HTMX
  + Alpine 2 of 35.
- **Missed: 13**, nothing tells you:
    - a misspelled HTML element, HTML attribute name, or CSS class: the
      page looks wrong
    - the data a button sends to the server has a misspelled field, a
      field of the wrong type, or a missing field: the server rejects
      it, but the page shows no error
    - the parent listens for a misspelled event, or the child's event
      sends a number where the parent expects text: clicking the
      child's button changes nothing
    - a misspelled browser event such as `@clik`: the button does
      nothing
    - a browser-side component gets text where it declares a boolean,
      or changes an input it received instead of telling its parent:
      the status shows the wrong value, or `Close` leaves the details
      open
    - the server and browser render different content in a part that
      passes values to a child component: the page shows the browser's
      version with no error
    - a secret sent to the browser through `js_data()`: the page looks
      right, but the secret is in what the browser receives. No
      framework here reports this one, and in Next.js and Nuxt even
      reading a server-only value in browser code puts it in the page
      before an error appears.
- **Warning only: 1**, an invalid attribute value such as
  `type="sumbit"`.
- **Only at runtime: 5**:
    - a misspelled template directive: fails in the browser
    - a syntax error in a browser expression: the server fails to render
      the page
    - browser code is passed a value it can't receive, such as a path
      object: the server fails to render the page
    - a slot fill reads a misspelled field of the data the component
      hands it, or uses a number as text: the server fails to render
      the page. Unpacking the data, as in `data="{ title, count }"`,
      reports a misspelled field before the app runs
- **Needs `template_data()`**: 3 of these reports (a wrong-typed
  input in markup, a misspelled attribute on a template object, a
  wrong-typed operation in a template expression) appear only when the
  component defines it. Without it they go unreported; this is a Citry
  bug ([#202](https://github.com/citry-dev/citry/issues/202)). The
  starter's components define it; components written from
  [Getting Started](/getting-started/installation/) often don't.
- **A similar mistake can go unreported.** The misspelled template
  directive above is a Vue one, `v-iff`, which fails in the browser. A
  misspelled server-side `c-if` isn't reported at all.
- **Why Next.js leads**: TypeScript checks its HTML elements, attribute
  names and values, and event names. Its server actions take typed
  arguments, so a wrong or missing field in the data a button sends is
  caught too.

### How we measured { #errors-how-we-measured }

- **When**: 2026-10-20, Citry 0.6.0 and citry-core 1.8.0 from PyPI.
  Every framework's versions are pinned in its app's lockfile.
- **Citry**: the editor extension's language server (measured with
  `citry check --types`) and `citry check`.
- **Every Python stack** (Citry, Django, Jinja, FastHTML): Pylance
  with type checking on (measured with pyright in standard mode), and
  ruff with its default rules.
- **Django and Jinja**: djLint with the Django or Jinja profile,
  `manage.py check` for Django, and VS Code's JavaScript syntax check
  for Django's one script file.
- **Next.js and Nuxt**: the editor's TypeScript checks (tsc for
  Next.js; vue-tsc and the Vue compiler's errors for Nuxt), ESLint, and
  the production build.
- **The running app**: each framework's server, started as its docs
  say, driven in Chromium through the same clicks. Server errors, error
  responses, and browser errors and warnings are recorded.
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
