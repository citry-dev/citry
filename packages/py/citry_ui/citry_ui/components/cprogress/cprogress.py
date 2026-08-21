"""Native task Progress component."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CProgressIntent = Literal["neutral", "primary", "success", "warn", "danger"]
CProgressSize = Literal["sm", "md", "lg"]
CProgressShape = Literal["square", "rounded", "pill"]

_INTENTS = ("neutral", "primary", "success", "warn", "danger")
_SIZES = ("sm", "md", "lg")
_SHAPES = ("square", "rounded", "pill")
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
        "aria-label",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
        "data-citry-ui-part",
        "data-intent",
        "data-shape",
        "data-size",
        "data-state",
        "max",
        "min",
        "role",
        "value",
    }
)


def _plain_string(input_name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"CProgress {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CProgress could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if not plain:
        msg = f"CProgress {input_name} must be non-empty."
        raise ValueError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_string(input_name, value)
    plain = cast("str", plain)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CProgress {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _number(input_name: str, value: object) -> float:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        msg = f"CProgress {input_name} must be a finite number, got {raw!r}."
        raise TypeError(msg)
    number = float(raw)
    if not math.isfinite(number):
        msg = f"CProgress {input_name} must be finite, got {raw!r}."
        raise ValueError(msg)
    return number


def _value(value: object, maximum: float) -> float | None:
    if const_value(value) is None:
        return None
    number = _number("value", value)
    if number < 0 or number > maximum:
        msg = f"CProgress value must be between 0 and max ({maximum:g}), got {number:g}."
        raise ValueError(msg)
    return number


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CProgress attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CProgress attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CProgress attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CProgress attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _OWNED_ATTRS:
            msg = f"CProgress attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CProgress(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        label: str
        value: float | int | None = None
        max: float | int = 100
        value_text: str | None = None
        intent: CProgressIntent = "primary"
        size: CProgressSize = "md"
        shape: CProgressShape = "rounded"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _normalized(self, kwargs: Kwargs) -> dict[str, object]:
        maximum = _number("max", kwargs.max)
        if maximum <= 0:
            msg = f"CProgress max must be greater than zero, got {maximum:g}."
            raise ValueError(msg)
        label = _plain_string("label", kwargs.label)
        value = _value(kwargs.value, maximum)
        value_text = _plain_string("value_text", kwargs.value_text, optional=True)
        label = cast("str", label)
        return {
            "label": label,
            "value": value,
            "max": maximum,
            "value_text": value_text,
            "intent": _plain_choice("intent", kwargs.intent, _INTENTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "shape": _plain_choice("shape", kwargs.shape, _SHAPES),
        }

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        data = self._normalized(kwargs)
        label = data["label"]
        value = cast("float | None", data["value"])
        maximum = cast("float", data["max"])
        data["state"] = "indeterminate" if value is None else "determinate"
        catalog_fallback_text = self.i18n.configured
        if value is None:
            data["fallback_text"] = label
        else:
            formatted_value = (
                self.i18n.format.number(Decimal(str(value)), format="citry-ui-progress-value")
                if self.i18n.configured
                else f"{float(value):g}"
            )
            formatted_maximum = (
                self.i18n.format.number(Decimal(str(maximum)), format="citry-ui-progress-value")
                if self.i18n.configured
                else f"{float(maximum):g}"
            )
            data["fallback_text"] = self.i18n.tr(
                "citry-ui-progress-value-text",
                label=label,
                value=formatted_value,
                max=formatted_maximum,
            )
        data["catalogFallbackText"] = catalog_fallback_text
        data["attrs"] = merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style)
        return data

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        normalized = self._normalized(kwargs)
        return {
            "label": normalized["label"],
            "value": normalized["value"],
            "max": normalized["max"],
            "valueText": normalized["value_text"],
            "intent": normalized["intent"],
            "size": normalized["size"],
            "shape": normalized["shape"],
            "catalogFallbackText": self.i18n.configured,
        }

    template = """
      <progress
        class="cui-progress"
        c-bind="attrs"
        data-citry-ui-part="progress"
        c-data-state="state"
        c-data-intent="intent"
        c-data-size="size"
        c-data-shape="shape"
        c-aria-label="label"
        c-aria-valuetext="value_text"
        c-value="value"
        c-max="max"
      >{{ fallback_text }}</progress>
    """

    js = """
      $component({
        props: {
          value: {},
          label: {},
          valueText: {},
          intent: {},
          size: {},
          shape: {},
        },
        init: ({ els, data, props, effect, i18n }) => {
          const progress = els[0];
          const allowedValues = {
            intent: ["neutral", "primary", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
            shape: ["square", "rounded", "pill"],
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
              `[citry-ui] CProgress ${name} received invalid client value ${describeValue(value)}; `
                + "using the server-rendered fallback.",
              progress,
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
          const resolveValueText = () => {
            const value = sourceValue("valueText");
            if (value === null || (typeof value === "string" && value.length > 0)) {
              invalidEpisodes.delete("valueText");
              return value;
            }
            reportInvalid("valueText", value);
            return data.valueText;
          };
          const resolveValue = () => {
            const value = sourceValue("value");
            if (
              value === null
              || (
                typeof value === "number"
                && Number.isFinite(value)
                && value >= 0
                && value <= data.max
              )
            ) {
              invalidEpisodes.delete("value");
              return value;
            }
            reportInvalid("value", value);
            return data.value;
          };
          const setAttribute = (name, value) => {
            if (value === null) {
              progress.removeAttribute(name);
            } else if (progress.getAttribute(name) !== String(value)) {
              progress.setAttribute(name, String(value));
            }
          };
          const setData = (name, value) => {
            if (progress.dataset[name] !== value) {
              progress.dataset[name] = value;
            }
          };

          const fallbackBinding = i18n && data.catalogFallbackText
            ? i18n.bind({
                message: "citry-ui-progress-value-text",
                values: () => {
                  const value = resolveValue();
                  return {
                    label: resolveLabel(),
                    value: i18n.format.number(value ?? 0, {format: "citry-ui-progress-value"}),
                    max: i18n.format.number(data.max, {format: "citry-ui-progress-value"}),
                  };
                },
                onChange: (text) => {
                  progress.textContent = resolveValue() === null ? resolveLabel() : text;
                },
              })
            : null;

          effect(() => {
            const value = resolveValue();
            setAttribute("value", value);
            setAttribute("aria-label", resolveLabel());
            setAttribute("aria-valuetext", resolveValueText());
            setData("state", value === null ? "indeterminate" : "determinate");
            setData("intent", resolveChoice("intent"));
            setData("size", resolveChoice("size"));
            setData("shape", resolveChoice("shape"));
          });

          progress.setAttribute("data-citry-progress-initialized", "");
          return () => {
            fallbackBinding?.dispose();
            progress.removeAttribute("data-citry-progress-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"

    messages = """
      # @param {str} $label - Progress label.
      # @param {str} $value - Locale-formatted current value.
      # @param {str} $max - Locale-formatted maximum value.
      citry-ui-progress-value-text = { $label }: { $value } of { $max }
    """


__all__ = [
    "CProgress",
    "CProgressIntent",
    "CProgressShape",
    "CProgressSize",
]
