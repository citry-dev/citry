"""
Cross-reference resolution for docstrings and content.

Authors write bracket cross-refs - ``[Component][citry.Component]`` or the
shorthand ``[`Component`][]`` (the key is parsed from the text) - and this
rewrites them, in the markdown before it becomes HTML, to links into the API
reference. An unknown key degrades to its plain text in docstrings (which we
author) and is left literal in content (so ``arr[i][j]`` survives).

Links are root-absolute (``/reference/...``), matching the site's other
absolute links, so a docstring needs no page context to resolve. The same
symbol index also builds the Sphinx ``objects.inv`` so other sites can link in.
"""

from __future__ import annotations

import re
import zlib
from functools import lru_cache
from typing import TYPE_CHECKING

from docs_site._internal.inventory import external_inventory
from docs_site._internal.reference_pages import CATEGORIES

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# [text][key] and the shortcut [text][] (the key is parsed from the text).
_CROSSREF_RE = re.compile(r"\[([^\]\[]+)\]\[([^\]\[]*)\]")
# Strip backticks / whitespace / a trailing "()" so [`render()`][] keys off "render".
_SYMBOL_CLEAN_RE = re.compile(r"[`\s]")
# Fenced code blocks; cross-refs are never resolved inside these.
_FENCED_CODE_RE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)


@lru_cache(maxsize=1)
def symbol_url_index() -> dict[str, str]:
    """
    Map a cross-ref key to a reference URL+anchor.

    Keyed by dotted path, short name, and member forms (``Component.render`` and
    ``citry.Component.render``), mirroring the anchors the pages render.
    """
    # Lazy: reference imports this module (for docstring rendering), so importing
    # it back at module load would be a cycle. By call time it is fully loaded.
    from docs_site._internal.reference import anchor, reference_anchor_map, resolve_symbol  # noqa: PLC0415

    # The same per-page-unique anchors the reference pages render, so a link and
    # its target id always match (e.g. the citry instance, not the Citry class).
    anchors = reference_anchor_map()
    index: dict[str, str] = {}

    # Pass 1: entry-level keys (a symbol's own page wins over a same-named member).
    for cat in CATEGORIES:
        base = f"/reference/{cat.slug}/"
        if cat.source == "builtin":
            for tag in cat.symbols:
                url = f"{base}#{anchor(f'c-{tag}')}"
                index.setdefault(f"c-{tag}", url)
                index.setdefault(tag, url)
            continue
        for path in cat.symbols:
            url = f"{base}#{anchors.get(path, anchor(path))}"
            index[path] = url
            index.setdefault(path.split(".")[-1], url)

    # Pass 2: member keys (classes only).
    for cat in CATEGORIES:
        if cat.source != "griffe":
            continue
        base = f"/reference/{cat.slug}/"
        for path in cat.symbols:
            obj = resolve_symbol(path)
            if obj is None or getattr(obj, "kind", None) is None or obj.kind.value != "class":
                continue
            leaf = path.split(".")[-1]
            for member_name, member in obj.members.items():
                if member_name.startswith("_") or member.kind.value not in ("function", "attribute"):
                    continue
                member_path = f"{path}.{member_name}"
                member_url = f"{base}#{anchors.get(member_path, anchor(member_path))}"
                index.setdefault(f"{leaf}.{member_name}", member_url)
                index.setdefault(member_path, member_url)

    return index


def resolve_crossrefs(md: str, *, degrade_unresolved: bool = True) -> tuple[str, list[str]]:
    """
    Rewrite ``[text][key]`` cross-refs in a markdown string.

    Returns the rewritten markdown and the unresolved keys. ``degrade_unresolved``
    True (docstrings) renders the plain text for an unknown key; False (content)
    leaves the original ``[text][key]`` so a non-ref bracket pair survives.
    """
    index = symbol_url_index()
    unresolved: list[str] = []

    def replace(match: re.Match[str]) -> str:
        text, key = match.group(1), match.group(2)
        lookup = key or _SYMBOL_CLEAN_RE.sub("", text).removesuffix("()")
        target = index.get(lookup)
        if target is not None:
            return f"[{text}]({target})"
        unresolved.append(lookup)
        return text if degrade_unresolved else match.group(0)

    return _CROSSREF_RE.sub(replace, md), unresolved


def resolve_crossrefs_in_prose(md: str) -> tuple[str, list[str]]:
    """Resolve cross-refs across a whole content page, skipping fenced code, leaving unknowns literal."""
    parts = _FENCED_CODE_RE.split(md)
    unresolved: list[str] = []
    # re.split with one group -> [prose, fence, prose, ...]; even indices are prose.
    for i in range(0, len(parts), 2):
        resolved, missing = resolve_crossrefs(parts[i], degrade_unresolved=False)
        parts[i] = resolved
        unresolved.extend(missing)
    return "".join(parts), unresolved


def _inventory_candidates(canonical_path: str) -> Iterator[str]:
    """
    Public-path candidates for an external-inventory lookup, most specific first.

    griffe hands us the definition's own module path (``foo.bar.baz.Thing``) while
    a Sphinx inventory keys the public re-export (``foo.Thing``). So after the exact
    path we also try dropping the innermost module segments one at a time, keeping
    the leaf name, until a shorter public form matches.
    """
    parts = canonical_path.split(".")
    if len(parts) < 2:  # a bare name has nothing to shorten
        yield canonical_path
        return
    leaf, mods = parts[-1], parts[:-1]
    for i in range(len(mods), 0, -1):
        yield ".".join([*mods[:i], leaf])


def resolve_external_url(name: str, canonical_path: str) -> str | None:
    """Resolve a type against the external (Python stdlib) inventory, or ``None``."""
    inventory = external_inventory()
    for candidate in _inventory_candidates(canonical_path):
        if candidate in inventory:
            return inventory[candidate]
    # A bare builtin (``dict``, ``str``) is keyed under its own name in the inventory.
    return inventory.get(name)


def make_type_resolver(current_url: str | None = None) -> Callable[[str, str], str | None]:  # noqa: ARG001
    """
    Build the resolver the annotation renderer uses to link types in a signature.

    A referenced type resolves to the internal reference index first (a type we
    document on our own pages), then to the external Python inventory; an unknown
    type resolves to ``None`` and renders as plain text. ``current_url`` is accepted
    for a uniform resolver signature; citry's reference links are root-absolute, so
    a page needs no relative rewriting.
    """
    index = symbol_url_index()

    def resolve(name: str, canonical_path: str) -> str | None:
        # The index is keyed by short leaf name and __all__ dotted path, so the leaf
        # is the usual hit and the canonical path is only a rare exact match.
        internal = index.get(name) or index.get(canonical_path)
        if internal is not None:
            return internal
        return resolve_external_url(name, canonical_path)

    return resolve


def build_objects_inv(version: str, *, project: str = "citry") -> bytes:
    """Build a Sphinx v2 ``objects.inv`` for citry's symbols (so other sites can link in)."""
    entries = sorted(
        (name, url.lstrip("/")) for name, url in symbol_url_index().items() if name.startswith(("citry.", "c-"))
    )
    header = (
        f"# Sphinx inventory version 2\n"
        f"# Project: {project}\n"
        f"# Version: {version}\n"
        f"# The remainder of this file is compressed using zlib.\n"
    ).encode()
    lines = "".join(f"{name} py:obj -1 {url} -\n" for name, url in entries)
    return header + zlib.compress(lines.encode("utf-8"), 9)
