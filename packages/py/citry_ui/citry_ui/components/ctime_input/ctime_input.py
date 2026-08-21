"""Styled native wall-clock time input."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
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
from citry_ui.components._form_control_runtime import FORM_CONTROL_RUNTIME_DEPENDENCY
from citry_ui.components._time import canonical_time
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CTimeInputValue: TypeAlias = time | str
CTimeInputVariant = Literal["outline", "filled", "plain"]
CTimeInputSize = Literal["sm", "md", "lg"]

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
        "data-citry-time-input-initialized",
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
        raise TypeError(f"CTimeInput step must be an exact positive integer, got {value!r}.")
    if value <= 0:
        raise ValueError(f"CTimeInput step must be greater than zero, got {value!r}.")
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
        raise TypeError(f"CTimeInput attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CTimeInput")
    reject_html_attr_bindings(copied, _OWNED_ATTRS, "CTimeInput")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CTimeInput attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CTimeInput attrs cannot contain reserved runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CTimeInput attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in _OWNED_ATTRS:
            raise ValueError(f"CTimeInput attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CTimeInput(LibraryComponent):
    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CTimeInputValue | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        min: CTimeInputValue | None = None
        max: CTimeInputValue | None = None
        step: int = 60
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        autocomplete: str | None = None
        variant: CTimeInputVariant = "outline"
        size: CTimeInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_time_input_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = canonical_time("CTimeInput", "value", kwargs.value, optional=True)
        minimum = canonical_time("CTimeInput", "min", kwargs.min, optional=True)
        maximum = canonical_time("CTimeInput", "max", kwargs.max, optional=True)
        step = _positive_step(kwargs.step)
        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CTimeInput", "name", name)
        validate_html_id("CTimeInput", form_input)
        validate_html_id("CTimeInput", supplied_id)
        validate_optional_boolean("CTimeInput", "required", kwargs.required)
        validate_optional_boolean("CTimeInput", "disabled", kwargs.disabled)
        validate_optional_boolean("CTimeInput", "readonly", kwargs.readonly)
        validate_optional_boolean("CTimeInput", "invalid", kwargs.invalid)
        validate_optional_string("CTimeInput", "autocomplete", kwargs.autocomplete)
        validate_choice("CTimeInput", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CTimeInput", "size", kwargs.size, _SIZES)

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
                    f"CTimeInput inside CField cannot set Field-owned state: {', '.join(supplied_states)}."
                )
            field.register_control("CTimeInput")
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CTimeInput id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )

        public_id = supplied_id or field_control_id or f"cui-time-input-{self.id}"
        caller_attrs = _attrs(kwargs.attrs)
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CTimeInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CTimeInput inside CForm cannot target a different native form owner.")

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
            pop_html_attr(caller_attrs, "aria-describedby", component_name="CTimeInput"),
        )
        external_error_message = cast(
            "str | None",
            pop_html_attr(caller_attrs, "aria-errormessage", component_name="CTimeInput"),
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
        self._cui_time_input_data: dict[str, object] = {
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
        self._cui_time_input_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_time_input_data

    template = """
      <input
        class="cui-time-input"
        c-id="public_id"
        c-name="name"
        c-form="form"
        type="time"
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
        data-citry-ui-part="time-input"
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
          if (!(input instanceof HTMLInputElement) || input.type !== 'time') {
            throw new Error('[citry-ui] CTimeInput settled anatomy is invalid.');
          }
          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CTimeInput form-control runtime is unavailable.');
          const resolver = runtime.resolver(input, props, 'CTimeInput');
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

          const canonicalTime = value => {
            if (typeof value !== 'string') return null;
            const match = value.match(/^([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?$/);
            if (match === null) return null;
            const hour = Number(match[1]);
            const minute = Number(match[2]);
            const second = Number(match[3] ?? 0);
            return hour <= 23 && minute <= 59 && second <= 59 ? value : null;
          };
          const optionalTime = (name, fallback) => {
            const value = props[name];
            if (value === undefined) { resolver.clear(name); return fallback; }
            if (value === null) { resolver.clear(name); return null; }
            const valid = canonicalTime(value);
            if (valid !== null) { resolver.clear(name); return valid; }
            resolver.report(name, value);
            return previousConstraints[name];
          };
          const resolveConstraints = () => {
            const minimum = optionalTime('min', data.min);
            const maximum = optionalTime('max', data.max);
            const requestedStep = props.step === undefined ? data.step : props.step;
            const step = Number.isInteger(requestedStep) && requestedStep > 0
              ? requestedStep : previousConstraints.step;
            if (step === requestedStep) resolver.clear('step'); else resolver.report('step', requestedStep);
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
              const normalized = canonicalTime(requested);
              if (normalized === null) resolver.report('value', requested);
              else { controlled = true; current = normalized; resolver.clear('value'); }
            }
            clearNativeInvalid();
            render();
          });
          mutations.start(() => render());
          owned(() => input.setAttribute('data-citry-time-input-initialized', ''));
          render();

          return () => {
            invalidGeneration += 1;
            listeners.stop();
            mutations.stop();
            stopFieldset();
            reset();
            if (nativeInvalid) field?.setNativeInvalid(false);
            owned(() => input.removeAttribute('data-citry-time-input-initialized'));
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = ["CTimeInput", "CTimeInputSize", "CTimeInputValue", "CTimeInputVariant"]
