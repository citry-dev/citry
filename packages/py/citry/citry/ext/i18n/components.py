"""The server-side components owned by the i18n extension."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from citry.component import Component
from citry.constness import const_value

from .config import direction_for, fallback_chain
from .context import LocaleContext
from .timezone import load_time_zone, tzdb_revision

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.slots import SlotInput


def make_i18n_component(citry_instance: Citry) -> type[Component]:
    """Create and register the subtree locale provider for one engine."""
    extension = cast("Any", citry_instance.extensions.get_extension("i18n"))

    class I18nProvider(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """Set locale context below this tag and optionally render a semantic host."""

        citry = citry_instance
        name = "i18n"
        transparent = True

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
            if client:
                raise ValueError(
                    "<c-i18n client> needs the browser locale-switching stage, which is not installed yet. "
                    "Use server navigation or omit 'client' for this release."
                )
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
            return {
                "tag": tag,
                "attrs": {"lang": context.locale, "dir": context.direction},
            }

        # This transparent component must not add whitespace around its Slot.
        template = """\
<c-if cond="tag"><c-element c-is="tag" c-bind="attrs"><c-slot /></c-element></c-if><c-else><c-slot /></c-else>\
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
