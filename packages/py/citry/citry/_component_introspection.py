"""Build value-only snapshots of registered component declarations."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from inspect import cleandoc
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

from citry._class_introspection import (
    _safe_class_import_path,
    _safe_class_text,
    _static_class_dict,
    _static_class_mro,
)
from citry._schema_introspection import _inspect_component_schemas
from citry.assets import ASSET_PAIRS, _find_pair_declaration, _inspect_asset_path
from citry.component_registry import _pascal_to_kebab
from citry.introspection import AssetInfo, ComponentAssets, ComponentCatalog, ComponentInfo, _is_utf8_string

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component
    from citry.extension import _ComponentInspector

_PATH_TYPE = type(Path())


def _installed_citry_version() -> str:
    """Return the installed package version used in a catalog envelope."""
    try:
        return version("citry")
    except PackageNotFoundError:
        return "unknown"


def _loaded_python_file(cls: type) -> Path | None:
    """Read a class's already-loaded module path without importing anything."""
    module_name = _safe_class_text(cls, "__module__")
    if module_name is None:
        return None
    module = sys.modules.get(module_name)
    if type(module) is not ModuleType:
        return None
    module_file = module.__dict__.get("__file__")
    if (
        type(module_file) is not str
        or not module_file
        or (module_file.startswith("<") and module_file.endswith(">"))
        or not _is_utf8_string(module_file)
    ):
        return None
    path = Path(module_file)
    return path if path.is_absolute() else path.absolute()


def _own_description(cls: type) -> str | None:
    """Return the class's own cleaned docstring without inheriting prose."""
    raw = _static_class_dict(cls).get("__doc__")
    if type(raw) is not str or not _is_utf8_string(raw):
        return None
    cleaned = cleandoc(raw)
    return cleaned or None


def _effective_raw_attribute(cls: type, name: str, *, default: object = None) -> object:
    for candidate in _static_class_mro(cls):
        namespace = _static_class_dict(candidate)
        if name in namespace:
            return namespace[name]
    return default


def _declared_path_text(value: object, *, class_name: str, field_name: str) -> str:
    if type(value) is str:
        return cast("str", value)
    if type(value) is _PATH_TYPE:
        return cast("Path", value).as_posix()
    msg = f"{class_name}.{field_name} must be a string or concrete pathlib.Path for introspection."
    raise TypeError(msg)


def _inspect_asset(
    comp_cls: type[Component],
    engine: Citry,
    inline_attr: str,
    file_attr: str,
    *,
    resolve_assets: bool,
) -> AssetInfo:
    owner, inline_value, file_value = _find_pair_declaration(comp_cls, inline_attr, file_attr)
    framework_default = _static_class_dict(owner).get("_citry_component_root", False) is True
    declared_on = None if framework_default else _safe_class_import_path(owner)
    owner_file = None if framework_default else _loaded_python_file(owner)
    owner_module = None if framework_default else _safe_class_text(owner, "__module__")
    owner_qualname = None if framework_default else _safe_class_text(owner, "__qualname__")

    if inline_value is None and file_value is None:
        return AssetInfo(
            kind="none",
            declared_on=declared_on,
            owner_file=owner_file,
            declared_path=None,
            resolution="not-applicable",
            resolved_path=None,
            searched_paths=(),
            owner_module=owner_module,
            owner_qualname=owner_qualname,
        )

    if declared_on is None:
        msg = f"Could not determine declaration provenance for {inline_attr}/{file_attr}."
        raise TypeError(msg)
    if inline_value is not None:
        return AssetInfo(
            kind="inline",
            declared_on=declared_on,
            owner_file=owner_file,
            declared_path=None,
            resolution="not-applicable",
            resolved_path=None,
            searched_paths=(),
            owner_module=owner_module,
            owner_qualname=owner_qualname,
        )

    class_name = _safe_class_text(owner, "__name__") or "Component"
    declared_path = _declared_path_text(file_value, class_name=class_name, field_name=file_attr)
    if not resolve_assets:
        return AssetInfo(
            kind="file",
            declared_on=declared_on,
            owner_file=owner_file,
            declared_path=declared_path,
            resolution="not-requested",
            resolved_path=None,
            searched_paths=(),
            owner_module=owner_module,
            owner_qualname=owner_qualname,
        )

    path_state = _inspect_asset_path(
        cast("str | Path", file_value),
        owner_dir=owner_file.parent if owner_file is not None else None,
        search_dirs=engine.settings.dirs,
    )
    return AssetInfo(
        kind="file",
        declared_on=declared_on,
        owner_file=owner_file,
        declared_path=declared_path,
        resolution=path_state.resolution,
        resolved_path=path_state.resolved_path,
        searched_paths=path_state.searched_paths,
        owner_module=owner_module,
        owner_qualname=owner_qualname,
    )


def _inspect_component_assets(
    comp_cls: type[Component],
    engine: Citry,
    *,
    resolve_assets: bool,
) -> ComponentAssets:
    assets = {
        inline_attr: _inspect_asset(
            comp_cls,
            engine,
            inline_attr,
            file_attr,
            resolve_assets=resolve_assets,
        )
        for inline_attr, file_attr in ASSET_PAIRS
    }
    return ComponentAssets(
        template=assets["template"],
        messages=assets["messages"],
        js=assets["js"],
        css=assets["css"],
    )


def _primary_name(comp_cls: type[Component], names: tuple[str, ...]) -> str:
    explicit_name = _effective_raw_attribute(comp_cls, "name")
    if type(explicit_name) is str:
        normalized_explicit = explicit_name.lower()
        if normalized_explicit in names:
            return normalized_explicit
    class_name = _safe_class_text(comp_cls, "__name__")
    if class_name is not None:
        derived_name = _pascal_to_kebab(class_name)
        if derived_name in names:
            return derived_name
    return names[0]


def _build_component_info(
    engine: Citry,
    comp_cls: type[Component],
    names: tuple[str, ...],
    *,
    builtin: bool,
    resolve_assets: bool,
    include_default_values: bool,
) -> ComponentInfo:
    """Build one record from a class generation and its copied names."""
    primary_name = _primary_name(comp_cls, names)
    aliases = tuple(name for name in names if name != primary_name)
    module = _safe_class_text(comp_cls, "__module__")
    qualname = _safe_class_text(comp_cls, "__qualname__")
    import_path = _safe_class_import_path(comp_cls)
    namespace = _static_class_dict(comp_cls)
    class_id = namespace.get("_class_id")
    definition_id = namespace.get("_definition_id")
    transparent = _effective_raw_attribute(comp_cls, "transparent", default=False)
    return ComponentInfo(
        class_id=cast("str", class_id),
        engine_id=engine.engine_id,
        definition_id=cast("str", definition_id),
        name=primary_name,
        aliases=aliases,
        class_name=_safe_class_text(comp_cls, "__name__"),
        module=module,
        qualname=qualname,
        import_path=import_path,
        python_file=_loaded_python_file(comp_cls),
        description=_own_description(comp_cls),
        transparent=cast("bool", transparent),
        builtin=builtin,
        schemas=_inspect_component_schemas(comp_cls, include_default_values=include_default_values),
        assets=_inspect_component_assets(comp_cls, engine, resolve_assets=resolve_assets),
        extensions=(),
    )


def _group_registrations(
    registrations: Mapping[str, type[Component]],
) -> tuple[tuple[type[Component], tuple[str, ...]], ...]:
    """Group copied registry names by exact class identity without hashing classes."""
    groups: dict[int, tuple[type[Component], list[str]]] = {}
    for name, comp_cls in registrations.items():
        identity = id(comp_cls)
        group = groups.get(identity)
        if group is None:
            groups[identity] = (comp_cls, [name])
        else:
            group[1].append(name)
    return tuple((comp_cls, tuple(sorted(names))) for comp_cls, names in groups.values())


def _build_component_catalog(
    engine: Citry,
    registrations: Mapping[str, type[Component]],
    *,
    include_builtins: bool,
    resolve_assets: bool,
    include_default_values: bool,
    inspectors: tuple[_ComponentInspector, ...],
) -> ComponentCatalog:
    """Build one canonical catalog from an already-copied registry snapshot."""
    core_records = [
        (
            comp_cls,
            _build_component_info(
                engine,
                comp_cls,
                names,
                builtin=engine._is_builtin_component(comp_cls),
                resolve_assets=resolve_assets,
                include_default_values=include_default_values,
            ),
        )
        for comp_cls, names in _group_registrations(registrations)
        if include_builtins or not engine._is_builtin_component(comp_cls)
    ]
    core_records.sort(key=lambda item: (item[1].name, item[1].import_path or "", item[1].class_id))
    components = tuple(
        engine.extensions._inspect_component_extensions(comp_cls, info, inspectors) for comp_cls, info in core_records
    )
    return ComponentCatalog(
        schema_version=1,
        citry_version=_installed_citry_version(),
        engine_id=engine.engine_id,
        extension_versions=engine.extensions._component_introspection_versions(inspectors),
        components=components,
    )


__all__: list[str] = []
