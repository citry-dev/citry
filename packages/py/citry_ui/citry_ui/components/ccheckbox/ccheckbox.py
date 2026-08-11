"""Styled native Checkbox component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    get_html_attr,
    get_html_form_owner,
    merge_root_attrs,
    pop_html_attr,
)
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_optional_boolean

CCheckboxVariant = Literal["solid", "outline"]
CCheckboxSize = Literal["sm", "md", "lg"]
CCheckboxLabelPos = Literal["start", "end"]

_VARIANTS = ("solid", "outline")
_SIZES = ("sm", "md", "lg")
_LABEL_POSITIONS = ("start", "end")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset({"x-bind", "x-html", "x-model", "x-modelable", "x-text"})
_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-checked",
        "data-citry-checkbox-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-indeterminate",
        "data-invalid",
        "data-label-pos",
        "data-required",
        "data-size",
        "data-variant",
        "for",
        "role",
        "tabindex",
    }
)
_INPUT_OWNED_ATTRS = frozenset(
    {
        "aria-checked",
        "aria-disabled",
        "aria-hidden",
        "aria-invalid",
        "aria-readonly",
        "aria-required",
        "checked",
        "data-citry-field-supports-readonly",
        "data-citry-field-supports-required",
        FIELD_CONTROL_MARKER,
        "data-citry-ui-part",
        "disabled",
        "id",
        "name",
        "readonly",
        "required",
        "role",
        "type",
        "value",
    }
)
_INPUT_DYNAMIC_OWNED_ATTRS = _INPUT_OWNED_ATTRS | {
    "aria-describedby",
    "aria-errormessage",
    "aria-label",
    "aria-labelledby",
    "form",
}


class CCheckboxDefaultSlotData:
    pass


class CCheckboxDescriptionSlotData:
    pass


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CCheckbox {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CCheckbox could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _canonical_string(input_name: str, value: object, *, allow_none: bool) -> str | None:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        if allow_none:
            return None
        msg = f"CCheckbox {input_name} must be a string."
        raise TypeError(msg)
    canonical = plain.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in canonical:
        msg = f"CCheckbox {input_name} cannot contain U+0000."
        raise ValueError(msg)
    return canonical


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CCheckbox {input_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)
    return plain


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CCheckbox {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(
    input_name: str,
    attrs: dict[str, object],
    *,
    owned: frozenset[str],
    dynamic_owned: frozenset[str] | None = None,
) -> None:
    component_name = f"CCheckbox {input_name}"
    reject_owned_attrs(attrs, owned, component_name)
    dynamic_targets = dynamic_owned or owned
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"{component_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in dynamic_targets:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _extract_naming_attr(attrs: dict[str, object], name: str) -> str | None:
    raw = pop_html_attr(attrs, name, component_name="CCheckbox")
    if raw is None or raw is False:
        return None
    plain = _plain_optional_string(name, raw)
    if plain is None or not plain.strip():
        msg = f"CCheckbox {name} must be non-empty when supplied."
        raise ValueError(msg)
    attrs[name] = plain
    return plain


class CCheckbox(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: str | None = None
        value: str = "on"
        id: str | None = None
        checked: bool = False
        indeterminate: bool = False
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        variant: CCheckboxVariant = "solid"
        size: CCheckboxSize = "md"
        label_pos: CCheckboxLabelPos = "end"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCheckboxDefaultSlotData] | None = None
        description: SlotInput[CCheckboxDescriptionSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        name = _canonical_string("name", kwargs.name, allow_none=True)
        if name == "":
            msg = "CCheckbox name must be non-empty when supplied."
            raise ValueError(msg)
        value = _canonical_string("value", kwargs.value, allow_none=False)
        element_id = _canonical_string("id", kwargs.id, allow_none=True)
        if element_id is not None and (not element_id or any(character in "\t\n\f\r " for character in element_id)):
            msg = "CCheckbox id must be non-empty and cannot contain ASCII whitespace."
            raise ValueError(msg)
        validate_boolean("CCheckbox", "checked", kwargs.checked)
        validate_boolean("CCheckbox", "indeterminate", kwargs.indeterminate)
        validate_optional_boolean("CCheckbox", "required", kwargs.required)
        validate_optional_boolean("CCheckbox", "disabled", kwargs.disabled)
        validate_optional_boolean("CCheckbox", "invalid", kwargs.invalid)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        label_pos = _plain_choice("label_pos", kwargs.label_pos, _LABEL_POSITIONS)

        attrs = _copy_attrs("attrs", kwargs.attrs)
        input_attrs = _copy_attrs("input_attrs", kwargs.input_attrs)
        _validate_attrs("attrs", attrs, owned=_ROOT_OWNED_ATTRS)
        _validate_attrs(
            "input_attrs",
            input_attrs,
            owned=_INPUT_OWNED_ATTRS,
            dynamic_owned=_INPUT_DYNAMIC_OWNED_ATTRS,
        )
        for html_attribute in (
            "form",
            "aria-label",
            "aria-labelledby",
            "aria-describedby",
            "aria-errormessage",
        ):
            get_html_attr(input_attrs, html_attribute, component_name="CCheckbox")

        has_label = "default" in self.raw_slots
        has_description = "description" in self.raw_slots
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None and (has_label or has_description):
            msg = "CCheckbox inside CField cannot supply default or description slots; CField owns that content."
            raise ValueError(msg)
        if field is not None:
            supplied_state = [
                state_name
                for state_name, state_value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("invalid", kwargs.invalid),
                )
                if state_value is not None
            ]
            if supplied_state:
                names = ", ".join(supplied_state)
                msg = f"CCheckbox inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            field.register_control(
                "CCheckbox",
                supports_required=True,
                supports_readonly=False,
            )

        aria_label = _extract_naming_attr(input_attrs, "aria-label")
        aria_labelledby = _extract_naming_attr(input_attrs, "aria-labelledby")
        if aria_label is not None and aria_labelledby is not None:
            msg = "CCheckbox label-free usage accepts either aria-label or aria-labelledby, not both."
            raise ValueError(msg)
        if (has_label or field is not None) and (aria_label is not None or aria_labelledby is not None):
            msg = "CCheckbox cannot override its visible default or CField label with ARIA naming."
            raise ValueError(msg)
        if not has_label and field is None and aria_label is None and aria_labelledby is None:
            msg = "CCheckbox without a default slot or CField requires aria-label or aria-labelledby in input_attrs."
            raise ValueError(msg)

        field_control_id = str(field.control_id) if field is not None else None
        if field_control_id is not None and element_id is not None and element_id != field_control_id:
            msg = (
                f"CCheckbox id {element_id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CCheckbox.id."
            )
            raise ValueError(msg)
        input_id = element_id or field_control_id or f"cui-checkbox-{self.id}"

        root_attrs = merge_root_attrs(attrs, kwargs.class_, kwargs.style)
        form_owner = get_html_form_owner(
            input_attrs,
            component_name="CCheckbox",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            msg = "CCheckbox inside CForm cannot target a different native form owner."
            raise ValueError(msg)

        external_described_by = pop_html_attr(
            input_attrs,
            "aria-describedby",
            component_name="CCheckbox",
        )
        external_error_message = pop_html_attr(
            input_attrs,
            "aria-errormessage",
            component_name="CCheckbox",
        )
        self._checkbox_external_described_by = external_described_by
        self._checkbox_external_error_message = external_error_message
        self._checkbox_value = value

        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            invalid = bool(field.invalid)
        else:
            required = kwargs.required if kwargs.required is not None else False
            local_disabled = kwargs.disabled if kwargs.disabled is not None else False
            disabled = (bool(form.disabled) if form is not None else False) or local_disabled
            invalid = kwargs.invalid if kwargs.invalid is not None else False

        description_id = f"{input_id}-description"
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            description_id if has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        self._checkbox_description_id = description_id
        self._checkbox_has_description = has_description
        return {
            "id": input_id,
            "name": name,
            "value": value,
            "checked": kwargs.checked,
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "variant": variant,
            "size": size,
            "label_pos": label_pos,
            "has_label": has_label,
            "has_description": has_description,
            "has_body": has_label or has_description,
            "label_attrs": {"for": input_id},
            "description_id": description_id,
            "field_control": field is not None,
            "field_supports_required": "true" if field is not None else None,
            "field_supports_readonly": "false" if field is not None else None,
            "attrs": root_attrs,
            "input_attrs": input_attrs,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        field = self.inject(FIELD_CONTEXT_KEY, None)
        return {
            "value": self._checkbox_value,
            "checked": kwargs.checked,
            "indeterminate": kwargs.indeterminate,
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
            "invalid": bool(field.invalid)
            if field is not None
            else kwargs.invalid
            if kwargs.invalid is not None
            else False,
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "labelPos": _plain_choice("label_pos", kwargs.label_pos, _LABEL_POSITIONS),
            "descriptionId": self._checkbox_description_id,
            "hasDescription": self._checkbox_has_description,
            "externalDescribedBy": self._checkbox_external_described_by,
            "externalErrorMessage": self._checkbox_external_error_message,
        }

    template = """
      <span
        class="cui-checkbox"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-data-label-pos="label_pos"
        c-bind="attrs"
        data-citry-ui-part="checkbox"
      >
        <input
          class="cui-checkbox__input"
          c-id="id"
          c-name="name"
          type="checkbox"
          c-value="value"
          c-checked="checked"
          c-required="required"
          c-disabled="disabled"
          c-aria-invalid="aria_invalid"
          c-aria-describedby="aria_describedby"
          c-aria-errormessage="aria_errormessage"
          c-data-citry-field-control="field_control"
          c-data-citry-field-supports-required="field_supports_required"
          c-data-citry-field-supports-readonly="field_supports_readonly"
          c-bind="input_attrs"
          data-citry-ui-part="input"
        />
        <c-if cond="has_body">
          <span class="cui-checkbox__body">
            <c-if cond="has_label">
              <label
                c-bind="label_attrs"
                data-citry-ui-part="label"
              >
                <c-slot />
              </label>
            </c-if>
            <c-if cond="has_description">
              <span
                c-id="description_id"
                data-citry-ui-part="description"
              >
                <c-slot name="description" />
              </span>
            </c-if>
          </span>
        </c-if>
      </span>
    """

    js = r"""
      $component({
        props: {
          checked: {},
          indeterminate: {},
          value: {},
          required: {},
          disabled: {},
          invalid: {},
          variant: {},
          size: {},
          label_pos: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
          if (!(input instanceof HTMLInputElement) || input.type !== "checkbox") {
            throw new Error("[citry-ui] CCheckbox requires one direct native checkbox input.");
          }
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const handoffKey = Symbol.for("citry-ui:checkbox-handoff");
          const allowedValues = {
            variant: ["solid", "outline"],
            size: ["sm", "md", "lg"],
            label_pos: ["start", "end"],
          };
          const invalidEpisodes = new Map();
          const resetTimers = new Set();
          let nativeInvalid = false;
          let controlledChecked = false;
          let controlledCheckedValue = false;
          let controlledIndeterminate = false;
          let controlledIndeterminateValue = false;
          let activationPending = false;
          let reconcileTimer = null;

          const handoff = root[handoffKey];
          delete root[handoffKey];
          // Correlated rerenders replace the initializer but may retain this root.
          // Restore browser-owned current state after HTML updates reset defaults.
          if (handoff) {
            input.checked = Boolean(handoff.checked);
            input.indeterminate = Boolean(handoff.indeterminate);
          } else {
            input.indeterminate = data.indeterminate;
          }

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
              `[citry-ui] CCheckbox ${name} received invalid client value ${describedValue}; `
                + "using the documented fallback.",
              root,
            );
          };
          const reportFieldOwned = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `field:${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CCheckbox ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describedValue}.`,
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
          const resolveChoice = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const canonicalizeValue = (value) => {
            if (typeof value !== "string" || value.includes("\0")) {
              return null;
            }
            return value.replace(/\r\n?/g, "\n");
          };
          const resolveValue = () => {
            if (props.value === undefined) {
              invalidEpisodes.delete("value");
              return data.value;
            }
            const canonical = canonicalizeValue(props.value);
            if (canonical === null) {
              reportInvalid("value", props.value);
              return data.value;
            }
            invalidEpisodes.delete("value");
            return canonical;
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
              data.hasDescription ? data.descriptionId : null,
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
          const syncNativeMirrors = () => {
            root.toggleAttribute("data-checked", input.checked);
            root.toggleAttribute("data-indeterminate", input.indeterminate);
          };
          const applyState = () => {
            let required;
            let disabled;
            let externalInvalid;
            if (field) {
              ["required", "disabled", "invalid"].forEach((name) => {
                if (props[name] !== undefined) {
                  reportFieldOwned(name, props[name]);
                } else {
                  invalidEpisodes.delete(name);
                }
              });
              required = field.required;
              disabled = field.disabled;
              externalInvalid = field.invalid;
            } else {
              required = resolveBoolean("required", data.required);
              disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
              externalInvalid = resolveBoolean("invalid", data.invalid);
            }
            const invalid = externalInvalid || nativeInvalid;
            const variant = resolveChoice("variant", data.variant);
            const size = resolveChoice("size", data.size);
            const labelPos = resolveChoice("label_pos", data.labelPos);
            const value = resolveValue();

            input.required = required;
            input.disabled = disabled;
            if (input.value !== value) {
              input.value = value;
            }
            root.toggleAttribute("data-required", required);
            root.toggleAttribute("data-disabled", input.matches(":disabled"));
            root.toggleAttribute("data-invalid", invalid);
            root.dataset.variant = variant;
            root.dataset.size = size;
            root.dataset.labelPos = labelPos;
            if (invalid) {
              input.setAttribute("aria-invalid", "true");
            } else {
              input.removeAttribute("aria-invalid");
            }
            syncRelationships(invalid);
            syncNativeMirrors();
          };
          const clearNativeInvalidWhenValid = () => {
            if (!nativeInvalid || !input.validity.valid) {
              return;
            }
            nativeInvalid = false;
            field?.setNativeInvalid(false);
            applyState();
          };
          const applyControlledBoolean = (name, property) => {
            const value = props[name];
            const controlledName = name === "checked" ? "controlledChecked" : "controlledIndeterminate";
            if (value === undefined) {
              invalidEpisodes.delete(name);
              if (controlledName === "controlledChecked") {
                controlledChecked = false;
              } else {
                controlledIndeterminate = false;
              }
              return;
            }
            if (typeof value !== "boolean") {
              reportInvalid(name, value);
              const isControlled = controlledName === "controlledChecked"
                ? controlledChecked
                : controlledIndeterminate;
              const retained = controlledName === "controlledChecked"
                ? controlledCheckedValue
                : controlledIndeterminateValue;
              if (isControlled && !activationPending && input[property] !== retained) {
                input[property] = retained;
              }
              return;
            }
            invalidEpisodes.delete(name);
            if (controlledName === "controlledChecked") {
              controlledChecked = true;
              controlledCheckedValue = value;
            } else {
              controlledIndeterminate = true;
              controlledIndeterminateValue = value;
            }
            if (!activationPending && input[property] !== value) {
              input[property] = value;
            }
          };
          const applyLatestControlled = () => {
            applyControlledBoolean("checked", "checked");
            applyControlledBoolean("indeterminate", "indeterminate");
            syncNativeMirrors();
          };
          const scheduleReconcile = () => {
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            reconcileTimer = setTimeout(() => {
              reconcileTimer = null;
              activationPending = false;
              applyLatestControlled();
              clearNativeInvalidWhenValid();
              applyState();
            }, 0);
          };
          const onInvalid = () => {
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const onInput = () => {
            // A microtask can run between native input and change. Keep the
            // browser-produced state visible to both consumer handlers.
            activationPending = true;
            syncNativeMirrors();
            scheduleReconcile();
            if (!controlledChecked) {
              clearNativeInvalidWhenValid();
            }
          };
          const onChange = () => {
            if (!activationPending) {
              activationPending = true;
              scheduleReconcile();
            }
            syncNativeMirrors();
            if (!controlledChecked) {
              clearNativeInvalidWhenValid();
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
              activationPending = false;
              applyLatestControlled();
              applyState();
            }, 0);
            resetTimers.add(resetTimer);
          };
          const unregisterCapabilities = field?.registerCapabilities({
            required: true,
            readonly: false,
          });
          const nativeForm = input.form;
          const ancestorFieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (ancestor instanceof HTMLFieldSetElement) {
              ancestorFieldsets.push(ancestor);
            }
          }
          // Native fieldset disabledness does not change input.disabled. Watch
          // only the resolved ancestor fieldsets so the public mirror follows
          // the browser's effective :disabled state.
          const fieldsetObserver = ancestorFieldsets.length > 0
            ? new MutationObserver(() => applyState())
            : null;
          ancestorFieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
            attributes: true,
            attributeFilter: ["disabled"],
          }));

          input.addEventListener("invalid", onInvalid);
          input.addEventListener("input", onInput);
          input.addEventListener("change", onChange);
          nativeForm?.addEventListener("reset", onReset);
          effect(() => {
            applyState();
            applyLatestControlled();
            if (!activationPending) {
              clearNativeInvalidWhenValid();
            }
          });
          root.setAttribute("data-citry-checkbox-initialized", "");

          return () => {
            root[handoffKey] = {
              checked: input.checked,
              indeterminate: input.indeterminate,
            };
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("input", onInput);
            input.removeEventListener("change", onChange);
            nativeForm?.removeEventListener("reset", onReset);
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
            resetTimers.clear();
            fieldsetObserver?.disconnect();
            unregisterCapabilities?.();
            if (nativeInvalid) {
              field?.setNativeInvalid(false);
            }
            root.removeAttribute("data-citry-checkbox-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-checkbox) {
          --_cui-checkbox-background: var(--cui-checkbox-background, Canvas);
          --_cui-checkbox-foreground: var(--cui-checkbox-foreground, CanvasText);
          --_cui-checkbox-border-color: var(
            --cui-checkbox-border-color,
            color-mix(in srgb, CanvasText 42%, transparent)
          );
          --_cui-checkbox-hover-border-color: var(
            --cui-checkbox-hover-border-color,
            color-mix(in srgb, CanvasText 72%, transparent)
          );
          --_cui-checkbox-active-color: var(
            --cui-checkbox-active-color,
            light-dark(#2563eb, #60a5fa)
          );
          --_cui-checkbox-indicator-color: var(
            --cui-checkbox-indicator-color,
            light-dark(white, #0b1220)
          );
          --_cui-checkbox-focus-color: var(--cui-checkbox-focus-color, Highlight);
          --_cui-checkbox-invalid-color: var(
            --cui-checkbox-invalid-color,
            light-dark(#b42318, #f97066)
          );
          --_cui-checkbox-disabled-opacity: var(--cui-checkbox-disabled-opacity, 0.55);
          --_cui-checkbox-control-size: var(--cui-checkbox-control-size, 1.125rem);
          --_cui-checkbox-radius: var(--cui-checkbox-radius, 0.3rem);
          --_cui-checkbox-gap: var(--cui-checkbox-gap, 0.625rem);
          --_cui-checkbox-description-color: var(
            --cui-checkbox-description-color,
            color-mix(in srgb, CanvasText 68%, transparent)
          );
          --_cui-checkbox-description-gap: var(--cui-checkbox-description-gap, 0.2rem);

          display: inline-flex;
          align-items: flex-start;
          gap: var(--_cui-checkbox-gap);
          min-inline-size: 0;
          color: var(--_cui-checkbox-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
          font-size: 1rem;
          line-height: 1.4;
          vertical-align: middle;
        }

        :where(.cui-checkbox[data-label-pos="start"]) {
          flex-direction: row-reverse;
        }

        :where(.cui-checkbox[data-size="sm"]) {
          --_cui-checkbox-control-size: var(--cui-checkbox-control-size, 1rem);
          --_cui-checkbox-gap: var(--cui-checkbox-gap, 0.5rem);

          font-size: 0.875rem;
        }

        :where(.cui-checkbox[data-size="lg"]) {
          --_cui-checkbox-control-size: var(--cui-checkbox-control-size, 1.25rem);
          --_cui-checkbox-gap: var(--cui-checkbox-gap, 0.75rem);

          font-size: 1.0625rem;
        }

        :where(.cui-checkbox__input) {
          appearance: none;
          display: grid;
          flex: 0 0 auto;
          place-content: center;
          box-sizing: border-box;
          inline-size: var(--_cui-checkbox-control-size);
          block-size: var(--_cui-checkbox-control-size);
          margin: 0.15em 0 0;
          border: 1px solid var(--_cui-checkbox-border-color);
          border-radius: var(--_cui-checkbox-radius);
          background: var(--_cui-checkbox-background);
          color: var(--_cui-checkbox-indicator-color);
          cursor: pointer;
          font: inherit;
          transition: border-color 120ms ease, background-color 120ms ease;
        }

        :where(.cui-checkbox__input)::after {
          content: "";
          display: block;
          box-sizing: border-box;
          opacity: 0;
        }

        :where(.cui-checkbox__input:checked) {
          border-color: var(--_cui-checkbox-active-color);
          background: var(--_cui-checkbox-active-color);
        }

        :where(.cui-checkbox__input:checked)::after {
          inline-size: 0.32em;
          block-size: 0.62em;
          border: solid currentcolor;
          border-width: 0 0.13em 0.13em 0;
          opacity: 1;
          transform: translateY(-0.04em) rotate(45deg);
        }

        :where(.cui-checkbox__input:indeterminate) {
          border-color: var(--_cui-checkbox-active-color);
          background: var(--_cui-checkbox-active-color);
        }

        :where(.cui-checkbox__input:indeterminate)::after {
          inline-size: 0.58em;
          block-size: 0.13em;
          border-radius: 999px;
          background: currentcolor;
          opacity: 1;
        }

        :where(.cui-checkbox[data-variant="outline"] .cui-checkbox__input:checked),
        :where(.cui-checkbox[data-variant="outline"] .cui-checkbox__input:indeterminate) {
          --_cui-checkbox-indicator-color: var(
            --cui-checkbox-indicator-color,
            var(--_cui-checkbox-active-color)
          );

          background: var(--_cui-checkbox-background);
          color: var(--_cui-checkbox-indicator-color);
        }

        :where(.cui-checkbox__input:focus-visible) {
          border-color: var(--_cui-checkbox-focus-color);
          outline: 0.1875rem solid color-mix(
            in srgb,
            var(--_cui-checkbox-focus-color) 38%,
            transparent
          );
          outline-offset: 0.125rem;
        }

        @media (hover: hover) {
          :where(.cui-checkbox:not([data-disabled]) .cui-checkbox__input:hover) {
            border-color: var(--_cui-checkbox-hover-border-color);
          }
        }

        :where(.cui-checkbox[data-invalid] .cui-checkbox__input) {
          border-color: var(--_cui-checkbox-invalid-color);
        }

        :where(.cui-checkbox__body) {
          display: grid;
          min-inline-size: 0;
          gap: var(--_cui-checkbox-description-gap);
        }

        :where(.cui-checkbox [data-citry-ui-part="label"]) {
          min-inline-size: 0;
          color: inherit;
          cursor: pointer;
          overflow-wrap: anywhere;
        }

        :where(.cui-checkbox[data-disabled]),
        :where(.cui-checkbox:has(> .cui-checkbox__input:disabled)) {
          opacity: var(--_cui-checkbox-disabled-opacity);
        }

        :where(.cui-checkbox[data-disabled] .cui-checkbox__input),
        :where(.cui-checkbox[data-disabled] [data-citry-ui-part="label"]),
        :where(.cui-checkbox > .cui-checkbox__input:disabled),
        :where(.cui-checkbox:has(> .cui-checkbox__input:disabled) [data-citry-ui-part="label"]) {
          cursor: not-allowed;
        }

        :where(.cui-checkbox [data-citry-ui-part="description"]) {
          min-inline-size: 0;
          color: var(--_cui-checkbox-description-color);
          font-size: 0.875em;
          overflow-wrap: anywhere;
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-checkbox__input) {
            transition: none;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-checkbox__input) {
            border-color: ButtonText;
            forced-color-adjust: auto;
          }

          :where(.cui-checkbox[data-invalid] .cui-checkbox__input) {
            border-color: Mark;
          }
        }

        @media print {
          :where(.cui-checkbox__input) {
            print-color-adjust: exact;
          }
        }
      }
    """


__all__ = [
    "CCheckbox",
    "CCheckboxDefaultSlotData",
    "CCheckboxDescriptionSlotData",
    "CCheckboxLabelPos",
    "CCheckboxSize",
    "CCheckboxVariant",
]
