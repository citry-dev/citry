"""Styled local and remote single-select Combobox component family."""

# ruff: noqa: E501 - Citry text bindings require one exact expression body.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._active_descendant import ACTIVE_DESCENDANT_RUNTIME_DEPENDENCY
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CComboboxFilter = Literal["contains", "starts_with", "none"]
CComboboxVariant = Literal["outline", "filled", "plain"]
CComboboxSize = Literal["sm", "md", "lg"]


@dataclass(frozen=True, slots=True)
class CComboboxOption:
    value: str
    label: str
    description: str | None = None
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class _ResolvedComboboxOption:
    value: str
    label: str
    description: str | None
    attrs: dict[str, object]


class CComboboxLoadingSlotData:
    pass


class CComboboxEmptySlotData:
    pass


class CComboboxErrorSlotData:
    pass


class CCombobox(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        options: Sequence[CComboboxOption] = ()
        name: str | None = None
        id: str | None = None
        value: str | None = None
        input_value: str | None = None
        open: bool = False
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        loading: bool = False
        clearable: bool = True
        open_on_focus: bool = False
        auto_highlight: bool = False
        filter: CComboboxFilter = "contains"
        min_chars: int = 0
        debounce_ms: int = 200
        placeholder: str | None = None
        autocomplete: str = "off"
        inputmode: str | None = None
        required_message: str = "Select an option."
        clear_label: str = "Clear selection"
        open_label: str = "Show options"
        close_label: str = "Hide options"
        loading_label: str = "Loading options..."
        empty_label: str = "No options found."
        error_label: str = "Options could not be loaded."
        variant: CComboboxVariant = "outline"
        size: CComboboxSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        loading: SlotInput[CComboboxLoadingSlotData] | None = None
        empty: SlotInput[CComboboxEmptySlotData] | None = None
        error: SlotInput[CComboboxErrorSlotData] | None = None

    def _localized_messages(self, kwargs: Kwargs) -> dict[str, object]:
        specs = (
            ("required_message", "citry-ui-combobox-required"),
            ("clear_label", "citry-ui-combobox-clear"),
            ("open_label", "citry-ui-combobox-open"),
            ("close_label", "citry-ui-combobox-close"),
            ("loading_label", "citry-ui-combobox-loading"),
            ("empty_label", "citry-ui-combobox-empty"),
            ("error_label", "citry-ui-combobox-error"),
        )
        result: dict[str, object] = {}
        for field_name, _message_id in specs:
            result[field_name] = getattr(kwargs, field_name)
            result[f"catalog_{field_name}"] = uses_catalog_default(self, field_name)
        if result["catalog_required_message"]:
            result["required_message"] = self.i18n.tr("citry-ui-combobox-required")
        if result["catalog_clear_label"]:
            result["clear_label"] = self.i18n.tr("citry-ui-combobox-clear")
        if result["catalog_open_label"]:
            result["open_label"] = self.i18n.tr("citry-ui-combobox-open")
        if result["catalog_close_label"]:
            result["close_label"] = self.i18n.tr("citry-ui-combobox-close")
        if result["catalog_loading_label"]:
            result["loading_label"] = self.i18n.tr("citry-ui-combobox-loading")
        if result["catalog_empty_label"]:
            result["empty_label"] = self.i18n.tr("citry-ui-combobox-empty")
        if result["catalog_error_label"]:
            result["error_label"] = self.i18n.tr("citry-ui-combobox-error")
        return result

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        messages = self._localized_messages(kwargs)
        if kwargs.name is not None:
            validate_non_empty_string("CCombobox", "name", kwargs.name)
        validate_html_id("CCombobox", kwargs.id)
        if kwargs.value is not None:
            validate_non_empty_string("CCombobox", "value", kwargs.value)
        if kwargs.input_value is not None and not isinstance(kwargs.input_value, str):
            msg = f"CCombobox input_value must be a string or None, got {kwargs.input_value!r}."
            raise TypeError(msg)
        validate_boolean("CCombobox", "open", kwargs.open)
        validate_optional_boolean("CCombobox", "required", kwargs.required)
        validate_optional_boolean("CCombobox", "disabled", kwargs.disabled)
        validate_optional_boolean("CCombobox", "readonly", kwargs.readonly)
        validate_optional_boolean("CCombobox", "invalid", kwargs.invalid)
        validate_boolean("CCombobox", "loading", kwargs.loading)
        validate_boolean("CCombobox", "clearable", kwargs.clearable)
        validate_boolean("CCombobox", "open_on_focus", kwargs.open_on_focus)
        validate_boolean("CCombobox", "auto_highlight", kwargs.auto_highlight)
        validate_choice("CCombobox", "filter", kwargs.filter, ("contains", "starts_with", "none"))
        self._validate_non_negative_integer("min_chars", kwargs.min_chars)
        self._validate_non_negative_integer("debounce_ms", kwargs.debounce_ms)
        validate_optional_string("CCombobox", "placeholder", kwargs.placeholder)
        validate_non_empty_string("CCombobox", "autocomplete", kwargs.autocomplete)
        if kwargs.inputmode is not None:
            validate_non_empty_string("CCombobox", "inputmode", kwargs.inputmode)
        for field_name in (
            "required_message",
            "clear_label",
            "open_label",
            "close_label",
            "loading_label",
            "empty_label",
            "error_label",
        ):
            validate_non_empty_string("CCombobox", field_name, messages[field_name])
        validate_choice("CCombobox", "variant", kwargs.variant, ("outline", "filled", "plain"))
        validate_choice("CCombobox", "size", kwargs.size, ("sm", "md", "lg"))
        reject_owned_attrs(
            kwargs.attrs,
            {
                "data-citry-combobox-initialized",
                "data-citry-ui-part",
                "data-disabled",
                "data-empty",
                "data-error",
                "data-invalid",
                "data-loading",
                "data-open",
                "data-readonly",
                "data-required",
                "data-size",
                "data-variant",
                "data-citry-combobox-root",
                "id",
            },
            "CCombobox attrs",
        )
        reject_owned_attrs(
            kwargs.input_attrs,
            {
                "aria-activedescendant",
                "aria-autocomplete",
                "aria-controls",
                "aria-expanded",
                "aria-invalid",
                "aria-required",
                "autocomplete",
                "data-citry-field-control",
                "data-citry-ui-part",
                "disabled",
                "form",
                "id",
                "inputmode",
                "name",
                "placeholder",
                "readonly",
                "required",
                "role",
                "type",
                "value",
            },
            "CCombobox input_attrs",
        )

        options = self._normalize_options(kwargs.options)
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            supplied_state = [
                name
                for name, value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("readonly", kwargs.readonly),
                    ("invalid", kwargs.invalid),
                )
                if value is not None
            ]
            if supplied_state:
                names = ", ".join(supplied_state)
                msg = f"CCombobox inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            field.register_control("CCombobox")
        if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
            msg = (
                f"CCombobox id {kwargs.id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CCombobox.id."
            )
            raise ValueError(msg)

        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            readonly = bool(field.readonly)
            invalid = bool(field.invalid)
        else:
            required = kwargs.required if kwargs.required is not None else False
            local_disabled = kwargs.disabled if kwargs.disabled is not None else False
            disabled = (bool(form.disabled) if form is not None else False) or local_disabled
            readonly = (
                kwargs.readonly if kwargs.readonly is not None else bool(form.readonly) if form is not None else False
            )
            invalid = kwargs.invalid if kwargs.invalid is not None else False
        input_id = kwargs.id or field_control_id or f"cui-combobox-{self.id}"
        root_id = f"{input_id}-root"
        listbox_id = f"{input_id}-listbox"
        selected_option = next((option for option in options if option.value == kwargs.value), None)
        input_value = kwargs.input_value
        if input_value is None:
            input_value = selected_option.label if selected_option is not None else ""
        effective_open = kwargs.open and not disabled and not readonly and len(input_value) >= kwargs.min_chars
        query_mirrors_selection = kwargs.input_value is None and kwargs.value is not None
        visible_options = (
            self._filter_options(options, input_value, kwargs.filter)
            if effective_open and not query_mirrors_selection
            else options
        )

        caller_input_attrs = dict(kwargs.input_attrs or {})
        external_described_by = caller_input_attrs.pop("aria-describedby", None)
        external_error_message = caller_input_attrs.pop("aria-errormessage", None)
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        resolved_options = tuple(
            _ResolvedComboboxOption(
                value=option.value,
                label=option.label,
                description=option.description,
                attrs={
                    "id": f"{listbox_id}-server-option-{index}",
                    "role": "option",
                    "aria-selected": "true" if option.value == kwargs.value else "false",
                    "aria-disabled": "true" if option.disabled else None,
                    "data-value": option.value,
                    "data-selected": option.value == kwargs.value,
                    "data-disabled": option.disabled,
                    "data-citry-ui-part": "option",
                },
            )
            for index, option in enumerate(visible_options)
        )
        return {
            "root_id": root_id,
            "input_id": input_id,
            "listbox_id": listbox_id,
            "name": kwargs.name,
            "value": kwargs.value,
            "input_value": input_value,
            "open": effective_open,
            "aria_expanded": "true" if effective_open else "false",
            "required": required,
            "native_required": required and kwargs.value is None,
            "aria_required": "true" if required else None,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "loading": kwargs.loading,
            "clearable": kwargs.clearable,
            "show_clear": kwargs.clearable and not disabled and not readonly and bool(kwargs.value or input_value),
            "placeholder": kwargs.placeholder,
            "autocomplete": kwargs.autocomplete,
            "inputmode": kwargs.inputmode,
            "clear_label": messages["clear_label"],
            "open_label": messages["open_label"],
            "close_label": messages["close_label"],
            "trigger_label": messages["close_label"] if effective_open else messages["open_label"],
            "trigger_disabled": disabled or readonly,
            "loading_label": messages["loading_label"],
            "empty_label": messages["empty_label"],
            "error_label": messages["error_label"],
            "variant": kwargs.variant,
            "size": kwargs.size,
            "options": resolved_options,
            "empty": effective_open and not visible_options and not kwargs.loading,
            "has_loading_slot": "loading" in self.raw_slots,
            "has_empty_slot": "empty" in self.raw_slots,
            "has_error_slot": "error" in self.raw_slots,
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
            "input_attrs": caller_input_attrs,
            "field_control": field is not None,
            **{key: value for key, value in messages.items() if key.startswith("catalog_")},
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        messages = self._localized_messages(kwargs)
        options = self._normalize_options(kwargs.options)
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        selected_option = next((option for option in options if option.value == kwargs.value), None)
        input_value = kwargs.input_value
        if input_value is None:
            input_value = selected_option.label if selected_option is not None else ""
        caller_input_attrs = dict(kwargs.input_attrs or {})
        input_id = kwargs.id or (str(field.control_id) if field is not None else f"cui-combobox-{self.id}")
        return {
            "items": [
                {
                    "value": option.value,
                    "label": option.label,
                    "description": option.description,
                    "disabled": option.disabled,
                }
                for option in options
            ],
            "value": kwargs.value,
            "inputValue": input_value,
            "inputValueExplicit": kwargs.input_value is not None,
            "open": kwargs.open and len(input_value) >= kwargs.min_chars,
            "required": bool(field.required)
            if field is not None
            else kwargs.required
            if kwargs.required is not None
            else False,
            "disabled": bool(field.disabled)
            if field is not None
            else kwargs.disabled
            if kwargs.disabled is not None
            else False,
            "readonly": bool(field.readonly)
            if field is not None
            else kwargs.readonly
            if kwargs.readonly is not None
            else bool(form.readonly)
            if form is not None
            else False,
            "invalid": bool(field.invalid)
            if field is not None
            else kwargs.invalid
            if kwargs.invalid is not None
            else False,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "loading": kwargs.loading,
            "clearable": kwargs.clearable,
            "openOnFocus": kwargs.open_on_focus,
            "autoHighlight": kwargs.auto_highlight,
            "filter": kwargs.filter,
            "minChars": kwargs.min_chars,
            "debounceMs": kwargs.debounce_ms,
            "requiredMessage": messages["required_message"],
            "openLabel": messages["open_label"],
            "closeLabel": messages["close_label"],
            "catalogRequiredMessage": messages["catalog_required_message"],
            "catalogOpenLabel": messages["catalog_open_label"],
            "catalogCloseLabel": messages["catalog_close_label"],
            "variant": kwargs.variant,
            "size": kwargs.size,
            "listboxId": f"{input_id}-listbox",
            "externalDescribedBy": caller_input_attrs.get("aria-describedby"),
            "externalErrorMessage": caller_input_attrs.get("aria-errormessage"),
        }

    @staticmethod
    def _validate_non_negative_integer(field_name: str, value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            msg = f"CCombobox {field_name} must be an integer, got {value!r}."
            raise TypeError(msg)
        if value < 0:
            msg = f"CCombobox {field_name} must be zero or greater, got {value!r}."
            raise ValueError(msg)

    @staticmethod
    def _normalize_options(options: Sequence[CComboboxOption]) -> tuple[CComboboxOption, ...]:
        if isinstance(options, (str, bytes)) or not isinstance(options, Sequence):
            msg = "CCombobox options must be a sequence of CComboboxOption values."
            raise TypeError(msg)
        normalized: list[CComboboxOption] = []
        seen: set[str] = set()
        for index, option in enumerate(options):
            if not isinstance(option, CComboboxOption):
                msg = f"CCombobox options[{index}] must be CComboboxOption, got {option!r}."
                raise TypeError(msg)
            validate_non_empty_string("CComboboxOption", "value", option.value)
            validate_non_empty_string("CComboboxOption", "label", option.label)
            if option.description is not None:
                validate_non_empty_string("CComboboxOption", "description", option.description)
            validate_boolean("CComboboxOption", "disabled", option.disabled)
            if option.value in seen:
                msg = f"CCombobox option values must be unique; {option.value!r} occurs more than once."
                raise ValueError(msg)
            seen.add(option.value)
            normalized.append(option)
        return tuple(normalized)

    @staticmethod
    def _filter_options(
        options: tuple[CComboboxOption, ...],
        query: str,
        filter_mode: CComboboxFilter,
    ) -> tuple[CComboboxOption, ...]:
        if filter_mode == "none":
            return options
        needle = query.lower()
        if filter_mode == "starts_with":
            return tuple(option for option in options if option.label.lower().startswith(needle))
        return tuple(option for option in options if needle in option.label.lower())

    template = """
      <div
        class="cui-combobox"
        c-id="root_id"
        c-data-open="open"
        c-data-loading="loading"
        c-data-empty="empty"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-combobox-root
        data-citry-ui-part="root"
      >
        <div
          class="cui-combobox__control"
          data-citry-ui-part="control"
        >
          <input
            class="cui-combobox__input"
            c-id="input_id"
            type="text"
            role="combobox"
            aria-autocomplete="list"
            c-aria-expanded="aria_expanded"
            c-aria-controls="listbox_id"
            c-aria-invalid="aria_invalid"
            c-aria-required="aria_required"
            c-aria-describedby="aria_describedby"
            c-aria-errormessage="aria_errormessage"
            c-value="input_value"
            c-required="native_required"
            c-disabled="disabled"
            c-placeholder="placeholder"
            c-autocomplete="autocomplete"
            c-inputmode="inputmode"
            c-data-citry-field-control="field_control"
            readonly
            c-bind="input_attrs"
            data-citry-ui-part="input"
          />
          <button
            class="cui-combobox__clear"
            type="button"
            c-aria-label="tr('citry-ui-combobox-clear') if catalog_clear_label else clear_label"
            c-$c-tr:citry-ui-combobox-clear[aria-label]="True if catalog_clear_label else None"
            c-hidden="not show_clear"
            tabindex="-1"
            data-citry-combobox-clear
            data-citry-ui-part="clear"
          >
            <span aria-hidden="true">
              &times;
            </span>
          </button>
          <button
            class="cui-combobox__trigger"
            type="button"
            c-aria-label="(
              tr('citry-ui-combobox-close') if catalog_close_label else close_label
            ) if open else (
              tr('citry-ui-combobox-open') if catalog_open_label else open_label
            )"
            c-aria-controls="listbox_id"
            c-aria-expanded="aria_expanded"
            aria-haspopup="listbox"
            c-disabled="trigger_disabled"
            tabindex="-1"
            data-citry-combobox-trigger
            data-citry-ui-part="trigger"
          >
            <span aria-hidden="true">
              &#9662;
            </span>
          </button>
        </div>
        <input
          c-name="name"
          c-value="value"
          c-disabled="disabled"
          type="hidden"
          data-citry-combobox-form-value
        />
        <div
          class="cui-combobox__popup"
          c-hidden="not open"
          data-citry-ui-part="popup"
        >
          <ul
            class="cui-combobox__listbox"
            c-id="listbox_id"
            role="listbox"
            c-aria-busy="loading"
            c-hidden="loading or empty"
            data-citry-ui-part="listbox"
          >
            <li
              c-for="option in options"
              c-bind="option.attrs"
            >
              <span data-citry-ui-part="option-label">
                {{ option.label }}
              </span>
              <span
                c-if="option.description is not None"
                data-citry-ui-part="option-description"
              >
                {{ option.description }}
              </span>
            </li>
          </ul>
          <div
            class="cui-combobox__status"
            c-hidden="not loading"
            role="status"
            data-citry-ui-part="loading"
          >
            <c-if cond="has_loading_slot">
              <c-slot name="loading" />
            </c-if>
            <c-else>
              <span c-$c-tr:citry-ui-combobox-loading="True if catalog_loading_label else None">{{ tr('citry-ui-combobox-loading') if catalog_loading_label else loading_label }}</span>
            </c-else>
          </div>
          <div
            class="cui-combobox__status"
            c-hidden="not empty"
            role="status"
            data-citry-ui-part="empty"
          >
            <c-if cond="has_empty_slot">
              <c-slot name="empty" />
            </c-if>
            <c-else>
              <span c-$c-tr:citry-ui-combobox-empty="True if catalog_empty_label else None">{{ tr('citry-ui-combobox-empty') if catalog_empty_label else empty_label }}</span>
            </c-else>
          </div>
          <div
            class="cui-combobox__status cui-combobox__status--error"
            role="status"
            data-citry-ui-part="error"
          >
            <c-if cond="has_error_slot">
              <c-slot name="error" />
            </c-if>
            <c-else>
              <span c-$c-tr:citry-ui-combobox-error="True if catalog_error_label else None">{{ tr('citry-ui-combobox-error') if catalog_error_label else error_label }}</span>
            </c-else>
          </div>
        </div>
      </div>
    """

    js_file = "runtime.min.js"

    css = """
      @layer citry-ui.theme {
        :where(.cui-combobox) {
          --_cui-combobox-background: var(--cui-combobox-background, Canvas);
          --_cui-combobox-foreground: var(--cui-combobox-foreground, CanvasText);
          --_cui-combobox-border-color: var(
            --cui-combobox-border-color,
            color-mix(in srgb, CanvasText 38%, transparent)
          );
          --_cui-combobox-focus-color: var(--cui-combobox-focus-color, Highlight);
          --_cui-combobox-invalid-color: var(
            --cui-combobox-invalid-color,
            light-dark(#d92d20, #f97066)
          );
          --_cui-combobox-radius: var(--cui-combobox-radius, 0.5rem);
          --_cui-combobox-height: var(--cui-combobox-height, 2.5rem);
          --_cui-combobox-inline-padding: var(--cui-combobox-inline-padding, 0.75rem);
          --_cui-combobox-popup-background: var(--cui-combobox-popup-background, Canvas);
          --_cui-combobox-popup-border-color: var(
            --cui-combobox-popup-border-color,
            color-mix(in srgb, CanvasText 20%, transparent)
          );
          --_cui-combobox-popup-shadow: var(
            --cui-combobox-popup-shadow,
            0 0.75rem 2rem rgb(15 23 42 / 18%)
          );
          --_cui-combobox-popup-max-height: var(--cui-combobox-popup-max-height, 18rem);
          --_cui-combobox-option-padding: var(--cui-combobox-option-padding, 0.625rem 0.75rem);
          --_cui-combobox-option-gap: var(--cui-combobox-option-gap, 0.125rem);
          --_cui-combobox-option-description-color: var(
            --cui-combobox-option-description-color,
            color-mix(in srgb, currentColor 68%, transparent)
          );
          --_cui-combobox-highlighted-background: var(
            --cui-combobox-highlighted-background,
            color-mix(in srgb, Highlight 16%, Canvas)
          );
          --_cui-combobox-selected-background: var(
            --cui-combobox-selected-background,
            color-mix(in srgb, Highlight 24%, Canvas)
          );
          --_cui-combobox-disabled-opacity: var(--cui-combobox-disabled-opacity, 0.55);
          --_cui-combobox-icon-size: var(--cui-combobox-icon-size, 2.25rem);
          --_cui-combobox-error-color: var(
            --cui-combobox-error-color,
            light-dark(#b42318, #fda29b)
          );

          position: relative;
          display: block;
          min-inline-size: 0;
          color: var(--_cui-combobox-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
        }

        :where(.cui-combobox__control) {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto auto;
          align-items: center;
          min-block-size: var(--_cui-combobox-height);
          border: 1px solid var(--_cui-combobox-border-color);
          border-radius: var(--_cui-combobox-radius);
          background: var(--_cui-combobox-background);
        }

        :where(.cui-combobox[data-variant="filled"] .cui-combobox__control) {
          --_cui-combobox-background: var(
            --cui-combobox-background,
            color-mix(in srgb, CanvasText 7%, Canvas)
          );
          --_cui-combobox-border-color: var(--cui-combobox-border-color, transparent);
        }

        :where(.cui-combobox[data-variant="plain"] .cui-combobox__control) {
          --_cui-combobox-background: var(--cui-combobox-background, transparent);
          --_cui-combobox-border-color: var(--cui-combobox-border-color, transparent);
          --_cui-combobox-radius: var(--cui-combobox-radius, 0);
        }

        :where(.cui-combobox[data-size="sm"]) {
          --_cui-combobox-height: var(--cui-combobox-height, 2.25rem);
          --_cui-combobox-inline-padding: var(--cui-combobox-inline-padding, 0.625rem);
        }

        :where(.cui-combobox[data-size="lg"]) {
          --_cui-combobox-height: var(--cui-combobox-height, 2.75rem);
          --_cui-combobox-inline-padding: var(--cui-combobox-inline-padding, 0.875rem);
        }

        :where(.cui-combobox:focus-within .cui-combobox__control) {
          border-color: var(--_cui-combobox-focus-color);
          outline: 0.1875rem solid color-mix(
            in srgb,
            var(--_cui-combobox-focus-color) 38%,
            transparent
          );
          outline-offset: 0.125rem;
        }

        :where(.cui-combobox[data-invalid] .cui-combobox__control) {
          border-color: var(--_cui-combobox-invalid-color);
        }

        :where(.cui-combobox__input) {
          min-inline-size: 0;
          block-size: 100%;
          padding-block: 0.5rem;
          padding-inline: var(--_cui-combobox-inline-padding);
          border: 0;
          outline: 0;
          background: transparent;
          color: inherit;
          font: inherit;
        }

        :where(.cui-combobox__clear, .cui-combobox__trigger) {
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-combobox-icon-size);
          block-size: var(--_cui-combobox-icon-size);
          padding: 0;
          border: 0;
          border-radius: calc(var(--_cui-combobox-radius) * 0.75);
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 1.125rem;
          cursor: pointer;
        }

        :where(.cui-combobox__clear[hidden], .cui-combobox__trigger[hidden]) {
          display: none;
        }

        :where(.cui-combobox__clear:focus-visible, .cui-combobox__trigger:focus-visible) {
          outline: 0.1875rem solid var(--_cui-combobox-focus-color);
          outline-offset: -0.1875rem;
        }

        :where(.cui-combobox__popup) {
          position: absolute;
          z-index: 20;
          inset-block-start: calc(100% + 0.375rem);
          inset-inline: 0;
          overflow: hidden;
          border: 1px solid var(--_cui-combobox-popup-border-color);
          border-radius: var(--_cui-combobox-radius);
          background: var(--_cui-combobox-popup-background);
          color: var(--_cui-combobox-foreground);
          box-shadow: var(--_cui-combobox-popup-shadow);
        }

        :where(.cui-combobox__listbox) {
          max-block-size: var(--_cui-combobox-popup-max-height);
          margin: 0;
          padding: 0.375rem;
          overflow: auto;
          list-style: none;
          overscroll-behavior: contain;
        }

        :where(.cui-combobox [data-citry-ui-part="option"]) {
          display: grid;
          gap: var(--_cui-combobox-option-gap);
          padding: var(--_cui-combobox-option-padding);
          border-radius: calc(var(--_cui-combobox-radius) * 0.75);
          cursor: default;
        }

        :where(.cui-combobox [data-citry-ui-part="option-description"]) {
          color: var(--_cui-combobox-option-description-color);
          font-size: 0.875em;
          line-height: 1.35;
        }

        :where(.cui-combobox [data-citry-ui-part="option"][data-highlighted]) {
          background: var(--_cui-combobox-highlighted-background);
        }

        :where(.cui-combobox [data-citry-ui-part="option"][data-selected]) {
          background: var(--_cui-combobox-selected-background);
          font-weight: 600;
        }

        :where(.cui-combobox [data-citry-ui-part="option"][data-disabled]) {
          opacity: var(--_cui-combobox-disabled-opacity);
        }

        :where(.cui-combobox__status) {
          padding: 0.75rem;
          color: color-mix(in srgb, currentColor 72%, transparent);
        }

        :where(.cui-combobox__status--error) {
          color: var(--_cui-combobox-error-color);
        }

        :where(.cui-combobox:not([data-error]) .cui-combobox__status--error) {
          display: none;
        }

        :where(.cui-combobox[data-disabled]) {
          opacity: var(--_cui-combobox-disabled-opacity);
        }

        @media (forced-colors: active) {
          :where(.cui-combobox__control, .cui-combobox__popup) {
            border-color: CanvasText;
          }

          :where(.cui-combobox [data-citry-ui-part="option"][data-highlighted]) {
            outline: 2px solid Highlight;
          }
        }
      }
    """

    messages = """
      citry-ui-combobox-required = Select an option.
      citry-ui-combobox-clear = Clear selection
      citry-ui-combobox-open = Show options
      citry-ui-combobox-close = Hide options
      citry-ui-combobox-loading = Loading options...
      citry-ui-combobox-empty = No options found.
      citry-ui-combobox-error = Options could not be loaded.
    """


class _CComboboxDependencies:
    js: ClassVar = [ACTIVE_DESCENDANT_RUNTIME_DEPENDENCY]


CCombobox.Dependencies = _CComboboxDependencies


__all__ = [
    "CCombobox",
    "CComboboxEmptySlotData",
    "CComboboxErrorSlotData",
    "CComboboxFilter",
    "CComboboxLoadingSlotData",
    "CComboboxOption",
    "CComboboxSize",
    "CComboboxVariant",
]
