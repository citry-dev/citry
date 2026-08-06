"""
Invalid-CSS guard for the built pages' inline styles.

Catches one specific corruption that a build can introduce after the stylesheet
is authored: a custom property immediately followed by the next value, as in
``var(--bg)0%`` or ``var(--rail)minmax(0,1fr)``. CSS requires a space there, and
without it the browser discards the whole declaration, so a gradient or a grid
track list silently stops applying while the page still builds and every other
check still passes.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# A var() reference butted straight against the value that should follow it.
_GLUED_VAR_RE = re.compile(r"var\(--[a-zA-Z0-9_-]+\)(?=[0-9a-zA-Z.#])")

_MAX_REPORTED = 3


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if page.is_redirect_stub or not page.glued_css_vars:
            continue
        shown = page.glued_css_vars[:_MAX_REPORTED]
        extra = len(page.glued_css_vars) - len(shown)
        detail = "; ".join(repr(sample) for sample in shown)
        if extra > 0:
            detail += f"; and {extra} more"
        yield GuardResult.error(
            guard="rendered_css",
            message=(
                f"Invalid CSS: a custom property is glued to the value after it ({detail}). "
                "The browser drops the whole declaration, so the rule stops applying."
            ),
            source=page.label,
        )
