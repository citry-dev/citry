---
title: Benchmarks
url: https://citry.dev/v/0.4.3/about/benchmarks/
description: "How citry's rendering performance compares to django-components, Django, and Jinja2, plus the benchmark chart and how to reproduce it."
---
# Benchmarks

Citry is built to render fast, and the repository ships a benchmark that keeps
that claim honest. It renders one large, realistic page and compares citry
against django-components, plain Django templates, and Jinja2.

The scenario is a full project-management page. The current Citry render has
about 350 component markers and produces 986,021 bytes, including its client
dependency manager, Events/Alpine runtime, and ownership graph. In the chart
below, lower bars mean faster results.

<img src="/static/img/benchmark.png" alt="Citry, Django, django-components, and Jinja2 rendering a large page; lower is better" width="720" />

## Versus django-components

django-components is the closest comparison, because both it and Citry pay the
full cost of a component lifecycle on every render: constructing components,
resolving slots, and collecting JS and CSS dependencies. Citry now also builds
its complete ownership graph and client lifecycle data. On this workload Citry
is a little slower on the first render, but faster once warm.

| What is measured | Citry vs django-components |
| --- | --- |
| First render | about 12% slower |
| Repeat renders | about 24% faster |
| Startup | about 1.4x slower |
| Import | about 1.3x slower |

## Versus bare template engines

Plain Django and Jinja2 render no components at all, so they skip the work
Citry does on every render. Citry's repeat render currently takes about 3.5x
the time of the bare Django template in this scenario.

## Jinja2, the no-component baseline

Jinja2 is the fast baseline with no component model, where each Citry component
becomes a precompiled macro. That makes it the quickest engine to start up and
the quickest once warm, since a warm render just runs precompiled macro code.
Its first render compiles the whole macro library and lands near
django-components.

## Reading these numbers

These are relative numbers from a single machine, not absolute guarantees.

- "Citry renders this page N times faster or slower than django-components
  here" is a fair reading of this run.
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

- [Performance](/v/0.4.3/advanced/performance/) covers opt-in reuse with
  [`Const`](/v/0.4.3/reference/rendering/#citry-const) and pure component classes.