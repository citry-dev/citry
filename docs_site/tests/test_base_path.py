"""Tests for the subpath (base-path) URL rewriting."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.base_path import apply_base_path


def _write(tmp_path: Path, html: str) -> Path:
    page = tmp_path / "page" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text(html, encoding="utf-8")
    return page


def test_rewrites_root_absolute_urls_and_injects_meta(tmp_path: Path) -> None:
    page = _write(
        tmp_path,
        '<head></head><body><link href="/static/x.css">'
        '<a href="/reference/">R</a><img src="/img.png">'
        '<button data-fragment-url="/examples/x/demo/y/"></button>'
        '<a href="https://ext.test/">ext</a></body>',
    )

    changed = apply_base_path(tmp_path, "/citry")

    out = page.read_text(encoding="utf-8")
    assert changed == 1
    assert 'href="/citry/static/x.css"' in out
    assert 'href="/citry/reference/"' in out
    assert 'src="/citry/img.png"' in out
    assert 'data-fragment-url="/citry/examples/x/demo/y/"' in out
    assert 'href="https://ext.test/"' in out  # external URLs untouched
    assert '<meta name="djc-base-path" content="/citry">' in out


def test_no_base_path_is_a_noop(tmp_path: Path) -> None:
    page = _write(tmp_path, '<head></head><a href="/x/">x</a>')
    assert apply_base_path(tmp_path, "") == 0
    assert 'href="/x/"' in page.read_text(encoding="utf-8")


def test_rewrite_is_idempotent(tmp_path: Path) -> None:
    page = _write(tmp_path, '<head></head><a href="/x/">x</a>')
    apply_base_path(tmp_path, "/citry")
    first = page.read_text(encoding="utf-8")
    apply_base_path(tmp_path, "/citry")  # a second run must not change anything
    assert page.read_text(encoding="utf-8") == first
    assert first.count("/citry/x/") == 1  # not double-prefixed


def test_protocol_relative_url_untouched(tmp_path: Path) -> None:
    page = _write(tmp_path, '<head></head><script src="//cdn.test/a.js"></script>')
    apply_base_path(tmp_path, "/citry")
    assert 'src="//cdn.test/a.js"' in page.read_text(encoding="utf-8")
