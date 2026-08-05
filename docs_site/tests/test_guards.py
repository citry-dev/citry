"""Tests for the post-build guard suite."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from citry.component_registry import BUILTIN_COMPONENT_NAMES, STRUCTURAL_TAG_NAMES
from docs_site._internal.build import build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.examples import ExampleInfo, get_example_registry
from docs_site._internal.guards import (
    anchor,
    api_symbols,
    asset,
    authored_reference,
    blog,
    blog_feed,
    builtin_tags,
    component_fence,
    example_contract,
    fence_validator,
    format_report,
    frontmatter,
    internal_link,
    json_ld,
    make_context,
    nav,
    redirect_target,
    rendered_css,
    rendered_markdown,
    run_guards,
    single_h1,
    snippet_path,
)
from docs_site._internal.guards.base import GuardContext, GuardResult, Severity
from docs_site._internal.guards.site_index import SiteIndex
from docs_site._internal.project import load_docs_project

# A page that carries the generator marker is treated as a real doc page.
_DOC = (
    '<!DOCTYPE html><html><head><meta name="generator" content="citry docs builder"></head><body>{body}</body></html>'
)


def _index_ctx(tmp_path: Path, build_dir: Path) -> GuardContext:
    return GuardContext(
        content_dir=tmp_path,
        examples_dir=tmp_path,
        nav_path=tmp_path / "_nav.yml",
        static_dir=tmp_path,
        repo_root=tmp_path,
        site_index=SiteIndex(build_dir),
    )


def _content_ctx(tmp_path: Path) -> GuardContext:
    """A context for the source-scanning guards: ``content_dir`` points at ``tmp_path``."""
    return GuardContext(
        content_dir=tmp_path,
        examples_dir=tmp_path,
        nav_path=tmp_path / "_nav.yml",
        static_dir=tmp_path,
        repo_root=tmp_path,
    )


def _example_contract_ctx(tmp_path: Path, registry: dict[str, ExampleInfo]) -> GuardContext:
    """A context for the example-contract guard: examples and content both at ``tmp_path``."""
    return GuardContext(
        content_dir=tmp_path,
        examples_dir=tmp_path,
        nav_path=tmp_path / "_nav.yml",
        static_dir=tmp_path,
        repo_root=tmp_path,
        example_registry=registry,
    )


def _write_builtin_tags_page(root: Path, *, omit: str = "") -> None:
    reference = root / "reference"
    reference.mkdir(exist_ok=True)
    lines = [
        *(f'<c-builtin tag="{tag}" />' for tag in sorted(BUILTIN_COMPONENT_NAMES)),
        *(f'<h3 id="c-{tag}">tag</h3>' for tag in sorted(STRUCTURAL_TAG_NAMES)),
    ]
    (reference / "builtins.md").write_text(
        "\n".join(line for line in lines if not omit or omit not in line),
        encoding="utf-8",
    )


def _write_browser_api_page(root: Path, *, omit: str = "") -> None:
    reference = root / "reference"
    reference.mkdir(exist_ok=True)
    cat = load_docs_project().reference.category("browser-apis")
    assert cat is not None
    lines = [f'<h3 id="{entry.anchor}"><code>{entry.key}</code></h3>' for entry in cat.entries]
    (reference / "browser-apis.md").write_text(
        "\n".join(line for line in lines if not omit or omit not in line),
        encoding="utf-8",
    )


def test_full_suite_passes_on_the_real_build() -> None:
    # The strongest check: build the actual docs site and run every guard. The
    # suite must produce no errors (warnings are allowed).
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "site"
        outcome = build_site(output_dir=out, search=False, minify=False)
        assert outcome.failed == 0
        results, _ok = run_guards(make_context(out, config=default_config))

    errors = [r for r in results if r.severity is Severity.ERROR]
    assert errors == [], format_report(results)


def test_nav_guard_checks_resolved_pages_against_the_build(
    tmp_path: Path,
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "page.md").write_text("# Page\n", encoding="utf-8")
    nav_path = content / "_nav.yml"
    nav_path.write_text(
        "areas:\n  - label: Docs\n    items:\n      - { title: Page, path: /page/ }\n",
        encoding="utf-8",
    )
    build = tmp_path / "build"
    build.mkdir()
    ctx = GuardContext(
        content_dir=content,
        examples_dir=tmp_path,
        nav_path=nav_path,
        static_dir=tmp_path,
        repo_root=tmp_path,
        site_index=SiteIndex(build),
    )

    results = list(nav.check(ctx))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "/page/" in results[0].message


@pytest.mark.parametrize("source", ["reference", "releases"])
def test_nav_guard_requires_sources_for_generated_pages(
    tmp_path: Path,
    source: str,
) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    nav_path = content / "_nav.yml"
    nav_path.write_text(
        "areas:\n  - label: Docs\n    items:\n      - { title: Home, path: / }\n",
        encoding="utf-8",
    )
    build = tmp_path / "build"
    build.mkdir()
    (build / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    generated = build / source
    generated.mkdir()
    (generated / "index.html").write_text(
        f"<h1>{source}</h1>",
        encoding="utf-8",
    )
    ctx = GuardContext(
        content_dir=content,
        examples_dir=tmp_path,
        nav_path=nav_path,
        static_dir=tmp_path,
        repo_root=tmp_path,
        site_index=SiteIndex(build),
    )

    results = list(nav.check(ctx))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert source in results[0].message


def test_fence_validator_flags_unclosed_fence(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_text("# X\n\n```python\nprint(1)\n", encoding="utf-8")
    ctx = GuardContext(
        content_dir=tmp_path,
        examples_dir=tmp_path,
        nav_path=tmp_path / "_nav.yml",
        static_dir=tmp_path,
        repo_root=tmp_path,
    )

    results = list(fence_validator.check(ctx))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "Unclosed code fence" in results[0].message


def test_snippet_path_ignores_escaped_markers_and_checks_both_include_forms(tmp_path: Path) -> None:
    (tmp_path / "inline.py").write_text("inline\n", encoding="utf-8")
    (tmp_path / "block.py").write_text("block\n", encoding="utf-8")
    (tmp_path / "page.md").write_text(
        ';--8<-- "intentionally-missing.py"\n--8<-- "inline.py"\n--8<--\nblock.py\n--8<--\n',
        encoding="utf-8",
    )

    assert list(snippet_path.check(_content_ctx(tmp_path))) == []


def test_snippet_path_reports_missing_active_include(tmp_path: Path) -> None:
    (tmp_path / "page.md").write_text('--8<-- "missing.py"\n', encoding="utf-8")

    results = list(snippet_path.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "missing.py" in results[0].message


def test_component_fence_flags_component_in_python_fence(tmp_path: Path) -> None:
    source = '# Doc\n\n```python\nclass Card(Component):\n    template = """\n      <c-slot />\n    """\n```\n'
    (tmp_path / "page.md").write_text(source, encoding="utf-8")

    results = list(component_fence.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.WARNING
    assert "citry" in results[0].message


def test_component_fence_catches_subclass_via_attr_fallback(tmp_path: Path) -> None:
    # The base is not literally `Component`, so only the template= fallback fires.
    source = '```python\nclass SpecialCard(BaseCard):\n    template = """<div>x</div>"""\n```\n'
    (tmp_path / "p.md").write_text(source, encoding="utf-8")

    assert len(list(component_fence.check(_content_ctx(tmp_path)))) == 1


def test_component_fence_ignores_plain_python_fragments_and_citry_fences(tmp_path: Path) -> None:
    source = (
        "```python\nx = 1\nprint(x)\n```\n\n"  # plain Python, no component
        '```python\ntemplate = """<c-slot />"""\n```\n\n'  # a bare fragment, no class
        "```citry\nclass Card(Component):\n    pass\n```\n"  # already migrated
    )
    (tmp_path / "p.md").write_text(source, encoding="utf-8")

    assert list(component_fence.check(_content_ctx(tmp_path))) == []


def test_frontmatter_flags_unknown_key(tmp_path: Path) -> None:
    # `author` is not a key the page layout reads, so it is almost certainly a
    # typo or a stray line - a warning, not a hard error.
    (tmp_path / "page.md").write_text("---\ntitle: Hi\nauthor: Jane\n---\n# Hi\n", encoding="utf-8")

    results = list(frontmatter.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.WARNING
    assert "author" in results[0].message


def test_frontmatter_flags_unparsable_typed_value(tmp_path: Path) -> None:
    # `boost` is a float; a non-numeric value used to silently fall back to the
    # default, which hides the mistake. The strict guard makes it an error.
    (tmp_path / "page.md").write_text("---\ntitle: Hi\nboost: abc\n---\n# Hi\n", encoding="utf-8")

    results = list(frontmatter.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "boost" in results[0].message
    assert "not a number" in results[0].message


def test_frontmatter_accepts_a_clean_page(tmp_path: Path) -> None:
    source = "---\ntitle: Hi\ndescription: A tidy page\nnoindex: true\nsearchable: false\nboost: 2.5\n---\n# Hi\n"
    (tmp_path / "page.md").write_text(source, encoding="utf-8")

    assert list(frontmatter.check(_content_ctx(tmp_path))) == []


def test_frontmatter_flags_unknown_layout(tmp_path: Path) -> None:
    (tmp_path / "page.md").write_text(
        "---\ntitle: Hi\nlayout: dashboard\n---\n# Hi\n",
        encoding="utf-8",
    )

    results = list(frontmatter.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "not a known layout" in results[0].message


def test_frontmatter_defers_dated_blog_posts_to_blog_guard(tmp_path: Path) -> None:
    post_dir = tmp_path / "blog"
    post_dir.mkdir()
    (post_dir / "2026-07-27-post.md").write_text(
        "---\ntitle: Post\ndate: 2026-07-27T09:00:00+02:00\nauthor: Maintainers\n---\nBody.\n",
        encoding="utf-8",
    )

    assert list(frontmatter.check(_content_ctx(tmp_path))) == []


def test_blog_guard_reports_source_and_line(tmp_path: Path) -> None:
    post_dir = tmp_path / "blog"
    post_dir.mkdir()
    (post_dir / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (post_dir / "2026-07-27-post.md").write_text(
        "---\ntitle: Post\ndescription: Summary.\ndate: tomorrow\nauthor: Maintainers\n---\nBody.\n",
        encoding="utf-8",
    )

    results = list(blog.check(_content_ctx(tmp_path)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert results[0].source == "blog/2026-07-27-post.md"
    assert results[0].line == 4


def test_blog_feed_guard_requires_feed_for_published_posts(tmp_path: Path) -> None:
    post_dir = tmp_path / "blog"
    post_dir.mkdir()
    (post_dir / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (post_dir / "2026-07-27-post.md").write_text(
        "---\ntitle: Post\ndescription: Summary.\ndate: 2026-07-27T09:00:00+02:00\nauthor: Maintainers\n---\nBody.\n",
        encoding="utf-8",
    )
    build_dir = tmp_path / "site"
    build_dir.mkdir()

    results = list(blog_feed.check(_index_ctx(tmp_path, build_dir)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "missing" in results[0].message


def test_builtin_tags_guard_accepts_complete_authored_page(tmp_path: Path) -> None:
    _write_builtin_tags_page(tmp_path)

    assert list(builtin_tags.check(_content_ctx(tmp_path))) == []


def test_builtin_tags_guard_reports_a_missing_tag(tmp_path: Path) -> None:
    _write_builtin_tags_page(tmp_path, omit='id="c-slot"')

    results = list(builtin_tags.check(_content_ctx(tmp_path)))

    assert any("#c-slot" in result.message for result in results)


def test_authored_reference_guard_accepts_declared_anchors(
    tmp_path: Path,
) -> None:
    _write_browser_api_page(tmp_path)

    assert list(authored_reference.check(_content_ctx(tmp_path))) == []


def test_authored_reference_guard_reports_a_missing_entry(
    tmp_path: Path,
) -> None:
    _write_browser_api_page(tmp_path, omit='id="state"')

    results = list(authored_reference.check(_content_ctx(tmp_path)))

    assert any("#state" in result.message for result in results)


def test_internal_link_flags_broken_and_accepts_valid(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    body = '<a href="/ok/">ok</a><a href="/gone/">gone</a>'
    (build / "index.html").write_text(_DOC.format(body=body), encoding="utf-8")
    (build / "ok").mkdir()
    (build / "ok" / "index.html").write_text(_DOC.format(body="ok"), encoding="utf-8")

    errors = [r for r in internal_link.check(_index_ctx(tmp_path, build)) if r.severity is Severity.ERROR]

    assert len(errors) == 1
    assert "/gone/" in errors[0].message


def test_link_and_anchor_guards_strip_the_deployment_base_path(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    body = '<a href="/citry/ok/#target">ok</a><a href="/citry/gone/">gone</a>'
    (build / "index.html").write_text(_DOC.format(body=body), encoding="utf-8")
    (build / "ok").mkdir()
    (build / "ok" / "index.html").write_text(_DOC.format(body='<h2 id="target">Target</h2>'), encoding="utf-8")
    context = _index_ctx(tmp_path, build)
    context.base_path = "/citry"

    link_errors = [result for result in internal_link.check(context) if result.severity is Severity.ERROR]
    anchor_warnings = list(anchor.check(context))

    assert len(link_errors) == 1
    assert "/citry/gone/" in link_errors[0].message
    assert anchor_warnings == []


def test_asset_guard_uses_the_configured_pagefind_directory(tmp_path: Path) -> None:
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
    build = tmp_path / "site"
    build.mkdir()
    body = '<script src="/custom-search/pagefind.js"></script><script src="/pagefind/pagefind.js"></script>'
    (build / "index.html").write_text(_DOC.format(body=body), encoding="utf-8")
    context = _index_ctx(tmp_path, build)
    context.project = project

    errors = [result for result in asset.check(context) if result.severity is Severity.ERROR]

    assert len(errors) == 1
    assert "/pagefind/pagefind.js" in errors[0].message


def test_single_h1_flags_pages_without_exactly_one(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    (build / "two").mkdir()
    (build / "two" / "index.html").write_text(_DOC.format(body="<h1>A</h1><h1>B</h1>"), encoding="utf-8")
    (build / "one").mkdir()
    (build / "one" / "index.html").write_text(_DOC.format(body="<h1>Only</h1>"), encoding="utf-8")

    warnings = list(single_h1.check(_index_ctx(tmp_path, build)))

    assert len(warnings) == 1
    assert "two/index.html" in (warnings[0].source or "")


def test_single_h1_flags_a_blog_post_heading_expanded_from_a_snippet(tmp_path: Path) -> None:
    content = tmp_path / "content"
    blog_dir = content / "blog"
    blog_dir.mkdir(parents=True)
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Blog\n    source: blog\n    scope: site\n    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    (blog_dir / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (blog_dir / "2026-07-27-snippet-heading.md").write_text(
        "---\n"
        "title: Snippet heading\n"
        "description: A rendered-heading guard regression.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "---\n\n"
        '--8<-- "included-heading.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "included-heading.md").write_text("# Included heading\n", encoding="utf-8")
    output = tmp_path / "site"
    config = DocsConfig(
        base_dir=tmp_path,
        content_dir=content,
        site_dir=output,
        repo_root=tmp_path,
        settings_config=default_config.settings_config,
        reference_config=default_config.reference_config,
        ui_library_config=default_config.ui_library_config,
        redirects_config=default_config.redirects_config,
        versions_config=default_config.versions_config,
        people_sources_config=default_config.people_sources_config,
    )

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)
    warnings = list(single_h1.check(make_context(output, config=config)))

    assert outcome.failed == 0
    assert len(warnings) == 1
    assert "blog/snippet-heading/index.html" in (warnings[0].source or "")
    assert "2 <h1>" in warnings[0].message


def test_json_ld_flags_malformed_block(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    body = '<script type="application/ld+json">{ not valid json }</script>'
    (build / "index.html").write_text(_DOC.format(body=body), encoding="utf-8")

    errors = [r for r in json_ld.check(_index_ctx(tmp_path, build)) if r.severity is Severity.ERROR]

    assert len(errors) == 1
    assert "Malformed JSON-LD" in errors[0].message


def test_json_ld_requires_blogposting_on_blog_post_pages(tmp_path: Path) -> None:
    build = tmp_path / "site" / "blog" / "post"
    build.mkdir(parents=True)
    (build / "index.html").write_text(
        _DOC.format(
            body='<script type="application/ld+json">{"@context":"https://schema.org","@type":"TechArticle","headline":"Post"}</script>'
        ),
        encoding="utf-8",
    )

    errors = [
        result
        for result in json_ld.check(_index_ctx(tmp_path, tmp_path / "site"))
        if result.severity is Severity.ERROR
    ]

    assert any("exactly one BlogPosting" in result.message for result in errors)
    assert any("must not emit TechArticle" in result.message for result in errors)


def test_redirect_target_flags_dead_stub(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    (build / "old").mkdir()
    stub = '<html><head><meta http-equiv="refresh" content="0; url=/gone/"></head><body></body></html>'
    (build / "old" / "index.html").write_text(stub, encoding="utf-8")

    errors = [r for r in redirect_target.check(_index_ctx(tmp_path, build)) if r.severity is Severity.ERROR]

    assert len(errors) == 1
    assert "/gone/" in errors[0].message


def test_api_symbols_pass_on_the_real_categories() -> None:
    # Every documented symbol resolves and every public export is covered, so the
    # guard (which reads the categories + package, not the build) finds nothing.
    ctx = GuardContext(
        content_dir=Path(),
        examples_dir=Path(),
        nav_path=Path("x"),
        static_dir=Path(),
        repo_root=Path(),
    )
    assert list(api_symbols.check(ctx)) == []


def test_run_guards_reports_a_crashing_guard() -> None:
    def boom(_ctx: GuardContext) -> Iterator[GuardResult]:
        raise ValueError("kaboom")
        yield  # unreachable; makes this a generator

    ctx = GuardContext(
        content_dir=Path(),
        examples_dir=Path(),
        nav_path=Path("x"),
        static_dir=Path(),
        repo_root=Path(),
    )

    results, ok = run_guards(ctx, guards=[boom])

    assert not ok
    assert any(r.severity is Severity.ERROR and "crash" in r.message.lower() for r in results)


def test_format_report_handles_empty() -> None:
    assert "passed" in format_report([])


def test_example_contract_flags_missing_test_file(tmp_path: Path) -> None:
    # An example dir that follows the contract - both files present and a page
    # class registered - but ships no test_example_*.py must be flagged.
    example = tmp_path / "widget"
    example.mkdir()
    (example / "component.py").write_text("", encoding="utf-8")
    (example / "page.py").write_text("", encoding="utf-8")
    recipes = tmp_path / "examples"
    recipes.mkdir()
    (recipes / "widget.md").write_text(
        '<c-example name="widget" />\n',
        encoding="utf-8",
    )
    # Any registered example's page class satisfies the "has a *Page" check, so
    # only the missing-test-file check can fire here.
    page_cls = get_example_registry()["card"].page_cls
    registry = {"widget": ExampleInfo(name="widget", page_cls=page_cls, example_dir=example)}

    results = list(example_contract.check(_example_contract_ctx(tmp_path, registry)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "test_example" in results[0].message


def test_example_contract_accepts_an_example_with_a_test_file(tmp_path: Path) -> None:
    # The same example, now shipping a test_example_*.py, satisfies the contract.
    example = tmp_path / "widget"
    example.mkdir()
    (example / "component.py").write_text("", encoding="utf-8")
    (example / "page.py").write_text("", encoding="utf-8")
    (example / "test_example_widget.py").write_text("", encoding="utf-8")
    recipes = tmp_path / "examples"
    recipes.mkdir()
    (recipes / "widget.md").write_text(
        '<c-example name="widget" />\n',
        encoding="utf-8",
    )
    page_cls = get_example_registry()["card"].page_cls
    registry = {"widget": ExampleInfo(name="widget", page_cls=page_cls, example_dir=example)}

    assert list(example_contract.check(_example_contract_ctx(tmp_path, registry))) == []


def test_example_contract_rejects_a_second_recipe_embedding(tmp_path: Path) -> None:
    example = tmp_path / "widget"
    example.mkdir()
    (example / "component.py").write_text("", encoding="utf-8")
    (example / "page.py").write_text("", encoding="utf-8")
    (example / "test_example_widget.py").write_text("", encoding="utf-8")
    recipes = tmp_path / "examples"
    recipes.mkdir()
    directive = '<c-example name="widget" />\n'
    (recipes / "widget.md").write_text(directive, encoding="utf-8")
    (recipes / "duplicate.md").write_text(directive, encoding="utf-8")
    page_cls = get_example_registry()["card"].page_cls
    registry = {
        "widget": ExampleInfo(
            name="widget",
            page_cls=page_cls,
            example_dir=example,
        )
    }

    results = list(example_contract.check(_example_contract_ctx(tmp_path, registry)))

    assert any("canonical recipe" in result.message for result in results)


def test_example_contract_flags_colliding_public_slugs(tmp_path: Path) -> None:
    page_cls = get_example_registry()["card"].page_cls
    registry: dict[str, ExampleInfo] = {}
    for name in ("foo_bar", "foo-bar"):
        example = tmp_path / name
        example.mkdir()
        (example / "component.py").write_text("", encoding="utf-8")
        (example / "page.py").write_text("", encoding="utf-8")
        (example / f"test_example_{name}.py").write_text("", encoding="utf-8")
        registry[name] = ExampleInfo(
            name=name,
            page_cls=page_cls,
            example_dir=example,
        )

    recipes = tmp_path / "examples"
    recipes.mkdir()
    (recipes / "foo-bar.md").write_text(
        '<c-example name="foo_bar" />\n',
        encoding="utf-8",
    )

    results = list(example_contract.check(_example_contract_ctx(tmp_path, registry)))

    assert any("share public slug" in result.message for result in results)


def test_rendered_markdown_guard_catches_a_wrapper_missing_markdown_attribute(tmp_path: Path) -> None:
    """A block the markdown pass skipped shows source to the reader; the build must fail."""
    build = tmp_path / "site"
    build.mkdir()
    (build / "index.html").write_text(
        "<html><body><article>"
        "<div><h3>Real heading</h3><p>Rendered fine.</p></div>"
        "<div>### Choose Citry when</div>"
        "<div>[Compatibility](/about/compatibility/)</div>"
        "</article></body></html>",
        encoding="utf-8",
    )

    results = list(rendered_markdown.check(_index_ctx(tmp_path, build)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "### Choose Citry when" in results[0].message
    assert "[Compatibility](/about/compatibility/)" in results[0].message


def test_rendered_markdown_guard_ignores_markdown_shown_on_purpose(tmp_path: Path) -> None:
    """Documenting Markdown inside code or a heading element is not a leak."""
    build = tmp_path / "site"
    build.mkdir()
    (build / "index.html").write_text(
        "<html><body><article>"
        "<pre><code>### A heading example\n[a link](/x/)</code></pre>"
        "<p>Write <code>[text](url)</code> to make a link.</p>"
        "<h3>An ordinary rendered heading</h3>"
        "<p>A sentence mentioning C# and a #hashtag.</p>"
        "</article></body></html>",
        encoding="utf-8",
    )

    assert list(rendered_markdown.check(_index_ctx(tmp_path, build))) == []


def test_rendered_css_guard_catches_a_custom_property_glued_to_its_value(tmp_path: Path) -> None:
    """`var(--x)0%` is invalid, and the browser drops the whole declaration."""
    build = tmp_path / "site"
    build.mkdir()
    (build / "index.html").write_text(
        "<html><body><style>"
        ".a{background:linear-gradient(90deg,var(--bg)0%,transparent)}"
        ".b{grid-template-columns:var(--rail)minmax(0,1fr)}"
        "</style></body></html>",
        encoding="utf-8",
    )

    results = list(rendered_css.check(_index_ctx(tmp_path, build)))

    assert len(results) == 1
    assert results[0].severity is Severity.ERROR
    assert "var(--bg)0%" in results[0].message


def test_rendered_css_guard_accepts_correctly_spaced_values(tmp_path: Path) -> None:
    """A space after the custom property is all that is required."""
    build = tmp_path / "site"
    build.mkdir()
    (build / "index.html").write_text(
        "<html><body><style>"
        ".a{background:linear-gradient(90deg, var(--bg) 0%, transparent)}"
        ".b{color:var(--fg);margin:var(--gap)}"
        "</style></body></html>",
        encoding="utf-8",
    )

    assert list(rendered_css.check(_index_ctx(tmp_path, build))) == []
