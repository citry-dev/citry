"""Shared validation for Citry directives evaluated by the browser runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from citry.constness import const_value
from citry.ext.dependencies.scripts import uses_component

if TYPE_CHECKING:
    from collections.abc import Iterable

    from citry.component import Component
    from citry.nodes import HtmlAttr

CLIENT_PROPS_ATTR = "$c-props"


class ComponentTagClientBindingKind(str, Enum):
    """The client behaviors resolved from a nested component tag."""

    PROP = "prop"
    PROPS_OBJECT = "props-object"
    EVENTS_OBJECT = "events-object"
    EVENT = "event"
    REF_STATIC = "ref-static"
    REF_EXPRESSION = "ref-expression"
    CITRY_HANDLER = "citry-handler"


class ComponentTagClientBindingSource(str, Enum):
    """How the winning component-tag client binding was authored."""

    DIRECT = "direct"
    SERVER_DYNAMIC = "server-dynamic"
    SPREAD = "spread"


@dataclass(frozen=True, slots=True)
class ComponentTagClientBinding:
    """One source-ordered browser binding retained on a Citry component call."""

    kind: ComponentTagClientBindingKind
    key: str
    value: str
    source: object
    span: tuple[int, int]
    _authored_attr: object | None = field(default=None, init=False, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class RuntimeComponentEventBinding:
    """One data-resolved server event from an authenticated ``c-bind`` attribute."""

    key: str
    value: str
    source: object
    span: tuple[int, int]
    _spread_attr: object | None = field(default=None, init=False, repr=False, compare=False)


def authenticated_component_tag_client_binding(
    *,
    kind: ComponentTagClientBindingKind,
    key: str,
    value: str,
    authored_attr: HtmlAttr,
) -> ComponentTagClientBinding:
    """Create a binding carrying its compiler-issued parser attribute identity."""
    binding = ComponentTagClientBinding(
        kind=kind,
        key=key,
        value=value,
        source=authored_attr.source,
        span=authored_attr.position,
    )
    object.__setattr__(binding, "_authored_attr", authored_attr)
    return binding


def is_authenticated_component_tag_client_binding(binding: ComponentTagClientBinding) -> bool:
    """Verify that a binding still names its exact compiler-issued static attribute."""
    from citry.nodes import StaticHtmlAttr  # noqa: PLC0415

    attr = binding._authored_attr
    return bool(
        type(attr) is StaticHtmlAttr
        and attr.key == binding.key
        and attr.source is binding.source
        and attr.position == binding.span
    )


def authenticated_runtime_component_event_binding(
    *, key: str, value: str, spread_attr: HtmlAttr
) -> RuntimeComponentEventBinding:
    """Create a runtime event binding tied to its compiler-issued ``c-bind`` attribute."""
    if type(key) is not str or type(value) is not str:
        raise TypeError("runtime component event key and handler must be exact strings")
    binding = RuntimeComponentEventBinding(key, value, spread_attr.source, spread_attr.position)
    object.__setattr__(binding, "_spread_attr", spread_attr)
    return binding


def is_authenticated_runtime_component_event_binding(binding: RuntimeComponentEventBinding) -> bool:
    """Verify the exact compiler-issued spread attribute behind one runtime event."""
    from citry.nodes import ExprHtmlAttr  # noqa: PLC0415

    attr = binding._spread_attr
    return bool(
        type(attr) is ExprHtmlAttr
        and attr.key == "c-bind"
        and attr.source is binding.source
        and attr.position == binding.span
    )


def is_client_props_key(key: Any, *, tag_name: str) -> bool:
    """Return whether ``key`` is canonical, rejecting case variants."""
    if not isinstance(key, str):
        return False
    if key == CLIENT_PROPS_ATTR:
        return True
    if key.lower() == CLIENT_PROPS_ATTR:
        msg = (
            f"Citry client directive names are lowercase; {key!r} resolved on "
            f"<{tag_name}>. Write {CLIENT_PROPS_ATTR!r}."
        )
        raise RuntimeError(msg)
    return False


def has_client_props_key(keys: Iterable[Any], *, tag_name: str) -> bool:
    """Validate dynamic keys and report whether the canonical key is present."""
    found = False
    for key in keys:
        if is_client_props_key(key, tag_name=tag_name):
            found = True
    return found


def classify_component_tag_client_binding_key(key: Any, *, tag_name: str) -> ComponentTagClientBindingKind | None:
    """Classify one resolved component attribute key as a client binding."""
    if not isinstance(key, str):
        return None
    if is_client_props_key(key, tag_name=tag_name):
        raise RuntimeError(f"{CLIENT_PROPS_ATTR!r} was removed; use native Vue :prop or v-bind syntax")
    if key.startswith("@c-"):
        return ComponentTagClientBindingKind.CITRY_HANDLER
    if key == "v-on":
        return ComponentTagClientBindingKind.EVENTS_OBJECT
    if key.startswith(("@", "v-on:")):
        return ComponentTagClientBindingKind.EVENT
    if key == "v-bind" or key.startswith("v-bind."):
        return ComponentTagClientBindingKind.PROPS_OBJECT
    if key in {":ref", "v-bind:ref"}:
        return ComponentTagClientBindingKind.REF_EXPRESSION
    if key.startswith((":", "v-bind:")):
        return ComponentTagClientBindingKind.PROP
    if key == "ref":
        return ComponentTagClientBindingKind.REF_STATIC
    return None


def resolve_component_tag_client_binding_value(
    key: str,
    value: Any,
    *,
    tag_name: str,
    kind: ComponentTagClientBindingKind,
) -> str | None:
    """Validate one source-ordered client-binding value, returning text or removal."""
    raw_value = const_value(value)
    if raw_value is None or raw_value is False:
        return None
    if raw_value is True or not isinstance(raw_value, str) or not raw_value.strip():
        if kind is ComponentTagClientBindingKind.EVENTS_OBJECT:
            msg = (
                f"Object event binding {key!r} on <{tag_name}> must resolve to a non-empty "
                f"client expression string, got {type(raw_value).__name__}."
            )
        elif kind in {ComponentTagClientBindingKind.PROP, ComponentTagClientBindingKind.PROPS_OBJECT}:
            msg = (
                f"{CLIENT_PROPS_ATTR} on <{tag_name}> must resolve to a non-empty client expression string, "
                f"got {type(raw_value).__name__}."
            )
        elif kind == ComponentTagClientBindingKind.EVENT:
            msg = (
                f"Boundary handler {key!r} on <{tag_name}> must resolve to a non-empty client expression string, "
                f"got {type(raw_value).__name__}."
            )
        else:
            msg = (
                f"Citry boundary event {key!r} on <{tag_name}> must resolve to a non-empty server-handler "
                f"binding string, got {type(raw_value).__name__}."
            )
        raise TypeError(msg)
    return raw_value


def apply_client_props_contribution(
    target: dict[str, Any],
    value: Any,
    *,
    tag_name: str,
    component_boundary: bool,
) -> None:
    """Apply one source-ordered client props contribution to ``target``."""
    raw_value = const_value(value)
    if raw_value is None or raw_value is False:
        target.pop(CLIENT_PROPS_ATTR, None)
        return

    if not component_boundary:
        msg = (
            f"{CLIENT_PROPS_ATTR!r} is only valid on a Citry component tag; "
            f"it resolved on <{tag_name}>, which renders plain HTML."
        )
        raise RuntimeError(msg)

    if raw_value is True or not isinstance(raw_value, str):
        msg = (
            f"{CLIENT_PROPS_ATTR} on <{tag_name}> must resolve to a non-empty client expression string, "
            f"got {type(raw_value).__name__}."
        )
        raise TypeError(msg)
    if not raw_value.strip():
        msg = f"{CLIENT_PROPS_ATTR} on <{tag_name}> must resolve to a non-empty client expression string."
        raise TypeError(msg)

    target[CLIENT_PROPS_ATTR] = value


def validate_client_props_target(
    component_class: type[Component],
    binding_keys: Iterable[str],
    *,
    tag_name: str,
) -> None:
    """Require a target-side ``$component`` registration for a resolved props supply."""
    if CLIENT_PROPS_ATTR not in binding_keys or uses_component(component_class):
        return
    msg = (
        f"{CLIENT_PROPS_ATTR} on <{tag_name}> cannot be delivered because target component "
        f"{component_class.__name__!r} has no $component(...) registration in its JavaScript. "
        f"Add a $component(...) registration to {component_class.__name__}.js or remove {CLIENT_PROPS_ATTR}."
    )
    raise RuntimeError(msg)
