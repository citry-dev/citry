"""Styled native Switch component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs, pop_html_attr
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_optional_boolean

CSwitchSize = Literal["sm", "md", "lg"]
CSwitchLabelPos = Literal["start", "end"]

_SIZES = ("sm", "md", "lg")
_LABEL_POSITIONS = ("start", "end")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-checked",
        "data-citry-switch-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-invalid",
        "data-label-pos",
        "data-required",
        "data-size",
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


class CSwitchDefaultSlotData:
    pass


class CSwitchDescriptionSlotData:
    pass


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CSwitch {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CSwitch could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _canonical_string(input_name: str, value: object, *, allow_none: bool) -> str | None:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        if allow_none:
            return None
        msg = f"CSwitch {input_name} must be a string."
        raise TypeError(msg)
    canonical = plain.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in canonical:
        msg = f"CSwitch {input_name} cannot contain U+0000."
        raise ValueError(msg)
    return canonical


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CSwitch {input_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)
    return plain


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CSwitch {input_name} must be a mapping or None, got {attrs!r}."
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
    component_name = f"CSwitch {input_name}"
    reject_owned_attrs(attrs, owned, component_name)
    dynamic_targets = dynamic_owned or owned
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{component_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in dynamic_targets:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _extract_naming_attr(attrs: dict[str, object], name: str) -> str | None:
    raw = pop_html_attr(attrs, name, component_name="CSwitch")
    if raw is None or raw is False:
        return None
    plain = _plain_optional_string(name, raw)
    if plain is None or not plain.strip():
        msg = f"CSwitch {name} must be non-empty when supplied."
        raise ValueError(msg)
    attrs[name] = plain
    return plain


class CSwitch(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: str | None = None
        value: str = "on"
        id: str | None = None
        checked: bool = False
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        size: CSwitchSize = "md"
        label_pos: CSwitchLabelPos = "end"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSwitchDefaultSlotData] | None = None
        description: SlotInput[CSwitchDescriptionSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        name = _canonical_string("name", kwargs.name, allow_none=True)
        if name == "":
            raise ValueError("CSwitch name must be non-empty when supplied.")
        value = _canonical_string("value", kwargs.value, allow_none=False)
        element_id = _canonical_string("id", kwargs.id, allow_none=True)
        if element_id is not None and (not element_id or any(character in "\t\n\f\r " for character in element_id)):
            raise ValueError("CSwitch id must be non-empty and cannot contain ASCII whitespace.")
        validate_boolean("CSwitch", "checked", kwargs.checked)
        validate_optional_boolean("CSwitch", "required", kwargs.required)
        validate_optional_boolean("CSwitch", "disabled", kwargs.disabled)
        validate_optional_boolean("CSwitch", "invalid", kwargs.invalid)
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

        has_label = "default" in self.raw_slots
        has_description = "description" in self.raw_slots
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None and (has_label or has_description):
            raise ValueError("CSwitch inside CField cannot supply default or description slots; CField owns them.")
        if field is not None:
            supplied = [
                key
                for key, item in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("invalid", kwargs.invalid),
                )
                if item is not None
            ]
            if supplied:
                raise ValueError(f"CSwitch inside CField cannot set Field-owned state: {', '.join(supplied)}.")
            field.register_control("CSwitch", supports_required=True, supports_readonly=False)

        aria_label = _extract_naming_attr(input_attrs, "aria-label")
        aria_labelledby = _extract_naming_attr(input_attrs, "aria-labelledby")
        if aria_label is not None and aria_labelledby is not None:
            raise ValueError("CSwitch accepts either aria-label or aria-labelledby, not both.")
        if (has_label or field is not None) and (aria_label is not None or aria_labelledby is not None):
            raise ValueError("CSwitch cannot replace its visible or CField label with ARIA naming.")
        if not has_label and field is None and aria_label is None and aria_labelledby is None:
            raise ValueError("CSwitch without a default slot or CField requires input_attrs ARIA naming.")

        field_control_id = str(field.control_id) if field is not None else None
        if field_control_id is not None and element_id is not None and element_id != field_control_id:
            raise ValueError(f"CSwitch id {element_id!r} conflicts with its CField control_id {field_control_id!r}.")
        input_id = element_id or field_control_id or f"cui-switch-{self.id}"
        form_owner = get_html_form_owner(
            input_attrs,
            component_name="CSwitch",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CSwitch inside CForm cannot target a different native form owner.")

        external_described_by = pop_html_attr(input_attrs, "aria-describedby", component_name="CSwitch")
        external_error_message = pop_html_attr(input_attrs, "aria-errormessage", component_name="CSwitch")
        self._switch_value = value
        self._switch_external_described_by = external_described_by
        self._switch_external_error_message = external_error_message
        description_id = f"{input_id}-description"
        self._switch_description_id = description_id
        self._switch_has_description = has_description

        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            invalid = bool(field.invalid)
        else:
            required = bool(kwargs.required)
            disabled = bool(form.disabled if form is not None else False) or bool(kwargs.disabled)
            invalid = bool(kwargs.invalid)
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
        return {
            "id": input_id,
            "name": name,
            "value": value,
            "form": form_owner,
            "checked": kwargs.checked,
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
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
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        field = self.inject(FIELD_CONTEXT_KEY, None)
        return {
            "value": self._switch_value,
            "checked": kwargs.checked,
            "required": bool(field.required) if field is not None else bool(kwargs.required),
            "disabled": bool(field.disabled) if field is not None else bool(kwargs.disabled),
            "invalid": bool(field.invalid) if field is not None else bool(kwargs.invalid),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "labelPos": _plain_choice("label_pos", kwargs.label_pos, _LABEL_POSITIONS),
            "descriptionId": self._switch_description_id,
            "hasDescription": self._switch_has_description,
            "externalDescribedBy": self._switch_external_described_by,
            "externalErrorMessage": self._switch_external_error_message,
        }

    template = """
      <span
        class="cui-switch"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-size="size"
        c-data-label-pos="label_pos"
        c-bind="attrs"
        data-citry-ui-part="switch"
      >
        <input
          class="cui-switch__input"
          c-id="id"
          c-name="name"
          type="checkbox"
          role="switch"
          c-value="value"
          c-form="form"
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
        <span data-citry-ui-part="surface">
          <span aria-hidden="true" data-citry-ui-part="track">
            <span data-citry-ui-part="thumb"></span>
          </span>
          <c-if cond="has_body">
            <span data-citry-ui-part="body">
              <c-if cond="has_label">
                <label c-bind="label_attrs" data-citry-ui-part="label">
                  <c-slot />
                </label>
              </c-if>
              <c-if cond="has_description">
                <span c-id="description_id" data-citry-ui-part="description">
                  <c-slot name="description" />
                </span>
              </c-if>
            </span>
          </c-if>
        </span>
      </span>
    """

    js = r"""
      $component({
        props: {
          checked: {},
          value: {},
          required: {},
          disabled: {},
          invalid: {},
          size: {},
          label_pos: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
          if (!(input instanceof HTMLInputElement) || input.type !== "checkbox") {
            throw new Error("[citry-ui] CSwitch requires one direct native checkbox input.");
          }
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const handoffKey = Symbol.for("citry-ui:switch-handoff");
          const invalidEpisodes = new Set();
          const resetTimers = new Set();
          let nativeInvalid = false;
          let controlled = false;
          let controlledValue = false;
          let activationPending = false;
          let reconcileTimer = null;
          const handoff = root[handoffKey];
          delete root[handoffKey];
          if (handoff) input.checked = Boolean(handoff.checked);

          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CSwitch ${name} received invalid client value; using the fallback.`,
              value,
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
          const resolveChoice = (name, fallback, choices) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (choices.includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const canonicalValue = () => {
            if (props.value === undefined) return data.value;
            if (typeof props.value !== "string" || props.value.includes("\0")) {
              reportInvalid("value", props.value);
              return data.value;
            }
            invalidEpisodes.delete("value");
            return props.value.replace(/\r\n?/g, "\n");
          };
          const syncRelationships = (invalid) => {
            const values = [
              field?.hasDescription ? field.descriptionId : null,
              data.hasDescription ? data.descriptionId : null,
              invalid && field?.hasError ? field.errorId : null,
              data.externalDescribedBy,
            ];
            const describedBy = [...new Set(values.filter(Boolean).flatMap((value) => value.split(/\s+/)))].join(" ");
            const errorMessage = invalid
              ? [field?.hasError ? field.errorId : null, data.externalErrorMessage].filter(Boolean).join(" ")
              : "";
            describedBy
              ? input.setAttribute("aria-describedby", describedBy)
              : input.removeAttribute("aria-describedby");
            errorMessage
              ? input.setAttribute("aria-errormessage", errorMessage)
              : input.removeAttribute("aria-errormessage");
          };
          const applyState = () => {
            let required;
            let disabled;
            let externalInvalid;
            if (field) {
              ["required", "disabled", "invalid"].forEach((name) => {
                if (props[name] !== undefined) reportInvalid(`${name}:field-owned`, props[name]);
                else invalidEpisodes.delete(`${name}:field-owned`);
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
            input.required = required;
            input.disabled = disabled;
            const value = canonicalValue();
            if (input.value !== value) input.value = value;
            root.toggleAttribute("data-required", required);
            root.toggleAttribute("data-disabled", input.matches(":disabled"));
            root.toggleAttribute("data-invalid", invalid);
            root.toggleAttribute("data-checked", input.checked);
            root.dataset.size = resolveChoice("size", data.size, ["sm", "md", "lg"]);
            root.dataset.labelPos = resolveChoice("label_pos", data.labelPos, ["start", "end"]);
            invalid ? input.setAttribute("aria-invalid", "true") : input.removeAttribute("aria-invalid");
            syncRelationships(invalid);
          };
          const applyControlled = () => {
            if (props.checked === undefined) {
              controlled = false;
              invalidEpisodes.delete("checked");
              return;
            }
            if (typeof props.checked !== "boolean") {
              reportInvalid("checked", props.checked);
              if (controlled && !activationPending) input.checked = controlledValue;
              return;
            }
            invalidEpisodes.delete("checked");
            controlled = true;
            controlledValue = props.checked;
            if (!activationPending && input.checked !== controlledValue) input.checked = controlledValue;
          };
          const settle = () => {
            activationPending = false;
            applyControlled();
            if (nativeInvalid && input.validity.valid) {
              nativeInvalid = false;
              field?.setNativeInvalid(false);
            }
            applyState();
          };
          const scheduleSettle = () => {
            if (reconcileTimer !== null) clearTimeout(reconcileTimer);
            reconcileTimer = setTimeout(() => {
              reconcileTimer = null;
              settle();
            }, 0);
          };
          const onInput = () => {
            activationPending = true;
            root.toggleAttribute("data-checked", input.checked);
            scheduleSettle();
          };
          const onChange = () => scheduleSettle();
          const onInvalid = () => {
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const nativeForm = input.form;
          const onReset = (event) => {
            const timer = setTimeout(() => {
              resetTimers.delete(timer);
              if (event.defaultPrevented) return;
              if (controlled) input.checked = controlledValue;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              applyState();
            }, 0);
            resetTimers.add(timer);
          };
          input.addEventListener("input", onInput);
          input.addEventListener("change", onChange);
          input.addEventListener("invalid", onInvalid);
          nativeForm?.addEventListener("reset", onReset);
          const unregisterCapability = field?.registerControlCapabilities?.({
            supportsRequired: true,
            supportsReadonly: false,
          });
          effect(() => {
            applyControlled();
            applyState();
          });
          root.setAttribute("data-citry-switch-initialized", "");
          return () => {
            root[handoffKey] = {checked: input.checked};
            input.removeEventListener("input", onInput);
            input.removeEventListener("change", onChange);
            input.removeEventListener("invalid", onInvalid);
            nativeForm?.removeEventListener("reset", onReset);
            if (reconcileTimer !== null) clearTimeout(reconcileTimer);
            resetTimers.forEach((timer) => clearTimeout(timer));
            unregisterCapability?.();
            root.removeAttribute("data-citry-switch-initialized");
          };
        },
      })
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-switch) {
          --_cui-switch-off-color: var(--cui-switch-off-color, light-dark(#667085, #98a2b3));
          --_cui-switch-on-color: var(--cui-switch-on-color, light-dark(#175cd3, #84adff));
          --_cui-switch-thumb-color: var(--cui-switch-thumb-color, Canvas);
          --_cui-switch-foreground: var(--cui-switch-foreground, CanvasText);
          --_cui-switch-focus-color: var(--cui-switch-focus-color, Highlight);
          --_cui-switch-invalid-color: var(--cui-switch-invalid-color, light-dark(#b42318, #f97066));
          --_cui-switch-disabled-opacity: var(--cui-switch-disabled-opacity, 0.52);
          --_cui-switch-width: var(--cui-switch-width, 2.5rem);
          --_cui-switch-height: var(--cui-switch-height, 1.5rem);
          --_cui-switch-padding: var(--cui-switch-padding, 0.1875rem);
          --_cui-switch-gap: var(--cui-switch-gap, 0.625rem);
          --_cui-switch-duration: var(--cui-switch-duration, 140ms);
          position: relative;
          display: inline-grid;
          color: var(--_cui-switch-foreground);
          font: inherit;
          line-height: 1.35;
        }

        :where(.cui-switch[data-size="sm"]) {
          --_cui-switch-width: var(--cui-switch-width, 2rem);
          --_cui-switch-height: var(--cui-switch-height, 1.25rem);
          font-size: 0.8125rem;
        }

        :where(.cui-switch[data-size="lg"]) {
          --_cui-switch-width: var(--cui-switch-width, 3rem);
          --_cui-switch-height: var(--cui-switch-height, 1.75rem);
          font-size: 1rem;
        }

        :where(.cui-switch__input) {
          position: absolute;
          inline-size: var(--_cui-switch-width);
          block-size: var(--_cui-switch-height);
          margin: 0;
          opacity: 0;
          cursor: pointer;
          z-index: 1;
        }

        :where(.cui-switch [data-citry-ui-part="surface"]) {
          display: inline-flex;
          align-items: flex-start;
          gap: var(--_cui-switch-gap);
          cursor: pointer;
        }

        :where(.cui-switch [data-citry-ui-part="track"]) {
          box-sizing: border-box;
          display: inline-flex;
          flex: 0 0 auto;
          align-items: center;
          inline-size: var(--_cui-switch-width);
          block-size: var(--_cui-switch-height);
          padding: var(--_cui-switch-padding);
          border: 1px solid transparent;
          border-radius: 999px;
          background: var(--_cui-switch-off-color);
          transition: background-color var(--_cui-switch-duration) ease;
        }

        :where(.cui-switch [data-citry-ui-part="thumb"]) {
          box-sizing: border-box;
          display: block;
          inline-size: calc(var(--_cui-switch-height) - 2 * var(--_cui-switch-padding) - 2px);
          block-size: calc(var(--_cui-switch-height) - 2 * var(--_cui-switch-padding) - 2px);
          border-radius: 50%;
          background: var(--_cui-switch-thumb-color);
          box-shadow: 0 1px 2px rgb(0 0 0 / 25%);
          transform: translateX(0);
          transition: transform var(--_cui-switch-duration) ease;
        }

        :where(.cui-switch__input:checked + [data-citry-ui-part="surface"] [data-citry-ui-part="track"]) {
          background: var(--_cui-switch-on-color);
        }

        :where(.cui-switch__input:checked + [data-citry-ui-part="surface"] [data-citry-ui-part="thumb"]) {
          transform: translateX(
            calc(var(--_cui-switch-width) - var(--_cui-switch-height))
          );
        }

        :where(
          .cui-switch:dir(rtl)
          .cui-switch__input:checked
          + [data-citry-ui-part="surface"]
          [data-citry-ui-part="thumb"]
        ) {
          transform: translateX(
            calc((var(--_cui-switch-width) - var(--_cui-switch-height)) * -1)
          );
        }

        :where(.cui-switch__input:focus-visible + [data-citry-ui-part="surface"] [data-citry-ui-part="track"]) {
          outline: 0.1875rem solid color-mix(in srgb, var(--_cui-switch-focus-color) 42%, transparent);
          outline-offset: 0.125rem;
        }

        :where(.cui-switch[data-invalid] [data-citry-ui-part="track"]) {
          box-shadow: 0 0 0 2px var(--_cui-switch-invalid-color);
        }

        :where(.cui-switch[data-disabled]) {
          opacity: var(--_cui-switch-disabled-opacity);
        }

        :where(.cui-switch[data-disabled] .cui-switch__input),
        :where(.cui-switch[data-disabled] [data-citry-ui-part="surface"]) {
          cursor: not-allowed;
        }

        :where(.cui-switch [data-citry-ui-part="body"]) {
          display: grid;
          min-inline-size: 0;
          gap: 0.2rem;
        }

        :where(.cui-switch [data-citry-ui-part="label"], .cui-switch [data-citry-ui-part="description"]) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }

        :where(.cui-switch [data-citry-ui-part="description"]) {
          color: color-mix(in srgb, currentColor 72%, transparent);
          font-size: 0.82em;
        }

        :where(.cui-switch[data-label-pos="start"] [data-citry-ui-part="surface"]) {
          flex-direction: row-reverse;
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-switch [data-citry-ui-part="track"], .cui-switch [data-citry-ui-part="thumb"]) {
            transition-duration: 0.01ms;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-switch [data-citry-ui-part="track"]) {
            border-color: ButtonText;
            background: Canvas;
          }

          :where(.cui-switch__input:checked + [data-citry-ui-part="surface"] [data-citry-ui-part="track"]) {
            background: Highlight;
          }

          :where(.cui-switch [data-citry-ui-part="thumb"]) {
            background: ButtonText;
            box-shadow: none;
          }
        }

        @media print {
          :where(.cui-switch [data-citry-ui-part="track"]) {
            border-color: currentColor;
            background: transparent;
          }

          :where(.cui-switch__input:checked + [data-citry-ui-part="surface"] [data-citry-ui-part="track"]) {
            background: currentColor;
          }
        }
      }
    """


__all__ = [
    "CSwitch",
    "CSwitchDefaultSlotData",
    "CSwitchDescriptionSlotData",
    "CSwitchLabelPos",
    "CSwitchSize",
]
