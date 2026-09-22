"""Immutable detached render artifacts and their strict JSON codec."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

from .errors import CacheArtifactError, _CacheArtifactCompatibilityError, _CacheArtifactOversizedError
from .limits import (
    _MAX_ARTIFACT_BYTES,
    _MAX_ARTIFACT_DEPTH,
    _MAX_ARTIFACT_RECORDS,
    _InvalidArtifactTextError,
    _validate_artifact_text_size,
)

_ARTIFACT_VERSION = 1
_CITRY_COMPATIBILITY_VERSION = 1
_CREATED_BY = "citry-python"
_ROOT_MARKER_RE = re.compile(r'([^\s=/><]+)(?:="([^"<>]*)")?\Z')


@dataclass(frozen=True, slots=True)
class FrozenJsonObject:
    """An ordered immutable JSON object used by extension payloads."""

    items: tuple[tuple[str, FrozenJsonValue], ...]


FrozenJsonValue: TypeAlias = "None | bool | int | float | str | tuple[FrozenJsonValue, ...] | FrozenJsonObject"


@dataclass(frozen=True, slots=True)
class ArtifactFramePart:
    frame: int


@dataclass(frozen=True, slots=True)
class ArtifactPlaceholderPart:
    key: str


@dataclass(frozen=True, slots=True)
class ArtifactSourceTextPart:
    source: str
    span: tuple[int, int]
    text: str


@dataclass(frozen=True, slots=True)
class ArtifactVerbatimHtmlPart:
    source: str
    span: tuple[int, int]
    html: str


@dataclass(frozen=True, slots=True)
class ArtifactTextValuePart:
    source: str
    span: tuple[int, int]
    value: FrozenJsonValue
    browser_binding: ArtifactBrowserBinding | None = None


@dataclass(frozen=True, slots=True)
class ArtifactTrustedHtmlPart:
    html: str


@dataclass(frozen=True, slots=True)
class ArtifactAttribute:
    name: str
    origin: str
    span: tuple[int, int]
    value: FrozenJsonValue


@dataclass(frozen=True, slots=True)
class ArtifactBrowserBinding:
    helper: str
    operand: FrozenJsonValue
    target: str
    name: str | None
    values_expression: str | None


@dataclass(frozen=True, slots=True)
class ArtifactElementOpenPart:
    source: str
    span: tuple[int, int]
    tag: str
    attrs: tuple[ArtifactAttribute, ...]
    is_void: bool
    is_self_closing: bool
    element_metadata: FrozenJsonValue
    event_bindings: tuple[FrozenJsonObject, ...]
    control_bindings: tuple[FrozenJsonObject, ...] = ()
    browser_bindings: tuple[ArtifactBrowserBinding, ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactElementClosePart:
    source: str
    span: tuple[int, int]
    tag: str


@dataclass(frozen=True, slots=True)
class ArtifactDynamicElementOpenPart:
    tag: str
    attrs: FrozenJsonObject
    is_void: bool
    authored_attrs: tuple[ArtifactAttribute, ...]
    key: str | None
    authored_source: str | None
    event_bindings: tuple[FrozenJsonObject, ...] = ()
    control_bindings: tuple[FrozenJsonObject, ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactDynamicElementClosePart:
    tag: str


@dataclass(frozen=True, slots=True)
class ArtifactStaticRunOpening:
    start_at: int
    insert_at: int
    end_at: int
    relative_depth: int
    attr_identities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtifactStaticRunStructure:
    openings: tuple[ArtifactStaticRunOpening, ...]
    final_depth_delta: int
    tag_transitions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactStaticRunPart:
    html: str
    structure: ArtifactStaticRunStructure | None


@dataclass(frozen=True, slots=True)
class ArtifactLeafProgramPart:
    template: str
    element_bindings: tuple[FrozenJsonObject, ...]
    browser_requirements: tuple[str, ...]
    safe_body: bool
    prepared_data: FrozenJsonObject
    vue_errors: tuple[str, ...]
    typed_parts: tuple[ArtifactPart, ...]
    static_parts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtifactDirectSlotPart:
    frame: int
    execution: int
    parent_execution: int | None
    external_parent_execution: bool
    lexical_instance: int | None
    lexical_parent_depth: int | None
    receiver_instance: int | None
    receiver_parent_depth: int | None
    kind: str
    public_name: str
    fill_source: str
    source: str
    span: tuple[int, int]
    origin: str | None


@dataclass(frozen=True, slots=True)
class ArtifactDirectCallRunPart:
    frame: int
    child_class_id: str
    source: str
    span: tuple[int, int]


@dataclass(frozen=True, slots=True)
class ArtifactDirectPythonComponentPart:
    frame: int
    local_ordinal: int


ArtifactPart: TypeAlias = (
    "ArtifactFramePart | ArtifactPlaceholderPart | ArtifactSourceTextPart | ArtifactVerbatimHtmlPart | "
    "ArtifactTextValuePart | ArtifactTrustedHtmlPart | ArtifactElementOpenPart | ArtifactElementClosePart | "
    "ArtifactDynamicElementOpenPart | ArtifactDynamicElementClosePart | ArtifactStaticRunPart | "
    "ArtifactLeafProgramPart | ArtifactDirectSlotPart | ArtifactDirectCallRunPart | "
    "ArtifactDirectPythonComponentPart"
)


@dataclass(frozen=True, slots=True)
class ArtifactFrame:
    """One detached render frame with no original render ID or live context."""

    instance: int | None
    class_id: str | None
    class_name: str | None
    is_component_root: bool
    root_markers: tuple[str, ...]
    parts: tuple[ArtifactPart, ...]
    is_transparent_root: bool = False
    data: FrozenJsonObject = FrozenJsonObject(())
    prepared_call: ArtifactPreparedCall | None = None
    source_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactPreparedCall:
    source: str
    span: tuple[int, int]
    explicit_key: str | None
    origin: str | None
    slot_free_body: bool
    raw_slots_present: bool
    bindings: tuple[ArtifactPreparedBinding, ...]


@dataclass(frozen=True, slots=True)
class ArtifactPreparedBinding:
    kind: str
    key: str
    value: str
    source: str
    span: tuple[int, int]
    provenance: Literal["authored", "runtime-spread"] = "authored"


@dataclass(frozen=True, slots=True)
class ArtifactExtension:
    """One payload extension's versioned immutable contribution."""

    name: str
    version: int
    payload: FrozenJsonObject


@dataclass(frozen=True, slots=True)
class CachedRenderArtifact:
    """A complete detached render contribution suitable for safe replay."""

    root_frame: int
    frames: tuple[ArtifactFrame, ...]
    extensions: tuple[ArtifactExtension, ...]


@dataclass(slots=True)
class _ShapeState:
    records: int = 0


def _encode_artifact(artifact: CachedRenderArtifact, *, max_entry_bytes: int | None = None) -> str:
    """Encode one validated artifact as deterministic compact UTF-8 JSON."""
    if type(artifact) is not CachedRenderArtifact:
        msg = f"Expected CachedRenderArtifact, got {type(artifact).__name__}."
        raise TypeError(msg)
    _validate_typed_artifact(artifact)
    wire = _artifact_to_wire(artifact)
    _validate_json_shape(wire)
    try:
        encoded = json.dumps(
            wire,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError, RecursionError) as err:
        raise CacheArtifactError(f"Could not encode cached render artifact: {err}") from err
    try:
        size = _validate_artifact_text_size(encoded)
    except _InvalidArtifactTextError as err:
        raise CacheArtifactError(str(err)) from err
    except ValueError as err:
        raise _CacheArtifactOversizedError(size=None, limit=_MAX_ARTIFACT_BYTES) from err
    if max_entry_bytes is not None:
        if type(max_entry_bytes) is not int or max_entry_bytes <= 0:
            msg = f"max_entry_bytes must be None or an exact positive int; got {max_entry_bytes!r}."
            raise ValueError(msg)
        if size > max_entry_bytes:
            raise _CacheArtifactOversizedError(size=size, limit=max_entry_bytes)
    return encoded


def _decode_artifact(value: str) -> CachedRenderArtifact:
    """Decode and fully validate an artifact without mutating render state."""
    artifact, _size = _decode_artifact_with_size(value)
    return artifact


def _decode_artifact_with_size(value: str) -> tuple[CachedRenderArtifact, int]:
    """Decode an artifact and return its validated UTF-8 byte size."""
    if type(value) is not str:
        raise CacheArtifactError(f"Cached render artifacts must be exact strings; got {type(value).__name__}.")
    try:
        size = _validate_artifact_text_size(value)
    except _InvalidArtifactTextError as err:
        raise CacheArtifactError(str(err)) from err
    except ValueError as err:
        raise _CacheArtifactOversizedError(size=None, limit=_MAX_ARTIFACT_BYTES) from err
    try:
        wire = json.loads(
            value,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except CacheArtifactError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as err:
        raise CacheArtifactError(f"Cached render artifact is not valid JSON: {err}") from err
    _validate_json_shape(wire)
    artifact = _artifact_from_wire(wire)
    _validate_typed_artifact(artifact)
    return artifact, size


def _validate_typed_artifact(artifact: CachedRenderArtifact) -> None:
    """Validate the immutable in-memory form as strictly as decoded JSON."""
    if type(artifact) is not CachedRenderArtifact:
        raise CacheArtifactError(f"Expected CachedRenderArtifact, got {type(artifact).__name__}.")
    if type(artifact.root_frame) is not int:
        raise CacheArtifactError("artifact.root_frame must be an exact integer.")
    if type(artifact.frames) is not tuple:
        raise CacheArtifactError("artifact.frames must be an immutable tuple.")
    if type(artifact.extensions) is not tuple:
        raise CacheArtifactError("artifact.extensions must be an immutable tuple.")
    extension_names: set[str] = set()
    for index, extension in enumerate(artifact.extensions):
        path = f"artifact.extensions[{index}]"
        if type(extension) is not ArtifactExtension:
            raise CacheArtifactError(f"{path} is not an ArtifactExtension.")
        _require_nonempty_string(extension.name, f"{path}.name")
        _require_positive_int(extension.version, f"{path}.version")
        if extension.name in extension_names:
            raise CacheArtifactError("Cached render artifact contains a duplicate extension payload name.")
        extension_names.add(extension.name)
        _validate_frozen_json(extension.payload, f"{path}.payload")
    for frame_index, frame in enumerate(artifact.frames):
        path = f"artifact.frames[{frame_index}]"
        if type(frame) is not ArtifactFrame:
            raise CacheArtifactError(f"{path} is not an ArtifactFrame.")
        if frame.instance is not None:
            _require_nonnegative_int(frame.instance, f"{path}.instance")
        _require_optional_nonempty_string(frame.class_id, f"{path}.class_id")
        _require_optional_nonempty_string(frame.class_name, f"{path}.class_name")
        if type(frame.is_component_root) is not bool:
            raise CacheArtifactError(f"{path}.component_root must be a bool.")
        if type(frame.is_transparent_root) is not bool:
            raise CacheArtifactError(f"{path}.transparent_root must be a bool.")
        if frame.is_component_root and frame.is_transparent_root:
            raise CacheArtifactError(f"{path} cannot be both a nontransparent component root and a transparent root.")
        if frame.instance is None:
            if (
                frame.class_id is not None
                or frame.class_name is not None
                or frame.is_component_root
                or frame.is_transparent_root
            ):
                raise CacheArtifactError(f"{path} has component identity without an instance reference.")
        elif frame.class_id is None or frame.class_name is None:
            raise CacheArtifactError(f"{path} instance requires class_id and class_name.")
        if type(frame.root_markers) is not tuple:
            raise CacheArtifactError(f"{path}.root_markers must be an immutable tuple.")
        if len(frame.root_markers) != len(set(frame.root_markers)):
            raise CacheArtifactError(f"{path}.root_markers contains a duplicate marker.")
        for marker_index, marker in enumerate(frame.root_markers):
            _validate_root_marker(
                marker,
                f"{path}.root_markers[{marker_index}]",
            )
        if type(frame.parts) is not tuple:
            raise CacheArtifactError(f"{path}.parts must be an immutable tuple.")
        _validate_frozen_json(frame.data, f"{path}.data")
        if frame.prepared_call is not None:
            _prepared_call_from_wire(_prepared_call_to_wire(frame.prepared_call), f"{path}.prepared_call")
        _require_optional_nonempty_string(frame.source_fingerprint, f"{path}.source_fingerprint")
    _validate_frame_tree(artifact)


def _validate_root_marker(marker: object, path: str) -> None:
    marker = _require_nonempty_string(marker, path)
    match = _ROOT_MARKER_RE.fullmatch(marker)
    if match is None or "{#" in marker:
        raise CacheArtifactError(f"{path} is not one complete safe HTML attribute marker.")
    name = match.group(1).lower()
    if name == "data-cid" or name.startswith("data-cid-"):
        raise CacheArtifactError(f"{path} contains reserved render identity marker {name!r}.")
    if name == "data-citry-key":
        raise CacheArtifactError(f"{path} contains a legacy component morph key marker.")


def _validate_frozen_json(root: object, path: str) -> None:
    """Validate immutable strict JSON without collapsing duplicate object keys."""
    pending: list[tuple[object, int, str]] = [(root, 0, path)]
    records = 0
    while pending:
        value, depth, value_path = pending.pop()
        if depth > _MAX_ARTIFACT_DEPTH:
            raise CacheArtifactError(
                f"Cached render artifact exceeds the {_MAX_ARTIFACT_DEPTH} level structural depth limit at"
                f" {value_path}."
            )
        if type(value) is FrozenJsonObject:
            records += 1
            items = value.items
            if type(items) is not tuple:
                raise CacheArtifactError(f"{value_path}.items must be an immutable tuple.")
            keys: list[str] = []
            for index, pair in enumerate(items):
                if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
                    raise CacheArtifactError(f"{value_path}.items[{index}] is not a string-keyed pair.")
                _validate_utf8_text(pair[0], f"{value_path}.items[{index}][0]")
                keys.append(pair[0])
                pending.append((pair[1], depth + 1, f"{value_path}.{pair[0]}"))
            if keys != sorted(keys) or len(keys) != len(set(keys)):
                raise CacheArtifactError(f"{value_path} keys must be unique and sorted.")
        elif type(value) is tuple:
            records += 1
            pending.extend((item, depth + 1, f"{value_path}[{index}]") for index, item in enumerate(value))
        elif type(value) is float:
            if not math.isfinite(value):
                raise CacheArtifactError(f"{value_path} contains a non-finite number.")
        elif type(value) is str:
            _validate_utf8_text(value, value_path)
        elif value is not None and type(value) not in (bool, int, str):
            raise CacheArtifactError(f"{value_path} contains unsupported frozen JSON value {type(value).__name__}.")
        if records > _MAX_ARTIFACT_RECORDS:
            raise CacheArtifactError(
                f"Cached render artifact exceeds the {_MAX_ARTIFACT_RECORDS:,} structural record limit."
            )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CacheArtifactError(f"Cached render artifact contains duplicate JSON field {key!r}.")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise CacheArtifactError(f"Cached render artifact requires finite JSON numbers; got {value}.")


def _validate_json_shape(root: object, path: str = "artifact") -> None:
    """Enforce structural limits iteratively before typed conversion."""
    state = _ShapeState()
    pending: list[tuple[object, int, str]] = [(root, 0, path)]
    while pending:
        value, depth, path = pending.pop()
        if depth > _MAX_ARTIFACT_DEPTH:
            raise CacheArtifactError(
                f"Cached render artifact exceeds the {_MAX_ARTIFACT_DEPTH} level structural depth limit at {path}."
            )
        if type(value) in (list, dict):
            state.records += 1
            if state.records > _MAX_ARTIFACT_RECORDS:
                raise CacheArtifactError(
                    f"Cached render artifact exceeds the {_MAX_ARTIFACT_RECORDS:,} structural record limit."
                )
        if type(value) is list:
            pending.extend((item, depth + 1, f"{path}[{index}]") for index, item in enumerate(value))
        elif type(value) is dict:
            for key, item in cast("dict[object, object]", value).items():
                if type(key) is not str:
                    raise CacheArtifactError(f"{path} contains a non-string object key.")
                _validate_utf8_text(key, f"{path} object key")
                pending.append((item, depth + 1, f"{path}.{key}"))
        elif type(value) is float and not math.isfinite(value):
            raise CacheArtifactError(f"Cached render artifact contains a non-finite number at {path}.")
        elif type(value) is str:
            _validate_utf8_text(value, path)
        elif value is not None and type(value) not in (bool, int, float, str):
            raise CacheArtifactError(
                f"Cached render artifact contains unsupported JSON value {type(value).__name__} at {path}."
            )


def _artifact_to_wire(artifact: CachedRenderArtifact) -> dict[str, object]:
    return {
        "artifact_version": _ARTIFACT_VERSION,
        "citry_version": _CITRY_COMPATIBILITY_VERSION,
        "created_by": _CREATED_BY,
        "root_frame": artifact.root_frame,
        "frames": [_frame_to_wire(frame) for frame in artifact.frames],
        "extensions": [
            {
                "name": extension.name,
                "version": extension.version,
                "payload": _thaw_json(extension.payload),
            }
            for extension in artifact.extensions
        ],
    }


def _frame_to_wire(frame: ArtifactFrame) -> dict[str, object]:
    return {
        "instance": frame.instance,
        "class_id": frame.class_id,
        "class_name": frame.class_name,
        "component_root": frame.is_component_root,
        "transparent_root": frame.is_transparent_root,
        "root_markers": list(frame.root_markers),
        "data": _thaw_json(frame.data),
        "prepared_call": None if frame.prepared_call is None else _prepared_call_to_wire(frame.prepared_call),
        "source_fingerprint": frame.source_fingerprint,
        "parts": [_part_to_wire(part) for part in frame.parts],
    }


def _prepared_call_to_wire(value: ArtifactPreparedCall) -> list[object]:
    return [
        value.source,
        list(value.span),
        value.explicit_key,
        value.origin,
        value.slot_free_body,
        value.raw_slots_present,
        [[item.kind, item.key, item.value, item.source, list(item.span), item.provenance] for item in value.bindings],
    ]


def _browser_binding_to_wire(value: ArtifactBrowserBinding) -> list[object]:
    return [value.helper, _thaw_json(value.operand), value.target, value.name, value.values_expression]


def _browser_binding_from_wire(value: object, path: str) -> ArtifactBrowserBinding:
    item = _require_list(value, path)
    if len(item) != 5:
        raise CacheArtifactError(f"{path} must contain exactly five fields.")
    target = _require_nonempty_string(item[2], f"{path}[2]")
    name = None if item[3] is None else _require_nonempty_string(item[3], f"{path}[3]")
    if target not in {"text", "attribute"} or (target == "text") != (name is None):
        raise CacheArtifactError(f"{path} has an invalid target.")
    return ArtifactBrowserBinding(
        _require_nonempty_string(item[0], f"{path}[0]"),
        _freeze_json_value(item[1], f"{path}[1]"),
        target,
        name,
        None if item[4] is None else _require_nonempty_string(item[4], f"{path}[4]"),
    )


def _part_to_wire(part: ArtifactPart) -> list[object]:
    if type(part) is ArtifactFramePart:
        return ["frame", part.frame]
    if type(part) is ArtifactPlaceholderPart:
        return ["placeholder", part.key]
    if type(part) is ArtifactSourceTextPart:
        return ["source_text", part.source, list(part.span), part.text]
    if type(part) is ArtifactVerbatimHtmlPart:
        return ["verbatim_html", part.source, list(part.span), part.html]
    if type(part) is ArtifactTextValuePart:
        return [
            "text_value",
            part.source,
            list(part.span),
            _thaw_json(part.value),
            None if part.browser_binding is None else _browser_binding_to_wire(part.browser_binding),
        ]
    if type(part) is ArtifactTrustedHtmlPart:
        return ["trusted_html", part.html]
    if type(part) is ArtifactElementOpenPart:
        return [
            "element_open",
            part.source,
            list(part.span),
            part.tag,
            [[item.name, item.origin, list(item.span), _thaw_json(item.value)] for item in part.attrs],
            part.is_void,
            part.is_self_closing,
            _thaw_json(part.element_metadata),
            [_thaw_json(item) for item in part.event_bindings],
            [_thaw_json(item) for item in part.control_bindings],
            [_browser_binding_to_wire(item) for item in part.browser_bindings],
        ]
    if type(part) is ArtifactElementClosePart:
        return ["element_close", part.source, list(part.span), part.tag]
    if type(part) is ArtifactDynamicElementOpenPart:
        return [
            "dynamic_open",
            part.tag,
            _thaw_json(part.attrs),
            part.is_void,
            [[item.name, item.origin, list(item.span), _thaw_json(item.value)] for item in part.authored_attrs],
            part.key,
            part.authored_source,
            [_thaw_json(item) for item in part.event_bindings],
            [_thaw_json(item) for item in part.control_bindings],
        ]
    if type(part) is ArtifactDynamicElementClosePart:
        return ["dynamic_close", part.tag]
    if type(part) is ArtifactStaticRunPart:
        structure = part.structure
        return [
            "static_run",
            part.html,
            None
            if structure is None
            else [
                [
                    [item.start_at, item.insert_at, item.end_at, item.relative_depth, list(item.attr_identities)]
                    for item in structure.openings
                ],
                structure.final_depth_delta,
                [list(item) for item in structure.tag_transitions],
            ],
        ]
    if type(part) is ArtifactLeafProgramPart:
        return [
            "leaf_program",
            part.template,
            [_thaw_json(item) for item in part.element_bindings],
            list(part.browser_requirements),
            part.safe_body,
            _thaw_json(part.prepared_data),
            list(part.vue_errors),
            [_part_to_wire(item) for item in part.typed_parts],
            list(part.static_parts),
        ]
    if type(part) is ArtifactDirectSlotPart:
        return [
            "direct_slot",
            part.frame,
            part.execution,
            part.parent_execution,
            part.external_parent_execution,
            part.lexical_instance,
            part.lexical_parent_depth,
            part.receiver_instance,
            part.receiver_parent_depth,
            part.kind,
            part.public_name,
            part.fill_source,
            part.source,
            list(part.span),
            part.origin,
        ]
    if type(part) is ArtifactDirectCallRunPart:
        return ["direct_call_run", part.frame, part.child_class_id, part.source, list(part.span)]
    if type(part) is ArtifactDirectPythonComponentPart:
        return ["direct_python_component", part.frame, part.local_ordinal]
    msg = f"Unsupported artifact part {type(part).__name__}."
    raise TypeError(msg)


def _artifact_from_wire(value: object) -> CachedRenderArtifact:
    root = _require_object(value, "artifact")
    _require_fields(
        root,
        {
            "artifact_version",
            "citry_version",
            "created_by",
            "root_frame",
            "frames",
            "extensions",
        },
        "artifact",
    )
    for version_value, path, expected in (
        (root["artifact_version"], "artifact.artifact_version", _ARTIFACT_VERSION),
        (root["citry_version"], "artifact.citry_version", _CITRY_COMPATIBILITY_VERSION),
    ):
        try:
            _require_exact_int(version_value, path, expected=expected)
        except CacheArtifactError as error:
            raise _CacheArtifactCompatibilityError(str(error)) from error
    if root["created_by"] != _CREATED_BY:
        raise CacheArtifactError(f"Invalid artifact.created_by value {root['created_by']!r}.")
    root_frame = _require_nonnegative_int(root["root_frame"], "artifact.root_frame")
    frame_values = _require_list(root["frames"], "artifact.frames")
    frames = tuple(_frame_from_wire(item, index) for index, item in enumerate(frame_values))
    extension_values = _require_list(root["extensions"], "artifact.extensions")
    extensions = tuple(_extension_from_wire(item, index) for index, item in enumerate(extension_values))
    names = [extension.name for extension in extensions]
    if len(names) != len(set(names)):
        raise CacheArtifactError("Cached render artifact contains a duplicate extension payload name.")
    return CachedRenderArtifact(
        root_frame=root_frame,
        frames=frames,
        extensions=extensions,
    )


def _frame_from_wire(value: object, index: int) -> ArtifactFrame:
    path = f"artifact.frames[{index}]"
    frame = _require_object(value, path)
    _require_fields(
        frame,
        {
            "instance",
            "class_id",
            "class_name",
            "component_root",
            "transparent_root",
            "root_markers",
            "data",
            "prepared_call",
            "source_fingerprint",
            "parts",
        },
        path,
    )
    instance_value = frame["instance"]
    instance = None if instance_value is None else _require_nonnegative_int(instance_value, f"{path}.instance")
    class_id = _require_optional_nonempty_string(frame["class_id"], f"{path}.class_id")
    class_name = _require_optional_nonempty_string(frame["class_name"], f"{path}.class_name")
    component_root = frame["component_root"]
    if type(component_root) is not bool:
        raise CacheArtifactError(f"{path}.component_root must be a bool.")
    transparent_root = frame["transparent_root"]
    if type(transparent_root) is not bool:
        raise CacheArtifactError(f"{path}.transparent_root must be a bool.")
    if component_root and transparent_root:
        raise CacheArtifactError(f"{path} cannot be both a nontransparent component root and a transparent root.")
    if instance is None:
        if class_id is not None or class_name is not None or component_root or transparent_root:
            raise CacheArtifactError(f"{path} has component identity without an instance reference.")
    elif class_id is None or class_name is None:
        raise CacheArtifactError(f"{path} instance requires class_id and class_name.")
    markers = _require_list(frame["root_markers"], f"{path}.root_markers")
    root_markers = tuple(
        _require_string(marker, f"{path}.root_markers[{marker_index}]") for marker_index, marker in enumerate(markers)
    )
    parts = tuple(
        _part_from_wire(part, f"{path}.parts[{part_index}]")
        for part_index, part in enumerate(_require_list(frame["parts"], f"{path}.parts"))
    )
    return ArtifactFrame(
        instance=instance,
        class_id=class_id,
        class_name=class_name,
        is_component_root=component_root,
        is_transparent_root=transparent_root,
        root_markers=root_markers,
        parts=parts,
        data=_freeze_object(frame["data"], f"{path}.data"),
        prepared_call=(
            None
            if frame["prepared_call"] is None
            else _prepared_call_from_wire(frame["prepared_call"], f"{path}.prepared_call")
        ),
        source_fingerprint=_require_optional_nonempty_string(
            frame["source_fingerprint"], f"{path}.source_fingerprint"
        ),
    )


def _prepared_call_from_wire(value: object, path: str) -> ArtifactPreparedCall:
    item = _require_list(value, path)
    if len(item) != 7:
        raise CacheArtifactError(f"{path} must contain exactly seven fields.")
    source = _require_string(item[0], f"{path}[0]")
    bindings: list[ArtifactPreparedBinding] = []
    for index, raw in enumerate(_require_list(item[6], f"{path}[6]")):
        binding = _require_list(raw, f"{path}[6][{index}]")
        if len(binding) not in {5, 6}:
            raise CacheArtifactError(f"{path}[6][{index}] must contain exactly five or six fields.")
        kind = _require_nonempty_string(binding[0], f"{path}[6][{index}][0]")
        if kind not in {
            "prop",
            "props-object",
            "events-object",
            "event",
            "ref-static",
            "ref-expression",
            "citry-handler",
        }:
            raise CacheArtifactError(f"{path}[6][{index}][0] has an unknown binding kind.")
        binding_source = _require_string(binding[3], f"{path}[6][{index}][3]")
        provenance = (
            "authored"
            if len(binding) == 5
            else _require_binding_provenance(
                _require_nonempty_string(binding[5], f"{path}[6][{index}][5]"), f"{path}[6][{index}][5]"
            )
        )
        if provenance == "runtime-spread" and kind != "citry-handler":
            raise CacheArtifactError(f"{path}[6][{index}] gives runtime provenance to a non-handler binding.")
        bindings.append(
            ArtifactPreparedBinding(
                kind,
                _require_nonempty_string(binding[1], f"{path}[6][{index}][1]"),
                _require_string(binding[2], f"{path}[6][{index}][2]"),
                binding_source,
                _require_source_span(binding[4], binding_source, f"{path}[6][{index}][4]"),
                provenance,
            )
        )
    return ArtifactPreparedCall(
        source,
        _require_source_span(item[1], source, f"{path}[1]"),
        None if item[2] is None else _require_string(item[2], f"{path}[2]"),
        _require_optional_nonempty_string(item[3], f"{path}[3]"),
        _require_bool(item[4], f"{path}[4]"),
        _require_bool(item[5], f"{path}[5]"),
        tuple(bindings),
    )


def _part_from_wire(value: object, path: str) -> ArtifactPart:
    part = _require_list(value, path)
    if not part or type(part[0]) is not str:
        raise CacheArtifactError(f"{path} must start with a string part tag.")
    tag = part[0]
    if tag == "frame" and len(part) == 2:
        return ArtifactFramePart(_require_nonnegative_int(part[1], f"{path}[1]"))
    if tag == "placeholder" and len(part) == 2:
        return ArtifactPlaceholderPart(_require_nonempty_string(part[1], f"{path}[1]"))
    if tag == "source_text" and len(part) == 4:
        source = _require_string(part[1], f"{path}[1]")
        return ArtifactSourceTextPart(
            source,
            _require_source_span(part[2], source, f"{path}[2]"),
            _require_string(part[3], f"{path}[3]"),
        )
    if tag == "verbatim_html" and len(part) == 4:
        source = _require_string(part[1], f"{path}[1]")
        return ArtifactVerbatimHtmlPart(
            source,
            _require_source_span(part[2], source, f"{path}[2]"),
            _require_string(part[3], f"{path}[3]"),
        )
    if tag == "text_value" and len(part) == 5:
        source = _require_string(part[1], f"{path}[1]")
        return ArtifactTextValuePart(
            source,
            _require_source_span(part[2], source, f"{path}[2]"),
            _freeze_json_value(part[3], f"{path}[3]"),
            None if part[4] is None else _browser_binding_from_wire(part[4], f"{path}[4]"),
        )
    if tag == "trusted_html" and len(part) == 2:
        return ArtifactTrustedHtmlPart(_require_string(part[1], f"{path}[1]"))
    if tag == "element_open" and len(part) == 11:
        source = _require_string(part[1], f"{path}[1]")
        attrs = tuple(
            _attribute_from_wire(item, source, f"{path}[4][{index}]")
            for index, item in enumerate(_require_list(part[4], f"{path}[4]"))
        )
        bindings = tuple(
            _freeze_object(item, f"{path}[8][{index}]")
            for index, item in enumerate(_require_list(part[8], f"{path}[8]"))
        )
        controls = tuple(
            _freeze_object(item, f"{path}[9][{index}]")
            for index, item in enumerate(_require_list(part[9], f"{path}[9]"))
        )
        browser_bindings = tuple(
            _browser_binding_from_wire(item, f"{path}[10][{index}]")
            for index, item in enumerate(_require_list(part[10], f"{path}[10]"))
        )
        return ArtifactElementOpenPart(
            source,
            _require_source_span(part[2], source, f"{path}[2]"),
            _require_nonempty_string(part[3], f"{path}[3]"),
            attrs,
            _require_bool(part[5], f"{path}[5]"),
            _require_bool(part[6], f"{path}[6]"),
            _freeze_json_value(part[7], f"{path}[7]"),
            bindings,
            controls,
            browser_bindings,
        )
    if tag == "element_close" and len(part) == 4:
        source = _require_string(part[1], f"{path}[1]")
        return ArtifactElementClosePart(
            source,
            _require_source_span(part[2], source, f"{path}[2]"),
            _require_nonempty_string(part[3], f"{path}[3]"),
        )
    if tag == "dynamic_open" and len(part) in {7, 9}:
        authored_source = None if part[6] is None else _require_string(part[6], f"{path}[6]")
        authored_attrs = tuple(
            _attribute_from_wire(item, authored_source or "", f"{path}[4][{index}]")
            for index, item in enumerate(_require_list(part[4], f"{path}[4]"))
        )
        if bool(authored_attrs) is (authored_source is None):
            raise CacheArtifactError(f"{path} has inconsistent authored dynamic element source.")
        if any(item.origin != "source" for item in authored_attrs):
            raise CacheArtifactError(f"{path}[4] contains a non-source dynamic element attribute.")
        return ArtifactDynamicElementOpenPart(
            _require_nonempty_string(part[1], f"{path}[1]"),
            _freeze_object(part[2], f"{path}[2]"),
            _require_bool(part[3], f"{path}[3]"),
            authored_attrs,
            None if part[5] is None else _require_string(part[5], f"{path}[5]"),
            authored_source,
            ()
            if len(part) == 7
            else tuple(_freeze_object(item, f"{path}[7]") for item in _require_list(part[7], f"{path}[7]")),
            ()
            if len(part) == 7
            else tuple(_freeze_object(item, f"{path}[8]") for item in _require_list(part[8], f"{path}[8]")),
        )
    if tag == "dynamic_close" and len(part) == 2:
        return ArtifactDynamicElementClosePart(_require_nonempty_string(part[1], f"{path}[1]"))
    if tag == "static_run" and len(part) == 3:
        html = _require_string(part[1], f"{path}[1]")
        return ArtifactStaticRunPart(html, _static_structure_from_wire(part[2], html, f"{path}[2]"))
    if tag == "leaf_program" and len(part) == 9:
        bindings = tuple(
            _freeze_object(item, f"{path}[2][{index}]")
            for index, item in enumerate(_require_list(part[2], f"{path}[2]"))
        )
        requirements = tuple(
            _require_nonempty_string(item, f"{path}[3][{index}]")
            for index, item in enumerate(_require_list(part[3], f"{path}[3]"))
        )
        if tuple(sorted(set(requirements))) != requirements:
            raise CacheArtifactError(f"{path}[3] must be unique and sorted.")
        errors = tuple(
            _require_nonempty_string(item, f"{path}[6][{index}]")
            for index, item in enumerate(_require_list(part[6], f"{path}[6]"))
        )
        typed = tuple(
            _part_from_wire(item, f"{path}[7][{index}]")
            for index, item in enumerate(_require_list(part[7], f"{path}[7]"))
        )
        if any(
            type(item)
            not in {
                ArtifactSourceTextPart,
                ArtifactVerbatimHtmlPart,
                ArtifactTextValuePart,
                ArtifactTrustedHtmlPart,
                ArtifactElementOpenPart,
                ArtifactElementClosePart,
                ArtifactDynamicElementOpenPart,
                ArtifactDynamicElementClosePart,
                ArtifactStaticRunPart,
            }
            for item in typed
        ):
            raise CacheArtifactError(f"{path}[7] contains a non-leaf typed projection part.")
        static = tuple(
            _require_string(item, f"{path}[8][{index}]")
            for index, item in enumerate(_require_list(part[8], f"{path}[8]"))
        )
        return ArtifactLeafProgramPart(
            _require_string(part[1], f"{path}[1]"),
            bindings,
            requirements,
            _require_bool(part[4], f"{path}[4]"),
            _freeze_object(part[5], f"{path}[5]"),
            errors,
            typed,
            static,
        )
    if tag == "direct_slot" and len(part) == 15:
        parent = part[3]
        source = _require_string(part[12], f"{path}[12]")
        return ArtifactDirectSlotPart(
            _require_nonnegative_int(part[1], f"{path}[1]"),
            _require_nonnegative_int(part[2], f"{path}[2]"),
            None if parent is None else _require_nonnegative_int(parent, f"{path}[3]"),
            _require_bool(part[4], f"{path}[4]"),
            None if part[5] is None else _require_nonnegative_int(part[5], f"{path}[5]"),
            None if part[6] is None else _require_positive_int(part[6], f"{path}[6]"),
            None if part[7] is None else _require_nonnegative_int(part[7], f"{path}[7]"),
            None if part[8] is None else _require_positive_int(part[8], f"{path}[8]"),
            _require_nonempty_string(part[9], f"{path}[9]"),
            _require_nonempty_string(part[10], f"{path}[10]"),
            _require_string(part[11], f"{path}[11]"),
            source,
            _require_source_span(part[13], source, f"{path}[13]"),
            _require_optional_nonempty_string(part[14], f"{path}[14]"),
        )
    if tag == "direct_call_run" and len(part) == 5:
        source = _require_string(part[3], f"{path}[3]")
        return ArtifactDirectCallRunPart(
            _require_nonnegative_int(part[1], f"{path}[1]"),
            _require_nonempty_string(part[2], f"{path}[2]"),
            source,
            _require_source_span(part[4], source, f"{path}[4]"),
        )
    if tag == "direct_python_component" and len(part) == 3:
        return ArtifactDirectPythonComponentPart(
            _require_nonnegative_int(part[1], f"{path}[1]"),
            _require_nonnegative_int(part[2], f"{path}[2]"),
        )
    raise CacheArtifactError(f"{path} has an unknown or malformed artifact part tag {tag!r}.")


def _attribute_from_wire(value: object, source: str, path: str) -> ArtifactAttribute:
    item = _require_list(value, path)
    if len(item) != 4:
        raise CacheArtifactError(f"{path} must contain exactly four fields.")
    origin = _require_string(item[1], f"{path}[1]")
    if origin not in {"source", "data"}:
        raise CacheArtifactError(f"{path}[1] must be 'source' or 'data'.")
    return ArtifactAttribute(
        _require_nonempty_string(item[0], f"{path}[0]"),
        origin,
        _require_source_span(item[2], source, f"{path}[2]"),
        _freeze_json_value(item[3], f"{path}[3]"),
    )


def _static_structure_from_wire(value: object, html: str, path: str) -> ArtifactStaticRunStructure | None:
    if value is None:
        return None
    item = _require_list(value, path)
    if len(item) != 3:
        raise CacheArtifactError(f"{path} must contain openings, final depth, and tag transitions.")
    openings: list[ArtifactStaticRunOpening] = []
    for index, raw in enumerate(_require_list(item[0], f"{path}[0]")):
        opening = _require_list(raw, f"{path}[0][{index}]")
        if len(opening) != 5:
            raise CacheArtifactError(f"{path}[0][{index}] must contain exactly five fields.")
        identities = tuple(
            _require_nonempty_string(v, f"{path}[0][{index}][4]")
            for v in _require_list(opening[4], f"{path}[0][{index}][4]")
        )
        if tuple(sorted(set(identities))) != identities:
            raise CacheArtifactError(f"{path}[0][{index}] attribute identities must be unique and sorted.")
        start_at, insert_at, end_at = (
            _require_nonnegative_int(opening[i], f"{path}[0][{index}][{i}]") for i in range(3)
        )
        if not start_at <= insert_at <= end_at <= len(html):
            raise CacheArtifactError(f"{path}[0][{index}] offsets must be ordered within the static HTML.")
        if openings and start_at < openings[-1].end_at:
            raise CacheArtifactError(f"{path}[0][{index}] overlaps or precedes the previous opening.")
        openings.append(
            ArtifactStaticRunOpening(
                start_at,
                insert_at,
                end_at,
                _require_int(opening[3], f"{path}[0][{index}][3]"),
                identities,
            )
        )
    transitions: list[tuple[str, str]] = []
    for index, raw in enumerate(_require_list(item[2], f"{path}[2]")):
        transition = _require_list(raw, f"{path}[2][{index}]")
        if len(transition) != 2 or transition[0] not in {"open", "close"}:
            raise CacheArtifactError(f"{path}[2][{index}] must be an open/close tag transition.")
        # Re-read the checked value as text so the pair carries the tag kind, not
        # the raw JSON entry it came from.
        kind = _require_nonempty_string(transition[0], f"{path}[2][{index}][0]")
        transitions.append((kind, _require_nonempty_string(transition[1], f"{path}[2][{index}][1]")))
    return ArtifactStaticRunStructure(tuple(openings), _require_int(item[1], f"{path}[1]"), tuple(transitions))


def _extension_from_wire(value: object, index: int) -> ArtifactExtension:
    path = f"artifact.extensions[{index}]"
    extension = _require_object(value, path)
    _require_fields(extension, {"name", "version", "payload"}, path)
    return ArtifactExtension(
        name=_require_nonempty_string(extension["name"], f"{path}.name"),
        version=_require_positive_int(extension["version"], f"{path}.version"),
        payload=_freeze_object(extension["payload"], f"{path}.payload"),
    )


def _validate_frame_tree(artifact: CachedRenderArtifact) -> None:
    frame_count = len(artifact.frames)
    if frame_count == 0:
        raise CacheArtifactError("Cached render artifact must contain at least one frame.")
    if type(artifact.root_frame) is not int or not 0 <= artifact.root_frame < frame_count:
        raise CacheArtifactError("artifact.root_frame does not refer to an existing frame.")
    incoming = [0] * frame_count
    adjacency: list[list[int]] = [[] for _ in artifact.frames]
    for frame_index, frame in enumerate(artifact.frames):
        if type(frame) is not ArtifactFrame:
            raise CacheArtifactError(f"artifact.frames[{frame_index}] is not an ArtifactFrame.")
        pending = [
            (part, f"artifact.frames[{frame_index}].parts[{part_index}]", 0)
            for part_index, part in enumerate(frame.parts)
        ]
        while pending:
            part, path, depth = pending.pop()
            if depth > _MAX_ARTIFACT_DEPTH:
                raise CacheArtifactError(
                    f"Cached render artifact exceeds the {_MAX_ARTIFACT_DEPTH} level structural depth limit at {path}."
                )
            if type(part) is ArtifactFramePart:
                if type(part.frame) is not int or not 0 <= part.frame < frame_count:
                    raise CacheArtifactError(f"artifact.frames[{frame_index}] refers to missing frame {part.frame!r}.")
                incoming[part.frame] += 1
                adjacency[frame_index].append(part.frame)
            # Spelled as separate identity checks rather than a membership test so the
            # exact-type rule stays visible and each branch's part type is known below.
            elif (
                type(part) is ArtifactDirectSlotPart
                or type(part) is ArtifactDirectCallRunPart
                or type(part) is ArtifactDirectPythonComponentPart
            ):
                child = part.frame
                if not 0 <= child < frame_count:
                    raise CacheArtifactError(f"artifact.frames[{frame_index}] refers to missing frame {child!r}.")
                incoming[child] += 1
                adjacency[frame_index].append(child)
                _part_from_wire(_part_to_wire(part), path)
                if type(part) is ArtifactDirectSlotPart:
                    if part.parent_execution is not None and part.external_parent_execution:
                        raise CacheArtifactError(f"{path} has conflicting direct execution parent anchors.")
                    if (part.lexical_instance is None) == (part.lexical_parent_depth is None):
                        raise CacheArtifactError(f"{path} must have exactly one lexical writer anchor.")
                    if (part.receiver_instance is None) == (part.receiver_parent_depth is None):
                        raise CacheArtifactError(f"{path} must have exactly one receiver anchor.")
                    projection_kinds = {"implicit", "named", "fallback", "nested-template"}
                    if part.kind not in projection_kinds:
                        raise CacheArtifactError(f"{path} has unknown direct projection kind {part.kind!r}.")
            elif type(part) is ArtifactPlaceholderPart:
                _require_nonempty_string(part.key, f"{path}.key")
            elif type(part) in (
                ArtifactSourceTextPart,
                ArtifactVerbatimHtmlPart,
                ArtifactTextValuePart,
                ArtifactTrustedHtmlPart,
                ArtifactElementOpenPart,
                ArtifactElementClosePart,
                ArtifactDynamicElementOpenPart,
                ArtifactDynamicElementClosePart,
                ArtifactStaticRunPart,
                ArtifactLeafProgramPart,
            ):
                # Use the wire decoder as the single exact-field/type validator
                # for immutable in-memory values as well as backend input.
                _part_from_wire(_part_to_wire(part), path)
            else:
                raise CacheArtifactError(
                    f"artifact.frames[{frame_index}] contains unsupported part {type(part).__name__}."
                )
    if incoming[artifact.root_frame] != 0:
        raise CacheArtifactError("Cached render artifact frame graph contains a cycle through its root.")
    for index, count in enumerate(incoming):
        if index != artifact.root_frame and count > 1:
            raise CacheArtifactError(f"artifact frame {index} is inserted more than once.")

    colors = [0] * frame_count
    stack: list[tuple[int, bool]] = [(artifact.root_frame, False)]
    while stack:
        frame_index, leaving = stack.pop()
        if leaving:
            colors[frame_index] = 2
            continue
        if colors[frame_index] == 1:
            raise CacheArtifactError("Cached render artifact frame graph contains a cycle.")
        if colors[frame_index] == 2:
            continue
        colors[frame_index] = 1
        stack.append((frame_index, True))
        stack.extend((child, False) for child in reversed(adjacency[frame_index]))
    if any(color == 0 for color in colors):
        raise CacheArtifactError("Cached render artifact contains an unreachable frame.")


def _freeze_object(value: object, path: str) -> FrozenJsonObject:
    # Validate iteratively first. Besides type and record limits, the depth cap
    # turns cyclic exporter payloads into CacheArtifactError before recursive
    # freezing can leak RecursionError into the component render.
    _validate_json_shape(value, path)
    frozen = _freeze_json(value, path)
    if type(frozen) is not FrozenJsonObject:
        raise CacheArtifactError(f"{path} must be a JSON object.")
    return frozen


def _freeze_json_value(value: object, path: str) -> FrozenJsonValue:
    _validate_json_shape(value, path)
    return _freeze_json(value, path)


def _freeze_json(value: object, path: str) -> FrozenJsonValue:
    if value is None or type(value) in (bool, int, str):
        return cast("None | bool | int | str", value)
    if type(value) is float:
        if not math.isfinite(value):
            raise CacheArtifactError(f"{path} contains a non-finite number.")
        return value
    if type(value) is list:
        return tuple(_freeze_json(item, f"{path}[{index}]") for index, item in enumerate(value))
    if type(value) is dict:
        mapping = cast("dict[object, object]", value)
        keys = list(mapping)
        for key in keys:
            if type(key) is not str:
                raise CacheArtifactError(f"{path} contains a non-string object key.")
        items: list[tuple[str, FrozenJsonValue]] = []
        for key in sorted(cast("list[str]", keys)):
            items.append((key, _freeze_json(mapping[key], f"{path}.{key}")))
        return FrozenJsonObject(tuple(items))
    raise CacheArtifactError(f"{path} contains unsupported JSON value {type(value).__name__}.")


def _thaw_json(value: FrozenJsonValue) -> object:
    if type(value) is FrozenJsonObject:
        return {key: _thaw_json(item) for key, item in value.items}
    if type(value) is tuple:
        return [_thaw_json(item) for item in value]
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise CacheArtifactError(f"Artifact contains unsupported frozen JSON value {type(value).__name__}.")


def _require_object(value: object, path: str) -> dict[str, object]:
    if type(value) is not dict:
        raise CacheArtifactError(f"{path} must be a JSON object.")
    return cast("dict[str, object]", value)


def _require_list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise CacheArtifactError(f"{path} must be a JSON array.")
    return cast("list[object]", value)


def _require_span(value: object, path: str) -> tuple[int, int]:
    raw = _require_list(value, path)
    if len(raw) != 2:
        raise CacheArtifactError(f"{path} must contain exactly two offsets.")
    start = _require_nonnegative_int(raw[0], f"{path}[0]")
    end = _require_nonnegative_int(raw[1], f"{path}[1]")
    if end < start:
        raise CacheArtifactError(f"{path} end must not precede its start.")
    return start, end


def _require_source_span(value: object, source: str, path: str) -> tuple[int, int]:
    span = _require_span(value, path)
    byte_offsets = {0}
    byte_length = 0
    for character in source:
        byte_length += len(character.encode("utf-8"))
        byte_offsets.add(byte_length)
    if span[1] > byte_length:
        raise CacheArtifactError(f"{path} exceeds its source UTF-8 length.")
    if span[0] not in byte_offsets or span[1] not in byte_offsets:
        raise CacheArtifactError(f"{path} must use UTF-8 byte boundaries in its source.")
    return span


def _require_fields(value: dict[str, object], expected: set[str], path: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise CacheArtifactError(f"{path} is missing required field {sorted(missing)[0]!r}.")
    if unknown:
        raise CacheArtifactError(f"{path} has unknown field {sorted(unknown)[0]!r}.")


def _require_exact_int(value: object, path: str, *, expected: int) -> int:
    if type(value) is not int or value != expected:
        raise CacheArtifactError(f"{path} must be the supported integer value {expected}; got {value!r}.")
    return value


def _require_nonnegative_int(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise CacheArtifactError(f"{path} must be an exact non-negative integer; got {value!r}.")
    return value


def _require_int(value: object, path: str) -> int:
    if type(value) is not int:
        raise CacheArtifactError(f"{path} must be an exact integer; got {value!r}.")
    return value


def _require_bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise CacheArtifactError(f"{path} must be a bool.")
    return value


def _require_positive_int(value: object, path: str) -> int:
    if type(value) is not int or value <= 0:
        raise CacheArtifactError(f"{path} must be an exact positive integer; got {value!r}.")
    return value


def _require_string(value: object, path: str) -> str:
    if type(value) is not str:
        raise CacheArtifactError(f"{path} must be an exact string; got {type(value).__name__}.")
    _validate_utf8_text(value, path)
    return value


def _validate_utf8_text(value: str, path: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CacheArtifactError(f"{path} must be valid UTF-8 text; Unicode surrogates are unsupported.") from error


def _require_nonempty_string(value: object, path: str) -> str:
    result = _require_string(value, path)
    if not result:
        raise CacheArtifactError(f"{path} must not be empty.")
    return result


def _require_binding_provenance(value: str, path: str) -> Literal["authored", "runtime-spread"]:
    """Narrow one replayed binding provenance to a value the renderer accepts."""
    # The artifact stores this as ordinary JSON text, so each accepted value is
    # returned by name: an unrecognized one must not reach the renderer, where
    # runtime provenance decides whether a handler may come from a spread.
    if value == "authored":
        return "authored"
    if value == "runtime-spread":
        return "runtime-spread"
    raise CacheArtifactError(f"{path} has an unknown binding provenance.")


def _require_attribute_origin(value: str, path: str) -> Literal["source", "data"]:
    """Narrow one replayed attribute origin to a value the renderer accepts."""
    # Origin decides whether the attribute is treated as template source or as
    # data, so a cache entry naming anything else is rejected rather than guessed.
    if value == "source":
        return "source"
    if value == "data":
        return "data"
    raise CacheArtifactError(f"{path} has an unknown attribute origin.")


def _require_optional_nonempty_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty_string(value, path)


__all__ = [
    "ArtifactAttribute",
    "ArtifactDirectCallRunPart",
    "ArtifactDirectSlotPart",
    "ArtifactDynamicElementClosePart",
    "ArtifactDynamicElementOpenPart",
    "ArtifactElementClosePart",
    "ArtifactElementOpenPart",
    "ArtifactExtension",
    "ArtifactFrame",
    "ArtifactFramePart",
    "ArtifactLeafProgramPart",
    "ArtifactPlaceholderPart",
    "ArtifactSourceTextPart",
    "ArtifactStaticRunOpening",
    "ArtifactStaticRunPart",
    "ArtifactStaticRunStructure",
    "ArtifactTextValuePart",
    "ArtifactTrustedHtmlPart",
    "ArtifactVerbatimHtmlPart",
    "CachedRenderArtifact",
    "FrozenJsonObject",
]
