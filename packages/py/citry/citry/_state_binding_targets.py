"""Pure State binding target and input-direction rules shared by analysis and runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, NoReturn

_TWO_WAY_INPUT_TYPES: Final = frozenset(
    {
        "text",
        "search",
        "tel",
        "url",
        "email",
        "password",
        "date",
        "month",
        "week",
        "time",
        "datetime-local",
        "number",
        "range",
        "color",
        "checkbox",
        "radio",
    }
)
_ONE_WAY_INPUT_TYPES: Final = frozenset({"hidden"})
_UNSUPPORTED_INPUT_TYPES: Final = frozenset({"file", "submit", "image", "reset", "button"})
_HTML_INPUT_TYPES: Final = _TWO_WAY_INPUT_TYPES | _ONE_WAY_INPUT_TYPES | _UNSUPPORTED_INPUT_TYPES

# The HTML elements the client can read a value from and write a value back to
# (`readControlValue` / `applyValueToControl` in the client runtime). A
# `<select multiple>` is included and carries a list of selected option values;
# the live element's `multiple` property decides that shape, so direct and
# dynamic/spread forms share the same path. A state binding on any other plain
# element has nothing to bind, so it is rejected.
# Widening this set is the single place a future "bind anything" feature hooks
# in; the client must learn the element's value shape in the same change.
_KNOWN_FORM_CONTROLS: Final = frozenset({"input", "textarea", "select"})

# Hyphenated names HTML reserves for SVG and MathML elements, so they are not
# custom element names however much they look like one. None of them holds a
# value, so a state binding on one is rejected with everything else.
_RESERVED_HYPHENATED_TAGS: Final = frozenset(
    {
        "annotation-xml",
        "color-profile",
        "font-face",
        "font-face-format",
        "font-face-name",
        "font-face-src",
        "font-face-uri",
        "missing-glyph",
    }
)


def _is_custom_element(tag_name: str) -> bool:
    """
    Whether a tag names a custom element, by HTML's own rule for the name.

    A custom element may expose a value the way a form control does, so a state
    binding is allowed on one. After the browser upgrades the element, the
    client reads and writes that typed property without native-control
    coercion, and the element names its own update event with ``.on:<event>``.

    Pass a lowercased name: HTML tag names are case insensitive, so ``<My-Box>``
    in markup is the custom element ``my-box``.

    A hyphen alone is not enough. HTML reserves a handful of hyphenated names
    for SVG and MathML elements that hold no value, a name must start with an
    ASCII letter, and Citry's own ``c-`` tags are components rather than
    elements (reachable here through ``<c-element is="c-foo">``).
    """
    if not tag_name or tag_name in _RESERVED_HYPHENATED_TAGS or tag_name.startswith("c-"):
        return False
    if not tag_name[0].isascii() or not tag_name[0].isalpha():
        return False
    return "-" in tag_name


@dataclass(frozen=True, slots=True)
class _Element:
    """The element a binding sits on, for the control-type validations."""

    tag_name: str
    input_type: str | None  # the static `type` value, when statically known
    type_static_known: bool  # False when the type is dynamic (e.g. via c-type / c-bind)
    tag_static_known: bool = True  # False for <c-element> whose `is` is dynamic


def _reject(message: str) -> NoReturn:
    raise ValueError(message)


def _validate_binding_target(element: _Element, *, binding_mode: str, attr_name: str) -> str:
    """
    Classify the element a ``:c-*`` binding sits on, or reject it.

    Returns ``"control"`` for a form control the client reads and writes
    directly, ``"custom"`` for a custom element (which must name its own
    update event), and ``"deferred"`` for a computed ``<c-element>`` target.

    Every other plain HTML element is rejected: the client has no value to read
    from it or write to it, so the binding would silently do nothing on the way
    down and write an undefined value on the way up.

    A ``<c-element>`` whose element name is computed cannot be classified while
    its template is loaded. Its compiled spec is re-checked by the final-attrs
    hook against the selected tag before any HTML reaches the browser, so only
    target-dependent checks defer; State and handler ownership still validate
    immediately.
    """
    if not element.tag_static_known:
        return "deferred"
    tag = element.tag_name.lower()
    if tag in _KNOWN_FORM_CONTROLS:
        if tag == "input":
            _validate_input_binding_mode(
                element,
                binding_mode=binding_mode,
                attr_name=attr_name,
            )
        return "control"
    if _is_custom_element(tag):
        return "custom"
    controls = ", ".join(f"<{name}>" for name in sorted(_KNOWN_FORM_CONTROLS))
    _reject(
        f"{attr_name!r}: <{element.tag_name}> holds no value, so a State binding has nothing to bind."
        f" State bindings go on {controls}, or on a custom element that exposes a value."
        f" To react to events on <{element.tag_name}>, use an '@c-*' event binding instead",
    )


def _input_type(element: _Element) -> str | None:
    """Return a known static input keyword, ``""`` for unknown, or ``None`` while dynamic."""
    if not element.type_static_known:
        return None
    raw = element.input_type
    if raw is None or raw == "":
        return "text"
    normalized = raw.lower()
    return normalized if normalized in _HTML_INPUT_TYPES else ""


def _validate_input_binding_mode(element: _Element, *, binding_mode: str, attr_name: str) -> None:
    """
    Enforce the complete HTML input-type/binding-direction matrix.

    A dynamic type is deferred to the final-attrs hook or browser classifier.
    Missing and empty types are Text; a present unknown keyword is rejected
    distinctly from a standard type that Citry deliberately does not bind.
    """
    input_type = _input_type(element)
    if input_type is None:
        return
    if input_type in _TWO_WAY_INPUT_TYPES:
        return
    if input_type == "hidden":
        if binding_mode == "one-way":
            return
        _reject(
            f'{attr_name!r}: <input type="hidden"> supports one-way State bindings only;'
            " it has no user update event. Remove the handler value to make this binding one-way",
        )
    if input_type == "file":
        _reject(
            f'{attr_name!r}: <input type="file"> cannot be bound to State (files cannot live in State);'
            " use an ordinary upload endpoint or a custom transport instead;"
            " Citry's JSON events transport does not carry files",
        )
    if input_type in _UNSUPPORTED_INPUT_TYPES:
        _reject(
            f'{attr_name!r}: <input type="{input_type}"> cannot be bound to State; {input_type} inputs are'
            " action controls, not editable value controls. Use an '@c-*' event binding instead",
        )
    raw = element.input_type or ""
    _reject(
        f'{attr_name!r}: <input type="{raw}"> is not a recognized input type in this Citry version,'
        " so its value and update behavior are unknown. Use a supported standard type",
    )


def _element_of(tag_name: str, attrs: list[tuple[str, str | None]]) -> _Element:
    """
    Read the control type off a parsed tag: a static ``type``, or a dynamic marker.

    HTML attribute names are case insensitive, so every name read here is
    lowercased first. Matching them exactly would let ``TYPE="file"`` walk past
    the checks that ``type="file"`` fails.
    """
    static_type: str | None = None
    dynamic = False
    effective_tag = tag_name
    tag_known = True
    names = [name.lower() for name, _ in attrs]
    if tag_name.startswith("c-") and tag_name[2:].lower() == "element":
        # `<c-element>` renders the element its `is` attribute names, so that
        # name is what the binding actually lands on. Only a literal `is` says
        # which element that is; target-dependent checks for a computed name
        # defer to the final-attrs hook, which sees the selected HTML tag.
        static_is = next((value for name, (_, value) in zip(names, attrs, strict=True) if name == "is"), None)
        computed = any(name in ("c-is", "c-bind") for name in names)
        if static_is and not computed:
            effective_tag = static_is
        else:
            tag_known = False
    for name, (_, value) in zip(names, attrs, strict=True):
        if name == "type":
            static_type = value
        elif name in ("c-type", ":type", "c-bind"):
            # Defer a Python-resolved c-type/spread to the final-attrs hook and
            # an Alpine bind to the live browser classifier. A literal binding
            # is already compiled by then, so both later phases explicitly
            # decode and revalidate its internal spec.
            dynamic = True
    return _Element(
        tag_name=effective_tag,
        input_type=static_type,
        type_static_known=not dynamic,
        tag_static_known=tag_known,
    )


def _custom_update_event_error(tag_name: str, attr_name: str) -> str:
    return (
        f"{attr_name!r}: <{tag_name}> is a custom element, so it has no default update event."
        " Name the event the element fires when its value changes, via '.on:<event>'"
    )
