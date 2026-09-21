"""Reusable browser programs without statically compiled component or slot nodes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, cast

from citry.attrs import _html_attr_identity, format_attrs
from citry.citry_render import _VALUE_CONTEXT, CitryRender, RenderPart
from citry.constness import const_value
from citry.ext.i18n.bindings import I18nBindingElementAttrsNode
from citry.nodes import ExprHtmlAttr, ForNode, IfNode, Node, StaticHtmlAttr
from citry.util.html import escape_to_str

from .capture import (
    PreparedAttribute,
    PreparedElementClose,
    PreparedElementCloseNode,
    PreparedElementOpen,
    PreparedElementOpenNode,
    PreparedExprNode,
    PreparedSourceText,
    PreparedSourceTextNode,
    PreparedStaticRun,
    PreparedStaticRunNode,
    PreparedTextValue,
    PreparedVerbatimHtmlNode,
    _reject_executable_dynamic_attrs,
    include_prepared_attribute,
    vue_render_active,
)
from .compiler import _ElementBindingDeclaration, _generated_vue_attr, _RuntimeEventDeclaration

if TYPE_CHECKING:
    from collections.abc import Sequence

    from citry.citry_context import CitryContext


@dataclass(frozen=True, slots=True)
class LeafProgramFragment:
    template: str
    element_bindings: tuple[dict[str, object], ...]
    browser_requirements: frozenset[str]
    safe_body: bool
    runtime_event_sites: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class PreparedLeafProgram:
    """One evaluated occurrence of an immutable leaf program."""

    fragment: LeafProgramFragment
    prepared_data: dict[str, object]
    operations: tuple[object, ...]
    vue_errors: tuple[str, ...]
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]]
    cached_typed_parts: tuple[RenderPart, ...] | None = None
    cached_static_parts: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class _Static:
    html: str
    typed: PreparedStaticRun | PreparedSourceText


@dataclass(frozen=True, slots=True)
class _Text:
    node: PreparedExprNode
    key: str


@dataclass(frozen=True, slots=True)
class _Open:
    node: PreparedElementOpenNode
    renderer: Node | None
    attrs_key: str | None
    key_key: str | None
    control_key: str | None
    runtime_events_key: str | None
    fixed_attrs: tuple[tuple[str, ExprHtmlAttr], ...] | None
    spread_renderer: Node | None
    authored_attrs: tuple[str, ...]
    authored_attributes: tuple[PreparedAttribute, ...]
    static: PreparedElementOpen | None


@dataclass(frozen=True, slots=True)
class _Close:
    value: PreparedElementClose


@dataclass(frozen=True, slots=True)
class _If:
    node: IfNode
    key: str
    branches: tuple[tuple[object, ...], ...]


@dataclass(frozen=True, slots=True)
class _For:
    node: ForNode
    key: str
    body: tuple[object, ...]
    empty: tuple[object, ...]


class LeafProgramNode(Node):
    """Evaluate a cached leaf program once into occurrence data or typed fallback output."""

    def __init__(self, fragment: LeafProgramFragment, operations: tuple[object, ...]) -> None:
        self.fragment = fragment
        self.operations = operations

    def render(self, context: CitryContext) -> RenderPart:
        data: dict[str, object] = {}
        vue_errors: list[str] = []
        special: dict[tuple[int, str], RenderPart] = {}
        resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]] = {}
        _evaluate(self.operations, context, data, data, vue_errors, special, resolved_opens)
        if special:
            parts: list[RenderPart] = []
            _materialize_typed(self.operations, data, data, special, resolved_opens, parts)
            return CitryRender(parts=parts, context=context)
        return PreparedLeafProgram(self.fragment, data, self.operations, tuple(vue_errors), resolved_opens)


def compile_leaf_program(body: Sequence[object], *, allow_i18n_passthrough: bool = False) -> LeafProgramNode | None:
    """Compile a final transformed leaf body, or return None for the general renderer."""
    compiler = _Compiler(allow_i18n_passthrough=allow_i18n_passthrough)
    operations = compiler.compile_body(body)
    if operations is None or not compiler.has_data_ops or not compiler.safe_body:
        return None
    return LeafProgramNode(
        LeafProgramFragment(
            "".join(compiler.output),
            cast("tuple[dict[str, object], ...]", tuple(compiler.element_bindings)),
            frozenset(compiler.browser_requirements),
            safe_body=True,
            runtime_event_sites=cast("tuple[dict[str, object], ...]", tuple(compiler.runtime_event_sites)),
        ),
        operations,
    )


class _Compiler:
    def __init__(self, *, allow_i18n_passthrough: bool = False, in_loop: bool = False) -> None:
        self.output: list[str] = []
        self.byte_position = 0
        self.element_bindings: list[_ElementBindingDeclaration] = []
        self.text_index = 0
        self.attrs_index = 0
        self.key_index = 0
        self.control_index = 0
        self.runtime_events_index = 0
        self.if_index = 0
        self.loop_index = 0
        self.has_data_ops = False
        self.browser_requirements: set[str] = set()
        self.safe_body = True
        self.runtime_event_sites: list[_RuntimeEventDeclaration] = []
        self.scope_steps: list[dict[str, object]] = []
        self.allow_i18n_passthrough = allow_i18n_passthrough
        self.in_loop = in_loop

    def append(self, value: str) -> None:
        self.output.append(value)
        self.byte_position += len(value.encode())

    def compile_body(self, body: Sequence[object]) -> tuple[object, ...] | None:
        operations: list[object] = []
        skip_close_tag: str | None = None
        for item in body:
            if (
                skip_close_tag is not None
                and isinstance(item, PreparedElementCloseNode)
                and item.tag == skip_close_tag
            ):
                skip_close_tag = None
                continue
            skip_close_tag = None
            operation = self.compile_item(item)
            if operation is None:
                return None
            operations.append(operation)
            if isinstance(operation, _Open) and operation.node.is_self_closing:
                skip_close_tag = operation.node.tag
        return tuple(operations)

    def compile_item(self, item: object) -> object | None:
        if type(item) is PreparedStaticRunNode:
            if _unsafe_body_text(item._prepared.html):
                self.safe_body = False
            self.append(item._prepared.html)
            return _Static(item._prepared.html, item._prepared)
        if type(item) is PreparedSourceTextNode:
            if _unsafe_body_text(item.text):
                self.safe_body = False
            self.append(item.text)
            return _Static(item.text, item._prepared)
        if type(item) is PreparedVerbatimHtmlNode:
            # Raw HTML is data, never Vue template source. Keep this component
            # on the general typed path until native opaque-HTML VNodes exist.
            return None
        if type(item) is PreparedExprNode:
            self.has_data_ops = True
            key = f"citryText{self.text_index}"
            self.text_index += 1
            self.append(f"{{{{ preparedData.{key} }}}}")
            return _Text(item, key)
        if type(item) is PreparedElementOpenNode:
            return self._compile_open(item, item)
        if (
            type(item) is I18nBindingElementAttrsNode
            and type(getattr(item, "original", None)) is PreparedElementOpenNode
            and (self.allow_i18n_passthrough or item.original._has_spread)
        ):
            original = item.original
            if not isinstance(original, PreparedElementOpenNode):
                raise AssertionError("validated i18n attribute wrapper lost its prepared opening")
            return self._compile_open(original, item)
        if type(item) is PreparedElementCloseNode:
            value = item._prepared
            self.append(f"</{value.tag}>")
            return _Close(value)
        if type(item) is IfNode:
            return self._compile_if(item)
        if type(item) is ForNode:
            if item._precomputed_parts is not None:
                return None
            return self._compile_for(item)
        return None

    def _compile_open(self, node: PreparedElementOpenNode, renderer: Node) -> _Open:
        # A spread or runtime hook may remove or replace an authored Vue
        # attribute. Its authenticated source bytes can only be selected after
        # resolution, so this opening must use the general typed assembler.
        if node._authored_vue_attrs and node._has_spread:
            self.safe_body = False
        if node._has_spread and not _source_attrs_are_projectable(node):
            # A spread can remove or replace these authored values, so the
            # leaf template would have to carry the selected value through
            # v-bind. Keep executable attributes and DOM properties on the
            # general typed assembler instead.
            self.safe_body = False
        if node.tag.casefold() in {"html", "head", "body", "script", "style", "iframe", "object"}:
            self.safe_body = False
        if self.in_loop and any(
            attr.key == "key" or attr.key.startswith((":key", "v-bind:key")) for attr in node.attrs
        ):
            self.safe_body = False
        start = self.byte_position
        attrs_key = None
        key_key = None
        control_key = None
        runtime_events_key = None
        dynamic_keys = {attr.key.removeprefix("c-") for attr in node.attrs if not isinstance(attr, StaticHtmlAttr)}
        attrs = (
            []
            if node._has_spread
            else [source for attr, source in node._static_source_attrs if attr.key not in dynamic_keys]
        )
        authored_attributes = tuple(
            PreparedAttribute(attr.key, "source", attr.position, source)
            for attr, source in node._static_source_attrs
            if attr.key not in dynamic_keys
        )
        authored_attrs = tuple(attrs)
        if node._authored_vue_attrs:
            self.browser_requirements.add("vue_binding")
        if node._event_bindings:
            self.browser_requirements.add("events")
        if node._poll_bindings:
            self.browser_requirements.add("events")
        if node._control_bindings:
            self.browser_requirements.add("events")
        if node._runtime_events_candidate:
            self.browser_requirements.add("events")
            self.has_data_ops = True
            runtime_events_key = f"citryRuntimeEvents{self.runtime_events_index}"
            self.runtime_events_index += 1
            attrs.append(f'v-citry-runtime-events="$citryEvents.runtimeEvents(preparedData.{runtime_events_key})"')
        event_names = [str(binding["event"]) for binding in node._event_bindings]
        if len(event_names) != len(set(event_names)):
            self.safe_body = False
        for binding in node._event_bindings:
            modifiers = [name for name in ("prevent", "stop", "self", "once") if binding[name] is True]
            if binding["key"] is not None:
                modifiers.append(str(binding["key"]))
            suffix = "" if not modifiers else "." + ".".join(modifiers)
            args = binding["args"]
            authored_args = "" if args is None else f", ({args})"
            attrs.append(
                _generated_vue_attr(
                    f"v-on:{binding['event']}{suffix}",
                    f"$citryEvents.dispatch('{binding['id']}', $event{authored_args})",
                )
            )
        timed_ids = ",".join(
            str(binding["id"])
            for binding in node._event_bindings
            if binding["debounce"] is not None or binding["throttle"] is not None
        )
        poll_entries = ",".join(
            "{id:'"
            + str(binding["id"])
            + "',args:"
            + ("undefined" if binding["args"] is None else f"()=>({binding['args']})")
            + "}"
            for binding in node._poll_bindings
        )
        if timed_ids or poll_entries:
            timing_expression = (
                f"$citryEvents.timings('{timed_ids}',[{poll_entries}])"
                if poll_entries
                else f"$citryEvents.timings('{timed_ids}')"
            )
            attrs.append(
                _generated_vue_attr(
                    "v-citry-event-timing",
                    timing_expression,
                )
            )
        if node._runtime_control_candidate:
            self.has_data_ops = True
            control_key = f"citryControls{self.control_index}"
            self.control_index += 1
            attrs.append(f'v-citry-control="$citryEvents.controls(preparedData.{control_key})"')
        elif node._control_bindings:
            ids = ",".join(str(binding["id"]) for binding in node._control_bindings)
            attrs.append(f"v-citry-control=\"$citryEvents.controls('{ids}')\"")
        fixed_attrs = _fixed_attrs_plan(node, renderer)
        spread_renderer = _spread_attrs_renderer(node, renderer)
        if fixed_attrs and any(attr.key.startswith((":[", "v-bind:[")) for attr, _source in node._static_source_attrs):
            # The dynamic argument may resolve to any of the fixed Python
            # attribute names. Let the general assembler inspect the actual
            # resolved dictionary instead of compiling an unchecked merge.
            self.safe_body = False
        if node._static_prepared is None:
            self.has_data_ops = True
            attrs_key = f"citryAttrs{self.attrs_index}"
            self.attrs_index += 1
            attrs.append(f'v-bind="preparedData.{attrs_key}"')
        if node.element_metadata and any(item and item[0] == "key" for item in node.element_metadata):
            if self.in_loop:
                self.safe_body = False
            self.has_data_ops = True
            key_key = f"citryKey{self.key_index}"
            self.key_index += 1
            attrs.append(f':key="preparedData.{key_key}"')
        rendered_attrs = "" if not attrs else " " + " ".join(attrs)
        ending = "/>" if node.is_self_closing else ">"
        self.append(f"<{node.tag}{rendered_attrs}{ending}")
        if attrs_key is not None or key_key is not None or runtime_events_key is not None:
            self.element_bindings.append(
                {
                    "sourceStart": start,
                    "sourceEnd": self.byte_position,
                    "attrsBindingKey": attrs_key,
                    "keyBindingKey": key_key,
                    "runtimeEventsBindingKey": runtime_events_key,
                }
            )
        if runtime_events_key is not None:
            self.runtime_event_sites.append(
                {
                    "sourceStart": start,
                    "sourceEnd": self.byte_position,
                    "bindingKey": runtime_events_key,
                    "steps": [dict(step) for step in self.scope_steps],
                }
            )
        return _Open(
            node,
            None if node._static_prepared is not None or fixed_attrs is not None else renderer,
            attrs_key,
            key_key,
            control_key,
            runtime_events_key,
            fixed_attrs,
            spread_renderer,
            authored_attrs,
            authored_attributes,
            node._static_prepared,
        )

    def _compile_if(self, node: IfNode) -> _If | None:
        self.has_data_ops = True
        key = f"citryIf{self.if_index}"
        self.if_index += 1
        branches: list[tuple[object, ...]] = []
        for index, branch in enumerate(node.branches):
            directive = "v-if" if index == 0 else "v-else-if"
            self.append(f'<template {directive}="preparedData.{key} === {index}">')
            self.scope_steps.append({"kind": "branch", "key": key, "index": index})
            compiled = self.compile_body(branch[2])
            self.scope_steps.pop()
            if compiled is None:
                return None
            branches.append(compiled)
            self.append("</template>")
        return _If(node, key, tuple(branches))

    def _compile_for(self, node: ForNode) -> _For | None:
        self.has_data_ops = True
        key = f"citryLoop{self.loop_index}"
        self.loop_index += 1
        self.append(f'<template v-for="preparedData in preparedData.{key}">')
        child = _Compiler(allow_i18n_passthrough=self.allow_i18n_passthrough, in_loop=True)
        child.scope_steps = [*self.scope_steps, {"kind": "each", "key": key}]
        compiled_body = child.compile_body(node.branches[0][2])
        if compiled_body is None:
            return None
        offset = self.byte_position
        self.append("".join(child.output))
        self.element_bindings.extend(_rebase(child.element_bindings, offset))
        self.runtime_event_sites.extend(_rebase(child.runtime_event_sites, offset))
        self.has_data_ops = self.has_data_ops or child.has_data_ops
        self.browser_requirements.update(child.browser_requirements)
        self.safe_body = self.safe_body and child.safe_body
        self.append("</template>")
        empty: tuple[object, ...] = ()
        if len(node.branches) > 1:
            self.append(f'<template v-if="preparedData.{key}.length === 0">')
            self.scope_steps.append({"kind": "empty", "key": key})
            compiled_empty = self.compile_body(node.branches[1][2])
            self.scope_steps.pop()
            if compiled_empty is None:
                return None
            empty = compiled_empty
            self.append("</template>")
        return _For(node, key, compiled_body, empty)


# citry supports Python 3.10, so the generic is spelled with an explicit TypeVar
# rather than the 3.12 type-parameter syntax, which is a syntax error on 3.10/3.11.
_RebasableT = TypeVar("_RebasableT", bound=_ElementBindingDeclaration | _RuntimeEventDeclaration)


def _rebase(values: list[_RebasableT], offset: int) -> list[_RebasableT]:
    return cast(
        "list[_RebasableT]",
        [
            {
                **value,
                "sourceStart": value["sourceStart"] + offset,
                "sourceEnd": value["sourceEnd"] + offset,
            }
            for value in values
        ],
    )


def _unsafe_body_text(value: str) -> bool:
    return (
        re.search(
            r"<(?:!doctype\b|/?(?:html|head|body|script|style|iframe|object)(?:\s|/?>))",
            value,
            re.IGNORECASE,
        )
        is not None
    )


def _fixed_attrs_plan(node: PreparedElementOpenNode, renderer: Node) -> tuple[tuple[str, ExprHtmlAttr], ...] | None:
    """Return a direct evaluator for unique, fixed-name ordinary attributes."""
    if (
        renderer is not node
        or node._static_prepared is not None
        or node._has_spread
        or node._event_bindings
        or node._poll_bindings
        or node._control_bindings
        or node._runtime_events_candidate
        or node.element_metadata
    ):
        return None
    identities: set[str] = set()
    source_targets = {
        _html_attr_identity(target)
        for attr, _source in node._static_source_attrs
        if (target := _source_target(attr.key)) is not None
    }
    dynamic: list[tuple[str, ExprHtmlAttr]] = []
    for attr in node.attrs:
        if type(attr) not in {StaticHtmlAttr, ExprHtmlAttr}:
            return None
        output_name = attr.key.removeprefix("c-")
        identity = _html_attr_identity(output_name)
        if identity in identities or identity in {"class", "style"}:
            return None
        identities.add(identity)
        if type(attr) is ExprHtmlAttr:
            if (
                identity in source_targets
                or identity in {"innerhtml", "outerhtml", "textcontent", "innertext"}
                or identity.startswith(("data-cev-", "on", "v-", "@", ":", "#", "$"))
            ):
                return None
            dynamic.append((output_name, attr))
    return tuple(dynamic)


def _spread_attrs_renderer(node: PreparedElementOpenNode, renderer: Node) -> Node | None:
    """Select the leaf-only resolved-dictionary path for one spread opening."""
    if (
        type(node) is not PreparedElementOpenNode
        or not node._has_spread
        or node._authored_vue_attrs
        or node._event_bindings
        or node._poll_bindings
        or node._control_bindings
        or node._runtime_events_candidate
        or node.element_metadata
    ):
        return None
    if renderer is node:
        return renderer
    if type(renderer) is I18nBindingElementAttrsNode and renderer.original is node and not renderer.has_static_binding:
        return renderer
    return None


def _spread_passthrough_is_live(renderer: Node, context: CitryContext) -> bool:
    if type(renderer) is PreparedElementOpenNode:
        return True
    if type(renderer) is not I18nBindingElementAttrsNode or context.component is None:
        return False
    component_i18n = getattr(context.component, "i18n", None)
    return component_i18n is not None and component_i18n._extension._compiled_catalog is None


def _evaluate(
    operations: tuple[object, ...],
    context: CitryContext,
    data: dict[str, object],
    root_data: dict[str, object],
    vue_errors: list[str],
    special: dict[tuple[int, str], RenderPart],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]],
) -> None:
    value_token = _VALUE_CONTEXT.set(context)
    try:
        _evaluate_inner(operations, context, data, root_data, vue_errors, special, resolved_opens)
    finally:
        _VALUE_CONTEXT.reset(value_token)


def _evaluate_inner(
    operations: tuple[object, ...],
    context: CitryContext,
    data: dict[str, object],
    root_data: dict[str, object],
    vue_errors: list[str],
    special: dict[tuple[int, str], RenderPart],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]],
) -> None:
    for operation in operations:
        if isinstance(operation, _Static):
            continue
        if isinstance(operation, _Text):
            try:
                text_value = operation.node.resolve_value(context)
            except Exception as error:
                _attach_error(error, operation.node, context)
                raise
            if not isinstance(text_value, str):
                special[(id(data), operation.key)] = text_value
                if isinstance(text_value, CitryRender) and text_value.context is not context:
                    from citry.component_render import _contains_deferred, _merge_dependencies  # noqa: PLC0415

                    if not _contains_deferred(text_value):
                        _merge_dependencies(context, text_value.context)
            else:
                data[operation.key] = text_value
        elif isinstance(operation, _Open):
            if operation.static is not None:
                continue
            if operation.fixed_attrs is not None:
                try:
                    open_value: PreparedElementOpen | dict[str, object] = {
                        name: resolved
                        for name, attr in operation.fixed_attrs
                        if (resolved := const_value(attr.resolve(context))) is not None and resolved is not False
                    }
                except Exception as error:
                    _attach_error(error, operation.node, context)
                    raise
            elif (
                operation.control_key is None
                and operation.spread_renderer is not None
                and _spread_passthrough_is_live(operation.spread_renderer, context)
            ):
                try:
                    resolved, extension_validated = operation.node._resolve_for_output(context)
                    fallback_value = operation.node._prepared_from_resolved(
                        resolved,
                        context=context,
                        extension_validated=extension_validated,
                    )
                    open_value = _spread_data_attrs(operation.node, fallback_value)
                    if vue_render_active():
                        _reject_executable_dynamic_attrs(open_value, tag=operation.node.tag)
                    validation_error = _validate_data_attrs(open_value, tag=operation.node.tag)
                    if validation_error is not None:
                        vue_errors.append(validation_error)
                    resolved_opens[(id(data), id(operation))] = fallback_value
                except Exception as error:
                    _attach_error(error, operation.node, context)
                    raise
            else:
                if operation.renderer is None:
                    raise AssertionError("general leaf attribute plan lost its renderer")
                try:
                    rendered_open = operation.renderer.render(context)
                except Exception as error:
                    _attach_error(error, operation.node, context)
                    raise
                if not isinstance(rendered_open, PreparedElementOpen):
                    raise TypeError("leaf browser program attribute produced structured output")
                validation_error = _validate_open(rendered_open)
                if validation_error is not None:
                    vue_errors.append(validation_error)
                open_value = rendered_open
            resolved_opens.setdefault((id(data), id(operation)), open_value)
            if operation.attrs_key is not None:
                if isinstance(open_value, PreparedElementOpen):
                    data[operation.attrs_key] = (
                        _spread_data_attrs(operation.node, open_value)
                        if operation.node._has_spread
                        else dict(open_value.data_attrs)
                    )
                else:
                    data[operation.attrs_key] = open_value
            if operation.key_key is not None:
                if not isinstance(open_value, PreparedElementOpen):
                    raise AssertionError("prepared key metadata requires a structured opening")
                metadata = dict(open_value.element_metadata)
                data[operation.key_key] = metadata["key"]
            if operation.control_key is not None:
                data[operation.control_key] = (
                    ",".join(str(binding["id"]) for binding in open_value.control_bindings)
                    if isinstance(open_value, PreparedElementOpen)
                    else ""
                )
            if operation.runtime_events_key is not None:
                data[operation.runtime_events_key] = (
                    ",".join(
                        str(binding["id"])
                        for binding in (*open_value.runtime_event_bindings, *open_value.runtime_poll_bindings)
                    )
                    if isinstance(open_value, PreparedElementOpen)
                    else ""
                )
            if isinstance(open_value, PreparedElementOpen) and (
                open_value.event_bindings or open_value.runtime_event_bindings
            ):
                events = root_data.setdefault("eventBindings", {})
                if not isinstance(events, dict):
                    raise AssertionError("leaf event binding container changed type")
                for binding in open_value.event_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = events.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf event binding id has conflicting metadata")
                for binding in open_value.runtime_event_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = events.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf runtime event binding id has conflicting metadata")
            if isinstance(open_value, PreparedElementOpen) and (
                open_value.poll_bindings or open_value.runtime_poll_bindings
            ):
                polls = root_data.setdefault("pollBindings", {})
                if not isinstance(polls, dict):
                    raise AssertionError("leaf poll binding container changed type")
                for binding in open_value.poll_bindings:
                    polls[str(binding["id"])] = dict(binding)
                for binding in open_value.runtime_poll_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = polls.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf runtime poll binding id has conflicting metadata")
            if isinstance(open_value, PreparedElementOpen) and open_value.control_bindings:
                controls = root_data.setdefault("controlBindings", {})
                if not isinstance(controls, dict):
                    raise AssertionError("leaf control binding container changed type")
                for binding in open_value.control_bindings:
                    controls[str(binding["id"])] = dict(binding)
        elif isinstance(operation, _Close):
            continue
        elif isinstance(operation, _If):
            try:
                body = operation.node.active_branch_body(context)
            except Exception as error:
                _attach_error(error, operation.node, context)
                raise
            selected = next((index for index, branch in enumerate(operation.node.branches) if branch[2] is body), -1)
            data[operation.key] = selected
            if selected >= 0:
                _evaluate(operation.branches[selected], context, data, root_data, vue_errors, special, resolved_opens)
        elif isinstance(operation, _For):
            records: list[dict[str, object]] = []
            rendered_any = False
            try:
                for _body, child_context in operation.node.iter_bodies(context):
                    if child_context is context:
                        _evaluate(operation.empty, context, data, root_data, vue_errors, special, resolved_opens)
                        continue
                    rendered_any = True
                    record: dict[str, object] = {}
                    records.append(record)
                    _evaluate(operation.body, child_context, record, root_data, vue_errors, special, resolved_opens)
            except Exception as error:
                _attach_error(error, operation.node, context)
                raise
            data[operation.key] = records
            if not rendered_any and not operation.empty:
                data[operation.key] = []
        else:
            raise TypeError(f"unknown leaf operation: {type(operation).__name__}")


def _attach_error(error: Exception, node: Node, context: CitryContext) -> None:
    from citry.component_render import _attach_template_position  # noqa: PLC0415

    _attach_template_position(error, node, context)


def _validate_open(value: PreparedElementOpen) -> str | None:
    data_targets = {_html_attr_identity(name): name for name in value.data_attrs}
    for name in value.data_attrs:
        if name.startswith(("v-", "@", ":")):
            return (
                f"Python-resolved attribute {name!r} on <{value.tag}> cannot introduce Vue syntax; "
                "Vue directives and bindings must be authored statically in the template."
            )
        normalized = name.casefold()
        if normalized in {"innerhtml", "outerhtml", "textcontent", "innertext"} or normalized.startswith("on"):
            return f"prepared dynamic DOM property is unsafe for the bounded Vue target: {name!r}"
    source_targets = {
        _html_attr_identity(target): attr.name
        for attr in value.attrs
        if attr.origin == "source"
        for target in [_source_target(attr.name)]
        if target is not None
    }
    metadata = dict(value.element_metadata)
    if "key" in metadata and ("key" in source_targets or "key" in data_targets):
        return "prepared #c-key conflicts with another authored key"
    conflict = source_targets.keys() & data_targets.keys()
    if conflict:
        names = [f"{source_targets[identity]!r} / {data_targets[identity]!r}" for identity in sorted(conflict)]
        return f"authored Vue and prepared Python attributes target the same HTML name: {names!r}"
    dynamic_bindings = [
        attr.name for attr in value.attrs if attr.origin == "source" and attr.name.startswith((":[", "v-bind:["))
    ]
    has_prepared_target = bool(value.data_attrs) or "key" in metadata
    if has_prepared_target and any(attr.name == "v-bind" for attr in value.attrs if attr.origin == "source"):
        return "authored object v-bind cannot yet be combined with prepared Python attributes"
    if has_prepared_target and dynamic_bindings:
        return (
            "authored dynamic-argument Vue bindings cannot be proven unrelated to prepared Python attributes: "
            f"{dynamic_bindings!r}"
        )
    return None


def _validate_data_attrs(value: dict[str, object], *, tag: str) -> str | None:
    reserved = next((name for name in value if name.lower().startswith("data-cev-")), None)
    if reserved is not None:
        return f"reserved Events metadata cannot be introduced through Python attributes: {reserved!r}"
    private = next(
        (name for name in value if name.lower() in {"data-citry-runtime-control", "data-citry-runtime-events"}),
        None,
    )
    if private is not None:
        return f"reserved Events metadata cannot be introduced through Python attributes: {private!r}"
    for name in value:
        if name.startswith(("v-", "@", ":")):
            return (
                f"Python-resolved attribute {name!r} on <{tag}> cannot introduce Vue syntax; "
                "Vue directives and bindings must be authored statically in the template."
            )
        normalized = name.casefold()
        if normalized in {"innerhtml", "outerhtml", "textcontent", "innertext"} or normalized.startswith("on"):
            return f"prepared dynamic DOM property is unsafe for the bounded Vue target: {name!r}"
    return None


def _source_attrs_are_projectable(node: PreparedElementOpenNode) -> bool:
    """Whether selected authored attributes may safely travel through v-bind."""
    return all(
        _validate_data_attrs({attr.key: attr.value}, tag=node.tag) is None
        for attr, _source in node._static_source_attrs
    )


def _spread_data_attrs(
    node: PreparedElementOpenNode,
    prepared: PreparedElementOpen,
) -> dict[str, object]:
    """Project one selected spread opening without parsing its source text."""
    value = dict(prepared.data_attrs)
    source_values = {(attr.key, attr.position): attr.value for attr, _source in node._static_source_attrs}
    for attr in prepared.attrs:
        if attr.origin != "source":
            continue
        identity = (attr.name, attr.span)
        if identity not in source_values:
            raise AssertionError("selected leaf source attribute lost its parsed identity")
        source_value = source_values[identity]
        value[attr.name] = "" if source_value is True else source_value
    return value


def _source_target(name: str) -> str | None:
    if name == "key":
        return name
    if name.startswith(":"):
        return name[1:].split(".", 1)[0]
    if name.startswith("v-bind:"):
        return name[7:].split(".", 1)[0]
    if re.fullmatch(r"[A-Za-z_:][A-Za-z0-9_.:-]*", name):
        return name
    return None


def static_leaf_parts(value: PreparedLeafProgram) -> list[str]:
    """Materialize static HTML from the values already recorded by the program."""
    if value.cached_static_parts is not None:
        return list(value.cached_static_parts)
    output: list[str] = []
    _materialize(value.operations, value.prepared_data, value.resolved_opens, output)
    return output


def typed_leaf_parts(value: PreparedLeafProgram) -> list[RenderPart]:
    """Materialize typed fallback parts from already-recorded program values."""
    if value.cached_typed_parts is not None:
        return list(value.cached_typed_parts)
    output: list[RenderPart] = []
    _materialize_typed(
        value.operations,
        value.prepared_data,
        value.prepared_data,
        {},
        value.resolved_opens,
        output,
    )
    return output


def _materialize_typed(
    operations: tuple[object, ...],
    data: dict[str, object],
    root_data: dict[str, object],
    special: dict[tuple[int, str], RenderPart],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]],
    output: list[RenderPart],
) -> None:
    for operation in operations:
        if isinstance(operation, _Static):
            output.append(operation.typed)
        elif isinstance(operation, _Text):
            special_value = special.get((id(data), operation.key))
            if special_value is not None:
                output.append(special_value)
            else:
                output.append(PreparedTextValue(operation.node.source, operation.node.position, data[operation.key]))
        elif isinstance(operation, _Open):
            resolved = operation.static or resolved_opens[(id(data), id(operation))]
            output.append(_prepared_open(operation, resolved))
            if operation.node.is_self_closing and not operation.node.is_void:
                end = operation.node.position[1]
                output.append(PreparedElementClose(operation.node.source, (end, end), operation.node.tag))
        elif isinstance(operation, _Close):
            output.append(operation.value)
        elif isinstance(operation, _If):
            selected_value = data[operation.key]
            if type(selected_value) is not int:
                raise AssertionError("leaf branch selection changed type")
            selected = selected_value
            if selected >= 0:
                _materialize_typed(operation.branches[selected], data, root_data, special, resolved_opens, output)
        elif isinstance(operation, _For):
            records = data[operation.key]
            if not isinstance(records, list):
                raise TypeError("leaf loop record changed type")
            if records:
                for record in records:
                    if not isinstance(record, dict):
                        raise TypeError("leaf loop item changed type")
                    _materialize_typed(operation.body, record, root_data, special, resolved_opens, output)
            else:
                _materialize_typed(operation.empty, data, root_data, special, resolved_opens, output)


def _materialize(
    operations: tuple[object, ...],
    data: dict[str, object],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object]],
    output: list[str],
) -> None:
    for operation in operations:
        if isinstance(operation, _Static):
            output.append(operation.html)
        elif isinstance(operation, _Text):
            output.append(escape_to_str(data[operation.key]))
        elif isinstance(operation, _Open):
            resolved = operation.static or resolved_opens[(id(data), id(operation))]
            if isinstance(resolved, dict):
                attrs = list(operation.authored_attrs)
                formatted = str(format_attrs(resolved))
                if formatted:
                    attrs.append(formatted)
            else:
                from citry._vue.capture import format_prepared_element_attrs  # noqa: PLC0415

                attrs = list(format_prepared_element_attrs(resolved))
            suffix = "" if not attrs else " " + " ".join(attrs)
            # The compiler emits an explicit close for non-void authored
            # self-closing elements. Only HTML void syntax keeps its slash in
            # materialized static output.
            ending = "/>" if operation.node.is_void and operation.node.is_self_closing else ">"
            output.append(f"<{operation.node.tag}{suffix}{ending}")
            if operation.node.is_self_closing and not operation.node.is_void:
                output.append(f"</{operation.node.tag}>")
        elif isinstance(operation, _Close):
            output.append(f"</{operation.value.tag}>")
        elif isinstance(operation, _If):
            selected_value = data[operation.key]
            if type(selected_value) is not int:
                raise AssertionError("leaf branch selection changed type")
            selected = selected_value
            if selected >= 0:
                _materialize(operation.branches[selected], data, resolved_opens, output)
        elif isinstance(operation, _For):
            records = data[operation.key]
            if not isinstance(records, list):
                raise TypeError("leaf loop record changed type")
            if records:
                for record in records:
                    if not isinstance(record, dict):
                        raise TypeError("leaf loop item changed type")
                    _materialize(operation.body, record, resolved_opens, output)
            else:
                _materialize(operation.empty, data, resolved_opens, output)
        else:
            raise TypeError(f"unknown leaf operation: {type(operation).__name__}")


def _prepared_open(operation: _Open, resolved: PreparedElementOpen | dict[str, object]) -> PreparedElementOpen:
    if isinstance(resolved, PreparedElementOpen):
        return resolved
    spans = {name: attr.position for name, attr in operation.fixed_attrs or ()}
    if operation.spread_renderer is not None:
        spans = {name: operation.node._data_attr_span(name) for name in resolved}
        authored_attributes: tuple[PreparedAttribute, ...] = ()
    else:
        authored_attributes = operation.authored_attributes
    data_attributes: list[PreparedAttribute] = []
    for name, value in resolved.items():
        if include_prepared_attribute(value):
            data_attributes.append(PreparedAttribute(name, "data", spans[name], value))
    return PreparedElementOpen(
        operation.node.source,
        operation.node.position,
        operation.node.tag,
        (
            *authored_attributes,
            *data_attributes,
        ),
        operation.node.is_void,
        operation.node.is_self_closing,
        (),
        (),
        (),
    )
