"""Tests for Pass 0 (fence protection) and Pass 1 (custom ``<c-*>`` tag expansion)."""

from __future__ import annotations

import html as html_module
import re
from pathlib import Path

from docs_site._internal.config import DocsConfig
from docs_site._internal.fence_protection import protect_fences, restore_protected_code
from docs_site._internal.pipeline import render_content, render_page


def test_fenced_block_wrapped_in_raw() -> None:
    out = protect_fences('before\n```python\n<c-if cond="x">hi</c-if>\n```\nafter')
    assert "<c-raw>" in out
    assert "</c-raw>" in out
    # The raw wrapper opens before the fence.
    assert out.index("<c-raw>") < out.index("```python")


def test_inline_code_with_citry_syntax_wrapped() -> None:
    assert "<c-raw>`<c-if>`</c-raw>" in protect_fences("Use `<c-if>` for conditionals.")
    assert "<c-raw>`{{ x }}`</c-raw>" in protect_fences("Write `{{ x }}` to interpolate.")


def test_inline_code_without_citry_syntax_untouched() -> None:
    assert protect_fences("Call `render` then `serialize`.") == "Call `render` then `serialize`."


def test_indented_code_with_citry_syntax_renders_as_literal_code() -> None:
    html = render_page('    <c-if cond="x">hi</c-if>\n').html

    assert "&lt;c-if" in html
    assert "hi" in html


def test_events_bindings_in_code_are_armored_then_restored() -> None:
    source = '```html\n<button @c-click="save" :c-query="refresh">Save</button>\n```'
    protected = protect_fences(source)

    assert '@c-click="save"' not in protected
    assert ':c-query="refresh"' not in protected
    assert restore_protected_code(protected).replace("<c-raw>\n", "").replace("\n</c-raw>", "") == source


def test_events_bindings_render_as_literal_fenced_code() -> None:
    source = '```html\n<button @c-click="save" :c-query="refresh">Save</button>\n```'

    html = render_page(source).html
    text = html_module.unescape(re.sub(r"<[^>]+>", "", html))

    assert '@c-click="save"' in text
    assert ':c-query="refresh"' in text
    assert "data-cev-" not in html


def test_version_global_resolves_in_content() -> None:
    # `version` is a Citry template global, so content can write {{ version }}.
    from citry import citry as citry_instance

    citry_instance.template_globals["version"] = "1.2.3"
    try:
        out = render_content("v={{ version }}", context={"current_path": ""})
    finally:
        citry_instance.template_globals.pop("version", None)
    assert out == "v=1.2.3"


def test_expression_expands_and_code_is_protected() -> None:
    from citry import citry as citry_instance

    citry_instance.template_globals["version"] = "9.9.9"
    try:
        md = '# Page\n\nVersion {{ version }} here.\n\n```html\n<c-if cond="x">hi</c-if>\n```\n'
        html = render_page(md).html
    finally:
        citry_instance.template_globals.pop("version", None)
    # The expression expanded outside the fence.
    assert "9.9.9" in html
    assert "Version " in html
    # The code example survived as a (highlighted) code block instead of being
    # executed: it shows in the block with its angle brackets escaped.
    match = re.search(r'<div class="highlight">.*?</div>', html, re.DOTALL)
    assert match
    block = match.group(0)
    assert "&lt;" in block  # angle brackets escaped, not rendered as a tag
    assert "c-if" in block


def test_include_file_tag(tmp_path: Path) -> None:
    (tmp_path / "snippet.py").write_text("greeting = 'hi'\n", encoding="utf-8")

    html = render_page(
        '<c-include-file path="snippet.py" />',
        config=DocsConfig(repo_root=tmp_path),
    ).html

    assert "greeting" in html
    assert 'class="highlight"' in html  # rendered as a code block
    assert "<c-include-file" not in html  # the tag was expanded


def test_admonition_still_renders_through_pass1() -> None:
    # Pass 1 must preserve markdown's blank lines / indentation so block syntax
    # (here an admonition) still works.
    md = "# T\n\n!!! note\n\n    An admonition body.\n"
    html = render_page(md).html
    assert 'class="admonition note"' in html
    assert "An admonition body." in html


def test_image_tag() -> None:
    html = render_content('<c-image src="/static/img/x.png" alt="A shot" width="400" css_class="rounded" />')
    assert '<img src="/static/img/x.png"' in html
    assert 'alt="A shot"' in html
    assert 'width="400"' in html
    assert 'class="rounded"' in html


def test_image_tag_minimal_has_empty_alt_and_no_optional_attrs() -> None:
    # Only src is required; alt defaults to empty and the optional attrs are omitted.
    html = render_content('<c-image src="/a.png" />')
    assert '<img src="/a.png" alt="" />' in html
    assert "width=" not in html
    assert "class=" not in html


def test_people_tag_renders_the_avatar_grid() -> None:
    # Reads the seeded data/people.yml and renders the UserGrid for the group.
    html = render_content('<c-people group="maintainers" />')
    assert 'class="user-list"' in html
    assert 'href="https://github.com/JuroOravec"' in html
    assert "@JuroOravec" in html
    # Maintainers hide the contribution count (only contributors show it).
    assert "Contributions:" not in html


def test_people_tag_renders_special_thanks_without_count() -> None:
    html = render_content('<c-people group="special_thanks" />')

    assert "@EmilStenstrom" in html
    assert "Contributions:" not in html


def test_people_tag_unknown_group_shows_inline_error() -> None:
    html = render_content('<c-people group="does-not-exist" />')
    assert 'class="docs-error"' in html
    assert "Unknown people group: does-not-exist" in html
