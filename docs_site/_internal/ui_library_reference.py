"""Load structured Citry UI API data and render its public reference."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import wrap
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from docs_site._internal.config_loading import DocsConfigError, load_yaml

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "ui_component_api.schema.json"
_CATEGORIES = (
    "inputs",
    "slots",
    "events",
    "methods",
    "css",
    "attributes",
    "selectors",
    "interfaces",
)
_CATEGORY_TITLES = {
    "inputs": "Inputs",
    "slots": "Slots",
    "events": "Events",
    "methods": "Methods",
    "attributes": "Attributes",
    "selectors": "Selectors",
    "css": "CSS",
    "interfaces": "Interfaces",
}
_ANCHOR_PARTS = {
    "inputs": "input",
    "slots": "slot",
    "events": "event",
    "methods": "method",
    "attributes": "attribute",
    "selectors": "selector",
    "css": "css",
}
_API_HEADING_RE = re.compile(r"^## API reference\s*$", re.MULTILINE)
_CONCEPT_HEADING_RE = re.compile(r"^## (?!API reference\s*$).+", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class UiApiReference:
    """One validated component-family API reference."""

    source: Path
    family: str
    components: tuple[str, ...]
    sections: Mapping[str, tuple[Mapping[str, Any], ...]]


def ui_library_reference_path(source_path: Path) -> Path:
    """Return the structured-reference path next to one component guide."""
    return source_path.with_suffix(".yml")


@lru_cache(maxsize=1)
def _reference_validator() -> Draft202012Validator:
    try:
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DocsConfigError(f"cannot load Citry UI API schema {_SCHEMA_PATH}: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def load_ui_api_reference(path: Path, *, expected_family: str) -> UiApiReference:
    """Load and validate one component family's structured API reference."""
    raw = load_yaml(path)
    error = best_match(_reference_validator().iter_errors(raw))
    if error is not None:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise DocsConfigError(f"{path}: {location}: {error.message}")
    if not isinstance(raw, Mapping):
        raise DocsConfigError(f"{path}: <root>: expected a mapping")

    family = str(raw["family"])
    if family != expected_family:
        raise DocsConfigError(f"{path}: family must be {expected_family!r}, got {family!r}")

    reference = UiApiReference(
        source=path,
        family=family,
        components=tuple(str(component) for component in raw["components"]),
        sections={
            category: tuple(_mapping(item, f"{path}: {category}") for item in raw[category])
            for category in _CATEGORIES
        },
    )
    _validate_reference_relationships(reference)
    return reference


def compose_ui_library_source(source_path: Path, *, family: str) -> str:
    """Append the component family's generated API reference to its guide."""
    source = source_path.read_text(encoding="utf-8")
    reference_path = ui_library_reference_path(source_path)
    if not reference_path.is_file():
        raise DocsConfigError(f"{source_path}: component guide requires sibling api.yml")
    if _API_HEADING_RE.search(source):
        raise DocsConfigError(
            f"{source_path}: structured component guides must leave API reference generation to api.yml"
        )
    if not _CONCEPT_HEADING_RE.search(source):
        raise DocsConfigError(f"{source_path}: component guide must explain use before its generated API reference")
    reference = load_ui_api_reference(reference_path, expected_family=family)
    return f"{source.rstrip()}\n\n{render_ui_api_reference(reference).rstrip()}\n"


def ui_api_entry_anchor(
    reference: UiApiReference,
    category: str,
    table: Mapping[str, Any],
    entry: Mapping[str, Any] | None = None,
) -> str:
    """Return the stable public anchor for a table entry or record interface."""
    if entry is not None and "anchor" in entry:
        return str(entry["anchor"])
    table_id = str(table["id"])
    if category == "interfaces":
        if str(table["kind"]) == "aliases":
            if entry is None:
                raise ValueError("alias tables do not have their own public anchor")
            return f"{reference.family}-interface-{entry['id']}"
        suffix = table_id if entry is None else f"{table_id}-{entry['id']}"
        return f"{reference.family}-interface-{suffix}"
    if entry is None:
        raise ValueError(f"{category} tables do not have their own public anchor")
    return f"{reference.family}-{_ANCHOR_PARTS[category]}-{table_id}-{entry['id']}"


def render_ui_api_reference(reference: UiApiReference) -> str:
    """Render one validated API reference as deterministic Markdown."""
    interface_anchors = _interface_anchors(reference)
    lines = [
        "## API reference",
        "",
    ]

    renderers = {
        "inputs": _render_inputs,
        "slots": _render_slots,
        "events": _render_events,
        "methods": _render_methods,
        "css": _render_css,
        "attributes": _render_attributes,
        "selectors": _render_selectors,
        "interfaces": _render_interfaces,
    }
    for category in _CATEGORIES:
        lines.extend((f"### {_CATEGORY_TITLES[category]}", ""))
        renderers[category](lines, reference, interface_anchors)
    return "\n".join(lines).rstrip() + "\n"


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DocsConfigError(f"{label}: expected a mapping")
    return value


def _validate_reference_relationships(reference: UiApiReference) -> None:
    components = set(reference.components)
    anchors: set[str] = set()
    interface_names: dict[str, str] = {}

    interface_table_ids: set[str] = set()
    for table in reference.sections["interfaces"]:
        table_id = str(table["id"])
        if table_id in interface_table_ids:
            raise DocsConfigError(f"{reference.source}: interfaces contains duplicate table id {table_id!r}")
        interface_table_ids.add(table_id)
        if str(table["kind"]) == "aliases":
            for entry in _entries(table):
                _claim_interface_name(reference, interface_names, str(entry["name"]), str(entry["id"]))
                _claim_anchor(anchors, ui_api_entry_anchor(reference, "interfaces", table, entry), reference.source)
        else:
            _claim_interface_name(reference, interface_names, str(table["name"]), table_id)
            _claim_anchor(anchors, ui_api_entry_anchor(reference, "interfaces", table), reference.source)
            _validate_entry_ids(reference, "interfaces", table, anchors)

    for category in _CATEGORIES[:-1]:
        table_ids: set[str] = set()
        for table in reference.sections[category]:
            table_id = str(table["id"])
            if table_id in table_ids:
                raise DocsConfigError(f"{reference.source}: {category} contains duplicate table id {table_id!r}")
            table_ids.add(table_id)
            component = str(table["component"])
            if component not in components:
                raise DocsConfigError(
                    f"{reference.source}: {category}.{table_id} references undeclared component {component!r}"
                )
            _validate_entry_ids(reference, category, table, anchors)

    for category in _CATEGORIES:
        for table in reference.sections[category]:
            for entry in _entries(table):
                for interface in _entry_interface_references(entry):
                    if interface not in interface_names:
                        raise DocsConfigError(
                            f"{reference.source}: {category}.{table['id']}.{entry['id']} references unknown "
                            f"interface {interface!r}"
                        )


def _claim_interface_name(
    reference: UiApiReference,
    names: dict[str, str],
    name: str,
    entry_id: str,
) -> None:
    previous = names.get(name)
    if previous is not None:
        raise DocsConfigError(
            f"{reference.source}: interface name {name!r} is duplicated by {previous!r} and {entry_id!r}"
        )
    names[name] = entry_id


def _validate_entry_ids(
    reference: UiApiReference,
    category: str,
    table: Mapping[str, Any],
    anchors: set[str],
) -> None:
    entry_ids: set[str] = set()
    for entry in _entries(table):
        entry_id = str(entry["id"])
        if entry_id in entry_ids:
            raise DocsConfigError(
                f"{reference.source}: {category}.{table['id']} contains duplicate entry id {entry_id!r}"
            )
        entry_ids.add(entry_id)
        explicit_anchor = entry.get("anchor")
        if explicit_anchor is not None:
            expected_prefix = f"{reference.family}-{_ANCHOR_PARTS[category]}-"
            if not str(explicit_anchor).startswith(expected_prefix):
                raise DocsConfigError(
                    f"{reference.source}: {category}.{table['id']}.{entry_id} anchor must start with "
                    f"{expected_prefix!r}"
                )
        _claim_anchor(anchors, ui_api_entry_anchor(reference, category, table, entry), reference.source)


def _claim_anchor(anchors: set[str], anchor: str, source: Path) -> None:
    if anchor in anchors:
        raise DocsConfigError(f"{source}: generated API anchor {anchor!r} is duplicated")
    anchors.add(anchor)


def _entry_interface_references(entry: Mapping[str, Any]) -> tuple[str, ...]:
    result: list[str] = []
    for value in entry.values():
        if isinstance(value, Mapping) and "interfaces" in value:
            result.extend(str(interface) for interface in value["interfaces"])
    return tuple(result)


def _entries(table: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(_mapping(entry, f"table {table['id']} entry") for entry in table["entries"])


def _interface_anchors(reference: UiApiReference) -> dict[str, str]:
    anchors: dict[str, str] = {}
    for table in reference.sections["interfaces"]:
        if str(table["kind"]) == "aliases":
            for entry in _entries(table):
                anchors[str(entry["name"])] = ui_api_entry_anchor(reference, "interfaces", table, entry)
        else:
            anchors[str(table["name"])] = ui_api_entry_anchor(reference, "interfaces", table)
    return anchors


def _render_inputs(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["inputs"]
    if not tables:
        lines.extend(("-", ""))
        return
    for table in tables:
        component = str(table["component"])
        channel = str(table["channel"])
        lines.extend((f"#### {component} {channel} inputs", ""))
        if channel == "server":
            _add_paragraph(
                lines,
                f"Server inputs are passed in a template through `<c-{component} ... />` or in Python through "
                f"`{component}(...)`.",
            )
            rows = [
                (
                    _entry_name(reference, "inputs", table, entry),
                    _display_value(entry["type"], interface_anchors),
                    _render_default(_mapping(entry["default"], "input default")),
                    _inline(str(entry["effect"])),
                )
                for entry in _entries(table)
            ]
            _add_table(
                lines,
                ("Input", "Type", "Default", "Effect"),
                rows,
                widths=_column_widths(table, ("fit", "12rem", "7rem", "auto")),
            )
        else:
            _add_paragraph(
                lines,
                f'Client inputs are passed in the browser through the `$c-props="{{ ... }}"` attribute on '
                f"`<c-{component} />`.",
            )
            rows = [
                (
                    _entry_name(reference, "inputs", table, entry),
                    _display_value(entry["type"], interface_anchors),
                    _inline(str(entry["omitted"])),
                    _inline(str(entry["effect"])),
                )
                for entry in _entries(table)
            ]
            _add_table(
                lines,
                ("Input", "Type", "Omitted behavior", "Effect"),
                rows,
                widths=_column_widths(table, ("fit", "12rem", "10rem", "auto")),
            )


def _render_slots(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["slots"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(
        lines,
        "Slots are passed as nested content or `<c-fill>` tags in a template, or through the `slots={...}` "
        "argument in Python.",
    )
    for table in tables:
        lines.extend((f"#### {table['component']} slots", ""))
        rows = [
            (
                _entry_name(reference, "slots", table, entry),
                "yes" if bool(entry["required"]) else "no",
                _display_value(entry["data"], interface_anchors),
                _inline(str(entry["fallback"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Slot", "Required", "Data", "Fallback"),
            rows,
            widths=_column_widths(table, ("fit", "6rem", "14rem", "auto")),
        )


def _render_events(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["events"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(
        lines,
        "Component events are callback inputs supplied through `$c-props`. Native browser events remain available "
        "through Alpine `@...` attributes.",
    )
    for table in tables:
        lines.extend((f"#### {table['component']} events", ""))
        rows = [
            (
                _entry_name(reference, "events", table, entry),
                _display_value(entry["signature"], interface_anchors),
                _inline(str(entry["trigger"])),
                _display_value(entry["detail"], interface_anchors),
                _inline(str(entry["behavior"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Event", "Signature", "Trigger and timing", "Detail", "Controlled and cancellation behavior"),
            rows,
            widths=_column_widths(table, ("fit", "13rem", "13rem", "11rem", "auto")),
        )


def _render_methods(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["methods"]
    if not tables:
        lines.extend(("-", ""))
        return
    for table in tables:
        lines.extend((f"#### {table['component']} methods", ""))
        rows = [
            (
                _entry_name(reference, "methods", table, entry),
                _display_value(entry["signature"], interface_anchors),
                _inline(str(entry["effect"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Method", "Signature", "Effect"),
            rows,
            widths=_column_widths(table, ("fit", "15rem", "auto")),
        )


def _render_attributes(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["attributes"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(
        lines,
        "HTML attributes defined on the components that you can refer to for CSS, inspection, and testing. Read-only.",
    )
    for table in tables:
        lines.extend((f"#### {table['component']} attributes", ""))
        rows = [
            (
                _entry_name(reference, "attributes", table, entry),
                _inline(str(entry["element"])),
                _display_value(entry["type"], interface_anchors),
                _inline(str(entry["meaning"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Attribute", "Element", "Type", "Meaning"),
            rows,
            widths=_column_widths(table, ("fit", "10rem", "13rem", "auto")),
        )


def _render_selectors(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],  # noqa: ARG001 - renderer signature is uniform
) -> None:
    tables = reference.sections["selectors"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(
        lines,
        "Selectors for the DOM nodes in the components that you can use for CSS, inspection, and testing.",
    )
    for table in tables:
        lines.extend((f"#### {table['component']} selectors", ""))
        rows = [
            (
                _entry_code(reference, "selectors", table, entry, str(entry["selector"])),
                _inline(str(entry["element"])),
                _inline(str(entry["purpose"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Selector", "Element", "Purpose"),
            rows,
            widths=_column_widths(table, ("15rem", "10rem", "auto")),
        )


def _render_css(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],  # noqa: ARG001 - renderer signature is uniform
) -> None:
    tables = reference.sections["css"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(
        lines,
        "CSS variables to theme the components. Set them on an ancestor or the component itself.",
    )
    for table in tables:
        component = str(table["component"])
        lines.extend((f"#### {component} CSS variables", ""))
        _add_paragraph(lines, f"Apply these variables to `{component}` or one of its ancestors.")
        rows = [
            (
                _entry_code(reference, "css", table, entry, str(entry["name"])),
                _code(str(entry["type"])),
                _inline(str(entry["purpose"])),
                _inline(str(entry["default"])),
            )
            for entry in _entries(table)
        ]
        _add_table(
            lines,
            ("Variable", "Type", "Purpose", "Default"),
            rows,
            widths=_column_widths(table, ("17rem", "8rem", "auto", "11rem")),
        )


def _render_interfaces(
    lines: list[str],
    reference: UiApiReference,
    interface_anchors: Mapping[str, str],
) -> None:
    tables = reference.sections["interfaces"]
    if not tables:
        lines.extend(("-", ""))
        return
    _add_paragraph(lines, "Aliases and data shapes referenced above.")
    for table in tables:
        if str(table["kind"]) == "aliases":
            lines.extend(("#### Input type aliases", ""))
            rows = [
                (
                    _entry_name(reference, "interfaces", table, entry),
                    _code(str(entry["definition"])),
                )
                for entry in _entries(table)
            ]
            _add_table(
                lines,
                ("Interface", "Definition"),
                rows,
                widths=_column_widths(table, ("fit", "auto")),
            )
            continue

        anchor = ui_api_entry_anchor(reference, "interfaces", table)
        lines.extend((f'<span id="{anchor}"></span>', "", f"#### `{table['name']}`", ""))
        entries = _entries(table)
        if not entries:
            lines.extend(("Empty dataclass: `{}`.", ""))
            continue
        rows = [
            (
                _entry_name(reference, "interfaces", table, entry),
                _display_value(entry["type"], interface_anchors),
                _inline(str(entry.get("default", "-"))),
                _inline(str(entry["meaning"])),
            )
            for entry in entries
        ]
        _add_table(
            lines,
            ("Field", "Type", "Default", "Meaning"),
            rows,
            widths=_column_widths(table, ("fit", "13rem", "8rem", "auto")),
        )


def _entry_name(
    reference: UiApiReference,
    category: str,
    table: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> str:
    return _entry_code(reference, category, table, entry, str(entry["name"]))


def _entry_code(
    reference: UiApiReference,
    category: str,
    table: Mapping[str, Any],
    entry: Mapping[str, Any],
    value: str,
) -> str:
    anchor = ui_api_entry_anchor(reference, category, table, entry)
    return f'<span id="{anchor}"></span>{_code(value)}'


def _display_value(value: object, interface_anchors: Mapping[str, str]) -> str:
    if isinstance(value, str):
        return _code(value)
    data = _mapping(value, "display value")
    display = _code(str(data["display"]))
    links = [f"[`{name}`](#{interface_anchors[str(name)]})" for name in data["interfaces"]]
    return f"{display} ({', '.join(links)})"


def _render_default(value: Mapping[str, Any]) -> str:
    kind = str(value["kind"])
    if kind in {"required", "generated"}:
        return kind
    if kind == "derived":
        return _inline(str(value["display"]))
    literal = value["value"]
    if literal is None:
        return _code("None")
    if isinstance(literal, bool):
        return _code("True" if literal else "False")
    if isinstance(literal, str):
        return _code(json.dumps(literal, ensure_ascii=False))
    return _code(str(literal))


def _add_paragraph(lines: list[str], text: str) -> None:
    lines.extend(wrap(text, width=92, break_long_words=False, break_on_hyphens=False))
    lines.append("")


def _column_widths(table: Mapping[str, Any], default: tuple[str, ...]) -> tuple[str, ...]:
    configured = table.get("column_widths")
    if configured is None:
        return default
    return tuple(str(width) for width in configured)


def _add_table(
    lines: list[str],
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    widths: tuple[str, ...],
) -> None:
    classes = ["ui-api-table"]
    styles: list[str] = []
    for index, width in enumerate(widths, start=1):
        if width == "auto":
            continue
        if width == "fit":
            classes.append(f"ui-api-table--fit-column-{index}")
            continue
        classes.append(f"ui-api-table--width-column-{index}")
        styles.append(f"--ui-api-column-{index}-width: {width}")

    attributes = f'class="{" ".join(classes)}" markdown="1"'
    if styles:
        attributes += f' style="{"; ".join(styles)}"'
    lines.extend((f"<div {attributes}>", ""))
    lines.append(f"| {' | '.join(headers)} |")
    lines.append(f"|{'|'.join('---' for _ in headers)}|")
    lines.extend(f"| {' | '.join(row)} |" for row in rows)
    lines.extend(("", "</div>", ""))


def _code(value: str) -> str:
    if "|" in value:
        return f"<code>{escape(value).replace('|', '&#124;')}</code>"
    return f"`{value}`"


def _inline(value: str) -> str:
    return value.replace("\\|", "|").replace("|", "\\|")
