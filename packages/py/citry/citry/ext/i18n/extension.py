"""The built-in i18n extension, project compiler, and explicit locale contexts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from hashlib import sha256
from threading import RLock
from typing import TYPE_CHECKING, Any, ClassVar, cast
from weakref import ReferenceType, WeakKeyDictionary, ref

from citry.extension import Extension, ExtensionCommand, TemplateNamespaceContribution
from citry_core.i18n import CatalogCompiler, CompiledCatalog, I18nCompileError

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
from .context import LocaleContext, LocalizedText, NumberParseResult
from .errors import I18nNotConfiguredError, I18nRuntimeUnavailableError
from .packages import CatalogSource, LoadedCatalogPackage, load_catalog_packages
from .timezone import load_time_zone, tzdb_revision

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.component import Component
    from citry.extension import (
        OnCitryClearedContext,
        OnComponentDataContext,
        OnComponentRegisteredContext,
        OnComponentUnregisteredContext,
        OnExtensionCreatedContext,
        OnFilesResetContext,
        OnMessagesLoadedContext,
        TemplateNamespaceContext,
    )

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


class _FormatFacade:
    def __init__(
        self,
        extension: I18nExtension,
        component: Component | None = None,
        context: LocaleContext | None = None,
    ) -> None:
        self._extension = extension
        self._component = component
        self._explicit_context = context

    @property
    def _context(self) -> LocaleContext:
        if self._component is not None:
            return self._extension.context_for_component(self._component)
        if self._explicit_context is not None:
            return self._explicit_context
        return self._extension.context

    def number(self, value: int | Decimal, *, format: str) -> str:  # noqa: A002
        return self._extension._format_number(value, profile=format, context=self._context)

    def currency(self, value: int | Decimal, currency: str, *, format: str) -> str:  # noqa: A002
        return self._extension._format_currency(
            value,
            currency,
            profile=format,
            context=self._context,
        )

    def date(self, value: date, *, format: str) -> str:  # noqa: A002
        return self._extension._format_date(value, profile=format, context=self._context)

    def time(self, value: time, *, format: str) -> str:  # noqa: A002
        return self._extension._format_time(value, profile=format, context=self._context)

    def datetime(self, value: datetime, *, format: str) -> str:  # noqa: A002
        return self._extension._format_datetime(value, profile=format, context=self._context)

    def relative_time(self, value: int | Decimal, *, unit: str, format: str) -> str:  # noqa: A002
        return self._extension._format_relative_time(
            value,
            unit=unit,
            profile=format,
            context=self._context,
        )

    def list(self, values: object, *, format: str) -> str:  # noqa: A002
        return self._extension._format_list(values, profile=format, context=self._context)

    def __getattr__(self, name: str) -> Any:
        raise I18nRuntimeUnavailableError(
            f"i18n formatter {name!r} is not available because its ICU4X and browser contract is not checked yet."
        )


class _ParseFacade:
    def __init__(
        self,
        extension: I18nExtension,
        component: Component | None = None,
        context: LocaleContext | None = None,
    ) -> None:
        self._extension = extension
        self._component = component
        self._explicit_context = context

    @property
    def _context(self) -> LocaleContext:
        if self._component is not None:
            return self._extension.context_for_component(self._component)
        if self._explicit_context is not None:
            return self._explicit_context
        return self._extension.context

    def number(self, input: str, *, format: str) -> NumberParseResult:  # noqa: A002
        return self._extension._parse_number(input, profile=format, context=self._context)

    def __getattr__(self, name: str) -> Any:
        raise I18nRuntimeUnavailableError(
            f"i18n parser {name!r} is not available because its strict editing contract is not checked yet."
        )


@dataclass(frozen=True, slots=True, weakref_slot=True)
class _SourceCatalog:
    owner: ReferenceType[type]
    content: str
    origin: str
    digest: str
    missing_param_type: str


class I18nExtension(Extension):
    """Own immutable i18n topology and build explicit locale contexts."""

    name = "i18n"
    Config = I18n
    commands: ClassVar[list[type[ExtensionCommand]]] = [*I18N_COMMANDS]
    render_cache_mode = "stateless"
    render_cache_version = 1

    def __init__(self) -> None:
        self._config = build_engine_config({})
        self._format = _FormatFacade(self)
        self._parse = _ParseFacade(self)
        self._catalog_lock = RLock()
        self._catalogs: WeakKeyDictionary[type, _SourceCatalog] = WeakKeyDictionary()
        self._packages: tuple[LoadedCatalogPackage, ...] = ()
        self._compiler = CatalogCompiler()
        self._compiled_catalog: CompiledCatalog | None = None
        self._catalog_revision = "none"
        self._registry_generation = 0
        self._loaded_registry_generation = -1

    @property
    def configured(self) -> bool:
        return self._config.configured

    @property
    def config(self) -> I18nEngineConfig:
        return self._config

    @property
    def context(self) -> LocaleContext:
        self._require_configured()
        self._load_project_sources()
        return self._make_context(self._config.default_locale)

    def context_for_component(self, component: Component) -> LocaleContext:
        self._require_configured()
        provided = component.inject("citry_i18n", _NO_PROVIDED_CONTEXT)
        if provided is _NO_PROVIDED_CONTEXT:
            return self.context
        if type(provided) is not LocaleContext:
            raise TypeError("The 'citry_i18n' provided value must be an exact LocaleContext.")
        return provided

    @property
    def format(self) -> _FormatFacade:
        self._require_configured()
        return self._format

    def format_for_component(self, component: Component) -> _FormatFacade:
        self._require_configured()
        return _FormatFacade(self, component)

    def format_for(self, context: LocaleContext) -> _FormatFacade:
        """Format values with one explicit locale context outside a component render."""
        self._require_configured()
        if type(context) is not LocaleContext:
            raise TypeError("i18n.format_for() requires an exact LocaleContext.")
        return _FormatFacade(self, context=context)

    @property
    def parse(self) -> _ParseFacade:
        self._require_configured()
        return self._parse

    def parse_for_component(self, component: Component) -> _ParseFacade:
        self._require_configured()
        return _ParseFacade(self, component)

    def parse_for(self, context: LocaleContext) -> _ParseFacade:
        """Parse edits with one explicit locale context outside a component render."""
        self._require_configured()
        if type(context) is not LocaleContext:
            raise TypeError("i18n.parse_for() requires an exact LocaleContext.")
        return _ParseFacade(self, context=context)

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
        object.__setattr__(self, "render_cache_mode", "stateless")
        object.__setattr__(self, "render_cache_version", 1)
        collisions = {"tr", "fmt"} & ctx.citry.template_globals.keys()
        if collisions:
            names = ", ".join(sorted(collisions))
            raise ValueError(f"Configured i18n reserves template global name(s): {names}.")
        self._packages = load_catalog_packages(self._config.catalogs, mode=ctx.citry.mode)
        self._catalog_revision = self._configuration_revision()
        if self._packages:
            # Package topology is complete at engine construction. Fail now,
            # before a request can observe a partly valid installed package.
            catalog = self._compile_snapshot({})
            self._compiled_catalog = catalog
            self._catalog_revision = catalog.revision

    def on_messages_loaded(self, ctx: OnMessagesLoadedContext) -> str | None:
        if not self.configured:
            return None
        self._install_source(owner=ctx.declaration_owner, content=ctx.content, origin=ctx.origin)
        return None

    def on_files_reset(self, _ctx: OnFilesResetContext) -> None:
        with self._catalog_lock:
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def on_component_registered(self, ctx: OnComponentRegisteredContext) -> None:
        from citry.assets import loaded_messages_source  # noqa: PLC0415

        with self._catalog_lock:
            self._registry_generation += 1
            self._loaded_registry_generation = -1
        loaded = loaded_messages_source(ctx.component_class)
        if loaded is not None and self.configured:
            owner, content, origin = loaded
            self._install_source(owner=owner, content=content, origin=origin)

    def on_component_unregistered(self, ctx: OnComponentUnregisteredContext) -> None:  # noqa: ARG002
        with self._catalog_lock:
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def on_citry_cleared(self, ctx: OnCitryClearedContext) -> None:  # noqa: ARG002
        with self._catalog_lock:
            self._catalogs.clear()
            self._compiler.clear()
            self._compiled_catalog = None
            self._catalog_revision = self._configuration_revision()
            self._registry_generation += 1
            self._loaded_registry_generation = -1

    def inspect_template_namespace(
        self,
        ctx: TemplateNamespaceContext,  # noqa: ARG002
    ) -> TemplateNamespaceContribution | None:
        if not self.configured:
            return None
        return TemplateNamespaceContribution(template_variables={"tr": object, "fmt": object})

    def on_component_data(self, ctx: OnComponentDataContext) -> None:
        if not self.configured:
            return
        type(ctx.component).get_messages()
        collisions = {"tr", "fmt"} & ctx.template_data.keys()
        if collisions:
            names = ", ".join(sorted(collisions))
            raise ValueError(
                f"Component {type(ctx.component).__name__} returned reserved i18n template name(s): {names}."
            )
        component_i18n = cast("Any", ctx.component).i18n
        ctx.template_data["tr"] = component_i18n.tr
        ctx.template_data["fmt"] = component_i18n.format

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
        utc = value.astimezone(UTC)
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
        """Build one validated locale context without changing task or engine state."""
        self._require_configured()
        self._load_project_sources()
        if time_zone is not None and (type(time_zone) is not str or not time_zone):
            raise ValueError("i18n time_zone must be None or an exact non-empty string.")
        selected_locale = self._config.default_locale if locale is None else locale
        return self._make_context(selected_locale, time_zone=time_zone)

    def tr(
        self,
        message_id: str,
        *,
        attr: str | None = None,
        context: LocaleContext | None = None,
        **values: object,
    ) -> str:
        return self.resolve(message_id, attr=attr, context=context, **values).text

    def resolve(
        self,
        message_id: str,
        *,
        attr: str | None = None,
        context: LocaleContext | None = None,
        **values: object,
    ) -> LocalizedText:
        self._validate_call(message_id, attr)
        self._load_project_sources()
        context = self.context if context is None else context
        args_json = json.dumps(
            {name: self._tag_value(name, value) for name, value in sorted(values.items())},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
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
                raw = catalog.resolve_json(context.locale, message_id, args_json, attr)
            except I18nCompileError as error:
                if error.code == "I18N_OUTPUT_MISSING":
                    if attr is None:
                        raise ValueError(f"Unknown i18n message ID {message_id!r}.") from error
                    output = f"{message_id}.{attr}"
                    raise ValueError(f"Unknown i18n message output {output!r}.") from error
                raise
        resolved = json.loads(raw)
        selected_locale = resolved["selected_locale"]
        selected_direction = direction_for(selected_locale)
        text = resolved["text"]
        if selected_direction != context.direction:
            text = _isolate_bidi_paragraphs(text, direction=selected_direction)
        return LocalizedText(
            text=text,
            locale=selected_locale,
            direction=selected_direction,
            used_fallback=resolved["used_fallback"],
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
        """Resolve one rich message to text and named structural Slot parts."""
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
        self._require_configured()
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
        if canonical not in self._config.locales:
            raise ValueError(f"Locale {canonical!r} is not allowed; expected one of {self._config.locales!r}.")
        return canonical

    def _make_context(self, locale: str | None, *, time_zone: str | None = None) -> LocaleContext:
        canonical = self._canonical_allowed_locale(locale)
        if time_zone is not None:
            load_time_zone(time_zone)
        return LocaleContext(
            locale=canonical,
            fallback_locales=fallback_chain(canonical, self._config.fallbacks),
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
                if self._loaded_registry_generation == generation and self._compiled_catalog is not None:
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
            catalog = self._compile_snapshot(snapshot)
            with self._catalog_lock:
                if self._registry_generation == generation:
                    self._compiled_catalog = catalog
                    self._catalog_revision = catalog.revision
                    self._loaded_registry_generation = generation
                    return
        raise I18nRuntimeUnavailableError(
            "The component registry kept changing while i18n built its source inventory. "
            "Finish component registration before rendering, then retry."
        )

    def _install_source(self, *, owner: type, content: str, origin: str) -> None:
        from citry._linting import _component_lint_info  # noqa: PLC0415
        from citry.assets import messages_declaration_owner  # noqa: PLC0415

        candidate = _SourceCatalog(
            owner=ref(owner, self._on_catalog_owner_collected),
            content=content,
            origin=origin,
            digest=sha256(content.encode()).hexdigest(),
            missing_param_type=_component_lint_info(self.citry, owner).rule_i18n_missing_param_type,
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
            if previous is None or previous.digest != candidate.digest or previous.origin != candidate.origin:
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

        application_package = "__citry_application__"
        source_locale = self._config.source_locale
        if source_locale is None:
            raise I18nNotConfiguredError("Configured i18n has no source locale.")
        packages.append({"name": application_package, "source_locale": source_locale, "exports": []})
        application_precedence = len(self._packages)
        for record in sorted(sources.values(), key=lambda item: item.origin):
            catalogs.append(
                {
                    "path": record.origin,
                    "package": application_package,
                    "layer": "application",
                    "precedence": application_precedence,
                    "locale": source_locale,
                    "source": record.content,
                    "missing_param_type": record.missing_param_type,
                }
            )
        return {
            "schema_version": 1,
            "active_locales": self._config.locales,
            "fallbacks": dict(self._config.fallbacks),
            "packages": packages,
            "catalogs": catalogs,
            "link_units": link_units,
            "formats": self._config.formats.to_wire(),
        }

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
                "i18n is not configured. Set extensions_defaults['i18n'] with source_locale and locales."
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
