"""Shared fixtures for the docs-site tests and the example tests beside them."""

from __future__ import annotations

import pytest

from citry import citry as default_citry


@pytest.fixture(autouse=True)
def _unmounted_default_citry(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Start every test with the shared Citry instance unmounted.

    `build_site()` and `create_app()` record a mount prefix on the shared
    instance. Once a prefix is recorded, a rendered page loads its component
    definitions from URLs instead of inline scripts, so a test that reads the
    inline definitions (the example tests under `docs_site/examples/` do)
    would pass or fail depending on which tests the same process ran first.
    Clearing the prefix here makes each test start from the state a fresh
    process has; a test that builds or serves the site records the prefix
    again itself, and monkeypatch restores the old value afterwards. This file
    sits at the `docs_site/` root so the example tests get the fixture too.
    """
    # The instance exposes no public way to forget a mount, so reset the
    # attribute that `set_mounted_prefix()` writes.
    monkeypatch.setattr(default_citry, "_mounted_prefix", None)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Refuse a pytest run that mixes the docs tests with the package tests.

    Importing a component module registers its class by name on the shared
    default Citry instance, and the docs examples and the package tests both
    define common names such as `Card` and `Page`. In one process the second
    definition fails to register, so the run breaks in ways unrelated to the
    code under test. Each suite runs in its own pytest process; this turns an
    accidental mix into one clear error.
    """
    del config
    if any(item.nodeid.startswith("packages/") for item in items):
        message = (
            "docs_site tests share the default Citry registry with the package tests. "
            "Run `pytest docs_site/tests docs_site/examples` in a separate pytest process."
        )
        raise pytest.UsageError(message)
