"""Styled progressive-enhancement single-value Select family."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
)
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    get_html_form_owner,
    merge_root_attrs,
    pop_html_attr,
)
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
)

CSelectPlacement = Literal["bottom-start", "bottom-end", "top-start", "top-end"]
CSelectVariant = Literal["outline", "filled", "plain"]
CSelectSize = Literal["sm", "md", "lg"]
CSelectChangeSource = Literal["pointer", "keyboard", "reset", "structure"]
CSelectOpenReason = Literal[
    "trigger",
    "keyboard",
    "selection",
    "escape",
    "tab",
    "outside",
    "focus-outside",
    "reset",
    "native",
    "ancestor",
]

_PLACEMENTS = ("bottom-start", "bottom-end", "top-start", "top-end")
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
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-invalid",
        "data-match-width",
        "data-open",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_TRIGGER_OWNED = frozenset(
    {
        "aria-activedescendant",
        "aria-controls",
        "aria-disabled",
        "aria-expanded",
        "aria-haspopup",
        "aria-hidden",
        "aria-invalid",
        "aria-readonly",
        "aria-required",
        "contenteditable",
        "data-citry-field-control",
        "data-citry-ui-part",
        "disabled",
        "form",
        "hidden",
        "id",
        "inert",
        "popover",
        "popovertarget",
        "popovertargetaction",
        "role",
        "tabindex",
        "type",
    }
)
_LISTBOX_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-multiselectable",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


@dataclass(frozen=True, slots=True)
class CSelectOption:
    value: str
    label: str
    description: str | None = None
    disabled: bool = False
    group: str | None = None


class CSelectValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    option: object | None
    controlled: bool
    source: CSelectChangeSource
    sourceEvent: object | None


class CSelectOpenChangeDetail(TypedDict):
    open: bool
    reason: CSelectOpenReason
    controlled: bool
    forced: bool
    source: object | None


@dataclass(frozen=True, slots=True)
class _ResolvedSelectOption:
    value: str
    label: str
    description: str | None
    disabled: bool
    group: str | None
    option_id: str
    label_id: str
    description_id: str | None
    selected: bool


@dataclass(frozen=True, slots=True)
class _ResolvedSelectGroup:
    label: str | None
    group_id: str | None
    label_id: str | None
    options: tuple[_ResolvedSelectOption, ...]


def _plain(owner: str, name: str, value: object, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"{owner} {name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip():
        msg = f"{owner} {name} must be nonempty."
        raise ValueError(msg)
    if "\0" in plain:
        msg = f"{owner} {name} cannot contain U+0000."
        raise ValueError(msg)
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
    dynamic_only: frozenset[str] = frozenset(),
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{owner} {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} {input_name}")
    for key in copied:
        if not isinstance(key, str):
            msg = f"{owner} {input_name} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{owner} {input_name} cannot contain Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{owner} {input_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in owned | dynamic_only:
            msg = f"{owner} {input_name} cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return merge_root_attrs(copied, class_, style)


def _normalize_options(
    source: object,
    *,
    input_id: str,
    selected_value: str | None,
) -> tuple[tuple[_ResolvedSelectOption, ...], tuple[_ResolvedSelectGroup, ...]]:
    raw = const_value(source)
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        msg = f"CSelect options must be a sequence of CSelectOption records, got {raw!r}."
        raise TypeError(msg)
    if not raw:
        raise ValueError("CSelect options must contain at least one CSelectOption.")
    resolved: list[_ResolvedSelectOption] = []
    values: set[str] = set()
    closed_groups: set[str] = set()
    active_group: str | None = None
    for index, item in enumerate(raw):
        if not isinstance(item, CSelectOption):
            msg = f"CSelect options[{index}] must be CSelectOption, got {item!r}."
            raise TypeError(msg)
        value = cast("str", _plain("CSelectOption", "value", item.value))
        label = cast("str", _plain("CSelectOption", "label", item.label))
        description = cast("str | None", _plain("CSelectOption", "description", item.description, optional=True))
        group = cast("str | None", _plain("CSelectOption", "group", item.group, optional=True))
        validate_boolean("CSelectOption", "disabled", item.disabled)
        if value in values:
            raise ValueError(f"CSelect requires unique Option values; {value!r} is duplicated.")
        values.add(value)
        if group != active_group:
            if active_group is not None:
                closed_groups.add(active_group)
            if group is not None and group in closed_groups:
                msg = f"CSelect group {group!r} must be contiguous in options."
                raise ValueError(msg)
            active_group = group
        token = sha256(value.encode()).hexdigest()[:12]
        option_id = f"{input_id}-option-{index}-{token}"
        resolved.append(
            _ResolvedSelectOption(
                value=value,
                label=label,
                description=description,
                disabled=bool(item.disabled),
                group=group,
                option_id=option_id,
                label_id=f"{option_id}-label",
                description_id=f"{option_id}-description" if description is not None else None,
                selected=value == selected_value,
            )
        )
    groups: list[_ResolvedSelectGroup] = []
    chunk: list[_ResolvedSelectOption] = []
    chunk_label: str | None = None
    for option in resolved:
        if chunk and option.group != chunk_label:
            group_index = len(groups)
            group_id = f"{input_id}-group-{group_index}" if chunk_label is not None else None
            groups.append(
                _ResolvedSelectGroup(
                    label=chunk_label,
                    group_id=group_id,
                    label_id=f"{group_id}-label" if group_id is not None else None,
                    options=tuple(chunk),
                )
            )
            chunk = []
        chunk_label = option.group
        chunk.append(option)
    group_index = len(groups)
    group_id = f"{input_id}-group-{group_index}" if chunk_label is not None else None
    groups.append(
        _ResolvedSelectGroup(
            label=chunk_label,
            group_id=group_id,
            label_id=f"{group_id}-label" if group_id is not None else None,
            options=tuple(chunk),
        )
    )
    return tuple(resolved), tuple(groups)


class CSelect(LibraryComponent):
    class Dependencies:
        js = (ANCHORED_LAYER_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        options: Sequence[CSelectOption]
        placeholder: str
        name: str | None = None
        form: str | None = None
        id: str | None = None
        value: str | None = None
        open: bool = False
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        loop: bool = False
        placement: CSelectPlacement = "bottom-start"
        match_width: bool = True
        variant: CSelectVariant = "outline"
        size: CSelectSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        listbox_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_select_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)

        placeholder = cast("str", _plain("CSelect", "placeholder", kwargs.placeholder))
        if kwargs.name is not None:
            validate_non_empty_string("CSelect", "name", kwargs.name)
        if kwargs.form is not None:
            validate_html_id("CSelect", kwargs.form)
        validate_html_id("CSelect", kwargs.id)
        if kwargs.value is not None:
            value = cast("str", _plain("CSelect", "value", kwargs.value))
        else:
            value = None
        validate_boolean("CSelect", "open", kwargs.open)
        validate_optional_boolean("CSelect", "required", kwargs.required)
        validate_optional_boolean("CSelect", "disabled", kwargs.disabled)
        validate_optional_boolean("CSelect", "readonly", kwargs.readonly)
        validate_optional_boolean("CSelect", "invalid", kwargs.invalid)
        validate_boolean("CSelect", "loop", kwargs.loop)
        validate_boolean("CSelect", "match_width", kwargs.match_width)
        validate_choice("CSelect", "placement", kwargs.placement, _PLACEMENTS)
        validate_choice("CSelect", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CSelect", "size", kwargs.size, _SIZES)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            competing = [
                name
                for name, supplied in (
                    ("required", kwargs.required),
                    ("disabled", kwargs.disabled),
                    ("readonly", kwargs.readonly),
                    ("invalid", kwargs.invalid),
                )
                if supplied is not None
            ]
            if competing:
                raise ValueError(f"CSelect inside CField cannot set Field-owned state: {', '.join(competing)}.")
            field.register_control("CSelect")
        if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
            msg = (
                f"CSelect id {kwargs.id!r} conflicts with its CField control_id {field_control_id!r}; "
                "set the same value on CField.control_id and CSelect.id."
            )
            raise ValueError(msg)

        input_id = kwargs.id or field_control_id or f"cui-select-{self.id}"
        trigger_id = f"{input_id}-trigger"
        listbox_id = f"{input_id}-listbox"
        popup_id = f"{input_id}-popup"
        options, groups = _normalize_options(kwargs.options, input_id=input_id, selected_value=value)
        values = {option.value for option in options}
        if value is not None and value not in values:
            raise ValueError(f"CSelect value {value!r} does not match an Option.")

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

        trigger_attrs = _attrs(
            "CSelect",
            "trigger_attrs",
            kwargs.trigger_attrs,
            _TRIGGER_OWNED,
            dynamic_only=frozenset({"aria-describedby", "aria-errormessage"}),
        )
        aria_label = pop_html_attr(trigger_attrs, "aria-label", component_name="CSelect trigger_attrs")
        aria_labelledby = pop_html_attr(trigger_attrs, "aria-labelledby", component_name="CSelect trigger_attrs")
        external_described_by = pop_html_attr(
            trigger_attrs,
            "aria-describedby",
            component_name="CSelect trigger_attrs",
        )
        external_error_message = pop_html_attr(
            trigger_attrs,
            "aria-errormessage",
            component_name="CSelect trigger_attrs",
        )
        if aria_label is not None and aria_labelledby is not None:
            raise ValueError("CSelect trigger_attrs accepts either aria-label or aria-labelledby, not both.")
        if field is not None and (aria_label is not None or aria_labelledby is not None):
            raise ValueError("CSelect cannot override its CField label with ARIA naming.")
        if field is None and aria_label is None and aria_labelledby is None:
            raise ValueError("Standalone CSelect requires aria-label or aria-labelledby in trigger_attrs.")

        form_owner = get_html_form_owner(
            {"form": kwargs.form} if kwargs.form is not None else {},
            component_name="CSelect",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CSelect inside CForm cannot target a different native form owner.")

        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        selected = next((option for option in options if option.value == value), None)
        effective_open = bool(kwargs.open) and not disabled and not readonly
        anchor_name = f"--_cui-select-anchor-{self.id}"
        data = {
            "value": value,
            "open": effective_open,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "loop": bool(kwargs.loop),
            "placement": kwargs.placement,
            "matchWidth": bool(kwargs.match_width),
            "variant": kwargs.variant,
            "size": kwargs.size,
            "placeholder": placeholder,
            "name": kwargs.name,
            "form": form_owner,
            "anchorName": anchor_name,
            "externalDescribedBy": external_described_by,
            "externalErrorMessage": external_error_message,
            "options": [
                {
                    "value": option.value,
                    "label": option.label,
                    "description": option.description,
                    "disabled": option.disabled,
                    "id": option.option_id,
                }
                for option in options
            ],
        }
        snapshot = {
            **data,
            "input_id": input_id,
            "trigger_id": trigger_id,
            "popup_id": popup_id,
            "listbox_id": listbox_id,
            "anchor_name": anchor_name,
            "trigger_anchor_style": {"anchor-name": anchor_name},
            "popup_anchor_style": {"position-anchor": anchor_name},
            "groups": groups,
            "options_resolved": options,
            "selected_label": selected.label if selected is not None else placeholder,
            "empty": selected is None,
            "aria_expanded": "true" if effective_open else "false",
            "aria_required": "true" if required else None,
            "aria_disabled": "true" if disabled else None,
            "aria_readonly": "true" if readonly else None,
            "aria_invalid": "true" if invalid else None,
            "aria_label": aria_label,
            "listbox_aria_label": aria_label,
            "aria_labelledby": field.label_id if field is not None else aria_labelledby,
            "aria_describedby": described_by,
            "aria_errormessage": error_message,
            "field_control": "" if field is not None else None,
            "native_name": None if readonly else kwargs.name,
            "native_disabled": disabled or readonly,
            "readonly_name": kwargs.name if readonly and not disabled else None,
            "attrs": _attrs("CSelect", "attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "trigger_attrs": trigger_attrs,
            "listbox_attrs": _attrs("CSelect", "listbox_attrs", kwargs.listbox_attrs, _LISTBOX_OWNED),
        }
        self._cui_select_snapshot = snapshot
        self._cui_select_data = data
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_select_data

    template = """
      <div
        class="cui-select"
        c-data-open="open"
        c-data-empty="empty"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-match-width="matchWidth"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="root"
      >
        <button
          class="cui-select__control"
          c-id="trigger_id"
          type="button"
          role="combobox"
          aria-haspopup="listbox"
          c-aria-expanded="aria_expanded"
          c-aria-controls="listbox_id"
          c-aria-required="aria_required"
          c-aria-disabled="aria_disabled"
          c-aria-readonly="aria_readonly"
          c-aria-invalid="aria_invalid"
          c-aria-label="aria_label"
          c-aria-labelledby="aria_labelledby"
          c-aria-describedby="aria_describedby"
          c-aria-errormessage="aria_errormessage"
          c-disabled="disabled"
          c-data-citry-field-control="field_control"
          c-style="trigger_anchor_style"
          c-bind="trigger_attrs"
          data-citry-ui-part="control"
        >
          <span data-citry-ui-part="value">{{ selected_label }}</span>
          <span class="cui-select__indicator" aria-hidden="true" data-citry-ui-part="indicator">&#9662;</span>
        </button>
        <select
          class="cui-select__native"
          c-id="input_id"
          c-name="native_name"
          c-form="form"
          c-aria-label="aria_label"
          c-aria-labelledby="aria_labelledby"
          c-required="required and not readonly"
          c-disabled="native_disabled"
          data-cui-select-native
        >
          <option value="" c-selected="value is None">{{ placeholder }}</option>
          <option
            c-for="option in options_resolved"
            c-value="option.value"
            c-disabled="option.disabled"
            c-selected="option.selected"
          >{{ option.label }}</option>
        </select>
        <input
          c-name="readonly_name"
          c-form="form"
          c-value="value or ''"
          c-disabled="disabled or not readonly"
          type="hidden"
          data-cui-select-readonly-value
        />
        <div
          class="cui-select__popup"
          c-id="popup_id"
          popover="manual"
          c-data-placement="placement"
          c-style="popup_anchor_style"
          hidden
          inert
          data-citry-ui-part="popup"
        >
          <div
            class="cui-select__listbox"
            c-id="listbox_id"
            role="listbox"
            c-aria-label="listbox_aria_label"
            c-aria-labelledby="aria_labelledby"
            c-bind="listbox_attrs"
            data-citry-ui-part="listbox"
          >
            <c-for each="group in groups">
              <c-if cond="group.label is None">
                <div
                  c-for="option in group.options"
                  class="cui-select__option"
                  c-id="option.option_id"
                  role="option"
                  c-aria-labelledby="option.label_id"
                  c-aria-describedby="option.description_id"
                  c-aria-selected="'true' if option.selected else 'false'"
                  c-aria-disabled="'true' if option.disabled else 'false'"
                  c-data-value="option.value"
                  c-data-selected="option.selected"
                  c-data-disabled="option.disabled"
                  data-citry-ui-part="option"
                >
                  <span c-id="option.label_id" data-citry-ui-part="option-label">{{ option.label }}</span>
                  <span
                    c-if="option.description is not None"
                    c-id="option.description_id"
                    data-citry-ui-part="option-description"
                  >{{ option.description }}</span>
                </div>
              </c-if>
              <c-else>
                <div
                  class="cui-select__group"
                  c-id="group.group_id"
                  role="group"
                  c-aria-labelledby="group.label_id"
                  data-citry-ui-part="group"
                >
                  <span
                    class="cui-select__group-label"
                    c-id="group.label_id"
                    data-citry-ui-part="group-label"
                  >{{ group.label }}</span>
                  <div
                    c-for="option in group.options"
                    class="cui-select__option"
                    c-id="option.option_id"
                    role="option"
                    c-aria-labelledby="option.label_id"
                    c-aria-describedby="option.description_id"
                    c-aria-selected="'true' if option.selected else 'false'"
                    c-aria-disabled="'true' if option.disabled else 'false'"
                    c-data-value="option.value"
                    c-data-selected="option.selected"
                    c-data-disabled="option.disabled"
                    data-citry-ui-part="option"
                  >
                    <span c-id="option.label_id" data-citry-ui-part="option-label">{{ option.label }}</span>
                    <span
                      c-if="option.description is not None"
                      c-id="option.description_id"
                      data-citry-ui-part="option-description"
                    >{{ option.description }}</span>
                  </div>
                </div>
              </c-else>
            </c-for>
          </div>
        </div>
      </div>
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"


__all__ = [
    "CSelect",
    "CSelectChangeSource",
    "CSelectOpenChangeDetail",
    "CSelectOpenReason",
    "CSelectOption",
    "CSelectPlacement",
    "CSelectSize",
    "CSelectValueChangeDetail",
    "CSelectVariant",
]
