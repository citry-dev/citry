"""Tests for the AI-readable index files: llms.txt and llms-full.txt."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.build import PageRecord
from docs_site._internal.llms import generate_llms_files
from docs_site._internal.nav import NavItem, NavSection, NavTree


def _rec(url: str, *, title: str = "", description: str = "", body: str = "") -> PageRecord:
    return PageRecord(
        url=url,
        canonical=f"https://x.test/{url}",
        title=title or url or "Home",
        description=description,
        noindex=False,
        is_doc_page=True,
        source_md=None,
        markdown_body=body,
    )


def _nav() -> NavTree:
    return NavTree(
        sections=[
            NavSection(label="Home", path="/"),
            NavSection(label="Concepts", items=[NavItem(title="Components", path="/concepts/components/")]),
        ]
    )


def test_llms_txt_is_nav_ordered_with_descriptions(tmp_path: Path) -> None:
    records = [
        _rec("", title="Citry", description="A templating engine.", body="Home body."),
        _rec("concepts/components/", title="Components", description="A component renders a template.", body="Body."),
    ]

    links, _pages = generate_llms_files(records, tmp_path, _nav(), site_url="https://x.test/", site_name="Citry")

    text = (tmp_path / "llms.txt").read_text(encoding="utf-8")
    assert links == 1
    assert text.startswith("# Citry")
    assert "> A templating engine." in text  # the home description is the summary
    assert "## Concepts" in text
    assert "- [Components](https://x.test/concepts/components/): A component renders a template." in text


def test_llms_full_concatenates_page_bodies(tmp_path: Path) -> None:
    records = [
        _rec("", title="Citry", body="The home page body."),
        _rec("concepts/components/", title="Components", body="The components body."),
    ]

    _links, pages = generate_llms_files(records, tmp_path, _nav(), site_url="https://x.test", site_name="Citry")

    full = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
    assert pages == 2
    assert "The home page body." in full
    assert "The components body." in full
    assert "Source: https://x.test/concepts/components/" in full
    assert "\n\n---\n\n" in full  # a rule separates the pages
