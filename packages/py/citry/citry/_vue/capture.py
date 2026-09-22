"""Build typed source and Python-value render parts for the experimental Vue renderer."""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from html import unescape
from inspect import getattr_static
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, cast

from citry.attrs import _html_attr_identity, merge_attrs
from citry.citry_render import CitryRender, _default_value_dispatch_for, _render_value
from citry.constness import const_value
from citry.nodes import ElementAttrsNode, ElementKeyNode, ExprHtmlAttr, ExprNode, ForNode, Node
from citry.util.html import Markup

from .direct import DirectProjectionRender, bind_nested_template, wrap_python_composition_result

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from citry.assets import HasHtml
    from citry.citry_context import CitryContext
    from citry.citry_element import CitryElement
    from citry.citry_render import PreparedRenderPart, RenderPart
    from citry.nodes import BodyItem, FillSink


_PREPARED_RENDER: ContextVar[bool] = ContextVar("citry_vue_prepared_render", default=False)
_DIRECT_PREPARED_RENDER: ContextVar[bool] = ContextVar("citry_vue_direct_prepared_render", default=False)
_VUE_RENDER: ContextVar[bool] = ContextVar("citry_vue_render_target", default=False)


def include_prepared_attribute(value: object) -> bool:
    """Omit absent HTML attributes while retaining presence metadata."""
    return value is not None and value is not False


VUE_OWNED_NATIVE_DIRECTIVE = "v-citry-vue-owned"
_NATIVE_PROPERTIES = frozenset({"value", "checked", "selected"})


def _attribute_name_and_value(attribute: object) -> tuple[str, object | None]:
    """Read a source attribute's name and value from either AST or prepared form."""
    if isinstance(attribute, str):
        match = re.match(r"\s*([^\s=/>]+)(?:\s*=\s*(.*?))?\s*$", attribute)
        return (match.group(1), match.group(2)) if match else (attribute.strip(), None)
    name = getattr(attribute, "name", getattr(attribute, "key", ""))
    value = getattr(attribute, "value", None)
    return str(name), value


def _source_static_value(value: object | None) -> str | None:
    """Extract a static attribute value from AST or serialized source text."""
    if not isinstance(value, str):
        return None
    match = re.match(r"\s*[^\s=/>]+\s*=\s*(['\"])(.*?)\1\s*$", value)
    if match:
        return match.group(2)
    return value.strip().strip("'\"")


def _native_properties_for_tag(tag: str, input_type: str | None = None) -> frozenset[str]:
    normalized = tag.casefold()
    if normalized == "textarea":
        return frozenset({"value"})
    if normalized == "select":
        return frozenset({"selected"})
    if normalized == "option":
        return frozenset({"value", "selected"})
    if normalized != "input":
        return frozenset()
    return frozenset({"value", "checked"}) if input_type in {None, "checkbox", "radio"} else frozenset({"value"})


def is_native_state_tag(tag: str) -> bool:
    """Whether the tag can retain browser-managed form state."""
    return tag.casefold() in {"input", "textarea", "select", "option"}


def vue_owned_native_properties(
    tag: str,
    authored_attrs: object = (),
    data_attrs: object = (),
    *,
    has_spread: bool = False,
) -> frozenset[str]:
    """
    Return native properties whose values are authored Vue/Python bindings.

    This marker is deliberately property-specific. A ``:value`` binding must
    not suppress preservation of an independently dirty checkbox, and a
    ``:checked`` binding must not suppress an input's text value. Object
    ``v-bind`` and dynamic arguments are conservative because their runtime
    property is not known at capture time.
    """
    attrs: tuple[object, ...] = () if authored_attrs is None else tuple(cast("Iterable[object]", authored_attrs))
    input_type: str | None = None
    dynamic_input_type = has_spread
    for attribute in attrs:
        name, value = _attribute_name_and_value(attribute)
        normalized = name.casefold()
        if normalized == "type":
            input_type = (_source_static_value(value) or "").casefold() or None
        elif normalized in {":type", "v-bind:type", "v-bind", ":["} or normalized.startswith(
            (":type.", "v-bind:type.", "v-bind.", "v-bind:[", ":[")
        ):
            dynamic_input_type = True
    if hasattr(data_attrs, "keys"):
        data_names: tuple[object, ...] = tuple(cast("Mapping[object, object]", data_attrs).keys())
    else:
        data_names = tuple(cast("Iterable[object]", data_attrs or ()))
    if any(str(name).casefold().removeprefix("c-") == "type" for name in data_names):
        dynamic_input_type = True
    if dynamic_input_type:
        input_type = None
    available = _native_properties_for_tag(tag, input_type)
    if not available:
        return frozenset()
    owned: set[str] = set()
    if has_spread:
        owned.update(available)
    for attribute in attrs:
        name, _value = _attribute_name_and_value(attribute)
        normalized = name.casefold()
        if normalized == "v-bind" or normalized.startswith(("v-bind.", ":[", "v-bind:[")):
            owned.update(available)
        elif normalized == "v-model" or normalized.startswith("v-model."):
            if input_type is None:
                owned.update(available)
            elif "checked" in available and input_type in {"checkbox", "radio"}:
                owned.add("checked")
            else:
                owned.update(available & {"value", "selected"})
        elif normalized in {":value", "v-bind:value"} or normalized.startswith((":value.", "v-bind:value.")):
            owned.add("value" if tag.casefold() == "option" else ("selected" if "selected" in available else "value"))
        elif normalized in {":checked", "v-bind:checked"} or normalized.startswith((":checked.", "v-bind:checked.")):
            owned.add("checked")
        elif normalized in {":selected", "v-bind:selected"} or normalized.startswith(
            (":selected.", "v-bind:selected.")
        ):
            owned.add("selected")
    for data_name in data_names:
        normalized = str(data_name).casefold().removeprefix("c-")
        if normalized == "value":
            owned.add("value" if tag.casefold() == "option" else ("selected" if "selected" in available else "value"))
        elif normalized == "checked":
            owned.add("checked")
        elif normalized == "selected":
            owned.add("selected")
    return frozenset(owned & set(available))


def vue_owned_native_marker(properties: object) -> str:
    """Serialize the private Vue ownership directive for trusted compiler output."""
    values: tuple[str, ...] = tuple(sorted(set(cast("Iterable[str]", properties)) & _NATIVE_PROPERTIES))
    expression = (
        "[]"
        if not values
        else (repr(values[0]) if len(values) == 1 else "[" + ",".join(repr(value) for value in values) + "]")
    )
    return f'{VUE_OWNED_NATIVE_DIRECTIVE}="{expression}"'


def _is_reserved_vue_owned_name(name: str) -> bool:
    normalized = name.casefold()
    return normalized == VUE_OWNED_NATIVE_DIRECTIVE or normalized.startswith(
        (VUE_OWNED_NATIVE_DIRECTIVE + ".", VUE_OWNED_NATIVE_DIRECTIVE + ":")
    )


def prepared_render_active() -> bool:
    """Whether the current render is using the private prepared target."""
    return _PREPARED_RENDER.get()


def direct_prepared_render_active() -> bool:
    """Whether graph-free relationship capture is active for this prepared render."""
    return _DIRECT_PREPARED_RENDER.get()


def vue_render_active() -> bool:
    """Whether the selected typed tree must satisfy the native Vue target."""
    return _VUE_RENDER.get()


@contextmanager
def typed_render_scope(*, direct: bool = False, vue: bool = False) -> Iterator[None]:
    """Select typed parts and direct relationships for one root render."""
    prepared_token = _PREPARED_RENDER.set(True)
    direct_token = _DIRECT_PREPARED_RENDER.set(direct)
    vue_token = _VUE_RENDER.set(vue)
    try:
        yield
    finally:
        _VUE_RENDER.reset(vue_token)
        _DIRECT_PREPARED_RENDER.reset(direct_token)
        _PREPARED_RENDER.reset(prepared_token)


def render_prepared(
    element: CitryElement,
    *,
    template_globals: Mapping[str, Any] | None = None,
    provides: Mapping[str, Any] | None = None,
) -> CitryRender:
    """Render through the sole graph-free prepared target."""
    return render_prepared_direct(element, template_globals=template_globals, provides=provides)


def render_prepared_direct(
    element: CitryElement,
    *,
    template_globals: Mapping[str, Any] | None = None,
    provides: Mapping[str, Any] | None = None,
) -> CitryRender:
    """Render with typed parts and direct relationships, without an ownership graph."""
    from citry._vue.direct import direct_render_scope  # noqa: PLC0415

    nested_direct = direct_prepared_render_active()
    if prepared_render_active() and not vue_render_active():
        raise RuntimeError("cannot enter direct prepared rendering inside another prepared-render mode")
    try:
        with typed_render_scope(direct=True, vue=True) if not nested_direct else direct_render_scope():
            rendered = element.render(template_globals=template_globals, provides=provides)
            _validate_prepared_render(rendered)
            return rendered
    finally:
        pass


def render_prepared_marker_replacement(
    renderable: CitryElement | CitryRender,
    *,
    citry: Any,
    name: str,
) -> CitryRender:
    """Render one payload once and wrap it in the engine-owned private Mark."""
    if prepared_render_active() and not vue_render_active():
        raise RuntimeError("cannot enter direct prepared rendering inside another prepared-render mode")
    with typed_render_scope(direct=True, vue=True):
        payload = renderable.render() if not isinstance(renderable, CitryRender) else renderable
        if payload.render_target != "prepared":
            raise TypeError("marker replacement requires a typed prepared CitryRender")
        metadata = payload.frame.prepared_occurrence
        adapted = CitryRender(
            list(payload.parts),
            payload.context,
            frame=replace(
                payload.frame,
                prepared_occurrence=replace(metadata, call=None) if metadata is not None else None,
            ),
            render_target="prepared",
        )
        mark_class = citry.get("mark")
        if not citry._is_builtin_component(mark_class) or mark_class.name != "mark":
            raise ValueError("marker replacement requires the engine-owned Mark component")
        from citry.components.mark import synthetic_mark_replacement  # noqa: PLC0415

        wrapped = synthetic_mark_replacement(mark_class, name, adapted).render()
        _validate_prepared_render(wrapped)
        return wrapped


@dataclass(frozen=True, slots=True)
class PreparedSourceText:
    source: str
    span: tuple[int, int]
    text: str


@dataclass(frozen=True, slots=True)
class PreparedVerbatimHtml:
    """Authenticated ``<c-raw>`` body retained as opaque HTML data."""

    source: str
    span: tuple[int, int]
    html: str


@dataclass(frozen=True, slots=True)
class PreparedTextValue:
    source: str
    span: tuple[int, int]
    value: object
    escape_policy: Literal["vue-text"] = "vue-text"
    browser_binding: PreparedBrowserBinding | None = None


@dataclass(frozen=True, slots=True)
class PreparedBrowserBinding:
    helper: str
    operand: object
    target: Literal["text", "attribute"]
    name: str | None = None
    values_expression: str | None = None
    _producer_token: object | None = field(default=None, init=False, repr=False, compare=False)


_BROWSER_BINDING_TOKEN = object()


def prepared_browser_binding(
    *,
    helper: str,
    operand: object,
    target: Literal["text", "attribute"],
    name: str | None = None,
    values_expression: str | None = None,
) -> PreparedBrowserBinding:
    """Create one checked browser projection from trusted producer metadata."""
    if not re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", helper):
        raise ValueError("prepared browser binding helper must be one reserved template-context name")
    if target not in {"text", "attribute"}:
        raise ValueError("prepared browser binding target is invalid")
    if (target == "text") != (name is None):
        raise ValueError("prepared browser binding target and attribute name disagree")
    if values_expression is not None and (type(values_expression) is not str or not values_expression):
        raise ValueError("prepared browser binding values expression must be non-empty")
    value = PreparedBrowserBinding(helper, operand, target, name, values_expression)
    object.__setattr__(value, "_producer_token", _BROWSER_BINDING_TOKEN)
    return value


def is_authenticated_browser_binding(value: PreparedBrowserBinding) -> bool:
    return value._producer_token is _BROWSER_BINDING_TOKEN


@dataclass(frozen=True, slots=True)
class PreparedTrustedHtmlValue:
    """Trusted Python HTML retained for the static serializer only."""

    html: str


@dataclass(frozen=True, slots=True)
class PreparedAttribute:
    name: str
    origin: Literal["source", "data"]
    span: tuple[int, int]
    value: object


@dataclass(frozen=True, slots=True)
class PreparedElementOpen:
    source: str
    span: tuple[int, int]
    tag: str
    attrs: tuple[PreparedAttribute, ...]
    is_void: bool
    is_self_closing: bool
    element_metadata: tuple[tuple[str, object], ...]
    event_bindings: tuple[Mapping[str, object], ...] = ()
    poll_bindings: tuple[Mapping[str, object], ...] = ()
    control_bindings: tuple[Mapping[str, object], ...] = ()
    browser_bindings: tuple[PreparedBrowserBinding, ...] = ()
    runtime_event_bindings: tuple[Mapping[str, object], ...] = ()
    runtime_events_candidate: bool = False
    runtime_poll_bindings: tuple[Mapping[str, object], ...] = ()
    has_spread: bool = False
    authored_attrs: tuple[str, ...] = field(init=False, repr=False)
    data_attrs: Mapping[str, object] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if (self.runtime_event_bindings or self.runtime_poll_bindings) and not self.runtime_events_candidate:
            raise ValueError("runtime event and poll bindings require an authenticated compiled candidate site")
        if any(attr.origin == "source" and _is_reserved_vue_owned_name(attr.name) for attr in self.attrs):
            raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")
        object.__setattr__(
            self,
            "authored_attrs",
            tuple(str(attr.value) for attr in self.attrs if attr.origin == "source"),
        )
        object.__setattr__(
            self,
            "data_attrs",
            MappingProxyType({attr.name: attr.value for attr in self.attrs if attr.origin == "data"}),
        )


def format_prepared_element_attrs(value: PreparedElementOpen) -> tuple[str, ...]:
    """Materialize one prepared opening's attributes in resolved first-seen order."""
    from citry.attrs import format_attrs  # noqa: PLC0415

    rendered: list[str] = []
    for attr in value.attrs:
        if attr.origin == "source":
            rendered.append(str(attr.value))
        else:
            formatted = str(format_attrs({attr.name: attr.value}))
            if formatted:
                rendered.append(formatted)
    return tuple(rendered)


@dataclass(frozen=True, slots=True)
class PreparedElementClose:
    source: str
    span: tuple[int, int]
    tag: str


@dataclass(frozen=True, slots=True)
class PreparedDynamicElementOpen:
    """Validated dynamic HTML opening retained without trusted-markup flattening."""

    tag: str
    attrs: Mapping[str, object]
    is_void: bool
    authored_attrs: tuple[PreparedAttribute, ...] = ()
    key: str | None = None
    authored_source: str | None = None
    event_bindings: tuple[Mapping[str, object], ...] = ()
    poll_bindings: tuple[Mapping[str, object], ...] = ()
    control_bindings: tuple[Mapping[str, object], ...] = ()
    runtime_event_bindings: tuple[Mapping[str, object], ...] = ()
    runtime_events_candidate: bool = False
    runtime_poll_bindings: tuple[Mapping[str, object], ...] = ()
    has_spread: bool = False
    _producer_token: object | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attrs", MappingProxyType(dict(self.attrs)))
        object.__setattr__(self, "event_bindings", _normalize_event_bindings(self.event_bindings))
        object.__setattr__(self, "poll_bindings", _normalize_poll_bindings(self.poll_bindings))
        object.__setattr__(self, "control_bindings", _normalize_control_bindings(self.control_bindings))
        object.__setattr__(self, "runtime_event_bindings", _normalize_event_bindings(self.runtime_event_bindings))
        object.__setattr__(
            self,
            "runtime_poll_bindings",
            _normalize_runtime_poll_bindings(self.runtime_poll_bindings),
        )
        if (self.runtime_event_bindings or self.runtime_poll_bindings) and not self.runtime_events_candidate:
            raise ValueError("runtime event and poll bindings require an authenticated compiled candidate site")
        if any(attr.origin == "source" and _is_reserved_vue_owned_name(attr.name) for attr in self.authored_attrs):
            raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")


@dataclass(frozen=True, slots=True)
class PreparedDynamicElementClose:
    """Closing boundary paired with one prepared dynamic opening."""

    tag: str


_DYNAMIC_ELEMENT_PRODUCER_TOKEN = object()


def prepared_dynamic_element_open(
    tag: str,
    attrs: Mapping[str, object],
    *,
    authored_bindings: tuple[object, ...] = (),
    key: str | None = None,
    normalized: PreparedElementOpen | None = None,
) -> PreparedDynamicElementOpen:
    """Freeze one validated dynamic-element opening with private producer provenance."""
    from citry.client_directives import (  # noqa: PLC0415
        ComponentTagClientBinding,
        ComponentTagClientBindingKind,
        is_authenticated_component_tag_client_binding,
    )
    from citry_core.template_parser import HTML_VOID_ELEMENTS  # noqa: PLC0415

    prepared_attrs: list[PreparedAttribute] = []
    authored_source: str | None = None
    for binding in authored_bindings:
        if (
            type(binding) is not ComponentTagClientBinding
            or binding.kind
            not in {
                ComponentTagClientBindingKind.EVENT,
                ComponentTagClientBindingKind.PROP,
                ComponentTagClientBindingKind.PROPS_OBJECT,
            }
            or not is_authenticated_component_tag_client_binding(binding)
            or type(binding.source) is not str
        ):
            raise TypeError("dynamic element authored Vue binding lost parser provenance")
        if authored_source is None:
            authored_source = binding.source
        elif binding.source is not authored_source:
            raise TypeError("dynamic element authored Vue bindings disagree on parser source")
        source_bytes = binding.source.encode()
        start, end = binding.span
        try:
            source_text = source_bytes[start:end].decode()
        except (UnicodeDecodeError, IndexError) as error:
            raise TypeError("dynamic element authored Vue binding has an invalid source span") from error
        prepared_attrs.append(PreparedAttribute(binding.key, "source", binding.span, source_text))
    if any(_is_reserved_vue_owned_name(attr.name) for attr in prepared_attrs):
        raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")
    if any(_is_reserved_vue_owned_name(str(name)) for name in attrs):
        raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")
    value = PreparedDynamicElementOpen(
        tag,
        MappingProxyType(dict(attrs)),
        tag.lower() in HTML_VOID_ELEMENTS,
        tuple(prepared_attrs),
        key,
        authored_source,
        () if normalized is None else tuple(dict(value) for value in normalized.event_bindings),
        () if normalized is None else tuple(dict(value) for value in normalized.poll_bindings),
        () if normalized is None else tuple(dict(value) for value in normalized.control_bindings),
        () if normalized is None else tuple(dict(value) for value in normalized.runtime_event_bindings),
        False if normalized is None else normalized.runtime_events_candidate,
        () if normalized is None else tuple(dict(value) for value in normalized.runtime_poll_bindings),
        False if normalized is None else normalized.has_spread,
    )
    object.__setattr__(value, "_producer_token", _DYNAMIC_ELEMENT_PRODUCER_TOKEN)
    return value


def is_authenticated_dynamic_element_open(value: PreparedDynamicElementOpen) -> bool:
    """Return whether this opening came from the dynamic-element producer."""
    from citry.components.dynamic import _validate_tag_name  # noqa: PLC0415
    from citry_core.template_parser import HTML_VOID_ELEMENTS  # noqa: PLC0415

    if value._producer_token is not _DYNAMIC_ELEMENT_PRODUCER_TOKEN:
        return False
    if bool(value.authored_attrs) is (value.authored_source is None):
        return False
    if value.authored_source is not None:
        source_bytes = value.authored_source.encode()
        for attr in value.authored_attrs:
            if (
                attr.origin != "source"
                or type(attr.value) is not str
                or (not attr.name.startswith(("@", ":", "v-on:", "v-bind:", "v-bind.")) and attr.name != "v-bind")
            ):
                return False
            if _is_reserved_vue_owned_name(attr.name):
                return False
            start, end = attr.span
            try:
                if source_bytes[start:end].decode() != attr.value:
                    return False
            except (UnicodeDecodeError, IndexError):
                return False
    if value.key is not None and type(value.key) is not str:
        return False
    if (value.runtime_event_bindings or value.runtime_poll_bindings) and not value.runtime_events_candidate:
        return False
    try:
        _validate_tag_name(value.tag)
    except (TypeError, ValueError):
        return False
    return value.is_void is (value.tag.lower() in HTML_VOID_ELEMENTS)


@dataclass(frozen=True, slots=True)
class PreparedStaticRun:
    """Adjacent authored markup rendered once from immutable descriptors."""

    html: str
    root_structure: StaticRunStructure | None = None


@dataclass(frozen=True, slots=True)
class StaticRunOpening:
    start_at: int
    insert_at: int
    end_at: int
    relative_depth: int
    attr_identities: frozenset[str]


@dataclass(frozen=True, slots=True)
class StaticRunStructure:
    openings: tuple[StaticRunOpening, ...]
    final_depth_delta: int
    tag_transitions: tuple[tuple[str, str], ...] = ()


class PreparedStaticRunNode(Node):
    def __init__(self, html: str, root_structure: StaticRunStructure | None = None) -> None:
        self._prepared = PreparedStaticRun(html, root_structure)

    def render(self, context: CitryContext) -> PreparedStaticRun:  # noqa: ARG002
        return self._prepared


class PreparedConstantNode(Node):
    """One immutable typed result selected by Const specialization."""

    def __init__(self, value: PreparedRenderPart) -> None:
        self.value = value

    def render(self, context: CitryContext) -> PreparedRenderPart:  # noqa: ARG002
        return self.value


@dataclass(frozen=True, slots=True)
class PreparedConstantElementKey:
    """One immutable plain-element key selected by Const specialization."""

    value: object


class PreparedConstPrecomputeAdapter:
    """Typed result representation for the shared Const visitor."""

    def expression(self, node: ExprNode, context: CitryContext) -> BodyItem:
        if not isinstance(node, PreparedExprNode):
            return node
        try:
            value = const_value(node.evaluate(context.variables, sandboxed=context.sandboxed))
            kind = type(value)
            if value is None:
                normalized: str | PreparedTrustedHtmlValue = ""
            elif kind in {str, int, float, bool} and _default_value_dispatch_for(kind):
                normalized = value if kind is str else str(value)
            elif kind is Markup:
                normalized = PreparedTrustedHtmlValue(str(value.__html__()))
            else:
                # Arbitrary value rendering can invoke slots, components, or
                # user-defined protocols. Keep that work at the selected live
                # render site even when the expression only refers to Consts.
                return node
        except Exception:  # noqa: BLE001 -- normal rendering owns the error
            return node
        if isinstance(normalized, PreparedTrustedHtmlValue):
            return PreparedConstantNode(normalized)
        return PreparedConstantNode(PreparedTextValue(node.source, node.position, normalized))

    def element_attrs(self, node: ElementAttrsNode, context: CitryContext) -> BodyItem:
        if not isinstance(node, PreparedElementOpenNode):
            return node
        try:
            return PreparedConstantNode(node.render(context))
        except Exception:  # noqa: BLE001 -- normal rendering owns the error
            return node

    def element_metadata(
        self,
        node: ElementAttrsNode,
        const_names: frozenset[str],
        context: CitryContext,
    ) -> ElementAttrsNode:
        if not isinstance(node, PreparedElementOpenNode):
            return node
        specialized: list[tuple[str, object]] = []
        changed = False
        for kind, value in node.element_metadata:
            if kind == "key" and isinstance(value, ExprHtmlAttr) and set(value.used_vars) <= const_names:
                try:
                    resolved = const_value(value.resolve(context))
                    resolved = None if resolved is None else str(resolved)
                except Exception:  # noqa: BLE001 -- normal rendering owns the error
                    specialized.append((kind, value))
                else:
                    specialized.append((kind, PreparedConstantElementKey(resolved)))
                    changed = True
            else:
                specialized.append((kind, value))
        return node._with_element_metadata(tuple(specialized)) if changed else node

    def element_key(self, node: ElementKeyNode, context: CitryContext) -> BodyItem:  # noqa: ARG002
        return node

    def static_parts(self, item: object) -> tuple[RenderPart, ...] | None:
        if isinstance(item, (PreparedSourceTextNode, PreparedStaticRunNode)):
            return (item._prepared,)
        if isinstance(item, PreparedElementCloseNode):
            return (item._prepared,)
        if isinstance(item, PreparedElementOpenNode) and item._static_prepared is not None:
            return (item._static_prepared,)
        if isinstance(item, PreparedConstantNode) and isinstance(
            item.value,
            (PreparedSourceText, PreparedStaticRun, PreparedTextValue, PreparedTrustedHtmlValue, PreparedElementOpen),
        ):
            return (item.value,)
        return None

    def unrolled_for(self, node: ForNode, parts: tuple[object, ...]) -> BodyItem:
        # This adapter's static_parts method is the only source of this tuple.
        return node._with_precomputed_parts(cast("tuple[RenderPart, ...]", parts))


PREPARED_CONST_PRECOMPUTE_ADAPTER = PreparedConstPrecomputeAdapter()


class PreparedSourceTextNode(Node):
    def __init__(self, source: str, span: tuple[int, int], text: str) -> None:
        self.source = source
        self.position = span
        self.text = text
        self._prepared = PreparedSourceText(source, span, text)

    def render(self, context: CitryContext) -> PreparedSourceText:  # noqa: ARG002
        return self._prepared

    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:  # noqa: ARG002
        if self.text.strip():
            msg = (
                f"Text cannot appear next to '<c-fill>' tags in the body of "
                f"<c-{sink.component_name}>. All other content must be inside the fills."
            )
            raise RuntimeError(msg)


class PreparedVerbatimHtmlNode(Node):
    def __init__(self, source: str, span: tuple[int, int], html: str) -> None:
        self.source = source
        self.position = span
        self.html = html
        self._prepared = PreparedVerbatimHtml(source, span, html)

    def render(self, context: CitryContext) -> PreparedVerbatimHtml:  # noqa: ARG002
        return self._prepared


class PreparedExprNode(ExprNode):
    def resolve_value(self, context: CitryContext) -> RenderPart:
        """Evaluate once and return normalized text or structured fallback output."""
        value = const_value(self.evaluate(context.variables, sandboxed=context.sandboxed))
        return self.resolve_evaluated_value(value, context)

    def resolve_evaluated_value(self, value: object, context: CitryContext) -> RenderPart:
        """Normalize one already evaluated expression without evaluating it again."""
        value = bind_nested_template(value, context)
        if isinstance(value, DirectProjectionRender):
            return value
        if isinstance(value, (PreparedDynamicElementOpen, PreparedDynamicElementClose)):
            return value
        kind = type(value)
        if value is None:
            return ""
        if kind in {str, int, float, bool} and _default_value_dispatch_for(kind):
            return str(value)
        from citry.slots import _EscapedSlotText  # noqa: PLC0415

        if isinstance(value, _EscapedSlotText) and "<" not in value:
            return str(unescape(value))
        if getattr_static(value, "__html__", None) is not None:
            html_value = cast("HasHtml", value)
            return PreparedTrustedHtmlValue(str(html_value.__html__()))
        rendered = _render_value(
            value,
            provides=context.provides,
            citry=context.component.citry if context.component is not None else None,
            context=context,
        )
        if isinstance(rendered, CitryRender):
            return wrap_python_composition_result(rendered)
        if isinstance(rendered, PreparedTextValue):
            return rendered
        if not isinstance(rendered, str):
            raise TypeError("prepared expression fallback must render as text or a component")
        return str(unescape(rendered))

    def render(self, context: CitryContext) -> RenderPart:
        value = self.resolve_value(context)
        if not isinstance(value, str):
            return value
        return PreparedTextValue(self.source, self.position, value)


class PreparedElementOpenNode(ElementAttrsNode):
    def __init__(
        self,
        source: str,
        start_span: tuple[int, int],
        tag: str,
        attrs: tuple[Any, ...],
        used_vars: tuple[str, ...],
        is_void: bool,
        is_self_closing: bool,
        element_metadata: tuple[tuple[str, object], ...],
        event_bindings: tuple[Mapping[str, object], ...] = (),
        poll_bindings: tuple[Mapping[str, object], ...] = (),
        control_bindings: tuple[Mapping[str, object], ...] = (),
    ) -> None:
        super().__init__(source, start_span, attrs, used_vars)
        from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

        if any(
            isinstance(attr, StaticHtmlAttr)
            and attr.key.lower() in {"data-citry-runtime-control", "data-citry-runtime-events"}
            for attr in attrs
        ):
            raise ValueError("data-citry-runtime-* is reserved internal metadata")
        self.tag = tag
        # Typed capture has already resolved a static ``c-element`` target.
        # Keep ElementAttrsNode's shared hook/validation view authoritative too,
        # rather than letting it recover the authored ``c-element`` name from
        # the source span.
        self._tag_name = tag
        self.is_void = is_void
        self.is_self_closing = is_self_closing
        self.element_metadata = element_metadata
        self._event_bindings = _normalize_event_bindings(event_bindings)
        self._poll_bindings = _normalize_poll_bindings(poll_bindings)
        self._control_bindings = _normalize_control_bindings(control_bindings)
        self._runtime_control_candidate = False
        self._runtime_events_candidate = False
        source_bytes = source.encode()
        self._static_source_attrs = tuple(
            (
                attr,
                source_bytes[attr.position[0] : attr.position[1]].decode(),
            )
            for attr in attrs
            if isinstance(attr, StaticHtmlAttr)
            and attr.position != start_span
            and not attr.key.startswith(("c-", "@c-", ":c-", "$c-", "#c-"))
        )
        self._authored_vue_attrs = tuple(
            attr for attr in attrs if isinstance(attr, StaticHtmlAttr) and attr.key.startswith(("v-", "@", ":"))
        )
        if any(
            attr.key == "v-citry-event-timing"
            or attr.key.startswith(("v-citry-event-timing.", "v-citry-event-timing:"))
            for attr in self._authored_vue_attrs
        ):
            raise ValueError("v-citry-event-timing is reserved compiler output for timed @c-* bindings")
        if any(
            attr.key == "v-citry-runtime-events"
            or attr.key.startswith(("v-citry-runtime-events.", "v-citry-runtime-events:"))
            for attr in self._authored_vue_attrs
        ):
            raise ValueError("v-citry-runtime-events is reserved compiler output for runtime @c-* bindings")
        if any(_is_reserved_vue_owned_name(attr.key) for attr in self._authored_vue_attrs):
            raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")
        self._static_prepared: PreparedElementOpen | None = None
        if (
            len(self._static_source_attrs) == len(attrs)
            and not element_metadata
            and not self._has_runtime_events_candidate
            and not self._event_bindings
            and not self._poll_bindings
            and not self._control_bindings
        ):
            self._static_prepared = PreparedElementOpen(
                source,
                start_span,
                tag,
                tuple(
                    PreparedAttribute(attr.key, "source", attr.position, source_text)
                    for attr, source_text in self._static_source_attrs
                ),
                is_void,
                is_self_closing,
                (),
                (),
            )
        if any(item and item[0] == "morph" for item in element_metadata):
            raise ValueError("prepared Vue rendering does not yet support #c-ignore or element morph metadata")

    def render(self, context: CitryContext) -> PreparedElementOpen:
        static = self._static_prepared
        if static is not None:
            return static
        resolved, extension_validated = self._resolve_for_output(context)
        return self._prepared_from_resolved(resolved, context=context, extension_validated=extension_validated)

    def _format(
        self,
        resolved: Mapping[str, Any],
        context: CitryContext,
        *,
        validate_keys: bool = True,
    ) -> PreparedElementOpen:
        """Keep the complete typed opening element through attribute extensions."""
        return self._prepared_from_resolved(dict(resolved), context=context, extension_validated=validate_keys)

    def _prepared_from_resolved(
        self,
        resolved: dict[str, Any],
        *,
        context: CitryContext,
        extension_validated: bool,
        owner_name: str | None = None,
    ) -> PreparedElementOpen:
        from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

        del extension_validated  # source preservation is decided from the exact resolved value below
        entries: list[PreparedAttribute] = []
        data_attrs = dict(resolved)
        control_bindings = self._control_bindings
        from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR  # noqa: PLC0415

        runtime_events_value = data_attrs.pop(RUNTIME_EVENTS_ATTR, None)
        runtime_event_bindings: tuple[Mapping[str, object], ...] = ()
        runtime_poll_bindings: tuple[Mapping[str, object], ...] = ()
        if runtime_events_value is not None:
            from citry.ext.events.bindings import _runtime_event_bindings  # noqa: PLC0415

            runtime_specs, runtime_poll_specs = _runtime_event_bindings(runtime_events_value)
            identified = []
            for spec in runtime_specs:
                canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
                identity_source = f"{self.position[0]}:{self.position[1]}:{canonical}"
                identity = hashlib.sha256(identity_source.encode()).hexdigest()[:16]
                identified.append({"id": f"citryRuntimeEvent{identity}", **spec})
            runtime_event_bindings = _normalize_event_bindings(tuple(identified))
            runtime_names = [str(binding["event"]) for binding in runtime_event_bindings]
            if len(runtime_names) != len(set(runtime_names)):
                raise ValueError("one element supports one Events binding per DOM event")
            authored_events = {str(binding["event"]) for binding in self._event_bindings}
            overlap = authored_events & {str(binding["event"]) for binding in runtime_event_bindings}
            if overlap:
                raise ValueError(f"one element supports one Events binding per DOM event: {sorted(overlap)!r}")
            identified_polls = []
            for spec in runtime_poll_specs:
                canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
                identity_source = f"{self.position[0]}:{self.position[1]}:{canonical}"
                identity = hashlib.sha256(identity_source.encode()).hexdigest()[:16]
                identified_polls.append({"id": f"citryRuntimePoll{identity}", **spec})
            runtime_poll_bindings = _normalize_runtime_poll_bindings(tuple(identified_polls))

        runtime_control = data_attrs.pop(RUNTIME_CONTROL_ATTR, None)
        if runtime_control is not None:
            from citry.ext.events.bindings import _runtime_control_bindings  # noqa: PLC0415

            specs = _runtime_control_bindings(runtime_control)
            if len(specs) != 1:
                raise ValueError("one element supports exactly one runtime State control binding")
            if control_bindings:
                raise ValueError("one element supports exactly one :c-* State binding")
            canonical = json.dumps(specs[0], sort_keys=True, separators=(",", ":"))
            identity = hashlib.sha256(f"{self.position[0]}:{self.position[1]}:{canonical}".encode()).hexdigest()[:16]
            control_bindings = _normalize_control_bindings(({"id": f"citryControl{identity}", **specs[0]},))
        private_aliases = [name for name in data_attrs if name.lower() in {RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR}]
        if private_aliases:
            raise TypeError(f"{private_aliases[0]!r} is reserved internal Events metadata")
        reserved = [name for name in data_attrs if name.lower().startswith("data-cev-")]
        if reserved:
            raise RuntimeError(f"{reserved[0]!r} is compiler-owned Events metadata")
        private_vue_owned = [name for name in data_attrs if _is_reserved_vue_owned_name(str(name))]
        if private_vue_owned:
            raise ValueError(f"{VUE_OWNED_NATIVE_DIRECTIVE} is reserved compiler output")
        if control_bindings:
            from citry.ext.events.bindings import _validate_final_control_bindings  # noqa: PLC0415

            _validate_final_control_bindings(
                self.tag,
                data_attrs,
                control_bindings,
                comp_name=owner_name
                or (type(context.component).__name__ if context.component is not None else "template"),
            )
        data_attrs = merge_attrs(data_attrs)
        dynamic_keys = {attr.key.removeprefix("c-") for attr in self.attrs if not isinstance(attr, StaticHtmlAttr)}
        preserved_source: dict[str, PreparedAttribute] = {}
        for attr, source_text in self._static_source_attrs:
            if (
                attr.key not in dynamic_keys
                and attr.key in data_attrs
                and type(data_attrs[attr.key]) is type(attr.value)
                and data_attrs[attr.key] == attr.value
            ):
                preserved_source[attr.key] = PreparedAttribute(
                    attr.key,
                    "source",
                    attr.position,
                    source_text,
                )
        remaining_data_attrs: dict[str, object] = {}
        for name, value in data_attrs.items():
            preserved = preserved_source.get(name)
            if preserved is not None:
                entries.append(preserved)
            else:
                if not include_prepared_attribute(value):
                    continue
                entries.append(PreparedAttribute(name, "data", self._data_attr_span(name), value))
                remaining_data_attrs[name] = value
        if vue_render_active():
            _reject_executable_dynamic_attrs(remaining_data_attrs, tag=self.tag)
        metadata = _resolve_element_metadata(self.element_metadata, context)
        return PreparedElementOpen(
            self.source,
            self.position,
            self.tag,
            tuple(entries),
            self.is_void,
            self.is_self_closing,
            metadata,
            self._event_bindings,
            self._poll_bindings,
            control_bindings,
            (),
            runtime_event_bindings,
            self._runtime_events_candidate,
            runtime_poll_bindings,
            self._has_spread,
        )

    def _data_attr_span(self, name: str) -> tuple[int, int]:
        """Return the authored span responsible for one resolved data attribute."""
        candidates = [
            attr.position for attr in self.attrs if attr.key == "c-bind" or attr.key.removeprefix("c-") == name
        ]
        return min(candidates, default=self.position)

    def _with_attrs(
        self,
        attrs: tuple[Any, ...],
        event_bindings: tuple[Mapping[str, object], ...] = (),
        poll_bindings: tuple[Mapping[str, object], ...] = (),
        control_bindings: tuple[Mapping[str, object], ...] = (),
    ) -> PreparedElementOpenNode:
        rebuilt = type(self)(
            self.source,
            self.position,
            self.tag,
            attrs,
            self.used_vars,
            self.is_void,
            self.is_self_closing,
            self.element_metadata,
            event_bindings,
            poll_bindings,
            control_bindings,
        )
        rebuilt._runtime_control_candidate = self._runtime_control_candidate
        rebuilt._runtime_events_candidate = self._runtime_events_candidate
        return rebuilt

    def _with_element_metadata(self, element_metadata: tuple[tuple[str, object], ...]) -> PreparedElementOpenNode:
        rebuilt = type(self)(
            self.source,
            self.position,
            self.tag,
            self.attrs,
            self.used_vars,
            self.is_void,
            self.is_self_closing,
            element_metadata,
            self._event_bindings,
            self._poll_bindings,
            self._control_bindings,
        )
        rebuilt._runtime_control_candidate = self._runtime_control_candidate
        rebuilt._runtime_events_candidate = self._runtime_events_candidate
        return rebuilt


class PreparedElementCloseNode(Node):
    def __init__(self, source: str, end_span: tuple[int, int], tag: str) -> None:
        self.source = source
        self.position = end_span
        self.tag = tag
        self._prepared = PreparedElementClose(source, end_span, tag)

    def render(self, context: CitryContext) -> PreparedElementClose:  # noqa: ARG002
        return self._prepared


def _reject_executable_dynamic_attrs(attrs: Mapping[str, object], *, tag: str) -> None:
    for name in attrs:
        if name.startswith(("v-", "@", ":")):
            raise ValueError(
                f"Python-resolved attribute {name!r} on <{tag}> cannot introduce Vue syntax; "
                "Vue directives and bindings must be authored statically in the template."
            )


_EVENT_BINDING_KEYS = frozenset(
    {"id", "event", "handler", "args", "prevent", "stop", "self", "once", "key", "debounce", "throttle"}
)


def _normalize_event_bindings(
    bindings: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    normalized: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for value in bindings:
        if type(value) is not dict or set(value) != _EVENT_BINDING_KEYS:
            raise TypeError("prepared event binding must have the exact trusted Events fields")
        binding_id = value["id"]
        event = value["event"]
        handler = value["handler"]
        if (
            type(binding_id) is not str
            or re.fullmatch(r"(?:citryEvent|citryRuntimeEvent)[0-9a-f]+", binding_id) is None
            or type(event) is not str
            or not event
            or type(handler) is not str
            or not handler
        ):
            raise TypeError("prepared event binding has invalid identity, event, or handler")
        args = value["args"]
        if args is not None and type(args) is not str:
            raise TypeError("prepared event binding args must be trusted authored source or null")
        for name in ("prevent", "stop", "self", "once"):
            if type(value[name]) is not bool:
                raise TypeError(f"prepared event binding {name} must be boolean")
        if value["key"] is not None and type(value["key"]) is not str:
            raise TypeError("prepared event binding key must be a string or null")
        for name in ("debounce", "throttle"):
            timing = value[name]
            if timing is not None and (type(timing) is not int or not 0 <= timing <= 2**53 - 1):
                raise TypeError(
                    f"prepared event binding {name} must be a nonnegative JavaScript-safe exact integer or null"
                )
        if binding_id in seen:
            raise ValueError("prepared event binding id is duplicated")
        seen.add(binding_id)
        normalized.append(MappingProxyType(dict(value)))
    return tuple(normalized)


_POLL_BINDING_KEYS = frozenset({"id", "handler", "args", "interval"})


def _normalize_poll_bindings(
    bindings: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    normalized: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for value in bindings:
        if type(value) is not dict or set(value) != _POLL_BINDING_KEYS:
            raise TypeError("prepared poll binding must have the exact trusted Events fields")
        binding_id = value["id"]
        if type(binding_id) is not str or re.fullmatch(r"citryPoll[0-9a-f]+", binding_id) is None:
            raise TypeError("prepared poll binding has invalid identity")
        if type(value["handler"]) is not str or not value["handler"]:
            raise TypeError("prepared poll binding handler must be non-empty")
        if value["args"] is not None and type(value["args"]) is not str:
            raise TypeError("prepared poll binding args must be trusted authored source or null")
        if type(value["interval"]) is not int or not 0 < value["interval"] <= 2**53 - 1:
            raise TypeError("prepared poll binding interval must be a positive JavaScript-safe exact integer")
        if binding_id in seen:
            raise ValueError("prepared poll binding id is duplicated")
        seen.add(binding_id)
        normalized.append(MappingProxyType(dict(value)))
    return tuple(normalized)


def _normalize_runtime_poll_bindings(
    bindings: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    normalized: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for value in bindings:
        if type(value) is not dict or set(value) != _POLL_BINDING_KEYS:
            raise TypeError("prepared runtime poll binding must have the exact trusted Events fields")
        binding_id = value["id"]
        if type(binding_id) is not str or re.fullmatch(r"citryRuntimePoll[0-9a-f]+", binding_id) is None:
            raise TypeError("prepared runtime poll binding has invalid identity")
        if type(value["handler"]) is not str or not value["handler"]:
            raise TypeError("prepared runtime poll binding handler must be non-empty")
        if value["args"] is not None:
            raise TypeError("prepared runtime poll binding args must be null")
        if type(value["interval"]) is not int or not 0 < value["interval"] <= 2**53 - 1:
            raise TypeError("prepared runtime poll binding interval must be a positive JavaScript-safe exact integer")
        if binding_id in seen:
            raise ValueError("prepared runtime poll binding id is duplicated")
        seen.add(binding_id)
        normalized.append(MappingProxyType(dict(value)))
    return tuple(normalized)


_CONTROL_BINDING_KEYS = frozenset(
    {"id", "field", "binding_mode", "handler", "lazy", "on", "key", "debounce", "throttle"}
)


def _normalize_control_bindings(
    bindings: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    normalized: list[Mapping[str, object]] = []
    seen: set[str] = set()
    for value in bindings:
        if type(value) is not dict or set(value) != _CONTROL_BINDING_KEYS:
            raise TypeError("prepared control binding must have the exact trusted Events fields")
        binding_id = value["id"]
        mode = value["binding_mode"]
        if type(binding_id) is not str or re.fullmatch(r"citryControl[0-9a-f]+", binding_id) is None:
            raise TypeError("prepared control binding has invalid identity")
        if type(value["field"]) is not str or not value["field"] or mode not in {"one-way", "two-way"}:
            raise TypeError("prepared control binding has invalid field or mode")
        if (mode == "one-way") != (value["handler"] is None):
            raise TypeError("prepared control binding handler disagrees with mode")
        if value["handler"] is not None and (type(value["handler"]) is not str or not value["handler"]):
            raise TypeError("prepared control binding handler must be non-empty or null")
        if type(value["lazy"]) is not bool:
            raise TypeError("prepared control binding lazy must be boolean")
        for name in ("on", "key"):
            if value[name] is not None and (type(value[name]) is not str or not value[name]):
                raise TypeError(f"prepared control binding {name} must be non-empty or null")
        for name in ("debounce", "throttle"):
            timing = value[name]
            if timing is not None and (type(timing) is not int or not 0 <= timing <= 2**53 - 1):
                raise TypeError(
                    f"prepared control binding {name} must be a nonnegative JavaScript-safe exact integer or null"
                )
        if binding_id in seen:
            raise ValueError("prepared control binding id is duplicated")
        seen.add(binding_id)
        normalized.append(MappingProxyType(dict(value)))
    return tuple(normalized)


def _resolve_element_metadata(
    metadata: tuple[tuple[str, object], ...], context: CitryContext
) -> tuple[tuple[str, object], ...]:
    resolved: list[tuple[str, object]] = []
    for item in metadata:
        kind, value = item
        if kind != "key":
            raise ValueError(f"unsupported prepared element metadata: {kind!r}")
        if isinstance(value, PreparedConstantElementKey):
            key = value.value
        elif isinstance(value, ExprHtmlAttr):
            key = const_value(value.resolve(context))
        else:
            raise TypeError("prepared element key metadata has an unsupported value")
        resolved.append(("key", None if key is None else str(key)))
    return tuple(resolved)


def _validate_prepared_render(render: CitryRender) -> None:
    from citry._vue.leaf_program import PreparedLeafProgram  # noqa: PLC0415
    from citry.citry_render import DeferredComponent, Placeholder  # noqa: PLC0415

    pending = [render]
    seen: set[int] = set()
    leaf_types = (
        PreparedSourceText,
        PreparedVerbatimHtml,
        PreparedStaticRun,
        PreparedTextValue,
        PreparedTrustedHtmlValue,
        PreparedElementOpen,
        PreparedElementClose,
        PreparedDynamicElementOpen,
        PreparedDynamicElementClose,
        PreparedLeafProgram,
    )
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if current.render_target != "prepared":
            raise TypeError("prepared Vue rendering cannot embed an ordinary HTML render")
        for part in current.parts:
            if isinstance(part, CitryRender):
                pending.append(part)
            elif type(part) is str and part == "":
                # ``on_render()`` uses an empty string as the public way to
                # suppress a component's output.  Direct assembly already
                # treats this exact marker as zero output; keep validation in
                # step with that consumer while continuing to reject all
                # non-empty raw strings.
                continue
            elif isinstance(part, leaf_types):
                continue
            elif isinstance(part, Placeholder) and part.key in {"deps:css", "deps:js"}:
                # Dependency insertion points are consumed by the ordinary
                # serializer.  Direct event rendering deliberately omits
                # them from the prepared view and publishes the dependency
                # manifest separately, so they are resolved placeholders from
                # the event renderer's perspective rather than unresolved
                # runtime output.
                continue
            elif isinstance(part, (DeferredComponent, Placeholder)):
                raise TypeError("prepared Vue rendering contains an unresolved runtime part")
            else:
                raise TypeError(f"prepared Vue rendering received unsupported raw output: {type(part).__name__}")


def coalesce_prepared_static_nodes(nodes: list[BodyItem]) -> list[BodyItem]:
    """Merge adjacent immutable authored nodes after template extension transforms."""
    # Physical document boundaries remain typed nodes so the serializer and
    # Vue assembler can select shell and logical-body contributions before
    # visiting excluded head subtrees.
    if any(
        (isinstance(node, PreparedSourceTextNode) and node.text.lstrip().lower().startswith("<!doctype"))
        or (
            isinstance(node, PreparedStaticRunNode)
            and any(marker in node._prepared.html.lower() for marker in ("<!doctype", "<html", "<head", "<body"))
        )
        or (isinstance(node, PreparedElementOpenNode) and node.tag.lower() in {"html", "head", "body"})
        for node in nodes
    ):
        return nodes
    output: list[BodyItem] = []
    pending: list[str] = []
    pending_openings: list[StaticRunOpening] = []
    pending_depth = 0
    pending_length = 0
    pending_tag_transitions: list[tuple[str, str]] = []

    def append_pending(text: str) -> None:
        nonlocal pending_length
        pending.append(text)
        pending_length += len(text)

    def flush() -> None:
        nonlocal pending_depth, pending_length
        if pending:
            output.append(
                PreparedStaticRunNode(
                    "".join(pending),
                    StaticRunStructure(tuple(pending_openings), pending_depth, tuple(pending_tag_transitions)),
                )
            )
            pending.clear()
            pending_openings.clear()
            pending_tag_transitions.clear()
            pending_depth = 0
            pending_length = 0

    index = 0
    while index < len(nodes):
        node = nodes[index]
        if isinstance(node, PreparedSourceTextNode):
            append_pending(node.text)
            index += 1
            continue
        if isinstance(node, PreparedStaticRunNode):
            prepared_run = node._prepared
            if prepared_run.root_structure is None:
                flush()
                output.append(node)
                index += 1
                continue
            pending_openings.extend(
                StaticRunOpening(
                    pending_length + opening.start_at,
                    pending_length + opening.insert_at,
                    pending_length + opening.end_at,
                    pending_depth + opening.relative_depth,
                    opening.attr_identities,
                )
                for opening in prepared_run.root_structure.openings
            )
            pending_tag_transitions.extend(prepared_run.root_structure.tag_transitions)
            append_pending(prepared_run.html)
            pending_depth += prepared_run.root_structure.final_depth_delta
            index += 1
            continue
        if isinstance(node, PreparedElementCloseNode):
            if (
                node.position[0] == node.position[1]
                and output
                and isinstance(output[-1], PreparedElementOpenNode)
                and output[-1].is_self_closing
                and not output[-1].is_void
                and output[-1].tag == node.tag
            ):
                flush()
                output.append(node)
                index += 1
                continue
            append_pending(f"</{node.tag}>")
            pending_depth -= 1
            pending_tag_transitions.append(("close", node.tag.lower()))
            index += 1
            continue
        if (
            isinstance(node, PreparedElementOpenNode)
            and node._static_prepared is not None
            # Authored Vue syntax is itself a browser-runtime requirement.
            # Keep that element typed so requirement detection can see it.
            and not node._authored_vue_attrs
        ):
            prepared = node._static_prepared
            attrs = "" if not prepared.authored_attrs else " " + " ".join(prepared.authored_attrs)
            ending = "/>" if prepared.is_void and prepared.is_self_closing else ">"
            opening = f"<{prepared.tag}{attrs}{ending}"
            insert_at = pending_length + len(opening) - (2 if ending == "/>" else 1)
            pending_openings.append(
                StaticRunOpening(
                    pending_length,
                    insert_at,
                    pending_length + len(opening),
                    pending_depth,
                    frozenset(_html_attr_identity(attr.name) for attr in prepared.attrs),
                )
            )
            append_pending(opening)
            if not prepared.is_void:
                pending_tag_transitions.append(("open", prepared.tag.lower()))
            index += 1
            # The parser emits a zero-width close descriptor for a non-void
            # authored self-closing element. Normalize the pair to explicit
            # markup so HTML and foreign-content parsers both keep siblings
            # outside the empty element.
            next_node = nodes[index] if index < len(nodes) else None
            if (
                prepared.is_self_closing
                and not prepared.is_void
                and isinstance(next_node, PreparedElementCloseNode)
                and next_node.tag == prepared.tag
                and next_node.position[0] == next_node.position[1]
            ):
                append_pending(f"</{prepared.tag}>")
                pending_tag_transitions.append(("close", prepared.tag.lower()))
                index += 1
            elif not prepared.is_void:
                pending_depth += 1
            continue
        flush()
        output.append(node)
        index += 1
    flush()
    return output
