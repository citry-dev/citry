"""Styled progressive-enhancement inline Editable component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    get_html_form_owner,
    merge_root_attrs,
    pop_html_attr,
)
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

CEditableActionPosition = Literal["inside", "outside"]
CEditableSubmitMode = Literal["enter", "blur", "both", "explicit"]
CEditableVariant = Literal["outline", "filled", "plain"]
CEditableSize = Literal["sm", "md", "lg"]
CEditableValueSource = Literal["submit", "blur", "reset"]
CEditableEditReason = Literal["edit", "submit", "cancel", "blur", "reset", "disabled", "readonly", "invalid"]

_ACTION_POSITIONS = ("inside", "outside")
_SUBMIT_MODES = ("enter", "blur", "both", "explicit")
_VARIANTS = ("outline", "filled", "plain")
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
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-action-position",
        "data-citry-ui-part",
        "data-disabled",
        "data-editing",
        "data-empty",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-submit-mode",
        "data-variant",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-invalid",
        "autocomplete",
        "contenteditable",
        "data-citry-field-control",
        "data-citry-ui-part",
        "disabled",
        "form",
        "hidden",
        "id",
        "inert",
        "inputmode",
        "maxlength",
        "name",
        "readonly",
        "required",
        "role",
        "tabindex",
        "type",
        "value",
    }
)
_PREVIEW_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)


class CEditableValueChangeDetail(TypedDict):
    value: str
    previousValue: str
    controlled: bool
    source: CEditableValueSource
    sourceEvent: object | None


class CEditableEditChangeDetail(TypedDict):
    editing: bool
    reason: CEditableEditReason
    controlled: bool
    forced: bool
    source: object | None


def _plain(owner: str, name: str, value: object, *, allow_empty: bool = False) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        raise TypeError(f"{owner} {name} must be a string, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not allow_empty and not plain.strip():
        raise ValueError(f"{owner} {name} must be nonempty.")
    if "\0" in plain:
        raise ValueError(f"{owner} {name} cannot contain U+0000.")
    return plain


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    input_name: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None = None,
    style: CStyleValue | None = None,
    *,
    dynamic_only: frozenset[str] = frozenset(),
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"{owner} {input_name} must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} {input_name}")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{owner} {input_name} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} {input_name} cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"{owner} {input_name} cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned | dynamic_only:
            raise ValueError(f"{owner} {input_name} cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


class CEditable(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        value: str = ""
        placeholder: str = "Click to edit"
        name: str | None = None
        form: str | None = None
        id: str | None = None
        editing: bool = False
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        max_length: int | None = None
        autocomplete: str | None = None
        inputmode: str | None = None
        submit_mode: CEditableSubmitMode = "both"
        select_on_focus: bool = True
        action_position: CEditableActionPosition = "inside"
        edit_label: str = "Edit"
        submit_label: str = "Save"
        cancel_label: str = "Cancel"
        variant: CEditableVariant = "outline"
        size: CEditableSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None
        preview_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_editable_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        value = _plain("CEditable", "value", kwargs.value, allow_empty=True)
        catalog_placeholder = uses_catalog_default(self, "placeholder")
        catalog_edit_label = uses_catalog_default(self, "edit_label")
        catalog_submit_label = uses_catalog_default(self, "submit_label")
        catalog_cancel_label = uses_catalog_default(self, "cancel_label")
        placeholder = _plain(
            "CEditable",
            "placeholder",
            self.i18n.tr("citry-ui-editable-click-to-edit") if catalog_placeholder else kwargs.placeholder,
        )
        edit_label = _plain(
            "CEditable",
            "edit_label",
            self.i18n.tr("citry-ui-editable-edit") if catalog_edit_label else kwargs.edit_label,
        )
        submit_label = _plain(
            "CEditable",
            "submit_label",
            self.i18n.tr("citry-ui-editable-save") if catalog_submit_label else kwargs.submit_label,
        )
        cancel_label = _plain(
            "CEditable",
            "cancel_label",
            self.i18n.tr("citry-ui-editable-cancel") if catalog_cancel_label else kwargs.cancel_label,
        )
        if kwargs.name is not None:
            validate_non_empty_string("CEditable", "name", kwargs.name)
        if kwargs.form is not None:
            validate_html_id("CEditable", kwargs.form)
        validate_html_id("CEditable", kwargs.id)
        validate_boolean("CEditable", "editing", kwargs.editing)
        validate_boolean("CEditable", "select_on_focus", kwargs.select_on_focus)
        for name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CEditable", name, getattr(kwargs, name))
        validate_optional_string("CEditable", "autocomplete", kwargs.autocomplete)
        validate_optional_string("CEditable", "inputmode", kwargs.inputmode)
        if kwargs.max_length is not None:
            if isinstance(kwargs.max_length, bool) or not isinstance(kwargs.max_length, int):
                raise TypeError(f"CEditable max_length must be an integer or None, got {kwargs.max_length!r}.")
            if kwargs.max_length < 0:
                raise ValueError("CEditable max_length must be zero or greater.")
        validate_choice("CEditable", "submit_mode", kwargs.submit_mode, _SUBMIT_MODES)
        validate_choice("CEditable", "action_position", kwargs.action_position, _ACTION_POSITIONS)
        validate_choice("CEditable", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CEditable", "size", kwargs.size, _SIZES)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            competing = [
                name for name in ("required", "disabled", "readonly", "invalid") if getattr(kwargs, name) is not None
            ]
            if competing:
                raise ValueError(f"CEditable inside CField cannot set Field-owned state: {', '.join(competing)}.")
            field.register_control("CEditable")
        if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
            raise ValueError("CEditable id conflicts with its CField control_id.")

        input_attrs = _attrs(
            "CEditable",
            "input_attrs",
            kwargs.input_attrs,
            _INPUT_OWNED,
            dynamic_only=frozenset({"aria-describedby", "aria-errormessage"}),
        )
        external_described_by = pop_html_attr(
            input_attrs,
            "aria-describedby",
            component_name="CEditable input_attrs",
        )
        external_error_message = pop_html_attr(
            input_attrs,
            "aria-errormessage",
            component_name="CEditable input_attrs",
        )
        form_owner = get_html_form_owner(
            {"form": kwargs.form} if kwargs.form is not None else {},
            component_name="CEditable",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CEditable inside CForm cannot target a different native form owner.")

        if field is not None:
            required, disabled, readonly, invalid = (
                bool(field.required),
                bool(field.disabled),
                bool(field.readonly),
                bool(field.invalid),
            )
        else:
            required = bool(kwargs.required)
            disabled = (bool(form.disabled) if form is not None else False) or bool(kwargs.disabled)
            readonly = bool(kwargs.readonly) if kwargs.readonly is not None else bool(form.readonly) if form else False
            invalid = bool(kwargs.invalid)

        input_id = kwargs.id or field_control_id or f"cui-editable-{self.id}"
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        effective_editing = bool(kwargs.editing) and not disabled and not readonly
        data = {
            "value": value,
            "editing": effective_editing,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "submitMode": kwargs.submit_mode,
            "selectOnFocus": bool(kwargs.select_on_focus),
            "actionPosition": kwargs.action_position,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "placeholder": placeholder,
            "catalogPlaceholder": catalog_placeholder,
            "externalDescribedBy": external_described_by,
            "externalErrorMessage": external_error_message,
        }
        snapshot = {
            **data,
            "input_id": input_id,
            "name": kwargs.name,
            "form": form_owner,
            "max_length": kwargs.max_length,
            "autocomplete": kwargs.autocomplete,
            "inputmode": kwargs.inputmode,
            "edit_label": edit_label,
            "submit_label": submit_label,
            "cancel_label": cancel_label,
            "catalog_edit_label": catalog_edit_label,
            "catalog_submit_label": catalog_submit_label,
            "catalog_cancel_label": catalog_cancel_label,
            "display_value": value or placeholder,
            "empty": not value,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "field_control": "" if field is not None else None,
            "attrs": _attrs("CEditable", "attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
            "preview_attrs": _attrs("CEditable", "preview_attrs", kwargs.preview_attrs, _PREVIEW_OWNED),
        }
        self._cui_editable_snapshot = snapshot
        self._cui_editable_data = data
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_editable_data

    template = """
      <div
        class="cui-editable"
        c-data-editing="editing"
        c-data-empty="empty"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-submit-mode="submitMode"
        c-data-action-position="actionPosition"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="root"
      >
        <div class="cui-editable__preview" c-bind="preview_attrs" data-citry-ui-part="preview">
          <span data-citry-ui-part="preview-value">{{ display_value }}</span>
          <button
            class="cui-editable__action cui-editable__edit"
            type="button"
            c-aria-label="tr('citry-ui-editable-edit') if catalog_edit_label else edit_label"
            c-$c-tr:citry-ui-editable-edit[aria-label]="True if catalog_edit_label else None"
            c-disabled="disabled or readonly"
            data-citry-ui-part="edit-action"
          ><span aria-hidden="true">&#9998;</span></button>
        </div>
        <div class="cui-editable__edit-surface" data-citry-ui-part="edit-surface">
          <input
            class="cui-editable__input"
            c-id="input_id"
            c-name="name"
            c-form="form"
            c-value="value"
            c-required="required"
            c-disabled="disabled"
            c-readonly="readonly"
            c-maxlength="max_length"
            c-autocomplete="autocomplete"
            c-inputmode="inputmode"
            c-placeholder="tr('citry-ui-editable-click-to-edit') if catalogPlaceholder else placeholder"
            c-aria-invalid="aria_invalid"
            c-aria-describedby="aria_describedby"
            c-aria-errormessage="aria_errormessage"
            c-data-citry-field-control="field_control"
            c-bind="input_attrs"
            type="text"
            data-citry-ui-part="input"
          />
          <span class="cui-editable__actions" data-citry-ui-part="actions">
            <button
              class="cui-editable__action cui-editable__submit"
              type="button"
              c-aria-label="tr('citry-ui-editable-save') if catalog_submit_label else submit_label"
              c-$c-tr:citry-ui-editable-save[aria-label]="True if catalog_submit_label else None"
              c-disabled="disabled or readonly"
              data-citry-ui-part="submit-action"
            ><span aria-hidden="true">&#10003;</span></button>
            <button
              class="cui-editable__action cui-editable__cancel"
              type="button"
              c-aria-label="tr('citry-ui-editable-cancel') if catalog_cancel_label else cancel_label"
              c-$c-tr:citry-ui-editable-cancel[aria-label]="True if catalog_cancel_label else None"
              c-disabled="disabled or readonly"
              data-citry-ui-part="cancel-action"
            ><span aria-hidden="true">&#10005;</span></button>
          </span>
        </div>
      </div>
    """

    js = r"""
      const editableHandoffKey = Symbol.for("citry-ui:editable-handoff");
      $component({
        props: {
          value: {}, editing: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
          submitMode: {}, selectOnFocus: {}, actionPosition: {}, variant: {}, size: {},
          onValueChange: {}, onEditChange: {},
        },
        init: ({ els, data, props, effect, inject, i18n }) => {
          const root = els[0];
          const preview = root.querySelector(':scope > [data-citry-ui-part="preview"]');
          const previewValue = preview?.querySelector('[data-citry-ui-part="preview-value"]');
          const editAction = preview?.querySelector('[data-citry-ui-part="edit-action"]');
          const editSurface = root.querySelector(':scope > [data-citry-ui-part="edit-surface"]');
          const input = editSurface?.querySelector(':scope > [data-citry-ui-part="input"]');
          const actions = editSurface?.querySelector(':scope > [data-citry-ui-part="actions"]');
          const submitAction = actions?.querySelector('[data-citry-ui-part="submit-action"]');
          const cancelAction = actions?.querySelector('[data-citry-ui-part="cancel-action"]');
          if (!(preview instanceof HTMLElement) || !(previewValue instanceof HTMLElement)
            || !(editAction instanceof HTMLButtonElement) || !(editSurface instanceof HTMLElement)
            || !(input instanceof HTMLInputElement) || !(actions instanceof HTMLElement)
            || !(submitAction instanceof HTMLButtonElement) || !(cancelAction instanceof HTMLButtonElement)) {
            throw new Error("[citry-ui] CEditable settled anatomy is invalid.");
          }

          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const invalidEpisodes = new Set();
          const prior = root[editableHandoffKey];
          delete root[editableHandoffKey];
          const serverFingerprint = data.value;
          let committed = prior?.serverFingerprint === serverFingerprint ? prior.committed : data.value;
          let draft = prior?.serverFingerprint === serverFingerprint ? prior.draft : committed;
          let dirty = prior?.serverFingerprint === serverFingerprint ? Boolean(prior.dirty) : false;
          let internalEditing = prior?.serverFingerprint === serverFingerprint
            ? Boolean(prior.internalEditing)
            : data.editing;
          let editing = false;
          let controlledValue = false;
          let controlledEditing = false;
          let clientValue;
          let clientEditing;
          let onValueChange = null;
          let onEditChange = null;
          let nativeInvalid = false;
          let composing = false;
          let actionPressPending = false;
          let active = true;
          let generation = 0;
          let pendingFocus = false;
          let configuration = {
            required: data.required,
            disabled: data.disabled,
            readonly: data.readonly,
            invalid: data.invalid,
            submitMode: data.submitMode,
            selectOnFocus: data.selectOnFocus,
            actionPosition: data.actionPosition,
            variant: data.variant,
            size: data.size,
          };

          const report = (name, value, suffix = "") => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CEditable ${name} received invalid client value${suffix}`, value);
          };
          const boolean = (name, fallback) => {
            const value = props[name];
            if (value === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof value === "boolean") { invalidEpisodes.delete(name); return value; }
            report(name, value, "; using the server fallback");
            return fallback;
          };
          const choice = (name, fallback, allowed) => {
            const value = props[name];
            if (value === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof value === "string" && allowed.includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            report(name, value, "; using the server fallback");
            return fallback;
          };
          const idrefs = (...values) => {
            const result = [];
            values.forEach((value) => {
              if (typeof value !== "string") return;
              value.split(/\s+/).filter(Boolean).forEach((token) => {
                if (!result.includes(token)) result.push(token);
              });
            });
            return result.join(" ") || null;
          };
          const effectiveDisabled = () => configuration.disabled || input.matches(":disabled");
          const syncRelationships = (invalid) => {
            const described = idrefs(
              field?.hasDescription ? field.descriptionId : null,
              invalid && field?.hasError ? field.errorId : null,
              data.externalDescribedBy,
            );
            const error = invalid
              ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
              : null;
            if (described) input.setAttribute("aria-describedby", described);
            else input.removeAttribute("aria-describedby");
            if (error) input.setAttribute("aria-errormessage", error);
            else input.removeAttribute("aria-errormessage");
          };
          const focusInput = () => {
            const scheduled = ++generation;
            queueMicrotask(() => {
              if (!active || scheduled !== generation || !editing || !input.isConnected) return;
              input.focus({ preventScroll: true });
              if (configuration.selectOnFocus) input.select();
            });
          };
          const sync = () => {
            const disabled = effectiveDisabled();
            const invalid = configuration.invalid || nativeInvalid;
            root.toggleAttribute("data-editing", editing);
            root.toggleAttribute("data-empty", !committed);
            root.toggleAttribute("data-required", configuration.required);
            root.toggleAttribute("data-disabled", disabled);
            root.toggleAttribute("data-readonly", configuration.readonly);
            root.toggleAttribute("data-invalid", invalid);
            root.dataset.submitMode = configuration.submitMode;
            root.dataset.actionPosition = configuration.actionPosition;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            previewValue.textContent = committed || data.placeholder;
            editAction.disabled = disabled || configuration.readonly;
            submitAction.disabled = disabled || configuration.readonly;
            cancelAction.disabled = disabled || configuration.readonly;
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            if (invalid) input.setAttribute("aria-invalid", "true");
            else input.removeAttribute("aria-invalid");
            syncRelationships(invalid);
            field?.setNativeInvalid(nativeInvalid);
          };
          const notifyEdit = (next, reason, source, forced = false) => {
            onEditChange?.(next, { editing: next, reason, controlled: controlledEditing, forced, source });
          };
          const applyEditing = (next, { focus = false } = {}) => {
            if (next && (effectiveDisabled() || configuration.readonly)) next = false;
            if (next === editing) {
              if (next && focus) focusInput();
              return;
            }
            editing = next;
            if (next) {
              if (!dirty) {
                draft = committed;
                input.value = draft;
              }
              sync();
              if (focus) focusInput();
            } else {
              pendingFocus = false;
              sync();
            }
          };
          const requestEditing = (next, reason, source, { focus = false, forced = false } = {}) => {
            if (forced) {
              internalEditing = next;
              applyEditing(next, { focus });
              notifyEdit(next, reason, source, true);
              return;
            }
            if (controlledEditing) {
              notifyEdit(next, reason, source);
              return;
            }
            internalEditing = next;
            applyEditing(next, { focus });
            notifyEdit(next, reason, source);
          };
          const startEdit = (source) => {
            if (effectiveDisabled() || configuration.readonly || editing) return;
            dirty = false;
            draft = committed;
            input.value = draft;
            requestEditing(true, "edit", source, { focus: true });
          };
          const clearNativeInvalid = () => {
            if (!nativeInvalid || !input.validity.valid) return;
            nativeInvalid = false;
            field?.setNativeInvalid(false);
          };
          const requestValue = (next, source, sourceEvent) => {
            if (next === committed) return false;
            const previous = committed;
            const detail = {
              value: next,
              previousValue: previous,
              controlled: controlledValue,
              source,
              sourceEvent,
            };
            if (!controlledValue) committed = next;
            onValueChange?.(next, detail);
            return true;
          };
          const submit = (reason, sourceEvent) => {
            if (!editing || effectiveDisabled() || configuration.readonly) return;
            if (!input.checkValidity()) {
              nativeInvalid = true;
              sync();
              input.focus({ preventScroll: true });
              return;
            }
            draft = input.value.replace(/\r\n?/g, "\n");
            dirty = false;
            requestValue(draft, reason === "blur" ? "blur" : "submit", sourceEvent);
            clearNativeInvalid();
            requestEditing(false, reason, sourceEvent);
            sync();
            if (!controlledEditing && !effectiveDisabled() && !configuration.readonly) {
              queueMicrotask(() => editAction.focus({ preventScroll: true }));
            }
          };
          const cancel = (sourceEvent, reason = "cancel") => {
            if (!editing) return;
            draft = committed;
            dirty = false;
            input.value = committed;
            nativeInvalid = false;
            requestEditing(false, reason, sourceEvent);
            sync();
            if (!controlledEditing && !effectiveDisabled() && !configuration.readonly) {
              queueMicrotask(() => editAction.focus({ preventScroll: true }));
            }
          };
          const forceClosed = (reason, source) => {
            if (!editing) return;
            draft = committed;
            dirty = false;
            input.value = committed;
            internalEditing = false;
            applyEditing(false);
            notifyEdit(false, reason, source, true);
          };

          const onClick = (event) => {
            const path = event.composedPath();
            if (path.includes(editAction)) startEdit(editAction);
            else if (path.includes(submitAction)) submit("submit", event);
            else if (path.includes(cancelAction)) cancel(event);
          };
          const onPointerDown = (event) => {
            const path = event.composedPath();
            if (!path.includes(submitAction) && !path.includes(cancelAction)) return;
            actionPressPending = true;
            setTimeout(() => { actionPressPending = false; }, 0);
          };
          const onInput = () => {
            draft = input.value;
            dirty = draft !== committed;
            clearNativeInvalid();
            sync();
          };
          const onKeyDown = (event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              cancel(event);
            } else if (
              event.key === "Enter"
              && !event.isComposing
              && !composing
              && ["enter", "both"].includes(configuration.submitMode)
            ) {
              event.preventDefault();
              submit("submit", event);
            }
          };
          const onFocusOut = (event) => {
            if (!editing || !["blur", "both"].includes(configuration.submitMode)) return;
            const scheduled = generation;
            queueMicrotask(() => {
              if (!active || scheduled !== generation || !editing || actionPressPending) return;
              const activeElement = root.ownerDocument.activeElement;
              if (root.contains(activeElement) || event.relatedTarget && root.contains(event.relatedTarget)) return;
              submit("blur", event);
            });
          };
          const onInvalid = (event) => {
            nativeInvalid = true;
            if (!editing) requestEditing(true, "invalid", input, { focus: true, forced: true });
            sync();
            void event;
          };
          const onReset = (event) => {
            const scheduled = generation;
            setTimeout(() => {
              if (!active || event.defaultPrevented || scheduled !== generation) return;
              const previous = committed;
              const next = data.value;
              nativeInvalid = false;
              dirty = false;
              draft = next;
              if (controlledValue) {
                input.value = committed;
                if (next !== committed) {
                  onValueChange?.(next, {
                    value: next,
                    previousValue: previous,
                    controlled: true,
                    source: "reset",
                    sourceEvent: event,
                  });
                }
              } else {
                committed = next;
                input.value = next;
                if (next !== previous) {
                  onValueChange?.(next, {
                    value: next,
                    previousValue: previous,
                    controlled: false,
                    source: "reset",
                    sourceEvent: event,
                  });
                }
              }
              if (editing) requestEditing(false, "reset", event);
              sync();
            }, 0);
          };
          const onCompositionStart = () => { composing = true; };
          const onCompositionEnd = () => { composing = false; };

          root.addEventListener("click", onClick, true);
          root.addEventListener("pointerdown", onPointerDown, true);
          root.addEventListener("focusout", onFocusOut);
          input.addEventListener("input", onInput);
          input.addEventListener("keydown", onKeyDown);
          input.addEventListener("invalid", onInvalid);
          input.addEventListener("compositionstart", onCompositionStart);
          input.addEventListener("compositionend", onCompositionEnd);
          input.form?.addEventListener("reset", onReset);
          const fieldsetObservers = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const observer = new MutationObserver(() => {
              if (effectiveDisabled()) forceClosed("disabled", ancestor);
              sync();
            });
            observer.observe(ancestor, { attributes: true, childList: true, attributeFilter: ["disabled"] });
            fieldsetObservers.push(observer);
          }

          const stop = effect(() => {
            clientValue = props.value;
            clientEditing = props.editing;
            onValueChange = typeof props.onValueChange === "function" ? props.onValueChange : null;
            onEditChange = typeof props.onEditChange === "function" ? props.onEditChange : null;
            if (props.onValueChange != null && onValueChange === null) report("onValueChange", props.onValueChange);
            else invalidEpisodes.delete("onValueChange");
            if (props.onEditChange != null && onEditChange === null) report("onEditChange", props.onEditChange);
            else invalidEpisodes.delete("onEditChange");

            configuration = {
              required: field ? field.required : boolean("required", data.required),
              disabled: field ? field.disabled : Boolean(form?.disabled) || boolean("disabled", data.disabled),
              readonly: field ? field.readonly : Boolean(form?.readonly) || boolean("readonly", data.readonly),
              invalid: field ? field.invalid : boolean("invalid", data.invalid),
              submitMode: choice("submitMode", data.submitMode, ["enter", "blur", "both", "explicit"]),
              selectOnFocus: boolean("selectOnFocus", data.selectOnFocus),
              actionPosition: choice("actionPosition", data.actionPosition, ["inside", "outside"]),
              variant: choice("variant", data.variant, ["outline", "filled", "plain"]),
              size: choice("size", data.size, ["sm", "md", "lg"]),
            };

            if (clientValue === undefined || clientValue === null) {
              invalidEpisodes.delete("value");
              controlledValue = false;
            } else if (typeof clientValue === "string" && !clientValue.includes("\0")) {
              invalidEpisodes.delete("value");
              controlledValue = true;
              committed = clientValue.replace(/\r\n?/g, "\n");
              if (!editing || !dirty) {
                draft = committed;
                input.value = committed;
              }
            } else {
              report("value", clientValue, "; releasing control to the committed value");
              controlledValue = false;
            }

            if (clientEditing === undefined || clientEditing === null) {
              invalidEpisodes.delete("editing");
              controlledEditing = false;
              applyEditing(internalEditing, { focus: internalEditing && pendingFocus });
            } else if (typeof clientEditing === "boolean") {
              invalidEpisodes.delete("editing");
              controlledEditing = true;
              internalEditing = clientEditing;
              applyEditing(clientEditing, { focus: clientEditing && !editing });
            } else {
              report("editing", clientEditing, "; releasing control to committed mode");
              controlledEditing = false;
              applyEditing(internalEditing);
            }
            pendingFocus = false;
            if (effectiveDisabled()) forceClosed("disabled", input);
            else if (configuration.readonly) forceClosed("readonly", input);
            sync();
          });

          const placeholderBinding = i18n && data.catalogPlaceholder
            ? i18n.bind({
                message: "citry-ui-editable-click-to-edit",
                onChange: (text) => {
                  data.placeholder = text;
                  input.placeholder = text;
                  sync();
                },
              })
            : null;

          root.setAttribute("data-citry-editable-initialized", "");
          input.value = draft;
          applyEditing(internalEditing, { focus: internalEditing });
          sync();

          return () => {
            active = false;
            generation += 1;
            root[editableHandoffKey] = {
              serverFingerprint,
              committed,
              draft,
              dirty,
              internalEditing,
            };
            stop?.();
            placeholderBinding?.dispose();
            fieldsetObservers.forEach((observer) => observer.disconnect());
            root.removeEventListener("click", onClick, true);
            root.removeEventListener("pointerdown", onPointerDown, true);
            root.removeEventListener("focusout", onFocusOut);
            input.removeEventListener("input", onInput);
            input.removeEventListener("keydown", onKeyDown);
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("compositionstart", onCompositionStart);
            input.removeEventListener("compositionend", onCompositionEnd);
            input.form?.removeEventListener("reset", onReset);
            if (nativeInvalid) field?.setNativeInvalid(false);
            root.removeAttribute("data-citry-editable-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-editable) {
          --_cui-editable-background: var(--cui-editable-background, Canvas);
          --_cui-editable-foreground: var(--cui-editable-foreground, CanvasText);
          --_cui-editable-border-color: var(--cui-editable-border-color, light-dark(#d0d5dd, #535862));
          --_cui-editable-hover-border-color: var(--cui-editable-hover-border-color, light-dark(#667085, #a4a7ae));
          --_cui-editable-focus-color: var(--cui-editable-focus-color, Highlight);
          --_cui-editable-invalid-border-color: var(--cui-editable-invalid-border-color, light-dark(#d92d20, #f97066));
          --_cui-editable-muted-color: var(--cui-editable-muted-color, light-dark(#667085, #a4a7ae));
          --_cui-editable-action-background: var(
            --cui-editable-action-background,
            color-mix(in srgb, CanvasText 7%, Canvas)
          );
          --_cui-editable-action-foreground: var(--cui-editable-action-foreground, CanvasText);
          --_cui-editable-radius: var(--cui-editable-radius, .5rem);
          --_cui-editable-height: var(--cui-editable-height, 2.5rem);
          --_cui-editable-padding: var(--cui-editable-padding, .5rem .75rem);
          --_cui-editable-action-size: var(--cui-editable-action-size, 1.75rem);
          --_cui-editable-gap: var(--cui-editable-gap, .375rem);
          box-sizing: border-box;
          display: grid;
          min-inline-size: 0;
          color: var(--_cui-editable-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
        }
        :where(.cui-editable[data-size="sm"]) {
          --_cui-editable-height: 2.25rem;
          --_cui-editable-padding: .375rem .625rem;
          --_cui-editable-action-size: 1.5rem;
          font-size: .875rem;
        }
        :where(.cui-editable[data-size="lg"]) {
          --_cui-editable-height: 2.75rem;
          --_cui-editable-padding: .625rem .875rem;
          --_cui-editable-action-size: 2rem;
          font-size: 1.0625rem;
        }
        :where(.cui-editable__preview), :where(.cui-editable__edit-surface) {
          box-sizing: border-box;
          min-inline-size: 0;
          min-block-size: var(--_cui-editable-height);
        }
        :where(.cui-editable__preview) {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: var(--_cui-editable-gap);
          padding: var(--_cui-editable-padding);
          border: 1px solid var(--_cui-editable-border-color);
          border-radius: var(--_cui-editable-radius);
          background: var(--_cui-editable-background);
        }
        :where(.cui-editable [data-citry-ui-part="preview-value"]) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where(.cui-editable[data-empty] [data-citry-ui-part="preview-value"]) {
          color: var(--_cui-editable-muted-color);
        }
        :where(.cui-editable__edit-surface) {
          position: relative;
          display: grid;
          min-inline-size: 0;
        }
        :where(.cui-editable__input) {
          box-sizing: border-box;
          inline-size: 100%;
          min-inline-size: 0;
          min-block-size: var(--_cui-editable-height);
          padding: var(--_cui-editable-padding);
          border: 1px solid var(--_cui-editable-border-color);
          border-radius: var(--_cui-editable-radius);
          background: var(--_cui-editable-background);
          color: var(--_cui-editable-foreground);
          font: inherit;
        }
        :where(.cui-editable[data-action-position="inside"] .cui-editable__input) {
          padding-inline-end: calc(var(--_cui-editable-action-size) * 2 + var(--_cui-editable-gap) * 3);
        }
        :where(.cui-editable__actions) {
          display: inline-flex;
          gap: var(--_cui-editable-gap);
        }
        :where(.cui-editable[data-action-position="inside"] .cui-editable__actions) {
          position: absolute;
          inset-inline-end: var(--_cui-editable-gap);
          inset-block-start: 50%;
          transform: translateY(-50%);
        }
        :where(.cui-editable[data-action-position="outside"] .cui-editable__edit-surface) {
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: var(--_cui-editable-gap);
        }
        :where(.cui-editable__action) {
          box-sizing: border-box;
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-editable-action-size);
          block-size: var(--_cui-editable-action-size);
          min-inline-size: var(--_cui-editable-action-size);
          margin: 0;
          padding: 0;
          border: 1px solid transparent;
          border-radius: calc(var(--_cui-editable-radius) - .125rem);
          background: var(--_cui-editable-action-background);
          color: var(--_cui-editable-action-foreground);
          font: inherit;
          line-height: 1;
          cursor: pointer;
        }
        :where(.cui-editable__action:focus-visible), :where(.cui-editable__input:focus-visible) {
          outline: 2px solid var(--_cui-editable-focus-color);
          outline-offset: 2px;
        }
        :where(.cui-editable__action:disabled) { cursor: not-allowed; opacity: .55; }
        :where(.cui-editable[data-variant="filled"] .cui-editable__preview),
        :where(.cui-editable[data-variant="filled"] .cui-editable__input) {
          background: color-mix(in srgb, CanvasText 6%, Canvas);
          border-color: transparent;
        }
        :where(.cui-editable[data-variant="plain"] .cui-editable__preview),
        :where(.cui-editable[data-variant="plain"] .cui-editable__input) {
          border-color: transparent;
          border-radius: 0;
          background: transparent;
        }
        :where(.cui-editable[data-invalid] .cui-editable__preview),
        :where(.cui-editable[data-invalid] .cui-editable__input) {
          border-color: var(--_cui-editable-invalid-border-color);
        }
        :where(.cui-editable[data-disabled]), :where(.cui-editable[data-readonly]) { opacity: .72; }
        :where(.cui-editable:not([data-citry-editable-initialized]) .cui-editable__preview),
        :where(.cui-editable:not([data-citry-editable-initialized]) .cui-editable__actions) { display: none; }
        :where(.cui-editable[data-citry-editable-initialized]:not([data-editing]) .cui-editable__edit-surface) {
          display: none;
        }
        :where(.cui-editable[data-citry-editable-initialized][data-editing] .cui-editable__preview) {
          display: none;
        }
        @media (hover: hover) {
          :where(.cui-editable:not([data-disabled]):not([data-readonly]) .cui-editable__preview:hover),
          :where(.cui-editable__input:not(:disabled):not([readonly]):hover) {
            border-color: var(--_cui-editable-hover-border-color);
          }
        }
        @media (forced-colors: active) {
          :where(.cui-editable__preview), :where(.cui-editable__input), :where(.cui-editable__action) {
            border-color: ButtonText;
          }
          :where(.cui-editable[data-invalid] .cui-editable__preview),
          :where(.cui-editable[data-invalid] .cui-editable__input) { border-color: Mark; }
        }
        @media print {
          :where(.cui-editable__edit-surface), :where(.cui-editable__action) { display: none !important; }
          :where(.cui-editable__preview) {
            display: block !important;
            min-block-size: auto;
            padding: 0;
            border: 0;
            background: transparent;
            color: CanvasText;
          }
        }
        @media (max-width: 24rem) {
          :where(.cui-editable[data-action-position="outside"] .cui-editable__edit-surface) {
            grid-template-columns: minmax(0, 1fr);
          }
        }
      }
    """

    messages = """
      citry-ui-editable-click-to-edit = Click to edit
      citry-ui-editable-edit = Edit
      citry-ui-editable-save = Save
      citry-ui-editable-cancel = Cancel
    """


__all__ = [
    "CEditable",
    "CEditableActionPosition",
    "CEditableEditChangeDetail",
    "CEditableEditReason",
    "CEditableSize",
    "CEditableSubmitMode",
    "CEditableValueChangeDetail",
    "CEditableValueSource",
    "CEditableVariant",
]
