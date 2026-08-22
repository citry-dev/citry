"""Opaque solid sRGB color selection with a native fallback."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import colorsys
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CColorPickerFormat = Literal["hex", "rgb", "hsl"]
CColorPickerSize = Literal["sm", "md", "lg"]
CColorPickerVariant = Literal["outline", "soft", "plain"]
CColorPickerSource = Literal["area", "hue", "text", "swatch", "native", "reset"]

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-readonly",
        "contenteditable",
        "data-citry-color-picker-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-format",
        "data-open",
        "data-readonly",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


@dataclass(frozen=True, slots=True)
class CColorSwatch:
    value: str
    label: str


class CColorPickerValueChangeDetail(TypedDict):
    value: str
    previousValue: str
    rgb: dict[str, int]
    hsl: dict[str, float]
    hsv: dict[str, float]
    controlled: bool
    source: CColorPickerSource
    sourceEvent: object


class CColorPickerOpenChangeDetail(TypedDict):
    open: bool
    reason: str
    sourceEvent: object


def _color(owner: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str) or not _HEX.fullmatch(raw):
        raise ValueError(f"{owner} must be #rgb or #rrggbb, got {raw!r}.")
    value = raw.casefold()
    return value if len(value) == 7 else "#" + "".join(character * 2 for character in value[1:])


def _plain(owner: str, name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{owner} {name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    validate_non_empty_string(owner, name, raw)
    if "\x00" in raw:
        raise ValueError(f"{owner} {name} cannot contain U+0000.")
    return raw


def _attrs(
    value: Mapping[str, object] | None, class_: CClassValue | None, style: CStyleValue | None
) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CColorPicker attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _ROOT_OWNED, "CColorPicker attrs")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CColorPicker attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CColorPicker attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"CColorPicker attrs cannot use ownership directive {key!r}.")
    return merge_root_attrs(copied, class_, style)


class CColorPicker(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        label: str
        value: str = "#7f56d9"
        id: str | None = None
        name: str | None = None
        form: str | None = None
        format: CColorPickerFormat = "hex"
        swatches: Sequence[CColorSwatch] = ()
        open: bool = False
        disabled: bool = False
        readonly: bool = False
        size: CColorPickerSize = "md"
        variant: CColorPickerVariant = "outline"
        open_label: str = "Open color picker"
        area_label: str = "Saturation and brightness"
        hue_label: str = "Hue"
        format_label: str = "Color format"
        value_label: str = "Color value"
        invalid_label: str = "Enter a valid color value"
        selected_label: str = "Selected {color}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_color_picker_snapshot", None)
        if cached is not None:
            return cast("dict[str,object]", cached)
        validate_html_id("CColorPicker", kwargs.id)
        label = cast("str", _plain("CColorPicker", "label", kwargs.label))
        value = _color("CColorPicker value", kwargs.value)
        for flag_name in ("open", "disabled", "readonly"):
            validate_boolean("CColorPicker", flag_name, getattr(kwargs, flag_name))
        validate_choice("CColorPicker", "format", kwargs.format, ("hex", "rgb", "hsl"))
        validate_choice("CColorPicker", "size", kwargs.size, ("sm", "md", "lg"))
        validate_choice("CColorPicker", "variant", kwargs.variant, ("outline", "soft", "plain"))
        name = cast("str|None", _plain("CColorPicker", "name", kwargs.name, optional=True))
        form = cast("str|None", _plain("CColorPicker", "form", kwargs.form, optional=True))
        raw_swatches = const_value(kwargs.swatches)
        if isinstance(raw_swatches, str | bytes | bytearray | Mapping) or not isinstance(raw_swatches, Sequence):
            raise TypeError("CColorPicker swatches must be a sequence of CColorSwatch.")
        swatches = []
        seen = set()
        for index, raw in enumerate(raw_swatches):
            if not isinstance(raw, CColorSwatch):
                raise TypeError(f"CColorPicker swatches[{index}] must be CColorSwatch, got {raw!r}.")
            color = _color(f"CColorPicker swatches[{index}].value", raw.value)
            if color in seen:
                raise ValueError(f"CColorPicker swatch color {color!r} is duplicated.")
            seen.add(color)
            swatches.append({"value": color, "label": cast("str", _plain("CColorSwatch", "label", raw.label))})
        catalog = {
            key: uses_catalog_default(self, f"{key}_label")
            for key in ("open", "area", "hue", "format", "value", "invalid", "selected")
        }
        labels = {key: getattr(kwargs, f"{key}_label") for key in catalog}
        for key, text in labels.items():
            validate_non_empty_string("CColorPicker", f"{key}_label", text)
        if not catalog["selected"] and "{color}" not in labels["selected"]:
            raise ValueError("CColorPicker selected_label must contain {color}.")
        red = int(value[1:3], 16) / 255
        green = int(value[3:5], 16) / 255
        blue = int(value[5:7], 16) / 255
        hue, saturation, brightness = colorsys.rgb_to_hsv(red, green, blue)
        root_id = kwargs.id or f"cui-color-picker-{self.id}"
        native_id = f"{root_id}-native"
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "label_id": f"{root_id}-label",
            "native_id": native_id,
            "label_attrs": {"for": native_id},
            "popup_id": f"{root_id}-popup",
            "value_id": f"{root_id}-value",
            "label": label,
            "value": value,
            "name": name,
            "form": form,
            "format": kwargs.format,
            "swatches": swatches,
            "open": bool(kwargs.open),
            "disabled": bool(kwargs.disabled),
            "readonly": bool(kwargs.readonly),
            "size": kwargs.size,
            "variant": kwargs.variant,
            "catalog": catalog,
            "labels": labels,
            "hue": round(hue * 360),
            "saturation": round(saturation * 100),
            "brightness": round(brightness * 100),
            "attrs": _attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }
        self._cui_color_picker_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        data = self._snapshot(kwargs)
        return {
            **data,
            "root_attrs": {
                **cast("dict[str, object]", data["attrs"]),
                "data-disabled": True if data["disabled"] else None,
                "data-readonly": True if data["readonly"] else None,
                "data-open": True if data["open"] else None,
                "data-format": data["format"],
                "data-size": data["size"],
                "data-variant": data["variant"],
            },
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        data = self._snapshot(kwargs)
        return {key: data[key] for key in ("value", "open", "disabled", "readonly", "format", "catalog", "labels")}

    template = """
      <div class="cui-color-picker" c-id="root_id" c-bind="root_attrs" c-aria-disabled="'true' if disabled else 'false'" data-citry-ui-part="color-picker">
        <label c-id="label_id" c-bind="label_attrs" data-citry-ui-part="label">{{ label }}</label>
        <input c-id="native_id" type="color" c-name="name" c-form="form" c-value="value" c-disabled="disabled" data-citry-ui-part="native" />
        <button hidden type="button" c-disabled="disabled" c-aria-labelledby="f'{label_id} {value_id}'" aria-haspopup="dialog" c-aria-controls="popup_id" c-aria-expanded="'true' if open else 'false'" c-title="tr('citry-ui-color-picker-open') if catalog['open'] else labels['open']" c-$c-tr:citry-ui-color-picker-open[title]="True if catalog['open'] else None" data-citry-ui-part="trigger"><span c-style="{'background-color':value}" aria-hidden="true" data-citry-ui-part="preview"></span><span c-id="value_id" data-citry-ui-part="value">{{ value }}</span></button>
        <div c-id="popup_id" c-hidden="not open" role="dialog" c-aria-labelledby="label_id" data-citry-ui-part="popup">
          <div role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="100" c-aria-valuenow="brightness" c-aria-valuetext="f'{saturation}% saturation, {brightness}% brightness, {value}'" c-aria-label="tr('citry-ui-color-picker-area') if catalog['area'] else labels['area']" c-$c-tr:citry-ui-color-picker-area[aria-label]="True if catalog['area'] else None" c-style="{'--_cui-color-picker-hue':f'hsl({hue} 100% 50%)','--_cui-color-picker-saturation':f'{saturation}%','--_cui-color-picker-brightness':f'{100-brightness}%'}" data-citry-color-picker-area data-citry-ui-part="area"><span aria-hidden="true" data-citry-ui-part="area-thumb"></span></div>
          <label data-citry-ui-part="hue"><span c-$c-tr:citry-ui-color-picker-hue="True if catalog['hue'] else None">{{ tr('citry-ui-color-picker-hue') if catalog['hue'] else labels['hue'] }}</span><input type="range" min="0" max="359" step="1" c-value="hue" /></label>
          <div data-citry-ui-part="fields"><label><span c-$c-tr:citry-ui-color-picker-format="True if catalog['format'] else None">{{ tr('citry-ui-color-picker-format') if catalog['format'] else labels['format'] }}</span><select c-disabled="disabled or readonly" data-citry-ui-part="format"><option value="hex" c-selected="format == 'hex'">HEX</option><option value="rgb" c-selected="format == 'rgb'">RGB</option><option value="hsl" c-selected="format == 'hsl'">HSL</option></select></label><label><span c-$c-tr:citry-ui-color-picker-value="True if catalog['value'] else None">{{ tr('citry-ui-color-picker-value') if catalog['value'] else labels['value'] }}</span><input type="text" c-value="value" c-disabled="disabled" c-readonly="readonly" data-citry-ui-part="input" /></label></div>
          <ul c-if="swatches" data-citry-ui-part="swatches"><c-for each="swatch in swatches"><li><button type="button" c-disabled="disabled or readonly" c-aria-label="swatch['label']" c-data-value="swatch['value']" c-style="{'--cui-color-swatch':swatch['value']}" data-citry-color-swatch data-citry-ui-part="swatch"><span aria-hidden="true"></span></button></li></c-for></ul>
        </div>
        <span role="status" aria-live="polite" aria-atomic="true" data-citry-ui-part="status"></span>
      </div>
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      citry-ui-color-picker-open = Open color picker
      citry-ui-color-picker-area = Saturation and brightness
      citry-ui-color-picker-hue = Hue
      citry-ui-color-picker-format = Color format
      citry-ui-color-picker-value = Color value
      citry-ui-color-picker-invalid = Enter a valid color value
      # @param {str} $color - Canonical hexadecimal color.
      citry-ui-color-picker-selected = Selected { $color }
    """


__all__ = [
    "CColorPicker",
    "CColorPickerFormat",
    "CColorPickerOpenChangeDetail",
    "CColorPickerSize",
    "CColorPickerSource",
    "CColorPickerValueChangeDetail",
    "CColorPickerVariant",
    "CColorSwatch",
]
