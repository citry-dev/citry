"""
Tests for the page-rendering pipeline (passes 2-3).

These render markdown through ``render_page`` and check the resulting HTML, both
for a small inline source and for the real ``content/index.md``.
"""

from __future__ import annotations

from pathlib import Path

from pygments.lexers import get_lexer_by_name

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


def test_cloudflare_web_analytics_is_explicitly_configured() -> None:
    assert "static.cloudflareinsights.com/beacon.min.js" not in render_page(SAMPLE).html

    cfg = DocsConfig(cloudflare_web_analytics_token="public-site-token")  # noqa: S106
    html = render_page(SAMPLE, config=cfg).html

    assert html.count("https://static.cloudflareinsights.com/beacon.min.js") == 1
    assert 'data-cf-beacon="{&#34;token&#34;:&#34;public-site-token&#34;}"' in html


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


def test_markdown_tables_have_a_bounded_scroll_container() -> None:
    result = render_page("| Name | Description |\n|---|---|\n| value | A long contract |")

    assert '<div class="table-wrapper" tabindex="0">' in result.html
    assert "<table>" in result.html


def test_citry_fence_styles_builtin_names_as_html_tags() -> None:
    result = render_page('```citry\ntemplate = """<c-slot /><c-template /><c-component is="card" />"""\n```')

    assert '<span class="nt">c-slot</span>' in result.html
    assert '<span class="nt">c-template</span>' in result.html
    assert '<span class="nt">c-component</span>' in result.html
    assert '<span class="nb">c-slot</span>' not in result.html


def test_fluent_lexer_alias_is_registered() -> None:
    lexer = get_lexer_by_name("fluent")

    assert "fluent" in lexer.aliases
    assert "ftl" in lexer.aliases
    assert "*.ftl" in lexer.filenames


def test_fluent_fence_highlights_messages_and_variables() -> None:
    result = render_page("```fluent\nhello = Hello, { $name }\n```")

    assert '<span class="no">hello</span>' in result.html
    assert '<span class="nv">$name</span>' in result.html


def test_markdown_body_captures_snippet_expansion_once(tmp_path: Path) -> None:
    snippet = tmp_path / "snippet.py"
    snippet.write_text(
        "# --8<-- [start:example]\n"
        "class IncludedFromSnippet:\n"
        '    template = "{{ value }}"\n'
        "    pass\n"
        "# --8<-- [end:example]\n",
        encoding="utf-8",
    )
    cfg = DocsConfig(repo_root=tmp_path, content_dir=tmp_path, site_dir=tmp_path / "site")
    source = (
        "```citry\n"
        '--8<-- "snippet.py:example"\n'
        "```\n\n"
        # An escaped directive is documentation, not another include. Capturing
        # the snippets preprocessor's output must not feed that output through a
        # second snippets pass, which would try to resolve missing.py.
        ';--8<-- "missing.py"\n'
    )

    result = render_page(source, config=cfg, wrap_in_layout=False)

    assert "IncludedFromSnippet" in result.html
    assert "class IncludedFromSnippet:" in result.markdown_body
    assert '```citry\nclass IncludedFromSnippet:\n    template = "{{ value }}"\n    pass\n```' in result.markdown_body
    assert '--8<-- "snippet.py:example"' not in result.markdown_body
    assert '--8<-- "missing.py"' in result.markdown_body


def test_markdown_body_expands_nested_block_and_empty_snippets(tmp_path: Path) -> None:
    (tmp_path / "leaf.py").write_text("NESTED_BLOCK_VALUE = 1\n", encoding="utf-8")
    (tmp_path / "empty.py").write_text("", encoding="utf-8")
    (tmp_path / "outer.md").write_text(
        "--8<--\nleaf.py\nempty.py\n--8<--\n",
        encoding="utf-8",
    )

    cfg = DocsConfig(repo_root=tmp_path, content_dir=tmp_path, site_dir=tmp_path / "site")
    result = render_page(
        '```python\n--8<-- "outer.md"\n```\n',
        config=cfg,
        wrap_in_layout=False,
    )

    assert "NESTED_BLOCK_VALUE" in result.html
    assert "NESTED_BLOCK_VALUE = 1" in result.markdown_body
    assert "--8<--" not in result.markdown_body


def test_configured_snippet_options_survive_runtime_path_overrides(tmp_path: Path) -> None:
    settings_source = config.settings_config.read_text(encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        settings_source.replace(
            "  docstrings:\n",
            "      pymdownx.snippets:\n        encoding: latin-1\n  docstrings:\n",
            1,
        ),
        encoding="utf-8",
    )
    (tmp_path / "latin.py").write_bytes("MESSAGE = 'café'\n".encode("latin-1"))
    cfg = DocsConfig(
        repo_root=tmp_path,
        content_dir=tmp_path,
        site_dir=tmp_path / "site",
        settings_config=settings_path,
    )

    result = render_page(
        '```python\n--8<-- "latin.py"\n```\n',
        config=cfg,
        wrap_in_layout=False,
    )

    assert "café" in result.html


def test_content_index_renders() -> None:
    # Configure globals exactly as build and serve do before exercising the real
    # page through all three rendering passes.
    configure_docs_globals(config)
    source = (config.content_dir / "index.md").read_text(encoding="utf-8")
    result = render_page(source)
    html = result.html

    assert "<!DOCTYPE html>" in html
    assert result.meta.layout == "landing"
    assert 'class="landing-shell"' in html
    assert 'class="djc-layout"' not in html
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
