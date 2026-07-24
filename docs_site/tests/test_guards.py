"""Tests for the post-build guard suite."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

from docs_site._internal.build import build_site
from docs_site._internal.config import config as default_config
from docs_site._internal.examples import ExampleInfo, get_example_registry
from docs_site._internal.guards import (
    api_symbols,
    component_fence,
    example_contract,
    fence_validator,
    format_report,
    frontmatter,
    internal_link,
    json_ld,
    make_context,
    redirect_target,
    run_guards,
    single_h1,
    snippet_path,
)
from docs_site._internal.guards.base import GuardContext, GuardResult, Severity
from docs_site._internal.guards.site_index import SiteIndex

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


def test_json_ld_flags_malformed_block(tmp_path: Path) -> None:
    build = tmp_path / "site"
    build.mkdir()
    body = '<script type="application/ld+json">{ not valid json }</script>'
    (build / "index.html").write_text(_DOC.format(body=body), encoding="utf-8")

    errors = [r for r in json_ld.check(_index_ctx(tmp_path, build)) if r.severity is Severity.ERROR]

    assert len(errors) == 1
    assert "Malformed JSON-LD" in errors[0].message


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
    page_cls = get_example_registry()["card"].page_cls
    registry = {"widget": ExampleInfo(name="widget", page_cls=page_cls, example_dir=example)}

    assert list(example_contract.check(_example_contract_ctx(tmp_path, registry))) == []
