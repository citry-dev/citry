"""The transparent ``<c-cache>`` component owned by the Cache extension."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from citry.component import Component

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.slots import SlotInput


def make_cache_component(citry_instance: Citry) -> type[Component]:
    """Create and register the ``<c-cache>`` component for one Citry instance."""
    cache_extension = cast("Any", citry_instance.extensions.get_extension("cache"))
    default_ttl = cache_extension._defaults.ttl

    class Cache(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """
        Save the HTML of the wrapped part of a template and reuse it on later renders.

        ``key`` (required) names the cached part. Templates that use the same
        ``key`` share saved HTML, so list in ``vary`` every value that can
        change the output, such as the user id or the locale: each
        combination gets its own saved copy. ``ttl`` is how many seconds a
        copy stays saved (by default, the app's cache setting); with
        ``None`` it never expires, and
        ``0`` turns caching off. Change ``version`` to stop reusing the
        copies saved under the old value, for example after you change what
        the wrapped part shows. ``enabled=False`` also turns caching off.
        Citry does not look at the wrapped content when it builds the key,
        and the tag adds no HTML of its own.
        """

        citry = citry_instance
        name = "cache"
        transparent = True

        class Kwargs:
            key: str
            vary: Any = ()
            ttl: float | None = default_ttl
            version: int | str = 1
            enabled: bool = True

        class Slots:
            default: SlotInput | None = None

        template = """\
<c-slot />\
"""

    return Cache
