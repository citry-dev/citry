"""
Check the reference pages against citry's public API.

Two directions. Forward (error): every symbol a reference page documents must
resolve, or its ``<c-docstring>`` / ``<c-builtin>`` would render an error stub
instead of real docs. Reverse (warning): every public export of citry should
appear on some reference page; one that does not is almost always a new export
nobody routed to a page yet.

This reads the category lists and the package, not the built site, so it runs
before the post-build checks.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

import citry
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.reference import extract_builtin, extract_symbol
from docs_site._internal.reference_pages import CATEGORIES

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:  # noqa: ARG001 - reads the categories + package, not the build
    # Forward: every documented symbol resolves.
    documented_leaves: set[str] = set()
    for cat in CATEGORIES:
        if cat.source == "builtin":
            for tag in cat.symbols:
                if extract_builtin(tag) is None:
                    yield GuardResult.error(
                        guard="api_symbols",
                        message=f"Documented built-in <c-{tag}> does not resolve in the registry.",
                        source=f"reference/{cat.slug}",
                    )
            continue
        for path in cat.symbols:
            if extract_symbol(path) is None:
                yield GuardResult.error(
                    guard="api_symbols",
                    message=(
                        f"Documented symbol {path!r} does not resolve; its <c-docstring> would render an error stub."
                    ),
                    source=f"reference/{cat.slug}",
                )
            documented_leaves.add(path.split("citry.")[-1])

    # Reverse: every public export is documented somewhere.
    for name in sorted(getattr(citry, "__all__", ())):
        obj = getattr(citry, name, None)
        if obj is None or inspect.ismodule(obj):
            continue  # a re-exported module namespace is not a documentable symbol
        if name in documented_leaves:
            continue
        yield GuardResult.warning(
            guard="api_symbols",
            message=f"Public API symbol {name!r} is exported from citry but is not on any reference page.",
            source="citry/__init__.py",
        )
