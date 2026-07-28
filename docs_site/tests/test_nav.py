"""Tests for the primary-area navigation tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.nav import SCOPE_SITE, SCOPE_VERSIONED, NavItem, load_nav, resolve_nav_sources

NAV_YAML = """\
areas:
  - label: Docs
    items:
      - { title: Home, path: / }
    groups:
      - label: Concepts
        items:
          - { title: Components, path: /concepts/components/ }
          - { title: Slots, path: /concepts/slots/ }
      - label: Release notes
        source: releases
        collapsible: true
        section_style: true
  - label: Examples
    items:
      - { title: Overview, path: /examples/ }
    groups:
      - label: Components
        collapsible: true
        items:
          - { title: Card, path: /examples/card/ }
  - label: Reference
    source: reference
"""


def _tree(tmp_path: Path):
    nav = tmp_path / "_nav.yml"
    nav.write_text(NAV_YAML, encoding="utf-8")
    return resolve_nav_sources(
        load_nav(nav),
        {
            "reference": [
                NavItem(title="Overview", path="/reference/"),
            ],
            "releases": [
                NavItem(title="Overview", path="/releases/"),
                NavItem(title="v1", path="/releases/v1/"),
            ],
        },
    )


def test_loads_areas_with_direct_items_groups_and_sources(
    tmp_path: Path,
) -> None:
    tree = _tree(tmp_path)
    assert [area.label for area in tree.areas] == [
        "Docs",
        "Examples",
        "Reference",
    ]
    assert tree.areas[0].items[0].title == "Home"
    assert [group.label for group in tree.areas[0].groups] == [
        "Concepts",
        "Release notes",
    ]
    assert not tree.areas[0].groups[0].collapsible
    assert tree.areas[0].groups[1].collapsible
    assert tree.areas[0].groups[1].section_style
    assert tree.areas[1].groups[0].collapsible
    assert tree.areas[2].entry_path == "/reference/"


def test_flat_pages_follow_area_and_sidebar_order(tmp_path: Path) -> None:
    paths = [page.path for page in _tree(tmp_path).flat_pages()]
    assert paths == [
        "/",
        "/concepts/components/",
        "/concepts/slots/",
        "/releases/",
        "/releases/v1/",
        "/examples/",
        "/examples/card/",
        "/reference/",
    ]


def test_prev_next_is_scoped_to_the_current_area(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    previous, following = tree.find_prev_next(
        "/concepts/components/",
    )
    assert previous is not None
    assert previous.path == "/"
    assert following is not None
    assert following.path == "/concepts/slots/"

    previous, following = tree.find_prev_next("/reference/")
    assert previous is None
    assert following is None


def test_breadcrumbs_follow_area_group_and_page(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    assert tree.find_breadcrumbs("/concepts/components/") == [
        ("Docs", "/"),
        ("Concepts", ""),
        ("Components", ""),
    ]
    assert tree.find_breadcrumbs("/releases/v1/") == [
        ("Docs", "/"),
        ("Release notes", "/releases/"),
        ("v1", ""),
    ]
    assert tree.find_breadcrumbs("/releases/") == [
        ("Docs", "/"),
        ("Release notes", ""),
    ]
    assert tree.find_breadcrumbs("/examples/") == [
        ("Examples", ""),
    ]
    assert tree.find_breadcrumbs("/") == [("Home", "")]


def test_find_title_and_area(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    assert tree.find_title("/concepts/slots/") == "Slots"
    assert tree.find_area("/examples/card/") is tree.areas[1]
    assert tree.find_title("/nope/") == ""
    assert tree.find_area("/nope/") is None


def test_set_active_expands_only_the_containing_group(
    tmp_path: Path,
) -> None:
    tree = _tree(tmp_path)
    tree.set_active("/examples/card/")
    assert tree.areas[1].groups[0].expanded
    assert tree.areas[1].groups[0].items[0].active
    assert not tree.areas[0].groups[0].expanded


def test_missing_nav_file_is_empty(tmp_path: Path) -> None:
    assert load_nav(tmp_path / "nope.yml").areas == []


def test_present_nav_requires_areas_root(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text("sections: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level 'areas'"):
        load_nav(nav)


def test_present_nav_requires_at_least_one_area(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text("areas: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one area"):
        load_nav(nav)


def test_present_nav_rejects_unknown_top_level_keys(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Home, path: / }]\nscpoes: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown top-level key"):
        load_nav(nav)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            """\
areas:
  - label: Reference
    source: reference
    items: [{ title: X, path: /x/ }]
""",
            "source and authored children",
        ),
        (
            """\
areas:
  - label: Docs
    items: [{ title: X, path: /x/ }]
  - label: Docs
    items: [{ title: Y, path: /y/ }]
""",
            "Duplicate navigation area label",
        ),
        (
            """\
areas:
  - label: Docs
    groups:
      - label: Same
        items: [{ title: X, path: /x/ }]
      - label: Same
        items: [{ title: Y, path: /y/ }]
""",
            "Duplicate navigation group label",
        ),
        (
            """\
areas:
  - label: Docs
    items: [{ title: X, path: /same/ }]
  - label: Examples
    items: [{ title: Y, path: /same/ }]
""",
            "belongs to both",
        ),
        (
            """\
areas:
  - label: Docs
    items: [{ title: '', path: /x/ }]
""",
            "titles may not be empty",
        ),
    ],
)
def test_invalid_navigation_is_rejected(
    tmp_path: Path,
    body: str,
    message: str,
) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_nav(nav)


def test_missing_release_source_omits_only_that_group(
    tmp_path: Path,
) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(NAV_YAML, encoding="utf-8")
    tree = resolve_nav_sources(
        load_nav(nav),
        {
            "reference": [
                NavItem(title="Overview", path="/reference/"),
            ],
            "releases": None,
        },
    )
    assert [group.label for group in tree.areas[0].groups] == [
        "Concepts",
    ]


def test_blog_area_source_hydrates_in_declared_order(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        """\
areas:
  - label: Docs
    items: [{ title: Home, path: / }]
  - label: Blog
    source: blog
    scope: site
    entry: { title: All posts, path: /blog/ }
""",
        encoding="utf-8",
    )

    tree = resolve_nav_sources(
        load_nav(nav),
        {
            "blog": [
                NavItem(title="All posts", path="/blog/"),
                NavItem(
                    title="New post",
                    path="/blog/new-post/",
                    date_iso="2026-07-28",
                    date_label="28 Jul 2026",
                ),
            ],
        },
    )

    assert [area.label for area in tree.areas] == ["Docs", "Blog"]
    assert tree.areas[-1].entry_path == "/blog/"
    assert tree.find_breadcrumbs("/blog/") == [("Blog", "")]
    assert tree.find_breadcrumbs("/blog/new-post/") == [
        ("Blog", "/blog/"),
        ("New post", ""),
    ]
    assert tree.areas[-1].items[-1].date_label == "28 Jul 2026"


def test_content_scope_inherits_and_allows_narrow_overrides(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        """\
areas:
  - label: Docs
    scope: versioned
    items:
      - { title: Home, path: /, scope: site }
    groups:
      - label: Guides
        scope: site
        items:
          - { title: News, path: /news/ }
          - { title: Frozen guide, path: /guide/, scope: versioned }
  - label: Blog
    source: blog
    scope: site
    entry: { title: All posts, path: /blog/ }
""",
        encoding="utf-8",
    )

    tree = resolve_nav_sources(
        load_nav(nav),
        {"blog": [NavItem(title="All posts", path="/blog/")]},
    )

    assert tree.areas[0].scope == SCOPE_VERSIONED
    assert tree.areas[0].groups[0].scope == SCOPE_SITE
    assert tree.scope_for_path("/") == SCOPE_SITE
    assert tree.scope_for_path("/news/") == SCOPE_SITE
    assert tree.scope_for_path("/guide/") == SCOPE_VERSIONED
    assert tree.scope_for_path("/not-in-nav/") == SCOPE_VERSIONED
    assert tree.scope_for_source("blog") == SCOPE_SITE
    assert all(item.scope == SCOPE_SITE for item in tree.areas[1].items)


def test_content_asset_scope_uses_unanimous_route_namespace(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    tree.areas[1].scope = SCOPE_SITE
    for item in tree.areas[1].flat_pages():
        item.scope = SCOPE_SITE

    assert tree.scope_for_content_asset(Path("examples/card.png")) == SCOPE_SITE
    assert tree.scope_for_content_asset(Path("concepts/diagram.svg")) == SCOPE_VERSIONED
    assert tree.scope_for_content_asset(Path("unowned/file.txt")) == SCOPE_VERSIONED


@pytest.mark.parametrize("scope", ["global", "", 3, True])
def test_invalid_content_scope_is_rejected(tmp_path: Path, scope: object) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        f"areas:\n  - label: Docs\n    scope: {scope!r}\n    items: [{{ title: Home, path: / }}]\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid scope"):
        load_nav(nav)


def test_unknown_navigation_key_is_rejected(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        "areas:\n  - label: Docs\n    scpoe: site\n    items: [{ title: Home, path: / }]\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"unknown key\(s\): scpoe"):
        load_nav(nav)


def test_generated_source_must_match_its_declared_entry(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        "areas:\n  - label: News\n    source: blog\n    scope: site\n    entry: { title: All news, path: /news/ }\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not its declared entry"):
        resolve_nav_sources(
            load_nav(nav),
            {"blog": [NavItem(title="All posts", path="/blog/")]},
        )


def test_site_scoped_generated_group_declares_and_hydrates_its_entry(tmp_path: Path) -> None:
    nav = tmp_path / "_nav.yml"
    nav.write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Updates\n"
        "        source: releases\n"
        "        scope: site\n"
        "        entry: { title: All updates, path: /updates/ }\n",
        encoding="utf-8",
    )
    tree = load_nav(nav)
    fallback = tree.fallback_items_for_source("releases")

    assert fallback is not None
    resolved = resolve_nav_sources(tree, {"releases": fallback})
    group = resolved.areas[0].groups[0]
    assert group.items[0].path == "/updates/"
    assert group.items[0].scope == SCOPE_SITE
    assert resolved.scope_for_url("/updates/post/") == SCOPE_SITE
