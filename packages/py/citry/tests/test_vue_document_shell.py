from __future__ import annotations

import pytest

from citry import Component, Markup, Slot
from citry._vue.capture import PreparedElementClose, PreparedElementOpen, PreparedSourceText, render_prepared_direct
from citry._vue.document import typed_document_shell
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender


def _open(tag: str) -> PreparedElementOpen:
    return PreparedElementOpen(
        source="",
        span=(0, 0),
        tag=tag,
        attrs=(),
        is_void=False,
        is_self_closing=False,
        element_metadata={},
    )


def _close(tag: str) -> PreparedElementClose:
    return PreparedElementClose("", (0, 0), tag)


def _document(*body: object, head: tuple[object, ...] = ()) -> CitryRender:
    return CitryRender(
        parts=[
            PreparedSourceText("<!doctype html>", (0, 15), "<!doctype html>"),
            _open("html"),
            _open("head"),
            *head,
            _close("head"),
            _open("body"),
            *body,
            _close("body"),
            _close("html"),
        ],
        context=CitryContext(),
    )


def test_trusted_markup_inside_typed_body_is_replaced_with_host() -> None:
    shell = typed_document_shell(
        _document(Markup('<span onclick="trusted()">body</span>')),
        '<div id="host"></div>',
    )

    assert shell is not None
    assert shell.html == ('<!doctype html><html><head></head><body><div id="host"></div></body></html>')


def test_plain_slot_text_inside_document_body_remains_escaped_and_is_replaced_with_host() -> None:
    class Page(Component):
        template = """
          <!doctype html>
          <html><head></head><body><c-slot /></body></html>
        """

    rendered = render_prepared_direct(Page(slots={"default": Slot("<unsafe>")}))
    shell = typed_document_shell(rendered, '<div id="host"></div>')

    assert shell is not None
    assert shell.html == '\n<!doctype html>\n<html><head></head><body><div id="host"></div></body></html>\n'


def test_trusted_markup_cannot_supply_or_modify_physical_shell() -> None:
    with pytest.raises(TypeError, match="unsupported typed part Markup"):
        typed_document_shell(
            CitryRender(
                parts=[Markup("<!doctype html>"), _open("body"), _close("body")],
                context=CitryContext(),
            ),
            '<div id="host"></div>',
        )

    with pytest.raises(TypeError, match="unsupported typed part Markup"):
        typed_document_shell(
            _document(head=(Markup("</head><body>injected"),)),
            '<div id="host"></div>',
        )


def test_trusted_markup_fragment_does_not_select_a_document_shell() -> None:
    rendered = CitryRender(parts=[Markup("<b>trusted</b>")], context=CitryContext())

    assert typed_document_shell(rendered, '<div id="host"></div>') is None
