"""
Write the Vue template that rendering would compile, from the authored template alone.

When a component renders in an interactive page, Citry turns the result into a
Vue template and compiles it with the Rust Vue compiler (`compiler.py`). A
template the compiler rejects fails only then. `citry check` and the editor
call `static_vue_template` instead, so they can run the same compiler before
anything renders.

A render writes that Vue template in one of two ways:

- When every node of a component's body has a fixed Vue form, the render
  compiles the body once into a leaf program (`leaf_program.py`): a Vue
  template it reuses for every render, with each `<c-if>` branch inside a
  `<template v-if>` and each `<c-for>` body inside a `<template v-for>`.
- Otherwise it writes the Vue template from what it rendered: the `<c-if>`
  branch it picked, every `<c-for>` row, the values of Python expressions.

This module asks the leaf program compiler whether the body qualifies, and
writes `<c-if>` and `<c-for>` the same way: wrapped for a leaf program, and
otherwise every branch and the loop body once, one after another, so each
branch a render may pick is compiled. It differs from a render in these ways:

- A Python value is always a text binding, and a component call passes
  every fill it is given, including fills for slots the child may not have.
- Extensions do not run, so attributes they handle (such as `@c-click`)
  are left out.
- A component that renders in place (a built-in such as `<c-provide>`, or a
  component the caller knows is `transparent` or `simple`) is written as its
  body, or as nothing when its own template decides what renders.
- The leaf program question is asked as for an ordinary component, before
  any constant is folded and without extension hooks, so a component that
  is `simple`, `pure`, or `transparent`, an application with an attribute
  hook other than the Events one, or a `<c-if>` with a constant condition
  can make a render write a branch differently.

Everything else is written by the same functions a render uses
(`direct_capture.py`, `capture.py`, and `leaf_program.py`), from the same
node objects the template compiler produces, so an element, a component
call, a fill, or a slot outlet has the same Vue source in both.

Alongside the text, the writer records which bytes of the Vue template were
copied from the authored template, so a compiler error can be mapped back to
the place the author wrote.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from citry._walk import Call, run
from citry.client_directives import ComponentTagClientBindingKind, classify_component_tag_client_binding_key
from citry.nodes import ComponentNode, FillNode, ForNode, IfNode, SlotNode, StaticHtmlAttr

from .capture import (
    PreparedAttribute,
    PreparedElementCloseNode,
    PreparedElementOpen,
    PreparedElementOpenNode,
    PreparedExprNode,
    PreparedSourceTextNode,
    PreparedVerbatimHtmlNode,
    UnsupportedPreparedView,
    coalesce_prepared_static_nodes,
    static_element_opening,
)
from .compiler import _authored_vue_attr, _guard_template_braces
from .direct_capture import (
    _append_element_open,
    _append_opaque_html,
    _append_slot_outlet,
    _append_text_binding,
    _component_call_binding_attr,
    _component_call_identity,
    _DefinitionFragment,
    _fill_opening,
    document_body_bounds,
)
from .leaf_program import branch_opening, compile_leaf_program, loop_empty_opening, loop_opening

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from citry.nodes import BodyItem

    from .compiler import DefinitionCompileInput


class UnsupportedStaticTemplate(ValueError):
    """Raised for a template this module cannot turn into the Vue template a render would compile."""


# The tag a component call gets. A render uses a name derived from the
# component class; any custom-element name parses the same way.
_CALL_TAG = "citry-check-call"
# Vue's conditional directives, which `VElseNoAdjacentIf` is about.
_ELSE_NAMES = frozenset({"v-else", "v-else-if"})
# Built-in components that render their body in place, so the body is part of
# the caller's Vue template.
_IN_PLACE_BODIES = frozenset({"provide", "cache"})
# Built-in components whose output the template does not show: `<c-js>` and
# `<c-css>` hold code, and `<c-component>` with a Python-chosen component
# renders that component's template.
_NO_VUE_SOURCE = frozenset({"js", "css", "component"})
_BUILTIN_NAMES = frozenset({"element", *_IN_PLACE_BODIES, *_NO_VUE_SOURCE})
# A callable that says whether a component tag (its name without `c-`)
# renders in place, or `None` when the caller cannot tell.
RendersInPlace = Callable[[str], "bool | None"]


@dataclass(frozen=True, slots=True)
class SourceSegment:
    """
    One run of the Vue template and the authored bytes it came from.

    An authored segment is a byte-for-byte copy, so a position inside it maps
    to the same position in the authored template. Any other segment is text
    the writer generated for an authored node, such as a component call's tag,
    and maps only to that node as a whole.
    """

    vue_start: int
    vue_end: int
    source_start: int
    source_end: int
    authored: bool


@dataclass(frozen=True, slots=True)
class ElseDirective:
    """A `v-else` or `v-else-if` the author wrote, where it sits in both templates."""

    vue_start: int
    vue_end: int
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True)
class StaticVueTemplate:
    """The Vue template for one authored template, and the map back to the authored bytes."""

    source: bytes
    compile_input: DefinitionCompileInput
    segments: tuple[SourceSegment, ...]
    else_directives: tuple[ElseDirective, ...]
    # `(tag, start of the opening tag, start of the closing tag, end of the
    # closing tag)` for each element the author wrote with both tags.
    elements: tuple[tuple[str, int, int, int], ...]
    # Where each component call known to be an ordinary call starts in the
    # Vue template; only such a call is reported inside a Vue `v-for`.
    ordinary_calls: frozenset[int]
    # Fills with `v-slot` passed to a component that copies them in place,
    # where no Vue slot function receives the props, so every render
    # refuses them: `(start, end, message)` in authored bytes.
    scoped_fill_refusals: tuple[tuple[int, int, str], ...] = ()

    def authored_range(self, start: int, end: int) -> tuple[int, int] | None:
        """
        Map a byte range of the Vue template to the authored template.

        Returns `None` unless `start` falls in authored text, so a compiler
        error is reported only where it points at something the author wrote.
        The end maps exactly when it also falls in authored text; otherwise
        the range ends where the authored run that holds `start` ends.
        """
        first = self._segment_at(start)
        if first is None or not first.authored:
            return None
        source_start = first.source_start + (start - first.vue_start)
        last = self._segment_at(max(start, end - 1))
        if last is not None and last.authored and end > start:
            source_end = last.source_start + (end - last.vue_start)
        else:
            source_end = first.source_end
        return source_start, max(source_start, source_end)

    def vue_offset(self, source_offset: int) -> int | None:
        """Return where an authored byte sits in the Vue template, when it was copied there."""
        for segment in self.segments:
            if segment.authored and segment.source_start <= source_offset < segment.source_end:
                return segment.vue_start + (source_offset - segment.source_start)
        return None

    def paragraphs_around(self, offset: int) -> list[tuple[int, int, int]]:
        """Return each `<p>` element that holds the authored `offset` inside its tags."""
        return [
            (start, close_start, end)
            for name, start, close_start, end in self.elements
            if name == "p" and start < offset < close_start
        ]

    def generated_source(self, offset: int) -> tuple[int, int] | None:
        """Return the authored span of the node whose generated text holds `offset`, if any."""
        segment = self._segment_at(offset)
        if segment is None or segment.authored:
            return None
        return segment.source_start, segment.source_end

    def _segment_at(self, offset: int) -> SourceSegment | None:
        # Segments are written in Vue-template order and never overlap, so the
        # last one that starts at or before `offset` is the only candidate.
        low, high = 0, len(self.segments)
        while low < high:
            middle = (low + high) // 2
            if self.segments[middle].vue_start <= offset:
                low = middle + 1
            else:
                high = middle
        if low == 0:
            return None
        segment = self.segments[low - 1]
        return segment if offset < segment.vue_end else None


def static_vue_template(
    source: str,
    nodes: Sequence[BodyItem],
    *,
    renders_in_place: RendersInPlace | None = None,
) -> StaticVueTemplate:
    """
    Write the Vue template for the prepared nodes of one authored template.

    `nodes` is what the prepared template compiler returns for `source`
    (see `citry.component_render._exec_template_code`). `renders_in_place`
    says which component tags render in place; without it, every component
    tag other than a built-in is written as a call whose kind is unknown.

    Raises:
        UnsupportedStaticTemplate: The template holds a node this module cannot
            write the way a render would. The caller skips the template rather
            than compile a guess.

    """
    try:
        bounds = document_body_bounds(
            nodes,
            text=lambda node: node.text if isinstance(node, PreparedSourceTextNode) else None,
            opening_tag=lambda node: node.tag if isinstance(node, PreparedElementOpenNode) else None,
            closing_tag=lambda node: node.tag if isinstance(node, PreparedElementCloseNode) else None,
        )
    except UnsupportedPreparedView as error:
        raise UnsupportedStaticTemplate(str(error)) from error
    writer = _Writer(source.encode(), leaf=_is_leaf_program(nodes), renders_in_place=renders_in_place)
    # A whole-document template gets only its body contents compiled, as in a render.
    run(writer.write_nodes(nodes if bounds is None else nodes[bounds[0] : bounds[1]]))
    return StaticVueTemplate(
        writer.source,
        writer.output.compile_input(),
        tuple(writer.segments),
        tuple(writer.else_directives),
        tuple(writer.elements),
        frozenset(writer.ordinary_calls),
        tuple(writer.scoped_fill_refusals),
    )


def _is_leaf_program(nodes: Sequence[BodyItem]) -> bool:
    """Whether a render compiles this body as a leaf program, asked the way the render asks."""
    # The render joins static nodes first and asks with the same defaults
    # for an ordinary component (see `component_render`).
    return compile_leaf_program(coalesce_prepared_static_nodes(list(nodes))) is not None


@dataclass(slots=True)
class _Writer:
    source: bytes
    # Whether a render compiles this body as a leaf program, which wraps
    # each `<c-if>` branch and `<c-for>` body in a `<template>`.
    leaf: bool = False
    renders_in_place: RendersInPlace | None = None
    output: _DefinitionFragment = field(default_factory=_DefinitionFragment.empty)
    segments: list[SourceSegment] = field(default_factory=list)
    else_directives: list[ElseDirective] = field(default_factory=list)
    elements: list[tuple[str, int, int, int]] = field(default_factory=list)
    ordinary_calls: set[int] = field(default_factory=set)
    scoped_fill_refusals: list[tuple[int, int, str]] = field(default_factory=list)
    # The elements open at this point, as `(tag, start of the opening tag)`.
    open_elements: list[tuple[str, int]] = field(default_factory=list)
    # For each open element with an authored `v-pre`, the number of elements
    # open outside it. Vue reads everything under it as written, so while
    # one is open no ownership marker is written, as a render does for a
    # `v-pre` element Vue reads as written.
    v_pre_depths: list[int] = field(default_factory=list)
    # Data keys only need to be distinct within one template.
    counter: int = 0

    def next_key(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}{self.counter}"

    def write_nodes(self, nodes: Sequence[BodyItem]) -> Generator[Call, Any, None]:
        index = 0
        while index < len(nodes):
            index = yield Call(self.write_node, nodes, index)

    def write_node(self, nodes: Sequence[BodyItem], index: int) -> Generator[Call, Any, int]:
        """Write `nodes[index]` and return the index of the next node to write."""
        node = nodes[index]
        if isinstance(node, PreparedSourceTextNode):
            self.write_copy(node.text, node.position)
        elif isinstance(node, PreparedExprNode):
            start = self.output.byte_length
            _append_text_binding(self.output, self.next_key("citryText"))
            self.mark_generated(start, node.position)
        elif isinstance(node, PreparedVerbatimHtmlNode):
            start = self.output.byte_length
            _append_opaque_html(self.output, self.next_key("citryOpaque"), "raw")
            self.mark_generated(start, node.position)
        elif isinstance(node, PreparedElementOpenNode):
            return self.write_element_open(nodes, index)
        elif isinstance(node, PreparedElementCloseNode):
            self.write_copy(f"</{node.tag}>", node.position)
            if self.open_elements and self.open_elements[-1][0] == node.tag.lower():
                tag, start = self.open_elements.pop()
                self.elements.append((tag, start, node.position[0], node.position[1]))
                if self.v_pre_depths and self.v_pre_depths[-1] == len(self.open_elements):
                    self.v_pre_depths.pop()
        elif isinstance(node, IfNode):
            yield Call(self.write_if, node)
        elif isinstance(node, ForNode):
            yield Call(self.write_for, node)
        elif isinstance(node, ComponentNode):
            yield Call(self.write_component, node)
        elif isinstance(node, SlotNode):
            yield Call(self.write_slot, node)
        else:
            msg = f"no Vue form for {type(node).__name__}"
            raise UnsupportedStaticTemplate(msg)
        return index + 1

    def write_if(self, node: IfNode) -> Generator[Call, Any, None]:
        if not self.leaf:
            # A render writes the branch it picks, so each branch is written
            # in turn and every one must compile.
            for branch in node.branches:
                yield Call(self.write_nodes, branch[2])
            return
        key = self.next_key("citryIf")
        for index, branch in enumerate(node.branches):
            self.write_generated(branch_opening(key, index), branch[0])
            yield Call(self.write_nodes, branch[2])
            self.write_generated("</template>", branch[0])

    def write_for(self, node: ForNode) -> Generator[Call, Any, None]:
        if not self.leaf:
            # A render repeats the body once per row; one copy compiles the same.
            for branch in node.branches:
                yield Call(self.write_nodes, branch[2])
            return
        key = self.next_key("citryLoop")
        self.write_generated(loop_opening(key), node.branches[0][0])
        yield Call(self.write_nodes, node.branches[0][2])
        self.write_generated("</template>", node.branches[0][0])
        for branch in node.branches[1:]:
            self.write_generated(loop_empty_opening(key), branch[0])
            yield Call(self.write_nodes, branch[2])
            self.write_generated("</template>", branch[0])

    def write_generated(self, text: str, span: tuple[int, int]) -> None:
        """Write text the author did not write, mapped to the authored node it stands for."""
        start = self.output.byte_length
        self.output.append(text)
        self.mark_generated(start, span)

    def write_copy(self, text: str, span: tuple[int, int]) -> None:
        """Write text that the author wrote at `span`, if it is a copy, mapped byte for byte."""
        if text.endswith("{") and span[1] > span[0]:
            # A trailing `{` is written as `&#123;` (`_guard_template_braces`),
            # so map the text before the brace byte for byte, and map the
            # reference to the brace.
            if len(text) > 1:
                self.write_copy(text[:-1], (span[0], span[1] - 1))
            self.write_generated(_guard_template_braces("{"), (span[1] - 1, span[1]))
            return
        start = self.output.byte_length
        self.output.append(text)
        if self.source[span[0] : span[1]] == text.encode():
            self.segments.append(SourceSegment(start, self.output.byte_length, span[0], span[1], authored=True))
        else:
            self.mark_generated(start, span)

    def mark_generated(self, start: int, span: tuple[int, int]) -> None:
        if self.output.byte_length > start:
            self.segments.append(SourceSegment(start, self.output.byte_length, span[0], span[1], authored=False))

    def write_element_open(self, nodes: Sequence[BodyItem], index: int) -> int:
        node = nodes[index]
        assert isinstance(node, PreparedElementOpenNode)  # noqa: S101 - the caller dispatched on the type
        start = self.output.byte_length
        first_chunk = len(self.output.chunks)
        static = node._static_prepared
        own_v_pre = any(attr.key.casefold() == "v-pre" for attr in node._authored_vue_attrs)
        if static is not None and not node._authored_vue_attrs:
            # The same markup a render joins into one block of static text.
            self.output.append(static_element_opening(static))
        else:
            part = PreparedElementOpen(
                node.source,
                node.position,
                node.tag,
                tuple(
                    PreparedAttribute(attr.key, "source", attr.position, text)
                    for attr, text in node._static_source_attrs
                ),
                node.is_void,
                node.is_self_closing,
                (),
                has_spread=node._has_spread,
            )
            # Attributes Python computes (`c-*`) reach Vue as one object
            # binding; its value does not change what the compiler accepts.
            has_data_attrs = len(node._static_source_attrs) != len(node.attrs)
            has_key = any(name == "key" for name, _value in node.element_metadata)
            _append_element_open(
                self.output,
                part,
                self.next_key("citryAttrs") if has_data_attrs else None,
                self.next_key("citryKey") if has_key else None,
                under_v_pre=own_v_pre or bool(self.v_pre_depths),
            )
        self.map_opening(
            start,
            "".join(self.output.chunks[first_chunk:]),
            node.position,
            node.tag,
            [(attr.key, text, attr.position) for attr, text in node._static_source_attrs],
        )
        if not node.is_void:
            if own_v_pre:
                self.v_pre_depths.append(len(self.open_elements))
            self.open_elements.append((node.tag.lower(), node.position[0]))
        ignored = any(name == "morph" and value == "ignore" for name, value in node.element_metadata)
        if not ignored or node.is_void:
            return index + 1
        # A render keeps a `#c-ignore` element's contents as HTML that Vue
        # does not compile, so only the element's own tags are written.
        close_index, close = _matching_close(nodes, index)
        start = self.output.byte_length
        _append_opaque_html(self.output, self.next_key("citryOpaque"), "raw")
        self.mark_generated(start, (node.position[1], close.position[0]))
        # The close is written next, as an ordinary close.
        return close_index

    def map_opening(
        self,
        start: int,
        written: str,
        span: tuple[int, int],
        tag: str,
        attrs: list[tuple[str, str, tuple[int, int]]],
    ) -> None:
        """
        Map an opening tag written from authored attributes back to the template.

        The tag name and each authored attribute are copies of the authored
        text; the spaces, the closing `>`, and any generated attribute map to
        the whole authored opening tag.
        """
        written_bytes = written.encode()
        end = start + len(written_bytes)
        authored = self.source[span[0] : span[1]]
        pieces: list[tuple[int, int, int, int]] = []
        name = f"<{tag}".encode()
        if authored.startswith(name) and written_bytes.startswith(name):
            pieces.append((0, len(name), span[0], span[0] + len(name)))
        cursor = len(name)
        for key, text, attr_span in attrs:
            found = _find_attribute(written_bytes, text.encode(), cursor)
            if found < 0:
                continue
            pieces.append((found, found + len(text.encode()), attr_span[0], attr_span[1]))
            cursor = found + len(text.encode())
            if key in _ELSE_NAMES:
                self.else_directives.append(
                    ElseDirective(start + found, start + found + len(key), attr_span[0], attr_span[0] + len(key))
                )
        if authored == written_bytes:
            self.segments.append(SourceSegment(start, end, span[0], span[1], authored=True))
            return
        if authored.endswith(b">") and written_bytes.endswith(b">") and cursor < len(written_bytes):
            pieces.append((len(written_bytes) - 1, len(written_bytes), span[1] - 1, span[1]))
        self.write_pieces(start, end, span, pieces)

    def write_pieces(
        self,
        start: int,
        end: int,
        span: tuple[int, int],
        pieces: list[tuple[int, int, int, int]],
    ) -> None:
        """Record authored pieces of one written run, and generated segments for the gaps between them."""
        cursor = start
        for piece_start, piece_end, source_start, source_end in pieces:
            if start + piece_start > cursor:
                self.segments.append(SourceSegment(cursor, start + piece_start, span[0], span[1], authored=False))
            self.segments.append(
                SourceSegment(start + piece_start, start + piece_end, source_start, source_end, authored=True)
            )
            cursor = start + piece_end
        if end > cursor:
            self.segments.append(SourceSegment(cursor, end, span[0], span[1], authored=False))

    def refuse_scoped_fills(self, node: ComponentNode) -> None:
        """Record each fill with `v-slot` that this in-place component would copy into the template."""
        # A built-in passes no Vue slot props at all; a component of the
        # author's own could stop copying its content in place.
        fix = (
            f"<c-{node.name}> passes no Vue slot props; remove 'v-slot' from the fill."
            if node.name in _BUILTIN_NAMES
            else "Remove 'v-slot' from the fill and read Python slot data with 'data=\"...\"', or remove "
            f"transparent = True or simple = True from {node.name}."
        )
        for _site_id, span, _body, pattern in _fills(node):
            if pattern is not None:
                self.scoped_fill_refusals.append(
                    (
                        span[0],
                        span[1],
                        f"<c-{node.name}> copies this fill into the template around it, so "
                        f"'v-slot=\"{pattern}\"' has no Vue slot to read from, and the page fails to render. " + fix,
                    )
                )

    def write_component(self, node: ComponentNode) -> Generator[Call, Any, None]:
        # A built-in is decided by its name; only another component's kind
        # comes from the caller, which may count a built-in as transparent.
        in_place = node.name in _IN_PLACE_BODIES or (
            node.name not in _BUILTIN_NAMES and self.renders_in_place is not None and self.renders_in_place(node.name)
        )
        if in_place or node.name == "element":
            self.refuse_scoped_fills(node)
        if node.name in _NO_VUE_SOURCE or (in_place and node.name not in _IN_PLACE_BODIES):
            # Its own template decides what renders here, and this module
            # does not have it.
            return
        if in_place:
            # The render copies the body into the caller's template.
            for _site_id, _span, body, _pattern in _fills(node):
                yield Call(self.write_nodes, body)
            return
        if node.name == "element":
            # A `<c-element>` whose tag Python chooses. The tag is unknown
            # here, so its contents go in a `<template>`: they are still
            # compiled, but their nesting is not judged against a guess.
            start = self.output.byte_length
            self.output.append("<template>")
            self.mark_generated(start, node.position)
            # Its fills render in place, as a `<c-provide>` body does.
            for _site_id, _span, body, _pattern in _fills(node):
                yield Call(self.write_nodes, body)
            start = self.output.byte_length
            self.output.append("</template>")
            self.mark_generated(start, node.position)
            return
        local_id = self.next_key("citryCall")
        call_start = self.output.byte_length
        if (
            node.name not in _BUILTIN_NAMES
            and self.renders_in_place is not None
            and self.renders_in_place(node.name) is False
        ):
            self.ordinary_calls.add(call_start)
        self.output.append(f"<{_CALL_TAG}")
        self.mark_generated(call_start, node.position)
        bindings: list[dict[str, object]] = []
        for attr in node.attrs:
            binding = self.write_call_binding(node, attr)
            if binding is not None:
                bindings.append(binding)
        start = self.output.byte_length
        self.output.append(_component_call_identity(local_id))
        self.output.append(">")
        opening_end = self.output.byte_length
        self.mark_generated(start, node.position)
        for site_id, span, body, vue_pattern in _fills(node):
            start = self.output.byte_length
            # The pattern binds the fill's Vue slot props, so the compiler sees
            # them as the fill's own names, as it does on a render.
            self.output.append(
                _fill_opening(site_id, "" if vue_pattern is None else _authored_vue_attr("", vue_pattern))
            )
            self.mark_generated(start, span)
            yield Call(self.write_nodes, body)
            start = self.output.byte_length
            self.output.append("</template>")
            self.mark_generated(start, span)
        start = self.output.byte_length
        self.output.append(f"</{_CALL_TAG}>")
        self.mark_generated(start, node.position)
        # The compiler checks the call against this record, as it does for a
        # render; `lint_vue_compile` keeps its component-in-`v-for` error only
        # for a call in `ordinary_calls`.
        self.output.local_calls.append(
            {
                "localId": local_id,
                "typeKey": node.name,
                "componentTag": _CALL_TAG,
                "sourceStart": call_start,
                "sourceEnd": opening_end,
                "bindings": bindings,  # type: ignore[typeddict-item]
            }
        )

    def write_call_binding(self, node: ComponentNode, attr: object) -> dict[str, object] | None:
        """Write one authored Vue binding of a component call, such as `v-if` or `:title`."""
        if not isinstance(attr, StaticHtmlAttr):
            return None
        try:
            kind = classify_component_tag_client_binding_key(attr.key, tag_name=f"c-{node.name}")
        except RuntimeError:
            # The parser or the call's render reports a directive a component
            # tag cannot carry; it is not part of what Vue compiles.
            return None
        # `@c-*` becomes a generated listener that an extension writes.
        if kind is None or kind is ComponentTagClientBindingKind.CITRY_HANDLER:
            return None
        value = "" if attr.value is True else str(attr.value)
        try:
            text = _component_call_binding_attr(attr.key, value)
        except ValueError:
            return None
        self.output.append(" ")
        start = self.output.byte_length
        self.output.append(text)
        end = self.output.byte_length
        authored = self.source[attr.position[0] : attr.position[1]]
        if authored == text.encode():
            self.segments.append(SourceSegment(start, end, attr.position[0], attr.position[1], authored=True))
        else:
            self.mark_generated(start, attr.position)
        if attr.key in _ELSE_NAMES:
            self.else_directives.append(
                ElseDirective(start, start + len(attr.key), attr.position[0], attr.position[0] + len(attr.key))
            )
        return {"kind": kind.value, "name": attr.key, "value": value, "sourceStart": start, "sourceEnd": end}

    def write_slot(self, node: SlotNode) -> Generator[Call, Any, None]:
        # The fallback is written on its own first, because the shared writer
        # takes it as one finished fragment.
        fallback = _Writer(self.source, leaf=self.leaf, renders_in_place=self.renders_in_place, counter=self.counter)
        yield Call(fallback.write_nodes, node.body)
        self.counter = fallback.counter
        # Element spans are authored positions, so they need no shift.
        self.elements.extend(fallback.elements)
        start = self.output.byte_length
        name = _static_attr(node, "name") or "default"
        # The outlet carries the slot's Vue props, so the compiler checks
        # their expressions in this component's scope, as on a render.
        props = "".join(" " + _authored_vue_attr(key, value) for key, value in node.vue_props)
        _append_slot_outlet(self.output, _site_id(name), fallback.output, props)
        end = self.output.byte_length
        if not fallback.output.chunks:
            self.mark_generated(start, node.position)
            return
        # The fallback sits just before the closing `</template>`, so its
        # segments move by where it starts.
        offset = end - len(b"</template>") - fallback.output.byte_length
        self.segments.append(SourceSegment(start, offset, node.position[0], node.position[1], authored=False))
        self.segments.extend(
            SourceSegment(
                item.vue_start + offset, item.vue_end + offset, item.source_start, item.source_end, item.authored
            )
            for item in fallback.segments
        )
        self.else_directives.extend(
            ElseDirective(item.vue_start + offset, item.vue_end + offset, item.source_start, item.source_end)
            for item in fallback.else_directives
        )
        self.ordinary_calls.update(start + offset for start in fallback.ordinary_calls)
        self.scoped_fill_refusals.extend(fallback.scoped_fill_refusals)
        self.segments.append(
            SourceSegment(
                offset + fallback.output.byte_length, end, node.position[0], node.position[1], authored=False
            )
        )


def _static_attr(node: SlotNode | FillNode, key: str) -> str | None:
    for attr in node.attrs:
        if isinstance(attr, StaticHtmlAttr) and attr.key == key and isinstance(attr.value, str):
            return attr.value
    return None


def _site_id(name: str) -> str:
    # The name sits inside `v-slot:['...']` and `name="..."`, so keep it to
    # characters that need no escaping in either.
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def _fills(node: ComponentNode) -> list[tuple[str, tuple[int, int], Sequence[BodyItem], str | None]]:
    """
    List the fills a component call passes, as `(site id, span, body, v-slot pattern or None)`.

    A render passes the fills of the `<c-if>` branch it picks; every branch's
    fills are listed here. Two fills for one slot in different branches get
    different site ids, because Vue rejects one call that passes a slot twice.
    """
    fills: list[FillNode] = []

    def collect(body: Sequence[BodyItem]) -> Generator[Call, Any, None]:
        for item in body:
            if isinstance(item, FillNode):
                fills.append(item)
            elif isinstance(item, (IfNode, ForNode)):
                for branch in item.branches:
                    yield Call(collect, branch[2])

    run(collect(node.body))
    if not fills:
        # Content without `<c-fill>` is the default fill.
        # A render passes any content, a comment included, but not whitespace alone.
        if any(not isinstance(item, PreparedSourceTextNode) or item.text.strip() for item in node.body):
            return [("default", node.position, node.body, None)]
        return []
    seen: dict[str, int] = {}
    listed: list[tuple[str, tuple[int, int], Sequence[BodyItem], str | None]] = []
    for fill in fills:
        site_id = _site_id(_static_attr(fill, "name") or "default")
        count = seen.get(site_id, 0)
        seen[site_id] = count + 1
        listed.append(
            (site_id if count == 0 else f"{site_id}-{count + 1}", fill.position, fill.body, fill.vue_pattern)
        )
    return listed


def _find_attribute(written: bytes, text: bytes, cursor: int) -> int:
    """Find authored attribute text in a written opening tag, as a whole attribute after `cursor`."""
    found = written.find(text, cursor)
    # A match must sit between spaces or before the tag's end; anything else
    # is inside another attribute, such as a generated `v-bind` value.
    while found >= 0 and not (
        written[found - 1 : found] == b" " and written[found + len(text) : found + len(text) + 1] in {b" ", b">", b"/"}
    ):
        found = written.find(text, found + 1)
    return found


def _matching_close(nodes: Sequence[BodyItem], index: int) -> tuple[int, PreparedElementCloseNode]:
    """Return the index of the close that ends the element opened at `index`."""
    depth = 0
    for position in range(index, len(nodes)):
        node = nodes[position]
        if isinstance(node, PreparedElementOpenNode) and not node.is_void:
            depth += 1
        elif isinstance(node, PreparedElementCloseNode):
            depth -= 1
            if depth == 0:
                return position, node
    msg = "a `#c-ignore` element has no close in the same body"
    raise UnsupportedStaticTemplate(msg)
