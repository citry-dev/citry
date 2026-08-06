"""Shared root-attribute inputs for styled Citry UI components."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003

from citry import merge_attrs
from citry.attrs import ClassValue as CClassValue
from citry.attrs import StyleValue as CStyleValue


def merge_root_attrs(
    attrs: Mapping[str, object] | None,
    class_: CClassValue | None,
    style: CStyleValue | None,
) -> dict[str, object]:
    """Merge convenient root class/style inputs with the general attribute map."""
    return merge_attrs(
        attrs or {},
        {
            "class": class_,
            "style": style,
        },
    )


__all__ = ["CClassValue", "CStyleValue", "merge_root_attrs"]
