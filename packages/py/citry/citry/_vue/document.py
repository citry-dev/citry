"""Select a physical document shell directly from the final typed render tree."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from citry.citry_render import CitryRender, Placeholder
from citry.util.html import Markup, escape_to_str

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry._vue.capture import PreparedElementOpen


@dataclass(frozen=True, slots=True)
class TypedDocumentShell:
    """The materialized physical shell and render IDs excluded from Vue."""

    html: str
    head_only_render_ids: frozenset[str]


def typed_document_shell(render: CitryRender, host_html: str) -> TypedDocumentShell | None:
    """Replace one selected typed ``body`` contribution without parsing rendered HTML."""
    from citry._vue.capture import (  # noqa: PLC0415
        PreparedDynamicElementClose,
        PreparedDynamicElementOpen,
        PreparedElementClose,
        PreparedElementOpen,
        PreparedSourceText,
        PreparedStaticRun,
        PreparedTextValue,
        PreparedTrustedHtmlValue,
        PreparedVerbatimHtml,
    )
    from citry._vue.leaf_program import PreparedLeafProgram  # noqa: PLC0415
    from citry.slots import _EscapedSlotText  # noqa: PLC0415

    output: list[str] = []
    body_depth = 0
    body_count = 0
    document_marker = False
    unsupported_before_document: list[str] = []
    states_by_render: dict[str, set[str]] = {}
    active_render_ids: list[str] = []

    def contains_document(parts: Iterable[object]) -> bool:
        for part in parts:
            if isinstance(part, CitryRender) and contains_document(part.parts):
                return True
            if isinstance(part, PreparedElementOpen) and part.tag.lower() in {"html", "head", "body"}:
                return True
            if isinstance(
                part,
                (PreparedSourceText, PreparedStaticRun, PreparedTrustedHtmlValue, PreparedVerbatimHtml),
            ):
                text = part.text if isinstance(part, PreparedSourceText) else part.html
                if text.lstrip().lower().startswith("<!doctype"):
                    return True
        return False

    document_hint = contains_document((render,))

    def record_region(region: str) -> None:
        for render_id in active_render_ids:
            states_by_render.setdefault(render_id, set()).add(region)

    def visit(parts: Iterable[object]) -> None:
        nonlocal body_count, body_depth, document_marker
        for part in parts:
            if isinstance(part, CitryRender):
                render_id = part.frame.render_id
                if render_id is not None:
                    active_render_ids.append(render_id)
                visit(part.parts)
                if render_id is not None:
                    active_render_ids.pop()
                continue
            if isinstance(part, PreparedElementOpen):
                tag = part.tag.lower()
                if (
                    document_hint
                    and not body_depth
                    and tag != "body"
                    and any(attr.name.startswith(("@c-", ":c-", "v-", "@", ":", "#")) for attr in part.attrs)
                ):
                    raise ValueError("Interactive Vue bindings are unsupported in the physical document head.")
                if tag in {"html", "head", "body"}:
                    document_marker = True
                if tag == "body":
                    body_count += 1
                    if body_count != 1 or body_depth:
                        raise ValueError("Interactive Vue document serialization requires exactly one body element.")
                    body_depth = 1
                    output.append(_open_html(part))
                    output.append(host_html)
                    record_region("body")
                    continue
                if body_depth:
                    record_region("body")
                    continue
                record_region("head")
                output.append(_open_html(part))
                continue
            if isinstance(part, PreparedElementClose):
                tag = part.tag.lower()
                if body_depth:
                    if tag == "body":
                        body_depth = 0
                        output.append(f"</{part.tag}>")
                    record_region("body")
                    continue
                record_region("head")
                output.append(f"</{part.tag}>")
                continue
            if isinstance(part, (PreparedDynamicElementOpen, PreparedDynamicElementClose)):
                if body_depth:
                    record_region("body")
                    continue
                if not document_marker:
                    unsupported_before_document.append(type(part).__name__)
                    continue
                raise TypeError(f"interactive document shell received unsupported typed part {type(part).__name__}")
            text_part = isinstance(
                part,
                (
                    PreparedSourceText,
                    PreparedStaticRun,
                    PreparedTextValue,
                    PreparedTrustedHtmlValue,
                    PreparedVerbatimHtml,
                ),
            )
            if body_depth and text_part:
                record_region("body")
                continue
            if body_depth and isinstance(part, PreparedLeafProgram):
                record_region("body")
                continue
            if body_depth and type(part) in {Markup, _EscapedSlotText}:
                # Markup is already trusted by the ordinary rendering
                # contract. The physical shell still cannot infer structure
                # from it, but Vue replaces all content inside the typed body.
                record_region("body")
                continue
            if isinstance(part, PreparedSourceText):
                text = part.text
            elif isinstance(part, PreparedStaticRun):
                text = part.html
            elif isinstance(part, PreparedTextValue):
                text = escape_to_str(part.value)
            elif isinstance(part, (PreparedTrustedHtmlValue, PreparedVerbatimHtml)):
                text = part.html
            elif isinstance(part, Placeholder):
                if part.key not in {"deps:css", "deps:js"}:
                    raise TypeError("interactive document shell cannot contain an unresolved placeholder")
                record_region("body" if body_depth else "head")
                continue
            elif part == "" and type(part) is str:
                # ``None`` has always rendered as the exact empty string. It
                # carries no markup or ownership and is safe to erase here.
                continue
            else:
                if not document_marker and not body_depth:
                    unsupported_before_document.append(type(part).__name__)
                    continue
                raise TypeError(f"interactive document shell received unsupported typed part {type(part).__name__}")
            if text.lstrip().lower().startswith("<!doctype"):
                document_marker = True
            record_region("head")
            output.append(text)

    visit((render,))
    if not document_marker:
        return None
    if unsupported_before_document:
        raise TypeError(f"interactive document shell received unsupported typed part {unsupported_before_document[0]}")
    if body_count != 1 or body_depth:
        raise ValueError("Interactive Vue document serialization requires one well-ordered body element.")
    head_only = frozenset(render_id for render_id, regions in states_by_render.items() if regions == {"head"})
    return TypedDocumentShell("".join(output), head_only)


def _open_html(part: PreparedElementOpen) -> str:
    from citry._vue.capture import format_prepared_element_attrs  # noqa: PLC0415

    authored = list(format_prepared_element_attrs(part))
    attrs = "" if not authored else " " + " ".join(authored)
    ending = "/>" if part.is_self_closing else ">"
    return f"<{part.tag}{attrs}{ending}"
