"""Tests for the release-notes generator (CHANGELOG.md -> /releases/ pages)."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.config import config
from docs_site._internal.pipeline import render_page
from docs_site._internal.release_notes import (
    _promote_body_headings,
    parse_changelog,
    release_index_markdown,
    release_page_markdown,
    releases_nav_items,
)

_SAMPLE = """\
# Release notes

## Unreleased

- Something new.

## v0.2.0

### Feat

- A feature.

### Fix

- A fix.

## v0.1.0

_30 Jun 2026_

Initial release.
"""


def test_parse_changelog_splits_into_releases() -> None:
    releases = parse_changelog(_SAMPLE)
    assert [r.slug for r in releases] == ["unreleased", "v0.2.0", "v0.1.0"]
    # File order is preserved (newest-first, as the changelog is written).
    assert releases[0].title == "Unreleased"


def test_parse_changelog_skips_the_title_preamble() -> None:
    # The "# Release notes" H1 is not a release section.
    assert all(r.title != "Release notes" for r in parse_changelog(_SAMPLE))


def test_parse_changelog_pulls_a_date_into_the_title() -> None:
    v01 = next(r for r in parse_changelog(_SAMPLE) if r.slug == "v0.1.0")
    assert v01.title == "v0.1.0 (2026-06-30)"  # "_30 Jun 2026_" -> ISO in the title
    assert "30 Jun 2026" not in v01.body  # and removed from the body
    assert "Initial release." in v01.body


def test_parse_changelog_keeps_the_body_verbatim() -> None:
    v02 = next(r for r in parse_changelog(_SAMPLE) if r.slug == "v0.2.0")
    assert "### Feat" in v02.body
    assert "- A feature." in v02.body


def test_parse_changelog_empty_text_is_no_releases() -> None:
    assert parse_changelog("# Release notes\n\nnothing yet.\n") == []


# --- robustness regressions (from the adversarial review) ---


def test_parse_changelog_does_not_split_on_a_heading_inside_a_fence() -> None:
    # A '## ' line inside a top-level fenced block must NOT start a new release.
    text = "# Release notes\n\n## v1.0.0\n\n- x\n\n```markdown\n# Title\n## Section two\n```\n\n- after the fence.\n"
    releases = parse_changelog(text)
    assert [r.slug for r in releases] == ["v1.0.0"]  # one release, not three
    assert "## Section two" in releases[0].body  # the fenced heading stayed put
    assert "after the fence." in releases[0].body  # nothing after the fence was lost


def test_parse_changelog_tolerates_an_invalid_date_without_raising() -> None:
    # A date-shaped italic line with a non-month word must not abort the build.
    releases = parse_changelog("# Release notes\n\n## v1.0.0\n\n_5 Mai 2024_\n\nNotes.\n")
    assert releases[0].title == "v1.0.0"  # not lifted (invalid)
    assert "_5 Mai 2024_" in releases[0].body  # left in place


def test_parse_changelog_accepts_a_full_month_name() -> None:
    releases = parse_changelog("# Release notes\n\n## v1.0.0\n\n_30 June 2026_\n\nNotes.\n")
    assert releases[0].title == "v1.0.0 (2026-06-30)"


def test_parse_changelog_makes_colliding_slugs_unique() -> None:
    # Two headings that normalize to the same slug get distinct pages.
    releases = parse_changelog("# Release notes\n\n## v1.0.0 (beta)\n\n- a\n\n## v1.0.0 beta\n\n- b\n")
    slugs = [r.slug for r in releases]
    assert len(slugs) == len(set(slugs))  # unique
    assert slugs == ["v1.0.0-beta", "v1.0.0-beta-2"]


def test_parse_changelog_omits_excluded_headings() -> None:
    text = "# Release notes\n\n## v1.0.0\n\n- x\n\n## 2025-12-21\n\n- initial commit\n"
    # The default exclusion drops the initial dated entry entirely.
    assert [r.slug for r in parse_changelog(text)] == ["v1.0.0"]
    # A caller can exclude nothing, or a different heading.
    assert [r.slug for r in parse_changelog(text, exclude=())] == ["v1.0.0", "2025-12-21"]
    assert [r.slug for r in parse_changelog(text, exclude={"v1.0.0"})] == ["2025-12-21"]


def test_real_changelog_excludes_the_initial_commit_entry() -> None:
    releases = parse_changelog((config.repo_root / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert all(r.slug != "2025-12-21" for r in releases)  # hidden from the docs site


def test_promote_body_headings_demotes_a_stray_h1() -> None:
    # An H1 in a body would collide with the page H1; it is pushed to H2.
    promoted = _promote_body_headings("# Big\n\ntext\n\n## sub")
    assert "\n# Big" not in "\n" + promoted  # no leading-H1 line remains
    assert "## Big" in promoted
    assert "### sub" in promoted  # relative depth preserved (H2 -> H3)


def test_promote_body_headings_lifts_the_shallowest_to_h2() -> None:
    # A version body's "### Feat" becomes "## Feat" so the page H1 -> H2 does not skip.
    promoted = _promote_body_headings("### Feat\n\n- x\n\n### Fix\n\n- y")
    assert "## Feat" in promoted
    assert "### Feat" not in promoted
    assert "## Fix" in promoted


def test_promote_body_headings_preserves_relative_depth() -> None:
    promoted = _promote_body_headings("### A\n\n#### B")
    assert "## A" in promoted  # 3 -> 2
    assert "### B" in promoted  # 4 -> 3 (relative depth kept)


def test_promote_body_headings_leaves_fenced_hashes_alone() -> None:
    body = "### Feat\n\n```python\n# a comment, not a heading\n```"
    promoted = _promote_body_headings(body)
    assert "## Feat" in promoted
    assert "# a comment, not a heading" in promoted  # untouched inside the fence


def test_promote_body_headings_no_headings_is_unchanged() -> None:
    body = "- just a bullet\n\nsome prose."
    assert _promote_body_headings(body) == body


def test_release_page_markdown_has_front_matter_and_one_h1() -> None:
    release = next(r for r in parse_changelog(_SAMPLE) if r.slug == "v0.2.0")
    source = release_page_markdown(release)
    assert source.startswith("---\ntitle: v0.2.0\n")
    assert "# v0.2.0" in source
    assert "## Feat" in source  # promoted


def test_release_index_markdown_links_every_release_with_clean_urls() -> None:
    md = release_index_markdown(parse_changelog(_SAMPLE))
    assert "# Release notes" in md
    assert "- [Unreleased](unreleased/)" in md
    assert "- [v0.2.0](v0.2.0/)" in md
    assert "- [v0.1.0 (2026-06-30)](v0.1.0/)" in md


def test_releases_nav_source_includes_overview_and_versions() -> None:
    items = releases_nav_items(parse_changelog(_SAMPLE))
    assert [item.title for item in items] == [
        "Overview",
        "Unreleased",
        "v0.2.0",
        "v0.1.0 (2026-06-30)",
    ]
    assert [item.path for item in items] == [
        "/releases/",
        "/releases/unreleased/",
        "/releases/v0.2.0/",
        "/releases/v0.1.0/",
    ]


def test_release_version_page_breadcrumbs_back_to_the_index() -> None:
    from docs_site._internal.nav import (
        NavArea,
        NavGroup,
        NavItem,
        NavTree,
    )

    tree = NavTree(
        areas=[
            NavArea(
                label="Docs",
                items=[NavItem(title="Home", path="/")],
                groups=[
                    NavGroup(
                        label="Release notes",
                        items=releases_nav_items(
                            parse_changelog(_SAMPLE),
                        ),
                    ),
                ],
            ),
        ],
    )
    # A version page: parent "Release notes" crumb links back to the index.
    assert tree.find_breadcrumbs("releases/v0.2.0") == [
        ("Docs", "/"),
        ("Release notes", "/releases/"),
        ("v0.2.0", ""),
    ]
    # The index page is just the current crumb.
    assert tree.find_breadcrumbs("releases") == [
        ("Docs", "/"),
        ("Release notes", ""),
    ]


# --- rendering behavior: release prose that shows citry syntax ---


def test_run_citry_pass_false_shows_c_raw_literally() -> None:
    # A `<c-raw>` mention (a reserved tag) is displayed as text, not executed.
    source = "---\ntitle: T\n---\n\n# T\n\nThe `<c-raw>` tag renders content verbatim.\n"
    html = render_page(source, current_path="releases/unreleased/", run_citry_pass=False).html
    assert "c-raw" in html  # rendered
    assert "<h1" in html


def test_run_citry_pass_true_breaks_on_c_raw_in_inline_code() -> None:
    # Documents WHY release pages skip the citry pass: fence protection wraps
    # inline code in <c-raw>, so inline code that itself closes a raw block (as
    # the real CHANGELOG does: "A `<c-raw>...</c-raw>` block") breaks Pass 1.
    source = "---\ntitle: T\n---\n\n# T\n\nA `<c-raw>...</c-raw>` block renders verbatim.\n"
    with pytest.raises(Exception):  # noqa: B017, PT011 - the point is that Pass 1 fails here
        render_page(source, current_path="x/", run_citry_pass=True)


def test_real_changelog_renders_every_release_page_cleanly() -> None:
    changelog = (config.repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    releases = parse_changelog(changelog)
    assert len(releases) >= 3  # unreleased + at least two versions
    for release in releases:
        source = release_page_markdown(release)
        html = render_page(source, current_path=f"releases/{release.slug}/", run_citry_pass=False).html
        assert html.count("<h1") == 1  # exactly one H1 (the version)
        # No unexecuted-and-unescaped citry tag leaked into the output.
        assert "<c-raw>" not in html


def test_real_changelog_index_renders() -> None:
    changelog = (config.repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    md = release_index_markdown(parse_changelog(changelog))
    html = render_page(md, current_path="releases/", run_citry_pass=False).html
    assert html.count("<h1") == 1
    assert "Release notes" in html


def test_llms_txt_links_per_version_release_notes(tmp_path: Path) -> None:
    # Generated version items must reach llms.txt through the resolved nav.
    from docs_site._internal.build import PageRecord
    from docs_site._internal.llms import write_llms_txt
    from docs_site._internal.nav import NavTree

    def rec(url: str, title: str, description: str) -> PageRecord:
        return PageRecord(
            url=url,
            canonical="",
            title=title,
            description=description,
            noindex=False,
            is_doc_page=True,
            source_md=None,
            markdown_body="",
        )

    # flat_pages reaches generated items the same way it reaches authored pages.
    from docs_site._internal.nav import NavArea, NavGroup

    items = releases_nav_items(
        parse_changelog(
            "# Release notes\n\n## v0.2.0\n\n- x\n",
        ),
    )
    nav = NavTree(
        areas=[
            NavArea(
                label="Docs",
                groups=[
                    NavGroup(label="Release notes", items=items),
                ],
            ),
        ],
    )
    by_url = {
        "releases": rec("releases/", "Release notes", "Pick a version."),
        "releases/v0.2.0": rec("releases/v0.2.0/", "v0.2.0", "A feature landed in v0.2.0."),
    }
    n = write_llms_txt(tmp_path, nav, by_url, site_url="https://x.test", site_name="Citry")
    out = (tmp_path / "llms.txt").read_text(encoding="utf-8")
    assert ("[v0.2.0](https://x.test/releases/v0.2.0/index.md): A feature landed in v0.2.0.") in out
    assert n == 2  # the index plus the one version, both via the resolved group
