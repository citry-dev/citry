"""Tests for the catalog-backed ``<c-blog-list />`` component family."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from docs_site._internal.blog import load_blog_catalog, use_blog_catalog
from docs_site._internal.components.blog import BlogList
from docs_site._internal.config import DocsConfig
from docs_site._internal.pipeline import render_page


def test_blog_list_renders_catalog_cards_and_plain_text_tags(tmp_path: Path) -> None:
    blog = tmp_path / "content" / "blog"
    blog.mkdir(parents=True)
    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (blog / "2026-07-28-first-post.md").write_text(
        """---
title: First post
description: The first post description.
date: 2026-07-28T09:00:00+02:00
author: Citry maintainers
tags: Project updates, Architecture
---

Opening context.
""",
        encoding="utf-8",
    )
    catalog = load_blog_catalog(
        blog.parent,
        now=datetime.fromisoformat("2026-07-29T12:00:00+00:00"),
    )

    with use_blog_catalog(catalog):
        html = str(BlogList())

    assert 'href="/blog/first-post/"' in html
    assert 'datetime="2026-07-28T09:00:00+02:00"' in html
    assert "Citry maintainers" in html
    assert 'aria-label="Tags"' in html
    assert "Project updates" in html
    assert 'href="/blog/feed.xml"' in html
    assert "docs-blog-list:start" in html


def test_blog_index_executes_only_the_directive_outside_markdown_code(tmp_path: Path) -> None:
    blog = tmp_path / "content" / "blog"
    blog.mkdir(parents=True)
    index = blog / "index.md"
    index.write_text(
        "The `<c-blog-list />` directive renders the cards below.\n\n    <c-blog-list />\n\n<c-blog-list />\n",
        encoding="utf-8",
    )
    (blog / "2026-07-28-first-post.md").write_text(
        "---\n"
        "title: First post\n"
        "description: The first post description.\n"
        "date: 2026-07-28T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "---\n\nOpening context.\n",
        encoding="utf-8",
    )
    catalog = load_blog_catalog(
        blog.parent,
        now=datetime.fromisoformat("2026-07-29T12:00:00+00:00"),
    )

    result = render_page(
        index.read_text(encoding="utf-8"),
        config=DocsConfig(content_dir=blog.parent, repo_root=tmp_path),
        current_path="blog/",
        source_path=index,
        blog_catalog=catalog,
        is_blog_index=True,
    )

    assert result.html.count('class="blog-card"') == 1
    assert result.html.count("docs-blog-list:start") == 1
