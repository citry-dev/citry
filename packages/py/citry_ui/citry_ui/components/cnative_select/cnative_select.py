"""Styled native single-select component family."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias, cast

from citry import LibraryComponent, const_value
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
from citry_ui.components._validation import reject_owned_attrs, validate_optional_boolean

CNativeSelectVariant = Literal["outline", "filled", "plain"]
CNativeSelectSize = Literal["sm", "md", "lg"]

_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-invalid",
        "autocomplete",
        "data-citry-field-supports-readonly",
        "data-citry-field-supports-required",
        "data-citry-native-select-initialized",
        FIELD_CONTROL_MARKER,
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-invalid",
        "data-required",
        "data-size",
        "data-variant",
        "disabled",
        "id",
        "multiple",
        "name",
        "readonly",
        "required",
        "size",
        "value",
    }
)
_ROOT_DYNAMIC_OWNED_ATTRS = _ROOT_OWNED_ATTRS | {"aria-describedby", "aria-errormessage", "form"}
_OPTION_OWNED_ATTRS = frozenset({"data-citry-key", "disabled", "label", "selected", "value"})
_GROUP_OWNED_ATTRS = frozenset({"disabled", "label"})
_OWNERSHIP_DIRECTIVES = frozenset({"x-bind", "x-html", "x-model", "x-modelable", "x-text"})


@dataclass(frozen=True, slots=True)
class CNativeSelectOption:
    value: str
    label: str
    disabled: bool = False
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CNativeSelectGroup:
    label: str
    options: Sequence[CNativeSelectOption]
    disabled: bool = False
    attrs: Mapping[str, object] | None = None


CNativeSelectItem: TypeAlias = CNativeSelectOption | CNativeSelectGroup


@dataclass(frozen=True, slots=True)
class _NormalizedOption:
    kind: Literal["option"]
    value: str
    label: str
    disabled: bool
    selected: bool
    morph_key: str
    attrs: dict[str, object]


@dataclass(frozen=True, slots=True)
class _NormalizedGroup:
    kind: Literal["group"]
    label: str
    disabled: bool
    attrs: dict[str, object]
    options: tuple[_NormalizedOption, ...]


_NormalizedItem: TypeAlias = _NormalizedOption | _NormalizedGroup


@dataclass(frozen=True, slots=True)
class _NormalizedSelect:
    items: tuple[_NormalizedItem, ...]
    flat_options: tuple[_NormalizedOption, ...]
    placeholder: str | None
    value: str | None
    attrs: dict[str, object]


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CNativeSelect {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CNativeSelect could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _plain_required_string(input_name: str, value: object) -> str:
    plain = _plain_optional_string(input_name, value)
    if not plain:
        msg = f"CNativeSelect {input_name} must be a non-empty string, got {plain!r}."
        raise ValueError(msg)
    return plain


def _canonical_value(input_name: str, value: object, *, allow_none: bool) -> str | None:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        if allow_none:
            return None
        msg = f"CNativeSelect {input_name} must be a non-empty string."
        raise ValueError(msg)
    canonical = plain.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in canonical:
        msg = f"CNativeSelect {input_name} cannot contain U+0000."
        raise ValueError(msg)
    if not canonical and not allow_none:
        msg = f"CNativeSelect {input_name} must be a non-empty string."
        raise ValueError(msg)
    return canonical


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CNativeSelect {input_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)
    return plain


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CNativeSelect {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.lower()
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
    component_name = f"CNativeSelect {input_name}"
    reject_owned_attrs(attrs, owned, component_name)
    dynamic_targets = dynamic_owned or owned
    for key in attrs:
        normalized = key.lower()
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


def _morph_key(value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return f"native-select-option-{digest}"


def _normalize_options(
    options: object,
    *,
    selected_value: str | None,
) -> tuple[tuple[_NormalizedItem, ...], tuple[_NormalizedOption, ...]]:
    if not isinstance(options, Sequence) or isinstance(options, (str, bytes, bytearray)):
        msg = f"CNativeSelect options must be a sequence of option or group records, got {options!r}."
        raise TypeError(msg)
    item_snapshot = tuple(options)
    seen: set[str] = set()
    items: list[_NormalizedItem] = []
    flat: list[_NormalizedOption] = []

    def normalize_option(option: object, *, group_disabled: bool = False) -> _NormalizedOption:
        if not isinstance(option, CNativeSelectOption):
            msg = f"CNativeSelect options require CNativeSelectOption records, got {option!r}."
            raise TypeError(msg)
        value = cast("str", _canonical_value("option value", option.value, allow_none=False))
        if value in seen:
            msg = f"CNativeSelect option values must be unique after normalization, got {value!r} twice."
            raise ValueError(msg)
        seen.add(value)
        label = _plain_required_string("option label", option.label)
        if not isinstance(option.disabled, bool):
            msg = f"CNativeSelect option disabled must be a bool, got {option.disabled!r}."
            raise TypeError(msg)
        attrs = _copy_attrs("option attrs", option.attrs)
        _validate_attrs("option attrs", attrs, owned=_OPTION_OWNED_ATTRS)
        disabled = group_disabled or option.disabled
        return _NormalizedOption(
            kind="option",
            value=value,
            label=label,
            disabled=disabled,
            selected=selected_value == value,
            morph_key=_morph_key(value),
            attrs=attrs,
        )

    for item in item_snapshot:
        if isinstance(item, CNativeSelectOption):
            option = normalize_option(item)
            items.append(option)
            flat.append(option)
            continue
        if not isinstance(item, CNativeSelectGroup):
            msg = f"CNativeSelect options require option or group records, got {item!r}."
            raise TypeError(msg)
        label = _plain_required_string("group label", item.label)
        if not isinstance(item.disabled, bool):
            msg = f"CNativeSelect group disabled must be a bool, got {item.disabled!r}."
            raise TypeError(msg)
        if not isinstance(item.options, Sequence) or isinstance(item.options, (str, bytes, bytearray)):
            msg = f"CNativeSelect group options must be a sequence, got {item.options!r}."
            raise TypeError(msg)
        group_options = tuple(normalize_option(option, group_disabled=item.disabled) for option in tuple(item.options))
        attrs = _copy_attrs("group attrs", item.attrs)
        _validate_attrs("group attrs", attrs, owned=_GROUP_OWNED_ATTRS)
        group = _NormalizedGroup(
            kind="group",
            label=label,
            disabled=item.disabled,
            attrs=attrs,
            options=group_options,
        )
        items.append(group)
        flat.extend(group_options)
    return tuple(items), tuple(flat)


class CNativeSelect(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        options: Sequence[CNativeSelectItem]
        name: str | None = None
        id: str | None = None
        value: str | None = None
        placeholder: str | None = None
        required: bool | None = None
        disabled: bool | None = None
        invalid: bool | None = None
        autocomplete: str | None = None
        variant: CNativeSelectVariant = "outline"
        size: CNativeSelectSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _normalize(self, kwargs: Kwargs) -> _NormalizedSelect:
        name = _plain_optional_string("name", kwargs.name)
        if name == "":
            msg = "CNativeSelect name must be non-empty when supplied."
            raise ValueError(msg)
        element_id = _plain_optional_string("id", kwargs.id)
        if element_id is not None and (not element_id or any(character in "\t\n\f\r " for character in element_id)):
            msg = "CNativeSelect id must be non-empty and cannot contain ASCII whitespace."
            raise ValueError(msg)
        placeholder = _plain_optional_string("placeholder", kwargs.placeholder)
        if placeholder == "":
            msg = "CNativeSelect placeholder must be non-empty when supplied."
            raise ValueError(msg)
        value = _canonical_value("value", kwargs.value, allow_none=True)
        if value == "" and placeholder is None:
            msg = "CNativeSelect value='' requires placeholder."
            raise ValueError(msg)
        items, flat_options = _normalize_options(kwargs.options, selected_value=value)
        options_by_value = {option.value: option for option in flat_options}
        if value is not None and value != "":
            selected = options_by_value.get(value)
            if selected is None:
                msg = f"CNativeSelect value {value!r} does not match an option."
                raise ValueError(msg)
            if selected.disabled or any(
                isinstance(item, _NormalizedGroup) and item.disabled and selected in item.options for item in items
            ):
                msg = f"CNativeSelect value {value!r} identifies a disabled option."
                raise ValueError(msg)
        attrs = _copy_attrs("attrs", kwargs.attrs)
        _validate_attrs(
            "attrs",
            attrs,
            owned=_ROOT_OWNED_ATTRS,
            dynamic_owned=_ROOT_DYNAMIC_OWNED_ATTRS,
        )
        self._native_select_name = name
        self._native_select_id = element_id
        return _NormalizedSelect(
            items=items,
            flat_options=flat_options,
            placeholder=placeholder,
            value=value,
            attrs=attrs,
        )

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        normalized = self._normalize(kwargs)
        self._native_select_snapshot = normalized
        validate_optional_boolean("CNativeSelect", "required", kwargs.required)
        validate_optional_boolean("CNativeSelect", "disabled", kwargs.disabled)
        validate_optional_boolean("CNativeSelect", "invalid", kwargs.invalid)
        autocomplete = _plain_optional_string("autocomplete", kwargs.autocomplete)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        supports_required = normalized.placeholder is not None
        if field is not None:
            supplied_state = [
                name
                for name, value in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("invalid", kwargs.invalid),
                )
                if value is not None
            ]
            if supplied_state:
                names = ", ".join(supplied_state)
                msg = f"CNativeSelect inside CField cannot set Field-owned state: {names}."
                raise ValueError(msg)
            field.register_control(
                "CNativeSelect",
                supports_required=supports_required,
                supports_readonly=False,
            )
        elif kwargs.required and not supports_required:
            msg = "CNativeSelect required=True requires placeholder."
            raise ValueError(msg)

        field_control_id = str(field.control_id) if field is not None else None
        element_id = self._native_select_id
        if field_control_id is not None and element_id is not None and element_id != field_control_id:
            msg = (
                f"CNativeSelect id {element_id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CNativeSelect.id."
            )
            raise ValueError(msg)
        for html_attribute in ("form", "aria-describedby", "aria-errormessage"):
            get_html_attr(
                normalized.attrs,
                html_attribute,
                component_name="CNativeSelect",
            )
        caller_attrs = merge_root_attrs(normalized.attrs, kwargs.class_, kwargs.style)
        form_owner = get_html_form_owner(
            caller_attrs,
            component_name="CNativeSelect",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            msg = "CNativeSelect inside CForm cannot target a different native form owner."
            raise ValueError(msg)

        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            invalid = bool(field.invalid)
        else:
            required = kwargs.required if kwargs.required is not None else False
            local_disabled = kwargs.disabled if kwargs.disabled is not None else False
            disabled = (bool(form.disabled) if form is not None else False) or local_disabled
            invalid = kwargs.invalid if kwargs.invalid is not None else False

        external_described_by = pop_html_attr(
            caller_attrs,
            "aria-describedby",
            component_name="CNativeSelect",
        )
        external_error_message = pop_html_attr(
            caller_attrs,
            "aria-errormessage",
            component_name="CNativeSelect",
        )
        self._native_select_external_described_by = external_described_by
        self._native_select_external_error_message = external_error_message
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        value = normalized.value
        placeholder_selected = normalized.placeholder is not None and value in (None, "")
        first_enabled = next((option for option in normalized.flat_options if not option.disabled), None)
        empty = placeholder_selected or (normalized.placeholder is None and value is None and first_enabled is None)
        return {
            "id": element_id or field_control_id or f"cui-native-select-{self.id}",
            "name": self._native_select_name,
            "items": normalized.items,
            "placeholder": normalized.placeholder,
            "placeholder_selected": placeholder_selected,
            "required": required,
            "disabled": disabled,
            "invalid": invalid,
            "aria_invalid": "true" if invalid else None,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "autocomplete": autocomplete,
            "variant": variant,
            "size": size,
            "empty": empty,
            "field_control": field is not None,
            "field_supports_required": ("true" if supports_required else "false") if field is not None else None,
            "field_supports_readonly": "false" if field is not None else None,
            "attrs": caller_attrs,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        normalized = self._native_select_snapshot
        field = self.inject(FIELD_CONTEXT_KEY, None)
        return {
            "value": normalized.value,
            "hasPlaceholder": normalized.placeholder is not None,
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
            "externalDescribedBy": self._native_select_external_described_by,
            "externalErrorMessage": self._native_select_external_error_message,
        }

    template = """
      <select
        class="cui-native-select"
        c-id="id"
        c-name="name"
        c-required="required"
        c-disabled="disabled"
        c-aria-invalid="aria_invalid"
        c-aria-describedby="aria_describedby"
        c-aria-errormessage="aria_errormessage"
        c-autocomplete="autocomplete"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-invalid="invalid"
        c-data-empty="empty"
        c-data-variant="variant"
        c-data-size="size"
        c-data-citry-field-control="field_control"
        c-data-citry-field-supports-required="field_supports_required"
        c-data-citry-field-supports-readonly="field_supports_readonly"
        c-bind="attrs"
        data-citry-ui-part="native-select"
      >
        <c-if cond="placeholder is not None">
          <option
            value=""
            c-selected="placeholder_selected"
            #c-key="'native-select-placeholder'"
          >{{ placeholder }}</option>
        </c-if>
        <c-for each="item in items">
          <c-if cond="item.kind == 'option'">
            <option
              c-value="item.value"
              c-disabled="item.disabled"
              c-selected="item.selected"
              #c-key="item.morph_key"
              c-bind="item.attrs"
            >{{ item.label }}</option>
          </c-if>
          <c-else>
            <optgroup
              c-label="item.label"
              c-disabled="item.disabled"
              c-bind="item.attrs"
            >
              <c-for each="option in item.options">
                <option
                  c-value="option.value"
                  c-disabled="option.disabled"
                  c-selected="option.selected"
                  #c-key="option.morph_key"
                  c-bind="option.attrs"
                >{{ option.label }}</option>
              </c-for>
            </optgroup>
          </c-else>
        </c-for>
      </select>
    """

    js = r"""
      $component({
        props: {
          value: {},
          required: {},
          disabled: {},
          invalid: {},
          variant: {},
          size: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const select = els[0];
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const handoffKey = Symbol.for("citry-ui:native-select-handoff");
          const placeholder = data.hasPlaceholder ? select.options[0] : null;
          const allowedValues = {
            variant: ["outline", "filled", "plain"],
            size: ["sm", "md", "lg"],
          };
          const invalidEpisodes = new Map();
          const optionByValue = new Map();
          Array.from(select.options).forEach((option) => {
            if (option !== placeholder) {
              optionByValue.set(option.value, option);
            }
          });
          let controlled = false;
          let controlledTarget = null;
          let nativeInvalid = false;
          let reconcileTimer = null;
          const resetTimers = new Set();

          const optionEnabled = (option) => Boolean(
            option
              && !option.disabled
              && !(option.parentElement instanceof HTMLOptGroupElement && option.parentElement.disabled)
          );
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
              `[citry-ui] CNativeSelect ${name} received invalid client value ${describedValue}; `
                + "using the documented fallback.",
              select,
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
              `[citry-ui] CNativeSelect ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describedValue}.`,
              select,
            );
          };
          const reportUnsupportedRequired = () => {
            const episode = "required:placeholder";
            if (invalidEpisodes.get(episode) === "unsupported:true") {
              return;
            }
            invalidEpisodes.set(episode, "unsupported:true");
            console.error(
              "[citry-ui] CNativeSelect required=true requires a placeholder; using false.",
              select,
            );
          };
          const canonicalize = (value) => {
            if (value.includes("\0")) {
              return null;
            }
            return value.replace(/\r\n?/g, "\n");
          };
          const valueTarget = (value) => {
            if (value === null) {
              return data.hasPlaceholder ? { kind: "value", value: "" } : { kind: "none" };
            }
            if (typeof value !== "string") {
              return null;
            }
            const canonical = canonicalize(value);
            if (canonical === null) {
              return null;
            }
            if (canonical === "") {
              return data.hasPlaceholder ? { kind: "value", value: "" } : null;
            }
            const option = optionByValue.get(canonical);
            return optionEnabled(option) ? { kind: "value", value: canonical } : null;
          };
          const currentTarget = () => {
            if (select.selectedIndex === -1) {
              return { kind: "none" };
            }
            return { kind: "value", value: select.value };
          };
          const targetAvailable = (target) => {
            if (!target) {
              return false;
            }
            if (target.kind === "none") {
              return true;
            }
            if (target.value === "") {
              return Boolean(placeholder);
            }
            return optionEnabled(optionByValue.get(target.value));
          };
          const targetMatches = (target) => {
            if (target.kind === "none") {
              return select.selectedIndex === -1;
            }
            if (target.value === "") {
              return select.selectedIndex === 0 && select.options[0] === placeholder;
            }
            const option = optionByValue.get(target.value);
            return optionEnabled(option)
              && select.selectedOptions.length === 1
              && select.selectedOptions[0] === option;
          };
          const applyTarget = (target) => {
            if (targetMatches(target)) {
              return;
            }
            if (target.kind === "none") {
              select.selectedIndex = -1;
            } else {
              select.value = target.value;
            }
          };
          const structuralFallback = () => {
            if (data.value !== null) {
              const incoming = valueTarget(data.value);
              if (incoming && targetAvailable(incoming)) {
                return incoming;
              }
            }
            if (placeholder) {
              return { kind: "value", value: "" };
            }
            const firstEnabled = Array.from(select.options).find(optionEnabled);
            return firstEnabled ? { kind: "value", value: firstEnabled.value } : { kind: "none" };
          };
          const handoff = select[handoffKey];
          delete select[handoffKey];
          if (handoff?.kind === "none") {
            applyTarget(handoff);
          } else if (handoff?.kind === "value" && targetAvailable(handoff)) {
            applyTarget(handoff);
          } else if (handoff) {
            applyTarget(structuralFallback());
          }
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
              select.setAttribute("aria-describedby", describedBy);
            } else {
              select.removeAttribute("aria-describedby");
            }
            if (errorMessage) {
              select.setAttribute("aria-errormessage", errorMessage);
            } else {
              select.removeAttribute("aria-errormessage");
            }
          };
          const syncEmpty = () => {
            select.toggleAttribute("data-empty", select.selectedIndex === -1 || select.value === "");
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
              const requestedRequired = resolveBoolean("required", data.required);
              if (requestedRequired && !data.hasPlaceholder) {
                reportUnsupportedRequired();
                required = false;
              } else {
                invalidEpisodes.delete("required:placeholder");
                required = requestedRequired;
              }
              disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
              externalInvalid = resolveBoolean("invalid", data.invalid);
            }
            const invalid = externalInvalid || nativeInvalid;
            select.required = required;
            select.disabled = disabled;
            select.toggleAttribute("data-required", required);
            select.toggleAttribute("data-disabled", disabled);
            select.toggleAttribute("data-invalid", invalid);
            select.dataset.variant = resolveChoice("variant");
            select.dataset.size = resolveChoice("size");
            if (invalid) {
              select.setAttribute("aria-invalid", "true");
            } else {
              select.removeAttribute("aria-invalid");
            }
            syncRelationships(invalid);
            syncEmpty();
          };
          const clearNativeInvalidWhenValid = () => {
            if (!nativeInvalid || !select.validity.valid) {
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
              controlledTarget = null;
              invalidEpisodes.delete("value");
              syncEmpty();
              clearNativeInvalidWhenValid();
              return;
            }
            const target = valueTarget(value);
            if (!target) {
              reportInvalid("value", value);
              if (controlled) {
                if (!targetAvailable(controlledTarget)) {
                  controlledTarget = structuralFallback();
                }
                applyTarget(controlledTarget);
              }
              syncEmpty();
              clearNativeInvalidWhenValid();
              return;
            }
            invalidEpisodes.delete("value");
            controlled = true;
            controlledTarget = target;
            applyTarget(target);
            syncEmpty();
            clearNativeInvalidWhenValid();
          };
          const scheduleReconcile = () => {
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            reconcileTimer = setTimeout(() => {
              reconcileTimer = null;
              applyLatestValueProp();
            }, 0);
          };
          const onInvalid = () => {
            nativeInvalid = true;
            field?.setNativeInvalid(true);
            applyState();
          };
          const onInput = () => {
            syncEmpty();
            if (controlled) {
              scheduleReconcile();
            } else {
              clearNativeInvalidWhenValid();
            }
          };
          const onChange = () => {
            syncEmpty();
            if (!controlled) {
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
              applyLatestValueProp();
              applyState();
            }, 0);
            resetTimers.add(resetTimer);
          };
          const unregisterCapabilities = field?.registerCapabilities({
            required: data.hasPlaceholder,
            readonly: false,
          });
          const nativeForm = select.form;

          select.addEventListener("invalid", onInvalid);
          select.addEventListener("input", onInput);
          select.addEventListener("change", onChange);
          nativeForm?.addEventListener("reset", onReset);
          effect(() => {
            applyState();
            clearNativeInvalidWhenValid();
          });
          effect(() => {
            applyLatestValueProp();
          });
          select.setAttribute("data-citry-native-select-initialized", "");

          return () => {
            select[handoffKey] = currentTarget();
            select.removeEventListener("invalid", onInvalid);
            select.removeEventListener("input", onInput);
            select.removeEventListener("change", onChange);
            nativeForm?.removeEventListener("reset", onReset);
            unregisterCapabilities?.();
            if (reconcileTimer !== null) {
              clearTimeout(reconcileTimer);
            }
            resetTimers.forEach((resetTimer) => clearTimeout(resetTimer));
            resetTimers.clear();
            if (nativeInvalid) {
              field?.setNativeInvalid(false);
            }
            select.removeAttribute("data-citry-native-select-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = [
    "CNativeSelect",
    "CNativeSelectGroup",
    "CNativeSelectItem",
    "CNativeSelectOption",
    "CNativeSelectSize",
    "CNativeSelectVariant",
]
