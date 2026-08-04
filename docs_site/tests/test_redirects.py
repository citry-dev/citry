"""Tests for the moved-page redirect stubs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.redirects import emit_redirects, load_redirect_catalog


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


@pytest.mark.parametrize(
    "unsafe",
    [
        "/bad\\path/",
        '/bad" onmouseover="x/',
        "/bad<path>/",
        "/bad\x00path/",
    ],
)
def test_redirect_catalog_rejects_filesystem_and_html_unsafe_paths(tmp_path: Path, unsafe: str) -> None:
    path = tmp_path / "redirects.yml"
    path.write_text(
        "redirects:\n  - from: " + json.dumps(unsafe) + "\n    to: /new/\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError):
        load_redirect_catalog(path)
