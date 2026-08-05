"""Tests for the subpath (base-path) URL rewriting."""

from __future__ import annotations

from pathlib import Path

import pytest

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
    assert 'name="djc-base-path" content="/citry"' in out
    assert 'data-djc-base-path-applied="/citry"' in out


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


def test_rewrite_only_touches_real_url_attributes(tmp_path: Path) -> None:
    page = _write(
        tmp_path,
        '<head></head><a href="/real/" onclick="sample=\'href=&quot;/event/&quot;\'">real</a>'
        '<code>href="/documented/" src="/example.js"</code>'
        "<script>const sample = 'src=\"/script.js\"';</script>",
    )

    apply_base_path(tmp_path, "/preview")

    output = page.read_text(encoding="utf-8")
    assert 'href="/preview/real/"' in output
    assert "href=&quot;/event/&quot;" in output
    assert 'href="/documented/" src="/example.js"' in output
    assert 'src="/script.js"' in output


def test_existing_base_path_meta_is_updated(tmp_path: Path) -> None:
    page = _write(tmp_path, '<head><meta name=djc-base-path></head><a href="/x/">x</a>')

    apply_base_path(tmp_path, "/preview")

    output = page.read_text(encoding="utf-8")
    assert 'name=djc-base-path content="/preview"' in output
    assert 'data-djc-base-path-applied="/preview"' in output


def test_runtime_mount_matching_base_path_is_still_prefixed(tmp_path: Path) -> None:
    runtime = tmp_path / "citry" / "citry.js"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("runtime", encoding="utf-8")
    page = _write(
        tmp_path,
        '<head><meta name="djc-base-path" content="/citry"></head><script src="/citry/citry.js"></script>',
    )

    apply_base_path(tmp_path, "/citry")

    output = page.read_text(encoding="utf-8")
    public_src = "/citry/citry/citry.js"
    assert f'src="{public_src}"' in output
    output_relative_src = public_src.removeprefix("/citry/")
    assert (tmp_path / output_relative_src).is_file()


@pytest.mark.parametrize("base", ["/", "/preview/", "preview"])
def test_invalid_base_path_is_rejected(tmp_path: Path, base: str) -> None:
    _write(tmp_path, '<head></head><a href="/x/">x</a>')

    with pytest.raises(ValueError, match="base path"):
        apply_base_path(tmp_path, base)
