"""Styled exact-decimal NumberInput component."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from string import Formatter
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
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CNumberInputCommitBehavior = Literal["validate", "clamp"]
CNumberInputSize = Literal["sm", "md", "lg"]
CNumberInputVariant = Literal["outline", "filled", "plain"]
CNumberInputChangeSource = Literal[
    "blur",
    "enter",
    "increment",
    "decrement",
    "page",
    "home",
    "end",
    "wheel",
    "reset",
]
CNumberInputParseStatus = Literal["empty", "incomplete", "invalid", "valid"]
CNumberInputExact = int | Decimal | str

_PLAIN_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_RUNTIME_PREFIXES = ("data-citry-", "data-cni", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "data-citry-number-input-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-invalid",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
        "autocomplete",
        FIELD_CONTROL_MARKER,
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
    }
)


class CNumberInputValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    inputValue: str
    controlled: bool
    source: CNumberInputChangeSource
    sourceEvent: object | None


class CNumberInputInputValueChangeDetail(TypedDict):
    inputValue: str
    previousInputValue: str
    status: CNumberInputParseStatus
    controlled: bool
    composing: bool
    sourceEvent: object | None


def _canonical_decimal(name: str, value: object, *, optional: bool = False, positive: bool = False) -> str | None:
    value = const_value(value)
    if value is None:
        if optional:
            return None
        raise TypeError(f"CNumberInput {name} cannot be None.")
    if type(value) is int:
        raw = str(value)
    elif type(value) is Decimal:
        decimal = cast("Decimal", value)
        if not decimal.is_finite():
            raise ValueError(f"CNumberInput {name} must be finite.")
        raw = format(decimal, "f")
    elif type(value) is str:
        raw = cast("str", value)
        if not _PLAIN_DECIMAL.fullmatch(raw):
            raise ValueError(f"CNumberInput {name} must use canonical plain-decimal syntax, got {raw!r}.")
    else:
        raise TypeError(
            f"CNumberInput {name} must be an int, Decimal, canonical decimal string"
            f"{' or None' if optional else ''}, got {value!r}."
        )
    negative = raw.startswith("-")
    unsigned = raw[1:] if negative else raw
    integer, dot, fraction = unsigned.partition(".")
    integer = integer.lstrip("0") or "0"
    fraction = fraction.rstrip("0") if dot else ""
    normalized = integer + (f".{fraction}" if fraction else "")
    if negative and normalized != "0":
        normalized = f"-{normalized}"
    digits = sum(character.isdigit() for character in normalized)
    if digits > 128:
        raise ValueError(f"CNumberInput {name} may contain at most 128 decimal digits.")
    if positive and Decimal(normalized) <= 0:
        raise ValueError(f"CNumberInput {name} must be greater than zero.")
    return normalized


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    value = const_value(value)
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"CNumberInput {name} must be a string{' or None' if optional else ''}, got {value!r}.")
    normalized = "".join(value).replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in normalized or not normalized.strip():
        raise ValueError(f"CNumberInput {name} must contain non-whitespace text and no U+0000.")
    return normalized


def _message(name: str, value: object, required_field: str | None = None) -> str:
    value = const_value(value)
    if not isinstance(value, str):
        raise TypeError(f"CNumberInput {name} must be a string, got {value!r}.")
    if "\0" in value or "\r" in value or "\n" in value or not value.strip():
        raise ValueError(f"CNumberInput {name} must be one nonempty line without U+0000.")
    text = value
    fields: list[str] = []
    for _literal, field_name, format_spec, conversion in Formatter().parse(text):
        if field_name is None:
            continue
        if field_name != required_field or format_spec or conversion:
            raise ValueError(f"CNumberInput {name} contains an unsupported placeholder.")
        fields.append(field_name)
    if required_field is not None and required_field not in fields:
        raise ValueError(f"CNumberInput {name} must contain {{{required_field}}}.")
    return text


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(destination: str, value: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CNumberInput {destination} must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"CNumberInput {destination}")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CNumberInput {destination} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CNumberInput {destination} cannot contain runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CNumberInput {destination} cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in owned:
            raise ValueError(f"CNumberInput {destination} cannot dynamically bind owned attribute {key!r}.")
    return copied


class CNumberInput(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CNumberInputExact | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CNumberInputExact | None = None
        max: CNumberInputExact | None = None
        step: CNumberInputExact = 1
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        show_controls: bool = True
        wheel: bool = False
        commit_behavior: CNumberInputCommitBehavior = "validate"
        placeholder: str | None = None
        autocomplete: str | None = None
        increment_label: str = "Increase value"
        decrement_label: str = "Decrease value"
        required_message: str = "Enter a number."
        invalid_message: str = "Enter a valid number."
        minimum_message: str = "Enter a value of at least {min}."
        maximum_message: str = "Enter a value of at most {max}."
        step_message: str = "Enter a value in increments of {step}."
        variant: CNumberInputVariant = "outline"
        size: CNumberInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_number_input_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)
        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CNumberInput", "name", name)
        validate_html_id("CNumberInput", supplied_id)
        validate_html_id("CNumberInput", form_input)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CNumberInput", input_name, getattr(kwargs, input_name))
        for input_name in ("show_controls", "wheel"):
            validate_boolean("CNumberInput", input_name, getattr(kwargs, input_name))
        for input_name in ("placeholder", "autocomplete"):
            validate_optional_string("CNumberInput", input_name, getattr(kwargs, input_name))
        commit_behavior = const_value(kwargs.commit_behavior)
        variant = const_value(kwargs.variant)
        size = const_value(kwargs.size)
        validate_choice("CNumberInput", "commit_behavior", commit_behavior, ("validate", "clamp"))
        validate_choice("CNumberInput", "variant", variant, ("outline", "filled", "plain"))
        validate_choice("CNumberInput", "size", size, ("sm", "md", "lg"))

        value = _canonical_decimal("value", kwargs.value, optional=True)
        minimum = _canonical_decimal("min", kwargs.min, optional=True)
        maximum = _canonical_decimal("max", kwargs.max, optional=True)
        step = cast("str", _canonical_decimal("step", kwargs.step, positive=True))
        if minimum is not None and maximum is not None and Decimal(minimum) > Decimal(maximum):
            raise ValueError("CNumberInput min cannot be greater than max.")
        if value is not None and minimum is not None and Decimal(value) < Decimal(minimum):
            raise ValueError("CNumberInput value cannot be less than min.")
        if value is not None and maximum is not None and Decimal(value) > Decimal(maximum):
            raise ValueError("CNumberInput value cannot be greater than max.")

        catalog = {
            name: uses_catalog_default(self, name)
            for name in (
                "increment_label",
                "decrement_label",
                "required_message",
                "invalid_message",
                "minimum_message",
                "maximum_message",
                "step_message",
            )
        }
        resolved_messages = {
            "increment_label": self.i18n.tr("citry-ui-number-input-increment")
            if catalog["increment_label"]
            else kwargs.increment_label,
            "decrement_label": self.i18n.tr("citry-ui-number-input-decrement")
            if catalog["decrement_label"]
            else kwargs.decrement_label,
            "required_message": self.i18n.tr("citry-ui-number-input-required")
            if catalog["required_message"]
            else kwargs.required_message,
            "invalid_message": self.i18n.tr("citry-ui-number-input-invalid")
            if catalog["invalid_message"]
            else kwargs.invalid_message,
            "minimum_message": self.i18n.tr("citry-ui-number-input-minimum", min="{min}")
            if catalog["minimum_message"]
            else kwargs.minimum_message,
            "maximum_message": self.i18n.tr("citry-ui-number-input-maximum", max="{max}")
            if catalog["maximum_message"]
            else kwargs.maximum_message,
            "step_message": self.i18n.tr("citry-ui-number-input-step", step="{step}")
            if catalog["step_message"]
            else kwargs.step_message,
        }
        increment_label = _message("increment_label", resolved_messages["increment_label"])
        decrement_label = _message("decrement_label", resolved_messages["decrement_label"])
        required_message = _message("required_message", resolved_messages["required_message"])
        invalid_message = _message("invalid_message", resolved_messages["invalid_message"])
        minimum_message = _message("minimum_message", resolved_messages["minimum_message"], "min")
        maximum_message = _message("maximum_message", resolved_messages["maximum_message"], "max")
        step_message = _message("step_message", resolved_messages["step_message"], "step")

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            supplied = [
                name for name in ("required", "disabled", "readonly", "invalid") if getattr(kwargs, name) is not None
            ]
            if supplied:
                raise ValueError(f"CNumberInput inside CField cannot set Field-owned state: {', '.join(supplied)}.")
            field.register_control("CNumberInput")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CNumberInput id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )
        public_id = supplied_id or field_control_id or f"cui-number-input-{self.id}"
        input_attrs = _attrs("input_attrs", kwargs.input_attrs, _INPUT_OWNED)
        root_attrs = _attrs("attrs", kwargs.attrs, _ROOT_OWNED)
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CNumberInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CNumberInput inside CForm cannot target a different native form owner.")
        required = bool(field.required) if field is not None else bool(kwargs.required)
        disabled = (
            bool(field.disabled)
            if field is not None
            else bool(form.disabled if form else False) or bool(kwargs.disabled)
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
            cast("str | None", input_attrs.pop("aria-describedby", None)),
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            cast("str | None", input_attrs.pop("aria-errormessage", None)) if invalid else None,
        )
        formatted = value or ""
        if value is not None and self.i18n.configured:
            formatted = self.i18n.format.number(Decimal(value), format="citry-ui-number-input")
        if self.i18n.configured:
            self.i18n.parse.number(formatted, format="citry-ui-number-input")

        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "transport_id": f"{public_id}-transport",
            "name": name,
            "form": form_owner,
            "value": value,
            "formatted_value": formatted,
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "show_controls": kwargs.show_controls,
            "placeholder": kwargs.placeholder,
            "autocomplete": kwargs.autocomplete,
            "increment_label": increment_label,
            "decrement_label": decrement_label,
            "catalog_increment_label": catalog["increment_label"],
            "catalog_decrement_label": catalog["decrement_label"],
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "field_control": field is not None,
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
            "variant": variant,
            "size": size,
        }
        self._cui_number_input_data = {
            "id": public_id,
            "transportId": f"{public_id}-transport",
            "name": name,
            "form": form_owner,
            "value": value,
            "formattedValue": formatted,
            "localizedServerValue": bool(self.i18n.configured and value is not None and formatted != value),
            "min": minimum,
            "max": maximum,
            "step": step,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "showControls": kwargs.show_controls,
            "wheel": kwargs.wheel,
            "commitBehavior": commit_behavior,
            "placeholder": kwargs.placeholder,
            "autocomplete": kwargs.autocomplete,
            "variant": variant,
            "size": size,
            "messages": {
                "required": required_message,
                "invalid": invalid_message,
                "minimum": minimum_message,
                "maximum": maximum_message,
                "step": step_message,
            },
            "catalog": {
                "required": catalog["required_message"],
                "invalid": catalog["invalid_message"],
                "minimum": catalog["minimum_message"],
                "maximum": catalog["maximum_message"],
                "step": catalog["step_message"],
            },
            "describedby": described_by,
            "errormessage": error_message,
        }
        self._cui_number_input_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_number_input_data

    template = """
      <div
        class="cui-number-input"
        c-data-empty="value is None"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="root_attrs"
        data-citry-ui-part="number-input"
      >
        <div data-citry-ui-part="control">
          <button
            type="button"
            tabindex="-1"
            c-hidden="not show_controls"
            c-disabled="disabled or readonly"
            c-aria-label="tr('citry-ui-number-input-decrement') if catalog_decrement_label else decrement_label"
            c-$c-tr:citry-ui-number-input-decrement[aria-label]="True if catalog_decrement_label else None"
            data-citry-ui-part="decrement"
          ><span aria-hidden="true">&minus;</span></button>
          <input
            c-id="public_id"
            c-name="name"
            c-form="form"
            type="text"
            role="spinbutton"
            inputmode="decimal"
            c-value="formatted_value"
            c-required="required"
            c-disabled="disabled"
            c-readonly="readonly"
            c-placeholder="placeholder"
            c-autocomplete="autocomplete"
            c-aria-invalid="'true' if invalid else None"
            c-aria-valuemin="minimum"
            c-aria-valuemax="maximum"
            c-aria-valuenow="value"
            c-aria-valuetext="formatted_value if value is not None else None"
            c-aria-describedby="aria_describedby"
            c-aria-errormessage="aria_errormessage"
            c-data-citry-field-control="field_control"
            c-bind="input_attrs"
            data-citry-ui-part="input"
          />
          <button
            type="button"
            tabindex="-1"
            c-hidden="not show_controls"
            c-disabled="disabled or readonly"
            c-aria-label="tr('citry-ui-number-input-increment') if catalog_increment_label else increment_label"
            c-$c-tr:citry-ui-number-input-increment[aria-label]="True if catalog_increment_label else None"
            data-citry-ui-part="increment"
          ><span aria-hidden="true">+</span></button>
        </div>
        <input c-id="transport_id" type="hidden" disabled />
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {}, min: {}, max: {}, step: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
          showControls: {}, wheel: {}, commitBehavior: {}, placeholder: {}, autocomplete: {},
          variant: {}, size: {}, onValueChange: {}, onInputValueChange: {},
        },
        init: ({ els, data, props, effect, inject, i18n }) => {
          const root = els[0];
          const control = root.querySelector(':scope > [data-citry-ui-part="control"]');
          const input = control?.querySelector(':scope > [data-citry-ui-part="input"]');
          const decrement = control?.querySelector(':scope > [data-citry-ui-part="decrement"]');
          const increment = control?.querySelector(':scope > [data-citry-ui-part="increment"]');
          const transport = root.querySelector(`:scope > #${CSS.escape(data.transportId)}`);
          if (!(control instanceof HTMLElement && input instanceof HTMLInputElement && transport instanceof HTMLInputElement)) {
            throw new Error('[citry-ui] CNumberInput settled anatomy is invalid.');
          }
          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CNumberInput form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CNumberInput');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          let current = data.value;
          let committed = data.value;
          let draft = data.formattedValue;
          let initialValue = data.value;
          let controlled = false;
          let composing = false;
          let dirty = false;
          let nativeInvalid = false;
          let serverLocalized = data.localizedServerValue;
          let generation = 0;
          let validationBinding = null;
          let lastFailure = null;
          let configuration = null;

          const canonical = value => {
            if (value === null) return null;
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
            if (normalized === undefined || normalized === null) return null;
            const negative = normalized.startsWith('-');
            const unsigned = negative ? normalized.slice(1) : normalized;
            const [integer, fraction = ''] = unsigned.split('.');
            return { integer: BigInt(`${negative ? '-' : ''}${integer}${fraction}`), scale: fraction.length };
          };
          const power = count => BigInt(`1${'0'.repeat(count)}`);
          const fromParts = (integer, scale) => {
            const negative = integer < BigInt(0);
            let digits = (negative ? -integer : integer).toString().padStart(scale + 1, '0');
            const text = scale ? `${digits.slice(0, -scale)}.${digits.slice(-scale)}` : digits;
            return canonical(`${negative ? '-' : ''}${text}`);
          };
          const align = (left, right) => {
            const scale = Math.max(left.scale, right.scale);
            return [left.integer * power(scale - left.scale), right.integer * power(scale - right.scale), scale];
          };
          const compare = (leftValue, rightValue) => {
            const [left, right] = align(parts(leftValue), parts(rightValue));
            return left < right ? -1 : left > right ? 1 : 0;
          };
          const add = (leftValue, rightValue, multiplier = 1) => {
            const left = parts(leftValue), right = parts(rightValue);
            const [a, b, scale] = align(left, right);
            return fromParts(a + b * BigInt(multiplier), scale);
          };
          const onGrid = (value, base, step) => {
            const valueParts = parts(value), baseParts = parts(base), stepParts = parts(step);
            const scale = Math.max(valueParts.scale, baseParts.scale, stepParts.scale);
            const amount = valueParts.integer * power(scale - valueParts.scale) - baseParts.integer * power(scale - baseParts.scale);
            const interval = stepParts.integer * power(scale - stepParts.scale);
            return amount % interval === BigInt(0);
          };
          const clamp = value => {
            if (configuration.min !== null && compare(value, configuration.min) < 0) return configuration.min;
            if (configuration.max !== null && compare(value, configuration.max) > 0) return configuration.max;
            return value;
          };
          const format = value => {
            if (value === null) return '';
            return i18n ? i18n.format.number(value, { format: 'citry-ui-number-input' }) : value;
          };
          const parse = text => {
            if (text === '') return { status: 'empty', value: null, reason: null };
            if (i18n) {
              const result = i18n.parse.number(text, { format: 'citry-ui-number-input' });
              return {
                status: result.state,
                value: result.state === 'valid' ? canonical(result.value) : null,
                reason: result.error,
              };
            }
            if (['-', '.', '-.'].includes(text)) return { status: 'incomplete', value: null, reason: 'incomplete' };
            const value = canonical(text);
            return value === undefined
              ? { status: 'invalid', value: null, reason: 'invalid' }
              : { status: 'valid', value, reason: null };
          };
          const replace = (template, key, value) => template.replaceAll(`{${key}}`, String(value));
          const localizedBound = (value, fallback) => value === null ? '' : format(value || fallback);
          const disposeValidationBinding = () => {
            validationBinding?.dispose();
            validationBinding = null;
          };
          const messageFor = (failure, values) => {
            let text = data.messages[failure];
            for (const [key, value] of Object.entries(values)) text = replace(text, key, value);
            return text;
          };
          const bindFailure = (failure, values) => {
            const fingerprint = `${failure ?? ''}:${JSON.stringify(values)}`;
            if (lastFailure === fingerprint && validationBinding !== null) {
              validationBinding.refresh();
              return;
            }
            disposeValidationBinding();
            lastFailure = fingerprint;
            const apply = text => {
              input.setCustomValidity(text);
              applyState();
            };
            if (!failure) {
              input.setCustomValidity('');
              return;
            }
            if (!i18n || !data.catalog[failure]) {
              apply(messageFor(failure, values));
              return;
            }
            if (failure === 'required') validationBinding = i18n.bind({ message: 'citry-ui-number-input-required', onChange: apply });
            else if (failure === 'invalid') validationBinding = i18n.bind({ message: 'citry-ui-number-input-invalid', onChange: apply });
            else if (failure === 'minimum') validationBinding = i18n.bind({ message: 'citry-ui-number-input-minimum', values: () => values, onChange: apply });
            else if (failure === 'maximum') validationBinding = i18n.bind({ message: 'citry-ui-number-input-maximum', values: () => values, onChange: apply });
            else validationBinding = i18n.bind({ message: 'citry-ui-number-input-step', values: () => values, onChange: apply });
          };
          const validity = (text = input.value) => {
            if (configuration.disabled || configuration.readonly) return { failure: null, parsed: parse(text), values: {} };
            const parsed = parse(text);
            if (parsed.status === 'empty') return { failure: configuration.required ? 'required' : null, parsed, values: {} };
            if (parsed.status !== 'valid' || parsed.value === undefined) return { failure: 'invalid', parsed, values: {} };
            if (configuration.min !== null && compare(parsed.value, configuration.min) < 0) {
              return { failure: 'minimum', parsed, values: { min: localizedBound(configuration.min, '') } };
            }
            if (configuration.max !== null && compare(parsed.value, configuration.max) > 0) {
              return { failure: 'maximum', parsed, values: { max: localizedBound(configuration.max, '') } };
            }
            if (!onGrid(parsed.value, configuration.min ?? '0', configuration.step)) {
              return { failure: 'step', parsed, values: { step: localizedBound(configuration.step, '1') } };
            }
            return { failure: null, parsed, values: {} };
          };
          const validate = () => {
            const result = validity();
            bindFailure(result.failure, result.values);
            return result;
          };
          const syncRelationships = invalid => runtime.relationships([input], field, {
            describedby: data.describedby, errormessage: data.errormessage, control: input,
            required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
          }, invalid);
          function applyState() {
            if (!configuration) return;
            const invalid = configuration.invalid || nativeInvalid || !input.validity.valid;
            owned(() => {
              input.required = configuration.required;
              input.disabled = configuration.disabled;
              input.readOnly = configuration.readonly;
              input.placeholder = configuration.placeholder ?? '';
              input.autocomplete = configuration.autocomplete ?? '';
              input.setAttribute('aria-valuemin', configuration.min ?? '');
              input.setAttribute('aria-valuemax', configuration.max ?? '');
              if (configuration.min === null) input.removeAttribute('aria-valuemin');
              if (configuration.max === null) input.removeAttribute('aria-valuemax');
              if (current === null) {
                input.removeAttribute('aria-valuenow');
                input.removeAttribute('aria-valuetext');
              } else {
                input.setAttribute('aria-valuenow', current);
                input.setAttribute('aria-valuetext', format(current));
              }
              transport.name = configuration.disabled ? '' : (data.name ?? '');
              transport.disabled = configuration.disabled || !data.name;
              transport.value = current ?? '';
              if (data.form) transport.setAttribute('form', data.form); else transport.removeAttribute('form');
              if (data.form) input.setAttribute('form', data.form); else input.removeAttribute('form');
              input.name = '';
              decrement && (decrement.disabled = configuration.disabled || configuration.readonly);
              increment && (increment.disabled = configuration.disabled || configuration.readonly);
              decrement?.toggleAttribute('hidden', !configuration.showControls);
              increment?.toggleAttribute('hidden', !configuration.showControls);
              runtime.states(root, {
                empty: current === null, required: configuration.required, disabled: configuration.disabled,
                readonly: configuration.readonly, invalid,
              });
              root.dataset.variant = configuration.variant;
              root.dataset.size = configuration.size;
              syncRelationships(invalid);
            });
          }
          const inputCallback = event => {
            const previous = draft;
            draft = input.value;
            dirty = true;
            serverLocalized = false;
            const result = validate();
            resolver.callback('onInputValueChange')?.(draft, {
              inputValue: draft, previousInputValue: previous, status: result.parsed.status,
              controlled, composing, sourceEvent: event,
            });
          };
          const nativeCommit = () => {
            transport.dispatchEvent(new Event('input', { bubbles: true }));
            transport.dispatchEvent(new Event('change', { bubbles: true }));
          };
          const request = (next, source, sourceEvent, visible = null) => {
            if (next === current) {
              dirty = false;
              draft = visible ?? format(next);
              input.value = draft;
              validate();
              return false;
            }
            const previous = current;
            dirty = false;
            const callback = resolver.callback('onValueChange');
            if (!controlled) {
              current = next;
              committed = next;
              draft = visible ?? format(next);
              input.value = draft;
            }
            callback?.(next, {
              value: next, previousValue: previous, inputValue: visible ?? format(next), controlled, source, sourceEvent,
            });
            if (!controlled) nativeCommit();
            applyState();
            validate();
            return true;
          };
          const commitDraft = (source, event) => {
            const result = validity();
            let next = result.parsed.status === 'valid' ? result.parsed.value : null;
            if (result.failure && configuration.commitBehavior === 'clamp' && next !== null && ['minimum', 'maximum'].includes(result.failure)) {
              next = clamp(next);
            } else if (result.failure) {
              nativeInvalid = true;
              field?.setNativeInvalid(true);
              bindFailure(result.failure, result.values);
              applyState();
              return false;
            }
            nativeInvalid = false;
            field?.setNativeInvalid(false);
            return request(next, source, event);
          };
          const stepValue = (direction, source, event, multiplier = 1) => {
            if (configuration.disabled || configuration.readonly) return;
            const parsed = parse(input.value);
            let base = parsed.status === 'valid' ? parsed.value : current;
            if (base === null) base = configuration.min ?? '0';
            const next = clamp(add(base, configuration.step, direction * multiplier));
            request(next, source, event);
            input.focus({ preventScroll: true });
            input.select();
          };
          const configurationValue = (name, fallback, optional = false, positive = false) => {
            const raw = props[name];
            if (raw === undefined) return fallback;
            if (raw === null && optional) return null;
            const value = canonical(raw);
            if (value === undefined || value === null || (positive && compare(value, '0') <= 0)) {
              resolver.report(name, raw);
              return fallback;
            }
            resolver.clear(name);
            return value;
          };
          const resolveConfiguration = () => {
            const min = configurationValue('min', data.min, true);
            const max = configurationValue('max', data.max, true);
            return {
              min, max, step: configurationValue('step', data.step, false, true),
              required: field ? field.required : resolver.boolean('required', data.required),
              disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled),
              readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
              invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
              showControls: resolver.boolean('showControls', data.showControls),
              wheel: resolver.boolean('wheel', data.wheel),
              commitBehavior: resolver.choice('commitBehavior', data.commitBehavior, ['validate', 'clamp']),
              placeholder: resolver.string('placeholder', data.placeholder),
              autocomplete: resolver.string('autocomplete', data.autocomplete),
              variant: resolver.choice('variant', data.variant, ['outline', 'filled', 'plain']),
              size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
            };
          };
          const reset = runtime.registerReset(root, input, {
            reset: () => {
              const next = initialValue;
              if (controlled) {
                resolver.callback('onValueChange')?.(next, {
                  value: next, previousValue: current, inputValue: format(next), controlled: true,
                  source: 'reset', sourceEvent: null,
                });
              } else {
                current = next; committed = next; dirty = false; draft = format(next); input.value = draft; nativeCommit();
              }
              nativeInvalid = false; field?.setNativeInvalid(false); validate(); applyState();
            },
            invalidate: () => { generation += 1; },
          });
          const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); applyState(); });

          listeners.add(input, 'focus', () => {
            if (!i18n && serverLocalized) {
              draft = current ?? '';
              input.value = draft;
              serverLocalized = false;
            }
            owned(() => root.toggleAttribute('data-focused', true));
          });
          listeners.add(input, 'blur', event => {
            owned(() => root.removeAttribute('data-focused'));
            if (!composing) commitDraft('blur', event);
          });
          listeners.add(input, 'input', event => inputCallback(event));
          listeners.add(input, 'compositionstart', () => { composing = true; });
          listeners.add(input, 'compositionend', event => { composing = false; inputCallback(event); });
          listeners.add(input, 'keydown', event => {
            if (composing || event.isComposing || event.keyCode === 229) return;
            if (event.key === 'ArrowUp') { event.preventDefault(); stepValue(1, 'increment', event); }
            else if (event.key === 'ArrowDown') { event.preventDefault(); stepValue(-1, 'decrement', event); }
            else if (event.key === 'PageUp') { event.preventDefault(); stepValue(1, 'page', event, 10); }
            else if (event.key === 'PageDown') { event.preventDefault(); stepValue(-1, 'page', event, 10); }
            else if (event.key === 'Home' && configuration.min !== null) { event.preventDefault(); request(configuration.min, 'home', event); }
            else if (event.key === 'End' && configuration.max !== null) { event.preventDefault(); request(configuration.max, 'end', event); }
            else if (event.key === 'Enter') commitDraft('enter', event);
          });
          listeners.add(input, 'wheel', event => {
            if (!configuration.wheel || document.activeElement !== input || event.deltaY === 0) return;
            event.preventDefault();
            stepValue(event.deltaY < 0 ? 1 : -1, 'wheel', event);
          }, { passive: false });
          decrement && listeners.add(decrement, 'pointerdown', event => event.preventDefault());
          increment && listeners.add(increment, 'pointerdown', event => event.preventDefault());
          decrement && listeners.add(decrement, 'click', event => stepValue(-1, 'decrement', event));
          increment && listeners.add(increment, 'click', event => stepValue(1, 'increment', event));
          listeners.add(input, 'invalid', event => {
            event.preventDefault(); nativeInvalid = true; field?.setNativeInvalid(true); validate(); applyState();
            const token = ++generation;
            queueMicrotask(() => { if (token === generation && root.isConnected) input.focus({ preventScroll: true }); });
          }, true);

          let unsubscribe = null;
          if (i18n) unsubscribe = i18n.subscribe(() => {
            if (!dirty && !composing) {
              draft = format(current); input.value = draft;
            }
            validationBinding?.refresh();
            applyState();
          });
          effect(() => {
            configuration = resolveConfiguration();
            if (configuration.min !== null && configuration.max !== null && compare(configuration.min, configuration.max) > 0) {
              resolver.report('min', configuration.min, 'min cannot exceed max');
              configuration.min = data.min; configuration.max = data.max;
            }
            const requested = props.value;
            if (requested === undefined) {
              if (controlled) { controlled = false; current = committed; draft = format(current); input.value = draft; }
              resolver.clear('value');
            } else {
              const normalized = requested === null ? null : canonical(requested);
              if (normalized === undefined) resolver.report('value', requested);
              else {
                resolver.clear('value'); controlled = true; current = normalized; dirty = false;
                if (!composing) { draft = format(current); input.value = draft; }
              }
            }
            validate(); applyState();
          });
          mutations.start(() => applyState());
          owned(() => root.setAttribute('data-citry-number-input-initialized', ''));

          return () => {
            generation += 1;
            disposeValidationBinding(); unsubscribe?.(); listeners.stop(); mutations.stop(); stopFieldset(); reset();
            if (nativeInvalid) field?.setNativeInvalid(false);
            owned(() => {
              root.removeAttribute('data-citry-number-input-initialized');
              input.name = data.name ?? '';
              transport.name = '';
              transport.disabled = true;
            });
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-number-input) {
          --_cui-number-input-background: var(--cui-number-input-background, Canvas);
          --_cui-number-input-foreground: var(--cui-number-input-foreground, CanvasText);
          --_cui-number-input-border-color: var(--cui-number-input-border-color, color-mix(in srgb, CanvasText 38%, transparent));
          --_cui-number-input-focus-color: var(--cui-number-input-focus-color, Highlight);
          --_cui-number-input-invalid-border-color: var(--cui-number-input-invalid-border-color, light-dark(#d92d20, #f97066));
          --_cui-number-input-radius: var(--cui-number-input-radius, .5rem);
          --_cui-number-input-height: var(--cui-number-input-height, 2.5rem);
          --_cui-number-input-inline-padding: var(--cui-number-input-inline-padding, .75rem);
          --_cui-number-input-control-size: var(--cui-number-input-control-size, 2.5rem);
          color: var(--_cui-number-input-foreground);
          inline-size: min(100%, 18rem);
        }
        :where(.cui-number-input [data-citry-ui-part="control"]) {
          display: flex;
          min-inline-size: 0;
          block-size: var(--_cui-number-input-height);
          overflow: clip;
          border: 1px solid var(--_cui-number-input-border-color);
          border-radius: var(--_cui-number-input-radius);
          background: var(--_cui-number-input-background);
        }
        :where(.cui-number-input [data-citry-ui-part="input"]) {
          min-inline-size: 0;
          flex: 1 1 auto;
          border: 0;
          outline: 0;
          background: transparent;
          color: inherit;
          padding-inline: var(--_cui-number-input-inline-padding);
          font: inherit;
          text-align: start;
        }
        :where(.cui-number-input [data-citry-ui-part="decrement"], .cui-number-input [data-citry-ui-part="increment"]) {
          flex: 0 0 var(--_cui-number-input-control-size);
          border: 0;
          border-inline-end: 1px solid var(--_cui-number-input-border-color);
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 1.15em;
          cursor: pointer;
        }
        :where(.cui-number-input [data-citry-ui-part="increment"]) {
          border-inline: 1px 0 solid var(--_cui-number-input-border-color);
        }
        :where(.cui-number-input [data-citry-ui-part="decrement"]:hover, .cui-number-input [data-citry-ui-part="increment"]:hover) {
          background: color-mix(in srgb, CanvasText 8%, transparent);
        }
        :where(.cui-number-input[data-variant="filled"] [data-citry-ui-part="control"]) {
          background: color-mix(in srgb, CanvasText 7%, Canvas);
        }
        :where(.cui-number-input[data-variant="plain"] [data-citry-ui-part="control"]) {
          border-color: transparent;
          border-block-end-color: var(--_cui-number-input-border-color);
          border-radius: 0;
        }
        :where(.cui-number-input[data-size="sm"]) { --_cui-number-input-height: 2rem; --_cui-number-input-control-size: 2rem; }
        :where(.cui-number-input[data-size="lg"]) { --_cui-number-input-height: 3rem; --_cui-number-input-control-size: 3rem; }
        :where(.cui-number-input:focus-within [data-citry-ui-part="control"]) {
          border-color: var(--_cui-number-input-focus-color);
          box-shadow: 0 0 0 2px color-mix(in srgb, var(--_cui-number-input-focus-color) 28%, transparent);
        }
        :where(.cui-number-input[data-invalid] [data-citry-ui-part="control"]) { border-color: var(--_cui-number-input-invalid-border-color); }
        :where(.cui-number-input[data-disabled]) { opacity: .58; }
        :where(.cui-number-input[data-disabled] button, .cui-number-input[data-readonly] button) { cursor: default; }
        @media (pointer: coarse) {
          :where(.cui-number-input) { --_cui-number-input-height: max(2.75rem, var(--cui-number-input-height, 2.5rem)); --_cui-number-input-control-size: max(2.75rem, var(--cui-number-input-control-size, 2.5rem)); }
        }
        @media (forced-colors: active) {
          :where(.cui-number-input [data-citry-ui-part="control"]) { border-color: CanvasText; forced-color-adjust: auto; }
          :where(.cui-number-input:focus-within [data-citry-ui-part="control"]) { outline: 2px solid Highlight; outline-offset: 2px; box-shadow: none; }
        }
        @media print {
          :where(.cui-number-input [data-citry-ui-part="decrement"], .cui-number-input [data-citry-ui-part="increment"]) { display: none; }
          :where(.cui-number-input [data-citry-ui-part="control"]) { border-color: transparent; }
        }
      }
    """

    messages = """
      citry-ui-number-input-decrement = Decrease value
      citry-ui-number-input-increment = Increase value
      citry-ui-number-input-required = Enter a number.
      citry-ui-number-input-invalid = Enter a valid number.
      # @param {str} $min - Locale-formatted inclusive minimum.
      citry-ui-number-input-minimum = Enter a value of at least { $min }.
      # @param {str} $max - Locale-formatted inclusive maximum.
      citry-ui-number-input-maximum = Enter a value of at most { $max }.
      # @param {str} $step - Locale-formatted exact step.
      citry-ui-number-input-step = Enter a value in increments of { $step }.
    """


__all__ = [
    "CNumberInput",
    "CNumberInputChangeSource",
    "CNumberInputCommitBehavior",
    "CNumberInputExact",
    "CNumberInputInputValueChangeDetail",
    "CNumberInputParseStatus",
    "CNumberInputSize",
    "CNumberInputValueChangeDetail",
    "CNumberInputVariant",
]
