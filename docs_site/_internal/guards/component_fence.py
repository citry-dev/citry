"""
Flag a ``python`` code fence that defines a Citry component.

A Citry component embeds HTML, JS, and CSS in its ``template`` / ``js`` / ``css``
string attributes. Under a ```python fence those bodies render as one flat
string; the ```citry fence (the pygments-citry lexer) highlights them as real
markup. This guard warns when a component class is still in a ```python fence,
so a later edit does not quietly undo the switch to ```citry.

``fence_defines_component`` is the shared detector: the one-time content
migration that first flipped the fences uses the same predicate, so the guard
and that migration agree on exactly what counts as a component fence.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files, scan_fences

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Fence info-string tokens treated as Python for this check.
_PYTHON_LANGS = frozenset({"python", "py", "python3"})

# A class whose base list names `Component`. `[^)]*` keeps the match inside the
# parentheses, so `class Foo(Bar): x = Component()` on one line is not a hit.
_COMPONENT_CLASS = re.compile(r"^[ \t]*class\s+\w+\([^)]*\bComponent\b", re.MULTILINE)
# Any class definition, used together with the attribute check below.
_CLASS_DEF = re.compile(r"^[ \t]*class\s+\w+\(", re.MULTILINE)
# A component-shaped attribute: template/js/css assigned a string literal (the
# optional `: Type` covers the annotated form `template: "html" = "..."`).
_COMPONENT_ATTR = re.compile(r'^[ \t]*(?:template|js|css)\s*(?::[^=\n]+)?=\s*["\']', re.MULTILINE)


def fence_defines_component(body: str) -> bool:
    """
    Return True if a fenced code body defines a Citry component class.

    Either signal is enough:

    - a class whose bases include ``Component`` (``class Card(Component):``); or
    - any class that assigns a ``template`` / ``js`` / ``css`` string, which
      catches a component subclass whose base is another component
      (``class SpecialCard(BaseCard):``) and so never names ``Component``.

    A bare ``template = "..."`` with no surrounding class is deliberately not a
    match: that is a fragment, not a component definition.
    """
    if _COMPONENT_CLASS.search(body):
        return True
    return bool(_CLASS_DEF.search(body) and _COMPONENT_ATTR.search(body))


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for fence in scan_fences(text):
            if fence.closed and fence.lang in _PYTHON_LANGS and fence_defines_component(fence.body):
                yield GuardResult.warning(
                    guard="component_fence",
                    message="Citry component in a ```python fence; use ```citry to highlight its template/js/css",
                    source=label,
                    line=fence.open_line,
                )
