"""
Per-page git metadata: when a content page was created and last changed, its
recent authors, and its "edit on GitHub" URL.

Adapted from the django-components docs site (`apps/docs/build/git_metadata.py`):
one `git log` per source file gives the dates and authors that feed the page
footer, the sitemap `<lastmod>`, and the TechArticle `datePublished` /
`dateModified`. Ported from there with citry's paths, repo URL, and branch; the
"view source" link also handles a package installed from a wheel.

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

import tomllib

from docs_site._internal.project import current_docs_project


@dataclass(frozen=True)
class PageGitMeta:
    # First-commit date (creation) and latest-commit date (last update).
    created: datetime | None
    last_updated: datetime | None
    authors: tuple[str, ...]


EMPTY_META = PageGitMeta(created=None, last_updated=None, authors=())

# Directories where an installer puts the packages it unpacks (a wheel install,
# or any third-party package). An editable install leaves its files in the
# checkout instead, so a path with one of these names holds an installed copy,
# not the file in the checkout.
_INSTALL_DIRS = frozenset({"site-packages", "dist-packages"})


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


def _workspace_member_dirs(repo_root: Path) -> list[Path]:
    """
    The package directories of the repo's uv workspace.

    uv is the Python package manager, and a workspace is a repo that holds
    several packages. The root ``pyproject.toml`` lists their directories as
    path patterns such as ``packages/py/*`` under ``[tool.uv.workspace].members``,
    which is the one place that says where first-party packages live. A repo with
    no readable ``pyproject.toml``, no such table, or a pattern that is not a
    relative path inside the repo has no members for that pattern.
    """
    try:
        root = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    # Each level can be any TOML value in a malformed file, and a bad table means
    # "no members" here, since uv rejects the same file with a clearer message.
    tool = root.get("tool")
    uv = tool.get("uv") if isinstance(tool, dict) else None
    workspace = uv.get("workspace") if isinstance(uv, dict) else None
    patterns = workspace.get("members") if isinstance(workspace, dict) else None
    if not isinstance(patterns, list):
        return []
    members: list[Path] = []
    for pattern in patterns:
        # An absolute or climbing pattern would reach files outside the checkout,
        # and Path.glob rejects an absolute or empty one with an error.
        if not isinstance(pattern, str) or not pattern or Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            continue
        # glob order depends on the filesystem, so sort to keep the answer the same on every machine.
        members.extend(sorted(repo_root.glob(pattern)))
    return members


def _checkout_relative_path(repo_root: Path, filepath: Path) -> Path | None:
    """
    The checkout-relative path of the source file behind ``filepath``, or ``None``.

    A file the checkout holds (an editable install, or a load by griffe, the tool
    that reads the Python source for the API reference, from the source tree)
    maps to itself. A file unpacked into ``site-packages`` maps to the same file
    in the workspace member that provides that package, so a package installed
    from a wheel links to the source it was built from. The virtual environment
    can sit inside the checkout (a ``.venv`` at the repo root), so a plain
    ``relative_to`` would turn the installed copy into a link to ``.venv/...``,
    a path the repository does not have.

    ``None`` means no link: the file is outside the checkout, or it is installed
    and no workspace member has a package with that file (a third-party package,
    or a wheel from a release whose files have since moved).
    """
    try:
        rel: Path | None = filepath.relative_to(repo_root)
    except ValueError:
        rel = None
    # Look inside the checkout-relative part only, so a checkout that itself
    # lives under a directory with one of these names is not mistaken for an
    # installed package.
    parts = (rel if rel is not None else filepath).parts
    # Take the last install directory: an environment can be nested inside
    # another one's site-packages (a tool installed into its own venv), and
    # only the innermost one holds this package.
    install_index = next((i for i in range(len(parts) - 1, -1, -1) if parts[i] in _INSTALL_DIRS), None)
    if install_index is None:
        return rel
    # What follows the install directory is the import path of the file, such
    # as ("citry_core", "safe_eval", "eval.py").
    import_path = parts[install_index + 1 :]
    # A ".." would let `member / import_path` land on a file other than the
    # installed one (for example `demo_core/../demo_core/x.py`), and the link
    # would carry the ".." into the URL.
    if not import_path or ".." in import_path:
        return None
    for member in _workspace_member_dirs(repo_root):
        # The top-level directory must be a Python package, so a stray `tests`
        # or `docs` folder in a member never matches a file that a third-party
        # wheel happens to unpack under the same name.
        candidate = member.joinpath(*import_path)
        if (member / import_path[0] / "__init__.py").is_file() and candidate.is_file():
            return candidate.relative_to(repo_root)
    return None


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
    object has no file on disk. Only a single file that the checkout holds gets
    a link, whether griffe read it from the source tree or from a wheel
    installed into ``site-packages`` (which maps back to the workspace member's
    copy of the file). When ``lineno`` is given, the link jumps straight to that
    line.
    """
    # A namespace package is spread over a list of paths and some objects have no
    # file at all, so neither can point at one source file to link to.
    if not isinstance(filepath, Path):
        return ""
    rel = _checkout_relative_path(repo_root, filepath)
    if rel is None:
        return ""
    repository = current_docs_project().settings.repository
    url = f"{repo_url or repository.url}/blob/{edit_branch or repository.edit_branch}/{rel.as_posix()}"
    if lineno:
        url += f"#L{lineno}"
    return url
