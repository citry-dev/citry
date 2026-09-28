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
