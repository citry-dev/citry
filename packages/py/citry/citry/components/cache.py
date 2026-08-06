"""The transparent ``<c-cache>`` built-in component."""

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
        Cache and replay one named transparent template region.

        ``key`` is a required stable fragment name. ``vary`` contains every
        caller-dependent value that can change the body, ``ttl`` controls expiry,
        ``version`` selects an author-controlled invalidation family, and
        ``enabled=False`` bypasses caching. The body is not inspected or included
        in the key, and a hit emits no wrapper element.
        """

        citry = citry_instance
        name = "cache"
        transparent = True
        template = """\
<c-slot />\
"""

        class Kwargs:
            key: str
            vary: Any = ()
            ttl: float | None = default_ttl
            version: int | str = 1
            enabled: bool = True

        class Slots:
            default: SlotInput | None = None

    return Cache
