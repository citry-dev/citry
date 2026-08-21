"""Styled string-valued PinInput component."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._form_control_runtime import (
    FORM_CONTROL_RUNTIME_DEPENDENCY,
    FORM_CONTROL_STYLE_DEPENDENCY,
)
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
    validate_optional_string,
)

CPinInputType = Literal["numeric", "alphabetic", "alphanumeric"]
CPinInputSize = Literal["sm", "md", "lg"]
CPinInputVariant = Literal["outline", "subtle"]
CPinInputChangeSource = Literal["input", "paste", "autofill", "composition", "reset"]
CPinInputInvalidSource = Literal["input", "paste", "autofill", "composition"]

_PATTERNS = {
    "numeric": re.compile(r"^[0-9]*$"),
    "alphabetic": re.compile(r"^[A-Za-z]*$"),
    "alphanumeric": re.compile(r"^[A-Za-z0-9]*$"),
}
_HTML_CLASSES = {
    "numeric": "0-9",
    "alphabetic": "A-Za-z",
    "alphanumeric": "A-Za-z0-9",
}
_RUNTIME_PREFIXES = ("data-citry-", "data-cpi", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "data-citry-pin-input-initialized",
        "data-citry-ui-part",
        "data-complete",
        "data-disabled",
        "data-filled",
        "data-focused",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "id",
    }
)
_INPUT_OWNED = frozenset(
    {
        FIELD_CONTROL_MARKER,
        "aria-invalid",
        "data-citry-ui-part",
        "disabled",
        "form",
        "id",
        "inputmode",
        "maxlength",
        "name",
        "pattern",
        "readonly",
        "required",
        "type",
        "value",
    }
)


class CPinInputValueChangeDetail(TypedDict):
    value: str
    previousValue: str
    controlled: bool
    source: CPinInputChangeSource
    sourceEvent: object | None


class CPinInputCompleteDetail(TypedDict):
    value: str
    controlled: bool
    source: CPinInputChangeSource
    sourceEvent: object | None


class CPinInputInvalidDetail(TypedDict):
    value: str
    rejected: str
    source: CPinInputInvalidSource
    sourceEvent: object | None


class CPinInputFocusChangeDetail(TypedDict):
    focused: bool
    sourceEvent: object | None


@dataclass(frozen=True, slots=True)
class CPinInputSeparatorSlotData:
    index: int


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(destination: str, value: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CPinInput {destination} must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"CPinInput {destination}")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CPinInput {destination} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CPinInput {destination} cannot contain runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CPinInput {destination} cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in owned:
            raise ValueError(f"CPinInput {destination} cannot dynamically bind owned attribute {key!r}.")
    return copied


def _pop_case_insensitive(attrs: dict[str, object], name: str) -> object | None:
    found: object | None = None
    for authored_name in tuple(attrs):
        if authored_name.casefold() == name:
            found = attrs.pop(authored_name)
    return found


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    value = const_value(value)
    if value is None and optional:
        return None
    if not isinstance(value, str):
        expected = "a string or None" if optional else "a string"
        raise TypeError(f"CPinInput {name} must be {expected}, got {value!r}.")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in normalized or "\n" in normalized:
        raise ValueError(f"CPinInput {name} must be one line without U+0000.")
    return normalized


def _value(value: object, kind: str, length: int) -> str:
    normalized = cast("str", _plain("value", value))
    if len(normalized) > length:
        raise ValueError(f"CPinInput value may contain at most {length} characters.")
    if not _PATTERNS[kind].fullmatch(normalized):
        raise ValueError(f"CPinInput value contains characters outside its {kind} alphabet.")
    return normalized


def _separator_indices(value: object, length: int) -> tuple[int, ...]:
    value = const_value(value)
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError("CPinInput separator_after must be a sequence of integers or None.")
    result: list[int] = []
    for position, raw_item in enumerate(value):
        item = const_value(raw_item)
        if type(item) is not int:
            raise TypeError(f"CPinInput separator_after[{position}] must be an integer, got {item!r}.")
        if not 0 <= item < length - 1:
            raise ValueError(f"CPinInput separator_after[{position}] must be between 0 and {length - 2}.")
        if item in result:
            raise ValueError(f"CPinInput separator_after contains duplicate index {item}.")
        result.append(item)
    return tuple(sorted(result))


class CPinInput(LibraryComponent):
    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: str = ""
        name: str | None = None
        form: str | None = None
        id: str | None = None
        length: int = 6
        type: CPinInputType = "numeric"
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        mask: bool = False
        one_time_code: bool = True
        placeholder: str | None = "○"
        attached: bool = False
        separator_after: Sequence[int] | None = None
        label: str | None = None
        size: CPinInputSize = "md"
        variant: CPinInputVariant = "outline"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        separator: SlotInput[CPinInputSeparatorSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        cached = getattr(self, "_cui_pin_input_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        raw_length = const_value(kwargs.length)
        if type(raw_length) is not int:
            raise TypeError(f"CPinInput length must be an integer, got {raw_length!r}.")
        if not 1 <= raw_length <= 32:
            raise ValueError("CPinInput length must be between 1 and 32.")
        kind = const_value(kwargs.type)
        size = const_value(kwargs.size)
        variant = const_value(kwargs.variant)
        validate_choice("CPinInput", "type", kind, tuple(_PATTERNS))
        validate_choice("CPinInput", "size", size, ("sm", "md", "lg"))
        validate_choice("CPinInput", "variant", variant, ("outline", "subtle"))
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CPinInput", input_name, getattr(kwargs, input_name))
        for input_name in ("mask", "one_time_code", "attached"):
            validate_boolean("CPinInput", input_name, getattr(kwargs, input_name))
        validate_optional_string("CPinInput", "label", kwargs.label)

        value = _value(kwargs.value, kind, raw_length)
        placeholder = _plain("placeholder", kwargs.placeholder, optional=True)
        if placeholder is not None and len(placeholder) != 1:
            raise ValueError("CPinInput placeholder must be one Unicode code point or None.")
        separators = _separator_indices(kwargs.separator_after, raw_length)
        if slots.separator is not None and not separators:
            raise ValueError("CPinInput separator slot requires at least one separator_after boundary.")

        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CPinInput", "name", name)
        validate_html_id("CPinInput", form_input)
        validate_html_id("CPinInput", supplied_id)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None:
            supplied = [
                input_name
                for input_name in ("required", "disabled", "readonly", "invalid")
                if getattr(kwargs, input_name) is not None
            ]
            if supplied:
                raise ValueError(f"CPinInput inside CField cannot set Field-owned state: {', '.join(supplied)}.")
            if kwargs.label is not None:
                raise ValueError("CPinInput inside CField cannot also set label; use the CField label slot.")
            field.register_control("CPinInput")
        field_control_id = str(field.control_id) if field is not None else None
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(
                f"CPinInput id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}."
            )
        public_id = supplied_id or field_control_id or f"cui-pin-input-{self.id}"

        root_attrs = _attrs("attrs", kwargs.attrs, _ROOT_OWNED)
        input_attrs = _attrs("input_attrs", kwargs.input_attrs, _INPUT_OWNED)
        authored_label = _pop_case_insensitive(input_attrs, "aria-label")
        authored_labelledby = _pop_case_insensitive(input_attrs, "aria-labelledby")
        authored_describedby = _pop_case_insensitive(input_attrs, "aria-describedby")
        authored_errormessage = _pop_case_insensitive(input_attrs, "aria-errormessage")
        authored_autocomplete = _pop_case_insensitive(input_attrs, "autocomplete")
        authored_dir = _pop_case_insensitive(input_attrs, "dir")
        label = cast("str | None", _plain("label", kwargs.label, optional=True))
        if field is None and label is None and authored_label is None and authored_labelledby is None:
            raise ValueError("Standalone CPinInput requires label or input_attrs aria-label/aria-labelledby.")
        for input_name, authored in (
            ("aria-label", authored_label),
            ("aria-labelledby", authored_labelledby),
            ("aria-describedby", authored_describedby),
            ("aria-errormessage", authored_errormessage),
            ("autocomplete", authored_autocomplete),
            ("dir", authored_dir),
        ):
            if authored is not None and not isinstance(authored, str):
                raise TypeError(f"CPinInput input_attrs {input_name} must be a string.")

        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CPinInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CPinInput inside CForm cannot target a different native form owner.")
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
            cast("str | None", authored_describedby),
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            cast("str | None", authored_errormessage) if invalid else None,
        )
        aria_labelledby = merge_idrefs(
            field.label_id if field is not None else None,
            cast("str | None", authored_labelledby),
        )
        autocomplete = cast("str | None", authored_autocomplete) or ("one-time-code" if kwargs.one_time_code else None)
        input_dir = cast("str | None", authored_dir) or "ltr"
        html_pattern = f"[{_HTML_CLASSES[kind]}]{{{raw_length}}}"
        cells = [
            {
                "index": index,
                "character": ("•" if kwargs.mask else value[index]) if index < len(value) else (placeholder or ""),
                "filled": index < len(value),
                "separator": index in separators,
            }
            for index in range(raw_length)
        ]

        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": f"{public_id}-root",
            "name": name,
            "form": form_owner,
            "value": value,
            "filled": bool(value),
            "complete": len(value) == raw_length,
            "length": raw_length,
            "inputmode": "numeric" if kind == "numeric" else "text",
            "pattern": html_pattern,
            "autocomplete": autocomplete,
            "input_dir": input_dir,
            "native_placeholder": (placeholder or "") * raw_length,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "mask": kwargs.mask,
            "attached": kwargs.attached,
            "size": size,
            "variant": variant,
            "cells": cells,
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
            "aria_label": cast("str | None", authored_label) or label,
            "aria_labelledby": aria_labelledby,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "field_control": field is not None,
        }
        self._cui_pin_input_data = {
            "id": public_id,
            "rootId": f"{public_id}-root",
            "name": name,
            "form": form_owner,
            "value": value,
            "initialValue": value,
            "length": raw_length,
            "kind": kind,
            "pattern": html_pattern,
            "inputmode": "numeric" if kind == "numeric" else "text",
            "autocomplete": autocomplete,
            "placeholder": placeholder,
            "disabled": disabled,
            "readonly": readonly,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "required": required,
            "invalid": invalid,
            "mask": kwargs.mask,
            "attached": kwargs.attached,
            "variant": variant,
            "size": size,
            "label": cast("str | None", authored_label) or label,
            "labelledby": aria_labelledby,
            "describedby": described_by,
            "errormessage": error_message,
        }
        self._cui_pin_input_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return self._snapshot(kwargs, slots)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        self._snapshot(kwargs, slots)
        return self._cui_pin_input_data

    template = """
      <div
        class="cui-pin-input"
        c-id="root_id"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-filled="filled"
        c-data-complete="complete"
        c-data-attached="attached"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="root_attrs"
        data-citry-ui-part="pin-input"
      >
        <input
          c-id="public_id"
          c-name="name"
          c-form="form"
          type="text"
          c-value="value"
          c-maxlength="length"
          c-pattern="pattern"
          c-inputmode="inputmode"
          c-autocomplete="autocomplete"
          c-dir="input_dir"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
          c-placeholder="native_placeholder"
          c-required="required"
          c-disabled="disabled"
          c-readonly="readonly"
          c-aria-label="aria_label"
          c-aria-labelledby="aria_labelledby"
          c-aria-describedby="aria_describedby"
          c-aria-errormessage="aria_errormessage"
          c-aria-invalid="'true' if invalid else None"
          c-data-citry-field-control="field_control"
          c-bind="input_attrs"
          data-citry-ui-part="input"
        />
        <span aria-hidden="true" data-citry-ui-part="cells">
          <span c-for="cell in cells" c-data-index="cell['index']" c-data-filled="cell['filled']" c-data-masked="cell['filled'] and mask" data-citry-ui-part="cell">
            <span data-citry-ui-part="character">{{ cell['character'] }}</span>
            <span data-citry-ui-part="caret"></span>
            <span c-if="cell['separator']" data-citry-ui-part="separator">
              <c-slot name="separator" c-index="cell['index']" />
            </span>
          </span>
        </span>
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, mask: {},
          variant: {}, size: {}, onValueChange: {}, onComplete: {}, onValueInvalid: {}, onFocusChange: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const input = root.querySelector(':scope > [data-citry-ui-part="input"]');
          const cellsHost = root.querySelector(':scope > [data-citry-ui-part="cells"]');
          const cells = Array.from(cellsHost?.querySelectorAll(':scope > [data-citry-ui-part="cell"]') ?? []);
          const characters = cells.map(cell => cell.querySelector(':scope > [data-citry-ui-part="character"]'));
          if (!(input instanceof HTMLInputElement && cellsHost instanceof HTMLElement) || cells.length !== data.length || characters.some(node => !(node instanceof HTMLElement))) {
            throw new Error('[citry-ui] CPinInput settled anatomy is invalid.');
          }
          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CPinInput form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CPinInput');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          const accepted = data.kind === 'numeric' ? /[0-9]/ : data.kind === 'alphabetic' ? /[A-Za-z]/ : /[A-Za-z0-9]/;
          let current = data.value;
          let committed = data.value;
          const initialValue = data.initialValue;
          let controlled = false;
          let composing = false;
          let focused = false;
          let nativeInvalid = false;
          let pendingSource = 'input';
          let configuration = null;
          let lastComplete = current.length === data.length ? current : null;
          let invalidGeneration = 0;

          const normalize = raw => {
            if (typeof raw !== 'string') return undefined;
            const values = Array.from(raw).filter(character => accepted.test(character));
            return values.slice(0, data.length).join('');
          };
          const exact = raw => {
            const normalized = normalize(raw);
            return normalized !== undefined && normalized === raw ? normalized : undefined;
          };
          const sourceFor = event => {
            const type = event?.inputType ?? '';
            if (pendingSource === 'paste' || type.includes('Paste')) return 'paste';
            if (type === 'insertReplacementText' || type === 'insertFromDrop') return 'autofill';
            if (pendingSource === 'composition' || type.includes('Composition')) return 'composition';
            return 'input';
          };
          const resolveConfiguration = () => ({
            required: field ? field.required : resolver.boolean('required', data.required),
            disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(input),
            readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
            mask: resolver.boolean('mask', data.mask),
            variant: resolver.choice('variant', data.variant, ['outline', 'subtle']),
            size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
          });
          const selectionIndex = () => {
            const start = input.selectionStart ?? current.length;
            if (!focused) return -1;
            return Math.max(0, Math.min(start, data.length - 1));
          };
          const syncRelationships = invalid => runtime.relationships([input], field, {
            label: data.label, labelledby: data.labelledby, describedby: data.describedby,
            errormessage: data.errormessage, control: input,
            required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
          }, invalid);
          const render = () => owned(() => {
            if (input.value !== current && !composing) input.value = current;
            const active = selectionIndex();
            cells.forEach((cell, index) => {
              const filled = index < current.length;
              characters[index].textContent = filled ? (configuration.mask ? '•' : current[index]) : (data.placeholder ?? '');
              cell.toggleAttribute('data-filled', filled);
              cell.toggleAttribute('data-masked', filled && configuration.mask);
              cell.toggleAttribute('data-active', index === active);
            });
            const invalid = configuration.invalid || nativeInvalid;
            runtime.states(root, {
              required: configuration.required, disabled: configuration.disabled, readonly: configuration.readonly,
              invalid, focused, filled: current.length > 0, complete: current.length === data.length,
            });
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            input.required = configuration.required;
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            input.pattern = data.pattern;
            input.maxLength = data.length;
            input.inputMode = data.inputmode;
            input.autocomplete = data.autocomplete ?? '';
            input.name = data.name ?? '';
            if (data.form) input.setAttribute('form', data.form); else input.removeAttribute('form');
            syncRelationships(invalid);
          });
          const invalidNotice = (raw, next, source, event) => {
            const rawCharacters = Array.from(raw);
            const rejectedCharacters = rawCharacters.filter(character => !accepted.test(character));
            const acceptedCharacters = rawCharacters.filter(character => accepted.test(character));
            const rejected = rejectedCharacters.join('') + acceptedCharacters.slice(data.length).join('');
            if (!rejected) return;
            resolver.callback('onValueInvalid')?.({ value: next, rejected, source, sourceEvent: event });
          };
          const complete = (next, source, event) => {
            if (next.length !== data.length) { lastComplete = null; return; }
            if (next === lastComplete) return;
            if (!controlled) lastComplete = next;
            resolver.callback('onComplete')?.(next, { value: next, controlled, source, sourceEvent: event });
          };
          const request = (raw, source, event) => {
            const next = normalize(raw);
            if (next === undefined) return false;
            invalidNotice(raw, next, source, event);
            if (next === current) { input.value = current; render(); return false; }
            const previousValue = current;
            if (!controlled) { current = next; committed = next; }
            resolver.callback('onValueChange')?.(next, { value: next, previousValue, controlled, source, sourceEvent: event });
            complete(next, source, event);
            if (controlled) input.value = current;
            nativeInvalid = false;
            field?.setNativeInvalid(false);
            render();
            return true;
          };
          const syncSelection = () => render();
          const selectCell = index => {
            const position = Math.min(index, current.length);
            input.focus({ preventScroll: true });
            if (position < current.length) input.setSelectionRange(position, position + 1, 'forward');
            else input.setSelectionRange(position, position, 'none');
            render();
          };

          const reset = runtime.registerReset(root, input, {
            reset: event => {
              lastComplete = initialValue.length === data.length ? initialValue : null;
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              if (controlled) resolver.callback('onValueChange')?.(initialValue, {
                value: initialValue, previousValue: current, controlled: true, source: 'reset', sourceEvent: event,
              });
              else { current = initialValue; committed = initialValue; input.value = current; }
              render();
            },
            invalidate: () => { invalidGeneration += 1; },
          });
          const stopFieldset = runtime.watchFieldset(root, input, () => { configuration = resolveConfiguration(); render(); });

          listeners.add(input, 'beforeinput', event => {
            pendingSource = event.inputType?.includes('Paste') ? 'paste'
              : event.inputType === 'insertReplacementText' ? 'autofill'
              : event.inputType?.includes('Composition') ? 'composition' : 'input';
          });
          listeners.add(input, 'paste', () => { pendingSource = 'paste'; });
          listeners.add(input, 'compositionstart', () => { composing = true; pendingSource = 'composition'; });
          listeners.add(input, 'compositionend', event => {
            composing = false;
            request(input.value, 'composition', event);
            pendingSource = 'input';
          });
          listeners.add(input, 'input', event => {
            if (composing || event.isComposing) return;
            request(input.value, sourceFor(event), event);
            pendingSource = 'input';
          });
          listeners.add(input, 'select', syncSelection);
          listeners.add(input, 'keyup', syncSelection);
          listeners.add(input, 'focus', event => {
            focused = true;
            render();
            resolver.callback('onFocusChange')?.(true, { focused: true, sourceEvent: event });
          });
          listeners.add(input, 'blur', event => {
            focused = false;
            render();
            resolver.callback('onFocusChange')?.(false, { focused: false, sourceEvent: event });
          });
          listeners.add(input, 'keydown', event => {
            if (composing || event.isComposing || event.keyCode === 229) return;
            if (event.key === 'Home') { event.preventDefault(); input.setSelectionRange(0, current.length ? 1 : 0, 'forward'); render(); }
            else if (event.key === 'End') {
              event.preventDefault();
              const start = current.length >= data.length ? data.length - 1 : current.length;
              input.setSelectionRange(start, start < current.length ? start + 1 : start, 'forward');
              render();
            }
          });
          cells.forEach((cell, index) => listeners.add(cell, 'pointerdown', event => {
            if (configuration.disabled) return;
            event.preventDefault();
            selectCell(index);
          }));
          listeners.add(input, 'invalid', event => {
            event.preventDefault();
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            render();
            const token = ++invalidGeneration;
            runtime.invalidFocus(root, input, () => token === invalidGeneration);
          }, true);

          effect(() => {
            configuration = resolveConfiguration();
            const requested = props.value;
            if (requested === undefined) {
              if (controlled) { controlled = false; current = committed; input.value = current; }
              resolver.clear('value');
            } else {
              const normalized = exact(requested);
              if (normalized === undefined) resolver.report('value', requested);
              else {
                resolver.clear('value'); controlled = true; current = normalized; input.value = current;
                lastComplete = current.length === data.length ? current : null;
              }
            }
            render();
          });
          mutations.start(() => render());
          owned(() => root.setAttribute('data-citry-pin-input-initialized', ''));
          render();

          return () => {
            invalidGeneration += 1;
            listeners.stop();
            mutations.stop();
            stopFieldset();
            reset();
            if (nativeInvalid) field?.setNativeInvalid(false);
            owned(() => root.removeAttribute('data-citry-pin-input-initialized'));
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = [
    "CPinInput",
    "CPinInputChangeSource",
    "CPinInputCompleteDetail",
    "CPinInputFocusChangeDetail",
    "CPinInputInvalidDetail",
    "CPinInputInvalidSource",
    "CPinInputSeparatorSlotData",
    "CPinInputSize",
    "CPinInputType",
    "CPinInputValueChangeDetail",
    "CPinInputVariant",
]
