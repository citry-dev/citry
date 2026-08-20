"""Localized inline calendar-date selector."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

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
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
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
_RUNTIME_PREFIXES = ("data-citry-", "data-ccalendar", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-describedby",
        "aria-errormessage",
        "aria-invalid",
        "aria-label",
        "aria-labelledby",
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
    normalized = tuple(
        cast("str", canonical_date("CCalendar", "unavailable_dates item", item)) for item in value
    )
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
                state for state in ("required", "disabled", "readonly", "invalid") if getattr(kwargs, state) is not None
            ]
            if supplied_states:
                raise ValueError(f"CCalendar inside CField cannot set Field-owned state: {', '.join(supplied_states)}.")
            if not uses_catalog_default(self, "label"):
                raise ValueError("CCalendar inside CField cannot also set label; use the CField label slot.")
            field.register_control("CCalendar")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(f"CCalendar id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}.")

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
        label = (
            str(authored_label)
            if authored_label is not None
            else self.i18n.tr("citry-ui-calendar-label")
            if catalog["label"]
            else kwargs.label
        )
        previous_label = (
            self.i18n.tr("citry-ui-calendar-previous-month")
            if catalog["previous_label"]
            else kwargs.previous_label
        )
        next_label = self.i18n.tr("citry-ui-calendar-next-month") if catalog["next_label"] else kwargs.next_label
        unavailable_message = (
            self.i18n.tr("citry-ui-calendar-unavailable")
            if catalog["unavailable_message"]
            else kwargs.unavailable_message
        )
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
        self._cui_calendar_data = {
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
        c-aria-label="label"
        c-aria-labelledby="labelled_by"
        c-aria-describedby="described_by"
        c-aria-errormessage="error_message"
        c-aria-invalid="'true' if invalid else None"
        c-aria-disabled="'true' if disabled else None"
        c-aria-readonly="'true' if readonly else None"
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
            c-aria-label="previous_label"
            c-$c-tr:citry-ui-calendar-previous-month[aria-label]="True if catalog_previous_label else None"
            data-citry-ui-part="previous"
          >
            <span class="cui-calendar__arrow" aria-hidden="true">‹</span>
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
            c-aria-label="next_label"
            c-$c-tr:citry-ui-calendar-next-month[aria-label]="True if catalog_next_label else None"
            data-citry-ui-part="next"
          >
            <span class="cui-calendar__arrow" aria-hidden="true">›</span>
          </button>
        </div>
        <table
          class="cui-calendar__grid"
          role="grid"
          c-aria-labelledby="heading_id"
          data-citry-ui-part="grid"
        >
          <thead><tr data-citry-ui-part="weekday-row"></tr></thead>
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
          c-aria-label="label"
          c-aria-labelledby="labelled_by"
          c-aria-describedby="described_by"
          c-aria-errormessage="error_message"
          c-aria-invalid="'true' if invalid else None"
          c-data-citry-field-control="field_control"
          data-citry-ui-part="fallback-input"
        />
      </div>
    """

    js = """
      $component({
        props: {
          value: {}, visibleDate: {}, min: {}, max: {}, unavailableDates: {},
          required: {}, disabled: {}, readonly: {}, invalid: {}, firstDayOfWeek: {},
          showAdjacentDays: {}, fixedWeeks: {}, variant: {}, size: {},
          onValueChange: {}, onVisibleDateChange: {},
        },
        init: ({ els, data, props, effect, inject, i18n }) => {
          const root = els[0];
          const header = root.querySelector(':scope > [data-citry-ui-part="header"]');
          const previous = header?.querySelector(':scope > [data-citry-ui-part="previous"]');
          const heading = header?.querySelector(':scope > [data-citry-ui-part="heading"]');
          const next = header?.querySelector(':scope > [data-citry-ui-part="next"]');
          const grid = root.querySelector(':scope > [data-citry-ui-part="grid"]');
          const weekdayRow = grid?.querySelector(':scope > thead > [data-citry-ui-part="weekday-row"]');
          const body = grid?.querySelector(':scope > tbody');
          const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
          if (!(root instanceof HTMLElement) || !(header instanceof HTMLElement) || !(previous instanceof HTMLButtonElement) || !(heading instanceof HTMLElement) || !(next instanceof HTMLButtonElement) || !(grid instanceof HTMLTableElement) || !(weekdayRow instanceof HTMLTableRowElement) || !(body instanceof HTMLTableSectionElement) || !(input instanceof HTMLInputElement) || input.type !== 'date') throw new Error('[citry-ui] CCalendar settled anatomy is invalid.');

          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CCalendar form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CCalendar');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          const DAY = 86400000;
          const PROFILE = Object.freeze({
            heading: 'citry-ui-calendar-heading',
            year: 'citry-ui-calendar-year',
            weekday: 'citry-ui-calendar-weekday',
            weekdayLong: 'citry-ui-calendar-weekday-long',
            day: 'citry-ui-calendar-day',
            label: 'citry-ui-calendar-date-label',
          });
          const FALLBACK_OPTIONS = Object.freeze({
            [PROFILE.heading]: { month: 'long', year: 'numeric' },
            [PROFILE.year]: { year: 'numeric' },
            [PROFILE.weekday]: { weekday: 'short' },
            [PROFILE.weekdayLong]: { weekday: 'long' },
            [PROFILE.day]: { day: 'numeric' },
            [PROFILE.label]: { day: 'numeric', month: 'long', weekday: 'long', year: 'numeric' },
          });
          let current = input.value || data.value;
          let visible = data.visibleDate || current || null;
          let focused = current;
          let pendingFocus = null;
          let controlledValue = false;
          let controlledVisible = false;
          let configuration = null;
          let previousConstraints = { min: data.min, max: data.max, unavailableDates: [...data.unavailableDates] };
          let initialValue = data.value;
          let initialVisible = data.visibleDate;
          let nativeInvalid = false;
          let invalidGeneration = 0;
          let unavailableMessage = data.unavailableMessage;
          let unavailableBinding = null;
          let ready = false;

          const pad = value => String(value).padStart(2, '0');
          const canonicalDate = value => {
            if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
            const [year, month, day] = value.split('-').map(Number);
            if (year < 1 || year > 9999) return null;
            const result = new Date(0);
            result.setUTCHours(12, 0, 0, 0);
            result.setUTCFullYear(year, month - 1, day);
            return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
          };
          const fromIso = value => {
            const [year, month, day] = value.split('-').map(Number);
            const result = new Date(0);
            result.setUTCHours(12, 0, 0, 0);
            result.setUTCFullYear(year, month - 1, day);
            return result;
          };
          const toIso = value => `${String(value.getUTCFullYear()).padStart(4, '0')}-${pad(value.getUTCMonth() + 1)}-${pad(value.getUTCDate())}`;
          const addDays = (value, amount) => {
            const result = fromIso(value);
            result.setUTCDate(result.getUTCDate() + amount);
            const year = result.getUTCFullYear();
            return year < 1 || year > 9999 ? null : toIso(result);
          };
          const daysBetween = (left, right) => Math.round((fromIso(right) - fromIso(left)) / DAY);
          const isoWeekday = value => fromIso(value).getUTCDay() || 7;
          const fields = value => {
            const parsed = fromIso(value);
            return { year: parsed.getUTCFullYear(), month: parsed.getUTCMonth() + 1, day: parsed.getUTCDate() };
          };
          const locale = () => i18n?.context.locale ?? data.locale;
          const direction = () => i18n?.context.direction ?? data.direction;
          const timeZone = () => i18n?.context.time_zone ?? data.timeZone;
          const formatDate = (value, profile) => i18n
            ? i18n.format.date(fields(value), { format: profile })
            : new Intl.DateTimeFormat(locale(), { ...FALLBACK_OPTIONS[profile], timeZone: 'UTC' }).format(fromIso(value));
          const today = () => {
            const zone = timeZone();
            const now = new Date();
            if (!zone) return `${String(now.getFullYear()).padStart(4, '0')}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA-u-ca-gregory-nu-latn', { day: '2-digit', month: '2-digit', timeZone: zone, year: 'numeric' }).formatToParts(now).filter(part => part.type !== 'literal').map(part => [part.type, part.value]));
            return `${String(parts.year).padStart(4, '0')}-${parts.month}-${parts.day}`;
          };
          const localeFirstDay = () => {
            const candidate = new Intl.Locale(locale());
            const info = typeof candidate.getWeekInfo === 'function' ? candidate.getWeekInfo() : candidate.weekInfo;
            return Number.isInteger(info?.firstDay) ? info.firstDay : 7;
          };
          const monthBounds = anchor => {
            const key = formatDate(anchor, PROFILE.heading);
            let start = anchor;
            let end = anchor;
            let guard = 0;
            while (guard < 40) {
              const candidate = addDays(start, -1);
              if (candidate === null || formatDate(candidate, PROFILE.heading) !== key) break;
              start = candidate;
              guard += 1;
            }
            if (guard === 40) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-month start.');
            guard = 0;
            while (guard < 40) {
              const candidate = addDays(end, 1);
              if (candidate === null || formatDate(candidate, PROFILE.heading) !== key) break;
              end = candidate;
              guard += 1;
            }
            if (guard === 40) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-month end.');
            return { start, end, key, count: daysBetween(start, end) + 1 };
          };
          const sameMonth = (left, right) => formatDate(left, PROFILE.heading) === formatDate(right, PROFILE.heading);
          const calendarYear = anchor => {
            const yearKey = formatDate(anchor, PROFILE.year);
            let first = monthBounds(anchor);
            let guard = 0;
            while (guard < 15) {
              const prior = addDays(first.start, -1);
              if (prior === null || formatDate(prior, PROFILE.year) !== yearKey) break;
              first = monthBounds(prior);
              guard += 1;
            }
            if (guard === 15) throw new Error('[citry-ui] CCalendar could not find a bounded calendar-year start.');
            const months = [];
            let candidate = first;
            while (months.length < 15 && formatDate(candidate.start, PROFILE.year) === yearKey) {
              months.push(candidate);
              const after = addDays(candidate.end, 1);
              if (after === null || formatDate(after, PROFILE.year) !== yearKey) break;
              candidate = monthBounds(after);
            }
            if (months.length === 15 && addDays(months.at(-1).end, 1) !== null && formatDate(addDays(months.at(-1).end, 1), PROFILE.year) === yearKey) throw new Error('[citry-ui] CCalendar calendar year exceeds 15 months.');
            const index = Math.max(0, months.findIndex(month => sameMonth(month.start, anchor)));
            return { months, index };
          };
          const hardDisabled = value => configuration.disabled || (configuration.min !== null && value < configuration.min) || (configuration.max !== null && value > configuration.max);
          const unavailable = value => configuration.unavailable.has(value);
          const clampAllowed = value => {
            if (configuration.min !== null && value < configuration.min) return configuration.min;
            if (configuration.max !== null && value > configuration.max) return configuration.max;
            return value;
          };
          const optionalDate = (name, fallback) => {
            const requested = props[name];
            if (requested === undefined) { resolver.clear(name); return fallback; }
            if (requested === null) { resolver.clear(name); return null; }
            const normalized = canonicalDate(requested);
            if (normalized !== null) { resolver.clear(name); return normalized; }
            resolver.report(name, requested);
            return previousConstraints[name];
          };
          const resolveUnavailable = () => {
            const requested = props.unavailableDates;
            if (requested === undefined) { resolver.clear('unavailableDates'); return [...data.unavailableDates]; }
            if (!Array.isArray(requested) || requested.length > 4096) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
            const normalized = requested.map(canonicalDate);
            if (normalized.some(value => value === null) || new Set(normalized).size !== normalized.length) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
            resolver.clear('unavailableDates');
            return normalized;
          };
          const resolveConstraints = () => {
            const min = optionalDate('min', data.min);
            const max = optionalDate('max', data.max);
            const unavailableDates = resolveUnavailable();
            if (min !== null && max !== null && min > max) {
              resolver.report('min/max', { min, max });
              return previousConstraints;
            }
            resolver.clear('min/max');
            previousConstraints = { min, max, unavailableDates };
            return previousConstraints;
          };
          const resolveFirstDay = () => {
            const requested = props.firstDayOfWeek;
            if (requested === undefined) return data.firstDayOfWeek;
            if (requested === null) { resolver.clear('firstDayOfWeek'); return null; }
            if (Number.isInteger(requested) && requested >= 1 && requested <= 7) { resolver.clear('firstDayOfWeek'); return requested; }
            resolver.report('firstDayOfWeek', requested);
            return data.firstDayOfWeek;
          };
          const resolveConfiguration = () => {
            const constraints = resolveConstraints();
            return {
              min: constraints.min,
              max: constraints.max,
              unavailable: new Set(constraints.unavailableDates),
              required: field ? field.required : resolver.boolean('required', data.required),
              disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
              readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
              invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
              firstDay: resolveFirstDay(),
              showAdjacentDays: resolver.boolean('showAdjacentDays', data.showAdjacentDays),
              fixedWeeks: resolver.boolean('fixedWeeks', data.fixedWeeks),
              variant: resolver.choice('variant', data.variant, ['outline', 'plain']),
              size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
            };
          };
          const reportFieldOwned = () => {
            if (!field) return;
            ['required', 'disabled', 'readonly', 'invalid'].forEach(name => {
              if (props[name] === undefined) resolver.clear(name);
              else resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state');
            });
          };
          const syncRelationships = invalid => runtime.relationships([root, input], field, {
            describedby: data.describedby,
            errormessage: data.errormessage,
            control: input,
            required: configuration.required,
            disabled: configuration.disabled,
            readonly: configuration.readonly,
          }, invalid);
          const syncTransport = () => {
            input.value = current ?? '';
            input.min = configuration.min ?? '';
            input.max = configuration.max ?? '';
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            input.tabIndex = -1;
            input.setCustomValidity(current !== null && configuration.unavailable.has(current) ? unavailableMessage : '');
          };
          const firstFocusableIn = bounds => {
            for (let value = bounds.start, guard = 0; value !== null && guard < 40; value = addDays(value, 1), guard += 1) {
              if (value > bounds.end) break;
              if (!hardDisabled(value)) return value;
            }
            return null;
          };
          const ensureAnchors = () => {
            const todayValue = today();
            if (visible === null) visible = clampAllowed(current ?? todayValue);
            else visible = clampAllowed(visible);
            const bounds = monthBounds(visible);
            if (focused === null || hardDisabled(focused) || !sameMonth(focused, visible)) {
              focused = current !== null && !hardDisabled(current) && sameMonth(current, visible)
                ? current
                : !hardDisabled(todayValue) && sameMonth(todayValue, visible)
                  ? todayValue
                  : firstFocusableIn(bounds);
            }
          };
          const render = (focusAfter = false) => owned(() => {
            ensureAnchors();
            const bounds = monthBounds(visible);
            const firstDay = configuration.firstDay ?? localeFirstDay();
            const todayValue = today();
            const invalid = configuration.invalid || nativeInvalid || (current !== null && configuration.unavailable.has(current));
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute('data-disabled', configuration.disabled);
            root.toggleAttribute('data-readonly', configuration.readonly);
            root.toggleAttribute('data-required', configuration.required);
            root.toggleAttribute('data-invalid', invalid);
            root.toggleAttribute('data-empty', current === null);
            root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
            root.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
            root.setAttribute('aria-invalid', invalid ? 'true' : 'false');
            heading.textContent = bounds.key;

            const weekdayNodes = [];
            const monday = '2026-08-17';
            for (let index = 0; index < 7; index += 1) {
              const weekday = ((firstDay - 1 + index) % 7) + 1;
              const sample = addDays(monday, weekday - 1);
              const cell = document.createElement('th');
              cell.scope = 'col';
              cell.setAttribute('role', 'columnheader');
              cell.setAttribute('data-citry-ui-part', 'weekday');
              const abbreviation = document.createElement('abbr');
              abbreviation.textContent = formatDate(sample, PROFILE.weekday);
              abbreviation.title = formatDate(sample, PROFILE.weekdayLong);
              cell.append(abbreviation);
              weekdayNodes.push(cell);
            }
            weekdayRow.replaceChildren(...weekdayNodes);

            const shift = (isoWeekday(bounds.start) - firstDay + 7) % 7;
            const naturalCount = Math.ceil((shift + bounds.count) / 7) * 7;
            const count = configuration.fixedWeeks ? 42 : naturalCount;
            const gridStart = addDays(bounds.start, -shift);
            const rows = [];
            for (let rowIndex = 0; rowIndex < count / 7; rowIndex += 1) {
              const row = document.createElement('tr');
              row.setAttribute('role', 'row');
              row.setAttribute('data-citry-ui-part', 'week');
              for (let column = 0; column < 7; column += 1) {
                const value = addDays(gridStart, rowIndex * 7 + column);
                const cell = document.createElement('td');
                cell.setAttribute('role', 'gridcell');
                cell.setAttribute('data-citry-ui-part', 'day');
                if (value === null) { cell.setAttribute('aria-disabled', 'true'); row.append(cell); continue; }
                const outside = value < bounds.start || value > bounds.end;
                if (outside && !configuration.showAdjacentDays) {
                  cell.setAttribute('aria-disabled', 'true');
                  cell.setAttribute('data-outside', '');
                  row.append(cell);
                  continue;
                }
                const isHardDisabled = hardDisabled(value);
                const isUnavailable = unavailable(value);
                cell.dataset.date = value;
                cell.setAttribute('aria-label', formatDate(value, PROFILE.label));
                cell.setAttribute('aria-selected', value === current ? 'true' : 'false');
                cell.setAttribute('aria-disabled', isHardDisabled || isUnavailable ? 'true' : 'false');
                if (value === todayValue) cell.setAttribute('aria-current', 'date');
                cell.tabIndex = !isHardDisabled && value === focused ? 0 : -1;
                cell.textContent = formatDate(value, PROFILE.day);
                cell.toggleAttribute('data-selected', value === current);
                cell.toggleAttribute('data-today', value === todayValue);
                cell.toggleAttribute('data-outside', outside);
                cell.toggleAttribute('data-unavailable', isUnavailable);
                cell.toggleAttribute('data-focused', value === focused);
                row.append(cell);
              }
              rows.push(row);
            }
            body.replaceChildren(...rows);
            const previousAnchor = addDays(bounds.start, -1);
            const nextAnchor = addDays(bounds.end, 1);
            previous.disabled = configuration.disabled || previousAnchor === null || (configuration.min !== null && monthBounds(previousAnchor).end < configuration.min);
            next.disabled = configuration.disabled || nextAnchor === null || (configuration.max !== null && monthBounds(nextAnchor).start > configuration.max);
            syncTransport();
            syncRelationships(invalid);
            root.toggleAttribute('data-enhanced', true);
            root.setAttribute('data-citry-calendar-initialized', '');
            if (focusAfter && focused !== null) body.querySelector(`[data-date="${focused}"]`)?.focus();
          });
          const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
          const visibleDetail = (value, previousValue, source, sourceEvent) => ({ visibleDate: value, previousVisibleDate: previousValue, controlled: controlledVisible, source, sourceEvent });
          const requestVisible = (value, source, event, focusTarget = null) => {
            const target = clampAllowed(value);
            if (sameMonth(target, visible)) {
              if (focusTarget !== null) focused = focusTarget;
              render(focusTarget !== null);
              return true;
            }
            const prior = visible;
            if (controlledVisible) pendingFocus = focusTarget;
            else { visible = target; focused = focusTarget ?? target; }
            resolver.callback('onVisibleDateChange')?.(target, visibleDetail(target, prior, source, event));
            render(!controlledVisible && focusTarget !== null);
            return !controlledVisible;
          };
          const requestValue = (value, source, event) => {
            if (value === current || hardDisabled(value) || unavailable(value) || configuration.readonly) return false;
            const prior = current;
            if (!controlledValue) current = value;
            resolver.callback('onValueChange')?.(value, valueDetail(value, prior, source, event));
            if (!controlledValue) {
              syncTransport();
              input.dispatchEvent(new Event('input', { bubbles: true }));
              input.dispatchEvent(new Event('change', { bubbles: true }));
            }
            if (!sameMonth(value, visible)) requestVisible(value, source, event, value);
            else { focused = value; render(true); }
            return true;
          };
          const moveFocus = (target, source, event) => {
            if (target === null || hardDisabled(target)) return false;
            if (!sameMonth(target, visible)) return requestVisible(target, source, event, target);
            focused = target;
            render(true);
            return true;
          };
          const shiftMonth = (amount, source, event) => {
            const bounds = monthBounds(visible);
            const anchor = amount < 0 ? addDays(bounds.start, -1) : addDays(bounds.end, 1);
            if (anchor === null) return false;
            const targetBounds = monthBounds(anchor);
            const ordinal = focused !== null && focused >= bounds.start && focused <= bounds.end ? daysBetween(bounds.start, focused) : 0;
            const target = addDays(targetBounds.start, Math.min(ordinal, targetBounds.count - 1));
            if (target === null || hardDisabled(clampAllowed(target))) return requestVisible(clampAllowed(target), source, event, clampAllowed(target));
            return requestVisible(target, source, event, target);
          };
          const shiftYear = (amount, source, event) => {
            const year = calendarYear(visible);
            const adjacentAnchor = amount < 0 ? addDays(year.months[0].start, -1) : addDays(year.months.at(-1).end, 1);
            if (adjacentAnchor === null) return false;
            const targetYear = calendarYear(adjacentAnchor);
            const month = targetYear.months[Math.min(year.index, targetYear.months.length - 1)];
            const currentBounds = monthBounds(visible);
            const ordinal = focused !== null && focused >= currentBounds.start && focused <= currentBounds.end ? daysBetween(currentBounds.start, focused) : 0;
            const target = clampAllowed(addDays(month.start, Math.min(ordinal, month.count - 1)));
            return requestVisible(target, source, event, target);
          };
          const clearNativeInvalid = () => {
            if (!nativeInvalid || !input.validity.valid) return;
            nativeInvalid = false;
            field?.setNativeInvalid(false);
          };

          listeners.add(previous, 'click', event => shiftMonth(-1, 'button', event));
          listeners.add(next, 'click', event => shiftMonth(1, 'button', event));
          listeners.add(body, 'click', event => {
            const cell = event.target.closest?.('[role="gridcell"][data-date]');
            if (!(cell instanceof HTMLTableCellElement) || !body.contains(cell)) return;
            focused = cell.dataset.date;
            requestValue(cell.dataset.date, 'pointer', event);
          });
          listeners.add(body, 'focusin', event => {
            const cell = event.target.closest?.('[role="gridcell"][data-date]');
            if (cell instanceof HTMLTableCellElement && !hardDisabled(cell.dataset.date)) focused = cell.dataset.date;
          });
          listeners.add(body, 'keydown', event => {
            const cell = event.target.closest?.('[role="gridcell"][data-date]');
            if (!(cell instanceof HTMLTableCellElement)) return;
            const value = cell.dataset.date;
            let handled = true;
            if (event.key === 'ArrowLeft') moveFocus(addDays(value, direction() === 'rtl' ? 1 : -1), 'keyboard', event);
            else if (event.key === 'ArrowRight') moveFocus(addDays(value, direction() === 'rtl' ? -1 : 1), 'keyboard', event);
            else if (event.key === 'ArrowUp') moveFocus(addDays(value, -7), 'keyboard', event);
            else if (event.key === 'ArrowDown') moveFocus(addDays(value, 7), 'keyboard', event);
            else if (event.key === 'Home') moveFocus(addDays(value, -((isoWeekday(value) - (configuration.firstDay ?? localeFirstDay()) + 7) % 7)), 'keyboard', event);
            else if (event.key === 'End') moveFocus(addDays(value, 6 - ((isoWeekday(value) - (configuration.firstDay ?? localeFirstDay()) + 7) % 7)), 'keyboard', event);
            else if (event.key === 'PageUp') event.shiftKey ? shiftYear(-1, 'keyboard', event) : shiftMonth(-1, 'keyboard', event);
            else if (event.key === 'PageDown') event.shiftKey ? shiftYear(1, 'keyboard', event) : shiftMonth(1, 'keyboard', event);
            else if (event.key === 'Enter' || event.key === ' ') requestValue(value, 'keyboard', event);
            else handled = false;
            if (handled) event.preventDefault();
          });
          listeners.add(input, 'focus', () => { if (!configuration.disabled) queueMicrotask(() => render(true)); });
          listeners.add(input, 'input', () => {
            const requested = canonicalDate(input.value);
            if (requested === null || hardDisabled(requested) || unavailable(requested)) { syncTransport(); return; }
            if (controlledValue) { syncTransport(); return; }
            const prior = current;
            current = requested;
            focused = requested;
            if (!controlledVisible) visible = requested;
            resolver.callback('onValueChange')?.(requested, valueDetail(requested, prior, 'value', null));
            render();
          });
          listeners.add(input, 'change', clearNativeInvalid);
          listeners.add(input, 'invalid', event => {
            event.preventDefault();
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            render();
            const token = ++invalidGeneration;
            runtime.invalidFocus(input, root, () => token === invalidGeneration && !configuration.disabled);
            queueMicrotask(() => { if (token === invalidGeneration) render(true); });
          }, true);

          const reset = runtime.registerReset(input, root, {
            reset: event => {
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              const prior = current;
              if (!controlledValue) current = initialValue;
              if (!controlledVisible) visible = initialVisible || current || today();
              focused = current;
              if (prior !== current) resolver.callback('onValueChange')?.(current, valueDetail(current, prior, 'reset', event));
              render();
            },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(input, root, () => {
            configuration = resolveConfiguration();
            render();
          });
          if (i18n && data.catalogUnavailableMessage) unavailableBinding = i18n.bind({
            message: 'citry-ui-calendar-unavailable',
            onChange: text => { unavailableMessage = text; if (ready) render(); },
          });
          const unsubscribe = i18n?.subscribe(() => { if (ready) render(document.activeElement?.matches?.('[data-citry-ui-part="day"]') ?? false); });

          effect(() => {
            reportFieldOwned();
            configuration = resolveConfiguration();
            const requestedValue = props.value;
            if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
            else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
            else {
              const normalized = canonicalDate(requestedValue);
              if (normalized === null || hardDisabled(normalized) || unavailable(normalized)) resolver.report('value', requestedValue);
              else { controlledValue = true; current = normalized; resolver.clear('value'); }
            }
            const requestedVisible = props.visibleDate;
            if (requestedVisible === undefined) { controlledVisible = false; resolver.clear('visibleDate'); }
            else {
              const normalized = canonicalDate(requestedVisible);
              if (normalized === null) resolver.report('visibleDate', requestedVisible);
              else {
                controlledVisible = true;
                visible = clampAllowed(normalized);
                if (pendingFocus !== null && sameMonth(pendingFocus, visible)) focused = pendingFocus;
                pendingFocus = null;
                resolver.clear('visibleDate');
              }
            }
            if (!controlledVisible && current !== null && !sameMonth(current, visible ?? current)) visible = current;
            clearNativeInvalid();
            ready = true;
            render();
          });
          mutations.start(() => render());

          return () => {
            ready = false;
            invalidGeneration += 1;
            unavailableBinding?.dispose();
            unsubscribe?.();
            listeners.stop();
            mutations.stop();
            stopFieldset();
            reset();
            if (nativeInvalid) field?.setNativeInvalid(false);
            owned(() => {
              root.removeAttribute('data-enhanced');
              root.removeAttribute('data-citry-calendar-initialized');
              weekdayRow.replaceChildren();
              body.replaceChildren();
            });
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-calendar) {
          --_cui-calendar-background: var(--cui-calendar-background, Canvas);
          --_cui-calendar-foreground: var(--cui-calendar-foreground, CanvasText);
          --_cui-calendar-border-color: var(--cui-calendar-border-color, color-mix(in srgb, CanvasText 28%, transparent));
          --_cui-calendar-focus-color: var(--cui-calendar-focus-color, Highlight);
          --_cui-calendar-selected-background: var(--cui-calendar-selected-background, Highlight);
          --_cui-calendar-selected-foreground: var(--cui-calendar-selected-foreground, HighlightText);
          --_cui-calendar-today-color: var(--cui-calendar-today-color, LinkText);
          --_cui-calendar-adjacent-color: var(--cui-calendar-adjacent-color, color-mix(in srgb, CanvasText 58%, transparent));
          --_cui-calendar-unavailable-color: var(--cui-calendar-unavailable-color, GrayText);
          --_cui-calendar-radius: var(--cui-calendar-radius, .75rem);
          --_cui-calendar-padding: var(--cui-calendar-padding, .75rem);
          --_cui-calendar-gap: var(--cui-calendar-gap, .25rem);
          --_cui-calendar-cell-size: var(--cui-calendar-cell-size, 2.5rem);
          --_cui-calendar-navigation-size: var(--cui-calendar-navigation-size, 2.5rem);
          --_cui-calendar-font-size: var(--cui-calendar-font-size, 1rem);
          box-sizing: border-box;
          display: grid;
          inline-size: min(100%, calc(7 * var(--_cui-calendar-cell-size) + 2 * var(--_cui-calendar-padding)));
          gap: var(--_cui-calendar-gap);
          padding: var(--_cui-calendar-padding);
          border: 1px solid var(--_cui-calendar-border-color);
          border-radius: var(--_cui-calendar-radius);
          background: var(--_cui-calendar-background);
          color: var(--_cui-calendar-foreground);
          font: inherit;
          font-size: var(--_cui-calendar-font-size);
        }
        :where(.cui-calendar[data-variant="plain"]) { border-color: transparent; background: transparent; }
        :where(.cui-calendar[data-size="sm"]) {
          --_cui-calendar-cell-size: var(--cui-calendar-cell-size, 2.25rem);
          --_cui-calendar-navigation-size: var(--cui-calendar-navigation-size, 2.25rem);
          --_cui-calendar-font-size: var(--cui-calendar-font-size, .875rem);
        }
        :where(.cui-calendar[data-size="lg"]) {
          --_cui-calendar-cell-size: var(--cui-calendar-cell-size, 2.75rem);
          --_cui-calendar-navigation-size: var(--cui-calendar-navigation-size, 2.75rem);
          --_cui-calendar-font-size: var(--cui-calendar-font-size, 1.0625rem);
        }
        :where(.cui-calendar:not([data-enhanced]) > .cui-calendar__header),
        :where(.cui-calendar:not([data-enhanced]) > .cui-calendar__grid) { display: none; }
        :where(.cui-calendar[data-enhanced] > .cui-calendar__fallback) {
          position: absolute;
          inline-size: 1px;
          block-size: 1px;
          margin: -1px;
          padding: 0;
          overflow: hidden;
          clip-path: inset(50%);
          white-space: nowrap;
          border: 0;
        }
        :where(.cui-calendar:not([data-enhanced]) > .cui-calendar__fallback) {
          box-sizing: border-box;
          inline-size: 100%;
          min-block-size: var(--_cui-calendar-cell-size);
          padding: .5rem .75rem;
          border: 1px solid var(--_cui-calendar-border-color);
          border-radius: calc(var(--_cui-calendar-radius) * .75);
          background: var(--_cui-calendar-background);
          color: var(--_cui-calendar-foreground);
          font: inherit;
        }
        :where(.cui-calendar__header) {
          display: grid;
          grid-template-columns: var(--_cui-calendar-navigation-size) minmax(0, 1fr) var(--_cui-calendar-navigation-size);
          align-items: center;
          gap: var(--_cui-calendar-gap);
        }
        :where(.cui-calendar__navigation) {
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-calendar-navigation-size);
          block-size: var(--_cui-calendar-navigation-size);
          padding: 0;
          border: 1px solid transparent;
          border-radius: 50%;
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 1.5em;
          cursor: pointer;
        }
        :where(.cui-calendar__navigation:disabled) { color: GrayText; cursor: not-allowed; }
        :where(.cui-calendar__navigation:focus-visible) {
          outline: .1875rem solid color-mix(in srgb, var(--_cui-calendar-focus-color) 42%, transparent);
          outline-offset: .0625rem;
        }
        :where(.cui-calendar__heading) {
          min-inline-size: 0;
          margin: 0;
          overflow-wrap: anywhere;
          text-align: center;
          font: inherit;
          font-weight: 650;
        }
        :where(.cui-calendar__grid) { inline-size: 100%; border-collapse: separate; border-spacing: var(--_cui-calendar-gap); table-layout: fixed; }
        :where(.cui-calendar__grid th) {
          block-size: 1.75rem;
          color: var(--_cui-calendar-adjacent-color);
          font-size: .8em;
          font-weight: 600;
          text-align: center;
        }
        :where(.cui-calendar__grid abbr) { text-decoration: none; }
        :where(.cui-calendar__grid td[role="gridcell"]) {
          box-sizing: border-box;
          inline-size: var(--_cui-calendar-cell-size);
          block-size: var(--_cui-calendar-cell-size);
          padding: 0;
          border: 1px solid transparent;
          border-radius: 50%;
          text-align: center;
          vertical-align: middle;
          cursor: pointer;
          user-select: none;
        }
        :where(.cui-calendar__grid td[data-outside]) { color: var(--_cui-calendar-adjacent-color); }
        :where(.cui-calendar__grid td[data-unavailable]) { color: var(--_cui-calendar-unavailable-color); text-decoration: line-through; cursor: not-allowed; }
        :where(.cui-calendar__grid td[data-today]) { border-color: var(--_cui-calendar-today-color); }
        :where(.cui-calendar__grid td[data-selected]) { border-color: var(--_cui-calendar-selected-background); background: var(--_cui-calendar-selected-background); color: var(--_cui-calendar-selected-foreground); }
        :where(.cui-calendar__grid td:focus-visible) {
          outline: .1875rem solid color-mix(in srgb, var(--_cui-calendar-focus-color) 42%, transparent);
          outline-offset: .0625rem;
        }
        :where(.cui-calendar[data-disabled]) { color: GrayText; }
        :where(.cui-calendar[data-disabled] .cui-calendar__grid td) { cursor: not-allowed; }
        :where(.cui-calendar[data-invalid]) { border-color: var(--cui-calendar-invalid-border-color, light-dark(#d92d20, #f97066)); }
        :where(.cui-calendar:dir(rtl) .cui-calendar__arrow) { display: inline-block; transform: scaleX(-1); }
        @media (hover: hover) {
          :where(.cui-calendar:not([data-disabled]):not([data-readonly]) .cui-calendar__grid td[data-date]:not([data-unavailable]):not([data-selected]):hover),
          :where(.cui-calendar__navigation:not(:disabled):hover) { background: color-mix(in srgb, CanvasText 8%, transparent); }
        }
        @media (pointer: coarse) {
          :where(.cui-calendar) { --_cui-calendar-cell-size: max(var(--cui-calendar-cell-size, 2.5rem), 2.75rem); }
        }
        @media (prefers-reduced-motion: reduce) {
          :where(.cui-calendar *) { scroll-behavior: auto; transition: none; }
        }
        @media (forced-colors: active) {
          :where(.cui-calendar) { border-color: ButtonText; forced-color-adjust: auto; }
          :where(.cui-calendar__grid td[data-selected]) { border-color: Highlight; background: Highlight; color: HighlightText; }
          :where(.cui-calendar__grid td[data-today]) { outline: 1px solid LinkText; }
          :where(.cui-calendar__grid td[data-unavailable]) { color: GrayText; }
        }
        @media print {
          :where(.cui-calendar__navigation) { visibility: hidden; }
          :where(.cui-calendar) { break-inside: avoid; }
        }
      }
    """

    messages = """
      citry-ui-calendar-label = Calendar
      citry-ui-calendar-previous-month = Previous month
      citry-ui-calendar-next-month = Next month
      citry-ui-calendar-unavailable = Choose an available date.
    """


__all__ = [
    "CCalendar",
    "CCalendarDate",
    "CCalendarSize",
    "CCalendarValueChangeDetail",
    "CCalendarVariant",
    "CCalendarVisibleDateChangeDetail",
]
