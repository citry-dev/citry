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


def _note(body: str) -> str:
    """Render one admonition whose body is the given indented lines."""
    return render_page(f"!!! note\n{body}\n", wrap_in_layout=False).html


def test_inline_code_in_an_admonition_is_shown_verbatim() -> None:
    # An admonition body is indented like code but is prose, so its inline
    # code must be protected exactly as in a top-level paragraph.
    html = _note("    Use `<span/>`, `<div>` and `<c-raw>` with <b>bold</b>.")

    assert "<code>&lt;span/&gt;</code>" in html
    assert "<code>&lt;div&gt;</code>" in html
    assert "<code>&lt;c-raw&gt;</code>" in html
    assert "<b>bold</b>" in html


def test_inline_code_in_a_list_continuation_is_shown_verbatim() -> None:
    html = render_page("- item\n    more `<span/>` text\n", wrap_in_layout=False).html

    assert "<code>&lt;span/&gt;</code>" in html


def _code_texts(html: str) -> list[str]:
    """Return the text of every inline ``<code>`` element, whitespace collapsed."""
    return [
        " ".join(html_module.unescape(code).split()) for code in re.findall(r"<code>(.*?)</code>", html, re.DOTALL)
    ]


def test_inline_code_wrapped_across_lines_in_a_paragraph_is_shown_verbatim() -> None:
    # Markdown lets a code span continue on the next line of its paragraph and
    # shows the line break as a space; protecting each line on its own would
    # hand citry half a tag.
    html = render_page('Wrap `<c-Button\n@click="go">` here.\n', wrap_in_layout=False).html

    assert _code_texts(html) == ['<c-Button @click="go">']


def test_inline_code_wrapped_across_lines_in_admonition_and_list_bodies() -> None:
    in_note = _note('    Wrap `<c-Button\n    @click="go">` here.')
    in_list = render_page('- Wrap `<c-Button\n  @click="go">` here.\n', wrap_in_layout=False).html
    deeper = render_page('Wrap `<c-Button\n        @click="go">` here.\n', wrap_in_layout=False).html

    for html in (in_note, in_list, deeper):
        assert _code_texts(html) == ['<c-Button @click="go">']


def test_inline_code_closes_only_at_a_backtick_run_of_the_same_length() -> None:
    # A shorter run inside a double-backtick span is code text, not a closer.
    assert protect_fences("A ``x ` <c-y/>`` z") == "A <c-raw>``x ` <c-y/>``</c-raw> z"
    # An unmatched run is literal and does not swallow the span after it.
    assert protect_fences("A ``` b `{{ c }}` d") == "A ``` b <c-raw>`{{ c }}`</c-raw> d"


def test_inline_code_does_not_cross_a_paragraph_or_block_boundary() -> None:
    # A blank line, a heading, the next list item, and an admonition body's
    # end each close the paragraph, so neither backtick has a partner.
    for source in ("`{{ a\n\nb }}`", "`{{ a\n# b }}`", "- `{{ a\n- b }}`", "!!! note\n    `{{ a\nb }}`"):
        assert protect_fences(source) == source, source
    # A fence also ends the paragraph; only the fence itself is wrapped.
    assert protect_fences("`{{ a\n```\nb }}`") == "`{{ a\n<c-raw>\n```\nb }}`\n</c-raw>"


def test_block_like_lines_inside_a_paragraph_continue_its_code_span() -> None:
    # Markdown starts a list, table, or admonition only after a blank line, so
    # inside a paragraph these lines are more of its text.
    for marker in ("- b", "1. b", "| b", "!!! note b"):
        html = render_page(f"Para `<c-a\n{marker}/>` z\n", wrap_in_layout=False).html
        assert _code_texts(html) == [f"<c-a {marker}/>"], marker


def test_paragraph_that_starts_with_an_inline_tag_still_protects_its_code() -> None:
    # Only a block-level tag or a comment makes a raw HTML block; <b> starts
    # an ordinary paragraph whose code spans Markdown still reads.
    html = render_page('<b>Note:</b> `<c-Button\n@click="go">`\n', wrap_in_layout=False).html

    assert _code_texts(html) == ['<c-Button @click="go">']


def test_lazy_continuation_line_keeps_the_list_item_open() -> None:
    # The second line is indented less than the item body, which Markdown
    # still reads as the item's text, so the fence after it is in the item.
    source = '1. Install:\n  more\n\n    ```html\n    <c-if cond="x">{{ y }}</c-if>\n    ```\n'

    assert "<c-raw>\n    ```html" in protect_fences(source)


def test_backtick_in_a_raw_html_block_does_not_pair_with_a_later_line() -> None:
    # Markdown passes a block that starts with a comment or a block-level tag
    # through as raw HTML, so its backticks open no code span and the <h1>
    # must still render.
    source = "<!-- `\n-->\n<h1>Title</h1>\n`\n"

    assert protect_fences(source) == source
    assert "<h1>Title</h1>" in render_page(source, wrap_in_layout=False).html


def test_backslash_escaped_backtick_does_not_open_a_span() -> None:
    assert protect_fences("A \\` b `{{ c }}`") == "A \\` b <c-raw>`{{ c }}`</c-raw>"


def test_code_nested_in_an_admonition_stays_literal() -> None:
    indented = _note('    Text.\n\n        <c-if cond="x">{{ y }}</c-if>')
    fenced = _note('    ```html\n    <c-if cond="x">{{ y }}</c-if>\n    ```')

    for html in (indented, fenced):
        text = html_module.unescape(re.sub(r"<[^>]+>", "", html))
        assert '<c-if cond="x">{{ y }}</c-if>' in text


def test_horizontal_rule_does_not_hide_the_indented_code_after_it() -> None:
    # `* * *` looks like a list item but is a rule, so the next indented
    # block is still top-level code and must stay literal.
    html = render_page('Para.\n\n* * *\n\n    <c-if cond="x">{{ y }}</c-if>\n', wrap_in_layout=False).html

    text = html_module.unescape(re.sub(r"<[^>]+>", "", html))
    assert '<c-if cond="x">{{ y }}</c-if>' in text


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


def test_include_file_infers_fluent_for_ftl(tmp_path: Path) -> None:
    (tmp_path / "messages.ftl").write_text("hello = Welcome\n", encoding="utf-8")

    html = render_page(
        '<c-include-file path="messages.ftl" />',
        config=DocsConfig(repo_root=tmp_path),
    ).html

    assert '<span class="no">hello</span>' in html


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
