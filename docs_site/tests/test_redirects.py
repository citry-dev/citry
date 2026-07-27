"""Tests for the moved-page redirect stubs."""

from __future__ import annotations

import json
from pathlib import Path

from docs_site._internal.redirects import emit_redirects


def test_empty_redirect_map_writes_nothing(tmp_path: Path) -> None:
    assert emit_redirects(tmp_path, site_url="https://x.test", redirects={}) == 0
    assert list(tmp_path.iterdir()) == []


def test_redirect_stub_forwards_and_self_excludes(tmp_path: Path) -> None:
    count = emit_redirects(
        tmp_path,
        site_url="https://x.test/",
        redirects={"/old/page/": "/new/page/"},
    )

    assert count == 1
    stub = (tmp_path / "old" / "page" / "index.html").read_text(encoding="utf-8")
    # Forwards three ways and keeps itself out of the index.
    assert 'http-equiv="refresh"' in stub
    assert "window.location.replace(" in stub
    assert 'name="robots" content="noindex,follow"' in stub
    # Canonical is absolute; the refresh/JS href is relative (base-path-safe).
    assert '<link rel="canonical" href="https://x.test/new/page/">' in stub
    href = json.dumps("../../new/page/")
    assert f"window.location.replace({href});" in stub
