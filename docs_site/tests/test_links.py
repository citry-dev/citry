"""Tests for HTML heading/link post-processing (docs_site/_internal/links.py)."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.links import (
    linkify_headings,
    project_internal_markdown_urls,
    project_markdown_base_path,
    rewrite_internal_md_links,
    rewrite_internal_md_links_in_markdown,
)
from docs_site._internal.nav import SCOPE_SITE, NavArea, NavItem, NavTree
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import load_docs_project, use_docs_project

_MARKDOWN_HEADING = (
    '<h2 id="refactor">Refactor<a class="headerlink" href="#refactor" title="Permanent link">¤</a></h2>'
)
_REFERENCE_HEADING = (
    '<h2 id="citry-extension" class="doc-heading">'
    '<span class="doc-symbol doc-symbol-class"></span>'
    '<span class="doc-object-name"><code>Extension</code></span>'
    '<span class="doc-kind">class</span></h2>'
)


def test_linkify_wraps_a_markdown_heading_and_drops_the_glyph() -> None:
    out = linkify_headings(_MARKDOWN_HEADING)
    assert out == '<h2 id="refactor"><a class="heading-anchor" href="#refactor">Refactor</a></h2>'
    assert "\xa4" not in out  # the ¤ glyph is dropped in favour of the whole-heading link


def test_linkify_wraps_a_reference_symbol_heading() -> None:
    # No ¤, class after id, child spans: the whole content becomes the link.
    out = linkify_headings(_REFERENCE_HEADING)
    assert '<a class="heading-anchor" href="#citry-extension">' in out
    assert '<span class="doc-object-name"><code>Extension</code></span>' in out  # spans preserved inside
    assert out.count("</a>") == 1
    assert 'class="doc-heading"' in out  # heading's own attributes are kept


def test_linkify_skips_a_heading_that_already_has_a_link() -> None:
    html = '<h2 id="x"><a href="/foo/">Foo</a><a class="headerlink" href="#x" title="Permanent link">¤</a></h2>'
    assert linkify_headings(html) == html  # unchanged (wrapping would nest anchors)


def test_linkify_leaves_a_heading_without_an_id_alone() -> None:
    assert linkify_headings("<h2>Plain</h2>") == "<h2>Plain</h2>"


def test_linkify_wraps_every_heading_level_including_h1() -> None:
    html = (
        '<h1 id="a">A<a class="headerlink" href="#a" title="Permanent link">¤</a></h1>'
        '<h3 id="b">B<a class="headerlink" href="#b" title="Permanent link">¤</a></h3>'
    )
    out = linkify_headings(html)
    assert out.count('class="heading-anchor"') == 2
    assert "\xa4" not in out


def test_pipeline_links_content_and_reference_headings_without_a_glyph() -> None:
    html = render_page("---\ntitle: T\n---\n\n# T\n\n## Refactor\n\nx\n", current_path="x/", wrap_in_layout=False).html
    assert '<a class="heading-anchor" href="#refactor">Refactor</a>' in html  # h2 wrapped
    assert '<a class="heading-anchor" href="#t">T</a>' in html  # the h1 too
    assert "\xa4" not in html  # no permalink glyph remains


def test_link_rewriting_uses_stable_source_route_for_page_and_target(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog = content / "blog"
    guide = content / "guide"
    blog.mkdir(parents=True)
    guide.mkdir()
    post = blog / "2026-07-28-first.md"
    target = blog / "2026-07-27-second.md"
    post.write_text("post", encoding="utf-8")
    target.write_text("target", encoding="utf-8")
    routes = {
        post.resolve(): "/blog/first/",
        target.resolve(): "/blog/second/",
    }

    html = rewrite_internal_md_links(
        '<a href="./2026-07-27-second.md?view=full#part">Second</a>',
        source_path=post,
        content_dir=content,
        current_public_path="/blog/first/",
        source_to_public_path=routes,
    )

    assert 'href="../second/?view=full#part"' in html


def test_markdown_link_rewriting_uses_routes_and_skips_fences(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    post = blog / "2026-07-28-first.md"
    target = blog / "2026-07-27-second.md"
    post.write_text("post", encoding="utf-8")
    target.write_text("target", encoding="utf-8")
    routes = {
        post.resolve(): "/blog/first/",
        target.resolve(): "/blog/second/",
    }
    source = "[Second](./2026-07-27-second.md#part)\n\n```markdown\n[Literal](./2026-07-27-second.md)\n```\n"

    rewritten = rewrite_internal_md_links_in_markdown(
        source,
        source_path=post,
        content_dir=content,
        current_public_path="/blog/first/",
        source_to_public_path=routes,
    )

    assert "[Second](../second/#part)" in rewritten
    assert "[Literal](./2026-07-27-second.md)" in rewritten


def test_link_rewriting_supports_catalog_sources_outside_content_dir(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    components = tmp_path / "package" / "components"
    components.mkdir(parents=True)
    button = components / "button.md"
    field = components / "field.md"
    routes = {
        button.resolve(): "/ui-library/components/button/",
        field.resolve(): "/ui-library/components/field/",
    }

    html = rewrite_internal_md_links(
        '<a href="./field.md#validation">Field</a>',
        source_path=button,
        content_dir=content,
        source_to_public_path=routes,
    )
    markdown = rewrite_internal_md_links_in_markdown(
        "[Field](./field.md#validation)\n",
        source_path=button,
        content_dir=content,
        source_to_public_path=routes,
    )

    assert 'href="../field/#validation"' in html
    assert markdown == "[Field](../field/#validation)\n"


def test_generated_markdown_projects_versioned_and_site_routes() -> None:
    tree = NavTree(
        areas=[
            NavArea(label="Reference", items=[NavItem(title="Widget", path="/reference/widget/")]),
            NavArea(
                label="Blog",
                items=[NavItem(title="Post", path="/blog/post/", scope=SCOPE_SITE)],
                scope=SCOPE_SITE,
            ),
        ]
    )
    source = (
        "[Widget](/reference/widget/?view=all#api)\n\n"
        "[Post](/blog/post/)\n\n"
        "```markdown\n[Literal](/reference/widget/)\n```\n"
    )

    projected = project_internal_markdown_urls(
        source,
        current_public_path="reference/",
        nav_tree=tree,
        version_prefix="/v/1.2.3",
    )

    assert "[Widget](/v/1.2.3/reference/widget/?view=all#api)" in projected
    assert "[Post](/blog/post/)" in projected
    assert "[Literal](/reference/widget/)" in projected


def test_generated_markdown_uses_the_configured_root_pagefind_directory(tmp_path: Path) -> None:
    settings = tmp_path / "settings.yml"
    settings.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/pagefind/pagefind.js",
            "/custom-search/pagefind.js",
            1,
        ),
        encoding="utf-8",
    )
    project = load_docs_project(DocsConfig(settings_config=settings))
    tree = NavTree(areas=[NavArea(label="Docs", items=[NavItem(title="Docs", path="/docs/")])])
    source = "[Current](/custom-search/pagefind.js) [Stale](/pagefind/pagefind.js)"

    with use_docs_project(project):
        projected = project_internal_markdown_urls(
            source,
            current_public_path="docs/",
            nav_tree=tree,
            version_prefix="/v/1.2.3",
        )

    assert "[Current](/custom-search/pagefind.js)" in projected
    assert "[Stale](/v/1.2.3/pagefind/pagefind.js)" in projected


def test_markdown_base_path_projection_preserves_non_root_and_fenced_destinations() -> None:
    source = (
        "[Guide](/guide/?view=all#part)\n"
        "![Image](</static/image.png>)\n"
        "[Route collision](/citry/reference/)\n"
        "[Relative](../other/)\n"
        "[Anchor](#part)\n"
        "[External](https://example.com/root/)\n\n"
        "[Guide reference]: /guide/reference/#part\n"
        '<a href="/guide/raw/">Raw link</a>\n'
        '<img src="/static/image.png">\n\n'
        "```markdown\n"
        "[Literal](/guide/)\n"
        "[Literal reference]: /guide/reference/\n"
        '<a href="/guide/raw/">Literal raw link</a>\n'
        '<img src="/static/literal.png">\n'
        "```\n"
    )

    projected = project_markdown_base_path(source, "/citry")

    assert "[Guide](/citry/guide/?view=all#part)" in projected
    assert "![Image](</citry/static/image.png>)" in projected
    assert "[Route collision](/citry/citry/reference/)" in projected
    assert "[Relative](../other/)" in projected
    assert "[Anchor](#part)" in projected
    assert "[External](https://example.com/root/)" in projected
    assert "[Guide reference]: /citry/guide/reference/#part" in projected
    assert '<a href="/citry/guide/raw/">Raw link</a>' in projected
    assert '<img src="/citry/static/image.png">' in projected
    assert "[Literal](/guide/)" in projected
    assert "[Literal reference]: /guide/reference/" in projected
    assert '<a href="/guide/raw/">Literal raw link</a>' in projected
    assert '<img src="/static/literal.png">' in projected
