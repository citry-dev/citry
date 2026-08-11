"""Responsive Container and CSS Grid layout components."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, SlotInput, const_value, is_const, merge_attrs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CContainerTag = Literal["div", "main", "section", "article", "nav", "aside"]
CGridTag = Literal["div", "main", "section", "article", "ul", "ol"]
CGridItemTag = Literal["div", "main", "section", "article", "aside", "li"]
CContainerSize = Literal["sm", "md", "lg", "xl", "xxl"]
CLayoutGap = Literal["0", "xs", "sm", "md", "lg", "xl"]

_CONTAINER_TAGS = ("div", "main", "section", "article", "nav", "aside")
_GRID_TAGS = ("div", "main", "section", "article", "ul", "ol")
_GRID_ITEM_TAGS = ("div", "main", "section", "article", "aside", "li")
_CONTAINER_SIZES = ("sm", "md", "lg", "xl", "xxl")
_GAPS = ("0", "xs", "sm", "md", "lg", "xl")
_BREAKPOINTS = ("sm", "md", "lg", "xl", "xxl")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-bind",
        "x-for",
        "x-html",
        "x-if",
        "x-ignore",
        "x-model",
        "x-modelable",
        "x-teleport",
        "x-text",
    }
)
_CONTAINER_OWNED_ATTRS = frozenset(
    {
        "data-citry-ui-part",
        "data-fluid",
        "data-gutter",
        "data-size",
    }
)
_GRID_OWNED_ATTRS = frozenset(
    {
        "data-citry-ui-part",
        "data-cols",
        "data-cols-sm",
        "data-cols-md",
        "data-cols-lg",
        "data-cols-xl",
        "data-cols-xxl",
        "data-gap",
        "data-intrinsic",
    }
)
_GRID_ITEM_OWNED_ATTRS = frozenset(
    {
        "data-citry-ui-part",
        "data-span",
        "data-span-sm",
        "data-span-md",
        "data-span-lg",
        "data-span-xl",
        "data-span-xxl",
    }
)
_CSS_LENGTH_RE = re.compile(
    r"(?P<number>(?:\d+(?:\.\d+)?|\.\d+))(?P<unit>px|rem|em|ch|vw|vh|vmin|vmax)\Z",
    re.ASCII,
)


class CContainerDefaultSlotData:
    pass


class CGridDefaultSlotData:
    pass


class CGridItemDefaultSlotData:
    pass


def _plain_choice(
    component_name: str,
    input_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{component_name} {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"{component_name} could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{component_name} {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _track_count(
    component_name: str,
    input_name: str,
    value: object,
    *,
    optional: bool = False,
) -> int | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    # Flat static template syntax deliberately supports ``sm="2"``. Python
    # and dynamic template expressions remain int-only.
    if is_const(value) and isinstance(raw, str) and raw.isascii() and raw.isdecimal():
        raw = int(raw)
    if isinstance(raw, bool) or not isinstance(raw, int):
        expected = "an integer or None" if optional else "an integer"
        msg = f"{component_name} {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    if raw < 1 or raw > 12:
        msg = f"{component_name} {input_name} must be between 1 and 12, got {raw!r}."
        raise ValueError(msg)
    return raw


def _minimum_column(value: object) -> str | None:
    raw = const_value(value)
    if raw is None:
        return None
    if not isinstance(raw, str):
        msg = f"CGrid min_col must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = "CGrid could not convert min_col to a plain string."
        raise TypeError(msg)
    match = _CSS_LENGTH_RE.fullmatch(plain)
    if match is None or float(match.group("number")) <= 0:
        msg = f"CGrid min_col must be one positive px, rem, em, ch, vw, vh, vmin, or vmax length, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    component_name: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{component_name} attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{component_name} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"{component_name} attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component_name} attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


def _responsive_values(
    component_name: str,
    kwargs: object,
) -> dict[str, int | None]:
    return {
        breakpoint_name: _track_count(
            component_name,
            breakpoint_name,
            getattr(kwargs, breakpoint_name),
            optional=True,
        )
        for breakpoint_name in _BREAKPOINTS
    }


def _responsive_styles(prefix: str, base: int, values: Mapping[str, int | None]) -> dict[str, object]:
    styles: dict[str, object] = {f"--_cui-{prefix}-base": base}
    styles.update(
        {f"--_cui-{prefix}-{breakpoint_name}": value for breakpoint_name, value in values.items() if value is not None}
    )
    return styles


class CContainer(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CContainerTag = "div"
        size: CContainerSize = "xl"
        fluid: bool = False
        gutter: CLayoutGap = "lg"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CContainerDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        tag = _plain_choice("CContainer", "tag", kwargs.tag, _CONTAINER_TAGS)
        size = _plain_choice("CContainer", "size", kwargs.size, _CONTAINER_SIZES)
        gutter = _plain_choice("CContainer", "gutter", kwargs.gutter, _GAPS)
        validate_boolean("CContainer", "fluid", kwargs.fluid)
        fluid = bool(kwargs.fluid)
        if fluid and size != "xl":
            msg = "CContainer fluid=True cannot be combined with a non-default size."
            raise ValueError(msg)
        attrs = _copy_attrs("CContainer", kwargs.attrs, _CONTAINER_OWNED_ATTRS)
        return {
            "tag": tag,
            "size": size,
            "fluid": fluid,
            "gutter": gutter,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-container"
        c-bind="attrs"
        data-citry-ui-part="container"
        c-data-size="size"
        c-data-fluid="fluid"
        c-data-gutter="gutter"
      >
        <c-slot />
      </c-element>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="container"]) {
          --_cui-container-max-width: var(--cui-container-max-width, 80rem);
          --_cui-container-gutter: var(--cui-container-gutter, 1rem);
          box-sizing: border-box;
          inline-size: 100%;
          max-inline-size: var(--_cui-container-max-width);
          min-inline-size: 0;
          margin-inline: auto;
          padding-inline: var(--_cui-container-gutter);
        }

        :where([data-citry-ui-part="container"][data-size="sm"]) {
          --_cui-container-max-width: var(--cui-container-max-width, 40rem);
        }

        :where([data-citry-ui-part="container"][data-size="md"]) {
          --_cui-container-max-width: var(--cui-container-max-width, 48rem);
        }

        :where([data-citry-ui-part="container"][data-size="lg"]) {
          --_cui-container-max-width: var(--cui-container-max-width, 64rem);
        }

        :where([data-citry-ui-part="container"][data-size="xxl"]) {
          --_cui-container-max-width: var(--cui-container-max-width, 96rem);
        }

        :where([data-citry-ui-part="container"][data-fluid]) {
          max-inline-size: none;
        }

        :where([data-citry-ui-part="container"][data-gutter="0"]) {
          --_cui-container-gutter: var(--cui-container-gutter, 0);
        }

        :where([data-citry-ui-part="container"][data-gutter="xs"]) {
          --_cui-container-gutter: var(--cui-container-gutter, 0.25rem);
        }

        :where([data-citry-ui-part="container"][data-gutter="sm"]) {
          --_cui-container-gutter: var(--cui-container-gutter, 0.5rem);
        }

        :where([data-citry-ui-part="container"][data-gutter="md"]) {
          --_cui-container-gutter: var(--cui-container-gutter, 0.75rem);
        }

        :where([data-citry-ui-part="container"][data-gutter="xl"]) {
          --_cui-container-gutter: var(--cui-container-gutter, 1.5rem);
        }
      }
    """


class CGrid(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CGridTag = "div"
        cols: int = 1
        sm: int | None = None
        md: int | None = None
        lg: int | None = None
        xl: int | None = None
        xxl: int | None = None
        min_col: str | None = None
        gap: CLayoutGap = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CGridDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        tag = _plain_choice("CGrid", "tag", kwargs.tag, _GRID_TAGS)
        cols = cast("int", _track_count("CGrid", "cols", kwargs.cols))
        responsive = _responsive_values("CGrid", kwargs)
        min_col = _minimum_column(kwargs.min_col)
        gap = _plain_choice("CGrid", "gap", kwargs.gap, _GAPS)
        if min_col is not None and (cols != 1 or any(value is not None for value in responsive.values())):
            msg = "CGrid min_col cannot be combined with cols other than 1 or responsive column inputs."
            raise ValueError(msg)
        attrs = _copy_attrs("CGrid", kwargs.attrs, _GRID_OWNED_ATTRS)
        private_styles: dict[str, object]
        if min_col is None:
            private_styles = _responsive_styles("grid-cols", cols, responsive)
        else:
            private_styles = {"--_cui-grid-min-column-input": min_col}
        return {
            "tag": tag,
            "cols": cols,
            "sm": responsive["sm"],
            "md": responsive["md"],
            "lg": responsive["lg"],
            "xl": responsive["xl"],
            "xxl": responsive["xxl"],
            "intrinsic": min_col is not None,
            "gap": gap,
            "attrs": merge_attrs(
                merge_root_attrs(attrs, kwargs.class_, kwargs.style),
                {"style": private_styles},
            ),
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-grid"
        c-bind="attrs"
        data-citry-ui-part="grid"
        c-data-cols="cols"
        c-data-cols-sm="sm"
        c-data-cols-md="md"
        c-data-cols-lg="lg"
        c-data-cols-xl="xl"
        c-data-cols-xxl="xxl"
        c-data-intrinsic="intrinsic"
        c-data-gap="gap"
      >
        <c-slot />
      </c-element>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="grid"]) {
          --_cui-grid-cols-sm: initial;
          --_cui-grid-cols-md: initial;
          --_cui-grid-cols-lg: initial;
          --_cui-grid-cols-xl: initial;
          --_cui-grid-cols-xxl: initial;
          --_cui-grid-min-column-input: initial;
          --_cui-grid-cols-through-sm: var(
            --_cui-grid-cols-sm,
            var(--_cui-grid-cols-base)
          );
          --_cui-grid-cols-through-md: var(
            --_cui-grid-cols-md,
            var(--_cui-grid-cols-through-sm)
          );
          --_cui-grid-cols-through-lg: var(
            --_cui-grid-cols-lg,
            var(--_cui-grid-cols-through-md)
          );
          --_cui-grid-cols-through-xl: var(
            --_cui-grid-cols-xl,
            var(--_cui-grid-cols-through-lg)
          );
          --_cui-grid-cols-through-xxl: var(
            --_cui-grid-cols-xxl,
            var(--_cui-grid-cols-through-xl)
          );
          --_cui-grid-effective-columns: var(--_cui-grid-cols-base);
          --_cui-grid-columns: var(
            --cui-grid-columns,
            var(--_cui-grid-effective-columns)
          );
          --_cui-grid-gap: var(--cui-grid-gap, 0.75rem);
          display: grid;
          min-inline-size: 0;
          grid-template-columns: repeat(
            var(--_cui-grid-columns),
            minmax(0, 1fr)
          );
          gap: var(--_cui-grid-gap);
        }

        :where([data-citry-ui-part="grid"][data-intrinsic]) {
          --_cui-grid-min-column: var(
            --cui-grid-min-column,
            var(--_cui-grid-min-column-input, 16rem)
          );
          grid-template-columns: repeat(
            auto-fit,
            minmax(min(100%, var(--_cui-grid-min-column)), 1fr)
          );
        }

        :where([data-citry-ui-part="grid"][data-gap="0"]) {
          --_cui-grid-gap: var(--cui-grid-gap, 0);
        }

        :where([data-citry-ui-part="grid"][data-gap="xs"]) {
          --_cui-grid-gap: var(--cui-grid-gap, 0.25rem);
        }

        :where([data-citry-ui-part="grid"][data-gap="sm"]) {
          --_cui-grid-gap: var(--cui-grid-gap, 0.5rem);
        }

        :where([data-citry-ui-part="grid"][data-gap="lg"]) {
          --_cui-grid-gap: var(--cui-grid-gap, 1rem);
        }

        :where([data-citry-ui-part="grid"][data-gap="xl"]) {
          --_cui-grid-gap: var(--cui-grid-gap, 1.5rem);
        }

        :where([data-citry-ui-part="grid"] > *) {
          min-inline-size: 0;
          min-block-size: 0;
        }

        @media (min-width: 40rem) {
          :where([data-citry-ui-part="grid"]) {
            --_cui-grid-effective-columns: var(--_cui-grid-cols-through-sm);
          }
        }

        @media (min-width: 48rem) {
          :where([data-citry-ui-part="grid"]) {
            --_cui-grid-effective-columns: var(--_cui-grid-cols-through-md);
          }
        }

        @media (min-width: 64rem) {
          :where([data-citry-ui-part="grid"]) {
            --_cui-grid-effective-columns: var(--_cui-grid-cols-through-lg);
          }
        }

        @media (min-width: 80rem) {
          :where([data-citry-ui-part="grid"]) {
            --_cui-grid-effective-columns: var(--_cui-grid-cols-through-xl);
          }
        }

        @media (min-width: 96rem) {
          :where([data-citry-ui-part="grid"]) {
            --_cui-grid-effective-columns: var(--_cui-grid-cols-through-xxl);
          }
        }
      }
    """


class CGridItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CGridItemTag = "div"
        span: int = 1
        sm: int | None = None
        md: int | None = None
        lg: int | None = None
        xl: int | None = None
        xxl: int | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CGridItemDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        tag = _plain_choice("CGridItem", "tag", kwargs.tag, _GRID_ITEM_TAGS)
        span = cast("int", _track_count("CGridItem", "span", kwargs.span))
        responsive = _responsive_values("CGridItem", kwargs)
        attrs = _copy_attrs("CGridItem", kwargs.attrs, _GRID_ITEM_OWNED_ATTRS)
        return {
            "tag": tag,
            "span": span,
            "sm": responsive["sm"],
            "md": responsive["md"],
            "lg": responsive["lg"],
            "xl": responsive["xl"],
            "xxl": responsive["xxl"],
            "attrs": merge_attrs(
                merge_root_attrs(attrs, kwargs.class_, kwargs.style),
                {"style": _responsive_styles("grid-item-span", span, responsive)},
            ),
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-grid-item"
        c-bind="attrs"
        data-citry-ui-part="grid-item"
        c-data-span="span"
        c-data-span-sm="sm"
        c-data-span-md="md"
        c-data-span-lg="lg"
        c-data-span-xl="xl"
        c-data-span-xxl="xxl"
      >
        <c-slot />
      </c-element>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="grid-item"]) {
          --_cui-grid-item-span-sm: initial;
          --_cui-grid-item-span-md: initial;
          --_cui-grid-item-span-lg: initial;
          --_cui-grid-item-span-xl: initial;
          --_cui-grid-item-span-xxl: initial;
          --_cui-grid-item-span-through-sm: var(
            --_cui-grid-item-span-sm,
            var(--_cui-grid-item-span-base)
          );
          --_cui-grid-item-span-through-md: var(
            --_cui-grid-item-span-md,
            var(--_cui-grid-item-span-through-sm)
          );
          --_cui-grid-item-span-through-lg: var(
            --_cui-grid-item-span-lg,
            var(--_cui-grid-item-span-through-md)
          );
          --_cui-grid-item-span-through-xl: var(
            --_cui-grid-item-span-xl,
            var(--_cui-grid-item-span-through-lg)
          );
          --_cui-grid-item-span-through-xxl: var(
            --_cui-grid-item-span-xxl,
            var(--_cui-grid-item-span-through-xl)
          );
          --_cui-grid-item-effective-span: var(--_cui-grid-item-span-base);
          --_cui-grid-item-span: var(
            --cui-grid-item-span,
            var(--_cui-grid-item-effective-span)
          );
          min-inline-size: 0;
          min-block-size: 0;
          grid-column:
            span var(--_cui-grid-item-span) /
            span var(--_cui-grid-item-span);
        }

        @media (min-width: 40rem) {
          :where([data-citry-ui-part="grid-item"]) {
            --_cui-grid-item-effective-span: var(--_cui-grid-item-span-through-sm);
          }
        }

        @media (min-width: 48rem) {
          :where([data-citry-ui-part="grid-item"]) {
            --_cui-grid-item-effective-span: var(--_cui-grid-item-span-through-md);
          }
        }

        @media (min-width: 64rem) {
          :where([data-citry-ui-part="grid-item"]) {
            --_cui-grid-item-effective-span: var(--_cui-grid-item-span-through-lg);
          }
        }

        @media (min-width: 80rem) {
          :where([data-citry-ui-part="grid-item"]) {
            --_cui-grid-item-effective-span: var(--_cui-grid-item-span-through-xl);
          }
        }

        @media (min-width: 96rem) {
          :where([data-citry-ui-part="grid-item"]) {
            --_cui-grid-item-effective-span: var(--_cui-grid-item-span-through-xxl);
          }
        }
      }
    """


__all__ = [
    "CContainer",
    "CContainerDefaultSlotData",
    "CContainerSize",
    "CContainerTag",
    "CGrid",
    "CGridDefaultSlotData",
    "CGridItem",
    "CGridItemDefaultSlotData",
    "CGridItemTag",
    "CGridTag",
    "CLayoutGap",
]
