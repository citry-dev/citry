"""Compact indeterminate activity Spinner component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CSpinnerIntent = Literal["neutral", "primary", "success", "warn", "danger"]
CSpinnerSize = Literal["sm", "md", "lg"]

_INTENTS = ("neutral", "primary", "success", "warn", "danger")
_SIZES = ("sm", "md", "lg")
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
_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
        "contenteditable",
        "data-citry-ui-part",
        "data-intent",
        "data-size",
        "role",
        "tabindex",
    }
)


def _plain_string(input_name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CSpinner {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CSpinner could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if not plain:
        msg = f"CSpinner {input_name} must be non-empty."
        raise ValueError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CSpinner {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CSpinner attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CSpinner attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CSpinner attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CSpinner attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _OWNED_ATTRS:
            msg = f"CSpinner attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CSpinner(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        intent: CSpinnerIntent = "primary"
        size: CSpinnerSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _normalized(self, kwargs: Kwargs) -> dict[str, str]:
        return {
            "label": _plain_string("label", kwargs.label),
            "intent": _plain_choice("intent", kwargs.intent, _INTENTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
        }

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        data = cast("dict[str, Any]", self._normalized(kwargs))
        data["attrs"] = merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style)
        return data

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, str]:
        return self._normalized(kwargs)

    template = """
      <span
        class="cui-spinner"
        c-bind="attrs"
        data-citry-ui-part="spinner"
        c-data-intent="intent"
        c-data-size="size"
        role="progressbar"
        c-aria-label="label"
      ></span>
    """

    js = """
      $component({
        props: {
          label: {},
          intent: {},
          size: {},
        },
        init: ({ els, data, props, effect }) => {
          const spinner = els[0];
          const allowedValues = {
            intent: ["neutral", "primary", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
          };
          const invalidEpisodes = new Set();

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CSpinner ${name} received invalid client value ${describeValue(value)}; `
                + "using the server-rendered fallback.",
              spinner,
            );
          };
          const sourceValue = (name) => props[name] === undefined ? data[name] : props[name];
          const resolveChoice = (name) => {
            const value = sourceValue(name);
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveLabel = () => {
            const value = sourceValue("label");
            if (typeof value === "string" && value.length > 0) {
              invalidEpisodes.delete("label");
              return value;
            }
            reportInvalid("label", value);
            return data.label;
          };
          const setAttribute = (name, value) => {
            if (spinner.getAttribute(name) !== value) {
              spinner.setAttribute(name, value);
            }
          };
          const setData = (name, value) => {
            if (spinner.dataset[name] !== value) {
              spinner.dataset[name] = value;
            }
          };

          effect(() => {
            setAttribute("aria-label", resolveLabel());
            setData("intent", resolveChoice("intent"));
            setData("size", resolveChoice("size"));
          });

          spinner.setAttribute("data-citry-spinner-initialized", "");
          return () => {
            spinner.removeAttribute("data-citry-spinner-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = ["CSpinner", "CSpinnerIntent", "CSpinnerSize"]
