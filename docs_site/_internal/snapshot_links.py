"""
Point the repository links in an archived docs version at the release it was built from.

An archived version under ``versions/<version>/`` stays published for as long as
the site exists. The pages it was built from link to files on GitHub through
``main`` (a reference page's "source" link, a guide's link to a benchmark folder,
an image on raw.githubusercontent.com). ``main`` keeps changing, so those links
would show code that no longer matches the archived page, and break once a file
moves. ``build-tag``, ``build-all``, and ``build --docs-version`` rewrite them
with ``pin_snapshot_links`` before the new version moves into place, and the
``snapshot_main_links`` version guard fails on any link to ``main`` left behind.

"Edit this page" links stay on ``main``, because a fix is always made there. The
shared link patterns live in ``scripts/release_links.py``, which the package
publish workflows use for the same rewrite, and they do not match ``/edit/``.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from scripts.release_links import main_links, pin

if TYPE_CHECKING:
    from pathlib import Path

# Docs versions document Citry releases, whose tags are `citry@<version>`.
RELEASE_TAG_PREFIX = "citry@"

# The files the rewrite changes: the pages and their Markdown and text copies.
# Every other file keeps its bytes. Images and fonts are binary, and the
# event-definition `.js` files are named by a hash of their contents, so
# rewriting them would break that name.
SNAPSHOT_TEXT_SUFFIXES = frozenset({".html", ".md", ".txt", ".xml", ".json"})


def checkout_release_ref(repo_root: Path, version: str) -> str:
    """
    Return the ref a version built from this checkout should link to.

    That is the ``citry@<version>`` tag when the checkout is exactly that tag's
    commit, and otherwise the checkout's own commit, so a version built before
    tagging, or from another commit, links to the code it was built from.
    Returns "" when git cannot say, in which case nothing is rewritten.
    """

    def rev_parse(ref: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "-q", "--verify", ref],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    head = rev_parse("HEAD^{commit}")
    tag = f"{RELEASE_TAG_PREFIX}{version}"
    if head and rev_parse(f"refs/tags/{tag}^{{commit}}") == head:
        return tag
    return head


def _regular_files(version_dir: Path) -> list[Path]:
    # A symlink could point outside the snapshot, so it is neither read nor written.
    return sorted(path for path in version_dir.rglob("*") if path.is_file() and not path.is_symlink())


def pin_snapshot_links(version_dir: Path, ref: str) -> int:
    """Rewrite every link to ``main`` in one built version's pages to ``ref``; return how many files changed."""
    changed = 0
    for path in _regular_files(version_dir):
        if path.suffix not in SNAPSHOT_TEXT_SUFFIXES:
            continue
        # Bytes in and out, so a page's line endings stay exactly as built.
        text = path.read_bytes().decode("utf-8")
        pinned = pin(text, ref)
        if pinned != text:
            path.write_bytes(pinned.encode("utf-8"))
            changed += 1
    return changed


def unpinned_snapshot_links(version_dir: Path) -> list[tuple[Path, int, str]]:
    """
    Return each link to ``main`` left in one built version, with its file and line.

    This reads every file that decodes as UTF-8, which is wider than the files
    the rewrite changes, so a link in a script, stylesheet, or copied YAML file
    that the rewrite cannot reach still fails the check.
    """
    found: list[tuple[Path, int, str]] = []
    for path in _regular_files(version_dir):
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            found.extend((path, number, link) for link in main_links(line))
    return found
