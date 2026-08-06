"""Frozen value records used by Citry's component introspection API."""

from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from secrets import token_hex
from typing import Literal, TypeAlias, cast

_SCHEMA_VERSION = 1
_MAX_SAFE_INTEGER = 2**53 - 1
_PATH_TYPE = type(Path())
_RUNTIME_ID_NONCE = token_hex(12)
_RUNTIME_ID_LOCK = threading.Lock()
_RUNTIME_ID_COUNTER = count(1)


def _new_runtime_id(kind: Literal["eng", "def"]) -> str:
    """Return a non-time-derived token unique within this Python process."""
    with _RUNTIME_ID_LOCK:
        sequence = next(_RUNTIME_ID_COUNTER)
    return f"{kind}_{_RUNTIME_ID_NONCE}_{sequence:x}"


def _new_engine_id() -> str:
    """Return the runtime token for one Citry instance."""
    return _new_runtime_id("eng")


def _new_definition_id() -> str:
    """Return the runtime token for one component class generation."""
    return _new_runtime_id("def")


class ComponentIntrospectionError(RuntimeError):
    """
    Report that a requested extension could not publish component metadata.

    Attributes:
        extension_name: The installed or requested extension name.
        component_name: The component's primary registered name, when the
            failure happened while inspecting one component.

    """

    def __init__(
        self,
        extension_name: str,
        component_name: str | None,
        detail: str,
    ) -> None:
        self.extension_name = extension_name
        self.component_name = component_name
        target = f" for component {component_name!r}" if component_name is not None else ""
        super().__init__(f"Extension {extension_name!r} cannot provide introspection{target}: {detail}")


class _FrozenJsonObject(tuple):
    """Tagged tuple used to distinguish frozen JSON objects from arrays."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return type(other) is _FrozenJsonObject and _json_values_equal(tuple(self), tuple(other))

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(("citry-json-object", _json_value_hash(tuple(self))))


FrozenJsonObject: TypeAlias = _FrozenJsonObject
FrozenJsonValue: TypeAlias = None | bool | str | int | float | tuple["FrozenJsonValue", ...] | FrozenJsonObject


class _UnsupportedJsonValue(ValueError):
    """A value cannot enter Citry's strict portable JSON representation."""


def _is_utf8_string(value: str) -> bool:
    """Return whether a string can be emitted as UTF-8 without surrogate code points."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _require_utf8_string(value: str, field_name: str) -> None:
    if not _is_utf8_string(value):
        msg = f"{field_name} must not contain unpaired Unicode surrogate code points."
        raise ValueError(msg)


def _json_values_equal(left: FrozenJsonValue, right: FrozenJsonValue) -> bool:
    """Compare frozen JSON with type-sensitive JSON scalar and container semantics."""
    if type(left) is not type(right):
        return False
    if type(left) is _FrozenJsonObject or type(left) is tuple:
        left_items = cast("tuple[object, ...]", left)
        right_items = cast("tuple[object, ...]", right)
        return len(left_items) == len(right_items) and all(
            _json_values_equal(cast("FrozenJsonValue", left_item), cast("FrozenJsonValue", right_item))
            for left_item, right_item in zip(left_items, right_items, strict=True)
        )
    if type(left) is float:
        return left.hex() == cast("float", right).hex()
    return bool(left == right)


def _json_value_hash(value: FrozenJsonValue) -> int:
    """Hash frozen JSON consistently with its type-sensitive equality."""
    if type(value) is _FrozenJsonObject:
        return hash(("object", tuple(_json_value_hash(cast("FrozenJsonValue", item)) for item in value)))
    if type(value) is tuple:
        return hash(("array", tuple(_json_value_hash(item) for item in value)))
    if type(value) is float:
        return hash((float, value.hex()))
    return hash((type(value), value))


def _freeze_json_value(
    value: object,
    active_containers: set[int] | None = None,
    *,
    allow_frozen_object: bool = True,
) -> FrozenJsonValue:
    """Copy one exact built-in JSON value into its recursively frozen form."""
    value_type = type(value)
    if value is None or value_type is bool:
        return cast("None | bool", value)
    if value_type is str:
        string_value = cast("str", value)
        if not _is_utf8_string(string_value):
            msg = "Portable JSON strings must not contain unpaired Unicode surrogate code points."
            raise _UnsupportedJsonValue(msg)
        return string_value
    if value_type is int:
        integer_value = cast("int", value)
        if not -_MAX_SAFE_INTEGER <= integer_value <= _MAX_SAFE_INTEGER:
            msg = "JSON integers must be within JavaScript's safe integer range."
            raise _UnsupportedJsonValue(msg)
        return integer_value
    if value_type is float:
        float_value = cast("float", value)
        if not math.isfinite(float_value):
            msg = "JSON floats must be finite."
            raise _UnsupportedJsonValue(msg)
        return float_value
    if value_type is _FrozenJsonObject:
        if not allow_frozen_object:
            msg = "Extension inspectors may publish only exact built-in JSON containers."
            raise _UnsupportedJsonValue(msg)
        frozen_items = cast("_FrozenJsonObject", value)
        keys: list[str] = []
        copied_items: list[tuple[str, FrozenJsonValue]] = []
        for item in frozen_items:
            if type(item) is not tuple or len(item) != 2 or type(item[0]) is not str:
                msg = "Frozen JSON objects must contain exact string-keyed pairs."
                raise _UnsupportedJsonValue(msg)
            key, item_value = item
            if not _is_utf8_string(key):
                msg = "Frozen JSON object keys must not contain unpaired Unicode surrogate code points."
                raise _UnsupportedJsonValue(msg)
            keys.append(key)
            copied_items.append(
                (
                    key,
                    _freeze_json_value(
                        item_value,
                        active_containers,
                        allow_frozen_object=allow_frozen_object,
                    ),
                )
            )
        if keys != sorted(set(keys)):
            msg = "Frozen JSON object keys must be unique and sorted."
            raise _UnsupportedJsonValue(msg)
        return _FrozenJsonObject(copied_items)

    if value_type is not list and value_type is not tuple and value_type is not dict:
        msg = "The value is not an exact built-in portable JSON type."
        raise _UnsupportedJsonValue(msg)

    if active_containers is None:
        active_containers = set()
    identity = id(value)
    if identity in active_containers:
        msg = "Portable JSON values cannot contain cycles."
        raise _UnsupportedJsonValue(msg)
    active_containers.add(identity)
    try:
        if value_type is list or value_type is tuple:
            sequence = cast("list[object] | tuple[object, ...]", value)
            return tuple(
                _freeze_json_value(item, active_containers, allow_frozen_object=allow_frozen_object)
                for item in sequence
            )

        raw_mapping = cast("dict[object, object]", value)
        if any(type(key) is not str for key in raw_mapping):
            msg = "Portable JSON object keys must be exact strings."
            raise _UnsupportedJsonValue(msg)
        mapping = cast("dict[str, object]", raw_mapping)
        if any(not _is_utf8_string(key) for key in mapping):
            msg = "Portable JSON object keys must not contain unpaired Unicode surrogate code points."
            raise _UnsupportedJsonValue(msg)
        items = tuple(
            (
                key,
                _freeze_json_value(
                    mapping[key],
                    active_containers,
                    allow_frozen_object=allow_frozen_object,
                ),
            )
            for key in sorted(mapping)
        )
        return _FrozenJsonObject(items)
    except RecursionError as err:
        msg = "Portable JSON values are nested too deeply."
        raise _UnsupportedJsonValue(msg) from err
    finally:
        active_containers.remove(identity)


def _freeze_json_object(value: object) -> FrozenJsonObject:
    """Copy a strict JSON object and reject a scalar or array at the root."""
    if type(value) is _FrozenJsonObject:
        return cast("FrozenJsonObject", _freeze_json_value(value))
    if type(value) is not dict:
        msg = "Extension introspection data must be an exact built-in dict."
        raise ValueError(msg)
    frozen = _freeze_json_value(value)
    return cast("FrozenJsonObject", frozen)


def _freeze_extension_publication(value: object) -> FrozenJsonObject:
    """Freeze one inspector result while accepting only exact built-in containers."""
    if type(value) is not dict:
        msg = "Extension introspection data must be an exact built-in dict."
        raise _UnsupportedJsonValue(msg)
    frozen = _freeze_json_value(value, allow_frozen_object=False)
    return cast("FrozenJsonObject", frozen)


def _thaw_json_value(value: FrozenJsonValue) -> object:
    """Return a fresh ordinary JSON-ready value from a frozen value."""
    if type(value) is _FrozenJsonObject:
        return {key: _thaw_json_value(item) for key, item in value}
    if type(value) is tuple:
        return [_thaw_json_value(item) for item in value]
    return value


def _require_exact_str(value: object, field_name: str) -> None:
    if type(value) is not str or not value:
        msg = f"{field_name} must be a non-empty string."
        raise ValueError(msg)
    _require_utf8_string(value, field_name)


def _require_tuple(value: object, field_name: str) -> None:
    if type(value) is not tuple:
        msg = f"{field_name} must be a tuple."
        raise TypeError(msg)


def _require_absolute_path(value: Path | None, field_name: str) -> None:
    if value is not None and (type(value) is not _PATH_TYPE or not value.is_absolute()):
        msg = f"{field_name} must be an absolute pathlib.Path or None."
        raise ValueError(msg)
    if value is not None:
        _require_utf8_string(value.as_posix(), field_name)


def _require_absolute_path_entry(value: object, field_name: str) -> None:
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        msg = f"{field_name} must be an absolute pathlib.Path."
        raise ValueError(msg)
    _require_utf8_string(value.as_posix(), field_name)


@dataclass(frozen=True, slots=True, eq=False, init=False)
class FieldInfo:
    """
    Describe one field in a recognized component schema.

    Attributes:
        name: The schema adapter's canonical field name.
        required: Whether callers must provide the field.
        type_display: A safe normalized type string, when available.
        type_fidelity: Whether ``type_display`` contains a normalized type.
        default_kind: Whether the field has no default, a value, or a factory.
        default_value_state: Whether a real default value was requested and copied.
        default_value: A recursively frozen portable default, when available.
        description: Runtime field documentation from a supported schema source.
        source_module: Module that owns the authored field, when provable.
        source_qualname: Qualified class name that owns the field, when provable.
        source_file: Absolute already-loaded module file for that class, when available.

    """

    name: str
    required: bool
    type_display: str | None
    type_fidelity: Literal["normalized", "unavailable"]
    default_kind: Literal["missing", "value", "factory"]
    default_value_state: Literal["not-applicable", "omitted", "available", "unsupported"]
    default_value: FrozenJsonValue | None
    description: str | None
    source_module: str | None = None
    source_qualname: str | None = None
    source_file: Path | None = None

    def __init__(
        self,
        name: str,
        required: bool,
        type_display: str | None,
        type_fidelity: Literal["normalized", "unavailable"],
        default_kind: Literal["missing", "value", "factory"],
        default_value_state: Literal["not-applicable", "omitted", "available", "unsupported"],
        default_value: object,
        description: str | None,
        source_module: str | None = None,
        source_qualname: str | None = None,
        source_file: Path | None = None,
    ) -> None:
        """Accept ordinary JSON inputs while storing only a frozen JSON value."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "required", required)
        object.__setattr__(self, "type_display", type_display)
        object.__setattr__(self, "type_fidelity", type_fidelity)
        object.__setattr__(self, "default_kind", default_kind)
        object.__setattr__(self, "default_value_state", default_value_state)
        object.__setattr__(self, "default_value", cast("FrozenJsonValue | None", default_value))
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source_module", source_module)
        object.__setattr__(self, "source_qualname", source_qualname)
        object.__setattr__(self, "source_file", source_file)
        self.__post_init__()

    def __eq__(self, other: object) -> bool:
        if type(other) is not FieldInfo:
            return False
        other_field = cast("FieldInfo", other)
        return (
            self.name,
            self.required,
            self.type_display,
            self.type_fidelity,
            self.default_kind,
            self.default_value_state,
            self.description,
            self.source_module,
            self.source_qualname,
            self.source_file,
        ) == (
            other_field.name,
            other_field.required,
            other_field.type_display,
            other_field.type_fidelity,
            other_field.default_kind,
            other_field.default_value_state,
            other_field.description,
            other_field.source_module,
            other_field.source_qualname,
            other_field.source_file,
        ) and _json_values_equal(self.default_value, other_field.default_value)

    def __hash__(self) -> int:
        return hash(
            (
                FieldInfo,
                self.name,
                self.required,
                self.type_display,
                self.type_fidelity,
                self.default_kind,
                self.default_value_state,
                _json_value_hash(self.default_value),
                self.description,
                self.source_module,
                self.source_qualname,
                self.source_file,
            )
        )

    def __post_init__(self) -> None:
        _require_exact_str(self.name, "FieldInfo.name")
        if type(self.required) is not bool:
            msg = "FieldInfo.required must be a bool."
            raise TypeError(msg)
        if type(self.type_fidelity) is not str or self.type_fidelity not in {"normalized", "unavailable"}:
            msg = f"Unknown field type fidelity: {self.type_fidelity!r}."
            raise ValueError(msg)
        normalized_type = type(self.type_display) is str and bool(self.type_display)
        unavailable_type = self.type_display is None
        if (self.type_fidelity == "normalized" and not normalized_type) or (
            self.type_fidelity == "unavailable" and not unavailable_type
        ):
            msg = "A normalized field type must have a non-empty display string, and an unavailable type must not."
            raise ValueError(msg)
        if self.type_display is not None:
            _require_utf8_string(self.type_display, "FieldInfo.type_display")
        if type(self.default_kind) is not str or self.default_kind not in {"missing", "value", "factory"}:
            msg = f"Unknown field default kind: {self.default_kind!r}."
            raise ValueError(msg)
        if type(self.default_value_state) is not str or self.default_value_state not in {
            "not-applicable",
            "omitted",
            "available",
            "unsupported",
        }:
            msg = f"Unknown field default value state: {self.default_value_state!r}."
            raise ValueError(msg)
        if self.required != (self.default_kind == "missing"):
            msg = "A field is required exactly when its default kind is 'missing'."
            raise ValueError(msg)
        if self.description is not None and type(self.description) is not str:
            msg = "FieldInfo.description must be a string or None."
            raise TypeError(msg)
        if self.description is not None:
            _require_utf8_string(self.description, "FieldInfo.description")
        for value, field_name in (
            (self.source_module, "FieldInfo.source_module"),
            (self.source_qualname, "FieldInfo.source_qualname"),
        ):
            if value is not None:
                _require_exact_str(value, field_name)
        if (self.source_module is None) != (self.source_qualname is None):
            msg = "FieldInfo source module and qualname must either both be present or both be absent."
            raise ValueError(msg)
        _require_absolute_path(self.source_file, "FieldInfo.source_file")
        if self.source_file is not None and self.source_module is None:
            msg = "FieldInfo.source_file requires source module and qualname provenance."
            raise ValueError(msg)

        if self.default_kind in {"missing", "factory"}:
            if self.default_value_state != "not-applicable" or self.default_value is not None:
                msg = "Missing and factory defaults use state 'not-applicable' and carry no value."
                raise ValueError(msg)
            return
        if self.default_value_state not in {"omitted", "available", "unsupported"}:
            msg = "A value default must be omitted, available, or unsupported."
            raise ValueError(msg)
        if self.default_value_state != "available":
            if self.default_value is not None:
                msg = "Omitted and unsupported defaults carry no value."
                raise ValueError(msg)
            return
        try:
            frozen = _freeze_json_value(self.default_value)
        except _UnsupportedJsonValue as err:
            msg = "An available default must be a portable JSON value."
            raise ValueError(msg) from err
        object.__setattr__(self, "default_value", frozen)


@dataclass(frozen=True, slots=True)
class SchemaInfo:
    """
    Describe one effective component schema binding.

    Attributes:
        kind: Whether the schema is absent, recognized as fields, or opaque.
        declared_on: Import path of the MRO class that supplied the binding.
        import_path: Import path of the effective schema class.
        fields: Recognized fields in runtime declaration order.

    """

    kind: Literal["absent", "fields", "opaque"]
    declared_on: str | None
    import_path: str | None
    fields: tuple[FieldInfo, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in {"absent", "fields", "opaque"}:
            msg = f"Unknown schema kind: {self.kind!r}."
            raise ValueError(msg)
        _require_tuple(self.fields, "SchemaInfo.fields")
        if any(type(field) is not FieldInfo for field in self.fields):
            msg = "SchemaInfo.fields must contain only FieldInfo values."
            raise TypeError(msg)
        field_names = tuple(field.name for field in self.fields)
        if len(field_names) != len(set(field_names)):
            msg = "SchemaInfo field names must be unique."
            raise ValueError(msg)
        if self.kind == "absent":
            if self.import_path is not None or self.fields:
                msg = "An absent schema has no import path or fields."
                raise ValueError(msg)
            if self.declared_on is not None:
                _require_exact_str(self.declared_on, "SchemaInfo.declared_on")
            return
        if self.kind == "fields":
            _require_exact_str(self.declared_on, "SchemaInfo.declared_on")
            _require_exact_str(self.import_path, "SchemaInfo.import_path")
            return
        if self.kind == "opaque":
            _require_exact_str(self.declared_on, "SchemaInfo.declared_on")
            _require_exact_str(self.import_path, "SchemaInfo.import_path")
            if self.fields:
                msg = "An opaque schema cannot contain recognized fields."
                raise ValueError(msg)
            return
        msg = f"Unknown schema kind: {self.kind!r}."
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ComponentSchemas:
    """
    Group the five typed schema roles exposed by a component.

    Attributes:
        kwargs: Inputs accepted as component keyword arguments.
        slots: Slot fills accepted by the component.
        template_data: Values returned for template rendering.
        js_data: Values made available to component JavaScript.
        css_data: Values made available to component CSS.

    """

    kwargs: SchemaInfo
    slots: SchemaInfo
    template_data: SchemaInfo
    js_data: SchemaInfo
    css_data: SchemaInfo

    def __post_init__(self) -> None:
        for field_name in ("kwargs", "slots", "template_data", "js_data", "css_data"):
            if type(getattr(self, field_name)) is not SchemaInfo:
                msg = f"ComponentSchemas.{field_name} must be a SchemaInfo value."
                raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class AssetInfo:
    """
    Describe one primary template, JavaScript, or CSS declaration.

    Attributes:
        kind: Whether the asset is absent, inline, or file-backed.
        declared_on: Import path of the class that supplied the declaration.
        owner_file: Absolute Python file containing the declaring class.
        declared_path: The file path exactly as declared by the component.
        resolution: Whether path resolution was requested and what it found.
        resolved_path: Absolute existing asset path when resolution succeeded.
        searched_paths: Absolute candidate paths checked during resolution.
        owner_module: Module of the class that supplied the declaration.
        owner_qualname: Qualified name of that declaring class.

    """

    kind: Literal["none", "inline", "file"]
    declared_on: str | None
    owner_file: Path | None
    declared_path: str | None
    resolution: Literal["not-applicable", "not-requested", "resolved", "missing", "unavailable"]
    resolved_path: Path | None
    searched_paths: tuple[Path, ...]
    owner_module: str | None = None
    owner_qualname: str | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in {"none", "inline", "file"}:
            msg = f"Unknown asset kind: {self.kind!r}."
            raise ValueError(msg)
        if type(self.resolution) is not str or self.resolution not in {
            "not-applicable",
            "not-requested",
            "resolved",
            "missing",
            "unavailable",
        }:
            msg = f"Unknown asset resolution: {self.resolution!r}."
            raise ValueError(msg)
        _require_tuple(self.searched_paths, "AssetInfo.searched_paths")
        _require_absolute_path(self.owner_file, "AssetInfo.owner_file")
        _require_absolute_path(self.resolved_path, "AssetInfo.resolved_path")
        for searched_path in self.searched_paths:
            _require_absolute_path_entry(searched_path, "AssetInfo.searched_paths entry")
        if (self.owner_module is None) != (self.owner_qualname is None):
            msg = "Asset owner module and qualified name must either both be present or both be absent."
            raise ValueError(msg)
        if self.owner_module is not None and self.owner_qualname is not None:
            _require_exact_str(self.owner_module, "AssetInfo.owner_module")
            _require_exact_str(self.owner_qualname, "AssetInfo.owner_qualname")
            if self.declared_on != f"{self.owner_module}.{self.owner_qualname}":
                msg = "Asset structured owner provenance must match declared_on."
                raise ValueError(msg)

        if self.kind == "none":
            if (
                self.resolution != "not-applicable"
                or any(value is not None for value in (self.declared_path, self.resolved_path))
                or self.searched_paths
            ):
                msg = "An absent asset has no path state and uses resolution 'not-applicable'."
                raise ValueError(msg)
            if self.declared_on is None and self.owner_file is not None:
                msg = "A framework-default absent asset cannot have an owner file."
                raise ValueError(msg)
            if self.declared_on is not None:
                _require_exact_str(self.declared_on, "AssetInfo.declared_on")
            return
        if self.kind == "inline":
            _require_exact_str(self.declared_on, "AssetInfo.declared_on")
            if (
                self.resolution != "not-applicable"
                or self.declared_path is not None
                or self.resolved_path is not None
                or self.searched_paths
            ):
                msg = "An inline asset has no path state and uses resolution 'not-applicable'."
                raise ValueError(msg)
            return
        if self.kind != "file":
            msg = f"Unknown asset kind: {self.kind!r}."
            raise ValueError(msg)

        _require_exact_str(self.declared_on, "AssetInfo.declared_on")
        _require_exact_str(self.declared_path, "AssetInfo.declared_path")
        if self.resolution == "not-requested":
            if self.resolved_path is not None or self.searched_paths:
                msg = "An unresolved file asset has no resolved or searched paths."
                raise ValueError(msg)
            return
        if self.resolution == "resolved":
            if self.resolved_path is None or not self.searched_paths or self.resolved_path not in self.searched_paths:
                msg = "A resolved file asset must include its absolute winning path among searched paths."
                raise ValueError(msg)
            return
        if self.resolution == "missing":
            if self.resolved_path is not None or not self.searched_paths:
                msg = "A missing file asset has searched paths but no resolved path."
                raise ValueError(msg)
            return
        if self.resolution == "unavailable":
            if (
                self.owner_file is not None
                or Path(cast("str", self.declared_path)).is_absolute()
                or self.resolved_path is not None
                or self.searched_paths
            ):
                msg = "An unavailable file asset is relative, has no owner file, and has no candidate paths."
                raise ValueError(msg)
            return
        msg = f"Invalid resolution {self.resolution!r} for a file asset."
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ComponentAssets:
    """
    Group a component's primary template, JavaScript, and CSS declarations.

    Attributes:
        template: The primary template declaration.
        js: The primary JavaScript declaration.
        css: The primary CSS declaration.

    """

    template: AssetInfo
    js: AssetInfo
    css: AssetInfo

    def __post_init__(self) -> None:
        for field_name in ("template", "js", "css"):
            if type(getattr(self, field_name)) is not AssetInfo:
                msg = f"ComponentAssets.{field_name} must be an AssetInfo value."
                raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ExtensionVersion:
    """
    Record one requested extension's introspection schema version.

    Attributes:
        name: The extension's unique registered name.
        introspection_version: The extension-owned positive schema version.

    """

    name: str
    introspection_version: int

    def __post_init__(self) -> None:
        _require_exact_str(self.name, "ExtensionVersion.name")
        if type(self.introspection_version) is not int or self.introspection_version <= 0:
            msg = "ExtensionVersion.introspection_version must be a positive integer."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, eq=False, init=False)
class ComponentExtensionInfo:
    """
    Store one extension's explicitly published component metadata.

    Attributes:
        name: The extension's unique registered name.
        introspection_version: The extension-owned positive schema version.
        data: A defensively copied and recursively frozen JSON object.

    """

    name: str
    introspection_version: int
    data: FrozenJsonObject

    def __init__(
        self,
        name: str,
        introspection_version: int,
        data: object,
    ) -> None:
        """Accept an ordinary JSON object while storing only its frozen form."""
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "introspection_version", introspection_version)
        object.__setattr__(self, "data", cast("FrozenJsonObject", data))
        self.__post_init__()

    def __eq__(self, other: object) -> bool:
        if type(other) is not ComponentExtensionInfo:
            return False
        other_info = cast("ComponentExtensionInfo", other)
        return (
            self.name == other_info.name
            and self.introspection_version == other_info.introspection_version
            and _json_values_equal(self.data, other_info.data)
        )

    def __hash__(self) -> int:
        return hash(
            (
                ComponentExtensionInfo,
                self.name,
                self.introspection_version,
                _json_value_hash(self.data),
            )
        )

    def __post_init__(self) -> None:
        _require_exact_str(self.name, "ComponentExtensionInfo.name")
        if type(self.introspection_version) is not int or self.introspection_version <= 0:
            msg = "ComponentExtensionInfo.introspection_version must be a positive integer."
            raise ValueError(msg)
        object.__setattr__(self, "data", _freeze_json_object(self.data))


@dataclass(frozen=True, slots=True)
class ComponentInfo:
    """
    Describe one exact registered component class generation.

    Attributes:
        class_id: Stable import-derived component route identity.
        engine_id: Runtime identity of the owning Citry instance.
        definition_id: Runtime identity of this exact class generation.
        name: Deterministically selected primary registration name.
        aliases: Other registration names for the same class.
        class_name: Python class name, when available.
        module: Python module name, when available.
        qualname: Python qualified class name, when available.
        import_path: Full Python import path, when available.
        python_file: Absolute already-loaded module file, when available.
        description: The component class's own cleaned docstring.
        transparent: Whether the component joins its parent's serialization frame.
        builtin: Whether Citry created this as a framework component.
        schemas: The component's five effective typed schemas.
        assets: The component's three primary asset declarations.
        extensions: Explicitly requested extension-owned metadata.

    """

    class_id: str
    engine_id: str
    definition_id: str
    name: str
    aliases: tuple[str, ...]
    class_name: str | None
    module: str | None
    qualname: str | None
    import_path: str | None
    python_file: Path | None
    description: str | None
    transparent: bool
    builtin: bool
    schemas: ComponentSchemas
    assets: ComponentAssets
    extensions: tuple[ComponentExtensionInfo, ...]

    def __post_init__(self) -> None:
        for field_name in ("class_id", "engine_id", "definition_id", "name"):
            _require_exact_str(getattr(self, field_name), f"ComponentInfo.{field_name}")
        _require_tuple(self.aliases, "ComponentInfo.aliases")
        _require_tuple(self.extensions, "ComponentInfo.extensions")
        if any(type(alias) is not str or not alias for alias in self.aliases):
            msg = "ComponentInfo.aliases must contain non-empty strings."
            raise ValueError(msg)
        for alias in self.aliases:
            _require_utf8_string(alias, "ComponentInfo.aliases entry")
        if tuple(sorted(set(self.aliases))) != self.aliases or self.name in self.aliases:
            msg = "ComponentInfo.aliases must be unique, sorted, and exclude the primary name."
            raise ValueError(msg)
        for field_name in ("class_name", "module", "qualname", "import_path", "description"):
            value = getattr(self, field_name)
            if value is not None and type(value) is not str:
                msg = f"ComponentInfo.{field_name} must be a string or None."
                raise TypeError(msg)
            if value is not None:
                _require_utf8_string(value, f"ComponentInfo.{field_name}")
        _require_absolute_path(self.python_file, "ComponentInfo.python_file")
        if type(self.transparent) is not bool or type(self.builtin) is not bool:
            msg = "ComponentInfo.transparent and builtin must be bool values."
            raise TypeError(msg)
        if type(self.schemas) is not ComponentSchemas or type(self.assets) is not ComponentAssets:
            msg = "ComponentInfo.schemas and assets must use their introspection records."
            raise TypeError(msg)
        if any(type(entry) is not ComponentExtensionInfo for entry in self.extensions):
            msg = "ComponentInfo.extensions must contain ComponentExtensionInfo values."
            raise TypeError(msg)
        extension_names = tuple(entry.name for entry in self.extensions)
        if tuple(sorted(set(extension_names))) != extension_names:
            msg = "ComponentInfo.extensions must be unique and sorted by name."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ComponentCatalog:
    """
    Hold one immutable, versioned snapshot of registered component metadata.

    Attributes:
        schema_version: The core component-catalog schema version.
        citry_version: Installed Citry package version used for the snapshot.
        engine_id: Runtime identity of the inspected Citry instance.
        extension_versions: Requested extension metadata versions, sorted by name.
        components: Component records in canonical catalog order.

    """

    schema_version: int
    citry_version: str
    engine_id: str
    extension_versions: tuple[ExtensionVersion, ...]
    components: tuple[ComponentInfo, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != _SCHEMA_VERSION:
            msg = f"ComponentCatalog.schema_version must be {_SCHEMA_VERSION}."
            raise ValueError(msg)
        _require_exact_str(self.citry_version, "ComponentCatalog.citry_version")
        _require_exact_str(self.engine_id, "ComponentCatalog.engine_id")
        _require_tuple(self.extension_versions, "ComponentCatalog.extension_versions")
        _require_tuple(self.components, "ComponentCatalog.components")
        if any(type(entry) is not ExtensionVersion for entry in self.extension_versions):
            msg = "ComponentCatalog.extension_versions must contain ExtensionVersion values."
            raise TypeError(msg)
        version_names = tuple(entry.name for entry in self.extension_versions)
        if tuple(sorted(set(version_names))) != version_names:
            msg = "ComponentCatalog.extension_versions must be unique and sorted by name."
            raise ValueError(msg)
        if any(type(component) is not ComponentInfo for component in self.components):
            msg = "ComponentCatalog.components must contain ComponentInfo values."
            raise TypeError(msg)
        if any(component.engine_id != self.engine_id for component in self.components):
            msg = "Every component in a catalog must belong to the catalog's engine."
            raise ValueError(msg)
        class_ids = tuple(component.class_id for component in self.components)
        definition_ids = tuple(component.definition_id for component in self.components)
        registered_names = tuple(
            registered_name
            for component in self.components
            for registered_name in (component.name, *component.aliases)
        )
        if len(class_ids) != len(set(class_ids)):
            msg = "ComponentCatalog component class IDs must be unique."
            raise ValueError(msg)
        if len(definition_ids) != len(set(definition_ids)):
            msg = "ComponentCatalog component definition IDs must be unique."
            raise ValueError(msg)
        if len(registered_names) != len(set(registered_names)):
            msg = "ComponentCatalog registration names must be unique across primary names and aliases."
            raise ValueError(msg)
        component_keys = tuple(
            (component.name, component.import_path or "", component.class_id) for component in self.components
        )
        if tuple(sorted(component_keys)) != component_keys or len(component_keys) != len(set(component_keys)):
            msg = "ComponentCatalog.components must be unique and in canonical order."
            raise ValueError(msg)
        versions = {entry.name: entry.introspection_version for entry in self.extension_versions}
        for component in self.components:
            for entry in component.extensions:
                if versions.get(entry.name) != entry.introspection_version:
                    msg = "Component extension entries must match the catalog extension-version envelope."
                    raise ValueError(msg)

    def to_dict(self) -> dict[str, object]:
        """
        Return a fresh JSON-ready dictionary for this catalog.

        Returns:
            A new nested tree of ordinary dictionaries, lists, and JSON scalar
            values. Mutating it does not change the frozen catalog.

        """
        return {
            "schema_version": self.schema_version,
            "citry_version": self.citry_version,
            "engine_id": self.engine_id,
            "extension_versions": {entry.name: entry.introspection_version for entry in self.extension_versions},
            "components": [_component_to_dict(component) for component in self.components],
        }

    def to_json(self, indent: int | None = None) -> str:
        """
        Serialize this catalog to deterministic UTF-8 JSON text.

        Args:
            indent: Optional non-negative indentation width. ``None`` emits
                compact JSON.

        Returns:
            Deterministic JSON with recursively sorted object keys and Unicode
            characters left unescaped.

        Raises:
            TypeError: If ``indent`` is not an integer or ``None``.
            ValueError: If ``indent`` is negative.

        """
        if indent is not None and type(indent) is not int:
            msg = "ComponentCatalog.to_json() indent must be an integer or None."
            raise TypeError(msg)
        if indent is not None and indent < 0:
            msg = "ComponentCatalog.to_json() indent cannot be negative."
            raise ValueError(msg)
        if indent is None:
            return json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=indent,
        )


def _schema_to_dict(schema: SchemaInfo) -> dict[str, object]:
    return {
        "kind": schema.kind,
        "declared_on": schema.declared_on,
        "import_path": schema.import_path,
        "fields": [
            {
                "name": field.name,
                "required": field.required,
                "type_display": field.type_display,
                "type_fidelity": field.type_fidelity,
                "default_kind": field.default_kind,
                "default_value_state": field.default_value_state,
                "default_value": _thaw_json_value(field.default_value),
                "description": field.description,
                "source_module": field.source_module,
                "source_qualname": field.source_qualname,
                "source_file": field.source_file.as_posix() if field.source_file is not None else None,
            }
            for field in schema.fields
        ],
    }


def _asset_to_dict(asset: AssetInfo) -> dict[str, object]:
    return {
        "kind": asset.kind,
        "declared_on": asset.declared_on,
        "owner_file": asset.owner_file.as_posix() if asset.owner_file is not None else None,
        "owner_module": asset.owner_module,
        "owner_qualname": asset.owner_qualname,
        "declared_path": asset.declared_path,
        "resolution": asset.resolution,
        "resolved_path": asset.resolved_path.as_posix() if asset.resolved_path is not None else None,
        "searched_paths": [path.as_posix() for path in asset.searched_paths],
    }


def _component_to_dict(component: ComponentInfo) -> dict[str, object]:
    return {
        "class_id": component.class_id,
        "engine_id": component.engine_id,
        "definition_id": component.definition_id,
        "name": component.name,
        "aliases": list(component.aliases),
        "class_name": component.class_name,
        "module": component.module,
        "qualname": component.qualname,
        "import_path": component.import_path,
        "python_file": component.python_file.as_posix() if component.python_file is not None else None,
        "description": component.description,
        "transparent": component.transparent,
        "builtin": component.builtin,
        "schemas": {
            "kwargs": _schema_to_dict(component.schemas.kwargs),
            "slots": _schema_to_dict(component.schemas.slots),
            "template_data": _schema_to_dict(component.schemas.template_data),
            "js_data": _schema_to_dict(component.schemas.js_data),
            "css_data": _schema_to_dict(component.schemas.css_data),
        },
        "assets": {
            "template": _asset_to_dict(component.assets.template),
            "js": _asset_to_dict(component.assets.js),
            "css": _asset_to_dict(component.assets.css),
        },
        "extensions": {
            entry.name: {
                "introspection_version": entry.introspection_version,
                "data": _thaw_json_value(entry.data),
            }
            for entry in component.extensions
        },
    }


__all__ = [
    "AssetInfo",
    "ComponentAssets",
    "ComponentCatalog",
    "ComponentExtensionInfo",
    "ComponentInfo",
    "ComponentIntrospectionError",
    "ComponentSchemas",
    "ExtensionVersion",
    "FieldInfo",
    "FrozenJsonObject",
    "FrozenJsonValue",
    "SchemaInfo",
]
