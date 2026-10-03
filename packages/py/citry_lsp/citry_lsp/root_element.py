"""
Work out the type of a component's `$el` from its template's top-level nodes.

Vue sets `$el` to the DOM node its render root produced. Citry renders a
component's template without a wrapper, so the top-level nodes of the
authored template decide that node:

- one element gives that element, typed from the DOM's tag-name maps;
- a `v-if` or `c-if` chain, in the tag or attribute form, gives the union
  of its branches, plus `Comment`
  when no branch may render (Vue then renders a placeholder comment);
- a child component gives that child's own `$el` type;
- several top-level nodes, a `v-for` or `c-for`, a slot, or anything else
  Vue renders as a fragment gives `Node`. Vue points `$el` at the fragment's
  empty start marker, a `Text` node; on a page Vue takes over from
  server-rendered HTML, the marker is a `Comment` instead, so `Node` covers
  both.

Every result is a TypeScript type expression for the JavaScript provider.
`Node` is also the answer when the template cannot be read, so a reader
must narrow the value before using element APIs rather than getting `any`.
Like Vue's own `$el` type, no result includes `null`, although `$el` is
`null` until the component mounts.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from citry_core.template_parser import RESERVED_TAG_NAMES, HtmlAttrKind, TemplateElement

# The type of `$el` when the root is a fragment or cannot be proven.
UNKNOWN_ROOT = "Node"

# Vue built-in tags whose rendered node is a fragment marker, a teleport
# marker, or whatever their child renders; none is a plain element.
_VUE_BUILTIN_TAGS = frozenset(
    {
        "component",
        "keep-alive",
        "keepalive",
        "slot",
        "suspense",
        "teleport",
        "transition",
        "transition-group",
        "transitiongroup",
    }
)

# A child tag resolves to that component's own `$el` type, or `None` when the
# tag names no known component.
ComponentRootResolver = Callable[[str], str | None]


def template_root_element_type(template: Any, resolve_component: ComponentRootResolver) -> str:
    """
    Return the TypeScript type of `$el` for one parsed Citry template.

    `resolve_component` receives each top-level `c-*` component tag as
    authored and returns the child's `$el` type. The caller owns cycle and
    depth limits, since only it knows which components it is already
    resolving.
    """
    types = _root_types(template.elements, resolve_component)
    return UNKNOWN_ROOT if types is None else _union(types)


def _root_types(elements: Any, resolve_component: ComponentRootResolver) -> tuple[str, ...] | None:
    """
    Return the possible root node types of one list of sibling nodes.

    `None` means the list renders a fragment or something this function
    cannot prove, which the caller reports as `Node`.
    """
    items = _meaningful(elements)
    if not items:
        # Vue renders a comment placeholder for a template with no nodes.
        return ("Comment",)
    first = items[0]
    if _is_node(first) and _server_branch(first) == "c-if":
        chain, rest = _server_chain(items)
        # Anything after the chain is another root, which makes a fragment.
        return None if rest else _server_chain_types(chain, resolve_component)
    if _is_node(first) and _attr(first, "v-if") is not None:
        chain, rest = _vue_chain(items)
        return None if rest else _vue_chain_types(chain, resolve_component)
    if len(items) > 1:
        return None
    return _single_types(first, resolve_component)


def _meaningful(elements: Any) -> list[Any]:
    """Drop the nodes Vue's compiler drops at the root: whitespace and comments."""
    kept: list[Any] = []
    for element in elements:
        if isinstance(element, TemplateElement.Text):
            text = element._0.token.content
            # Citry's Vue compiler condenses whitespace-only text between
            # elements away and strips HTML comments from the render.
            if not text.strip() or text.lstrip().startswith("<!--"):
                continue
        kept.append(element)
    return kept


def _single_types(element: Any, resolve_component: ComponentRootResolver) -> tuple[str, ...] | None:
    """Return the node types one top-level template element can render."""
    if isinstance(element, TemplateElement.Text):
        return ("Text",)
    if not _is_node(element):
        # A `{{ }}` output or text from an external template provider may
        # render markup as well as text.
        return None
    return _element_types(element._0, resolve_component)


def _element_types(node: Any, resolve_component: ComponentRootResolver) -> tuple[str, ...] | None:
    """Return the node type of one element, ignoring any `v-if` it carries."""
    authored = node.start_tag.name.content
    tag = authored.lower()
    # `v-for` renders a list, which Vue wraps in a fragment, and the server
    # repeats a `c-for` element zero or more times.
    if any(_node_attr(node, name) is not None for name in ("v-for", "c-for", "c-empty")):
        return None
    if tag == "template":
        # `<template v-if>` renders its children in place of itself; a bare
        # `<template>` is a real `<template>` element.
        if any(_node_attr(node, name) is not None for name in ("v-if", "v-else-if", "v-else", "v-slot")):
            return _root_types(node.body.elements, resolve_component) if hasattr(node, "body") else ("Comment",)
        return ("HTMLTemplateElement",)
    if tag in RESERVED_TAG_NAMES or tag in _VUE_BUILTIN_TAGS:
        return None
    if tag == "c-element":
        # A dynamic tag name is always an element, but not a known one.
        return ("Element",)
    if tag.startswith("c-"):
        # An explicit `#c-key` may wrap the child in a keyed fragment.
        if any(attr.key.content.lower() == "#c-key" for attr in node.start_tag.attrs):
            return None
        child = resolve_component(authored)
        return None if child is None or child == UNKNOWN_ROOT else (child,)
    return (_tag_element_type(authored),)


def _tag_element_type(authored: str) -> str:
    """
    Return the DOM type of one native root tag as a TypeScript expression.

    TypeScript's own tag-name map decides the answer, so the list of tags
    stays with the DOM library. A root node is parsed as HTML, where only
    `<svg>` and `<math>` start another namespace, so a root such as
    `<circle>` or a custom element is an `HTMLElement`, as
    `document.createElement` makes it.
    """
    return f"CitryTagElement<{json.dumps(authored.lower())}>"


# The generic type `_tag_element_type` names. TypeScript resolves a
# conditional type only through a type parameter, so the lookup is generic.
TAG_ELEMENT_TYPEDEF = (
    "/** @template {string} T @typedef {"
    "T extends keyof HTMLElementTagNameMap ? HTMLElementTagNameMap[T] : "
    "T extends 'svg' ? SVGSVGElement : T extends 'math' ? MathMLElement : HTMLElement"
    "} CitryTagElement */"
)


def _vue_chain(items: list[Any]) -> tuple[list[Any], list[Any]]:
    """Split a leading `v-if` / `v-else-if` / `v-else` chain from the nodes after it."""
    chain = [items[0]]
    for index, item in enumerate(items[1:], start=1):
        if not _is_node(item) or _chain_closed(chain):
            return chain, items[index:]
        if _attr(item, "v-else-if") is None and _attr(item, "v-else") is None:
            return chain, items[index:]
        chain.append(item)
    return chain, []


def _chain_closed(chain: list[Any]) -> bool:
    """Whether the chain already ends with its `v-else` branch."""
    return _attr(chain[-1], "v-else") is not None


def _vue_chain_types(chain: list[Any], resolve_component: ComponentRootResolver) -> tuple[str, ...] | None:
    """Join the branch types; without `v-else` Vue may render a comment instead."""
    found: list[str] = []
    for item in chain:
        types = _element_types(item._0, resolve_component)
        if types is None:
            return None
        found.extend(types)
    if not _chain_closed(chain):
        found.append("Comment")
    return tuple(found)


def _server_branch(element: Any) -> str | None:
    """
    Return `c-if`, `c-elif`, or `c-else` when a node is a server branch.

    A branch is either the tag form, `<c-if cond="...">...</c-if>`, or the
    attribute form on the element itself, `<p c-if="...">`.
    """
    tag = _tag(element)
    if tag in {"c-if", "c-elif", "c-else"}:
        return tag
    for name in ("c-if", "c-elif", "c-else"):
        if _attr(element, name) is not None:
            return name
    return None


def _server_chain(items: list[Any]) -> tuple[list[Any], list[Any]]:
    """Split a leading `c-if` / `c-elif` / `c-else` chain from the nodes after it."""
    chain = [items[0]]
    for index, item in enumerate(items[1:], start=1):
        if (
            not _is_node(item)
            or _server_branch(chain[-1]) == "c-else"
            or _server_branch(item) not in {"c-elif", "c-else"}
        ):
            return chain, items[index:]
        chain.append(item)
    return chain, []


def _server_chain_types(chain: list[Any], resolve_component: ComponentRootResolver) -> tuple[str, ...] | None:
    """
    Join the server-selected branches.

    The server keeps one branch and drops the rest. The tag form keeps the
    branch body, which is a root list of its own; the attribute form keeps the
    element itself. With no `c-else`, the server may keep nothing, and Vue then
    renders a comment placeholder.
    """
    found: list[str] = []
    for item in chain:
        node = item._0
        if _tag(item) in {"c-if", "c-elif", "c-else"}:
            types = _root_types(node.body.elements if hasattr(node, "body") else [], resolve_component)
        else:
            types = _element_types(node, resolve_component)
        if types is None:
            return None
        found.extend(types)
    if _server_branch(chain[-1]) != "c-else":
        found.append("Comment")
    return tuple(found)


def _is_node(element: Any) -> bool:
    return isinstance(element, TemplateElement.Node)


def _tag(element: Any) -> str:
    return element._0.start_tag.name.content.lower()


def _attr(element: Any, name: str) -> Any | None:
    return _node_attr(element._0, name)


def _node_attr(node: Any, name: str) -> Any | None:
    """Return the attribute with this directive name, ignoring an argument or modifiers."""
    for attr in node.start_tag.attrs:
        if attr.kind == HtmlAttrKind.Template:
            continue
        key = attr.key.content.lower()
        if (
            key == name
            or key.startswith((f"{name}:", f"{name}."))
            or (
                # `#name` is the `v-slot` shorthand; `#c-*` is Citry metadata.
                name == "v-slot" and key.startswith("#") and not key.startswith("#c-")
            )
        ):
            return attr
    return None


def _union(types: tuple[str, ...]) -> str:
    """Join distinct types in source order; a lone `Node` absorbs the rest."""
    unique = tuple(dict.fromkeys(types))
    if UNKNOWN_ROOT in unique:
        return UNKNOWN_ROOT
    return " | ".join(unique)
