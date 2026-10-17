---
title: Compatibility
description: The Python versions, operating systems, CPU architectures, and browsers Citry runs on, and when installing it needs Rust.
---

# Compatibility

Check this page before you install Citry on a new server, CI image, or
platform. It lists the Python versions, systems, and browsers Citry
supports, and the one case where installing it needs a compiler.

## Python versions { #supported-python-versions }

Citry supports every
[officially supported Python version](https://devguide.python.org/versions/){: target="_blank" rel="noopener"}:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

## Operating systems

Citry's tests run on Linux and Windows with every supported Python version,
and on macOS with the oldest and newest. Citry should run on any operating
system that runs Python.

## Prebuilt wheels { #architectures-and-prebuilt-wheels }

Most of Citry is plain Python. The one compiled part is `citry-core`, a
Rust package that parses and compiles your component templates. A normal
`pip install` downloads a ready-made `citry-core` wheel, so you do not
need a compiler.

Wheels are published for:

- Linux on x86-64, x86, ARM64, and ARMv7, for both glibc (manylinux) and
  musl (musllinux), plus s390x and ppc64le on glibc
- Windows, 64-bit and 32-bit
- macOS, on Intel and Apple Silicon

These wheels cover regular CPython 3.10 to 3.14. Free-threaded CPython
3.14 and PyPy 3.11 have wheels only on Linux; elsewhere pip builds
`citry-core` from source, as described below.

The exact list is in the
[files on PyPI](https://pypi.org/project/citry-core/#files){: target="_blank" rel="noopener"}.

## Build from source { #building-from-source }

When PyPI has no wheel for your platform, pip downloads the source of
`citry-core` and builds it on your machine. That build needs Rust 1.96 or
newer. Install it with [rustup](https://rustup.rs/){: target="_blank" rel="noopener"},
then run the install again. Nothing else in Citry needs a build step.

## Browsers { #browser-runtime }

Citry's browser code is tested in Chromium, Firefox, and WebKit.

Citry loads its own pinned copy of Vue for interactive components. Do not
mount another Vue application over HTML that Citry rendered. To use Vue
helpers such as `ref` in your own code, take them from `Citry.vue`, so
they come from the same Vue copy as the page.

## See also

- [Installation](/getting-started/installation/) walks through installing
  Citry and checking that it works.
- [Vue in Citry](/vue/) explains which Vue version Citry ships and how the
  browser loads it, and [Server-rendered HTML](/vue/server-rendering/)
  covers what your deployment must leave untouched.
