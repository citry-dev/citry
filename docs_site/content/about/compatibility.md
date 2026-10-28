---
title: Compatibility
description: The Python versions, operating systems, CPU architectures, and browsers Citry runs on, and when installing it needs Rust.
---

# Compatibility

Check this page before you install Citry on a new server, CI image, or
platform. It lists the Python versions, systems, and browsers Citry
supports, and the one case where installing it needs a compiler.

## Python versions { #supported-python-versions }

Citry supports Python 3.11 through 3.15:

- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- Python 3.15

See the
[Python release status](https://devguide.python.org/versions/){: target="_blank" rel="noopener"}
for which versions are still maintained upstream.

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

These wheels cover regular CPython 3.11 through 3.15. Free-threaded
CPython 3.14 and 3.15 and PyPy 3.11 have wheels only on Linux; elsewhere
pip builds `citry-core` from source, as described below. On a free-threaded
build, Citry installs and works, but for now importing `citry-core` turns the
GIL back on for the whole process
([#433](https://github.com/citry-dev/citry/issues/433)).

The exact list is in the
[files on PyPI](https://pypi.org/project/citry-core/#files){: target="_blank" rel="noopener"}.

Citry writes the same pages on every interpreter, apart from the builtins
difference with the sandbox off described below. On standard CPython it
renders [`simple = "vue"` components faster](/performance/#faster-simple-vue-rows-on-cpython)
than on PyPy, Pyodide, or free-threaded builds.

### Differences on PyPy

On PyPy, `citry check` and the editor check less. PyPy has no `_symtable`
module, which two of their analyses use. So the editor and `citry check
--types` give no types to a template that uses a name its
`template_data()` method assigns. And `citry check` does not read the
module-level values that `js_data()` sends, so it misses a `Secret` or
`Path` constant sent to the browser. `citry check` prints a note saying
so, and the editor shows a warning when it starts. These checks do not
change how a page renders, and Citry still refuses a `Secret` in
`js_data()` while it renders. For the full check, run `citry check` on
CPython. Issue [#434](https://github.com/citry-dev/citry/issues/434)
tracks giving PyPy the same answers.

If you turn off the [expression sandbox](/security/#turning-the-sandbox-off)
with `Citry(sandbox_expressions=False)`, template expressions on PyPy can
also call any Python builtin. A missing variable that shares a builtin's
name, such as `{{ id }}`, also renders on PyPy (as
`<built-in function id>`) instead of failing. Compute such values in
`template_data()` instead, as the security page shows in
[Builtins are missing](/security/#why-builtins-are-not-available). Then
both interpreters give the same result.

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
