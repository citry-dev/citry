"""Composable decorative Skeleton primitives."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CSkeletonKind = Literal["rect", "text", "circle"]
CSkeletonAnimation = Literal["pulse", "wave", "none"]

_KINDS = ("rect", "text", "circle")
_ANIMATIONS = ("pulse", "wave", "none")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-animation",
        "data-citry-ui-part",
        "data-kind",
        "role",
        "tabindex",
    }
)


def _plain_string(input_name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"CSkeleton {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CSkeleton could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if not plain:
        msg = f"CSkeleton {input_name} must be non-empty."
        raise ValueError(msg)
    if "\x00" in plain or any(token in plain for token in (";", "{", "}", "/*", "*/")):
        msg = f"CSkeleton {input_name} must be one CSS length or percentage."
        raise ValueError(msg)
    return plain


def _choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = cast("str", _plain_string(input_name, value))
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CSkeleton {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _lines(value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = f"CSkeleton lines must be a positive integer, got {raw!r}."
        raise TypeError(msg)
    if raw < 1:
        msg = f"CSkeleton lines must be at least 1, got {raw!r}."
        raise ValueError(msg)
    if raw > 100:
        msg = f"CSkeleton lines must be at most 100, got {raw!r}."
        raise ValueError(msg)
    return raw


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CSkeleton attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CSkeleton attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CSkeleton attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CSkeleton attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _OWNED_ATTRS:
            msg = f"CSkeleton attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CSkeleton(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        kind: CSkeletonKind = "rect"
        lines: int = 1
        animation: CSkeletonAnimation = "pulse"
        width: str | None = None
        height: str | None = None
        last_line_width: str = "70%"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        kind = _choice("kind", kwargs.kind, _KINDS)
        animation = _choice("animation", kwargs.animation, _ANIMATIONS)
        lines = _lines(kwargs.lines)
        width = _plain_string("width", kwargs.width, optional=True)
        height = _plain_string("height", kwargs.height, optional=True)
        last_line_width = _plain_string("last_line_width", kwargs.last_line_width)
        if lines != 1 and kind != "text":
            msg = "CSkeleton lines other than 1 require kind='text'."
            raise ValueError(msg)
        if kind == "circle":
            if width is not None and height is not None and width != height:
                msg = "CSkeleton circle width and height must match when both are supplied."
                raise ValueError(msg)
            width = width or height
            height = height or width

        owned_style: dict[str, str] = {}
        if width is not None:
            owned_style["--cui-skeleton-width"] = width
        if height is not None:
            owned_style["--cui-skeleton-height"] = height
        if lines > 1:
            owned_style["--cui-skeleton-last-line-width"] = cast("str", last_line_width)
        styles: list[CStyleValue] = []
        if kwargs.style is not None:
            styles.append(kwargs.style)
        if owned_style:
            styles.append(owned_style)
        return {
            "kind": kind,
            "animation": animation,
            "lines": tuple(range(lines)),
            "has_multiple_lines": lines > 1,
            "attrs": merge_root_attrs(
                _copy_attrs(kwargs.attrs),
                kwargs.class_,
                styles or None,
            ),
        }

    template = """
      <span
        class="cui-skeleton"
        c-bind="attrs"
        data-citry-ui-part="skeleton"
        c-data-kind="kind"
        c-data-animation="animation"
        aria-hidden="true"
      >
        <c-if cond="kind == 'text'">
          <span
            c-for="line in lines"
            class="cui-skeleton__line"
            data-citry-ui-part="line"
            c-data-last="has_multiple_lines and line == lines[-1]"
          ></span>
        </c-if>
      </span>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="skeleton"]) {
          --_cui-skeleton-width: var(--cui-skeleton-width, 100%);
          --_cui-skeleton-height: var(--cui-skeleton-height, 6rem);
          --_cui-skeleton-radius: var(--cui-skeleton-radius, 0.5rem);
          --_cui-skeleton-background: var(--cui-skeleton-background, light-dark(#e7e5e4, #44403c));
          --_cui-skeleton-highlight: var(--cui-skeleton-highlight, rgb(255 255 255 / 45%));
          --_cui-skeleton-gap: var(--cui-skeleton-gap, 0.5em);
          --_cui-skeleton-duration: var(--cui-skeleton-duration, 1.5s);
          --_cui-skeleton-last-line-width: var(--cui-skeleton-last-line-width, 70%);
          position: relative;
          display: inline-block;
          box-sizing: border-box;
          inline-size: min(100%, var(--_cui-skeleton-width));
          block-size: var(--_cui-skeleton-height);
          overflow: hidden;
          border-radius: var(--_cui-skeleton-radius);
          background: var(--_cui-skeleton-background);
          color: transparent;
          vertical-align: middle;
          pointer-events: none;
          user-select: none;
        }

        :where([data-citry-ui-part="skeleton"][data-kind="circle"]) {
          --_cui-skeleton-width: var(--cui-skeleton-width, 3rem);
          --_cui-skeleton-height: var(--cui-skeleton-height, 3rem);
          --_cui-skeleton-radius: var(--cui-skeleton-radius, 50%);
          flex: 0 0 auto;
        }

        :where([data-citry-ui-part="skeleton"][data-kind="text"]) {
          --_cui-skeleton-height: var(--cui-skeleton-height, 0.75em);
          --_cui-skeleton-radius: var(--cui-skeleton-radius, 999px);
          display: grid;
          block-size: auto;
          gap: var(--_cui-skeleton-gap);
          overflow: visible;
          border-radius: 0;
          background: transparent;
        }

        :where([data-citry-ui-part="line"]) {
          position: relative;
          display: block;
          inline-size: 100%;
          block-size: var(--_cui-skeleton-height);
          overflow: hidden;
          border-radius: var(--_cui-skeleton-radius);
          background: var(--_cui-skeleton-background);
        }

        :where([data-citry-ui-part="line"][data-last]) {
          inline-size: var(--_cui-skeleton-last-line-width);
        }

        :where(
          [data-citry-ui-part="skeleton"][data-animation="pulse"]:not([data-kind="text"]),
          [data-citry-ui-part="skeleton"][data-animation="pulse"] [data-citry-ui-part="line"]
        ) {
          animation: cui-skeleton-pulse var(--_cui-skeleton-duration) ease-in-out infinite;
        }

        :where(
          [data-citry-ui-part="skeleton"][data-animation="wave"]:not([data-kind="text"]),
          [data-citry-ui-part="skeleton"][data-animation="wave"] [data-citry-ui-part="line"]
        )::after {
          position: absolute;
          inset: 0;
          background: linear-gradient(90deg, transparent, var(--_cui-skeleton-highlight), transparent);
          content: "";
          transform: translateX(-100%);
          animation: cui-skeleton-wave var(--_cui-skeleton-duration) ease-in-out infinite;
        }

        @keyframes cui-skeleton-pulse {
          0%,
          100% {
            opacity: 1;
          }

          50% {
            opacity: 0.45;
          }
        }

        @keyframes cui-skeleton-wave {
          100% {
            transform: translateX(100%);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          :where(
            [data-citry-ui-part="skeleton"],
            [data-citry-ui-part="line"]
          ) {
            animation: none !important;
          }

          :where(
            [data-citry-ui-part="skeleton"],
            [data-citry-ui-part="line"]
          )::after {
            animation: none !important;
          }
        }

        @media (forced-colors: active) {
          :where(
            [data-citry-ui-part="skeleton"]:not([data-kind="text"]),
            [data-citry-ui-part="line"]
          ) {
            border: 1px solid CanvasText;
            background: Canvas;
          }
        }

        @media print {
          :where(
            [data-citry-ui-part="skeleton"]:not([data-kind="text"]),
            [data-citry-ui-part="line"]
          ) {
            border: 1px solid currentColor;
            background: transparent;
          }
        }
      }
    """
