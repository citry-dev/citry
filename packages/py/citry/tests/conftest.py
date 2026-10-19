import itertools

import pytest

collect_ignore_glob: list[str] = []

# The Django/DJC benchmark scenario files (docs/design/benchmarking.md) need
# the optional `benchmark` dependency group. Skipping them here (rather than
# with importorskip inside the files) keeps the vendored files' import section
# byte-identical to upstream, which the benchmark harness slices and times.
try:
    import django_components  # noqa: F401
except ImportError:
    collect_ignore_glob += ["test_benchmark_django*", "test_benchmark_djc*"]

# The Jinja2 benchmark scenario (the first engine beyond the Django family,
# docs/design/benchmarking.md section 2.1) needs the same optional `benchmark`
# dependency group. Skipped here when Jinja2 is absent, so the default dev
# install collects the suite without it.
try:
    import jinja2  # noqa: F401
except ImportError:
    collect_ignore_glob += ["test_benchmark_jinja2*"]


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


def _uses_pytest_playwright(item: pytest.Item) -> bool:
    # pytest-playwright's ``playwright`` fixture starts the sync runtime, and
    # ``page``, ``context``, and ``browser`` all depend on it. Check where the
    # fixture is defined, not only its name: a test module may define its own
    # fake fixture under one of these names that starts nothing.
    fixture_info = getattr(item, "_fixtureinfo", None)
    definitions = fixture_info.name2fixturedefs.get("playwright", ()) if fixture_info is not None else ()
    # A conftest may wrap the plugin's fixture under the same name, so check every definition.
    return any(definition.func.__module__.startswith("pytest_playwright") for definition in definitions)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    Run sync-Playwright E2E cases after tests that call ``asyncio.run``.

    Pytest Playwright's session-scoped sync runtime keeps its asyncio loop
    active on the main thread until session teardown. If filesystem discovery
    collects ``tests/e2e`` first, later ordinary tests cannot call
    ``asyncio.run``. Stable-partitioning the E2E marker to the end preserves
    order within both groups and lets the two valid test styles share one
    repository-wide invocation.

    A test that asks for a Playwright fixture is an E2E test whether or not
    its module says so. It gets the marker here, before ``-m`` selection runs,
    so a forgotten marker cannot put a browser test among the ordinary tests
    of a pytest-xdist worker, where it would break every later ``asyncio.run``.
    """
    for item in items:
        if item.get_closest_marker("e2e") is None and _uses_pytest_playwright(item):
            item.add_marker(pytest.mark.e2e)
    items.sort(key=lambda item: item.get_closest_marker("e2e") is not None)
