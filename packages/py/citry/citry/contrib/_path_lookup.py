"""
Helpers the framework integrations share when they answer whether the host app serves a path.

Each integration registers a path checker (see ``citry._path_checks``): a
function that takes one root-relative path and says whether one of the
host's routes or static files serves it. For a missing static file, the
checker also lists the files that do exist beside it, so ``citry check`` can
suggest the one a misspelled link meant.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def files_beside(path: str, folders: Iterable[str | os.PathLike[str]]) -> tuple[str, ...]:
    """
    Return a URL for each file in ``folders``, made by swapping the last segment of ``path`` for the file's name.

    ``folders`` are the folders on disk that hold the files the parent URL of
    ``path`` serves, already confirmed by the caller to lie inside a static
    folder. A file name found in several of them is listed once.
    """
    # The suggestion replaces only the last segment of what the template
    # wrote, so it keeps the template's own spelling of the folder part.
    parent = path.rsplit("/", 1)[0]
    names: set[str] = set()
    for folder in folders:
        try:
            entries = os.scandir(folder)
        except (OSError, ValueError):
            # A folder that vanished or cannot be read, or a name holding a
            # null character, offers no suggestion; the verdict for the path
            # itself is already decided.
            continue
        with entries:
            names.update(entry.name for entry in entries if entry.is_file())
    # Sorted, so the suggestion picked from these does not depend on disk order.
    return tuple(f"{parent}/{name}" for name in sorted(names))


def path_below(path: str, sub_path: str) -> str | None:
    """
    Return a link ``path`` as the app's routes see it, or ``None`` when ``path`` is not below ``sub_path``.

    ``sub_path`` is the sub-path the app is served below, such as ``/shop``,
    or ``""`` for the site root, as the integration's sub-path reader
    returns it (``citry._sub_path.normalize_sub_path``), so the link check
    reads the same sub-path Citry starts its own URLs with.
    Links in templates start with the sub-path, while the app's routes are
    written without it, so the checker removes it before it asks the
    framework. The sub-path alone gives ``""``, which each framework
    handles in its own way.
    """
    prefix = sub_path
    if not prefix:
        return path
    if path == prefix:
        return ""
    # "/shopping" starts with "/shop" but is a different page, so the
    # sub-path must be followed by a "/".
    if path.startswith(f"{prefix}/"):
        return path[len(prefix) :]
    return None
