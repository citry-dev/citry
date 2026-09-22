"""The ``<c-mark>`` built-in component."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from citry.citry_element import CitryElement
from citry.component import Component
from citry.constness import const_value

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_render import CitryRender
    from citry.slots import SlotInput


_MARK_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")


class _SyntheticMarkElement(CitryElement):
    """Exact private element type for one replacement wrapper."""


def synthetic_mark_replacement(mark_class: type[Component], name: str, body: CitryRender) -> CitryElement:
    """Build one exact private wrapper without authorizing nested Marks."""
    return _SyntheticMarkElement(mark_class, {"name": name}, {"default": body})


def validate_mark_name(value: object) -> str:
    """Return one validated, case-sensitive marker name."""
    name = const_value(value)
    if type(name) is not str or _MARK_NAME.fullmatch(name) is None:
        raise ValueError("<c-mark> name must match [A-Za-z][A-Za-z0-9_-]*.")
    return name


def make_mark_component(citry_instance: Citry) -> type[Component]:
    """Create the engine-owned, nontransparent ``<c-mark>`` component."""

    class Mark(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """Keep one named default-slot region addressable in prepared Vue output."""

        citry = citry_instance
        name = "mark"
        template = "<c-slot />"

        class Kwargs:
            name: str

        class Slots:
            default: SlotInput | None = None

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
            if set(self.raw_kwargs) != {"name"}:
                raise ValueError("<c-mark> requires exactly one 'name' attribute.")
            unexpected_slots = set(self.raw_slots) - {"default"}
            if unexpected_slots:
                raise ValueError("<c-mark> accepts only its default slot.")
            self._citry_mark_name = validate_mark_name(kwargs.name)
            return {}

    return Mark


__all__ = ["make_mark_component", "synthetic_mark_replacement", "validate_mark_name"]
