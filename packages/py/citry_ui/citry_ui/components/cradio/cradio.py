"""Native Radio Group and Radio components."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_optional_boolean

CRadioOrientation = Literal["vertical", "horizontal"]
CRadioVariant = Literal["solid", "outline"]
CRadioSize = Literal["sm", "md", "lg"]
CRadioLabelPos = Literal["start", "end"]

_RADIO_GROUP_CONTEXT_KEY = "citry_ui_radio_group"
_ORIENTATIONS = ("vertical", "horizontal")
_VARIANTS = ("solid", "outline")
_SIZES = ("sm", "md", "lg")
_LABEL_POSITIONS = ("start", "end")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_GROUP_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-describedby",
        "aria-errormessage",
        "aria-invalid",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-readonly",
        "aria-required",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-invalid",
        "data-label-pos",
        "data-orientation",
        "data-required",
        "data-size",
        "data-value",
        "data-variant",
        FIELD_CONTROL_MARKER,
        "disabled",
        "form",
        "name",
        "role",
        "tabindex",
    }
)
_RADIO_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-checked",
        "data-citry-ui-part",
        "data-disabled",
        "data-value",
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
        "aria-label",
        "aria-labelledby",
        "aria-readonly",
        "aria-required",
        "checked",
        "disabled",
        "form",
        "id",
        "name",
        "readonly",
        "required",
        "role",
        "type",
        "value",
    }
)


class CRadioGroupDefaultSlotData:
    pass


class CRadioGroupLabelSlotData:
    pass


class CRadioDefaultSlotData:
    pass


class CRadioDescriptionSlotData:
    pass


@dataclass(slots=True)
class _RadioEntry:
    value: str
    input_id: str
    disabled: bool


@dataclass(slots=True)
class _RadioRegistry:
    entries: list[_RadioEntry] = field(default_factory=list)

    def register(self, value: str, input_id: str, disabled: bool) -> int:
        self.entries.append(_RadioEntry(value=value, input_id=input_id, disabled=disabled))
        return len(self.entries) - 1


@dataclass(slots=True)
class _RadioServerContext:
    registry: _RadioRegistry
    name: str
    form_owner: str | None
    selected: str | None
    disabled: bool
    first_input_id: str | None


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"Could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _canonical_string(input_name: str, value: object, *, allow_none: bool = False) -> str | None:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        if allow_none:
            return None
        msg = f"{input_name} must be a string."
        raise TypeError(msg)
    canonical = plain.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in canonical:
        msg = f"{input_name} cannot contain U+0000."
        raise ValueError(msg)
    if not canonical:
        msg = f"{input_name} must be non-empty."
        raise ValueError(msg)
    return canonical


def _plain_choice(component: str, input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(f"{component} {input_name}", value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{component} {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _plain_id(component: str, value: object) -> str | None:
    element_id = _canonical_string(f"{component} id", value, allow_none=True)
    if element_id is not None and any(character in "\t\n\f\r " for character in element_id):
        msg = f"{component} id cannot contain ASCII whitespace."
        raise ValueError(msg)
    return element_id


def _copy_attrs(component: str, input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{component} {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs or {})


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _validate_attrs(component: str, attrs: dict[str, object], owned: frozenset[str]) -> None:
    reject_owned_attrs(attrs, owned, component)
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{component} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


class CRadioGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: str
        value: str | None = None
        form: str | None = None
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        orientation: CRadioOrientation = "vertical"
        variant: CRadioVariant = "solid"
        size: CRadioSize = "md"
        label_pos: CRadioLabelPos = "end"
        id: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CRadioGroupDefaultSlotData]
        label: SlotInput[CRadioGroupLabelSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        name = _canonical_string("CRadioGroup name", kwargs.name)
        selected = _canonical_string("CRadioGroup value", kwargs.value, allow_none=True)
        form_owner_input = _plain_id("CRadioGroup form", kwargs.form)
        group_id = _plain_id("CRadioGroup", kwargs.id) or f"cui-radio-group-{self.id}"
        validate_optional_boolean("CRadioGroup", "required", kwargs.required)
        validate_optional_boolean("CRadioGroup", "disabled", kwargs.disabled)
        validate_optional_boolean("CRadioGroup", "invalid", kwargs.invalid)
        orientation = _plain_choice("CRadioGroup", "orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _plain_choice("CRadioGroup", "variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("CRadioGroup", "size", kwargs.size, _SIZES)
        label_pos = _plain_choice("CRadioGroup", "label_pos", kwargs.label_pos, _LABEL_POSITIONS)
        attrs = _copy_attrs("CRadioGroup", "attrs", kwargs.attrs)
        _validate_attrs("CRadioGroup attrs", attrs, _GROUP_OWNED_ATTRS)

        field_context = self.inject(FIELD_CONTEXT_KEY, None)
        form_context = self.inject(FORM_CONTEXT_KEY, None)
        has_label = "label" in self.raw_slots
        if field_context is not None and has_label:
            msg = "CRadioGroup inside CField cannot supply a label slot; CField owns the group label."
            raise ValueError(msg)
        if field_context is None and not has_label:
            msg = "Standalone CRadioGroup requires a label slot."
            raise ValueError(msg)
        if field_context is not None:
            if kwargs.id is not None and group_id != str(field_context.control_id):
                msg = f"CRadioGroup id {group_id!r} conflicts with its CField control_id {field_context.control_id!r}."
                raise ValueError(msg)
            group_id = str(field_context.control_id)
            supplied = [
                key
                for key, value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("invalid", kwargs.invalid),
                )
                if value is not None
            ]
            if supplied:
                msg = f"CRadioGroup inside CField cannot set Field-owned state: {', '.join(supplied)}."
                raise ValueError(msg)
            field_context.register_control("CRadioGroup", supports_required=True, supports_readonly=False)

        form_owner = get_html_form_owner(
            {"form": form_owner_input} if form_owner_input is not None else {},
            component_name="CRadioGroup",
            default=form_context.form_id if form_context is not None else None,
        )
        form_owner = cast("str | None", form_owner)
        if form_context is not None and form_owner != form_context.form_id:
            msg = "CRadioGroup inside CForm cannot target a different native form owner."
            raise ValueError(msg)

        if field_context is not None:
            required = bool(field_context.required)
            disabled = bool(field_context.disabled)
            invalid = bool(field_context.invalid)
            first_input_id = None
            labelledby = str(field_context.label_id)
            describedby = merge_idrefs(
                field_context.description_id if field_context.has_description else None,
                field_context.error_id if field_context.has_error and invalid else None,
            )
        else:
            required = bool(kwargs.required)
            disabled = bool(form_context.disabled if form_context is not None else False) or bool(kwargs.disabled)
            invalid = bool(kwargs.invalid)
            first_input_id = None
            labelledby = None
            describedby = None

        registry = _RadioRegistry()
        context = _RadioServerContext(
            registry=registry,
            name=str(name),
            form_owner=form_owner,
            selected=selected,
            disabled=disabled,
            first_input_id=first_input_id,
        )
        self.provide(_RADIO_GROUP_CONTEXT_KEY, context=context)
        self._radio_registry = registry
        self._radio_selected = selected
        return {
            "id": group_id,
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "orientation": orientation,
            "variant": variant,
            "size": size,
            "label_pos": label_pos,
            "value": selected,
            "has_label": has_label,
            "labelledby": labelledby,
            "describedby": describedby,
            "field_control": field_context is not None,
            "field_supports_required": "true" if field_context is not None else None,
            "field_supports_readonly": "false" if field_context is not None else None,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            msg = "CRadioGroup completed without a render result."
            raise RuntimeError(msg)
        entries = self._radio_registry.entries
        if not entries:
            msg = "CRadioGroup requires at least one descendant CRadio."
            raise ValueError(msg)
        values = [entry.value for entry in entries]
        if len(values) != len(set(values)):
            msg = "CRadioGroup requires every CRadio value to be unique."
            raise ValueError(msg)
        if self._radio_selected is not None and self._radio_selected not in values:
            msg = f"CRadioGroup value {self._radio_selected!r} does not match a CRadio value."
            raise ValueError(msg)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        field_context = self.inject(FIELD_CONTEXT_KEY, None)
        return {
            "value": self._radio_selected,
            "required": bool(field_context.required) if field_context is not None else bool(kwargs.required),
            "disabled": bool(field_context.disabled) if field_context is not None else bool(kwargs.disabled),
            "invalid": bool(field_context.invalid) if field_context is not None else bool(kwargs.invalid),
            "orientation": _plain_choice("CRadioGroup", "orientation", kwargs.orientation, _ORIENTATIONS),
            "variant": _plain_choice("CRadioGroup", "variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("CRadioGroup", "size", kwargs.size, _SIZES),
            "labelPos": _plain_choice("CRadioGroup", "label_pos", kwargs.label_pos, _LABEL_POSITIONS),
        }

    template = """
      <fieldset
        class="cui-radio-group"
        c-id="id"
        c-disabled="disabled"
        c-aria-invalid="'true' if invalid else None"
        c-aria-labelledby="labelledby"
        c-aria-describedby="describedby"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-orientation="orientation"
        c-data-variant="variant"
        c-data-size="size"
        c-data-label-pos="label_pos"
        c-data-value="value"
        c-data-citry-field-control="field_control"
        c-data-citry-field-supports-required="field_supports_required"
        c-data-citry-field-supports-readonly="field_supports_readonly"
        c-bind="attrs"
        data-citry-ui-part="radio-group"
      >
        <c-if cond="has_label">
          <legend data-citry-ui-part="legend">
            <c-slot name="label" />
          </legend>
        </c-if>
        <c-slot required />
      </fieldset>
    """

    js = r"""
      $component({
        props: {
          value: {},
          required: {},
          disabled: {},
          invalid: {},
          orientation: {},
          variant: {},
          size: {},
          label_pos: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const radios = [...root.querySelectorAll('[data-citry-ui-part="input"][type="radio"]')]
            .filter((input) => input.closest('[data-citry-ui-part="radio-group"]') === root);
          if (!radios.length) {
            throw new Error("[citry-ui] CRadioGroup requires at least one owned native radio input.");
          }
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const unregisterCapabilities = field?.registerCapabilities({required: true, readonly: false});
          const allowed = {
            orientation: ["vertical", "horizontal"],
            variant: ["solid", "outline"],
            size: ["sm", "md", "lg"],
            label_pos: ["start", "end"],
          };
          const invalidEpisodes = new Set();
          const resetTimers = new Set();
          let nativeInvalid = false;
          let controlled = false;
          let controlledValue = null;
          let activationPending = false;
          let reconcileTimer = null;

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CRadioGroup ${name} received invalid client value ${describeValue(value)}; `
                + "using the documented fallback.",
              root,
            );
          };
          const reportFieldOwned = (name, value) => {
            const key = `field:${name}`;
            if (invalidEpisodes.has(key)) {
              return;
            }
            invalidEpisodes.add(key);
            console.error(
              `[citry-ui] CRadioGroup ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describeValue(value)}.`,
              root,
            );
          };
          const canonicalize = (value) => {
            if (typeof value !== "string" || value.includes("\0") || value.length === 0) {
              return undefined;
            }
            return value.replace(/\r\n?/g, "\n");
          };
          const knownValues = new Set(radios.map((input) => input.value));
          const resolveChoice = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (allowed[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
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
          const setCheckedValue = (value) => {
            radios.forEach((input) => {
              input.checked = value !== null && input.value === value;
            });
          };
          const selectedValue = () => radios.find((input) => input.checked)?.value ?? null;
          const syncSelection = () => {
            const value = selectedValue();
            if (value === null) {
              root.removeAttribute("data-value");
            } else {
              root.setAttribute("data-value", value);
            }
            radios.forEach((input) => {
              input.closest('[data-citry-ui-part="radio"]')?.toggleAttribute("data-checked", input.checked);
            });
          };
          const syncInvalid = (invalid) => {
            root.toggleAttribute("data-invalid", invalid);
            if (invalid) {
              root.setAttribute("aria-invalid", "true");
            } else {
              root.removeAttribute("aria-invalid");
            }
            radios.forEach((input) => {
              if (invalid) {
                input.setAttribute("aria-invalid", "true");
              } else {
                input.removeAttribute("aria-invalid");
              }
            });
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
                  invalidEpisodes.delete(`field:${name}`);
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
            root.disabled = disabled;
            root.toggleAttribute("data-required", required);
            root.toggleAttribute("data-disabled", root.matches(":disabled"));
            root.dataset.orientation = resolveChoice("orientation", data.orientation);
            root.dataset.variant = resolveChoice("variant", data.variant);
            root.dataset.size = resolveChoice("size", data.size);
            root.dataset.labelPos = resolveChoice("label_pos", data.labelPos);
            radios.forEach((input) => {
              input.required = required;
              input.closest('[data-citry-ui-part="radio"]')?.toggleAttribute(
                "data-disabled",
                input.matches(":disabled"),
              );
            });
            syncInvalid(externalInvalid || nativeInvalid);
            syncSelection();
          };
          const clearNativeInvalidWhenValid = () => {
            if (!nativeInvalid || !radios.every((input) => input.validity.valid)) {
              return;
            }
            nativeInvalid = false;
            field?.setNativeInvalid(false);
          };
          const applyControlled = () => {
            const supplied = props.value;
            if (supplied === undefined) {
              controlled = false;
              invalidEpisodes.delete("value");
              return;
            }
            if (supplied === null) {
              controlled = true;
              controlledValue = null;
              invalidEpisodes.delete("value");
              setCheckedValue(null);
              return;
            }
            const value = canonicalize(supplied);
            if (value === undefined || !knownValues.has(value)) {
              reportInvalid("value", supplied);
              if (!controlled) {
                setCheckedValue(data.value);
              }
              return;
            }
            invalidEpisodes.delete("value");
            controlled = true;
            controlledValue = value;
            setCheckedValue(value);
          };
          const reconcile = () => {
            reconcileTimer = null;
            activationPending = false;
            applyControlled();
            clearNativeInvalidWhenValid();
            applyState();
          };
          const scheduleReconcile = () => {
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            reconcileTimer = setTimeout(reconcile, 0);
          };
          const onInput = (event) => {
            if (!radios.includes(event.target)) {
              return;
            }
            activationPending = true;
            syncSelection();
            scheduleReconcile();
            if (!controlled) {
              clearNativeInvalidWhenValid();
            }
          };
          const onChange = (event) => {
            if (!radios.includes(event.target)) {
              return;
            }
            if (!activationPending) {
              activationPending = true;
              scheduleReconcile();
            }
            syncSelection();
          };
          const onInvalid = (event) => {
            if (!radios.includes(event.target)) {
              return;
            }
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const nativeForm = radios[0].form;
          const onReset = (event) => {
            const timer = setTimeout(() => {
              resetTimers.delete(timer);
              if (event.defaultPrevented) {
                return;
              }
              nativeInvalid = false;
              field?.setNativeInvalid(false);
              if (controlled) {
                setCheckedValue(controlledValue);
              }
              applyState();
            }, 0);
            resetTimers.add(timer);
          };

          root.addEventListener("input", onInput);
          root.addEventListener("change", onChange);
          root.addEventListener("invalid", onInvalid, true);
          nativeForm?.addEventListener("reset", onReset);
          effect(() => {
            applyState();
            if (!activationPending) {
              applyControlled();
              clearNativeInvalidWhenValid();
              applyState();
            }
          });
          root.setAttribute("data-citry-radio-group-initialized", "");

          return () => {
            root.removeEventListener("input", onInput);
            root.removeEventListener("change", onChange);
            root.removeEventListener("invalid", onInvalid, true);
            nativeForm?.removeEventListener("reset", onReset);
            unregisterCapabilities?.();
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            resetTimers.forEach((timer) => clearTimeout(timer));
            resetTimers.clear();
            if (nativeInvalid) {
              field?.setNativeInvalid(false);
            }
            root.removeAttribute("data-citry-radio-group-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


class CRadio(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CRadioDefaultSlotData]
        description: SlotInput[CRadioDescriptionSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        context_value = self.inject(_RADIO_GROUP_CONTEXT_KEY, None)
        if context_value is None:
            msg = "CRadio must be rendered inside CRadioGroup."
            raise ValueError(msg)
        context: _RadioServerContext = context_value.context
        value = _canonical_string("CRadio value", kwargs.value)
        validate_boolean("CRadio", "disabled", kwargs.disabled)
        attrs = _copy_attrs("CRadio", "attrs", kwargs.attrs)
        input_attrs = _copy_attrs("CRadio", "input_attrs", kwargs.input_attrs)
        _validate_attrs("CRadio attrs", attrs, _RADIO_OWNED_ATTRS)
        _validate_attrs("CRadio input_attrs", input_attrs, _INPUT_OWNED_ATTRS)
        item_index = len(context.registry.entries)
        input_id = context.first_input_id if item_index == 0 and context.first_input_id else f"cui-radio-{self.id}"
        context.registry.register(str(value), input_id, bool(kwargs.disabled))
        description_id = f"{input_id}-description"
        has_description = "description" in self.raw_slots
        return {
            "value": value,
            "id": input_id,
            "name": context.name,
            "form": context.form_owner,
            "checked": context.selected == value,
            "disabled": bool(kwargs.disabled),
            "effective_disabled": context.disabled or bool(kwargs.disabled),
            "description_id": description_id,
            "describedby": description_id if has_description else None,
            "has_description": has_description,
            "label_attrs": {"for": input_id},
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
        }

    template = """
      <span
        class="cui-radio"
        c-data-checked="checked"
        c-data-disabled="effective_disabled"
        c-data-value="value"
        c-bind="attrs"
        data-citry-ui-part="radio"
      >
        <input
          class="cui-radio__input"
          c-id="id"
          c-name="name"
          type="radio"
          c-value="value"
          c-form="form"
          c-checked="checked"
          c-disabled="disabled"
          c-aria-describedby="describedby"
          c-bind="input_attrs"
          data-citry-ui-part="input"
        />
        <span data-citry-ui-part="body">
          <label c-bind="label_attrs" data-citry-ui-part="label">
            <c-slot required />
          </label>
          <c-if cond="has_description">
            <span c-id="description_id" data-citry-ui-part="description">
              <c-slot name="description" />
            </span>
          </c-if>
        </span>
      </span>
    """


__all__ = [
    "CRadio",
    "CRadioDefaultSlotData",
    "CRadioDescriptionSlotData",
    "CRadioGroup",
    "CRadioGroupDefaultSlotData",
    "CRadioGroupLabelSlotData",
    "CRadioLabelPos",
    "CRadioOrientation",
    "CRadioSize",
    "CRadioVariant",
]
