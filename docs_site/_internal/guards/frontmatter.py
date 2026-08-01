"""
Strict front-matter validator.

A content page may open with a ``---`` block of ``key: value`` lines. The page
layout only reads a fixed set of keys (see ``PageMeta`` in ``frontmatter.py``),
and each key has a type: ``boost`` is a number, ``noindex`` and ``searchable``
are booleans, the rest are free-form text. ``parse_page`` is lenient - it
silently coerces a bad value to the field default - so a typo like ``boost:
hihg`` or ``noindex: mabye`` would otherwise slip through and quietly do
nothing. This guard surfaces those:

- a value that cannot parse to its declared type -> error
- a key the layout does not recognise -> warning (usually a typo)

The known keys and their types are read straight from ``PageMeta``, and the
boolean tokens from the same sets ``parse_page`` uses, so this guard stays in
lockstep with the real parser instead of keeping a second copy that could drift.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, get_type_hints

from docs_site._internal import frontmatter
from docs_site._internal.frontmatter import PageMeta
from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_GUARD = "frontmatter"

# The keys the layout understands, mapped to their declared type, read straight
# from PageMeta so this set can never drift from the real schema. ``body`` is
# the page body that parse_page fills in, not a front-matter key, so it is left
# out.
_SCHEMA: dict[str, type] = {name: typ for name, typ in get_type_hints(PageMeta).items() if name != "body"}

# The exact tokens parse_page accepts for a boolean key (reused, not re-copied,
# so a change to the accepted spellings reaches this guard automatically).
_BOOL_TOKENS = frontmatter._TRUTHY | frontmatter._FALSY


def _type_error(key: str, value: str, declared: type) -> str | None:
    """Return an error message if ``value`` cannot parse to ``declared``, else ``None``."""
    # An empty value means "unset": parse_page falls back to the field default
    # for it, so the guard treats it the same and does not flag it. You would
    # just omit the key rather than write it blank.
    if value == "":
        return None
    if declared is bool and value.lower() not in _BOOL_TOKENS:
        expected = ", ".join(sorted(_BOOL_TOKENS))
        return f"{key}: {value!r} is not a boolean (expected one of: {expected})"
    if key == "layout" and value not in frontmatter._LAYOUTS:
        expected = ", ".join(sorted(frontmatter._LAYOUTS))
        return f"{key}: {value!r} is not a known layout (expected one of: {expected})"
    if declared is float:
        try:
            float(value)
        except ValueError:
            return f"{key}: {value!r} is not a number"
    return None


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    content_dir = ctx.content_dir
    if not content_dir.is_dir():
        return

    for md in sorted(content_dir.rglob("*.md")):
        rel = md.relative_to(content_dir)
        if len(rel.parts) == 2 and rel.parts[0] == "blog" and md.name != "index.md":
            # Dated posts use the stricter Blog schema and are checked by the
            # Blog catalog guard. The ordinary PageMeta parser intentionally
            # does not know about editorial keys such as date and author.
            continue
        front, _body = frontmatter._split_front_matter(md.read_text(encoding="utf-8"))
        source = rel.as_posix()
        # Iterating the dict walks the keys in the order they appear in the
        # file (dicts keep insertion order), so the report is deterministic.
        for key, value in front.items():
            declared = _SCHEMA.get(key)
            if declared is None:
                yield GuardResult.warning(
                    guard=_GUARD,
                    message=f"Unknown front-matter key {key!r} (not read by the page layout)",
                    source=source,
                )
                continue
            message = _type_error(key, value, declared)
            if message is not None:
                yield GuardResult.error(guard=_GUARD, message=message, source=source)
