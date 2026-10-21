"""
Lint rules that need the loaded application.

``citry check`` runs these only with the component registry, because each one
needs a fact that a template alone does not show: which class a component tag
renders, whether that class uses Vue, or which data class a server event
handler validates its arguments with.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from citry._browser_expressions import (
    _ascii_lower,
    _browser_object_literal,
    _conditional_branches,
    _javascript_number,
    _nested_template,
    _plain_string_literal_text,
)
from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD,
    BROWSER_MISSING_SERVER_EVENT_FIELD,
    BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
)
from citry._diagnostics import render_diagnostic
from citry._markup_lint import one_slip_from
from citry.ext.events.schemas import json_value_error, payload_fields
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry_core.template_parser import Template


@dataclass(frozen=True, slots=True)
class RepeatedComponentCall:
    """One component tag that a ``<c-for>`` repeats and that has no ``#c-key``."""

    tag: str
    start_index: int
    end_index: int


def unkeyed_repeated_component_calls(
    template: Template,
    *,
    parse_nested: Callable[[str], Template],
) -> tuple[RepeatedComponentCall, ...]:
    """
    Return the component tags inside a ``<c-for>`` body, or with ``c-for`` themselves, that have no ``#c-key``.

    Each tag is returned as written, spanning its name. The caller decides
    which of them render a component that needs a key.
    """
    found: list[RepeatedComponentCall] = []
    _collect_repeated_calls(template, found, parse_nested=parse_nested, base_index=0, in_loop=False)
    return tuple(found)


def _collect_repeated_calls(
    template: Template,
    found: list[RepeatedComponentCall],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    in_loop: bool,
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = node.start_tag.name.content
        lower = _ascii_lower(tag)
        names = {_ascii_lower(attr.key.content) for attr in node.start_tag.attrs}
        # A `<c-empty>` is the loop's sibling, so its body repeats only when
        # an outer loop repeats it.
        repeats = in_loop or lower == "c-for" or "c-for" in names
        component = lower.startswith("c-") and lower != "c-element" and lower not in RESERVED_TAG_NAMES
        if repeats and component and "#c-key" not in names:
            found.append(
                RepeatedComponentCall(
                    tag,
                    base_index + node.start_tag.name.start_index,
                    base_index + node.start_tag.name.end_index,
                )
            )
        # A keyed component call tells each repetition of everything inside
        # it apart, so the calls in its body and fills need no key of their
        # own. A key on a plain element does not do that for the runtime.
        inner_loop = repeats and not (component and "#c-key" in names)
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            # A template-valued attribute renders wherever its element does,
            # so a call inside it repeats with the element.
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_repeated_calls(
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                        in_loop=inner_loop,
                    )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_repeated_calls(
                body,
                found,
                parse_nested=parse_nested,
                base_index=base_index,
                in_loop=inner_loop,
            )


def template_has_vue_attributes(template: Template, *, parse_nested: Callable[[str], Template]) -> bool:
    """
    Return whether any tag in a template has a Vue attribute: a ``v-*``, ``@``, or ``:`` name.

    Such an attribute, including Citry's ``@c-*`` and ``:c-*`` bindings,
    makes the page that renders the template use Vue.
    """
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        for attr in node.start_tag.attrs:
            if attr.key.content.startswith(("v-", "@", ":")):
                return True
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None and template_has_vue_attributes(nested[0], parse_nested=parse_nested):
                    return True
        body = getattr(node, "body", None)
        if body is not None and template_has_vue_attributes(body, parse_nested=parse_nested):
            return True
    return False


@dataclass(frozen=True, slots=True)
class ServerEventCall:
    """
    One ``@c-*`` binding that calls a server event handler.

    Attributes:
        handler: The handler's wire name.
        event: The DOM event, such as ``click`` for ``@c-click.prevent``.
        element: The tag the binding is on, as written.
        arguments: The text between the call's parentheses, or None when the
            binding sends no arguments, as ``save`` and ``save()`` do.
        arguments_start: The byte offset of ``arguments`` in the template.
        start_index: The byte offset where the handler name starts.
        end_index: The byte offset where the handler name ends.

    """

    handler: str
    event: str
    element: str
    arguments: str | None
    arguments_start: int
    start_index: int
    end_index: int


def server_event_calls(
    template: Template,
    handler_names: frozenset[str],
    *,
    parse_nested: Callable[[str], Template],
) -> tuple[ServerEventCall, ...]:
    """Return every ``@c-*`` binding whose handler is one of ``handler_names``, with its written arguments."""
    found: list[ServerEventCall] = []
    _collect_server_event_calls(template, found, handler_names, parse_nested=parse_nested, base_index=0)
    return tuple(found)


def _collect_server_event_calls(
    template: Template,
    found: list[ServerEventCall],
    handler_names: frozenset[str],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None:
                continue
            if attr.kind == HtmlAttrKind.Template:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_server_event_calls(
                        parsed,
                        found,
                        handler_names,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
                continue
            if not attr.key.content.startswith("@c-"):
                continue
            call = _server_event_call(inner.content, handler_names)
            if call is None:
                continue
            handler, handler_start, arguments, arguments_offset = call
            start = base_index + inner.start_index
            found.append(
                ServerEventCall(
                    handler=handler,
                    event=attr.key.content[len("@c-") :].split(".", 1)[0],
                    element=node.start_tag.name.content,
                    arguments=arguments,
                    arguments_start=start + len(inner.content[:arguments_offset].encode("utf-8")),
                    start_index=start + len(inner.content[:handler_start].encode("utf-8")),
                    end_index=start + len(inner.content[: handler_start + len(handler)].encode("utf-8")),
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_server_event_calls(body, found, handler_names, parse_nested=parse_nested, base_index=base_index)


def _server_event_call(value: str, handler_names: frozenset[str]) -> tuple[str, int, str | None, int] | None:
    """
    Split a binding value into its handler, the handler's offset, its arguments, and their offset.

    This follows the runtime: a complete handler name wins, otherwise the
    call runs from the first ``(`` to a final ``)``, and empty parentheses
    send no arguments.
    """
    stripped = value.strip()
    leading = len(value) - len(value.lstrip())
    if stripped in handler_names:
        return stripped, leading, None, leading + len(stripped)
    open_index = stripped.find("(")
    if open_index < 0 or not stripped.endswith(")"):
        return None
    handler = stripped[:open_index].strip()
    if handler not in handler_names:
        return None
    arguments = stripped[open_index + 1 : -1]
    return handler, leading, (arguments if arguments.strip() else None), leading + open_index + 1


# Elements whose content cannot include a `<form>`, so an event on one of
# them never has a form as its target. A call without arguments from any
# other element may send a form's fields instead of nothing.
_ELEMENTS_WITHOUT_FORMS = frozenset(
    {
        "abbr",
        "b",
        "button",
        "code",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "i",
        "img",
        "input",
        "label",
        "option",
        "p",
        "select",
        "small",
        "span",
        "strong",
        "summary",
        "textarea",
    }
)


@dataclass(frozen=True, slots=True)
class ServerEventPayloadFinding:
    """One mistake in the arguments an ``@c-*`` binding sends to a server event."""

    code: str
    message: str
    start_index: int
    end_index: int


def server_event_payload_findings(
    call: ServerEventCall,
    data_class: type | None,
    *,
    query_string: bool = False,
) -> tuple[ServerEventPayloadFinding, ...]:
    """
    Compare the arguments one ``@c-*`` binding writes with its handler's data class.

    The server checks the arguments against the data class before the
    handler runs and rejects the call on any mistake, so each finding here
    is a call that always fails. Only what the template proves is checked:

    - a key of an object literal that the data class does not declare, or
      any key when the handler takes no ``data``;
    - a required field that an object literal with no ``...`` spread or
      computed key leaves out, or that a call without arguments leaves out,
      unless the browser may send a form's fields instead;
    - a literal value, or a condition whose two results are literals, that
      the server's own check for that field rejects.

    A Pydantic data class is skipped: Pydantic ignores extra keys and
    converts values by its own rules.

    Args:
        call: One binding, from ``server_event_calls``.
        data_class: The handler's ``data`` annotation, or None when the
            handler takes no ``data``.
        query_string: Whether the browser may send the arguments as a GET
            query string, which the server reads as text, so `'2'` fits an
            `int` field. A value is then reported only when both ways of
            sending it fail.

    Returns:
        Findings in source order.

    """
    fields = None if data_class is None else payload_fields(data_class)
    if data_class is not None and fields is None:
        return ()
    accepted = {} if fields is None else {field.name: field for field in fields}
    if call.arguments is None:
        # The browser sends a form's fields when the event comes from a
        # `<form>`, which any other element but these may contain.
        if call.event == "submit" or _ascii_lower(call.element) not in _ELEMENTS_WITHOUT_FORMS:
            return ()
        return tuple(_missing_field(call, name) for name, field in accepted.items() if field.required)
    parsed = _browser_object_literal(call.arguments.strip(), base_index=0)
    if parsed is None:
        return ()
    properties, dynamic = parsed
    # The object literal's offsets count from its first non-space character.
    base = call.arguments_start + len(call.arguments[: len(call.arguments) - len(call.arguments.lstrip())].encode())
    findings: list[ServerEventPayloadFinding] = []
    written = {item.name for item in properties}
    # JavaScript keeps the last of two equal keys, so only its value is sent.
    sent = {item.name: item for item in properties}
    for item in properties:
        field = accepted.get(item.name)
        if field is None:
            findings.append(_unknown_field(call, item.name, data_class, accepted, base, item))
            continue
        if sent[item.name] is not item:
            continue
        detail = _rejected_literal(field.annotation, item.value_source, query_string=query_string)
        if detail is not None:
            findings.append(
                ServerEventPayloadFinding(
                    BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD,
                    render_diagnostic(
                        BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD,
                        name=item.name,
                        event=call.handler,
                        detail=detail,
                    ),
                    base + item.value_start_index,
                    base + item.value_end_index,
                )
            )
    if not dynamic:
        findings.extend(
            _missing_field(call, name) for name, field in accepted.items() if field.required and name not in written
        )
    return tuple(sorted(findings, key=lambda item: (item.start_index, item.end_index)))


def _unknown_field(
    call: ServerEventCall,
    name: str,
    data_class: type | None,
    accepted: Mapping[str, Any],
    base: int,
    item: Any,
) -> ServerEventPayloadFinding:
    if data_class is None:
        message = render_diagnostic(
            BROWSER_UNKNOWN_SERVER_EVENT_FIELD, variant="no-data", name=name, event=call.handler
        )
    else:
        suggestion = next((field for field in accepted if one_slip_from(name, field)), None)
        message = (
            render_diagnostic(BROWSER_UNKNOWN_SERVER_EVENT_FIELD, name=name, event=call.handler)
            if suggestion is None
            else render_diagnostic(
                BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
                variant="suggestion",
                name=name,
                event=call.handler,
                suggestion=suggestion,
            )
        )
    return ServerEventPayloadFinding(
        BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
        message,
        base + item.start_index,
        base + item.end_index,
    )


def _missing_field(call: ServerEventCall, name: str) -> ServerEventPayloadFinding:
    return ServerEventPayloadFinding(
        BROWSER_MISSING_SERVER_EVENT_FIELD,
        render_diagnostic(BROWSER_MISSING_SERVER_EVENT_FIELD, name=name, event=call.handler),
        call.start_index,
        call.end_index,
    )


# What a missing value is, so a literal that names nothing is told apart.
_NOT_A_LITERAL = object()


def _rejected_literal(annotation: Any, source: str, *, query_string: bool) -> str | None:
    """Return the server's message for a literal value it rejects, checking both results of a condition."""
    branches = _conditional_branches(source.strip())
    candidates = branches if branches is not None else (source,)
    values = [_json_literal_value(candidate) for candidate in candidates]
    # Only a value the template spells out completely can be checked.
    if any(value is _NOT_A_LITERAL for value in values):
        return None
    for value in values:
        error = json_value_error(annotation, value)
        # A query string carries the value as text, which the server binds
        # more loosely, so the call fails only when that fails too. The
        # browser cannot put null in a query string at all.
        if error is not None and query_string and value is not None:
            error = json_value_error(annotation, _query_text(value), bind_strings=True)
        if error is not None:
            return error
    return None


def _query_text(value: object) -> str:
    """Write a JSON scalar the way the browser writes it into a GET query string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _json_literal_value(source: str) -> object:
    """Return the value a JavaScript literal arrives as after JSON, or ``_NOT_A_LITERAL``."""
    value = source.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if _javascript_number(value):
        number = float(value)
        # JavaScript sends an infinite number as null, which is not this literal.
        if not math.isfinite(number):
            return _NOT_A_LITERAL
        # JSON writes a whole number below 1e21 without a fraction, so the
        # server reads `1.0` as the int 1, as Python's JSON decoder does.
        if number.is_integer() and abs(number) < 1e21:
            return int(number)
        return number
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'", "`"}:
        text = _plain_string_literal_text(value)
        return _NOT_A_LITERAL if text is None else text
    return _NOT_A_LITERAL


__all__ = [
    "RepeatedComponentCall",
    "ServerEventCall",
    "ServerEventPayloadFinding",
    "server_event_calls",
    "server_event_payload_findings",
    "template_has_vue_attributes",
    "unkeyed_repeated_component_calls",
]
