"""
Cross-reference guard.

An author links an API name with ``[text][key]``, for example
``[`Const`][citry.Const]``. The builder rewrites each one into a link to the
Reference page, but a key it does not know never becomes a link: a page shows
the literal brackets, and a docstring shows only the text. Nothing on the page
says the link was lost, so a renamed symbol or a dropped ``reference.yml`` key
quietly breaks every link to it.

This guard looks up every cross-reference in the Markdown pages and in the
docstrings the Reference pages render, and reports each key the builder cannot
resolve: the page file and line, or the symbol whose docstring holds it.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from docs_site._internal.crossrefs import _CROSSREF_RE, _FENCED_CODE_RE, _SYMBOL_CLEAN_RE, symbol_url_index
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files
from docs_site._internal.project import current_docs_project
from docs_site._internal.reference import is_external_alias, resolve_symbol

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Inline code shows brackets as text (a regex such as `[a-z][a-z0-9]`), so a
# bracket pair that starts inside one is not a cross-reference.
_INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
# A Markdown reference-style link definition, `[label]: /url`. A page that
# defines its own label is using an ordinary Markdown link, not an API key.
_LINK_DEFINITION_RE = re.compile(r"^ {0,3}\[([^\]]+)\]:\s", re.MULTILINE)


def unresolved_crossrefs(text: str, index: dict[str, str], *, skip_code: bool = True) -> Iterator[tuple[str, int]]:
    """
    Yield ``(key, line)`` for each cross-reference in ``text`` that ``index`` lacks.

    With ``skip_code`` (Markdown pages), the scan skips fenced code and bracket
    pairs inside inline code, as the page builder leaves those untouched.
    Without it (docstrings), every bracket pair counts, because the docstring
    renderer rewrites code too. Both modes skip labels the text defines as
    ordinary Markdown links.
    """
    defined = {label.casefold() for label in _LINK_DEFINITION_RE.findall(text)}
    offset = 0
    # re.split with one group alternates prose and fenced code, like the builder.
    parts = _FENCED_CODE_RE.split(text) if skip_code else [text]
    for position, part in enumerate(parts):
        if position % 2 == 0:
            code_spans = [match.span() for match in _INLINE_CODE_RE.finditer(part)] if skip_code else []
            for match in _CROSSREF_RE.finditer(part):
                start = match.start()
                if any(span_start < start < span_end for span_start, span_end in code_spans):
                    continue
                text_part, key = match.group(1), match.group(2)
                # The builder reads the shortcut `[`name`][]` key from its text.
                lookup = key or _SYMBOL_CLEAN_RE.sub("", text_part).removesuffix("()")
                if lookup in index or (key or text_part).casefold() in defined:
                    continue
                yield lookup, text.count("\n", 0, offset + start) + 1
        offset += len(part)


def _docstring_texts(ctx: GuardContext) -> Iterator[tuple[str, str]]:
    """Yield ``(path, text)`` for each docstring a generated Reference page renders."""
    project = ctx.project or current_docs_project()
    for cat in project.reference.categories:
        if cat.source != "griffe":
            continue
        for path in cat.symbols:
            obj = resolve_symbol(path)
            if obj is None:
                continue  # the api_symbols guard reports a symbol that does not resolve
            yield from _own_texts(project, path, obj)
            # Members are walked with the same filter the Reference page uses.
            if obj.kind.value == "class" and not is_external_alias(obj):
                for name, member in obj.members.items():
                    if name.startswith("_") or member.kind.value not in ("function", "attribute"):
                        continue
                    yield from _own_texts(project, f"{path}.{name}", member)


def _own_texts(project: Any, path: str, obj: Any) -> Iterator[tuple[str, str]]:
    # A repository-owned description replaces only the docstring's free text;
    # the parameter, raise, and attribute sections still render from the
    # docstring, so scan both.
    override = project.reference.description_override(path)
    if override:
        yield path, override
    if obj.docstring:
        yield path, obj.docstring.value


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = symbol_url_index()
    for label, text in _source_files(ctx):
        for key, line in unresolved_crossrefs(text, index):
            yield GuardResult.error(
                guard="crossref",
                message=f"Cross-reference key {key!r} does not resolve, so the page shows the literal brackets instead of a link.",
                source=label,
                line=line,
            )
    for path, text in _docstring_texts(ctx):
        for key, _line in unresolved_crossrefs(text, index, skip_code=False):
            yield GuardResult.error(
                guard="crossref",
                message=f"Docstring cross-reference key {key!r} does not resolve, so it renders as plain text.",
                source=path,
            )
