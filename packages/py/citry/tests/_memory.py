"""
Give tests that measure memory with ``tracemalloc`` a way to run on PyPy.

PyPy ships ``tracemalloc.py`` but not the ``_tracemalloc`` module it
imports, because PyPy's garbage collector does not report allocations the
way CPython's allocator does. A test module that imported ``tracemalloc``
directly would then fail to load on PyPy and take all its other tests with
it (#585). Import ``tracemalloc`` from here instead and mark each test that
uses it with ``requires_tracemalloc``.
"""

import pytest

try:
    import tracemalloc
except ImportError:
    # The mark below skips every test that would use it, so the name never
    # needs a real value on PyPy.
    tracemalloc = None  # type: ignore[assignment]

requires_tracemalloc = pytest.mark.skipif(tracemalloc is None, reason="PyPy has no _tracemalloc; see #585")

__all__ = ["requires_tracemalloc", "tracemalloc"]
