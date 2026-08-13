"""Pure Python adapter used by the browser playground's analysis Worker."""

from __future__ import annotations

import json
import re

from citry_core.template_parser import RESERVED_TAG_NAMES, parse_template

try:
    from citry_portable_ide import component_name_match, template_tag_uses, unknown_component_uses
except ImportError:
    from citry._portable_ide import component_name_match, template_tag_uses, unknown_component_uses

_LEGACY_POSITION = re.compile(r"-->\s+(\d+):(\d+)")
_TAG_PREFIX = re.compile(r"</?(c-[A-Za-z0-9-]*)$")
_PARSE_FALLBACK_CODE = "citry.parse"
_UNKNOWN_COMPONENT_CODE = "citry.template.unknown-component"
_COMPONENT_DOCUMENTATION_URL = "https://citry.dev/concepts/components/"
_components: tuple[dict[str, object], ...] = ()
_components_by_name: dict[str, tuple[dict[str, object], ...]] | None = None

_TAG_HELP = {
    "c-if": (
        "Conditional branch",
        "Render this block when its cond Python expression is truthy.",
        "https://citry.dev/reference/builtins/#c-if",
    ),
    "c-elif": (
        "Else-if branch",
        "Add another conditional block after an adjacent c-if or c-elif.",
        "https://citry.dev/reference/builtins/#c-elif",
    ),
    "c-else": (
        "Else branch",
        "Add the final fallback block to an adjacent conditional chain.",
        "https://citry.dev/reference/builtins/#c-else",
    ),
    "c-for": (
        "Loop over an iterable",
        "Repeat this block using the Python-style loop clause in each.",
        "https://citry.dev/reference/builtins/#c-for",
    ),
    "c-empty": (
        "Empty branch for a loop",
        "Render this block when the adjacent c-for produces no values.",
        "https://citry.dev/reference/builtins/#c-empty",
    ),
    "c-raw": (
        "Render its body as literal text",
        "Keep template-looking text in this block unchanged.",
        "https://citry.dev/reference/builtins/#c-raw",
    ),
    "c-fill": (
        "Fill a component slot",
        "Choose the slot that receives this block of content.",
        "https://citry.dev/reference/builtins/#c-fill",
    ),
    "c-slot": (
        "Declare a component slot outlet",
        "Mark where content supplied by a component caller should appear.",
        "https://citry.dev/reference/builtins/#c-slot",
    ),
}


def _require_dict(value: object, fields: frozenset[str], label: str) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != fields:
        msg = f"{label} must contain exactly {sorted(fields)!r}"
        raise ValueError(msg)
    return value


def _optional_string(value: object, label: str) -> str | None:
    if value is not None and type(value) is not str:
        msg = f"{label} must be a string or null"
        raise ValueError(msg)
    return value


def _catalog_field(value: object) -> dict[str, object]:
    field = _require_dict(
        value,
        frozenset({"name", "required", "typeDisplay", "description"}),
        "catalog field",
    )
    if type(field["name"]) is not str or not field["name"] or type(field["required"]) is not bool:
        msg = "catalog field name and required flag are invalid"
        raise ValueError(msg)
    _optional_string(field["typeDisplay"], "catalog field typeDisplay")
    _optional_string(field["description"], "catalog field description")
    return field


def _catalog_component(value: object) -> dict[str, object]:
    component = _require_dict(
        value,
        frozenset(
            {
                "definitionId",
                "name",
                "aliases",
                "className",
                "importPath",
                "description",
                "builtin",
                "kwargs",
                "slots",
            }
        ),
        "catalog component",
    )
    if (
        type(component["definitionId"]) is not str
        or not component["definitionId"]
        or type(component["name"]) is not str
        or not component["name"]
        or type(component["builtin"]) is not bool
    ):
        msg = "catalog component identity is invalid"
        raise ValueError(msg)
    aliases = component["aliases"]
    if type(aliases) is not list or any(type(alias) is not str or not alias for alias in aliases):
        msg = "catalog component aliases must be non-empty strings"
        raise ValueError(msg)
    if len(aliases) != len(set(aliases)):
        msg = "catalog component aliases must be unique"
        raise ValueError(msg)
    _optional_string(component["className"], "catalog component className")
    _optional_string(component["importPath"], "catalog component importPath")
    _optional_string(component["description"], "catalog component description")
    for field_name in ("kwargs", "slots"):
        fields = component[field_name]
        if type(fields) is not list:
            msg = f"catalog component {field_name} must be a list"
            raise ValueError(msg)
        component[field_name] = [_catalog_field(field) for field in fields]
        names = [field["name"] for field in component[field_name]]
        if len(names) != len(set(names)):
            msg = f"catalog component {field_name} names must be unique"
            raise ValueError(msg)
    return component


def _component_identity(name: str) -> str:
    return re.sub(r"[-_.]", "", name.removeprefix("c-")).casefold()


def update_catalog_json(payload_json: str) -> str:
    """Replace runtime registry facts after one successful exact-source run."""
    global _components, _components_by_name  # noqa: PLW0603

    payload = json.loads(payload_json)
    if payload is None:
        _components = ()
        _components_by_name = None
        return json.dumps({"updated": True}, separators=(",", ":"))
    snapshot = _require_dict(payload, frozenset({"schemaVersion", "registries"}), "catalog snapshot")
    if type(snapshot["schemaVersion"]) is not int or snapshot["schemaVersion"] != 1:
        msg = "catalog snapshot schema is unsupported"
        raise ValueError(msg)
    if type(snapshot["registries"]) is not list:
        msg = "catalog snapshot schema is unsupported"
        raise ValueError(msg)
    components: list[dict[str, object]] = []
    engine_ids: set[str] = set()
    for value in snapshot["registries"]:
        registry = _require_dict(value, frozenset({"engineId", "components"}), "catalog registry")
        if type(registry["engineId"]) is not str or not registry["engineId"] or registry["engineId"] in engine_ids:
            msg = "catalog registry engineId is invalid or duplicated"
            raise ValueError(msg)
        engine_ids.add(registry["engineId"])
        if type(registry["components"]) is not list:
            msg = "catalog registry components must be a list"
            raise ValueError(msg)
        components.extend(_catalog_component(component) for component in registry["components"])
    by_name: dict[str, list[dict[str, object]]] = {}
    for component in components:
        for name in (component["name"], *component["aliases"]):
            by_name.setdefault(_component_identity(name), []).append(component)
    _components = tuple(components)
    _components_by_name = {name: tuple(records) for name, records in by_name.items()}
    return json.dumps({"updated": True}, separators=(",", ":"))


def _position_to_index(source: str, value: object) -> int:
    position = _require_dict(value, frozenset({"line", "character"}), "position")
    line = position["line"]
    character = position["character"]
    if type(line) is not int or line < 0 or type(character) is not int or character < 0:
        msg = "position coordinates must be non-negative integers"
        raise ValueError(msg)

    lines = source.splitlines(keepends=True)
    if not lines:
        lines = [""]
    if line >= len(lines):
        msg = "position line is outside the template"
        raise ValueError(msg)
    line_start = sum(len(part) for part in lines[:line])
    line_text = lines[line]
    content = line_text.removesuffix("\n").removesuffix("\r")
    units = 0
    for offset, char in enumerate(content):
        if units == character:
            return line_start + offset
        units += 2 if ord(char) > 0xFFFF else 1
        if units > character:
            msg = "position splits a UTF-16 surrogate pair"
            raise ValueError(msg)
    if units == character:
        return line_start + len(content)
    msg = "position character is outside the template line"
    raise ValueError(msg)


def _index_to_position(source: str, index: int) -> dict[str, int]:
    if index < 0 or index > len(source):
        msg = "template index is outside the source"
        raise ValueError(msg)
    prefix = source[:index]
    line = prefix.count("\n")
    line_start = prefix.rfind("\n") + 1
    character = sum(2 if ord(char) > 0xFFFF else 1 for char in source[line_start:index])
    return {"line": line, "character": character}


def _byte_to_index(source: str, byte_index: int) -> int:
    encoded = source.encode()
    if byte_index < 0 or byte_index > len(encoded):
        msg = "parser byte index is outside the template"
        raise ValueError(msg)
    return len(encoded[:byte_index].decode())


def _range(source: str, start: int, end: int) -> dict[str, object]:
    return {
        "start": _index_to_position(source, start),
        "end": _index_to_position(source, end),
    }


def _legacy_error_range(source: str, message: str) -> tuple[int, int]:
    match = _LEGACY_POSITION.search(message)
    if match is None:
        return 0, len(source)
    line = int(match.group(1)) - 1
    column = int(match.group(2)) - 1
    try:
        start = _position_to_index(source, {"line": line, "character": column})
    except ValueError:
        return 0, len(source)
    return start, min(len(source), start + 1)


def _parser_error(source: str, error: SyntaxError | ValueError) -> dict[str, object]:
    diagnostic = getattr(error, "diagnostic", None)
    start_byte = getattr(diagnostic, "start_index", None)
    end_byte = getattr(diagnostic, "end_index", None)
    if type(start_byte) is int and type(end_byte) is int:
        try:
            start = _byte_to_index(source, start_byte)
            end = _byte_to_index(source, end_byte)
        except (UnicodeDecodeError, ValueError):
            start, end = _legacy_error_range(source, str(error))
    else:
        start, end = _legacy_error_range(source, str(error))
    code = getattr(diagnostic, "code", _PARSE_FALLBACK_CODE)
    message = getattr(diagnostic, "message", str(error))
    return {
        "range": _range(source, start, end),
        "message": message if type(message) is str and message else str(error),
        "severity": "error",
        "code": code if type(code) is str and code else _PARSE_FALLBACK_CODE,
    }


def _parse(source: str) -> tuple[object | None, dict[str, object] | None]:
    try:
        return parse_template(source), None
    except (SyntaxError, ValueError) as error:
        return None, _parser_error(source, error)


def _validated_regions(payload_json: str) -> list[dict[str, object]]:
    payload = json.loads(payload_json)
    if type(payload) is not list:
        msg = "analysis regions must be a list"
        raise ValueError(msg)
    regions: list[dict[str, object]] = []
    for value in payload:
        region = _require_dict(value, frozenset({"id", "source"}), "analysis region")
        if type(region["id"]) is not str or not region["id"] or type(region["source"]) is not str:
            msg = "analysis region id and source must be strings"
            raise ValueError(msg)
        regions.append(region)
    return regions


def analyze_regions_json(payload_json: str) -> str:
    """Return parser diagnostics for exact template-region inputs."""
    diagnostics: list[dict[str, object]] = []
    for region in _validated_regions(payload_json):
        template, finding = _parse(region["source"])
        if finding is not None:
            diagnostics.append({"regionId": region["id"], **finding})
        elif template is not None and _components_by_name is not None:
            for use in unknown_component_uses(template, _components_by_name):
                start = _byte_to_index(region["source"], use.start_index)
                end = _byte_to_index(region["source"], use.end_index)
                diagnostics.append(
                    {
                        "regionId": region["id"],
                        "range": _range(region["source"], start, end),
                        "message": f"Component <{use.tag}> is not registered.",
                        "severity": "error",
                        "code": _UNKNOWN_COMPONENT_CODE,
                    }
                )
    return json.dumps({"diagnostics": diagnostics}, separators=(",", ":"))


def _tag_help(label: str) -> tuple[str, str, str]:
    return _TAG_HELP.get(
        label,
        (
            "Citry structural tag",
            "This tag controls how Citry parses or renders its template body.",
            "https://citry.dev/reference/builtins/",
        ),
    )


def _component_for_label(label: str) -> dict[str, object] | None:
    if _components_by_name is None:
        return None
    records = _components_by_name.get(_component_identity(label), ())
    if not records:
        return None
    first = records[0]
    return first if all(record == first for record in records[1:]) else None


def _component_help(component: dict[str, object]) -> tuple[str, str, str]:
    detail = component["importPath"] or component["className"] or "Registered Citry component"
    paragraphs = [component["description"] or "Registered Citry component."]
    kwargs = component["kwargs"]
    slots = component["slots"]
    if kwargs:
        paragraphs.append("Inputs: " + ", ".join(field["name"] for field in kwargs) + ".")
    if slots:
        paragraphs.append("Slots: " + ", ".join(field["name"] for field in slots) + ".")
    return str(detail), " ".join(paragraphs), _COMPONENT_DOCUMENTATION_URL


def _component_completion_items(prefix: str) -> list[tuple[str, dict[str, str]]]:
    matches: list[tuple[str, str, dict[str, str]]] = []
    seen: set[str] = set()
    for component in _components:
        variants: list[tuple[str, bool, int]] = []
        class_name = component["className"]
        if type(class_name) is str and _component_for_label(class_name) == component:
            variants.append((f"c-{class_name}", True, 1))
        variants.extend(
            (f"c-{name}", False, 0 if index == 0 else index + 1)
            for index, name in enumerate((component["name"], *component["aliases"]))
        )
        for label, is_class_name, variant_index in variants:
            if _component_for_label(label) != component:
                continue
            if label in seen:
                continue
            seen.add(label)
            match = component_name_match(
                prefix,
                label,
                is_class_name=is_class_name,
                variant_index=variant_index,
            )
            if match is None:
                continue
            detail, documentation, documentation_url = _component_help(component)
            matches.append(
                (
                    match.sort_text,
                    label,
                    {
                        "label": label,
                        "detail": detail,
                        "documentation": documentation,
                        "documentationUrl": documentation_url,
                    },
                )
            )
    return [(label, item) for _, label, item in sorted(matches)]


def _tag_can_start_at(source: str, candidate: int) -> bool:
    """Reject tag-shaped text inside an existing tag value or comment."""
    index = 0
    tag_open = False
    quote: str | None = None
    while index < candidate:
        if source.startswith("<!--", index):
            closing = source.find("-->", index + 4)
            if closing < 0 or closing >= candidate:
                return False
            index = closing + 3
            continue
        if source.startswith("{#", index):
            closing = source.find("#}", index + 2)
            if closing < 0 or closing >= candidate:
                return False
            index = closing + 2
            continue
        char = source[index]
        if quote is not None:
            if char == quote:
                quote = None
            index += 1
            continue
        if tag_open and char in {'"', "'"}:
            quote = char
        elif tag_open and char == ">":
            tag_open = False
        elif char == "<":
            tag_open = True
        index += 1
    return not tag_open and quote is None


def complete_region_json(source: str, position_json: str) -> str:
    """Complete parser-owned structural tags at one template position."""
    position = json.loads(position_json)
    cursor = _position_to_index(source, position)
    match = _TAG_PREFIX.search(source[:cursor])
    if match is None or not _tag_can_start_at(source, match.start()):
        return "null"
    prefix = match.group(1).lower()
    ranked_items: list[tuple[str, dict[str, str]]] = []
    for label in sorted(RESERVED_TAG_NAMES):
        if not label.startswith(prefix):
            continue
        detail, documentation, documentation_url = _tag_help(label)
        ranked_items.append(
            (
                label,
                {
                    "label": label,
                    "detail": detail,
                    "documentation": documentation,
                    "documentationUrl": documentation_url,
                },
            )
        )
    ranked_items.extend(_component_completion_items(prefix))
    items = [item for _, item in ranked_items]
    return json.dumps(
        {
            "range": _range(source, match.start(1), cursor),
            "items": items,
        },
        separators=(",", ":"),
    )


def hover_region_json(source: str, position_json: str) -> str:
    """Return parser-proven help for one structural tag token."""
    position = json.loads(position_json)
    cursor = _position_to_index(source, position)
    parser_index = len(source[:cursor].encode())
    template, _ = _parse(source)
    if template is None:
        return "null"
    for use in template_tag_uses(template):
        label = use.tag.lower()
        if not use.start_index <= parser_index < use.end_index:
            continue
        component = _component_for_label(label)
        if label in RESERVED_TAG_NAMES:
            detail, documentation, documentation_url = _tag_help(label)
        elif component is not None:
            detail, documentation, documentation_url = _component_help(component)
        else:
            continue
        start = _byte_to_index(source, use.start_index)
        end = _byte_to_index(source, use.end_index)
        return json.dumps(
            {
                "range": _range(source, start, end),
                "label": label,
                "detail": detail,
                "documentation": documentation,
                "documentationUrl": documentation_url,
            },
            separators=(",", ":"),
        )
    return "null"


__all__ = ["analyze_regions_json", "complete_region_json", "hover_region_json", "update_catalog_json"]
