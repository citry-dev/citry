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
  are short: the wait for the next layout takes up to about 35 ms, and
  the other phases a few milliseconds each.
- The dashed line marks Citry's total.
- "Rusty" is
  [Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
  an experimental Rust version of Django's template engine.

## Where Citry stands

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

## How we measured { #how-the-numbers-were-taken }

Measured on 2026-10-19 with Citry 0.6.0 and citry-core 1.8.0 from PyPI,
using Citry's Vue runtime and
[`simple="vue"`](/performance/simple-components/), on an Apple M4 Mac
with Chromium 151, an empty browser cache, and a local connection. All
twelve frameworks were measured in the same run. Each framework reports
its own server time, so the work it covers can differ a little. Each bar
is a single measurement, so treat a gap of a few tens of milliseconds as
noise.

## Related pages

- [Performance overview](/performance/) compares the ways to make
  rendering faster.
- [Simple components](/performance/simple-components/) explains how to
  render repeated components with less overhead.
