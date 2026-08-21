"""Native file picker and drop-backed file picker family."""

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
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_optional_boolean

CFileInputCapture = Literal["user", "environment"]
CFileInputVariant = Literal["outline", "soft", "plain"]
CFileInputSize = Literal["sm", "md", "lg"]

_CAPTURES = ("user", "environment")
_VARIANTS = ("outline", "soft", "plain")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-bind",
        "x-for",
        "x-html",
        "x-if",
        "x-ignore",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_INPUT_OWNED_ATTRS = frozenset(
    {
        "accept",
        "aria-disabled",
        "aria-hidden",
        "aria-invalid",
        "aria-readonly",
        "aria-required",
        "capture",
        "data-citry-field-control",
        "data-citry-ui-part",
        "data-disabled",
        "data-has-files",
        "data-invalid",
        "data-required",
        "data-size",
        "data-variant",
        "disabled",
        "files",
        "id",
        "multiple",
        "name",
        "readonly",
        "required",
        "role",
        "tabindex",
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
_DROP_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-dragging",
        "data-has-files",
        "data-invalid",
        "data-required",
        "data-size",
        "data-variant",
        "for",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


class CDropTargetDefaultSlotData:
    pass


def _plain_optional(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in plain:
        msg = f"{input_name} cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_required(input_name: str, value: object) -> str:
    plain = _plain_optional(input_name, value)
    if plain is None or not plain.strip():
        msg = f"{input_name} must be a nonempty string."
        raise ValueError(msg)
    return plain


def _choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_required(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    component_name: str,
    attrs: Mapping[str, object] | None,
    *,
    owned: frozenset[str],
    dynamic_owned: frozenset[str] | None = None,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{component_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, component_name)
    dynamic_owned = dynamic_owned or owned
    for key in copied:
        if not isinstance(key, str):
            msg = f"{component_name} requires string keys, got {key!r}."
            raise TypeError(msg)
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
        if target in dynamic_owned:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


def _validate_identity(component_name: str, input_name: str, value: object) -> str | None:
    plain = _plain_optional(f"{component_name} {input_name}", value)
    if plain is not None and (not plain or any(character in "\t\n\f\r " for character in plain)):
        msg = f"{component_name} {input_name} must be nonempty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    return plain


def _normalize_common(
    component_name: str,
    *,
    element_id: object,
    name: object,
    accept: object,
    capture: object,
    multiple: object,
    required: object,
    disabled: object,
    invalid: object,
    variant: object,
    size: object,
) -> dict[str, object]:
    validate_boolean(component_name, "multiple", multiple)
    validate_optional_boolean(component_name, "required", required)
    validate_optional_boolean(component_name, "disabled", disabled)
    validate_optional_boolean(component_name, "invalid", invalid)
    normalized_capture = _plain_optional(f"{component_name} capture", capture)
    if normalized_capture is not None and normalized_capture not in _CAPTURES:
        expected = ", ".join(repr(item) for item in _CAPTURES)
        msg = f"{component_name} capture must be one of {expected} or None, got {capture!r}."
        raise ValueError(msg)
    return {
        "element_id": _validate_identity(component_name, "id", element_id),
        "name": _validate_identity(component_name, "name", name),
        "accept": _plain_optional(f"{component_name} accept", accept),
        "capture": normalized_capture,
        "multiple": bool(multiple),
        "required": required,
        "disabled": disabled,
        "invalid": invalid,
        "variant": _choice(f"{component_name} variant", variant, _VARIANTS),
        "size": _choice(f"{component_name} size", size, _SIZES),
    }


class CFileInput(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        name: str | None = None
        accept: str | None = None
        capture: CFileInputCapture | None = None
        multiple: bool = False
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        variant: CFileInputVariant = "outline"
        size: CFileInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        normalized = _normalize_common(
            "CFileInput",
            element_id=kwargs.id,
            name=kwargs.name,
            accept=kwargs.accept,
            capture=kwargs.capture,
            multiple=kwargs.multiple,
            required=kwargs.required,
            disabled=kwargs.disabled,
            invalid=kwargs.invalid,
            variant=kwargs.variant,
            size=kwargs.size,
        )
        attrs = _copy_attrs(
            "CFileInput attrs",
            kwargs.attrs,
            owned=_INPUT_OWNED_ATTRS,
            dynamic_owned=_INPUT_DYNAMIC_OWNED_ATTRS,
        )
        for html_attribute in (
            "aria-describedby",
            "aria-errormessage",
            "aria-label",
            "aria-labelledby",
            "form",
        ):
            get_html_attr(attrs, html_attribute, component_name="CFileInput")
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None:
            supplied_state = [
                input_name
                for input_name, value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("invalid", kwargs.invalid),
                )
                if value is not None
            ]
            if supplied_state:
                names = ", ".join(supplied_state)
                msg = f"CFileInput inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            if (
                get_html_attr(attrs, "aria-label", component_name="CFileInput") is not None
                or get_html_attr(attrs, "aria-labelledby", component_name="CFileInput") is not None
            ):
                raise ValueError("CFileInput inside CField cannot replace its Field-owned accessible name.")
            field.register_control("CFileInput", supports_readonly=False)
        field_id = str(field.control_id) if field is not None else None
        element_id = normalized["element_id"]
        if field_id is not None and element_id is not None and element_id != field_id:
            msg = (
                f"CFileInput id {element_id!r} conflicts with its CField control_id {field_id!r}; "
                "set the same value on both."
            )
            raise ValueError(msg)
        caller_attrs = merge_root_attrs(attrs, kwargs.class_, kwargs.style)
        form_owner = get_html_form_owner(
            caller_attrs,
            component_name="CFileInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CFileInput inside CForm cannot target a different native form owner.")
        external_described_by = pop_html_attr(caller_attrs, "aria-describedby", component_name="CFileInput")
        external_error_message = pop_html_attr(caller_attrs, "aria-errormessage", component_name="CFileInput")
        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            invalid = bool(field.invalid)
        else:
            required = bool(normalized["required"] or False)
            disabled = (bool(form.disabled) if form is not None else False) or bool(normalized["disabled"] or False)
            invalid = bool(normalized["invalid"] or False)
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        self._external_described_by = external_described_by
        self._external_error_message = external_error_message
        return {
            **normalized,
            "id": element_id or field_id or f"cui-file-input-{self.id}",
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "field_control": field is not None,
            "attrs": caller_attrs,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        normalized = _normalize_common(
            "CFileInput",
            element_id=kwargs.id,
            name=kwargs.name,
            accept=kwargs.accept,
            capture=kwargs.capture,
            multiple=kwargs.multiple,
            required=kwargs.required,
            disabled=kwargs.disabled,
            invalid=kwargs.invalid,
            variant=kwargs.variant,
            size=kwargs.size,
        )
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        return {
            "accept": normalized["accept"],
            "capture": normalized["capture"],
            "multiple": normalized["multiple"],
            "required": bool(field.required) if field is not None else bool(normalized["required"] or False),
            "disabled": bool(field.disabled) if field is not None else bool(normalized["disabled"] or False),
            "invalid": bool(field.invalid) if field is not None else bool(normalized["invalid"] or False),
            "variant": normalized["variant"],
            "size": normalized["size"],
            "externalDescribedBy": self._external_described_by,
            "externalErrorMessage": self._external_error_message,
            "inheritsFormDisabled": field is None and form is not None,
        }

    template = """
      <input
        class="cui-file-input"
        c-bind="attrs"
        type="file"
        c-id="id"
        c-name="name"
        c-accept="accept"
        c-capture="capture"
        c-multiple="multiple"
        c-required="required"
        c-disabled="disabled"
        c-aria-invalid="aria_invalid"
        c-aria-describedby="aria_describedby"
        c-aria-errormessage="aria_errormessage"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-data-citry-field-control="field_control"
        data-citry-ui-part="file-input"
      />
    """

    js = r"""
      $component({
        props: {
          accept: {}, capture: {}, multiple: {}, required: {}, disabled: {}, invalid: {},
          variant: {}, size: {},
        },
        init: ({els, data, props, effect, inject}) => {
          const input = els[0];
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const invalidEpisodes = new Set();
          const resetTimers = new Set();
          let nativeInvalid = false;

          const report = (name, value, message = "received invalid client value") => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CFileInput ${name} ${message}`, value, input);
          };
          const booleanValue = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const choiceValue = (name, fallback, allowed) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "string" && allowed.includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const optionalString = (name, fallback, allowed = null) => {
            if (props[name] === undefined) {
              invalidEpisodes.delete(name);
              return fallback;
            }
            const value = props[name];
            if (typeof value === "string" && !value.includes("\0") && (!allowed || allowed.includes(value))) {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const idrefs = (...values) => {
            const tokens = [];
            values.forEach(value => {
              if (typeof value !== "string") return;
              value.split(/\s+/).filter(Boolean).forEach(token => {
                if (!tokens.includes(token)) tokens.push(token);
              });
            });
            return tokens.join(" ") || null;
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
            if (describedBy) input.setAttribute("aria-describedby", describedBy);
            else input.removeAttribute("aria-describedby");
            if (errorMessage) input.setAttribute("aria-errormessage", errorMessage);
            else input.removeAttribute("aria-errormessage");
          };
          const syncFiles = () => input.toggleAttribute("data-has-files", input.files.length > 0);
          const applyState = () => {
            let required;
            let disabled;
            let externalInvalid;
            if (field) {
              ["required", "disabled", "invalid"].forEach(name => {
                if (props[name] !== undefined) report(name, props[name], "is owned by CField; ignoring");
                else invalidEpisodes.delete(name);
              });
              required = field.required;
              disabled = field.disabled;
              externalInvalid = field.invalid;
            } else {
              required = booleanValue("required", data.required);
              disabled = Boolean(form?.disabled) || booleanValue("disabled", data.disabled);
              externalInvalid = booleanValue("invalid", data.invalid);
            }
            input.accept = optionalString("accept", data.accept) ?? "";
            const capture = optionalString("capture", data.capture, ["user", "environment"]);
            if (capture) input.setAttribute("capture", capture);
            else input.removeAttribute("capture");
            input.multiple = booleanValue("multiple", data.multiple);
            input.required = required;
            input.disabled = disabled;
            const invalid = externalInvalid || nativeInvalid;
            input.toggleAttribute("data-required", required);
            input.toggleAttribute("data-disabled", input.matches(":disabled"));
            input.toggleAttribute("data-invalid", invalid);
            input.dataset.variant = choiceValue("variant", data.variant, ["outline", "soft", "plain"]);
            input.dataset.size = choiceValue("size", data.size, ["sm", "md", "lg"]);
            if (invalid) input.setAttribute("aria-invalid", "true");
            else input.removeAttribute("aria-invalid");
            syncRelationships(invalid);
            syncFiles();
          };
          const clearNativeInvalid = () => {
            if (!nativeInvalid || !input.validity.valid) return;
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
            syncFiles();
            clearNativeInvalid();
          };
          const onReset = (event) => {
            const timer = setTimeout(() => {
              resetTimers.delete(timer);
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              applyState();
            }, 0);
            resetTimers.add(timer);
          };
          const nativeForm = input.form;
          const fieldsets = [];
          for (let ancestor = input.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
          }
          const fieldsetObserver = fieldsets.length
            ? new MutationObserver(applyState)
            : null;
          fieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
            childList: true, attributes: true, attributeFilter: ["disabled"],
          }));
          const unregisterCapabilities = field?.registerCapabilities({required: true, readonly: false});
          input.addEventListener("invalid", onInvalid);
          input.addEventListener("input", onInput);
          input.addEventListener("change", onInput);
          nativeForm?.addEventListener("reset", onReset);
          const stop = effect(applyState);
          input.setAttribute("data-citry-file-input-initialized", "");
          return () => {
            stop?.();
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("input", onInput);
            input.removeEventListener("change", onInput);
            nativeForm?.removeEventListener("reset", onReset);
            resetTimers.forEach(clearTimeout);
            resetTimers.clear();
            fieldsetObserver?.disconnect();
            unregisterCapabilities?.();
            if (nativeInvalid) field?.setNativeInvalid(false);
            input.removeAttribute("data-citry-file-input-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


class CDropTarget(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        id: str | None = None
        name: str | None = None
        accept: str | None = None
        capture: CFileInputCapture | None = None
        multiple: bool = False
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        variant: CFileInputVariant = "outline"
        size: CFileInputSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CDropTargetDefaultSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(FIELD_CONTEXT_KEY, None) is not None:
            raise ValueError("CDropTarget cannot be used as the control inside CField; use CFileInput.")
        label = _plain_required("CDropTarget label", kwargs.label)
        normalized = _normalize_common(
            "CDropTarget",
            element_id=kwargs.id,
            name=kwargs.name,
            accept=kwargs.accept,
            capture=kwargs.capture,
            multiple=kwargs.multiple,
            required=kwargs.required,
            disabled=kwargs.disabled,
            invalid=kwargs.invalid,
            variant=kwargs.variant,
            size=kwargs.size,
        )
        root_attrs = merge_root_attrs(
            _copy_attrs("CDropTarget attrs", kwargs.attrs, owned=_DROP_ROOT_OWNED_ATTRS),
            kwargs.class_,
            kwargs.style,
        )
        input_attrs = _copy_attrs(
            "CDropTarget input_attrs",
            kwargs.input_attrs,
            owned=_INPUT_OWNED_ATTRS | {"aria-label", "aria-labelledby", "class", "style"},
            dynamic_owned=_INPUT_DYNAMIC_OWNED_ATTRS,
        )
        for html_attribute in ("aria-describedby", "aria-errormessage", "form"):
            get_html_attr(input_attrs, html_attribute, component_name="CDropTarget input_attrs")
        form = self.inject(FORM_CONTEXT_KEY, None)
        form_owner = get_html_form_owner(
            input_attrs,
            component_name="CDropTarget",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CDropTarget inside CForm cannot target a different native form owner.")
        required = bool(normalized["required"] or False)
        disabled = (bool(form.disabled) if form is not None else False) or bool(normalized["disabled"] or False)
        invalid = bool(normalized["invalid"] or False)
        return {
            **normalized,
            "id": normalized["element_id"] or f"cui-drop-target-{self.id}",
            "label": label,
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "has_default": "default" in self.raw_slots,
            "attrs": root_attrs,
            "input_attrs": input_attrs,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        normalized = _normalize_common(
            "CDropTarget",
            element_id=kwargs.id,
            name=kwargs.name,
            accept=kwargs.accept,
            capture=kwargs.capture,
            multiple=kwargs.multiple,
            required=kwargs.required,
            disabled=kwargs.disabled,
            invalid=kwargs.invalid,
            variant=kwargs.variant,
            size=kwargs.size,
        )
        form = self.inject(FORM_CONTEXT_KEY, None)
        return {
            "accept": normalized["accept"],
            "capture": normalized["capture"],
            "multiple": normalized["multiple"],
            "required": bool(normalized["required"] or False),
            "disabled": bool(normalized["disabled"] or False),
            "invalid": bool(normalized["invalid"] or False),
            "variant": normalized["variant"],
            "size": normalized["size"],
            "hasForm": form is not None,
        }

    template = """
      <label
        class="cui-drop-target"
        c-bind="attrs"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        data-citry-ui-part="drop-target"
      >
        <input
          class="cui-drop-target__input"
          c-bind="input_attrs"
          type="file"
          c-id="id"
          c-name="name"
          c-accept="accept"
          c-capture="capture"
          c-multiple="multiple"
          c-required="required"
          c-disabled="disabled"
          c-aria-label="label"
          c-aria-invalid="aria_invalid"
          data-citry-ui-part="input"
        />
        <span class="cui-drop-target__label" data-citry-ui-part="label">{{ label }}</span>
        <c-if cond="has_default">
          <span class="cui-drop-target__content" data-citry-ui-part="content"><c-slot /></span>
        </c-if>
      </label>
    """

    js = r"""
      $component({
        props: {
          accept: {}, capture: {}, multiple: {}, required: {}, disabled: {}, invalid: {},
          variant: {}, size: {},
        },
        init: ({els, data, props, effect, inject}) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
          const form = inject(Symbol.for("citry-ui:form"), null);
          const invalidEpisodes = new Set();
          const resetTimers = new Set();
          let nativeInvalid = false;
          let structureValid = false;
          let dragDepth = 0;
          let configuredDisabled = data.disabled;

          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CDropTarget ${name} received invalid value`, value, root);
          };
          const booleanValue = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const choiceValue = (name, fallback, allowed) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "string" && allowed.includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const optionalString = (name, fallback, allowed = null) => {
            if (props[name] === undefined) {
              invalidEpisodes.delete(name);
              return fallback;
            }
            const value = props[name];
            if (typeof value === "string" && !value.includes("\0") && (!allowed || allowed.includes(value))) {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value);
            return fallback;
          };
          const fileDrag = event => [...(event.dataTransfer?.types ?? [])].includes("Files");
          const effectiveDisabled = () => !structureValid || input.matches(":disabled");
          const clearDragging = () => {
            dragDepth = 0;
            root.removeAttribute("data-dragging");
          };
          const syncFiles = () => {
            const hasFiles = input.files.length > 0;
            input.toggleAttribute("data-has-files", hasFiles);
            root.toggleAttribute("data-has-files", hasFiles);
          };
          const invalidStructure = () => {
            const forbiddenSelector = 'a[href], button, input, select, textarea, label, '
              + '[contenteditable]:not([contenteditable="false"]), [tabindex]';
            const forbidden = [...root.querySelectorAll(forbiddenSelector)]
              .find(element => element !== input);
            return forbidden ? forbidden.outerHTML : null;
          };
          const applyState = () => {
            input.accept = optionalString("accept", data.accept) ?? "";
            const capture = optionalString("capture", data.capture, ["user", "environment"]);
            if (capture) input.setAttribute("capture", capture);
            else input.removeAttribute("capture");
            input.multiple = booleanValue("multiple", data.multiple);
            input.required = booleanValue("required", data.required);
            configuredDisabled = Boolean(form?.disabled) || booleanValue("disabled", data.disabled);
            input.disabled = configuredDisabled || !structureValid;
            const invalid = booleanValue("invalid", data.invalid) || nativeInvalid;
            root.toggleAttribute("data-required", input.required);
            root.toggleAttribute("data-disabled", effectiveDisabled());
            root.toggleAttribute("data-invalid", invalid);
            root.dataset.variant = choiceValue("variant", data.variant, ["outline", "soft", "plain"]);
            root.dataset.size = choiceValue("size", data.size, ["sm", "md", "lg"]);
            if (invalid) input.setAttribute("aria-invalid", "true");
            else input.removeAttribute("aria-invalid");
            if (effectiveDisabled()) clearDragging();
            syncFiles();
          };
          const reconcileStructure = () => {
            const problem = invalidStructure();
            structureValid = problem === null;
            if (problem) {
              report("structure", problem);
              root.removeAttribute("data-citry-drop-target-initialized");
            } else {
              invalidEpisodes.delete("structure");
              root.setAttribute("data-citry-drop-target-initialized", "");
            }
            applyState();
          };
          const clearNativeInvalid = () => {
            if (!nativeInvalid || !input.validity.valid) return;
            nativeInvalid = false;
            applyState();
          };
          const onInvalid = () => {
            nativeInvalid = true;
            applyState();
          };
          const onInput = () => {
            syncFiles();
            clearNativeInvalid();
          };
          const onDragEnter = event => {
            if (!fileDrag(event) || effectiveDisabled()) return;
            event.preventDefault();
            dragDepth += 1;
            root.setAttribute("data-dragging", "");
          };
          const onDragOver = event => {
            if (!fileDrag(event) || effectiveDisabled()) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "copy";
          };
          const onDragLeave = event => {
            if (!fileDrag(event)) return;
            dragDepth = Math.max(0, dragDepth - 1);
            if (dragDepth === 0) root.removeAttribute("data-dragging");
          };
          const onDrop = event => {
            if (!fileDrag(event) || effectiveDisabled()) return;
            event.preventDefault();
            clearDragging();
            const dropped = event.dataTransfer.files;
            if (!dropped.length) return;
            let nextFiles = dropped;
            if (!input.multiple && dropped.length > 1) {
              const transfer = new DataTransfer();
              transfer.items.add(dropped[0]);
              nextFiles = transfer.files;
            }
            try {
              input.files = nextFiles;
            } catch (error) {
              report("drop", error);
              return;
            }
            input.dispatchEvent(new Event("input", {bubbles: true, composed: true}));
            input.dispatchEvent(new Event("change", {bubbles: true, composed: true}));
          };
          const onReset = event => {
            const timer = setTimeout(() => {
              resetTimers.delete(timer);
              if (event.defaultPrevented) return;
              nativeInvalid = false;
              clearDragging();
              applyState();
            }, 0);
            resetTimers.add(timer);
          };
          const nativeForm = input.form;
          const fieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (ancestor instanceof HTMLFieldSetElement) fieldsets.push(ancestor);
          }
          const fieldsetObserver = fieldsets.length ? new MutationObserver(applyState) : null;
          fieldsets.forEach(fieldset => fieldsetObserver.observe(fieldset, {
            childList: true, attributes: true, attributeFilter: ["disabled"],
          }));
          const observer = new MutationObserver(records => {
            if (records.some(record => record.target !== input)) reconcileStructure();
          });
          observer.observe(root, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["contenteditable", "href", "role", "tabindex"],
          });
          input.addEventListener("invalid", onInvalid);
          input.addEventListener("input", onInput);
          input.addEventListener("change", onInput);
          root.addEventListener("dragenter", onDragEnter);
          root.addEventListener("dragover", onDragOver);
          root.addEventListener("dragleave", onDragLeave);
          root.addEventListener("drop", onDrop);
          nativeForm?.addEventListener("reset", onReset);
          const stop = effect(applyState);
          reconcileStructure();
          return () => {
            stop?.();
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("input", onInput);
            input.removeEventListener("change", onInput);
            root.removeEventListener("dragenter", onDragEnter);
            root.removeEventListener("dragover", onDragOver);
            root.removeEventListener("dragleave", onDragLeave);
            root.removeEventListener("drop", onDrop);
            nativeForm?.removeEventListener("reset", onReset);
            resetTimers.forEach(clearTimeout);
            resetTimers.clear();
            observer.disconnect();
            fieldsetObserver?.disconnect();
            root.removeAttribute("data-citry-drop-target-initialized");
            clearDragging();
          };
        },
      });
    """

    css_file = "runtime.c-drop-target.min.css"


__all__ = [
    "CDropTarget",
    "CDropTargetDefaultSlotData",
    "CFileInput",
    "CFileInputCapture",
    "CFileInputSize",
    "CFileInputVariant",
]
