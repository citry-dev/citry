"""Validation for the built-in i18n extension."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from citry.extension import ExtensionConfig
from citry_core.i18n import canonicalize_locale, locale_direction

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Literal

    from .bindings import I18nBindingCollector
    from .context import LocaleContext, LocalizedText
    from .extension import I18nExtension, I18nFormatter, I18nParser
    from .formats import FormatRegistry
    from .usage import I18nUsageCollector

_ENGINE_FIELDS = frozenset({"source_locale", "default_locale", "locales", "fallbacks", "catalogs", "formats"})
_COMPONENT_FIELDS = frozenset({"client_messages", "messages_locale"})


class I18n(ExtensionConfig):
    """
    Per-component i18n settings and access to the provided locale context.

    Set `Component.I18n.messages_locale` to the locale in which that
    component's `messages` / `messages_file` source is authored. Declaring a
    message asset activates server translations even when the engine has no
    i18n settings. Declare `client_messages` only for finite dynamic message
    IDs that static browser analysis cannot see. Instances expose the nearest
    explicit context, translation, formatting, and parsing through `self.i18n`.
    """

    messages_locale: str | None = None
    client_messages: tuple[str, ...] = ()

    def __init__(self, component: Any) -> None:
        super().__init__(component)
        self._usage_state: I18nUsageCollector | None = None
        self._bindings_state: I18nBindingCollector | None = None
        self._translation_capture: Any = None
        self._extension_state: I18nExtension | None = None
        self._context_state: LocaleContext | None = None

    @property
    def _usage(self) -> I18nUsageCollector:
        """Allocate render-usage tracking only when i18n is actually active."""
        collector = self._usage_state
        if collector is None:
            from .usage import I18nUsageCollector  # noqa: PLC0415

            collector = I18nUsageCollector()
            self._usage_state = collector
        return collector

    @property
    def _bindings(self) -> I18nBindingCollector:
        """Allocate checked binding state only for translated templates."""
        collector = self._bindings_state
        if collector is None:
            from .bindings import I18nBindingCollector  # noqa: PLC0415

            collector = I18nBindingCollector(self.component)
            self._bindings_state = collector
        return collector

    @property
    def configured(self) -> bool:
        """Return whether this component's engine has explicit i18n settings."""
        return self._extension.configured

    @property
    def available(self) -> bool:
        """Return whether server translation is available from settings or component messages."""
        return self._extension.available

    @property
    def context(self) -> LocaleContext:
        """Return the explicit locale context provided to this component tree."""
        context = self._context_state
        if context is None:
            context = self._extension.context_for_component(self.component)
            self._context_state = context
        return context

    @property
    def _extension(self) -> I18nExtension:
        extension = self._extension_state
        if extension is None:
            extension = cast("I18nExtension", self.component.citry.extensions.get_extension("i18n"))
            self._extension_state = extension
        return extension

    def tr(self, message_id: str, *, attr: str | None = None, **values: object) -> str:
        """Resolve one message or attribute to plain text."""
        resolved = self.resolve(message_id, attr=attr, **values)
        capture = self._translation_capture
        if capture is None:
            return resolved.text
        from .bindings import CapturedTranslationText  # noqa: PLC0415

        text = CapturedTranslationText(resolved.text)
        capture(message_id, attr, dict(values), text)
        return text

    def resolve(self, message_id: str, *, attr: str | None = None, **values: object) -> LocalizedText:
        """Resolve text and keep the selected locale and fallback metadata."""
        resolved = self._extension.resolve(
            message_id,
            attr=attr,
            context=self.context,
            **values,
        )
        self._usage.record_message(message_id, attr)
        return resolved

    @property
    def format(self) -> I18nFormatter:
        """Return named formatter operations bound to this component context."""
        return self._extension.format_for_component(self.component, usage=self._usage)

    @property
    def parse(self) -> I18nParser:
        """Return strict parser operations bound to this component context."""
        return self._extension.parse_for_component(self.component, usage=self._usage)


@dataclass(frozen=True, slots=True)
class I18nEngineConfig:
    """Validated, detached engine configuration."""

    configured: bool
    source_locale: str | None
    default_locale: str | None
    locales: tuple[str, ...]
    fallbacks: Mapping[str, tuple[str, ...]]
    catalogs: tuple[str, ...]
    formats: FormatRegistry
    catalog_revision: str
    formats_revision: str


def validate_engine_fields(fields: Mapping[str, Any]) -> None:
    build_engine_config(fields)


def validate_component_fields(fields: Mapping[str, Any]) -> None:
    unknown = set(fields) - _COMPONENT_FIELDS
    if unknown:
        names = ", ".join(repr(name) for name in sorted(unknown, key=repr))
        raise ValueError(
            f"unknown component I18n field(s): {names}; valid fields are {', '.join(sorted(_COMPONENT_FIELDS))}."
        )
    if "messages_locale" in fields:
        value = fields["messages_locale"]
        if value is not None:
            _canonical_locale(value, source="Component.I18n.messages_locale")
    if "client_messages" in fields:
        _validate_message_ids(fields["client_messages"], source="Component.I18n.client_messages")


def build_engine_config(fields: Mapping[str, Any]) -> I18nEngineConfig:
    from .formats import FormatRegistry  # noqa: PLC0415

    unknown = set(fields) - _ENGINE_FIELDS
    if unknown:
        names = ", ".join(repr(name) for name in sorted(unknown, key=repr))
        raise ValueError(
            f"unknown engine i18n field(s): {names}; valid fields are {', '.join(sorted(_ENGINE_FIELDS))}."
        )

    if not fields:
        formats = FormatRegistry()
        return I18nEngineConfig(
            configured=False,
            source_locale=None,
            default_locale=None,
            locales=(),
            fallbacks=MappingProxyType({}),
            catalogs=(),
            formats=formats,
            catalog_revision="none",
            formats_revision=formats.revision,
        )

    if "source_locale" not in fields or "locales" not in fields:
        raise ValueError("configured i18n requires both 'source_locale' and 'locales'.")

    source_locale = _canonical_locale(fields["source_locale"], source="i18n source_locale")
    locales = _canonical_locale_sequence(fields["locales"], source="i18n locales", allow_empty=False)
    default_locale = _canonical_locale(fields.get("default_locale", source_locale), source="i18n default_locale")
    if default_locale not in locales:
        raise ValueError("i18n default_locale must be present in locales.")

    catalogs = _validate_catalogs(fields.get("catalogs", ()))
    formats = fields.get("formats", FormatRegistry())
    if type(formats) is not FormatRegistry:
        raise TypeError(f"i18n formats must be a FormatRegistry; got {type(formats).__name__}.")
    known_locales = frozenset((*locales, source_locale))
    fallbacks = _validate_fallbacks(fields.get("fallbacks", {}), known_locales=known_locales)
    revision_input = {
        "catalogs": catalogs,
        "default_locale": default_locale,
        "fallbacks": sorted((key, value) for key, value in fallbacks.items()),
        "locales": locales,
        "formats": formats.to_wire(),
    }
    revision = sha256(
        json.dumps(revision_input, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return I18nEngineConfig(
        configured=True,
        source_locale=source_locale,
        default_locale=default_locale,
        locales=locales,
        fallbacks=MappingProxyType(dict(fallbacks)),
        catalogs=catalogs,
        formats=formats,
        catalog_revision=revision,
        formats_revision=formats.revision,
    )


def direction_for(locale: str) -> Literal["ltr", "rtl"]:
    direction = locale_direction(locale)
    if direction not in {"ltr", "rtl"}:
        raise ValueError(f"Could not derive a writing direction for locale {locale!r}.")
    return cast("Literal['ltr', 'rtl']", direction)


def fallback_chain(locale: str, fallbacks: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    result: list[str] = []

    def visit(current: str) -> None:
        for parent in fallbacks.get(current, ()):
            if parent not in result and parent != locale:
                result.append(parent)
                visit(parent)

    visit(locale)
    return tuple(result)


def _canonical_locale(value: object, *, source: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{source} must be an exact non-empty string; got {value!r}.")
    try:
        return canonicalize_locale(value)
    except ValueError as error:
        raise ValueError(f"{source} is invalid: {error}") from error


def _canonical_locale_sequence(value: object, *, source: str, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{source} must be a sequence of locale strings, not one string.")  # noqa: TRY004
    if not isinstance(value, Sequence):
        raise ValueError(f"{source} must be an ordered sequence of locale strings.")  # noqa: TRY004
    raw: tuple[object, ...] = tuple(value)
    if not raw and not allow_empty:
        raise ValueError(f"{source} must not be empty.")
    canonical = tuple(_canonical_locale(item, source=source) for item in raw)
    duplicate = next((item for index, item in enumerate(canonical) if item in canonical[:index]), None)
    if duplicate is not None:
        raise ValueError(f"{source} contains duplicate canonical locale {duplicate!r}.")
    return canonical


def _validate_catalogs(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(  # noqa: TRY004
            "i18n catalogs must be a sequence of import-package strings, not one string."
        )
    if not isinstance(value, Sequence):
        raise ValueError("i18n catalogs must be an ordered sequence of import-package strings.")  # noqa: TRY004
    raw_catalogs: tuple[object, ...] = tuple(value)
    catalogs: list[str] = []
    for package in raw_catalogs:
        if type(package) is not str or not package or package.startswith("."):
            raise ValueError(f"i18n catalog package must be an absolute non-empty import name; got {package!r}.")
        if any(not segment.isidentifier() for segment in package.split(".")):
            raise ValueError(f"i18n catalog package is not a valid import name: {package!r}.")
        catalogs.append(package)
    duplicate = next((item for index, item in enumerate(catalogs) if item in catalogs[:index]), None)
    if duplicate is not None:
        raise ValueError(f"i18n catalogs contains duplicate package {duplicate!r}.")
    return tuple(catalogs)


def _validate_fallbacks(value: object, *, known_locales: frozenset[str]) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        raise ValueError(  # noqa: TRY004
            "i18n fallbacks must be a mapping from locale to a sequence of locales."
        )
    result: dict[str, tuple[str, ...]] = {}
    for raw_locale, raw_parents in value.items():
        locale = _canonical_locale(raw_locale, source="i18n fallback locale")
        parents = _canonical_locale_sequence(raw_parents, source=f"i18n fallbacks[{locale!r}]", allow_empty=True)
        if locale not in known_locales:
            raise ValueError(f"i18n fallback graph contains unknown locale {locale!r}.")
        unknown = next((parent for parent in parents if parent not in known_locales), None)
        if unknown is not None:
            raise ValueError(f"i18n fallback graph contains unknown locale {unknown!r}.")
        if locale in result:
            raise ValueError(f"i18n fallback graph contains duplicate canonical locale {locale!r}.")
        result[locale] = parents

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(locale: str) -> None:
        if locale in visiting:
            raise ValueError(f"i18n fallback graph contains a cycle through {locale!r}.")
        if locale in visited:
            return
        visiting.add(locale)
        for parent in result.get(locale, ()):
            visit(parent)
        visiting.remove(locale)
        visited.add(locale)

    for locale in result:
        visit(locale)
    return result


def _validate_message_ids(value: object, *, source: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{source} must be a tuple of message ID strings.")
    for message_id in value:
        if type(message_id) is not str or not message_id:
            raise ValueError(f"{source} entries must be exact non-empty strings; got {message_id!r}.")
    if len(set(value)) != len(value):
        raise ValueError(f"{source} must not contain duplicate IDs.")
    return value
