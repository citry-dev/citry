"""
Runtime node classes for the Citry template compiler output.

The V3 compiler generates Python source code that instantiates these classes.
Each class accepts the exact arguments the compiler emits and stores them as
attributes.

The value node ``ExprNode`` renders against a ``CitryContext`` (see
docs/design/component_rendering.md), and the attribute nodes
(``StaticHtmlAttr``, ``ExprHtmlAttr``, ``TemplateHtmlAttr``) ``resolve`` to
their values. ``ComponentNode`` renders a child component across a context
boundary: attributes become the child's kwargs, and its body content becomes
the child's slots (the implicit default slot, or the collected ``<c-fill>``
tags; see docs/design/component_slots.md section 4). The control-flow nodes (``IfNode``,
``ForNode``) render their matching branch / per-item body. ``SlotNode``
renders the fill given for the slot, or its own body as the fallback (see
docs/design/component_slots.md section 5). ``FillNode`` is consumed during fill
collection and is never rendered directly, so its inherited ``render``
raising is intentional.

See the compiler module docstring in
``crates/citry_template_parser/src/compiler.rs`` for the full node taxonomy
and constructor signatures.

Example:
    Parse a template, compile it, and exec the result::

        from citry_core.template_parser import parse_template, compile_template
        from citry.nodes import (
            ExprNode, ElementAttrsNode, ElementKeyNode, ComponentNode,
            IfNode, ForNode, SlotNode, FillNode, StaticHtmlAttr,
            ExprHtmlAttr, TemplateHtmlAttr,
        )

        source = '<c-Card title="Hi">{{ body }}</c-Card>'
        t = parse_template(source)
        code = compile_template(t)

        ns = {
            "source": source,
            "ExprNode": ExprNode,
            "ElementKeyNode": ElementKeyNode,
            "ComponentNode": ComponentNode,
            "ElementAttrsNode": ElementAttrsNode,
            "IfNode": IfNode,
            "ForNode": ForNode,
            "SlotNode": SlotNode,
            "FillNode": FillNode,
            "StaticHtmlAttr": StaticHtmlAttr,
            "ExprHtmlAttr": ExprHtmlAttr,
            "TemplateHtmlAttr": TemplateHtmlAttr,
        }
        exec(code, ns)
        body = ns["generate_template"]()

        # body[0] is a ComponentNode with name="card"
        print(body[0].name)       # "card"
        print(body[0].attrs[0])   # StaticHtmlAttr(key='title', value='Hi')

"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import get_close_matches
from enum import Enum
from keyword import iskeyword
from threading import RLock
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, TypeAlias, cast, final
from unicodedata import normalize
from weakref import ReferenceType, ref

from typing_extensions import Unpack, override

from citry._i18n_directives import looks_like_i18n_binding
from citry._vue import native_render as _native_render
from citry._vue import native_walk as _native_walk
from citry.attrs import (
    TEMPLATE_EMPTY_VALUE,
    _format_resolved_attrs_to_str,
    _has_default_attr_formatting,
    _merge_resolved_attrs,
    format_attrs,
    is_vue_code_attr_name,
    is_vue_directive_name,
    merge_attrs,
    reject_vue_code_attr_name,
    template_attr_value,
    validate_html_attr_name,
    vue_code_error,
)
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement, _ElementMorphMetadata, _PreparedCallMetadata
from citry.citry_render import (
    _VALUE_CONTEXT,
    CitryRender,
    DeferredComponent,
    _DeferredRun,
    _DeferredRunRow,
    _render_slot_value,
    _render_value,
)
from citry.client_directives import (
    CLIENT_PROPS_ATTR,
    ComponentTagClientBinding,
    ComponentTagClientBindingKind,
    ComponentTagClientBindingSource,
    RuntimeComponentEventBinding,
    apply_client_props_contribution,
    authenticated_runtime_component_event_binding,
    classify_component_tag_client_binding_key,
    has_client_props_key,
    is_client_props_key,
    resolve_component_tag_client_binding_value,
    unsupported_component_tag_directive_hint,
    unsupported_slot_tag_directive_message,
)
from citry.constness import (
    Const,
    _const_mapping,
    _ConstMapping,
    _ConstProxy,
    _mapping_value_is_const,
    _overlay_const_mapping,
    const_value,
)
from citry.slots import Slot, SlotData, normalize_slot_fills
from citry.util.exception import add_slot_to_error_message
from citry.util.html import escape
from citry.util.logger import is_tracing, trace_component_msg, trace_node_msg
from citry_core.safe_eval import compile_expr

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from citry._vue.direct import DirectExecutionFrame
    from citry.citry_render import RenderPart
    from citry.citry_template import CitryTemplate
    from citry.component import Component
    from citry.extension import ForeignClaim


_EVENTS_COMPILER_ATTR_PREFIX = "data-cev-"


def _reject_reserved_events_attr(name: str, *, tag_name: str) -> None:
    """Keep authored and render-time attributes out of the Events-reserved namespace."""
    folded = name.lower()
    if folded.startswith(_EVENTS_COMPILER_ATTR_PREFIX) or folded in {
        "data-citry-runtime-control",
        "data-citry-runtime-events",
    }:
        namespace = "'data-cev-*'" if folded.startswith(_EVENTS_COMPILER_ATTR_PREFIX) else repr(name)
        msg = (
            f"{name!r} on <{tag_name}> is in the {namespace} reserved internal Events namespace; "
            "author State bindings with ':c-*' "
            "and event bindings with '@c-*' instead."
        )
        raise RuntimeError(msg)


def _reject_dynamic_translation_binding(name: Any, *, tag_name: str) -> None:
    """Keep `$c-tr` on literal final plain HTML elements after spreads resolve."""
    if isinstance(name, str) and name.lower().startswith("$c-tr:"):
        raise RuntimeError(
            f"{name!r} resolved on <{tag_name}>, but $c-tr is valid only on a literal final plain HTML element."
        )


# NOTE: Not abstract on purpose: the compiler builds the whole node tree up front
# (including nodes inside branches that may never render), so a
# not-yet-implemented node must still be instantiable. The default ``render``
# therefore raises ``NotImplementedError`` only when the node is actually
# rendered, not when it is constructed.
class Node:
    """
    Base class for the runtime nodes the template compiler output instantiates.

    A node renders to a body part (a ``str`` or a nested ``CitryRender``) against
    the render-scoped ``CitryContext``. Concrete nodes override ``render``.

    A node sitting in a *fill group* (a component body that contains
    ``<c-fill>`` tags) takes part in fill collection through
    ``Node.collect_fills()`` instead of ``Node.render()``. The default says
    the node is not allowed there; nodes that are (``FillNode``, the control-flow nodes)
    override it.
    """

    def render(self, context: CitryContext) -> RenderPart:
        raise NotImplementedError(f"{type(self).__name__}.render is not implemented")

    # `context` is unused here (the base only raises) but is the documented
    # signature for overriding nodes, hence the noqa.
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:  # noqa: ARG002
        """
        Register this node's fills into ``sink``.

        Called instead of ``render`` when the node sits in a fill group. The
        base implementation rejects the node: when a component body contains
        ``<c-fill>`` tags, all other content must be inside the fills. A node
        kind that may sit beside fills (for example one injected by an
        extension via ``on_template_compiled``) overrides this to register its
        fills with ``sink.add(...)``, recursing into its own bodies with
        ``collect_fills_from_body``.
        """
        msg = (
            f"Tag ({type(self).__name__}) cannot appear next to '<c-fill>' tags in the body of "
            f"<c-{sink.component_name}>. All other content must be inside the fills."
        )
        raise RuntimeError(msg)


# One item in a compiled template body: a runtime Node or a static text run.
BodyItem: TypeAlias = "Node | str"


@final
class ForeignNode(Node):
    """Fail-closed source contribution owned by an installed host provider."""

    def __init__(
        self,
        source: str,
        position: tuple[int, int],
        provider: str,
        ordinal: int,
        text: str,
        may_control_body: bool = False,
    ) -> None:
        self.source = source
        self.position = position
        self.provider = provider
        self.ordinal = ordinal
        self.text = text
        self.may_control_body = may_control_body

    def claim(self, locus: Literal["body", "component_input"]) -> ForeignClaim:
        from citry.extension import ForeignClaim  # noqa: PLC0415

        return ForeignClaim(
            provider=self.provider,
            ordinal=self.ordinal,
            source=self.text,
            position=self.position,
            may_control_body=self.may_control_body,
            locus=locus,
        )

    @override
    def render(self, context: CitryContext) -> RenderPart:
        msg = f"Unresolved foreign source claim {(self.provider, self.ordinal)!r} reached rendering."
        raise RuntimeError(msg)

    @override
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:
        msg = f"Unresolved foreign source claim {(self.provider, self.ordinal)!r} reached fill collection."
        raise RuntimeError(msg)


class HtmlAttr:
    """
    Base class for HTML attribute nodes (a component's or slot's inputs).

    An attribute resolves to a value (which becomes a component kwarg), not to a
    rendered body part. Concrete attributes override ``resolve``.
    """

    # Set by every concrete attribute's __init__; declared here so code iterating
    # a ``tuple[HtmlAttr, ...]`` can read the shared source metadata.
    key: str
    source: Any
    position: tuple[int, int]

    def resolve(self, context: CitryContext) -> Any:
        raise NotImplementedError(f"{type(self).__name__}.resolve is not implemented")


@final
class ForeignHtmlAttr(HtmlAttr):
    """Fail-closed component input assembled from literal and foreign parts."""

    def __init__(
        self,
        source: str,
        position: tuple[int, int],
        key: str,
        parts: tuple[str | ForeignNode, ...],
        used_vars: tuple[str, ...],
    ) -> None:
        self.source = source
        self.position = position
        self.key = key
        self.parts = parts
        self.used_vars = used_vars

    def foreign_nodes(self) -> tuple[ForeignNode, ...]:
        return tuple(part for part in self.parts if isinstance(part, ForeignNode))

    @override
    def resolve(self, context: CitryContext) -> Any:
        claims = [(part.provider, part.ordinal) for part in self.foreign_nodes()]
        raise RuntimeError(f"Unresolved foreign component input claims reached rendering: {claims!r}.")


class LogicalFillKind(str, Enum):
    IMPLICIT = "implicit"
    NAMED = "named"
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class FillDataBinding:
    """Compiled one-level destructuring plan for a fill's slot data."""

    fields: tuple[tuple[str, str], ...]
    rest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            tuple((source, normalize("NFKC", target)) for source, target in self.fields),
        )
        object.__setattr__(self, "rest", normalize("NFKC", self.rest))

    @property
    def targets(self) -> tuple[str, ...]:
        field_targets = tuple(target for _, target in self.fields)
        return (*field_targets, self.rest) if self.rest else field_targets


def _find_attr(attrs: tuple[HtmlAttr, ...], key: str) -> HtmlAttr | None:
    """Return the first attribute with the given key, or ``None``."""
    for attr in attrs:
        if attr.key == key:
            return attr
    return None


def _validate_introduced_variables(
    tag_name: str,
    names: tuple[str, ...],
    context: CitryContext,
) -> None:
    """Reject a Citry binding that would reuse a name already in scope."""
    introduced: set[str] = set()
    for name in names:
        if name in introduced:
            msg = (
                f"Cannot define variable {name!r} more than once in tag '<{tag_name}>'. "
                "Variable shadowing is not allowed, use a different name."
            )
            raise RuntimeError(msg)
        introduced.add(name)
        if name in context.variables:
            msg = (
                f"Cannot define variable {name!r} in tag '<{tag_name}>' - variable name is already taken. "
                "Variable shadowing is not allowed, use a different name."
            )
            raise RuntimeError(msg)


class FillSink:
    """
    Where ``collect_fills`` registers the fills of one component tag.

    Created by ``ComponentNode`` when it collects its body's fills, and passed
    down through ``Node.collect_fills``. Carries the name of the component
    receiving the fills (for error messages and slot metadata) and enforces
    that each materialized slot name appears only once.
    """

    __slots__ = ("component_name", "fills")

    def __init__(self, component_name: str) -> None:
        self.component_name = component_name
        self.fills: dict[str, Slot] = {}

    def add(self, name: str, slot: Slot) -> None:
        """Register one fill. Raises if the slot name is already taken."""
        if name in self.fills:
            msg = f"Multiple fills target the same slot name {name!r} in the body of <c-{self.component_name}>."
            raise RuntimeError(msg)
        self.fills[name] = slot


def collect_fills_from_body(body: Sequence[BodyItem], context: CitryContext, sink: FillSink) -> None:
    """
    Walk one level of a fill-group body, collecting fills into ``sink``.

    Whitespace strings between fills are formatting only: neither captured
    into a slot nor rendered. Non-whitespace text is rejected (when a
    component body contains ``<c-fill>`` tags, all other content must be
    inside the fills). Each node dispatches through its own
    ``collect_fills``, so what a node contributes (a fill or an error) is the
    node's own business, except for the two control-flow nodes below.

    The parser already rejects most content beside fills; the checks on this
    path are the runtime half of that contract (dynamic fill names make some
    shapes undecidable statically), so the errors mirror the parser's.

    A ``<c-if>`` or ``<c-for>`` contributes the fills of its bodies. Those
    bodies are walked here, on this function's own stack, rather than through
    the node's ``collect_fills``, so Python's call depth does not grow with how
    deeply they nest. A loop's next iteration is read only once the previous
    body is finished, as ``ForNode.collect_fills`` reads them.
    """
    # Each entry is either one body still being walked, with its context, or
    # a `<c-for>` whose remaining iterations are read one at a time.
    stack: list[tuple[Iterator[BodyItem], CitryContext] | Iterator[tuple[list[BodyItem], CitryContext]]] = [
        (iter(body), context)
    ]
    try:
        while stack:
            entry = stack[-1]
            if type(entry) is not tuple:
                loop = cast("Iterator[tuple[list[BodyItem], CitryContext]]", entry)
                following = next(loop, None)
                if following is None:
                    stack.pop()
                else:
                    stack.append((iter(following[0]), following[1]))
                continue
            items, items_context = cast("tuple[Iterator[BodyItem], CitryContext]", entry)
            for item in items:
                if isinstance(item, str):
                    if item.strip():
                        msg = (
                            f"Text cannot appear next to '<c-fill>' tags in the body of "
                            f"<c-{sink.component_name}>. All other content must be inside the fills."
                        )
                        raise RuntimeError(msg)
                    continue
                item_type = type(item)
                if item_type is IfNode:
                    branch = cast("IfNode", item).active_branch_body(items_context)
                    if branch is not None:
                        stack.append((iter(branch), items_context))
                        break
                elif item_type is ForNode:
                    stack.append(cast("ForNode", item).iter_bodies(items_context))
                    break
                else:
                    item.collect_fills(items_context, sink)
            else:
                stack.pop()
    except BaseException:
        # Close each loop still open, innermost first, so its `finally`
        # blocks run before the error leaves this function.
        for entry in reversed(stack):
            close = getattr(entry, "close", None)
            if close is not None:
                close()
        raise


class _TemplateSlotContent:
    """One template fill callable that does not strongly point back to its Slot."""

    __slots__ = (
        "_body",
        "_component_name",
        "_context",
        "_data_binding",
        "_fallback_var",
        "_slot_name",
        "_slot_ref",
    )

    def __init__(
        self,
        body: list[BodyItem],
        context: CitryContext,
        component_name: str,
        slot_name: str,
        data_binding: str | FillDataBinding | None,
        fallback_var: str | None,
    ) -> None:
        self._body = body
        self._context = context
        self._component_name = component_name
        self._slot_name = slot_name
        self._data_binding = data_binding
        self._fallback_var = fallback_var
        self._slot_ref: ReferenceType[Slot] | None = None

    def bind_slot(self, slot: Slot) -> None:
        """Bind the finished Slot through a weak identity reference."""
        self._slot_ref = ref(slot)

    def __call__(self, ctx: Any) -> CitryRender:
        slot_ref = self._slot_ref
        slot = slot_ref() if slot_ref is not None else None
        if slot is None:
            raise RuntimeError("A template Slot content callable lost its owning Slot.")

        def render_content() -> CitryRender:
            return self._render(ctx)

        return render_content()

    def _render(self, ctx: Any) -> CitryRender:
        # Imported lazily: component_render imports the node classes, so
        # importing the body walker at module load would be circular.
        from citry.component_render import _render_body  # noqa: PLC0415

        context = self._context
        provides = context.provides
        if ctx.provides is not None and ctx.provides is not provides:
            provides = {**provides, **ctx.provides} if provides else ctx.provides

        if self._data_binding is not None or self._fallback_var is not None or provides is not context.provides:
            overlay = _bind_fill_data(
                self._data_binding,
                ctx.data,
                component_name=self._component_name,
                slot_name=self._slot_name,
            )
            if self._fallback_var is not None:
                overlay[self._fallback_var] = ctx.fallback
            render_context = CitryContext(
                variables=_overlay_const_mapping(context.variables, overlay),
                extra=context.extra,
                component=context.component,
                provides=provides,
                sandboxed=context.sandboxed,
                template_record=context.template_record,
                _simple_scope=context._simple_scope,
            )
        else:
            render_context = context
        return CitryRender(parts=_render_body(self._body, render_context), context=render_context)


def _make_body_slot(
    body: list[BodyItem],
    context: CitryContext,
    component_name: str,
    slot_name: str,
    data_binding: str | FillDataBinding | None,
    fallback_var: str | None,
    position: tuple[int, int] | None,
    *,
    source: object,
    kind: LogicalFillKind,
    fallback_slot_site_location_id: Any = None,  # noqa: ARG001
) -> Slot:
    """
    Wrap a fill body (or a component's implicit default body) as a ``Slot``.

    The Slot closes over ``context``, the scope where the fill was written,
    so the body renders against the writer's variables no matter when or
    how often the child invokes it. When the child passes slot data or the
    fallback handle, they are overlaid under the fill's whole-data variable,
    destructured field variables, and ``fallback`` variable. The overlay
    context shares the captured ``extra`` bag, so dependencies collected while
    the fill renders reach the fill's lexical owner.

    Provide/inject entries are the one part of the scope that does NOT come
    from the capture alone: when the body renders at a ``<c-slot>`` site, the
    provides active at that site extend (and on a key collision win over) the
    captured ones, so a component inside the body can inject what the slot's
    owner provides around the slot. Invoked standalone (no slot site), the
    body keeps the captured provides. See docs/design/component_provide.md section 4.3.
    """
    content_func = _TemplateSlotContent(body, context, component_name, slot_name, data_binding, fallback_var)
    slot = Slot(
        _public_slot_contents(body),
        content_func=content_func,
        component_name=component_name,
        slot_name=slot_name,
        source_position=position,
    )
    content_func.bind_slot(slot)
    if position is not None and context.component is not None:
        from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

        if not direct_prepared_render_active():
            return slot
        from citry._vue.direct import bind_template_fill  # noqa: PLC0415

        bind_template_fill(
            slot,
            lexical_render_id=context.component.id,
            kind=kind.value,
            public_name=slot_name,
            source=source,
            span=position,
            origin=context.template_record.origin if context.template_record is not None else None,
        )
    return slot


def _public_slot_contents(body: list[BodyItem]) -> list[BodyItem]:
    """Expose authored text while retaining every non-text runtime body object."""
    # Imported locally because capture imports this node module while defining
    # the prepared subclasses.
    from citry._vue.capture import PreparedSourceTextNode  # noqa: PLC0415

    converted: list[BodyItem] | None = None
    for index, item in enumerate(body):
        if type(item) is not PreparedSourceTextNode:
            if converted is not None:
                converted.append(item)
            continue
        if converted is None:
            converted = body[:index]
        converted.append(item.text)
    return body if converted is None else converted


def _body_is_whitespace_only(body: list[BodyItem]) -> bool:
    """Return whether a component body contains only authored whitespace text."""
    # Imported locally because capture imports this node module while defining
    # the prepared subclasses.
    from citry._vue.capture import PreparedSourceTextNode  # noqa: PLC0415

    return all(
        (isinstance(item, str) and not item.strip())
        or (type(item) is PreparedSourceTextNode and not item.text.strip())
        for item in body
    )


def _missing_required_slot_message(component: Any, name: str) -> str:
    """Build the required-slot diagnostic, including a nearby supplied fill name."""
    close = get_close_matches(name, sorted(component.raw_slots), n=1, cutoff=0.7)
    hint = f" Did you mean {close[0]!r}?" if close else ""
    return (
        f"Slot {name!r} of component {type(component).__name__!r} is marked as required, "
        f"but no fill was provided.{hint}"
    )


def _bind_fill_data(
    binding: str | FillDataBinding | None,
    data: SlotData,
    *,
    component_name: str,
    slot_name: str,
) -> dict[str, Any]:
    if binding is None:
        return {}
    if isinstance(binding, str):
        return {binding: data}

    overlay: dict[str, Any] = {}
    consumed: set[str] = set()
    for source, target in binding.fields:
        try:
            overlay[target] = data[source]
        except KeyError:
            available = ", ".join(repr(key) for key in data) or "none"
            msg = (
                f"Fill for slot {slot_name!r} of component {component_name!r} requested "
                f"slot-data field {source!r}, but the available fields are: {available}."
            )
            raise RuntimeError(msg) from None
        consumed.add(source)
    if binding.rest:
        overlay[binding.rest] = SlotData({key: value for key, value in data.items() if key not in consumed})
    return overlay


def _render_part_ids(part: RenderPart) -> set[str]:
    """Collect component render IDs reachable through one selected part."""
    if not isinstance(part, CitryRender):
        return set()
    render_ids: set[str] = set()
    pending = [part]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        render_id = current.frame.render_id
        if render_id is not None:
            render_ids.add(render_id)
        for child in current.parts:
            nested_child = child
            if isinstance(nested_child, CitryRender):
                pending.append(nested_child)
    return render_ids


def _render_part_object_ids(part: RenderPart) -> set[int]:
    """Collect transient part identities reachable through one part."""
    if not isinstance(part, CitryRender):
        return {id(part)}
    object_ids: set[int] = set()
    pending: list[RenderPart] = [part]
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in object_ids:
            continue
        object_ids.add(object_id)
        if isinstance(current, CitryRender):
            pending.extend(current.parts)
    return object_ids


class ExprNode(Node):
    """
    A ``{{ expr }}`` expression node.

    Generated as: ``ExprNode(source, (start, end), "expr", ("var1", ...))``

    Example:
        Template ``{{ name }}`` compiles to::

            ExprNode(source, (0, 10,), "name ", ("name",))

    """

    def __init__(self, source: Any, position: tuple[int, int], expr: str, used_vars: tuple[str, ...]) -> None:
        self.source = source
        self.position = position
        self.expr = expr
        self.used_vars = used_vars
        # The safe-eval function for `expr`, compiled lazily on first render and
        # reused afterwards (the node is cached across renders, so this compiles
        # once). Compiling lazily avoids paying for nodes that are never
        # rendered, e.g. an expression in an `<c-if>` branch that is never taken.
        self._eval: Callable[[Any], Any] | None = None

    def evaluate(self, variables: Mapping[str, Any], *, sandboxed: bool = True) -> Any:
        """
        Evaluate the expression against ``variables`` and return the raw value.

        The compiled evaluator is built on first use and reused (the node is
        cached across renders, so the expression compiles once). ``sandboxed``
        chooses the security sandbox or plain evaluation; it is read only on the
        first call, when the evaluator is compiled, and ignored afterwards (the
        instance's setting is fixed, so every call passes the same value).
        Called by ``render``, and by the ``Const`` optimization, which
        evaluates an expression ahead of time when all of its variables are
        marked constant.
        """
        if self._eval is None:
            self._eval = compile_expr(self.expr, sandboxed=sandboxed)
        plain_variables = variables if isinstance(variables, _ConstMapping) else _const_mapping(variables)
        return self._eval(plain_variables)

    @override
    def render(self, context: CitryContext) -> RenderPart:
        value = self.evaluate(context.variables, sandboxed=context.sandboxed)
        # An element or Slot found in the expression renders with the
        # provide/inject entries active here, so it can inject what this
        # render site provides (docs/design/component_provide.md section 4.4).
        return _render_value(
            value,
            provides=context.provides,
            citry=context.component.citry if context.component is not None else None,
            context=context,
        )

    @override
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:
        # Same rule as the base, with a friendlier name for what the user wrote.
        msg = (
            f"Expression cannot appear next to '<c-fill>' tags in the body of "
            f"<c-{sink.component_name}>. All other content must be inside the fills."
        )
        raise RuntimeError(msg)

    def __repr__(self) -> str:
        return f"ExprNode(position={self.position}, expr={self.expr!r}, used_vars={self.used_vars})"


@final
class StaticHtmlAttr(HtmlAttr):
    """
    A static HTML attribute (``key="value"``).

    Generated as: ``StaticHtmlAttr(source, (start, end), "key", "value", ())``

    Example:
        Template ``<c-Card title="Hello" />`` produces::

            StaticHtmlAttr(source, (8, 21,), "title", "Hello", ())

    """

    def __init__(
        self, source: Any, position: tuple[int, int], key: str, value: Any, used_vars: tuple[str, ...]
    ) -> None:
        _reject_reserved_events_attr(key, tag_name="HTML element")
        self.source = source
        self.position = position
        self.key = key
        self.value = value
        self.used_vars = used_vars

    @override
    def resolve(self, context: CitryContext) -> Any:
        """
        Return the static value (a string, or ``True`` for a boolean attribute).

        The value is returned as-is, without the ``Const`` marker ("this is
        the same on every render"). Attribute values serve double duty: they
        can be slot and fill names, provide keys, or component inputs, and
        only the component-input use benefits from the marker. So
        ``ComponentNode`` adds the marker where the value becomes a component
        input, not here.
        """
        return self.value

    def __repr__(self) -> str:
        return f"StaticHtmlAttr(key={self.key!r}, value={self.value!r})"


@final
class ExprHtmlAttr(HtmlAttr):
    """
    A dynamic expression attribute (``c-class="expr"``).

    Generated as: ``ExprHtmlAttr(source, (start, end), "c-class", "expr", ("var",))``

    Example:
        Template ``<c-Card c-title="t" />`` produces::

            ExprHtmlAttr(source, (8, 19,), "c-title", "t", ("t",))

    """

    def __init__(
        self, source: Any, position: tuple[int, int], key: str, expr: str | bool, used_vars: tuple[str, ...]
    ) -> None:
        self.source = source
        self.position = position
        self.key = key
        # The expression string, or `True` for a value-less attribute (`c-foo`).
        self.expr = expr
        self.used_vars = used_vars
        # The safe-eval function for `expr`, compiled lazily on first resolve and
        # reused afterwards (the node is cached across renders, so this compiles
        # once).
        self._eval: Callable[[Any], Any] | None = None

    @override
    def resolve(self, context: CitryContext) -> Any:
        """
        Evaluate the expression and return the raw value.

        The value is NOT escaped or stringified: it becomes a component kwarg (a
        Python object). Escaping happens later, when the child component renders
        the value through an ``ExprNode``. The value is returned without the
        ``Const`` marker; for an expression that uses no variables (a literal
        written in the template), ``ComponentNode`` adds the marker where the
        value becomes a component input.
        """
        # The parser rejects a value-less `c-*` attribute, but node classes
        # are public API: an extension building an ExprHtmlAttr by hand (via
        # on_template_compiled) may pass `True` as the boolean form. There is
        # nothing to evaluate then; the attribute is simply on.
        if not isinstance(self.expr, str):
            return True
        if self._eval is None:
            self._eval = compile_expr(self.expr, sandboxed=context.sandboxed)
        return self._eval(context.variables)

    def __repr__(self) -> str:
        return f"ExprHtmlAttr(key={self.key!r}, expr={self.expr!r})"


@final
class TemplateHtmlAttr(HtmlAttr):
    """
    A nested template attribute (``c-body="<div>...</div>"``).

    Generated as::

        TemplateHtmlAttr(
            source, (start, end), "c-body", "<div>...</div>", ("var",)
        )

    Example:
        Template ``<c-Card c-body="<span>{{ x }}</span>" />`` produces::

            TemplateHtmlAttr(
                source, (8, 37,),
                "c-body", "<span>{{ x }}</span>", ("x",),
            )

    """

    def __init__(
        self,
        source: Any,
        position: tuple[int, int],
        key: str,
        template: str,
        used_vars: tuple[str, ...],
        foreign_spans: tuple[tuple[int, int, str, int, bool], ...] = (),
        source_offset: int = 0,
    ) -> None:
        self.source = source
        self.position = position
        self.key = key
        self.template = template
        self.used_vars = used_vars
        self.foreign_spans = foreign_spans
        self.source_offset = source_offset
        # Compiled lazily on first use in each render mode and then reused in that mode.
        self._generators: dict[bool, Callable[[], list[Any]]] = {}
        self._compile_lock = RLock()

    def _compiled_body(
        self,
        component_class: type[Component] | None,
        template_record: CitryTemplate | None,
    ) -> Callable[[], list[Any]]:
        """
        Return the nested template's body generator for the current render mode, compiling it on first use.

        Both ``resolve`` and the ``simple=True`` template check call this, so
        whichever runs first compiles the body and the other reuses it. The
        compile runs the compiled-template hooks and may start component
        discovery, so it runs with no lock held: two threads making the first
        render at once may each compile and run the hooks, and both get the
        generator stored first.
        """
        from citry._vue.capture import prepared_render_active  # noqa: PLC0415
        from citry.component_render import _compile_nested_template  # noqa: PLC0415

        prepared = prepared_render_active()
        generator = self._generators.get(prepared)
        if generator is not None:
            return generator
        # The nested template is validated like any other: the parse gets
        # the rules derived from the registered components' declarations.
        user_rules = component_class.citry._tag_rules() if component_class is not None else None
        compiled = _compile_nested_template(
            self.template,
            user_rules,
            component_class,
            root_source=self.source if self.foreign_spans else None,
            source_offset=self.source_offset,
            foreign_spans=self.foreign_spans,
            provider_metadata=(template_record.foreign_provider_metadata if template_record is not None else None),
            template_id=(template_record.template_id if template_record is not None else None),
            origin=(template_record.origin if template_record is not None else None),
        )
        with self._compile_lock:
            return self._generators.setdefault(prepared, compiled)

    @override
    def resolve(self, context: CitryContext) -> CitryRender:
        """
        Render the nested template and return it as a ``CitryRender`` kwarg value.

        The template is defined in the parent's scope, so it renders against the
        surrounding component's context.
        """
        from citry._vue.capture import prepared_render_active  # noqa: PLC0415
        from citry.component_render import _render_body  # noqa: PLC0415

        # A simple component renders inside its caller's context, so the
        # context's component is the caller. The class that owns this template
        # (and whose tag rules and hooks apply) is the simple component's.
        component = context.component
        if context._simple_scope is not None:
            owner: type[Component] | None = context._simple_scope.component_class
        else:
            owner = type(component) if component is not None else None
        generator = self._compiled_body(owner, context.template_record)
        prepared = prepared_render_active()
        parts = _render_body(generator(), context)
        selected = CitryRender(parts=parts, context=context)
        if prepared:
            from citry._vue.direct import (  # noqa: PLC0415
                active_execution,
                direct_execution_scope,
                wrap_nested_template,
            )

            component = context.component
            if component is not None and component.id is not None:
                active_template = context.template_record
                # A component that prints the value more than once renders it
                # again for each later print, as a slot is rendered for each
                # outlet. Each later render runs inside the same slot fill call
                # as this one (when the attribute sits in a fill), so the
                # browser data places its components in that same fill, as it
                # does for the first render.
                execution = active_execution()

                def render_again() -> CitryRender:
                    with direct_execution_scope(execution):
                        return CitryRender(parts=_render_body(generator(), context), context=context)

                return wrap_nested_template(
                    selected,
                    render_again=render_again,
                    lexical_render_id=component.id,
                    public_name=self.key,
                    source=self.source,
                    span=self.position,
                    origin=active_template.origin if active_template is not None else None,
                )
        return selected

    def __repr__(self) -> str:
        return f"TemplateHtmlAttr(key={self.key!r})"


_AttrsOutputKey: TypeAlias = tuple[tuple[str, type, object], ...]
_attrs_output_cache: dict[_AttrsOutputKey, str] = {}
_attrs_output_cache_lock = RLock()


class ElementAttrsNode(Node):
    """
    The attribute region of a plain HTML start tag with dynamic attributes.

    Generated as: ``ElementAttrsNode(source, (start, end), (attrs...), ("var1", ...))``

    Emitted when an HTML element (not a component) has at least one dynamic
    attribute (a ``c-*`` value or a ``c-bind`` spread), or a literal extension
    binding/output name that must remain structurally visible. The node covers
    ALL of the tag's attributes, static ones included, because the set resolves
    as one unit:

    - Contributions collect left to right in source order; ``c-bind``
      contributes each entry of its mapping (which must be a ``Mapping``).
    - ``class`` and ``style`` merge across contributions and accept the
      structured value forms (string / dict / nested list); every other key
      resolves last-one-wins.
    - ``True`` renders the bare attribute, ``False`` and ``None`` omit it,
      everything else renders escaped, ``Markup`` included.

    Renders to one string like ``' class="btn" disabled'`` (leading space
    included) or ``""`` when every attribute resolved away.

    An ``on_template_compiled`` extension may consume parser-proven literal
    attributes and collapse an otherwise-static region back to a string before
    this node reaches rendering. Events uses that path for ``@c-*`` / ``:c-*``.

    Example:
        Template ``<div id="x" c-class="cls">hi</div>`` produces::

            ElementAttrsNode(
                source, (0, 26,),
                (StaticHtmlAttr(...), ExprHtmlAttr(...),),
                ("cls",),
            )

    """

    def __init__(
        self, source: Any, position: tuple[int, int], attrs: tuple[HtmlAttr, ...], used_vars: tuple[str, ...]
    ) -> None:
        self.source = source
        self.position = position
        self.attrs = attrs
        self.used_vars = used_vars
        self._resolved_keys = tuple(attr.key.removeprefix("c-") for attr in attrs)
        # A `class` or `style` written empty (`<p class c-class="c">`) joins
        # the class/style merge as an empty marker rather than the boolean
        # `True` the parser gives it, which the merge rejects. Only a written
        # attribute qualifies, so a `True` from Python data still raises.
        self._template_empty = tuple(
            type(attr) is StaticHtmlAttr and template_attr_value(attr.key, attr.value) is TEMPLATE_EMPTY_VALUE
            for attr in attrs
        )
        self._has_spread = any(attr.key == "c-bind" for attr in attrs)
        self._validated_spread_keys: set[str] = set()
        # A `c-*` attribute such as `c-v-if` lets Python data fill a Vue
        # directive. Its name is fixed in the template, so it is found once
        # here and every render only checks this one field.
        self._vue_code_attr_key = next(
            (
                resolved_key
                for attr, resolved_key in zip(attrs, self._resolved_keys, strict=True)
                if attr.key.startswith("c-") and attr.key != "c-bind" and is_vue_code_attr_name(resolved_key)
            ),
            None,
        )
        self._has_runtime_events_candidate = self._has_spread or any(
            attr.key.startswith(("@c-", ":c-"))
            or attr.key.lower().startswith("data-cev-")
            or attr.key.lower() in {"data-citry-runtime-control", "data-citry-runtime-events"}
            for attr in attrs
        )
        # The tag name, read lazily from the template source on first use
        # (the compiler emits the tag name as a separate static chunk, so the
        # node itself does not receive it).
        self._tag_name: str | None = None

    @property
    def tag_name(self) -> str:
        """The element's tag name (e.g. ``"div"``), read from the source slice."""
        if self._tag_name is None:
            # Parser positions are UTF-8 byte offsets. Slice encoded source so
            # non-ASCII text before this tag cannot shift the Python indices.
            # The position spans the start tag, e.g. `<div c-class="cls">`.
            source = str(self.source).encode()
            name = source[self.position[0] + 1 : self.position[1]].decode()
            for index, char in enumerate(name):
                if char.isspace() or char in "/>":
                    name = name[:index]
                    break
            self._tag_name = name
        return self._tag_name

    @override
    def render(self, context: CitryContext) -> RenderPart:
        resolved, validate_keys = self._resolve_for_output(context)
        return self._format(resolved, context, validate_keys=validate_keys)

    def _resolve_for_output(self, context: CitryContext) -> tuple[dict[str, Any], bool]:
        """Resolve and run attribute hooks once, before target-specific formatting."""
        resolved = self._resolve(context)
        runtime_candidate = self._runtime_extension_candidate(resolved)

        # Let extensions rewrite the resolved dict (e.g. class dedup). Fires
        # only when an installed extension implements the hook; the manager
        # short-cuts otherwise (docs/design/template_html_attrs.md section 5.5).
        component = context.component
        validate_extension_output = False
        if component is not None:
            extensions = component.citry.extensions
            validate_extension_output = extensions.has_attrs_resolved_hook(
                runtime_candidate=runtime_candidate,
            )
            if validate_extension_output:
                resolved = extensions.on_attrs_resolved(
                    component=component,
                    tag_name=self.tag_name,
                    attrs=resolved,
                    runtime_candidate=runtime_candidate,
                )
                if has_client_props_key(resolved, tag_name=self.tag_name):
                    apply_client_props_contribution(
                        resolved,
                        resolved[CLIENT_PROPS_ATTR],
                        tag_name=self.tag_name,
                        component_boundary=False,
                    )

        if validate_extension_output:
            for key in resolved:
                validate_html_attr_name(key, where=f"attributes resolved for <{self.tag_name}>")
        return resolved, validate_extension_output

    def _runtime_extension_candidate(self, resolved: Mapping[str, Any]) -> bool:
        """Whether final attrs can still contain one render-time Events binding."""
        if not self._has_spread:
            return self._has_runtime_events_candidate
        return any(
            isinstance(key, str)
            and (
                str.startswith(key, ("@c-", ":c-"))
                or key.lower().startswith("data-cev-")
                or key.lower() in {"data-citry-runtime-control", "data-citry-runtime-events"}
            )
            for key in resolved
        )

    def _resolve(self, context: CitryContext) -> dict[str, Any]:
        """
        Collect the attribute contributions and merge them into one dict.

        ``False`` and ``None`` values are dropped here, so the merged dict
        holds only the attributes that will appear in the output (the
        ``on_attrs_resolved`` hook sees them already gone). A ``Const``
        marker is unwrapped so the normalizers see the real value.
        """
        # Every render path for this element resolves its attributes here,
        # so a `c-v-if`-style attribute fails on every page, with or without Vue.
        if self._vue_code_attr_key is not None:
            raise vue_code_error(self._vue_code_attr_key, tag_name=self.tag_name, origin="c-attr")
        if not self._has_spread:
            items: list[tuple[str, Any]] = []
            for attr, resolved_key, template_empty in zip(
                self.attrs, self._resolved_keys, self._template_empty, strict=True
            ):
                if template_empty:
                    items.append((resolved_key, TEMPLATE_EMPTY_VALUE))
                    continue
                if attr.key.startswith("c-"):
                    _reject_reserved_events_attr(resolved_key, tag_name=self.tag_name)
                items.append((resolved_key, const_value(attr.resolve(context))))
            merged = _merge_resolved_attrs(items)
        else:
            merged = self._resolve_with_spread(context)
        # `#c-*` framework attributes (`#c-key`, `#c-ignore`) are
        # template-authored only in v1: authored on the tag, the compiler
        # handles them before this node exists, so one arriving here came
        # through a spread or a dynamic attribute name and would render as a
        # meaningless literal attribute. Fail loudly, naming the fix.
        for merged_key in merged:
            if str.startswith(merged_key, "#c-"):
                msg = (
                    f"{merged_key!r} arrived on <{self.tag_name}> through an attribute spread or a "
                    "dynamic attribute. '#c-*' framework attributes are template-authored only: "
                    "write the attribute directly on the tag in the template."
                )
                raise RuntimeError(msg)
        if has_client_props_key(merged, tag_name=self.tag_name):
            apply_client_props_contribution(
                merged,
                merged[CLIENT_PROPS_ATTR],
                tag_name=self.tag_name,
                component_boundary=False,
            )
        return {key: value for key, value in merged.items() if value is not None and value is not False}

    def _resolve_with_spread(self, context: CitryContext) -> dict[str, Any]:
        """Resolve the general path used when a dynamic ``c-bind`` is present."""
        items: list[tuple[str, Any]] = []
        for attr, compiled_key, template_empty in zip(
            self.attrs, self._resolved_keys, self._template_empty, strict=True
        ):
            if template_empty:
                items.append((compiled_key, TEMPLATE_EMPTY_VALUE))
                continue
            if attr.key == "c-bind":
                value = const_value(attr.resolve(context))
                # A c-bind of None contributes nothing, so an optional
                # attribute dict (a common case) needs no guard at the call
                # site. This matches Vue's `v-bind="null"`. A non-None,
                # non-mapping value is still a mistake and is rejected.
                if value is None:
                    continue
                if not isinstance(value, Mapping):
                    msg = (
                        f"c-bind on <{self.tag_name}> must resolve to a mapping of attributes, "
                        f"got {type(value).__name__}"
                    )
                    raise TypeError(msg)
                for key, item in value.items():
                    # Only bounded exact strings can share validation across
                    # renders. Values and user-defined key behavior stay live.
                    cacheable_key = type(key) is str and len(key) <= 256
                    if cacheable_key and key in self._validated_spread_keys:
                        items.append((key, const_value(item)))
                        continue
                    resolved_key = validate_html_attr_name(key, where=f"c-bind on <{self.tag_name}>")
                    # The key is rejected whatever its value: even `None`
                    # would remove a listener written in the template. A key
                    # that passes is cached below, so repeat renders skip this.
                    reject_vue_code_attr_name(resolved_key, tag_name=self.tag_name, origin="c-bind")
                    if looks_like_i18n_binding(resolved_key):
                        if context._simple_scope is not None:
                            msg = (
                                f"Component {context._simple_scope.component_class.__name__} uses simple=True; "
                                "$c-tr bindings are unsupported."
                            )
                            raise TypeError(msg)
                        raise RuntimeError(
                            f"{resolved_key!r} resolved on <{self.tag_name}> through c-bind, but no active "
                            "i18n catalog consumed it. Configure i18n or declare component messages before "
                            "rendering a dynamic $c-tr binding."
                        )
                    _reject_reserved_events_attr(resolved_key, tag_name=self.tag_name)
                    if cacheable_key and len(self._validated_spread_keys) < 64:
                        self._validated_spread_keys.add(resolved_key)
                    items.append((resolved_key, const_value(item)))
            else:
                if attr.key.startswith("c-"):
                    _reject_reserved_events_attr(compiled_key, tag_name=self.tag_name)
                items.append((compiled_key, const_value(attr.resolve(context))))
        return _merge_resolved_attrs(items)

    def _format(
        self,
        resolved: Mapping[str, Any],
        context: CitryContext,
        *,
        validate_keys: bool = True,
    ) -> RenderPart:
        """Format the merged dict into the output part(s)."""
        cache_key: _AttrsOutputKey | None = None
        if (
            validate_keys is False
            and type(self) is ElementAttrsNode
            and type(resolved) is dict
            and len(resolved) <= 16
            and _has_default_attr_formatting(_format_resolved_attrs_to_str)
        ):
            items: list[tuple[str, type, object]] = []
            chars = 0
            for key, value in resolved.items():
                if type(key) is not str:
                    break
                chars += len(key)
                kind = type(value)
                if kind is str:
                    chars += len(value)
                elif kind is int:
                    if value.bit_length() > 256:
                        break
                elif value is not None and kind is not bool:
                    break
                if chars > 2048:
                    break
                items.append((key, kind, value))
            else:
                cache_key = tuple(items)
                cached = _attrs_output_cache.get(cache_key)
                if cached is not None:
                    return cached
                # Format the same immutable values used by the key, even if a
                # caller retains and changes its input dictionary concurrently.
                resolved = {key: value for key, _, value in cache_key}

        if validate_keys:
            for key in resolved:
                validate_html_attr_name(key, where=f"attributes resolved for <{self.tag_name}>")
        formatter = format_attrs if validate_keys else _format_resolved_attrs_to_str

        # Common case: no attribute value is a nested-template render, so the
        # whole dict formats in a single pass. Doing it per key (the mixed-case
        # path below) would escape, join, and concatenate once per attribute,
        # which is the dominant per-element cost on a big page.
        if not any(isinstance(value, CitryRender) for value in resolved.values()):
            chunk = formatter(resolved)
            result = (" " + chunk) if chunk else ""
            if (
                cache_key is not None
                and type(result) is str
                and _has_default_attr_formatting(_format_resolved_attrs_to_str)
            ):
                # Only misses take the lock. Eviction/insertion must be one
                # operation so simultaneous misses retain at most 256 entries.
                with _attrs_output_cache_lock:
                    if cache_key not in _attrs_output_cache and len(_attrs_output_cache) >= 256:
                        _attrs_output_cache.pop(next(iter(_attrs_output_cache)))
                    _attrs_output_cache[cache_key] = result
            return result

        # Mixed: a nested-template value (`c-foo="<div>...</div>"`) keeps its
        # parts so components inside it stay deferred and render through the
        # queue. Format the runs of plain attributes around it in one call each.
        parts: list[RenderPart] = []
        plain: dict[str, Any] = {}

        def flush_plain() -> None:
            if plain:
                chunk = formatter(plain)
                if chunk:
                    parts.append(" " + chunk)
                plain.clear()

        for key, value in resolved.items():
            if isinstance(value, CitryRender):
                flush_plain()
                parts.append(f' {escape(key)}="')
                parts.append(value)
                parts.append('"')
            else:
                plain[key] = value
        flush_plain()

        if not parts:
            return ""
        if all(isinstance(part, str) for part in parts):
            return "".join(str(part) for part in parts)
        return CitryRender(parts=parts, context=context)

    def __repr__(self) -> str:
        return f"ElementAttrsNode(attrs={len(self.attrs)}, used_vars={self.used_vars})"


@final
class ElementKeyNode(Node):
    """
    An explicit ``#c-key`` on a plain HTML element.

    Generated as ``ElementKeyNode(ExprHtmlAttr(...))``. The wrapped attribute
    evaluates in the surrounding template scope. ``None`` emits nothing, which
    makes the element behave exactly as if ``#c-key`` were absent. Every other
    value, including ``False``, ``0``, and ``""``, emits the escaped composite
    key ``data-citry-key=":<value>"``.

    The node owns the complete output attribute so omission cannot leave an
    empty scope prefix or a dangling quote in the start tag. It stays outside
    ``ElementAttrsNode`` because framework metadata must not enter ordinary
    attribute merging or the ``on_attrs_resolved`` extension hook.

    Args:
        attr: The compiled ``#c-key`` expression and its source metadata.

    """

    def __init__(self, attr: ExprHtmlAttr) -> None:
        self.attr = attr
        self.source = attr.source
        self.position = attr.position
        self.used_vars = attr.used_vars

    @override
    def render(self, context: CitryContext) -> RenderPart:
        value = const_value(self.attr.resolve(context))
        if value is None:
            return ""
        # The key is identity text, never markup: str() first, so a Markup
        # key is escaped too, the same way the Vue render writes it.
        return f' data-citry-key=":{escape(str(value))}"'

    def __repr__(self) -> str:
        return f"ElementKeyNode(expr={self.attr.expr!r}, used_vars={self.used_vars})"


def _kwarg_is_const(attr: HtmlAttr, context: CitryContext) -> bool:
    """
    Whether a resolved component-input value is the same on every render.

    A static attribute (``age="30"``) is always the same. An expression
    attribute (``c-age="..."``) is the same on every render when every variable
    it reads is itself constant. Two cases follow from that one rule:

    - An expression that reads no variables at all (``c-items="[1, 2]"``,
      ``c-age="30"``) is constant: nothing in it can change. An empty list
      of variable names therefore counts as constant.
    - An expression that reads only constant variables (``c-age="base + 1"``
      when ``base`` is constant) is constant too: a template expression only
      depends on its inputs, so if none of the inputs can change, neither can
      the result. Marking it lets the child component reuse the work it already
      did for that input.

    A ``TemplateHtmlAttr`` renders fresh output every time, and an attribute kind
    an extension added is unknown to us, so neither is treated as constant.
    """
    if isinstance(attr, StaticHtmlAttr):
        return True
    if isinstance(attr, ExprHtmlAttr):
        # Read live variables in order without allocating a generator for each input.
        for name in attr.used_vars:
            try:
                if not _mapping_value_is_const(context.variables, name):
                    return False
            except StopIteration as error:
                # Callers expect callback StopIteration to surface as RuntimeError.
                raise RuntimeError("generator raised StopIteration") from error
        return True
    return False


def _is_special_component_input_key(key: str) -> bool:
    """
    Whether a fixed component attr must go through the full client-binding checks in ``_resolve_inputs``.

    Every name Vue reads as a directive or binding goes through them,
    including Vue syntax a component tag rejects, so the classifier can
    report it rather than letting it become a kwarg the child never reads.
    """
    return key == "ref" or key.startswith(("$c-", "x-on:")) or is_vue_directive_name(key)


def _component_tag_vue_code_hint(key: str, *, component_boundary: bool) -> str | None:
    """
    Pick the fix for a Vue-code name that Python data put on a component tag.

    A directive the tag cannot carry at all (`v-for`, `#slot`, `.prop`) gets
    the hint the template parser gives for it, because writing it in the
    template would fail as well. `<c-element>` renders a plain HTML element,
    so it takes the general advice.
    """
    return unsupported_component_tag_directive_hint(key) if component_boundary else None


@dataclass(frozen=True, slots=True)
class _PendingComponentTagClientBinding:
    """One winning component-tag client binding before its location is recorded."""

    kind: ComponentTagClientBindingKind
    key: str
    value: str
    source: ComponentTagClientBindingSource
    attr: HtmlAttr
    mapping_key: str | None = None
    mapping_index: int | None = None


@dataclass(frozen=True, slots=True)
class _ResolvedComponentInputs:
    """The two independent channels resolved from a component start tag."""

    kwargs: dict[str, Any]
    # A spread-authored handler becomes a runtime event binding; everything else
    # on a component tag stays an ordinary client binding.
    client_bindings: tuple[ComponentTagClientBinding | RuntimeComponentEventBinding, ...]
    element_bindings: tuple[ComponentTagClientBinding, ...] = ()


# ComponentNode._finish_render's default for "the key is not evaluated yet",
# distinct from None, which is an evaluated key that opts out.
_KEY_NOT_EVALUATED = object()

ComponentNodeMetadataEntry: TypeAlias = (
    tuple[Literal["key"], ExprHtmlAttr] | tuple[Literal["morph"], Literal["ignore"]]
)
ComponentNodeMetadata: TypeAlias = tuple[
    Literal["range", "element"],
    Unpack[tuple[ComponentNodeMetadataEntry, ...]],
]


@final
class ComponentNode(Node):
    """
    A component node (``<c-Card>``, ``<c-component>``, any ``<c-*>``).

    Generated as::

        ComponentNode(
            source, (start, end), (attrs,...), [body],
            (used_vars,), "name", contains_fills,
        )

    Example:
        Template ``<c-Card title="Hi">body</c-Card>`` produces::

            ComponentNode(
                source, (0, 32,),
                (StaticHtmlAttr(source, (8, 18,), "title", "Hi", ()),),
                ["body"],
                (), "card", False,
            )

        Component names are lowercased (``Card`` -> ``card``); kebab names
        are preserved (``my-card`` stays ``my-card``).

    A tag carrying framework metadata appends one trailing tagged tuple. The
    ``range`` locus records a logical component-range directive; ``element``
    privately carries directives to the dynamic ordinary-element built-in.
    Metadata never joins ``attrs`` and can therefore never become a kwarg.

    """

    def __init__(
        self,
        source: Any,
        position: tuple[int, int],
        attrs: tuple[HtmlAttr, ...],
        body: list[BodyItem],
        used_vars: tuple[str, ...],
        name: str,
        contains_fills: bool,
        metadata: ComponentNodeMetadata | None = None,
    ) -> None:
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.name = name
        self.contains_fills = contains_fills
        self.metadata = metadata
        if name == "mark" and (len(attrs) != 1 or type(attrs[0]) is not StaticHtmlAttr or attrs[0].key != "name"):
            raise ValueError("<c-mark> requires one directly authored literal 'name' attribute.")
        self._has_plain_component_inputs = name != "element" and all(
            attr.key != "c-bind" and not _is_special_component_input_key(attr.key.removeprefix("c-")) for attr in attrs
        )
        # A `c-*` input such as `c-v-if` lets Python data fill a Vue binding.
        # Its name is fixed in the template, so it is found once here and
        # every render only checks this one field.
        self._vue_code_attr_key = next(
            (
                attr.key.removeprefix("c-")
                for attr in attrs
                if attr.key.startswith("c-")
                and attr.key != "c-bind"
                and is_vue_code_attr_name(attr.key.removeprefix("c-"))
            ),
            None,
        )
        self._metadata_locus: Literal["range", "element"] | None = None
        self.key: ExprHtmlAttr | None = None
        self.morph_mode: Literal["ignore"] | None = None
        # Filled by the Events extension from `_transform_element_attrs`, which
        # compiles each literal binding into a plain JSON-shaped mapping.
        self._element_event_bindings: tuple[dict[str, object], ...] = ()
        self._element_poll_bindings: tuple[dict[str, object], ...] = ()
        self._element_control_bindings: tuple[dict[str, object], ...] = ()
        self._element_runtime_events_candidate = False

        if metadata is None:
            return
        if not isinstance(metadata, tuple):
            msg = "ComponentNode metadata must be a tuple."
            raise TypeError(msg)
        if not metadata or metadata[0] not in {"range", "element"}:
            msg = "ComponentNode metadata locus must be 'range' or 'element'."
            raise TypeError(msg)
        self._metadata_locus = metadata[0]
        seen: set[str] = set()
        for entry in metadata[1:]:
            if not isinstance(entry, tuple) or len(entry) != 2:
                msg = "ComponentNode metadata entries must be two-item tuples."
                raise TypeError(msg)
            entry_name, payload = entry
            if entry_name not in {"key", "morph"}:
                msg = f"Unknown ComponentNode metadata entry {entry_name!r}."
                raise TypeError(msg)
            if entry_name in seen:
                msg = f"Duplicate ComponentNode metadata entry {entry_name!r}."
                raise TypeError(msg)
            seen.add(entry_name)
            if entry_name == "key":
                if not isinstance(payload, ExprHtmlAttr):
                    msg = "ComponentNode 'key' metadata requires an ExprHtmlAttr payload."
                    raise TypeError(msg)
                self.key = payload
            elif payload != "ignore":
                msg = "ComponentNode 'morph' metadata must be 'ignore'."
                raise TypeError(msg)
            else:
                self.morph_mode = "ignore"
        if self._metadata_locus == "range" and self.morph_mode == "ignore":
            # Whether a page becomes a Vue app is decided only when the
            # finished tree is serialized, after this tag's metadata is gone.
            # Rejecting when the template loads keeps the directive from being
            # dropped silently from an interactive page, even inside a branch
            # that never renders. A child component renders through its own Vue
            # instance, so its output cannot be kept as fixed HTML; the fix is
            # to mark the element inside the child that a library manages.
            msg = (
                f"'#c-ignore' is not supported on the component tag <{self._authored_tag()}>. The component"
                " renders through Vue, so its output cannot be kept as fixed HTML. Remove '#c-ignore' from"
                " the tag and put it on the HTML element inside the component's template whose contents a"
                " browser library manages, for example <div #c-ignore>."
            )
            raise TypeError(msg)

    def _authored_tag(self) -> str:
        """Return the tag name as the template spells it (``c-Child``), for error messages."""
        # `name` is lowercased, so a message quoting it would not match what
        # the author searches for. Parser positions are UTF-8 byte offsets and
        # start at the tag's `<`, so slice the encoded source.
        start = str(self.source).encode()[self.position[0] : self.position[1]].decode(errors="replace")
        end = next((index for index, char in enumerate(start) if char.isspace() or char in "/>"), len(start))
        authored = start[1:end]
        # A node built by hand rather than from a template has no source tag to quote.
        return authored if start.startswith("<") and authored.lower() == f"c-{self.name}" else f"c-{self.name}"

    @override
    def render(self, context: CitryContext) -> DeferredComponent:
        """
        Work out the child's inputs, but don't render the child yet.

        This turns the tag's attributes into the child's kwargs, collects the
        body into the child's slots, and returns a ``DeferredComponent``. It
        does not render the child here: doing so would make one component
        render the next and so on, hitting Python's recursion limit on deeply
        nested pages. ``render_impl`` renders the child later, with its own
        ``CitryContext``, and copies its dependencies into the parent.

        The attributes and fill structure are read now, while this component is
        still rendering, so a loop variable from an enclosing ``<c-for>`` has
        the right value. Fill *bodies* stay lazy: each becomes a ``Slot`` that
        closes over the current scope and renders only when the child invokes
        it.
        """
        component = context.component
        if component is None:
            msg = "ComponentNode.render requires a component context bound to a Citry instance."
            raise RuntimeError(msg)

        resolved = self._resolve_inputs(context)
        child_cls = component.citry.get(self.name)
        return self._finish_render(context, component, resolved, child_cls)

    def _finish_render(
        self,
        context: CitryContext,
        component: Component,
        resolved: _ResolvedComponentInputs,
        child_cls: type[Component],
        *,
        evaluated_key: str | None | object = _KEY_NOT_EVALUATED,
    ) -> DeferredComponent:
        """
        Finish ``render`` once the inputs are resolved and the class is looked up.

        A call-run row whose class no longer fits its run
        (``_render_run_row``) ends here, so it finishes exactly as
        ``render`` would without resolving its inputs or looking up its
        class a second time. ``evaluated_key`` is the key such a row already
        evaluated, so the key expression still runs once.
        """
        if child_cls.simple is True:
            from citry._simple_runtime import simple_deferred  # noqa: PLC0415

            if self.contains_fills or self.metadata is not None:
                msg = (
                    f"Component {child_cls.__name__} uses simple=True;"
                    " named fills and range directives are unsupported."
                )
                raise TypeError(msg)
            return simple_deferred(
                CitryElement(child_cls, resolved.kwargs, component_tag_client_bindings=resolved.client_bindings),
                context,
                body=self.body,
            )
        slots = self._collect_slots(context)
        # The key expression evaluates once in the parent's scope. Exactly
        # None opts out; every other value, including falsey values, is a key.
        if evaluated_key is _KEY_NOT_EVALUATED:
            evaluated_key = None
            if self.key is not None:
                key_value = const_value(self.key.resolve(context))
                evaluated_key = None if key_value is None else str(key_value)
        evaluated_key = cast("str | None", evaluated_key)
        element_key_target = self._metadata_locus == "element" or self.name == "element"
        element_morph_metadata = None
        if element_key_target and (
            evaluated_key is not None
            or self.morph_mode is not None
            or resolved.element_bindings
            or self._element_event_bindings
            or self._element_poll_bindings
            or self._element_control_bindings
            or self._element_runtime_events_candidate
        ):
            element_morph_metadata = _ElementMorphMetadata(
                key=evaluated_key,
                morph_mode=self.morph_mode,
                authored_bindings=resolved.element_bindings,
                event_bindings=self._element_event_bindings,
                poll_bindings=self._element_poll_bindings,
                control_bindings=self._element_control_bindings,
                owner_name=type(context.component).__name__,
                runtime_events_candidate=self._element_runtime_events_candidate,
            )
        element_type = CitryElement
        if child_cls._citry_dynamic_selector:
            from citry.components.dynamic import _DynamicSelectorElement  # noqa: PLC0415

            element_type = _DynamicSelectorElement
        # Element-locus keys travel through _ElementMorphMetadata to the
        # selected native root. They are not also keys for a transparent
        # component-call range.
        call_key = None if element_key_target else evaluated_key
        element = element_type(
            child_cls,
            resolved.kwargs,
            slots,
            component_tag_client_bindings=resolved.client_bindings,
            element_morph_metadata=element_morph_metadata,
            prepared_call_metadata=_PreparedCallMetadata(
                self.source,
                self.position,
                call_key,
                context.template_record.origin if context.template_record is not None else None,
                slot_free_body=not self.body,
            ),
        )
        if child_cls._citry_dynamic_selector:
            selector = cast("_DynamicSelectorElement", element)
            selector.contains_fills = self.contains_fills
            selector.has_range_directives = self.metadata is not None
        direct_parent_execution = None
        from citry._vue.direct import active_execution  # noqa: PLC0415

        direct_parent_execution = active_execution()
        # The active provide/inject entries are captured now, like the kwargs:
        # the child renders later (through the queue), when this context is
        # gone, but must still inherit what was provided around its tag.
        return DeferredComponent(
            element,
            component,
            context.provides,
            direct_parent_execution=direct_parent_execution,
        )

    def _render_run_row(
        self,
        context: CitryContext,
        run: _DeferredRun | None,
        run_class: type[Component],
    ) -> DeferredComponent | tuple[dict[str, Any], _PreparedCallMetadata, DirectExecutionFrame | None]:
        """
        Run ``render`` for one row of a call run, returning the row's data instead of its element.

        A call run is the rows one ``<c-for>`` places at one component call
        site. ``ForNode._call_run_class`` accepted this call as a run (no
        body, a key, plain inputs, no element locus), so this makes
        ``render``'s steps in the same order: the inputs, the registry
        lookup, the ``simple`` read, the key and the selector read. It
        returns the row's kwargs, call metadata and execution frame for the
        run to hold.

        When the looked-up class no longer fits the run, or the execution
        frame differs from the run's, the row is finished as ``render``
        would finish it and its ``DeferredComponent`` is returned, which
        ends the run. For a row that stays in the run, ``render`` reads the
        class's ``_citry_dynamic_selector`` twice and this reads it once. It
        is a plain class attribute, and ``ComponentMeta`` defines no read
        hook for it.
        """
        component = cast("Component", context.component)
        resolved = self._resolve_inputs(context)
        child_cls = component.citry.get(self.name)
        # A class registered under the name since the loop started takes
        # render's own path, as in a loop that is not a run. The simple read
        # keeps render's read order; the metaclass keeps it fixed per class.
        if child_cls is not run_class or child_cls.simple is True:
            return self._finish_render(context, component, resolved, child_cls)
        # render collects the slots here, which gives {} for the empty body
        # every admitted call has, so that step has nothing to do.
        key_value = const_value(cast("ExprHtmlAttr", self.key).resolve(context))
        evaluated_key = None if key_value is None else str(key_value)
        # render reads the selector flag after the key, to pick the element
        # type; a class that became a selector also leaves the run.
        if child_cls._citry_dynamic_selector:
            return self._finish_render(context, component, resolved, child_cls, evaluated_key=evaluated_key)
        metadata = _PreparedCallMetadata(
            self.source,
            self.position,
            evaluated_key,
            context.template_record.origin if context.template_record is not None else None,
            slot_free_body=True,
        )
        from citry._vue.direct import active_execution  # noqa: PLC0415

        execution = active_execution()
        # The run holds one execution frame for every row, so a row that sees
        # another frame keeps its own deferred component.
        if run is not None and execution is not run.execution:
            element = CitryElement(child_cls, resolved.kwargs, {}, prepared_call_metadata=metadata)
            return DeferredComponent(element, component, context.provides, direct_parent_execution=execution)
        return resolved.kwargs, metadata, execution

    def _resolve_inputs(self, context: CitryContext) -> _ResolvedComponentInputs:
        """
        Turn the attribute nodes into the child component's kwargs.

        - ``c-bind="expr"`` is a spread: its evaluated mapping is merged in,
          rather than producing a ``bind`` kwarg.
        - Other dynamic attrs carry a leading ``c-`` (``c-foo`` -> ``foo``);
          static attrs have a plain key. ``removeprefix`` handles both.

        A value that is the same on every render is marked ``Const`` here, so
        the child component can reuse the work it already did for that input,
        with no opt-in needed (see docs/design/component_constness.md). That covers a
        literal (``age="30"``, ``c-items="[1, 2]"``) and also an expression
        whose variables are all constant at render time (``c-age="base + 1"``
        when ``base`` is constant): the result of such an expression cannot
        change either, so it is constant too. ``_kwarg_is_const`` is the single
        rule that decides this. The marking happens here, where a value becomes
        a component input, and nowhere else, so values used as names or keys
        (slot/fill names, provide keys) stay plain. This is a transient
        renderer transport marker: component construction consumes it into a
        plain value plus name provenance before hooks or callbacks run. It is
        applied fresh on each render, so a mutable literal (a list) is still a
        new object every render; equal values still land on the same cache
        entry.
        """
        # Checked before any input resolves, so the error is the same on every
        # page, whether or not the page goes on to start Vue.
        if self._vue_code_attr_key is not None:
            raise vue_code_error(
                self._vue_code_attr_key,
                tag_name=f"c-{self.name}",
                origin="c-attr",
                hint=_component_tag_vue_code_hint(self._vue_code_attr_key, component_boundary=self.name != "element"),
            )
        if self._has_plain_component_inputs:
            plain_kwargs: dict[str, Any] = {}
            for attr in self.attrs:
                value = attr.resolve(context)
                if _kwarg_is_const(attr, context):
                    value = Const(value)
                plain_kwargs[attr.key.removeprefix("c-")] = value
            return _ResolvedComponentInputs(kwargs=plain_kwargs, client_bindings=())

        kwargs: dict[str, Any] = {}
        element_attr_contributions: list[Mapping[str, Any]] = []
        pending_client_bindings: dict[str, _PendingComponentTagClientBinding] = {}
        pending_element_bindings: dict[str, _PendingComponentTagClientBinding] = {}
        tag_name = f"c-{self.name}"
        component_boundary = self.name != "element"
        component = context.component
        if component is None:
            msg = "Component input resolution requires a component-owned context."
            raise RuntimeError(msg)

        def apply_kwarg(resolved_key: str, value: Any) -> None:
            # A dynamic <c-element> is an HTML-attribute boundary, so every
            # input keeps its source-ordered contribution until the shared
            # HTML merge can fold case variants and accumulate class/style.
            # Ordinary components keep exact-case Python-kwarg last-one-wins.
            if not component_boundary:
                element_attr_contributions.append({resolved_key: value})
            else:
                kwargs[resolved_key] = value

        def reject_component_state_binding(resolved_key: Any) -> None:
            if component_boundary and isinstance(resolved_key, str) and resolved_key.startswith("x-on:"):
                raise RuntimeError(
                    f"Alpine binding {resolved_key!r} was removed; use native Vue v-on or @event syntax."
                )
            if component_boundary and isinstance(resolved_key, str) and resolved_key.startswith(":c-"):
                msg = (
                    f"State binding {resolved_key!r} is not valid on the <{tag_name}> component boundary. "
                    "State bindings go on HTML controls; a child binds its own State in its template. "
                    "Pass data down with a native Vue prop binding (`:prop` or `v-bind:prop`) or Python kwargs."
                )
                raise RuntimeError(msg)

        def apply_client_binding(
            resolved_key: str,
            raw_value: Any,
            attr: HtmlAttr,
            *,
            source: ComponentTagClientBindingSource,
            mapping_key: str | None = None,
            mapping_index: int | None = None,
        ) -> bool:
            if (
                not component_boundary
                and source is not ComponentTagClientBindingSource.DIRECT
                and resolved_key.startswith(("@c-", ":c-"))
            ):
                # Dynamic Events/State spread keys remain ordinary Python
                # attributes until the final-tag attrs hook authenticates and
                # validates them against the selected HTML element.
                return False
            client_binding_kind = classify_component_tag_client_binding_key(
                resolved_key, tag_name=tag_name, component_boundary=component_boundary
            )
            if client_binding_kind is None:
                return False
            if not component_boundary:
                if client_binding_kind not in {
                    ComponentTagClientBindingKind.EVENT,
                    ComponentTagClientBindingKind.PROP,
                    ComponentTagClientBindingKind.PROPS_OBJECT,
                }:
                    return False
                # Vue-prefixed names from c-bind and c-* already failed with
                # VueCodeError. What remains is `ref` set from Python data, which
                # Vue also reads although it has no Vue prefix, or a written
                # binding whose value another template language filled in.
                if source is not ComponentTagClientBindingSource.DIRECT:
                    raise RuntimeError(
                        f"{resolved_key!r} on <c-element> came from Python data; write "
                        f'{resolved_key}="name" directly in the template.'
                    )
                if type(attr) is not StaticHtmlAttr:
                    raise RuntimeError(
                        f"Vue binding {resolved_key!r} on <c-element> must be written in the template "
                        "with a plain text value."
                    )
                if "{{" in str(raw_value):
                    raise RuntimeError(
                        f"Vue binding {resolved_key!r} on <c-element> cannot use template interpolation."
                    )
                pending_element_bindings.pop(resolved_key, None)
                pending_element_bindings[resolved_key] = _PendingComponentTagClientBinding(
                    kind=client_binding_kind,
                    key=resolved_key,
                    value=resolve_component_tag_client_binding_value(
                        resolved_key,
                        raw_value,
                        tag_name="c-element",
                        kind=client_binding_kind,
                    )
                    or "",
                    source=source,
                    attr=attr,
                    mapping_key=mapping_key,
                    mapping_index=mapping_index,
                )
                element_attr_contributions.append({resolved_key: raw_value})
                return True
            # Vue-prefixed names from c-bind and c-* already failed with
            # VueCodeError. What remains is `ref` set from Python data, which
            # Vue also reads although it has no Vue prefix, or a written
            # binding whose value another template language filled in.
            if client_binding_kind is not ComponentTagClientBindingKind.CITRY_HANDLER:
                if source is not ComponentTagClientBindingSource.DIRECT:
                    raise RuntimeError(
                        f"{resolved_key!r} on <{tag_name}> came from Python data; write "
                        f'{resolved_key}="name" directly in the template.'
                    )
                if type(attr) is not StaticHtmlAttr:
                    raise RuntimeError(
                        f"Vue binding {resolved_key!r} on <{tag_name}> must be written in the template "
                        "with a plain text value."
                    )
            if client_binding_kind is not ComponentTagClientBindingKind.CITRY_HANDLER and "{{" in str(raw_value):
                raise RuntimeError(f"Vue binding {resolved_key!r} on <{tag_name}> cannot use template interpolation.")
            # `v-model:key` would pass its value as the same `key` prop, which
            # the call's own identity then overrides without a trace.
            if resolved_key.split(".", 1)[0] in {
                ":key",
                "v-bind:key",
                ":citry-id",
                "v-bind:citry-id",
                "v-model:key",
                "v-model:citry-id",
                "v-model:citryId",
            }:
                raise RuntimeError(
                    f"Vue binding {resolved_key!r} on <{tag_name}> targets Citry-owned component identity."
                )
            client_binding_value = resolve_component_tag_client_binding_value(
                resolved_key,
                raw_value,
                tag_name=tag_name,
                kind=client_binding_kind,
            )
            if client_binding_value is None:
                pending_client_bindings.pop(resolved_key, None)
            else:
                # Replacement moves the exact key to this later contribution's
                # position, matching the accepted source-order contract.
                pending_client_bindings.pop(resolved_key, None)
                pending_client_bindings[resolved_key] = _PendingComponentTagClientBinding(
                    kind=client_binding_kind,
                    key=resolved_key,
                    value=client_binding_value,
                    source=source,
                    attr=attr,
                    mapping_key=mapping_key,
                    mapping_index=mapping_index,
                )
            return True

        for attr in self.attrs:
            key: str = attr.key
            if key == "c-bind":
                bound = attr.resolve(context)
                # A c-bind of None contributes nothing (an optional kwargs dict
                # needs no `or {}` guard at the call site), matching Vue's
                # `v-bind="null"` and the same rule on plain elements. A
                # non-None, non-mapping value is still a mistake.
                if bound is None:
                    continue
                if not isinstance(bound, Mapping):
                    msg = f"c-bind on <{self.name}> must resolve to a mapping of kwargs, got {type(bound).__name__}"
                    raise TypeError(msg)
                for mapping_index, (bound_key, bound_value) in enumerate(bound.items()):
                    if self.name == "element":
                        resolved_bound_key = validate_html_attr_name(bound_key, where="c-bind on <c-element>")
                        _reject_reserved_events_attr(resolved_bound_key, tag_name="c-element")
                    elif not isinstance(bound_key, str):
                        msg = (
                            f"c-bind on <c-{self.name}> must use string kwarg names, "
                            f"got {type(bound_key).__name__} key {bound_key!r}"
                        )
                        raise TypeError(msg)
                    else:
                        resolved_bound_key = bound_key
                    # A mapping key is Python data, so it may not name Vue
                    # code, even with a None value that would only remove it.
                    if is_vue_code_attr_name(resolved_bound_key):
                        raise vue_code_error(
                            resolved_bound_key,
                            tag_name=tag_name,
                            origin="c-bind",
                            hint=_component_tag_vue_code_hint(
                                resolved_bound_key, component_boundary=component_boundary
                            ),
                        )
                    reject_component_state_binding(resolved_bound_key)
                    _reject_dynamic_translation_binding(resolved_bound_key, tag_name=tag_name)
                    if apply_client_binding(
                        resolved_bound_key,
                        bound_value,
                        attr,
                        source=ComponentTagClientBindingSource.SPREAD,
                        mapping_key=resolved_bound_key,
                        mapping_index=mapping_index,
                    ):
                        continue
                    if is_client_props_key(resolved_bound_key, tag_name=tag_name):
                        apply_client_props_contribution(
                            kwargs,
                            bound_value,
                            tag_name=tag_name,
                            component_boundary=False,
                        )
                    else:
                        apply_kwarg(resolved_bound_key, bound_value)
                continue
            value = attr.resolve(context)
            resolved_key = key.removeprefix("c-")
            if not component_boundary and type(attr) is StaticHtmlAttr:
                # A dynamic <c-element> merges its class and style like a
                # plain element, so a written empty one joins as the marker.
                value = template_attr_value(resolved_key, value)
            reject_component_state_binding(resolved_key)
            _reject_dynamic_translation_binding(resolved_key, tag_name=tag_name)
            client_binding_source = (
                ComponentTagClientBindingSource.SERVER_DYNAMIC
                if key.startswith("c-")
                else ComponentTagClientBindingSource.DIRECT
            )
            if not component_boundary and client_binding_source == ComponentTagClientBindingSource.SERVER_DYNAMIC:
                _reject_reserved_events_attr(resolved_key, tag_name="c-element")
            if apply_client_binding(resolved_key, value, attr, source=client_binding_source):
                continue
            if _kwarg_is_const(attr, context):
                value = Const(value)
            if resolved_key == CLIENT_PROPS_ATTR:
                apply_client_props_contribution(
                    kwargs,
                    value,
                    tag_name=f"c-{self.name}",
                    component_boundary=False,
                )
            else:
                apply_kwarg(resolved_key, value)

        if element_attr_contributions:
            kwargs.update(merge_attrs(*element_attr_contributions))
        # `#c-*` framework attributes are template-authored only in v1: the
        # compiler carries an authored `#c-key` as the node's `key` (never a
        # kwarg), so one arriving here came through a `c-bind` spread or a
        # dynamic attribute name and would silently become an unusable kwarg.
        # Fail loudly, naming the fix.
        for kwarg_key in kwargs:
            if isinstance(kwarg_key, str) and str.startswith(kwarg_key, "#c-"):
                msg = (
                    f"{kwarg_key!r} arrived on <c-{self.name}> through an attribute spread or a "
                    "dynamic attribute. '#c-*' framework attributes are template-authored only: "
                    "write the attribute in the template itself, where Citry checks that the tag allows it."
                )
                raise RuntimeError(msg)
        from citry.client_directives import authenticated_component_tag_client_binding  # noqa: PLC0415

        client_bindings = tuple(
            authenticated_runtime_component_event_binding(
                key=value.key,
                value=value.value,
                spread_attr=value.attr,
            )
            if value.source is ComponentTagClientBindingSource.SPREAD
            else authenticated_component_tag_client_binding(
                kind=value.kind,
                key=value.key,
                value=value.value,
                authored_attr=value.attr,
            )
            for value in pending_client_bindings.values()
        )
        element_bindings = tuple(
            authenticated_component_tag_client_binding(
                kind=value.kind,
                key=value.key,
                value=value.value,
                authored_attr=value.attr,
            )
            for value in pending_element_bindings.values()
        )
        return _ResolvedComponentInputs(
            kwargs=kwargs,
            client_bindings=client_bindings,
            element_bindings=element_bindings,
        )

    def _collect_slots(self, context: CitryContext) -> dict[str, Slot]:
        """
        Turn the tag's body into the child component's slots.

        Two body modes, split by the compiler's ``contains_fills`` flag (see
        docs/design/component_slots.md section 4):

        - No fills: the whole body is the implicit default slot, registered
          under ``"default"``. A whitespace-only body is formatting, not
          content, and produces no slot.
        - Fills: the body is a fill group. Each ``<c-fill>`` becomes one slot;
          control flow between fills is evaluated now, against the live
          context, to decide which fills exist.
        """
        if not self.body:
            return {}

        if not self.contains_fills:
            if _body_is_whitespace_only(self.body):
                return {}
            return {
                "default": _make_body_slot(
                    self.body,
                    context,
                    self.name,
                    "default",
                    None,
                    None,
                    self.position,
                    source=self.source,
                    kind=LogicalFillKind.IMPLICIT,
                )
            }

        sink = FillSink(self.name)
        collect_fills_from_body(self.body, context, sink)
        return sink.fills

    def __repr__(self) -> str:
        return f"ComponentNode(name={self.name!r}, attrs={len(self.attrs)}, body={len(self.body)} items)"


@final
class BodySteps(NamedTuple):
    """
    The bodies a control-flow node renders, and how it wraps their parts.

    ``IfNode`` and ``ForNode`` return this from ``_render_steps``, so the body
    renderer can render each body on its own stack instead of calling the
    node's ``render``, which would call the body renderer again for every
    level of nesting. ``bodies`` yields each ``(body, context)`` pair in render
    order, and is read one pair at a time, so loop side effects and errors
    happen in the same order as in ``render``. ``finish`` takes the parts of
    every body, in order, and returns the node's part.
    """

    bodies: Iterator[tuple[Sequence[BodyItem], CitryContext]]
    finish: Callable[[list[RenderPart]], CitryRender]


@final
class IfNode(Node):
    """
    A conditional node (``<c-if>``/``<c-elif>``/``<c-else>``).

    Generated as: ``IfNode(source, (branch1, branch2, ...), (used_vars,))``

    Each branch is a tuple: ``((start, end), (attrs,), [body], (introduced_vars,))``

    Example:
        Template ``<c-if cond="x">yes</c-if><c-else>no</c-else>`` produces
        an ``IfNode`` with two branches - one for the if-body and one for
        the else-body.

    Each branch is ``((start, end), (attrs,), [body], (introduced_vars,))``.
    The ``c-if``/``c-elif`` branches carry a ``cond`` attribute (an
    ``ExprHtmlAttr``); the ``c-else`` branch has none and always matches.

    """

    def __init__(self, source: Any, branches: tuple[Any, ...], used_vars: tuple[str, ...]) -> None:
        self.source = source
        self.branches = branches
        self.used_vars = used_vars

    def active_branch_body(self, context: CitryContext) -> list[BodyItem] | None:
        """
        Return the body of the first branch that matches, or ``None``.

        Branches are tried in source order (``c-if`` then each ``c-elif`` then
        ``c-else``). A branch's ``cond`` attribute is resolved against the
        context; the first truthy one wins. A branch with no ``cond`` (the
        ``c-else``) always matches.

        Shared by ``render`` and by fill collection (``ComponentNode`` walks
        the matching branch when gathering ``<c-fill>`` tags).
        """
        for branch in self.branches:
            attrs: tuple[HtmlAttr, ...] = branch[1]
            body: list[BodyItem] = branch[2]
            cond_attr = _find_attr(attrs, "cond")
            if cond_attr is None or cond_attr.resolve(context):
                return body
        return None

    @override
    def render(self, context: CitryContext) -> CitryRender:
        """
        Render the first branch whose ``cond`` is truthy.

        If no branch matches, the render is empty. The body renders against the
        surrounding ``context`` unchanged: an ``<c-if>`` introduces no
        variables, so there is no new scope.
        """
        # Imported lazily: component_render imports the node classes, so importing
        # the body walker at module load would be circular.
        from citry.component_render import _render_body  # noqa: PLC0415

        body = self.active_branch_body(context)
        if body is None:
            return CitryRender(parts=[], context=context)
        return CitryRender(parts=_render_body(body, context), context=context)

    def _render_steps(self, context: CitryContext) -> BodySteps:
        """
        Return what ``render`` would render, for the body renderer's own stack.

        The matching branch's body renders against ``context``, and its parts
        are wrapped exactly as ``render`` wraps them.
        """
        body = self.active_branch_body(context)
        bodies = iter(((body, context),) if body is not None else ())
        return BodySteps(bodies, lambda parts: CitryRender(parts=parts, context=context))

    @override
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:
        """In a fill group, an ``<c-if>`` contributes the fills of its matching branch."""
        body = self.active_branch_body(context)
        if body is not None:
            collect_fills_from_body(body, context, sink)

    def __repr__(self) -> str:
        return f"IfNode(branches={len(self.branches)})"


@final
class ForNode(Node):
    """
    A loop node (``<c-for>``/``<c-empty>``).

    Generated as: ``ForNode(source, (for_branch, empty_branch?), (used_vars,))``

    Each branch is a tuple: ``((start, end), (attrs,), [body], (introduced_vars,))``

    Example:
        Template ``<c-for each="item in items">{{ item }}</c-for>`` produces
        a ``ForNode`` with one branch. Adding ``<c-empty>none</c-empty>``
        after it adds a second branch for the empty state.

    Each branch is ``((start, end), (attrs,), [body], (introduced_vars,))``.
    The loop branch carries an ``each`` attribute holding a Python comprehension
    clause (``"item in items"``, or the full ``"x in xs for y in ys if ..."``);
    ``introduced_vars`` are the loop targets it binds.

    """

    def __init__(self, source: Any, branches: tuple[Any, ...], used_vars: tuple[str, ...]) -> None:
        self.source = source
        self.branches = branches
        self.used_vars = used_vars
        # Const precomputation may evaluate an all-const loop once and retain
        # only its rendered text. The ForNode itself still survives so its
        # binding check runs against the live context immediately before that
        # text is emitted (an earlier expression may have mutated the mapping
        # since the cache entry was built).
        self._precomputed_parts: tuple[RenderPart, ...] | None = None
        # The generator-expression evaluator for the `each` clause, compiled
        # lazily on first render and reused afterwards (the node is cached across
        # renders, so this compiles once).
        self._iter_eval: Callable[[Any], Any] | None = None
        # The Rust loop walk's plan for this loop and the scope names its
        # inputs read (level C2 of the native render path), built on the
        # loop's first walk; a str names why the loop has none.
        self._walk_plan: tuple[Any, tuple[str, ...]] | str | None = None

    def _with_precomputed_text(self, text: str) -> ForNode:
        """Return a fresh runtime guard for text produced by const unrolling."""
        return self._with_precomputed_parts((text,))

    def _with_precomputed_parts(self, parts: tuple[RenderPart, ...]) -> ForNode:
        """Return a fresh runtime guard for certified immutable render parts."""
        node = ForNode(self.source, self.branches, self.used_vars)
        node._precomputed_parts = parts
        return node

    def iter_bodies(self, context: CitryContext) -> Iterator[tuple[list[BodyItem], CitryContext]]:
        """
        Yield ``(body, context)`` once per loop iteration.

        The ``each`` clause is a Python comprehension clause, so the loop is
        evaluated by wrapping it in a generator expression that yields the loop
        targets as a tuple: ``each="x in xs if x > 0"`` becomes
        ``((x,) for x in xs if x > 0)``. This reuses Python's own comprehension
        semantics, so multi-target unpacking and ``if`` filters work for free.

        Each iteration's context overlays the loop bindings on the surrounding
        ``variables``; it shares the parent's ``component`` and ``extra`` bag,
        so the loop introduces a variable scope without crossing a component
        boundary. With no iterations, the optional ``<c-empty>`` branch's body
        is yielded once, with the surrounding context.

        Shared by ``render`` and by fill collection (``ComponentNode`` walks
        the iterations when gathering ``<c-fill>`` tags, so each collected fill
        closes over its own iteration's bindings).
        """
        for_branch = self.branches[0]
        targets: tuple[str, ...] = for_branch[3]
        body: list[BodyItem] = for_branch[2]

        # Validate before evaluating the iterable so an empty loop cannot hide
        # an invalid binding and no loop expression runs in an invalid scope.
        _validate_introduced_variables("c-for", targets, context)

        if self._iter_eval is None:
            each_attr = _find_attr(for_branch[1], "each")
            if not isinstance(each_attr, ExprHtmlAttr):
                msg = "ForNode loop branch is missing a usable 'each' expression."
                raise RuntimeError(msg)
            # `each_attr.expr` is the raw clause, e.g. "item in items". Wrapping
            # the targets in a 1-tuple keeps single- and multi-target binding
            # uniform: `(x,)` for one target, `(k, v,)` for several.
            clause = each_attr.expr
            gen_src = f"(({', '.join(targets)},) for {clause})"
            self._iter_eval = compile_expr(gen_src, sandboxed=context.sandboxed)

        count = 0
        for values in self._iter_eval(context.variables):
            count += 1
            child = CitryContext(
                variables=_overlay_const_mapping(context.variables, dict(zip(targets, values, strict=True))),
                extra=context.extra,
                component=context.component,
                provides=context.provides,
                sandboxed=context.sandboxed,
                template_record=context.template_record,
                _simple_scope=context._simple_scope,
            )
            yield body, child

        # No iterations: the optional <c-empty> branch (second branch).
        if count == 0 and len(self.branches) > 1:
            yield self.branches[1][2], context

    @override
    def render(self, context: CitryContext) -> CitryRender:
        """
        Render the loop body once per item; the empty branch if there are none.

        See ``iter_bodies`` for the loop evaluation and scoping rules.
        """
        from citry.component_render import _render_body  # noqa: PLC0415

        steps = self._render_steps(context)
        if type(steps) is not BodySteps:
            return steps
        parts: list[RenderPart] = []
        for body, body_context in steps.bodies:
            parts.extend(_render_body(body, body_context))
        return steps.finish(parts)

    def _render_steps(self, context: CitryContext) -> BodySteps | CitryRender:
        """
        Return what ``render`` would render, for the body renderer's own stack.

        A loop with precomputed parts, or one that records its rows as a
        call run, renders here and returns its finished part: neither one
        renders a nested body. Any other loop returns one body per
        iteration, read one at a time from ``iter_bodies``, and the step
        that wraps their parts as ``render`` does.
        """
        if self._precomputed_parts is not None:
            targets: tuple[str, ...] = self.branches[0][3]
            _validate_introduced_variables("c-for", targets, context)
            return CitryRender(parts=list(self._precomputed_parts), context=context)

        # A loop that places simple='vue' rows records them in one run, which
        # the render queue then renders in a single task.
        run_class = self._call_run_class(context)
        if run_class is not None:
            # On the native render path, Rust reads the rows when every path
            # the loop reads is plain; a str says why it did not, and
            # Python's walk then runs the loop from the start.
            walked = self._walk_call_run(context, run_class) if _native_render.ACTIVE else None
            parts = walked if type(walked) is list else self._render_call_run(context, run_class)
            return self._finish_render(parts, context)
        return BodySteps(self.iter_bodies(context), lambda parts: self._finish_render(parts, context))

    def _finish_render(self, parts: list[RenderPart], context: CitryContext) -> CitryRender:
        """Wrap the loop's parts as ``render`` returns them: a render, or a call run."""
        selected = CitryRender(parts=parts, context=context)
        from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

        if not direct_prepared_render_active() or len(self.branches) != 1:
            return selected
        body = self.branches[0][2]
        if len(body) != 1 or type(body[0]) is not ComponentNode:
            return selected
        call_node = body[0]
        from citry.client_directives import classify_component_tag_client_binding_key  # noqa: PLC0415

        has_browser_binding = any(
            attr.key == "c-bind"
            or classify_component_tag_client_binding_key(
                attr.key.removeprefix("c-"),
                tag_name=f"c-{call_node.name}",
                component_boundary=call_node.name != "element",
            )
            is not None
            for attr in call_node.attrs
        )
        if (
            call_node.body
            or call_node.key is None
            or call_node.name == "element"
            or has_browser_binding
            or context.component is None
            or any(_is_special_component_input_key(attr.key) for attr in call_node.attrs)
        ):
            return selected
        registry = context.component.citry
        if not registry._registry_ready():
            return selected
        child_cls = registry._registry._name_to_cls.get(call_node.name)
        if child_cls is None or child_cls.simple is True or child_cls.transparent or child_cls._citry_dynamic_selector:
            return selected
        from citry._vue.direct import DirectCallRunRender  # noqa: PLC0415

        return DirectCallRunRender(selected, call_node=call_node, child_type_key=child_cls.class_id)

    def _call_run_class(self, context: CitryContext) -> type[Component] | None:
        """
        Return the class whose rows this loop records as one call run, or None.

        A call run is the rows one ``<c-for>`` places at one component call
        site. A loop qualifies when ``render`` would wrap its result as a
        call run (the checks ``render`` makes after its loop, made here
        before it) and, in addition, the call's class is ``simple = "vue"``,
        the call's inputs are plain, it has no browser bindings, and its
        metadata does not target an element. The registry can change while
        the loop runs, so each row looks its class up again, and the checks
        after the loop still run unchanged and decide whether the loop's
        output is marked as a call run (``DirectCallRunRender``).
        """
        from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

        if not direct_prepared_render_active() or len(self.branches) != 1:
            return None
        body = self.branches[0][2]
        if len(body) != 1 or type(body[0]) is not ComponentNode:
            return None
        call_node = body[0]
        if (
            call_node.body
            or call_node.key is None
            or call_node.name == "element"
            or call_node._metadata_locus == "element"
            or not call_node._has_plain_component_inputs
            or context.component is None
        ):
            return None
        try:
            has_browser_binding = any(
                classify_component_tag_client_binding_key(
                    attr.key.removeprefix("c-"), tag_name=f"c-{call_node.name}", component_boundary=True
                )
                is not None
                for attr in call_node.attrs
            )
        except Exception:  # noqa: BLE001 - the same check after the loop raises it, as in a loop that is not a run
            return None
        if has_browser_binding or any(_is_special_component_input_key(attr.key) for attr in call_node.attrs):
            return None
        registry = context.component.citry
        if not registry._registry_ready():
            return None
        child_cls = registry._registry._name_to_cls.get(call_node.name)
        if (
            child_cls is None
            or child_cls.simple != "vue"
            or child_cls.transparent
            or child_cls._citry_dynamic_selector
        ):
            return None
        return child_cls

    def _render_call_run(self, context: CitryContext, run_class: type[Component]) -> list[RenderPart]:
        """
        Walk the loop, recording its rows in one ``_DeferredRun`` and one ``_DeferredRunRow`` per row.

        Each row makes the steps ``_render_body`` and ``ComponentNode.render``
        make for it, in the same order: the row's value context, the trace
        line, the inputs, the registry lookup, the key, the call metadata,
        and the template position on an error. Only the row's element and
        deferred component are not built; the run's task builds them later
        if the row needs the ordinary component path. When a row's class no
        longer fits the run or its execution frame differs, that row is
        finished as ``render`` would finish it and every later row renders
        through ``_render_body``. ``ComponentNode._render_run_row`` names
        the difference in reads.
        """
        from citry.component_render import _attach_template_position, _render_body  # noqa: PLC0415

        call_node = cast("ComponentNode", self.branches[0][2][0])
        parts: list[RenderPart] = []
        run: _DeferredRun | None = None
        batching = True
        for body, body_context in self.iter_bodies(context):
            if not batching:
                parts.extend(_render_body(body, body_context))
                continue
            # _render_body's effects for this one-node body: the value
            # context, the trace line and the template position on an error.
            value_token = _VALUE_CONTEXT.set(body_context)
            try:
                if is_tracing():
                    trace_node_msg("RENDER", "ComponentNode", call_node.position)
                try:
                    row = call_node._render_run_row(body_context, run, run_class)
                except Exception as err:
                    _attach_template_position(err, call_node, body_context)
                    raise
            finally:
                _VALUE_CONTEXT.reset(value_token)
            if type(row) is DeferredComponent:
                # This row left the run; it and every later row render as
                # they do in a loop that is not a run, so the run keeps only
                # earlier rows.
                parts.append(row)
                batching = False
                continue
            kwargs, metadata, execution = cast(
                "tuple[dict[str, Any], _PreparedCallMetadata, DirectExecutionFrame | None]", row
            )
            if run is None:
                run = _DeferredRun(run_class, cast("Component", context.component), body_context.provides, execution)
            parts.append(_DeferredRunRow(run, len(run)))
            run.kwargs.append(kwargs)
            run.metadata.append(metadata)
        return parts

    def _build_walk_plan(self) -> tuple[Any, tuple[str, ...]] | str:
        """
        Return this loop's Rust walk plan and the scope names its inputs read, or why there is none.

        Called once per node, for a loop ``_call_run_class`` accepted. The
        plan exists only when the loop is ``<target> in <plain path>``, the
        key and every input are plain paths (a name and constant subscripts;
        see ``citry._vue.native_walk``), and each input's ``used_vars`` is
        exactly its path's name, so ``_kwarg_is_const``, which decides
        constness from ``used_vars``, looks at exactly the name the path
        reads. Any error while the plan is built means no plan, so the
        error, if it matters, is raised by Python's walk.
        """
        try:
            return self._lower_walk_plan()
        except Exception:  # noqa: BLE001 - no plan; Python's walk raises whatever the loop raises
            return "no_plan_error"

    def _lower_walk_plan(self) -> tuple[Any, tuple[str, ...]] | str:
        """Build the plan for ``_build_walk_plan``, or return why there is none."""
        native = _native_render.native
        # Plans follow SUPPORTED, never ACTIVE, so a Python-path render cannot
        # cache "no plan" for a later render on the native path.
        if native is None:
            return "no_plan_unsupported"
        for_branch = self.branches[0]
        call_node = cast("ComponentNode", for_branch[2][0])
        each_attr = _find_attr(for_branch[1], "each")
        if type(each_attr) is not ExprHtmlAttr or not isinstance(each_attr.expr, str):
            return "no_plan_loop"
        loop = _native_walk.lower_loop(for_branch[3], each_attr.expr)
        if loop is None:
            return "no_plan_loop"
        target, iterable = loop
        key_attr = call_node.key
        if type(key_attr) is not ExprHtmlAttr or not isinstance(key_attr.expr, str):
            return "no_plan_key"
        key = _native_walk.lower_path(key_attr.expr)
        if key is None:
            return "no_plan_key"
        # An input holding Vue code raises in _resolve_inputs; that error is Python's walk's to raise.
        if call_node._vue_code_attr_key is not None:
            return "no_plan_input"
        paths: list[tuple[str, tuple[str | int, ...]]] = []
        names: list[str] = []
        for attr in call_node.attrs:
            # Only expression inputs can be walked: a static input is always
            # constant, which Rust does not mark, and other kinds are not paths.
            if type(attr) is not ExprHtmlAttr or not isinstance(attr.expr, str):
                return "no_plan_input"
            path = _native_walk.lower_path(attr.expr)
            if path is None or tuple(attr.used_vars) != (path[0],):
                return "no_plan_input"
            paths.append(path)
            names.append(attr.key.removeprefix("c-"))
        plan = native._CallRunWalkPlan(
            target,
            iterable,
            paths,
            key,
            names,
            call_node.name,
            call_node.source,
            call_node.position,
            _PreparedCallMetadata,
            _ConstMapping,
            _ConstProxy,
        )
        # An input that reads a scope name is constant when that name is, so
        # the walk declines then. One that reads the loop variable never is:
        # _overlay_const_mapping clears the loop variable's constant mark,
        # and a row whose item is a marker, which would set it, declines.
        scope_roots = tuple(dict.fromkeys(path[0] for path in paths if path[0] != target))
        return plan, scope_roots

    def _walk_call_run(self, context: CitryContext, run_class: type[Component]) -> list[RenderPart] | str:
        """
        Walk this call run's loop in Rust, or return why Python's walk must run it.

        A call run is the rows one ``<c-for>`` places at one component call
        site. Rust (``native_render._CallRunWalkPlan``) reads every row
        first, running no template or user code (a dict lookup can run a
        colliding key's ``__eq__``, as Python's read does), then looks each
        row's class up with the registry's ``get``, as
        ``ComponentNode._render_run_row`` does per row, and builds each row's kwargs dict and call metadata.
        The result is the parts ``_render_call_run`` would return: one
        ``_DeferredRunRow`` per row of one ``_DeferredRun``.

        It returns a reason instead, and ``render`` runs ``_render_call_run``
        from the start, when the loop has no plan; when tracing is on (the
        trace lines are Python's); when the variables are not exactly
        ``_ConstMapping``; when an input would be marked constant, which Rust
        does not do; when the engine's ``get`` is not Citry's own; or when
        Rust meets a value or failure it does not read
        as Python would. ``docs/design/native_render.md`` lists the reasons.

        Two of ``_render_body``'s per-row effects are not made: the value
        context (``_VALUE_CONTEXT``) is not set per row, because nothing that
        runs during the walk reads it, and the template position is never
        needed, because a failing read declines. ``active_execution()`` and
        ``component.citry.get`` are read once per walk; reading them for each
        row would give another answer only for a ``Citry`` subclass or a
        class with a custom attribute lookup.
        """
        plan = self._walk_plan
        if plan is None:
            plan = self._walk_plan = self._build_walk_plan()
        if type(plan) is str:
            return plan
        if is_tracing():
            return "tracing"
        variables = context.variables
        # Python's walk copies the scope for each row. A _ConstMapping copy
        # reuses the stored hashes; any other mapping would have Python run
        # each non-str key's __hash__ once per row, which Rust never does. Checked
        # before the binding check, so a user mapping's __contains__ runs
        # only in Python's walk.
        if type(variables) is not _ConstMapping:
            return "scope"
        # The loop's binding check runs first, as in iter_bodies.
        _validate_introduced_variables("c-for", self.branches[0][3], context)
        walk_plan, scope_roots = cast("tuple[Any, tuple[str, ...]]", plan)
        for name in scope_roots:
            if _mapping_value_is_const(variables, name):
                return "const_input"
        component = cast("Component", context.component)
        # The registry lookup only returns each row's class, so when Rust
        # calls it, after every read, does not change what the loop renders.
        get = component.citry.get
        origin = context.template_record.origin if context.template_record is not None else None
        result = walk_plan.walk(variables, get, run_class, origin)
        if type(result) is str:
            return cast("str", result)
        kwargs, metadata = cast("tuple[list[dict[str, Any]], list[_PreparedCallMetadata]]", result)
        if not kwargs:
            return []
        from citry._vue.direct import active_execution  # noqa: PLC0415 - citry._vue.direct imports this module

        run = _DeferredRun(run_class, component, context.provides, active_execution())
        run.kwargs = kwargs
        run.metadata = metadata
        # One object per row position, as _render_call_run places them.
        return [_DeferredRunRow(run, index) for index in range(len(kwargs))]

    @override
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:
        """
        In a fill group, a ``<c-for>`` contributes its fills once per iteration.

        Each iteration's fills close over that iteration's loop bindings, so a
        fill body using the loop variable keeps the right value no matter when
        the child invokes it.
        """
        for body, body_context in self.iter_bodies(context):
            collect_fills_from_body(body, body_context, sink)

    def __repr__(self) -> str:
        return f"ForNode(branches={len(self.branches)})"


@final
class SlotNode(Node):
    """
    A slot definition (``<c-slot>``): the insertion point for slot content.

    Generated as::

        SlotNode(
            source, (start, end), (attrs,), [body],
            (used_vars,), (introduced_vars,),
        )

    Example:
        Template ``<c-slot name="header" />`` produces::

            SlotNode(source, (0, 24,), (StaticHtmlAttr(...),), [], (), ())

    Rendering resolves the slot name, looks up the fill the component
    received, and invokes it with the slot data; with no fill, the slot's own
    body renders as the fallback.

    """

    def __init__(
        self,
        source: Any,
        position: tuple[int, int],
        attrs: tuple[HtmlAttr, ...],
        body: list[BodyItem],
        used_vars: tuple[str, ...],
        introduced_vars: tuple[str, ...],
    ) -> None:
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.introduced_vars = introduced_vars

    @override
    def render(self, context: CitryContext) -> RenderPart:
        """
        Render the fill given for this slot, or the slot's own body as fallback.

        The slot data (the tag's extra attributes) resolves against the current
        context per render of this site, so a slot inside a loop passes
        per-iteration data. The fill and the fallback render through the same
        path: both are Slots, invoked with ``(data, fallback)``. A fill renders
        against the scope where it was written (it closed over it at
        collection); the fallback body renders against the current context, as
        if the ``<c-slot>`` tags were not there.

        A required slot with no fill raises, with a "did you mean" hint over
        the fills the component received.
        """
        component = context.component
        if component is None:
            msg = "SlotNode.render requires a component context bound to a Citry instance."
            raise RuntimeError(msg)

        if context._simple_scope is not None:
            from citry._simple_runtime import render_simple_outlet  # noqa: PLC0415

            if self.attrs or self.body or self.introduced_vars:
                raise TypeError("A simple template supports only an empty default slot outlet.")
            return render_simple_outlet(context)

        name, required, data = self._resolve_props(context)
        fills = component.raw_slots
        fill = fills.get(name)

        # No fill passed: fall back to a default on the typed `Slots` field, used
        # as the slot's fill (docs/design/component_slots.md section 9.5). `getattr` returns
        # that default here because the caller passed nothing for `name`; a `None`
        # default (or a dynamic name that is not a field) yields no fill, so the
        # in-template body below stays the fallback and a required slot still
        # raises. A passed fill always wins over the default.
        if fill is None and type(component).Slots is not None:
            default = getattr(component.slots, name, None)
            if default is not None:
                fill = normalize_slot_fills({name: default}, component_name=type(component).__name__).get(name)

        # Trace the slot render. All args are cheap, so call directly; the
        # helper itself skips the work when TRACE is off.
        trace_component_msg(
            "RENDER_SLOT",
            type(component).__name__,
            component.id,
            slot_name=name,
            slot_fills=fills,
        )

        from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

        if direct_prepared_render_active():
            return self._render_direct(context, component, name, required, data, fill)
        return self._render_plain(context, component, name, required, data, fill)

    def _render_plain(
        self,
        context: CitryContext,
        component: Any,
        name: str,
        required: bool,
        data: dict[str, Any],
        fill: Slot | None,
    ) -> RenderPart:
        """Render an ordinary HTML slot without client ownership bookkeeping."""
        body_slot = _make_body_slot(
            self.body,
            context,
            type(component).__name__,
            name,
            None,
            None,
            self.position,
            source=self.source,
            kind=LogicalFillKind.FALLBACK,
        )
        if fill is None and required:
            raise RuntimeError(_missing_required_slot_message(component, name))
        slot_used = fill if fill is not None else body_slot
        with add_slot_to_error_message(type(component).__name__, name):
            part = _render_slot_value(slot_used, data, body_slot if fill is not None else None, context)
        if not component.citry.extensions.has_hook("on_slot_rendered"):
            return part
        # Text or HTML a hook returns comes back as a render of its own, so a
        # plain str stays text (the manager applies the {{ ... }} rule).
        return component.citry.extensions.on_slot_rendered(
            component=component,
            slot=slot_used,
            slot_name=name,
            slot_node=self,
            slot_is_required=required,
            result=part,
            context=context,
        )

    def _render_direct(
        self,
        context: CitryContext,
        component: Any,
        name: str,
        required: bool,
        data: dict[str, Any],
        fill: Slot | None,
    ) -> RenderPart:
        """Render one prepared outlet and retain only its selected direct relation."""
        from citry._vue.direct import (  # noqa: PLC0415
            DirectSlotRender,
            begin_slot_execution,
            direct_execution_scope,
            direct_fill_source,
            wrap_slot_result,
        )

        body_slot = _make_body_slot(
            self.body,
            context,
            type(component).__name__,
            name,
            None,
            None,
            self.position,
            source=self.source,
            kind=LogicalFillKind.FALLBACK,
        )
        if fill is None and required:
            raise RuntimeError(_missing_required_slot_message(component, name))
        slot_used = fill if fill is not None else body_slot
        source = direct_fill_source(slot_used)
        if source is None:
            # A Python-provided Slot has no authored fill relation of its own,
            # but components rendered by that Slot can contain authenticated
            # template fills. Keep direct capture active for those descendants;
            # _render_plain does not manufacture a relation for this outlet.
            return self._render_plain(context, component, name, required, data, fill)
        execution = begin_slot_execution(
            source,
            public_name=name,
            receiver_render_id=component.id,
            source=self.source,
            span=self.position,
        )
        with direct_execution_scope(execution), add_slot_to_error_message(type(component).__name__, name):
            part = _render_slot_value(slot_used, data, body_slot if fill is not None else None, context)
            if not component.citry.extensions.has_hook("on_slot_rendered"):
                return part
            hook_result = part.selected if isinstance(part, DirectSlotRender) else part
            selected = component.citry.extensions.on_slot_rendered(
                component=component,
                slot=slot_used,
                slot_name=name,
                slot_node=self,
                slot_is_required=required,
                result=hook_result,
                # Text or HTML a hook returns comes back as a render of its
                # own, which a direct slot needs for its fill.
                context=context,
            )
            selected_source = source
            if isinstance(selected, DirectSlotRender):
                selected_source = selected.fill_source
                selected = selected.selected
            return wrap_slot_result(
                selected,
                fill_source=selected_source,
                public_name=name,
                receiver_render_id=component.id,
                source=self.source,
                span=self.position,
                execution=execution,
            )

    def _resolve_props(self, context: CitryContext) -> tuple[str, bool, dict[str, Any]]:
        """
        Resolve the slot's attributes to ``(name, required, data)``.

        Attributes are applied left to right, so the rightmost write wins:
        ``name``/``required`` are static, ``c-name``/``c-required`` are
        evaluated, and ``c-bind`` spreads a mapping (its ``name`` and
        ``required`` keys land on the slot; everything else is slot data).
        Every remaining attribute is slot data, with the ``c-`` prefix dropped
        from evaluated keys, the same rule as component kwargs.
        """
        name: Any = "default"
        required: Any = False
        data: dict[str, Any] = {}
        for attr in self.attrs:
            key = attr.key
            if key == "c-bind":
                spread = const_value(attr.resolve(context))
                if spread is None:
                    continue
                if not isinstance(spread, Mapping):
                    msg = f"'c-bind' on <c-slot> must resolve to a mapping, got {type(spread).__name__}."
                    raise RuntimeError(msg)
                for spread_key, spread_value in spread.items():
                    if not isinstance(spread_key, str):
                        msg = (
                            "'c-bind' on <c-slot> must use string keys, "
                            f"got {type(spread_key).__name__} key {spread_key!r}."
                        )
                        raise TypeError(msg)
                    _reject_dynamic_translation_binding(spread_key, tag_name="c-slot")
                    # The parser rejects authored Vue directives here; a spread
                    # key would otherwise become slot data the fill never uses.
                    unsupported = unsupported_slot_tag_directive_message(spread_key)
                    if unsupported is not None:
                        raise RuntimeError(unsupported)
                    if spread_key == "name":
                        name = spread_value
                    elif spread_key == "required":
                        required = spread_value
                    else:
                        data[spread_key] = spread_value
            elif key in ("name", "c-name"):
                name = attr.resolve(context)
            elif key in ("required", "c-required"):
                required = attr.resolve(context)
            else:
                data[key.removeprefix("c-")] = attr.resolve(context)

        if not isinstance(name, str) or not name:
            msg = f"<c-slot> 'name' must resolve to a non-empty string, got {name!r}."
            raise RuntimeError(msg)

        return name, bool(required), data

    def __repr__(self) -> str:
        return f"SlotNode(attrs={len(self.attrs)})"


@final
class FillNode(Node):
    """
    A slot fill (``<c-fill>``).

    Generated as::

        FillNode(
            source, (start, end), (attrs,), [body],
            (used_vars,), (introduced_vars,),
        )

    Example:
        The fill in ``<c-Card><c-fill name="header">content</c-fill></c-Card>``
        produces (positions are those of the fill tag on its own)::

            FillNode(
                source, (0, 38,),
                (StaticHtmlAttr(...),), ["content"], (), (),
            )

    A fill is consumed during fill collection (``collect_fills`` wraps its body
    as a ``Slot`` and registers it), so it is never rendered as output; it
    inherits ``Node.render`` raising, and reaching it would mean a
    parser/runtime bug.

    """

    def __init__(
        self,
        source: Any,
        position: tuple[int, int],
        attrs: tuple[HtmlAttr, ...],
        body: list[BodyItem],
        used_vars: tuple[str, ...],
        introduced_vars: tuple[str, ...],
    ) -> None:
        self.source = source
        self.position = position
        self.attrs = attrs
        self.body = body
        self.used_vars = used_vars
        self.introduced_vars = introduced_vars

    @override
    def collect_fills(self, context: CitryContext, sink: FillSink) -> None:
        """
        Resolve this fill's attributes and register its body as a ``Slot``.

        The Slot closes over ``context``, the scope where the fill was written
        (including any loop bindings from an enclosing ``<c-for>``); the body
        stays unrendered until the child component invokes the slot.
        """
        name, data_binding, fallback_var = self._resolve_props(context)
        data_targets = data_binding.targets if isinstance(data_binding, FillDataBinding) else (data_binding,)
        bindings = tuple(var for var in (*data_targets, fallback_var) if var is not None)
        _validate_introduced_variables("c-fill", bindings, context)
        slot = _make_body_slot(
            self.body,
            context,
            sink.component_name,
            name,
            data_binding,
            fallback_var,
            self.position,
            source=self.source,
            kind=LogicalFillKind.NAMED,
        )
        sink.add(name, slot)

    def _resolve_props(
        self,
        context: CitryContext,
    ) -> tuple[str, str | FillDataBinding | None, str | None]:
        """
        Resolve the fill's attributes to ``(slot_name, data_var, fallback_var)``.

        Attributes are applied left to right, so the rightmost write wins
        (matching the parser's identity rules): ``name`` and ``data``/
        ``fallback`` are static values, ``c-name`` is evaluated, and ``c-bind``
        spreads a mapping whose recognized keys are ``name``, ``data``, and
        ``fallback``.
        """
        props: dict[str, Any] = {}
        for attr in self.attrs:
            key = attr.key
            if key == "c-bind":
                spread = const_value(attr.resolve(context))
                if spread is None:
                    continue
                if not isinstance(spread, Mapping):
                    msg = f"'c-bind' on <c-fill> must resolve to a mapping, got {type(spread).__name__}."
                    raise RuntimeError(msg)
                for spread_key, spread_value in spread.items():
                    if not isinstance(spread_key, str):
                        msg = (
                            "'c-bind' on <c-fill> must use string keys, "
                            f"got {type(spread_key).__name__} key {spread_key!r}."
                        )
                        raise TypeError(msg)
                    _reject_dynamic_translation_binding(spread_key, tag_name="c-fill")
                    if spread_key not in ("name", "data", "fallback"):
                        msg = (
                            f"'c-bind' on <c-fill> got an unsupported key {spread_key!r}. "
                            "Allowed keys: 'name', 'data', 'fallback'."
                        )
                        raise RuntimeError(msg)
                    if spread_key == "data" and isinstance(spread_value, FillDataBinding):
                        msg = (
                            "<c-fill> data destructuring must be written directly in the template; "
                            "it cannot be supplied dynamically through 'c-bind'."
                        )
                        raise RuntimeError(msg)
                    props[spread_key] = spread_value
            elif key == "c-name":
                props["name"] = attr.resolve(context)
            else:
                # The parser only lets "name", "data", and "fallback" through.
                props[key] = attr.resolve(context)

        name = props.get("name")
        if not isinstance(name, str) or not name:
            msg = f"<c-fill> 'name' must resolve to a non-empty string, got {name!r}."
            raise RuntimeError(msg)

        data_var = props.get("data")
        fallback_var = props.get("fallback")
        if isinstance(data_var, str) and data_var.lstrip().startswith("{"):
            msg = (
                "<c-fill> data destructuring must be written directly in the template; "
                "it cannot be supplied dynamically through 'c-bind'."
            )
            raise RuntimeError(msg)
        for label, var in (("data", data_var), ("fallback", fallback_var)):
            if label == "data" and isinstance(var, FillDataBinding):
                continue
            canonical_var = normalize("NFKC", var) if isinstance(var, str) else var
            if canonical_var is not None and (
                not isinstance(canonical_var, str) or not canonical_var.isidentifier() or iskeyword(canonical_var)
            ):
                msg = f"<c-fill> {label!r} must be a valid Python identifier, got {var!r}."
                raise RuntimeError(msg)
            if label == "data":
                data_var = canonical_var
            else:
                fallback_var = canonical_var
        data_targets = data_var.targets if isinstance(data_var, FillDataBinding) else (data_var,)
        if fallback_var is not None and fallback_var in data_targets:
            msg = f"<c-fill name=\"{name}\"> binds 'data' and 'fallback' to the same variable {fallback_var!r}."
            raise RuntimeError(msg)

        return name, data_var, fallback_var

    def __repr__(self) -> str:
        return f"FillNode(attrs={len(self.attrs)})"
