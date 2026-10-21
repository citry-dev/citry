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
