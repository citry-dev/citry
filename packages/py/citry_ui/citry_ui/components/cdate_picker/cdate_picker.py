"""Localized popup calendar-date picker."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias, TypedDict, cast

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

CDatePickerDate: TypeAlias = date | str
CDatePickerVariant = Literal["outline", "filled", "plain"]
CDatePickerSize = Literal["sm", "md", "lg"]
CDatePickerValueChangeSource = Literal["calendar", "clear", "reset", "native"]


class CDatePickerValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    controlled: bool
    source: CDatePickerValueChangeSource
    sourceEvent: object | None


class CDatePickerOpenChangeDetail(TypedDict):
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
_RUNTIME_PREFIXES = ("data-citry-", "data-cdate-picker", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "aria-readonly",
        "data-citry-date-picker-initialized",
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
        raise TypeError(f"CDatePicker attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _ROOT_OWNED, "CDatePicker")
    reject_html_attr_bindings(copied, _ROOT_OWNED, "CDatePicker")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CDatePicker attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CDatePicker attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CDatePicker attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _ROOT_OWNED:
            raise ValueError(f"CDatePicker attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


def _dates(value: object) -> tuple[str, ...]:
    value = const_value(value)
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError("CDatePicker unavailable_dates must be a sequence of exact dates or canonical strings.")
    if len(value) > 4096:
        raise ValueError("CDatePicker unavailable_dates may contain at most 4096 dates.")
    normalized = tuple(cast("str", canonical_date("CDatePicker", "unavailable_dates item", item)) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("CDatePicker unavailable_dates cannot contain duplicates.")
    return tuple(sorted(normalized))


def _first_day(value: object) -> int | None:
    value = const_value(value)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"CDatePicker first_day_of_week must be an exact integer or None, got {value!r}.")
    if value < 1 or value > 7:
        raise ValueError(f"CDatePicker first_day_of_week must be from 1 through 7, got {value!r}.")
    return value


def _source_display_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{_SOURCE_MONTHS[parsed.month]} {parsed.day}, {parsed.year:04d}"


class CDatePicker(LibraryComponent):
    class I18n:
        messages_locale = "en-US"
        client_messages = (
            "citry-ui-date-picker-placeholder",
            "citry-ui-date-picker-change",
            "citry-ui-date-picker-unavailable",
        )

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CDatePickerDate | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CDatePickerDate | None = None
        max: CDatePickerDate | None = None
        unavailable_dates: Sequence[CDatePickerDate] = ()
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
        placeholder: str = "Choose a date"
        picker_label: str = "Choose date"
        change_label: str = "Change date, {date}"
        clear_label: str = "Clear date"
        unavailable_message: str = "Choose an available date."
        variant: CDatePickerVariant = "outline"
        size: CDatePickerSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_date_picker_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = canonical_date("CDatePicker", "value", kwargs.value, optional=True)
        minimum = canonical_date("CDatePicker", "min", kwargs.min, optional=True)
        maximum = canonical_date("CDatePicker", "max", kwargs.max, optional=True)
        unavailable_dates = _dates(kwargs.unavailable_dates)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"CDatePicker min {minimum!r} cannot be later than max {maximum!r}.")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("CDatePicker value cannot be earlier than min.")
        if value is not None and maximum is not None and value > maximum:
            raise ValueError("CDatePicker value cannot be later than max.")
        if value in unavailable_dates:
            raise ValueError("CDatePicker value cannot be one of unavailable_dates.")

        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CDatePicker", "name", name)
        validate_html_id("CDatePicker", form_input)
        validate_html_id("CDatePicker", supplied_id)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CDatePicker", input_name, getattr(kwargs, input_name))
        for input_name in ("clearable", "dismissible", "match_width", "show_adjacent_days", "fixed_weeks"):
            validate_boolean("CDatePicker", input_name, getattr(kwargs, input_name))
        first_day = _first_day(kwargs.first_day_of_week)
        validate_choice("CDatePicker", "placement", kwargs.placement, _PLACEMENTS)
        validate_choice("CDatePicker", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CDatePicker", "size", kwargs.size, _SIZES)
        for input_name in (
            "placeholder",
            "picker_label",
            "change_label",
            "clear_label",
            "unavailable_message",
        ):
            validate_non_empty_string("CDatePicker", input_name, const_value(getattr(kwargs, input_name)))
        if "{date}" not in kwargs.change_label:
            raise ValueError("CDatePicker change_label must contain the {date} placeholder.")

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
                    f"CDatePicker inside CField cannot set Field-owned state: {', '.join(supplied_states)}."
                )
            field.register_control("CDatePicker")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CDatePicker id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )

        public_id = supplied_id or field_control_id or f"cui-date-picker-{self.id}"
        root_id = f"{public_id}-root"
        native_id = f"{public_id}-native"
        visible_id = f"{public_id}-visible"
        popover_id = f"{public_id}-popover"
        calendar_id = f"{public_id}-calendar"
        caller_attrs = _attrs(kwargs.attrs)
        external_described_by = pop_html_attr(caller_attrs, "aria-describedby", component_name="CDatePicker")
        external_error_message = pop_html_attr(caller_attrs, "aria-errormessage", component_name="CDatePicker")
        for input_name, authored in (
            ("attrs aria-describedby", external_described_by),
            ("attrs aria-errormessage", external_error_message),
        ):
            if authored is not None and not isinstance(authored, str):
                raise TypeError(f"CDatePicker {input_name} must be a string.")

        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CDatePicker",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CDatePicker inside CForm cannot target a different native form owner.")

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
            for input_name in (
                "placeholder",
                "picker_label",
                "change_label",
                "clear_label",
                "unavailable_message",
            )
        }
        placeholder = (
            self.i18n.tr("citry-ui-date-picker-placeholder") if catalog["placeholder"] else kwargs.placeholder
        )
        picker_label = self.i18n.tr("citry-ui-date-picker-label") if catalog["picker_label"] else kwargs.picker_label
        clear_label = self.i18n.tr("citry-ui-date-picker-clear") if catalog["clear_label"] else kwargs.clear_label
        unavailable_message = (
            self.i18n.tr("citry-ui-date-picker-unavailable")
            if catalog["unavailable_message"]
            else kwargs.unavailable_message
        )
        display_value = None
        if value is not None:
            display_value = (
                self.i18n.format.date(date.fromisoformat(value), format=_DISPLAY_PROFILE)
                if self.i18n.configured
                else _source_display_date(value)
            )
        if value is not None and catalog["change_label"]:
            trigger_label = self.i18n.tr("citry-ui-date-picker-change", date=display_value)
        elif value is not None:
            trigger_label = kwargs.change_label.replace("{date}", display_value or value)
        else:
            trigger_label = picker_label
        if self.i18n.configured:
            self.i18n.format.date(date(2000, 1, 3), format=_DISPLAY_PROFILE)

        # The nested Calendar is an implementation detail, not a second Field or
        # Form control. Preserve the inherited owners for this component, then
        # stop them before rendering composed descendants.
        self.unprovide(FIELD_CONTEXT_KEY)
        self.unprovide(FORM_CONTEXT_KEY)

        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": root_id,
            "native_id": native_id,
            "visible_id": visible_id,
            "popover_id": popover_id,
            "calendar_id": calendar_id,
            "name": name,
            "form": form_owner,
            "value": value,
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
            "picker_label": picker_label,
            "trigger_label": trigger_label,
            "clear_label": clear_label,
            "catalog_picker_label": catalog["picker_label"],
            "catalog_clear_label": catalog["clear_label"],
            "display_value": display_value,
            "described_by": described_by,
            "error_message": error_message,
            "field_control": field is not None,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "attrs": merge_root_attrs(caller_attrs, kwargs.class_, kwargs.style),
        }
        context = self.i18n.context
        client_data: dict[str, object] = {
            "publicId": public_id,
            "nativeId": native_id,
            "visibleId": visible_id,
            "value": value,
            "min": minimum,
            "max": maximum,
            "unavailableDates": unavailable_dates,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "clearable": kwargs.clearable,
            "dismissible": kwargs.dismissible,
            "placement": kwargs.placement,
            "matchWidth": kwargs.match_width,
            "firstDayOfWeek": first_day,
            "showAdjacentDays": kwargs.show_adjacent_days,
            "fixedWeeks": kwargs.fixed_weeks,
            "placeholder": placeholder,
            "pickerLabel": picker_label,
            "changeLabel": kwargs.change_label,
            "clearLabel": clear_label,
            "unavailableMessage": unavailable_message,
            "catalog": catalog,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "locale": context.locale,
            "describedby": cast("str | None", external_described_by),
            "errormessage": cast("str | None", external_error_message),
        }
        self._cui_date_picker_data = client_data
        self._cui_date_picker_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_date_picker_data

    template = """
      <div
        class="cui-date-picker"
        c-id="root_id"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-empty="not value"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="date-picker"
      >
        <input
          class="cui-date-picker__fallback"
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
          c-aria-describedby="described_by"
          c-aria-errormessage="error_message"
          c-aria-invalid="'true' if invalid else None"
          c-data-citry-field-control="field_control"
          data-citry-ui-part="fallback-input"
        />
        <div class="cui-date-picker__enhanced" data-citry-ui-part="enhanced-control">
          <c-CPopover
            c-id="popover_id"
            c-dismissible="dismissible"
            c-placement="placement"
            c-match_width="match_width"
            class_="cui-date-picker__popover"
            $c-props="{open:datePickerOpen,dismissible:datePickerDismissible,placement:datePickerPlacement,matchWidth:datePickerMatchWidth,onOpenChange:datePickerOnPopoverOpenChange}"
          >
            <c-fill name="activator" data="{ activator_attrs }">
              <button
                class="cui-date-picker__control"
                c-id="visible_id"
                type="button"
                c-disabled="disabled"
                c-aria-label="trigger_label"
                c-bind="activator_attrs"
                data-citry-date-picker-trigger
                data-citry-ui-part="control"
              >
                <span class="cui-date-picker__value" data-citry-ui-part="value">{{ display_value if display_value else placeholder }}</span>
                <c-CIcon name="calendar" class_="cui-date-picker__icon" />
              </button>
            </c-fill>
            <c-fill name="title">
              <span
                c-$c-tr:citry-ui-date-picker-label="True if catalog_picker_label else None"
              >{{ tr('citry-ui-date-picker-label') if catalog_picker_label else picker_label }}</span>
            </c-fill>
            <c-fill name="default">
              <c-CCalendar
                c-id="calendar_id"
                c-value="value"
                c-min="minimum"
                c-max="maximum"
                c-unavailable_dates="unavailable_dates"
                c-disabled="disabled"
                c-readonly="readonly"
                c-first_day_of_week="first_day"
                c-show_adjacent_days="show_adjacent_days"
                c-fixed_weeks="fixed_weeks"
                variant="plain"
                $c-props="{value:datePickerCalendarValue,visibleDate:datePickerVisibleDate,min:datePickerMin,max:datePickerMax,unavailableDates:datePickerUnavailableDates,disabled:datePickerDisabled,readonly:datePickerReadonly,firstDayOfWeek:datePickerFirstDayOfWeek,showAdjacentDays:datePickerShowAdjacentDays,fixedWeeks:datePickerFixedWeeks,onValueChange:datePickerOnCalendarValueChange,onVisibleDateChange:datePickerOnVisibleDateChange}"
              />
            </c-fill>
          </c-CPopover>
          <button
            class="cui-date-picker__clear"
            type="button"
            c-aria-label="tr('citry-ui-date-picker-clear') if catalog_clear_label else clear_label"
            c-$c-tr:citry-ui-date-picker-clear[aria-label]="True if catalog_clear_label else None"
            c-hidden="not clearable or required or not value"
            c-disabled="disabled or readonly"
            data-citry-ui-part="clear"
          ><span aria-hidden="true">&times;</span></button>
        </div>
      </div>
    """

    js = """
      $component({
        props: {
          value: {}, open: {}, min: {}, max: {}, unavailableDates: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
          clearable: {}, dismissible: {}, placement: {}, matchWidth: {}, firstDayOfWeek: {}, showAdjacentDays: {}, fixedWeeks: {},
          variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
        },
        init: ({ els, data, props, scope, effect, inject, unprovide, i18n }) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
          const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
          const trigger = root.querySelector('[data-citry-date-picker-trigger]');
          const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
          const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
          if (!(root instanceof HTMLElement) || !(input instanceof HTMLInputElement) || input.type !== 'date' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement)) throw new Error('[citry-ui] CDatePicker settled anatomy is invalid.');

          const fieldKey = Symbol.for('citry-ui:field');
          const formKey = Symbol.for('citry-ui:form');
          const field = inject(fieldKey, null);
          const form = inject(formKey, null);
          unprovide(fieldKey);
          unprovide(formKey);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CDatePicker form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CDatePicker');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          let current = input.value || data.value || null;
          let internalOpen = false;
          let controlledValue = false;
          let controlledOpen = false;
          let visibleDate = current || undefined;
          let initialValue = data.value || null;
          let nativeInvalid = false;
          let unavailableMessage = data.unavailableMessage;
          let invalidGeneration = 0;
          let dispatching = false;
          let ready = false;
          let configuration = null;
          let previousConstraints = { min: data.min, max: data.max, unavailableDates: [...data.unavailableDates] };
          const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
          const DISPLAY_PROFILE = 'citry-ui-date-picker-display';

          const canonicalDate = value => {
            if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
            const [year, month, day] = value.split('-').map(Number);
            if (year < 1 || year > 9999) return null;
            const result = new Date(0);
            result.setUTCHours(12, 0, 0, 0);
            result.setUTCFullYear(year, month - 1, day);
            return result.getUTCFullYear() === year && result.getUTCMonth() === month - 1 && result.getUTCDate() === day ? value : null;
          };
          const fields = value => { const [year, month, day] = value.split('-').map(Number); return { year, month, day }; };
          const fromIso = value => { const [year, month, day] = value.split('-').map(Number); const result = new Date(0); result.setUTCHours(12,0,0,0); result.setUTCFullYear(year,month-1,day); return result; };
          const formatDate = value => i18n
            ? i18n.format.date(fields(value), { format: DISPLAY_PROFILE })
            : new Intl.DateTimeFormat(data.locale, { day:'numeric', month:'long', year:'numeric', timeZone:'UTC' }).format(fromIso(value));
          const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
          const placeholderText = () => translated('placeholder', 'citry-ui-date-picker-placeholder', data.placeholder);
          const pickerLabel = () => translated('picker_label', 'citry-ui-date-picker-label', data.pickerLabel);
          const triggerLabel = value => {
            if (!value) return pickerLabel();
            const date = formatDate(value);
            return data.catalog.change_label
              ? i18n?.tr('citry-ui-date-picker-change', { date }) ?? data.changeLabel.replaceAll('{date}', date)
              : data.changeLabel.replaceAll('{date}', date);
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
          const unavailableDates = () => {
            const requested = props.unavailableDates;
            if (requested === undefined) { resolver.clear('unavailableDates'); return [...data.unavailableDates]; }
            if (!Array.isArray(requested) || requested.length > 4096) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
            const normalized = requested.map(canonicalDate);
            if (normalized.some(value => value === null) || new Set(normalized).size !== normalized.length) { resolver.report('unavailableDates', requested); return previousConstraints.unavailableDates; }
            resolver.clear('unavailableDates');
            return normalized.sort();
          };
          const resolveConstraints = () => {
            const minimum = optionalDate('min', data.min);
            const maximum = optionalDate('max', data.max);
            const unavailable = unavailableDates();
            if (minimum !== null && maximum !== null && minimum > maximum) { resolver.report('min/max', {min:minimum,max:maximum}); return previousConstraints; }
            resolver.clear('min/max');
            previousConstraints = { min: minimum, max: maximum, unavailableDates: unavailable };
            return previousConstraints;
          };
          const firstDay = () => {
            const value = props.firstDayOfWeek;
            if (value === undefined) { resolver.clear('firstDayOfWeek'); return data.firstDayOfWeek; }
            if (value === null || (Number.isInteger(value) && value >= 1 && value <= 7)) { resolver.clear('firstDayOfWeek'); return value; }
            resolver.report('firstDayOfWeek', value); return data.firstDayOfWeek;
          };
          const resolveConfiguration = () => ({
            constraints: resolveConstraints(),
            required: field ? field.required : resolver.boolean('required', data.required),
            disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
            readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
            clearable: resolver.boolean('clearable', data.clearable),
            dismissible: resolver.boolean('dismissible', data.dismissible),
            placement: resolver.choice('placement', data.placement, allowedPlacements),
            matchWidth: resolver.boolean('matchWidth', data.matchWidth),
            firstDayOfWeek: firstDay(),
            showAdjacentDays: resolver.boolean('showAdjacentDays', data.showAdjacentDays),
            fixedWeeks: resolver.boolean('fixedWeeks', data.fixedWeeks),
            variant: resolver.choice('variant', data.variant, ['outline','filled','plain']),
            size: resolver.choice('size', data.size, ['sm','md','lg']),
          });
          const reportFieldOwned = () => {
            if (!field) return;
            ['required','disabled','readonly','invalid'].forEach(name => props[name] === undefined ? resolver.clear(name) : resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state'));
          };
          const emitNative = () => {
            dispatching = true;
            try { input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); }
            finally { dispatching = false; }
          };
          const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
          const openDetail = (reason, source, forced = false) => ({ reason, controlled: controlledOpen, forced, source });
          const focusCalendar = () => requestAnimationFrame(() => requestAnimationFrame(() => {
            if (!root.isConnected || !scope.datePickerOpen) return;
            const selected = current ? root.querySelector(`[data-citry-ui-part="day"][data-date="${CSS.escape(current)}"]`) : null;
            const target = selected ?? root.querySelector('[data-citry-ui-part="day"][tabindex="0"]');
            if (target instanceof HTMLElement) target.focus({ preventScroll: true });
          }));
          const requestOpen = (next, reason, source = null, forced = false) => {
            if (next === scope.datePickerOpen && !forced) return;
            if (!controlledOpen || forced) { internalOpen = next; scope.datePickerOpen = next; }
            resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
          };
          const requestValue = (next, source, event) => {
            if (configuration.disabled || configuration.readonly || next === current) return false;
            if (next !== null && (canonicalDate(next) === null || (configuration.constraints.min !== null && next < configuration.constraints.min) || (configuration.constraints.max !== null && next > configuration.constraints.max) || configuration.constraints.unavailableDates.includes(next))) return false;
            const previous = current;
            if (!controlledValue) { current = next; scope.datePickerCalendarValue = next; visibleDate = next || visibleDate; scope.datePickerVisibleDate = visibleDate; }
            resolver.callback('onValueChange')?.(next, valueDetail(next, previous, source, event));
            if (!controlledValue) { render(); emitNative(); }
            requestOpen(false, source === 'calendar' ? 'selection' : 'clear', event);
            return true;
          };
          const render = () => owned(() => {
            const constraints = configuration.constraints;
            input.value = current || '';
            runtime.attr(input, 'min', constraints.min);
            runtime.attr(input, 'max', constraints.max);
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            const unavailable = current !== null && constraints.unavailableDates.includes(current);
            input.setCustomValidity(unavailable ? unavailableMessage : '');
            const invalid = configuration.invalid || nativeInvalid || unavailable;
            trigger.disabled = configuration.disabled;
            trigger.setAttribute('aria-label', triggerLabel(current));
            valueText.textContent = current ? formatDate(current) : placeholderText();
            clear.hidden = !configuration.clearable || configuration.required || current === null;
            clear.disabled = configuration.disabled || configuration.readonly;
            runtime.states(root, { empty: current === null, open: scope.datePickerOpen, required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly, invalid });
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            runtime.relationships([trigger], field, { describedby: data.describedby, errormessage: data.errormessage }, invalid);
            scope.datePickerCalendarValue = current;
            scope.datePickerMin = constraints.min;
            scope.datePickerMax = constraints.max;
            scope.datePickerUnavailableDates = constraints.unavailableDates;
            scope.datePickerDisabled = configuration.disabled;
            scope.datePickerReadonly = configuration.readonly;
            scope.datePickerDismissible = configuration.dismissible;
            scope.datePickerPlacement = configuration.placement;
            scope.datePickerMatchWidth = configuration.matchWidth;
            scope.datePickerFirstDayOfWeek = configuration.firstDayOfWeek;
            scope.datePickerShowAdjacentDays = configuration.showAdjacentDays;
            scope.datePickerFixedWeeks = configuration.fixedWeeks;
          });

          scope.datePickerOpen = internalOpen;
          scope.datePickerCalendarValue = current;
          scope.datePickerVisibleDate = visibleDate;
          scope.datePickerOnPopoverOpenChange = (next, detail) => {
            if (detail?.forced) { internalOpen = false; scope.datePickerOpen = false; resolver.callback('onOpenChange')?.(false, { ...detail, controlled: controlledOpen }); if (ready) render(); return; }
            requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
            if (next) focusCalendar();
            if (ready) render();
          };
          scope.datePickerOnCalendarValueChange = (next, detail) => requestValue(next, 'calendar', detail?.sourceEvent ?? null);
          scope.datePickerOnVisibleDateChange = next => { visibleDate = next; scope.datePickerVisibleDate = next; };

          listeners.add(clear, 'click', event => requestValue(null, 'clear', event));
          listeners.add(input, 'input', event => {
            if (dispatching) return;
            const next = input.value || null;
            if (controlledValue) { queueMicrotask(() => render()); return; }
            const previous = current;
            current = next;
            visibleDate = next || visibleDate;
            resolver.callback('onValueChange')?.(next, valueDetail(next, previous, 'native', event));
            render();
          });
          listeners.add(input, 'change', () => {
            if (nativeInvalid && input.validity.valid) { nativeInvalid = false; field?.setNativeInvalid(false); render(); }
          });
          listeners.add(input, 'invalid', event => {
            event.preventDefault();
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            requestOpen(true, 'trigger', event);
            render();
            const token = ++invalidGeneration;
            runtime.invalidFocus(root, trigger, () => token === invalidGeneration && !configuration.disabled);
            focusCalendar();
          }, true);
          const reset = runtime.registerReset(root, input, {
            reset: event => {
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              const previous = current;
              if (!controlledValue) { current = initialValue; visibleDate = current || undefined; }
              else resolver.callback('onValueChange')?.(initialValue, valueDetail(initialValue, previous, 'reset', event));
              requestOpen(false, 'reset', event);
              render();
            },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });
          const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message: 'citry-ui-date-picker-unavailable', onChange: text => { unavailableMessage = text; if (ready) render(); } }) : null;
          const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

          effect(() => {
            reportFieldOwned();
            configuration = resolveConfiguration();
            const requestedValue = props.value;
            if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
            else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
            else {
              const normalized = canonicalDate(requestedValue);
              if (normalized === null || (configuration.constraints.min !== null && normalized < configuration.constraints.min) || (configuration.constraints.max !== null && normalized > configuration.constraints.max) || configuration.constraints.unavailableDates.includes(normalized)) resolver.report('value', requestedValue);
              else { controlledValue = true; current = normalized; resolver.clear('value'); }
            }
            const requestedOpen = props.open;
            if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.datePickerOpen; controlledOpen = false; resolver.clear('open'); }
            else if (typeof requestedOpen === 'boolean') { const opening = !scope.datePickerOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.datePickerOpen = requestedOpen; resolver.clear('open'); if (opening) focusCalendar(); }
            else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.datePickerOpen; controlledOpen = false; }
            if (current) { visibleDate = current; scope.datePickerVisibleDate = current; }
            ready = true;
            render();
          });
          mutations.start(() => render());
          owned(() => {
            runtime.enhanceNative(input, trigger, { publicId: data.publicId, nativeId: data.nativeId, visibleId: data.visibleId, className: 'cui-form-control__native--enhanced' });
            root.toggleAttribute('data-enhanced', true);
            root.setAttribute('data-citry-date-picker-initialized', '');
          });
          render();

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
              runtime.enhanceNative(input, trigger, { publicId: data.publicId, nativeId: data.nativeId, visibleId: data.visibleId, className: 'cui-form-control__native--enhanced' }, false);
              root.removeAttribute('data-enhanced');
              root.removeAttribute('data-citry-date-picker-initialized');
            });
          };
        },
      });
    """

    css_file = "runtime.min.css"

    messages = """
      citry-ui-date-picker-placeholder = Choose a date
      citry-ui-date-picker-label = Choose date
      # @param {str} $date - Locale-formatted selected date.
      citry-ui-date-picker-change = Change date, { $date }
      citry-ui-date-picker-clear = Clear date
      citry-ui-date-picker-unavailable = Choose an available date.
    """


__all__ = [
    "CDatePicker",
    "CDatePickerDate",
    "CDatePickerOpenChangeDetail",
    "CDatePickerSize",
    "CDatePickerValueChangeDetail",
    "CDatePickerValueChangeSource",
    "CDatePickerVariant",
]
