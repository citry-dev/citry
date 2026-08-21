"""Styled Field and native Input component family."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    get_html_attr,
    get_html_form_owner,
    merge_root_attrs,
    pop_html_attr,
    reject_html_attr_bindings,
)
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CFieldOrientation = Literal["vertical", "horizontal"]
CFieldDensity = Literal["default", "comfortable", "compact"]
CInputType = Literal["text", "email", "password", "search", "tel", "url"]
CInputVariant = Literal["outline", "filled", "plain"]
CInputSize = Literal["sm", "md", "lg"]


@dataclass(slots=True)
class _FieldRegistry:
    control_name: str | None = None
    supports_required: bool = True
    supports_readonly: bool = True

    def register(
        self,
        control_name: str,
        *,
        supports_required: bool = True,
        supports_readonly: bool = True,
    ) -> None:
        if self.control_name is not None:
            msg = f"CField accepts exactly one library control, but received {self.control_name} and {control_name}."
            raise ValueError(msg)
        self.control_name = control_name
        self.supports_required = supports_required
        self.supports_readonly = supports_readonly


class CFieldLabelSlotData:
    pass


class CFieldDefaultSlotData:
    control_attrs: dict[str, object]
    control_id: str
    label_id: str
    description_id: str
    error_id: str
    is_required: bool
    is_disabled: bool
    is_readonly: bool
    is_invalid: bool


class CFieldDescriptionSlotData:
    pass


class CFieldErrorSlotData:
    pass


class CField(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        control_id: str | None = None
        required: bool = False
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool = False
        orientation: CFieldOrientation = "vertical"
        density: CFieldDensity = "default"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        label: SlotInput[CFieldLabelSlotData]
        default: SlotInput[CFieldDefaultSlotData]
        description: SlotInput[CFieldDescriptionSlotData] | None = None
        error: SlotInput[CFieldErrorSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if self.inject(FIELD_CONTEXT_KEY, None) is not None:
            msg = "CField cannot be nested inside another CField."
            raise ValueError(msg)
        validate_html_id("CField", kwargs.control_id)
        validate_boolean("CField", "required", kwargs.required)
        validate_optional_boolean("CField", "disabled", kwargs.disabled)
        validate_optional_boolean("CField", "readonly", kwargs.readonly)
        validate_boolean("CField", "invalid", kwargs.invalid)
        validate_choice("CField", "orientation", kwargs.orientation, ("vertical", "horizontal"))
        validate_choice("CField", "density", kwargs.density, ("default", "comfortable", "compact"))
        reject_owned_attrs(
            kwargs.attrs,
            {
                "data-citry-field-initialized",
                "data-citry-field-root",
                "data-citry-ui-part",
                "data-density",
                "data-disabled",
                "data-invalid",
                "data-orientation",
                "data-readonly",
                "data-required",
                "id",
            },
            "CField",
        )

        form = self.inject(FORM_CONTEXT_KEY, None)
        local_disabled = kwargs.disabled if kwargs.disabled is not None else False
        disabled = bool(form.disabled) if form is not None else False
        disabled = disabled or local_disabled
        readonly = (
            kwargs.readonly if kwargs.readonly is not None else bool(form.readonly) if form is not None else False
        )
        control_id = kwargs.control_id or f"cui-field-{self.id}-control"
        field_id = f"{control_id}-field"
        label_id = f"{control_id}-label"
        description_id = f"{control_id}-description"
        error_id = f"{control_id}-error"
        has_description = "description" in self.raw_slots
        has_error = "error" in self.raw_slots
        registry = _FieldRegistry()
        self._field_registry = registry
        self._field_required = kwargs.required
        self._field_readonly = readonly
        described_by = merge_idrefs(
            description_id if has_description else None,
            error_id if kwargs.invalid and has_error else None,
        )
        control_attrs: dict[str, object] = {
            "id": control_id,
            "required": kwargs.required,
            "disabled": disabled,
            "readonly": readonly,
            "aria-invalid": "true" if kwargs.invalid else None,
            "aria-describedby": described_by,
            "aria-errormessage": error_id if kwargs.invalid and has_error else None,
            FIELD_CONTROL_MARKER: True,
        }
        self.provide(
            FIELD_CONTEXT_KEY,
            control_id=control_id,
            label_id=label_id,
            description_id=description_id,
            error_id=error_id,
            has_description=has_description,
            has_error=has_error,
            required=kwargs.required,
            disabled=disabled,
            readonly=readonly,
            invalid=kwargs.invalid,
            register_control=registry.register,
        )
        return {
            "field_id": field_id,
            "control_id": control_id,
            "label_id": label_id,
            "label_attrs": {"for": control_id},
            "description_id": description_id,
            "error_id": error_id,
            "control_attrs": control_attrs,
            "required": kwargs.required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": kwargs.invalid,
            "orientation": kwargs.orientation,
            "density": kwargs.density,
            "has_description": has_description,
            "has_error": has_error,
            "show_error": kwargs.invalid and has_error,
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            msg = "CField completed without a render result."
            raise RuntimeError(msg)
        registry = self._field_registry
        if registry.control_name is None:
            return
        if self._field_required and not registry.supports_required:
            msg = f"CField required=True is not supported by its {registry.control_name} control."
            raise ValueError(msg)
        if self._field_readonly and not registry.supports_readonly:
            msg = f"CField readonly=True is not supported by its {registry.control_name} control."
            raise ValueError(msg)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        form = self.inject(FORM_CONTEXT_KEY, None)
        control_id = kwargs.control_id or f"cui-field-{self.id}-control"
        return {
            "required": kwargs.required,
            "disabled": kwargs.disabled if kwargs.disabled is not None else False,
            "readonly": kwargs.readonly
            if kwargs.readonly is not None
            else bool(form.readonly)
            if form is not None
            else False,
            "inheritsReadonly": kwargs.readonly is None,
            "invalid": kwargs.invalid,
            "orientation": kwargs.orientation,
            "density": kwargs.density,
            "controlId": control_id,
            "descriptionId": f"{control_id}-description",
            "errorId": f"{control_id}-error",
            "hasDescription": "description" in self.raw_slots,
            "hasError": "error" in self.raw_slots,
        }

    template = """
      <div
        class="cui-field"
        c-id="field_id"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-orientation="orientation"
        c-data-density="density"
        data-citry-field-root
        c-bind="attrs"
        data-citry-ui-part="field"
      >
        <label
          c-id="label_id"
          c-bind="label_attrs"
          data-citry-ui-part="label"
        >
          <c-slot name="label" required />
          <span
            class="cui-field__required"
            aria-hidden="true"
            c-hidden="not required"
            data-citry-ui-part="required-indicator"
          >
            *
          </span>
        </label>
        <div data-citry-ui-part="control">
          <c-slot
            c-control_attrs="control_attrs"
            c-control_id="control_id"
            c-label_id="label_id"
            c-description_id="description_id"
            c-error_id="error_id"
            c-is_required="required"
            c-is_disabled="disabled"
            c-is_readonly="readonly"
            c-is_invalid="invalid"
            required
          />
        </div>
        <c-if cond="has_description">
          <div
            c-id="description_id"
            data-citry-ui-part="description"
          >
            <c-slot name="description" />
          </div>
        </c-if>
        <div
          c-id="error_id"
          aria-live="polite"
          c-hidden="not show_error"
          data-citry-ui-part="error"
        >
          <c-if cond="has_error">
            <c-slot name="error" />
          </c-if>
        </div>
      </div>
    """

    js = """
      $component({
        props: {
          required: {},
          disabled: {},
          readonly: {},
          invalid: {},
          orientation: {},
          density: {},
        },
        init: ({ els, data, props, effect, reactive, provide, inject }) => {
          const root = els[0];
          const requiredIndicator = root.querySelector(
            ':scope > [data-citry-ui-part="label"] > [data-citry-ui-part="required-indicator"]',
          );
          // Controls may expose parts with the same public names. Restrict the
          // lookup to this Field's direct status node so nested component
          // internals are never mistaken for Field-owned UI.
          const error = root.querySelector(':scope > [data-citry-ui-part="error"]');
          const controls = root.querySelectorAll('[data-citry-field-control]');
          if (controls.length !== 1) {
            throw new Error(
              `[citry-ui] CField requires exactly one marked control, but found ${controls.length}.`,
            );
          }
          const control = controls[0];
          const initialSupportsRequired = control.getAttribute(
            "data-citry-field-supports-required",
          ) !== "false";
          const initialSupportsReadonly = control.getAttribute(
            "data-citry-field-supports-readonly",
          ) !== "false";
          const form = inject(Symbol.for("citry-ui:form"), null);
          const allowedValues = {
            orientation: ["vertical", "horizontal"],
            density: ["default", "comfortable", "compact"],
          };
          const invalidEpisodes = new Map();
          let externalInvalid = data.invalid;
          let capabilityGeneration = 0;
          let activeCapabilityGeneration = null;

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CField ${name} received invalid client value ${describedValue}; `
                + "using the server-rendered fallback.",
              root,
            );
          };
          const reportUnsupported = (name) => {
            const episode = `capability:${name}`;
            const fingerprint = "unsupported:true";
            if (invalidEpisodes.get(episode) === fingerprint) {
              return;
            }
            invalidEpisodes.set(episode, fingerprint);
            console.error(
              `[citry-ui] CField ${name}=true is not supported by its registered control; using false.`,
              root,
            );
          };
          const resolveBoolean = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const context = reactive({
            controlId: data.controlId,
            descriptionId: data.descriptionId,
            errorId: data.errorId,
            hasDescription: data.hasDescription,
            hasError: data.hasError,
            required: data.required,
            disabled: data.disabled,
            readonly: data.readonly,
            invalid: data.invalid,
            nativeInvalid: false,
            supportsRequired: initialSupportsRequired,
            supportsReadonly: initialSupportsReadonly,
            registerCapabilities(capabilities) {
              const generation = ++capabilityGeneration;
              activeCapabilityGeneration = generation;
              context.supportsRequired = capabilities.required !== false;
              context.supportsReadonly = capabilities.readonly !== false;
              return () => {
                if (activeCapabilityGeneration !== generation) {
                  return;
                }
                activeCapabilityGeneration = null;
                context.supportsRequired = true;
                context.supportsReadonly = true;
              };
            },
            setNativeInvalid(value) {
              context.nativeInvalid = Boolean(value);
              applyInvalid();
            },
          });
          provide(Symbol.for("citry-ui:field"), context);

          const applyInvalid = () => {
            const invalid = externalInvalid || context.nativeInvalid;
            context.invalid = invalid;
            root.toggleAttribute("data-invalid", invalid);
            error.hidden = !(invalid && context.hasError);
          };
          effect(() => {
            const requestedRequired = resolveBoolean("required", data.required);
            const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.readonly;
            // CForm uses a native disabled fieldset, so its disabled state
            // must win over a descendant's local configuration.
            const disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
            const requestedReadonly = resolveBoolean("readonly", readonlyFallback);
            const required = requestedRequired && context.supportsRequired;
            const readonly = requestedReadonly && context.supportsReadonly;
            if (requestedRequired && !context.supportsRequired) {
              reportUnsupported("required");
            } else {
              invalidEpisodes.delete("capability:required");
            }
            if (requestedReadonly && !context.supportsReadonly) {
              reportUnsupported("readonly");
            } else {
              invalidEpisodes.delete("capability:readonly");
            }
            externalInvalid = resolveBoolean("invalid", data.invalid);
            const orientation = resolveChoice("orientation");
            const density = resolveChoice("density");

            context.required = required;
            context.disabled = disabled;
            context.readonly = readonly;
            root.toggleAttribute("data-required", required);
            root.toggleAttribute("data-disabled", disabled);
            root.toggleAttribute("data-readonly", readonly);
            root.dataset.orientation = orientation;
            root.dataset.density = density;
            requiredIndicator.hidden = !required;
            applyInvalid();
          });
          root.setAttribute("data-citry-field-initialized", "");

          return () => {
            root.removeAttribute("data-citry-field-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


class CInput(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: str | None = None
        type: CInputType = "text"
        id: str | None = None
        value: str | None = None
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        autocomplete: str | None = None
        inputmode: str | None = None
        placeholder: str | None = None
        variant: CInputVariant = "outline"
        size: CInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if kwargs.name is not None:
            validate_non_empty_string("CInput", "name", kwargs.name)
        validate_choice("CInput", "type", kwargs.type, ("text", "email", "password", "search", "tel", "url"))
        validate_html_id("CInput", kwargs.id)
        validate_optional_string("CInput", "value", kwargs.value)
        validate_optional_boolean("CInput", "required", kwargs.required)
        validate_optional_boolean("CInput", "disabled", kwargs.disabled)
        validate_optional_boolean("CInput", "readonly", kwargs.readonly)
        validate_optional_boolean("CInput", "invalid", kwargs.invalid)
        validate_optional_string("CInput", "autocomplete", kwargs.autocomplete)
        validate_optional_string("CInput", "inputmode", kwargs.inputmode)
        validate_optional_string("CInput", "placeholder", kwargs.placeholder)
        validate_choice("CInput", "variant", kwargs.variant, ("outline", "filled", "plain"))
        validate_choice("CInput", "size", kwargs.size, ("sm", "md", "lg"))
        reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-invalid",
                "autocomplete",
                "data-citry-input-initialized",
                FIELD_CONTROL_MARKER,
                "data-citry-ui-part",
                "data-disabled",
                "data-invalid",
                "data-readonly",
                "data-required",
                "data-size",
                "data-variant",
                "disabled",
                "id",
                "inputmode",
                "name",
                "placeholder",
                "readonly",
                "required",
                "type",
                "value",
            },
            "CInput",
        )
        reject_html_attr_bindings(kwargs.attrs, {"form"}, "CInput")

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
                msg = f"CInput inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            field.register_control("CInput")
        if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
            msg = (
                f"CInput id {kwargs.id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CInput.id."
            )
            raise ValueError(msg)
        for html_attribute in ("form", "aria-describedby", "aria-errormessage"):
            get_html_attr(
                kwargs.attrs or {},
                html_attribute,
                component_name="CInput",
            )
        caller_attrs = merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style)
        form_owner = get_html_form_owner(
            caller_attrs,
            component_name="CInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            msg = "CInput inside CForm cannot target a different native form owner."
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
        input_id = kwargs.id or field_control_id or f"cui-input-{self.id}"
        external_described_by = pop_html_attr(
            caller_attrs,
            "aria-describedby",
            component_name="CInput",
        )
        external_error_message = pop_html_attr(
            caller_attrs,
            "aria-errormessage",
            component_name="CInput",
        )
        self._input_external_described_by = external_described_by
        self._input_external_error_message = external_error_message
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        return {
            "id": input_id,
            "name": kwargs.name,
            "type": kwargs.type,
            "value": kwargs.value,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "autocomplete": kwargs.autocomplete,
            "inputmode": kwargs.inputmode,
            "placeholder": kwargs.placeholder,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "field_control": field is not None,
            "attrs": caller_attrs,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        return {
            "value": kwargs.value,
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
            "variant": kwargs.variant,
            "size": kwargs.size,
            "externalDescribedBy": self._input_external_described_by,
            "externalErrorMessage": self._input_external_error_message,
        }

    template = """
      <input
        class="cui-input"
        c-id="id"
        c-name="name"
        c-type="type"
        c-value="value"
        c-required="required"
        c-disabled="disabled"
        c-readonly="readonly"
        c-aria-invalid="aria_invalid"
        c-aria-describedby="aria_describedby"
        c-aria-errormessage="aria_errormessage"
        c-autocomplete="autocomplete"
        c-inputmode="inputmode"
        c-placeholder="placeholder"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-data-citry-field-control="field_control"
        c-bind="attrs"
        data-citry-ui-part="input"
      />
    """

    js = r"""
      $component({
        props: {
          value: {},
          required: {},
          disabled: {},
          readonly: {},
          invalid: {},
          variant: {},
          size: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const input = els[0];
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const allowedValues = {
            variant: ["outline", "filled", "plain"],
            size: ["sm", "md", "lg"],
          };
          const invalidEpisodes = new Map();
          let nativeInvalid = false;
          let controlled = false;
          let controlledValue = null;
          let composing = false;
          const resetTimers = new Set();

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CInput ${name} received invalid client value ${describedValue}; `
                + "using the previous valid or server-rendered fallback.",
              input,
            );
          };
          const resolveBoolean = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const reportFieldOwned = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `field:${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CInput ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describedValue}.`,
              input,
            );
          };
          const idrefs = (...values) => {
            const result = [];
            values.forEach((value) => {
              if (typeof value !== "string") {
                return;
              }
              value.split(/\s+/).filter(Boolean).forEach((token) => {
                if (!result.includes(token)) {
                  result.push(token);
                }
              });
            });
            return result.join(" ") || null;
          };
          const syncRelationships = (invalid) => {
            const describedBy = idrefs(
              field?.hasDescription ? field.descriptionId : null,
              invalid && field?.hasError ? field.errorId : null,
              data.externalDescribedBy,
            );
            const errorMessage = invalid
              ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
              : null;
            if (describedBy) {
              input.setAttribute("aria-describedby", describedBy);
            } else {
              input.removeAttribute("aria-describedby");
            }
            if (errorMessage) {
              input.setAttribute("aria-errormessage", errorMessage);
            } else {
              input.removeAttribute("aria-errormessage");
            }
          };
          const applyState = () => {
            let required;
            let disabled;
            let readonly;
            let externalInvalid;
            if (field) {
              ["required", "disabled", "readonly", "invalid"].forEach((name) => {
                if (props[name] !== undefined) {
                  reportFieldOwned(name, props[name]);
                } else {
                  invalidEpisodes.delete(name);
                }
              });
              required = field.required;
              disabled = field.disabled;
              readonly = field.readonly;
              externalInvalid = field.invalid;
            } else {
              required = resolveBoolean("required", data.required);
              // A native disabled CForm fieldset always wins.
              disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
              const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.readonly;
              readonly = resolveBoolean("readonly", readonlyFallback);
              externalInvalid = resolveBoolean("invalid", data.invalid);
            }
            const invalid = externalInvalid || nativeInvalid;
            const variant = resolveChoice("variant");
            const size = resolveChoice("size");

            input.required = required;
            input.disabled = disabled;
            input.readOnly = readonly;
            input.toggleAttribute("data-required", required);
            input.toggleAttribute("data-disabled", disabled);
            input.toggleAttribute("data-readonly", readonly);
            input.toggleAttribute("data-invalid", invalid);
            input.dataset.variant = variant;
            input.dataset.size = size;
            if (invalid) {
              input.setAttribute("aria-invalid", "true");
            } else {
              input.removeAttribute("aria-invalid");
            }
            syncRelationships(invalid);
          };
          const clearNativeInvalidWhenValid = () => {
            if (!nativeInvalid || !input.validity.valid) {
              return;
            }
            nativeInvalid = false;
            field?.setNativeInvalid(false);
            applyState();
          };
          const onInvalid = () => {
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const onInput = () => {
            clearNativeInvalidWhenValid();
            if (controlled && !composing) {
              queueMicrotask(() => {
                if (controlled && !composing) {
                  input.value = controlledValue;
                }
              });
            }
          };
          const onChange = () => {
            clearNativeInvalidWhenValid();
          };
          const onCompositionStart = () => {
            composing = true;
          };
          const onCompositionEnd = () => {
            composing = false;
            if (controlled) {
              queueMicrotask(() => {
                if (controlled && !composing) {
                  input.value = controlledValue;
                }
              });
            }
          };
          const onReset = (event) => {
            const resetTimer = setTimeout(() => {
              resetTimers.delete(resetTimer);
              if (event.defaultPrevented) {
                return;
              }
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              if (controlled) {
                input.value = controlledValue;
              }
              applyState();
            }, 0);
            resetTimers.add(resetTimer);
          };
          const nativeForm = input.form;

          input.addEventListener("invalid", onInvalid);
          input.addEventListener("input", onInput);
          input.addEventListener("change", onChange);
          input.addEventListener("compositionstart", onCompositionStart);
          input.addEventListener("compositionend", onCompositionEnd);
          nativeForm?.addEventListener("reset", onReset);
          effect(() => {
            applyState();
            clearNativeInvalidWhenValid();
          });
          effect(() => {
            const value = props.value;
            if (value === undefined) {
              controlled = false;
              invalidEpisodes.delete("value");
              return;
            }
            if (typeof value !== "string") {
              reportInvalid("value", value);
              return;
            }
            invalidEpisodes.delete("value");
            controlled = true;
            controlledValue = value;
            if (!composing) {
              input.value = value;
            }
          });
          input.setAttribute("data-citry-input-initialized", "");

          return () => {
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("input", onInput);
            input.removeEventListener("change", onChange);
            input.removeEventListener("compositionstart", onCompositionStart);
            input.removeEventListener("compositionend", onCompositionEnd);
            nativeForm?.removeEventListener("reset", onReset);
            resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
            resetTimers.clear();
            if (nativeInvalid) {
              field?.setNativeInvalid(false);
            }
            input.removeAttribute("data-citry-input-initialized");
          };
        },
      });
    """

    css_file = "runtime.c-input.min.css"


__all__ = [
    "CField",
    "CFieldDefaultSlotData",
    "CFieldDensity",
    "CFieldDescriptionSlotData",
    "CFieldErrorSlotData",
    "CFieldLabelSlotData",
    "CFieldOrientation",
    "CInput",
    "CInputSize",
    "CInputType",
    "CInputVariant",
]
