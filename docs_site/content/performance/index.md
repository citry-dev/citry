---
title: Performance
description: Find out why a page renders slowly and pick the option that skips the work it repeats.
---

# Performance

A page usually renders slowly because it repeats work: it sets up
hundreds of small components, renders the same template with the same
data again and again, or loads and renders the same content on every
request. Citry has one option for each kind of repeated work.

Measure a real page first and find the work that repeats. Then pick the
option below that skips it. Most options ask you to promise something
about your code that Citry cannot fully check, so turn them on only
where the measurement shows a gain.

## Match a slow page to an option

- **A page with many small components renders slowly**, and most of them
  only turn inputs into HTML: make them
  [simple components](/performance/simple-components/).
- **The same input value reaches many renders**, such as a fixed label
  or a layout setting: mark it with [`Const`](/performance/const/).
- **One component repeats on a page with the same data**, such as a
  status icon in every table row: declare it
  [pure](/performance/pure/).
- **Every request renders the same expensive output again**, such as a
  product card that loads its data from a database:
  [cache the rendered output](/performance/caching/).
- **Several workers or hosts should share that cached output**: give
  them a shared [cache backend](/performance/cache-backends/).

## Compare what each option skips

| Option | What it skips | What you promise | How long the saving lasts |
| --- | --- | --- | --- |
| [`simple = True`](/performance/simple-components/) | Setting up a component instance for each call | The component needs no instance, hooks, or JavaScript and CSS of its own | Each call; nothing is stored |
| [`Const(value)`](/performance/const/) | Template work that uses only constant values | The marked value never changes | Across renders, for the 512 most recently used combinations on each `Citry` instance |
| [`pure = True`](/performance/pure/) | Rendering the template again for the same data; child components and slots still render | The template's output depends only on its data | One page render |
| [`Cache` or `<c-cache>`](/performance/caching/) | Data methods, the template, and child components | The cache key includes every value that changes the output | Until the entry expires, you remove it, or the backend drops it |

The first three options still load data and render child components on
every call. Cache the rendered output when that is the work you want to
skip.

## Know what each option costs

- **Simple components** have no Python instance and no lifecycle hooks.
  With `simple = True` they also have no named slots and no JavaScript,
  CSS, or translation messages of their own. `simple = "vue"` keeps its
  own JavaScript and CSS but accepts no slots, and some app-wide settings
  make it render at ordinary speed. Citry raises an error
  when a class uses a feature its mode does not support.
- **`Const`** values are never checked again. If you change a marked
  object in place after passing it, the page can show the old output.
  Marking a value that differs on almost every render, such as a user
  ID, fills the store with entries that are never reused.
- **Pure components** produce wrong output when the template changes
  something or reads values that are not in its data. The saving only
  appears when the same data repeats within one page render.
- **Cached output** can show stale or private HTML when the key leaves
  out a value that changes the result. Entries use memory in the
  backend, and inputs are still validated on every call. A component
  that receives slot content needs a custom `Cache.vary()`.
- **A shared cache backend** is one more service to run and secure.
  Citry also stores generated scripts and other values there, so size it
  for more than rendered output.

## Combine options

A component can declare both `simple = True` and `pure = True` when both
promises hold. Its `template_data()` still runs on every call.

`Const` values and pure components also speed up the first render of a
cached component or region. Once a cached entry exists, Citry reuses it
and skips everything inside, including nested caches. Give an outer
entry an expiry no longer than any content inside it can tolerate.

## Related pages

- [Benchmarks](/about/benchmarks/) compares how long a large page takes
  to become usable in Citry and other frameworks.
- [Rendering](/concepts/rendering/) explains the full render process.
