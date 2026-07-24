"""
Tests for the page-rendering pipeline (passes 2-3).

These render markdown through ``render_page`` and check the resulting HTML, both
for a small inline source and for the real ``content/index.md``.
"""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.build import configure_docs_globals
from docs_site._internal.config import DocsConfig, config
from docs_site._internal.pipeline import render_page

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

    # Content wrapper and rendered markdown (the article also carries the
    # search-index hook, so match the opening tag rather than an exact string).
    assert '<article class="prose"' in html
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
    # The home page reads the {{ version }} template global, which build and serve
    # configure at startup; do the same here so rendering the real page matches
    # production instead of relying on another test having set the global.
    configure_docs_globals(config)
    source = (config.content_dir / "index.md").read_text(encoding="utf-8")
    result = render_page(source)
    html = result.html

    assert "<!DOCTYPE html>" in html
    assert "<title>Citry</title>" in html  # title == site_name, so no suffix
    # The home page's sections and its "where to go next" links rendered.
    assert "Two simple rules" in html
    assert 'href="/getting-started/installation/"' in html
    # toc tokens were captured.
    assert isinstance(result.toc_tokens, list)


def test_no_layout_returns_content_only() -> None:
    result = render_page("# Heading\n\nText.", wrap_in_layout=False)
    assert "<!DOCTYPE html>" not in result.html
    assert "<h1" in result.html


def test_site_default_description_backfills_a_page_with_no_usable_body() -> None:
    # A page with no front-matter description and only a heading in its body has
    # nothing to derive a description from, so the site-level default backfills
    # the meta/OG/Twitter description tags (they are never left empty).
    html = render_page("---\ntitle: Bare\n---\n\n# Bare page\n").html
    default = config.default_description
    assert f'<meta name="description" content="{default}"/>' in html
    assert f'<meta property="og:description" content="{default}"' in html
    assert f'<meta name="twitter:description" content="{default}"' in html


def test_first_paragraph_beats_site_default_at_render() -> None:
    # With no front-matter description but a real first paragraph, the derived
    # paragraph wins over the site default (tier 2 before tier 3).
    html = render_page("---\ntitle: T\n---\n\nA real intro paragraph.\n").html
    assert '<meta name="description" content="A real intro paragraph."/>' in html
    assert config.default_description not in html


def test_internal_md_link_rewritten_external_untouched(tmp_path: Path) -> None:
    # A page under the content dir with two `.md` links: an internal one authored
    # against the source tree, and an external GitHub one. The rewrite turns the
    # internal link into a clean relative URL that resolves under the clean-URL
    # scheme (the page at /test/pipeline_test/ reaches /test/other/ via ../other/),
    # and leaves the external link alone. site_url is pinned so the assertion does
    # not depend on the DOCS_SITE_URL environment.
    content = tmp_path / "content"
    (content / "test").mkdir(parents=True)
    cfg = DocsConfig(
        content_dir=content, site_dir=tmp_path / "site", repo_root=tmp_path, site_url="https://citry.dev/"
    )
    source_path = content / "test" / "pipeline_test.md"
    source = (
        "---\ntitle: T\n---\n\n"
        "[another page](./other.md)\n\n"
        "[readme](https://github.com/citry-dev/citry/blob/main/README.md)\n"
    )
    source_path.write_text(source, encoding="utf-8")

    # Content-only render (the Pass 2 output, before the DocPage wrap).
    content_only = render_page(source, config=cfg, source_path=source_path, wrap_in_layout=False).html
    assert '<a href="../other/">another page</a>' in content_only
    assert 'href="https://github.com/citry-dev/citry/blob/main/README.md"' in content_only

    # The wrapped page runs the same rewrite, so its content carries it too.
    wrapped = render_page(source, config=cfg, source_path=source_path).html
    assert '<a href="../other/">another page</a>' in wrapped
    assert 'href="https://github.com/citry-dev/citry/blob/main/README.md"' in wrapped
