"""Tests for the navigation tree (``_nav.yml`` loading and nav queries)."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.nav import load_nav

CONTENT_NAV = Path(__file__).resolve().parents[1] / "content" / "_nav.yml"

NAV_YAML = """\
sections:
  - label: Home
    path: /
  - label: Getting started
    path: /getting-started/
  - label: Concepts
    items:
      - { title: Components, path: /concepts/components/ }
      - { title: Slots, path: /concepts/slots/ }
  - label: Guides
    groups:
      - label: Advanced
        items:
          - { title: Caching, path: /guides/caching/ }
"""


def _tree(tmp_path: Path):
    nav = tmp_path / "_nav.yml"
    nav.write_text(NAV_YAML, encoding="utf-8")
    return load_nav(nav)


def test_load_sections(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    assert [s.label for s in tree.sections] == ["Home", "Getting started", "Concepts", "Guides"]
    assert tree.sections[0].path == "/"
    assert [i.title for i in tree.sections[2].items] == ["Components", "Slots"]
    assert tree.sections[3].groups[0].label == "Advanced"


def test_flat_pages_in_document_order(tmp_path: Path) -> None:
    paths = [p.path for p in _tree(tmp_path).flat_pages()]
    assert paths == [
        "/",
        "/getting-started/",
        "/concepts/components/",
        "/concepts/slots/",
        "/guides/caching/",
    ]


def test_prev_next(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    prev, nxt = tree.find_prev_next("/concepts/components/")
    assert prev.path == "/getting-started/"
    assert nxt.path == "/concepts/slots/"

    prev, nxt = tree.find_prev_next("/")
    assert prev is None
    assert nxt.path == "/getting-started/"


def test_breadcrumbs(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    assert tree.find_breadcrumbs("/concepts/components/") == [("Concepts", ""), ("Components", "")]
    assert tree.find_breadcrumbs("/guides/caching/") == [("Guides", ""), ("Advanced", ""), ("Caching", "")]
    assert tree.find_breadcrumbs("/getting-started/") == [("Getting started", "")]


def test_find_title(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    assert tree.find_title("/concepts/slots/") == "Slots"
    assert tree.find_title("/nope/") == ""


def test_set_active_expands_containing_group(tmp_path: Path) -> None:
    tree = _tree(tmp_path)
    tree.set_active("/guides/caching/")
    assert tree.sections[3].groups[0].expanded
    assert tree.sections[3].groups[0].items[0].active

    tree.set_active("/concepts/components/")
    assert tree.sections[2].items[0].active
    assert not tree.sections[2].items[1].active


def test_missing_nav_file_is_empty(tmp_path: Path) -> None:
    assert load_nav(tmp_path / "nope.yml").sections == []


def test_both_items_and_groups_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "_nav.yml"
    bad.write_text(
        "sections:\n  - label: X\n    items: [{title: A, path: /a/}]\n    groups: [{label: G, items: []}]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="both 'items' and 'groups'"):
        load_nav(bad)


def test_real_nav_places_cli_in_advanced_and_security_in_about() -> None:
    tree = load_nav(CONTENT_NAV)
    by_label = {section.label: section for section in tree.sections}

    assert [(item.title, item.path) for item in by_label["Advanced"].items][-1] == ("Command line", "/cli/")
    assert [(item.title, item.path) for item in by_label["About"].items][-1] == ("Security", "/security/")
    assert "Command line" not in {section.label for section in tree.sections}
    assert "Security" not in {section.label for section in tree.sections}
    assert tree.find_breadcrumbs("/cli/") == [("Advanced", ""), ("Command line", "")]
    assert tree.find_breadcrumbs("/security/") == [("About", ""), ("Security", "")]


def test_real_nav_splits_events_before_guides() -> None:
    tree = load_nav(CONTENT_NAV)
    by_label = {section.label: section for section in tree.sections}
    labels = [section.label for section in tree.sections]

    assert labels.index("Events") + 1 == labels.index("Guides")
    assert [(item.title, item.path) for item in by_label["Events"].items] == [
        ("Server events", "/guides/server-events/"),
        ("Migrate from Component.View", "/guides/migrate-from-component-view/"),
        ("Migrate from django-unicorn", "/guides/migrate-from-django-unicorn/"),
        ("Migrate from Tetra", "/guides/migrate-from-tetra/"),
        ("Migrate from livecomponents", "/guides/migrate-from-livecomponents/"),
        ("Events migration parity", "/guides/events-migration-parity/"),
    ]
    assert [(item.title, item.path) for item in by_label["Guides"].items] == [
        ("Web frameworks", "/web-frameworks/"),
        ("Troubleshooting", "/guides/troubleshooting/"),
        ("Hot reload", "/guides/dev-server/"),
    ]
    assert "Web frameworks" not in {section.label for section in tree.sections}
    assert tree.find_breadcrumbs("/guides/server-events/") == [("Events", ""), ("Server events", "")]
    assert tree.find_breadcrumbs("/web-frameworks/") == [("Guides", ""), ("Web frameworks", "")]
