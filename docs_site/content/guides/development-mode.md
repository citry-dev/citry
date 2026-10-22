---
title: Development mode
description: Turn on development mode while you develop, so Citry warns when two elements share an id or when Vue changes the page as it starts, and reads translations straight from your .ftl files.
---

# Development mode

Some mistakes show up only on a whole page while it runs. Two components
both write `id="board"`, so a label points at the wrong element. A panel
opens the moment Vue starts, so the page jumps. Each template looks right
on its own, so the editor and `citry check` cannot see these.

Pass `mode="development"` while you develop, and Citry checks the running
page for them and warns you. It also reads translations straight from
your `.ftl` files, so you can edit them without compiling. Keep the
default, `"production"`, for deployed apps.

## Turn it on

Pick the mode where you create the [Citry][citry.Citry] instance. Reading
it from an environment variable keeps one code path for both:

```python
import os

from citry import Citry

debug = os.environ.get("DEBUG") == "1"
app = Citry(mode="development" if debug else "production")
```

Any other value raises `ValueError` when you create the instance.

## What it turns on

Development mode turns on three things:

- When you turn a page into HTML, such as with `str(page)`, Citry warns
  if two elements on it share an `id`. See
  [Fix repeated ids](#repeated-ids) below.
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

## Fix repeated ids { #repeated-ids }

When two elements on a page share an `id`, a label's `for`, a
`#fragment` link, and `getElementById` find only the first. The
[duplicate ids](/ide/template-linting/#find-duplicate-ids) rule finds a
repeat inside one template. Development mode also finds one across the
page: two components that write the same `id`, or one component rendered
twice. When Citry turns such a page into HTML (`str(page)` or
`.serialize()`), it issues a `RuntimeWarning` that names the components:

```text
RuntimeWarning: Citry found 1 id used by more than one element
on one page:
- id "board": Board (app/board.py::Board), Sidebar
  (app/sidebar.py::Sidebar)
...
```

When two different components use the same id, rename one. When one
component appears more than once, build the id from a value it receives,
so each occurrence gets its own:

```citry-html
{# Wrong: every Board on the page has id="board" #}
<section id="board">...</section>

{# Right: the caller passes a different name to each Board #}
<section c-id="'board-' + name">...</section>
```

You see the warning only on the first render that has the repeat:
Python shows the same warning once per process.

## Less common cases

Read on when the id check stays silent or warns about a page that looks
right, or when development mode refuses your translations. The browser
console check lists its own limits under
[Limits of the check](/vue/server-rendering/#first-render-check-limits).

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
