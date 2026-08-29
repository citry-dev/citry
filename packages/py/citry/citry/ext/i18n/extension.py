"""The built-in i18n extension, project compiler, and explicit locale contexts."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timezone
from decimal import Decimal
from hashlib import sha256
from threading import RLock
from typing import TYPE_CHECKING, Any, ClassVar, cast
from weakref import ReferenceType, WeakKeyDictionary, ref

from citry.extension import Extension, ExtensionCommand, StagedRenderCacheContribution, TemplateNamespaceContribution
from citry_core.i18n import CatalogCompiler, CompiledCatalog, I18nCompileError, canonicalize_locale

from .commands import I18N_COMMANDS
from .config import (
    I18n,
    I18nEngineConfig,
    build_engine_config,
    direction_for,
    fallback_chain,
    validate_component_fields,
    validate_engine_fields,
)
from .context import (
    DateParseResult,
    DateSegments,
    DateTimeParseResult,
    DateTimeSegments,
    LocaleContext,
    LocalizedText,
    NumberParseResult,
    PercentParseResult,
    TimeParseResult,
    TimeSegments,
)
from .errors import I18nNotConfiguredError, I18nRuntimeUnavailableError
from .formats import merge_format_registries
from .packages import CatalogSource, LoadedCatalogPackage, load_catalog_packages
from .timezone import load_time_zone, tzdb_revision
from .usage import (
    AMBIENT_CLIENT_OWNER,
    CLIENT_CONTEXT_KEY,
    EXTRA_KEY,
    ClientProviderUse,
    I18nRenderRecord,
    I18nUsageCollector,
    MessageOutputUse,
    ProviderFieldPolicy,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.component import Component
    from citry.ext.dependencies.emission import OnDependenciesContext
    from citry.extension import (
        OnCitryClearedContext,
        OnComponentDataContext,
        OnComponentRegisteredContext,
        OnComponentRenderedContext,
        OnComponentUnregisteredContext,
        OnExtensionCreatedContext,
        OnFilesResetContext,
        OnMessagesLoadedContext,
        OnRenderCacheExportContext,
        OnRenderCacheStageContext,
        OnRenderContextMergeContext,
        OnTemplateCompiledContext,
        TemplateNamespaceContext,
    )
    from citry.util.routing import URLRoute

_DEFERRED_INVENTORY_CODES = frozenset(
    {
        "I18N_CANDIDATE_INCOMPLETE",
        "I18N_OWNER_SOURCE_MISSING",
        "I18N_OWNER_SOURCE_OUTPUT_MISSING",
        "I18N_UNKNOWN_PUBLIC_MESSAGE",
    }
)
_FSI = "\u2068"
_LRI = "\u2066"
_RLI = "\u2067"
_PDI = "\u2069"
_BIDI_CONTROLS = frozenset("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
_BIDI_PARAGRAPH_BOUNDARIES = frozenset("\r\n\x1c\x1d\x1e\x85\u2029")
_NO_PROVIDED_CONTEXT = object()


def _record_to_wire(
    record: I18nRenderRecord,
    *,
    instance: int,
    local_by_id: dict[str, int],
) -> dict[str, object]:
    usage = record.server_usage
    record.bindings.assert_ready()
    binding_index = {binding.id: index for index, binding in enumerate(record.bindings.records)}
    return {
        "binding_markers": [
            {
                "ids": [binding_index[binding_id] for binding_id in marker],
                "value": " ".join(marker),
            }
            for marker in record.bindings.markers
        ],
        "bindings": [_binding_to_wire(binding, local_by_id=local_by_id) for binding in record.bindings.records],
        "class_id": record.class_id,
        "client_barrier": record.client_barrier,
        "client_owner": _owner_to_wire(record.client_owner, local_by_id=local_by_id),
        "client_messages": list(record.client_messages),
        "client_outputs": [{"attr": item.attr, "message": item.message} for item in record.client_outputs],
        "formats": [{"operation": item.operation, "profile": item.profile} for item in usage.formats],
        "instance": instance,
        "messages": [{"attr": item.attr, "message": item.message} for item in usage.messages],
        "parsers": [{"operation": item.operation, "profile": item.profile} for item in usage.parsers],
        "provider": _provider_to_wire(record.provider, local_by_id=local_by_id),
    }


def _binding_to_wire(binding: Any, *, local_by_id: dict[str, int]) -> dict[str, object]:
    target: dict[str, object] = {"kind": binding.target.kind}
    if binding.target.kind == "attribute":
        target["name"] = binding.target.name
    return {
        "id": binding.id,
        "message": binding.message,
        "owner": _owner_to_wire(binding.owner, local_by_id=local_by_id),
        "output": binding.output,
        "target": target,
        "values": {name: {"type": tagged[0], "value": tagged[1]} for name, tagged in binding.values},
        "values_expression": binding.values_expression,
    }


def _owner_to_wire(owner: str | None, *, local_by_id: dict[str, int]) -> int | str | None:
    if owner is None:
        return None
    return local_by_id.get(owner, "ambient")


def _provider_to_wire(
    provider: ClientProviderUse | None,
    *,
    local_by_id: dict[str, int],
) -> dict[str, object] | None:
    if provider is None:
        return None
    context = provider.context
    return {
        "context": {
            "catalog_revision": context.catalog_revision,
            "direction": context.direction,
            "fallback_locales": list(context.fallback_locales),
            "formats_revision": context.formats_revision,
            "locale": context.locale,
            "time_zone": context.time_zone,
            "tzdb_revision": context.tzdb_revision,
        },
        "direction": _policy_to_wire(provider.direction),
        "locale": _policy_to_wire(provider.locale),
        "parent": _owner_to_wire(provider.parent, local_by_id=local_by_id),
        "time_zone": _policy_to_wire(provider.time_zone),
    }


def _policy_to_wire(policy: ProviderFieldPolicy) -> dict[str, object]:
    value: dict[str, object] = {"mode": policy.mode}
    if policy.mode == "explicit":
        value["value"] = policy.value
    return value


def _records_from_wire(ctx: OnRenderCacheStageContext) -> dict[str, I18nRenderRecord]:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if set(ctx.payload) != {"records"} or type(ctx.payload["records"]) is not list:
        raise CacheArtifactError("i18n render-cache payload has an invalid field set.")
    records: dict[str, I18nRenderRecord] = {}
    seen_instances: set[int] = set()
    for index, raw in enumerate(ctx.payload["records"]):
        path = f"i18n.records[{index}]"
        expected = {
            "binding_markers",
            "bindings",
            "class_id",
            "client_barrier",
            "client_owner",
            "client_messages",
            "client_outputs",
            "formats",
            "instance",
            "messages",
            "parsers",
            "provider",
        }
        if type(raw) is not dict or set(raw) != expected:
            raise CacheArtifactError(f"{path} has an invalid field set.")
        item = cast("dict[str, object]", raw)
        instance = item["instance"]
        if type(instance) is not int or not 0 <= instance < len(ctx.instance_ids):
            raise CacheArtifactError(f"{path}.instance refers to a missing artifact instance.")
        if instance in seen_instances:
            raise CacheArtifactError(f"{path}.instance is duplicated.")
        seen_instances.add(instance)
        class_id = item["class_id"]
        if type(class_id) is not str or not class_id or class_id != ctx.instance_class_ids[instance]:
            raise CacheArtifactError(f"{path}.class_id does not match its artifact instance.")
        try:
            component_class = ctx.citry.get_component_by_class_id(class_id)
        except KeyError as error:
            raise CacheArtifactError(f"{path}.class_id has no current registered component.") from error
        client_messages = _wire_strings(item["client_messages"], path=f"{path}.client_messages")
        current_client_messages = tuple(cast("Any", component_class).I18n.client_messages)
        if client_messages != current_client_messages:
            raise CacheArtifactError(f"{path}.client_messages does not match the current component declaration.")
        client_outputs = tuple(
            MessageOutputUse(message, attr)
            for message, attr in _wire_messages(item["client_outputs"], path=f"{path}.client_outputs")
        )
        extension = cast("I18nExtension", ctx.citry.extensions.get_extension("i18n"))
        if client_outputs != extension._client_outputs(component_class):
            raise CacheArtifactError(f"{path}.client_outputs does not match the current component sources.")
        usage = I18nUsageCollector()
        for message, attr in _wire_messages(item["messages"], path=f"{path}.messages"):
            usage.record_message(message, attr)
        for operation, profile in _wire_profiles(item["formats"], path=f"{path}.formats"):
            usage.record_profile("format", operation, profile)
        for operation, profile in _wire_profiles(item["parsers"], path=f"{path}.parsers"):
            usage.record_profile("parse", operation, profile)
        render_id = ctx.instance_ids[instance]
        client_owner = _owner_from_wire(
            item["client_owner"],
            path=f"{path}.client_owner",
            instance_ids=ctx.instance_ids,
        )
        client_barrier = item["client_barrier"]
        if type(client_barrier) is not bool:
            raise CacheArtifactError(f"{path}.client_barrier must be an exact boolean.")
        provider = _provider_from_wire(
            item["provider"],
            path=f"{path}.provider",
            extension=extension,
            instance_ids=ctx.instance_ids,
        )
        is_provider_component = getattr(component_class, "_citry_i18n_provider_component", False) is True
        if (provider is not None or client_barrier) and not is_provider_component:
            raise CacheArtifactError(f"{path} assigns provider state to a non-i18n component.")
        if provider is not None and client_barrier:
            raise CacheArtifactError(f"{path} cannot be both a client provider and a barrier.")
        bindings, _binding_markers, replacements = _bindings_from_wire(
            item["bindings"],
            item["binding_markers"],
            path=path,
            render_id=render_id,
            instance_ids=ctx.instance_ids,
        )
        records[render_id] = I18nRenderRecord(
            render_id=render_id,
            class_id=class_id,
            server_usage=usage,
            client_outputs=client_outputs,
            client_messages=client_messages,
            bindings=bindings,
            client_owner=client_owner,
            provider=provider,
            client_barrier=client_barrier,
        )
        bindings._cache_text_replacements = replacements
    return records


def _bindings_from_wire(
    raw_bindings: object,
    raw_markers: object,
    *,
    path: str,
    render_id: str,
    instance_ids: tuple[str, ...],
) -> tuple[Any, list[tuple[str, ...]], tuple[tuple[str, str], ...]]:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    from .bindings import (  # noqa: PLC0415
        ATTRIBUTE_TARGETS,
        I18nBindingCollector,
        I18nBindingRecord,
        I18nBindingTarget,
    )

    if type(raw_bindings) is not list or type(raw_markers) is not list:
        raise CacheArtifactError(f"{path}.bindings and {path}.binding_markers must be exact lists.")
    records: list[I18nBindingRecord] = []
    old_ids: list[str] = []
    for index, raw in enumerate(raw_bindings):
        item_path = f"{path}.bindings[{index}]"
        expected = {"id", "message", "output", "owner", "target", "values", "values_expression"}
        if type(raw) is not dict or set(raw) != expected:
            raise CacheArtifactError(f"{item_path} has an invalid field set.")
        item = cast("dict[str, object]", raw)
        old_id = item["id"]
        expected_suffix = f"~i18n-{index}"
        if type(old_id) is not str or not old_id.endswith(expected_suffix):
            raise CacheArtifactError(f"{item_path}.id is not the expected artifact-local binding ID.")
        message = item["message"]
        output = item["output"]
        if type(message) is not str or not message:
            raise CacheArtifactError(f"{item_path}.message must be a non-empty string.")
        if output is not None and (type(output) is not str or not output):
            raise CacheArtifactError(f"{item_path}.output must be null or a non-empty string.")
        owner = _owner_from_wire(
            item["owner"],
            path=f"{item_path}.owner",
            instance_ids=instance_ids,
        )
        if owner is None:
            raise CacheArtifactError(f"{item_path}.owner must name a client provider.")
        expression = item["values_expression"]
        if expression is not None and (type(expression) is not str or not expression):
            raise CacheArtifactError(f"{item_path}.values_expression must be null or a non-empty string.")
        raw_target = item["target"]
        if type(raw_target) is not dict:
            raise CacheArtifactError(f"{item_path}.target must be an exact object.")
        target_item = cast("dict[str, object]", raw_target)
        if target_item == {"kind": "text"}:
            target = I18nBindingTarget("text")
        elif set(target_item) == {"kind", "name"} and target_item["kind"] == "attribute":
            name = target_item["name"]
            if type(name) is not str or name not in ATTRIBUTE_TARGETS:
                raise CacheArtifactError(f"{item_path}.target.name is not an allowlisted attribute.")
            target = I18nBindingTarget("attribute", name)
        else:
            raise CacheArtifactError(f"{item_path}.target has an invalid field set.")
        raw_values = item["values"]
        if type(raw_values) is not dict:
            raise CacheArtifactError(f"{item_path}.values must be an exact object.")
        values: list[tuple[str, tuple[str, str]]] = []
        for name, tagged in sorted(cast("dict[object, object]", raw_values).items(), key=lambda entry: repr(entry[0])):
            if type(name) is not str or not name or type(tagged) is not dict or set(tagged) != {"type", "value"}:
                raise CacheArtifactError(f"{item_path}.values has an invalid tagged value.")
            tagged_item = cast("dict[str, object]", tagged)
            type_name = tagged_item["type"]
            value = tagged_item["value"]
            if type(type_name) is not str or type_name not in {"datetime", "decimal", "int", "str"}:
                raise CacheArtifactError(f"{item_path}.values[{name!r}].type is invalid.")
            if type(value) is not str:
                raise CacheArtifactError(f"{item_path}.values[{name!r}].value must be a string.")
            values.append((name, (type_name, value)))
        old_ids.append(old_id)
        records.append(
            I18nBindingRecord(
                id=f"{render_id}{expected_suffix}",
                owner=owner,
                message=message,
                output=cast("str | None", output),
                values=tuple(values),
                values_expression=cast("str | None", expression),
                target=target,
            )
        )
    markers: list[tuple[str, ...]] = []
    replacements: list[tuple[str, str]] = []
    for index, raw in enumerate(raw_markers):
        marker_path = f"{path}.binding_markers[{index}]"
        if type(raw) is not dict or set(raw) != {"ids", "value"}:
            raise CacheArtifactError(f"{marker_path} has an invalid field set.")
        item = cast("dict[str, object]", raw)
        indices = item["ids"]
        old_value = item["value"]
        if (
            type(indices) is not list
            or not indices
            or any(
                type(binding_index) is not int or not 0 <= binding_index < len(records) for binding_index in indices
            )
            or len(set(cast("list[int]", indices))) != len(indices)
            or type(old_value) is not str
        ):
            raise CacheArtifactError(f"{marker_path} is invalid.")
        selected = cast("list[int]", indices)
        if old_value != " ".join(old_ids[binding_index] for binding_index in selected):
            raise CacheArtifactError(f"{marker_path}.value does not match its binding IDs.")
        fresh = tuple(records[binding_index].id for binding_index in selected)
        markers.append(fresh)
        replacements.append(
            (
                f'data-citry-i18n-binding="{old_value}"',
                f'data-citry-i18n-binding="{" ".join(fresh)}"',
            )
        )
    collector = I18nBindingCollector.restored(records, markers)
    return collector, markers, tuple(replacements)


def _provider_from_wire(
    value: object,
    *,
    path: str,
    extension: I18nExtension,
    instance_ids: tuple[str, ...],
) -> ClientProviderUse | None:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if value is None:
        return None
    if type(value) is not dict or set(value) != {"context", "direction", "locale", "parent", "time_zone"}:
        raise CacheArtifactError(f"{path} has an invalid field set.")
    item = cast("dict[str, object]", value)
    raw_context = item["context"]
    context_fields = {
        "catalog_revision",
        "direction",
        "fallback_locales",
        "formats_revision",
        "locale",
        "time_zone",
        "tzdb_revision",
    }
    if type(raw_context) is not dict or set(raw_context) != context_fields:
        raise CacheArtifactError(f"{path}.context has an invalid field set.")
    data = cast("dict[str, object]", raw_context)
    locale = data["locale"]
    if type(locale) is not str or locale not in extension.config.locales:
        raise CacheArtifactError(f"{path}.context.locale is not selectable.")
    direction = data["direction"]
    if direction not in {"ltr", "rtl"}:
        raise CacheArtifactError(f"{path}.context.direction is invalid.")
    fallback_locales = _wire_strings(data["fallback_locales"], path=f"{path}.context.fallback_locales")
    time_zone = data["time_zone"]
    if time_zone is not None and (type(time_zone) is not str or not time_zone):
        raise CacheArtifactError(f"{path}.context.time_zone must be null or a non-empty string.")
    for revision_name in ("catalog_revision", "formats_revision", "tzdb_revision"):
        revision = data[revision_name]
        if type(revision) is not str or not revision:
            raise CacheArtifactError(f"{path}.context.{revision_name} must be a non-empty string.")
    context = LocaleContext(
        locale=locale,
        fallback_locales=fallback_locales,
        direction=cast("Any", direction),
        time_zone=cast("str | None", time_zone),
        tzdb_revision=cast("str", data["tzdb_revision"]),
        catalog_revision=cast("str", data["catalog_revision"]),
        formats_revision=cast("str", data["formats_revision"]),
    )
    return ClientProviderUse(
        context=context,
        parent=_owner_from_wire(
            item["parent"],
            path=f"{path}.parent",
            instance_ids=instance_ids,
        ),
        locale=_policy_from_wire(item["locale"], path=f"{path}.locale", clear=False),
        direction=_policy_from_wire(item["direction"], path=f"{path}.direction", clear=False),
        time_zone=_policy_from_wire(item["time_zone"], path=f"{path}.time_zone", clear=True),
    )


def _owner_from_wire(
    value: object,
    *,
    path: str,
    instance_ids: tuple[str, ...],
) -> str | None:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if value is None:
        return None
    if value == "ambient":
        return AMBIENT_CLIENT_OWNER
    if type(value) is not int or not 0 <= value < len(instance_ids):
        raise CacheArtifactError(f"{path} must be null, 'ambient', or an artifact instance index.")
    return instance_ids[value]


def _policy_from_wire(value: object, *, path: str, clear: bool) -> ProviderFieldPolicy:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if type(value) is not dict:
        raise CacheArtifactError(f"{path} must be an object.")
    item = cast("dict[str, object]", value)
    mode = item.get("mode")
    expected = {"mode", "value"} if mode == "explicit" else {"mode"}
    if set(item) != expected or mode not in ({"inherit", "explicit", "clear"} if clear else {"inherit", "explicit"}):
        raise CacheArtifactError(f"{path} has an invalid provider policy.")
    policy_value = item.get("value")
    if mode == "explicit" and (type(policy_value) is not str or not policy_value):
        raise CacheArtifactError(f"{path}.value must be a non-empty string.")
    return ProviderFieldPolicy(cast("Any", mode), cast("str | None", policy_value))


def _wire_strings(value: object, *, path: str) -> tuple[str, ...]:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if type(value) is not list or any(type(item) is not str or not item for item in value):
        raise CacheArtifactError(f"{path} must be a list of non-empty strings.")
    result = tuple(cast("list[str]", value))
    if len(set(result)) != len(result):
        raise CacheArtifactError(f"{path} contains duplicates.")
    return result


def _wire_messages(value: object, *, path: str) -> tuple[tuple[str, str | None], ...]:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if type(value) is not list:
        raise CacheArtifactError(f"{path} must be a list.")
    result: list[tuple[str, str | None]] = []
    for index, raw in enumerate(value):
        item_path = f"{path}[{index}]"
        if type(raw) is not dict or set(raw) != {"attr", "message"}:
            raise CacheArtifactError(f"{item_path} has an invalid field set.")
        item = cast("dict[str, object]", raw)
        message = item["message"]
        attr = item["attr"]
        if type(message) is not str or not message:
            raise CacheArtifactError(f"{item_path}.message must be a non-empty string.")
        if attr is not None and (type(attr) is not str or not attr):
            raise CacheArtifactError(f"{item_path}.attr must be null or a non-empty string.")
        pair = (message, cast("str | None", attr))
        if pair in result:
            raise CacheArtifactError(f"{path} contains duplicates.")
        result.append(pair)
    return tuple(result)


def _wire_profiles(value: object, *, path: str) -> tuple[tuple[str, str], ...]:
    from citry.ext.cache.errors import CacheArtifactError  # noqa: PLC0415

    if type(value) is not list:
        raise CacheArtifactError(f"{path} must be a list.")
    result: list[tuple[str, str]] = []
    for index, raw in enumerate(value):
        item_path = f"{path}[{index}]"
        if type(raw) is not dict or set(raw) != {"operation", "profile"}:
            raise CacheArtifactError(f"{item_path} has an invalid field set.")
        item = cast("dict[str, object]", raw)
        operation = item["operation"]
        profile = item["profile"]
        if type(operation) is not str or not operation:
            raise CacheArtifactError(f"{item_path}.operation must be a non-empty string.")
        if type(profile) is not str or not profile:
            raise CacheArtifactError(f"{item_path}.profile must be a non-empty string.")
        pair = (operation, profile)
        if pair in result:
            raise CacheArtifactError(f"{path} contains duplicates.")
        result.append(pair)
    return tuple(result)


class I18nFormatter:
    """
    Format canonical values with one component or locale context.

    Citry creates this object for [`I18n.format`][citry.I18n.format] and
    [`I18nService.format`][citry.I18nService.format]. Application code should
    use those entry points rather than constructing it directly.
    """

    def __init__(
        self,
        extension: I18nExtension,
        component: Component | None = None,
        context: LocaleContext | None = None,
        usage: I18nUsageCollector | None = None,
    ) -> None:
        if (component is None) == (context is None):
            raise TypeError("I18nFormatter requires exactly one component or LocaleContext.")
        self._extension = extension
        self._component = component
        self._explicit_context = context
        self._usage = usage

    @property
    def _context(self) -> LocaleContext:
        if self._component is not None:
            return self._extension.context_for_component(self._component)
        return cast("LocaleContext", self._explicit_context)

    def number(self, value: int | Decimal, *, format: str) -> str:  # noqa: A002
        """Format an exact integer or decimal with a named number profile."""
        result = self._extension._format_number(value, profile=format, context=self._context)
        self._record("number", format)
        return result

    def percent(self, value: int | Decimal, *, format: str) -> str:  # noqa: A002
        """Format an exact ratio with a named percent profile."""
        result = self._extension._format_percent(value, profile=format, context=self._context)
        self._record("percent", format)
        return result

    def currency(self, value: int | Decimal, currency: str, *, format: str) -> str:  # noqa: A002
        """Format an exact value and ISO 4217 code with a currency profile."""
        result = self._extension._format_currency(
            value,
            currency,
            profile=format,
            context=self._context,
        )
        self._record("currency", format)
        return result

    def date(self, value: date, *, format: str) -> str:  # noqa: A002
        """Format a calendar date with a named date profile."""
        result = self._extension._format_date(value, profile=format, context=self._context)
        self._record("date", format)
        return result

    def time(self, value: time, *, format: str) -> str:  # noqa: A002
        """Format a zone-free wall-clock time with a named profile."""
        result = self._extension._format_time(value, profile=format, context=self._context)
        self._record("time", format)
        return result

    def datetime(self, value: datetime, *, format: str) -> str:  # noqa: A002
        """Format an aware instant in the context's explicit time zone."""
        result = self._extension._format_datetime(value, profile=format, context=self._context)
        self._record("datetime", format)
        return result

    def relative_time(self, value: int | Decimal, *, unit: str, format: str) -> str:  # noqa: A002
        """Format an exact relative value with a named relative-time profile."""
        result = self._extension._format_relative_time(
            value,
            unit=unit,
            profile=format,
            context=self._context,
        )
        self._record("relative_time", format)
        return result

    def list(self, values: object, *, format: str) -> str:  # noqa: A002
        """Format non-empty strings as a localized conjunction or disjunction."""
        result = self._extension._format_list(values, profile=format, context=self._context)
        self._record("list", format)
        return result

    def unit(self, value: int | Decimal, unit: str, *, format: str) -> str:  # noqa: A002
        """Format an exact value with an explicit CLDR unit identifier."""
        result = self._extension._format_unit(
            value,
            unit,
            profile=format,
            context=self._context,
        )
        self._record("unit", format)
        return result

    def _record(self, operation: str, profile: str) -> None:
        if self._usage is not None:
            self._usage.record_profile("format", operation, profile)

    def __getattr__(self, name: str) -> Any:
        raise I18nRuntimeUnavailableError(
            f"i18n formatter {name!r} is not available because its ICU4X and browser contract is not checked yet."
        )


class I18nParser:
    """
    Parse localized edits with one component or locale context.

    Citry creates this object for [`I18n.parse`][citry.I18n.parse] and
    [`I18nService.parse`][citry.I18nService.parse]. Application code should
    use those entry points rather than constructing it directly.
    """

    def __init__(
        self,
        extension: I18nExtension,
        component: Component | None = None,
        context: LocaleContext | None = None,
        usage: I18nUsageCollector | None = None,
    ) -> None:
        if (component is None) == (context is None):
            raise TypeError("I18nParser requires exactly one component or LocaleContext.")
        self._extension = extension
        self._component = component
        self._explicit_context = context
        self._usage = usage

    @property
    def _context(self) -> LocaleContext:
        if self._component is not None:
            return self._extension.context_for_component(self._component)
        return cast("LocaleContext", self._explicit_context)

    def number(self, input: str, *, format: str) -> NumberParseResult:  # noqa: A002
        """Parse one strict localized number edit into an exact decimal."""
        result = self._extension._parse_number(input, profile=format, context=self._context)
        self._record("number", format)
        return result

    def percent(self, input: str, *, format: str) -> PercentParseResult:  # noqa: A002
        """Parse one strict localized percent edit into its exact ratio."""
        result = self._extension._parse_percent(input, profile=format, context=self._context)
        self._record("percent", format)
        return result

    def date(self, input: str, *, format: str) -> DateParseResult:  # noqa: A002
        """Parse one strict localized date string with a text-input profile."""
        result = self._extension._parse_date(input, profile=format, context=self._context)
        self._record("date", format)
        return result

    def date_segments(self, input: DateSegments, *, format: str) -> DateParseResult:  # noqa: A002
        """Parse named date fields with a segmented-input profile."""
        result = self._extension._parse_date_segments(input, profile=format, context=self._context)
        self._record("date", format)
        return result

    def time(self, input: str, *, format: str) -> TimeParseResult:  # noqa: A002
        """Parse one strict localized wall-clock time string."""
        result = self._extension._parse_time(input, profile=format, context=self._context)
        self._record("time", format)
        return result

    def time_segments(self, input: TimeSegments, *, format: str) -> TimeParseResult:  # noqa: A002
        """Parse named wall-clock fields with a segmented-input profile."""
        result = self._extension._parse_time_segments(input, profile=format, context=self._context)
        self._record("time", format)
        return result

    def datetime(
        self,
        input: str,  # noqa: A002
        *,
        format: str,  # noqa: A002
        fold: str | None = None,
    ) -> DateTimeParseResult:
        """Parse local datetime text and resolve it through the context time zone."""
        result = self._extension._parse_datetime(
            input,
            profile=format,
            fold=fold,
            context=self._context,
        )
        self._record("datetime", format)
        return result

    def datetime_segments(
        self,
        input: DateTimeSegments,  # noqa: A002
        *,
        format: str,  # noqa: A002
        fold: str | None = None,
    ) -> DateTimeParseResult:
        """Parse named local datetime fields and resolve an explicit DST fold."""
        result = self._extension._parse_datetime_segments(
            input,
            profile=format,
            fold=fold,
            context=self._context,
        )
        self._record("datetime", format)
        return result

    def _record(self, operation: str, profile: str) -> None:
        if self._usage is not None:
            self._usage.record_profile("parse", operation, profile)

    def __getattr__(self, name: str) -> Any:
        raise I18nRuntimeUnavailableError(
            f"i18n parser {name!r} is not available because its strict editing contract is not checked yet."
        )


class I18nService:
    """
    Use messages, formatting, and parsing with one explicit locale context.

    Create this service with
    [`I18nExtension.for_context`][citry.I18nExtension.for_context]. Components
    receive the same operations through [`Component.i18n`][citry.Component.i18n].

    Attributes:
        context: The exact locale context used by every operation.
        format: Named formatting operations bound to `context`.
        parse: Strict parsing operations bound to `context`.

    """

    def __init__(self, extension: I18nExtension, context: LocaleContext) -> None:
        self._extension = extension
        self._context = context
        self._format = I18nFormatter(extension, context=context)
        self._parse = I18nParser(extension, context=context)

    @property
    def configured(self) -> bool:
        """Return whether the owning engine configured i18n."""
        return self._extension.configured

    @property
    def available(self) -> bool:
        """Return whether settings or component messages provide server i18n."""
        return self._extension.available

    @property
    def context(self) -> LocaleContext:
        """Return the exact locale context bound to this service."""
        return self._context

    def tr(self, message_id: str, *, attr: str | None = None, **values: object) -> str:
        """Resolve one message to plain text with the bound context."""
        return self._extension.tr(message_id, attr=attr, context=self._context, **values)

    def resolve(self, message_id: str, *, attr: str | None = None, **values: object) -> LocalizedText:
        """Resolve text and retain its selected locale and fallback metadata."""
        return self._extension.resolve(message_id, attr=attr, context=self._context, **values)

    @property
    def format(self) -> I18nFormatter:
        """Return the named formatter operations bound to this context."""
        return self._format

    @property
    def parse(self) -> I18nParser:
        """Return the strict parser operations bound to this context."""
        return self._parse


class _WeakrefableSlots:
    """Provide a weak-reference slot on every supported Python version."""

    __slots__ = ("__weakref__",)


@dataclass(frozen=True, slots=True)
class _SourceCatalog(_WeakrefableSlots):
    owner: ReferenceType[type]
    content: str
    origin: str
    digest: str
    missing_param_type: str
    messages_locale: str
    is_library: bool


class I18nExtension(Extension):
    """
    Own one application's catalog graph, profiles, and locale contexts.

    Registered component messages activate the server catalog in source mode.
    Explicit engine settings additionally activate selectable locales, catalog
    packages, named profiles, parsing, and browser delivery.

    Application code normally obtains this built-in extension from
    `app.extensions.get_extension("i18n")`. Create a context with
    [`make_context()`][citry.ext.i18n.make_context], pass it through root
    `render(provides={"citry_i18n": context})`, and use
    [`for_context()`][citry.I18nExtension.for_context] outside components.
    Components receive the same operations through `self.i18n`.
    """

    name = "i18n"
    Config = I18n
    commands: ClassVar[list[type[ExtensionCommand]]] = [*I18N_COMMANDS]
    render_cache_mode = "stateless"
    render_cache_version = 1

    def __init__(self) -> None:
        self._config = build_engine_config({})
        self._catalog_lock = RLock()
        self._catalogs: WeakKeyDictionary[type, _SourceCatalog] = WeakKeyDictionary()
        self._client_output_cache: WeakKeyDictionary[type, tuple[MessageOutputUse, ...]] = WeakKeyDictionary()
        self._packages: tuple[LoadedCatalogPackage, ...] = ()
        self._compiler = CatalogCompiler()
        self._compiled_catalog: CompiledCatalog | None = None
        self._catalog_revision = "none"
        self._source_default_locale: str | None = None
        self._source_locales: tuple[str, ...] = ()
        self._registry_generation = 0
        self._loaded_registry_generation = -1

    @property
    def configured(self) -> bool:
        """Return whether the engine supplied the required i18n settings."""
        return self._config.configured

    @property
    def available(self) -> bool:
        """Return whether settings or registered component messages provide server i18n."""
        self._load_project_sources()
        with self._catalog_lock:
            return self._compiled_catalog is not None and self._effective_default_locale() is not None

    @property
    def config(self) -> I18nEngineConfig:
        """Return the validated immutable engine configuration."""
        return self._config

    @property
    def catalog_revision(self) -> str:
        """The current checked catalog graph revision."""
        self._load_project_sources()
        self._require_available()
        return self._catalog_revision

    @property
    def urls(self) -> list[URLRoute]:
        """Serve the browser runtime and exact message-partition endpoint."""
        if not self.configured:
            return []
        from .routes import i18n_routes  # noqa: PLC0415

        return i18n_routes(self)

    @property
    def context(self) -> LocaleContext:
        """Build a fresh context for the configured or inferred source locale."""
        self._load_project_sources()
        self._require_available()
        return self._make_context(self._effective_default_locale())

    def context_for_component(self, component: Component) -> LocaleContext:
        """Return the exact context provided to a component, or the default."""
        self._load_project_sources()
        self._require_available()
        provided = component.inject("citry_i18n", _NO_PROVIDED_CONTEXT)
        if provided is _NO_PROVIDED_CONTEXT:
            return self.context
        if type(provided) is not LocaleContext:
            raise TypeError("The 'citry_i18n' provided value must be an exact LocaleContext.")
        return provided

    def format_for_component(
        self,
        component: Component,
        *,
        usage: I18nUsageCollector | None = None,
    ) -> I18nFormatter:
        self._load_project_sources()
        self._require_available()
        return I18nFormatter(self, component, usage=usage)

    def parse_for_component(
        self,
        component: Component,
        *,
        usage: I18nUsageCollector | None = None,
    ) -> I18nParser:
        self._load_project_sources()
        self._require_available()
        return I18nParser(self, component, usage=usage)

    def for_context(self, context: LocaleContext) -> I18nService:
        """
        Return the complete i18n service bound to one explicit context.

        Args:
            context: The locale, direction, time zone, and catalog revisions
                that every operation must use.

        Returns:
            Translation, resolution, formatting, and parsing operations that
            all use `context`.

        Raises:
            I18nNotConfiguredError: The engine has no i18n configuration.
            TypeError: `context` is not an exact [`LocaleContext`][citry.LocaleContext].

        """
        self._load_project_sources()
        self._require_available()
        if type(context) is not LocaleContext:
            raise TypeError("i18n.for_context() requires an exact LocaleContext.")
        return I18nService(self, context)

    def _tooling_index(self) -> dict[str, object]:
        """Return detached compiler facts for Citry's isolated tooling worker."""
        self._load_project_sources()
        with self._catalog_lock:
            catalog = self._compiled_catalog
            if catalog is None:
                return {"version": 2, "available": False, "configured": self.configured}
            artifact = cast("dict[str, object]", json.loads(catalog.artifact_json()))
        manifest = cast("dict[str, dict[str, dict[str, object]]]", artifact["manifest"])
        locale = self._effective_default_locale()
        if locale is None or locale not in manifest:
            raise I18nRuntimeUnavailableError("Available i18n has no manifest for its default locale.")
        outputs: list[dict[str, object]] = []
        for token, entry in sorted(manifest[locale].items()):
            message, separator, attribute = token.partition(".")
            outputs.append(
                {
                    "token": token,
                    "message": message,
                    "attribute": attribute if separator else None,
                    "owner": entry["owner"],
                    "definition": {
                        "path": entry["definition_path"],
                        "start": entry["definition_start"],
                        "end": entry["definition_end"],
                        "line": entry["definition_line"],
                        "column": entry["definition_column"],
                    },
                    "interface": entry["interface"],
                }
            )
        references = sorted(
            {
                (
                    cast("str", source_map["authored_path"]),
                    cast("int", source_map["authored_start"]),
                    cast("int", source_map["authored_end"]),
                    cast("str", source_map["detail"]),
                )
                for source_map in cast("list[dict[str, object]]", artifact["source_maps"])
                if source_map["kind"] == "public-reference" and type(source_map["detail"]) is str
            }
        )
        format_profiles = {kind: sorted(profiles) for kind, profiles in self._config.formats.to_wire().items()}
        parse_profiles = {
            "number": sorted(self._config.formats.number),
            "percent": sorted(self._config.formats.percent),
            "date": sorted(name for name, profile in self._config.formats.date.items() if profile.input is not None),
            "time": sorted(name for name, profile in self._config.formats.time.items() if profile.input is not None),
            "datetime": sorted(
                name for name, profile in self._config.formats.datetime.items() if profile.input is not None
            ),
        }
        return {
            "version": 2,
            "available": True,
            "configured": self.configured,
            "revision": self._catalog_revision,
            "locales": list(self._effective_locales()),
            "outputs": outputs,
            "references": [
                {"path": path, "start": start, "end": end, "token": token} for path, start, end, token in references
            ],
            "profiles": {"format": format_profiles, "parse": parse_profiles},
        }

    def validate_config_fields(self, fields: Mapping[str, Any], *, component: type[Component] | None = None) -> None:
        if component is None:
            validate_engine_fields(fields)
        else:
            validate_component_fields(fields)

    def _component_config_defaults(self, fields: Mapping[str, Any]) -> Mapping[str, Any]:  # noqa: ARG002
        return {}

    def _render_cache_participates(self, ctx: object) -> bool:  # noqa: ARG002
        return self.configured

    def on_extension_created(self, ctx: OnExtensionCreatedContext) -> None:
        self._config = build_engine_config(ctx.citry.settings.extensions_defaults.get("i18n", {}))
        if not self.configured:
            return
        object.__setattr__(self, "render_cache_mode", "payload")
        object.__setattr__(self, "render_cache_version", 3)
        self._validate_template_global_names()
        self._packages = load_catalog_packages(self._config.catalogs, mode=ctx.citry.mode)
        format_contributions = tuple(
            (package.owner, package.formats) for package in self._packages if package.formats is not None
        )
        if format_contributions:
            merged_formats = merge_format_registries(self._config.formats, format_contributions)
            merged_revision = sha256(
                f"{self._config.catalog_revision}\npackage-formats:{merged_formats.revision}".encode()
            ).hexdigest()
            self._config = replace(
                self._config,
                formats=merged_formats,
                formats_revision=merged_formats.revision,
                catalog_revision=merged_revision,
            )
        self._catalog_revision = self._configuration_revision()
        if self._packages:
            # Package topology is complete at engine construction. Fail now,
            # before a request can observe a partly valid installed package.
            catalog = self._compile_snapshot({})
            self._compiled_catalog = catalog
            self._catalog_revision = catalog.revision

    def on_messages_loaded(self, ctx: OnMessagesLoadedContext) -> str | None:
        self._install_source(
            component_class=ctx.component_class,
            owner=ctx.declaration_owner,
            content=ctx.content,
            origin=ctx.origin,
        )
        return None

    def on_files_reset(self, _ctx: OnFilesResetContext) -> None:
        with self._catalog_lock:
            self._client_output_cache.clear()
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def on_component_registered(self, ctx: OnComponentRegisteredContext) -> None:
        from citry.assets import loaded_messages_source  # noqa: PLC0415

        with self._catalog_lock:
            self._registry_generation += 1
            self._loaded_registry_generation = -1
        loaded = loaded_messages_source(ctx.component_class)
        if loaded is not None:
            owner, content, origin = loaded
            self._install_source(
                component_class=ctx.component_class,
                owner=owner,
                content=content,
                origin=origin,
            )

    def on_component_unregistered(self, ctx: OnComponentUnregisteredContext) -> None:  # noqa: ARG002
        with self._catalog_lock:
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def on_citry_cleared(self, ctx: OnCitryClearedContext) -> None:  # noqa: ARG002
        with self._catalog_lock:
            self._catalogs.clear()
            self._client_output_cache.clear()
            self._compiler.clear()
            self._compiled_catalog = None
            self._catalog_revision = self._configuration_revision()
            self._source_default_locale = None
            self._source_locales = ()
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def inspect_template_namespace(
        self,
        ctx: TemplateNamespaceContext,  # noqa: ARG002
    ) -> TemplateNamespaceContribution | None:
        if not self.configured and not self._has_registered_message_source():
            return None
        return TemplateNamespaceContribution(template_variables={"tr": Callable[..., str], "fmt": I18nFormatter})

    def _has_registered_message_source(self) -> bool:
        """Check whether source mode applies without loading assets or recursing through lint."""
        from citry.assets import _find_pair_declaration  # noqa: PLC0415

        for component_class in self.citry._registered_component_classes_snapshot():
            _owner, inline, path = _find_pair_declaration(component_class, "messages", "messages_file")
            if inline is not None or path is not None:
                return True
        return False

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        with self._catalog_lock:
            catalog_is_current = self._loaded_registry_generation == self._registry_generation
            catalog_available = self._compiled_catalog is not None
        if not catalog_is_current:
            type(ctx.component).get_messages()
            self._load_project_sources()
            with self._catalog_lock:
                catalog_available = self._compiled_catalog is not None
        if not catalog_available:
            return
        component_i18n = cast("Any", ctx.component).i18n
        if type(ctx.component).get_template() is not None:
            collisions = {"tr", "fmt"} & ctx.template_data.keys()
            if collisions:
                names = ", ".join(sorted(collisions))
                raise ValueError(
                    f"Component {type(ctx.component).__name__} returned reserved i18n template name(s): {names}."
                )
            ctx.template_data["tr"] = component_i18n.tr
            ctx.template_data["fmt"] = component_i18n.format
        if not self.configured:
            return
        provider = cast("ClientProviderUse | None", getattr(ctx.component, "_citry_i18n_client_provider", None))
        client_barrier = getattr(ctx.component, "_citry_i18n_client_barrier", False) is True
        client_owner = ctx.component.inject(CLIENT_CONTEXT_KEY, None)
        if client_owner is not None and type(client_owner) is not str:
            raise TypeError(f"The internal {CLIENT_CONTEXT_KEY!r} provided value must be a render ID.")
        records: dict[str, I18nRenderRecord] = ctx.context.extra.setdefault(EXTRA_KEY, {})
        records[ctx.component.id] = I18nRenderRecord(
            render_id=ctx.component.id,
            class_id=ctx.component._citry_class_id,
            server_usage=component_i18n._usage,
            client_outputs=self._client_outputs(type(ctx.component)),
            client_messages=tuple(component_i18n.client_messages),
            bindings=component_i18n._bindings,
            client_owner=cast("str | None", client_owner),
            provider=provider,
            client_barrier=client_barrier,
        )

    def on_template_compiled(self, ctx: OnTemplateCompiledContext) -> list[Any]:
        """Install render-time wrappers for direct, dynamic, and spread `$c-tr`."""
        from .bindings import compile_template_bindings  # noqa: PLC0415

        return compile_template_bindings(ctx.nodes, component_name=ctx.component_class.__name__)

    def on_component_rendered(self, ctx: OnComponentRenderedContext) -> None:
        """Seal checked binding metadata after the complete component body rendered."""
        if ctx.error is None:
            bindings = cast("Any", ctx.component).i18n._bindings_state
            if bindings is not None:
                bindings.seal()

    def _client_outputs(self, component_class: type[Component]) -> tuple[MessageOutputUse, ...]:
        """Return literal browser message roots proven for one component class."""
        with self._catalog_lock:
            cached = self._client_output_cache.get(component_class)
            if cached is not None:
                return cached

        from citry._browser_expressions import (  # noqa: PLC0415
            BrowserExpression,
            analyze_browser_component_source,
            analyze_browser_expression,
            browser_expressions,
            browser_i18n_bind_calls,
            browser_member_literal_calls,
        )
        from citry.tag_rules import build_tag_rules  # noqa: PLC0415
        from citry_core.template_parser import parse_template  # noqa: PLC0415

        outputs: dict[MessageOutputUse, None] = {}
        template = component_class.get_template()
        if template is not None:
            rules = dict(build_tag_rules(self.citry))
            parsed = parse_template(template.source, user_rules=rules)
            nested_parser = lambda source: parse_template(source, user_rules=rules)  # noqa: E731
            for expression in browser_expressions(parsed, parse_nested=nested_parser):
                if not analyze_browser_expression(expression).valid:
                    continue
                for call in browser_member_literal_calls(
                    expression,
                    frozenset({"$i18n"}),
                    frozenset({"resolve", "tr"}),
                ):
                    outputs[MessageOutputUse(call.value, None)] = None

        javascript = component_class.get_js()
        if javascript is not None:
            analysis = analyze_browser_component_source(javascript)
            if analysis.valid:
                references: dict[str, set[tuple[int, int]]] = {}
                for binding in analysis.bindings:
                    if binding.name == "i18n":
                        references.setdefault(binding.local_name, set()).update(binding.references)
                expression = BrowserExpression(
                    javascript,
                    0,
                    len(javascript.encode()),
                    "statement",
                    "component-js",
                )
                for call in browser_member_literal_calls(
                    expression,
                    frozenset(references),
                    frozenset({"resolve", "tr"}),
                ):
                    if (call.owner_start_index, call.owner_end_index) in references[call.owner]:
                        outputs[MessageOutputUse(call.value, None)] = None
                for bind_call in browser_i18n_bind_calls(expression, frozenset(references)):
                    if (
                        bind_call.owner_start_index,
                        bind_call.owner_end_index,
                    ) not in references[bind_call.owner] or bind_call.has_dynamic_output:
                        continue
                    outputs[MessageOutputUse(bind_call.message, bind_call.output)] = None

        result = tuple(outputs)
        with self._catalog_lock:
            existing = self._client_output_cache.setdefault(component_class, result)
        return existing

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        child_records = ctx.child_context.extra.get(EXTRA_KEY)
        if child_records:
            parent_records: dict[str, I18nRenderRecord] = ctx.parent_context.extra.setdefault(EXTRA_KEY, {})
            parent_records.update(child_records)

    def on_dependencies(self, ctx: OnDependenciesContext) -> None:
        """Emit browser i18n only for a client-enabled provider subtree."""
        from .emission import emit_i18n_dependencies  # noqa: PLC0415

        emit_i18n_dependencies(self, ctx)

    def export_render_cache(self, ctx: OnRenderCacheExportContext) -> dict[str, object]:
        """Detach i18n metadata for the selected cached subtree."""
        local_by_id = {instance.render_id: instance.index for instance in ctx.instances}
        records: dict[str, I18nRenderRecord] = ctx.root_context.extra.get(EXTRA_KEY, {})
        return {
            "records": [
                _record_to_wire(
                    record,
                    instance=local_by_id[record.render_id],
                    local_by_id=local_by_id,
                )
                for record in records.values()
                if record.render_id in ctx.selected_render_ids
                and (
                    not record.server_usage.empty
                    or record.client_outputs
                    or record.client_messages
                    or record.bindings.records
                    or record.provider is not None
                    or record.client_barrier
                )
            ]
        }

    def stage_render_cache(self, ctx: OnRenderCacheStageContext) -> StagedRenderCacheContribution:
        """Validate cached i18n metadata and bind it to fresh render IDs."""
        records = _records_from_wire(ctx)
        replacements = tuple(
            replacement for record in records.values() for replacement in record.bindings._cache_text_replacements
        )
        return StagedRenderCacheContribution(
            extra_items=((EXTRA_KEY, records),) if records else (),
            text_replacements=replacements,
        )

    def _formatter_catalog(self, context: LocaleContext) -> CompiledCatalog:
        self._load_project_sources()
        with self._catalog_lock:
            if context.catalog_revision != self._catalog_revision:
                raise I18nRuntimeUnavailableError(
                    "The i18n catalog or formatter inventory changed after this context was created. Retry the render."
                )
            catalog = self._compiled_catalog
            if catalog is None:
                raise I18nRuntimeUnavailableError("The checked i18n runtime has not been built.")
            if context.formats_revision != catalog.formats_revision:
                raise I18nRuntimeUnavailableError(
                    "The formatter registry changed after this locale context was created. Retry the render."
                )
            return catalog

    def _format_number(self, value: object, *, profile: str, context: LocaleContext) -> str:
        return self._formatter_catalog(context).format_number(
            context.locale,
            self._format_profile(profile),
            self._exact_decimal(value),
        )

    def _parse_number(self, input_text: object, *, profile: str, context: LocaleContext) -> NumberParseResult:
        if type(input_text) is not str:
            raise TypeError(f"i18n number parser requires an exact string, got {type(input_text).__name__}.")
        raw = self._formatter_catalog(context).parse_number_json(
            context.locale,
            self._format_profile(profile),
            input_text,
        )
        parsed = json.loads(raw)
        state = parsed["state"]
        value = Decimal(parsed["value"]) if state == "valid" else None
        return NumberParseResult(
            input=input_text,
            state=state,
            value=value,
            error=parsed["error"],
        )

    def _format_percent(self, value: object, *, profile: str, context: LocaleContext) -> str:
        return self._formatter_catalog(context).format_percent(
            context.locale,
            self._format_profile(profile),
            self._exact_decimal(value),
        )

    def _parse_percent(self, input_text: object, *, profile: str, context: LocaleContext) -> PercentParseResult:
        if type(input_text) is not str:
            raise TypeError(f"i18n percent parser requires an exact string, got {type(input_text).__name__}.")
        raw = self._formatter_catalog(context).parse_percent_json(
            context.locale,
            self._format_profile(profile),
            input_text,
        )
        parsed = json.loads(raw)
        state = parsed["state"]
        value = Decimal(parsed["value"]) if state == "valid" else None
        return PercentParseResult(
            input=input_text,
            state=state,
            value=value,
            error=parsed["error"],
        )

    def _format_currency(
        self,
        value: object,
        currency: object,
        *,
        profile: str,
        context: LocaleContext,
    ) -> str:
        if type(currency) is not str or len(currency) != 3 or not currency.isascii() or not currency.isupper():
            raise ValueError("i18n currency must be exactly three uppercase ASCII letters.")
        return self._formatter_catalog(context).format_currency(
            context.locale,
            self._format_profile(profile),
            self._exact_decimal(value),
            currency,
        )

    def _format_date(self, value: object, *, profile: str, context: LocaleContext) -> str:
        if type(value) is not date:
            raise TypeError(f"i18n date formatter requires an exact date, got {type(value).__name__}.")
        return self._formatter_catalog(context).format_date(
            context.locale,
            self._format_profile(profile),
            value.year,
            value.month,
            value.day,
        )

    def _parse_date(self, input_text: object, *, profile: str, context: LocaleContext) -> DateParseResult:
        if type(input_text) is not str:
            raise TypeError(f"i18n date parser requires an exact string, got {type(input_text).__name__}.")
        raw = self._formatter_catalog(context).parse_date_json(
            context.locale,
            self._format_profile(profile),
            input_text,
        )
        return self._date_parse_result(input_text, raw)

    def _parse_date_segments(
        self,
        input_segments: object,
        *,
        profile: str,
        context: LocaleContext,
    ) -> DateParseResult:
        if type(input_segments) is not DateSegments:
            raise TypeError(
                f"i18n segmented date parser requires an exact DateSegments, got {type(input_segments).__name__}."
            )
        segments = cast("DateSegments", input_segments)
        raw = self._formatter_catalog(context).parse_date_segments_json(
            context.locale,
            self._format_profile(profile),
            segments.year,
            segments.month,
            segments.day,
        )
        return self._date_parse_result(segments, raw)

    @staticmethod
    def _date_parse_result(input_value: str | DateSegments, raw: str) -> DateParseResult:
        parsed = json.loads(raw)
        raw_value = parsed["value"]
        value = date(raw_value["year"], raw_value["month"], raw_value["day"]) if parsed["state"] == "valid" else None
        return DateParseResult(
            input=input_value,
            state=parsed["state"],
            value=value,
            error=parsed["error"],
        )

    def _parse_time(self, input_text: object, *, profile: str, context: LocaleContext) -> TimeParseResult:
        if type(input_text) is not str:
            raise TypeError(f"i18n time parser requires an exact string, got {type(input_text).__name__}.")
        raw = self._formatter_catalog(context).parse_time_json(
            context.locale,
            self._format_profile(profile),
            input_text,
        )
        return self._time_parse_result(input_text, raw)

    def _parse_time_segments(
        self,
        input_segments: object,
        *,
        profile: str,
        context: LocaleContext,
    ) -> TimeParseResult:
        if type(input_segments) is not TimeSegments:
            raise TypeError(
                f"i18n segmented time parser requires an exact TimeSegments, got {type(input_segments).__name__}."
            )
        segments = cast("TimeSegments", input_segments)
        raw = self._formatter_catalog(context).parse_time_segments_json(
            context.locale,
            self._format_profile(profile),
            segments.hour,
            segments.minute,
            segments.second,
            segments.day_period,
        )
        return self._time_parse_result(segments, raw)

    @staticmethod
    def _time_parse_result(input_value: str | TimeSegments, raw: str) -> TimeParseResult:
        parsed = json.loads(raw)
        raw_value = parsed["value"]
        value = None
        if parsed["state"] == "valid":
            nanosecond = raw_value["nanosecond"]
            if nanosecond % 1_000:
                raise I18nRuntimeUnavailableError(
                    "The i18n time parser returned sub-microsecond precision that Python cannot preserve."
                )
            value = time(
                raw_value["hour"],
                raw_value["minute"],
                raw_value["second"],
                nanosecond // 1_000,
            )
        return TimeParseResult(
            input=input_value,
            state=parsed["state"],
            value=value,
            error=parsed["error"],
        )

    def _parse_datetime(
        self,
        input_text: object,
        *,
        profile: str,
        fold: object,
        context: LocaleContext,
    ) -> DateTimeParseResult:
        if type(input_text) is not str:
            raise TypeError(f"i18n datetime parser requires an exact string, got {type(input_text).__name__}.")
        self._validate_datetime_parse_context(context, fold)
        raw = self._formatter_catalog(context).parse_datetime_json(
            context.locale,
            self._format_profile(profile),
            input_text,
        )
        return self._datetime_parse_result(input_text, raw, context=context, fold=fold)

    def _parse_datetime_segments(
        self,
        input_segments: object,
        *,
        profile: str,
        fold: object,
        context: LocaleContext,
    ) -> DateTimeParseResult:
        if type(input_segments) is not DateTimeSegments:
            raise TypeError(
                "i18n segmented datetime parser requires an exact DateTimeSegments, "
                f"got {type(input_segments).__name__}."
            )
        self._validate_datetime_parse_context(context, fold)
        segments = cast("DateTimeSegments", input_segments)
        raw = self._formatter_catalog(context).parse_datetime_segments_json(
            context.locale,
            self._format_profile(profile),
            segments.date.year,
            segments.date.month,
            segments.date.day,
            segments.time.hour,
            segments.time.minute,
            segments.time.second,
            segments.time.day_period,
        )
        return self._datetime_parse_result(segments, raw, context=context, fold=fold)

    @staticmethod
    def _validate_datetime_parse_context(context: LocaleContext, fold: object) -> None:
        if context.time_zone is None:
            raise ValueError(
                "i18n datetime parser requires time_zone in the explicit LocaleContext. "
                "Create the context with i18n.make_context(time_zone=...)."
            )
        if fold is not None and (type(fold) is not str or fold not in {"earlier", "later"}):
            raise ValueError("i18n datetime fold must be None, 'earlier', or 'later'.")

    def _datetime_parse_result(
        self,
        input_value: str | DateTimeSegments,
        raw: str,
        *,
        context: LocaleContext,
        fold: object,
    ) -> DateTimeParseResult:
        parsed = json.loads(raw)
        if parsed["state"] != "valid":
            return DateTimeParseResult(
                input=input_value,
                state=parsed["state"],
                value=None,
                error=parsed["error"],
            )
        raw_value = parsed["value"]
        nanosecond = raw_value["nanosecond"]
        if nanosecond % 1_000:
            raise I18nRuntimeUnavailableError(
                "The i18n datetime parser returned sub-microsecond precision that Python cannot preserve."
            )
        local = datetime(  # noqa: DTZ001 - local wall time is resolved below.
            raw_value["year"],
            raw_value["month"],
            raw_value["day"],
            raw_value["hour"],
            raw_value["minute"],
            raw_value["second"],
            nanosecond // 1_000,
        )
        zone = load_time_zone(cast("str", context.time_zone))
        candidates: list[datetime] = []
        for fold_value in (0, 1):
            candidate = local.replace(tzinfo=zone, fold=fold_value).astimezone(timezone.utc)
            if candidate.astimezone(zone).replace(tzinfo=None) == local and candidate not in candidates:
                candidates.append(candidate)
        candidates.sort()
        if not candidates:
            return DateTimeParseResult(
                input=input_value,
                state="invalid",
                value=None,
                error="nonexistent_local_time",
            )
        if len(candidates) == 1:
            return DateTimeParseResult(
                input=input_value,
                state="valid",
                value=candidates[0],
                error=None,
            )
        alternatives = tuple(candidates)
        if fold is None:
            return DateTimeParseResult(
                input=input_value,
                state="ambiguous",
                value=None,
                error="ambiguous_local_time",
                alternatives=alternatives,
            )
        selected = candidates[0] if fold == "earlier" else candidates[-1]
        return DateTimeParseResult(
            input=input_value,
            state="valid",
            value=selected,
            error=None,
            alternatives=alternatives,
        )

    def _format_time(self, value: object, *, profile: str, context: LocaleContext) -> str:
        if type(value) is not time:
            raise TypeError(f"i18n time formatter requires an exact time, got {type(value).__name__}.")
        if value.tzinfo is not None:
            raise ValueError(
                "i18n time formatter accepts wall-clock fields only. Use an aware datetime for time-zone conversion."
            )
        return self._formatter_catalog(context).format_time(
            context.locale,
            self._format_profile(profile),
            value.hour,
            value.minute,
            value.second,
            value.microsecond * 1_000,
        )

    def _format_datetime(self, value: object, *, profile: str, context: LocaleContext) -> str:
        if type(value) is not datetime:
            raise TypeError(f"i18n datetime formatter requires an exact datetime, got {type(value).__name__}.")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("i18n datetime formatter requires an aware datetime that identifies one instant.")
        if context.time_zone is None:
            raise ValueError(
                "i18n datetime formatter requires time_zone in the explicit LocaleContext. "
                "Create the context with i18n.make_context(time_zone=...)."
            )
        zone = load_time_zone(context.time_zone)
        local = value.astimezone(zone)
        offset = local.utcoffset()
        if offset is None:
            raise I18nRuntimeUnavailableError(f"Time zone {context.time_zone!r} did not resolve a UTC offset.")
        offset_seconds = int(offset.total_seconds())
        utc = value.astimezone(timezone.utc)
        epoch_seconds = (utc.date() - date(1970, 1, 1)).days * 86_400
        epoch_seconds += utc.hour * 3_600 + utc.minute * 60 + utc.second
        return self._formatter_catalog(context).format_datetime(
            context.locale,
            self._format_profile(profile),
            local.year,
            local.month,
            local.day,
            local.hour,
            local.minute,
            local.second,
            local.microsecond * 1_000,
            context.time_zone,
            offset_seconds,
            epoch_seconds,
        )

    def _format_relative_time(
        self,
        value: object,
        *,
        unit: object,
        profile: str,
        context: LocaleContext,
    ) -> str:
        if type(unit) is not str or not unit:
            raise ValueError("i18n relative-time unit must be an exact non-empty string.")
        return self._formatter_catalog(context).format_relative_time(
            context.locale,
            self._format_profile(profile),
            self._exact_decimal(value),
            unit,
        )

    def _format_list(self, values: object, *, profile: str, context: LocaleContext) -> str:
        if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple)):
            raise TypeError("i18n list formatter requires a list or tuple of exact strings.")
        normalized = list(values)
        if any(type(item) is not str for item in normalized):
            raise TypeError("i18n list formatter values must be exact strings.")
        isolated: list[str] = []
        for item in cast("list[str]", normalized):
            if not item:
                raise ValueError("i18n list formatter values must not be empty.")
            if any(character in _BIDI_CONTROLS for character in item):
                raise ValueError("i18n list formatter values must not contain Unicode bidi controls.")
            if any(character in _BIDI_PARAGRAPH_BOUNDARIES for character in item):
                raise ValueError("i18n list formatter values must not contain paragraph boundaries.")
            isolated.append(item)
        formatted = self._formatter_catalog(context).format_list(
            context.locale,
            self._format_profile(profile),
            isolated,
        )
        parts: list[str] = []
        cursor = 0
        for item in isolated:
            position = formatted.find(item, cursor)
            if position < 0:
                raise I18nRuntimeUnavailableError(
                    "The ICU4X list formatter changed an item instead of preserving its exact text."
                )
            parts.extend((formatted[cursor:position], _FSI, item, _PDI))
            cursor = position + len(item)
        parts.append(formatted[cursor:])
        return "".join(parts)

    def _format_unit(
        self,
        value: object,
        unit: object,
        *,
        profile: str,
        context: LocaleContext,
    ) -> str:
        if type(unit) is not str or not unit:
            raise ValueError("i18n unit must be an exact non-empty string.")
        return self._formatter_catalog(context).format_unit(
            context.locale,
            self._format_profile(profile),
            self._exact_decimal(value),
            unit,
        )

    @staticmethod
    def _format_profile(value: object) -> str:
        if type(value) is not str or not value:
            raise ValueError("i18n format profile must be an exact non-empty string.")
        return value

    @staticmethod
    def _exact_decimal(value: object) -> str:
        if type(value) is int:
            return str(value)
        if type(value) is Decimal and value.is_finite():
            text = format(value, "f")
            return "0" if Decimal(text).is_zero() else text
        raise TypeError("i18n numeric formatters require an exact int or finite Decimal.")

    def make_context(
        self,
        *,
        locale: str | None = None,
        time_zone: str | None = None,
    ) -> LocaleContext:
        """
        Build one validated locale context without changing shared state.

        Args:
            locale: An allowed configured/source locale, or ``None`` for the
                configured or inferred default locale.
            time_zone: An IANA time-zone name, or ``None`` for a zone-free context.

        Returns:
            A new immutable context carrying the current catalog and profile revisions.

        Raises:
            I18nNotConfiguredError: The extension has neither settings nor
                registered component message sources.
            ValueError: The locale or time zone is invalid or unavailable.

        """
        self._load_project_sources()
        self._require_available()
        if time_zone is not None and (type(time_zone) is not str or not time_zone):
            raise ValueError("i18n time_zone must be None or an exact non-empty string.")
        selected_locale = self._effective_default_locale() if locale is None else locale
        return self._make_context(selected_locale, time_zone=time_zone)

    def browser_artifact(
        self,
        *,
        locale: str,
        outputs: tuple[MessageOutputUse, ...] | tuple[str, ...],
        messages: tuple[str, ...],
    ) -> dict[str, object]:
        """Compile one exact browser catalog partition from checked roots."""
        self._require_configured()
        canonical = self._canonical_allowed_locale(locale)
        output_tokens: list[str] = []
        for item in outputs:
            if isinstance(item, str):
                if type(item) is not str:
                    raise TypeError("i18n browser output names must be exact strings.")
                output_tokens.append(item)
            else:
                output_tokens.append(item.message if item.attr is None else f"{item.message}.{item.attr}")
        if len(set(output_tokens)) != len(output_tokens) or len(set(messages)) != len(messages):
            raise ValueError("i18n browser artifact roots must not contain duplicates.")
        context = self.make_context(locale=canonical)
        catalog = self._formatter_catalog(context)
        request = json.dumps(
            {"messages": list(messages), "outputs": output_tokens},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return cast("dict[str, object]", json.loads(catalog.browser_artifact_json(canonical, request)))

    def browser_parser_artifact(self, *, locale: str) -> dict[str, object]:
        """Build locale-specific records for the checked browser parsers."""
        self._require_configured()
        canonical = self._canonical_allowed_locale(locale)
        context = self.make_context(locale=canonical)
        catalog = self._formatter_catalog(context)
        return cast(
            "dict[str, object]",
            json.loads(catalog.browser_parser_artifact_json(canonical)),
        )

    def tr(
        self,
        message_id: str,
        *,
        attr: str | None = None,
        context: LocaleContext | None = None,
        **values: object,
    ) -> str:
        """
        Resolve one message or attribute to plain text.

        Prefer `for_context(context).tr(...)` outside components so the locale
        dependency stays explicit. Omitting `context` here uses a new default
        context and is mainly useful for tooling and simple startup checks.
        """
        return self.resolve(message_id, attr=attr, context=context, **values).text

    def resolve(
        self,
        message_id: str,
        *,
        attr: str | None = None,
        context: LocaleContext | None = None,
        **values: object,
    ) -> LocalizedText:
        """
        Resolve one message and retain its selected locale and fallback data.

        `message_id` and `attr` must name a public checked output. `values`
        must match that output's `@param` interface exactly. The supplied
        context must still carry the current catalog revision.
        """
        self._validate_call(message_id, attr)
        context = self.context if context is None else context
        args_json = (
            json.dumps(
                {name: self._tag_value(name, value) for name, value in sorted(values.items())},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            if values
            else "{}"
        )
        with self._catalog_lock:
            if context.catalog_revision != self._catalog_revision:
                raise I18nRuntimeUnavailableError(
                    "The i18n catalog inventory changed after this locale context was bound. "
                    "Retry the render with a new binding so one response cannot mix catalog revisions."
                )
            catalog = self._compiled_catalog
            if catalog is None:
                raise ValueError(f"Unknown i18n message ID {message_id!r}.")
            try:
                text, selected_locale, used_fallback = catalog._resolve(context.locale, message_id, args_json, attr)
            except I18nCompileError as error:
                if error.code == "I18N_OUTPUT_MISSING":
                    if attr is None:
                        raise ValueError(f"Unknown i18n message ID {message_id!r}.") from error
                    output = f"{message_id}.{attr}"
                    raise ValueError(f"Unknown i18n message output {output!r}.") from error
                raise
        selected_direction = direction_for(selected_locale)
        if selected_direction != context.direction:
            text = _isolate_bidi_paragraphs(text, direction=selected_direction)
        return LocalizedText(
            text=text,
            locale=selected_locale,
            direction=selected_direction,
            used_fallback=used_fallback,
        )

    def resolve_rich(
        self,
        message_id: str,
        *,
        values: Mapping[str, object],
        slots: Mapping[str, object],
        attr: str | None = None,
        context: LocaleContext | None = None,
    ) -> dict[str, object]:
        """
        Resolve one rich message to escaped text records and named Slot parts.

        This is the lower-level operation used by `<c-trans>`. Application code
        should normally use that component so fills retain their Citry scope
        and ownership.
        """
        self._validate_call(message_id, attr)
        self._load_project_sources()
        context = context if context is not None else self.context
        args_json = json.dumps(
            {name: self._tag_value(name, value) for name, value in sorted(values.items())},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        slot_names_json = json.dumps(sorted(slots), separators=(",", ":"))
        with self._catalog_lock:
            if context.catalog_revision != self._catalog_revision:
                raise I18nRuntimeUnavailableError(
                    "The i18n catalog inventory changed after this locale context was bound. Retry the render."
                )
            catalog = self._compiled_catalog
            if catalog is None:
                raise ValueError(f"Unknown i18n message ID {message_id!r}.")
            try:
                raw = catalog.resolve_rich_json(context.locale, message_id, args_json, slot_names_json, attr)
            except I18nCompileError as error:
                if error.code == "I18N_OUTPUT_MISSING":
                    if attr is None:
                        raise ValueError(f"Unknown i18n message ID {message_id!r}.") from error
                    output = f"{message_id}.{attr}"
                    raise ValueError(f"Unknown i18n message output {output!r}.") from error
                raise
        resolved = cast("dict[str, object]", json.loads(raw))
        selected_locale = cast("str", resolved["selected_locale"])
        selected_direction = direction_for(selected_locale)
        if selected_locale != context.locale:
            raise I18nRuntimeUnavailableError(
                f"Rich message {message_id!r} fell back from {context.locale!r} to {selected_locale!r}, "
                "but transparent rich output cannot mark that fallback language. Add this locale's translation "
                "or use a text-only message whose language metadata can be carried by its sink."
            )
        resolved["direction"] = selected_direction
        return resolved

    def _validate_call(self, message_id: str, attr: str | None) -> None:
        self._load_project_sources()
        self._require_available()
        if type(message_id) is not str or not message_id:
            raise ValueError("i18n message_id must be an exact non-empty string.")
        if attr is not None and (type(attr) is not str or not attr):
            raise ValueError("i18n attr must be None or an exact non-empty string.")

    def _canonical_allowed_locale(self, locale: str | None) -> str:
        if locale is None:
            raise I18nNotConfiguredError("Configured i18n has no default locale.")
        from citry_core.i18n import canonicalize_locale  # noqa: PLC0415

        try:
            canonical = canonicalize_locale(locale)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid i18n locale {locale!r}: {error}") from error
        locales = self._effective_locales()
        if canonical not in locales:
            raise ValueError(f"Locale {canonical!r} is not allowed; expected one of {locales!r}.")
        return canonical

    def _make_context(self, locale: str | None, *, time_zone: str | None = None) -> LocaleContext:
        canonical = self._canonical_allowed_locale(locale)
        if time_zone is not None:
            load_time_zone(time_zone)
        return LocaleContext(
            locale=canonical,
            fallback_locales=fallback_chain(canonical, self._effective_fallbacks()),
            direction=direction_for(canonical),
            time_zone=time_zone,
            tzdb_revision="none" if time_zone is None else tzdb_revision(),
            catalog_revision=self._catalog_revision,
            formats_revision=self._config.formats_revision,
        )

    def _load_project_sources(self) -> None:
        from citry.assets import messages_declaration_owner  # noqa: PLC0415

        for _attempt in range(16):
            with self._catalog_lock:
                generation = self._registry_generation
                if self._loaded_registry_generation == generation:
                    return
            components = set(self.citry.components.values())
            active_owners = {messages_declaration_owner(component) for component in components}
            with self._catalog_lock:
                for owner in set(self._catalogs) - active_owners:
                    self._catalogs.pop(owner, None)
            for component in sorted(components, key=lambda item: item.class_id):
                component.get_messages()
            with self._catalog_lock:
                if self._registry_generation != generation:
                    continue
                snapshot = dict(self._catalogs)
            if not self.configured and not snapshot:
                with self._catalog_lock:
                    if self._registry_generation == generation:
                        self._compiled_catalog = None
                        self._catalog_revision = self._configuration_revision()
                        self._source_default_locale = None
                        self._source_locales = ()
                        self._loaded_registry_generation = generation
                        return
                continue
            self._validate_template_global_names()
            catalog = self._compile_snapshot(snapshot)
            source_default, source_locales = self._source_topology(snapshot)
            with self._catalog_lock:
                if self._registry_generation == generation:
                    self._compiled_catalog = catalog
                    self._catalog_revision = catalog.revision
                    self._source_default_locale = source_default
                    self._source_locales = source_locales
                    self._loaded_registry_generation = generation
                    return
        raise I18nRuntimeUnavailableError(
            "The component registry kept changing while i18n built its source inventory. "
            "Finish component registration before rendering, then retry."
        )

    def _install_source(
        self,
        *,
        component_class: type[Component],
        owner: type,
        content: str,
        origin: str,
    ) -> None:
        from citry._linting import _component_lint_info  # noqa: PLC0415
        from citry.assets import messages_declaration_owner  # noqa: PLC0415

        # Library-owned Component.messages are the authoring source for the
        # matching side-effect-free catalog package. Once that package is
        # configured, loading the same block again as an application override
        # would duplicate its definition and @param contract.
        library_owner = next(
            (
                installation.library.name
                for installation in self.citry._library_installations.values()
                if owner in installation.definitions
            ),
            None,
        )
        if library_owner is not None and any(package.owner == library_owner for package in self._packages):
            with self._catalog_lock:
                self._catalogs.pop(owner, None)
            return

        messages_locale = self._messages_locale(owner)
        is_library = bool(owner.__dict__.get("_citry_is_library_component_definition", False)) or (
            component_class in self.citry._library_definitions_by_class
        )
        candidate = _SourceCatalog(
            owner=ref(owner, self._on_catalog_owner_collected),
            content=content,
            origin=origin,
            digest=sha256(content.encode()).hexdigest(),
            missing_param_type=_component_lint_info(self.citry, owner).rule_i18n_missing_param_type,
            messages_locale=messages_locale,
            is_library=is_library,
        )
        with self._catalog_lock:
            active_owners = {
                messages_declaration_owner(component)
                for component in self.citry._registered_component_classes_snapshot()
            }
            for inactive_owner in set(self._catalogs) - active_owners:
                self._catalogs.pop(inactive_owner, None)
            previous = self._catalogs.get(owner)
            snapshot = dict(self._catalogs)
            snapshot[owner] = candidate
            try:
                self._compile_snapshot(snapshot)
            except I18nCompileError as error:
                if error.code not in _DEFERRED_INVENTORY_CODES:
                    raise ValueError(str(error)) from error
            self._catalogs[owner] = candidate
            if (
                previous is None
                or previous.digest != candidate.digest
                or previous.origin != candidate.origin
                or previous.messages_locale != candidate.messages_locale
                or previous.is_library != candidate.is_library
            ):
                self._registry_generation += 1
                self._loaded_registry_generation = -1

    def _on_catalog_owner_collected(self, _owner: ReferenceType[type]) -> None:
        with self._catalog_lock:
            # WeakKeyDictionary may remove the key before this callback runs.
            # The compiled graph can still mention that source, so always mark
            # it stale when the declaration owner disappears.
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def _compile_snapshot(self, sources: Mapping[type, _SourceCatalog]) -> CompiledCatalog:
        request = self._compile_request(sources)
        return self._compiler.compile(json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True))

    def _compile_request(self, sources: Mapping[type, _SourceCatalog]) -> dict[str, object]:
        packages: list[dict[str, object]] = []
        catalogs: list[dict[str, object]] = []
        link_units: list[dict[str, object]] = []
        for precedence, package in enumerate(self._packages):
            if package.link_artifact is not None:
                link_units.append(
                    {
                        "artifact_json": package.link_artifact,
                        "layer": f"package:{precedence}:{package.owner}",
                        "precedence": precedence,
                    }
                )
                continue
            packages.append(
                {
                    "name": package.owner,
                    "source_locale": package.source_locale,
                    "exports": [],
                }
            )
            catalogs.extend(self._package_catalog_record(source) for source in package.sources)

        application_precedence = len(self._packages)
        grouped: dict[tuple[str, str], list[_SourceCatalog]] = {}
        for record in sorted(sources.values(), key=lambda item: item.origin):
            package_name = self._source_package_name(record.messages_locale)
            grouped.setdefault((package_name, record.messages_locale), []).append(record)
        for (package_name, source_locale), records in sorted(grouped.items()):
            packages.append({"name": package_name, "source_locale": source_locale, "exports": []})
            for record in records:
                catalogs.append(
                    {
                        "path": record.origin,
                        "package": package_name,
                        "layer": "application",
                        "precedence": application_precedence,
                        "locale": source_locale,
                        "source": record.content,
                        "missing_param_type": record.missing_param_type,
                    }
                )
        _source_default, source_locales = self._source_topology(sources)
        return {
            "schema_version": 1,
            "active_locales": self._config.locales if self.configured else source_locales,
            "fallbacks": dict(self._config.fallbacks) if self.configured else {},
            "packages": packages,
            "catalogs": catalogs,
            "link_units": link_units,
            "formats": self._config.formats.to_wire(),
        }

    def _messages_locale(self, owner: type) -> str:
        component_config = getattr(owner, "I18n", None)
        declared = getattr(component_config, "messages_locale", None)
        value = self._config.source_locale if declared is None else declared
        if value is None:
            label = f"{owner.__module__}.{owner.__qualname__}"
            raise ValueError(
                f"Component {label} defines messages but their locale is unknown. "
                "Set Component.I18n.messages_locale, or configure the engine i18n source_locale."
            )
        try:
            return canonicalize_locale(value)
        except (TypeError, ValueError) as error:
            label = f"{owner.__module__}.{owner.__qualname__}"
            raise ValueError(f"Component {label} has invalid I18n.messages_locale {value!r}: {error}") from error

    def _source_package_name(self, source_locale: str) -> str:
        if self.configured and source_locale == self._config.source_locale:
            return "__citry_application__"
        digest = sha256(source_locale.encode()).hexdigest()[:16]
        return f"__citry_component_source_{digest}__"

    def _source_topology(
        self,
        sources: Mapping[type, _SourceCatalog],
    ) -> tuple[str | None, tuple[str, ...]]:
        locales = tuple(sorted({record.messages_locale for record in sources.values()}))
        if self.configured:
            return self._config.default_locale, self._config.locales
        application_locales = sorted({record.messages_locale for record in sources.values() if not record.is_library})
        if len(application_locales) > 1:
            rendered = ", ".join(repr(locale) for locale in application_locales)
            raise ValueError(
                "Zero-configuration i18n found application messages authored in multiple locales "
                f"({rendered}). Configure source_locale, default_locale, and locales explicitly."
            )
        if application_locales:
            return application_locales[0], locales
        library_locales = sorted({record.messages_locale for record in sources.values() if record.is_library})
        if len(library_locales) > 1:
            rendered = ", ".join(repr(locale) for locale in library_locales)
            raise ValueError(
                "Zero-configuration i18n found library messages authored in multiple locales "
                f"({rendered}). Configure source_locale, default_locale, and locales explicitly."
            )
        return (library_locales[0] if library_locales else None), locales

    def _effective_default_locale(self) -> str | None:
        return self._config.default_locale if self.configured else self._source_default_locale

    def _effective_locales(self) -> tuple[str, ...]:
        return self._config.locales if self.configured else self._source_locales

    def _effective_fallbacks(self) -> Mapping[str, tuple[str, ...]]:
        return self._config.fallbacks if self.configured else {}

    def _validate_template_global_names(self) -> None:
        collisions = {"tr", "fmt"} & self.citry.template_globals.keys()
        if collisions:
            names = ", ".join(sorted(collisions))
            raise ValueError(f"Active i18n reserves template global name(s): {names}.")

    @staticmethod
    def _package_catalog_record(source: CatalogSource) -> dict[str, object]:
        return {
            "path": source.path,
            "package": source.owner,
            "layer": source.layer,
            "precedence": source.precedence,
            "locale": source.locale,
            "source": source.content,
            "missing_param_type": "warning",
        }

    def _configuration_revision(self) -> str:
        parts = [self._config.catalog_revision]
        parts.extend(package.manifest_revision for package in self._packages)
        return sha256("\n".join(parts).encode()).hexdigest()

    @staticmethod
    def _tag_value(name: str, value: object) -> dict[str, str]:
        if type(value) is str:
            return {"type": "str", "value": value}
        if type(value) is int:
            return {"type": "int", "value": str(value)}
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError(f"i18n argument {name!r} must be a finite Decimal.")
            text = format(value, "f")
            if value.is_zero():
                text = "0"
            return {"type": "decimal", "value": text}
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"i18n argument {name!r} must be an aware datetime.")
            return {"type": "datetime", "value": value.isoformat()}
        raise TypeError(
            f"i18n argument {name!r} has unsupported type {type(value).__name__}; "
            "use str, int, Decimal, or an aware datetime."
        )

    def _require_configured(self) -> None:
        if not self.configured:
            raise I18nNotConfiguredError(
                "i18n is not configured for this browser/configuration operation. Set "
                "extensions_defaults['i18n'] with source_locale and locales."
            )

    def _require_available(self) -> None:
        if self._compiled_catalog is None or self._effective_default_locale() is None:
            raise I18nNotConfiguredError(
                "i18n is not configured and no component messages are available. Define component messages with "
                "Component.I18n.messages_locale, or configure "
                "extensions_defaults['i18n'] with source_locale and locales."
            )


def _isolate_bidi_paragraphs(value: str, *, direction: str) -> str:
    isolate = _LRI if direction == "ltr" else _RLI
    parts: list[str] = []
    paragraph_start = 0
    index = 0
    while index < len(value):
        character = value[index]
        if character not in _BIDI_PARAGRAPH_BOUNDARIES:
            index += 1
            continue
        paragraph = value[paragraph_start:index]
        if paragraph:
            parts.extend((isolate, paragraph, _PDI))
        if character == "\r" and value[index : index + 2] == "\r\n":
            parts.append("\r\n")
            index += 2
        else:
            parts.append(character)
            index += 1
        paragraph_start = index
    paragraph = value[paragraph_start:]
    if paragraph:
        parts.extend((isolate, paragraph, _PDI))
    return "".join(parts)
