"""Styled exact-decimal Slider and RangeSlider components."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._form_control_runtime import (
    FORM_CONTROL_RUNTIME_DEPENDENCY,
    FORM_CONTROL_STYLE_DEPENDENCY,
)
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CSliderExact = int | Decimal | str
CSliderOrientation = Literal["horizontal", "vertical"]
CSliderVariant = Literal["solid", "subtle"]
CSliderSize = Literal["sm", "md", "lg"]
CSliderShowValue = Literal["never", "interaction", "always"]
CSliderChangeSource = Literal["pointer", "keyboard", "reset"]
CSliderChangePhase = Literal["change", "end"]
CRangeSliderThumb = Literal["lower", "upper"]

_PLAIN_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_RUNTIME_PREFIXES = ("data-citry-", "data-csl", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "data-active",
        "data-citry-slider-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-dragging",
        "data-enhanced",
        "data-invalid",
        "data-orientation",
        "data-readonly",
        "data-show-value",
        "data-size",
        "data-variant",
        "id",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-invalid",
        "aria-orientation",
        "aria-readonly",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
        FIELD_CONTROL_MARKER,
        "data-citry-ui-part",
        "disabled",
        "form",
        "id",
        "max",
        "min",
        "name",
        "readonly",
        "role",
        "step",
        "tabindex",
        "type",
        "value",
    }
)
_RANGE_INPUT_OWNED = _INPUT_OWNED | {"aria-label", "aria-labelledby"}


class CSliderValueChangeDetail(TypedDict):
    value: str
    previousValue: str
    controlled: bool
    source: CSliderChangeSource
    sourceEvent: object | None
    phase: CSliderChangePhase


class CRangeSliderValueChangeDetail(TypedDict):
    value: tuple[str, str]
    previousValue: tuple[str, str]
    controlled: bool
    source: CSliderChangeSource
    sourceEvent: object | None
    phase: CSliderChangePhase
    activeThumb: CRangeSliderThumb


def _canonical_decimal(component: str, name: str, value: object, *, optional: bool = False) -> str | None:
    value = const_value(value)
    if value is None:
        if optional:
            return None
        raise TypeError(f"{component} {name} cannot be None.")
    if type(value) is int:
        raw = str(value)
    elif type(value) is Decimal:
        decimal = cast("Decimal", value)
        if not decimal.is_finite():
            raise ValueError(f"{component} {name} must be finite.")
        raw = format(decimal, "f")
    elif type(value) is str:
        raw = cast("str", value)
        if not _PLAIN_DECIMAL.fullmatch(raw):
            raise ValueError(f"{component} {name} must use canonical plain-decimal syntax, got {raw!r}.")
    else:
        raise TypeError(f"{component} {name} must be an int, Decimal, or canonical decimal string, got {value!r}.")
    negative = raw.startswith("-")
    unsigned = raw[1:] if negative else raw
    integer, dot, fraction = unsigned.partition(".")
    integer = integer.lstrip("0") or "0"
    fraction = fraction.rstrip("0") if dot else ""
    normalized = integer + (f".{fraction}" if fraction else "")
    if negative and normalized != "0":
        normalized = f"-{normalized}"
    if sum(character.isdigit() for character in normalized) > 128:
        raise ValueError(f"{component} {name} may contain at most 128 decimal digits.")
    return normalized


def _plain(component: str, name: str, value: object) -> str:
    value = const_value(value)
    if not isinstance(value, str):
        raise TypeError(f"{component} {name} must be a string, got {value!r}.")
    normalized = "".join(value).replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in normalized or "\n" in normalized or not normalized.strip():
        raise ValueError(f"{component} {name} must be one nonempty line without U+0000.")
    return normalized


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(
    component: str, destination: str, value: Mapping[str, object] | None, owned: frozenset[str]
) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"{component} {destination} must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"{component} {destination}")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{component} {destination} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{component} {destination} cannot contain runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"{component} {destination} cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in owned:
            raise ValueError(f"{component} {destination} cannot dynamically bind owned attribute {key!r}.")
    return copied


def _normalize_marks(
    component: str, raw_marks: object, minimum: Decimal, maximum: Decimal, step: Decimal
) -> list[dict[str, object]]:
    raw_marks = const_value(raw_marks)
    if raw_marks is None:
        return []
    if isinstance(raw_marks, Mapping):
        source = list(raw_marks.items())
    elif isinstance(raw_marks, Sequence) and not isinstance(raw_marks, (str, bytes, bytearray)):
        source = [(item, None) for item in raw_marks]
    else:
        raise TypeError(f"{component} marks must be a mapping, a sequence of exact values, or None.")
    if len(source) > 101:
        raise ValueError(f"{component} marks accepts at most 101 entries.")
    normalized: dict[str, str | None] = {}
    for raw_value, raw_label in source:
        value = cast("str", _canonical_decimal(component, "mark value", raw_value))
        decimal = Decimal(value)
        if decimal < minimum or decimal > maximum or (decimal - minimum) % step:
            raise ValueError(f"{component} mark {value!r} must be a bounded value on the min-origin step grid.")
        if value in normalized:
            raise ValueError(f"{component} marks contains duplicate normalized value {value!r}.")
        label = None if raw_label is None else _plain(component, "mark label", raw_label)
        normalized[value] = label
    span = maximum - minimum
    return [
        {
            "value": value,
            "label": label,
            "has_label": label is not None,
            "style": {"--_cui-slider-mark-position": f"{(Decimal(value) - minimum) / span * 100}%"},
        }
        for value, label in sorted(normalized.items(), key=lambda item: Decimal(item[0]))
    ]


def _format_value(component: LibraryComponent, value: str, profile: str) -> str:
    if not component.i18n.configured:
        return value
    return component.i18n.format.number(Decimal(value), format=profile)


def _snapshot(component: LibraryComponent, kwargs: Any, *, is_range: bool) -> dict[str, Any]:
    cache_name = "_cui_range_slider_snapshot" if is_range else "_cui_slider_snapshot"
    cached = getattr(component, cache_name, None)
    if cached is not None:
        return cast("dict[str, Any]", cached)
    component_name = "CRangeSlider" if is_range else "CSlider"
    name = const_value(kwargs.name)
    lower_name = const_value(getattr(kwargs, "lower_name", None)) if is_range else None
    upper_name = const_value(getattr(kwargs, "upper_name", None)) if is_range else None
    form_input = const_value(kwargs.form)
    supplied_id = const_value(kwargs.id)
    for input_name, value in (("name", name), ("lower_name", lower_name), ("upper_name", upper_name)):
        if value is not None:
            validate_non_empty_string(component_name, input_name, value)
    if is_range and (lower_name is None) != (upper_name is None):
        raise ValueError("CRangeSlider lower_name and upper_name must be supplied together.")
    validate_html_id(component_name, supplied_id)
    validate_html_id(component_name, form_input)
    for input_name in ("disabled", "readonly", "invalid"):
        validate_optional_boolean(component_name, input_name, getattr(kwargs, input_name))
    for input_name in ("show_marks",):
        validate_optional_boolean(component_name, input_name, getattr(kwargs, input_name))
    for input_name in ("orientation", "variant", "size", "show_value"):
        value = const_value(getattr(kwargs, input_name))
        allowed = {
            "orientation": ("horizontal", "vertical"),
            "variant": ("solid", "subtle"),
            "size": ("sm", "md", "lg"),
            "show_value": ("never", "interaction", "always"),
        }[input_name]
        validate_choice(component_name, input_name, value, allowed)
    validate_optional_string(component_name, "format", kwargs.format)
    profile = _plain(component_name, "format", kwargs.format)

    minimum = cast("str", _canonical_decimal(component_name, "min", kwargs.min))
    maximum = cast("str", _canonical_decimal(component_name, "max", kwargs.max))
    step = cast("str", _canonical_decimal(component_name, "step", kwargs.step))
    minimum_decimal = Decimal(minimum)
    maximum_decimal = Decimal(maximum)
    step_decimal = Decimal(step)
    if minimum_decimal >= maximum_decimal:
        raise ValueError(f"{component_name} min must be less than max.")
    if step_decimal <= 0:
        raise ValueError(f"{component_name} step must be greater than zero.")
    step_count = (maximum_decimal - minimum_decimal) / step_decimal
    if step_count != step_count.to_integral_value() or step_count > 1_000_000:
        raise ValueError(f"{component_name} requires max - min to contain 1 to 1,000,000 whole steps.")
    large_step_raw = _canonical_decimal(component_name, "large_step", kwargs.large_step, optional=True)
    large_step = large_step_raw or format(step_decimal * 10, "f")
    large_decimal = Decimal(large_step)
    if large_decimal <= 0 or large_decimal % step_decimal:
        raise ValueError(f"{component_name} large_step must be a positive whole multiple of step.")

    values: tuple[str, ...]
    if is_range:
        gap = const_value(kwargs.min_steps_between_thumbs)
        if type(gap) is not int or gap < 0 or gap > int(step_count):
            raise ValueError("CRangeSlider min_steps_between_thumbs must be a nonnegative integer within the grid.")
        raw_value = const_value(kwargs.value)
        if raw_value is None:
            values = (minimum, maximum)
        elif (
            not isinstance(raw_value, Sequence)
            or isinstance(raw_value, (str, bytes, bytearray))
            or len(raw_value) != 2
        ):
            raise TypeError("CRangeSlider value must be an exact-decimal pair or None.")
        else:
            values = (
                cast("str", _canonical_decimal(component_name, "value[0]", raw_value[0])),
                cast("str", _canonical_decimal(component_name, "value[1]", raw_value[1])),
            )
        decimals = tuple(Decimal(value) for value in values)
        if any(value < minimum_decimal or value > maximum_decimal for value in decimals):
            raise ValueError("CRangeSlider values must be within min and max.")
        if any((value - minimum_decimal) % step_decimal for value in decimals):
            raise ValueError("CRangeSlider values must lie on the min-origin step grid.")
        if decimals[1] - decimals[0] < step_decimal * gap:
            raise ValueError("CRangeSlider values do not satisfy min_steps_between_thumbs.")
    else:
        gap = 0
        value = _canonical_decimal(component_name, "value", kwargs.value, optional=True) or minimum
        decimal = Decimal(value)
        if decimal < minimum_decimal or decimal > maximum_decimal:
            raise ValueError("CSlider value must be within min and max.")
        if (decimal - minimum_decimal) % step_decimal:
            raise ValueError("CSlider value must lie on the min-origin step grid.")
        values = (value,)

    marks = _normalize_marks(component_name, kwargs.marks, minimum_decimal, maximum_decimal, step_decimal)
    show_marks = bool(marks) if kwargs.show_marks is None else bool(kwargs.show_marks)
    field = component.inject(FIELD_CONTEXT_KEY, None)
    form = component.inject(FORM_CONTEXT_KEY, None)
    field_control_id = str(field.control_id) if field is not None else None
    if field is not None:
        supplied = [
            input_name for input_name in ("disabled", "readonly", "invalid") if getattr(kwargs, input_name) is not None
        ]
        if supplied:
            raise ValueError(f"{component_name} inside CField cannot set Field-owned state: {', '.join(supplied)}.")
        field.register_control(component_name, supports_required=False, supports_readonly=True)
    if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
        raise ValueError(
            f"{component_name} id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
        )
    public_id = supplied_id or field_control_id or f"cui-{'range-' if is_range else ''}slider-{component.id}"
    root_attrs = _attrs(component_name, "attrs", kwargs.attrs, _ROOT_OWNED)
    input_owned = _RANGE_INPUT_OWNED if is_range else _INPUT_OWNED
    input_attrs = _attrs(component_name, "input_attrs", kwargs.input_attrs, input_owned) if not is_range else {}
    lower_input_attrs = (
        _attrs(component_name, "lower_input_attrs", kwargs.lower_input_attrs, input_owned) if is_range else input_attrs
    )
    upper_input_attrs = (
        _attrs(component_name, "upper_input_attrs", kwargs.upper_input_attrs, input_owned) if is_range else {}
    )
    form_owner = get_html_form_owner(
        {"form": form_input} if form_input is not None else {},
        component_name=component_name,
        default=form.form_id if form is not None else None,
    )
    if form is not None and form_owner != form.form_id:
        raise ValueError(f"{component_name} inside CForm cannot target another form owner.")
    disabled = (
        bool(field.disabled) if field is not None else bool(form.disabled if form else False) or bool(kwargs.disabled)
    )
    readonly = (
        bool(field.readonly)
        if field is not None
        else bool(kwargs.readonly if kwargs.readonly is not None else form.readonly if form else False)
    )
    invalid = bool(field.invalid) if field is not None else bool(kwargs.invalid)
    described_by = merge_idrefs(
        field.description_id if field is not None and field.has_description else None,
        field.error_id if field is not None and field.has_error and invalid else None,
        cast("str | None", lower_input_attrs.pop("aria-describedby", None)),
    )
    error_message = merge_idrefs(
        field.error_id if field is not None and field.has_error and invalid else None,
        cast("str | None", lower_input_attrs.pop("aria-errormessage", None)) if invalid else None,
    )
    upper_described_by = merge_idrefs(
        field.description_id if field is not None and field.has_description else None,
        field.error_id if field is not None and field.has_error and invalid else None,
        cast("str | None", upper_input_attrs.pop("aria-describedby", None)),
    )
    upper_error_message = merge_idrefs(
        field.error_id if field is not None and field.has_error and invalid else None,
        cast("str | None", upper_input_attrs.pop("aria-errormessage", None)) if invalid else None,
    )

    if is_range:
        lower_catalog = uses_catalog_default(component, "lower_label")
        upper_catalog = uses_catalog_default(component, "upper_label")
        lower_label = _plain(
            component_name,
            "lower_label",
            component.i18n.tr("citry-ui-range-slider-lower") if lower_catalog else kwargs.lower_label,
        )
        upper_label = _plain(
            component_name,
            "upper_label",
            component.i18n.tr("citry-ui-range-slider-upper") if upper_catalog else kwargs.upper_label,
        )
    else:
        lower_catalog = upper_catalog = False
        lower_label = upper_label = ""

    formatted_values = tuple(_format_value(component, value, profile) for value in values)
    span = maximum_decimal - minimum_decimal
    thumb_records = []
    for index, (value, formatted) in enumerate(zip(values, formatted_values, strict=True)):
        percent = (Decimal(value) - minimum_decimal) / span * 100
        thumb_records.append(
            {
                "kind": ("lower", "upper")[index] if is_range else "single",
                "value": value,
                "formatted": formatted,
                "style": {"--_cui-slider-position": f"{percent}%"},
            }
        )
    single_aria_label = None if is_range else cast("str | None", input_attrs.get("aria-label"))
    single_aria_labelledby = (
        field.label_id
        if field is not None
        else cast("str | None", input_attrs.get("aria-labelledby"))
        if not is_range
        else None
    )
    if not is_range:
        input_attrs.pop("aria-label", None)
        input_attrs.pop("aria-labelledby", None)
    root_id = f"{public_id}-root" if is_range else None
    lower_id = public_id
    upper_id = f"{public_id}-upper"
    lower_label_id = f"{public_id}-lower-label"
    upper_label_id = f"{public_id}-upper-label"
    lower_labelledby = (
        merge_idrefs(field.label_id if field is not None else None, lower_label_id)
        if is_range
        else single_aria_labelledby
    )
    upper_labelledby = (
        merge_idrefs(field.label_id if field is not None else None, upper_label_id) if is_range else None
    )
    effective_names: tuple[str | None, ...] = ((lower_name or name), (upper_name or name)) if is_range else (name,)
    snapshot: dict[str, Any] = {
        "is_range": is_range,
        "part": "range-slider" if is_range else "slider",
        "public_id": public_id,
        "root_id": root_id,
        "lower_id": lower_id,
        "upper_id": upper_id,
        "lower_transport_id": f"{lower_id}-readonly",
        "upper_transport_id": f"{upper_id}-readonly",
        "lower_name": effective_names[0],
        "upper_name": effective_names[1] if is_range else None,
        "form": form_owner,
        "minimum": minimum,
        "maximum": maximum,
        "step": step,
        "orientation": kwargs.orientation,
        "variant": kwargs.variant,
        "size": kwargs.size,
        "show_value": kwargs.show_value,
        "show_marks": show_marks,
        "marks": marks,
        "thumbs": thumb_records,
        "disabled": disabled,
        "readonly": readonly,
        "invalid": invalid,
        "field_control": field is not None,
        "aria_describedby": described_by,
        "aria_errormessage": error_message,
        "upper_aria_describedby": upper_described_by,
        "upper_aria_errormessage": upper_error_message,
        "single_aria_label": single_aria_label,
        "single_aria_labelledby": single_aria_labelledby,
        "lower_label": lower_label,
        "upper_label": upper_label,
        "lower_label_id": lower_label_id,
        "upper_label_id": upper_label_id,
        "lower_labelledby": lower_labelledby,
        "upper_labelledby": upper_labelledby,
        "catalog_lower_label": lower_catalog,
        "catalog_upper_label": upper_catalog,
        "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
        "lower_input_attrs": lower_input_attrs,
        "upper_input_attrs": upper_input_attrs,
    }
    cast("Any", component)._cui_slider_data = {
        "kind": "range" if is_range else "single",
        "id": public_id,
        "rootId": root_id,
        "ids": [lower_id, upper_id] if is_range else [lower_id],
        "transportIds": [f"{lower_id}-readonly", f"{upper_id}-readonly"] if is_range else [f"{lower_id}-readonly"],
        "names": list(effective_names),
        "form": form_owner,
        "value": list(values) if is_range else values[0],
        "min": minimum,
        "max": maximum,
        "step": step,
        "largeStep": large_step,
        "minStepsBetweenThumbs": gap,
        "disabled": disabled,
        "readonly": readonly,
        "inheritsReadonly": field is None and kwargs.readonly is None,
        "invalid": invalid,
        "orientation": kwargs.orientation,
        "variant": kwargs.variant,
        "size": kwargs.size,
        "showValue": kwargs.show_value,
        "format": profile,
        "describedby": [described_by, upper_described_by] if is_range else [described_by],
        "errormessage": [error_message, upper_error_message] if is_range else [error_message],
        "ariaLabel": single_aria_label,
        "ariaLabelledby": single_aria_labelledby,
        "rangeLabelledby": [lower_labelledby, upper_labelledby] if is_range else [],
        "fieldLabelId": field.label_id if field is not None else None,
    }
    setattr(component, cache_name, snapshot)
    return snapshot


_SLIDER_TEMPLATE = """
  <div
    class="cui-slider"
    c-id="root_id"
    c-data-orientation="orientation"
    c-data-variant="variant"
    c-data-size="size"
    c-data-show-value="show_value"
    c-data-disabled="disabled"
    c-data-readonly="readonly"
    c-data-invalid="invalid"
    c-bind="root_attrs"
    c-data-citry-ui-part="part"
  >
    <span
      c-if="is_range"
      class="cui-slider__visually-hidden"
      c-id="lower_label_id"
      c-$c-tr:citry-ui-range-slider-lower="True if catalog_lower_label else None"
    >{{ tr('citry-ui-range-slider-lower') if catalog_lower_label else lower_label }}</span>
    <span
      c-if="is_range"
      class="cui-slider__visually-hidden"
      c-id="upper_label_id"
      c-$c-tr:citry-ui-range-slider-upper="True if catalog_upper_label else None"
    >{{ tr('citry-ui-range-slider-upper') if catalog_upper_label else upper_label }}</span>
    <input
      c-id="lower_id"
      c-name="lower_name"
      c-form="form"
      type="range"
      c-min="minimum"
      c-max="maximum"
      c-step="step"
      c-value="thumbs[0]['value']"
      c-disabled="disabled or readonly"
      c-aria-label="single_aria_label"
      c-aria-labelledby="lower_labelledby"
      c-aria-describedby="aria_describedby"
      c-aria-errormessage="aria_errormessage"
      c-aria-invalid="'true' if invalid else None"
      c-data-citry-field-control="field_control"
      c-bind="lower_input_attrs"
      c-data-thumb="thumbs[0]['kind']"
      data-citry-ui-part="native-input"
    />
    <input
      c-if="is_range"
      c-id="upper_id"
      c-name="upper_name"
      c-form="form"
      type="range"
      c-min="minimum"
      c-max="maximum"
      c-step="step"
      c-value="thumbs[1]['value']"
      c-disabled="disabled or readonly"
      c-aria-labelledby="upper_labelledby"
      c-aria-describedby="upper_aria_describedby"
      c-aria-errormessage="upper_aria_errormessage"
      c-aria-invalid="'true' if invalid else None"
      c-bind="upper_input_attrs"
      data-thumb="upper"
      data-citry-ui-part="native-input"
    />
    <input
      c-id="lower_transport_id"
      c-name="lower_name"
      c-form="form"
      c-value="thumbs[0]['value']"
      type="hidden"
      c-disabled="disabled or not readonly or lower_name is None"
      data-thumb="single-or-lower"
      data-citry-ui-part="readonly-transport"
    />
    <input
      c-if="is_range"
      c-id="upper_transport_id"
      c-name="upper_name"
      c-form="form"
      c-value="thumbs[1]['value']"
      type="hidden"
      c-disabled="disabled or not readonly or upper_name is None"
      data-thumb="upper"
      data-citry-ui-part="readonly-transport"
    />
    <div hidden data-citry-ui-part="control">
      <div data-citry-ui-part="track">
        <span data-citry-ui-part="fill"></span>
        <span
          c-for="mark in marks"
          c-hidden="not show_marks"
          c-data-value="mark['value']"
          c-style="mark['style']"
          data-citry-ui-part="mark"
        ><span c-if="mark['has_label']" data-citry-ui-part="mark-label">{{ mark['label'] }}</span></span>
        <button
          type="button"
          role="slider"
          c-disabled="disabled"
          c-aria-readonly="'true' if readonly else None"
          c-aria-valuemin="minimum"
          c-aria-valuemax="thumbs[1]['value'] if is_range else maximum"
          c-aria-valuenow="thumbs[0]['value']"
          c-aria-valuetext="thumbs[0]['formatted']"
          c-aria-orientation="orientation if orientation == 'vertical' else None"
          c-aria-label="single_aria_label"
          c-aria-labelledby="lower_labelledby"
          c-aria-describedby="aria_describedby"
          c-aria-errormessage="aria_errormessage"
          c-aria-invalid="'true' if invalid else None"
          c-style="thumbs[0]['style']"
          c-data-thumb="thumbs[0]['kind']"
          data-citry-ui-part="thumb"
        ><span c-hidden="show_value == 'never'" data-citry-ui-part="value">{{ thumbs[0]['formatted'] }}</span></button>
        <button
          c-if="is_range"
          type="button"
          role="slider"
          c-disabled="disabled"
          c-aria-readonly="'true' if readonly else None"
          c-aria-valuemin="thumbs[0]['value']"
          c-aria-valuemax="maximum"
          c-aria-valuenow="thumbs[1]['value']"
          c-aria-valuetext="thumbs[1]['formatted']"
          c-aria-orientation="orientation if orientation == 'vertical' else None"
          c-aria-labelledby="upper_labelledby"
          c-aria-describedby="upper_aria_describedby"
          c-aria-errormessage="upper_aria_errormessage"
          c-aria-invalid="'true' if invalid else None"
          c-style="thumbs[1]['style']"
          c-data-thumb="thumbs[1]['kind']"
          data-citry-ui-part="thumb"
        ><span c-hidden="show_value == 'never'" data-citry-ui-part="value">{{ thumbs[1]['formatted'] }}</span></button>
      </div>
    </div>
  </div>
"""


_SLIDER_JS = r"""
  $component({
    props: {
      value: {}, min: {}, max: {}, step: {}, largeStep: {}, minStepsBetweenThumbs: {},
      disabled: {}, readonly: {}, invalid: {}, orientation: {}, variant: {}, size: {},
      showValue: {}, format: {}, onValueChange: {}, onValueChangeEnd: {},
    },
    init: ({ els, data, props, effect, inject, i18n }) => {
      const root = els[0];
      const nativeInputs = Array.from(root.querySelectorAll(':scope > [data-citry-ui-part="native-input"]'));
      const transports = Array.from(root.querySelectorAll(':scope > [data-citry-ui-part="readonly-transport"]'));
      const control = root.querySelector(':scope > [data-citry-ui-part="control"]');
      const track = control?.querySelector(':scope > [data-citry-ui-part="track"]');
      const fill = track?.querySelector(':scope > [data-citry-ui-part="fill"]');
      const thumbs = Array.from(track?.querySelectorAll(':scope > [data-citry-ui-part="thumb"]') ?? []);
      const expected = data.kind === 'range' ? 2 : 1;
      if (nativeInputs.length !== expected || transports.length !== expected || thumbs.length !== expected || !(control instanceof HTMLElement && track instanceof HTMLElement && fill instanceof HTMLElement) || nativeInputs.some(input => !(input instanceof HTMLInputElement)) || transports.some(input => !(input instanceof HTMLInputElement)) || thumbs.some(thumb => !(thumb instanceof HTMLButtonElement))) {
        throw new Error('[citry-ui] Slider settled anatomy is invalid.');
      }
      const field = inject(Symbol.for('citry-ui:field'), null);
      const form = inject(Symbol.for('citry-ui:form'), null);
      const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
      if (runtime?.generation !== 1) throw new Error('[citry-ui] Slider form-control runtime is unavailable.');
      const resolver = runtime.resolver(root, props, data.kind === 'range' ? 'CRangeSlider' : 'CSlider');
      const listeners = runtime.listeners();
      const mutations = runtime.mutations(root);
      const owned = mutations.owned;
      let current = data.kind === 'range' ? [...data.value] : [data.value];
      let committed = [...current];
      let lastRequested = [...current];
      let initialValue = [...current];
      let controlled = false;
      let configuration = null;
      let activeIndex = 0;
      let lastFocusedIndex = null;
      let dragging = false;
      let changedDuringDrag = false;
      let dragPrevious = null;
      let pendingPointer = null;
      let frame = 0;

      const canonical = value => {
        if (typeof value !== 'string' || !/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/.test(value)) return undefined;
        let negative = value.startsWith('-');
        let unsigned = negative ? value.slice(1) : value;
        let [integer, fraction = ''] = unsigned.split('.');
        integer = integer.replace(/^0+(?=\d)/, '') || '0';
        fraction = fraction.replace(/0+$/, '');
        let result = integer + (fraction ? `.${fraction}` : '');
        if (negative && result !== '0') result = `-${result}`;
        return result.replace('-', '').replace('.', '').length <= 128 ? result : undefined;
      };
      const parts = value => {
        const normalized = canonical(value);
        if (normalized === undefined) return null;
        const negative = normalized.startsWith('-');
        const unsigned = negative ? normalized.slice(1) : normalized;
        const [integer, fraction = ''] = unsigned.split('.');
        return { integer: BigInt(`${negative ? '-' : ''}${integer}${fraction}`), scale: fraction.length };
      };
      const power = count => BigInt(`1${'0'.repeat(count)}`);
      const fromParts = (integer, scale) => {
        const negative = integer < BigInt(0);
        const digits = (negative ? -integer : integer).toString().padStart(scale + 1, '0');
        const text = scale ? `${digits.slice(0, -scale)}.${digits.slice(-scale)}` : digits;
        return canonical(`${negative ? '-' : ''}${text}`);
      };
      const aligned = values => {
        const parsed = values.map(parts);
        if (parsed.some(value => value === null)) return null;
        const scale = Math.max(...parsed.map(value => value.scale));
        return { values: parsed.map(value => value.integer * power(scale - value.scale)), scale };
      };
      const compare = (left, right) => {
        const result = aligned([left, right]);
        return result.values[0] < result.values[1] ? -1 : result.values[0] > result.values[1] ? 1 : 0;
      };
      const grid = (min, max, step) => {
        const result = aligned([min, max, step]);
        if (!result) return null;
        const [a, b, interval] = result.values;
        const difference = b - a;
        if (a >= b || interval <= BigInt(0) || difference % interval !== BigInt(0)) return null;
        const count = difference / interval;
        if (count <= BigInt(0) || count > BigInt(1000000)) return null;
        return { min: a, max: b, step: interval, count: Number(count), scale: result.scale };
      };
      const indexFor = value => {
        const result = aligned([configuration.min, value, configuration.step]);
        if (!result) return null;
        const [min, item, step] = result.values;
        const difference = item - min;
        if (difference < BigInt(0) || difference % step !== BigInt(0)) return null;
        const index = Number(difference / step);
        return index <= configuration.count ? index : null;
      };
      const valueFor = index => fromParts(configuration.gridMin + configuration.gridStep * BigInt(index), configuration.scale);
      const format = value => i18n ? i18n.format.number(value, { format: configuration.format }) : value;
      const normalizeValue = (raw, fallback) => {
        const value = canonical(raw);
        if (value === undefined) return fallback;
        return indexFor(value) === null ? fallback : value;
      };
      const valuesEqual = (left, right) => left.length === right.length && left.every((value, index) => value === right[index]);
      const boundsFor = index => data.kind === 'range'
        ? index === 0
          ? [0, indexFor(current[1]) - configuration.gap]
          : [indexFor(current[0]) + configuration.gap, configuration.count]
        : [0, configuration.count];
      const clampIndex = (index, thumbIndex) => {
        const [minimum, maximum] = boundsFor(thumbIndex);
        return Math.max(minimum, Math.min(maximum, index));
      };
      const percentFor = value => indexFor(value) / configuration.count * 100;
      const applyGeometry = () => {
        const percentages = current.map(percentFor);
        thumbs.forEach((thumb, index) => thumb.style.setProperty('--_cui-slider-position', `${percentages[index]}%`));
        const start = data.kind === 'range' ? percentages[0] : 0;
        const stop = data.kind === 'range' ? percentages[1] : percentages[0];
        fill.style.setProperty('--_cui-slider-fill-start', `${start}%`);
        fill.style.setProperty('--_cui-slider-fill-stop', `${stop}%`);
      };
      const syncRelationships = () => thumbs.forEach((thumb, index) => runtime.relationships([thumb], field, data.kind === 'range' ? {
        labelledby: data.rangeLabelledby[index], describedby: data.describedby[index], errormessage: data.errormessage[index],
        control: thumb, disabled: configuration.disabled, readonly: configuration.readonly,
      } : {
        label: data.ariaLabel, labelledby: data.ariaLabelledby, describedby: data.describedby[0], errormessage: data.errormessage[0],
        control: thumb, disabled: configuration.disabled, readonly: configuration.readonly,
      }, configuration.invalid));
      const applyState = () => owned(() => {
        root.dataset.orientation = configuration.orientation;
        root.dataset.variant = configuration.variant;
        root.dataset.size = configuration.size;
        root.dataset.showValue = configuration.showValue;
        root.toggleAttribute('data-disabled', configuration.disabled);
        root.toggleAttribute('data-readonly', configuration.readonly);
        root.toggleAttribute('data-invalid', configuration.invalid);
        root.toggleAttribute('data-dragging', dragging);
        current.forEach((value, index) => {
          const native = nativeInputs[index];
          const transport = transports[index];
          const thumb = thumbs[index];
          native.min = configuration.min;
          native.max = configuration.max;
          native.step = configuration.step;
          native.value = value;
          native.name = configuration.disabled || configuration.readonly ? '' : (data.names[index] ?? '');
          native.disabled = configuration.disabled || configuration.readonly || !data.names[index];
          native.tabIndex = -1;
          transport.value = value;
          transport.name = configuration.disabled || !configuration.readonly ? '' : (data.names[index] ?? '');
          transport.disabled = configuration.disabled || !configuration.readonly || !data.names[index];
          thumb.disabled = configuration.disabled;
          thumb.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
          thumb.setAttribute('aria-valuenow', value);
          thumb.setAttribute('aria-valuetext', format(value));
          const [allowedMin, allowedMax] = boundsFor(index);
          thumb.setAttribute('aria-valuemin', valueFor(allowedMin));
          thumb.setAttribute('aria-valuemax', valueFor(allowedMax));
          thumb.setAttribute('aria-invalid', configuration.invalid ? 'true' : 'false');
          if (configuration.orientation === 'vertical') thumb.setAttribute('aria-orientation', 'vertical');
          else thumb.removeAttribute('aria-orientation');
          const bubble = thumb.querySelector(':scope > [data-citry-ui-part="value"]');
          if (bubble) {
            bubble.textContent = format(value);
            bubble.hidden = configuration.showValue === 'never';
          }
          thumb.toggleAttribute('data-active', activeIndex === index && (dragging || document.activeElement === thumb));
        });
        syncRelationships();
        applyGeometry();
      });
      const nativeEvents = (index, phase) => {
        nativeInputs[index].dispatchEvent(new Event(phase === 'change' ? 'input' : 'change', { bubbles: true }));
      };
      const detail = (next, previous, source, event, phase, index) => {
        const result = { value: data.kind === 'range' ? [...next] : next[0], previousValue: data.kind === 'range' ? [...previous] : previous[0], controlled, source, sourceEvent: event, phase };
        if (data.kind === 'range') result.activeThumb = index === 0 ? 'lower' : 'upper';
        return result;
      };
      const request = (next, index, source, event, phase = 'change') => {
        if (valuesEqual(next, controlled ? lastRequested : current)) return null;
        const previous = [...current];
        lastRequested = [...next];
        if (!controlled) {
          current = [...next];
          committed = [...next];
        }
        resolver.callback(phase === 'change' ? 'onValueChange' : 'onValueChangeEnd')?.(data.kind === 'range' ? [...next] : next[0], detail(next, previous, source, event, phase, index));
        if (!controlled) nativeEvents(index, phase);
        applyState();
        return { previous, next: [...next] };
      };
      const changeIndex = (nextIndex, index, source, event) => {
        const bounded = clampIndex(nextIndex, index);
        const next = [...current];
        next[index] = valueFor(bounded);
        return request(next, index, source, event, 'change');
      };
      const end = (index, source, event, previous, next = current) => {
        if (!previous || valuesEqual(previous, next)) return false;
        resolver.callback('onValueChangeEnd')?.(data.kind === 'range' ? [...next] : next[0], detail(next, previous, source, event, 'end', index));
        if (!controlled) nativeEvents(index, 'end');
        else lastRequested = [...current];
        return true;
      };
      const pointerRatio = event => {
        const rect = track.getBoundingClientRect();
        if (configuration.orientation === 'vertical') return Math.max(0, Math.min(1, (rect.bottom - event.clientY) / rect.height));
        const raw = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
        return getComputedStyle(root).direction === 'rtl' ? 1 - raw : raw;
      };
      const pointerIndex = event => Math.round(pointerRatio(event) * configuration.count);
      const chooseThumb = (index, event) => {
        if (data.kind !== 'range') return 0;
        const target = event.target.closest?.('[data-citry-ui-part="thumb"]');
        const direct = thumbs.indexOf(target);
        if (direct >= 0) return direct;
        const distances = current.map(value => Math.abs(indexFor(value) - index));
        if (distances[0] !== distances[1]) return distances[0] < distances[1] ? 0 : 1;
        if (lastFocusedIndex !== null) return lastFocusedIndex;
        return index >= indexFor(current[0]) ? 1 : 0;
      };
      const flushPointer = event => {
        if (!event) return;
        changedDuringDrag = Boolean(changeIndex(pointerIndex(event), activeIndex, 'pointer', event)) || changedDuringDrag;
      };
      const queuePointer = event => {
        pendingPointer = event;
        if (frame) return;
        frame = requestAnimationFrame(() => { frame = 0; const pending = pendingPointer; pendingPointer = null; flushPointer(pending); });
      };
      listeners.add(control, 'pointerdown', event => {
        if (configuration.disabled || configuration.readonly || event.button !== 0) return;
        const index = pointerIndex(event);
        activeIndex = chooseThumb(index, event);
        lastFocusedIndex = activeIndex;
        dragging = true;
        changedDuringDrag = false;
        dragPrevious = [...current];
        lastRequested = [...current];
        control.setPointerCapture(event.pointerId);
        thumbs[activeIndex].focus({ preventScroll: true });
        event.preventDefault();
        changedDuringDrag = Boolean(changeIndex(index, activeIndex, 'pointer', event)) || changedDuringDrag;
        applyState();
      });
      listeners.add(control, 'pointermove', event => { if (dragging && control.hasPointerCapture(event.pointerId)) queuePointer(event); });
      const stopPointer = event => {
        if (!dragging) return;
        if (frame) { cancelAnimationFrame(frame); frame = 0; flushPointer(pendingPointer); pendingPointer = null; }
        dragging = false;
        if (control.hasPointerCapture(event.pointerId)) control.releasePointerCapture(event.pointerId);
        if (changedDuringDrag) end(activeIndex, 'pointer', event, dragPrevious, lastRequested);
        dragPrevious = null;
        applyState();
      };
      listeners.add(control, 'pointerup', stopPointer);
      listeners.add(control, 'pointercancel', stopPointer);
      thumbs.forEach((thumb, index) => {
        listeners.add(thumb, 'focus', () => { activeIndex = index; lastFocusedIndex = index; applyState(); });
        listeners.add(thumb, 'blur', () => applyState());
        listeners.add(thumb, 'keydown', event => {
          if (configuration.disabled || configuration.readonly) return;
          let nextIndex = indexFor(current[index]);
          if (event.key === 'ArrowRight' || event.key === 'ArrowUp') nextIndex += 1;
          else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') nextIndex -= 1;
          else if (event.key === 'PageUp') nextIndex += configuration.largeSteps;
          else if (event.key === 'PageDown') nextIndex -= configuration.largeSteps;
          else if (event.key === 'Home') nextIndex = boundsFor(index)[0];
          else if (event.key === 'End') nextIndex = boundsFor(index)[1];
          else return;
          event.preventDefault();
          const previous = [...current];
          const requested = changeIndex(nextIndex, index, 'keyboard', event);
          if (requested) end(index, 'keyboard', event, previous, requested.next);
        });
      });
      const reset = runtime.registerReset(root, nativeInputs[0], {
        reset: () => {
          const previous = [...current];
          if (controlled) {
            resolver.callback('onValueChange')?.(data.kind === 'range' ? [...initialValue] : initialValue[0], detail(initialValue, previous, 'reset', null, 'change', 0));
            resolver.callback('onValueChangeEnd')?.(data.kind === 'range' ? [...initialValue] : initialValue[0], detail(initialValue, previous, 'reset', null, 'end', 0));
          } else {
            current = [...initialValue]; committed = [...initialValue]; lastRequested = [...initialValue]; applyState(); nativeInputs.forEach((_, index) => { nativeEvents(index, 'change'); nativeEvents(index, 'end'); });
          }
        },
        invalidate: () => {},
      });
      const stopFieldset = runtime.watchFieldset(root, nativeInputs[0], () => { configuration = resolveConfiguration(); if (dragging && configuration.disabled) dragging = false; applyState(); });
      const configValue = (name, fallback) => {
        const raw = props[name];
        if (raw === undefined) return fallback;
        const value = canonical(raw);
        if (value === undefined) { resolver.report(name, raw); return fallback; }
        resolver.clear(name); return value;
      };
      const resolveConfiguration = () => {
        let min = configValue('min', data.min), max = configValue('max', data.max), step = configValue('step', data.step);
        let exactGrid = grid(min, max, step);
        if (!exactGrid) { resolver.report('min', min, 'min/max/step must form a finite whole-step grid'); min = data.min; max = data.max; step = data.step; exactGrid = grid(min, max, step); }
        const largeStep = configValue('largeStep', data.largeStep);
        const largeIndex = (() => { const result = aligned([largeStep, step]); return result && result.values[0] > BigInt(0) && result.values[0] % result.values[1] === BigInt(0) ? Number(result.values[0] / result.values[1]) : null; })();
        let gap = 0;
        if (data.kind === 'range') {
          const requestedGap = props.minStepsBetweenThumbs;
          if (requestedGap === undefined) {
            gap = data.minStepsBetweenThumbs;
            resolver.clear('minStepsBetweenThumbs');
          } else if (Number.isInteger(requestedGap) && requestedGap >= 0 && requestedGap <= exactGrid.count) {
            gap = requestedGap;
            resolver.clear('minStepsBetweenThumbs');
          } else {
            gap = data.minStepsBetweenThumbs;
            resolver.report('minStepsBetweenThumbs', requestedGap);
          }
        }
        return {
          min, max, step, count: exactGrid.count, gridMin: exactGrid.min, gridStep: exactGrid.step, scale: exactGrid.scale,
          largeSteps: largeIndex ?? Math.min(10, exactGrid.count), gap,
          disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled),
          readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
          invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
          orientation: resolver.choice('orientation', data.orientation, ['horizontal', 'vertical']),
          variant: resolver.choice('variant', data.variant, ['solid', 'subtle']),
          size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
          showValue: resolver.choice('showValue', data.showValue, ['never', 'interaction', 'always']),
          format: resolver.string('format', data.format) || data.format,
        };
      };
      let unsubscribe = null;
      effect(() => {
        const previousConfiguration = configuration;
        configuration = resolveConfiguration();
        if (previousConfiguration && dragging && (configuration.min !== previousConfiguration.min || configuration.max !== previousConfiguration.max || configuration.step !== previousConfiguration.step || configuration.orientation !== previousConfiguration.orientation || configuration.disabled || configuration.readonly)) {
          dragging = false; changedDuringDrag = false; dragPrevious = null;
        }
        const requested = props.value;
        if (requested === undefined) {
          if (controlled) { controlled = false; current = [...committed]; lastRequested = [...current]; }
          resolver.clear('value');
        } else {
          const raw = data.kind === 'range' ? requested : [requested];
          if (!Array.isArray(raw) || raw.length !== expected) resolver.report('value', requested);
          else {
            const normalized = raw.map((value, index) => normalizeValue(value, current[index]));
            const indices = normalized.map(indexFor);
            const validRange = data.kind !== 'range' || indices[1] - indices[0] >= configuration.gap;
            if (indices.some(index => index === null) || !validRange) resolver.report('value', requested);
            else { resolver.clear('value'); controlled = true; current = normalized; lastRequested = [...normalized]; }
          }
        }
        applyState();
      });
      if (i18n) unsubscribe = i18n.subscribe(() => applyState());
      if (data.kind === 'range' && data.fieldLabelId) {
        const label = root.ownerDocument.getElementById(data.fieldLabelId);
        if (label) listeners.add(label, 'click', event => queueMicrotask(() => {
          if (!event.defaultPrevented && root.isConnected && !configuration.disabled) thumbs[0].focus({ preventScroll: true });
        }));
      }
      mutations.start(() => applyState());
      owned(() => { control.hidden = false; root.setAttribute('data-enhanced', ''); root.setAttribute('data-citry-slider-initialized', ''); });
      applyState();
      return () => {
        if (frame) cancelAnimationFrame(frame);
        unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
        owned(() => { control.hidden = true; root.removeAttribute('data-enhanced'); root.removeAttribute('data-citry-slider-initialized'); });
      };
    },
  });
"""


_SLIDER_CSS = """
  @layer citry-ui.theme {
    :where(.cui-slider) {
      --_cui-slider-track-color: var(--cui-slider-track-color, color-mix(in srgb, CanvasText 22%, transparent));
      --_cui-slider-fill-color: var(--cui-slider-fill-color, AccentColor);
      --_cui-slider-thumb-color: var(--cui-slider-thumb-color, Canvas);
      --_cui-slider-thumb-border-color: var(--cui-slider-thumb-border-color, AccentColor);
      --_cui-slider-focus-color: var(--cui-slider-focus-color, Highlight);
      --_cui-slider-mark-color: var(--cui-slider-mark-color, CanvasText);
      --_cui-slider-value-background: var(--cui-slider-value-background, #111827);
      --_cui-slider-value-foreground: var(--cui-slider-value-foreground, #fff);
      --_cui-slider-track-size: var(--cui-slider-track-size, .375rem);
      --_cui-slider-thumb-size: var(--cui-slider-thumb-size, 1.25rem);
      --_cui-slider-control-size: var(--cui-slider-control-size, 2.75rem);
      --_cui-slider-radius: var(--cui-slider-radius, 999px);
      display: block;
      inline-size: min(100%, 24rem);
      color: CanvasText;
    }
    :where(.cui-slider[data-orientation="vertical"]) { inline-size: var(--_cui-slider-control-size); block-size: 12rem; }
    :where(.cui-slider[data-enhanced] > [data-citry-ui-part="native-input"]) { display: none; }
    :where(.cui-slider > [data-citry-ui-part="native-input"]) { inline-size: 100%; }
    :where(.cui-slider [data-citry-ui-part="control"]) { position: relative; min-block-size: var(--_cui-slider-control-size); touch-action: none; user-select: none; }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="control"]) { min-block-size: 100%; min-inline-size: var(--_cui-slider-control-size); }
    :where(.cui-slider [data-citry-ui-part="track"]) {
      position: absolute;
      inset-inline: calc(var(--_cui-slider-thumb-size) / 2);
      inset-block-start: 50%;
      block-size: var(--_cui-slider-track-size);
      translate: 0 -50%;
      border-radius: var(--_cui-slider-radius);
      background: var(--_cui-slider-track-color);
    }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="track"]) {
      inset-block: calc(var(--_cui-slider-thumb-size) / 2);
      inset-inline-start: 50%;
      inline-size: var(--_cui-slider-track-size);
      block-size: auto;
      translate: -50% 0;
    }
    :where(.cui-slider [data-citry-ui-part="fill"]) {
      position: absolute;
      inset-block: 0;
      inset-inline-start: var(--_cui-slider-fill-start, 0%);
      inline-size: calc(var(--_cui-slider-fill-stop, 0%) - var(--_cui-slider-fill-start, 0%));
      border-radius: inherit;
      background: var(--_cui-slider-fill-color);
    }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="fill"]) {
      inset-inline: 0;
      inset-block-start: auto;
      inset-block-end: var(--_cui-slider-fill-start, 0%);
      inline-size: auto;
      block-size: calc(var(--_cui-slider-fill-stop, 0%) - var(--_cui-slider-fill-start, 0%));
    }
    :where(.cui-slider [data-citry-ui-part="thumb"]) {
      position: absolute;
      z-index: 1;
      inset-inline-start: var(--_cui-slider-position);
      inset-block-start: 50%;
      box-sizing: border-box;
      inline-size: var(--_cui-slider-thumb-size);
      block-size: var(--_cui-slider-thumb-size);
      translate: -50% -50%;
      border: 2px solid var(--_cui-slider-thumb-border-color);
      border-radius: var(--_cui-slider-radius);
      background: var(--_cui-slider-thumb-color);
      color: inherit;
      padding: 0;
      cursor: grab;
    }
    :where([dir="rtl"] .cui-slider [data-citry-ui-part="thumb"]) { translate: 50% -50%; }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="thumb"]) {
      inset-inline-start: 50%;
      inset-block-start: auto;
      inset-block-end: var(--_cui-slider-position);
      translate: -50% 50%;
    }
    :where([dir="rtl"] .cui-slider[data-orientation="vertical"] [data-citry-ui-part="thumb"]) { translate: 50% 50%; }
    :where(.cui-slider [data-citry-ui-part="thumb"]:focus-visible) { outline: 3px solid var(--_cui-slider-focus-color); outline-offset: 3px; }
    :where(.cui-slider[data-dragging] [data-citry-ui-part="thumb"][data-active]) { cursor: grabbing; scale: 1.08; }
    :where(.cui-slider [data-citry-ui-part="value"]) {
      position: absolute;
      inset-block-end: calc(100% + .5rem);
      inset-inline-start: 50%;
      translate: -50% 0;
      min-inline-size: max-content;
      border-radius: .375rem;
      padding: .2rem .4rem;
      background: var(--_cui-slider-value-background);
      color: var(--_cui-slider-value-foreground);
      font: 500 .75rem/1.2 system-ui, sans-serif;
      pointer-events: none;
      visibility: hidden;
      opacity: 0;
    }
    :where([dir="rtl"] .cui-slider [data-citry-ui-part="value"]) { translate: 50% 0; }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="value"]) { inset-block-end: auto; inset-inline-start: calc(100% + .5rem); translate: 0 -50%; }
    :where(.cui-slider [data-citry-ui-part="thumb"]:focus [data-citry-ui-part="value"], .cui-slider[data-dragging] [data-citry-ui-part="thumb"][data-active] [data-citry-ui-part="value"], .cui-slider [data-citry-ui-part="thumb"]:hover [data-citry-ui-part="value"]) { visibility: visible; opacity: 1; }
    :where(.cui-slider[data-show-value="always"] [data-citry-ui-part="value"]) { visibility: visible; opacity: 1; }
    :where(.cui-slider [data-citry-ui-part="mark"]) {
      position: absolute;
      inset-inline-start: var(--_cui-slider-mark-position);
      inset-block-start: 50%;
      inline-size: .25rem;
      block-size: .25rem;
      translate: -50% -50%;
      border-radius: 50%;
      background: var(--_cui-slider-mark-color);
    }
    :where([dir="rtl"] .cui-slider [data-citry-ui-part="mark"]) { translate: 50% -50%; }
    :where(.cui-slider [data-citry-ui-part="mark-label"]) { position: absolute; inset-block-start: .75rem; inset-inline-start: 50%; translate: -50% 0; inline-size: max-content; max-inline-size: 8rem; text-align: center; font-size: .75rem; }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="mark"]) { inset-inline-start: 50%; inset-block-start: auto; inset-block-end: var(--_cui-slider-mark-position); translate: -50% 50%; }
    :where(.cui-slider[data-orientation="vertical"] [data-citry-ui-part="mark-label"]) { inset-block-start: 50%; inset-inline-start: .75rem; translate: 0 -50%; }
    :where(.cui-slider[data-size="sm"]) { --_cui-slider-thumb-size: 1rem; --_cui-slider-control-size: 2.25rem; --_cui-slider-track-size: .25rem; }
    :where(.cui-slider[data-size="lg"]) { --_cui-slider-thumb-size: 1.5rem; --_cui-slider-control-size: 3rem; --_cui-slider-track-size: .5rem; }
    :where(.cui-slider[data-variant="subtle"]) { --_cui-slider-fill-color: color-mix(in srgb, AccentColor 62%, Canvas); }
    :where(.cui-slider[data-disabled]) { opacity: .5; }
    :where(.cui-slider[data-disabled] [data-citry-ui-part="thumb"]) { cursor: not-allowed; }
    :where(.cui-slider[data-invalid]) { --_cui-slider-thumb-border-color: light-dark(#d92d20, #f97066); --_cui-slider-fill-color: light-dark(#d92d20, #f97066); }
    :where(.cui-slider__visually-hidden) { position: absolute; inline-size: 1px; block-size: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
    @media (pointer: coarse) { :where(.cui-slider) { --_cui-slider-control-size: max(2.75rem, var(--cui-slider-control-size, 2.75rem)); } }
    @media (prefers-reduced-motion: reduce) { :where(.cui-slider [data-citry-ui-part="thumb"], .cui-slider [data-citry-ui-part="value"]) { transition: none; } }
    @media (forced-colors: active) { :where(.cui-slider) { --_cui-slider-track-color: GrayText; --_cui-slider-fill-color: Highlight; --_cui-slider-thumb-color: Canvas; --_cui-slider-thumb-border-color: ButtonText; } }
    @media print { :where(.cui-slider [data-citry-ui-part="value"]) { opacity: 1; } }
  }
"""


class CSlider(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CSliderExact | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CSliderExact = 0
        max: CSliderExact = 100
        step: CSliderExact = 1
        large_step: CSliderExact | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        orientation: CSliderOrientation = "horizontal"
        variant: CSliderVariant = "solid"
        size: CSliderSize = "md"
        show_value: CSliderShowValue = "interaction"
        show_marks: bool | None = None
        marks: Mapping[CSliderExact, str] | Sequence[CSliderExact] | None = None
        format: str = "citry-ui-slider"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return _snapshot(self, kwargs, is_range=False)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        _snapshot(self, kwargs, is_range=False)
        return cast("dict[str, object]", cast("Any", self)._cui_slider_data)

    template = _SLIDER_TEMPLATE
    js = _SLIDER_JS
    css_file = "runtime.min.css"


class CRangeSlider(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: tuple[CSliderExact, CSliderExact] | None = None
        name: str | None = None
        lower_name: str | None = None
        upper_name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CSliderExact = 0
        max: CSliderExact = 100
        step: CSliderExact = 1
        large_step: CSliderExact | None = None
        min_steps_between_thumbs: int = 0
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        orientation: CSliderOrientation = "horizontal"
        variant: CSliderVariant = "solid"
        size: CSliderSize = "md"
        show_value: CSliderShowValue = "interaction"
        show_marks: bool | None = None
        marks: Mapping[CSliderExact, str] | Sequence[CSliderExact] | None = None
        format: str = "citry-ui-slider"
        lower_label: str = "Lower value"
        upper_label: str = "Upper value"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        lower_input_attrs: Mapping[str, object] | None = None
        upper_input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return _snapshot(self, kwargs, is_range=True)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        _snapshot(self, kwargs, is_range=True)
        return cast("dict[str, object]", cast("Any", self)._cui_slider_data)

    template = _SLIDER_TEMPLATE
    js = _SLIDER_JS
    css_file = "runtime.min.css"

    messages = """
      citry-ui-range-slider-lower = Lower value
      citry-ui-range-slider-upper = Upper value
    """
