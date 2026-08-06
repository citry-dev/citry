"""Immutable detached render artifacts and their strict JSON codec."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import TypeAlias, cast

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
    """An ordered immutable JSON object used by extension and ownership payloads."""

    items: tuple[tuple[str, FrozenJsonValue], ...]


FrozenJsonValue: TypeAlias = "None | bool | int | float | str | tuple[FrozenJsonValue, ...] | FrozenJsonObject"


@dataclass(frozen=True, slots=True)
class ArtifactTextPart:
    text: str


@dataclass(frozen=True, slots=True)
class ArtifactFramePart:
    frame: int


@dataclass(frozen=True, slots=True)
class ArtifactPlaceholderPart:
    key: str


@dataclass(frozen=True, slots=True)
class ArtifactRegionPart:
    region: int
    part: ArtifactPart


ArtifactPart: TypeAlias = "ArtifactTextPart | ArtifactFramePart | ArtifactPlaceholderPart | ArtifactRegionPart"


@dataclass(frozen=True, slots=True)
class ArtifactFrame:
    """One detached render frame with no original render ID or live context."""

    instance: int | None
    class_id: str | None
    class_name: str | None
    is_component_root: bool
    root_markers: tuple[str, ...]
    parts: tuple[ArtifactPart, ...]


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
    ownership: FrozenJsonObject
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
    _validate_frozen_json(artifact.ownership, "artifact.ownership")
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
        if frame.instance is None:
            if frame.class_id is not None or frame.class_name is not None or frame.is_component_root:
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
        "ownership": _thaw_json(artifact.ownership),
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
        "root_markers": list(frame.root_markers),
        "parts": [_part_to_wire(part) for part in frame.parts],
    }


def _part_to_wire(part: ArtifactPart) -> list[object]:
    if type(part) is ArtifactTextPart:
        return ["text", part.text]
    if type(part) is ArtifactFramePart:
        return ["frame", part.frame]
    if type(part) is ArtifactPlaceholderPart:
        return ["placeholder", part.key]
    if type(part) is ArtifactRegionPart:
        return ["region", part.region, _part_to_wire(part.part)]
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
            "ownership",
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
    ownership = _freeze_object(root["ownership"], "artifact.ownership")
    extension_values = _require_list(root["extensions"], "artifact.extensions")
    extensions = tuple(_extension_from_wire(item, index) for index, item in enumerate(extension_values))
    names = [extension.name for extension in extensions]
    if len(names) != len(set(names)):
        raise CacheArtifactError("Cached render artifact contains a duplicate extension payload name.")
    return CachedRenderArtifact(
        root_frame=root_frame,
        frames=frames,
        ownership=ownership,
        extensions=extensions,
    )


def _frame_from_wire(value: object, index: int) -> ArtifactFrame:
    path = f"artifact.frames[{index}]"
    frame = _require_object(value, path)
    _require_fields(
        frame,
        {"instance", "class_id", "class_name", "component_root", "root_markers", "parts"},
        path,
    )
    instance_value = frame["instance"]
    instance = None if instance_value is None else _require_nonnegative_int(instance_value, f"{path}.instance")
    class_id = _require_optional_nonempty_string(frame["class_id"], f"{path}.class_id")
    class_name = _require_optional_nonempty_string(frame["class_name"], f"{path}.class_name")
    component_root = frame["component_root"]
    if type(component_root) is not bool:
        raise CacheArtifactError(f"{path}.component_root must be a bool.")
    if instance is None:
        if class_id is not None or class_name is not None or component_root:
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
        root_markers=root_markers,
        parts=parts,
    )


def _part_from_wire(value: object, path: str) -> ArtifactPart:
    part = _require_list(value, path)
    if not part or type(part[0]) is not str:
        raise CacheArtifactError(f"{path} must start with a string part tag.")
    tag = part[0]
    if tag == "text" and len(part) == 2:
        return ArtifactTextPart(_require_string(part[1], f"{path}[1]"))
    if tag == "frame" and len(part) == 2:
        return ArtifactFramePart(_require_nonnegative_int(part[1], f"{path}[1]"))
    if tag == "placeholder" and len(part) == 2:
        return ArtifactPlaceholderPart(_require_nonempty_string(part[1], f"{path}[1]"))
    if tag == "region" and len(part) == 3:
        return ArtifactRegionPart(
            _require_nonnegative_int(part[1], f"{path}[1]"),
            _part_from_wire(part[2], f"{path}[2]"),
        )
    raise CacheArtifactError(f"{path} has an unknown or malformed artifact part tag {tag!r}.")


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
            elif type(part) is ArtifactRegionPart:
                _require_nonnegative_int(part.region, f"{path}.region")
                pending.append((part.part, f"{path}.part", depth + 1))
            elif type(part) is ArtifactTextPart:
                _require_string(part.text, f"{path}.text")
            elif type(part) is ArtifactPlaceholderPart:
                _require_nonempty_string(part.key, f"{path}.key")
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


def _require_optional_nonempty_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty_string(value, path)


__all__ = [
    "ArtifactExtension",
    "ArtifactFrame",
    "ArtifactFramePart",
    "ArtifactPlaceholderPart",
    "ArtifactRegionPart",
    "ArtifactTextPart",
    "CachedRenderArtifact",
    "FrozenJsonObject",
]
