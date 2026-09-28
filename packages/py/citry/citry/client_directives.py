"""Shared validation for Citry directives evaluated by the browser runtime."""

from __future__ import annotations

import re
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
    SHOW = "show"
    # `v-if`, `v-else-if`, or `v-else`: decides whether the call renders.
    CONDITION = "condition"
    # `v-model` in any argument or modifier form: a prop and its update listener.
    MODEL = "model"
    # A custom directive the caller registered, applied to the child's root element.
    DIRECTIVE = "directive"


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


_SLOT_CONDITION_HINT = (
    "Wrap the slot in '<template v-if=\"...\">' for a browser-side condition, or use '<c-if>' when Python decides."
)
_CONTENT_HINT = (
    "This directive would replace the child's own content. Pass the value as a prop or through '<c-fill>' and "
    "render it inside the child."
)
_CONDITION_FORM_HINT = "Write 'v-if', 'v-else-if', and 'v-else' without an argument or modifiers."
_ONCE_MEMO_HINT = (
    "Citry does not support 'v-once' or 'v-memo' in component templates, "
    "on elements or component tags. Remove the directive."
)
# What to write instead, by directive name. The template parser reports the
# same wording for attributes written directly in a template.
_COMPONENT_TAG_DIRECTIVE_HINTS = {
    "if": _CONDITION_FORM_HINT,
    "else-if": _CONDITION_FORM_HINT,
    "else": _CONDITION_FORM_HINT,
    "for": "A browser 'v-for' cannot create Citry components. Repeat the component with '<c-for>'.",
    "slot": "Pass slot content with '<c-fill name=\"...\">' inside the component tag.",
    "html": _CONTENT_HINT,
    "text": _CONTENT_HINT,
    "show": "Write 'v-show' without an argument or modifiers.",
    "model": "Name the prop after 'v-model:', or write 'v-model' alone for 'modelValue'.",
    "bind": "Bind an object with a plain 'v-bind=\"...\"', or bind each prop as ':name=\"...\"'.",
    "on": (
        "Write each listener as '@event=\"...\"' or 'v-on:event=\"...\"', "
        "or bind a listener object with a plain 'v-on=\"...\"'."
    ),
    "prop": "Pass the value as a component prop with ':name=\"...\"'.",
    # Pointing these at an element inside the child would only move the
    # failure, because component templates reject them everywhere.
    "once": _ONCE_MEMO_HINT,
    "memo": _ONCE_MEMO_HINT,
}
# Vue's own directives that never pass through a component tag unchanged.
# Any other `v-` name is a custom directive the caller registered. Mirrors
# `VUE_BUILT_IN_DIRECTIVES` in the template parser.
_VUE_BUILT_IN_DIRECTIVES = frozenset(
    {
        "bind",
        "on",
        "show",
        "if",
        "else-if",
        "else",
        "for",
        "model",
        "slot",
        "html",
        "text",
        "once",
        "memo",
        "cloak",
        "pre",
        "is",
    }
)
_CONDITION_KEYS = frozenset({"v-if", "v-else-if", "v-else"})
_OTHER_DIRECTIVE_HINT = "Put the directive on an element inside the child's template."


def _vue_directive_name(key: str) -> str | None:
    """Return the Vue directive ``key`` spells, without argument or modifiers."""
    if key.startswith("#"):
        # `#c-*` is Citry metadata; any other `#name` is Vue's slot shorthand.
        return None if key.startswith("#c-") else "slot"
    if len(key) > 1 and key.startswith("."):
        # `.name` is Vue's shorthand for binding a DOM property.
        return "prop"
    if not key.startswith("v-"):
        return None
    return re.split(r"[:.]", key[2:], maxsplit=1)[0]


def _is_custom_vue_directive(directive: str) -> bool:
    """
    Return whether a directive name (without its ``v-``) names a custom directive.

    ``v-c-*`` and ``v-citry-*`` belong to Citry's own browser runtime (the
    translation and Events bindings), so a component tag does not pass them on.
    """
    # Compared in lowercase, so `v-If` is not taken for a custom directive
    # that Vue would look up and skip without an error.
    lowercase = directive.lower()
    return bool(directive) and lowercase not in _VUE_BUILT_IN_DIRECTIVES and not lowercase.startswith(("c-", "citry-"))


def unsupported_component_tag_directive_message(key: str, *, tag_name: str) -> str | None:
    """
    Explain why a Vue directive cannot sit on a Citry component tag.

    Returns ``None`` for the directives a component tag carries: ``v-bind``
    and ``v-on`` (with their ``:`` and ``@`` forms and their object forms), the ``v-if`` chain,
    ``v-model``, a bare ``v-show``, and custom directives. The template
    parser reports the same wording for directly authored attributes; this
    covers keys that only appear at render time.
    """
    directive = _vue_directive_name(key)
    if directive is None:
        return None
    # Props, one props object, listeners, and one listener object cross the
    # boundary; the argument-less `v-bind.prop` form has no translation.
    # The condition directives and `v-show` take no argument or modifiers.
    # `v-model:` or `v-on:` with nothing after the colon names no prop or event.
    _, colon, argument = key.partition(":")
    empty_argument = bool(colon) and (not argument or argument.startswith("."))
    if not empty_argument:
        if key in {"v-bind", "v-on", "v-show", *_CONDITION_KEYS} or key.startswith(("v-bind:", "v-on:")):
            return None
        if key.startswith("v-") and (directive == "model" or _is_custom_vue_directive(directive)):
            return None
    if directive.lower() != directive:
        hint = "Vue's own directives and Citry's 'v-c-*' and 'v-citry-*' names are lowercase."
    elif directive.startswith(("c-", "citry-")):
        hint = "Citry reserves 'v-c-*' and 'v-citry-*' for its own browser runtime."
    else:
        hint = _COMPONENT_TAG_DIRECTIVE_HINTS.get(directive, _OTHER_DIRECTIVE_HINT)
    return f"Vue directive {key!r} is not supported on the component tag '<{tag_name}>'. {hint}"


# What to write instead of a Vue directive on `<c-slot>`, by directive name.
# The template parser reports the same wording for attributes written
# directly in a template.
_SLOT_DATA_HINT = (
    "Vue slot props are not supported. Pass Python slot data as a plain attribute ('item=\"text\"') or a "
    "'c-' attribute ('c-item=\"expr\"')."
)
_SLOT_TAG_DIRECTIVE_HINTS = {
    "if": _SLOT_CONDITION_HINT,
    "else-if": _SLOT_CONDITION_HINT,
    "else": _SLOT_CONDITION_HINT,
    "for": "Repeat the slot with '<c-for>'.",
    "show": "Wrap the slot in an element that carries 'v-show'.",
    "slot": "Name the slot with 'name=\"...\"'; the caller fills it with '<c-fill name=\"...\">'.",
    "bind": _SLOT_DATA_HINT,
    "on": "Put the listener on an element around the slot or inside the fill.",
    "prop": _SLOT_DATA_HINT,
}
_OTHER_SLOT_DIRECTIVE_HINT = "Put the directive on an element around the slot or inside its fallback content."


def unsupported_slot_tag_directive_message(key: Any) -> str | None:
    """
    Explain why a Vue directive cannot sit on `<c-slot>`.

    Every `<c-slot>` attribute other than its name and `required` becomes
    Python slot data, so a Vue directive there would reach the fill as a data
    key and never reach the browser. Returns ``None`` for any other key. The
    template parser reports the same wording for directly authored attributes;
    this covers keys that only appear at render time through `c-bind`.
    """
    if not isinstance(key, str):
        return None
    # The `:` and `@` shorthands spell `v-bind` and `v-on`; `v-*`, `#name`,
    # and `.name` are named by the shared helper.
    if key.startswith(":"):
        directive: str | None = "bind"
    elif key.startswith("@"):
        directive = "on"
    else:
        directive = _vue_directive_name(key)
    if directive is None:
        return None
    hint = _SLOT_TAG_DIRECTIVE_HINTS.get(directive, _OTHER_SLOT_DIRECTIVE_HINT)
    return (
        f"Vue directive {key!r} is not supported on '<c-slot>'. Its attributes other than 'name' and 'required' "
        f"become Python slot data, which the browser never sees. {hint}"
    )


def classify_component_tag_client_binding_key(
    key: Any, *, tag_name: str, component_boundary: bool = True
) -> ComponentTagClientBindingKind | None:
    """
    Classify one resolved component attribute key as a client binding.

    ``component_boundary=False`` is the ``<c-element>`` case: that tag renders
    a plain HTML element, so every Vue directive stays valid on it.

    Raises:
        RuntimeError: When ``key`` is a Vue directive that a component tag
            cannot carry. Returning ``None`` would make it a Python kwarg that
            the child silently ignores.

    """
    if not isinstance(key, str):
        return None
    unsupported = unsupported_component_tag_directive_message(key, tag_name=tag_name) if component_boundary else None
    if unsupported is not None:
        raise RuntimeError(unsupported)
    if key == "v-show":
        return ComponentTagClientBindingKind.SHOW
    if key in _CONDITION_KEYS:
        return ComponentTagClientBindingKind.CONDITION
    if key == "v-model" or key.startswith(("v-model:", "v-model.")):
        return ComponentTagClientBindingKind.MODEL
    # A component-boundary check above has already rejected every other
    # built-in directive, so a remaining `v-` name is a custom directive.
    if component_boundary and key.startswith("v-") and _vue_directive_name(key) not in {"bind", "on"}:
        return ComponentTagClientBindingKind.DIRECTIVE
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
    # `v-else` and a custom directive may be written without a value, which
    # the template stores as `True`. The empty text writes the bare name.
    valueless = key == "v-else" or kind is ComponentTagClientBindingKind.DIRECTIVE
    if valueless and (raw_value is True or (isinstance(raw_value, str) and not raw_value.strip())):
        return ""
    if key == "v-else":
        msg = f"'v-else' on <{tag_name}> takes no value, got {raw_value!r}."
        raise TypeError(msg)
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
        elif kind in {ComponentTagClientBindingKind.SHOW, ComponentTagClientBindingKind.CONDITION}:
            msg = (
                f"{key!r} on <{tag_name}> must be a non-empty client expression string, "
                f"got {type(raw_value).__name__}."
            )
        elif kind == ComponentTagClientBindingKind.MODEL:
            msg = (
                f"{key!r} on <{tag_name}> must name a non-empty client expression string, "
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
