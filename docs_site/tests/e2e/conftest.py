"""
Harness for the docs-site browser e2e tests.

Builds the real static site once (the same artifact a deploy ships: minified,
with the Pagefind search index) and serves it over a background HTTP server that
Playwright can point a real browser at. This is the integration layer the unit
tests miss: it exercises the whole rendered site (chrome, TOC, nav, search,
assets) in a browser, so a dropped markup hook, a broken asset URL, or an empty
table of contents fails a test instead of shipping.

Playwright comes from the optional ``e2e`` dependency group plus the ``docs``
extra; each test module ``importorskip``s it, so the suite is skipped anywhere
Playwright is not installed (the default dev env).
"""

from __future__ import annotations

import functools
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from docs_site._internal.build import build_site

if TYPE_CHECKING:
    from collections.abc import Iterator


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


@pytest.fixture(scope="session")
def docs_site_url() -> Iterator[str]:
    """Build the static docs site once, serve it, and yield its base URL."""
    tmp = Path(tempfile.mkdtemp(prefix="citry-docs-e2e-"))
    site = tmp / "site"
    # Social cards off (they need a browser and are unit-tested elsewhere); search
    # and minify stay on so the served site matches the deployed artifact.
    build_site(output_dir=site, social_cards=False)

    handler = functools.partial(_QuietHandler, directory=str(site))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
