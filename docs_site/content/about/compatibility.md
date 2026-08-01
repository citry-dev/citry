---
title: Compatibility
description: The Python versions, operating systems, and CPU architectures citry runs on, and when building from source needs Rust.
---

# Compatibility

## Supported Python versions

Citry runs on and supports every [officially supported Python version](https://devguide.python.org/versions/){: target="_blank" rel="noopener"}:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

## Operating systems

Citry is tested on Linux, Windows, and macOS across every supported Python version. It should run on any operating system that supports Python.

## Architectures and prebuilt wheels

Most of citry is pure Python. The one compiled piece is its Rust core, `citry-core`, which parses and compiles your component templates.

It is built with [maturin](https://www.maturin.rs/){: target="_blank" rel="noopener"} and [PyO3](https://pyo3.rs/){: target="_blank" rel="noopener"},
and prebuilt wheels are published for a wide range of platforms, so a normal install pulls in a ready-made binary and needs no compiler.

Prebuilt `citry-core` wheels are published for:

- Linux on x86-64, x86, ARM64, and ARMv7, for both glibc (manylinux) and musl (musllinux), plus s390x and ppc64le on glibc
- Windows, 64-bit and 32-bit
- macOS, on Intel and Apple Silicon

For the exact, current list, see the [files on PyPI](https://pypi.org/project/citry-core/#files){: target="_blank" rel="noopener"}. This covers most environments.

## Building from source

If pip has no prebuilt wheel for your platform, it falls back to the source distribution and builds `citry-core` locally. That build needs a Rust toolchain, so install [Rust and Cargo](/community/development#getting-set-up) first, then run the install again. Nothing else in citry needs a build step.

## Browser runtime

Citry's JavaScript browser code is tested aginst Chromium, Firefox, and
WebKit.

Citry injects a pinned version of [Alpine.js](http://alpinejs.dev/){: target="_blank" rel="noopener"} into the browser:

- Do **NOT** inject your own Alpine runtime.
- To load custom Alpine plugins, use
[the pre-start API](/advanced/alpine-runtime/#add-an-alpine-plugin).

## See also

- [Installation](/getting-started/installation/) walks through installing citry and confirming it works.
- [Alpine runtime](/advanced/alpine-runtime/) documents browser loading and deployment.
