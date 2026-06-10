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
- omits a required (no-default) slot.

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

from typing import TYPE_CHECKING

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
    for name, comp_cls in citry.registry.all().items():
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
        # (`c-title="expr"`); putting both spellings in one group also makes
        # them mutually exclusive. `c-bind` needs no entry: the parser always
        # lets it through (it can supply any attribute at runtime).
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
    )
