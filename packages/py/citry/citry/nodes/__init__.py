"""
Stub runtime node classes for the Citry template compiler output.

The V3 compiler generates Python source code that instantiates these classes.
Each class accepts the exact arguments the compiler emits and stores them as
attributes.

The value nodes ``ExprNode`` and ``TemplateNode`` render against a
``CitryContext`` (see docs/design/component_rendering.md), and the attribute nodes
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
        from citry_core.template_parser.nodes import (
            ExprNode, ElementKeyNode, ComponentNode, IfNode, ForNode,
            SlotNode, FillNode, StaticHtmlAttr, ExprHtmlAttr,
            TemplateHtmlAttr, TemplateNode,
        )

        source = '<c-Card title="Hi">{{ body }}</c-Card>'
        t = parse_template(source)
        code = compile_template(t)

        ns = {
            "source": source,
            "ExprNode": ExprNode,
            "ElementKeyNode": ElementKeyNode,
            "TemplateNode": TemplateNode,
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

from collections.abc import Mapping
from dataclasses import dataclass
from difflib import get_close_matches
from keyword import iskeyword
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast, final
from unicodedata import normalize

from typing_extensions import Unpack, override

from citry.attrs import format_attrs, merge_attrs, validate_html_attr_name
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement, _ElementMorphMetadata
from citry.citry_render import (
    CitryRender,
    DeferredComponent,
    PhysicalRegionPart,
    PhysicalRegionRender,
    _render_value,
    unwrap_physical_region,
)
from citry.client_directives import (
    CLIENT_PROPS_ATTR,
    ComponentTagClientBindingKind,
    ComponentTagClientBindingSource,
    apply_client_props_contribution,
    classify_component_tag_client_binding_key,
    has_client_props_key,
    is_client_props_key,
    resolve_component_tag_client_binding_value,
)
from citry.constness import Const, const_value, is_const
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    ComponentTagClientBindingPayload,
    ComponentTagClientBindingRecord,
    LogicalFillKind,
    PropsClientBindingPayload,
    SourceLocationKind,
    current_ownership_graph,
    resume_ownership_graph,
)
from citry.slots import Slot, SlotData, normalize_slot_fills
from citry.util.exception import add_slot_to_error_message
from citry.util.html import escape
from citry.util.logger import trace_component_msg
from citry_core.safe_eval import compile_expr

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from citry.citry_render import RenderPart
    from citry.ext.events.extension import EventsExtension


_EVENTS_COMPILER_ATTR_PREFIX = "data-cev-"


def _reject_dynamic_events_compiler_attr(name: str, *, tag_name: str) -> None:
    """Keep render-time attributes out of the Events compiler-owned namespace."""
    if name.lower().startswith(_EVENTS_COMPILER_ATTR_PREFIX):
        msg = (
            f"{name!r} arrived on <{tag_name}> through an attribute spread or a dynamic attribute. "
            "'data-cev-*' attributes are compiler-owned; author State bindings with ':c-*' "
            "and event bindings with '@c-*' instead."
        )
        raise RuntimeError(msg)


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


def collect_fills_from_body(body: list[BodyItem], context: CitryContext, sink: FillSink) -> None:
    """
    Walk one level of a fill-group body, collecting fills into ``sink``.

    Whitespace strings between fills are formatting only: neither captured
    into a slot nor rendered. Non-whitespace text is rejected (when a
    component body contains ``<c-fill>`` tags, all other content must be
    inside the fills). Each node dispatches through its own
    ``collect_fills``, so what a node contributes (a fill, a taken branch,
    one pass per loop iteration, or an error) is the node's own business.

    The parser already rejects most content beside fills; the checks on this
    path are the runtime half of that contract (dynamic fill names make some
    shapes undecidable statically), so the errors mirror the parser's.
    """
    for item in body:
        if isinstance(item, str):
            if item.strip():
                msg = (
                    f"Text cannot appear next to '<c-fill>' tags in the body of "
                    f"<c-{sink.component_name}>. All other content must be inside the fills."
                )
                raise RuntimeError(msg)
        else:
            item.collect_fills(context, sink)


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
    fallback_slot_site_location_id: Any = None,
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
    # Imported lazily: component_render imports the node classes, so importing
    # the body walker at module load would be circular.
    from citry.component_render import _render_body  # noqa: PLC0415

    slot: Slot

    def content_func(ctx: Any) -> CitryRender:
        def render_content() -> CitryRender:
            provides = context.provides
            if ctx.provides is not None and ctx.provides is not provides:
                provides = {**provides, **ctx.provides} if provides else ctx.provides

            if data_binding is not None or fallback_var is not None or provides is not context.provides:
                overlay = _bind_fill_data(
                    data_binding,
                    ctx.data,
                    component_name=component_name,
                    slot_name=slot_name,
                )
                if fallback_var is not None:
                    overlay[fallback_var] = ctx.fallback
                render_context = CitryContext(
                    variables={**context.variables, **overlay},
                    extra=context.extra,
                    component=context.component,
                    provides=provides,
                    sandboxed=context.sandboxed,
                    ownership=context.ownership,
                )
            else:
                render_context = context
            return CitryRender(parts=_render_body(body, render_context), context=render_context)

        # A stored template Slot may be invoked after its root render has
        # returned. Resume capture into its original graph without putting a
        # logical fill ID on the reusable Slot object itself.
        graph = context.ownership
        if graph is not None and current_ownership_graph() is None:
            with resume_ownership_graph(graph):
                return graph.capture_slot_call(slot, render_content)
        return render_content()

    slot = Slot(
        body,
        content_func=content_func,
        component_name=component_name,
        slot_name=slot_name,
        source_position=position,
    )
    if context.ownership is not None and position is not None:
        context.ownership.record_template_fill(
            slot,
            context,
            kind=kind,
            slot_name=slot_name,
            source=source,
            position=position,
            fallback_slot_site_location_id=fallback_slot_site_location_id,
        )
    return slot


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
    part = unwrap_physical_region(part)
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
            nested_child = unwrap_physical_region(child)
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
        if isinstance(current, (PhysicalRegionPart, PhysicalRegionRender)):
            pending.append(current.part)
        elif isinstance(current, CitryRender):
            pending.extend(current.parts)
    return object_ids


@final
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
        Called by ``render``, and by the ``Const`` optimization
        (``citry/constness.py``), which evaluates an expression ahead of time
        when all of its variables are marked constant.
        """
        if self._eval is None:
            self._eval = compile_expr(self.expr, sandboxed=sandboxed)
        return self._eval(variables)

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
class TemplateNode(Node):
    """
    A nested template value on an HTML tag's dynamic attribute.

    Emitted when a ``c-*`` attribute value is itself a template (starts with a
    tag and ends with a closing tag), as opposed to a plain expression (which
    becomes an ``ExprNode``). The ``expr`` field holds the nested template
    source string.

    Generated as: ``TemplateNode(source, (start, end), "template", ("var1", ...))``

    Example:
        Template ``<div c-body="<span>{{ x }}</span>">`` compiles the
        ``c-body`` value to::

            TemplateNode(source, (13, 33,), "<span>{{ x }}</span>", ("x",))

    """

    def __init__(self, source: Any, position: tuple[int, int], expr: str, used_vars: tuple[str, ...]) -> None:
        self.source = source
        self.position = position
        # `expr` is the nested template SOURCE STRING (for example
        # "<span>{{ x }}</span>"), not a Python expression.
        self.expr = expr
        self.used_vars = used_vars
        # The body-generating function for the nested template, compiled lazily
        # on first render and reused afterwards (compile once per node).
        self._generator: Callable[[], list[Any]] | None = None

    @override
    def render(self, context: CitryContext) -> CitryRender:
        # A nested template is not a component boundary: it shares the
        # surrounding component's context, so it renders against the same
        # variables and writes any dependencies into the same context.
        #
        # Imported lazily because component_render imports the node classes:
        # importing the body pipeline at module load would be circular.
        from citry.component_render import _compile_nested_template, _render_body  # noqa: PLC0415

        if self._generator is None:
            # The nested template is validated like any other: the parse gets
            # the rules derived from the registered components' declarations.
            component = context.component
            user_rules = component.citry._tag_rules() if component is not None else None
            self._generator = _compile_nested_template(
                self.expr,
                user_rules,
                type(component) if component is not None else None,
            )
        parts = _render_body(self._generator(), context)
        return CitryRender(parts=parts, context=context)

    def __repr__(self) -> str:
        return f"TemplateNode(position={self.position}, expr={self.expr!r})"


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
        only the component-input use benefits from the marker. So the marking
        happens in ``ComponentNode._resolve_inputs``, where the value becomes
        a component input, not here.
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
        written in the template), ``ComponentNode._resolve_inputs`` adds the
        marker where the value becomes a component input.
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

    Generated as: ``TemplateHtmlAttr(source, (start, end), "c-body", "<div>...</div>", ("var",))``

    Example:
        Template ``<c-Card c-body="<span>{{ x }}</span>" />`` produces::

            TemplateHtmlAttr(source, (8, 37,), "c-body", "<span>{{ x }}</span>", ("x",))

    """

    def __init__(
        self, source: Any, position: tuple[int, int], key: str, template: str, used_vars: tuple[str, ...]
    ) -> None:
        self.source = source
        self.position = position
        self.key = key
        self.template = template
        self.used_vars = used_vars
        # The body-generating function for the nested template, compiled lazily
        # on first resolve and reused afterwards (compile once per node).
        self._generator: Callable[[], list[Any]] | None = None

    @override
    def resolve(self, context: CitryContext) -> CitryRender:
        """
        Render the nested template and return it as a ``CitryRender`` kwarg value.

        The template is defined in the parent's scope, so it renders against the
        surrounding component's context (the same rule as ``TemplateNode``).
        """
        from citry.component_render import _compile_nested_template, _render_body  # noqa: PLC0415

        if self._generator is None:
            # The nested template is validated like any other: the parse gets
            # the rules derived from the registered components' declarations.
            component = context.component
            user_rules = component.citry._tag_rules() if component is not None else None
            self._generator = _compile_nested_template(
                self.template,
                user_rules,
                type(component) if component is not None else None,
            )
        parts = _render_body(self._generator(), context)
        return CitryRender(parts=parts, context=context)

    def __repr__(self) -> str:
        return f"TemplateHtmlAttr(key={self.key!r})"


@final
class ElementAttrsNode(Node):
    """
    The attribute region of a plain HTML start tag with dynamic attributes.

    Generated as: ``ElementAttrsNode(source, (start, end), (attrs...), ("var1", ...))``

    Emitted when an HTML element (not a component) has at least one dynamic
    attribute—a ``c-*`` value or a ``c-bind`` spread—or a literal extension
    binding/output name that must remain structurally visible. The node covers
    ALL of the tag's attributes, static ones included, because the set resolves
    as one unit:

    - Contributions collect left to right in source order; ``c-bind``
      contributes each entry of its mapping (which must be a ``Mapping``).
    - ``class`` and ``style`` merge across contributions and accept the
      structured value forms (string / dict / nested list); every other key
      resolves last-one-wins.
    - ``True`` renders the bare attribute, ``False`` and ``None`` omit it,
      everything else renders escaped (``__html__`` values pass through).

    Renders to one string like ``' class="btn" disabled'`` (leading space
    included) or ``""`` when every attribute resolved away.

    An ``on_template_compiled`` extension may consume parser-proven literal
    attributes and collapse an otherwise-static region back to a string before
    this node reaches rendering. Events uses that path for ``@c-*`` / ``:c-*``.

    Example:
        Template ``<div id="x" c-class="cls">hi</div>`` produces::

            ElementAttrsNode(source, (0, 26,), (StaticHtmlAttr(...), ExprHtmlAttr(...),), ("cls",))

    """

    def __init__(
        self, source: Any, position: tuple[int, int], attrs: tuple[HtmlAttr, ...], used_vars: tuple[str, ...]
    ) -> None:
        self.source = source
        self.position = position
        self.attrs = attrs
        self.used_vars = used_vars
        # The tag name, read lazily from the template source on first use
        # (the compiler emits the tag name as a separate static chunk, so the
        # node itself does not receive it).
        self._tag_name: str | None = None

    @property
    def tag_name(self) -> str:
        """The element's tag name (e.g. ``"div"``), read from the source slice."""
        if self._tag_name is None:
            # The position spans the start tag, e.g. `<div c-class="cls">`.
            name = str(self.source)[self.position[0] + 1 : self.position[1]]
            for index, char in enumerate(name):
                if char.isspace() or char in "/>":
                    name = name[:index]
                    break
            self._tag_name = name
        return self._tag_name

    @override
    def render(self, context: CitryContext) -> RenderPart:
        resolved = self._resolve(context)

        # Let extensions rewrite the resolved dict (e.g. class dedup). Fires
        # only when an installed extension implements the hook; the manager
        # short-cuts otherwise (docs/design/template_html_attrs.md section 5.5).
        component = context.component
        if component is not None:
            resolved = component.citry.extensions.on_attrs_resolved(
                component=component,
                tag_name=self.tag_name,
                attrs=resolved,
            )
            if has_client_props_key(resolved, tag_name=self.tag_name):
                apply_client_props_contribution(
                    resolved,
                    resolved[CLIENT_PROPS_ATTR],
                    tag_name=self.tag_name,
                    component_boundary=False,
                )

        return self._format(resolved, context)

    def _resolve(self, context: CitryContext) -> dict[str, Any]:
        """
        Collect the attribute contributions and merge them into one dict.

        ``False`` and ``None`` values are dropped here, so the merged dict
        holds only the attributes that will appear in the output (the
        ``on_attrs_resolved`` hook sees them already gone). A ``Const``
        marker is unwrapped so the normalizers see the real value.
        """
        contributions: list[Mapping[str, Any]] = []
        for attr in self.attrs:
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
                contribution: dict[str, Any] = {}
                for key, item in value.items():
                    resolved_key = validate_html_attr_name(key, where=f"c-bind on <{self.tag_name}>")
                    _reject_dynamic_events_compiler_attr(resolved_key, tag_name=self.tag_name)
                    contribution[resolved_key] = const_value(item)
                contributions.append(contribution)
            else:
                resolved_key = attr.key.removeprefix("c-")
                if attr.key.startswith("c-"):
                    _reject_dynamic_events_compiler_attr(resolved_key, tag_name=self.tag_name)
                contributions.append({resolved_key: const_value(attr.resolve(context))})
        merged = merge_attrs(*contributions)
        # `#c-*` framework attributes (`#c-key`, `#c-ignore`) are
        # template-authored only in v1: authored on the tag, the compiler
        # handles them before this node exists, so one arriving here came
        # through a spread or a dynamic attribute name and would render as a
        # meaningless literal attribute. Fail loudly, naming the fix.
        for merged_key in merged:
            if merged_key.startswith("#c-"):
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

    def _format(self, resolved: Mapping[str, Any], context: CitryContext) -> RenderPart:
        """Format the merged dict into the output part(s)."""
        for key in resolved:
            validate_html_attr_name(key, where=f"attributes resolved for <{self.tag_name}>")

        # Common case: no attribute value is a nested-template render, so the
        # whole dict formats in a single pass. Doing it per key (the mixed-case
        # path below) would escape, join, and concatenate once per attribute,
        # which is the dominant per-element cost on a big page.
        if not any(isinstance(value, CitryRender) for value in resolved.values()):
            chunk = format_attrs(resolved)
            return (" " + chunk) if chunk else ""

        # Mixed: a nested-template value (`c-foo="<div>...</div>"`) keeps its
        # parts so components inside it stay deferred and render through the
        # queue. Format the runs of plain attributes around it in one call each.
        parts: list[RenderPart] = []
        plain: dict[str, Any] = {}

        def flush_plain() -> None:
            if plain:
                chunk = format_attrs(plain)
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
        return f' data-citry-key=":{escape(value)}"'

    def __repr__(self) -> str:
        return f"ElementKeyNode(expr={self.attr.expr!r}, used_vars={self.used_vars})"


def _kwarg_is_const(attr: HtmlAttr, context: CitryContext) -> bool:
    """
    Whether a resolved component-input value is the same on every render.

    A static attribute (``age="30"``) is always the same. An expression
    attribute (``c-age="..."``) is the same on every render when every variable
    it reads is itself constant. Two cases follow from that one rule:

    - An expression that reads no variables at all (``c-items="[1, 2]"``,
      ``c-age="30"``) is constant: nothing in it can change. (This is why
      ``all()`` of an empty list of variables is true.)
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
        return all(is_const(context.variables.get(name)) for name in attr.used_vars)
    return False


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
    client_bindings: tuple[ComponentTagClientBindingRecord, ...]


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

        ComponentNode(source, (start, end), (attrs,...), [body], (used_vars,), "name", contains_fills)

    Example:
        Template ``<c-Card title="Hi">body</c-Card>`` produces::

            ComponentNode(
                source, (0, 21,),
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
        self._metadata_locus: Literal["range", "element"] | None = None
        self.key: ExprHtmlAttr | None = None
        self.morph_mode: Literal["ignore"] | None = None

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
        slots = self._collect_slots(context)
        # The key expression evaluates once in the parent's scope. Exactly
        # None opts out; every other value, including falsey values, is a key.
        evaluated_key: str | None = None
        if self.key is not None:
            key_value = const_value(self.key.resolve(context))
            evaluated_key = None if key_value is None else str(key_value)
        range_morph_key = evaluated_key if self._metadata_locus == "range" else None
        range_morph_mode = self.morph_mode if self._metadata_locus == "range" else None
        element_morph_metadata = (
            _ElementMorphMetadata(key=evaluated_key, morph_mode=self.morph_mode)
            if self._metadata_locus == "element"
            else None
        )
        ownership = context.ownership
        if ownership is None:
            msg = "ComponentNode.render requires an active ownership graph."
            raise RuntimeError(msg)
        invocation_id = ownership.record_component_invocation(
            context,
            authored_tag=self.name,
            target_class_id=child_cls.class_id,
            morph_key=range_morph_key,
            morph_mode=range_morph_mode,
            source=self.source,
            position=self.position,
            client_bindings=resolved.client_bindings,
        )
        ownership.bind_template_fill_sources(slots, invocation_id)
        element = CitryElement(
            child_cls,
            resolved.kwargs,
            slots,
            component_tag_client_bindings=resolved.client_bindings,
            ownership_invocation_id=invocation_id,
            ownership_graph=ownership,
            element_morph_metadata=element_morph_metadata,
            forward_ownership_invocation=self.name == "component",
        )
        # The active provide/inject entries are captured now, like the kwargs:
        # the child renders later (through the queue), when this context is
        # gone, but must still inherit what was provided around its tag.
        return DeferredComponent(
            element,
            component,
            context.provides,
            physical_parent_region_id=ownership.current_region_id(),
        )

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
        (slot/fill names, provide keys) stay plain. The marker is applied fresh
        on each render, so a mutable literal (a list) is still a new object
        every render; equal values still land on the same cache entry.
        """
        kwargs: dict[str, Any] = {}
        element_attr_contributions: list[Mapping[str, Any]] = []
        pending_client_bindings: dict[str, _PendingComponentTagClientBinding] = {}
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
            if component_boundary and isinstance(resolved_key, str) and resolved_key.startswith(":c-"):
                msg = (
                    f"State binding {resolved_key!r} is not valid on the <{tag_name}> component boundary. "
                    "State bindings target HTML elements; pass data down through $c-props or Python kwargs."
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
            if not component_boundary:
                return False
            client_binding_kind = classify_component_tag_client_binding_key(resolved_key, tag_name=tag_name)
            if client_binding_kind is None:
                return False
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
                        _reject_dynamic_events_compiler_attr(resolved_bound_key, tag_name="c-element")
                    elif not isinstance(bound_key, str):
                        msg = (
                            f"c-bind on <c-{self.name}> must use string kwarg names, "
                            f"got {type(bound_key).__name__} key {bound_key!r}"
                        )
                        raise TypeError(msg)
                    else:
                        resolved_bound_key = bound_key
                    reject_component_state_binding(resolved_bound_key)
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
            reject_component_state_binding(resolved_key)
            client_binding_source = (
                ComponentTagClientBindingSource.SERVER_DYNAMIC
                if key.startswith("c-")
                else ComponentTagClientBindingSource.DIRECT
            )
            if not component_boundary and client_binding_source == ComponentTagClientBindingSource.SERVER_DYNAMIC:
                _reject_dynamic_events_compiler_attr(resolved_key, tag_name="c-element")
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
            if isinstance(kwarg_key, str) and kwarg_key.startswith("#c-"):
                msg = (
                    f"{kwarg_key!r} arrived on <c-{self.name}> through an attribute spread or a "
                    "dynamic attribute. '#c-*' framework attributes are template-authored only: "
                    "write the attribute directly on the component tag in the template."
                )
                raise RuntimeError(msg)
        ownership = context.ownership
        if ownership is None:
            msg = "Component input resolution requires an active ownership graph."
            raise RuntimeError(msg)
        client_bindings: list[ComponentTagClientBindingRecord] = []
        for pending in pending_client_bindings.values():
            source_location_id = ownership.record_source_location(
                context,
                kind=SourceLocationKind.COMPONENT_TAG_CLIENT_BINDING,
                source=pending.attr.source,
                position=pending.attr.position,
                mapping_key=pending.mapping_key,
                mapping_index=pending.mapping_index,
            )
            location = ownership.source_location(source_location_id)
            payload: ComponentTagClientBindingPayload
            if pending.kind == ComponentTagClientBindingKind.PROPS:
                payload = PropsClientBindingPayload(type="props", expression=pending.value)
            elif pending.kind == ComponentTagClientBindingKind.ALPINE_HANDLER:
                payload = AlpineHandlerClientBindingPayload(type="alpine-handler", expression=pending.value)
            else:
                # Import lazily: the core node model does not import the Events
                # extension while built-ins are still being constructed.
                from citry.ext.events.bindings import (  # noqa: PLC0415
                    DATA_CEV_ON,
                    compile_citry_boundary_binding,
                )

                events = cast("EventsExtension", component.citry.extensions.get_extension("events"))
                compiled = compile_citry_boundary_binding(
                    events.resolve(type(component)),
                    type(component).class_id,
                    type(component).__name__,
                    tag_name,
                    pending.key,
                    pending.value,
                    line=location.line,
                    column=location.column,
                )
                spec = compiled.spec
                if compiled.channel == DATA_CEV_ON:
                    payload = CitryDomEventClientBindingPayload(
                        type="citry-dom-event",
                        class_id=str(spec["cid"]),
                        event=str(spec["event"]),
                        handler=str(spec["handler"]),
                        args=spec["args"] if isinstance(spec["args"], str) else None,
                        prevent=bool(spec["prevent"]),
                        stop=bool(spec["stop"]),
                        self_=bool(spec["self"]),
                        once=bool(spec["once"]),
                        key=spec["key"] if isinstance(spec["key"], str) else None,
                        debounce=spec["debounce"] if isinstance(spec["debounce"], int) else None,
                        throttle=spec["throttle"] if isinstance(spec["throttle"], int) else None,
                    )
                else:
                    payload = CitryPollClientBindingPayload(
                        type="citry-poll",
                        class_id=str(spec["cid"]),
                        handler=str(spec["handler"]),
                        args=spec["args"] if isinstance(spec["args"], str) else None,
                        interval=int(spec["interval"]),
                    )
            client_bindings.append(
                ComponentTagClientBindingRecord(
                    key=pending.key,
                    payload=payload,
                    source=pending.source,
                    source_location_id=source_location_id,
                )
            )
        return _ResolvedComponentInputs(kwargs=kwargs, client_bindings=tuple(client_bindings))

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
            if all(isinstance(item, str) and not item.strip() for item in self.body):
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
        self._precomputed_text: str | None = None
        # The generator-expression evaluator for the `each` clause, compiled
        # lazily on first render and reused afterwards (the node is cached across
        # renders, so this compiles once).
        self._iter_eval: Callable[[Any], Any] | None = None

    def _with_precomputed_text(self, text: str) -> ForNode:
        """Return a fresh runtime guard for text produced by const unrolling."""
        node = ForNode(self.source, self.branches, self.used_vars)
        node._precomputed_text = text
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
                variables={**context.variables, **dict(zip(targets, values, strict=True))},
                extra=context.extra,
                component=context.component,
                provides=context.provides,
                sandboxed=context.sandboxed,
                ownership=context.ownership,
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

        if self._precomputed_text is not None:
            targets: tuple[str, ...] = self.branches[0][3]
            _validate_introduced_variables("c-for", targets, context)
            return CitryRender(parts=[self._precomputed_text], context=context)

        parts: list[RenderPart] = []
        for body, body_context in self.iter_bodies(context):
            parts.extend(_render_body(body, body_context))
        return CitryRender(parts=parts, context=context)

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

        SlotNode(source, (start, end), (attrs,), [body], (used_vars,), (introduced_vars,))

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

        ownership = context.ownership
        if ownership is None:
            msg = "SlotNode.render requires an active ownership graph."
            raise RuntimeError(msg)
        has_rendered_hook = component.citry.extensions.has_hook("on_slot_rendered")
        selection_checkpoint = ownership.checkpoint()

        with ownership.slot_site(context, source=self.source, position=self.position) as slot_site_location_id:
            # The slot's own body, as a Slot: the fallback handle when a fill
            # exists, the rendered content when none does.
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
                fallback_slot_site_location_id=slot_site_location_id,
            )

            if fill is not None:
                slot_used = fill
                fill_id = ownership.supplied_fill_id(component, name)
                if fill_id is None:
                    fill_id = ownership.bind_typed_default(component, name)
                # The provides active at this slot site travel into the fill, so
                # components inside the fill body can inject what this component
                # provides around the slot (docs/design/component_provide.md section 4.3).
                # An error raised by the slot content gets this slot as a path
                # frame ("Card(slot:body)") in its message.
                with ownership.select_supply(fill, fill_id):
                    with add_slot_to_error_message(type(component).__name__, name):
                        part = fill(data, fallback=body_slot, provides=context.provides)
            else:
                if required:
                    msg = (
                        f"Slot {name!r} of component {type(component).__name__!r} is marked as "
                        "required, but no fill was provided."
                    )
                    close = get_close_matches(name, list(fills), n=1, cutoff=0.7)
                    if close:
                        msg += f" Did you mean {close[0]!r}?"
                    raise RuntimeError(msg)
                slot_used = body_slot
                with add_slot_to_error_message(type(component).__name__, name):
                    part = body_slot(data, provides=context.provides)

        if not has_rendered_hook:
            return part

        result_checkpoint = ownership.checkpoint()
        outlet_region_id = ownership.resolve_slot_region(slot_site_location_id)
        try:
            with ownership.active_region(outlet_region_id):
                selected_part = component.citry.extensions.on_slot_rendered(
                    component=component,
                    slot=slot_used,
                    slot_name=name,
                    slot_node=self,
                    slot_is_required=required,
                    result=unwrap_physical_region(part),
                )
        except Exception:
            ownership.retire_unselected_after(
                result_checkpoint,
                through_order=ownership.checkpoint(),
                preserved_render_ids=set(),
            )
            raise
        hook_checkpoint = ownership.checkpoint()
        selected_part = ownership.rebind_slot_region(outlet_region_id, selected_part)
        selected_render_ids = _render_part_ids(selected_part)
        selected_region_ids = ownership.selected_region_ids(
            render_object_ids=_render_part_object_ids(selected_part),
        )
        ownership.retire_unselected_after(
            result_checkpoint,
            through_order=hook_checkpoint,
            preserved_render_ids=selected_render_ids,
            preserved_region_ids=selected_region_ids,
        )
        ownership.retire_unselected_after(
            selection_checkpoint,
            through_order=result_checkpoint,
            preserved_render_ids={component.id, *selected_render_ids},
            preserved_region_ids={outlet_region_id, *selected_region_ids},
        )
        return selected_part

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

        FillNode(source, (start, end), (attrs,), [body], (used_vars,), (introduced_vars,))

    Example:
        Template ``<c-fill name="header">content</c-fill>`` produces::

            FillNode(source, (0, 40,), (StaticHtmlAttr(...),), ["content"], (), ())

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
