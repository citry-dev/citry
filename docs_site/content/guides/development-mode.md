---
title: Development mode
description: Turn on development mode while you work on your app, so Citry warns about mistakes on the running page and reads translations straight from your .ftl files.
---

# Development mode

Development mode makes Citry favor fast feedback over render speed
while you work on your app. It warns about mistakes that only show up
on a whole running page, such as two components that both write
`id="board"`, or a part of the page that changes when Vue starts. It
also reads translations straight from your `.ftl` files.

Pass `mode="development"` on your own machine, and keep the default,
`"production"`, for deployed apps.

## Turn on development mode

Pick the mode where you create the [Citry][citry.Citry] instance. Reading
it from an environment variable keeps one code path for both:

```python
import os

from citry import Citry

debug = os.environ.get("DEBUG") == "1"
app = Citry(mode="development" if debug else "production")
```

Any other value raises `ValueError` when you create the instance.

## What development mode changes

Development mode changes three things:

- When you turn a page into HTML, such as with `str(page)`, Citry warns
  if two elements on it share an `id`. See
  [Fix repeated ids](#repeated-ids).
- The browser console warns when Vue's first render of a part it builds
  in the browser differs from the HTML the server sent. See
  [First render warnings](/vue/server-rendering/#first-render-warnings).
- Citry reads translations straight from your `.ftl` files, so you can
  edit them without compiling. See
  [Production and deployment](/i18n/production/).

The checks cost time on every render and add a script to some pages, so
use production mode for deployed apps; a production page does not load
that script.

To pick up edited template, JS, or CSS files without a restart, turn on
[hot reload](/guides/hot-reload/). It is separate from the mode and is
for development only.

## Less common cases

Read on to fix a repeated id, when the id check stays silent or warns
about a page that looks right, or when development mode refuses your
translations. The browser console check lists its own limits under
[Limits of the check](/vue/server-rendering/#first-render-check-limits).

### Fix repeated ids { #repeated-ids }

The warning names the components that write each repeated id:

```text
RuntimeWarning: Citry found 1 id used by more than one element
on one page:
- id "board": Board (app/board.py::Board), Sidebar
  (app/sidebar.py::Sidebar)
...
```

When two different components write the same id, rename one. When one
component appears more than once, build the id from a value it
receives, such as `c-id="'board-' + name"`, so each copy gets its own.

Python shows the same warning once per process, so you see it only on
the first render that has the repeat. The
[duplicate ids](/ide/template-linting/#find-duplicate-ids) rule in the
editor already finds a repeat inside one template.

### Ids the check misses { #ids-the-check-misses }

The check counts the ids in the HTML the server writes, so it does not
see:

- an id on or inside an element with `v-if`, `v-else-if`, `v-else`, or
  `v-for`, or inside a `<template>` or `<noscript>`, because the browser
  decides whether those exist;
- an id that a Vue binding such as `:id`, or other browser code, sets;
- a repeat between an HTML fragment, or a part of the page that a server
  event renders again, and the page it lands in.

### Unexpected warnings { #unexpected-warnings }

A component in both branches of a `v-if`, written on its own tag, such
as `<c-Panel v-if="wide" />` and `<c-Panel v-else />`, warns even though
only one branch shows. Put the condition on an element around each call
instead.

A [simple component](/performance/simple-components/) (`simple = True`)
writes its HTML into its caller's HTML, so the warning names the caller.

### Translation file errors { #translation-file-errors }

If a [catalog package](/i18n/catalogs/) also holds compiled files from
`citry ext run i18n compile`, development mode still checks that they
match your `.ftl` files. When they do not, creating the `Citry` instance
raises `ValueError`. After you edit translations, delete the compiled
files or compile again.

Production mode needs those compiled files: when a package has none, or
they do not match each other and the package's `citry-i18n.toml`,
creating the `Citry` instance raises `ValueError`.
