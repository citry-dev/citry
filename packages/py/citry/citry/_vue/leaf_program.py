"""Reusable browser programs without statically compiled component or slot nodes."""

from __future__ import annotations

import abc
import ast
import math
import re
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast, overload

from citry.attrs import (
    _format_resolved_attrs_to_str,
    _has_default_attr_formatting,
    _html_attr_identity,
    format_attrs,
    merge_attrs,
    validate_html_attr_name,
)
from citry.citry_render import _VALUE_CONTEXT, CitryRender, RenderPart
from citry.constness import Const, _ConstMapping, const_value
from citry.ext.i18n.bindings import I18nBindingElementAttrsNode
from citry.nodes import (
    ComponentNode,
    ExprHtmlAttr,
    ForNode,
    IfNode,
    Node,
    StaticHtmlAttr,
    _merge_resolved_attrs,
    _reject_dynamic_translation_binding,
    _reject_reserved_events_attr,
    _validate_introduced_variables,
)
from citry.util import html as _html_module
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
    conflicting_attribute_targets,
    format_prepared_element_attrs,
    include_prepared_attribute,
    is_native_state_tag,
    is_vue_directive_name,
    prepared_spread_index,
    vue_owned_native_marker,
    vue_owned_native_properties,
    vue_render_active,
)
from .compiler import (
    _ElementBindingDeclaration,
    _generated_event_args,
    _generated_vue_attr,
    _RuntimeEventDeclaration,
)
from .json_data import _JS_SAFE_INTEGER, _vue_attribute_map, _vue_attribute_value

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from typing import Protocol, TypeAlias

    from citry.citry_context import CitryContext

    # A generated row HTML writer, called as (data, resolved_opens, row_html, row_marks).
    _RowHtmlWrite: TypeAlias = Callable[[dict[str, object], dict[Any, Any], list[str | None], list[int]], None]

    # The generated root evaluator. It takes the same arguments as ``_evaluate``
    # without the operations, and the context is None on the context-free path.
    _SimpleJsonEvaluate: TypeAlias = Callable[
        [
            CitryContext | None,
            dict[str, Any],
            dict[str, object],
            dict[str, object],
            list[str],
            dict[tuple[int, str], RenderPart],
            dict[tuple[int, int], PreparedElementOpen | dict[str, object] | "_SpreadResolvedOpen"],
        ],
        None,
    ]

    class _SimpleJsonPreflight(Protocol):
        """
        The generated check that every variable the template reads is a plain JSON value.

        It reads ``candidate_variables`` only when the context is None.
        """

        def __call__(
            self,
            context: CitryContext | None,
            candidate_variables: dict[str, Any] | None = None,
            /,
        ) -> bool: ...


# Names the shape of the Vue template this module writes into
# ``LeafProgramFragment.template``: the name the template reads its prepared
# data through, the data keys it reads, and the runtime helpers it calls. The
# render cache stores these templates, so it stamps each entry with a hash of
# this text and treats an entry written under different text as a miss rather
# than compiling an old template against the current runtime. Edit this text in
# the same change as any edit to the generated template. A test in
# test_ext_cache_typed_artifact.py locks this text beside one stored template, so
# it fails when either moves alone; the other clauses rely on this reminder.
LEAF_TEMPLATE_CONTRACT_DESCRIPTOR = (
    "leaf-template/1;data=$citryPrepared;"
    "text={{ $citryPrepared.citryText<n> }};attrs=v-bind=$citryPrepared.citryAttrs<n>;"
    "key=:key=$citryPrepared.citryKey<n>;"
    "if=template v-if/v-else-if $citryPrepared.citryIf<n> === <branch>;"
    "loop=template v-for $citryPrepared in $citryPrepared.citryLoop<n>,v-if length === 0;"
    "runtimeEvents=v-citry-runtime-events $citryEvents.runtimeEvents($citryPrepared.citryRuntimeEvents<n>);"
    "events=v-on:<event>.<modifiers> $citryEvents.dispatch('<id>', $event, (<args>));"
    "timing=v-citry-event-timing $citryEvents.timings('<ids>',[{id,args}]);"
    "controls=v-citry-control $citryEvents.controls($citryPrepared.citryControls<n>) or ('<ids>')"
)


@dataclass(frozen=True, slots=True)
class LeafProgramFragment:
    template: str
    element_bindings: tuple[dict[str, object], ...]
    browser_requirements: frozenset[str]
    safe_body: bool
    runtime_event_sites: tuple[dict[str, object], ...] = ()
    # The child component calls of a simple='vue' template, in source order.
    # ``template`` holds no element for them: the assembler writes each
    # child's component element at its offset, because the element's tag
    # comes from the serialization's tag mapping.
    calls: tuple[_Call, ...] = ()

    @property
    def calls_unconditional(self) -> bool:
        """Whether every occurrence of this template makes every call exactly once."""
        return all(call.unconditional for call in self.calls)


@dataclass(slots=True)
class LeafCallChildren:
    """
    The child components one ``simple='vue'`` occurrence calls, in the order its template makes the calls.

    The occurrence records each call's inputs while its template is
    evaluated. The render loop then renders each child the way it renders
    any other child component, and replaces the ``DeferredComponent`` in
    ``parts`` with the child's result, so the list ends up holding the
    rendered children.
    """

    parts: list[RenderPart]
    # (id of the data record the call was evaluated in, call key) -> index
    # in ``parts``. A call inside ``c-for`` is evaluated once per item, and
    # each item has its own data record.
    index: dict[tuple[int, str], int]
    # Class id of the child a keyed call that is the whole body of a c-for
    # names, by call key. An ordinary parent renders such a loop as one
    # browser loop over its children, and so does this one; the id is
    # known even when the loop is empty.
    run_types: dict[str, str] = field(default_factory=dict)

    def by_site(self) -> dict[tuple[int, str], RenderPart]:
        """Map each evaluated call site to its child's current part."""
        parts = self.parts
        return {site: parts[position] for site, position in self.index.items()}


@dataclass(frozen=True, slots=True)
class PreparedLeafProgram:
    """One evaluated occurrence of an immutable leaf program."""

    fragment: LeafProgramFragment
    prepared_data: dict[str, object]
    operations: tuple[object, ...]
    vue_errors: tuple[str, ...]
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen]
    cached_typed_parts: tuple[RenderPart, ...] | None = None
    cached_static_parts: tuple[str, ...] | None = None
    # For a simple='vue' occurrence, the compiled template's row HTML writer:
    # it takes prepared_data and resolved_opens and returns the row's HTML
    # cut where root markers go, or None. Evaluation only records values;
    # the HTML is written when serialize asks for row_html_segments, so a
    # full document, client-mounted or hydrated, never pays for it.
    row_html_writer: Callable[[dict[str, object], dict[Any, Any]], tuple[str, ...] | None] | None = None
    # True only when the generated simple JSON evaluator wrote every value in
    # prepared_data without a render context. Before it ran, a check confirmed
    # that every variable path the template reads (its read set) holds exact
    # JSON types, so assembly copies the data without converting it.
    prepared_data_evaluated_plain: bool = False
    # For a simple='vue' template that calls child components, the calls
    # this occurrence made. None when the template makes no calls.
    call_children: LeafCallChildren | None = None

    @property
    def row_html_segments(self) -> tuple[str, ...] | None:
        """
        Return this occurrence's HTML, cut at each root start tag's marker position.

        Serialize joins the pieces with the component's marker attributes
        instead of rebuilding and re-scanning the row. None means serialize
        must build the HTML from the recorded values itself. Each call writes
        the HTML again; serialize reads it once per row.
        """
        writer = self.row_html_writer
        if writer is None:
            return None
        return writer(self.prepared_data, self.resolved_opens)


@dataclass(slots=True)
class _SpreadResolvedOpen:
    """Retain one resolved spread for lazy typed fallback without resolving twice."""

    resolved: dict[str, object]
    context: CitryContext
    extension_validated: bool
    prepared: PreparedElementOpen | None = None


@dataclass(frozen=True, slots=True)
class PreparedStaticText:
    """Escaped dynamic text retained while serializing a static fallback."""

    text: str


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


@dataclass(frozen=True, slots=True)
class _Call:
    """A slot-free child component call inside an instance-free ``simple='vue'`` template."""

    node: ComponentNode
    # Where the evaluator records this call's inputs, per data record.
    key: str
    # Byte position in the fragment template where the child's component
    # element goes. Only calls outside c-if and c-for use it.
    offset: int
    # Tags of the elements open around the call, outermost first.
    element_stack: tuple[str, ...]
    # True when no c-if or c-for encloses the call, so every occurrence of
    # the template makes this call exactly once.
    unconditional: bool


@dataclass(frozen=True, slots=True)
class _SimpleJsonExpr:
    kind: str
    root: str | None = None
    keys: tuple[str, ...] = ()
    value: object = None
    test: _SimpleJsonExpr | None = None
    body: _SimpleJsonExpr | None = None
    otherwise: _SimpleJsonExpr | None = None


@dataclass(frozen=True, slots=True)
class _SimpleJsonOperation:
    kind: str
    operation: object
    expression: _SimpleJsonExpr | None = None
    attributes: tuple[tuple[str, _SimpleJsonExpr], ...] = ()
    branches: tuple[tuple[_SimpleJsonExpr | None, tuple[_SimpleJsonOperation, ...]], ...] = ()
    iterable: _SimpleJsonExpr | None = None
    target: str | None = None
    body: tuple[_SimpleJsonOperation, ...] = ()
    empty: tuple[_SimpleJsonOperation, ...] = ()


@dataclass(frozen=True, slots=True)
class _SimpleJsonReadNode:
    kinds: frozenset[str]
    children: tuple[tuple[str, _SimpleJsonReadNode], ...]
    items: _SimpleJsonReadNode | None = None


@dataclass(slots=True)
class _SimpleJsonReadNodeBuilder:
    kinds: set[str] = field(default_factory=set)
    children: dict[str, _SimpleJsonReadNodeBuilder] = field(default_factory=dict)
    items: _SimpleJsonReadNodeBuilder | None = None


@dataclass(frozen=True, slots=True)
class _SimpleJsonReadSet:
    roots: tuple[tuple[str, _SimpleJsonReadNode], ...]
    loop_targets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _SimpleJsonProgram:
    readset_preflight: _SimpleJsonPreflight
    evaluate: _SimpleJsonEvaluate


_SIMPLE_VUE_ERROR_COMPONENT: ContextVar[str | None] = ContextVar("citry_simple_vue_error_component", default=None)


def _simple_json_path_names(expression: _SimpleJsonExpr) -> frozenset[str]:
    if expression.kind == "path":
        return frozenset((cast("str", expression.root),))
    if expression.kind == "if":
        return (
            _simple_json_path_names(cast("_SimpleJsonExpr", expression.test))
            | _simple_json_path_names(cast("_SimpleJsonExpr", expression.body))
            | _simple_json_path_names(cast("_SimpleJsonExpr", expression.otherwise))
        )
    return frozenset()


def _simple_json_expr_from_ast(node: ast.expr) -> _SimpleJsonExpr | None:
    if type(node) is ast.Name:
        name = node.id
        if type(name) is not str or name.startswith("_") or name == "forloop":
            return None
        return _SimpleJsonExpr("path", root=name)
    if type(node) is ast.Constant:
        value = node.value
        if type(value) in {str, bool, type(None)}:
            return _SimpleJsonExpr("constant", value=value)
        return None
    if type(node) is ast.Subscript:
        key_node = node.slice
        if type(key_node) is not ast.Constant or type(key_node.value) is not str or key_node.value.startswith("_"):
            return None
        parent = _simple_json_expr_from_ast(node.value)
        if parent is None or parent.kind != "path":
            return None
        return _SimpleJsonExpr("path", root=parent.root, keys=(*parent.keys, key_node.value))
    if type(node) is ast.IfExp:
        test = _simple_json_expr_from_ast(node.test)
        body = _simple_json_expr_from_ast(node.body)
        otherwise = _simple_json_expr_from_ast(node.orelse)
        if test is None or test.kind != "path" or body is None or otherwise is None:
            return None
        return _SimpleJsonExpr("if", test=test, body=body, otherwise=otherwise)
    return None


def _compile_simple_json_expr(source: object, used_vars: object) -> _SimpleJsonExpr | None:
    if type(source) is not str or type(used_vars) is not tuple:
        return None
    try:
        parsed = ast.parse(source, mode="eval")
    except SyntaxError:
        return None
    expression = _simple_json_expr_from_ast(parsed.body)
    if expression is None:
        return None
    names = _simple_json_path_names(expression)
    if not names.issubset(used_vars):
        return None
    return expression


def _compile_call_input(source: str, used_vars: tuple[str, ...]) -> _SimpleJsonExpr | None:
    """
    Compile a child call's input or ``#c-key`` expression.

    A call passes its value on without formatting it, so a number literal
    (``c-count="3"``, ``#c-key="1"``) is accepted here even though text and
    attribute expressions keep numbers out of the shared subset.
    """
    try:
        parsed = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    if type(parsed) is ast.Constant and type(parsed.value) in {int, float}:
        return _SimpleJsonExpr("constant", value=parsed.value)
    return _compile_simple_json_expr(source, used_vars)


def _compile_simple_json_loop(node: ForNode) -> tuple[str, _SimpleJsonExpr] | None:
    if node._precomputed_parts is not None or len(node.branches) != 1:
        return None
    branch = node.branches[0]
    each = next((attr for attr in branch[1] if getattr(attr, "key", None) == "each"), None)
    if type(each) is not ExprHtmlAttr or type(each.expr) is not str:
        return None
    try:
        expression = ast.parse(f"[None for {each.expr}]", mode="eval").body
    except SyntaxError:
        return None
    if type(expression) is not ast.ListComp or len(expression.generators) != 1:
        return None
    generator = expression.generators[0]
    target = generator.target
    if (
        type(target) is not ast.Name
        or target.id.startswith("_")
        or generator.is_async != 0
        or generator.ifs
        or branch[3] != (target.id,)
    ):
        return None
    iterable = _simple_json_expr_from_ast(generator.iter)
    if iterable is None or iterable.kind != "path":
        return None
    if not _simple_json_path_names(iterable).issubset(each.used_vars):
        return None
    return target.id, iterable


def _simple_json_fixed_attrs(operation: _Open) -> tuple[tuple[str, ExprHtmlAttr], ...] | None:
    """Admit fixed values beside source-authored class/style without changing shared policy."""
    node = operation.node
    if (
        operation.renderer is not node
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
        for source_attr, _source in node._static_source_attrs
        if (target := _source_target(source_attr.key)) is not None
    }
    selected: list[tuple[str, ExprHtmlAttr]] = []
    for attr in node.attrs:
        if type(attr) not in {StaticHtmlAttr, ExprHtmlAttr}:
            return None
        output_name = attr.key.removeprefix("c-")
        identity = _html_attr_identity(output_name)
        if identity in identities:
            return None
        identities.add(identity)
        if identity in {"class", "style"}:
            if (
                type(attr) is not StaticHtmlAttr
                or attr.key != identity
                or not any(source_attr is attr for source_attr, _source in node._static_source_attrs)
            ):
                return None
            continue
        if type(attr) is not ExprHtmlAttr:
            continue
        if (
            identity in source_targets
            or identity in {"innerhtml", "outerhtml", "textcontent", "innertext"}
            or identity.startswith(("data-cev-", "on", "v-", "@", ":", "#", "$"))
        ):
            return None
        selected.append((output_name, attr))
    return tuple(selected)


def _simple_json_spread_expression(operation: _Open) -> _SimpleJsonExpr | None:
    """Keep the generic root spread inside the bounded path-only expression subset."""
    spreads = [attr for attr in operation.node.attrs if getattr(attr, "key", None) == "c-bind"]
    if len(spreads) != 1 or type(spreads[0]) is not ExprHtmlAttr or type(spreads[0].expr) is not str:
        return None
    expression = _compile_simple_json_expr(spreads[0].expr, spreads[0].used_vars)
    return expression if expression is not None and expression.kind == "path" else None


def _static_html_piece(operation: object) -> str | None:
    if isinstance(operation, _Static):
        return operation.html
    if isinstance(operation, _Close):
        return f"</{operation.value.tag}>"
    if isinstance(operation, _Open) and operation.static is not None:
        from citry._vue.capture import format_prepared_element_attrs  # noqa: PLC0415

        attrs = list(format_prepared_element_attrs(operation.static))
        suffix = "" if not attrs else " " + " ".join(attrs)
        ending = "/>" if operation.node.is_void and operation.node.is_self_closing else ">"
        result = f"<{operation.node.tag}{suffix}{ending}"
        if operation.node.is_self_closing and not operation.node.is_void:
            result += f"</{operation.node.tag}>"
        return result
    return None


@dataclass(frozen=True, slots=True)
class _MaterializedRowPlan:
    """
    Where a simple='vue' row HTML writer cuts its occurrence HTML for root markers.

    Serialize tags each component root with marker attributes through the
    native ``mark_html`` scan, which puts them after the last attribute of
    every start tag at nesting depth 0. This plan finds those positions once
    per template, so each occurrence only joins its pieces around the
    markers. Entries are keyed by ``id()`` of each ``_SimpleJsonOperation``;
    the plan is only read while code is generated, when those objects are
    still alive.
    """

    # Fixed output for an operation, cut where root markers go (one more
    # piece than markers; most operations have exactly one piece).
    literal_pieces: dict[int, tuple[str, ...]]
    # Openings formatted per occurrence. True marks a root start tag, whose
    # markers go right before its closing ``>``.
    runtime_opens: dict[int, bool]
    # Fixed-name openings whose attribute names are valid, outside class and
    # style, and fold into distinct attributes, so each value can be
    # formatted on its own.
    plain_name_opens: frozenset[int] = frozenset()


# The byte-level rules below mirror crates/citry_html_transform/src/marker.rs.
# The row HTML writer exists only when this Python walk and the native
# scan provably agree, so every rule that is not copied exactly declines.
_MARKER_WHITESPACE = " \t\n\r\x0c"
_MARKER_ASCII_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_MARKER_VOID_TAGS = frozenset(
    ("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr")
)
_MARKER_RAW_TEXT_TAGS = frozenset(("script", "style", "textarea", "title"))
_MARKER_PLACEHOLDER_ATTR = frozenset(("c-render-id",))
_MARKER_PLACEHOLDER_TAG = frozenset(("template",))


def _marker_name_is(name: str, names: frozenset[str]) -> bool:
    """Compare a tag name the way the native scan does: ASCII case-insensitively."""
    return name.isascii() and name.lower() in names


def _marker_start_tag(html: str, start: int) -> tuple[str, int, int, bool, bool] | None:
    """
    Lex the start tag at ``start`` like the native marker scan.

    Returns the tag name, where root markers would be inserted, the index
    after the tag, whether it ends with ``/>``, and whether it carries the
    ``c-render-id`` placeholder attribute. None means the tag does not end
    inside this piece, so its meaning depends on text written later.
    """
    length = len(html)
    index = start + 1
    while index < length and html[index] not in _MARKER_WHITESPACE and html[index] not in "/>":
        index += 1
    name = html[start + 1 : index]
    insert_at = index
    has_render_id = False
    while True:
        while index < length and html[index] in _MARKER_WHITESPACE:
            index += 1
        if index >= length:
            return None
        character = html[index]
        if character == ">":
            return name, insert_at, index + 1, False, has_render_id
        if character == "/":
            if index + 1 < length and html[index + 1] == ">":
                return name, insert_at, index + 2, True, has_render_id
            index += 1
            continue
        attr_start = index
        while index < length and html[index] not in _MARKER_WHITESPACE and html[index] not in "=>/":
            index += 1
        attr_end = index
        lookahead = index
        while lookahead < length and html[lookahead] in _MARKER_WHITESPACE:
            lookahead += 1
        if lookahead < length and html[lookahead] == "=":
            lookahead += 1
            while lookahead < length and html[lookahead] in _MARKER_WHITESPACE:
                lookahead += 1
            if lookahead < length and html[lookahead] in "\"'":
                quote = html[lookahead]
                closing = html.find(quote, lookahead + 1)
                if closing < 0:
                    return None
                index = closing + 1
            else:
                while lookahead < length and html[lookahead] not in _MARKER_WHITESPACE and html[lookahead] != ">":
                    lookahead += 1
                index = lookahead
        # A boolean attribute leaves the lookahead whitespace unconsumed.
        if _marker_name_is(html[attr_start:attr_end], _MARKER_PLACEHOLDER_ATTR):
            has_render_id = True
        insert_at = index


def _marker_raw_text_end(html: str, start: int, name: str) -> int | None:
    """
    Find the end of a raw-text element's closing tag within one piece.

    Returns the index after the closing ``>``, ``-1`` when the element
    continues into later output, or None when a closing tag could straddle
    this piece and the next one, which only the joined output can answer.
    """
    length = len(html)
    lowered = name.lower()
    index = html.find("<", start)
    while index >= 0 and index + 2 + len(name) <= length:
        candidate = html[index + 2 : index + 2 + len(name)]
        if html[index + 1] == "/" and candidate.isascii() and candidate.lower() == lowered:
            after = index + 2 + len(name)
            if after >= length:
                return None
            if html[after] in _MARKER_WHITESPACE or html[after] in "/>":
                closing = html.find(">", after)
                return None if closing < 0 else closing + 1
        index = html.find("<", index + 1)
    # Escaped text never contains "<", so only a partial closing tag at the
    # end of this piece could complete in a later piece.
    if "<" in html[max(start, length - len(name) - 2) :]:
        return None
    return -1


def _marker_scan_piece(
    html: str,
    depth: int,
    raw: str | None,
    *,
    allow_roots: bool,
) -> tuple[int, str | None, list[int]] | None:
    """
    Advance the native marker scan over one fixed piece of output.

    ``depth`` and ``raw`` (the raw-text element being skipped, if any) carry
    the scan state between pieces. Returns the new state and the positions
    of root start tags inside the piece. None declines: the piece ends inside
    a comment or tag, or holds a root where roots are not allowed.
    """
    position = 0
    length = len(html)
    root_positions: list[int] = []
    if raw is not None:
        end = _marker_raw_text_end(html, 0, raw)
        if end is None:
            return None
        if end < 0:
            return depth, raw, root_positions
        position = end
        raw = None
    while position < length:
        position = html.find("<", position)
        if position < 0:
            break
        if html.startswith("<!--", position):
            end = html.find("-->", position + 4)
            if end < 0:
                return None
            position = end + 3
        elif html.startswith("<![CDATA[", position):
            end = html.find("]]>", position + 9)
            if end < 0:
                return None
            position = end + 3
        elif html.startswith(("<!", "<?"), position):
            end = html.find(">", position)
            if end < 0:
                return None
            position = end + 1
        elif html.startswith("</", position):
            name_end = position + 2
            while name_end < length and html[name_end] not in _MARKER_WHITESPACE and html[name_end] != ">":
                name_end += 1
            end = html.find(">", position)
            if end < 0:
                return None
            if not _marker_name_is(html[position + 2 : name_end], _MARKER_VOID_TAGS):
                depth -= 1
            position = end + 1
        elif position + 1 < length and html[position + 1] in _MARKER_ASCII_LETTERS:
            tag = _marker_start_tag(html, position)
            # A placeholder template would be split out of the row, which
            # only the per-row scan reproduces.
            if tag is None or tag[4]:
                return None
            name, insert_at, position, self_closing, _render_id = tag
            if depth == 0:
                if not allow_roots:
                    return None
                root_positions.append(insert_at)
            if not self_closing and not _marker_name_is(name, _MARKER_VOID_TAGS):
                if _marker_name_is(name, _MARKER_RAW_TEXT_TAGS):
                    end = _marker_raw_text_end(html, position, name)
                    if end is None:
                        return None
                    if end < 0:
                        return depth, name, root_positions
                    position = end
                else:
                    depth += 1
        elif position + 1 >= length:
            # A trailing "<" would join the next piece's first character.
            return None
        else:
            position += 1
    return depth, raw, root_positions


def _materialized_row_plan(operations: tuple[_SimpleJsonOperation, ...]) -> _MaterializedRowPlan | None:
    """
    Prove where root markers go in every occurrence of a simple='vue' template.

    Root start tags must come from the top-level operations, so each
    occurrence gets markers at the same compile-time positions. Branches and
    loops must sit inside an element and leave the scan where they found it,
    so any branch choice or item count produces the same roots. Returns None
    when the template does not fit; serialize then scans each row as before.
    """
    literal_pieces: dict[int, tuple[str, ...]] = {}
    runtime_opens: dict[int, bool] = {}
    plain_name_opens: set[int] = set()

    def open_tag(
        simple: _SimpleJsonOperation, depth: int, raw: str | None, *, top: bool
    ) -> tuple[int, str | None] | None:
        operation = cast("_Open", simple.operation)
        node = operation.node
        # An opening written per occurrence cannot sit inside skipped raw
        # text, and a template tag could become a serialize placeholder.
        if raw is not None or _marker_name_is(node.tag, _MARKER_PLACEHOLDER_TAG):
            return None
        # The opening ends with "/>" only for self-closing void syntax, and
        # the native scan must read the same tag the same way.
        self_closing = node.is_void and node.is_self_closing
        native_void = _marker_name_is(node.tag, _MARKER_VOID_TAGS)
        if self_closing and not native_void:
            return None
        is_root = depth == 0
        if is_root and (not top or self_closing):
            return None
        runtime_opens[id(simple)] = is_root
        if simple.kind == "open" and _row_plain_names(tuple(name for name, _expression in simple.attributes)):
            plain_name_opens.add(id(simple))
        if not self_closing and not native_void:
            if _marker_name_is(node.tag, _MARKER_RAW_TEXT_TAGS):
                raw = node.tag
            else:
                depth += 1
        if node.is_self_closing and not node.is_void:
            scanned = _marker_scan_piece(f"</{node.tag}>", depth, raw, allow_roots=False)
            if scanned is None:
                return None
            depth, raw, _positions = scanned
        return depth, raw

    def walk(
        simple_operations: tuple[_SimpleJsonOperation, ...],
        depth: int,
        raw: str | None,
        *,
        top: bool,
    ) -> tuple[int, str | None] | None:
        for simple in simple_operations:
            if simple.kind == "skip":
                operation = simple.operation
                if isinstance(operation, _Open) and any(
                    attr.origin != "source" for attr in cast("PreparedElementOpen", operation.static).attrs
                ):
                    # Data attributes are escaped per occurrence, like the
                    # serialize-time path, instead of formatted once here.
                    state = open_tag(simple, depth, raw, top=top)
                else:
                    piece = _static_html_piece(operation)
                    if piece is None:
                        return None
                    scanned = _marker_scan_piece(piece, depth, raw, allow_roots=top)
                    if scanned is None:
                        return None
                    depth, raw, positions = scanned
                    bounds = [0, *positions, len(piece)]
                    literal_pieces[id(simple)] = tuple(piece[start:end] for start, end in pairwise(bounds))
                    continue
            elif simple.kind == "text":
                # Escaped text holds no "<", so the scan passes over it in
                # both ordinary text and skipped raw text.
                continue
            elif simple.kind in {"open", "generic"}:
                state = open_tag(simple, depth, raw, top=top)
            elif simple.kind in {"if", "for"}:
                if raw is not None or depth <= 0:
                    return None
                bodies = (
                    tuple(body for _condition, body in simple.branches)
                    if simple.kind == "if"
                    else (simple.body, simple.empty)
                )
                for body in bodies:
                    if walk(body, depth, None, top=False) != (depth, None):
                        return None
                continue
            else:
                return None
            if state is None:
                return None
            depth, raw = state
        return depth, raw

    if walk(operations, 0, None, top=True) is None:
        return None
    return _MaterializedRowPlan(literal_pieces, runtime_opens, frozenset(plain_name_opens))


def _row_plain_names(names: tuple[str, ...]) -> bool:
    """Whether format_attrs keeps every one of these fixed names as its own attribute."""
    identities: set[str] = set()
    for name in names:
        try:
            validate_html_attr_name(name)
        except (TypeError, ValueError):
            return False
        # Generated code writes these names verbatim, which matches their
        # escaped form only when nothing in them needs escaping.
        if any(character in name for character in "&\"'<>"):
            return False
        identity = _html_attr_identity(name)
        if identity in _ROW_FOLDED_ATTR_IDENTITIES or identity in identities:
            return False
        identities.add(identity)
    return True


def _materialized_open_html(
    operation: _Open,
    resolved: PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen,
) -> str:
    """Format one opening tag from its recorded values, without any closing tag."""
    if isinstance(resolved, _SpreadResolvedOpen):
        resolved = _prepared_open(operation, resolved)
    if isinstance(resolved, dict):
        attrs = list(operation.authored_attrs)
        formatted = str(format_attrs(resolved))
        if formatted:
            attrs.append(formatted)
    else:
        attrs = list(format_prepared_element_attrs(resolved))
    suffix = "" if not attrs else " " + " ".join(attrs)
    # The compiler emits an explicit close for non-void authored
    # self-closing elements. Only HTML void syntax keeps its slash in
    # materialized static output.
    ending = "/>" if operation.node.is_void and operation.node.is_self_closing else ">"
    return f"<{operation.node.tag}{suffix}{ending}"


# format_attrs folds these attributes' values (an empty class is dropped, a
# structured style is normalized), so they always go through it.
_ROW_FOLDED_ATTR_IDENTITIES = frozenset(("class", "style"))


def _row_plain_attr(name: str, value: object) -> str | None:
    """
    Return ``format_attrs({name: value})`` for one plain scalar, formatted directly.

    This skips format_attrs' general merging, which one plain value outside
    class and style never needs. None means the value needs format_attrs.
    """
    kind = type(value)
    if (
        kind is not str and kind is not int and kind is not float and kind is not bool and value is not None
    ) or _html_attr_identity(name) in _ROW_FOLDED_ATTR_IDENTITIES:
        return None
    # format_attrs rejects the same names with the same error.
    validate_html_attr_name(name)
    if value is None or value is False:
        return ""
    if value is True:
        return escape_to_str(name)
    return f'{escape_to_str(name)}="{escape_to_str(value)}"'


def _row_formatted_attrs(
    operation: _Open,
    resolved: PreparedElementOpen | dict[str, object],
    *,
    plain_names: bool,
) -> list[str]:
    """Format an opening's attributes as _materialized_open_html does, one plain value at a time."""
    if isinstance(resolved, dict):
        attrs = list(operation.authored_attrs)
        # Only names proved at compile time to fold into distinct attributes
        # can be formatted one by one; format_attrs merges the whole map.
        pieces = [_row_plain_attr(name, value) for name, value in resolved.items()] if plain_names else [None]
        if None in pieces:
            formatted = str(format_attrs(resolved))
            if formatted:
                attrs.append(formatted)
        else:
            formatted = " ".join(piece for piece in cast("list[str]", pieces) if piece)
            if formatted:
                attrs.append(formatted)
        return attrs
    rendered: list[str] = []
    for attr in resolved.attrs:
        if attr.origin == "source":
            rendered.append(str(attr.value))
            continue
        # format_prepared_element_attrs formats each data attribute alone.
        formatted_attr = _row_plain_attr(attr.name, attr.value)
        if formatted_attr is None:
            formatted_attr = str(format_attrs({attr.name: attr.value}))
        if formatted_attr:
            rendered.append(formatted_attr)
    return rendered


def _row_open_html(
    operation: _Open,
    data: dict[str, object],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
    plain_names: bool,
) -> str | None:
    """
    Format an occurrence's opening tag for its row HTML, or None to give up.

    The result matches _materialized_open_html. Serialize formats the same
    opening when no row HTML exists, so any error here is left for that
    later call to raise at the time it always did.
    """
    try:
        resolved = operation.static or resolved_opens[(id(data), id(operation))]
        if isinstance(resolved, _SpreadResolvedOpen):
            resolved = _prepared_open(operation, resolved)
        attrs = _row_formatted_attrs(operation, resolved, plain_names=plain_names)
    except Exception:  # noqa: BLE001 - serialize reformats and reports it
        return None
    suffix = "" if not attrs else " " + " ".join(attrs)
    ending = "/>" if operation.node.is_void and operation.node.is_self_closing else ">"
    return f"<{operation.node.tag}{suffix}{ending}"


def _row_append_root_open(
    operation: _Open,
    data: dict[str, object],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
    plain_names: bool,
    row_html: list[str | None],
    row_marks: list[int],
) -> None:
    """Write a root opening split right before its ``>``, where the markers go."""
    html = _row_open_html(operation, data, resolved_opens, plain_names)
    # The native scan inserts after the last attribute. That is the final
    # ">" unless the attribute text ends in whitespace, which it never does
    # for formatted attributes; a mismatch drops the row HTML instead.
    if html is None or html[-2] in _MARKER_WHITESPACE:
        row_html.append(None)
        return
    row_html.append(html[:-1])
    row_marks.append(len(row_html))
    row_html.append(">")


def _row_int_attr(prefix: str, value: object) -> str | None:
    """
    Write one exact-int attribute value for row HTML, or None to drop the row HTML.

    Python refuses to convert a very large int to text. Returning None leaves
    that error for serialize, which formats the row itself and raises there,
    as it does without row HTML. Any other type also needs format_attrs.
    """
    if type(value) is not int:
        return None
    try:
        return prefix + escape_to_str(value) + '"'
    except ValueError:
        return None


def _row_html_segments(row_html: list[str | None], row_marks: list[int]) -> tuple[str, ...] | None:
    """Join the row HTML writer's pieces into the text between root markers."""
    bounds = [0, *row_marks, len(row_html)]
    try:
        return tuple("".join(row_html[start:end]) for start, end in pairwise(bounds))  # type: ignore[arg-type]
    except TypeError:
        # An opening could not be formatted; serialize rebuilds this row.
        return None


# Captured at import, before a caller can replace the module attribute.
_DEFAULT_ROW_FORMAT_ATTRS = format_attrs


def _default_row_formatting() -> bool:
    """
    Whether escaping and attribute formatting still use Citry's own functions.

    The row plan assumes escaped text never contains "<", and the row HTML
    writer formats plain attributes itself. A replaced escaper or formatter
    could break either, so while one is in place serialize keeps its per-row
    materialization and scan. The writer checks this each time serialize
    calls it, since that is when the HTML is written.
    """
    return (
        escape_to_str is _html_module._DEFAULT_ESCAPE_TO_STR
        and format_attrs is _DEFAULT_ROW_FORMAT_ATTRS
        and _has_default_attr_formatting(_format_resolved_attrs_to_str)
        and _html_module._escape_to_str_impl is _html_module._DEFAULT_ESCAPE_TO_STR_IMPL
    )


def _compile_simple_json_operations(
    operations: tuple[object, ...],
    *,
    nested: bool = False,
    lexical_names: tuple[str, ...] = (),
    allow_instance_free_spread: bool = False,
) -> tuple[_SimpleJsonOperation, ...] | None:
    compiled: list[_SimpleJsonOperation] = []
    for operation in operations:
        if isinstance(operation, (_Static, _Close)):
            compiled.append(_SimpleJsonOperation("skip", operation))
        elif isinstance(operation, _Text):
            expression = _compile_simple_json_expr(operation.node.expr, operation.node.used_vars)
            if expression is None:
                return None
            compiled.append(_SimpleJsonOperation("text", operation, expression=expression))
        elif isinstance(operation, _Open):
            if operation.static is not None:
                compiled.append(_SimpleJsonOperation("skip", operation))
                continue
            fixed_attrs = operation.fixed_attrs
            if fixed_attrs is None:
                fixed_attrs = _simple_json_fixed_attrs(operation)
            if (
                fixed_attrs is None
                or operation.attrs_key is None
                or operation.key_key is not None
                or operation.control_key is not None
                or operation.runtime_events_key is not None
                or operation.spread_renderer is not None
                or operation.node._has_spread
                or operation.node._event_bindings
                or operation.node._poll_bindings
                or operation.node._control_bindings
                or (operation.node._runtime_events_candidate and not allow_instance_free_spread)
            ):
                # The root spread, controls, and any event-bearing opening keep
                # the existing resolver and side-table behavior.
                if (
                    nested
                    or not allow_instance_free_spread
                    or not operation.node._has_spread
                    or operation.node._event_bindings
                    or operation.node._poll_bindings
                    or operation.node._control_bindings
                    or (operation.node._runtime_events_candidate and not allow_instance_free_spread)
                    or (operation.node._runtime_control_candidate and not allow_instance_free_spread)
                    or operation.attrs_key is None
                ):
                    return None
                spread_expression = _simple_json_spread_expression(operation)
                if spread_expression is None:
                    return None
                compiled.append(_SimpleJsonOperation("generic", operation, expression=spread_expression))
                continue
            attributes: list[tuple[str, _SimpleJsonExpr]] = []
            for name, attr in fixed_attrs:
                if type(attr) is not ExprHtmlAttr:
                    return None
                if type(attr.expr) is str:
                    expression = _compile_simple_json_expr(attr.expr, attr.used_vars)
                else:
                    # ExprHtmlAttr.resolve treats every non-string expression
                    # as the boolean form and returns True.
                    expression = _SimpleJsonExpr("constant", value=True)
                if expression is None:
                    return None
                attributes.append((name, expression))
            compiled.append(_SimpleJsonOperation("open", operation, attributes=tuple(attributes)))
        elif isinstance(operation, _If):
            branches: list[tuple[_SimpleJsonExpr | None, tuple[_SimpleJsonOperation, ...]]] = []
            if len(operation.node.branches) != len(operation.branches):
                return None
            for branch, branch_operations in zip(operation.node.branches, operation.branches, strict=True):
                condition_attr = next((attr for attr in branch[1] if getattr(attr, "key", None) == "cond"), None)
                condition = None
                if condition_attr is not None:
                    if type(condition_attr) is not ExprHtmlAttr:
                        return None
                    condition = _compile_simple_json_expr(condition_attr.expr, condition_attr.used_vars)
                    if condition is None or condition.kind != "path":
                        return None
                body = _compile_simple_json_operations(
                    branch_operations,
                    nested=True,
                    lexical_names=lexical_names,
                    allow_instance_free_spread=allow_instance_free_spread,
                )
                if body is None:
                    return None
                branches.append((condition, body))
            compiled.append(_SimpleJsonOperation("if", operation, branches=tuple(branches)))
        elif isinstance(operation, _For):
            loop = _compile_simple_json_loop(operation.node)
            if loop is None:
                return None
            target, iterable = loop
            if target in lexical_names:
                return None
            body = _compile_simple_json_operations(
                operation.body,
                nested=True,
                lexical_names=(*lexical_names, target),
                allow_instance_free_spread=allow_instance_free_spread,
            )
            empty = _compile_simple_json_operations(
                operation.empty,
                nested=True,
                lexical_names=lexical_names,
                allow_instance_free_spread=allow_instance_free_spread,
            )
            if body is None or empty is None:
                return None
            compiled.append(
                _SimpleJsonOperation(
                    "for",
                    operation,
                    iterable=iterable,
                    target=target,
                    body=body,
                    empty=empty,
                )
            )
        elif isinstance(operation, _Call):
            # Each input keeps its authored order, like the ordinary call's
            # kwargs. A static attribute is a constant expression.
            inputs: list[tuple[str, _SimpleJsonExpr]] = []
            for input_attr in operation.node.attrs:
                name = input_attr.key.removeprefix("c-")
                if isinstance(input_attr, StaticHtmlAttr):
                    inputs.append((name, _SimpleJsonExpr("constant", value=input_attr.value)))
                    continue
                if not isinstance(input_attr, ExprHtmlAttr):
                    return None
                if type(input_attr.expr) is not str:
                    # ExprHtmlAttr.resolve returns True for the boolean form.
                    inputs.append((name, _SimpleJsonExpr("constant", value=True)))
                    continue
                expression = _compile_call_input(input_attr.expr, input_attr.used_vars)
                if expression is None:
                    return None
                inputs.append((name, expression))
            key_expression = None
            key_attr = operation.node.key
            if key_attr is not None:
                if type(key_attr.expr) is not str:
                    return None
                key_expression = _compile_call_input(key_attr.expr, key_attr.used_vars)
                if key_expression is None:
                    return None
            compiled.append(
                _SimpleJsonOperation("call", operation, expression=key_expression, attributes=tuple(inputs))
            )
        else:
            return None
    return tuple(compiled)


def _simple_json_read_set(operations: tuple[_SimpleJsonOperation, ...]) -> _SimpleJsonReadSet:
    """Merge the evaluator's literal reads into one bounded path trie per scope."""
    roots: dict[str, _SimpleJsonReadNodeBuilder] = {}

    def new_node() -> _SimpleJsonReadNodeBuilder:
        return _SimpleJsonReadNodeBuilder()

    def add_path(
        expression: _SimpleJsonExpr,
        kind: str,
        local_nodes: dict[str, _SimpleJsonReadNodeBuilder],
    ) -> _SimpleJsonReadNodeBuilder:
        if expression.kind != "path" or expression.root is None:
            raise AssertionError("simple JSON read set received a non-path expression")
        root_name = expression.root
        node = local_nodes.get(root_name)
        if node is None:
            node = roots.setdefault(root_name, new_node())
        for key in expression.keys:
            node = node.children.setdefault(key, new_node())
        node.kinds.add(kind)
        return node

    def add_expression(
        expression: _SimpleJsonExpr,
        kind: str,
        local_nodes: dict[str, _SimpleJsonReadNodeBuilder],
    ) -> None:
        if expression.kind == "constant":
            return
        if expression.kind == "path":
            add_path(expression, kind, local_nodes)
            return
        if expression.kind == "if":
            add_expression(cast("_SimpleJsonExpr", expression.test), "truth", local_nodes)
            add_expression(cast("_SimpleJsonExpr", expression.body), kind, local_nodes)
            add_expression(cast("_SimpleJsonExpr", expression.otherwise), kind, local_nodes)
            return
        raise AssertionError(f"unknown simple JSON read expression: {expression.kind}")

    def visit(
        scoped_operations: tuple[_SimpleJsonOperation, ...],
        local_nodes: dict[str, _SimpleJsonReadNodeBuilder],
    ) -> None:
        for simple in scoped_operations:
            if simple.kind == "text":
                add_expression(cast("_SimpleJsonExpr", simple.expression), "scalar", local_nodes)
            elif simple.kind == "open":
                for _name, expression in simple.attributes:
                    add_expression(expression, "scalar", local_nodes)
            elif simple.kind == "generic":
                # The ordinary G2 resolver still runs for the root c-bind. Its
                # source value must be a plain scalar-valued attribute map so
                # it cannot execute user mapping/value protocols or mutate a
                # later field between validation and generated evaluation.
                add_expression(cast("_SimpleJsonExpr", simple.expression), "safe_attrs_or_none", local_nodes)
            elif simple.kind == "if":
                for condition, body in simple.branches:
                    if condition is not None:
                        add_expression(condition, "truth", local_nodes)
                    visit(body, local_nodes)
            elif simple.kind == "call":
                # A call passes each value to the child unchanged, as the
                # ordinary call does. The walk to it must still go through
                # exact dicts, but the value itself can be anything: the
                # child's own schema and template decide what it accepts.
                for _name, expression in simple.attributes:
                    add_expression(expression, "value", local_nodes)
                if simple.expression is not None:
                    add_expression(simple.expression, "value", local_nodes)
            elif simple.kind == "for":
                iterable = add_path(cast("_SimpleJsonExpr", simple.iterable), "list", local_nodes)
                if iterable.items is None:
                    iterable.items = new_node()
                loop_nodes = dict(local_nodes)
                loop_nodes[cast("str", simple.target)] = iterable.items
                visit(simple.body, loop_nodes)
                # Empty branches do not introduce the loop variable.
                visit(simple.empty, local_nodes)

    visit(operations, {})

    def freeze(node: _SimpleJsonReadNodeBuilder) -> _SimpleJsonReadNode:
        return _SimpleJsonReadNode(
            frozenset(node.kinds),
            tuple((key, freeze(child)) for key, child in node.children.items()),
            None if node.items is None else freeze(node.items),
        )

    return _SimpleJsonReadSet(
        tuple((name, freeze(node)) for name, node in roots.items()),
        _simple_json_loop_targets(operations),
    )


def _simple_json_loop_targets(operations: tuple[_SimpleJsonOperation, ...]) -> tuple[str, ...]:
    targets: list[str] = []
    for operation in operations:
        if operation.kind == "for":
            targets.append(cast("str", operation.target))
            targets.extend(_simple_json_loop_targets(operation.body))
            targets.extend(_simple_json_loop_targets(operation.empty))
        elif operation.kind == "if":
            for _condition, body in operation.branches:
                targets.extend(_simple_json_loop_targets(body))
    return tuple(dict.fromkeys(targets))


def _simple_json_nested_operations(
    operations: tuple[_SimpleJsonOperation, ...],
) -> Iterator[_SimpleJsonOperation]:
    for operation in operations:
        yield operation
        if operation.kind == "if":
            for _condition, body in operation.branches:
                yield from _simple_json_nested_operations(body)
        elif operation.kind == "for":
            yield from _simple_json_nested_operations(operation.body)
            yield from _simple_json_nested_operations(operation.empty)


def _simple_json_has_dynamic_attributes(operations: tuple[_SimpleJsonOperation, ...]) -> bool:
    return any(operation.kind in {"open", "generic"} for operation in _simple_json_nested_operations(operations))


def _simple_json_has_i18n_spread(operations: tuple[_SimpleJsonOperation, ...]) -> bool:
    return any(
        operation.kind == "generic"
        and type(cast("_Open", operation.operation).spread_renderer) is I18nBindingElementAttrsNode
        for operation in _simple_json_nested_operations(operations)
    )


def _simple_json_has_i18n_attrs(operations: tuple[_SimpleJsonOperation, ...]) -> bool:
    """Reject authored `$c-tr` directives that need the ordinary i18n compiler."""
    from citry._i18n_directives import looks_like_i18n_binding  # noqa: PLC0415

    return any(
        isinstance(source := operation.operation, _Open)
        and any(looks_like_i18n_binding(attr.key.removeprefix("c-")) for attr in source.node.attrs)
        for operation in _simple_json_nested_operations(operations)
    )


def _simple_json_has_spread(operations: tuple[_SimpleJsonOperation, ...]) -> bool:
    return any(operation.kind == "generic" for operation in _simple_json_nested_operations(operations))


def _simple_vue_spread_hooks_supported(extensions: Any) -> bool:
    """Allow only the built-in Events hook, whose reserved keys are rejected below."""
    if not extensions.has_hook("on_attrs_resolved"):
        return True
    from citry.ext.events.extension import EventsExtension  # noqa: PLC0415

    for extension in extensions._extensions_with_hook("on_attrs_resolved"):
        if (
            type(extension) is not EventsExtension
            or extension.__dict__.get("on_attrs_resolved") is not None
            or getattr(extension.on_attrs_resolved, "__func__", None) is not EventsExtension.on_attrs_resolved
        ):
            return False
    return True


class _SimpleJsonCodegen:
    """Build a cached evaluator for the deliberately small JSON expression subset."""

    def __init__(self, operations: tuple[_SimpleJsonOperation, ...]) -> None:
        self.operations: list[object] = []
        self.functions: list[str] = []
        self.counter = 0
        self._root_operations = operations
        self._read_set = _simple_json_read_set(operations)
        self.readset_preflight_root = self._readset_preflight_function()

    def _new_name(self, prefix: str) -> str:
        self.counter += 1
        return f"_{prefix}{self.counter}"

    def _operation_index(self, operation: object) -> int:
        self.operations.append(operation)
        return len(self.operations) - 1

    @staticmethod
    def _expr(
        expression: _SimpleJsonExpr,
        variables: str = "variables",
        local_names: tuple[tuple[str, str], ...] = (),
    ) -> str:
        if expression.kind == "constant":
            return repr(expression.value)
        if expression.kind == "path":
            local = dict(local_names).get(cast("str", expression.root))
            value = local if local is not None else f"dict.__getitem__({variables}, {expression.root!r})"
            for key in expression.keys:
                value = f"dict.__getitem__({value}, {key!r})"
            return value
        if expression.kind == "if":
            body = _SimpleJsonCodegen._expr(cast("_SimpleJsonExpr", expression.body), variables, local_names)
            test = _SimpleJsonCodegen._expr(cast("_SimpleJsonExpr", expression.test), variables, local_names)
            otherwise = _SimpleJsonCodegen._expr(cast("_SimpleJsonExpr", expression.otherwise), variables, local_names)
            return f"({body} if {test} else {otherwise})"
        raise AssertionError(f"unknown simple JSON expression: {expression.kind}")

    def _readset_preflight_function(self) -> str:
        name = self._new_name("readset_preflight")
        header = [
            f"def {name}(context, candidate_variables=None):",
            "    variables = context.variables if context is not None else candidate_variables",
        ]
        # The read set is fixed for this program, so its walk is written out
        # as straight-line checks once; each row then runs only value checks.
        # A template nested too deeply for Python's block limit falls back to
        # _simple_json_readset_is_plain, the general check, which gives the
        # same answer.
        checks = _simple_json_readset_check_lines(self._read_set, indent=4)
        candidate = "\n".join((*header, *checks))
        try:
            compile(candidate, "<citry-simple-json-readset>", "exec")
        except (SyntaxError, RecursionError):
            candidate = "\n".join((*header, "    return _simple_json_readset_is_plain(variables, _read_set)"))
        self.functions.append(candidate)
        return name

    def _evaluate_lines(
        self,
        operations: tuple[_SimpleJsonOperation, ...],
        local_names: tuple[tuple[str, str], ...],
        indent: int,
    ) -> list[str]:
        lines: list[str] = []
        pad = " " * indent
        for simple in operations:
            index = self._operation_index(simple.operation)
            operation_name = self._new_name("operation")
            lines.append(f"{pad}{operation_name} = _operations[{index}]")
            if simple.kind == "skip":
                continue
            if simple.kind == "generic":
                lines.append(f"{pad}if context is None:")
                resolved_name = self._new_name("resolved_spread")
                projected_name = self._new_name("projected_spread")
                opening_name = self._new_name("spread_opening")
                # Which attributes this c-bind writes, in what order and at
                # which source positions, depends only on the row's keys, so
                # it is computed once per key set and kept with this program.
                plans_index = self._operation_index(_RootSpreadPlans())
                lines.extend(
                    (
                        f"{pad}    try:",
                        f"{pad}        {resolved_name} = "
                        f"{self._expr(cast('_SimpleJsonExpr', simple.expression), local_names=local_names)}",
                        f"{pad}        if {resolved_name} is None:",
                        f"{pad}            {resolved_name} = {{}}",
                        f"{pad}        elif type({resolved_name}) is not dict:",
                        f"{pad}            raise TypeError("
                        "\"simple='vue' c-bind requires a plain JSON object or None\")",
                        f"{pad}        {projected_name}, {opening_name} = _instance_free_root_spread("
                        f"{operation_name}, {resolved_name}, _operations[{plans_index}])",
                        f"{pad}        resolved_opens.setdefault((id(data), id({operation_name})), {opening_name})",
                        f"{pad}        data[{operation_name}.attrs_key] = {projected_name}",
                        f"{pad}    except Exception as error:",
                        f"{pad}        _attach_error(error, {operation_name}.node, context)",
                        f"{pad}        raise",
                        f"{pad}else:",
                        f"{pad}    _evaluate(({operation_name},), "
                        "context, data, root_data, vue_errors, special, resolved_opens)",
                    )
                )
            elif simple.kind == "text":
                text_name = self._new_name("text")
                lines.extend(
                    (
                        f"{pad}try:",
                        f"{pad}    {text_name} = "
                        f"{self._expr(cast('_SimpleJsonExpr', simple.expression), local_names=local_names)}",
                        f"{pad}    if {text_name} is None:",
                        f"{pad}        {text_name} = ''",
                        f"{pad}    elif type({text_name}) in (str, int, float, bool):",
                        f"{pad}        {text_name} = str({text_name})",
                        f"{pad}    else:",
                        f"{pad}        raise RuntimeError('simple JSON evaluator requires scalar text')",
                        f"{pad}except Exception as error:",
                        f"{pad}    _attach_error(error, {operation_name}.node, context)",
                        f"{pad}    raise",
                        f"{pad}data[{operation_name}.key] = {text_name}",
                    )
                )
            elif simple.kind == "open":
                attrs_name = self._new_name("attrs")
                lines.extend(
                    (
                        f"{pad}try:",
                        f"{pad}    {attrs_name} = {{}}",
                    )
                )
                for attribute_name, expression in simple.attributes:
                    value_name = self._new_name("attribute")
                    lines.extend(
                        (
                            f"{pad}    {value_name} = {self._expr(expression, local_names=local_names)}",
                            f"{pad}    if {value_name} is not None and {value_name} is not False:",
                            # A float or a huge int reads differently in JavaScript,
                            # so it gets the text Python's HTML writes.
                            f"{pad}        if type({value_name}) is float or (",
                            f"{pad}            type({value_name}) is int",
                            f"{pad}            and not -_JS_SAFE_INTEGER <= {value_name} <= _JS_SAFE_INTEGER",
                            f"{pad}        ):",
                            f"{pad}            {value_name} = _vue_attribute_value({value_name})",
                            f"{pad}        {attrs_name}[{attribute_name!r}] = {value_name}",
                        )
                    )
                lines.extend(
                    (
                        f"{pad}except Exception as error:",
                        f"{pad}    _attach_error(error, {operation_name}.node, context)",
                        f"{pad}    raise",
                        f"{pad}resolved_opens.setdefault((id(data), id({operation_name})), {attrs_name})",
                        f"{pad}data[{operation_name}.attrs_key] = {attrs_name}",
                    )
                )
            elif simple.kind == "if":
                selected = self._new_name("selected")
                lines.append(f"{pad}{selected} = -1")
                lines.append(f"{pad}try:")
                for branch_index, (condition, _body) in enumerate(simple.branches):
                    lines.append(f"{pad}    if {selected} < 0:")
                    if condition is None:
                        lines.append(f"{pad}        {selected} = {branch_index}")
                    else:
                        condition_value = self._new_name("condition")
                        lines.append(
                            f"{pad}        {condition_value} = {self._expr(condition, local_names=local_names)}"
                        )
                        lines.append(f"{pad}        if {condition_value}:")
                        lines.append(f"{pad}            {selected} = {branch_index}")
                lines.extend(
                    (
                        f"{pad}except Exception as error:",
                        f"{pad}    _attach_error(error, {operation_name}.node, context)",
                        f"{pad}    raise",
                        f"{pad}data[{operation_name}.key] = {selected}",
                    )
                )
                for branch_index, (_condition, body) in enumerate(simple.branches):
                    branch_function = self._evaluate_function(body, local_names)
                    lines.append(f"{pad}if {selected} == {branch_index}:")
                    lines.append(
                        f"{pad}    {branch_function}("
                        "context, variables, data, root_data, vue_errors, special, resolved_opens"
                        f"{self._local_call_args(local_names)})"
                    )
            elif simple.kind == "for":
                node = cast("_For", simple.operation).node
                records = self._new_name("records")
                iterable = self._new_name("iterable")
                record = self._new_name("record")
                rendered_any = self._new_name("rendered_any")
                loop_value = self._new_name("loop_value")
                body_locals = (*local_names, (cast("str", simple.target), loop_value))
                body_function = self._evaluate_function(simple.body, body_locals)
                empty_function = self._evaluate_function(simple.empty, local_names) if simple.empty else None
                lines.extend(
                    (
                        f"{pad}{records} = []",
                        f"{pad}{rendered_any} = False",
                        f"{pad}try:",
                        f"{pad}    if context is None:",
                        f"{pad}        _validate_context_free_introduced_variables("
                        f"'c-for', {node.branches[0][3]!r}, variables)",
                        f"{pad}    else:",
                        f"{pad}        _validate_introduced_variables('c-for', {node.branches[0][3]!r}, context)",
                        f"{pad}    {iterable} = "
                        f"{self._expr(cast('_SimpleJsonExpr', simple.iterable), local_names=local_names)}",
                        f"{pad}    if type({iterable}) is not list:",
                        f"{pad}        raise RuntimeError('simple JSON evaluator requires list-valued c-for input')",
                        f"{pad}    for {loop_value} in {iterable}:",
                        f"{pad}        {rendered_any} = True",
                        f"{pad}        {record} = {{}}",
                        f"{pad}        {records}.append({record})",
                        f"{pad}        {body_function}("
                        f"context, variables, {record}, root_data, vue_errors, special, resolved_opens"
                        f"{self._local_call_args(local_names, trailing=loop_value)})",
                    )
                )
                if empty_function is not None:
                    lines.extend(
                        (
                            f"{pad}    if not {rendered_any}:",
                            f"{pad}        {empty_function}("
                            "context, variables, data, root_data, vue_errors, special, resolved_opens"
                            f"{self._local_call_args(local_names)})",
                        )
                    )
                lines.extend(
                    (
                        f"{pad}except Exception as error:",
                        f"{pad}    _attach_error(error, {operation_name}.node, context)",
                        f"{pad}    raise",
                        f"{pad}data[{operation_name}.key] = {records}",
                    )
                )
            elif simple.kind == "call":
                kwargs_name = self._new_name("call_kwargs")
                key_name = self._new_name("call_key")
                lines.extend((f"{pad}try:", f"{pad}    {kwargs_name} = {{}}"))
                for input_name, expression in simple.attributes:
                    value_code = self._expr(expression, local_names=local_names)
                    # The ordinary call marks an input Const when it reads no
                    # variables (a static attribute or a literal), so the
                    # child can reuse work for it. The instance-free
                    # variables carry no Const marks, so an input that reads
                    # a variable is passed plain.
                    if not _simple_json_path_names(expression):
                        value_code = f"_Const({value_code})"
                    lines.append(f"{pad}    {kwargs_name}[{input_name!r}] = {value_code}")
                lines.append(f"{pad}    {key_name} = None")
                if simple.expression is not None:
                    # Exactly None opts out of a key, as in ComponentNode.render.
                    lines.extend(
                        (
                            f"{pad}    {key_name} = _const_value("
                            f"{self._expr(simple.expression, local_names=local_names)})",
                            f"{pad}    if {key_name} is not None:",
                            f"{pad}        {key_name} = str({key_name})",
                        )
                    )
                lines.extend(
                    (
                        f"{pad}except Exception as error:",
                        f"{pad}    _attach_error(error, {operation_name}.node, context)",
                        f"{pad}    raise",
                        # The instance-free caller passes its call table as
                        # ``special``; it creates each child from this entry.
                        f"{pad}special[(id(data), {operation_name}.key)] = "
                        f"({operation_name}, {kwargs_name}, {key_name})",
                    )
                )
            else:
                raise AssertionError(f"unknown simple JSON operation: {simple.kind}")
        return lines

    @staticmethod
    def _local_call_args(
        local_names: tuple[tuple[str, str], ...],
        *,
        trailing: str | None = None,
    ) -> str:
        names = [value_name for _source_name, value_name in local_names]
        if trailing is not None:
            names.append(trailing)
        return "" if not names else ", " + ", ".join(names)

    def _evaluate_function(
        self,
        operations: tuple[_SimpleJsonOperation, ...],
        local_names: tuple[tuple[str, str], ...] = (),
    ) -> str:
        name = self._new_name("evaluate")
        lines = [
            f"def {name}(context, variables, data, root_data, vue_errors, special, resolved_opens"
            f"{self._local_call_args(local_names)}):",
            "    value_token = _VALUE_CONTEXT.set(context)",
            "    try:",
        ]
        body_lines = self._evaluate_lines(operations, local_names, 8)
        lines.extend(body_lines or ["        pass"])
        lines.extend(("    finally:", "        _VALUE_CONTEXT.reset(value_token)"))
        self.functions.append("\n".join(lines))
        return name

    def build(self) -> _SimpleJsonProgram:
        evaluate_root = self._evaluate_function(self._root_operations)
        source = "\n\n".join(self.functions)
        namespace: dict[str, object] = {
            "_ConstMapping": _ConstMapping,
            "_Const": Const,
            "_const_value": const_value,
            "_VALUE_CONTEXT": _VALUE_CONTEXT,
            "_attach_error": _attach_error,
            "_evaluate": _evaluate,
            "_simple_json_readset_is_plain": _simple_json_readset_is_plain,
            "_simple_json_plain_scalar_types": _simple_json_plain_scalar_types,
            "_readset_safe_attrs": _readset_safe_attrs,
            "_READSET_TRUTH_TYPES": _READSET_TRUTH_TYPES,
            "_NoneType": type(None),
            "_isfinite": math.isfinite,
            "_validate_introduced_variables": _validate_introduced_variables,
            "_validate_context_free_introduced_variables": _validate_context_free_introduced_variables,
            "_instance_free_root_spread": _instance_free_root_spread,
            "_vue_attribute_value": _vue_attribute_value,
            "_JS_SAFE_INTEGER": _JS_SAFE_INTEGER,
            "_operations": tuple(self.operations),
            "_read_set": self._read_set,
            "dict": dict,
        }
        # The source is built above from the template's own operations only.
        exec(compile(source, "<citry-simple-json-leaf>", "exec"), namespace)  # noqa: S102
        # The two names were defined by the generated source with the
        # signatures that _readset_preflight_function and _evaluate_function write.
        return _SimpleJsonProgram(
            cast("_SimpleJsonPreflight", namespace[self.readset_preflight_root]),
            cast("_SimpleJsonEvaluate", namespace[evaluate_root]),
        )


@dataclass(frozen=True, slots=True)
class _RowLiteral:
    """Fixed text the row HTML writer appends; adjacent ones are joined into one append."""

    text: str


class _RowHtmlWriterCodegen:
    """
    Build the function that writes a simple='vue' occurrence's HTML from its recorded values.

    The evaluator records each text value, each opening's attributes, the
    chosen branch of each ``c-if`` and one record per ``c-for`` item. The
    generated function walks the same operations over those records and
    writes what serialize-time materialization would, cut where the plan puts
    root markers. It runs no template expression, so calling it later, or not
    at all, cannot change what the template evaluated.
    """

    def __init__(self, operations: tuple[_SimpleJsonOperation, ...], plan: _MaterializedRowPlan) -> None:
        self._root_operations = operations
        self._plan = plan
        self.functions: list[str] = []
        # Operation objects are bound as module globals of the generated code,
        # so the source text stays the same from run to run.
        self.namespace: dict[str, object] = {}
        self.counter = 0

    def _new_name(self, prefix: str) -> str:
        self.counter += 1
        return f"_{prefix}{self.counter}"

    def _bind(self, operation: object) -> tuple[str, str]:
        """Bind an operation and its id() as globals; resolved_opens is keyed by that id."""
        name = self._new_name("operation")
        self.namespace[name] = operation
        self.namespace[f"{name}_id"] = id(operation)
        return name, f"{name}_id"

    def _function(self, operations: tuple[_SimpleJsonOperation, ...]) -> str:
        # Each branch and loop body is its own function, as in the evaluator,
        # so a deeply nested template never hits Python's nested-block limit.
        name = self._new_name("write")
        lines = [f"def {name}(data, resolved_opens, row_html, row_marks):"]
        # Fixed text between two runtime values is written as one string, so
        # a row does one append per run of markup instead of one per piece.
        # Root marker lines stay between runs, because they record how many
        # pieces were appended before them.
        pending: list[str] = []
        for line in self._lines(operations):
            if isinstance(line, _RowLiteral):
                pending.append(line.text)
                continue
            if pending:
                lines.append(f"    row_html.append({''.join(pending)!r})")
                pending.clear()
            lines.append(line)
        if pending:
            lines.append(f"    row_html.append({''.join(pending)!r})")
        if len(lines) == 1:
            lines.append("    pass")
        self.functions.append("\n".join(lines))
        return name

    def _lines(self, operations: tuple[_SimpleJsonOperation, ...]) -> list[str | _RowLiteral]:
        lines: list[str | _RowLiteral] = []
        pad = "    "
        for simple in operations:
            if simple.kind == "skip":
                pieces = self._plan.literal_pieces.get(id(simple))
                if pieces is None:
                    # A fixed opening with data attributes is formatted per occurrence.
                    lines.extend(self._open_lines(simple))
                    continue
                for index, piece in enumerate(pieces):
                    # The plan cut this fixed piece at each root start tag.
                    if index:
                        lines.append(f"{pad}row_marks.append(len(row_html))")
                    if piece:
                        lines.append(_RowLiteral(piece))
            elif simple.kind == "text":
                # The evaluator stored the text already converted to str.
                key = cast("_Text", simple.operation).key
                lines.append(f"{pad}row_html.append(_escape_to_str(data[{key!r}]))")
            elif simple.kind in {"open", "generic"}:
                lines.extend(self._open_lines(simple))
            elif simple.kind == "if":
                # The evaluator stored the chosen branch index, or -1 for none.
                key = cast("_If", simple.operation).key
                selected = self._new_name("selected")
                lines.append(f"{pad}{selected} = data[{key!r}]")
                for branch_index, (_condition, body) in enumerate(simple.branches):
                    branch = self._function(body)
                    keyword = "if" if branch_index == 0 else "elif"
                    lines.append(f"{pad}{keyword} {selected} == {branch_index}:")
                    lines.append(f"{pad}    {branch}(data, resolved_opens, row_html, row_marks)")
            elif simple.kind == "for":
                # One record per item; the empty branch reads the enclosing
                # data, as it did when the evaluator ran it.
                key = cast("_For", simple.operation).key
                records = self._new_name("records")
                record = self._new_name("record")
                item_function = self._function(simple.body)
                lines.extend(
                    (
                        f"{pad}{records} = data[{key!r}]",
                        f"{pad}for {record} in {records}:",
                        f"{pad}    {item_function}({record}, resolved_opens, row_html, row_marks)",
                    )
                )
                if simple.empty:
                    empty_function = self._function(simple.empty)
                    lines.extend(
                        (
                            f"{pad}if not {records}:",
                            f"{pad}    {empty_function}(data, resolved_opens, row_html, row_marks)",
                        )
                    )
            else:
                # _materialized_row_plan admits only the kinds above.
                raise AssertionError(f"row HTML writer cannot write operation kind {simple.kind!r}")
        return lines

    def _open_lines(self, simple: _SimpleJsonOperation) -> list[str | _RowLiteral]:
        """Write an opening formatted from this occurrence's recorded values, plus its explicit close."""
        pad = "    "
        operation = cast("_Open", simple.operation)
        operation_name, operation_id = self._bind(operation)
        plain_names = id(simple) in self._plan.plain_name_opens
        if self._plan.runtime_opens[id(simple)]:
            # A root opening is split right before its ">", where the markers go.
            lines: list[str | _RowLiteral] = [
                f"{pad}_row_append_root_open("
                f"{operation_name}, data, resolved_opens, {plain_names!r}, row_html, row_marks)"
            ]
        elif plain_names and simple.kind == "open" and simple.attributes:
            # Nested fixed-name openings are the most common per-row work, so
            # their attributes are written inline, the way format_attrs would
            # write them. The evaluator left None and False out of the map.
            attrs = self._new_name("attrs")
            value = self._new_name("value")
            authored = "" if not operation.authored_attrs else " " + " ".join(operation.authored_attrs)
            lines = [
                f"{pad}{attrs} = resolved_opens[(id(data), {operation_id})]",
                _RowLiteral(f"<{operation.node.tag}{authored}"),
            ]
            for name, _expression in simple.attributes:
                lines.extend(
                    (
                        f"{pad}{value} = {attrs}.get({name!r})",
                        f"{pad}if {value} is True:",
                        f"{pad}    row_html.append({' ' + name!r})",
                        f"{pad}elif {value} is not None and {value} is not False:",
                        # Strings and floats always format; other values go
                        # through a helper, and its None drops the row HTML.
                        f"{pad}    row_html.append({' ' + name + '=' + chr(34)!r} + _escape_to_str({value}) + '\"'"
                        f" if type({value}) in (str, float)"
                        f" else _row_int_attr({' ' + name + '=' + chr(34)!r}, {value}))",
                    )
                )
            lines.append(_RowLiteral("/>" if operation.node.is_void and operation.node.is_self_closing else ">"))
        else:
            lines = [f"{pad}row_html.append(_row_open_html({operation_name}, data, resolved_opens, {plain_names!r}))"]
        if operation.node.is_self_closing and not operation.node.is_void:
            lines.append(_RowLiteral(f"</{operation.node.tag}>"))
        return lines

    def build(self) -> _RowHtmlWrite:
        root = self._function(self._root_operations)
        namespace: dict[str, object] = {
            **self.namespace,
            "_escape_to_str": escape_to_str,
            "_row_open_html": _row_open_html,
            "_row_append_root_open": _row_append_root_open,
            "_row_int_attr": _row_int_attr,
        }
        # The source is built above from the template's own operations only.
        exec(compile("\n\n".join(self.functions), "<citry-simple-vue-row-html>", "exec"), namespace)  # noqa: S102
        return cast("_RowHtmlWrite", namespace[root])


def _simple_json_readset_check_lines(read_set: _SimpleJsonReadSet, *, indent: int) -> list[str]:
    """
    Write _simple_json_readset_is_plain for one fixed read set as straight-line code.

    The emitted checks give the same answer as the shared walker and visit
    values in the same order: exact root mapping, no loop-target shadowing, then each
    read path depth first. The live plain scalar types are read once per call,
    so registering a type with ComponentLike later still affects the next row.
    """
    pad = " " * indent
    lines = [
        f"{pad}if type(variables) is not dict and type(variables) is not _ConstMapping:",
        f"{pad}    return False",
    ]
    for target in read_set.loop_targets:
        lines.extend(
            (
                f"{pad}if dict.__contains__(variables, {target!r}):",
                f"{pad}    return False",
            )
        )
    lines.append(f"{pad}plain_scalar_types = _simple_json_plain_scalar_types()")
    counter = 0

    def emit(value: str, plan: _SimpleJsonReadNode, depth: int) -> None:
        nonlocal counter
        counter += 1
        kind = f"value_type{counter}"
        at = " " * depth
        lines.append(f"{at}{kind} = type({value})")
        if "scalar" in plan.kinds:
            # A scalar is plain when it is None or a str, int, bool or float
            # type that no ComponentLike registration has claimed.
            # plain_scalar_types holds only those types, so this also rejects
            # every container.
            lines.extend(
                (
                    f"{at}if {kind} is not _NoneType and {kind} not in plain_scalar_types:",
                    f"{at}    return False",
                    f"{at}if {kind} is float and not _isfinite({value}):",
                    f"{at}    return False",
                )
            )
        if "list" in plan.kinds:
            lines.extend((f"{at}if {kind} is not list:", f"{at}    return False"))
        if "truth" in plan.kinds:
            lines.extend(
                (
                    f"{at}if {kind} not in _READSET_TRUTH_TYPES:",
                    f"{at}    return False",
                    f"{at}if {kind} is float and not _isfinite({value}):",
                    f"{at}    return False",
                )
            )
        if "safe_attrs_or_none" in plan.kinds or "safe_attrs" in plan.kinds:
            if "safe_attrs" in plan.kinds:
                lines.extend((f"{at}if {kind} is not dict:", f"{at}    return False"))
            else:
                lines.extend((f"{at}if {kind} is not dict and {kind} is not _NoneType:", f"{at}    return False"))
            lines.extend(
                (
                    f"{at}if {kind} is dict and not _readset_safe_attrs({value}):",
                    f"{at}    return False",
                )
            )
        if plan.children:
            lines.extend((f"{at}if {kind} is not dict:", f"{at}    return False"))
            for key, child in plan.children:
                counter += 1
                child_value = f"child{counter}"
                lines.extend(
                    (
                        f"{at}if not dict.__contains__({value}, {key!r}):",
                        f"{at}    return False",
                        f"{at}{child_value} = dict.__getitem__({value}, {key!r})",
                    )
                )
                emit(child_value, child, depth)
        if plan.items is not None:
            counter += 1
            item_value = f"item{counter}"
            lines.extend(
                (
                    f"{at}if {kind} is not list:",
                    f"{at}    return False",
                    f"{at}for {item_value} in {value}:",
                )
            )
            emit(item_value, plan.items, depth + 4)

    for name, plan in read_set.roots:
        counter += 1
        root_value = f"root{counter}"
        lines.extend(
            (
                f"{pad}if not dict.__contains__(variables, {name!r}):",
                f"{pad}    return False",
                f"{pad}{root_value} = dict.__getitem__(variables, {name!r})",
            )
        )
        emit(root_value, plan, indent)
    lines.append(f"{pad}return True")
    return lines


_READSET_TRUTH_TYPES = frozenset((str, int, bool, type(None), float, list, dict))
_READSET_ATTR_VALUE_TYPES = frozenset((str, int, bool, type(None), float))


def _readset_safe_attrs(value: dict[object, object]) -> bool:
    """Check one exact dict read by the root c-bind: str names and finite plain scalar values."""
    for name, item in dict.items(value):
        item_type = type(item)
        if type(name) is not str or item_type not in _READSET_ATTR_VALUE_TYPES:
            return False
        if item_type is float and not math.isfinite(cast("float", item)):
            return False
    return True


def _simple_json_readset_is_plain(variables: object, read_set: _SimpleJsonReadSet) -> bool:
    """Validate only values the generated evaluator or root c-bind will read."""
    if type(variables) not in {dict, _ConstMapping}:
        return False
    for target in read_set.loop_targets:
        if dict.__contains__(cast("dict[object, object]", variables), target):
            return False
    for name, plan in read_set.roots:
        if not dict.__contains__(cast("dict[object, object]", variables), name):
            return False
        value = dict.__getitem__(cast("dict[str, object]", variables), name)
        if not _simple_json_read_node_is_plain(value, plan):
            return False
    return True


def _simple_json_read_node_is_plain(value: object, plan: _SimpleJsonReadNode) -> bool:
    value_type = type(value)
    plain_scalar_types = _simple_json_plain_scalar_types() if "scalar" in plan.kinds else frozenset()
    if "scalar" in plan.kinds:
        if value_type not in {str, int, bool, type(None), float}:
            return False
        if value_type is not type(None) and value_type not in plain_scalar_types:
            return False
    if "scalar" in plan.kinds and value_type is float and not math.isfinite(cast("float", value)):
        return False
    if "list" in plan.kinds and value_type is not list:
        return False
    if "truth" in plan.kinds:
        if value_type not in {str, int, bool, type(None), float, list, dict}:
            return False
        if value_type is float and not math.isfinite(cast("float", value)):
            return False
    if "safe_attrs_or_none" in plan.kinds and value_type not in {dict, type(None)}:
        return False
    if "safe_attrs_or_none" in plan.kinds and value_type is dict:
        for name, item in dict.items(cast("dict[object, object]", value)):
            item_type = type(item)
            if type(name) is not str or item_type not in {str, int, bool, type(None), float}:
                return False
            if item_type is float and not math.isfinite(cast("float", item)):
                return False
    if "safe_attrs" in plan.kinds:
        if value_type is not dict:
            return False
        for name, item in dict.items(cast("dict[object, object]", value)):
            item_type = type(item)
            if type(name) is not str or item_type not in {str, int, bool, type(None), float}:
                return False
            if item_type is float and not math.isfinite(cast("float", item)):
                return False
    if plan.children:
        if value_type is not dict:
            return False
        mapping = cast("dict[object, object]", value)
        for key, child in plan.children:
            if not dict.__contains__(mapping, key):
                return False
            if not _simple_json_read_node_is_plain(dict.__getitem__(mapping, key), child):
                return False
    if plan.items is not None:
        if value_type is not list:
            return False
        for item in cast("list[object]", value):
            if not _simple_json_read_node_is_plain(item, plan.items):
                return False
    return True


_SIMPLE_JSON_SCALAR_TYPES = (str, int, bool, float)


@dataclass(slots=True)
class _SimpleJsonScalarCache:
    key: tuple[object, ...] | None = None
    plain_types: frozenset[type[object]] = frozenset()


_SIMPLE_JSON_PLAIN_SCALAR_CACHE = _SimpleJsonScalarCache()


def _simple_json_plain_scalar_types() -> frozenset[type[object]]:
    """Return scalars still using default renderer dispatch, keyed by ABC state."""
    import citry.citry_render as render_module  # noqa: PLC0415

    cache = _SIMPLE_JSON_PLAIN_SCALAR_CACHE
    cache_key = (
        abc.get_cache_token(),
        render_module.ComponentLike,
        render_module.CitryElement,
        render_module.CitryRender,
    )
    if cache_key != cache.key:
        cache.plain_types = frozenset(
            kind for kind in _SIMPLE_JSON_SCALAR_TYPES if render_module._default_value_dispatch_for(kind)
        )
        cache.key = cache_key
    return cache.plain_types


def _evaluation_only_operations(operations: tuple[object, ...]) -> tuple[object, ...]:
    """Drop static materialization visits while retaining dynamic branch/loop decisions."""
    selected: list[object] = []
    for operation in operations:
        if isinstance(operation, (_Static, _Close)):
            continue
        if isinstance(operation, _Open) and operation.static is not None:
            continue
        if isinstance(operation, _If):
            selected.append(
                _If(
                    operation.node,
                    operation.key,
                    tuple(_evaluation_only_operations(branch) for branch in operation.branches),
                )
            )
        elif isinstance(operation, _For):
            selected.append(
                _For(
                    operation.node,
                    operation.key,
                    _evaluation_only_operations(operation.body),
                    _evaluation_only_operations(operation.empty),
                )
            )
        else:
            selected.append(operation)
    return tuple(selected)


class LeafProgramNode(Node):
    """Evaluate a cached leaf program once into occurrence data or typed fallback output."""

    def __init__(
        self,
        fragment: LeafProgramFragment,
        operations: tuple[object, ...],
        evaluation_operations: tuple[object, ...],
    ) -> None:
        self.fragment = fragment
        self.operations = operations
        # Keep the full plan for fallback materialization. Normal evaluation
        # skips static/close visits while preserving branch and loop decisions.
        self.evaluation_operations = evaluation_operations
        # Cache generated code only when this leaf's source operations fit the
        # bounded evaluator; unsupported operations keep the ordinary path.
        self._simple_json_program: _SimpleJsonProgram | None = None
        self._simple_json_has_dynamic_attributes = False
        self._simple_json_has_spread = False
        self._simple_json_has_i18n_spread = False
        self._simple_json_has_i18n_attrs = False
        self._simple_json_compile_attempted = False
        # The template half of the simple='vue' check depends only on this
        # immutable node, so it is computed on first use and reused. None
        # means not computed yet.
        self._static_instance_free_template_supported: bool | None = None
        # The simple='vue' row HTML writer, built the first time serialize
        # asks for a row's HTML; None after an attempt means the template's
        # root markers could not be placed at compile time. The bound method
        # is created once here, so each occurrence only stores a reference.
        self._row_html_writer: _RowHtmlWrite | None = None
        self._row_html_writer_attempted = False
        self._write_row_html_method = self._write_row_html

    def supports_static_instance_free(self, component_class: type[Any]) -> bool:
        """Whether this leaf is a static, context-free Vue definition candidate."""
        return self.static_instance_free_template_supported() and self.static_instance_free_hooks_supported(
            component_class.citry.extensions
        )

    def static_instance_free_template_supported(self) -> bool:
        """Whether this template alone fits the context-free evaluator; computed once per node."""
        supported_template = self._static_instance_free_template_supported
        if supported_template is None:
            supported_template = self._compute_static_instance_free_template_supported()
            self._static_instance_free_template_supported = supported_template
        return supported_template

    def static_instance_free_hooks_supported(self, extensions: Any) -> bool:
        """Whether the engine's attribute hooks leave this template's evaluator output unchanged."""
        # The engine, not the template, decides these, so the caller treats a
        # False answer as a reason to render ordinarily rather than an error.
        if self._simple_json_has_dynamic_attributes and extensions.has_attrs_resolved_hook(runtime_candidate=False):
            return False
        return not (self._simple_json_has_spread and not _simple_vue_spread_hooks_supported(extensions))

    def _compute_static_instance_free_template_supported(self) -> bool:
        """Compile the evaluator and walk the plan for operations it cannot run."""
        if not self._simple_json_compile_attempted:
            self._simple_json_compile_attempted = True
            simple_operations = _compile_simple_json_operations(
                self.evaluation_operations,
                allow_instance_free_spread=True,
            )
            try:
                if simple_operations is not None:
                    self._simple_json_has_dynamic_attributes = _simple_json_has_dynamic_attributes(simple_operations)
                    self._simple_json_has_spread = _simple_json_has_spread(simple_operations)
                    self._simple_json_has_i18n_spread = _simple_json_has_i18n_spread(simple_operations)
                    self._simple_json_has_i18n_attrs = _simple_json_has_i18n_attrs(simple_operations)
                    self._simple_json_program = _SimpleJsonCodegen(simple_operations).build()
            except (SyntaxError, ValueError):
                self._simple_json_program = None
        if self._simple_json_program is None or self._simple_json_has_i18n_spread or self._simple_json_has_i18n_attrs:
            return False

        def supported(operations: Sequence[object]) -> bool:
            for operation in operations:
                if isinstance(operation, (_Static, _Close, _Text)):
                    continue
                if isinstance(operation, _Open):
                    if operation.node._has_spread:
                        dynamic_attributes = [
                            attr for attr in operation.node.attrs if attr.key.startswith("c-") and attr.key != "c-bind"
                        ]
                        if (
                            operation.key_key is not None
                            or operation.control_key is not None
                            or operation.runtime_events_key is not None
                            or operation.node._event_bindings
                            or operation.node._poll_bindings
                            or operation.node._control_bindings
                            or operation.node.element_metadata
                            or dynamic_attributes
                        ):
                            return False
                        continue
                    if (
                        operation.key_key is not None
                        or operation.control_key is not None
                        or operation.runtime_events_key is not None
                        or operation.spread_renderer is not None
                        or operation.node._has_spread
                        or operation.node._event_bindings
                        or operation.node._poll_bindings
                        or operation.node._control_bindings
                        or operation.node._runtime_events_candidate
                        or operation.node._runtime_control_candidate
                    ):
                        return False
                    continue
                if isinstance(operation, _If):
                    if any(not supported(branch) for branch in operation.branches):
                        return False
                    continue
                if isinstance(operation, _For):
                    if not supported(operation.body) or not supported(operation.empty):
                        return False
                    continue
                if isinstance(operation, _Call):
                    continue
                return False
            return True

        return supported(self.operations)

    def _row_html_writer_function(self) -> _RowHtmlWrite | None:
        """
        Return the function that writes this template's row HTML, building it once.

        The evaluator runs a copy of these operations without the static
        pieces, which keeps the same opening objects and ``c-if``/``c-for``
        keys, so every record this writer looks up exists.
        """
        if not self._row_html_writer_attempted:
            writer = None
            # A template that calls child components has another
            # component's HTML inside its own, which serialize writes through
            # the child's frame, so it keeps the per-row path.
            operations = (
                None
                if self.fragment.calls
                else _compile_simple_json_operations(self.operations, allow_instance_free_spread=True)
            )
            plan = None if operations is None else _materialized_row_plan(operations)
            if operations is not None and plan is not None:
                try:
                    writer = _RowHtmlWriterCodegen(operations, plan).build()
                except (SyntaxError, RecursionError, ValueError):
                    # A template too large to compile keeps the per-row path.
                    writer = None
            # Publish the writer before the flag, so a concurrent serialize
            # sees either nothing yet (and builds it too) or the final value.
            self._row_html_writer = writer
            self._row_html_writer_attempted = True
        return self._row_html_writer

    def _write_row_html(
        self,
        data: dict[str, object],
        resolved_opens: dict[Any, Any],
    ) -> tuple[str, ...] | None:
        """
        Write one occurrence's HTML from its recorded values, or return None for the per-row path.

        Serialize calls this when it builds the frame that holds the row. The
        answer is decided before serialize writes anything for the row, and
        writing touches only local lists, so a None costs nothing but the
        attempt.
        """
        if not _default_row_formatting():
            return None
        writer = self._row_html_writer_function()
        if writer is None:
            return None
        row_html: list[str | None] = []
        row_marks: list[int] = []
        try:
            writer(data, resolved_opens, row_html, row_marks)
        except Exception:  # noqa: BLE001 - the per-row path formats the row again and raises there
            return None
        return _row_html_segments(row_html, row_marks)

    def render_static_instance_free(
        self,
        variables: dict[str, object],
        *,
        component_name: str,
        calls: dict[tuple[int, str], tuple[_Call, dict[str, object], str | None]] | None = None,
    ) -> PreparedLeafProgram:
        """
        Evaluate one admitted ``simple='vue'`` template without component or render context.

        For a template that calls child components, ``calls`` receives one
        entry per call the evaluation made, in template order: the call, its
        inputs and its ``#c-key``. The returned leaf carries an empty
        ``call_children`` that the caller fills with those children.
        """
        program = self._simple_json_program
        if program is None:
            raise TypeError("simple='vue' leaf is not eligible for the context-free evaluator")
        if not program.readset_preflight(None, variables):
            raise TypeError("simple='vue' template data is not safe for the context-free evaluator")
        data: dict[str, object] = {}
        resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen] = {}
        token = _SIMPLE_VUE_ERROR_COMPONENT.set(component_name)
        try:
            # Evaluation only records values. The row HTML, when an output
            # needs it, is written later from these records by the writer.
            # The context-free path never uses ``special`` for text, so the
            # generated call operations record into it.
            call_sink = cast("dict[tuple[int, str], RenderPart]", {} if calls is None else calls)
            program.evaluate(None, variables, data, data, [], call_sink, resolved_opens)
        finally:
            _SIMPLE_VUE_ERROR_COMPONENT.reset(token)
        return PreparedLeafProgram(
            self.fragment,
            data,
            self.operations,
            (),
            resolved_opens,
            row_html_writer=self._write_row_html_method,
            prepared_data_evaluated_plain=True,
            call_children=LeafCallChildren([], {}) if self.fragment.calls else None,
        )

    def render(self, context: CitryContext) -> RenderPart:
        data: dict[str, object] = {}
        root_data = data
        vue_errors: list[str] = []
        special: dict[tuple[int, str], RenderPart] = {}
        resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen] = {}
        component = context.component
        if not self._simple_json_compile_attempted:
            self._simple_json_compile_attempted = True
            simple_operations = _compile_simple_json_operations(self.evaluation_operations)
            try:
                if simple_operations is not None:
                    self._simple_json_has_dynamic_attributes = _simple_json_has_dynamic_attributes(simple_operations)
                    self._simple_json_has_i18n_spread = _simple_json_has_i18n_spread(simple_operations)
                    self._simple_json_program = _SimpleJsonCodegen(simple_operations).build()
            except (SyntaxError, ValueError):
                # Unsupported templates keep the established evaluator.
                self._simple_json_program = None
        simple_program = self._simple_json_program
        if simple_program is not None:
            extensions = component.citry.extensions if component is not None else None
            if self._simple_json_has_i18n_spread or (
                extensions is not None
                and extensions.has_hook("on_attrs_resolved")
                and self._simple_json_has_dynamic_attributes
            ):
                # These resolvers can rewrite an opening after the read-set guard.
                simple_program = None
        if simple_program is not None and simple_program.readset_preflight(context):
            simple_program.evaluate(
                context,
                context.variables,
                data,
                root_data,
                vue_errors,
                special,
                resolved_opens,
            )
        else:
            _evaluate(
                self.evaluation_operations,
                context,
                data,
                root_data,
                vue_errors,
                special,
                resolved_opens,
            )
        if special:
            parts: list[RenderPart] = []
            _materialize_typed(
                self.operations,
                data,
                root_data,
                special,
                resolved_opens,
                parts,
            )
            return CitryRender(parts=parts, context=context)
        return PreparedLeafProgram(
            self.fragment,
            data,
            self.operations,
            tuple(vue_errors),
            resolved_opens,
        )


def compile_leaf_program(
    body: Sequence[object],
    *,
    allow_i18n_passthrough: bool = False,
    allow_static_only: bool = False,
    allow_calls: bool = False,
) -> LeafProgramNode | None:
    """
    Compile a final transformed leaf body, or return None for the general renderer.

    ``allow_calls`` admits slot-free child component calls. Only the
    instance-free ``simple='vue'`` renderer sets it, because only it knows
    how to render the children the evaluator records.
    """
    compiler = _Compiler(allow_i18n_passthrough=allow_i18n_passthrough, allow_calls=allow_calls)
    operations = compiler.compile_body(body)
    if operations is None or (not compiler.has_data_ops and not allow_static_only) or not compiler.safe_body:
        return None
    evaluation_operations = _evaluation_only_operations(operations)
    return LeafProgramNode(
        LeafProgramFragment(
            "".join(compiler.output),
            cast("tuple[dict[str, object], ...]", tuple(compiler.element_bindings)),
            frozenset(compiler.browser_requirements),
            safe_body=True,
            runtime_event_sites=cast("tuple[dict[str, object], ...]", tuple(compiler.runtime_event_sites)),
            calls=tuple(compiler.calls),
        ),
        operations,
        evaluation_operations,
    )


class _Compiler:
    def __init__(
        self,
        *,
        allow_i18n_passthrough: bool = False,
        in_loop: bool = False,
        allow_calls: bool = False,
    ) -> None:
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
        self.allow_calls = allow_calls
        self.calls: list[_Call] = []
        self.call_index = 0
        # Tags of the elements open at the current position, so each call
        # records the elements around it (the assembler checks raw-text and
        # SVG parents against it, as it does for an ordinary call).
        self.open_tags: list[str] = []

    def append(self, value: str) -> None:
        self.output.append(value)
        self.byte_position += len(value.encode("utf-8"))

    def compile_body(self, body: Sequence[object]) -> tuple[object, ...] | None:
        operations: list[object] = []
        skip_close_tag: str | None = None
        index = 0
        while index < len(body):
            item = body[index]
            if (
                skip_close_tag is not None
                and isinstance(item, PreparedElementCloseNode)
                and item.tag == skip_close_tag
            ):
                skip_close_tag = None
                index += 1
                continue
            skip_close_tag = None
            operation = self.compile_item(item)
            if operation is None:
                return None
            operations.append(operation)
            if isinstance(operation, _Open) and operation.node.is_self_closing:
                skip_close_tag = operation.node.tag
            index += 1
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
            self.append(f"{{{{ $citryPrepared.{key} }}}}")
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
            if self.open_tags and self.open_tags[-1] == value.tag:
                self.open_tags.pop()
            return _Close(value)
        if type(item) is ComponentNode and self.allow_calls:
            return self._compile_call(item)
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
        # A leaf template would write a `#c-ignore` element's contents as
        # ordinary Vue nodes, which Vue then updates. The general assembler
        # writes them as HTML the browser keeps.
        if any(item[0] == "morph" for item in node.element_metadata):
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
        # A native form control marks which of its properties an authored or
        # Python binding owns, so the browser keeps a user's unsaved edit
        # only in the properties nothing binds.
        native_marker = (
            vue_owned_native_marker(
                vue_owned_native_properties(
                    node.tag,
                    node._authored_vue_attrs,
                    dynamic_keys,
                    has_spread=node._has_spread,
                )
            )
            if is_native_state_tag(node.tag)
            else ""
        )
        if native_marker:
            attrs.append(native_marker)
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
            attrs.append(f'v-citry-runtime-events="$citryEvents.runtimeEvents($citryPrepared.{runtime_events_key})"')
        event_names = [str(binding["event"]) for binding in node._event_bindings]
        if len(event_names) != len(set(event_names)):
            self.safe_body = False
        for binding in node._event_bindings:
            modifiers = [name for name in ("prevent", "stop", "self", "once") if binding[name] is True]
            if binding["key"] is not None:
                modifiers.append(str(binding["key"]))
            suffix = "" if not modifiers else "." + ".".join(modifiers)
            args = binding["args"]
            authored_args = _generated_event_args(args)
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
            attrs.append(f'v-citry-control="$citryEvents.controls($citryPrepared.{control_key})"')
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
            # Authored attributes lead `attrs`, so their index is valid here.
            spread_index = prepared_spread_index(authored_attrs)
            spread = f'v-bind="$citryPrepared.{attrs_key}"'
            if spread_index is None:
                attrs.append(spread)
            else:
                attrs.insert(spread_index, spread)
        if node.element_metadata and any(item and item[0] == "key" for item in node.element_metadata):
            if self.in_loop:
                self.safe_body = False
            self.has_data_ops = True
            key_key = f"citryKey{self.key_index}"
            self.key_index += 1
            attrs.append(f':key="$citryPrepared.{key_key}"')
        rendered_attrs = "" if not attrs else " " + " ".join(attrs)
        ending = "/>" if node.is_self_closing else ">"
        self.append(f"<{node.tag}{rendered_attrs}{ending}")
        if not node.is_self_closing and not node.is_void:
            self.open_tags.append(node.tag)
        if attrs_key is not None or key_key is not None or runtime_events_key is not None:
            element_binding: _ElementBindingDeclaration = {
                "sourceStart": start,
                "sourceEnd": self.byte_position,
                "attrsBindingKey": attrs_key,
                "keyBindingKey": key_key,
                "runtimeEventsBindingKey": runtime_events_key,
            }
            self.element_bindings.append(element_binding)
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

    def _compile_call(self, node: ComponentNode) -> _Call | None:
        """
        Admit a child call that the instance-free renderer can hand to the render loop.

        The call must pass no content (a body would be a slot fill), use
        plain inputs (no ``c-bind`` spread and no Vue bindings on the
        component tag), and carry at most a ``#c-key``. Anything else keeps
        the template off the instance-free path.
        """
        if (
            node.body
            or node.name == "element"
            or not node._has_plain_component_inputs
            or (node.metadata is not None and (node._metadata_locus != "range" or node.morph_mode is not None))
            or any(type(attr) not in {StaticHtmlAttr, ExprHtmlAttr} for attr in node.attrs)
        ):
            return None
        self.has_data_ops = True
        key = f"citryCall{self.call_index}"
        self.call_index += 1
        call = _Call(
            node,
            key,
            self.byte_position,
            tuple(self.open_tags),
            unconditional=not self.in_loop and not self.scope_steps,
        )
        self.calls.append(call)
        return call

    def _compile_if(self, node: IfNode) -> _If | None:
        self.has_data_ops = True
        key = f"citryIf{self.if_index}"
        self.if_index += 1
        branches: list[tuple[object, ...]] = []
        for index, branch in enumerate(node.branches):
            directive = "v-if" if index == 0 else "v-else-if"
            self.append(f'<template {directive}="$citryPrepared.{key} === {index}">')
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
        self.append(f'<template v-for="$citryPrepared in $citryPrepared.{key}">')
        child = _Compiler(
            allow_i18n_passthrough=self.allow_i18n_passthrough,
            in_loop=True,
            allow_calls=self.allow_calls,
        )
        child.open_tags = list(self.open_tags)
        child.scope_steps = [*self.scope_steps, {"kind": "each", "key": key}]
        compiled_body = child.compile_body(node.branches[0][2])
        if compiled_body is None:
            return None
        offset = self.byte_position
        self.append("".join(child.output))
        self.element_bindings.extend(_rebase(child.element_bindings, offset))
        self.runtime_event_sites.extend(_rebase(child.runtime_event_sites, offset))
        # A call inside the loop is never unconditional, so the assembler
        # never reads its offset; it is rebased only to stay truthful.
        self.calls.extend(replace(call, offset=call.offset + offset) for call in child.calls)
        self.has_data_ops = self.has_data_ops or child.has_data_ops
        self.browser_requirements.update(child.browser_requirements)
        self.safe_body = self.safe_body and child.safe_body
        self.append("</template>")
        empty: tuple[object, ...] = ()
        if len(node.branches) > 1:
            self.append(f'<template v-if="$citryPrepared.{key}.length === 0">')
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
    transparent_i18n_wrapper = _transparent_i18n_wrapper(node, renderer)
    if (
        type(node) is not PreparedElementOpenNode
        or not node._has_spread
        or node._authored_vue_attrs
        or node._event_bindings
        or node._poll_bindings
        or node._control_bindings
        or (not transparent_i18n_wrapper and node._runtime_control_candidate)
        or (not transparent_i18n_wrapper and node._runtime_events_candidate)
        or node.element_metadata
    ):
        return None
    if renderer is node or transparent_i18n_wrapper:
        return renderer
    return None


def _transparent_i18n_wrapper(node: PreparedElementOpenNode, renderer: Node) -> bool:
    if (
        type(renderer) is not I18nBindingElementAttrsNode
        or renderer.original is not node
        or renderer.has_static_binding
    ):
        return False
    render_method = getattr(renderer, "render", None)
    return (
        getattr(render_method, "__self__", None) is renderer
        and getattr(render_method, "__func__", None) is I18nBindingElementAttrsNode.render
    )


def _spread_passthrough_is_live(renderer: Node, context: CitryContext, node: PreparedElementOpenNode) -> bool:
    if type(renderer) is PreparedElementOpenNode:
        return renderer is node
    if not _transparent_i18n_wrapper(node, renderer) or context.component is None:
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
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
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
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
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
                    # Fixed attributes record the same dict for data and for
                    # the opening; the spread branch below may record a
                    # _SpreadResolvedOpen instead, hence the wider type.
                    resolved_open: PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen = open_value
                except Exception as error:
                    _attach_error(error, operation.node, context)
                    raise
            elif operation.spread_renderer is not None and _spread_passthrough_is_live(
                operation.spread_renderer, context, operation.node
            ):
                try:
                    resolved, extension_validated = operation.node._resolve_for_output(context)
                    projected_attrs = (
                        _spread_project_attrs(operation.node, resolved)
                        if type(operation.spread_renderer) is I18nBindingElementAttrsNode
                        else None
                    )
                    if projected_attrs is not None:
                        open_value = projected_attrs
                        resolved_open = _SpreadResolvedOpen(resolved, context, extension_validated)
                    else:
                        fallback_value = operation.node._prepared_from_resolved(
                            resolved,
                            context=context,
                            extension_validated=extension_validated,
                        )
                        open_value = _spread_data_attrs(operation.node, fallback_value)
                        resolved_open = fallback_value
                    if vue_render_active():
                        _reject_executable_dynamic_attrs(open_value, tag=operation.node.tag)
                    validation_error = _validate_data_attrs(open_value, tag=operation.node.tag)
                    if validation_error is not None:
                        vue_errors.append(validation_error)
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
                resolved_open = rendered_open
                open_value = rendered_open

            resolved_opens.setdefault((id(data), id(operation)), resolved_open)
            if operation.attrs_key is not None:
                if isinstance(open_value, PreparedElementOpen):
                    attrs = (
                        _spread_data_attrs(operation.node, open_value)
                        if operation.node._has_spread
                        else dict(open_value.data_attrs)
                    )
                else:
                    attrs = open_value
                # Vue must set the same attribute text Python's HTML writes.
                data[operation.attrs_key] = _vue_attribute_map(attrs)
            if operation.key_key is not None:
                if not isinstance(resolved_open, PreparedElementOpen):
                    raise AssertionError("prepared key metadata requires a structured opening")
                metadata = dict(resolved_open.element_metadata)
                data[operation.key_key] = metadata["key"]
            if operation.control_key is not None:
                control_value = (
                    ",".join(str(binding["id"]) for binding in resolved_open.control_bindings)
                    if isinstance(resolved_open, PreparedElementOpen)
                    else ""
                )
                data[operation.control_key] = control_value
            if operation.runtime_events_key is not None:
                runtime_events_value = (
                    ",".join(
                        str(binding["id"])
                        for binding in (*resolved_open.runtime_event_bindings, *resolved_open.runtime_poll_bindings)
                    )
                    if isinstance(resolved_open, PreparedElementOpen)
                    else ""
                )
                data[operation.runtime_events_key] = runtime_events_value
            if isinstance(resolved_open, PreparedElementOpen) and (
                resolved_open.event_bindings or resolved_open.runtime_event_bindings
            ):
                events = root_data.setdefault("eventBindings", {})
                if not isinstance(events, dict):
                    raise AssertionError("leaf event binding container changed type")
                for binding in resolved_open.event_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = events.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf event binding id has conflicting metadata")
                for binding in resolved_open.runtime_event_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = events.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf runtime event binding id has conflicting metadata")
            if isinstance(resolved_open, PreparedElementOpen) and (
                resolved_open.poll_bindings or resolved_open.runtime_poll_bindings
            ):
                polls = root_data.setdefault("pollBindings", {})
                if not isinstance(polls, dict):
                    raise AssertionError("leaf poll binding container changed type")
                for binding in resolved_open.poll_bindings:
                    polls[str(binding["id"])] = dict(binding)
                for binding in resolved_open.runtime_poll_bindings:
                    binding_id = str(binding["id"])
                    serialized = dict(binding)
                    previous = polls.setdefault(binding_id, serialized)
                    if previous != serialized:
                        raise ValueError("one leaf runtime poll binding id has conflicting metadata")
            if isinstance(resolved_open, PreparedElementOpen) and resolved_open.control_bindings:
                controls = root_data.setdefault("controlBindings", {})
                if not isinstance(controls, dict):
                    raise AssertionError("leaf control binding container changed type")
                for binding in resolved_open.control_bindings:
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
                _evaluate(
                    operation.branches[selected],
                    context,
                    data,
                    root_data,
                    vue_errors,
                    special,
                    resolved_opens,
                )
        elif isinstance(operation, _For):
            records: list[dict[str, object]] = []
            rendered_any = False
            try:
                for _body, child_context in operation.node.iter_bodies(context):
                    if child_context is context:
                        _evaluate(
                            operation.empty,
                            context,
                            data,
                            root_data,
                            vue_errors,
                            special,
                            resolved_opens,
                        )
                        continue
                    rendered_any = True
                    record: dict[str, object] = {}
                    records.append(record)
                    _evaluate(
                        operation.body,
                        child_context,
                        record,
                        root_data,
                        vue_errors,
                        special,
                        resolved_opens,
                    )
            except Exception as error:
                _attach_error(error, operation.node, context)
                raise
            data[operation.key] = records
            if not rendered_any and not operation.empty:
                data[operation.key] = []
        else:
            raise TypeError(f"unknown leaf operation: {type(operation).__name__}")


def _attach_error(error: Exception, node: Node, context: CitryContext | None) -> None:
    if context is None:
        source = getattr(node, "source", None)
        position = getattr(node, "position", None)
        if isinstance(source, str) and isinstance(position, tuple) and len(position) == 2:
            from citry.util.exception import set_template_position_error_message  # noqa: PLC0415

            set_template_position_error_message(
                error,
                source,
                position,
                _SIMPLE_VUE_ERROR_COMPONENT.get() or "component",
                None,
            )
        return
    from citry.component_render import _attach_template_position  # noqa: PLC0415

    _attach_template_position(error, node, context)


def _validate_open(value: PreparedElementOpen) -> str | None:
    data_targets = {_html_attr_identity(name): name for name in value.data_attrs}
    for name in value.data_attrs:
        if is_vue_directive_name(name):
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
    conflict = conflicting_attribute_targets(source_targets, data_targets)
    if conflict:
        names = [f"{source_targets[identity]!r} / {data_targets[identity]!r}" for identity in conflict]
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
        if is_vue_directive_name(name):
            return (
                f"Python-resolved attribute {name!r} on <{tag}> cannot introduce Vue syntax; "
                "Vue directives and bindings must be authored statically in the template."
            )
        normalized = name.casefold()
        if normalized in {"innerhtml", "outerhtml", "textcontent", "innertext"} or normalized.startswith("on"):
            return f"prepared dynamic DOM property is unsafe for the bounded Vue target: {name!r}"
    return None


def _validate_context_free_introduced_variables(
    tag_name: str,
    names: tuple[str, ...],
    variables: dict[str, object],
) -> None:
    """Apply the ordinary c-for shadowing guard to an exact JSON root map."""
    introduced: set[str] = set()
    for name in names:
        if name in introduced:
            raise RuntimeError(
                f"Cannot define variable {name!r} more than once in tag '<{tag_name}>'. "
                "Variable shadowing is not allowed, use a different name."
            )
        introduced.add(name)
        if name in variables:
            raise RuntimeError(
                f"Cannot define variable {name!r} in tag '<{tag_name}>' - variable name is already taken. "
                "Variable shadowing is not allowed, use a different name."
            )


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


def _spread_with_source_attrs(
    node: PreparedElementOpenNode,
    resolved: dict[str, object],
) -> dict[str, object]:
    """Resolve a plain root spread with the ordinary source-order merge rules."""
    from citry.client_directives import (  # noqa: PLC0415
        CLIENT_PROPS_ATTR,
        apply_client_props_contribution,
        has_client_props_key,
    )

    items: list[tuple[str, object]] = []
    for attr, resolved_key in zip(node.attrs, node._resolved_keys, strict=True):
        if attr.key == "c-bind":
            for key, value in resolved.items():
                name = validate_html_attr_name(key, where=f"c-bind on <{node.tag}>")
                _reject_dynamic_translation_binding(name, tag_name=node.tag)
                _reject_reserved_events_attr(name, tag_name=node.tag)
                items.append((name, const_value(value)))
        elif type(attr) is StaticHtmlAttr:
            items.append((resolved_key, attr.value))
        else:
            raise TypeError("simple='vue' c-bind cannot be combined with dynamic server attributes")

    merged = _merge_resolved_attrs(items)
    for name in merged:
        if name.startswith("#c-"):
            raise RuntimeError(
                f"{name!r} arrived on <{node.tag}> through an attribute spread. "
                "'#c-*' framework attributes are template-authored only."
            )
    if has_client_props_key(merged, tag_name=node.tag):
        apply_client_props_contribution(
            merged,
            merged[CLIENT_PROPS_ATTR],
            tag_name=node.tag,
            component_boundary=False,
        )
    return {name: value for name, value in merged.items() if value is not None and value is not False}


def _spread_project_attrs(
    node: PreparedElementOpenNode,
    resolved: dict[str, object],
) -> dict[str, object] | None:
    """Project safe wrapper spreads directly, retaining source-order semantics."""
    # Keep any case that needs PreparedElementOpen's runtime metadata, security
    # checks, or error behavior on its established path.
    if any(type(name) is not str for name in resolved):
        return None
    if _validate_data_attrs(resolved, tag=node.tag) is not None:
        return None
    lowered = {name.lower() for name in resolved}
    if lowered & {"data-citry-runtime-control", "data-citry-runtime-events"}:
        return None
    if any(name.startswith("data-cev-") for name in lowered):
        return None

    # This is the same merge used by _prepared_from_resolved. Keep source attrs
    # separate because their original spelling and quoting are wire-significant.
    data_attrs = merge_attrs(resolved)
    dynamic_keys = {attr.key.removeprefix("c-") for attr in node.attrs if not isinstance(attr, StaticHtmlAttr)}
    preserved_source: dict[str, StaticHtmlAttr] = {}
    for attr, _source_text in node._static_source_attrs:
        if (
            attr.key not in dynamic_keys
            and attr.key in data_attrs
            and type(data_attrs[attr.key]) is type(attr.value)
            and data_attrs[attr.key] == attr.value
        ):
            preserved_source[attr.key] = attr

    # Match _prepared_from_resolved's single pass so a preserved source attr
    # keeps its first-contribution position when a spread also supplied it.
    projected: dict[str, object] = {}
    for name in data_attrs:
        source_attr = preserved_source.get(name)
        if source_attr is not None:
            projected[name] = "" if source_attr.value is True else source_attr.value
        elif include_prepared_attribute(data_attrs[name]):
            projected[name] = data_attrs[name]
    return projected


# A template whose c-bind produces a new key set every row would otherwise
# grow a plan per row. Past this many key sets, rows take the full path. The
# first key sets stay for the template's life; a concurrent first render may
# store a few more than the limit, which only costs memory.
_ROOT_SPREAD_PLAN_LIMIT = 32
_ROOT_SPREAD_VALUE_TYPES = frozenset((str, int, bool, float, type(None)))


@dataclass(frozen=True, slots=True)
class _RootSpreadEntry:
    """One attribute of a root c-bind opening, in the order the merge emits it."""

    name: str
    # A static attribute's projected value and prepared attribute never
    # change; ``is_static`` False means the value comes from the spread row.
    is_static: bool
    projected: object = None
    has_projected: bool = False
    prepared: PreparedAttribute | None = None
    span: tuple[int, int] = (0, 0)


@dataclass(slots=True)
class _RootSpreadPlans:
    """
    Per-template cache of the key-dependent layout of one root ``c-bind`` opening.

    The generated evaluator owns one instance per root spread, so the cache
    lives exactly as long as the compiled template. Each entry is keyed by the
    spread's key tuple in row order; None records a key set that needs the
    full per-row merge.
    """

    plans: dict[tuple[str, ...], tuple[_RootSpreadEntry, ...] | None] = field(default_factory=dict)


def _root_spread_plan(node: PreparedElementOpenNode, keys: tuple[str, ...]) -> tuple[_RootSpreadEntry, ...] | None:
    """
    Resolve everything about one c-bind key set that does not depend on values.

    Returns None when a name is invalid or reserved, when two names share an
    HTML identity, when class, style, client props, or #c-* names are
    involved, when the root has another dynamic attribute, or when a name is
    reserved for runtime markers (data-citry-runtime-*, data-cev-*). Those
    cases keep the full merge, which also raises their errors. An authored
    class or style on the root therefore always takes the full merge.
    """
    from citry.client_directives import is_client_props_key  # noqa: PLC0415

    items: list[tuple[str, bool, object]] = []
    for attr, resolved_key in zip(node.attrs, node._resolved_keys, strict=True):
        if attr.key == "c-bind":
            items.extend((key, False, None) for key in keys)
        elif type(attr) is StaticHtmlAttr:
            items.append((resolved_key, True, attr.value))
        else:
            return None
    names = [name for name, _is_static, _value in items]
    try:
        for name in keys:
            # The full merge validates spread names in this order; a failure
            # here sends the row there so it raises the same error.
            validate_html_attr_name(name, where=f"c-bind on <{node.tag}>")
            _reject_dynamic_translation_binding(name, tag_name=node.tag)
            _reject_reserved_events_attr(name, tag_name=node.tag)
        if any(is_client_props_key(name, tag_name=node.tag) for name in names):
            return None
    except (TypeError, ValueError, RuntimeError):
        return None
    identities = [_html_attr_identity(name) for name in names]
    # Distinct identities mean the merge keeps every item in order with its
    # own value, and a spread value can never replace a static one.
    if len(set(identities)) != len(identities) or {"class", "style"} & set(identities):
        return None
    if any(name.startswith("#c-") for name in names):
        return None
    # _spread_project_attrs checks the names that survive value filtering;
    # checking every name up front makes that check value-independent.
    if _validate_data_attrs(dict.fromkeys(names), tag=node.tag) is not None:
        return None
    lowered = {name.lower() for name in names}
    if lowered & {"data-citry-runtime-control", "data-citry-runtime-events"} or any(
        name.startswith("data-cev-") for name in lowered
    ):
        return None

    dynamic_keys = {attr.key.removeprefix("c-") for attr in node.attrs if not isinstance(attr, StaticHtmlAttr)}
    source_values = {attr.key: (attr, source_text) for attr, source_text in node._static_source_attrs}
    entries: list[_RootSpreadEntry] = []
    for name, is_static, value in items:
        span = node._data_attr_span(name)
        if not is_static:
            entries.append(_RootSpreadEntry(name, is_static=False, span=span))
            continue
        # Mirror the three full-path steps for a value known now: the merge
        # drops None/False, the projection restores a preserved source
        # attribute's authored value, and the opening keeps authored text for
        # an unchanged source attribute.
        if value is None or value is False:
            entries.append(_RootSpreadEntry(name, is_static=True))
            continue
        source = source_values.get(name)
        if (
            source is not None
            and name not in dynamic_keys
            and type(value) is type(source[0].value)
            and value == source[0].value
        ):
            # The opening keeps the authored text whenever the merged value
            # still equals the authored one, as _prepared_from_resolved
            # decides. The projection turns an authored boolean into "" for
            # the browser, so comparing the projected value instead would
            # write `hidden` as `hidden=""`.
            projected = "" if source[0].value is True else source[0].value
            prepared: PreparedAttribute | None = PreparedAttribute(name, "source", source[0].position, source[1])
        elif include_prepared_attribute(value):
            projected = value
            prepared = PreparedAttribute(name, "data", span, projected)
        else:
            entries.append(_RootSpreadEntry(name, is_static=True))
            continue
        entries.append(
            _RootSpreadEntry(name, is_static=True, projected=projected, has_projected=True, prepared=prepared)
        )
    return tuple(entries)


def _instance_free_root_spread(
    operation: _Open,
    resolved: dict[str, object],
    plans: _RootSpreadPlans,
) -> tuple[dict[str, object], PreparedElementOpen]:
    """
    Resolve one context-free root ``c-bind`` row into projected attrs and its opening.

    The result equals _spread_with_source_attrs, _spread_project_attrs and
    _prepared_open run in turn. A key set seen before reuses the result
    _root_spread_plan computed for it, so a row only filters and places its
    values.
    """
    node = operation.node
    keys = tuple(resolved)
    # The preflight that admitted this row proved every key an exact str, so
    # hashing the tuple runs no user code.
    if keys in plans.plans:
        plan = plans.plans[keys]
    elif len(plans.plans) < _ROOT_SPREAD_PLAN_LIMIT:
        plan = _root_spread_plan(node, keys)
        plans.plans[keys] = plan
    else:
        plan = None
    if plan is not None:
        projected: dict[str, object] = {}
        attributes: list[PreparedAttribute] = []
        for entry in plan:
            if entry.is_static:
                if entry.has_projected:
                    projected[entry.name] = entry.projected
                if entry.prepared is not None:
                    attributes.append(entry.prepared)
                continue
            value = resolved[entry.name]
            # The read-set check should admit only these exact scalars. If
            # another type reaches here, the full merge below handles it.
            if type(value) not in _ROOT_SPREAD_VALUE_TYPES:
                plan = None
                break
            if value is None or value is False:
                continue
            # Vue gets the text Python's HTML writes for this value.
            projected[entry.name] = _vue_attribute_value(value)
            attributes.append(PreparedAttribute(entry.name, "data", entry.span, value))
        if plan is not None:
            return projected, PreparedElementOpen(
                node.source,
                node.position,
                node.tag,
                tuple(attributes),
                node.is_void,
                node.is_self_closing,
                (),
                (),
                (),
            )
    merged = _spread_with_source_attrs(node, resolved)
    full_projected = _spread_project_attrs(node, merged)
    if full_projected is None:
        raise TypeError("simple='vue' c-bind contains unsupported or unsafe attributes")
    # The opening is built from the merged values, not the projection, so an
    # authored boolean attribute is recognized as unchanged and keeps its
    # authored text, as it does on the ordinary path. merge_attrs gives the
    # same result _spread_project_attrs computed from the same input, so the
    # names and their order match the projection.
    return _vue_attribute_map(full_projected), _prepared_open(operation, merge_attrs(merged))


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
    if value.call_children is not None:
        raise TypeError("a leaf that called child components needs static_leaf_parts_with_children")
    return cast("list[str]", static_leaf_parts_with_children(value))


@overload
def static_leaf_parts_with_children(
    value: PreparedLeafProgram,
    *,
    preserve_dynamic_text: Literal[False] = False,
) -> list[str | RenderPart]: ...


@overload
def static_leaf_parts_with_children(
    value: PreparedLeafProgram,
    *,
    preserve_dynamic_text: bool,
) -> list[str | RenderPart | PreparedStaticText]: ...


def static_leaf_parts_with_children(
    value: PreparedLeafProgram,
    *,
    preserve_dynamic_text: bool = False,
) -> list[str | RenderPart] | list[str | RenderPart | PreparedStaticText]:
    """
    Materialize static HTML, with each called child's render part at its call.

    Only a ``simple='vue'`` occurrence that called child components yields
    render parts; the caller writes each child through the child's own
    frame. Every other leaf yields only strings, except that
    ``preserve_dynamic_text`` wraps each dynamic text value in
    ``PreparedStaticText`` so the serializer can tell it apart from authored
    text (it needs that inside a textarea).
    """
    # The cached parts are already joined text, so they cannot say which text
    # was dynamic; the serializer asks for the marked form only when it must.
    if value.cached_static_parts is not None and not preserve_dynamic_text:
        cached: list[str | RenderPart] = list(value.cached_static_parts)
        return cached
    output: list[str | RenderPart | PreparedStaticText] = []
    _materialize(
        value.operations,
        value.prepared_data,
        value.resolved_opens,
        output,
        {} if value.call_children is None else value.call_children.by_site(),
        preserve_dynamic_text=preserve_dynamic_text,
    )
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
        # A called child's render part is looked up by its call site, the
        # same way a special text part is.
        {} if value.call_children is None else value.call_children.by_site(),
        value.resolved_opens,
        output,
        {} if value.call_children is None else value.call_children.run_types,
    )
    return output


def _materialize_typed(
    operations: tuple[object, ...],
    data: dict[str, object],
    root_data: dict[str, object],
    special: dict[tuple[int, str], RenderPart],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
    output: list[RenderPart],
    call_runs: dict[str, str] | None = None,
) -> None:
    for operation in operations:
        if isinstance(operation, _Static):
            output.append(operation.typed)
        elif isinstance(operation, _Text):
            special_value = special.get((id(data), operation.key))
            if special_value is not None:
                output.append(special_value)
            else:
                output.append(
                    PreparedTextValue(
                        operation.node.source,
                        operation.node.position,
                        data[operation.key],
                    )
                )
        elif isinstance(operation, _Open):
            resolved = operation.static or resolved_opens[(id(data), id(operation))]
            output.append(_prepared_open(operation, resolved))
            if operation.node.is_self_closing and not operation.node.is_void:
                end = operation.node.position[1]
                output.append(PreparedElementClose(operation.node.source, (end, end), operation.node.tag))
        elif isinstance(operation, _Close):
            output.append(operation.value)
        elif isinstance(operation, _Call):
            output.append(special[(id(data), operation.key)])
        elif isinstance(operation, _If):
            selected_value = data[operation.key]
            if type(selected_value) is not int:
                raise AssertionError("leaf branch selection changed type")
            selected = selected_value
            if selected >= 0:
                _materialize_typed(
                    operation.branches[selected],
                    data,
                    root_data,
                    special,
                    resolved_opens,
                    output,
                    call_runs,
                )
        elif isinstance(operation, _For):
            records = data[operation.key]
            if not isinstance(records, list):
                raise TypeError("leaf loop record changed type")
            run_call = operation.body[0] if len(operation.body) == 1 else None
            run_type = (
                call_runs.get(run_call.key)
                if call_runs and isinstance(run_call, _Call) and len(operation.node.branches) == 1
                else None
            )
            # A loop whose whole body is one keyed call is kept together, as
            # ForNode.render keeps it for an ordinary parent, so the browser
            # gets one loop over the children rather than one call each.
            loop_output: list[RenderPart] = output if run_type is None else []
            if records:
                for record in records:
                    if not isinstance(record, dict):
                        raise TypeError("leaf loop item changed type")
                    _materialize_typed(
                        operation.body,
                        record,
                        root_data,
                        special,
                        resolved_opens,
                        loop_output,
                        call_runs,
                    )
            else:
                _materialize_typed(
                    operation.empty,
                    data,
                    root_data,
                    special,
                    resolved_opens,
                    loop_output,
                    call_runs,
                )
            if run_type is not None:
                from citry.citry_context import CitryContext  # noqa: PLC0415

                from .direct import DirectCallRunRender  # noqa: PLC0415

                output.append(
                    DirectCallRunRender(
                        CitryRender(parts=loop_output, context=CitryContext()),
                        call_node=cast("_Call", run_call).node,
                        child_type_key=run_type,
                    )
                )


def _materialize(
    operations: tuple[object, ...],
    data: dict[str, object],
    resolved_opens: dict[tuple[int, int], PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen],
    output: list[str | RenderPart | PreparedStaticText],
    children: dict[tuple[int, str], RenderPart],
    *,
    preserve_dynamic_text: bool = False,
) -> None:
    for operation in operations:
        if isinstance(operation, _Static):
            output.append(operation.html)
        elif isinstance(operation, _Text):
            text = escape_to_str(data[operation.key])
            output.append(PreparedStaticText(text) if preserve_dynamic_text else text)
        elif isinstance(operation, _Open):
            # _row_open_html must produce the same text for simple='vue' row
            # HTML; tests compare both paths byte for byte.
            output.append(
                _materialized_open_html(operation, operation.static or resolved_opens[(id(data), id(operation))])
            )
            if operation.node.is_self_closing and not operation.node.is_void:
                output.append(f"</{operation.node.tag}>")
        elif isinstance(operation, _Close):
            output.append(f"</{operation.value.tag}>")
        elif isinstance(operation, _Call):
            output.append(children[(id(data), operation.key)])
        elif isinstance(operation, _If):
            selected_value = data[operation.key]
            if type(selected_value) is not int:
                raise AssertionError("leaf branch selection changed type")
            selected = selected_value
            if selected >= 0:
                _materialize(
                    operation.branches[selected],
                    data,
                    resolved_opens,
                    output,
                    children,
                    preserve_dynamic_text=preserve_dynamic_text,
                )
        elif isinstance(operation, _For):
            records = data[operation.key]
            if not isinstance(records, list):
                raise TypeError("leaf loop record changed type")
            if records:
                for record in records:
                    if not isinstance(record, dict):
                        raise TypeError("leaf loop item changed type")
                    _materialize(
                        operation.body,
                        record,
                        resolved_opens,
                        output,
                        children,
                        preserve_dynamic_text=preserve_dynamic_text,
                    )
            else:
                _materialize(
                    operation.empty,
                    data,
                    resolved_opens,
                    output,
                    children,
                    preserve_dynamic_text=preserve_dynamic_text,
                )
        else:
            raise TypeError(f"unknown leaf operation: {type(operation).__name__}")


def _prepared_open(
    operation: _Open,
    resolved: PreparedElementOpen | dict[str, object] | _SpreadResolvedOpen,
) -> PreparedElementOpen:
    if isinstance(resolved, PreparedElementOpen):
        return resolved
    if isinstance(resolved, _SpreadResolvedOpen):
        if resolved.prepared is None:
            resolved.prepared = operation.node._prepared_from_resolved(
                resolved.resolved,
                context=resolved.context,
                extension_validated=resolved.extension_validated,
            )
        return resolved.prepared
    spans = {name: attr.position for name, attr in operation.fixed_attrs or ()}
    if operation.node._has_spread:
        spans = {name: operation.node._data_attr_span(name) for name in resolved}
        authored_attributes: tuple[PreparedAttribute, ...] = ()
        dynamic_keys = {
            attr.key.removeprefix("c-") for attr in operation.node.attrs if not isinstance(attr, StaticHtmlAttr)
        }
        source_values = {attr.key: (attr, source_text) for attr, source_text in operation.node._static_source_attrs}
        spread_attributes: list[PreparedAttribute] = []
        for name, value in resolved.items():
            source = source_values.get(name)
            if (
                source is not None
                and name not in dynamic_keys
                and type(value) is type(source[0].value)
                and value == source[0].value
            ):
                spread_attributes.append(PreparedAttribute(name, "source", source[0].position, source[1]))
            elif include_prepared_attribute(value):
                spread_attributes.append(PreparedAttribute(name, "data", spans[name], value))
        return PreparedElementOpen(
            operation.node.source,
            operation.node.position,
            operation.node.tag,
            tuple(spread_attributes),
            operation.node.is_void,
            operation.node.is_self_closing,
            (),
            (),
            (),
        )
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
        has_spread=operation.node._has_spread,
    )
