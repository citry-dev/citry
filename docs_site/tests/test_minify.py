"""Tests for the post-build HTML minify pass."""

from __future__ import annotations

import json
from pathlib import Path

from docs_site._internal.minify import minify_site


def test_minify_shrinks_html_and_preserves_pre(tmp_path: Path) -> None:
    src = (
        "<!DOCTYPE html>\n<html>\n  <head>\n    <title>T</title>\n  </head>\n"
        "  <body>\n    <p>hello     world</p>\n"
        "    <pre>def f():\n    return 1\n</pre>\n  </body>\n</html>\n"
    )
    page = tmp_path / "index.html"
    page.write_text(src, encoding="utf-8")

    outcome = minify_site(tmp_path)

    out = page.read_text(encoding="utf-8")
    assert outcome.files == 1
    assert outcome.after < outcome.before
    assert "hello world" in out  # prose whitespace collapsed
    assert "def f():\n    return 1" in out  # but <pre> indentation kept


def test_minify_leaves_ld_json_valid(tmp_path: Path) -> None:
    # Inline-JS minification is off, so a JSON-LD block stays valid JSON.
    src = (
        "<!DOCTYPE html><html><head>"
        '<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article"}</script>'
        "</head><body></body></html>"
    )
    page = tmp_path / "index.html"
    page.write_text(src, encoding="utf-8")

    minify_site(tmp_path)

    out = page.read_text(encoding="utf-8")
    # The JSON-LD object survives intact (attribute quotes may be dropped, so
    # read the object by its braces rather than a fixed delimiter).
    inner = out[out.index("{") : out.rindex("}") + 1]
    assert json.loads(inner) == {"@context": "https://schema.org", "@type": "Article"}


def test_minify_preserves_citry_ownership_caps(tmp_path: Path) -> None:
    digest = "a" * 8
    start = f"<!--citry:g1:{digest}:0:i:1:s-->"
    end = f"<!--citry:g1:{digest}:0:i:1:e-->"
    page = tmp_path / "index.html"
    page.write_text(f"<!DOCTYPE html><html><body>{start}<span>Hi</span>{end}</body></html>", encoding="utf-8")

    minify_site(tmp_path)

    out = page.read_text(encoding="utf-8")
    assert start in out
    assert end in out
    assert out.index(start) < out.index(end)
