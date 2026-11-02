"""
Read Vue slot props from templates: the ``:row`` props a ``<c-slot>`` passes and the names a ``<c-fill v-slot>`` reads.

A component passes Vue data to a fill with ``<c-slot name="item" :row="row" />``,
and the caller reads it with ``<c-fill name="item" v-slot="{ row }">``. The
two sides sit in different templates, so ``citry check`` and the editor read
both: the caller's fills from the template being checked, and the slot's props
from the receiving component's template. Both tools then warn about a name the
slot does not pass, and the editor gives the names their types.

These functions only read templates. They never import or render a component.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from citry._browser_expressions import _ascii_lower, _nested_template, _tokens
from citry._diagnostic_catalog import VUE_UNKNOWN_SLOT_PROP
from citry._diagnostics import render_diagnostic
from citry._walk import Call, run
from citry.analysis import VueLintFinding
from citry.nodes import _camelize
from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping

    from citry_core.template_parser import Template

# The slot a `<c-slot>` without a `name` serves; a `<c-fill>` names it with
# `name="default"`.
DEFAULT_SLOT_NAME = "default"


@dataclass(frozen=True, slots=True)
class SlotVueProp:
    """One ``:row`` or ``v-bind:row`` prop on a ``<c-slot>``, with its expression's span in the template."""

    # The name the fill receives. Vue camelizes it, so `:row-data` passes `rowData`.
    name: str
    # The attribute as written, such as `:row-data`.
    attribute: str
    # The Vue expression, such as `row`.
    source: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class SlotOutlet:
    """One ``<c-slot>`` tag with the Vue props it passes."""

    # `None` when the slot name comes from `c-name` or `c-bind`, so nothing
    # here can tell which fill the outlet serves.
    slot: str | None
    props: tuple[SlotVueProp, ...]
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class SlotPatternKey:
    """One top-level key of a ``v-slot`` object pattern, such as ``row`` in ``{ row: item }``."""

    name: str
    start_index: int
    end_index: int
    # The variable the key binds: `row` for `{ row }` or `{ row = 1 }`, `item`
    # for `{ row: item }`. `None` when the value is a nested pattern.
    local: str | None = None


@dataclass(frozen=True, slots=True)
class ScopedFill:
    """One ``<c-fill v-slot="...">`` inside a component call, with the slot it fills."""

    # The component tag that receives the fill, as written, such as `c-Table`.
    tag: str
    slot: str
    pattern: str
    pattern_start_index: int
    pattern_end_index: int
    # The keys of an object pattern. `None` for a single name, such as
    # `v-slot="props"`, and for a pattern this reader cannot split safely.
    keys: tuple[SlotPatternKey, ...] | None


def camelize(name: str) -> str:
    """Name a slot prop as Vue passes it to the fill: ``row-data`` becomes ``rowData``."""
    # The render path names the props it passes with this same function, so
    # the check and the page agree on every name.
    return _camelize(name)


def slot_prop_name(attribute: str) -> str | None:
    """
    Return the prop a ``<c-slot>`` attribute passes: ``row`` for ``:row`` or ``v-bind:row``, else ``None``.

    The parser rejects every other ``:`` spelling on ``<c-slot>``, such as
    ``:[name]`` or ``:row.prop``, so only these two forms pass a prop.
    """
    rest = attribute.removeprefix("v-bind:") if attribute.startswith("v-bind:") else attribute.removeprefix(":")
    if rest == attribute or not rest or rest.startswith("[") or "." in rest:
        return None
    return rest


def slot_outlets(template: Template, *, parse_nested: Callable[[str], Template]) -> tuple[SlotOutlet, ...]:
    """
    Return the ``<c-slot>`` tags of a template, in source order.

    A ``<c-slot>`` without a ``name`` serves the default slot. One whose name
    comes from ``c-name`` or ``c-bind`` has the slot ``None``.
    """
    found: list[SlotOutlet] = []
    # `run` steps through the walk in one loop, so a deeply nested template
    # cannot reach Python's recursion limit.
    run(_collect_outlets(template, found, parse_nested=parse_nested, base_index=0))
    return tuple(found)


def outlets_for_slot(outlets: tuple[SlotOutlet, ...], slot: str) -> tuple[SlotOutlet, ...] | None:
    """
    Return the outlets that serve one slot, or ``None`` when that is not known.

    It is not known when the template has an outlet with a dynamic name,
    which may serve this slot too, or when no outlet names the slot.
    """
    if any(outlet.slot is None for outlet in outlets):
        return None
    serving = tuple(outlet for outlet in outlets if outlet.slot == slot)
    return serving or None


def scoped_fills(template: Template, *, parse_nested: Callable[[str], Template]) -> tuple[ScopedFill, ...]:
    """
    Return each ``<c-fill>`` with ``v-slot`` whose component tag and slot name are written in the template.

    The slot name counts only when the rightmost of ``name``, ``c-name`` and
    ``c-bind`` is a static ``name``, as the parser decides which slot a fill
    targets. The parser requires one of them on every fill.
    """
    found: list[ScopedFill] = []
    run(_collect_fills(template, found, parse_nested=parse_nested, base_index=0, owner=None))
    return tuple(found)


def lint_unknown_slot_props(
    fills: tuple[ScopedFill, ...],
    props_for: Callable[[str, str], frozenset[str] | None],
) -> tuple[VueLintFinding, ...]:
    """
    Warn about each name a ``v-slot`` pattern reads that its slot does not pass.

    Vue gives such a name ``undefined`` without any error, so a typo or a prop
    the component removed would otherwise go unnoticed.

    Args:
        fills: The scoped fills of the template being checked.
        props_for: Returns the Vue props a component's slot passes, given the
            component tag and the slot name, or ``None`` when that is not
            known, such as for an unregistered tag or a receiving template that
            does not parse. An unknown slot gets no finding.

    Returns:
        One finding per unknown key, spanning the key, in source order.

    """
    findings: list[VueLintFinding] = []
    for fill in fills:
        # A single name, such as `v-slot="props"`, reads no prop by name here;
        # the editor's TypeScript check covers `props.missing`.
        if fill.keys is None:
            continue
        available = props_for(fill.tag, fill.slot)
        if available is None:
            continue
        for key in fill.keys:
            if key.name in available:
                continue
            # The `none` message has no list to show, so only the `default`
            # message receives the names the slot passes.
            parameters = {"name": key.name, "slot": fill.slot, "tag": fill.tag}
            if available:
                message = render_diagnostic(
                    VUE_UNKNOWN_SLOT_PROP, variant="default", available=", ".join(sorted(available)), **parameters
                )
            else:
                message = render_diagnostic(VUE_UNKNOWN_SLOT_PROP, variant="none", **parameters)
            findings.append(
                VueLintFinding(
                    name=key.name,
                    message=message,
                    code=VUE_UNKNOWN_SLOT_PROP,
                    severity="warning",
                    start_index=key.start_index,
                    end_index=key.end_index,
                )
            )
    return tuple(findings)


def outlet_prop_names(outlets: tuple[SlotOutlet, ...]) -> frozenset[str]:
    """Return every prop name that any of a slot's outlets passes."""
    # Different outlets of one slot can pass different props, as in two
    # branches of a `c-if`. A fill may read any of them.
    return frozenset(prop.name for outlet in outlets for prop in outlet.props)


def _static_slot_name(node: Any) -> str | None:
    """Return the slot a ``<c-slot>`` or ``<c-fill>`` names in the template, or ``None`` when it is dynamic."""
    for attr in reversed(node.start_tag.attrs):
        key = attr.key.content
        if key in {"c-name", "c-bind"}:
            return None
        if key == "name":
            value = attr.inner_value.content if attr.inner_value is not None else ""
            return value or None
    return DEFAULT_SLOT_NAME


def _is_component_call(tag: str) -> bool:
    lower = _ascii_lower(tag)
    return lower.startswith("c-") and lower != "c-element" and lower not in RESERVED_TAG_NAMES


def _collect_outlets(
    template: Template,
    found: list[SlotOutlet],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> Generator[Call, Any, None]:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        if _ascii_lower(node.start_tag.name.content) == "c-slot":
            slot = _static_slot_name(node)
            props = tuple(
                SlotVueProp(
                    camelize(prop),
                    attr.key.content,
                    attr.inner_value.content,
                    base_index + attr.inner_value.start_index,
                    base_index + attr.inner_value.end_index,
                )
                for attr in node.start_tag.attrs
                if (prop := slot_prop_name(attr.key.content)) is not None and attr.inner_value is not None
            )
            found.append(
                SlotOutlet(
                    slot,
                    props,
                    base_index + node.start_tag.name.start_index,
                    base_index + node.start_tag.name.end_index,
                )
            )
        yield from _nested_walks(node, found, _collect_outlets, parse_nested=parse_nested, base_index=base_index)


def _collect_fills(
    template: Template,
    found: list[ScopedFill],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    owner: str | None,
) -> Generator[Call, Any, None]:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        tag = node.start_tag.name.content
        if owner is not None and _ascii_lower(tag) == "c-fill":
            fill = _scoped_fill(node, owner, base_index)
            if fill is not None:
                found.append(fill)
        # A fill belongs to the nearest component call around it; control-flow
        # tags such as `<c-if>` between the two do not change that.
        inner_owner = tag if _is_component_call(tag) else owner
        yield from _nested_walks(
            node, found, _collect_fills, parse_nested=parse_nested, base_index=base_index, owner=inner_owner
        )


def _nested_walks(
    node: Any,
    found: list[Any],
    walker: Callable[..., Generator[Call, Any, None]],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    **extra: Any,
) -> Generator[Call, Any, None]:
    """Walk a node's template-valued attributes and its body with the same walker."""
    for attr in node.start_tag.attrs:
        inner = attr.inner_value
        if attr.kind == HtmlAttrKind.Template and inner is not None:
            nested = _nested_template(inner.content, parse_nested)
            if nested is not None:
                parsed, nested_start = nested
                yield Call(
                    walker,
                    parsed,
                    found,
                    parse_nested=parse_nested,
                    base_index=base_index + inner.start_index + nested_start,
                    **extra,
                )
    body = getattr(node, "body", None)
    if body is not None:
        yield Call(walker, body, found, parse_nested=parse_nested, base_index=base_index, **extra)


def _scoped_fill(node: Any, owner: str, base_index: int) -> ScopedFill | None:
    slot = _static_slot_name(node)
    if slot is None:
        return None
    for attr in node.start_tag.attrs:
        if attr.key.content != "v-slot" or attr.inner_value is None:
            continue
        pattern = attr.inner_value.content
        start = base_index + attr.inner_value.start_index
        return ScopedFill(
            owner,
            slot,
            pattern,
            start,
            base_index + attr.inner_value.end_index,
            pattern_keys(pattern, start),
        )
    return None


def pattern_keys(pattern: str, start_index: int = 0) -> tuple[SlotPatternKey, ...] | None:
    """
    Return the top-level keys of a ``v-slot`` object pattern, with byte spans offset by ``start_index``.

    ``{ row, index: position, ...rest }`` gives ``row`` and ``index``; a rest
    element reads no prop by name. Returns ``None`` for a single name such as
    ``props``, and for any pattern this tokenizer cannot split with
    certainty: a computed key, a template literal, or a ``/`` that could start
    a regular expression inside a default value.
    """
    tokens = _tokens(pattern)
    if not tokens or tokens[0].source != "{" or tokens[-1].source != "}":
        return None
    if any(token.source == "/" or token.source.startswith("`") for token in tokens):
        return None
    keys: list[SlotPatternKey] = []
    depth = 0
    # Whether the next top-level token opens an entry: the first one after
    # `{` or `,`.
    expecting_key = False
    for index, token in enumerate(tokens):
        if token.kind == "punctuation" and token.source in "([{":
            depth += 1
            if depth == 1:
                expecting_key = True
            continue
        if token.kind == "punctuation" and token.source in ")]}":
            depth -= 1
            continue
        if depth != 1:
            continue
        if token.kind == "punctuation" and token.source == ",":
            expecting_key = True
            continue
        if not expecting_key:
            continue
        expecting_key = False
        if token.source == "...":
            continue
        if token.kind == "identifier":
            name = token.source
        elif token.kind == "string" and token.value is not None:
            name = token.value
        else:
            # A computed key such as `[name]`, or a numeric key.
            return None
        keys.append(
            SlotPatternKey(
                name,
                start_index + len(pattern[: token.start].encode("utf-8")),
                start_index + len(pattern[: token.end].encode("utf-8")),
                _entry_local(tokens, index),
            )
        )
    return tuple(keys)


def _entry_local(tokens: tuple[Any, ...], key_index: int) -> str | None:
    """Return the variable an object-pattern entry binds, given the index of its key token."""
    after = tokens[key_index + 1].source if key_index + 1 < len(tokens) else "}"
    key = tokens[key_index]
    # `{ row }` and `{ row = fallback }` bind the key's own name.
    if after in {",", "}", "="}:
        return key.source if key.kind == "identifier" else None
    # `{ row: item }` and `{ row: item = fallback }` bind the name after the
    # colon; `{ row: { title } }` binds a nested pattern instead.
    if after == ":" and key_index + 3 < len(tokens):
        value, following = tokens[key_index + 2], tokens[key_index + 3]
        if value.kind == "identifier" and following.source in {",", "}", "="}:
            return value.source
    return None


def unknown_slot_props_for(
    receivers: Mapping[str, tuple[SlotOutlet, ...] | None],
) -> Callable[[str, str], frozenset[str] | None]:
    """
    Build ``props_for`` for `lint_unknown_slot_props` from each component tag's outlets.

    ``receivers`` maps a lower-case component tag to its template's outlets,
    or to ``None`` when that template is unknown.
    """

    def props_for(tag: str, slot: str) -> frozenset[str] | None:
        outlets = receivers.get(_ascii_lower(tag))
        if outlets is None:
            return None
        serving = outlets_for_slot(outlets, slot)
        return None if serving is None else outlet_prop_names(serving)

    return props_for
