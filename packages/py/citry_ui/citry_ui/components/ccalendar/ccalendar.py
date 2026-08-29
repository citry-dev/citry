"""Localized inline calendar-date selector."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, Literal, TypeAlias, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._aria import merge_idrefs
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
from citry_ui.components._form_control_runtime import FORM_CONTROL_RUNTIME_DEPENDENCY
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
)

CCalendarDate: TypeAlias = date | str
CCalendarVariant = Literal["outline", "plain"]
CCalendarSize = Literal["sm", "md", "lg"]
CCalendarChangeSource = Literal["pointer", "keyboard", "button", "value", "reset"]


class CCalendarValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    controlled: bool
    source: CCalendarChangeSource
    sourceEvent: object | None


class CCalendarVisibleDateChangeDetail(TypedDict):
    visibleDate: str
    previousVisibleDate: str
    controlled: bool
    source: CCalendarChangeSource
    sourceEvent: object | None


_VARIANTS = ("outline", "plain")
_SIZES = ("sm", "md", "lg")
_CALENDAR_DATE_FORMATS = (
    "citry-ui-calendar-heading",
    "citry-ui-calendar-year",
    "citry-ui-calendar-weekday",
    "citry-ui-calendar-weekday-long",
    "citry-ui-calendar-day",
    "citry-ui-calendar-date-label",
)
_RUNTIME_PREFIXES = ("data-citry-", "data-ccalendar", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "aria-readonly",
        "data-citry-calendar-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-enhanced",
        "data-invalid",
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
        raise TypeError(f"CCalendar attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _ROOT_OWNED, "CCalendar")
    reject_html_attr_bindings(copied, _ROOT_OWNED, "CCalendar")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CCalendar attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CCalendar attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CCalendar attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _ROOT_OWNED:
            raise ValueError(f"CCalendar attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


def _dates(value: object) -> tuple[str, ...]:
    value = const_value(value)
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError("CCalendar unavailable_dates must be a sequence of exact dates or canonical strings.")
    if len(value) > 4096:
        raise ValueError("CCalendar unavailable_dates may contain at most 4096 dates.")
    normalized = tuple(cast("str", canonical_date("CCalendar", "unavailable_dates item", item)) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("CCalendar unavailable_dates cannot contain duplicates.")
    return tuple(sorted(normalized))


def _first_day(value: object) -> int | None:
    value = const_value(value)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError("CCalendar first_day_of_week must be an exact integer from 1 through 7 or None.")
    if not 1 <= value <= 7:
        raise ValueError("CCalendar first_day_of_week must be from 1 through 7.")
    return cast("int", value)


class CCalendar(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CCalendarDate | None = None
        visible_date: CCalendarDate | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CCalendarDate | None = None
        max: CCalendarDate | None = None
        unavailable_dates: Sequence[CCalendarDate] = ()
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        first_day_of_week: Literal[1, 2, 3, 4, 5, 6, 7] | None = None
        show_adjacent_days: bool = True
        fixed_weeks: bool = True
        label: str = "Calendar"
        previous_label: str = "Previous month"
        next_label: str = "Next month"
        unavailable_message: str = "Choose an available date."
        variant: CCalendarVariant = "outline"
        size: CCalendarSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_calendar_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = canonical_date("CCalendar", "value", kwargs.value, optional=True)
        visible_date = canonical_date("CCalendar", "visible_date", kwargs.visible_date, optional=True)
        minimum = canonical_date("CCalendar", "min", kwargs.min, optional=True)
        maximum = canonical_date("CCalendar", "max", kwargs.max, optional=True)
        unavailable_dates = _dates(kwargs.unavailable_dates)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"CCalendar min {minimum!r} cannot be later than max {maximum!r}.")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("CCalendar value cannot be earlier than min.")
        if value is not None and maximum is not None and value > maximum:
            raise ValueError("CCalendar value cannot be later than max.")
        if value in unavailable_dates:
            raise ValueError("CCalendar value cannot be one of unavailable_dates.")
        if visible_date is not None and minimum is not None and visible_date < minimum:
            raise ValueError("CCalendar visible_date cannot be earlier than min.")
        if visible_date is not None and maximum is not None and visible_date > maximum:
            raise ValueError("CCalendar visible_date cannot be later than max.")

        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CCalendar", "name", name)
        validate_html_id("CCalendar", form_input)
        validate_html_id("CCalendar", supplied_id)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CCalendar", input_name, getattr(kwargs, input_name))
        for input_name in ("show_adjacent_days", "fixed_weeks"):
            validate_boolean("CCalendar", input_name, getattr(kwargs, input_name))
        first_day = _first_day(kwargs.first_day_of_week)
        validate_choice("CCalendar", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CCalendar", "size", kwargs.size, _SIZES)
        for input_name in ("label", "previous_label", "next_label", "unavailable_message"):
            validate_non_empty_string("CCalendar", input_name, const_value(getattr(kwargs, input_name)))

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            supplied_states = [
                state
                for state in ("required", "disabled", "readonly", "invalid")
                if getattr(kwargs, state) is not None
            ]
            if supplied_states:
                raise ValueError(
                    f"CCalendar inside CField cannot set Field-owned state: {', '.join(supplied_states)}."
                )
            if not uses_catalog_default(self, "label"):
                raise ValueError("CCalendar inside CField cannot also set label; use the CField label slot.")
            field.register_control("CCalendar")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CCalendar id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )

        public_id = supplied_id or field_control_id or f"cui-calendar-{self.id}"
        root_id = f"{public_id}-calendar"
        heading_id = f"{public_id}-heading"
        caller_attrs = _attrs(kwargs.attrs)
        authored_label = pop_html_attr(caller_attrs, "aria-label", component_name="CCalendar")
        authored_labelledby = pop_html_attr(caller_attrs, "aria-labelledby", component_name="CCalendar")
        external_described_by = pop_html_attr(caller_attrs, "aria-describedby", component_name="CCalendar")
        external_error_message = pop_html_attr(caller_attrs, "aria-errormessage", component_name="CCalendar")
        for input_name, authored in (
            ("attrs aria-label", authored_label),
            ("attrs aria-labelledby", authored_labelledby),
            ("attrs aria-describedby", external_described_by),
            ("attrs aria-errormessage", external_error_message),
        ):
            if authored is not None and not isinstance(authored, str):
                raise TypeError(f"CCalendar {input_name} must be a string.")

        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CCalendar",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CCalendar inside CForm cannot target a different native form owner.")

        required = bool(field.required) if field is not None else bool(kwargs.required)
        disabled = (
            bool(field.disabled)
            if field is not None
            else bool(form.disabled if form is not None else False) or bool(kwargs.disabled)
        )
        readonly = (
            bool(field.readonly)
            if field is not None
            else bool(kwargs.readonly if kwargs.readonly is not None else form.readonly if form is not None else False)
        )
        invalid = bool(field.invalid) if field is not None else bool(kwargs.invalid)
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            cast("str | None", external_described_by),
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            cast("str | None", external_error_message) if invalid else None,
        )

        catalog = {
            input_name: uses_catalog_default(self, input_name)
            for input_name in ("label", "previous_label", "next_label", "unavailable_message")
        }
        label = str(authored_label) if authored_label is not None else kwargs.label
        previous_label = kwargs.previous_label
        next_label = kwargs.next_label
        unavailable_message = (
            self.i18n.tr("citry-ui-calendar-unavailable")
            if catalog["unavailable_message"]
            else kwargs.unavailable_message
        )
        if self.i18n.configured:
            profile_probe = date(2000, 1, 3)
            for profile in _CALENDAR_DATE_FORMATS:
                self.i18n.format.date(profile_probe, format=profile)
        labelled_by = merge_idrefs(
            field.label_id if field is not None else None,
            cast("str | None", authored_labelledby),
        )
        if field is None and authored_label is None and labelled_by is None and not label:
            raise ValueError("Standalone CCalendar requires a non-empty accessible label.")

        context = self.i18n.context
        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": root_id,
            "heading_id": heading_id,
            "name": name,
            "form": form_owner,
            "value": value,
            "minimum": minimum,
            "maximum": maximum,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "label": None if field is not None or authored_labelledby is not None else label,
            "labelled_by": labelled_by,
            "described_by": described_by,
            "error_message": error_message,
            "previous_label": previous_label,
            "next_label": next_label,
            "catalog_label": field is None
            and authored_label is None
            and authored_labelledby is None
            and catalog["label"],
            "catalog_previous_label": catalog["previous_label"],
            "catalog_next_label": catalog["next_label"],
            "field_control": field is not None,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "attrs": merge_root_attrs(caller_attrs, kwargs.class_, kwargs.style),
        }
        client_data: dict[str, object] = {
            "value": value,
            "visibleDate": visible_date,
            "min": minimum,
            "max": maximum,
            "unavailableDates": unavailable_dates,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "firstDayOfWeek": first_day,
            "showAdjacentDays": kwargs.show_adjacent_days,
            "fixedWeeks": kwargs.fixed_weeks,
            "unavailableMessage": unavailable_message,
            "catalogUnavailableMessage": catalog["unavailable_message"],
            "variant": kwargs.variant,
            "size": kwargs.size,
            "locale": context.locale,
            "direction": context.direction,
            "timeZone": context.time_zone,
            "describedby": cast("str | None", external_described_by),
            "errormessage": cast("str | None", external_error_message),
        }
        self._cui_calendar_data = client_data
        self._cui_calendar_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_calendar_data

    template = """
      <div
        class="cui-calendar"
        c-id="root_id"
        role="group"
        c-aria-label="tr('citry-ui-calendar-label') if catalog_label else label"
        c-aria-labelledby="labelled_by"
        c-aria-describedby="described_by"
        c-aria-errormessage="error_message"
        c-aria-invalid="'true' if invalid else None"
        c-aria-disabled="'true' if disabled else None"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-empty="not value"
        c-data-variant="variant"
        c-data-size="size"
        c-$c-tr:citry-ui-calendar-label[aria-label]="True if catalog_label else None"
        c-bind="attrs"
        data-citry-ui-part="calendar"
      >
        <div class="cui-calendar__header" data-citry-ui-part="header">
          <button
            class="cui-calendar__navigation"
            type="button"
            c-aria-label="tr('citry-ui-calendar-previous-month') if catalog_previous_label else previous_label"
            c-$c-tr:citry-ui-calendar-previous-month[aria-label]="True if catalog_previous_label else None"
            data-citry-ui-part="previous"
          >
            <span class="cui-calendar__arrow" aria-hidden="true">&lsaquo;</span>
          </button>
          <h2
            class="cui-calendar__heading"
            c-id="heading_id"
            aria-live="polite"
            aria-atomic="true"
            data-citry-ui-part="heading"
          ></h2>
          <button
            class="cui-calendar__navigation"
            type="button"
            c-aria-label="tr('citry-ui-calendar-next-month') if catalog_next_label else next_label"
            c-$c-tr:citry-ui-calendar-next-month[aria-label]="True if catalog_next_label else None"
            data-citry-ui-part="next"
          >
            <span class="cui-calendar__arrow" aria-hidden="true">&rsaquo;</span>
          </button>
        </div>
        <table
          class="cui-calendar__grid"
          role="grid"
          c-aria-labelledby="heading_id"
          c-aria-readonly="'true' if readonly else None"
          data-citry-ui-part="grid"
        >
          <thead>
            <tr data-citry-ui-part="weekday-row">
              <c-for each="_ in (0, 1, 2, 3, 4, 5, 6)"><th scope="col" aria-hidden="true">&#160;</th></c-for>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
        <input
          class="cui-calendar__fallback"
          c-id="public_id"
          c-name="name"
          c-form="form"
          type="date"
          c-value="value"
          c-min="minimum"
          c-max="maximum"
          c-required="required"
          c-disabled="disabled"
          c-readonly="readonly"
          c-aria-label="tr('citry-ui-calendar-label') if catalog_label else label"
          c-$c-tr:citry-ui-calendar-label[aria-label]="True if catalog_label else None"
          c-aria-labelledby="labelled_by"
          c-aria-describedby="described_by"
          c-aria-errormessage="error_message"
          c-aria-invalid="'true' if invalid else None"
          c-data-citry-field-control="field_control"
          data-citry-ui-part="fallback-input"
        />
      </div>
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-calendar-label = Calendar
      citry-ui-calendar-previous-month = Previous month
      citry-ui-calendar-next-month = Next month
      citry-ui-calendar-unavailable = Choose an available date.
    """


__all__ = [
    "CCalendar",
    "CCalendarChangeSource",
    "CCalendarDate",
    "CCalendarSize",
    "CCalendarValueChangeDetail",
    "CCalendarVariant",
    "CCalendarVisibleDateChangeDetail",
]
