"""Localized two-ended calendar date range picker."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    get_html_form_owner,
    merge_root_attrs,
    pop_html_attr,
    reject_html_attr_bindings,
)
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._date import canonical_date
from citry_ui.components._form_control_runtime import (
    FORM_CONTROL_RUNTIME_DEPENDENCY,
    FORM_CONTROL_STYLE_DEPENDENCY,
)
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
)

if TYPE_CHECKING:
    from citry_ui.components.cpopover import CPopoverPlacement

CDateRangeDate: TypeAlias = date | str
CDateRangeVariant = Literal["outline", "filled", "plain"]
CDateRangeSize = Literal["sm", "md", "lg"]
CDateRangeValueChangeSource = Literal["calendar", "clear", "reset", "native"]


class CDateRangeValue(TypedDict):
    start: str
    end: str


class CDateRangeValueChangeDetail(TypedDict):
    value: CDateRangeValue | None
    previousValue: CDateRangeValue | None
    controlled: bool
    source: CDateRangeValueChangeSource
    sourceEvent: object | None


class CDateRangeOpenChangeDetail(TypedDict):
    reason: Literal[
        "trigger",
        "selection",
        "clear",
        "reset",
        "escape",
        "outside",
        "focus-outside",
        "native",
        "ancestor",
        "modal",
    ]
    controlled: bool
    forced: bool
    source: object | None


_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_PLACEMENTS = ("top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end")
_DISPLAY_PROFILE = "citry-ui-date-picker-display"
_SOURCE_MONTHS = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_RUNTIME_PREFIXES = ("data-citry-", "data-cdate-range", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "aria-label",
        "aria-labelledby",
        "aria-readonly",
        "data-citry-date-range-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-enhanced",
        "data-invalid",
        "data-open",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "id",
        "role",
        "tabindex",
    }
)


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(value: Mapping[str, object] | None) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CDateRange attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _ROOT_OWNED - {"aria-label", "aria-labelledby"}, "CDateRange")
    reject_html_attr_bindings(copied, _ROOT_OWNED, "CDateRange")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CDateRange attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CDateRange attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CDateRange attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _ROOT_OWNED:
            raise ValueError(f"CDateRange attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


def _dates(value: object) -> tuple[str, ...]:
    value = const_value(value)
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError("CDateRange unavailable_dates must be a sequence of exact dates or canonical strings.")
    if len(value) > 4096:
        raise ValueError("CDateRange unavailable_dates may contain at most 4096 dates.")
    normalized = tuple(cast("str", canonical_date("CDateRange", "unavailable_dates item", item)) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("CDateRange unavailable_dates cannot contain duplicates.")
    return tuple(sorted(normalized))


def _first_day(value: object) -> int | None:
    value = const_value(value)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"CDateRange first_day_of_week must be an exact integer or None, got {value!r}.")
    if value < 1 or value > 7:
        raise ValueError(f"CDateRange first_day_of_week must be from 1 through 7, got {value!r}.")
    return value


def _source_display_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{_SOURCE_MONTHS[parsed.month]} {parsed.day}, {parsed.year:04d}"


def _range_crosses_unavailable(start: str, end: str, unavailable: Sequence[str]) -> bool:
    return any(start <= item <= end for item in unavailable)


class CDateRange(LibraryComponent):
    class I18n:
        messages_locale = "en-US"
        client_messages = (
            "citry-ui-date-range-placeholder",
            "citry-ui-date-range-change",
            "citry-ui-date-range-start-label",
            "citry-ui-date-range-end-label",
            "citry-ui-date-range-unavailable",
        )

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        start: CDateRangeDate | None = None
        end: CDateRangeDate | None = None
        start_name: str | None = None
        end_name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CDateRangeDate | None = None
        max: CDateRangeDate | None = None
        unavailable_dates: Sequence[CDateRangeDate] = ()
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        clearable: bool = True
        dismissible: bool = True
        placement: CPopoverPlacement = "bottom-start"
        match_width: bool = True
        first_day_of_week: int | None = None
        show_adjacent_days: bool = True
        fixed_weeks: bool = True
        placeholder: str = "Choose dates"
        range_label: str = "Choose date range"
        change_label: str = "Change date range, {start} to {end}"
        start_label: str = "Start date"
        end_label: str = "End date"
        clear_label: str = "Clear date range"
        unavailable_message: str = "Choose an available date range."
        variant: CDateRangeVariant = "outline"
        size: CDateRangeSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_date_range_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        start = canonical_date("CDateRange", "start", kwargs.start, optional=True)
        end = canonical_date("CDateRange", "end", kwargs.end, optional=True)
        minimum = canonical_date("CDateRange", "min", kwargs.min, optional=True)
        maximum = canonical_date("CDateRange", "max", kwargs.max, optional=True)
        unavailable_dates = _dates(kwargs.unavailable_dates)
        if (start is None) != (end is None):
            raise ValueError("CDateRange start and end must either both be provided or both be empty.")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"CDateRange min {minimum!r} cannot be later than max {maximum!r}.")
        if start is not None and end is not None:
            if start > end:
                raise ValueError("CDateRange start cannot be later than end.")
            if minimum is not None and start < minimum:
                raise ValueError("CDateRange start cannot be earlier than min.")
            if maximum is not None and end > maximum:
                raise ValueError("CDateRange end cannot be later than max.")
            if _range_crosses_unavailable(start, end, unavailable_dates):
                raise ValueError("CDateRange committed range cannot include an unavailable date.")

        start_name = const_value(kwargs.start_name)
        end_name = const_value(kwargs.end_name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        for input_name, value in (("start_name", start_name), ("end_name", end_name)):
            if value is not None:
                validate_non_empty_string("CDateRange", input_name, value)
        if start_name is not None and start_name == end_name:
            raise ValueError("CDateRange start_name and end_name must be different when both are supplied.")
        validate_html_id("CDateRange", form_input)
        validate_html_id("CDateRange", supplied_id)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CDateRange", input_name, getattr(kwargs, input_name))
        for input_name in ("clearable", "dismissible", "match_width", "show_adjacent_days", "fixed_weeks"):
            validate_boolean("CDateRange", input_name, getattr(kwargs, input_name))
        first_day = _first_day(kwargs.first_day_of_week)
        validate_choice("CDateRange", "placement", kwargs.placement, _PLACEMENTS)
        validate_choice("CDateRange", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CDateRange", "size", kwargs.size, _SIZES)
        for input_name in (
            "placeholder",
            "range_label",
            "change_label",
            "start_label",
            "end_label",
            "clear_label",
            "unavailable_message",
        ):
            validate_non_empty_string("CDateRange", input_name, const_value(getattr(kwargs, input_name)))
        if "{start}" not in kwargs.change_label or "{end}" not in kwargs.change_label:
            raise ValueError("CDateRange change_label must contain both {start} and {end} placeholders.")

        field = self.inject(FIELD_CONTEXT_KEY, None)
        if field is not None:
            raise ValueError(
                "CDateRange cannot compose inside CField because it submits two controls; use a fieldset and legend."
            )
        form = self.inject(FORM_CONTEXT_KEY, None)
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CDateRange",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CDateRange inside CForm cannot target a different native form owner.")

        public_id = supplied_id or f"cui-date-range-{self.id}"
        root_id = f"{public_id}-root"
        start_id = f"{public_id}-start"
        end_id = f"{public_id}-end"
        popover_id = f"{public_id}-popover"
        calendar_id = f"{public_id}-calendar"
        caller_attrs = _attrs(kwargs.attrs)
        authored_label = pop_html_attr(caller_attrs, "aria-label", component_name="CDateRange")
        authored_labelledby = pop_html_attr(caller_attrs, "aria-labelledby", component_name="CDateRange")
        external_described_by = pop_html_attr(caller_attrs, "aria-describedby", component_name="CDateRange")
        external_error_message = pop_html_attr(caller_attrs, "aria-errormessage", component_name="CDateRange")
        for input_name, authored in (
            ("attrs aria-label", authored_label),
            ("attrs aria-labelledby", authored_labelledby),
            ("attrs aria-describedby", external_described_by),
            ("attrs aria-errormessage", external_error_message),
        ):
            if authored is not None and not isinstance(authored, str):
                raise TypeError(f"CDateRange {input_name} must be a string.")

        required = bool(kwargs.required)
        disabled = bool(form.disabled if form is not None else False) or bool(kwargs.disabled)
        readonly = bool(
            kwargs.readonly if kwargs.readonly is not None else form.readonly if form is not None else False
        )
        invalid = bool(kwargs.invalid)
        catalog = {
            input_name: uses_catalog_default(self, input_name)
            for input_name in (
                "placeholder",
                "range_label",
                "change_label",
                "start_label",
                "end_label",
                "clear_label",
                "unavailable_message",
            )
        }

        def translated(owner: str, message: str, fallback: str) -> str:
            return self.i18n.tr(message) if catalog[owner] else fallback

        placeholder = translated("placeholder", "citry-ui-date-range-placeholder", kwargs.placeholder)
        range_label = (
            str(authored_label)
            if authored_label is not None
            else translated("range_label", "citry-ui-date-range-label", kwargs.range_label)
        )
        start_label = translated("start_label", "citry-ui-date-range-start-label", kwargs.start_label)
        end_label = translated("end_label", "citry-ui-date-range-end-label", kwargs.end_label)
        clear_label = translated("clear_label", "citry-ui-date-range-clear", kwargs.clear_label)
        unavailable_message = translated(
            "unavailable_message", "citry-ui-date-range-unavailable", kwargs.unavailable_message
        )
        if self.i18n.configured:
            self.i18n.format.date(date(2000, 1, 3), format=_DISPLAY_PROFILE)

        def display(value: str) -> str:
            return (
                self.i18n.format.date(date.fromisoformat(value), format=_DISPLAY_PROFILE)
                if self.i18n.configured
                else _source_display_date(value)
            )

        display_start = display(start) if start is not None else None
        display_end = display(end) if end is not None else None
        display_value = (
            f"{display_start} \N{EN DASH} {display_end}"
            if display_start is not None and display_end is not None
            else None
        )
        if display_start is not None and display_end is not None and catalog["change_label"]:
            trigger_label = self.i18n.tr("citry-ui-date-range-change", start=display_start, end=display_end)
        elif display_start is not None and display_end is not None:
            trigger_label = kwargs.change_label.replace("{start}", display_start).replace("{end}", display_end)
        else:
            trigger_label = range_label

        # The child Calendar is selection UI, not a third Form control.
        self.unprovide(FIELD_CONTEXT_KEY)
        self.unprovide(FORM_CONTEXT_KEY)

        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": root_id,
            "start_id": start_id,
            "end_id": end_id,
            "popover_id": popover_id,
            "calendar_id": calendar_id,
            "start_name": start_name,
            "end_name": end_name,
            "form": form_owner,
            "start": start,
            "end": end,
            "start_max": end or maximum,
            "end_min": start or minimum,
            "minimum": minimum,
            "maximum": maximum,
            "unavailable_dates": unavailable_dates,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "clearable": kwargs.clearable,
            "dismissible": kwargs.dismissible,
            "placement": kwargs.placement,
            "match_width": kwargs.match_width,
            "first_day": first_day,
            "show_adjacent_days": kwargs.show_adjacent_days,
            "fixed_weeks": kwargs.fixed_weeks,
            "placeholder": placeholder,
            "range_label": range_label,
            "start_label": start_label,
            "end_label": end_label,
            "trigger_label": trigger_label,
            "clear_label": clear_label,
            "catalog_range_label": authored_label is None and authored_labelledby is None and catalog["range_label"],
            "catalog_start_label": catalog["start_label"],
            "catalog_end_label": catalog["end_label"],
            "catalog_clear_label": catalog["clear_label"],
            "display_value": display_value,
            "labelled_by": authored_labelledby,
            "described_by": external_described_by,
            "error_message": external_error_message if invalid else None,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "attrs": merge_root_attrs(caller_attrs, kwargs.class_, kwargs.style),
        }
        context = self.i18n.context
        client_data: dict[str, object] = {
            "publicId": public_id,
            "startId": start_id,
            "endId": end_id,
            "value": {"start": start, "end": end} if start is not None and end is not None else None,
            "min": minimum,
            "max": maximum,
            "unavailableDates": unavailable_dates,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": kwargs.readonly is None,
            "clearable": kwargs.clearable,
            "dismissible": kwargs.dismissible,
            "placement": kwargs.placement,
            "matchWidth": kwargs.match_width,
            "placeholder": placeholder,
            "rangeLabel": range_label,
            "changeLabel": kwargs.change_label,
            "startLabel": start_label,
            "endLabel": end_label,
            "clearLabel": clear_label,
            "unavailableMessage": unavailable_message,
            "catalog": catalog,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "locale": context.locale,
            "describedby": cast("str | None", external_described_by),
            "errormessage": cast("str | None", external_error_message),
        }
        self._cui_date_range_data = client_data
        self._cui_date_range_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_date_range_data

    template = """
      <div
        class="cui-date-range"
        c-id="root_id"
        role="group"
        c-aria-label="tr('citry-ui-date-range-label') if catalog_range_label else range_label if not labelled_by else None"
        c-aria-labelledby="labelled_by"
        c-aria-describedby="described_by"
        c-aria-errormessage="error_message"
        c-aria-invalid="'true' if invalid else None"
        c-aria-disabled="'true' if disabled else None"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-empty="not start"
        c-data-variant="variant"
        c-data-size="size"
        c-$c-tr:citry-ui-date-range-label[aria-label]="True if catalog_range_label else None"
        c-bind="attrs"
        data-citry-ui-part="date-range"
      >
        <div class="cui-date-range__fallback" data-citry-ui-part="fallback-group">
          <label class="cui-date-range__fallback-field">
            <span c-$c-tr:citry-ui-date-range-start-label="True if catalog_start_label else None">{{ tr('citry-ui-date-range-start-label') if catalog_start_label else start_label }}</span>
            <input
              c-id="start_id"
              c-name="start_name"
              c-form="form"
              type="date"
              c-value="start"
              c-min="minimum"
              c-max="start_max"
              c-required="required"
              c-disabled="disabled"
              c-readonly="readonly"
              c-aria-describedby="described_by"
              c-aria-errormessage="error_message"
              c-aria-invalid="'true' if invalid else None"
              data-citry-ui-part="start-input"
            />
          </label>
          <label class="cui-date-range__fallback-field">
            <span c-$c-tr:citry-ui-date-range-end-label="True if catalog_end_label else None">{{ tr('citry-ui-date-range-end-label') if catalog_end_label else end_label }}</span>
            <input
              c-id="end_id"
              c-name="end_name"
              c-form="form"
              type="date"
              c-value="end"
              c-min="end_min"
              c-max="maximum"
              c-required="required"
              c-disabled="disabled"
              c-readonly="readonly"
              c-aria-describedby="described_by"
              c-aria-errormessage="error_message"
              c-aria-invalid="'true' if invalid else None"
              data-citry-ui-part="end-input"
            />
          </label>
        </div>
        <div class="cui-date-range__enhanced" data-citry-ui-part="enhanced-control">
          <c-CPopover
            c-id="popover_id"
            c-dismissible="dismissible"
            c-placement="placement"
            c-match_width="match_width"
            class_="cui-date-range__popover"
            $c-props="{open:dateRangeOpen,dismissible:dateRangeDismissible,placement:dateRangePlacement,matchWidth:dateRangeMatchWidth,onOpenChange:dateRangeOnPopoverOpenChange}"
          >
            <c-fill name="activator" data="{ activator_attrs }">
              <button
                class="cui-date-range__control"
                c-id="public_id"
                type="button"
                c-disabled="disabled"
                c-aria-label="trigger_label"
                c-bind="activator_attrs"
                data-citry-date-range-trigger
                data-citry-ui-part="control"
              >
                <span class="cui-date-range__value" data-citry-ui-part="value">{{ display_value if display_value else placeholder }}</span>
                <c-CIcon name="calendar" class_="cui-date-range__icon" />
              </button>
            </c-fill>
            <c-fill name="title">
              <span c-$c-tr:citry-ui-date-range-label="True if catalog_range_label else None">{{ tr('citry-ui-date-range-label') if catalog_range_label else range_label }}</span>
            </c-fill>
            <c-fill name="default">
              <c-CCalendar
                c-id="calendar_id"
                c-value="end if end else start"
                c-min="minimum"
                c-max="maximum"
                c-unavailable_dates="unavailable_dates"
                c-disabled="disabled"
                c-readonly="readonly"
                c-first_day_of_week="first_day"
                c-show_adjacent_days="show_adjacent_days"
                c-fixed_weeks="fixed_weeks"
                c-label="range_label"
                variant="plain"
                class_="cui-date-range__calendar"
                $c-props="{value:dateRangeCalendarValue,disabled:dateRangeCalendarDisabled,readonly:dateRangeCalendarReadonly,rangeStart:dateRangeRangeStart,rangeEnd:dateRangeRangeEnd,rangePreview:dateRangeRangePreview,rangeStartLabel:dateRangeStartLabel,rangeEndLabel:dateRangeEndLabel,accessibleLabel:dateRangeAccessibleLabel,onValueChange:dateRangeOnCalendarValueChange}"
              />
            </c-fill>
          </c-CPopover>
          <button
            class="cui-date-range__clear"
            type="button"
            c-aria-label="tr('citry-ui-date-range-clear') if catalog_clear_label else clear_label"
            c-$c-tr:citry-ui-date-range-clear[aria-label]="True if catalog_clear_label else None"
            c-hidden="not clearable or required or not start"
            c-disabled="disabled or readonly"
            data-citry-ui-part="clear"
          ><span aria-hidden="true">&times;</span></button>
        </div>
      </div>
    """

    js = """
      $component({
        props: {
          value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, clearable: {},
          dismissible: {}, placement: {}, matchWidth: {}, variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
        },
        init: ({ els, data, props, scope, effect, inject, i18n }) => {
          const root = els[0];
          const fallback = root.querySelector(':scope > [data-citry-ui-part="fallback-group"]');
          const startInput = fallback?.querySelector('[data-citry-ui-part="start-input"]');
          const endInput = fallback?.querySelector('[data-citry-ui-part="end-input"]');
          const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
          const trigger = root.querySelector('[data-citry-date-range-trigger]');
          const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
          const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
          const calendar = root.querySelector('.cui-date-range__calendar[data-citry-ui-part="calendar"]');
          if (!(root instanceof HTMLElement) || !(fallback instanceof HTMLElement) || !(startInput instanceof HTMLInputElement) || startInput.type !== 'date' || !(endInput instanceof HTMLInputElement) || endInput.type !== 'date' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement) || !(calendar instanceof HTMLElement)) throw new Error('[citry-ui] CDateRange settled anatomy is invalid.');

          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CDateRange form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CDateRange');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          const unavailable = new Set(data.unavailableDates);
          const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
          let current = data.value ? { ...data.value } : null;
          const initialValue = data.value ? { ...data.value } : null;
          let draftStart = null;
          let previewEnd = null;
          let internalOpen = false;
          let controlledValue = false;
          let controlledOpen = false;
          let nativeInvalid = false;
          let unavailableMessage = data.unavailableMessage;
          let invalidGeneration = 0;
          let dispatching = false;
          let ready = false;
          let configuration = null;
          let lastRangePresentation = null;

          const canonicalDate = value => {
            if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
            const [year, month, day] = value.split('-').map(Number);
            if (year < 1 || year > 9999) return null;
            const result = new Date(0); result.setUTCHours(12, 0, 0, 0); result.setUTCFullYear(year, month - 1, day);
            return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
          };
          const fields = value => { const [year, month, day] = value.split('-').map(Number); return { year, month, day }; };
          const fromIso = value => { const [year, month, day] = value.split('-').map(Number); const result = new Date(0); result.setUTCHours(12, 0, 0, 0); result.setUTCFullYear(year, month - 1, day); return result; };
          const formatDate = value => i18n
            ? i18n.format.date(fields(value), { format:'citry-ui-date-picker-display' })
            : new Intl.DateTimeFormat(data.locale, { day:'numeric', month:'long', timeZone:'UTC', year:'numeric' }).format(fromIso(value));
          const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
          const placeholderText = () => translated('placeholder', 'citry-ui-date-range-placeholder', data.placeholder);
          const rangeLabel = () => translated('range_label', 'citry-ui-date-range-label', data.rangeLabel);
          const startLabel = () => translated('start_label', 'citry-ui-date-range-start-label', data.startLabel);
          const endLabel = () => translated('end_label', 'citry-ui-date-range-end-label', data.endLabel);
          const triggerLabel = value => value
            ? translated('change_label', 'citry-ui-date-range-change', data.changeLabel.replaceAll('{start}', formatDate(value.start)).replaceAll('{end}', formatDate(value.end)), { start:formatDate(value.start), end:formatDate(value.end) })
            : rangeLabel();
          const rangeCrossesUnavailable = value => value !== null && data.unavailableDates.some(item => item >= value.start && item <= value.end);
          const normalizePair = (start, end) => start <= end ? { start, end } : { start:end, end:start };
          const validPair = value => value !== null && canonicalDate(value.start) !== null && canonicalDate(value.end) !== null && value.start <= value.end && (data.min === null || value.start >= data.min) && (data.max === null || value.end <= data.max) && !rangeCrossesUnavailable(value);
          const samePair = (left, right) => left === right || (left !== null && right !== null && left.start === right.start && left.end === right.end);
          const resolveConfiguration = () => ({
            required: resolver.boolean('required', data.required),
            disabled: Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(startInput) || runtime.fieldsetDisabled(endInput),
            readonly: resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: resolver.boolean('invalid', data.invalid),
            clearable: resolver.boolean('clearable', data.clearable),
            dismissible: resolver.boolean('dismissible', data.dismissible),
            placement: resolver.choice('placement', data.placement, allowedPlacements),
            matchWidth: resolver.boolean('matchWidth', data.matchWidth),
            variant: resolver.choice('variant', data.variant, ['outline','filled','plain']),
            size: resolver.choice('size', data.size, ['sm','md','lg']),
          });
          const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled:controlledValue, source, sourceEvent });
          const openDetail = (reason, source, forced = false) => ({ reason, controlled:controlledOpen, forced, source });
          const emitNative = (previous, next) => {
            dispatching = true;
            try {
              if (previous?.start !== next?.start) { startInput.dispatchEvent(new Event('input', { bubbles:true })); startInput.dispatchEvent(new Event('change', { bubbles:true })); }
              if (previous?.end !== next?.end) { endInput.dispatchEvent(new Event('input', { bubbles:true })); endInput.dispatchEvent(new Event('change', { bubbles:true })); }
            } finally { dispatching = false; }
          };
          const focusCalendar = () => requestAnimationFrame(() => requestAnimationFrame(() => {
            if (!root.isConnected || !scope.dateRangeOpen) return;
            calendar.querySelector('[data-citry-ui-part="day"][tabindex="0"]')?.focus({ preventScroll:true });
          }));
          const requestOpen = (next, reason, source = null, forced = false) => {
            if (next === scope.dateRangeOpen && !forced) return;
            if (next) { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = null; }
            else { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = current?.end ?? null; }
            if (!controlledOpen || forced) { internalOpen = next; scope.dateRangeOpen = next; }
            resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
          };
          const requestValue = (next, source, event) => {
            if (configuration.disabled || configuration.readonly || samePair(next, current)) return false;
            if (next !== null && !validPair(next)) return false;
            const previous = current ? { ...current } : null;
            if (!controlledValue) current = next ? { ...next } : null;
            resolver.callback('onValueChange')?.(next ? { ...next } : null, valueDetail(next ? { ...next } : null, previous, source, event));
            if (!controlledValue) { render(); emitNative(previous, current); }
            return true;
          };
          const commitCalendarDate = (next, event) => {
            if (configuration.disabled || configuration.readonly || unavailable.has(next)) return false;
            if (draftStart === null) {
              draftStart = next; previewEnd = next; scope.dateRangeCalendarValue = next; render(); return true;
            }
            const pair = normalizePair(draftStart, next);
            if (!validPair(pair)) { previewEnd = next; render(); return false; }
            draftStart = null; previewEnd = null;
            requestValue(pair, 'calendar', event);
            requestOpen(false, 'selection', event);
            render();
            return true;
          };
          const syncRangePresentation = () => {
            const preview = draftStart !== null ? normalizePair(draftStart, previewEnd ?? draftStart) : null;
            const shown = preview ?? current;
            const presentation = {
              rangeStart:shown?.start ?? null,
              rangeEnd:shown?.end ?? null,
              rangePreview:preview !== null,
              rangeStartLabel:startLabel(),
              rangeEndLabel:endLabel(),
              accessibleLabel:rangeLabel(),
            };
            scope.dateRangeRangeStart = presentation.rangeStart;
            scope.dateRangeRangeEnd = presentation.rangeEnd;
            scope.dateRangeRangePreview = presentation.rangePreview;
            scope.dateRangeStartLabel = presentation.rangeStartLabel;
            scope.dateRangeEndLabel = presentation.rangeEndLabel;
            scope.dateRangeAccessibleLabel = presentation.accessibleLabel;
            const serialized = JSON.stringify(presentation);
            if (serialized === lastRangePresentation) return;
            lastRangePresentation = serialized;
            calendar.dispatchEvent(new CustomEvent('citry-ui:calendar-range-presentation', { detail:presentation }));
          };
          const render = () => owned(() => {
            startInput.value = current?.start ?? '';
            endInput.value = current?.end ?? '';
            startInput.required = configuration.required; endInput.required = configuration.required;
            startInput.disabled = configuration.disabled; endInput.disabled = configuration.disabled;
            startInput.readOnly = configuration.readonly; endInput.readOnly = configuration.readonly;
            startInput.min = data.min ?? ''; startInput.max = current?.end ?? data.max ?? '';
            endInput.min = current?.start ?? data.min ?? ''; endInput.max = data.max ?? '';
            const unavailableValue = current !== null && !validPair(current);
            startInput.setCustomValidity(unavailableValue ? unavailableMessage : '');
            endInput.setCustomValidity(unavailableValue ? unavailableMessage : '');
            const invalid = configuration.invalid || nativeInvalid || unavailableValue;
            trigger.disabled = configuration.disabled;
            trigger.setAttribute('aria-label', triggerLabel(current));
            valueText.textContent = current ? `${formatDate(current.start)} \u2013 ${formatDate(current.end)}` : placeholderText();
            clear.hidden = !configuration.clearable || configuration.required || current === null;
            clear.disabled = configuration.disabled || configuration.readonly;
            runtime.states(root, { empty:current === null, open:scope.dateRangeOpen, required:configuration.required, disabled:configuration.disabled, readonly:configuration.readonly, invalid });
            root.dataset.variant = configuration.variant; root.dataset.size = configuration.size;
            root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
            root.setAttribute('aria-invalid', invalid ? 'true' : 'false');
            scope.dateRangeCalendarDisabled = configuration.disabled;
            scope.dateRangeCalendarReadonly = configuration.readonly;
            scope.dateRangeDismissible = configuration.dismissible;
            scope.dateRangePlacement = configuration.placement;
            scope.dateRangeMatchWidth = configuration.matchWidth;
            syncRangePresentation();
          });

          scope.dateRangeOpen = internalOpen;
          scope.dateRangeCalendarValue = current?.end ?? null;
          scope.dateRangeCalendarDisabled = false;
          scope.dateRangeCalendarReadonly = false;
          scope.dateRangeRangeStart = current?.start ?? null;
          scope.dateRangeRangeEnd = current?.end ?? null;
          scope.dateRangeRangePreview = false;
          scope.dateRangeStartLabel = startLabel();
          scope.dateRangeEndLabel = endLabel();
          scope.dateRangeAccessibleLabel = rangeLabel();
          scope.dateRangeOnPopoverOpenChange = (next, detail) => {
            if (detail?.forced) { internalOpen = false; scope.dateRangeOpen = false; draftStart = null; previewEnd = null; resolver.callback('onOpenChange')?.(false, { ...detail, controlled:controlledOpen }); if (ready) render(); return; }
            requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
            if (next) focusCalendar();
            if (ready) render();
          };
          scope.dateRangeOnCalendarValueChange = (next, detail) => commitCalendarDate(next, detail?.sourceEvent ?? null);

          listeners.add(clear, 'click', event => { if (requestValue(null, 'clear', event)) requestOpen(false, 'clear', event); });
          listeners.add(calendar, 'pointerover', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement) { previewEnd = cell.dataset.date; render(); } });
          listeners.add(calendar, 'focusin', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement) { previewEnd = cell.dataset.date; render(); } });
          listeners.add(calendar, 'click', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement && cell.dataset.date === draftStart) { event.stopImmediatePropagation(); commitCalendarDate(draftStart, event); } }, true);
          listeners.add(calendar, 'keydown', event => { const cell = event.target.closest?.('[data-citry-ui-part="day"][data-date]'); if (draftStart !== null && cell instanceof HTMLElement && cell.dataset.date === draftStart && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); event.stopImmediatePropagation(); commitCalendarDate(draftStart, event); } }, true);
          const nativeCommit = event => {
            if (dispatching) return;
            const start = startInput.value || null; const end = endInput.value || null;
            if (start === null || end === null) { if (!configuration.required && start === null && end === null) requestValue(null, 'native', event); return; }
            const pair = { start, end };
            if (validPair(pair)) { nativeInvalid = false; requestValue(pair, 'native', event); }
          };
          listeners.add(startInput, 'input', nativeCommit); listeners.add(endInput, 'input', nativeCommit);
          listeners.add(startInput, 'change', nativeCommit); listeners.add(endInput, 'change', nativeCommit);
          const onInvalid = event => {
            event.preventDefault(); nativeInvalid = true; requestOpen(true, 'native', event); render();
            const token = ++invalidGeneration; runtime.invalidFocus(root, trigger, () => token === invalidGeneration && !configuration.disabled); focusCalendar();
          };
          listeners.add(startInput, 'invalid', onInvalid, true); listeners.add(endInput, 'invalid', onInvalid, true);
          const reset = runtime.registerReset(root, startInput, {
            reset: event => { if (event.defaultPrevented) return; nativeInvalid = false; draftStart = null; previewEnd = null; const previous = current; if (!controlledValue) current = initialValue ? { ...initialValue } : null; else resolver.callback('onValueChange')?.(initialValue ? { ...initialValue } : null, valueDetail(initialValue, previous, 'reset', event)); requestOpen(false, 'reset', event); render(); },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(root, startInput, () => { configuration = resolveConfiguration(); render(); });
          const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message:'citry-ui-date-range-unavailable', onChange:text => { unavailableMessage = text; if (ready) render(); } }) : null;
          const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

          effect(() => {
            configuration = resolveConfiguration();
            const requestedValue = props.value;
            if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
            else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
            else if (typeof requestedValue === 'object' && validPair(requestedValue)) { controlledValue = true; current = { start:requestedValue.start, end:requestedValue.end }; resolver.clear('value'); }
            else resolver.report('value', requestedValue);
            const requestedOpen = props.open;
            if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.dateRangeOpen; controlledOpen = false; resolver.clear('open'); }
            else if (typeof requestedOpen === 'boolean') { const opening = !scope.dateRangeOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.dateRangeOpen = requestedOpen; resolver.clear('open'); if (opening) { draftStart = null; previewEnd = null; scope.dateRangeCalendarValue = null; focusCalendar(); } }
            else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.dateRangeOpen; controlledOpen = false; }
            ready = true; render();
          });
          mutations.start(() => render());
          owned(() => { startInput.tabIndex = -1; endInput.tabIndex = -1; root.toggleAttribute('data-enhanced', true); root.setAttribute('data-citry-date-range-initialized', ''); });
          render();

          return () => {
            ready = false; invalidGeneration += 1; unavailableBinding?.dispose(); unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
            owned(() => { startInput.removeAttribute('tabindex'); endInput.removeAttribute('tabindex'); root.removeAttribute('data-enhanced'); root.removeAttribute('data-citry-date-range-initialized'); });
          };
        },
      });
    """

    css_file = "runtime.min.css"

    messages = """
      citry-ui-date-range-placeholder = Choose dates
      citry-ui-date-range-label = Choose date range
      # @param {str} $start - Locale-formatted start date.
      # @param {str} $end - Locale-formatted end date.
      citry-ui-date-range-change = Change date range, { $start } to { $end }
      citry-ui-date-range-start-label = Start date
      citry-ui-date-range-end-label = End date
      citry-ui-date-range-clear = Clear date range
      citry-ui-date-range-unavailable = Choose an available date range.
    """


__all__ = [
    "CDateRange",
    "CDateRangeDate",
    "CDateRangeOpenChangeDetail",
    "CDateRangeSize",
    "CDateRangeValue",
    "CDateRangeValueChangeDetail",
    "CDateRangeValueChangeSource",
    "CDateRangeVariant",
]
