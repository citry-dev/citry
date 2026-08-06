"""Validated, lossless component catalog records used by editor features."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast
from urllib.parse import unquote, urlparse

from citry_lsp.protocol import CATALOG_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class FieldRecord:
    """One effective schema field, including optional authoring provenance."""

    name: str
    required: bool
    type_display: str | None
    type_fidelity: str
    default_kind: str
    default_value_state: str
    default_value: object
    description: str | None
    source_module: str | None
    source_qualname: str | None
    source_file: Path | None


@dataclass(frozen=True, slots=True)
class SchemaRecord:
    """One absent, field-shaped, or opaque component schema."""

    kind: str
    declared_on: str | None
    import_path: str | None
    fields: tuple[FieldRecord, ...]


@dataclass(frozen=True, slots=True)
class ComponentSchemasRecord:
    """All five effective typed component interfaces."""

    kwargs: SchemaRecord
    slots: SchemaRecord
    template_data: SchemaRecord
    js_data: SchemaRecord
    css_data: SchemaRecord


@dataclass(frozen=True, slots=True)
class AssetRecord:
    """One inline, file-backed, or absent component asset declaration."""

    kind: str
    declared_on: str | None
    owner_file: Path | None
    owner_module: str | None
    owner_qualname: str | None
    declared_path: str | None
    resolution: str
    resolved_path: Path | None
    searched_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class ComponentAssetsRecord:
    """The effective template, JavaScript, and CSS assets."""

    template: AssetRecord
    js: AssetRecord
    css: AssetRecord


@dataclass(frozen=True, slots=True)
class ComponentRecord:
    """One complete runtime component catalog record."""

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
    schemas: ComponentSchemasRecord
    assets: ComponentAssetsRecord
    extensions: Mapping[str, Mapping[str, object]]

    @property
    def kwargs(self) -> tuple[FieldRecord, ...]:
        """Compatibility view used by component-input tooling."""
        return self.schemas.kwargs.fields

    @property
    def slots(self) -> tuple[FieldRecord, ...]:
        """Compatibility view used by slot tooling."""
        return self.schemas.slots.fields

    @property
    def template_file(self) -> Path | None:
        """Compatibility view used by standalone-template association."""
        return self.assets.template.resolved_path

    @property
    def js_file(self) -> Path | None:
        return self.assets.js.resolved_path

    @property
    def css_file(self) -> Path | None:
        return self.assets.css.resolved_path

    @property
    def registered_names(self) -> tuple[str, ...]:
        """Return the primary name followed by aliases."""
        return (self.name, *self.aliases)


class CatalogIndex:
    """Index a validated worker catalog by name and resolved asset ownership."""

    __slots__ = (
        "_asset_owners",
        "_by_name",
        "citry_version",
        "components",
        "engine_id",
        "extension_versions",
        "schema_version",
    )

    def __init__(self, payload: object) -> None:
        if type(payload) is not dict:
            msg = "component catalog must be a dict"
            raise ValueError(msg)
        schema_version = payload.get("schema_version")
        citry_version = payload.get("citry_version")
        engine_id = payload.get("engine_id")
        extension_versions = payload.get("extension_versions")
        raw_components = payload.get("components")
        if (
            schema_version != CATALOG_SCHEMA_VERSION
            or type(schema_version) is not int
            or type(raw_components) is not list
        ):
            msg = "component catalog envelope is invalid"
            raise ValueError(msg)
        citry_version = _required_str(citry_version, "citry_version")
        engine_id = _required_str(engine_id, "engine_id")
        validated_extension_versions = _extension_versions(extension_versions)

        components = tuple(_component_record(item) for item in raw_components)
        class_ids = tuple(component.class_id for component in components)
        definition_ids = tuple(component.definition_id for component in components)
        component_keys = tuple(
            (component.name, component.import_path or "", component.class_id) for component in components
        )
        if len(class_ids) != len(set(class_ids)) or len(definition_ids) != len(set(definition_ids)):
            msg = "component catalog class and definition ids must be unique"
            raise ValueError(msg)
        if component_keys != tuple(sorted(component_keys)) or len(component_keys) != len(set(component_keys)):
            msg = "component catalog entries are not in canonical order"
            raise ValueError(msg)
        by_name: dict[str, ComponentRecord] = {}
        for component in components:
            if component.engine_id != engine_id:
                msg = f"component {component.name!r} engine id does not match its catalog"
                raise ValueError(msg)
            for name in component.registered_names:
                normalized = name.lower()
                if normalized in by_name:
                    msg = f"duplicate registered component name {name!r}"
                    raise ValueError(msg)
                by_name[normalized] = component
            for extension_name, extension in component.extensions.items():
                if validated_extension_versions.get(extension_name) != extension["introspection_version"]:
                    msg = f"component {component.name!r} extension versions do not match the catalog"
                    raise ValueError(msg)

        asset_owners: dict[tuple[str, Path], list[ComponentRecord]] = {}
        for component in components:
            for kind in ("template", "js", "css"):
                asset = getattr(component.assets, kind)
                if asset.resolved_path is None:
                    continue
                asset_owners.setdefault((kind, asset.resolved_path.resolve()), []).append(component)

        self.schema_version = schema_version
        self.citry_version = citry_version
        self.engine_id = engine_id
        self.extension_versions = validated_extension_versions
        self.components = components
        self._by_name = by_name
        self._asset_owners = {key: tuple(value) for key, value in asset_owners.items()}

    def get(self, tag_name: str) -> ComponentRecord | None:
        """Resolve a bare registered name, with tag spelling as a fallback."""
        normalized = tag_name.lower()
        component = self._by_name.get(normalized)
        if component is not None or not tag_name.startswith("c-"):
            return component
        return self._by_name.get(normalized.removeprefix("c-"))

    def get_tag(self, tag_name: str) -> ComponentRecord | None:
        """Resolve an exact-prefix ``<c-*>`` tag with a case-insensitive suffix."""
        if not tag_name.startswith("c-"):
            return None
        return self._by_name.get(tag_name[2:].lower())

    def names(self) -> tuple[str, ...]:
        """Return all registered names in stable order."""
        return tuple(sorted(self._by_name))

    def asset_owners(self, uri: str, kind: str) -> tuple[ComponentRecord, ...]:
        """Return every component whose resolved asset of ``kind`` owns ``uri``."""
        path = _file_uri_path(uri)
        if path is None or kind not in {"template", "js", "css"}:
            return ()
        return self._asset_owners.get((kind, path.resolve()), ())

    def inline_asset_consumers(
        self,
        uri: str,
        kind: str,
        component_qualname: str,
    ) -> tuple[ComponentRecord, ...]:
        """Return consumers of one AST-proven inline asset declaration."""
        path = _file_uri_path(uri)
        if path is None or kind not in {"template", "js", "css"}:
            return ()
        canonical = path.resolve()

        # Structured owner provenance identifies the physical class-body
        # declaration even when that base or LibraryComponent is not itself a
        # registered catalog entry.
        return tuple(
            component
            for component in self.components
            if (asset := getattr(component.assets, kind)).kind == "inline"
            and asset.owner_qualname == component_qualname
            and asset.owner_file is not None
            and asset.owner_file.resolve() == canonical
        )

    def owns_template_uri(self, uri: str) -> bool:
        """Return whether a file URI is any resolved registered template asset."""
        return bool(self.asset_owners(uri, "template"))


def _component_record(value: object) -> ComponentRecord:
    if type(value) is not dict:
        msg = "component catalog entries must be dicts"
        raise ValueError(msg)
    name = _required_str(value.get("name"), "component name")
    aliases = value.get("aliases")
    schemas = value.get("schemas")
    assets = value.get("assets")
    if (
        type(aliases) is not list
        or any(type(alias) is not str or not alias for alias in aliases)
        or len(aliases) != len(set(aliases))
    ):
        msg = f"component {name!r} aliases are invalid"
        raise ValueError(msg)
    if tuple(aliases) != tuple(sorted(set(aliases))) or name in aliases:
        msg = f"component {name!r} aliases must be sorted and exclude its primary name"
        raise ValueError(msg)
    if type(schemas) is not dict:
        msg = f"component {name!r} schemas are invalid"
        raise ValueError(msg)
    if type(assets) is not dict:
        msg = f"component {name!r} assets are invalid"
        raise ValueError(msg)
    return ComponentRecord(
        class_id=_required_str(value.get("class_id"), "class_id"),
        engine_id=_required_str(value.get("engine_id"), "engine_id"),
        definition_id=_required_str(value.get("definition_id"), "definition_id"),
        name=name,
        aliases=tuple(aliases),
        class_name=_optional_str(value.get("class_name"), "class_name"),
        module=_optional_str(value.get("module"), "module"),
        qualname=_optional_str(value.get("qualname"), "qualname"),
        import_path=_optional_str(value.get("import_path"), "import_path"),
        python_file=_optional_path(value.get("python_file"), "python_file"),
        description=_optional_str(value.get("description"), "description"),
        transparent=_required_bool(value.get("transparent"), "transparent"),
        builtin=_required_bool(value.get("builtin"), "builtin"),
        schemas=ComponentSchemasRecord(
            kwargs=_schema_record(schemas.get("kwargs"), name, "kwargs"),
            slots=_schema_record(schemas.get("slots"), name, "slots"),
            template_data=_schema_record(schemas.get("template_data"), name, "template_data"),
            js_data=_schema_record(schemas.get("js_data"), name, "js_data"),
            css_data=_schema_record(schemas.get("css_data"), name, "css_data"),
        ),
        assets=ComponentAssetsRecord(
            template=_asset_record(assets.get("template"), name, "template"),
            js=_asset_record(assets.get("js"), name, "js"),
            css=_asset_record(assets.get("css"), name, "css"),
        ),
        extensions=_extensions(value.get("extensions"), name),
    )


def _schema_record(value: object, component: str, role: str) -> SchemaRecord:
    if type(value) is not dict or type(value.get("fields")) is not list:
        msg = f"component {component!r} {role} schema is invalid"
        raise ValueError(msg)
    kind = value.get("kind")
    if kind not in {"absent", "fields", "opaque"}:
        msg = f"component {component!r} {role} schema kind is invalid"
        raise ValueError(msg)
    declared_on = _optional_nonempty_str(value.get("declared_on"), "declared_on")
    import_path = _optional_nonempty_str(value.get("import_path"), "import_path")
    fields = tuple(_field_record(raw, component, role) for raw in value["fields"])
    if len(fields) != len({field.name for field in fields}):
        msg = f"component {component!r} {role} schema field names are not unique"
        raise ValueError(msg)
    if kind == "absent" and (import_path is not None or fields):
        msg = f"component {component!r} {role} absent schema has field state"
        raise ValueError(msg)
    if kind in {"fields", "opaque"} and (declared_on is None or import_path is None):
        msg = f"component {component!r} {role} schema provenance is invalid"
        raise ValueError(msg)
    if kind == "opaque" and fields:
        msg = f"component {component!r} {role} opaque schema has fields"
        raise ValueError(msg)
    return SchemaRecord(
        kind=kind,
        declared_on=declared_on,
        import_path=import_path,
        fields=fields,
    )


def _schema_fields(value: object, component: str, role: str) -> tuple[FieldRecord, ...]:
    """Compatibility helper retained for focused catalog validation tests."""
    return _schema_record(value, component, role).fields


def _field_record(value: object, component: str, role: str) -> FieldRecord:
    if type(value) is not dict or type(value.get("required")) is not bool:
        msg = f"component {component!r} {role} field is invalid"
        raise ValueError(msg)
    type_fidelity = value.get("type_fidelity")
    default_kind = value.get("default_kind")
    default_value_state = value.get("default_value_state")
    if type_fidelity not in {"normalized", "unavailable"}:
        msg = f"component {component!r} {role} field type fidelity is invalid"
        raise ValueError(msg)
    if default_kind not in {"missing", "value", "factory"}:
        msg = f"component {component!r} {role} field default kind is invalid"
        raise ValueError(msg)
    if default_value_state not in {"not-applicable", "omitted", "available", "unsupported"}:
        msg = f"component {component!r} {role} field default state is invalid"
        raise ValueError(msg)
    required = value["required"]
    type_display = _optional_nonempty_str(value.get("type_display"), "type_display")
    if (type_fidelity == "normalized") != (type_display is not None):
        msg = f"component {component!r} {role} field type state is invalid"
        raise ValueError(msg)
    if required != (default_kind == "missing"):
        msg = f"component {component!r} {role} field required/default state is invalid"
        raise ValueError(msg)
    default_value = value.get("default_value")
    if default_kind in {"missing", "factory"}:
        valid_default = default_value_state == "not-applicable" and default_value is None
    elif default_value_state == "available":
        valid_default = True
        default_value = _freeze_json(default_value, set())
    else:
        valid_default = default_value_state in {"omitted", "unsupported"} and default_value is None
    if not valid_default:
        msg = f"component {component!r} {role} field default value state is invalid"
        raise ValueError(msg)

    source_module = _optional_nonempty_str(value.get("source_module"), "source_module")
    source_qualname = _optional_nonempty_str(value.get("source_qualname"), "source_qualname")
    source_file = _optional_path(value.get("source_file"), "source_file")
    if (source_module is None) != (source_qualname is None) or (source_file is not None and source_module is None):
        msg = f"component {component!r} {role} field source provenance is invalid"
        raise ValueError(msg)
    return FieldRecord(
        name=_required_str(value.get("name"), "field name"),
        required=required,
        type_display=type_display,
        type_fidelity=type_fidelity,
        default_kind=default_kind,
        default_value_state=default_value_state,
        default_value=default_value,
        description=_optional_str(value.get("description"), "description"),
        source_module=source_module,
        source_qualname=source_qualname,
        source_file=source_file,
    )


def _asset_record(value: object, component: str, role: str) -> AssetRecord:
    if type(value) is not dict:
        msg = f"component {component!r} {role} asset is invalid"
        raise ValueError(msg)
    kind = value.get("kind")
    resolution = value.get("resolution")
    searched_paths = value.get("searched_paths")
    if (
        kind not in {"none", "inline", "file"}
        or resolution not in {"not-applicable", "not-requested", "resolved", "missing", "unavailable"}
        or type(searched_paths) is not list
    ):
        msg = f"component {component!r} {role} asset is invalid"
        raise ValueError(msg)
    declared_on = _optional_nonempty_str(value.get("declared_on"), "declared_on")
    owner_file = _optional_path(value.get("owner_file"), "owner_file")
    owner_module = _optional_nonempty_str(value.get("owner_module"), "owner_module")
    owner_qualname = _optional_nonempty_str(value.get("owner_qualname"), "owner_qualname")
    declared_path = _optional_nonempty_str(value.get("declared_path"), "declared_path")
    resolved_path = _optional_path(value.get("resolved_path"), "resolved_path")
    paths = tuple(_required_path(item, "searched path") for item in searched_paths)
    owner_identity_valid = (owner_module is None) == (owner_qualname is None) and (
        owner_module is None or declared_on == f"{owner_module}.{owner_qualname}"
    )
    if kind == "none":
        valid = (
            owner_identity_valid
            and not (declared_on is None and owner_module is not None)
            and resolution == "not-applicable"
            and declared_path is None
            and resolved_path is None
            and not paths
            and not (declared_on is None and owner_file is not None)
        )
    elif kind == "inline":
        valid = (
            owner_identity_valid
            and declared_on is not None
            and resolution == "not-applicable"
            and declared_path is None
            and resolved_path is None
            and not paths
        )
    elif not owner_identity_valid or declared_on is None or declared_path is None:
        valid = False
    elif resolution == "not-requested":
        valid = resolved_path is None and not paths
    elif resolution == "resolved":
        valid = resolved_path is not None and bool(paths) and resolved_path in paths
    elif resolution == "missing":
        valid = resolved_path is None and bool(paths)
    elif resolution == "unavailable":
        valid = owner_file is None and not Path(declared_path).is_absolute() and resolved_path is None and not paths
    else:
        valid = False
    if not valid:
        msg = f"component {component!r} {role} asset state is invalid"
        raise ValueError(msg)
    return AssetRecord(
        kind=kind,
        declared_on=declared_on,
        owner_file=owner_file,
        owner_module=owner_module,
        owner_qualname=owner_qualname,
        declared_path=declared_path,
        resolution=resolution,
        resolved_path=resolved_path,
        searched_paths=paths,
    )


def _file_uri_path(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme != "file" or parsed.netloc:
        return None
    return Path(unquote(parsed.path))


def _required_str(value: object, field_name: str) -> str:
    if type(value) is not str or not value:
        msg = f"{field_name} must be a non-empty string"
        raise ValueError(msg)
    _require_utf8(value, field_name)
    return value


def _optional_str(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        msg = f"{field_name} must be a string or None"
        raise ValueError(msg)
    _require_utf8(value, field_name)
    return value


def _optional_nonempty_str(value: object, field_name: str) -> str | None:
    return None if value is None else _required_str(value, field_name)


def _required_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        msg = f"{field_name} must be a bool"
        raise ValueError(msg)
    return value


def _optional_path(value: object, field_name: str) -> Path | None:
    return None if value is None else _required_path(value, field_name)


def _required_path(value: object, field_name: str) -> Path:
    if type(value) is not str:
        msg = f"{field_name} must be a path string"
        raise ValueError(msg)
    _require_utf8(value, field_name)
    path = Path(value)
    if not path.is_absolute():
        msg = f"{field_name} must be an absolute path string"
        raise ValueError(msg)
    return path


def _extension_versions(value: object) -> MappingProxyType[str, int]:
    if type(value) is not dict:
        msg = "component catalog extension versions are invalid"
        raise ValueError(msg)
    versions: dict[str, int] = {}
    for name, version in value.items():
        normalized_name = _required_str(name, "extension name")
        if type(version) is not int or version <= 0:
            msg = f"extension {normalized_name!r} version must be a positive integer"
            raise ValueError(msg)
        versions[normalized_name] = version
    if tuple(versions) != tuple(sorted(versions)):
        msg = "component catalog extension versions must be sorted by name"
        raise ValueError(msg)
    return MappingProxyType(versions)


def _extensions(value: object, component: str) -> MappingProxyType[str, Mapping[str, object]]:
    if type(value) is not dict:
        msg = f"component {component!r} extensions are invalid"
        raise ValueError(msg)
    extensions: dict[str, Mapping[str, object]] = {}
    for name, publication in value.items():
        extension_name = _required_str(name, "extension name")
        if type(publication) is not dict:
            msg = f"component {component!r} extension {extension_name!r} is invalid"
            raise ValueError(msg)
        version = publication.get("introspection_version")
        data = publication.get("data")
        if type(version) is not int or version <= 0 or type(data) is not dict:
            msg = f"component {component!r} extension {extension_name!r} is invalid"
            raise ValueError(msg)
        frozen = _freeze_json(publication, set())
        if not isinstance(frozen, Mapping):  # The exact-dict check above makes this defensive only.
            msg = f"component {component!r} extension {extension_name!r} is invalid"
            raise TypeError(msg)
        extensions[extension_name] = frozen
    if tuple(extensions) != tuple(sorted(extensions)):
        msg = f"component {component!r} extensions must be sorted by name"
        raise ValueError(msg)
    return MappingProxyType(extensions)


def _freeze_json(value: object, active: set[int]) -> object:
    """Validate and recursively freeze the exact JSON values from the worker."""
    value_type = type(value)
    if value is None or value_type is bool:
        return value
    if value_type is str:
        string_value = cast("str", value)
        _require_utf8(string_value, "catalog JSON string")
        return string_value
    if value_type is int:
        integer_value = cast("int", value)
        if not -(2**53 - 1) <= integer_value <= 2**53 - 1:
            msg = "catalog JSON integers must be within JavaScript's safe range"
            raise ValueError(msg)
        return integer_value
    if value_type is float:
        float_value = cast("float", value)
        if not math.isfinite(float_value):
            msg = "catalog JSON floats must be finite"
            raise ValueError(msg)
        return float_value
    if value_type not in {list, dict}:
        msg = "catalog values must contain only exact JSON types"
        raise ValueError(msg)
    identity = id(value)
    if identity in active:
        msg = "catalog JSON values cannot contain cycles"
        raise ValueError(msg)
    active.add(identity)
    try:
        if value_type is list:
            sequence = cast("list[object]", value)
            return tuple(_freeze_json(item, active) for item in sequence)
        raw_mapping = cast("dict[object, object]", value)
        if any(type(key) is not str for key in raw_mapping):
            msg = "catalog JSON object keys must be strings"
            raise ValueError(msg)
        mapping = cast("dict[str, object]", raw_mapping)
        for key in mapping:
            _require_utf8(key, "catalog JSON object key")
        return MappingProxyType({key: _freeze_json(item, active) for key, item in mapping.items()})
    finally:
        active.remove(identity)


def _require_utf8(value: str, field_name: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        msg = f"{field_name} must not contain unpaired Unicode surrogates"
        raise ValueError(msg) from exc


__all__ = [
    "AssetRecord",
    "CatalogIndex",
    "ComponentAssetsRecord",
    "ComponentRecord",
    "ComponentSchemasRecord",
    "FieldRecord",
    "SchemaRecord",
]
