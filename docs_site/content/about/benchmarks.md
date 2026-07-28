---
title: Benchmarks
description: How citry's rendering performance compares to django-components, Django, and Jinja2, plus the benchmark chart and how to reproduce it.
---

# Benchmarks

Citry is built to render fast, and the repository ships a benchmark that keeps
that claim honest. It renders one large, realistic page and compares citry
against django-components, plain Django templates, and Jinja2.

The scenario is a full page with about 325 component instances and roughly
205 KB of HTML in a single render. In the chart below, lower bars mean faster
renders.

<c-image src="/static/img/benchmark.png" alt="Citry vs Django vs django-components rendering a large page; lower is better" width="720" />

## Versus django-components

django-components is the fair comparison, because both it and citry pay the
full cost of a component lifecycle on every render: constructing components,
resolving slots, and collecting JS and CSS dependencies. On this page citry
comes out ahead across the board.

| What is measured | Citry vs django-components |
| --- | --- |
| First render | about 1.7x faster |
| Repeat renders | about 3.4x faster |
| Startup and import | about 2x faster |

## Versus bare template engines

Plain Django and Jinja2 render no components at all, so they skip the work
citry does on every render. That head start shows up in the raw numbers, but
the gap is smaller than it sounds: citry's repeat render is only about 1.3x the
time of a bare Django template, even though Django is doing none of the
component work.

## Jinja2, the no-component baseline

Jinja2 is the fast baseline with no component model, where each citry component
becomes a precompiled macro. That makes it the quickest engine to start up and
the quickest once warm, since a warm render just runs precompiled macro code.
It pays for that on the first render, where its whole macro library compiles at
once.

## Reading these numbers

These are relative numbers from a single machine, not absolute guarantees.

- "Citry renders this page N times faster than django-components here" is a
  fair reading.
- "A render takes X milliseconds, so my page will take X" is not: a real page
  has a different mix of components, templates, and data.
- Never compare numbers across machines, runs, or build profiles.

## Reproduce it

The full methodology, the exact engine versions, and step-by-step instructions
to run the comparison yourself live in the benchmarks README:
[benchmarks/README.md](https://github.com/citry-dev/citry/blob/main/benchmarks/README.md).

One trap worth repeating from there: the Rust extension must be built in
release mode before measuring. A debug build makes citry's Rust-backed paths
many times slower and invalidates every citry number.

## Related pages

- [Performance](/advanced/performance/) covers [`Const`][citry.Const], the
  opt-in optimization that renders a template's unchanging parts once and
  reuses them across renders.
