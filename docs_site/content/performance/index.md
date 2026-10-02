---
title: Performance
description: Find the rendering optimization that fits your slow page, what each one asks your code to promise, and how long its savings last.
---

# Performance

Each optimization in this section skips one kind of repeated rendering
work. You turn it on, and most of them ask your code for a promise that
Citry cannot fully check. Measure a real page first, find the work that
repeats, then use the optimization that skips that work.

## Match a slow page to an optimization

- **A page with many small components renders slowly**, and most of them
  only turn inputs into HTML: use
  [simple components](/performance/simple-components/).
- **The same input value reaches many renders**, such as a fixed label or
  a layout setting: mark it with
  [`Const`](/performance/const/).
- **One component repeats on a page with the same data**, such as a status
  icon in every table row: declare it
  [pure](/performance/pure/).
- **Every request renders the same expensive output again**, such as a
  product card that loads its data from a database: cache the
  [rendered output](/performance/caching/).
- **Several workers or hosts should share that cached output**: choose a
  shared [cache backend](/performance/cache-backends/) and give every
  worker the same namespace and generation.

## Compare what each optimization skips

In the table, one root render is one top-level render call, such as
rendering one page.

| Choice | What it skips | What your code promises | How long the saving lasts |
| --- | --- | --- | --- |
| [`simple = True`](/performance/simple-components/) | Setting up an independent component instance | The component needs no instance, hooks, or JS/CSS of its own | Each call; nothing is stored |
| [`Const(value)`](/performance/const/) | Template work that depends only on that value | The marked value will not change | Across renders, for the 512 most recently used combinations of component and `Const` values on each `Citry` instance |
| [`pure = True`](/performance/pure/) | Rendering the body again for equal template data, apart from child components and slots | The template is deterministic and side-effect-free | One root render |
| [`Cache` or `<c-cache>`](/performance/caching/) | Data methods such as `template_data()`, template work, and child components on a hit | The cache key includes every value that changes the output | Until the entry expires, you invalidate it, or the backend drops it |

Use `Const(...)` when only selected values are stable. Use `pure = True` only
when the complete body keeps the stronger promise. Cache rendered output when
the work you want to skip includes data loading or child components, which
the first three options still run on every call.

## Know what each optimization costs

- **Simple components** give up their own Python instance and lifecycle
  hooks. With `simple = True` they also give up named slots and their own
  JavaScript, CSS, and translation messages. `simple = "vue"` keeps its own
  JavaScript and CSS but accepts no slots, and it renders at ordinary speed
  while app-wide translation settings or some extensions need a component
  instance. Citry raises an error when a class uses a feature its mode does
  not support.
- **`Const`** values are never checked again. If you change a marked object
  in place after passing it, the page can show the old output. Marking a
  value that differs on almost every render, such as a user ID, stores an
  entry that is never reused and pushes out useful ones.
- **Pure components** produce wrong output when the template has side effects
  or reads values that are not in its template data. The saving only appears
  when equal data repeats within the same root render.
- **Rendered output caching** can show stale or private output when the cache
  key leaves out a value that changes the result. Entries use memory in the
  cache backend, and inputs are still validated on every call, even on a hit.
  A component that receives slot content needs a custom `Cache.vary()`.
- **A shared cache backend** adds a service to run and secure. Citry also
  stores generated scripts and other values there, so size it for more than
  rendered output.

## Combine optimizations

A component can declare both `simple = True` and `pure = True` when both
promises hold. Its `template_data()` still runs on every call, and a simple
component that shows supplied content with `<c-slot />` renders its body
again on every call, even with `pure = True`. `Const` values and pure
components still apply while Citry renders a cached region for the first
time. When an outer cache entry is used, Citry skips the whole region,
including the cache lookups nested inside it, so give the outer entry an
expiry no longer than any content inside it can tolerate.

## Related pages

- [Benchmarks](/about/benchmarks/) shows render times for a large page that
  uses `simple` and `pure`.
- [Rendering](/concepts/rendering/) explains the full render process.
