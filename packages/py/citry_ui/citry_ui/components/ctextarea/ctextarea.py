"""Styled native Textarea component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from markupsafe import escape

from citry import LibraryComponent, Markup, const_value, is_const
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
from citry_ui.components._validation import reject_owned_attrs, validate_optional_boolean

CTextareaVariant = Literal["outline", "filled", "plain"]
CTextareaSize = Literal["sm", "md", "lg"]
CTextareaResize = Literal["none", "vertical", "horizontal", "both"]
CTextareaWrap = Literal["soft", "hard"]

_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_RESIZE_VALUES = ("none", "vertical", "horizontal", "both")
_WRAP_VALUES = ("soft", "hard")
_OWNED_ATTRS = frozenset(
    {
        "aria-invalid",
        "autocomplete",
        "cols",
        "data-citry-textarea-initialized",
        FIELD_CONTROL_MARKER,
        "data-citry-ui-part",
        "data-disabled",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-resize",
        "data-size",
        "data-variant",
        "disabled",
        "id",
        "inputmode",
        "name",
        "placeholder",
        "readonly",
        "required",
        "rows",
        "value",
        "wrap",
    }
)


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        msg = f"CTextarea {input_name} must be a string or None, got {value!r}."
        raise TypeError(msg)

    # Joining de-trusts Markup, Django SafeString, and Citry's static-value
    # proxy without calling a user-controlled __html__ or __str__ method.
    plain = "".join(value)
    if type(plain) is not str:
        msg = f"CTextarea could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CTextarea {input_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)
    return plain


def _positive_integer(input_name: str, value: object) -> int:
    # Static component attributes arrive as constant strings, so accept their
    # HTML-style decimal spelling while Python composition remains int-only.
    raw_value = const_value(value)
    if is_const(value) and isinstance(raw_value, str) and raw_value.isascii() and raw_value.isdecimal():
        parsed = int(raw_value)
        if parsed > 0:
            return parsed
        value = parsed
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"CTextarea {input_name} must be a positive integer, got {value!r}."
        raise TypeError(msg)
    if value <= 0:
        msg = f"CTextarea {input_name} must be greater than zero, got {value!r}."
        raise ValueError(msg)
    return value


def _validate_attrs(attrs: Mapping[str, object] | None) -> None:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CTextarea attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    reject_owned_attrs(attrs, _OWNED_ATTRS, "CTextarea")
    reject_html_attr_bindings(attrs, {"form"}, "CTextarea")
    for key in attrs or {}:
        normalized = key.lower()
        if normalized.startswith(("data-citry-", "data-cev", "data-cid")):
            msg = f"CTextarea attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)


def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _encode_initial_value(value: str | None) -> Markup:
    normalized = _normalize_newlines(value or "")
    encoded = escape(normalized)
    if normalized.startswith("\n"):
        # HTML strips one newline immediately after a textarea start tag, so
        # this extra newline preserves the caller's actual first character.
        return Markup("\n") + encoded
    return encoded


class CTextarea(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: str | None = None
        id: str | None = None
        value: str | None = None
        rows: int = 4
        cols: int | None = None
        wrap: CTextareaWrap = "soft"
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        autocomplete: str | None = None
        inputmode: str | None = None
        placeholder: str | None = None
        variant: CTextareaVariant = "outline"
        size: CTextareaSize = "md"
        resize: CTextareaResize = "vertical"
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
        name = _plain_optional_string("name", kwargs.name)
        if name == "":
            msg = "CTextarea name must be non-empty when supplied."
            raise ValueError(msg)
        element_id = _plain_optional_string("id", kwargs.id)
        if element_id is not None and (not element_id or any(character in "\t\n\f\r " for character in element_id)):
            msg = "CTextarea id must be non-empty and cannot contain ASCII whitespace."
            raise ValueError(msg)
        value = _plain_optional_string("value", kwargs.value)
        rows = _positive_integer("rows", kwargs.rows)
        cols = _positive_integer("cols", kwargs.cols) if kwargs.cols is not None else None
        wrap = _plain_choice("wrap", kwargs.wrap, _WRAP_VALUES)
        if wrap == "hard" and cols is None:
            msg = "CTextarea wrap='hard' requires cols."
            raise ValueError(msg)
        validate_optional_boolean("CTextarea", "required", kwargs.required)
        validate_optional_boolean("CTextarea", "disabled", kwargs.disabled)
        validate_optional_boolean("CTextarea", "readonly", kwargs.readonly)
        validate_optional_boolean("CTextarea", "invalid", kwargs.invalid)
        autocomplete = _plain_optional_string("autocomplete", kwargs.autocomplete)
        inputmode = _plain_optional_string("inputmode", kwargs.inputmode)
        placeholder = _plain_optional_string("placeholder", kwargs.placeholder)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        resize = _plain_choice("resize", kwargs.resize, _RESIZE_VALUES)
        _validate_attrs(kwargs.attrs)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            supplied_state = [
                input_name
                for input_name, state_value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("readonly", kwargs.readonly),
                    ("invalid", kwargs.invalid),
                )
                if state_value is not None
            ]
            if supplied_state:
                names = ", ".join(supplied_state)
                msg = f"CTextarea inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            field.register_control("CTextarea")
        if field_control_id is not None and element_id is not None and element_id != field_control_id:
            msg = (
                f"CTextarea id {element_id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CTextarea.id."
            )
            raise ValueError(msg)

        for html_attribute in ("form", "aria-describedby", "aria-errormessage"):
            get_html_attr(
                kwargs.attrs or {},
                html_attribute,
                component_name="CTextarea",
            )
        caller_attrs = merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style)
        form_owner = get_html_form_owner(
            caller_attrs,
            component_name="CTextarea",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            msg = "CTextarea inside CForm cannot target a different native form owner."
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

        textarea_id = element_id or field_control_id or f"cui-textarea-{self.id}"
        external_described_by = pop_html_attr(
            caller_attrs,
            "aria-describedby",
            component_name="CTextarea",
        )
        external_error_message = pop_html_attr(
            caller_attrs,
            "aria-errormessage",
            component_name="CTextarea",
        )
        self._textarea_external_described_by = external_described_by
        self._textarea_external_error_message = external_error_message
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
            "id": textarea_id,
            "name": name,
            "default_value": _encode_initial_value(value),
            "rows": rows,
            "cols": cols,
            "wrap": wrap,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "autocomplete": autocomplete,
            "inputmode": inputmode,
            "placeholder": placeholder,
            "variant": variant,
            "size": size,
            "resize": resize,
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
        value = _plain_optional_string("value", kwargs.value)
        return {
            "value": _normalize_newlines(value) if value is not None else None,
            "rows": _positive_integer("rows", kwargs.rows),
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
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "resize": _plain_choice("resize", kwargs.resize, _RESIZE_VALUES),
            "externalDescribedBy": self._textarea_external_described_by,
            "externalErrorMessage": self._textarea_external_error_message,
        }

    template = """
      <textarea
        class="cui-textarea"
        c-id="id"
        c-name="name"
        c-rows="rows"
        c-cols="cols"
        c-wrap="wrap"
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
        c-data-resize="resize"
        c-data-citry-field-control="field_control"
        c-bind="attrs"
        data-citry-ui-part="textarea"
      >{{ default_value }}</textarea>
    """

    js = r"""
      $component({
        props: {
          value: {},
          rows: {},
          required: {},
          disabled: {},
          readonly: {},
          invalid: {},
          variant: {},
          size: {},
          resize: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const textarea = els[0];
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const allowedValues = {
            variant: ["outline", "filled", "plain"],
            size: ["sm", "md", "lg"],
            resize: ["none", "vertical", "horizontal", "both"],
          };
          const invalidEpisodes = new Map();
          let nativeInvalid = false;
          let controlled = false;
          let controlledValue = null;
          let composing = false;
          let reconcileTimer = null;
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
              `[citry-ui] CTextarea ${name} received invalid client value ${describedValue}; `
                + "using the previous valid value or server-rendered fallback.",
              textarea,
            );
          };
          const normalizeNewlines = (value) => value.replace(/\r\n?/g, "\n");
          const resolveBoolean = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveRows = () => {
            const value = props.rows === undefined ? data.rows : props.rows;
            if (Number.isInteger(value) && value > 0) {
              invalidEpisodes.delete("rows");
              return value;
            }
            reportInvalid("rows", value);
            return data.rows;
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
              `[citry-ui] CTextarea ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describedValue}.`,
              textarea,
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
              textarea.setAttribute("aria-describedby", describedBy);
            } else {
              textarea.removeAttribute("aria-describedby");
            }
            if (errorMessage) {
              textarea.setAttribute("aria-errormessage", errorMessage);
            } else {
              textarea.removeAttribute("aria-errormessage");
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
              // A disabled native CForm fieldset always wins.
              disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
              const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.readonly;
              readonly = resolveBoolean("readonly", readonlyFallback);
              externalInvalid = resolveBoolean("invalid", data.invalid);
            }
            const invalid = externalInvalid || nativeInvalid;

            textarea.required = required;
            textarea.disabled = disabled;
            textarea.readOnly = readonly;
            textarea.rows = resolveRows();
            textarea.toggleAttribute("data-required", required);
            textarea.toggleAttribute("data-disabled", disabled);
            textarea.toggleAttribute("data-readonly", readonly);
            textarea.toggleAttribute("data-invalid", invalid);
            textarea.dataset.variant = resolveChoice("variant");
            textarea.dataset.size = resolveChoice("size");
            textarea.dataset.resize = resolveChoice("resize");
            if (invalid) {
              textarea.setAttribute("aria-invalid", "true");
            } else {
              textarea.removeAttribute("aria-invalid");
            }
            syncRelationships(invalid);
          };
          const clearNativeInvalidWhenValid = () => {
            if (!nativeInvalid || !textarea.validity.valid) {
              return;
            }
            nativeInvalid = false;
            field?.setNativeInvalid(false);
            applyState();
          };
          const applyLatestValueProp = () => {
            const value = props.value;
            if (value === undefined) {
              controlled = false;
              invalidEpisodes.delete("value");
              return;
            }
            if (typeof value !== "string") {
              reportInvalid("value", value);
              if (controlled && !composing && textarea.value !== controlledValue) {
                textarea.value = controlledValue;
              }
              return;
            }
            invalidEpisodes.delete("value");
            controlled = true;
            controlledValue = normalizeNewlines(value);
            if (!composing && textarea.value !== controlledValue) {
              textarea.value = controlledValue;
            }
          };
          const scheduleReconcile = () => {
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            // Consumer event handlers and Alpine effects settle before this
            // task reads the latest value prop.
            reconcileTimer = setTimeout(() => {
              reconcileTimer = null;
              if (!composing) {
                applyLatestValueProp();
              }
            }, 0);
          };
          const onInvalid = () => {
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const onInput = () => {
            clearNativeInvalidWhenValid();
            if (controlled && !composing) {
              scheduleReconcile();
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
            scheduleReconcile();
          };
          const onReset = (event) => {
            const resetTimer = setTimeout(() => {
              resetTimers.delete(resetTimer);
              if (event.defaultPrevented) {
                return;
              }
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              applyLatestValueProp();
              applyState();
            }, 0);
            resetTimers.add(resetTimer);
          };
          const nativeForm = textarea.form;

          textarea.addEventListener("invalid", onInvalid);
          textarea.addEventListener("input", onInput);
          textarea.addEventListener("change", onChange);
          textarea.addEventListener("compositionstart", onCompositionStart);
          textarea.addEventListener("compositionend", onCompositionEnd);
          nativeForm?.addEventListener("reset", onReset);
          effect(() => {
            applyState();
            clearNativeInvalidWhenValid();
          });
          effect(() => {
            applyLatestValueProp();
          });
          textarea.setAttribute("data-citry-textarea-initialized", "");

          return () => {
            textarea.removeEventListener("invalid", onInvalid);
            textarea.removeEventListener("input", onInput);
            textarea.removeEventListener("change", onChange);
            textarea.removeEventListener("compositionstart", onCompositionStart);
            textarea.removeEventListener("compositionend", onCompositionEnd);
            nativeForm?.removeEventListener("reset", onReset);
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
            resetTimers.clear();
            if (nativeInvalid) {
              field?.setNativeInvalid(false);
            }
            textarea.removeAttribute("data-citry-textarea-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = [
    "CTextarea",
    "CTextareaResize",
    "CTextareaSize",
    "CTextareaVariant",
    "CTextareaWrap",
]
