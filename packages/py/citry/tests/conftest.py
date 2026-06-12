import itertools

import pytest

# The Django/DJC benchmark scenario files (docs/design/benchmarking.md) need
# the optional `benchmark` dependency group. Skipping them here (rather than
# with importorskip inside the files) keeps the vendored files' import section
# byte-identical to upstream, which the benchmark harness slices and times.
try:
    import django_components  # noqa: F401
except ImportError:
    collect_ignore_glob += ["test_benchmark_django*", "test_benchmark_djc*"]


@pytest.fixture(autouse=True)
def _deterministic_render_ids(monkeypatch):
    """
    Make component render ids predictable within each test.

    ``serialize()`` tags each component's root element(s) with a
    ``data-cid-<id>=""`` marker, where ``<id>`` is normally a random per-render
    id. Tests assert on the real marker output, so within a test the ids are a
    simple counter (``c1``, ``c2``, ...), assigned in render order: the root
    component first, then its children depth-first.
    """
    counter = itertools.count(1)
    monkeypatch.setattr("citry.component.gen_render_id", lambda: f"c{next(counter)}")
