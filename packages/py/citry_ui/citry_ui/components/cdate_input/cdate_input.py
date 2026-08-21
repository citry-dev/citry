"""Styled native calendar-date input."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, Literal, TypeAlias, cast

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
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CDateInputValue: TypeAlias = date | str
CDateInputVariant = Literal["outline", "filled", "plain"]
CDateInputSize = Literal["sm", "md", "lg"]

_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_OWNED_ATTRS = frozenset(
    {
        "aria-invalid",
        "autocomplete",
        "data-citry-date-input-initialized",
        FIELD_CONTROL_MARKER,
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "disabled",
        "form",
        "id",
        "max",
        "min",
        "name",
        "readonly",
        "required",
        "step",
        "type",
        "value",
    }
)


def _positive_step(value: object) -> int:
    value = const_value(value)
    if type(value) is not int:
        raise TypeError(f"CDateInput step must be an exact positive integer, got {value!r}.")
    if value <= 0:
        raise ValueError(f"CDateInput step must be greater than zero, got {value!r}.")
    return cast("int", value)


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(value: Mapping[str, object] | None) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CDateInput attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CDateInput")
    reject_html_attr_bindings(copied, _OWNED_ATTRS, "CDateInput")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CDateInput attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CDateInput attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CDateInput attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _OWNED_ATTRS:
            raise ValueError(f"CDateInput attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CDateInput(LibraryComponent):
    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CDateInputValue | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CDateInputValue | None = None
        max: CDateInputValue | None = None
        step: int = 1
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        autocomplete: str | None = None
        variant: CDateInputVariant = "outline"
        size: CDateInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_date_input_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = canonical_date("CDateInput", "value", kwargs.value, optional=True)
        minimum = canonical_date("CDateInput", "min", kwargs.min, optional=True)
        maximum = canonical_date("CDateInput", "max", kwargs.max, optional=True)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"CDateInput min {minimum!r} cannot be later than max {maximum!r}.")
        step = _positive_step(kwargs.step)
        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CDateInput", "name", name)
        validate_html_id("CDateInput", form_input)
        validate_html_id("CDateInput", supplied_id)
        validate_optional_boolean("CDateInput", "required", kwargs.required)
        validate_optional_boolean("CDateInput", "disabled", kwargs.disabled)
        validate_optional_boolean("CDateInput", "readonly", kwargs.readonly)
        validate_optional_boolean("CDateInput", "invalid", kwargs.invalid)
        validate_optional_string("CDateInput", "autocomplete", kwargs.autocomplete)
        validate_choice("CDateInput", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CDateInput", "size", kwargs.size, _SIZES)

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
                    f"CDateInput inside CField cannot set Field-owned state: {', '.join(supplied_states)}."
                )
            field.register_control("CDateInput")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CDateInput id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )

        public_id = supplied_id or field_control_id or f"cui-date-input-{self.id}"
        caller_attrs = _attrs(kwargs.attrs)
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CDateInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CDateInput inside CForm cannot target a different native form owner.")

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
        external_described_by = cast(
            "str | None",
            pop_html_attr(caller_attrs, "aria-describedby", component_name="CDateInput"),
        )
        external_error_message = cast(
            "str | None",
            pop_html_attr(caller_attrs, "aria-errormessage", component_name="CDateInput"),
        )
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "name": name,
            "form": form_owner,
            "value": value,
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "autocomplete": kwargs.autocomplete,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "field_control": field is not None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "attrs": merge_root_attrs(caller_attrs, kwargs.class_, kwargs.style),
        }
        self._cui_date_input_data: dict[str, object] = {
            "value": value,
            "min": minimum,
            "max": maximum,
            "step": step,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "describedby": external_described_by,
            "errormessage": external_error_message,
        }
        self._cui_date_input_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_date_input_data

    template = """
      <input
        class="cui-date-input"
        c-id="public_id"
        c-name="name"
        c-form="form"
        type="date"
        c-value="value"
        c-min="minimum"
        c-max="maximum"
        c-step="step"
        c-required="required"
        c-disabled="disabled"
        c-readonly="readonly"
        c-autocomplete="autocomplete"
        c-aria-invalid="'true' if invalid else None"
        c-aria-describedby="aria_describedby"
        c-aria-errormessage="aria_errormessage"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-empty="not value"
        c-data-variant="variant"
        c-data-size="size"
        c-data-citry-field-control="field_control"
        c-bind="attrs"
        data-citry-ui-part="date-input"
      />
    """

    js = """
      $component({
        props: {
          value: {}, min: {}, max: {}, step: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
          variant: {}, size: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const input = els[0];
          if (!(input instanceof HTMLInputElement) || input.type !== 'date') {
            throw new Error('[citry-ui] CDateInput settled anatomy is invalid.');
          }
          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CDateInput form-control runtime is unavailable.');
          const resolver = runtime.resolver(input, props, 'CDateInput');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(input);
          const owned = mutations.owned;
          let controlled = false;
          let current = data.value ?? '';
          const initialValue = current;
          let nativeInvalid = false;
          let invalidGeneration = 0;
          let configuration = null;
          let previousConstraints = { min: data.min, max: data.max, step: data.step };

          const canonicalDate = value => {
            if (typeof value !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) return null;
            const [year, month, day] = value.split('-').map(Number);
            if (year < 1 || year > 9999) return null;
            const date = new Date(0);
            date.setUTCHours(12, 0, 0, 0);
            date.setUTCFullYear(year, month - 1, day);
            return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
              ? value : null;
          };
          const optionalDate = (name, fallback) => {
            const value = props[name];
            if (value === undefined) { resolver.clear(name); return fallback; }
            if (value === null) { resolver.clear(name); return null; }
            const valid = canonicalDate(value);
            if (valid !== null) { resolver.clear(name); return valid; }
            resolver.report(name, value);
            return previousConstraints[name];
          };
          const resolveConstraints = () => {
            const minimum = optionalDate('min', data.min);
            const maximum = optionalDate('max', data.max);
            const requestedStep = props.step === undefined ? data.step : props.step;
            const step = Number.isInteger(requestedStep) && requestedStep > 0
              ? requestedStep : previousConstraints.step;
            if (step === requestedStep) resolver.clear('step'); else resolver.report('step', requestedStep);
            if (minimum !== null && maximum !== null && minimum > maximum) {
              resolver.report('min/max', { min: minimum, max: maximum });
              return previousConstraints;
            }
            resolver.clear('min/max');
            previousConstraints = { min: minimum, max: maximum, step };
            return previousConstraints;
          };
          const resolveConfiguration = () => ({
            required: field ? field.required : resolver.boolean('required', data.required),
            disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
            readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
            variant: resolver.choice('variant', data.variant, ['outline', 'filled', 'plain']),
            size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
            constraints: resolveConstraints(),
          });
          const reportFieldOwned = () => {
            if (!field) return;
            ['required', 'disabled', 'readonly', 'invalid'].forEach(name => {
              if (props[name] === undefined) resolver.clear(name);
              else resolver.report(name, props[name], 'ignoring it because the enclosing CField owns this state');
            });
          };
          const syncRelationships = invalid => runtime.relationships([input], field, {
            describedby: data.describedby,
            errormessage: data.errormessage,
            control: input,
            required: configuration.required,
            disabled: configuration.disabled,
            readonly: configuration.readonly,
          }, invalid);
          const render = () => owned(() => {
            if (input.value !== current) input.value = current;
            const constraints = configuration.constraints;
            runtime.attr(input, 'min', constraints.min);
            runtime.attr(input, 'max', constraints.max);
            input.step = String(constraints.step);
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            const invalid = configuration.invalid || nativeInvalid;
            runtime.states(input, {
              required: configuration.required,
              disabled: configuration.disabled,
              readonly: configuration.readonly,
              invalid,
              empty: !current,
            });
            input.dataset.variant = configuration.variant;
            input.dataset.size = configuration.size;
            syncRelationships(invalid);
          });
          const clearNativeInvalid = () => {
            if (!nativeInvalid || !input.validity.valid) return;
            nativeInvalid = false;
            field?.setNativeInvalid(false);
          };
          const onInput = () => {
            const requested = input.value;
            clearNativeInvalid();
            if (controlled) {
              queueMicrotask(() => { if (controlled) render(); });
              return;
            }
            current = requested;
            render();
          };
          const reset = runtime.registerReset(input, input, {
            reset: event => {
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              if (!controlled) current = initialValue;
              render();
            },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(input, input, () => {
            configuration = resolveConfiguration();
            render();
          });

          listeners.add(input, 'input', onInput);
          listeners.add(input, 'change', clearNativeInvalid);
          listeners.add(input, 'invalid', event => {
            event.preventDefault();
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            render();
            const token = ++invalidGeneration;
            runtime.invalidFocus(input, input, () => token === invalidGeneration);
          }, true);
          effect(() => {
            reportFieldOwned();
            configuration = resolveConfiguration();
            const requested = props.value;
            if (requested === undefined) {
              controlled = false;
              resolver.clear('value');
            } else if (requested === null) {
              controlled = true;
              current = '';
              resolver.clear('value');
            } else {
              const normalized = canonicalDate(requested);
              if (normalized === null) resolver.report('value', requested);
              else { controlled = true; current = normalized; resolver.clear('value'); }
            }
            clearNativeInvalid();
            render();
          });
          mutations.start(() => render());
          owned(() => input.setAttribute('data-citry-date-input-initialized', ''));
          render();

          return () => {
            invalidGeneration += 1;
            listeners.stop();
            mutations.stop();
            stopFieldset();
            reset();
            if (nativeInvalid) field?.setNativeInvalid(false);
            owned(() => input.removeAttribute('data-citry-date-input-initialized'));
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = ["CDateInput", "CDateInputSize", "CDateInputValue", "CDateInputVariant"]
