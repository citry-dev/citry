"""
Lint rules that need the loaded application.

``citry check`` runs these only with the component registry, because each one
needs a fact that a template alone does not show: which class a component tag
renders, whether that class uses Vue, or which data class a server event
handler validates its arguments with.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Union
from urllib.parse import unquote

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
    BROWSER_MISSING_FORM_FIELD,
    BROWSER_MISSING_SERVER_EVENT_FIELD,
    BROWSER_UNKNOWN_FORM_FIELD,
    BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
    TEMPLATE_UNKNOWN_INJECT_KEY,
    TEMPLATE_UNKNOWN_URL,
)
from citry._diagnostics import render_diagnostic
from citry._html_attribute_values import HTML_ELEMENTS
from citry._markup_lint import one_slip_from
from citry._provide_keys import method_calls, python_class_node
from citry._source_lines import source_lines
from citry._walk import Call, run
from citry.ext.events.schemas import json_value_error, payload_fields
from citry.util.html import decode_attribute_entities
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

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
    run(_collect_repeated_calls(template, found, parse_nested=parse_nested, base_index=0, in_loop=False))
    return tuple(found)


def _collect_repeated_calls(
    template: Template,
    found: list[RepeatedComponentCall],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    in_loop: bool,
) -> Generator[Call, Any, None]:
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
                    yield Call(
                        _collect_repeated_calls,
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                        in_loop=inner_loop,
                    )
        body = getattr(node, "body", None)
        if body is not None:
            yield Call(
                _collect_repeated_calls,
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
    # `run` steps through the walk in one loop, so Python's call depth stays
    # the same however deeply the template nests.
    return run(_template_has_vue_attributes_walk(template, parse_nested=parse_nested))


def _template_has_vue_attributes_walk(
    template: Template, *, parse_nested: Callable[[str], Template]
) -> Generator[Call, Any, bool]:
    """The walk generator behind ``template_has_vue_attributes``."""
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
                if nested is not None and (
                    yield Call(_template_has_vue_attributes_walk, nested[0], parse_nested=parse_nested)
                ):
                    return True
        body = getattr(node, "body", None)
        if body is not None and (yield Call(_template_has_vue_attributes_walk, body, parse_nested=parse_nested)):
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
    run(_collect_server_event_calls(template, found, handler_names, parse_nested=parse_nested, base_index=0))
    return tuple(found)


def _collect_server_event_calls(
    template: Template,
    found: list[ServerEventCall],
    handler_names: frozenset[str],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> Generator[Call, Any, None]:
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
                    yield Call(
                        _collect_server_event_calls,
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
            yield Call(
                _collect_server_event_calls,
                body,
                found,
                handler_names,
                parse_nested=parse_nested,
                base_index=base_index,
            )


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
class ServerEventField:
    """
    One field a handler's data class takes from the browser.

    Attributes:
        name: The key the browser sends.
        required: Whether the server rejects a call that leaves it out.
        annotation: The field's type, which the server checks each value
            against, or None when it is not known, so its values are not
            checked.

    """

    name: str
    required: bool
    annotation: Any


@dataclass(frozen=True, slots=True)
class ServerEventPayload:
    """
    What the server accepts as one handler's arguments, as far as the template rules can tell.

    ``citry check`` builds it from the handler's data class with
    ``server_event_payload``, and the editor from the handler description
    the app worker sends with ``server_event_payload_from_description``, so
    both run the same rules.

    Attributes:
        takes_data: Whether the handler has a ``data`` parameter. A handler
            without one rejects every key.
        fields: The data class's fields by name, or None when they are not
            known, which turns off the checks that need them.
        rejects_unknown: Whether the server rejects a key the data class
            does not declare.
        query_string: Whether the browser may send the arguments as a GET
            query string, which the server reads as text, so ``'2'`` fits
            an ``int`` field.

    """

    takes_data: bool
    fields: Mapping[str, ServerEventField] | None
    rejects_unknown: bool
    query_string: bool = False


def server_event_payload(data_class: type | None, *, query_string: bool = False) -> ServerEventPayload | None:
    """
    Describe what the server accepts from a handler's data class, or None when the rules must skip it.

    A Pydantic model is skipped: Pydantic converts values by its own rules
    and may read a field under an alias. So is a class whose annotations
    cannot be resolved, which fails when the handler first runs.
    """
    if data_class is None:
        return ServerEventPayload(takes_data=False, fields={}, rejects_unknown=True, query_string=query_string)
    specs = payload_fields(data_class)
    if specs is None:
        return None
    return ServerEventPayload(
        takes_data=True,
        fields={spec.name: ServerEventField(spec.name, spec.required, spec.annotation) for spec in specs},
        rejects_unknown=True,
        query_string=query_string,
    )


def server_event_payload_from_description(handler: Mapping[str, object]) -> ServerEventPayload | None:
    """
    Describe what the server accepts from one handler of the Events introspection entry.

    The editor cannot import the application, so it reads the handler
    description the app worker copies out of it (``docs/design/events.md``
    section 9.1). Returns None, so the rules skip the handler, when the
    description does not prove that Citry's own rules check the arguments:
    a Pydantic model, a description from an older Citry without
    ``extra_fields`` and ``validated_by``, a value this version does not
    know, or a malformed entry. A field whose type text is not one of the
    plain JSON types, a ``Literal``, a union, or a container of those has its
    values left unchecked.
    """
    if handler.get("validated_by") != "citry":
        return None
    extra_fields = handler.get("extra_fields")
    if extra_fields not in {"reject", "ignore"}:
        return None
    methods = handler.get("methods")
    # The editor's copy of the description holds tuples where the JSON had lists.
    query_string = isinstance(methods, (list, tuple)) and "GET" in methods
    schema = handler.get("request_schema")
    if schema is None:
        return ServerEventPayload(takes_data=False, fields={}, rejects_unknown=True, query_string=query_string)
    if not isinstance(schema, Mapping):
        return None
    raw_fields = schema.get("fields")
    # An opaque schema lists no fields, which says nothing about the class.
    if schema.get("kind") != "fields" or not isinstance(raw_fields, (list, tuple)):
        return ServerEventPayload(
            takes_data=True, fields=None, rejects_unknown=extra_fields == "reject", query_string=query_string
        )
    fields: dict[str, ServerEventField] = {}
    for raw in raw_fields:
        if not isinstance(raw, Mapping):
            return None
        name, required, display = raw.get("name"), raw.get("required"), raw.get("type_display")
        if not isinstance(name, str) or not isinstance(required, bool):
            return None
        annotation = annotation_from_type_display(display) if isinstance(display, str) else None
        fields[name] = ServerEventField(name, required, annotation)
    return ServerEventPayload(
        takes_data=True, fields=fields, rejects_unknown=extra_fields == "reject", query_string=query_string
    )


# The names a description's type text may use, with the annotation each
# means. A class name, such as `datetime` or a nested data class, is not
# here, because the text alone does not say which class it is.
_DISPLAY_NAMES: dict[str, Any] = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "None": type(None),
    "NoneType": type(None),
    "Any": Any,
    "object": object,
    "list": list,
    "dict": dict,
}
_DISPLAY_GENERICS: dict[str, Any] = {
    "list": list,
    "List": list,
    "tuple": tuple,
    "Tuple": tuple,
    "set": set,
    "Set": set,
    "frozenset": frozenset,
    "dict": dict,
    "Dict": dict,
}


def annotation_from_type_display(text: str) -> Any:
    """
    Rebuild the annotation that a handler description's ``type_display`` text names, or None.

    Only names whose meaning the text alone proves are read: the plain JSON
    types, ``None``, ``Any``, ``Literal`` with constant values, unions
    written with ``|``, ``Optional``, or ``Union``, and ``list``, ``tuple``,
    ``set``, and ``dict`` of those. Anything else returns None, so the
    caller does not check values of that field.
    """
    try:
        node = ast.parse(text, mode="eval").body
    except (SyntaxError, ValueError):
        return None
    return _display_annotation(node)


def _display_annotation(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant) and node.value is None:
        return type(None)
    if isinstance(node, ast.Name):
        return _DISPLAY_NAMES.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = _display_annotation(node.left), _display_annotation(node.right)
        return None if left is None or right is None else Union[left, right]  # noqa: UP007 - built from parts
    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
        return None
    name = node.value.id
    items = list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]
    if name == "Literal":
        values = [_literal_constant(item) for item in items]
        if any(value is _NOT_A_LITERAL for value in values):
            return None
        return Literal[tuple(values)]
    # `tuple[int, ...]` is the one form whose second item is not a type.
    if (
        name in {"Tuple", "tuple"}
        and len(items) == 2
        and isinstance(items[1], ast.Constant)
        and items[1].value is Ellipsis
    ):
        inner = _display_annotation(items[0])
        return None if inner is None else tuple.__class_getitem__((inner, ...))
    parts = [_display_annotation(item) for item in items]
    if any(part is None for part in parts):
        return None
    if name == "Optional" and len(parts) == 1:
        return Union[parts[0], None]  # noqa: UP007 - built from parts
    if name == "Union":
        return Union[tuple(parts)]  # noqa: UP007 - built from parts
    origin = _DISPLAY_GENERICS.get(name)
    if origin is None:
        return None
    return origin[tuple(parts)] if len(parts) > 1 else origin[parts[0]]


def _literal_constant(node: ast.expr) -> object:
    """Return the value a ``Literal`` item's text spells, or ``_NOT_A_LITERAL``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
        return node.value
    # A negative number is written as a minus sign before the constant.
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, (int, float))
        and not isinstance(node.operand.value, bool)
    ):
        return -node.operand.value
    return _NOT_A_LITERAL


@dataclass(frozen=True, slots=True)
class ServerEventPayloadFinding:
    """One mistake in the arguments an ``@c-*`` binding sends to a server event."""

    code: str
    message: str
    start_index: int
    end_index: int


def server_event_payload_findings(
    call: ServerEventCall,
    payload: ServerEventPayload,
) -> tuple[ServerEventPayloadFinding, ...]:
    """
    Compare the arguments one ``@c-*`` binding writes with what its handler accepts.

    The server checks the arguments against the data class before the
    handler runs and rejects the call on any mistake, so each finding here
    is a call that always fails. Only what the template proves is checked:

    - a key of an object literal that the data class does not declare, or
      any key when the handler takes no ``data``;
    - a required field that an object literal with no ``...`` spread or
      computed key leaves out, or that a call without arguments leaves out,
      unless the browser may send a form's fields instead, which
      ``server_event_form_findings`` checks;
    - a literal value, or a condition whose two results are literals, that
      the server's own check for that field rejects.

    Args:
        call: One binding, from ``server_event_calls``.
        payload: What the handler accepts, from ``server_event_payload`` or
            ``server_event_payload_from_description``.

    Returns:
        Findings in source order.

    """
    accepted = payload.fields
    if call.arguments is None:
        # The browser sends a form's fields when the event comes from a
        # `<form>`, which any other element but these may contain.
        if accepted is None or call.event == "submit" or _ascii_lower(call.element) not in _ELEMENTS_WITHOUT_FORMS:
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
        field = None if accepted is None else accepted.get(item.name)
        if field is None:
            if _rejects_key(payload, item.name):
                findings.append(
                    ServerEventPayloadFinding(
                        BROWSER_UNKNOWN_SERVER_EVENT_FIELD,
                        _unknown_field_message(BROWSER_UNKNOWN_SERVER_EVENT_FIELD, item.name, call.handler, payload),
                        base + item.start_index,
                        base + item.end_index,
                    )
                )
            continue
        if sent[item.name] is not item or field.annotation is None:
            continue
        detail = _rejected_literal(field.annotation, item.value_source, query_string=payload.query_string)
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
    if not dynamic and accepted is not None:
        findings.extend(
            _missing_field(call, name) for name, field in accepted.items() if field.required and name not in written
        )
    return tuple(sorted(findings, key=lambda item: (item.start_index, item.end_index)))


def _rejects_key(payload: ServerEventPayload, name: str) -> bool:
    """Return whether the server rejects a call that sends this key."""
    if not payload.takes_data:
        return True
    return payload.rejects_unknown and payload.fields is not None and name not in payload.fields


def _unknown_field_message(code: str, name: str, event: str, payload: ServerEventPayload) -> str:
    if not payload.takes_data:
        return render_diagnostic(code, variant="no-data", name=name, event=event)
    suggestion = next((field for field in payload.fields or () if one_slip_from(name, field)), None)
    if suggestion is None:
        return render_diagnostic(code, name=name, event=event)
    return render_diagnostic(code, variant="suggestion", name=name, event=event, suggestion=suggestion)


def _missing_field(call: ServerEventCall, name: str) -> ServerEventPayloadFinding:
    return ServerEventPayloadFinding(
        BROWSER_MISSING_SERVER_EVENT_FIELD,
        render_diagnostic(BROWSER_MISSING_SERVER_EVENT_FIELD, name=name, event=call.handler),
        call.start_index,
        call.end_index,
    )


@dataclass(frozen=True, slots=True)
class FormControlName:
    """One control of a form whose static ``name`` the browser sends with the form's fields."""

    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class ServerEventForm:
    """
    One ``<form>`` whose ``@c-submit`` binding sends the form's fields to a server event.

    Attributes:
        call: The ``@c-submit`` binding on the form, which writes no
            arguments, so the browser collects the form's named controls.
        sent: The controls a submit includes under their written name when
            they hold a value: an ``<input>``, ``<select>``, ``<textarea>``,
            or submit ``<button>`` with a static ``name`` that is not
            disabled, does not belong to another form, has no attribute
            spread, and is not a file or image input.
        names: Every static control name in the form, including controls
            that are sent only sometimes, such as a disabled one.
        complete: Whether ``names`` lists every name the form can send:
            the form has no ``id`` that a control outside it could name,
            and it holds no component, custom element, slot, ``<template>``,
            loop, ``v-html``, ``#c-ignore`` content, spread, or name written
            as an expression.

    """

    call: ServerEventCall
    sent: tuple[FormControlName, ...]
    names: frozenset[str]
    complete: bool


def server_event_forms(
    template: Template,
    handler_names: frozenset[str],
    *,
    parse_nested: Callable[[str], Template],
) -> tuple[ServerEventForm, ...]:
    """Return each ``<form>`` whose argument-free ``@c-submit`` binding calls one of ``handler_names``."""
    found: list[ServerEventForm] = []
    run(_collect_server_event_forms(template, found, handler_names, parse_nested=parse_nested, base_index=0))
    return tuple(found)


def _collect_server_event_forms(
    template: Template,
    found: list[ServerEventForm],
    handler_names: frozenset[str],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> Generator[Call, Any, None]:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        attrs = node.start_tag.attrs
        for attr in attrs:
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    yield Call(
                        _collect_server_event_forms,
                        parsed,
                        found,
                        handler_names,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
        body = getattr(node, "body", None)
        call = (
            _form_submit_call(node, handler_names, base_index)
            if _ascii_lower(node.start_tag.name.content) == "form"
            else None
        )
        if call is not None:
            form = _FormControls(complete=not any(_set_attribute(attr) == "id" for attr in attrs))
            if body is not None:
                yield Call(form.walk, body, base_index=base_index, disabled=False)
            found.append(ServerEventForm(call, tuple(form.sent), frozenset(form.names), form.complete))
        # A form inside a form is invalid HTML, which the browser drops, so
        # the walk goes on into any element's content either way.
        if body is not None:
            yield Call(
                _collect_server_event_forms,
                body,
                found,
                handler_names,
                parse_nested=parse_nested,
                base_index=base_index,
            )


def _form_submit_call(node: Any, handler_names: frozenset[str], base_index: int) -> ServerEventCall | None:
    """Return the form's ``@c-submit`` binding when it calls a known handler and writes no arguments."""
    for attr in node.start_tag.attrs:
        key = attr.key.content
        inner = attr.inner_value
        if inner is None or not key.startswith("@c-") or key[len("@c-") :].split(".", 1)[0] != "submit":
            continue
        parsed = _server_event_call(inner.content, handler_names)
        if parsed is None or parsed[2] is not None:
            continue
        handler, handler_start, _arguments, arguments_offset = parsed
        start = base_index + inner.start_index
        return ServerEventCall(
            handler=handler,
            event="submit",
            element=node.start_tag.name.content,
            arguments=None,
            arguments_start=start + len(inner.content[:arguments_offset].encode("utf-8")),
            start_index=start + len(inner.content[:handler_start].encode("utf-8")),
            end_index=start + len(inner.content[: handler_start + len(handler)].encode("utf-8")),
        )
    return None


# The controls a submit sends. A submit button sends its name only when it
# is the one that submitted the form, which both Citry's browser runtime and
# a post without JavaScript include.
_FORM_CONTROLS = frozenset({"input", "select", "textarea", "button"})
# Input types a submit never sends as text: buttons that cannot submit, an
# image button, which sends `name.x` and `name.y` instead, and a file, which
# the browser runtime leaves out.
_UNSENT_INPUT_TYPES = frozenset({"image", "reset", "button", "file"})
# Button types that never submit the form.
_UNSENT_BUTTON_TYPES = frozenset({"reset", "button"})
# Citry tags that render their content in place, at most once.
_IN_PLACE_CONDITIONS = frozenset({"c-if", "c-elif", "c-else"})


def _set_attribute(attr: Any) -> str | None:
    """Return the attribute an attribute key sets, lowercased, whether written plainly or bound."""
    key = _ascii_lower(attr.key.content)
    # `.name` and `^name` are Vue's shorthands for `:name.prop` and
    # `:name.attr`.
    for prefix in (":", "v-bind:", "c-", ".", "^"):
        if key.startswith(prefix):
            # A modifier such as `.prop` still sets the same name.
            return key[len(prefix) :].split(".", 1)[0]
    return key


@dataclass(slots=True)
class _FormControls:
    """Collect the control names inside one form, and whether they are all the form can send."""

    complete: bool
    sent: list[FormControlName] = field(default_factory=list)
    names: set[str] = field(default_factory=set)

    def walk(self, template: Template, *, base_index: int, disabled: bool) -> Generator[Call, Any, None]:
        for element in template.elements:
            if not isinstance(element, TemplateElement.Node):
                continue
            node = element._0
            tag = node.start_tag.name.content
            lower = _ascii_lower(tag)
            attrs = node.start_tag.attrs
            keys = {_ascii_lower(attr.key.content) for attr in attrs}
            # A component, custom element, slot, or `<template>` can render
            # controls the template does not show, and a loop or spread can
            # repeat a control or give it another name.
            if (
                (lower.startswith("c-") and lower not in _IN_PLACE_CONDITIONS)
                or tag != lower
                or "-" in lower
                or lower in {"slot", "template", "component"}
                # A library may add controls inside `#c-ignore` content.
                or keys & {"v-for", "c-for", "v-bind", "c-bind", "v-html", "v-slot", "#c-ignore"}
                or any(key.startswith("v-slot:") for key in keys)
                # Markup written inside an attribute renders elsewhere.
                or any(attr.kind == HtmlAttrKind.Template for attr in attrs)
            ):
                self.complete = False
            # A disabled fieldset disables every control inside it.
            inside_disabled = disabled or (
                lower == "fieldset" and any(_set_attribute(attr) == "disabled" for attr in attrs)
            )
            if lower in _FORM_CONTROLS:
                self._control(lower, attrs, base_index, disabled=inside_disabled)
            body = getattr(node, "body", None)
            if body is not None:
                yield Call(self.walk, body, base_index=base_index, disabled=inside_disabled)

    def _control(self, lower: str, attrs: Any, base_index: int, *, disabled: bool) -> None:
        name_attr = None
        image_type = None
        # Whether the browser may leave the control out of this form's submit.
        sometimes = disabled
        # Whether its type means it never sends its name as text.
        unsent_type = False
        for attr in attrs:
            key = _ascii_lower(attr.key.content)
            sets = _set_attribute(attr)
            if key == "name":
                name_attr = attr
            elif lower == "button" and _prevents_click(key):
                # A button whose click is prevented never submits the form.
                sometimes = True
            elif sets == "name":
                # A name written as an expression may be anything.
                self.complete = False
                return
            elif sets in {"disabled", "form"} or key in {"v-bind", "c-bind"}:
                # A disabled control is not sent, one tied to another form by
                # `form` is sent with that form, and a spread may set
                # another name.
                sometimes = True
            elif sets == "type" and lower in {"input", "button"}:
                inner = attr.inner_value
                written_type = None if key != "type" or inner is None else _ascii_lower(inner.content.strip())
                if written_type is None:
                    # A type written as an expression may be any of them.
                    sometimes = True
                elif written_type in (_UNSENT_INPUT_TYPES if lower == "input" else _UNSENT_BUTTON_TYPES):
                    unsent_type = True
                    if written_type == "image" and lower == "input":
                        image_type = inner
        inner = None if name_attr is None else name_attr.inner_value
        if image_type is not None:
            # An image button that submits the form sends where it was
            # clicked, as `x` and `y`, or `name.x` and `name.y`, and never
            # its bare name, so the bare name is not one the form sends.
            if not sometimes:
                prefix = f"{inner.content}." if inner is not None and inner.content else ""
                for axis in ("x", "y"):
                    self.sent.append(
                        FormControlName(
                            prefix + axis,
                            base_index + image_type.start_index,
                            base_index + image_type.end_index,
                        )
                    )
            return
        if inner is None or not inner.content:
            return
        self.names.add(inner.content)
        if not sometimes and not unsent_type:
            self.sent.append(
                FormControlName(inner.content, base_index + inner.start_index, base_index + inner.end_index)
            )


def _prevents_click(key: str) -> bool:
    """Return whether an attribute is a click listener with the ``.prevent`` modifier."""
    for prefix in ("@click", "v-on:click", "@c-click"):
        if key.startswith(prefix) and ".prevent" in key[len(prefix) :]:
            return True
    return False


def server_event_form_findings(
    form: ServerEventForm,
    payload: ServerEventPayload,
    *,
    dropped_names: frozenset[str] = frozenset(),
) -> tuple[ServerEventPayloadFinding, ...]:
    """
    Compare the control names a form sends with what its ``@c-submit`` handler accepts.

    The browser sends the form's named controls, and so does a post without
    JavaScript, so a name the data class does not declare fails each submit
    that sends that control. A required field is reported missing only when
    the form proves it lists every name it can send.

    Args:
        form: One form, from ``server_event_forms``.
        payload: What the handler accepts.
        dropped_names: The host CSRF field names the server removes before
            it checks the data class, such as ``csrfmiddlewaretoken``.

    Returns:
        Findings in source order.

    """
    findings: list[ServerEventPayloadFinding] = []
    accepted = payload.fields
    for control in form.sent:
        declared = accepted is not None and control.name in accepted
        if declared or (control.name in dropped_names) or not _rejects_key(payload, control.name):
            continue
        findings.append(
            ServerEventPayloadFinding(
                BROWSER_UNKNOWN_FORM_FIELD,
                _unknown_field_message(BROWSER_UNKNOWN_FORM_FIELD, control.name, form.call.handler, payload),
                control.start_index,
                control.end_index,
            )
        )
    if form.complete and payload.takes_data and accepted is not None:
        findings.extend(
            ServerEventPayloadFinding(
                BROWSER_MISSING_FORM_FIELD,
                render_diagnostic(BROWSER_MISSING_FORM_FIELD, name=name, event=form.call.handler),
                form.call.start_index,
                form.call.end_index,
            )
            for name, item in accepted.items()
            if item.required and name not in form.names
        )
    return tuple(sorted(findings, key=lambda item: (item.start_index, item.end_index)))


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


@dataclass(frozen=True, slots=True)
class TemplateUrl:
    """
    One literal root-relative link path in a template.

    Attributes:
        path: The path the browser requests, with character references and
            percent escapes decoded and the query string and fragment removed,
            such as ``/static/avatar.svg``.
        start_index: Inclusive UTF-8 byte offset of the attribute value.
        end_index: Exclusive UTF-8 byte offset of the attribute value.

    """

    path: str
    start_index: int
    end_index: int


# The attributes whose value the browser requests or navigates to. Others,
# such as `srcset`, hold several URLs and are not read here.
_URL_ATTRIBUTES = frozenset({"href", "src", "action"})


def template_urls(template: Template, *, parse_nested: Callable[[str], Template]) -> tuple[TemplateUrl, ...]:
    """
    Return each literal ``href``, ``src`` and ``action`` path on an HTML element that starts at the site root.

    Only a plain attribute written without an expression counts, on an HTML
    element: a component or custom element may treat the value as anything.
    A value with a scheme (``https:``, ``mailto:``), a protocol-relative
    ``//host/...`` value, and a relative path such as ``page.html`` are left
    out: a scheme or a ``//host`` names another site, and a relative path
    depends on the page's own URL.
    """
    found: list[TemplateUrl] = []
    run(_collect_template_urls(template, found, parse_nested=parse_nested, base_index=0))
    return tuple(found)


def _collect_template_urls(
    template: Template,
    found: list[TemplateUrl],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> Generator[Call, Any, None]:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        # Tag names are case-sensitive in the parser, so `<A>` is a component
        # call and only a lowercase name is an HTML element.
        html = node.start_tag.name.content in HTML_ELEMENTS
        attrs = node.start_tag.attrs
        for attr in attrs:
            inner = attr.inner_value
            if attr.kind == HtmlAttrKind.Template and inner is not None:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    yield Call(
                        _collect_template_urls,
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
                continue
            if (
                not html
                or not _requests_a_page(node.start_tag.name.content, attrs)
                or attr.kind != HtmlAttrKind.Static
                or attr.foreign_parts
                or inner is None
                or _ascii_lower(attr.key.content) not in _URL_ATTRIBUTES
            ):
                continue
            path = root_relative_path(decode_attribute_entities(inner.content))
            if path is not None:
                found.append(TemplateUrl(path, base_index + inner.start_index, base_index + inner.end_index))
        body = getattr(node, "body", None)
        if body is not None:
            yield Call(_collect_template_urls, body, found, parse_nested=parse_nested, base_index=base_index)


# `<link>` types whose `href` names a server to connect to early, not a
# page or file the browser requests.
_CONNECTION_LINK_TYPES = frozenset({"preconnect", "dns-prefetch"})


def _requests_a_page(tag: str, attrs: Any) -> bool:
    """Return whether an element's link attribute names something the browser requests from that path."""
    # `<base href>` sets the folder relative links start from; it need not be
    # a page itself.
    if tag == "base":
        return False
    if tag != "link":
        return True
    for attr in attrs:
        inner = attr.inner_value
        if _ascii_lower(attr.key.content) == "rel" and attr.kind == HtmlAttrKind.Static and inner is not None:
            return not (set(_ascii_lower(inner.content).split()) & _CONNECTION_LINK_TYPES)
    return True


def root_relative_path(value: str) -> str | None:
    """
    Return the path a link value requests from the site root, or ``None`` when it is not root-relative.

    The browser removes leading and trailing whitespace from a URL, reads a
    backslash as a slash, and does not send the fragment. The query string
    is sent, but routes and static files match on the path alone.
    """
    # The browser also drops every tab and line break inside a URL.
    url = value.strip(" \t\n\f\r").translate(_URL_DROPPED_CHARACTERS).replace("\\", "/")
    # `//host/path` names another host, and an empty or relative value
    # depends on the page's own URL.
    if not url.startswith("/") or url.startswith("//"):
        return None
    for separator in ("#", "?"):
        url = url.split(separator, 1)[0]
    # The browser resolves `.` and `..` before it decodes the path, so an
    # escaped slash stays inside its segment. The server then matches on the
    # decoded characters.
    resolved = _without_dot_segments(url)
    return unquote(resolved) if "%" in resolved else resolved


# Characters the browser removes from anywhere in a URL before reading it.
_URL_DROPPED_CHARACTERS = str.maketrans("", "", "\t\n\r")


def _without_dot_segments(path: str) -> str:
    """Resolve ``.`` and ``..`` segments the way the browser does before it requests a path."""
    segments = path.split("/")[1:]
    resolved: list[str] = []
    for segment in segments:
        # The browser reads an escaped dot, `%2e`, as a dot here too.
        dots = segment.lower().replace("%2e", ".")
        if dots == "..":
            # `..` at the root stays at the root, as in the browser.
            if resolved:
                resolved.pop()
        elif dots != ".":
            resolved.append(segment)
    # A last `.` or `..` segment leaves the path ending in a folder.
    if segments and segments[-1].lower().replace("%2e", ".") in {".", ".."}:
        resolved.append("")
    return "/" + "/".join(resolved)


@dataclass(frozen=True, slots=True)
class UnknownUrlFinding:
    """One link path the host app does not serve, at template byte offsets."""

    code: str
    message: str
    start_index: int
    end_index: int


def unknown_url_findings(
    urls: tuple[TemplateUrl, ...],
    verdicts: Mapping[str, tuple[bool, str | None]],
) -> list[UnknownUrlFinding]:
    """
    Report each path the host app answered it does not serve.

    ``verdicts`` maps a path to whether it is served and, for a missing one,
    a served path one typing slip away. A path without a verdict, because no
    checker could answer for it, is not reported.
    """
    findings: list[UnknownUrlFinding] = []
    for url in urls:
        verdict = verdicts.get(url.path)
        if verdict is None or verdict[0]:
            continue
        suggestion = verdict[1]
        message = (
            render_diagnostic(TEMPLATE_UNKNOWN_URL, path=url.path)
            if suggestion is None
            else render_diagnostic(TEMPLATE_UNKNOWN_URL, variant="suggestion", path=url.path, suggestion=suggestion)
        )
        findings.append(UnknownUrlFinding(TEMPLATE_UNKNOWN_URL, message, url.start_index, url.end_index))
    return findings


@dataclass(frozen=True, slots=True)
class UnknownInjectKeyFinding:
    """One ``self.inject("key")`` call whose key reaches the component from no provider, at UTF-8 byte offsets."""

    code: str
    message: str
    start_index: int
    end_index: int


def unknown_inject_key_findings(
    source: str,
    tree: ast.Module,
    qualname: str,
    *,
    component: str,
    provided: frozenset[str],
    everywhere: bool,
) -> list[UnknownInjectKeyFinding]:
    """
    Report each ``self.inject("key")`` in one class whose key is not in ``provided``.

    Only a call with one string literal and no default counts: a default
    says the key may be missing on purpose, and a key written as an
    expression cannot be compared. ``everywhere`` says ``provided`` is every
    key the app provides, because no template renders the component, which
    changes the message. Offsets point at the key's string literal in
    ``source``.
    """
    scope = python_class_node(tree, qualname)
    if scope is None:
        return []
    lines = source_lines(source)
    # Byte offset where each line starts, since `ast` gives byte columns.
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))
    findings: list[UnknownInjectKeyFinding] = []
    for call in method_calls(scope, "inject"):
        receiver = call.func.value if isinstance(call.func, ast.Attribute) else None
        argument = call.args[0] if len(call.args) == 1 else None
        if (
            not isinstance(receiver, ast.Name)
            or receiver.id != "self"
            or call.keywords
            or not isinstance(argument, ast.Constant)
            or not isinstance(argument.value, str)
            or argument.value in provided
        ):
            continue
        key = argument.value
        suggestion = next((candidate for candidate in sorted(provided) if one_slip_from(key, candidate)), None)
        variant = "nowhere" if everywhere else "default"
        if suggestion is None:
            message = render_diagnostic(TEMPLATE_UNKNOWN_INJECT_KEY, variant=variant, component=component, key=key)
        else:
            message = render_diagnostic(
                TEMPLATE_UNKNOWN_INJECT_KEY,
                variant="nowhereSuggestion" if everywhere else "suggestion",
                component=component,
                key=key,
                suggestion=suggestion,
            )
        end_lineno = argument.end_lineno if argument.end_lineno is not None else argument.lineno
        end_col = argument.end_col_offset if argument.end_col_offset is not None else argument.col_offset
        findings.append(
            UnknownInjectKeyFinding(
                TEMPLATE_UNKNOWN_INJECT_KEY,
                message,
                starts[argument.lineno - 1] + argument.col_offset,
                starts[end_lineno - 1] + end_col,
            )
        )
    findings.sort(key=lambda finding: finding.start_index)
    return findings


__all__ = [
    "FormControlName",
    "RepeatedComponentCall",
    "ServerEventCall",
    "ServerEventField",
    "ServerEventForm",
    "ServerEventPayload",
    "ServerEventPayloadFinding",
    "TemplateUrl",
    "UnknownInjectKeyFinding",
    "UnknownUrlFinding",
    "annotation_from_type_display",
    "root_relative_path",
    "server_event_calls",
    "server_event_form_findings",
    "server_event_forms",
    "server_event_payload",
    "server_event_payload_findings",
    "server_event_payload_from_description",
    "template_has_vue_attributes",
    "template_urls",
    "unkeyed_repeated_component_calls",
    "unknown_inject_key_findings",
    "unknown_url_findings",
]
