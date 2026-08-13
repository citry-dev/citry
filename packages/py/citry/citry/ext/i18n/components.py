"""The server-side components owned by the i18n extension."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from citry.component import Component
from citry.constness import const_value

from .config import direction_for, fallback_chain
from .context import LocaleContext
from .timezone import load_time_zone, tzdb_revision
from .usage import CLIENT_CONTEXT_KEY, ClientProviderUse, ProviderFieldPolicy

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.slots import SlotInput


def make_i18n_component(citry_instance: Citry) -> type[Component]:
    """Create and register the subtree locale provider for one engine."""
    extension = cast("Any", citry_instance.extensions.get_extension("i18n"))
    internal_token = citry_instance._registry._builtin_registration_token

    class _HostKwargs:
        attrs: dict[str, object]
        policy: ClientProviderUse | None = None
        tag: str | None = None

    class _HostSlots:
        default: SlotInput | None = None

    class I18nClientHost(Component, _citry_internal=internal_token):
        """Private real-element host for a client-enabled provider."""

        citry = citry_instance
        _citry_i18n_provider_component = True
        Kwargs = _HostKwargs
        Slots = _HostSlots

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
            policy = const_value(kwargs.policy)
            if type(policy) is not ClientProviderUse:
                raise TypeError("The private i18n client host requires an exact provider policy.")
            self._citry_i18n_client_provider = policy
            self.provide(CLIENT_CONTEXT_KEY, self.id)
            return {
                "attrs": const_value(kwargs.attrs),
                "tag": const_value(kwargs.tag),
            }

        template = """\
<c-element
  c-is="tag"
  c-bind="attrs"
  x-init="$provide('citry_i18n', Citry.i18n.provider($el, $inject('citry_i18n', null)))"
><c-slot /></c-element>\
"""

    class I18nBarrierHost(Component, _citry_internal=internal_token):
        """Private real-element host that blocks an inherited client service."""

        citry = citry_instance
        _citry_i18n_provider_component = True
        Kwargs = _HostKwargs
        Slots = _HostSlots

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
            self._citry_i18n_client_barrier = True
            self.unprovide(CLIENT_CONTEXT_KEY)
            return {
                "attrs": const_value(kwargs.attrs),
                "tag": const_value(kwargs.tag),
            }

        template = """\
<c-element c-is="tag" c-bind="attrs" x-init="$unprovide('citry_i18n')"><c-slot /></c-element>\
"""

    class I18nElementHost(Component, _citry_internal=internal_token):
        """Private real-element host for a server-only provider."""

        citry = citry_instance
        Kwargs = _HostKwargs
        Slots = _HostSlots

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
            return {
                "attrs": const_value(kwargs.attrs),
                "tag": const_value(kwargs.tag),
            }

        template = """\
<c-element c-is="tag" c-bind="attrs"><c-slot /></c-element>\
"""

    class I18nTransparentHost(Component, _citry_internal=internal_token):
        """Private transparent host for a server-only provider."""

        citry = citry_instance
        Kwargs = _HostKwargs
        Slots = _HostSlots
        transparent = True
        template = """\
<c-slot />\
"""

    class I18nProvider(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """Set locale context below this tag and optionally render a semantic host."""

        citry = citry_instance
        name = "i18n"
        _citry_i18n_provider_component = True

        class Kwargs:
            context: LocaleContext | None = None
            tag: str | None = None
            locale: str | None = None
            direction: str | None = None
            time_zone: str | None = None
            client: bool = False

        class Slots:
            default: SlotInput | None = None

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
            client = const_value(kwargs.client)
            if type(client) is not bool:
                raise TypeError("<c-i18n> client must be an exact boolean.")
            raw = self.raw_kwargs
            context_value = const_value(kwargs.context)
            if context_value is not None and type(context_value) is not LocaleContext:
                raise TypeError("<c-i18n> context must be None or an exact LocaleContext.")
            base = context_value if context_value is not None else extension.context_for_component(self)
            locale_given = "locale" in raw
            raw_locale = const_value(kwargs.locale)
            locale = extension._canonical_allowed_locale(raw_locale) if locale_given else base.locale
            direction_given = "direction" in raw
            if direction_given:
                direction = const_value(kwargs.direction)
                if direction not in {"ltr", "rtl"}:
                    raise ValueError("<c-i18n> direction must be 'ltr' or 'rtl'.")
            elif locale_given:
                direction = direction_for(locale)
            else:
                direction = base.direction
            if "time_zone" in raw:
                time_zone = const_value(kwargs.time_zone)
                if time_zone is not None and (type(time_zone) is not str or not time_zone):
                    raise ValueError("<c-i18n> time_zone must be None or an exact non-empty string.")
                if time_zone is not None:
                    load_time_zone(time_zone)
            else:
                time_zone = base.time_zone
            context = LocaleContext(
                locale=locale,
                fallback_locales=fallback_chain(locale, extension.config.fallbacks),
                direction=direction,
                time_zone=time_zone,
                tzdb_revision="none" if time_zone is None else tzdb_revision(),
                catalog_revision=base.catalog_revision,
                formats_revision=base.formats_revision,
            )
            self.provide("citry_i18n", context)
            tag = const_value(kwargs.tag)
            if tag is not None and (type(tag) is not str or not tag):
                raise ValueError("<c-i18n> tag must be None or an exact non-empty HTML tag name.")
            inherited_client_owner = self.inject(CLIENT_CONTEXT_KEY, None)
            if inherited_client_owner is not None and type(inherited_client_owner) is not str:
                raise TypeError(f"The internal {CLIENT_CONTEXT_KEY!r} provided value must be a render ID.")

            # Browser providers and barriers need a real element where Citry's
            # existing ambient provide/inject machinery can own their scope.
            if (client or inherited_client_owner is not None) and tag is None:
                kind = "client provider" if client else "client barrier"
                raise ValueError(f"<c-i18n> used as a {kind} requires a real 'tag' wrapper.")

            attrs: dict[str, object] = {"lang": context.locale, "dir": context.direction}
            host: type[Component]
            if client:
                locale_is_explicit = context_value is not None or locale_given or inherited_client_owner is None
                if context_value is not None or "time_zone" in raw:
                    time_zone_policy = ProviderFieldPolicy(
                        "clear" if time_zone is None else "explicit",
                        time_zone,
                    )
                else:
                    time_zone_policy = ProviderFieldPolicy("inherit")
                policy = ClientProviderUse(
                    context=context,
                    parent=cast("str | None", inherited_client_owner),
                    locale=ProviderFieldPolicy(
                        "explicit" if locale_is_explicit else "inherit",
                        context.locale if locale_is_explicit else None,
                    ),
                    direction=ProviderFieldPolicy(
                        "explicit" if context_value is not None or direction_given else "inherit",
                        context.direction if context_value is not None or direction_given else None,
                    ),
                    time_zone=time_zone_policy,
                )
            if client:
                host = I18nClientHost
            elif inherited_client_owner is not None:
                host = I18nBarrierHost
            elif tag is not None:
                host = I18nElementHost
            else:
                host = I18nTransparentHost
            return {
                "attrs": attrs,
                "host": host,
                "policy": policy if client else None,
                "tag": tag,
            }

        # One dynamic call keeps the public slot in the checked ownership
        # graph while the selected private host remains unavailable as a tag.
        template = """\
<c-component c-is="host" c-tag="tag" c-attrs="attrs" c-policy="policy"><c-slot /></c-component>\
"""

    return I18nProvider


def make_trans_component(citry_instance: Citry) -> type[Component]:
    """Create and register the transparent rich-message component."""
    extension = cast("Any", citry_instance.extensions.get_extension("i18n"))

    class Trans(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """Render escaped translated text with application-owned named fills."""

        citry = citry_instance
        name = "trans"
        transparent = True

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
            data = dict(kwargs)
            message_id = const_value(data.pop("message", None))
            if type(message_id) is not str or not message_id:
                raise ValueError("<c-trans> requires an exact non-empty 'message' string.")
            attr = const_value(data.pop("attr", None))
            values = data.pop("values", {})
            if data:
                names = ", ".join(sorted(data))
                raise ValueError(f"<c-trans> received unknown attribute(s): {names}.")
            if not isinstance(values, Mapping):
                raise TypeError("<c-trans> values must be a mapping from parameter name to value.")
            fills = dict(self.raw_slots)
            fills.pop("default", None)
            collisions = set(values) & fills.keys()
            if collisions:
                names = ", ".join(sorted(collisions))
                raise ValueError(f"<c-trans> names cannot be both scalar values and fills: {names}.")
            resolved = extension.resolve_rich(
                message_id,
                values=dict(values),
                slots=fills,
                attr=attr,
                context=extension.context_for_component(self),
            )
            cast("Any", self).i18n._usage.record_message(message_id, attr)
            segments: list[dict[str, object]] = []
            for segment in cast("list[dict[str, str]]", resolved["segments"]):
                if segment["type"] == "text":
                    segments.append({"type": "text", "value": segment["value"]})
                else:
                    segments.append({"type": "slot", "value": fills[segment["name"]]})
            return {"segments": segments}

        # This transparent component must not add whitespace between segments.
        template = """\
<c-for each="segment in segments">\
<c-if cond="segment['type'] == 'text'">{{ segment["value"] }}</c-if>\
<c-else><bdi dir="auto">{{ segment["value"] }}</bdi></c-else>\
</c-for>\
"""

    return Trans
