"""Authoring, projection, and build contracts for inline live-code examples."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from lxml import html as lxml_html

from citry._alpine_csp import classify_alpine_csp
from citry.analysis import browser_expressions
from citry_core.template_parser import parse_template
from docs_site._internal.components.live_code import LiveCode
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.guards import live_code as live_code_guard
from docs_site._internal.guards.base import GuardContext
from docs_site._internal.live_code import LiveCodeValidationError, load_live_source
from docs_site._internal.pipeline import render_page

_LIVE_SNIPPETS = Path(__file__).parents[1] / "live_snippets"


def test_published_live_templates_are_strict_csp_compatible() -> None:
    """Executable docs examples keep Alpine attributes inside the pinned subset."""
    issues: list[str] = []
    for path in sorted(_LIVE_SNIPPETS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Name) and target.id == "template" for target in targets):
                continue
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for expression in browser_expressions(parse_template(value.value)):
                result = classify_alpine_csp(expression)
                if result.outcome == "incompatible":
                    issues.append(f"{path.name}:{node.lineno} {expression.attribute}: {result.detail}")

    assert issues == []


def _docs_config(root: Path) -> DocsConfig:
    """Use temporary runtime paths with the repository's declarations."""
    return DocsConfig(
        repo_root=root,
        base_dir=root / "docs_site",
        versions_config=default_config.versions_config,
        settings_config=default_config.settings_config,
        reference_config=default_config.reference_config,
        ui_library_config=default_config.ui_library_config,
        redirects_config=default_config.redirects_config,
        people_sources_config=default_config.people_sources_config,
    )


def _snippet_path(root: Path, source: str | bytes, name: str = "sample.py") -> str:
    relative = Path("docs_site/live_snippets") / name
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(source, bytes):
        target.write_bytes(source)
    else:
        target.write_text(source, encoding="utf-8", newline="")
    return relative.as_posix()


def _component_snippet_path(root: Path, source: str, name: str = "sample.py") -> str:
    relative = Path("packages/py/citry_ui/citry_ui/components/ctabs/snippets") / name
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8", newline="")
    return relative.as_posix()


def _guard_context(root: Path, markdown: str) -> GuardContext:
    content = root / "content"
    content.mkdir(exist_ok=True)
    (content / "page.md").write_text(markdown, encoding="utf-8")
    return GuardContext(
        content_dir=content,
        examples_dir=root / "examples",
        nav_path=content / "_nav.yml",
        static_dir=root / "static",
        repo_root=root,
    )


def test_live_code_owns_its_dom_as_a_citry_template() -> None:
    assert "<figure" in LiveCode.template
    assert "<c-LiveActivationControls" in LiveCode.template
    assert "<c-LiveWorkspace" in LiveCode.template
    assert "{{ block }}" not in LiveCode.template


def test_live_code_is_static_first_exact_and_source_projected(tmp_path: Path) -> None:
    source = "\nfrom markupsafe import Markup\nvalue = 'héllo <>&'\nMarkup(f'<p>{value}</p>')"
    path = _snippet_path(tmp_path, source)
    cfg = _docs_config(tmp_path)
    result = render_page(
        f'<c-live-code path="{path}" title="Escaped &amp; exact" />',
        config=cfg,
    )

    tree = lxml_html.fromstring(result.html)
    [highlight] = tree.xpath(
        "//*[@data-live-static]//*[contains(concat(' ', normalize-space(@class), ' '), ' highlight ')]"
    )

    assert highlight.text_content() == source
    assert "data-citry-live-code" in result.html
    assert "/static/playground/live_code.css" in result.html
    assert "/static/playground/live_code.js" in result.html
    assert "live_code_runtime.js" not in result.html
    assert 'class="citry-live-code__sr-only"' in result.html
    assert "### Escaped &amp; exact" in result.markdown_body
    assert source in result.markdown_body
    assert "docs-live-code:" not in result.markdown_body


def test_live_code_assets_are_conditional_and_historical_pages_are_static(tmp_path: Path) -> None:
    path = _snippet_path(tmp_path, "html = '<p>hello</p>'\nhtml\n")
    cfg = _docs_config(tmp_path)

    ordinary = render_page("# Ordinary", config=cfg).html
    literal_hook = render_page(
        '```html\n<figure class="citry-live-code" data-citry-live-code></figure>\n```',
        config=cfg,
    ).html
    historical = render_page(
        f'<c-live-code path="{path}" title="Hello" full_height />',
        config=cfg,
        version_prefix="/v/0.3.0/",
    ).html

    assert "live_code.css" not in ordinary
    assert "live_code.js" not in ordinary
    assert "live_code.css" not in literal_hook
    assert "live_code.js" not in literal_hook
    assert "data-citry-live-code" not in historical
    assert "Try live" not in historical
    assert "live_code.css" in historical
    assert "live_code.js" not in historical
    assert "hello" in historical
    assert "citry-live-code--full-height" in historical
    assert 'href="/playground/"' in historical
    assert "Open the current playground" in historical


def test_multiple_live_code_blocks_have_independent_accessible_ids(tmp_path: Path) -> None:
    path = _snippet_path(tmp_path, "html = '<p>hello</p>'\nhtml\n")
    cfg = _docs_config(tmp_path)
    directive = f'<c-live-code path="{path}" title="Hello" />'

    tree = lxml_html.fromstring(render_page(f"{directive}\n\n{directive}", config=cfg).html)
    tab_ids = tree.xpath("//*[@data-live-tab]/@id")
    controls = tree.xpath("//*[@data-live-tab]/@aria-controls")

    assert len(tab_ids) == 4
    assert len(tab_ids) == len(set(tab_ids))
    assert len(controls) == len(set(controls))
    assert all(tree.xpath(f'//*[@id="{panel_id}"]') for panel_id in controls)


def test_live_code_full_height_is_opt_in(tmp_path: Path) -> None:
    path = _snippet_path(tmp_path, "html = '<p>hello</p>'\nhtml\n")
    cfg = _docs_config(tmp_path)
    default = f'<c-live-code path="{path}" title="Default height" />'
    full_height = f'<c-live-code path="{path}" title="Full height" full_height />'

    tree = lxml_html.fromstring(render_page(f"{default}\n\n{full_height}", config=cfg).html)
    figures = tree.xpath("//figure[contains(@class, 'citry-live-code')]")

    assert len(figures) == 2
    assert "citry-live-code--full-height" not in figures[0].classes
    assert "citry-live-code--full-height" in figures[1].classes
    assert list(live_code_guard.check(_guard_context(tmp_path, full_height))) == []


def test_static_component_snippet_uses_live_code_presentation_without_activation(tmp_path: Path) -> None:
    source = "import citry_ui\nfrom citry_ui import CTabs\nCTabs\n"
    path = _component_snippet_path(tmp_path, source)
    directive = f'<c-live-code path="{path}" title="Tabs" static />'
    cfg = _docs_config(tmp_path)

    result = render_page(directive, config=cfg)

    assert source in result.markdown_body
    assert "data-citry-live-code" not in result.html
    assert "Try live" not in result.html
    assert "Open the current playground" not in result.html
    assert "data-live-workspace" not in result.html
    assert "live_code.css" in result.html
    assert "live_code.js" not in result.html
    assert list(live_code_guard.check(_guard_context(tmp_path, directive))) == []


def test_local_ui_runtime_activates_an_authored_static_component_snippet(tmp_path: Path) -> None:
    source = "import citry_ui\nfrom citry_ui import CTabs\nCTabs\n"
    path = _component_snippet_path(tmp_path, source)
    directive = f'<c-live-code path="{path}" title="Tabs" static />'
    cfg = _docs_config(tmp_path)

    result = render_page(directive, config=cfg, allow_citry_ui=True)

    assert "data-citry-live-code" in result.html
    assert "Try live" in result.html
    assert "data-live-workspace" in result.html


def test_component_snippet_requires_static_mode_and_exact_location(tmp_path: Path) -> None:
    source = "import citry_ui\ncitry_ui\n"
    path = _component_snippet_path(tmp_path, source)
    wrong_location = tmp_path / "packages/py/citry_ui/citry_ui/components/ctabs/demo.py"
    wrong_location.parent.mkdir(parents=True, exist_ok=True)
    wrong_location.write_text(source, encoding="utf-8")

    with pytest.raises(LiveCodeValidationError, match="unsupported import"):
        load_live_source(path, repo_root=tmp_path, title="Tabs")
    assert (
        load_live_source(
            path,
            repo_root=tmp_path,
            title="Tabs",
            allow_citry_ui=True,
        )
        == source
    )
    with pytest.raises(LiveCodeValidationError, match="must be inside"):
        load_live_source(
            wrong_location.relative_to(tmp_path).as_posix(),
            repo_root=tmp_path,
            title="Tabs",
            static=True,
        )
    docs_path = _snippet_path(tmp_path, source, "citry-ui.py")
    with pytest.raises(LiveCodeValidationError, match="must be inside"):
        load_live_source(docs_path, repo_root=tmp_path, title="Tabs", static=True)


def test_live_code_projection_fence_exceeds_source_backtick_runs(tmp_path: Path) -> None:
    source = 'html = """\n````\n"""\nhtml\n'
    path = _snippet_path(tmp_path, source)
    cfg = _docs_config(tmp_path)

    body = render_page(f'<c-live-code path="{path}" title="Ticks" />', config=cfg).markdown_body

    assert "`````citry\n" in body
    assert body.rstrip().endswith("`````")


@pytest.mark.parametrize(
    ("source", "problem"),
    [
        ("await later()\n", "top-level await"),
        ("import definitely_not_in_pyodide\n'<p>x</p>'\n", "unsupported import"),
        ("from .thing import value\nvalue\n", "relative imports"),
        ("return 1\n", "invalid Python syntax"),
        ("try:\n    pass\nexcept* ValueError:\n    pass\n'<p>x</p>'\n", "invalid Python syntax"),
    ],
)
def test_live_source_rejects_invalid_modules(tmp_path: Path, source: str, problem: str) -> None:
    path = _snippet_path(tmp_path, source)

    with pytest.raises(LiveCodeValidationError, match=problem):
        load_live_source(path, repo_root=tmp_path, title="Sample")


@pytest.mark.parametrize(
    "source",
    [
        "",
        '"module docs"\n',
        "value = '<p>x</p>'\n",
    ],
)
def test_live_source_accepts_modules_without_a_preview_value(tmp_path: Path, source: str) -> None:
    path = _snippet_path(tmp_path, source)

    assert load_live_source(path, repo_root=tmp_path, title="Sample") == source


def test_incomplete_live_source_remains_static_and_passes_the_guard(tmp_path: Path) -> None:
    source = "value = '<p>complete me</p>'\n"
    path = _snippet_path(tmp_path, source)
    directive = f'<c-live-code path="{path}" title="Incomplete example" />'
    cfg = _docs_config(tmp_path)

    result = render_page(directive, config=cfg)
    tree = lxml_html.fromstring(result.html)
    [highlight] = tree.xpath("//*[@data-live-static]//*[contains(@class, 'highlight')]")

    assert highlight.text_content() == source
    assert source.rstrip() in result.markdown_body
    assert list(live_code_guard.check(_guard_context(tmp_path, directive))) == []


def test_nested_async_is_allowed_but_crlf_and_invalid_utf8_are_not(tmp_path: Path) -> None:
    nested = _snippet_path(
        tmp_path,
        "async def later():\n    await something()\n\n'<p>x</p>'\n",
        "nested.py",
    )
    crlf = _snippet_path(tmp_path, b"value = '<p>x</p>'\r\nvalue\r\n", "crlf.py")
    invalid = _snippet_path(tmp_path, b"'\xff'", "invalid.py")

    assert "await something" in load_live_source(nested, repo_root=tmp_path, title="Nested")
    with pytest.raises(LiveCodeValidationError, match="LF line endings"):
        load_live_source(crlf, repo_root=tmp_path, title="CRLF")
    with pytest.raises(LiveCodeValidationError, match="valid UTF-8"):
        load_live_source(invalid, repo_root=tmp_path, title="Encoding")


def test_live_source_size_boundary_and_repository_path_boundary(tmp_path: Path) -> None:
    tail = "\nhtml = '<p>x</p>'\nhtml"
    source = "#" + "x" * (64 * 1024 - len(tail.encode()) - 1) + tail
    exact = _snippet_path(tmp_path, source, "exact.py")
    large = _snippet_path(tmp_path, source + "x", "large.py")
    elsewhere = tmp_path / "docs_site" / "examples" / "elsewhere.py"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text("html = '<p>elsewhere</p>'\nhtml\n", encoding="utf-8")
    outside = tmp_path / "packages" / "outside.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("'<p>x</p>'\n", encoding="utf-8")

    assert len(load_live_source(exact, repo_root=tmp_path, title="Exact").encode()) == 64 * 1024
    assert (
        load_live_source(
            "docs_site/examples/elsewhere.py",
            repo_root=tmp_path,
            title="Elsewhere",
        )
        == "html = '<p>elsewhere</p>'\nhtml\n"
    )
    with pytest.raises(LiveCodeValidationError, match="64 KiB"):
        load_live_source(large, repo_root=tmp_path, title="Large")
    assert load_live_source("packages/outside.py", repo_root=tmp_path, title="Outside") == "'<p>x</p>'\n"


def test_live_source_rejects_path_tricks_and_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    outside.write_text("'<p>x</p>'\n", encoding="utf-8")
    snippets = tmp_path / "docs_site" / "live_snippets"
    snippets.mkdir(parents=True)
    link = snippets / "linked.py"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    for path in (
        "/docs_site/live_snippets/linked.py",
        "docs_site/live_snippets/../linked.py",
        r"docs_site\live_snippets\linked.py",
        "docs_site/live_snippets/./linked.py",
        "docs_site/live_snippets/linked.txt",
        "docs_site/live_snippets/linked.py://bad",
    ):
        with pytest.raises(LiveCodeValidationError):
            load_live_source(path, repo_root=tmp_path, title="Path")
    with pytest.raises(LiveCodeValidationError, match="outside"):
        load_live_source("docs_site/live_snippets/linked.py", repo_root=tmp_path, title="Link")


def test_guard_reports_original_markdown_line_and_ignores_code_regions(tmp_path: Path) -> None:
    path = _snippet_path(tmp_path, "html = '<p>hello</p>'\nhtml\n")
    directive = f'<c-live-code path="{path}" title="" />'
    markdown = f"```html\n{directive}\n```\n\nInline `{directive}`.\n\n<!-- {directive} -->\n\n{directive}\n"

    results = list(live_code_guard.check(_guard_context(tmp_path, markdown)))

    assert len(results) == 1
    assert results[0].source == "page.md"
    assert results[0].line == 9
    assert "title must not be blank" in results[0].message


@pytest.mark.parametrize(
    ("directive", "problem"),
    [
        ('<c-live-code path="x.py" title="X">', "self-closing"),
        ('<C-LIVE-CODE path="x.py" title="X" />', "lowercase"),
        ('<c-live-code path="x.py" />', "missing title"),
        ('<c-live-code path="x.py" title="X" extra="y" />', "unsupported extra"),
        ('<c-live-code path="x.py" path="y.py" title="X" />', "repeated"),
        ('<c-live-code path="x.py" title="X" full-height />', "malformed"),
        ('<c-live-code path="x.py" title="X" full_height full_height />', "repeated"),
        ('<c-live-code path="x.py" title="X" full_height="false" />', "value-less"),
        ('<c-live-code path="x.py" title="X" static static />', "repeated"),
        ('<c-live-code path="x.py" title="X" static="true" />', "value-less"),
        ('<c-live-code path={{ value }} title="X" />', "malformed"),
    ],
)
def test_guard_rejects_malformed_directives(tmp_path: Path, directive: str, problem: str) -> None:
    [result] = live_code_guard.check(_guard_context(tmp_path, directive))

    assert problem in result.message
    assert result.line == 1
