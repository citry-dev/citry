"""
Fail when a committed docs version still links to ``main`` on GitHub.

A version under ``docs_site/versions/<version>/`` stays published for as long as
the site exists, so a link from it to ``main`` drifts away from the page and
breaks once the file moves. ``build-tag``, ``build-all``, and
``build --docs-version`` rewrite those links to the release the version was
built from (``docs_site/_internal/snapshot_links.py``). This guard fails on any
link to ``main`` that is left in any text file, including forms the rewrite
cannot change, such as ``commits/main``. "Edit this page" links (``edit/main/``)
are allowed, because an edit is always made on ``main``.

Runs only when ``ctx.versions_dir`` is set.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.snapshot_links import unpinned_snapshot_links
from docs_site._internal.versioning import BUILD_INFO_NAME

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    root = ctx.versions_dir
    if root is None or not root.is_dir():
        return
    # Only built versions carry a stamp; alias dirs such as latest/ hold
    # redirect stubs that point inside the tree.
    for version_dir in sorted(d for d in root.iterdir() if d.is_dir() and (d / BUILD_INFO_NAME).is_file()):
        for path, line, link in unpinned_snapshot_links(version_dir):
            yield GuardResult.error(
                guard="snapshot_main_links",
                message=(
                    f"links to main: {link}; rebuild the version with build-tag, "
                    "or change the link to name the release tag"
                ),
                source=path.relative_to(root).as_posix(),
                line=line,
            )
