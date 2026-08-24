"""Tests for the AI-readable navigation and bulk text files."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.build import PageRecord
from docs_site._internal.llms import generate_llms_files
from docs_site._internal.nav import NavArea, NavGroup, NavItem, NavTree


def _rec(
    url: str,
    *,
    title: str = "",
    description: str = "",
    body: str = "",
    noindex: bool = False,
) -> PageRecord:
    return PageRecord(
        url=url,
        canonical=f"https://x.test/{url}",
        title=title or url or "Home",
        description=description,
        noindex=noindex,
        is_doc_page=True,
        source_md=None,
        markdown_body=body,
    )


def _nav() -> NavTree:
    return NavTree(
        areas=[
            NavArea(
                label="Docs",
                items=[NavItem(title="Home", path="/")],
                groups=[
                    NavGroup(
                        label="Concepts",
                        items=[
                            NavItem(
                                title="Components [API]",
                                path="/concepts/components/",
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )


def test_llms_txt_is_nav_ordered_with_markdown_links(tmp_path: Path) -> None:
    records = [
        _rec("", title="Citry", description="A templating\nengine.", body="Home body."),
        _rec(
            "concepts/components/",
            title="Components",
            description="A component renders\na template.",
            body="Body.",
        ),
    ]

    links, pages = generate_llms_files(records, tmp_path, _nav(), site_url="https://x.test/", site_name="Citry")

    text = (tmp_path / "llms.txt").read_text(encoding="utf-8")
    assert links == 1
    assert text.startswith("# Citry")
    assert "> A templating engine." in text  # the home description is the summary
    assert "## Docs" in text
    assert "## Docs: Concepts" in text
    assert "###" not in text
    assert (
        "- [Components &#91;API&#93;](https://x.test/concepts/components/index.md): A component renders a template."
    ) in text
    full = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")
    assert pages == 2
    assert "Home body." in full
    assert "Body." in full


@pytest.mark.parametrize("component_record", [None, _rec("concepts/components/", noindex=True)])
def test_llms_txt_omits_pages_without_a_published_companion(
    tmp_path: Path,
    component_record: PageRecord | None,
) -> None:
    records = [_rec("", title="Citry")]
    if component_record is not None:
        records.append(component_record)

    links, _pages = generate_llms_files(
        records,
        tmp_path,
        _nav(),
        site_url="https://x.test",
        site_name="Citry",
    )

    assert links == 0
    assert "concepts/components" not in (tmp_path / "llms.txt").read_text(encoding="utf-8")
