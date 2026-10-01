"""Typed prepared-output traversal for compound-component validators."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Protocol

from citry import CitryRender
from citry._vue.capture import (
    PreparedDynamicElementClose,
    PreparedDynamicElementOpen,
    PreparedElementClose,
    PreparedElementOpen,
    PreparedSourceText,
    PreparedStaticRun,
    PreparedTextValue,
    PreparedTrustedHtmlValue,
)
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts

if TYPE_CHECKING:
    from collections.abc import Callable


class DirectOutputParser(Protocol):
    invalid: bool

    def feed_text(self, text: str) -> None: ...


def feed_typed_direct_output(
    parser: DirectOutputParser,
    part: object,
    expected_render_ids: frozenset[str],
    enter: Callable[[str], None],
    exit_render: Callable[[str], None],
) -> None:
    """Feed prepared output through an existing structural HTML parser."""
    if isinstance(part, str):
        parser.feed_text(part)
        return
    if isinstance(part, PreparedSourceText):
        parser.feed_text(part.text)
        return
    if isinstance(part, PreparedStaticRun):
        parser.feed_text(part.html)
        return
    if isinstance(part, PreparedTextValue):
        parser.feed_text(escape(str(part.value)))
        return
    if isinstance(part, PreparedTrustedHtmlValue):
        parser.feed_text(part.html)
        return
    if isinstance(part, PreparedElementOpen):
        suffix = "/" if part.is_self_closing else ""
        parser.feed_text(f"<{part.tag}{suffix}>")
        return
    if isinstance(part, PreparedDynamicElementOpen):
        parser.feed_text(f"<{part.tag}>")
        return
    if isinstance(part, PreparedDynamicElementClose):
        parser.feed_text(f"</{part.tag}>")
        return
    if isinstance(part, PreparedElementClose):
        parser.feed_text(f"</{part.tag}>")
        return
    if isinstance(part, PreparedLeafProgram):
        for child in typed_leaf_parts(part):
            feed_typed_direct_output(parser, child, expected_render_ids, enter, exit_render)
        return
    if not isinstance(part, CitryRender):
        parser.invalid = True
        return

    render_id = part.frame.render_id
    is_expected_root = part.is_component_root and render_id in expected_render_ids
    if is_expected_root and render_id is not None:
        enter(render_id)
    for child in part.parts:
        feed_typed_direct_output(parser, child, expected_render_ids, enter, exit_render)
    if is_expected_root and render_id is not None:
        exit_render(render_id)
