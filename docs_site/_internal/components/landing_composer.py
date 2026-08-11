"""A bounded visual composer that demonstrates real Citry UI nesting."""

from __future__ import annotations

import html
import json
import re
import textwrap
from copy import deepcopy
from functools import cache
from typing import Any

from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from docs_site._internal.project import current_docs_project
from docs_site._internal.util import flatten_for_markdown

_BROAD_CONTENT = ["layout", "content", "action", "control"]


def _slot(label: str, accepts: list[str]) -> dict[str, Any]:
    return {"label": label, "accepts": accepts}


# Definitions describe only the nesting relationships the board needs. The
# component classes remain the source of truth and are checked below.
_DEFINITIONS: dict[str, dict[str, Any]] = {
    "CContainer": {
        "label": "Container",
        "kind": "layout",
        "slots": {"default": _slot("Container content", _BROAD_CONTENT)},
    },
    "CStack": {
        "label": "Stack",
        "kind": "layout",
        "slots": {"default": _slot("Stack content", _BROAD_CONTENT)},
    },
    "CGroup": {
        "label": "Group",
        "kind": "layout",
        "slots": {"default": _slot("Group content", _BROAD_CONTENT)},
    },
    "CGrid": {
        "label": "Grid",
        "kind": "layout",
        "slots": {"default": _slot("Grid items", ["grid-item"])},
    },
    "CGridItem": {
        "label": "Grid item",
        "kind": "grid-item",
        "slots": {"default": _slot("Grid item content", _BROAD_CONTENT)},
    },
    "CCard": {
        "label": "Card",
        "kind": "content",
        "slots": {
            "media": _slot("Card media", []),
            "header": _slot("Card heading", []),
            "default": _slot("Card body", _BROAD_CONTENT),
            "actions": _slot("Card actions", ["action"]),
        },
    },
    "CDivider": {
        "label": "Divider",
        "kind": "content",
        "slots": {"default": _slot("Divider label", [])},
    },
    "CButton": {
        "label": "Button",
        "kind": "action",
        "slots": {"default": _slot("Button label", [])},
    },
    "CButtonGroup": {
        "label": "Button group",
        "kind": "content",
        "slots": {"default": _slot("Grouped buttons", ["action"])},
    },
    "CField": {
        "label": "Field and input",
        "kind": "content",
        "slots": {
            "label": _slot("Field label", []),
            "default": _slot("Field control", ["control"]),
            "description": _slot("Field description", []),
        },
    },
    "CInput": {
        "label": "Input",
        "kind": "control",
        "slots": {},
        "self_closing": True,
    },
    "CCheckbox": {
        "label": "Checkbox",
        "kind": "control",
        "slots": {
            "default": _slot("Checkbox label", []),
            "description": _slot("Checkbox description", []),
        },
    },
    "CSwitch": {
        "label": "Switch",
        "kind": "control",
        "slots": {
            "default": _slot("Switch label", []),
            "description": _slot("Switch description", []),
        },
    },
    "CBadge": {
        "label": "Badge",
        "kind": "content",
        "slots": {
            "start": _slot("Badge start", []),
            "default": _slot("Badge label", []),
            "end": _slot("Badge end", []),
        },
    },
    "CList": {
        "label": "List",
        "kind": "content",
        "slots": {"default": _slot("List items", ["list-item"])},
    },
    "CListItem": {
        "label": "List item",
        "kind": "list-item",
        "slots": {
            "start": _slot("Item start", []),
            "default": _slot("Item label", []),
            "description": _slot("Item description", []),
            "end": _slot("Item end", []),
        },
    },
    "CTabs": {
        "label": "Tabs",
        "kind": "content",
        "slots": {"default": _slot("Tabs and panels", ["tab-declaration"])},
    },
    "CTab": {
        "label": "Tab",
        "kind": "tab-declaration",
        "slots": {"default": _slot("Tab label", [])},
    },
    "CTabPanel": {
        "label": "Tab panel",
        "kind": "tab-declaration",
        "slots": {"default": _slot("Panel content", _BROAD_CONTENT)},
    },
    "CAlert": {
        "label": "Alert",
        "kind": "content",
        "slots": {
            "title": _slot("Alert title", []),
            "default": _slot("Alert message", _BROAD_CONTENT),
            "actions": _slot("Alert actions", ["action"]),
        },
    },
    "CProgress": {
        "label": "Progress",
        "kind": "content",
        "slots": {},
        "self_closing": True,
    },
    "CSkeleton": {
        "label": "Skeleton",
        "kind": "content",
        "slots": {},
        "self_closing": True,
    },
}


def _content(value: str) -> dict[str, str]:
    return {"kind": "text", "value": value}


def _drop() -> dict[str, Any]:
    return {"kind": "drop", "accepts": list(_BROAD_CONTENT)}


def _node(
    component: str,
    *,
    props: dict[str, Any] | None = None,
    slots: dict[str, list[dict[str, Any]]] | None = None,
    locked: bool = False,
) -> dict[str, Any]:
    return {
        "component": component,
        "props": props or {},
        "slots": slots or {},
        **({"locked": True} if locked else {}),
    }


_RECIPE_SURFACE = (
    "margin: 0.5rem 0; padding: 1rem; box-sizing: border-box; "
    "border: 1px solid color-mix(in srgb, CanvasText 13%, transparent); "
    "border-radius: 1rem; background: color-mix(in srgb, LinkText 4%, Canvas); "
    "box-shadow: 0 0.65rem 1.8rem color-mix(in srgb, CanvasText 9%, transparent);"
)


_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "button",
        "family": "button",
        "label": "Button",
        "node": _node(
            "CButton",
            props={
                "block": True,
                "size": "lg",
                "style": (
                    "margin: 0.5rem 0; --cui-button-radius: 999px; "
                    "--cui-button-font-weight: 750; "
                    "box-shadow: 0 0.7rem 1.5rem color-mix(in srgb, LinkText 24%, transparent);"
                ),
            },
            slots={"default": [_content("Create observation")]},
        ),
    },
    {
        "id": "button-group",
        "family": "button-group",
        "label": "Button group",
        "node": _node(
            "CButtonGroup",
            props={
                "label": "Navigation actions",
                "grow": True,
                "style": _RECIPE_SURFACE + " --cui-button-group-gap: 0.4rem;",
            },
            slots={
                "default": [
                    _node(
                        "CButton",
                        props={"intent": "neutral", "variant": "ghost"},
                        slots={"default": [_content("Back")]},
                    ),
                    _node(
                        "CButton",
                        props={"variant": "outline"},
                        slots={"default": [_content("Preview")]},
                    ),
                    _node("CButton", slots={"default": [_content("Publish")]}),
                ],
            },
        ),
    },
    {
        "id": "field-input",
        "family": "field-input",
        "label": "Field and input",
        "node": _node(
            "CField",
            props={
                "style": _RECIPE_SURFACE,
            },
            slots={
                "label": [_content("Project name")],
                "default": [
                    _node(
                        "CInput",
                        props={
                            "name": "$id:field",
                            "placeholder": "Aurora atlas",
                            "size": "lg",
                            "variant": "filled",
                        },
                    )
                ],
                "description": [_content("A clear name helps the whole team find it later.")],
            },
        ),
    },
    {
        "id": "checkbox",
        "family": "checkbox",
        "label": "Checkbox",
        "node": _node(
            "CCheckbox",
            props={
                "checked": True,
                "size": "lg",
                "style": _RECIPE_SURFACE,
            },
            slots={
                "default": [_content("Include archived observations")],
                "description": [_content("Search across active and completed projects.")],
            },
        ),
    },
    {
        "id": "switch",
        "family": "switch",
        "label": "Switch",
        "node": _node(
            "CSwitch",
            props={
                "checked": True,
                "size": "lg",
                "style": _RECIPE_SURFACE,
            },
            slots={
                "default": [_content("Live updates")],
                "description": [_content("Refresh the dashboard as new readings arrive.")],
            },
        ),
    },
    {
        "id": "container",
        "family": "grid-container",
        "label": "Container",
        "node": _node(
            "CContainer",
            props={
                "size": "lg",
                "gutter": "lg",
                "style": _RECIPE_SURFACE + " --cui-container-max-width: 52rem;",
            },
            slots={
                "default": [
                    _node(
                        "CAlert",
                        props={"intent": "info", "variant": "soft"},
                        slots={
                            "title": [_content("A comfortable content width")],
                            "default": [_content("Container keeps the page readable as the viewport grows.")],
                        },
                    ),
                    _drop(),
                ],
            },
        ),
    },
    {
        "id": "group",
        "family": "flow-layout",
        "label": "Group",
        "node": _node(
            "CGroup",
            props={
                "gap": "md",
                "align": "center",
                "justify": "between",
                "wrap": True,
                "style": _RECIPE_SURFACE,
            },
            slots={
                "default": [
                    _content("Observatory ready"),
                    _node(
                        "CBadge",
                        props={"intent": "success", "shape": "pill", "variant": "solid"},
                        slots={"default": [_content("All systems online")]},
                    ),
                    _drop(),
                ],
            },
        ),
    },
    {
        "id": "grid",
        "family": "grid-container",
        "label": "Grid",
        "node": _node(
            "CGrid",
            props={
                "gap": "lg",
                "min_col": "11rem",
                "style": "margin: 0.5rem 0;",
            },
            slots={
                "default": [
                    _node(
                        "CGridItem",
                        slots={
                            "default": [
                                _node(
                                    "CCard",
                                    props={
                                        "size": "sm",
                                        "style": (
                                            "--cui-card-background: color-mix(in srgb, #2563eb 8%, Canvas); "
                                            "--cui-card-border-color: color-mix(in srgb, #2563eb 24%, transparent);"
                                        ),
                                    },
                                    slots={
                                        "header": [
                                            _node(
                                                "CGroup",
                                                props={"align": "center", "justify": "between"},
                                                slots={
                                                    "default": [
                                                        _content("Observation plan"),
                                                        _node(
                                                            "CBadge",
                                                            props={"intent": "primary", "shape": "pill"},
                                                            slots={"default": [_content("Tonight")]},
                                                        ),
                                                    ]
                                                },
                                            )
                                        ],
                                        "default": [_content("Three targets are ready for the evening window.")],
                                        "actions": [_drop()],
                                    },
                                ),
                            ],
                        },
                    ),
                    _node(
                        "CGridItem",
                        slots={
                            "default": [
                                _node(
                                    "CCard",
                                    props={
                                        "size": "sm",
                                        "style": (
                                            "--cui-card-background: color-mix(in srgb, #7c3aed 8%, Canvas); "
                                            "--cui-card-border-color: color-mix(in srgb, #7c3aed 24%, transparent);"
                                        ),
                                    },
                                    slots={
                                        "header": [
                                            _node(
                                                "CGroup",
                                                props={"align": "center", "justify": "between"},
                                                slots={
                                                    "default": [
                                                        _content("Team notes"),
                                                        _node(
                                                            "CBadge",
                                                            props={"intent": "success", "shape": "pill"},
                                                            slots={"default": [_content("4 new")]},
                                                        ),
                                                    ]
                                                },
                                            )
                                        ],
                                        "default": [_content("The latest handoff is organized and ready to share.")],
                                        "actions": [_drop()],
                                    },
                                ),
                            ],
                        },
                    ),
                ],
            },
        ),
    },
    {
        "id": "divider",
        "family": "divider",
        "label": "Divider",
        "node": _node(
            "CDivider",
            props={
                "label_pos": "center",
                "size": "md",
                "variant": "dashed",
                "style": (
                    "margin: 1.1rem 0; --cui-divider-color: color-mix(in srgb, LinkText 58%, transparent); "
                    "--cui-divider-label-color: LinkText; --cui-divider-label-font-weight: 750;"
                ),
            },
            slots={"default": [_content("Tonight's schedule")]},
        ),
    },
    {
        "id": "card",
        "family": "card",
        "label": "Card",
        "node": _node(
            "CCard",
            props={
                "style": "margin: 0.5rem 0;",
            },
            slots={
                "media": [_node("CSkeleton", props={"height": "8rem", "animation": "wave"})],
                "header": [_content("Observation summary")],
                "default": [
                    _content("Three clear nights are forecast this week, with the best visibility after midnight.")
                ],
                "actions": [_drop()],
            },
        ),
    },
    {
        "id": "badge",
        "family": "badge",
        "label": "Badge",
        "node": _node(
            "CBadge",
            props={
                "intent": "success",
                "shape": "pill",
                "size": "lg",
                "variant": "solid",
                "style": (
                    "margin: 0.5rem 0; box-shadow: 0 0.45rem 1rem color-mix(in srgb, #067647 20%, transparent);"
                ),
            },
            slots={"default": [_content("Ready for review")]},
        ),
    },
    {
        "id": "list",
        "family": "list",
        "label": "List",
        "node": _node(
            "CList",
            props={
                "label": "Observation queue",
                "variant": "surface",
                "divided": True,
                "style": _RECIPE_SURFACE + " --cui-list-item-padding: 0.75rem 0.85rem;",
            },
            slots={
                "default": [
                    _node(
                        "CListItem",
                        slots={
                            "default": [_content("Calibrate telescope")],
                            "description": [_content("Alignment and focus check")],
                            "end": [
                                _node(
                                    "CBadge",
                                    props={"intent": "success", "shape": "pill"},
                                    slots={"default": [_content("Ready")]},
                                )
                            ],
                        },
                    ),
                    _node(
                        "CListItem",
                        slots={
                            "default": [_content("Open observatory roof")],
                            "description": [_content("Scheduled after civil twilight")],
                            "end": [_content("20:42")],
                        },
                    ),
                    _node(
                        "CListItem",
                        slots={
                            "default": [_content("Begin exposure")],
                            "description": [_content("M31 · 12 frames · 180 seconds")],
                            "end": [
                                _node(
                                    "CBadge",
                                    props={"intent": "primary", "shape": "pill"},
                                    slots={"default": [_content("Queued")]},
                                )
                            ],
                        },
                    ),
                ],
            },
        ),
    },
    {
        "id": "tabs",
        "family": "tabs",
        "label": "Tabs",
        "node": _node(
            "CTabs",
            props={
                "default_value": "$id:overview",
                "aria_label": "Composition sections",
                "density": "comfortable",
                "grow": True,
                "variant": "pill",
                "style": (
                    _RECIPE_SURFACE + " --cui-tabs-accent: light-dark(#5946d2, #b4a9ff); "
                    "--cui-tabs-active-background: color-mix(in srgb, var(--cui-tabs-accent) 15%, Canvas);"
                ),
            },
            slots={
                "default": [
                    _node(
                        "CTab", props={"value": "$id:overview"}, slots={"default": [_content("Overview")]}, locked=True
                    ),
                    _node(
                        "CTab", props={"value": "$id:details"}, slots={"default": [_content("Details")]}, locked=True
                    ),
                    _node(
                        "CTabPanel",
                        props={"value": "$id:overview"},
                        slots={
                            "default": [
                                _node(
                                    "CAlert",
                                    props={"intent": "info", "size": "lg", "variant": "soft"},
                                    slots={
                                        "title": [_content("A real component tree")],
                                        "default": [_content("Components can be nested inside each panel.")],
                                    },
                                ),
                                _drop(),
                            ],
                        },
                        locked=True,
                    ),
                    _node(
                        "CTabPanel",
                        props={"value": "$id:details"},
                        slots={
                            "default": [
                                _node(
                                    "CCard",
                                    props={"variant": "outline"},
                                    slots={
                                        "header": [_content("Nested composition")],
                                        "default": [_content("This Card lives inside a Tab Panel.")],
                                        "actions": [_node("CButton", slots={"default": [_content("Continue")]})],
                                    },
                                ),
                            ],
                        },
                        locked=True,
                    ),
                ],
            },
        ),
    },
    {
        "id": "alert",
        "family": "alert",
        "label": "Alert",
        "node": _node(
            "CAlert",
            props={
                "intent": "success",
                "size": "lg",
                "variant": "soft",
                "style": "margin: 0.5rem 0; box-shadow: 0 0.65rem 1.6rem color-mix(in srgb, #067647 12%, transparent);",
            },
            slots={
                "title": [_content("Import complete")],
                "default": [_content("Twelve observations are ready to review.")],
                "actions": [_drop()],
            },
        ),
    },
    {
        "id": "progress",
        "family": "progress",
        "label": "Progress",
        "node": _node(
            "CCard",
            props={
                "variant": "subtle",
                "style": (
                    "margin: 0.5rem 0; --cui-card-background: color-mix(in srgb, #6d5ce7 7%, Canvas); "
                    "--cui-card-border-color: color-mix(in srgb, #6d5ce7 20%, transparent);"
                ),
            },
            slots={
                "header": [
                    _node(
                        "CGroup",
                        props={"align": "center", "justify": "between"},
                        slots={
                            "default": [
                                _content("Importing observations"),
                                _node(
                                    "CBadge",
                                    props={"intent": "primary", "shape": "pill"},
                                    slots={"default": [_content("68%")]},
                                ),
                            ]
                        },
                    )
                ],
                "default": [
                    _node(
                        "CProgress",
                        props={
                            "label": "Importing observations",
                            "value": 68,
                            "shape": "pill",
                            "size": "lg",
                            "style": (
                                "--cui-progress-range-color: light-dark(#5946d2, #b4a9ff); "
                                "--cui-progress-track-color: color-mix(in srgb, "
                                "var(--cui-progress-range-color) 15%, Canvas);"
                            ),
                        },
                    )
                ],
            },
        ),
    },
)


def _validate_catalog() -> None:
    component_names = {component.__name__ for component in citry_ui.COMPONENTS}
    missing_components = sorted(set(_DEFINITIONS) - component_names)
    if missing_components:
        raise RuntimeError(f"Landing composer names missing Citry UI components: {', '.join(missing_components)}")

    for component_name, definition in _DEFINITIONS.items():
        component = getattr(citry_ui, component_name)
        slots = set(getattr(component.Slots, "__annotations__", {}))
        unknown_slots = set(definition.get("slots", {})) - slots
        if unknown_slots:
            raise RuntimeError(
                f"Landing composer names unknown {component_name} slots: {', '.join(sorted(unknown_slots))}",
            )

    recipe_ids: set[str] = set()

    def validate_node(node: dict[str, Any], *, recipe_id: str) -> None:
        component_name = node.get("component")
        if component_name not in _DEFINITIONS:
            raise RuntimeError(f"Landing composer recipe {recipe_id!r} names unknown component {component_name!r}")
        component = getattr(citry_ui, component_name)
        kwargs = set(getattr(component.Kwargs, "__annotations__", {}))
        unknown_props = set(node.get("props", {})) - kwargs
        if unknown_props:
            raise RuntimeError(
                f"Landing composer recipe {recipe_id!r} names unknown {component_name} inputs: "
                f"{', '.join(sorted(unknown_props))}",
            )
        definition_slots = _DEFINITIONS[component_name].get("slots", {})
        unknown_slots = set(node.get("slots", {})) - set(definition_slots)
        if unknown_slots:
            raise RuntimeError(
                f"Landing composer recipe {recipe_id!r} names unavailable {component_name} slots: "
                f"{', '.join(sorted(unknown_slots))}",
            )
        for items in node.get("slots", {}).values():
            for item in items:
                if item.get("kind") == "text":
                    if not isinstance(item.get("value"), str):
                        raise RuntimeError(f"Landing composer recipe {recipe_id!r} has non-text slot content")
                elif item.get("kind") == "drop":
                    accepts = item.get("accepts")
                    if (
                        not isinstance(accepts, list)
                        or not accepts
                        or any(value not in _BROAD_CONTENT for value in accepts)
                    ):
                        raise RuntimeError(f"Landing composer recipe {recipe_id!r} has an invalid drop target")
                else:
                    validate_node(item, recipe_id=recipe_id)

    for recipe in _RECIPES:
        recipe_id = recipe["id"]
        if recipe_id in recipe_ids:
            raise RuntimeError(f"Landing composer repeats recipe {recipe_id!r}")
        recipe_ids.add(recipe_id)
        validate_node(recipe["node"], recipe_id=recipe_id)


def _instantiate(template: dict[str, Any], *, start: int = 1) -> tuple[dict[str, Any], int]:
    next_id = start
    tokens: dict[str, str] = {}

    def resolve(value: Any) -> Any:
        if not isinstance(value, str) or not value.startswith("$id:"):
            return value
        token = value[4:]
        if token not in tokens:
            tokens[token] = f"composer-{token}-{start}"
        return tokens[token]

    def visit(node: dict[str, Any]) -> dict[str, Any]:
        nonlocal next_id
        node_id = f"node-{next_id}"
        next_id += 1
        return {
            "id": node_id,
            "component": node["component"],
            "props": {name: resolve(value) for name, value in node.get("props", {}).items()},
            "slots": {
                name: [
                    {"kind": "text", "value": item["value"]}
                    if item.get("kind") == "text"
                    else deepcopy(item)
                    if item.get("kind") == "drop"
                    else visit(item)
                    for item in items
                ]
                for name, items in node.get("slots", {}).items()
            },
            **({"locked": True} if node.get("locked") else {}),
        }

    return visit(deepcopy(template)), next_id


def _initial_state() -> dict[str, Any]:
    return {
        "nextId": 1,
        "root": {
            "id": "composer-root",
            "component": "CStack",
            "props": {"gap": "lg"},
            "slots": {"default": []},
            "locked": True,
        },
    }


def _escaped_text(value: object) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    return html.escape(text, quote=True)


def _attribute(name: str, value: Any) -> str:
    if value is True:
        return f" {name}"
    if value in (False, None, ""):
        return ""
    if isinstance(value, (int, float)):
        return f' c-{name.replace("_", "-")}="{value}"'
    return f' {name}="{_escaped_text(value)}"'


def _serialize_node(node: dict[str, Any], level: int = 0) -> list[str]:
    indent = "  " * level
    component = node["component"]
    definition = _DEFINITIONS[component]
    attrs = "".join(_attribute(name, value) for name, value in node.get("props", {}).items())
    if definition.get("self_closing"):
        return [f"{indent}<c-{component}{attrs} />"]

    lines = [f"{indent}<c-{component}{attrs}>"]
    has_named_content = any(name != "default" and items for name, items in node.get("slots", {}).items())
    for slot_name, items in node.get("slots", {}).items():
        if not items:
            continue
        child_level = level + 1
        uses_fill = slot_name != "default" or has_named_content
        if uses_fill:
            lines.append(f'{"  " * child_level}<c-fill name="{slot_name}">')
            child_level += 1
        for item in items:
            if item.get("kind") == "text":
                lines.extend(f"{'  ' * child_level}{line}" for line in _escaped_text(item["value"]).splitlines())
            elif item.get("kind") == "drop":
                accepts = " ".join(item["accepts"])
                lines.extend(
                    (
                        f'{"  " * child_level}<button type="button" class="landing-composer__drop"',
                        f'{"  " * (child_level + 1)}data-composer-drop data-composer-accepts="{accepts}"',
                        f'{"  " * (child_level + 1)}aria-label="Choose this spot for another component">',
                        f'{"  " * (child_level + 1)}<span aria-hidden="true">+</span>',
                        f"{'  ' * (child_level + 1)}<strong>Drop here</strong>",
                        f"{'  ' * child_level}</button>",
                    ),
                )
            else:
                lines.extend(_serialize_node(item, child_level))
        if uses_fill:
            lines.append(f"{'  ' * (child_level - 1)}</c-fill>")
    lines.append(f"{indent}</c-{component}>")
    return lines


def _serialize_source(state: dict[str, Any]) -> str:
    template = "\n".join(_serialize_node(state["root"]))
    indented = textwrap.indent(template, "      ")
    return (
        "import citry_ui\n"
        "from citry import Component, citry\n\n"
        "citry.register_library(citry_ui)\n\n\n"
        "class LandingComposition(Component):\n"
        '    template = """\n'
        f"{indented}\n"
        '    """\n\n\n'
        "preview = LandingComposition()\n\n"
        "preview  # noqa: B018\n"
    )


def _composer_groups() -> list[dict[str, Any]]:
    _validate_catalog()
    project = current_docs_project()
    catalog_families = {projection.family for projection in project.ui_library.projections}
    recipe_families = {recipe["family"] for recipe in _RECIPES}
    missing_families = sorted(recipe_families - catalog_families)
    if missing_families:
        raise RuntimeError(f"Landing composer recipes are missing from ui_library.yml: {', '.join(missing_families)}")

    recipes_by_family: dict[str, list[dict[str, Any]]] = {}
    for recipe in _RECIPES:
        recipes_by_family.setdefault(recipe["family"], []).append(recipe)
    groups = [
        {
            "id": group.id,
            "label": group.label,
            "recipes": [
                {
                    "id": recipe["id"],
                    "label": recipe["label"],
                    "kind": _DEFINITIONS[recipe["node"]["component"]]["kind"],
                }
                for projection in group.projections
                for recipe in recipes_by_family.get(projection.family, [])
            ],
        }
        for group in project.ui_library.groups
        if any(projection.family in recipes_by_family for projection in group.projections)
    ]
    return groups


def _recipe_bank_template() -> str:
    templates: list[str] = []
    for index, recipe in enumerate(_RECIPES, start=1):
        node, _ = _instantiate(recipe["node"], start=index * 100)
        rendered_recipe = "\n".join(_serialize_node(node, level=3))
        recipe_id = _escaped_text(recipe["id"])
        templates.extend(
            (
                f'  <template data-composer-recipe-template="{recipe_id}">',
                f'    <div class="landing-composer__rendered-recipe" data-composer-rendered-recipe="{recipe_id}">',
                rendered_recipe,
                "    </div>",
                "  </template>",
            ),
        )
    return "\n".join(templates)


_recipe_citry = Citry(autodiscover=False)
_recipe_citry.register_library(citry_ui)


class LandingRecipeBank(Component):
    """Render inert, reusable component recipes through the real Citry UI classes."""

    citry = _recipe_citry
    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    template = _recipe_bank_template()


@cache
def _render_recipe_bank() -> Markup:
    rendered = str(LandingRecipeBank())
    rendered = re.sub(r"<script\b[^>]*>.*?</script>", "", rendered, flags=re.IGNORECASE | re.DOTALL)
    rendered = re.sub(r"<!--citry:.*?-->", "", rendered, flags=re.DOTALL)
    rendered = re.sub(r'\sdata-cid(?:-[^\s=>]+)?(?:="[^"]*")?', "", rendered)
    return Markup(rendered)  # noqa: S704 - trusted output from the fixed recipe component


@cache
def _render_recipe_payload() -> Markup:
    """Encode recipe HTML so the surrounding Markdown pass cannot parse it."""
    payload = json.dumps(str(_render_recipe_bank()), ensure_ascii=True)
    payload = payload.replace("<", r"\u003c").replace("&", r"\u0026")
    return Markup(payload)  # noqa: S704 - JSON with every HTML opener escaped above


class LandingComposerMarkup(Component):
    """Render the composer shell before the surrounding Markdown pass."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"groups": _composer_groups(), "recipe_payload": _render_recipe_payload()}

    template = """
      <div
        class="landing-composer"
        data-landing-composer
      >
        <div class="landing-composer__bar">
          <div class="landing-composer__bar-copy">
            <h3 id="landing-composer-palette-title">Citry UI components</h3>
            <p>Drag a component onto the canvas and watch it arrive ready to use.</p>
          </div>
          <button type="button" class="landing-composer__reset" data-composer-reset>Reset</button>
        </div>

        <div class="landing-composer__layout">
          <aside class="landing-composer__palette" aria-labelledby="landing-composer-palette-title">
            <div c-for="group in groups" class="landing-composer__palette-group">
              <h4>{{ group['label'] }}</h4>
              <ul>
                <li c-for="recipe in group['recipes']" data-composer-palette-item>
                  <button
                    type="button"
                    class="landing-composer__palette-item"
                    c-data-composer-palette-drag="recipe['id']"
                    c-data-composer-kind="recipe['kind']"
                    c-aria-label="recipe['label'] + '. Drag to the sample page or press Enter to place it.'"
                  >
                    <span class="landing-composer__grip" aria-hidden="true">⠿</span>
                    <strong>{{ recipe['label'] }}</strong>
                  </button>
                </li>
              </ul>
            </div>
          </aside>

          <section class="landing-composer__workspace" aria-label="Component sample page">
            <div
              class="landing-composer__board"
              data-composer-board
            >
              <div class="landing-composer__drag-cue" data-composer-drag-cue aria-hidden="true">
                Release over a blue area
              </div>
              <div class="landing-composer__canvas" data-composer-canvas>
                <button
                  type="button"
                  class="landing-composer__drop landing-composer__drop--root"
                  data-composer-drop
                  data-composer-accepts="layout content action control"
                  aria-pressed="true"
                >
                  <span aria-hidden="true"></span>
                  <strong>Drop a component here</strong>
                  <small>Start with a Card, Grid, or anything you like.</small>
                </button>
              </div>
            </div>
          </section>
        </div>

        <script type="application/json" data-composer-recipe-bank>{{ recipe_payload }}</script>
      </div>
    """


class LandingComposer(Component):
    """Protect the static-first composer shell from Markdown reinterpretation."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = flatten_for_markdown(str(LandingComposerMarkup()))
        return {"markup": Markup(markup)}  # noqa: S704 - generated by the component above

    template = "{{ markup }}"


__all__ = ["LandingComposer", "LandingComposerMarkup", "LandingRecipeBank"]
