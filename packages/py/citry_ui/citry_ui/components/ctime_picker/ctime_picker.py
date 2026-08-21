"""Localized finite-option wall-clock time picker."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import time
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
from citry_ui.components._form_control_runtime import (
    FORM_CONTROL_RUNTIME_DEPENDENCY,
    FORM_CONTROL_STYLE_DEPENDENCY,
)
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._time import canonical_time, time_seconds
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

CTimePickerTime: TypeAlias = time | str
CTimePickerVariant = Literal["outline", "filled", "plain"]
CTimePickerSize = Literal["sm", "md", "lg"]
CTimePickerValueChangeSource = Literal["option", "clear", "reset", "native"]


class CTimePickerValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    controlled: bool
    source: CTimePickerValueChangeSource
    sourceEvent: object | None


class CTimePickerOpenChangeDetail(TypedDict):
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


@dataclass(frozen=True, slots=True)
class _TimeOption:
    value: str
    label: str


_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_PLACEMENTS = ("top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end")
_DISPLAY_PROFILE = "citry-ui-time-picker-display"
_SECONDS_PROFILE = "citry-ui-time-picker-display-seconds"
_MAX_OPTIONS = 288
_RUNTIME_PREFIXES = ("data-citry-", "data-ctime-picker", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "aria-readonly",
        "data-citry-time-picker-initialized",
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
        raise TypeError(f"CTimePicker attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _ROOT_OWNED, "CTimePicker")
    reject_html_attr_bindings(copied, _ROOT_OWNED, "CTimePicker")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CTimePicker attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CTimePicker attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CTimePicker attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _ROOT_OWNED:
            raise ValueError(f"CTimePicker attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


def _step(value: object) -> int:
    value = const_value(value)
    if type(value) is not int:
        raise TypeError(f"CTimePicker step must be an exact integer, got {value!r}.")
    if value < 300:
        raise ValueError(f"CTimePicker step must be at least 300 seconds, got {value!r}.")
    return cast("int", value)


def _within(value: int, minimum: int | None, maximum: int | None) -> bool:
    if minimum is None and maximum is None:
        return True
    if minimum is None:
        return value <= cast("int", maximum)
    if maximum is None:
        return value >= minimum
    if minimum <= maximum:
        return minimum <= value <= maximum
    return value >= minimum or value <= maximum


def _canonical_seconds(value: int, *, seconds: bool) -> str:
    hour, remainder = divmod(value, 3600)
    minute, second = divmod(remainder, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}" if seconds else f"{hour:02d}:{minute:02d}"


def _option_values(
    values: Sequence[CTimePickerTime] | None,
    *,
    minimum: str | None,
    maximum: str | None,
    step: int,
) -> tuple[str, ...]:
    minimum_seconds = time_seconds(minimum) if minimum is not None else None
    maximum_seconds = time_seconds(maximum) if maximum is not None else None
    if values is not None:
        values = const_value(values)
        if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
            raise TypeError("CTimePicker options must be a sequence of times or canonical strings.")
        if not values:
            raise ValueError("CTimePicker options must contain at least one time.")
        if len(values) > _MAX_OPTIONS:
            raise ValueError(f"CTimePicker options may contain at most {_MAX_OPTIONS} times.")
        normalized = tuple(
            cast("str", canonical_time("CTimePicker", "options item", item, optional=False)) for item in values
        )
        if len(set(normalized)) != len(normalized):
            raise ValueError("CTimePicker options cannot contain duplicates.")
        if any(not _within(time_seconds(item), minimum_seconds, maximum_seconds) for item in normalized):
            raise ValueError("CTimePicker options must all be inside the min/max interval.")
        return normalized

    start = minimum_seconds if minimum_seconds is not None else 0
    end = maximum_seconds if maximum_seconds is not None else 86_399
    span = (end - start) % 86_400 if start > end else end - start
    count = span // step + 1
    if count < 1 or count > _MAX_OPTIONS:
        raise ValueError(
            f"CTimePicker min/max/step produce {count} options; choose a larger step or explicit options "
            f"so the count is from 1 through {_MAX_OPTIONS}."
        )
    seconds = step % 60 != 0 or any(item is not None and len(item.split(":")) == 3 for item in (minimum, maximum))
    return tuple(_canonical_seconds((start + index * step) % 86_400, seconds=seconds) for index in range(count))


def _source_display_time(value: str, *, seconds: bool) -> str:
    hour, minute, *rest = [int(part) for part in value.split(":")]
    second = rest[0] if rest else 0
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    suffix = f":{second:02d}" if seconds else ""
    return f"{display_hour}:{minute:02d}{suffix} {period}"


class CTimePicker(LibraryComponent):
    class I18n:
        messages_locale = "en-US"
        client_messages = (
            "citry-ui-time-picker-placeholder",
            "citry-ui-time-picker-change",
            "citry-ui-time-picker-unavailable",
        )

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CTimePickerTime | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CTimePickerTime | None = None
        max: CTimePickerTime | None = None
        step: int = 900
        options: Sequence[CTimePickerTime] | None = None
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        clearable: bool = True
        dismissible: bool = True
        placement: CPopoverPlacement = "bottom-start"
        match_width: bool = True
        placeholder: str = "Choose a time"
        picker_label: str = "Choose time"
        change_label: str = "Change time, {time}"
        clear_label: str = "Clear time"
        unavailable_message: str = "Choose an available time."
        variant: CTimePickerVariant = "outline"
        size: CTimePickerSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_time_picker_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = canonical_time("CTimePicker", "value", kwargs.value, optional=True)
        minimum = canonical_time("CTimePicker", "min", kwargs.min, optional=True)
        maximum = canonical_time("CTimePicker", "max", kwargs.max, optional=True)
        step = _step(kwargs.step)
        option_values = _option_values(kwargs.options, minimum=minimum, maximum=maximum, step=step)
        if value is not None and value not in option_values:
            raise ValueError("CTimePicker value must equal one of the generated or explicit options.")
        show_seconds = any(len(item.split(":")) == 3 for item in option_values)

        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CTimePicker", "name", name)
        validate_html_id("CTimePicker", form_input)
        validate_html_id("CTimePicker", supplied_id)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CTimePicker", input_name, getattr(kwargs, input_name))
        for input_name in ("clearable", "dismissible", "match_width"):
            validate_boolean("CTimePicker", input_name, getattr(kwargs, input_name))
        validate_choice("CTimePicker", "placement", kwargs.placement, _PLACEMENTS)
        validate_choice("CTimePicker", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CTimePicker", "size", kwargs.size, _SIZES)
        for input_name in ("placeholder", "picker_label", "change_label", "clear_label", "unavailable_message"):
            validate_non_empty_string("CTimePicker", input_name, const_value(getattr(kwargs, input_name)))
        if "{time}" not in kwargs.change_label:
            raise ValueError("CTimePicker change_label must contain the {time} placeholder.")

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
                    f"CTimePicker inside CField cannot set Field-owned state: {', '.join(supplied_states)}."
                )
            field.register_control("CTimePicker")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CTimePicker id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )

        public_id = supplied_id or field_control_id or f"cui-time-picker-{self.id}"
        root_id = f"{public_id}-root"
        native_id = f"{public_id}-native"
        visible_id = f"{public_id}-visible"
        popover_id = f"{public_id}-popover"
        caller_attrs = _attrs(kwargs.attrs)
        external_described_by = pop_html_attr(caller_attrs, "aria-describedby", component_name="CTimePicker")
        external_error_message = pop_html_attr(caller_attrs, "aria-errormessage", component_name="CTimePicker")
        for input_name, authored in (
            ("attrs aria-describedby", external_described_by),
            ("attrs aria-errormessage", external_error_message),
        ):
            if authored is not None and not isinstance(authored, str):
                raise TypeError(f"CTimePicker {input_name} must be a string.")
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CTimePicker",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CTimePicker inside CForm cannot target a different native form owner.")

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
            for input_name in ("placeholder", "picker_label", "change_label", "clear_label", "unavailable_message")
        }
        placeholder = (
            self.i18n.tr("citry-ui-time-picker-placeholder") if catalog["placeholder"] else kwargs.placeholder
        )
        picker_label = self.i18n.tr("citry-ui-time-picker-label") if catalog["picker_label"] else kwargs.picker_label
        clear_label = self.i18n.tr("citry-ui-time-picker-clear") if catalog["clear_label"] else kwargs.clear_label
        unavailable_message = (
            self.i18n.tr("citry-ui-time-picker-unavailable")
            if catalog["unavailable_message"]
            else kwargs.unavailable_message
        )
        profile = _SECONDS_PROFILE if show_seconds else _DISPLAY_PROFILE
        if self.i18n.configured:
            self.i18n.format.time(time(13, 5, 9), format=profile)

        def display(item: str) -> str:
            parsed = time.fromisoformat(item)
            return (
                self.i18n.format.time(parsed, format=profile)
                if self.i18n.configured
                else _source_display_time(item, seconds=show_seconds)
            )

        display_value = display(value) if value is not None else None
        if value is not None and catalog["change_label"]:
            trigger_label = self.i18n.tr("citry-ui-time-picker-change", time=display_value)
        elif value is not None:
            trigger_label = kwargs.change_label.replace("{time}", display_value or value)
        else:
            trigger_label = picker_label
        options = tuple(_TimeOption(item, display(item)) for item in option_values)

        # The nested Listbox is selection UI, not a second Field/Form control.
        self.unprovide(FIELD_CONTEXT_KEY)
        self.unprovide(FORM_CONTEXT_KEY)

        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": root_id,
            "native_id": native_id,
            "visible_id": visible_id,
            "popover_id": popover_id,
            "name": name,
            "form": form_owner,
            "value": value,
            "minimum": minimum,
            "maximum": maximum,
            "native_step": "any" if kwargs.options is not None else step,
            "options": options,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "clearable": kwargs.clearable,
            "dismissible": kwargs.dismissible,
            "placement": kwargs.placement,
            "match_width": kwargs.match_width,
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
            "step": "any" if kwargs.options is not None else step,
            "optionValues": option_values,
            "showSeconds": show_seconds,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "clearable": kwargs.clearable,
            "dismissible": kwargs.dismissible,
            "placement": kwargs.placement,
            "matchWidth": kwargs.match_width,
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
        self._cui_time_picker_data = client_data
        self._cui_time_picker_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_time_picker_data

    template = """
      <div
        class="cui-time-picker"
        c-id="root_id"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-empty="not value"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="time-picker"
      >
        <input
          class="cui-time-picker__fallback"
          c-id="public_id"
          c-name="name"
          c-form="form"
          type="time"
          c-value="value"
          c-min="minimum"
          c-max="maximum"
          c-step="native_step"
          c-required="required"
          c-disabled="disabled"
          c-readonly="readonly"
          c-aria-describedby="described_by"
          c-aria-errormessage="error_message"
          c-aria-invalid="'true' if invalid else None"
          c-data-citry-field-control="field_control"
          data-citry-ui-part="fallback-input"
        />
        <div class="cui-time-picker__enhanced" data-citry-ui-part="enhanced-control">
          <c-CPopover
            c-id="popover_id"
            c-dismissible="dismissible"
            c-placement="placement"
            c-match_width="match_width"
            class_="cui-time-picker__popover"
            $c-props="{open:timePickerOpen,dismissible:timePickerDismissible,placement:timePickerPlacement,matchWidth:timePickerMatchWidth,onOpenChange:timePickerOnPopoverOpenChange}"
          >
            <c-fill name="activator" data="{ activator_attrs }">
              <button
                class="cui-time-picker__control"
                c-id="visible_id"
                type="button"
                c-disabled="disabled"
                c-aria-label="trigger_label"
                c-bind="activator_attrs"
                data-citry-time-picker-trigger
                data-citry-ui-part="control"
              >
                <span class="cui-time-picker__value" data-citry-ui-part="value">{{ display_value if display_value else placeholder }}</span>
                <c-CIcon name="clock" class_="cui-time-picker__icon" />
              </button>
            </c-fill>
            <c-fill name="title">
              <span c-$c-tr:citry-ui-time-picker-label="True if catalog_picker_label else None">{{ tr('citry-ui-time-picker-label') if catalog_picker_label else picker_label }}</span>
            </c-fill>
            <c-fill name="default">
              <c-CListbox
                c-label="picker_label"
                c-value="value"
                loop
                variant="plain"
                class_="cui-time-picker__listbox"
                $c-props="{value:timePickerListValue,disabled:timePickerListDisabled,onValueChange:timePickerOnListValueChange}"
              >
                <c-for each="option in options">
                  <c-CListboxOption c-value="option.value" c-text_value="option.label">{{ option.label }}</c-CListboxOption>
                </c-for>
              </c-CListbox>
            </c-fill>
          </c-CPopover>
          <button
            class="cui-time-picker__clear"
            type="button"
            c-aria-label="tr('citry-ui-time-picker-clear') if catalog_clear_label else clear_label"
            c-$c-tr:citry-ui-time-picker-clear[aria-label]="True if catalog_clear_label else None"
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
          value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, clearable: {},
          dismissible: {}, placement: {}, matchWidth: {}, variant: {}, size: {}, onValueChange: {}, onOpenChange: {},
        },
        init: ({ els, data, props, scope, effect, inject, unprovide, i18n }) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="fallback-input"]');
          const enhanced = root.querySelector(':scope > [data-citry-ui-part="enhanced-control"]');
          const trigger = root.querySelector('[data-citry-time-picker-trigger]');
          const valueText = trigger?.querySelector('[data-citry-ui-part="value"]');
          const clear = enhanced?.querySelector(':scope > [data-citry-ui-part="clear"]');
          if (!(root instanceof HTMLElement) || !(input instanceof HTMLInputElement) || input.type !== 'time' || !(enhanced instanceof HTMLElement) || !(trigger instanceof HTMLButtonElement) || !(valueText instanceof HTMLElement) || !(clear instanceof HTMLButtonElement)) throw new Error('[citry-ui] CTimePicker settled anatomy is invalid.');

          const fieldKey = Symbol.for('citry-ui:field');
          const formKey = Symbol.for('citry-ui:form');
          const field = inject(fieldKey, null);
          const form = inject(formKey, null);
          unprovide(fieldKey);
          unprovide(formKey);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CTimePicker form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CTimePicker');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          const optionSet = new Set(data.optionValues);
          const allowedPlacements = ['top-start','top','top-end','bottom-start','bottom','bottom-end'];
          const profile = data.showSeconds ? 'citry-ui-time-picker-display-seconds' : 'citry-ui-time-picker-display';
          let current = input.value || data.value || null;
          let initialValue = data.value || null;
          let internalOpen = false;
          let controlledValue = false;
          let controlledOpen = false;
          let nativeInvalid = false;
          let unavailableMessage = data.unavailableMessage;
          let invalidGeneration = 0;
          let dispatching = false;
          let ready = false;
          let configuration = null;

          const canonicalTime = value => {
            if (typeof value !== 'string') return null;
            const match = value.match(/^([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?$/);
            if (match === null || Number(match[1]) > 23 || Number(match[2]) > 59 || Number(match[3] ?? 0) > 59) return null;
            return value;
          };
          const fields = value => { const [hour, minute, second = '0'] = value.split(':'); return { hour:Number(hour), minute:Number(minute), second:Number(second) }; };
          const fromIso = value => { const result = new Date(0); const parsed = fields(value); result.setUTCHours(parsed.hour, parsed.minute, parsed.second, 0); return result; };
          const formatTime = value => i18n
            ? i18n.format.time(fields(value), { format: profile })
            : new Intl.DateTimeFormat(data.locale, { hour:'numeric', minute:'2-digit', second:data.showSeconds?'2-digit':undefined, timeZone:'UTC' }).format(fromIso(value));
          const translated = (owner, message, fallback, values = undefined) => i18n && data.catalog[owner] ? i18n.tr(message, values) : fallback;
          const placeholderText = () => translated('placeholder', 'citry-ui-time-picker-placeholder', data.placeholder);
          const pickerLabel = () => translated('picker_label', 'citry-ui-time-picker-label', data.pickerLabel);
          const triggerLabel = value => {
            if (!value) return pickerLabel();
            const formatted = formatTime(value);
            return data.catalog.change_label
              ? i18n?.tr('citry-ui-time-picker-change', { time: formatted }) ?? data.changeLabel.replaceAll('{time}', formatted)
              : data.changeLabel.replaceAll('{time}', formatted);
          };
          const resolveConfiguration = () => ({
            required: field ? field.required : resolver.boolean('required', data.required),
            disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
            readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
            clearable: resolver.boolean('clearable', data.clearable),
            dismissible: resolver.boolean('dismissible', data.dismissible),
            placement: resolver.choice('placement', data.placement, allowedPlacements),
            matchWidth: resolver.boolean('matchWidth', data.matchWidth),
            variant: resolver.choice('variant', data.variant, ['outline','filled','plain']),
            size: resolver.choice('size', data.size, ['sm','md','lg']),
          });
          const reportFieldOwned = () => {
            if (!field) return;
            ['required','disabled','readonly','invalid'].forEach(name => props[name] === undefined ? resolver.clear(name) : resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state'));
          };
          const emitNative = () => {
            dispatching = true;
            try { input.dispatchEvent(new Event('input', { bubbles:true })); input.dispatchEvent(new Event('change', { bubbles:true })); }
            finally { dispatching = false; }
          };
          const valueDetail = (value, previousValue, source, sourceEvent) => ({ value, previousValue, controlled: controlledValue, source, sourceEvent });
          const openDetail = (reason, source, forced = false) => ({ reason, controlled: controlledOpen, forced, source });
          const focusListbox = () => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
            if (!root.isConnected || !scope.timePickerOpen) return;
            const selected = current ? root.querySelector(`[data-citry-ui-part="listbox-option"][data-value="${CSS.escape(current)}"]`) : null;
            const target = selected ?? root.querySelector('[data-citry-ui-part="listbox-option"][tabindex="0"]');
            if (target instanceof HTMLElement) target.focus({ preventScroll:true });
          })));
          const requestOpen = (next, reason, source = null, forced = false) => {
            if (next === scope.timePickerOpen && !forced) return;
            if (!controlledOpen || forced) { internalOpen = next; scope.timePickerOpen = next; }
            resolver.callback('onOpenChange')?.(next, openDetail(reason, source, forced));
          };
          const requestValue = (next, source, event) => {
            if (configuration.disabled || configuration.readonly || next === current) return false;
            if (next !== null && (canonicalTime(next) === null || !optionSet.has(next))) return false;
            const previous = current;
            if (!controlledValue) { current = next; scope.timePickerListValue = next; }
            resolver.callback('onValueChange')?.(next, valueDetail(next, previous, source, event));
            if (!controlledValue) { render(); emitNative(); }
            requestOpen(false, source === 'option' ? 'selection' : 'clear', event);
            return true;
          };
          const updateGeneratedLabels = () => {
            const label = root.querySelector('[data-citry-ui-part="listbox-label"]');
            if (label instanceof HTMLElement) label.textContent = pickerLabel();
            root.querySelectorAll('[data-citry-ui-part="listbox-option"]').forEach(option => {
              const copy = option.querySelector('[data-citry-ui-part="listbox-option-label"]');
              if (copy instanceof HTMLElement && option instanceof HTMLElement && option.dataset.value) copy.textContent = formatTime(option.dataset.value);
            });
          };
          const render = () => owned(() => {
            input.value = current || '';
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            const unavailable = current !== null && !optionSet.has(current);
            input.setCustomValidity(unavailable ? unavailableMessage : '');
            const invalid = configuration.invalid || nativeInvalid || unavailable;
            trigger.disabled = configuration.disabled;
            trigger.setAttribute('aria-label', triggerLabel(current));
            valueText.textContent = current ? formatTime(current) : placeholderText();
            clear.hidden = !configuration.clearable || configuration.required || current === null;
            clear.disabled = configuration.disabled || configuration.readonly;
            runtime.states(root, { empty:current === null, open:scope.timePickerOpen, required:configuration.required, disabled:configuration.disabled, readonly:configuration.readonly, invalid });
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            runtime.relationships([trigger], field, { describedby:data.describedby, errormessage:data.errormessage }, invalid);
            scope.timePickerListValue = current;
            scope.timePickerListDisabled = configuration.disabled || configuration.readonly;
            scope.timePickerDismissible = configuration.dismissible;
            scope.timePickerPlacement = configuration.placement;
            scope.timePickerMatchWidth = configuration.matchWidth;
            updateGeneratedLabels();
          });

          scope.timePickerOpen = internalOpen;
          scope.timePickerListValue = current;
          scope.timePickerListDisabled = false;
          scope.timePickerOnPopoverOpenChange = (next, detail) => {
            if (detail?.forced) { internalOpen = false; scope.timePickerOpen = false; resolver.callback('onOpenChange')?.(false, { ...detail, controlled: controlledOpen }); if (ready) render(); return; }
            requestOpen(next, detail?.reason ?? 'native', detail?.source ?? null);
            if (next) focusListbox();
            if (ready) render();
          };
          scope.timePickerOnListValueChange = (next, detail) => requestValue(next, 'option', detail?.sourceEvent ?? null);

          listeners.add(clear, 'click', event => requestValue(null, 'clear', event));
          listeners.add(input, 'input', event => {
            if (dispatching) return;
            const next = input.value || null;
            if (controlledValue) { queueMicrotask(() => render()); return; }
            const previous = current;
            current = next;
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
            focusListbox();
          }, true);
          const reset = runtime.registerReset(root, input, {
            reset: event => {
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              const previous = current;
              if (!controlledValue) current = initialValue;
              else resolver.callback('onValueChange')?.(initialValue, valueDetail(initialValue, previous, 'reset', event));
              requestOpen(false, 'reset', event);
              render();
            },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });
          const unavailableBinding = i18n && data.catalog.unavailable_message ? i18n.bind({ message:'citry-ui-time-picker-unavailable', onChange:text => { unavailableMessage = text; if (ready) render(); } }) : null;
          const unsubscribe = i18n?.subscribe(() => { if (ready) render(); });

          effect(() => {
            reportFieldOwned();
            configuration = resolveConfiguration();
            const requestedValue = props.value;
            if (requestedValue === undefined) { controlledValue = false; resolver.clear('value'); }
            else if (requestedValue === null) { controlledValue = true; current = null; resolver.clear('value'); }
            else {
              const normalized = canonicalTime(requestedValue);
              if (normalized === null || !optionSet.has(normalized)) resolver.report('value', requestedValue);
              else { controlledValue = true; current = normalized; resolver.clear('value'); }
            }
            const requestedOpen = props.open;
            if (requestedOpen === undefined || requestedOpen === null) { if (controlledOpen) internalOpen = scope.timePickerOpen; controlledOpen = false; resolver.clear('open'); }
            else if (typeof requestedOpen === 'boolean') { const opening = !scope.timePickerOpen && requestedOpen; controlledOpen = true; internalOpen = requestedOpen; scope.timePickerOpen = requestedOpen; resolver.clear('open'); if (opening) focusListbox(); }
            else { resolver.report('open', requestedOpen); if (controlledOpen) internalOpen = scope.timePickerOpen; controlledOpen = false; }
            ready = true;
            render();
          });
          mutations.start(() => render());
          owned(() => {
            runtime.enhanceNative(input, trigger, { publicId:data.publicId, nativeId:data.nativeId, visibleId:data.visibleId, className:'cui-form-control__native--enhanced' });
            root.toggleAttribute('data-enhanced', true);
            root.setAttribute('data-citry-time-picker-initialized', '');
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
              runtime.enhanceNative(input, trigger, { publicId:data.publicId, nativeId:data.nativeId, visibleId:data.visibleId, className:'cui-form-control__native--enhanced' }, false);
              root.removeAttribute('data-enhanced');
              root.removeAttribute('data-citry-time-picker-initialized');
            });
          };
        },
      });
    """

    css_file = "runtime.min.css"

    messages = """
      citry-ui-time-picker-placeholder = Choose a time
      citry-ui-time-picker-label = Choose time
      # @param {str} $time - Locale-formatted selected wall-clock time.
      citry-ui-time-picker-change = Change time, { $time }
      citry-ui-time-picker-clear = Clear time
      citry-ui-time-picker-unavailable = Choose an available time.
    """


__all__ = [
    "CTimePicker",
    "CTimePickerOpenChangeDetail",
    "CTimePickerSize",
    "CTimePickerTime",
    "CTimePickerValueChangeDetail",
    "CTimePickerValueChangeSource",
    "CTimePickerVariant",
]
