---
title: Error prevention
description: How early Citry and five other frameworks report the same 24 developer mistakes, from the editor to the running page.
---

# Error prevention

This page shows how early each framework tells you about a mistake. We
wrote the same small app in Citry and five other frameworks, then made
the same 24 developer mistakes in each one: a misspelled component
name, a wrong-typed input, an unclosed tag, and so on. For every
mistake we recorded the first place that reported it: the editor, a
command-line check, the production build, the running app, or nowhere.
The earlier a mistake is reported, the less time it costs you.

<c-error-benchmark-chart
  title="How the 24 mistakes ended in each framework"
/>

## What the chart shows

- Each bar is one framework. Its full length stands for all 24
  mistakes, and each colored part shows how many ended one way.
- Dark green, "Error before running": the editor, a command-line check,
  or the production build reported an error before the app ran. This
  is the best outcome.
- Light green, "Warning before running": a tool reported the mistake
  before the app ran, but only as a warning, which is easy to miss.
- Orange, "Error at runtime": nothing reported the mistake until the
  app ran, and then the server, an error response, or the browser
  reported an error.
- Light orange, "Warning at runtime": the running app only printed a
  warning.
- Red, "Missed, page wrong": nothing reported the mistake, and the page
  looks or behaves wrongly.
- Dark gray, "Missed, no visible change": nothing reported the mistake,
  and the page looks the same, so the mistake stays hidden until the
  case it affects comes up.
- Light gray, "Does not apply": the mistake cannot be made in this
  framework, either because it has no equivalent or because the
  framework's design prevents it.
- The number at the end of each bar counts the mistakes reported as an
  error before running.

## Where Citry stands

- Citry reports 16 of the 24 mistakes as an error before the app runs,
  and one more as a warning. Next.js reports 18, Nuxt 13, FastHTML 11,
  Django + HTMX + Alpine 3, and Jinja + HTMX + Alpine 2.
- Citry's misses are in plain HTML and CSS, plus one request field. A
  misspelled HTML element, HTML attribute name or CSS class, and a
  misspelled field in the data a button sends to the server, each leave
  the page wrong with no message. An invalid attribute value, such as
  `type="sumbit"`, is only a warning.
- Three mistakes are reported only once the app runs. A misspelled
  template directive and server and browser rendering different content
  fail in the browser; a syntax error in a browser expression makes the
  server fail to render the page.
- Three of Citry's catches (a wrong-typed input written in markup, a
  misspelled attribute on a template object, and a wrong-typed operation
  in a template expression) need the component to define
  `template_data()`. The components in Citry's starter do. Components
  written from the Getting Started guide often do not, and then these
  three mistakes are not reported. This is a Citry bug
  ([#202](https://github.com/citry-dev/citry/issues/202)).
- Some cases are written where a Citry rule checks, and a close variant
  goes unreported: a misspelled event name in the parent's listener
  (the child's misspelled emit is caught), a misspelled server-side
  `c-if` (the case misspells a Vue directive), and a server-only value
  sent to the browser through `js_data()` (the case reads it in browser
  code, which is caught). In the Next.js and Nuxt cases, the secret
  does reach the page.
- Next.js catches more than Citry because TypeScript checks its HTML
  elements, attribute names and attribute values, and its server
  actions take typed arguments.

## How we measured

Measured on 2026-10-20 with Citry 0.6.0 and citry-core 1.8.0 from PyPI.
Every framework's versions are pinned in its app's lockfile in the
benchmark source.

- Citry: the Citry editor extension's language server, measured with
  `citry check --types`, and the `citry check` command.
- Every Python stack (Citry, Django, Jinja, and FastHTML): Pylance with
  type checking turned on, measured with pyright in standard mode, and
  ruff with its default rules.
- Django and Jinja: djLint with its Django or Jinja profile for the
  templates, `manage.py check` for Django, and VS Code's JavaScript
  syntax check for Django's one script file.
- Next.js and Nuxt: the TypeScript checks the editor runs (tsc for
  Next.js, vue-tsc and the Vue compiler's own errors for Nuxt), ESLint,
  and each framework's production build.
- The running app: each framework's server, started the way its docs
  start it, driven in Chromium through the same clicks, with server
  errors, error responses, and browser errors and warnings recorded.
- Each framework uses the project layout its own docs or starter
  template recommend, with default settings unless the benchmark notes
  say otherwise.

## Every mistake

Each cell shows, as a short code, where the mistake was first
reported. A scored cell is tinted with its chart color. On a computer, hover
over a cell to see what the tools printed, or why the mistake does not
apply.

<c-error-benchmark-table />

## Related pages

- [Benchmarks](/about/benchmarks/) compares how long a page takes to
  become usable in Citry and eleven other frameworks.
- The [benchmark source](https://github.com/citry-dev/citry/tree/main/benchmarks/errors)
  has every mistake, every framework's app, and the notes on how each
  tool was set up.
