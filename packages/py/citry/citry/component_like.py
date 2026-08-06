"""Contextual composition for values that become components during rendering."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from citry.citry_element import CitryElement

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry import Citry
else:
    Citry = Any

_CURRENT_RENDER_CITRY: ContextVar[Citry | None] = ContextVar("citry_component_like_instance", default=None)


@runtime_checkable
class ComponentLike(Protocol):
    """
    A value that composes a component for the Citry instance rendering it.

    Implement this structural protocol when a third-party object should work
    in template expressions or slot values without itself being a
    [`Component`][citry.Component]. Citry resolves the object once at the
    render site and verifies that the returned element belongs to the exact
    active instance.

    Example:
        ::

            class NoticeValue:
                def __citry_element__(self, citry, /):
                    Notice = citry.get("Notice")
                    return Notice(message="Saved")

    """

    def __citry_element__(self, citry: Citry, /) -> CitryElement:
        """
        Compose this value into an element associated with ``citry``.

        Args:
            citry: The exact Citry instance active at the render site.

        Returns:
            A [`CitryElement`][citry.CitryElement] whose component class is
            associated with ``citry``.

        """
        ...


@contextmanager
def _component_like_render_scope(citry: Citry) -> Iterator[None]:
    """Expose only the Citry instance active for this render task or thread."""
    token = _CURRENT_RENDER_CITRY.set(citry)
    try:
        yield
    finally:
        _CURRENT_RENDER_CITRY.reset(token)


def _resolve_component_like(value: ComponentLike, citry: Citry | None = None) -> CitryElement:
    """Resolve and validate one component-like value exactly once."""
    active_citry = citry if citry is not None else _CURRENT_RENDER_CITRY.get()
    if active_citry is None:
        msg = (
            f"Cannot resolve {type(value).__name__!r} without a Citry render context. "
            "Resolve it explicitly or render it inside a component tree."
        )
        raise RuntimeError(msg)

    element = value.__citry_element__(active_citry)
    if not isinstance(element, CitryElement):
        msg = (
            f"{type(value).__name__}.__citry_element__() returned {type(element).__name__!r}; expected a CitryElement."
        )
        raise TypeError(msg)
    if element.comp_cls.citry is not active_citry:
        msg = (
            f"{type(value).__name__}.__citry_element__() returned an element whose component class "
            "is associated with a different Citry instance."
        )
        raise ValueError(msg)
    return element


def _bind_citry_runtime_type(citry_type: type[Citry]) -> None:
    """Complete the protocol's public runtime annotation after Citry is defined."""
    globals()["Citry"] = citry_type


__all__ = ["ComponentLike"]
