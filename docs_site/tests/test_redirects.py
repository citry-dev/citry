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
    assert f"window.location.replace({href} + window.location.search + window.location.hash);" in stub


def test_redirect_stub_script_appends_fragment_and_precedes_meta_refresh(tmp_path: Path) -> None:
    # A link to /old/#section must land on /new/#section. Only the script can
    # read the fragment, so it has to run before the meta refresh is parsed and
    # append location.hash; the meta refresh and link remain the no-JS route.
    emit_redirects(tmp_path, site_url="https://x.test", redirects={"/old/": "/new/"})

    stub = (tmp_path / "old" / "index.html").read_text(encoding="utf-8")
    script = stub.index("<script>")
    assert "window.location.hash" in stub[script : stub.index("</script>")]
    assert script < stub.index('http-equiv="refresh"')
    assert '<meta http-equiv="refresh" content="0; url=../new/">' in stub
    assert '<a href="../new/">' in stub


@pytest.mark.parametrize(
    "unsafe",
    [
        "/bad\\path/",
        '/bad" onmouseover="x/',
        "/bad<path>/",
        "/bad\x00path/",
        "/old/%2e%2e/new/",
        "/C:/escape/",
        "/bad path/",
        "/bad\N{NO-BREAK SPACE}path/",
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


def test_redirect_stub_script_cannot_be_closed_by_the_target_path(tmp_path: Path) -> None:
    # emit_redirects also serves callers whose paths skip the catalog checks.
    emit_redirects(tmp_path, site_url="https://x.test", redirects={"/old/": "/</script>/"})

    stub = (tmp_path / "old" / "index.html").read_text(encoding="utf-8")
    assert stub.count("</script>") == 1
