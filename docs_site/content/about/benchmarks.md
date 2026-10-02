---
title: Benchmarks
description: How long a page with 1,400 rendered outputs takes to become usable in Citry and eleven other frameworks.
---

# Benchmarks

We built the same project page in twelve frameworks and timed how long
each page takes to become usable: from the moment the browser asks for
the page until its scripts are ready to respond to the reader and the
browser has had its next chance to lay the page out. The page shows
1,400 outputs, each a repeated block of content with its own data, so
framework overhead adds up instead of hiding behind a small page.

Each bar splits that time into phases, such as the server building the
page and the browser running scripts. Shorter bars are faster. The
dashed line marks Citry's total, so a bar that ends left of it finished
sooner than Citry in this run, and one that ends right of it finished
later.

## How Citry compares in this run

Each bar is a single measurement, so read the results in broad bands
rather than as a ranking.

On the first load, Citry takes 359 ms. Nuxt finishes about 90 ms
sooner. The three Django template stacks with HTMX and Alpine, Tetra
and Next.js finish within about 50 ms of Citry, all of them sooner.
Reflex, django-components, django-unicorn, FastHTML and ReactPy take
clearly longer, from about 40 ms to more than 450 ms.

On the second load Citry takes 304 ms. Nuxt again finishes about 90 ms
sooner. The Django template stacks, Tetra and Next.js all finish within
about 25 ms of Citry, on either side. The same five frameworks again take
clearly longer.

Citry spends more time on the server than most frameworks here (161 ms
on the first load), and less time in the browser than any of them except
Nuxt. Each framework reports its own server time, so the work it covers
can differ a little between them. On these numbers, server time is where
Citry trails most of the other frameworks.

"Rusty" in the charts is
[Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
an experimental Rust implementation of Django's template engine.

## First load

<c-benchmark-chart
  load="first"
  title="First load: time until usable, 1,400 outputs"
/>

## Second load

The second load requests the page again in a fresh browser context in
the same browser, so nothing comes from the browser cache, but the
server has already rendered the page once.

<c-benchmark-chart
  load="second"
  title="Second load: time until usable, 1,400 outputs"
/>

## What the phases mean

- **Server builds the page**: the time the server reports for producing
  the page, including rendering.
- **Page download**: the time the browser spends receiving the page.
- **Before the page request** and **Other request time**: the wait
  before the browser sends the request, and the rest of the request
  time: the connection, plus any server work that the server's own
  timing does not cover. Both are usually a few milliseconds or less.
- **Browser work and later requests**: everything after the page
  arrives until its scripts are ready: loading scripts, styles and
  data, running them, and attaching to the HTML.
- **Wait for the next layout**: after the scripts are ready, the time
  until the browser's next chance to lay out the page. The totals
  include this wait.

## How the numbers were taken

Each bar is one measurement, taken on 2026-09-27 on an Apple M4 Mac
with Chromium 151, over a local connection with no compression and an
empty browser cache. Next.js was measured in a separate run early on
2026-09-28, after its first build failed the benchmark's correctness
check at 1,400 outputs. With one measurement per bar,
treat a gap of a few tens of milliseconds as noise.

Citry ran as an unreleased build from its working tree, compiled with
release optimizations, using its Vue runtime and default settings, with
[`simple="vue"`](/performance/simple-components/) on the repeated
component. The server renders the full page and Vue attaches to that
HTML in the browser. Reflex's bars come from an earlier run on
2026-09-24, because in this run Reflex failed the benchmark's
correctness check before timing. The benchmark run also measured apps
that build the page in the browser from a JSON API; they are left out
here because this page compares pages rendered on the server.

## Related pages

- [Performance overview](/performance/) compares simple rendering,
  `Const`, pure component bodies, and rendered output caching.
- [Simple components](/performance/simple-components/) explains how to
  render repeated components with less overhead.
