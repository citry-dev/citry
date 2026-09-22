"""Generic extension contributions to one prepared browser render."""

from __future__ import annotations

import json
import math
import re
from copy import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypeVar, cast

from citry.ext.dependencies.types import Script, Style

DependencyT = TypeVar("DependencyT", Script, Style)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry._vue.prepared import PreparedViewMetadata
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.citry_render import CitryRender


@dataclass(frozen=True, slots=True)
class OnBrowserRenderPrepareContext:
    """Read-only inputs for one extension's prepared-browser projection."""

    citry: Citry
    context: CitryContext
    selected_render: CitryRender
    view: PreparedViewMetadata
    render_to_occurrence: Mapping[str, str]
    app_id: str
    revision: int
    base_revision: int | None


@dataclass(frozen=True, slots=True)
class BrowserPluginDescriptor:
    """Fixed client plugin identity and capabilities installed before mount."""

    schema_version: int
    script: Script
    allows_late_component_assets: bool = False
    template_context_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BrowserRenderContribution:
    """One extension's detached payload and immutable render assets."""

    schema_version: int
    payload: dict[str, object]
    scripts: tuple[Script, ...] = ()
    styles: tuple[Style, ...] = ()


@dataclass(frozen=True, slots=True)
class PreparedBrowserExtension:
    """Validated name-keyed extension data ready for wire encoding."""

    name: str
    schema_version: int
    payload: dict[str, object]
    scripts: tuple[Script, ...]
    styles: tuple[Style, ...]
    plugin: BrowserPluginDescriptor
    _source_assets: tuple[Script | Style, ...] = ()
    _source_asset_states: tuple[tuple[object, ...], ...] = ()
    _registration: BrowserPluginRegistration | None = None
    _citry: Citry | None = None

    def validate(self) -> None:
        if tuple(_dependency_state(value) for value in self._source_assets) != self._source_asset_states:
            raise RuntimeError(f"Extension {self.name!r} browser contribution assets changed during preparation.")
        if self._registration is not None and self._citry is not None:
            _validate_registration(self._registration, self._citry)


@dataclass(frozen=True, slots=True)
class BrowserPluginRegistration:
    """One extension and its browser plugin descriptor, captured once."""

    extension: Any
    name: str
    plugin: BrowserPluginDescriptor | None
    original_plugin: BrowserPluginDescriptor | None
    original_script_state: tuple[object, ...] | None
    registry_state: tuple[tuple[Any, str], ...]


def collect_browser_plugin_descriptors(citry: Citry) -> tuple[BrowserPluginRegistration, ...]:
    """Capture and validate browser plugin descriptors before view assembly."""
    registrations: list[BrowserPluginRegistration] = []
    claimed_context_names: dict[str, str] = {}
    plugin_extensions = set(citry.extensions._extensions_with_hook("browser_plugin"))
    contribution_extensions = set(citry.extensions._extensions_with_hook("prepare_browser_render"))
    registry_state = tuple((extension, extension.name) for extension in citry.extensions._extensions)
    for extension in citry.extensions._extensions:
        if extension not in plugin_extensions and extension not in contribution_extensions:
            continue
        if type(extension.name) is not str or re.fullmatch(r"[a-z][a-z0-9_]*", extension.name) is None:
            raise TypeError("Browser extension name must match [a-z][a-z0-9_]*.")
        plugin = extension.browser_plugin()
        if plugin is not None and type(plugin) is not BrowserPluginDescriptor:
            raise TypeError(
                f"Extension {extension.name!r} browser_plugin() must return BrowserPluginDescriptor or None."
            )
        if plugin is not None:
            _validate_plugin(plugin, extension.name)
            for context_name in plugin.template_context_names:
                prior = claimed_context_names.setdefault(context_name, extension.name)
                if prior != extension.name:
                    raise ValueError(
                        f"Browser template context name {context_name!r} is claimed by both {prior!r} "
                        f"and {extension.name!r}."
                    )
        detached_plugin = None if plugin is None else _detach_plugin(plugin)
        registrations.append(
            BrowserPluginRegistration(
                extension,
                extension.name,
                detached_plugin,
                plugin,
                None if plugin is None else _script_state(plugin.script),
                registry_state,
            )
        )
    return tuple(registrations)


def prepare_browser_extensions(
    *,
    citry: Citry,
    context: CitryContext,
    selected_render: CitryRender,
    view: PreparedViewMetadata,
    render_to_occurrence: Mapping[str, str],
    app_id: str,
    revision: int,
    base_revision: int | None,
    registrations: tuple[BrowserPluginRegistration, ...] | None = None,
) -> tuple[PreparedBrowserExtension, ...]:
    """Collect and detach every installed extension's browser contribution."""
    mapping = MappingProxyType(dict(render_to_occurrence))
    hook_context = OnBrowserRenderPrepareContext(
        citry=citry,
        context=context,
        selected_render=selected_render,
        view=view,
        render_to_occurrence=mapping,
        app_id=app_id,
        revision=revision,
        base_revision=base_revision,
    )
    prepared: list[PreparedBrowserExtension] = []
    captured = collect_browser_plugin_descriptors(citry) if registrations is None else registrations
    for registration in captured:
        extension = registration.extension
        contribution = extension.prepare_browser_render(hook_context)
        if contribution is None:
            if registration.plugin is None:
                continue
            contribution = BrowserRenderContribution(registration.plugin.schema_version, {})
        if type(contribution) is not BrowserRenderContribution:
            raise TypeError(
                f"Extension {extension.name!r} must return BrowserRenderContribution or None "
                "from prepare_browser_render()."
            )
        if extension.name != registration.name:
            raise RuntimeError("Browser extension name changed during render preparation.")
        plugin = registration.plugin
        if type(plugin) is not BrowserPluginDescriptor:
            raise TypeError(f"Extension {extension.name!r} contributed browser data without a browser plugin.")
        _validate_version(contribution.schema_version, extension.name, "contribution")
        _validate_version(plugin.schema_version, extension.name, "plugin")
        if contribution.schema_version != plugin.schema_version:
            raise ValueError(f"Extension {extension.name!r} browser schema versions do not match.")
        if type(contribution.payload) is not dict:
            raise TypeError(f"Extension {extension.name!r} browser payload must be an exact dict.")
        _validate_json(contribution.payload, f"Extension {extension.name!r} browser payload")
        payload = json.loads(json.dumps(contribution.payload, allow_nan=False))
        if type(payload) is not dict:
            raise TypeError(f"Extension {extension.name!r} browser payload must be a JSON object.")
        source_scripts = _dependencies(contribution.scripts, Script, extension.name, "script")
        source_styles = _dependencies(contribution.styles, Style, extension.name, "style")
        for source_script in source_scripts:
            _validate_dependency_snapshot(source_script, extension.name)
        for source_style in source_styles:
            _validate_dependency_snapshot(source_style, extension.name)
        scripts = tuple(_detach_dependency(value) for value in source_scripts)
        styles = tuple(_detach_dependency(value) for value in source_styles)
        _validate_plugin(plugin, extension.name)
        if (
            registration.original_plugin is None
            or registration.original_script_state != _script_state(registration.original_plugin.script)
            or registration.original_plugin.schema_version != plugin.schema_version
            or registration.original_plugin.allows_late_component_assets != plugin.allows_late_component_assets
            or registration.original_plugin.template_context_names != plugin.template_context_names
        ):
            raise RuntimeError(
                f"Extension {registration.name!r} browser plugin descriptor changed during preparation."
            )
        source_assets: tuple[Script | Style, ...] = (*source_scripts, *source_styles)
        prepared.append(
            PreparedBrowserExtension(
                name=registration.name,
                schema_version=contribution.schema_version,
                payload=cast("dict[str, object]", payload),
                scripts=scripts,
                styles=styles,
                plugin=plugin,
                _source_assets=source_assets,
                _source_asset_states=tuple(_dependency_state(value) for value in source_assets),
                _registration=registration,
                _citry=citry,
            )
        )
    if dict(render_to_occurrence) != dict(mapping):
        raise RuntimeError("The prepared render occurrence mapping changed during extension preparation.")
    for registration in captured:
        _validate_registration(registration, citry)
    return tuple(sorted(prepared, key=lambda item: item.name))


def _validate_registration(registration: BrowserPluginRegistration, citry: Citry) -> None:
    current = tuple(citry.extensions._extensions)
    if len(current) != len(registration.registry_state) or any(
        extension is not expected or extension.name != name
        for extension, (expected, name) in zip(current, registration.registry_state, strict=True)
    ):
        raise RuntimeError("Browser extension registry changed during render preparation.")
    plugin = registration.original_plugin
    if plugin is not None and (
        registration.plugin is None
        or registration.original_script_state != _script_state(plugin.script)
        or plugin.schema_version != registration.plugin.schema_version
        or plugin.allows_late_component_assets != registration.plugin.allows_late_component_assets
        or plugin.template_context_names != registration.plugin.template_context_names
    ):
        raise RuntimeError(f"Extension {registration.name!r} browser plugin descriptor changed during preparation.")


def validate_browser_plugin_registrations(citry: Citry, registrations: tuple[BrowserPluginRegistration, ...]) -> None:
    """Recheck the captured registry and descriptors at the final publication boundary."""
    for registration in registrations:
        _validate_registration(registration, citry)


_TEMPLATE_CONTEXT_NAME = re.compile(r"\$[A-Za-z][A-Za-z0-9_]*\Z")
_RESERVED_TEMPLATE_CONTEXT_NAMES = frozenset(
    {
        "$attrs",
        "$citryEvents",
        "$data",
        "$el",
        "$emit",
        "$error",
        "$event",
        "$forceUpdate",
        "$loading",
        "$nextTick",
        "$options",
        "$parent",
        "$props",
        "$refs",
        "$root",
        "$sendEvent",
        "$slots",
        "$state",
        "$watch",
    }
)


def _validate_plugin(plugin: BrowserPluginDescriptor, extension_name: str) -> None:
    _validate_version(plugin.schema_version, extension_name, "plugin")
    if type(plugin.script) is not Script:
        raise TypeError(f"Extension {extension_name!r} browser plugin script must be an exact Script.")
    _validate_dependency_snapshot(plugin.script, extension_name)
    if type(plugin.allows_late_component_assets) is not bool:
        raise TypeError(f"Extension {extension_name!r} late component asset policy must be an exact bool.")
    _validate_template_context_names(plugin.template_context_names, f"Extension {extension_name!r}")


def _validate_template_context_names(names: object, label: str) -> None:
    if type(names) is not tuple or any(
        type(name) is not str
        or _TEMPLATE_CONTEXT_NAME.fullmatch(name) is None
        or name in _RESERVED_TEMPLATE_CONTEXT_NAMES
        for name in cast("tuple[object, ...]", names)
    ):
        raise TypeError(f"{label} browser template context names must be a tuple of non-reserved exact $Identifiers.")
    names = cast("tuple[str, ...]", names)
    if len(set(names)) != len(names) or names != tuple(sorted(names)):
        raise ValueError(f"{label} browser template context names must be unique and sorted.")


def _script_state(script: Script) -> tuple[object, ...]:
    return (
        script.content,
        script.url,
        tuple(sorted(script.attrs.items())),
        script.kind,
        script.origin_class_id,
        script.wrap,
        getattr(script, "_owned_resource", None),
    )


def _dependency_state(value: Script | Style) -> tuple[object, ...]:
    base: tuple[object, ...] = (
        type(value),
        value.content,
        value.url,
        tuple(sorted(value.attrs.items())),
        value.kind,
        value.origin_class_id,
        getattr(value, "_owned_resource", None),
    )
    return (*base, value.wrap) if type(value) is Script else base


def _validate_dependency_snapshot(value: Script | Style, extension_name: str) -> None:
    if type(value.content) is not str and value.content is not None:
        raise TypeError(f"Extension {extension_name!r} browser asset content must be an exact string or None.")
    if type(value.url) is not str and value.url is not None:
        raise TypeError(f"Extension {extension_name!r} browser asset URL must be an exact string or None.")
    if type(value.attrs) is not dict or any(
        type(key) is not str or type(item) not in (str, bool) for key, item in value.attrs.items()
    ):
        raise TypeError(f"Extension {extension_name!r} browser asset attrs must contain exact string/bool values.")
    value._check_validity()
    from citry._serialization_security import _browser_loader_descriptor  # noqa: PLC0415

    _browser_loader_descriptor(value)


def _detach_dependency(value: DependencyT) -> DependencyT:
    detached = copy(value)
    detached.attrs = dict(value.attrs)
    return detached


def _detach_plugin(plugin: BrowserPluginDescriptor) -> BrowserPluginDescriptor:
    script = copy(plugin.script)
    script.attrs = dict(plugin.script.attrs)
    return BrowserPluginDescriptor(
        plugin.schema_version,
        script,
        plugin.allows_late_component_assets,
        plugin.template_context_names,
    )


def _validate_version(value: object, name: str, source: str) -> None:
    if type(value) is not int or value <= 0:
        raise TypeError(f"Extension {name!r} browser {source} schema version must be a positive exact int.")


def _validate_json(value: object, label: str) -> None:
    """Reject values whose behavior or keys could change during JSON materialization."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise TypeError(f"{label} contains a non-finite number.")
        return
    if type(value) is list:
        for item in value:
            _validate_json(item, label)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{label} contains a non-string or non-exact string key.")
            _validate_json(item, label)
        return
    raise TypeError(f"{label} contains a value that is not an exact JSON type.")


def _dependencies(
    values: object,
    expected: type[DependencyT],
    extension_name: str,
    label: str,
) -> tuple[DependencyT, ...]:
    if type(values) is not tuple or any(type(value) is not expected for value in values):
        raise TypeError(
            f"Extension {extension_name!r} browser {label} assets must be a tuple of exact {expected.__name__} values."
        )
    return cast("tuple[DependencyT, ...]", values)


__all__ = [
    "BrowserPluginDescriptor",
    "BrowserPluginRegistration",
    "BrowserRenderContribution",
    "OnBrowserRenderPrepareContext",
    "collect_browser_plugin_descriptors",
    "prepare_browser_extensions",
    "validate_browser_plugin_registrations",
]
