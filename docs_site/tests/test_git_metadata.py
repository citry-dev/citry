"""Tests for per-page git metadata (dates, authors, edit link) and its wiring."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import docs_site._internal.git_metadata as gm
from docs_site._internal.config import config
from docs_site._internal.git_metadata import edit_url_for, get_page_git_meta, is_excluded, source_url_for
from docs_site._internal.pipeline import render_page

_CONTENT_PAGE = config.repo_root / "docs_site" / "content" / "concepts" / "components.md"


def test_edit_url_for_a_file_under_the_repo() -> None:
    assert edit_url_for(config.repo_root, _CONTENT_PAGE) == (
        "https://github.com/citry-dev/citry/edit/main/docs_site/content/concepts/components.md"
    )


def test_edit_url_for_a_generated_page_outside_the_repo_is_empty() -> None:
    assert edit_url_for(config.repo_root, Path("/outside/staging/reference/x.md")) == ""


def test_source_url_for_a_file_under_the_repo_with_a_line() -> None:
    assert source_url_for(config.repo_root, _CONTENT_PAGE, 42) == (
        "https://github.com/citry-dev/citry/blob/main/docs_site/content/concepts/components.md#L42"
    )


def test_source_url_for_without_a_line_has_no_anchor() -> None:
    assert source_url_for(config.repo_root, _CONTENT_PAGE) == (
        "https://github.com/citry-dev/citry/blob/main/docs_site/content/concepts/components.md"
    )


def test_source_url_for_a_path_outside_the_repo_is_empty() -> None:
    assert source_url_for(config.repo_root, Path("/outside/staging/reference/x.py"), 5) == ""


def test_source_url_for_a_list_or_none_filepath_is_empty() -> None:
    # Namespace packages give a list of paths; objects with no source file give None.
    assert source_url_for(config.repo_root, [_CONTENT_PAGE], 5) == ""
    assert source_url_for(config.repo_root, None, 5) == ""


def test_is_excluded_matches_the_configured_patterns() -> None:
    assert is_excluded(Path("community/license.md"))
    assert is_excluded(Path("community/code-of-conduct.md"))
    assert not is_excluded(Path("concepts/components.md"))


def test_get_page_git_meta_parses_git_log(tmp_path: Path, monkeypatch: Any) -> None:
    # Newest-first "date<TAB>author" rows, as `git log --format=%cI%x09%an` emits.
    log = "2026-07-02T10:00:00+00:00\tAda\n2026-07-01T09:00:00+00:00\tGrace\n2026-06-30T08:00:00+00:00\tAda\n"
    monkeypatch.setattr(
        gm.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=log, stderr=""),  # noqa: ARG005
    )
    gm.get_page_git_meta.cache_clear()

    meta = gm.get_page_git_meta(tmp_path, tmp_path / "p.md")

    assert meta.last_updated.date().isoformat() == "2026-07-02"  # newest commit
    assert meta.created.date().isoformat() == "2026-06-30"  # first commit
    assert meta.authors == ("Ada", "Grace")  # deduped, newest-first


def test_get_page_git_meta_reads_real_history() -> None:
    # README.md is committed, so git reports a real creation and last-updated date.
    meta = get_page_git_meta(config.repo_root, config.repo_root / "README.md")
    assert meta.created is not None
    assert meta.last_updated is not None
    assert meta.created <= meta.last_updated


def test_get_page_git_meta_untracked_file_is_empty(tmp_path: Path) -> None:
    # A file with no git history returns EMPTY_META, not an error.
    assert get_page_git_meta(tmp_path, tmp_path / "never-committed.md") is gm.EMPTY_META


def test_render_page_adds_the_edit_link_from_source_path() -> None:
    html = render_page("# Components\n\nText.", current_path="concepts/components/", source_path=_CONTENT_PAGE).html
    assert "Edit this page on GitHub" in html
    assert "github.com/citry-dev/citry/edit/main/docs_site/content/concepts/components.md" in html


def test_render_page_without_source_path_has_no_edit_link() -> None:
    html = render_page("# X\n\nText.", current_path="x/").html
    assert "Edit this page on GitHub" not in html


def test_render_page_puts_git_dates_in_the_article_json_ld(monkeypatch: Any) -> None:
    import docs_site._internal.pipeline as pipeline_mod
    from docs_site._internal.git_metadata import PageGitMeta

    meta = PageGitMeta(
        created=datetime(2026, 6, 1, tzinfo=UTC),
        last_updated=datetime(2026, 7, 2, tzinfo=UTC),
        authors=("Ada",),
    )
    monkeypatch.setattr(pipeline_mod, "get_page_git_meta", lambda _root, _path: meta)
    html = render_page(
        "# Components\n\nText.",
        canonical="https://x.test/concepts/components/",
        current_path="concepts/components/",
        source_path=_CONTENT_PAGE,
    ).html
    assert '"datePublished": "2026-06-01T00:00:00+00:00"' in html
    assert '"dateModified": "2026-07-02T00:00:00+00:00"' in html
    assert "Last updated" in html
    assert "Ada" in html
