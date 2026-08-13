# Generated from packages/py/citry/citry/_portable_ide.py
# by docs_site/_internal/frontend/scripts/build.mjs. Do not edit.
"""Small parser-owned IDE rules shared by native and browser transports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Collection


@dataclass(frozen=True, slots=True)
class ComponentNameMatch:
    """Describe one component completion match without editor-specific types."""

    sort_text: str
    filter_text: str


@dataclass(frozen=True, slots=True)
class UnknownComponentUse:
    """Identify one parser-proven component tag absent from a registry."""

    tag: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class TemplateTagUse:
    """Identify one parser-proven tag spelling, including nested templates."""

    tag: str
    start_index: int
    end_index: int
    closing: bool


def component_name_match(
    prefix: str,
    label: str,
    *,
    is_class_name: bool,
    variant_index: int,
) -> ComponentNameMatch | None:
    """Match one registered component spelling while preserving typed shape."""
    query = prefix.removeprefix("c-")
    suffix = label.removeprefix("c-")
    surfaces = [(suffix, False)]
    if is_class_name and len(suffix) > 1 and suffix[0] == "C" and suffix[1].isupper():
        surfaces.append((suffix[1:], True))

    matches: list[tuple[tuple[int, int, int, int], str]] = []
    for surface, elided in surfaces:
        result = _component_surface_match(query, surface, is_class_name=is_class_name)
        if result is None:
            continue
        tier, matched_surface, consumed_query = result
        comparison_query = query if consumed_query == len(query) else _compact_component_name(query)
        case_mismatches = sum(
            left != right
            for left, right in zip(comparison_query, matched_surface, strict=False)
            if left.casefold() == right.casefold()
        )
        score = (
            tier + (2 if elided else 0),
            variant_index,
            case_mismatches,
            len(matched_surface) - consumed_query,
        )
        matches.append((score, prefix + matched_surface[consumed_query:]))
    if not matches:
        return None
    score, filter_text = min(matches)
    tier, variant, case_mismatches, remaining = score
    return ComponentNameMatch(
        sort_text=f"1:{tier:03}:{variant:03}:{case_mismatches:03}:{remaining:04}:{label.casefold()}:{label}",
        filter_text=filter_text,
    )


def unknown_component_uses(
    template: object,
    known_names: Collection[str],
    *,
    parse_nested: Callable[[str], object] = parse_template,
) -> tuple[UnknownComponentUse, ...]:
    """Return component tags absent from one proven registry snapshot."""
    normalized_names = frozenset(name.casefold().removeprefix("c-") for name in known_names)
    return tuple(
        UnknownComponentUse(
            tag=use.tag,
            start_index=use.start_index,
            end_index=use.end_index,
        )
        for use in template_tag_uses(
            template,
            parse_nested=parse_nested,
        )
        if not use.closing
        and use.tag.startswith("c-")
        and use.tag.casefold() not in RESERVED_TAG_NAMES
        and use.tag.casefold().removeprefix("c-") not in normalized_names
    )


def template_tag_uses(
    template: object,
    *,
    parse_nested: Callable[[str], object] = parse_template,
) -> tuple[TemplateTagUse, ...]:
    """Return exact tag tokens from a template and its nested templates."""
    uses: list[TemplateTagUse] = []
    _collect_template_tags(
        template,
        uses,
        parse_nested=parse_nested,
        base_index=0,
    )
    return tuple(sorted(uses, key=lambda use: (use.start_index, use.end_index)))


def _component_surface_match(
    query: str,
    surface: str,
    *,
    is_class_name: bool,
) -> tuple[int, str, int] | None:
    if query == surface:
        return 0, surface, len(query)
    if not query:
        return 20, surface, 0
    compact_query = _compact_component_name(query)
    compact_surface = _compact_component_name(surface)
    if (
        is_class_name
        and len(compact_query) >= 2
        and query == compact_query
        and len(compact_query) < len(compact_surface)
        and compact_surface.casefold().startswith(compact_query.casefold())
    ):
        return 10, compact_surface, len(compact_query)
    if surface.startswith(query):
        return 20, surface, len(query)
    if surface.casefold().startswith(query.casefold()):
        return 30, surface, len(query)
    if compact_surface.startswith(compact_query):
        return 40, compact_surface, len(compact_query)
    if compact_surface.casefold().startswith(compact_query.casefold()):
        return 50, compact_surface, len(compact_query)
    return None


def _compact_component_name(value: str) -> str:
    return re.sub(r"[-_.]", "", value)


def _collect_template_tags(
    template: object,
    uses: list[TemplateTagUse],
    *,
    parse_nested: Callable[[str], object],
    base_index: int,
) -> None:
    elements = getattr(template, "elements", None)
    if type(elements) is not list:
        msg = "template must expose parser elements"
        raise TypeError(msg)
    for element in elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag = node.start_tag.name
        uses.append(
            TemplateTagUse(
                tag=tag.content,
                start_index=base_index + tag.start_index,
                end_index=base_index + tag.end_index,
                closing=False,
            )
        )
        end_tag = getattr(node, "end_tag", None)
        if end_tag is not None:
            tag = end_tag.name
            uses.append(
                TemplateTagUse(
                    tag=tag.content,
                    start_index=base_index + tag.start_index,
                    end_index=base_index + tag.end_index,
                    closing=True,
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_template_tags(
                body,
                uses,
                parse_nested=parse_nested,
                base_index=base_index,
            )
        for attr in node.start_tag.attrs:
            if attr.inner_value is None or not _is_nested_template_attr(attr):
                continue
            nested = _nested_template(attr.inner_value.content, parse_nested)
            if nested is None:
                continue
            nested_template, nested_start = nested
            _collect_template_tags(
                nested_template,
                uses,
                parse_nested=parse_nested,
                base_index=base_index + attr.inner_value.start_index + nested_start,
            )


def _is_nested_template_attr(attr: Any) -> bool:
    kind = getattr(attr, "kind", None)
    if kind is not None:
        return kind == HtmlAttrKind.Template
    # citry-core 1.4 constructs the enum but does not expose its attribute.
    # Its supported nested-template spelling still has the fragment wrapper,
    # which safely distinguishes it from Python and static attribute values.
    source = attr.inner_value.content.strip()
    return source.startswith("<>") and source.endswith("</>")


def _nested_template(
    source: str,
    parse_nested: Callable[[str], object],
) -> tuple[object, int] | None:
    stripped = source.lstrip()
    leading = len(source) - len(stripped)
    if stripped.startswith("<>") and stripped.rstrip().endswith("</>"):
        trailing = len(stripped.rstrip()) - len("</>")
        content_start = leading + len("<>")
        content_end = leading + trailing
    else:
        content_start = leading
        content_end = len(source.rstrip())
    if content_end < content_start:
        return None
    try:
        nested_start = len(source[:content_start].encode())
        return parse_nested(source[content_start:content_end]), nested_start
    except (SyntaxError, ValueError):
        return None


__all__ = [
    "ComponentNameMatch",
    "TemplateTagUse",
    "UnknownComponentUse",
    "component_name_match",
    "template_tag_uses",
    "unknown_component_uses",
]
