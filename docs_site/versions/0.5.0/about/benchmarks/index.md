---
title: Benchmarks
url: https://citry.dev/v/0.5.0/about/benchmarks/
description: "Compare optimized Citry rendering with Django, django-components and Jinja2."
---
# Benchmarks

The chart compares a large project-management page rendered with Citry,
django-components, Django templates and Jinja2 macros. Citry uses the documented
performance optimizations described below. The chart shows one controlled run
from 2026-09-10. Lower bars mean less rendering time.

<img src="/static/img/benchmark.png" alt="First, second and warmed render times for optimized Citry, Django, django-components and Jinja2" width="720" />

\* Citry uses `simple` and `pure` optimizations. See the
[performance optimization guide](/v/0.5.0/advanced/performance/).

| Configuration | First render | Second render | Warmed render |
| --- | ---: | ---: | ---: |
| Django | 19.67 ms | 11.79 ms | 11.67 ms |
| django-components | 68.27 ms | 48.11 ms | 54.69 ms |
| Jinja2 | 66.10 ms | 6.77 ms | 7.21 ms |
| Citry* | 64.19 ms | 25.02 ms | 24.62 ms |

## What the Citry result includes

Button, Icon and HeroIcon are declared as
[simple components](/v/0.5.0/advanced/simple-components/). Their data callbacks stay
live, but they give up independent instances, hooks and browser identity.
HeroIcon and ProjectOutputBadge also retain the scenario's existing `pure`
declarations. The page constructs 146 ordinary instances and emits 989,431 bytes,
including dependencies, browser runtimes and ownership data. It takes about 55%
less time than django-components once warm.

These optimizations are explicit application choices with documented contracts.
The [repository benchmark guide](https://github.com/citry-dev/citry/blob/main/benchmarks/README.md)
also retains the ordinary Citry measurements and the paired comparison that
isolates the effect of opting the three classes into simple mode.

## Compare with template engines

The warmed Citry page takes about 2.11 times Django's render time. Jinja2 is the
fastest warmed engine here. Its first render compiles the macro library.

These engines produce different output and perform different framework work.
Django emits 456,422 bytes, django-components 309,837 bytes and Jinja2 151,789
bytes. The Django scenario still uses django-components' HTML-attribute helper;
Jinja2 represents the component templates as macros. The chart compares these
workloads, not equivalent implementations of every Citry feature.

## How the run is measured

The run uses Apple M4, CPython 3.14.3 and the release Citry Core extension,
with Django 6.0.6, django-components 0.152.0 and Jinja2 3.1.6. Citry 0.5.0 is measured with the qualified Core 1.7.0 release wheel.

The underlying run also measured ordinary Citry as a control; the chart shows
four configurations. Ten blocks each start a fresh process for every configuration, balancing
execution position and before/after order. Each process renders six initial
outputs and 80 warmed outputs, with normal garbage collection enabled, and
keeps all output strings alive until timing finishes. Loading the scenario
and preparing application data happen outside the render timer.

First and second columns are medians of the corresponding observations.
The warmed column is the median of each process's mean of 80 renders.
A warmed average can be higher than one second-render observation because
it includes a longer execution period and garbage collection.

Every timed Citry output is checked after timing using a projection that
removes ownership markers and normalizes generated IDs; its browser manifests
are validated too. Callback and ownership counts come from a separate observed
render after each Citry process's timed loop. The other engines retain output
hashes and sizes; their scenario content tests run separately.

These results are relative to this workload and machine. Use them to compare
rows within this run, then measure the components and data in your application.

## Reproduce it

The measurement runner and its experiment helpers are retained in the
[performance research archive](https://github.com/citry-dev/citry/blob/37007427bc7157085f8ce4d55ff73155d873764f/benchmarks/RESEARCH.md).
Use that checkout with the documented dependencies and a release Core extension
to repeat the measurement.

The main checkout keeps the compact chart data and image generator:


```sh
uv run --no-project --with matplotlib python benchmarks/plot.py
```


The [benchmark repository guide](https://github.com/citry-dev/citry/blob/main/benchmarks/README.md)
contains dependency setup, detailed methodology and links to raw observations.
The extension must be built in release mode; a debug build does not provide
comparable Citry timings.

## Related pages

- [Performance](/v/0.5.0/advanced/performance/) compares simple rendering, `Const`
  and pure component bodies.
- [Simple components](/v/0.5.0/advanced/simple-components/) explains the opt-in
  contract used by the Citry result.