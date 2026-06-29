"""
Tests for the page-rendering pipeline (passes 2-3).

These render markdown through ``render_page`` and check the resulting HTML, both
for a small inline source and for the real ``content/index.md``.
"""

from __future__ import annotations

from docs_site.config import config
from docs_site.pipeline import render_page

SAMPLE = """\
---
title: Sample
description: A sample page.
---

# Sample

Some **bold** prose.

```python
print("hello")
```

!!! note

    An admonition.
"""


def test_full_page_structure() -> None:
    result = render_page(SAMPLE)
    html = result.html

    # A complete HTML document came out.
    assert "<!DOCTYPE html>" in html
    assert '<html lang="en"' in html
    assert "</html>" in html

    # Head metadata from the front matter.
    assert "<title>Sample - Citry</title>" in html
    assert '<meta name="description" content="A sample page."/>' in html
    assert '<meta name="robots" content="index,follow"/>' in html

    # Content wrapper and rendered markdown.
    assert '<article class="prose">' in html
    assert "<strong>bold</strong>" in html


def test_exactly_one_h1() -> None:
    # Content with its own H1: the layout must not inject a second.
    with_h1 = render_page("---\ntitle: T\n---\n\n# My Heading\n\nText.").html
    assert with_h1.count("<h1") == 1

    # Content without an H1 but with a title: the layout injects one.
    no_h1 = render_page("---\ntitle: My Title\n---\n\nJust text.").html
    assert no_h1.count("<h1") == 1
    assert "<h1>My Title</h1>" in no_h1


def test_markdown_extensions_render() -> None:
    result = render_page(SAMPLE)
    html = result.html

    # pymdownx.highlight turned the fenced block into a highlighted code block.
    assert 'class="highlight"' in html
    # The admonition extension produced its block.
    assert 'class="admonition note"' in html


def test_content_index_renders() -> None:
    source = (config.content_dir / "index.md").read_text(encoding="utf-8")
    result = render_page(source)
    html = result.html

    assert "<!DOCTYPE html>" in html
    assert "<title>Citry</title>" in html  # title == site_name, so no suffix
    # The table from the page rendered.
    assert "<table>" in html
    # toc tokens were captured.
    assert isinstance(result.toc_tokens, list)


def test_no_layout_returns_content_only() -> None:
    result = render_page("# Heading\n\nText.", wrap_in_layout=False)
    assert "<!DOCTYPE html>" not in result.html
    assert "<h1" in result.html
