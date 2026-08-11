"""
Parse-time validation rules derived from component declarations.

A component's typed inputs (the inner ``Kwargs`` and ``Slots`` classes) double
as a contract for the templates that *use* the component. This module turns
the declarations of every component registered on a ``Citry`` instance into
the parser's ``user_rules``, so a parent template fails at parse time (not at
render, and not silently) when it:

- passes an attribute the component's ``Kwargs`` does not declare,
- omits a required (no-default) kwarg,
- fills a slot the component's ``Slots`` does not declare, or
- omits a required (no-default) slot, or
- destructures a field outside a statically known ``SlotInput[T]`` data shape.

The rules are opt-in per dimension: a component without a ``Kwargs`` class
accepts any attributes, one without a ``Slots`` class accepts any fills, and a
component declaring neither gets no rules at all. This mirrors the runtime
contract exactly: constructing ``Kwargs(**raw)`` / ``Slots(**raw)`` already
raises on unknown or missing fields, so the parse-time check only moves the
same error earlier, to where the template is written.

Escape hatches the parser grants on its own: ``c-bind`` bypasses both the
allowed and the required attribute checks (it can supply anything at
runtime), dynamic fill names relax the per-name slot checks, and a fill
inside control flow is exempt from static duplicate detection. So the rules
here never reject a template that could be valid at runtime.

Used by the render pipeline when compiling templates; cached per ``Citry``
instance (see ``Citry._tag_rules``).
"""

from __future__ import annotations

import sys
import types
import typing
from typing import TYPE_CHECKING, Any, get_args, get_origin, get_type_hints

from citry._annotation_introspection import _own_annotations
from citry.slots import SlotInput
from citry.util.misc import get_fields
from citry_core.template_parser import TagRules

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.component import Component

# Control flow can be written as attributes on any tag (`<c-card c-if="x">`),
# so these are always allowed alongside a component's declared kwargs.
_CONTROL_FLOW_ATTRS = ("c-if", "c-elif", "c-else", "c-for", "c-empty")


def build_tag_rules(citry: Citry) -> dict[str, TagRules]:
    """
    Build the parser ``user_rules`` for every component registered on ``citry``.

    Keys are lowercase tag names (``c-`` plus each registered name, so a class
    registered as both ``mycard`` and ``my-card`` gets two entries); the parser
    matches template tags against them case-insensitively. Components that
    declare neither ``Kwargs`` nor ``Slots`` contribute no entry.
    """
    rules: dict[str, TagRules] = {}
    for name, comp_cls in citry.components.items():
        tag_rules = _component_tag_rules(comp_cls)
        if tag_rules is not None:
            rules[f"c-{name}"] = tag_rules
    return rules


def _component_tag_rules(comp_cls: type[Component]) -> TagRules | None:
    """
    Derive one component's ``TagRules`` from its ``Kwargs``/``Slots`` classes.

    The declarations are read with ``util.misc.get_fields``, which understands
    every declaration style the runtime accepts (dataclasses, Pydantic models,
    NamedTuples); an unrecognized style is treated as undeclared, never
    rejected. A field with no default is required.
    """
    kwargs_fields = get_fields(comp_cls.Kwargs)
    slots_fields = get_fields(comp_cls.Slots)
    if kwargs_fields is None and slots_fields is None:
        return None

    allowed_attrs: list[list[str]] | None = None
    required_attrs: list[list[str]] = []
    if kwargs_fields is not None:
        # Each kwarg may be passed statically (`title="x"`) or dynamically
        # (`c-title="expr"`). Both spellings name one logical input, so putting
        # them in one group rejects an explicit duplicate while either form
        # still satisfies the required-input check.
        # `c-bind` needs no entry: the parser always lets it through (it can
        # supply any attribute at runtime).
        allowed_attrs = [[field.name, f"c-{field.name}"] for field in kwargs_fields]
        allowed_attrs += [[attr] for attr in _CONTROL_FLOW_ATTRS]
        required_attrs = [[field.name, f"c-{field.name}"] for field in kwargs_fields if field.required]

    allowed_slots: list[str] | None = None
    required_slots: list[str] = []
    if slots_fields is not None:
        allowed_slots = [field.name for field in slots_fields]
        required_slots = [field.name for field in slots_fields if field.required]

    return TagRules(
        allowed_attrs=allowed_attrs,
        required_attrs=required_attrs,
        allowed_slots=allowed_slots,
        required_slots=required_slots,
        slot_data_fields=_slot_data_fields(comp_cls, allowed_slots or []),
    )


def _slot_data_fields(comp_cls: type[Component], slot_names: list[str]) -> dict[str, list[str]]:
    """Return statically known slot-data field names for typed slots."""
    slots_cls = comp_cls.Slots
    if slots_cls is None:
        return {}

    annotations = _resolved_schema_annotations(comp_cls, slots_cls)
    result: dict[str, list[str]] = {}
    for slot_name in slot_names:
        annotation = annotations.get(slot_name)
        data_shape = _slot_input_data_shape(annotation)
        field_names = _data_shape_field_names(data_shape)
        if field_names is not None:
            result[slot_name] = field_names
    return result


def _resolved_schema_annotations(comp_cls: type[Component], schema_cls: type) -> dict[str, object]:
    """Resolve schema fields independently so one bad annotation stays local."""
    raw_annotations: dict[str, object] = {}
    for candidate in reversed(schema_cls.__mro__):
        if candidate is object:
            continue
        try:
            candidate_annotations = _own_annotations(candidate)
        except (NameError, TypeError, ValueError):
            candidate_annotations = candidate.__dict__.get("__annotations__", {})
        if isinstance(candidate_annotations, dict):
            raw_annotations.update(candidate_annotations)

    module = sys.modules.get(comp_cls.__module__)
    globalns = dict(vars(module)) if module is not None else {}
    localns = dict(globalns)
    localns["SlotInput"] = SlotInput
    for candidate in reversed(comp_cls.__mro__):
        localns.update(vars(candidate))
    for candidate in reversed(schema_cls.__mro__):
        localns.update(vars(candidate))
    localns[comp_cls.__name__] = comp_cls
    localns[schema_cls.__name__] = schema_cls

    resolved: dict[str, object] = {}
    for field_name, annotation in raw_annotations.items():
        resolved[field_name] = _resolve_schema_annotation(annotation, globalns, localns)
    return resolved


def _resolve_schema_annotation(
    annotation: object,
    globalns: dict[str, object],
    localns: dict[str, object],
) -> object:
    """Resolve one annotation without coupling it to its sibling fields."""

    def annotation_probe() -> None:
        pass

    annotation_probe.__annotations__ = {"value": annotation}
    try:
        return get_type_hints(
            annotation_probe,
            globalns=globalns,
            localns=localns,
            include_extras=True,
        )["value"]
    except (AttributeError, NameError, SyntaxError, TypeError, ValueError):
        return annotation


def _slot_input_data_shape(annotation: object) -> object | None:
    """Unwrap ``SlotInput[T]`` with optional ``None`` and ``Annotated``."""
    if annotation is None:
        return None

    origin = get_origin(annotation)
    if origin is typing.Annotated:
        arguments = get_args(annotation)
        return _slot_input_data_shape(arguments[0]) if arguments else None
    if origin in {typing.Union, types.UnionType}:
        members = [member for member in get_args(annotation) if member is not type(None)]
        return _slot_input_data_shape(members[0]) if len(members) == 1 else None
    if origin is not SlotInput:
        return None

    arguments = get_args(annotation)
    if len(arguments) != 1 or arguments[0] is Any or arguments[0] is object:
        return None
    return arguments[0]


def _data_shape_field_names(data_shape: object | None) -> list[str] | None:
    """Read the finite field set of one supported slot-data shape."""
    if not isinstance(data_shape, type) or vars(data_shape).get("__module__") == "builtins":
        return None

    schema_fields = get_fields(data_shape)
    if schema_fields is not None:
        return [field.name for field in schema_fields]

    annotations: dict[str, object] = {}
    for candidate in reversed(data_shape.__mro__):
        if candidate is object:
            continue
        try:
            candidate_annotations = _own_annotations(candidate)
        except (NameError, TypeError, ValueError):
            candidate_annotations = candidate.__dict__.get("__annotations__", {})
        if not isinstance(candidate_annotations, dict):
            return None
        for name, annotation in candidate_annotations.items():
            if _is_classvar(annotation):
                annotations.pop(name, None)
        annotations.update(
            {name: annotation for name, annotation in candidate_annotations.items() if not _is_classvar(annotation)}
        )

    return list(annotations)


def _is_classvar(annotation: object) -> bool:
    """Recognize runtime and postponed ``ClassVar`` annotations."""
    if annotation is typing.ClassVar or get_origin(annotation) is typing.ClassVar:
        return True
    if not isinstance(annotation, str):
        return False
    compact = annotation.replace(" ", "")
    return compact == "ClassVar" or compact.startswith(("ClassVar[", "typing.ClassVar["))
