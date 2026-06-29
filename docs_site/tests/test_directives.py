"""Tests for Pass 0 (fence protection) and Pass 1 (directive expansion)."""

from __future__ import annotations

from pathlib import Path

from docs_site.directives import expand_directives
from docs_site.fence_protection import protect_fences
from docs_site.pipeline import render_page


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


def test_expand_version_directive() -> None:
    out = expand_directives("v=<c-version />")
    assert out.startswith("v=")
    assert "<c-version" not in out  # the directive was expanded


def test_directive_expands_and_code_is_protected() -> None:
    import re

    md = '# Page\n\nVersion <c-version /> here.\n\n```html\n<c-if cond="x">hi</c-if>\n```\n'
    html = render_page(md).html
    # The directive expanded (no raw tag left).
    assert "<c-version" not in html
    assert "Version " in html
    # The code example survived as a (highlighted) code block instead of being
    # executed: it shows in the block with its angle brackets escaped.
    match = re.search(r'<div class="highlight">.*?</div>', html, re.DOTALL)
    assert match
    block = match.group(0)
    assert "&lt;" in block  # angle brackets escaped, not rendered as a tag
    assert "c-if" in block


def test_include_file_directive(tmp_path: Path, monkeypatch) -> None:
    import docs_site.directives as directives_mod

    monkeypatch.setattr(directives_mod.default_config, "repo_root", tmp_path)
    (tmp_path / "snippet.py").write_text("greeting = 'hi'\n", encoding="utf-8")

    html = render_page('<c-include-file path="snippet.py" />').html

    assert "greeting" in html
    assert 'class="highlight"' in html  # rendered as a code block
    assert "<c-include-file" not in html  # the directive was expanded


def test_admonition_still_renders_through_pass1() -> None:
    # Pass 1 must preserve markdown's blank lines / indentation so block syntax
    # (here an admonition) still works.
    md = "# T\n\n!!! note\n\n    An admonition body.\n"
    html = render_page(md).html
    assert 'class="admonition note"' in html
    assert "An admonition body." in html
