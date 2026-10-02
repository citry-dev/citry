---
title: Benchmarks
description: How long a page with 1,400 rendered entries takes to become usable in Citry and eleven other frameworks.
---

# Benchmarks

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

## What the charts show

- Every framework serves the same project page with 1,400 entries:
  repeated blocks of content, each with its own data.
- A bar runs from the moment the browser asks for the page until the
  page's scripts respond to input and the browser has laid the page out.
- The first chart times the first request for the page. The second
  chart times the next request for the same page, after the server has
  handled it once. The browser cache is empty both times.
- Green is the server building the page. Blue is the browser loading and
  running scripts after the page arrives. The remaining parts of each bar
  are short: the wait for the next layout takes 5 to 25 ms, and the
  other phases a few milliseconds each.
- The dashed line marks Citry's total.
- "Rusty" is
  [Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
  an experimental Rust version of Django's template engine.

## Where Citry stands

- First load: Citry takes 359 ms. Nuxt is about 90 ms faster. The
  three HTMX + Alpine stacks, Tetra, and Next.js are 20 to 50 ms faster.
- Second load: Citry takes 304 ms. Nuxt is again about 90 ms faster. The
  HTMX + Alpine stacks, Tetra, and Next.js are within 25 ms of Citry, on
  either side.
- Reflex, django-components, django-unicorn, FastHTML, and ReactPy are
  slower on both loads.
- Citry spends more time on the server than most frameworks here, and
  less time in the browser than any of them except Nuxt.

## How we measured { #how-the-numbers-were-taken }

Measured on 2026-09-27 with an unreleased build of Citry, using its Vue
runtime and [`simple="vue"`](/performance/simple-components/), on an
Apple M4 Mac with Chromium 151, an empty browser cache, and a local
connection. Next.js was measured on 2026-09-28 and Reflex on
2026-09-24. Each framework reports its own server time, so the work it
covers can differ a little. Each bar is a single measurement, so treat
a gap of a few tens of milliseconds as noise.

## Related pages

- [Performance overview](/performance/) compares the ways to make
  rendering faster.
- [Simple components](/performance/simple-components/) explains how to
  render repeated components with less overhead.
