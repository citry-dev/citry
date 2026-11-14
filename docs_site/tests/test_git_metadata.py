"""Tests for per-page git metadata (dates, authors, edit link) and its wiring."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

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


# --- source links for packages installed into site-packages ------------------

_REPO_URL = "https://example.test/repo"


def _source_link(checkout: Path, filepath: Path, lineno: int | None = None) -> str:
    return source_url_for(checkout, filepath, lineno, repo_url=_REPO_URL, edit_branch="main")


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """A synthetic checkout with two uv workspace members and a stray test folder."""
    (tmp_path / "pyproject.toml").write_text('[tool.uv.workspace]\nmembers = ["packages/py/*"]\n', encoding="utf-8")
    files = [
        "packages/py/demo_core/demo_core/__init__.py",
        "packages/py/demo_core/demo_core/safe/eval.py",
        "packages/py/demo_core/tests/test_eval.py",
        "packages/py/demo_ui/demo_ui/__init__.py",
        "packages/py/demo_ui/demo_ui/widgets.py",
    ]
    for name in files:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    return tmp_path


def test_source_url_for_a_wheel_in_a_venv_inside_the_checkout_maps_to_the_workspace_member(checkout: Path) -> None:
    # The shape CI produces: `.venv` at the repo root holds the wheel's copy of the file.
    installed = checkout / ".venv/lib/python3.14/site-packages/demo_core/safe/eval.py"

    assert _source_link(checkout, installed, 18) == (
        f"{_REPO_URL}/blob/main/packages/py/demo_core/demo_core/safe/eval.py#L18"
    )


@pytest.mark.parametrize(
    ("installed", "expected"),
    [
        # A venv outside the checkout, such as a shared developer environment.
        ("/elsewhere/venv/lib/python3.14/site-packages/demo_ui/widgets.py", "demo_ui/demo_ui/widgets.py"),
        # The Debian install directory name.
        ("/usr/lib/python3/dist-packages/demo_core/safe/eval.py", "demo_core/demo_core/safe/eval.py"),
        # The Windows layout. On a POSIX machine this is an ordinary relative path,
        # so it covers the directory-name rule and not drive-letter handling.
        ("C:/venv/Lib/site-packages/demo_core/safe/eval.py", "demo_core/demo_core/safe/eval.py"),
        # An environment nested inside another one's site-packages: the innermost
        # install directory decides what the import path is.
        ("/env/lib/site-packages/tool/venv/lib/site-packages/demo_ui/widgets.py", "demo_ui/demo_ui/widgets.py"),
    ],
)
def test_source_url_for_a_wheel_outside_the_checkout_maps_to_the_workspace_member(
    checkout: Path, installed: str, expected: str
) -> None:
    assert _source_link(checkout, Path(installed)) == f"{_REPO_URL}/blob/main/packages/py/{expected}"


def test_source_url_for_an_editable_install_links_the_checkout_file(checkout: Path) -> None:
    # An editable install reads the source tree directly, so no mapping applies.
    editable = checkout / "packages/py/demo_core/demo_core/safe/eval.py"

    assert _source_link(checkout, editable, 3) == (
        f"{_REPO_URL}/blob/main/packages/py/demo_core/demo_core/safe/eval.py#L3"
    )


def test_source_url_for_a_checkout_under_a_site_packages_directory_still_links(tmp_path: Path) -> None:
    # Only the part below the checkout decides whether a file was installed.
    nested = tmp_path / "site-packages" / "checkout"
    nested.mkdir(parents=True)
    file = nested / "packages/py/demo_core/demo_core/mod.py"
    file.parent.mkdir(parents=True)
    file.touch()

    assert _source_link(nested, file) == f"{_REPO_URL}/blob/main/packages/py/demo_core/demo_core/mod.py"


@pytest.mark.parametrize(
    "installed",
    [
        # A third-party package that no workspace member provides.
        ".venv/lib/python3.14/site-packages/markupsafe/__init__.py",
        # A first-party file that this checkout no longer has.
        ".venv/lib/python3.14/site-packages/demo_core/safe/removed.py",
        # A stray top-level folder is not a Python package of the member.
        ".venv/lib/python3.14/site-packages/tests/test_eval.py",
        # A loose module, and the install directory itself.
        ".venv/lib/python3.14/site-packages/loose.py",
        ".venv/lib/python3.14/site-packages",
        # Climbing out of the install directory and back into the checkout.
        ".venv/lib/python3.14/site-packages/../../../../packages/py/demo_core/demo_core/__init__.py",
        # Stepping out of a package and back in names a file the checkout really
        # has, so only the check for ".." keeps it from becoming a link.
        ".venv/lib/python3.14/site-packages/demo_core/../demo_core/safe/eval.py",
    ],
)
def test_source_url_for_an_installed_file_the_checkout_lacks_is_empty(checkout: Path, installed: str) -> None:
    assert _source_link(checkout, checkout / installed) == ""


def test_source_url_for_an_installed_file_without_a_workspace_table_is_empty(tmp_path: Path) -> None:
    installed = tmp_path / ".venv/lib/python3.14/site-packages/demo_core/safe/eval.py"
    # No pyproject.toml at all, then one that declares no uv workspace.
    assert _source_link(tmp_path, installed) == ""

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert _source_link(tmp_path, installed) == ""

    (tmp_path / "pyproject.toml").write_text("not = [valid toml", encoding="utf-8")
    assert _source_link(tmp_path, installed) == ""


@pytest.mark.parametrize(
    "pyproject",
    [
        # A string where a list belongs, and a table where a table is not expected.
        '[tool.uv.workspace]\nmembers = "packages/py/*"\n',
        '[tool]\nuv = "x"\n',
        '[tool.uv]\nworkspace = ["packages/py/*"]\n',
        # Entries that are not relative paths inside the checkout.
        "[tool.uv.workspace]\nmembers = [1, '', '/abs/packages/*', '../outside/*']\n",
    ],
)
def test_source_url_for_a_malformed_workspace_table_gives_no_link_and_no_error(checkout: Path, pyproject: str) -> None:
    (checkout / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    installed = checkout / ".venv/lib/python3.14/site-packages/demo_core/safe/eval.py"

    assert _source_link(checkout, installed) == ""


def test_source_url_for_skips_a_bad_workspace_entry_and_uses_the_good_ones(checkout: Path) -> None:
    (checkout / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = [1, "/abs/*", "packages/py/*"]\n',
        encoding="utf-8",
    )
    installed = checkout / ".venv/lib/python3.14/site-packages/demo_core/safe/eval.py"

    assert _source_link(checkout, installed) == (f"{_REPO_URL}/blob/main/packages/py/demo_core/demo_core/safe/eval.py")


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
        created=datetime(2026, 6, 1, tzinfo=timezone.utc),
        last_updated=datetime(2026, 7, 2, tzinfo=timezone.utc),
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
