"""
Per-page git metadata: when a content page was created and last changed, its
recent authors, and its "edit on GitHub" URL.

Adapted from the django-components docs site (`apps/docs/build/git_metadata.py`):
one `git log` per source file gives the dates and authors that feed the page
footer, the sitemap `<lastmod>`, and the TechArticle `datePublished` /
`dateModified`. Kept a straight port; only the paths, repo URL, and branch are
citry's.

The data comes from commit history, so CI checkouts must be full clones (set
`fetch-depth: 0` on `actions/checkout` in the docs workflows). A shallow clone
makes every page report the checkout commit as its creation and last update.
Uncommitted files have no history and return `EMPTY_META` (no dates, no link).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatch
from functools import cache
from pathlib import Path

from docs_site._internal.project import current_docs_project


@dataclass(frozen=True)
class PageGitMeta:
    # First-commit date (creation) and latest-commit date (last update).
    created: datetime | None
    last_updated: datetime | None
    authors: tuple[str, ...]


EMPTY_META = PageGitMeta(created=None, last_updated=None, authors=())


def is_excluded(content_rel_path: Path, patterns: tuple[str, ...] | None = None) -> bool:
    """True for content pages that should not show a last-updated date."""
    posix = content_rel_path.as_posix()
    patterns = patterns if patterns is not None else current_docs_project().settings.git.exclude_patterns
    return any(fnmatch(posix, pattern) for pattern in patterns)


@cache
def get_page_git_meta(repo_root: Path, page_path: Path, max_authors: int | None = None) -> PageGitMeta:
    """
    Creation date, last-updated date, and recent authors for one source file.

    Authors are unique, most-recent-first, capped at ``MAX_AUTHORS``. Returns
    ``EMPTY_META`` for files with no git history (new/untracked/generated) or
    when git is unavailable. Cached, so a page is looked up at most once.
    """
    try:
        rel = page_path.relative_to(repo_root)
    except ValueError:
        return EMPTY_META

    try:
        # Newest-first "commit-date<TAB>author" rows; --follow tracks renames.
        proc = subprocess.run(
            ["git", "log", "--follow", "--format=%cI%x09%an", "--", rel.as_posix()],  # noqa: S607
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return EMPTY_META

    rows = [line for line in proc.stdout.splitlines() if line.strip()]
    if not rows:
        return EMPTY_META

    # Rows are newest-first: the first is the latest commit, the last the first.
    last_updated = datetime.fromisoformat(rows[0].split("\t", 1)[0])
    created = datetime.fromisoformat(rows[-1].split("\t", 1)[0])
    # fromkeys dedups while preserving the newest-first order.
    authors = dict.fromkeys(row.split("\t", 1)[1] for row in rows if "\t" in row)
    limit = max_authors if max_authors is not None else current_docs_project().settings.git.max_authors
    return PageGitMeta(created=created, last_updated=last_updated, authors=tuple(list(authors)[:limit]))


def edit_url_for(
    repo_root: Path,
    page_path: Path,
    *,
    repo_url: str | None = None,
    edit_branch: str | None = None,
) -> str:
    """
    GitHub "edit this page" URL for a content source file, or "" if it has none.

    Only files under the repo get a link. Generated Reference pages, standalone
    example demos, and the 404 are rendered from strings or temp dirs outside
    it, so ``relative_to`` raises and they correctly get no link.
    """
    try:
        rel = page_path.relative_to(repo_root)
    except ValueError:
        return ""
    repository = current_docs_project().settings.repository
    return f"{repo_url or repository.url}/edit/{edit_branch or repository.edit_branch}/{rel.as_posix()}"


def source_url_for(
    repo_root: Path,
    filepath: Path | list[Path] | None,
    lineno: int | None = None,
    *,
    repo_url: str | None = None,
    edit_branch: str | None = None,
) -> str:
    """
    GitHub "view source" URL for a documented symbol's file, or "" if it has none.

    ``filepath`` is a griffe object's ``.filepath``: a single file for a normal
    module, a list of directories for a namespace package, or ``None`` when the
    object has no file on disk. Only a single file under the repo gets a link;
    when ``lineno`` is given, the link jumps straight to that line.
    """
    # A namespace package is spread over a list of paths and some objects have no
    # file at all, so neither can point at one source file to link to.
    if not isinstance(filepath, Path):
        return ""
    try:
        rel = filepath.relative_to(repo_root)
    except ValueError:
        return ""
    repository = current_docs_project().settings.repository
    url = f"{repo_url or repository.url}/blob/{edit_branch or repository.edit_branch}/{rel.as_posix()}"
    if lineno:
        url += f"#L{lineno}"
    return url
