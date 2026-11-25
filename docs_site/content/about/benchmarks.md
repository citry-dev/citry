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

Citry makes a page with 1,400 rendered entries usable in **315 ms**
on the first load and **257 ms** on the second. Of the eleven other
frameworks, Nuxt, Rusty + HTMX + Alpine and Jinja + HTMX + Alpine are
10 to 15 ms faster on the first load, a gap within the
[noise](#how-the-numbers-were-taken). On the second load only Nuxt is
faster, by about 28 ms. Shorter bars are faster.

<c-benchmark-chart
  load="first"
  title="First load: time until usable, 1,400 entries"
/>

<c-benchmark-chart
  load="second"
  title="Second load: time until usable, 1,400 entries"
/>

### Where Citry stands

- **First load, 315 ms**: Nuxt, Rusty + HTMX + Alpine, and
  Jinja + HTMX + Alpine are 10 to 15 ms faster, and Tetra is 13 ms
  slower, all within the noise (see
  [How we measured](#how-the-numbers-were-taken)).
  Django + HTMX + Alpine and Next.js are 42 and 56 ms slower.
- **Second load, 257 ms**: Nuxt is about 28 ms faster.
  Rusty + HTMX + Alpine and Jinja + HTMX + Alpine are 39 to 43 ms
  slower. Next.js, Tetra, and Django + HTMX + Alpine are 67 to 85 ms
  slower.
- **Slower on both loads**: Reflex, django-components, django-unicorn,
  FastHTML, and ReactPy.
- **Where the time goes**: Citry spends more time on the server than
  most frameworks here, and the least time in the browser.
- **Rusty** is
  [Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
  an experimental Rust version of Django's template engine.

??? "How to read the charts"

    - Every framework serves the same project page with 1,400 entries:
      repeated blocks of content, each with its own data.
    - A bar runs from the moment the browser asks for the page until the
      page's scripts respond to input and the browser has laid the page
      out.
    - The first chart times the first request for the page. The second
      chart times the next request for the same page, after the server
      has handled it once. The browser cache is empty both times.
    - Green is the server building the page. Blue is the browser loading
      and running scripts after the page arrives. The remaining parts of
      each bar are short: the wait for the next layout takes up to about
      35 ms, and the other phases a few milliseconds each.
    - The dashed line marks Citry's total.

### How we measured { #how-the-numbers-were-taken }

Each bar is a single measurement. Jinja + HTMX + Alpine's first load
took 295, 304, 317 and 319 ms in four runs of the same setup, so treat a
gap of about 20 ms or less as noise. Each framework reports its own
server time, so the work it covers can differ a little. Citry was
measured on 2026-11-16, Rusty + HTMX + Alpine on 2026-11-25 and the
other ten frameworks on 2026-10-19, on the same Mac.

??? "Dates, versions and repeat runs"

    - **When**: Citry on 2026-11-16, Rusty + HTMX + Alpine on
      2026-11-25, the other ten frameworks on 2026-10-19.
    - **Which Citry**: Citry 1.0.0 and citry-core 2.1.0, both installed
      from PyPI. The Citry app uses Citry's Vue runtime and
      [`simple="vue"`](/performance/simple-components/). The 2026-10-19
      run measured all twelve frameworks with Citry 0.6.0 and citry-core
      1.8.0 from PyPI; the charts use that run only for the other ten.
    - **Which Rusty**: Django Rusty Templates at commit `6d10c20`,
      committed on 2026-11-24, rendering the Django + HTMX + Alpine app's
      templates unchanged; a test checks that both apps produce the same
      HTML. The 2026-10-19 run used commit `0725f87`, which rendered
      `{% empty %}` wrongly for an empty list, so its app rewrote each
      `{% empty %}` branch. The charts take Rusty's numbers from the
      2026-11-25 run.
    - **Where**: every run used the same Apple M4 Mac with Chromium 151,
      an empty browser cache, and a local connection.
    - **Same Mac, same times**: the 2026-11-16 run also measured
      Jinja + HTMX + Alpine again, to confirm the Mac gave the same times
      on both days. Its totals changed by 9 ms on the first load and
      11 ms on the second, which is within the noise, so the charts keep
      its 2026-10-19 numbers.
    - **Same Mac again**: the 2026-11-25 run also measured Citry and
      Jinja + HTMX + Alpine again. Citry's totals were 318.7 ms on the
      first load (314.6 ms kept) and 254.4 ms on the second (257.3 ms
      kept); Jinja's were 318.7 ms (304.2 ms kept) and 299.2 ms
      (299.8 ms kept). All are within the noise, so the charts keep the
      earlier numbers for both.
    - **Repeat run**: a second run on 2026-11-16 gave Citry 313 ms on the
      first load and 249 ms on the second. The charts show the earlier
      run.

## Catching errors

The earlier a mistake is reported, the less time it costs you. We
wrote the same small app in Citry and eleven other frameworks, made
the same 63 mistakes in each (a misspelled component name, a
wrong-typed input, an unclosed tag, and so on), and recorded **where
each mistake was first reported**.

Citry 1.0.0 reports **56** of the 61 mistakes that apply to it before
the app runs, in the editor or a command-line check. Next.js comes
next with 45 of 57, then Nuxt with 39 of 58 and Reflex with 38 of 54.
The Django, Rusty, django-components and Jinja apps with HTMX and
Alpine report 5 or 6. Each count leaves out the mistakes that don't apply to that
framework.

<c-error-benchmark-chart
  title="How the 63 mistakes ended in each framework"
/>

### Read the error chart { #errors-what-the-chart-shows }

| Outcome | Meaning |
|---|---|
| **Static/IDE error** (best) | The editor, a command-line check, or the production build, before the app runs. |
| **Static/IDE warning** | The same, but only a warning. Easy to miss. |
| **Runtime error** | Only once the app runs, from the server, an error response, or the browser. |
| **Runtime warning** | The running app only prints a warning. |
| **N/A or prevented** | No equivalent in this framework, or its design prevents the mistake. |
| **Missed** (worst) | Nothing reports it, whether or not the page looks different. |

The number on the right of each bar is static/IDE errors plus
warnings. The dashed line is Citry's number.

### Where Citry stands { #errors-where-citry-stands }

- **Before the app runs: 56 of 61** (47 errors, 9 warnings),
  measured on the Citry 1.0.0 release (see
  [How we measured](#errors-how-we-measured)). Two of the 63 mistakes
  don't apply to Citry.
- **Warning only: 9** of those 56, reported before the app runs, but
  easy to miss.
- **Only at runtime: 1**.
- **Missed: 4**, nothing tells you.
- **What Citry checks**: when you point `citry check` at your app
  (`citry --app app.main:citry_app check`) and set the editor
  extension's `citry.app` setting to the same app, `citry check` and
  the extension check each template against your components, their
  slots and events, your server events and forms, the CSS variables
  the server sets, and the pages and files your app serves. They also
  run Vue's compiler and HTML checks over every template.

Tetra, Reflex and the other less familiar frameworks are described
under [Error benchmark apps](#frameworks).

??? "Every framework's count before the app runs"

    | Framework | Caught before the app runs |
    |---|---|
    | Citry | 56 of 61 |
    | Next.js | 45 of 57 |
    | Nuxt | 39 of 58 |
    | Reflex | 38 of 54 |
    | ReactPy | 24 of 56 |
    | FastHTML | 20 of 48 |
    | django-unicorn | 12 of 55 |
    | Tetra | 9 of 57 |
    | Django + HTMX + Alpine | 6 of 52 |
    | Rusty + HTMX + Alpine | 6 of 50 |
    | django-components + HTMX + Alpine | 6 of 54 |
    | Jinja + HTMX + Alpine | 5 of 51 |

??? "The 9 mistakes Citry reports only as warnings"

    - a misspelled CSS class: the warning suggests the class the
      component's CSS styles
    - a component reads a value the page shares with `<c-provide>`
      under a misspelled key, such as `self.inject("bord")` where the
      page provides `board`: the warning says the page would fail to
      render
    - a listener with a misspelled event name: a component event such
      as `@hdie`, or a browser event such as `@clik`
    - a CSS variable whose name differs from the one the server sets
    - a link to a page that doesn't exist, or an image with a
      misspelled path: if you ship it, the browser gets a 404
    - an image without alt text
    - the server passes browser code a value it can't receive, such as
      a path object. The warning points at the `js_data()` line that
      sends the value rather than the line that creates it

??? "The mistake Citry reports only at runtime"

    A link that passes a word, such as `/projects/alpha`, where the
    route takes a number: FastAPI answers with a 422 validation error.
    The check knows which pages the app serves, but not the type of a
    page's parameters.

??? "The 4 mistakes Citry misses"

    - the child's event sends a number where the parent expects text:
      clicking the child's button changes nothing
    - the parent's handler takes more arguments than the child's event
      sends: the extra argument is `undefined`
    - the server and browser render different content in a part that
      passes values to a child component: the page shows the browser's
      version with no error. Citry's development mode can warn about this
      in the browser console, but the benchmark runs in the default
      production mode.
    - a secret sent to the browser through `js_data()`: the page looks
      right, but the secret is in what the browser receives. Citry
      refuses a value wrapped in [`Secret`](/advanced/secrets/), but
      the benchmark's secret is a plain string, which Citry can't tell
      from any other text. No framework here reports this one, and in
      Next.js and Nuxt even reading a server-only value in browser code
      puts it in the page before an error appears.

??? "Why Next.js, Nuxt and Reflex come next"

    - **Next.js and Nuxt**: TypeScript checks Next.js's HTML elements,
      attribute names and values, and event names. Its server actions
      take typed arguments, so a wrong or missing field in the data a
      button sends is caught too. Nuxt's template check, with its
      `strictTemplates` setting on, reports unknown components,
      elements, attributes, directives and component events. Both
      linters report a missing list key, and Next.js's also warns about
      accessibility mistakes such as a misspelled ARIA attribute.
    - **Reflex**, close behind Nuxt: its components are typed Python
      functions and its state fields have types, so Pylance checks
      component inputs, reads of state fields and event arguments, and
      `reflex compile` checks prop values, event names and loops before
      the app runs.

### How we measured { #errors-how-we-measured }

Citry was measured on 2026-11-16 and the other eleven frameworks on
2026-10-21. Every framework's versions are pinned in its app's
lockfile. Each app was checked with editor and command-line tools,
then run in Chromium through the same clicks.

??? "Dates and versions"

    - **When**: Citry on 2026-11-16, the other eleven frameworks on
      2026-10-21.
    - **Which Citry**: Citry 1.0.0, citry-lsp 1.0.0 (the editor
      extension's language server) and citry-core 2.1.0, all installed
      from PyPI. The 2026-10-21 run measured all twelve frameworks,
      with Citry built from the repository before the 0.7.0 release;
      the chart uses that run only for the other eleven.
    - **The other eleven**: their cases and tools have not changed
      since the 2026-10-21 run, apart from a newer certificate bundle
      (certifi) in the ReactPy and Reflex apps, so the chart keeps
      their results.

??? "The tools run for each framework"

    - **Citry**: a FastAPI app that adds Citry's routes with
      `citry.contrib.fastapi.mount()`, as Citry's FastAPI starter does.
      The editor extension's language server (measured with
      `citry check --types`) and `citry check` check it.
    - **Every Python stack** (Citry, Django, Rusty, Jinja, Tetra,
      django-unicorn, django-components, FastHTML, ReactPy, Reflex):
      Pylance with type checking on (measured with pyright in standard
      mode), and ruff with its default rules.
    - **Django, Rusty, Jinja, Tetra, django-unicorn and
      django-components**: djLint with the Django or Jinja profile,
      `manage.py check` for every app except Jinja's, and VS Code's
      JavaScript syntax check for the script files in every app except
      Jinja's and Tetra's. The Tetra app writes its components'
      templates and scripts inside Python classes, as Tetra's tutorial
      does, where djLint and the JavaScript check don't look; its build
      command, `manage.py tetrabuild`, reports a script's syntax error
      but still succeeds, so that counts as a warning.
    - **Reflex**: `reflex compile --dry`, which builds every page
      without starting the app.
    - **Next.js and Nuxt**: the editor's TypeScript checks (tsc for
      Next.js; vue-tsc and the Vue compiler's errors for Nuxt), ESLint,
      and the production build.
    - **The running app**: each framework's server, started as its docs
      say, driven in Chromium through the same clicks. Server errors,
      error responses, and browser errors and warnings are recorded.
    - **Setup**: the project layout from each framework's docs or
      starter, with default settings unless the
      [benchmark notes](https://github.com/citry-dev/citry/tree/main/benchmarks/errors)
      say otherwise.

??? "Stricter settings turned on"

    When a framework has a setting that turns on a stricter check, and
    other frameworks here have the same kind of check, the benchmark
    turns it on in that framework's app, so the frameworks are compared
    like for like:

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

### Every mistake

Each cell is a short code for where the mistake was first reported.
Cells in the five outcomes are tinted with their chart color. On a
computer, hover over a cell to see what the tools printed, or why the
mistake doesn't apply.

<c-error-benchmark-table />

### Error benchmark apps { #frameworks }

| Framework | Description |
|---|---|
| Rusty | The Django app with its templates rendered by [Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates), an experimental Rust version of Django's template engine. |
| django-components | The Django app with its page, cards, counter and status line rewritten as components of [django-components](https://github.com/django-components/django-components), the Django library Citry grew out of. |
| ReactPy | [ReactPy](https://github.com/reactive-python/reactpy) lets you write React-style components in Python: the server runs them and sends the browser the page to show. |
| django-unicorn | The Django app with its cards, counter, details and search form rewritten as components of [django-unicorn](https://www.django-unicorn.com/). Each click goes to the server, which sends back the component's new HTML. |
| Tetra | The Django app with its interactive parts rewritten as components of [Tetra](https://www.tetraframework.com/): the server renders each component, and the component's Alpine code in the browser calls its Python methods on the server. |
| Reflex | [Reflex](https://reflex.dev/) compiles components written in Python into a React app, which sends each click to a Python backend. |

## Related pages

- [Performance overview](/performance/) compares the ways to make
  rendering faster.
- [Simple components](/performance/simple-components/) explains how to
  render repeated components with less overhead.
- The [error benchmark source](https://github.com/citry-dev/citry/tree/main/benchmarks/errors)
  has every mistake, every framework's app, and the notes on how each
  tool was set up.
