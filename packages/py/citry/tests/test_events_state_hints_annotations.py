"""
State field types resolve when the class body has no ``from __future__ import annotations``.

This module deliberately leaves out that import: on Python 3.14 the class
then keeps no ``__annotations__`` entry, only a function that builds it, and
the field-by-field fallback must still find every field.
"""

from citry.ext.events.tokens import _resolve_hints


def test_one_unresolvable_field_leaves_the_other_fields_checked() -> None:
    class State:
        count: int
        other: "Missing"  # type: ignore[name-defined]  # noqa: F821 - deliberately unresolvable

    # The whole-class read fails on `Missing`, so the fields resolve one by
    # one: `count` keeps its type check, `other` falls back to lenient.
    assert _resolve_hints(State) == {"count": int}
