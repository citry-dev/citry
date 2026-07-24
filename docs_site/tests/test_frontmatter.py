"""
Tests for front-matter parsing and the derived meta description.

The description follows a three-tier fallback: a front-matter ``description:``,
else the first real paragraph of the body (markdown stripped, length-capped),
else a site-level default. The first two tiers live in ``parse_page`` and are
exercised here; the site-level default is applied at render time and is tested
in ``test_pipeline`` (it needs the config that ``parse_page`` does not have).
"""

from __future__ import annotations

from docs_site._internal.frontmatter import _DESCRIPTION_CAP, parse_page


def test_front_matter_description_wins_over_body() -> None:
    # Tier 1: an explicit front-matter description is used verbatim, even when
    # the body has a paragraph that could have supplied one.
    source = "---\ndescription: Explicit desc.\n---\n\n# T\n\nBody paragraph here.\n"
    assert parse_page(source).description == "Explicit desc."


def test_first_paragraph_used_when_front_matter_absent() -> None:
    # Tier 2: with no front-matter description, the first body paragraph fills in.
    assert parse_page("# Title\n\nPlain intro paragraph.\n").description == "Plain intro paragraph."


def test_first_paragraph_strips_markdown_formatting() -> None:
    # Links, bold, and inline code are reduced to their plain text.
    source = "# T\n\nUse **bold**, a [link](https://ex.com), and `code` in prose.\n"
    assert parse_page(source).description == "Use bold, a link, and code in prose."


def test_first_paragraph_preserves_snake_case_identifiers() -> None:
    # Underscore-stripping must not mangle snake_case names into one word.
    source = "# T\n\nConfigure django_components and my_other_setting.\n"
    assert parse_page(source).description == "Configure django_components and my_other_setting."


def test_first_paragraph_strips_images_badges_and_crossrefs() -> None:
    # A badge link (image wrapped in a link) and a reference cross-ref both
    # reduce to plain text with no leftover markdown punctuation.
    source = "# T\n\n[![badge](img.svg)](https://x) See [Component.render()][Component.render] for details.\n"
    desc = parse_page(source).description
    assert "![" not in desc
    assert "](" not in desc
    assert "][" not in desc
    assert desc == "See Component.render() for details."


def test_first_paragraph_capped_at_word_boundary() -> None:
    # A paragraph longer than the cap is truncated to a whole word plus an
    # ellipsis, so the meta description stays within a search snippet's length.
    long_body = "# T\n\n" + ("word " * 40).strip() + " END.\n"
    desc = parse_page(long_body).description
    assert desc.endswith("...")
    assert len(desc) <= _DESCRIPTION_CAP
    assert desc.startswith("word word word")
    # The trailing partial word is dropped cleanly (no dangling half-word).
    assert " EN..." not in desc


def test_short_first_paragraph_is_not_capped() -> None:
    # A paragraph under the cap is returned whole, without an ellipsis.
    desc = parse_page("# T\n\nA short intro.\n").description
    assert desc == "A short intro."


def test_first_paragraph_skips_leading_admonition() -> None:
    # An admonition block ("!!! note ...") is not prose; the extractor walks past
    # it to the first real paragraph that follows.
    source = '!!! note "Heads up"\n    An admonition body.\n\nThe intro prose after the note.\n'
    assert parse_page(source).description == "The intro prose after the note."


def test_first_paragraph_skips_version_annotation() -> None:
    # A "New in version X" note (a standalone italic line) makes a useless
    # description, so it is skipped in favour of the following prose.
    source = "## Heading\n\n_New in version 0.89_\n\nThe real first paragraph of prose.\n"
    assert parse_page(source).description == "The real first paragraph of prose."


def test_first_paragraph_skips_changed_and_deprecated_annotations() -> None:
    # The skip covers every version-note verb, and stacked notes in a row.
    source = "## H\n\n_Changed in version 1.2_\n\n_Deprecated in version 1.3_\n\nActual prose here.\n"
    assert parse_page(source).description == "Actual prose here."


def test_first_paragraph_skips_html_comments_tags_and_snippets() -> None:
    # Raw HTML (a comment or a tag) and a snippet include are not prose; the
    # extractor skips them and returns the first real paragraph.
    source = '# T\n\n<!-- TODO -->\n\n<img src="x.png">\n\n--8<-- "LICENSE"\n\nThe real prose.\n'
    assert parse_page(source).description == "The real prose."


def test_description_empty_when_body_has_no_usable_paragraph() -> None:
    # A body that is only a heading yields no first paragraph, so tiers 1 and 2
    # both come up empty and the render-time site default takes over.
    assert parse_page("---\ntitle: T\n---\n\n# Only a heading\n").description == ""
