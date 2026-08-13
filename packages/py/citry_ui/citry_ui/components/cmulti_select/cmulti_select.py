"""Styled progressive-enhancement multiple-value Select family."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
    ANCHORED_LAYER_RUNTIME_JS,
)
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs, pop_html_attr
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._form_control_runtime import FORM_CONTROL_RUNTIME_DEPENDENCY, FORM_CONTROL_STYLE_DEPENDENCY
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
    validate_optional_boolean,
)

CMultiSelectPlacement = Literal["bottom-start", "bottom-end", "top-start", "top-end"]
CMultiSelectVariant = Literal["outline", "filled", "plain"]
CMultiSelectSize = Literal["sm", "md", "lg"]
CMultiSelectChangeSource = Literal["pointer", "keyboard", "reset", "structure"]
CMultiSelectOpenReason = Literal[
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
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "data-close-on-select",
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
class CMultiSelectOption:
    value: str
    label: str
    description: str | None = None
    disabled: bool = False
    group: str | None = None


class CMultiSelectValueChangeDetail(TypedDict):
    value: list[str]
    previousValue: list[str]
    option: object | None
    selected: bool
    controlled: bool
    source: CMultiSelectChangeSource
    sourceEvent: object | None


class CMultiSelectOpenChangeDetail(TypedDict):
    open: bool
    reason: CMultiSelectOpenReason
    controlled: bool
    forced: bool
    source: object | None


@dataclass(frozen=True, slots=True)
class _ResolvedOption:
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
class _ResolvedGroup:
    label: str | None
    group_id: str | None
    label_id: str | None
    options: tuple[_ResolvedOption, ...]


def _plain(owner: str, name: str, value: object, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        raise TypeError(f"{owner} {name} must be {expected}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip():
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


def _values(source: object, *, owner: str) -> tuple[str, ...]:
    raw = const_value(source)
    if raw is None:
        return ()
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"{owner} value must be a sequence of strings or None, got {raw!r}.")
    output: list[str] = []
    for index, item in enumerate(raw):
        value = cast("str", _plain(owner, f"value[{index}]", item))
        if value in output:
            raise ValueError(f"{owner} value cannot contain duplicate {value!r}.")
        output.append(value)
    return tuple(output)


def _options(
    source: object,
    *,
    input_id: str,
    selected: tuple[str, ...],
) -> tuple[tuple[_ResolvedOption, ...], tuple[_ResolvedGroup, ...], tuple[str, ...]]:
    raw = const_value(source)
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"CMultiSelect options must be a sequence of CMultiSelectOption records, got {raw!r}.")
    if not raw:
        raise ValueError("CMultiSelect options must contain at least one CMultiSelectOption.")
    resolved: list[_ResolvedOption] = []
    seen: set[str] = set()
    closed_groups: set[str] = set()
    active_group: str | None = None
    for index, item in enumerate(raw):
        if not isinstance(item, CMultiSelectOption):
            raise TypeError(f"CMultiSelect options[{index}] must be CMultiSelectOption, got {item!r}.")
        value = cast("str", _plain("CMultiSelectOption", "value", item.value))
        label = cast("str", _plain("CMultiSelectOption", "label", item.label))
        description = cast("str | None", _plain("CMultiSelectOption", "description", item.description, optional=True))
        group = cast("str | None", _plain("CMultiSelectOption", "group", item.group, optional=True))
        validate_boolean("CMultiSelectOption", "disabled", item.disabled)
        if value in seen:
            raise ValueError(f"CMultiSelect requires unique Option values; {value!r} is duplicated.")
        seen.add(value)
        if group != active_group:
            if active_group is not None:
                closed_groups.add(active_group)
            if group is not None and group in closed_groups:
                raise ValueError(f"CMultiSelect group {group!r} must be contiguous in options.")
            active_group = group
        token = sha256(value.encode()).hexdigest()[:12]
        option_id = f"{input_id}-option-{index}-{token}"
        resolved.append(
            _ResolvedOption(
                value,
                label,
                description,
                bool(item.disabled),
                group,
                option_id,
                f"{option_id}-label",
                f"{option_id}-description" if description is not None else None,
                value in selected,
            )
        )
    unknown = [value for value in selected if value not in seen]
    if unknown:
        raise ValueError(f"CMultiSelect value contains unknown Options: {unknown!r}.")
    ordered_selected = tuple(option.value for option in resolved if option.value in selected)
    groups: list[_ResolvedGroup] = []
    chunk: list[_ResolvedOption] = []
    chunk_label: str | None = None
    for option in resolved:
        if chunk and option.group != chunk_label:
            group_id = f"{input_id}-group-{len(groups)}" if chunk_label is not None else None
            groups.append(
                _ResolvedGroup(
                    chunk_label,
                    group_id,
                    f"{group_id}-label" if group_id else None,
                    tuple(chunk),
                )
            )
            chunk = []
        chunk_label = option.group
        chunk.append(option)
    group_id = f"{input_id}-group-{len(groups)}" if chunk_label is not None else None
    groups.append(_ResolvedGroup(chunk_label, group_id, f"{group_id}-label" if group_id else None, tuple(chunk)))
    return tuple(resolved), tuple(groups), ordered_selected


class CMultiSelect(LibraryComponent):
    class Dependencies:
        js = (ANCHORED_LAYER_RUNTIME_DEPENDENCY, FORM_CONTROL_RUNTIME_DEPENDENCY)
        css = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        options: Sequence[CMultiSelectOption]
        placeholder: str
        name: str | None = None
        form: str | None = None
        id: str | None = None
        value: Sequence[str] | None = None
        open: bool = False
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        loop: bool = False
        close_on_select: bool = False
        placement: CMultiSelectPlacement = "bottom-start"
        match_width: bool = True
        variant: CMultiSelectVariant = "outline"
        size: CMultiSelectSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        listbox_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_multi_select_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)
        placeholder = cast("str", _plain("CMultiSelect", "placeholder", kwargs.placeholder))
        if kwargs.name is not None:
            validate_non_empty_string("CMultiSelect", "name", kwargs.name)
        if kwargs.form is not None:
            validate_html_id("CMultiSelect", kwargs.form)
        validate_html_id("CMultiSelect", kwargs.id)
        selected_input = _values(kwargs.value, owner="CMultiSelect")
        for name in ("open", "loop", "close_on_select", "match_width"):
            validate_boolean("CMultiSelect", name, getattr(kwargs, name))
        for name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CMultiSelect", name, getattr(kwargs, name))
        validate_choice("CMultiSelect", "placement", kwargs.placement, _PLACEMENTS)
        validate_choice("CMultiSelect", "variant", kwargs.variant, _VARIANTS)
        validate_choice("CMultiSelect", "size", kwargs.size, _SIZES)

        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        field_control_id = str(field.control_id) if field is not None else None
        if field is not None:
            competing = [
                name for name in ("required", "disabled", "readonly", "invalid") if getattr(kwargs, name) is not None
            ]
            if competing:
                raise ValueError(f"CMultiSelect inside CField cannot set Field-owned state: {', '.join(competing)}.")
            field.register_control("CMultiSelect")
        if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
            raise ValueError("CMultiSelect id conflicts with its CField control_id.")

        input_id = kwargs.id or field_control_id or f"cui-multi-select-{self.id}"
        trigger_id = f"{input_id}-trigger"
        listbox_id = f"{input_id}-listbox"
        options, groups, selected = _options(kwargs.options, input_id=input_id, selected=selected_input)

        if field is not None:
            required, disabled, readonly, invalid = (
                bool(field.required),
                bool(field.disabled),
                bool(field.readonly),
                bool(field.invalid),
            )
        else:
            required = kwargs.required if kwargs.required is not None else False
            disabled = (bool(form.disabled) if form is not None else False) or bool(kwargs.disabled)
            readonly = kwargs.readonly if kwargs.readonly is not None else bool(form.readonly) if form else False
            invalid = kwargs.invalid if kwargs.invalid is not None else False

        trigger_attrs = _attrs(
            "CMultiSelect",
            "trigger_attrs",
            kwargs.trigger_attrs,
            _TRIGGER_OWNED,
            dynamic_only=frozenset({"aria-describedby", "aria-errormessage"}),
        )
        aria_label = pop_html_attr(trigger_attrs, "aria-label", component_name="CMultiSelect trigger_attrs")
        aria_labelledby = pop_html_attr(
            trigger_attrs,
            "aria-labelledby",
            component_name="CMultiSelect trigger_attrs",
        )
        external_described_by = pop_html_attr(
            trigger_attrs,
            "aria-describedby",
            component_name="CMultiSelect trigger_attrs",
        )
        external_error_message = pop_html_attr(
            trigger_attrs,
            "aria-errormessage",
            component_name="CMultiSelect trigger_attrs",
        )
        if aria_label is not None and aria_labelledby is not None:
            raise ValueError("CMultiSelect accepts either aria-label or aria-labelledby, not both.")
        if field is not None and (aria_label is not None or aria_labelledby is not None):
            raise ValueError("CMultiSelect cannot override its CField label with ARIA naming.")
        if field is None and aria_label is None and aria_labelledby is None:
            raise ValueError("Standalone CMultiSelect requires aria-label or aria-labelledby in trigger_attrs.")

        form_owner = get_html_form_owner(
            {"form": kwargs.form} if kwargs.form is not None else {},
            component_name="CMultiSelect",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CMultiSelect inside CForm cannot target a different native form owner.")
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            external_described_by,
        )
        error_message = merge_idrefs(
            field.error_id if field is not None and field.has_error and invalid else None,
            external_error_message if invalid else None,
        )
        selected_options = tuple(replace(option, selected=True) for option in options if option.value in selected)
        effective_open = (
            bool(kwargs.open) and not disabled and not readonly and any(not option.disabled for option in options)
        )
        anchor_name = f"--_cui-multi-select-anchor-{self.id}"
        data = {
            "value": list(selected),
            "open": effective_open,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "loop": bool(kwargs.loop),
            "closeOnSelect": bool(kwargs.close_on_select),
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
                {"value": option.value, "label": option.label, "disabled": option.disabled, "id": option.option_id}
                for option in options
            ],
        }
        snapshot = {
            **data,
            "input_id": input_id,
            "trigger_id": trigger_id,
            "listbox_id": listbox_id,
            "popup_id": f"{input_id}-popup",
            "trigger_anchor_style": {"anchor-name": anchor_name},
            "popup_anchor_style": {"position-anchor": anchor_name},
            "options_resolved": options,
            "groups": groups,
            "selected_options": selected_options,
            "empty": not selected,
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
            "readonly_values": selected if readonly and not disabled and kwargs.name else (),
            "attrs": _attrs("CMultiSelect", "attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "trigger_attrs": trigger_attrs,
            "listbox_attrs": _attrs(
                "CMultiSelect",
                "listbox_attrs",
                kwargs.listbox_attrs,
                _LISTBOX_OWNED,
            ),
        }
        self._cui_multi_select_snapshot = snapshot
        self._cui_multi_select_data = data
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_multi_select_data

    template = """
      <div
        class="cui-multi-select"
        c-data-open="open"
        c-data-empty="empty"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-close-on-select="closeOnSelect"
        c-data-match-width="matchWidth"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="root"
      >
        <button
          class="cui-multi-select__control"
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
          <span class="cui-multi-select__values" data-citry-ui-part="values">
            <span c-if="empty" data-citry-ui-part="placeholder">{{ placeholder }}</span>
            <span
              c-for="option in selected_options"
              class="cui-multi-select__chip"
              c-data-value="option.value"
              data-citry-ui-part="chip"
            >{{ option.label }}</span>
          </span>
          <span class="cui-multi-select__indicator" aria-hidden="true" data-citry-ui-part="indicator">&#9662;</span>
        </button>
        <select
          class="cui-multi-select__native"
          c-id="input_id"
          c-name="native_name"
          c-form="form"
          c-aria-label="aria_label"
          c-aria-labelledby="aria_labelledby"
          c-aria-describedby="aria_describedby"
          c-aria-errormessage="aria_errormessage"
          c-aria-invalid="aria_invalid"
          c-required="required and not readonly"
          c-disabled="native_disabled"
          multiple
          data-cui-multi-select-native
        >
          <option
            c-for="option in options_resolved"
            c-value="option.value"
            c-disabled="option.disabled"
            c-selected="option.selected"
          >{{ option.label }}</option>
        </select>
        <span hidden data-cui-multi-select-readonly-values>
          <input
            c-for="readonly_value in readonly_values"
            c-name="name"
            c-form="form"
            c-value="readonly_value"
            type="hidden"
          />
        </span>
        <div
          class="cui-multi-select__popup"
          c-id="popup_id"
          popover="manual"
          c-data-placement="placement"
          c-style="popup_anchor_style"
          hidden
          inert
          data-citry-ui-part="popup"
        >
          <div
            class="cui-multi-select__listbox"
            c-id="listbox_id"
            role="listbox"
            aria-multiselectable="true"
            c-aria-label="listbox_aria_label"
            c-aria-labelledby="aria_labelledby"
            c-bind="listbox_attrs"
            data-citry-ui-part="listbox"
          >
            <c-for each="group in groups">
              <c-if cond="group.label is None">
                <div
                  c-for="option in group.options"
                  class="cui-multi-select__option"
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
                  <span class="cui-multi-select__check" aria-hidden="true">&#10003;</span>
                  <span>
                    <span c-id="option.label_id" data-citry-ui-part="option-label">{{ option.label }}</span>
                    <span c-if="option.description is not None" c-id="option.description_id" data-citry-ui-part="option-description">{{ option.description }}</span>
                  </span>
                </div>
              </c-if>
              <c-else>
                <div class="cui-multi-select__group" c-id="group.group_id" role="group" c-aria-labelledby="group.label_id" data-citry-ui-part="group">
                  <span class="cui-multi-select__group-label" c-id="group.label_id" data-citry-ui-part="group-label">{{ group.label }}</span>
                  <div
                    c-for="option in group.options"
                    class="cui-multi-select__option"
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
                    <span class="cui-multi-select__check" aria-hidden="true">&#10003;</span>
                    <span>
                      <span c-id="option.label_id" data-citry-ui-part="option-label">{{ option.label }}</span>
                      <span c-if="option.description is not None" c-id="option.description_id" data-citry-ui-part="option-description">{{ option.description }}</span>
                    </span>
                  </div>
                </div>
              </c-else>
            </c-for>
          </div>
        </div>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      const multiSelectHandoffKey = Symbol.for('citry-ui:multi-select-handoff');
      $component({
        props: {
          value:{}, open:{}, required:{}, disabled:{}, readonly:{}, invalid:{}, loop:{},
          closeOnSelect:{}, placement:{}, matchWidth:{}, variant:{}, size:{},
          onValueChange:{}, onOpenChange:{},
        },
        init: ({els, data, props, effect, inject}) => {
          const root=els[0];
          const trigger=root.querySelector(':scope > [data-citry-ui-part="control"]');
          const nativeSelect=root.querySelector(':scope > [data-cui-multi-select-native]');
          const readonlyValues=root.querySelector(':scope > [data-cui-multi-select-readonly-values]');
          const popup=root.querySelector(':scope > [data-citry-ui-part="popup"]');
          const listbox=popup?.querySelector(':scope > [data-citry-ui-part="listbox"]');
          const valuesSurface=trigger?.querySelector('[data-citry-ui-part="values"]');
          if (!(trigger instanceof HTMLButtonElement) || !(nativeSelect instanceof HTMLSelectElement)
            || !(readonlyValues instanceof HTMLElement) || !(popup instanceof HTMLElement)
            || !(listbox instanceof HTMLElement) || !(valuesSurface instanceof HTMLElement)) {
            throw new Error('[citry-ui] CMultiSelect settled anatomy is invalid.');
          }
          const field=inject(Symbol.for('citry-ui:field'),null);
          const form=inject(Symbol.for('citry-ui:form'),null);
          const formRuntime=globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if(formRuntime?.generation!==1)throw new Error('[citry-ui] CMultiSelect form-control runtime dependency did not load.');
          const listeners=formRuntime.listeners();
          const nativeForm=nativeSelect.form;
          const coordinator=anchoredLayerRuntime.coordinatorFor(popup);
          const invalidEpisodes=new Set();
          const options=()=>[...listbox.querySelectorAll('[role="option"]')]
            .filter(option=>option.closest('[role="listbox"]')===listbox);
          const enabledOptions=()=>options().filter(option=>!option.hasAttribute('data-disabled'));
          const optionFor=value=>options().find(option=>option.dataset.value===value)??null;
          const canonical=value=>formRuntime.canonical(value);
          const normalize=value=>{
            if(!Array.isArray(value)) return null;
            const result=formRuntime.stringList([],value,canonical);if(result.reason)return null;
            const seen=new Set(result.values), output=[];if(result.values.some(item=>!optionFor(item)))return null;
            options().forEach(option=>{if(seen.has(option.dataset.value))output.push(option.dataset.value);});
            return output;
          };
          const report=(name,value,suffix='')=>{if(invalidEpisodes.has(name))return;invalidEpisodes.add(name);console.error(`[citry-ui] CMultiSelect ${name} received invalid client value${suffix}`,value);};
          const boolean=(name,fallback)=>{const value=props[name];if(value===undefined){invalidEpisodes.delete(name);return fallback;}if(typeof value==='boolean'){invalidEpisodes.delete(name);return value;}report(name,value,'; using the server fallback');return fallback;};
          const choice=(name,fallback,allowed)=>{const value=props[name];if(value===undefined){invalidEpisodes.delete(name);return fallback;}if(typeof value==='string'&&allowed.includes(value)){invalidEpisodes.delete(name);return value;}report(name,value,'; using the server fallback');return fallback;};
          const prior=root[multiSelectHandoffKey];delete root[multiSelectHandoffKey];
          const serverFingerprint=JSON.stringify(data.value);
          let committed=prior?.serverFingerprint===serverFingerprint?[...prior.committed]:[...data.value];
          let current=[...committed];
          let internalOpen=prior?.serverFingerprint===serverFingerprint?Boolean(prior.internalOpen):data.open;
          let logicalOpen=false, highlightedValue=prior?.highlightedValue??null;
          let controlledValue=false, controlledOpen=false, clientValue, clientOpen;
          let onValueChange=null,onOpenChange=null,nativeInvalid=false,active=true,generation=0;
          let typeBuffer='',typeTimer=null,tabGesture=false,pendingDirection=1,selectionTransaction=false,pendingForced=null;
          let configuration={required:data.required,disabled:data.disabled,readonly:data.readonly,invalid:data.invalid,loop:data.loop,closeOnSelect:data.closeOnSelect,placement:data.placement,matchWidth:data.matchWidth,variant:data.variant,size:data.size};
          const anchorName=data.anchorName;
          if(!anchorName.startsWith('--'))throw new Error('[citry-ui] CMultiSelect could not resolve its anchor.');
          trigger.style.setProperty('anchor-name',anchorName);popup.style.setProperty('position-anchor',anchorName);
          const same=formRuntime.same;
          const effectiveDisabled=()=>configuration.disabled||trigger.matches(':disabled');
          const eligible=()=>!effectiveDisabled()&&!configuration.readonly&&enabledOptions().length>0;
          const syncValue=()=>{
            const selected=new Set(current);root.toggleAttribute('data-empty',!current.length);
            if(!current.length){const placeholder=root.ownerDocument.createElement('span');placeholder.dataset.citryUiPart='placeholder';placeholder.textContent=data.placeholder;valuesSurface.replaceChildren(placeholder);}
            else formRuntime.renderTokens(valuesSurface,current,{className:'cui-multi-select__chip',part:'chip',
              label:value=>data.options.find(option=>option.value===value)?.label??value});
            options().forEach(option=>{const chosen=selected.has(option.dataset.value);option.setAttribute('aria-selected',chosen?'true':'false');option.toggleAttribute('data-selected',chosen);});
            formRuntime.highlight(listbox,'[role="option"]',logicalOpen?highlightedValue:null);
            formRuntime.syncTransport(nativeSelect,readonlyValues,current,{name:data.name,form:data.form,required:configuration.required,
              readonly:configuration.readonly,disabled:effectiveDisabled()});
            if(current.length)nativeInvalid=false;const invalid=configuration.invalid||nativeInvalid;root.toggleAttribute('data-invalid',invalid);formRuntime.relationships([trigger],field,{describedby:data.externalDescribedBy,errormessage:data.externalErrorMessage,required:configuration.required,disabled:effectiveDisabled(),readonly:configuration.readonly},invalid);field?.setNativeInvalid(nativeInvalid);
          };
          const sync=()=>{const disabled=effectiveDisabled();formRuntime.states(root,{open:logicalOpen,required:configuration.required,disabled,readonly:configuration.readonly,'close-on-select':configuration.closeOnSelect,'match-width':configuration.matchWidth});root.dataset.variant=configuration.variant;root.dataset.size=configuration.size;popup.dataset.placement=configuration.placement;trigger.disabled=configuration.disabled;formRuntime.attrs([trigger],{'aria-expanded':logicalOpen?'true':'false','aria-activedescendant':logicalOpen&&highlightedValue?optionFor(highlightedValue)?.id:null});syncValue();};
          const chooseHighlight=direction=>{const enabled=enabledOptions();const selected=direction<0?[...current].reverse():current;const match=selected.map(optionFor).find(option=>option&&!option.hasAttribute('data-disabled'));return match?.dataset.value??(direction<0?enabled.at(-1):enabled[0])?.dataset.value??null;};
          const layer={trigger,surface:popup,isOpen:()=>active&&logicalOpen,isEligible:eligible,requestDismiss:(reason,source)=>{if(!(tabGesture&&reason==='focus-outside'))requestOpen(false,reason,source);},forceClose:(reason,source)=>forceClose(reason==='modal'?'ancestor':reason,source)};
          const notifyOpen=(next,reason,source,forced=false)=>onOpenChange?.(next,{open:next,reason,controlled:controlledOpen,forced,source});
          const applyOpen=(next,{reason=null,source=null,focus=false}={})=>{if(next===logicalOpen){if(next&&!coordinator.register(layer))forceClose('ancestor',popup);return;}generation+=1;if(next){if(!eligible()||!coordinator.mayOpen(layer)){internalOpen=false;logicalOpen=false;popup.hidden=true;popup.inert=true;sync();return;}highlightedValue=chooseHighlight(pendingDirection);pendingDirection=1;popup.hidden=false;popup.inert=false;try{if(!popup.matches(':popover-open'))popup.showPopover();}catch(error){console.error('[citry-ui] CMultiSelect could not open:',error);popup.hidden=true;popup.inert=true;internalOpen=false;sync();return;}logicalOpen=true;popup.setAttribute('data-open','');if(!coordinator.register(layer)){logicalOpen=false;popup.hidePopover();popup.hidden=true;popup.inert=true;popup.removeAttribute('data-open');sync();return;}sync();if(focus)formRuntime.focus(trigger);optionFor(highlightedValue)?.scrollIntoView({block:'nearest'});return;}logicalOpen=false;highlightedValue=null;popup.inert=true;popup.removeAttribute('data-open');coordinator.unregister(layer);if(popup.matches(':popover-open'))popup.hidePopover();popup.hidden=true;sync();void reason;void source;};
          const requestOpen=(next,reason,source,focus=false,direction=1)=>{if(next===logicalOpen)return;if(next){pendingDirection=direction;coordinator.clearSuppression(layer);}if(controlledOpen){notifyOpen(next,reason,source);return;}internalOpen=next;applyOpen(next,{reason,source,focus});notifyOpen(next,reason,source);};
          const forceClose=(reason,source)=>{if(!logicalOpen){internalOpen=false;return;}internalOpen=false;applyOpen(false,{reason,source});if(selectionTransaction)pendingForced={reason,source};else notifyOpen(false,reason,source,true);};
          const nativeCommit=()=>formRuntime.commit(nativeSelect);
          const requestValue=(next,option,selected,source,event)=>{if(same(next,current))return false;const previous=[...current],detail={value:[...next],previousValue:previous,option,selected,controlled:controlledValue,source,sourceEvent:event};if(!controlledValue){current=[...next];committed=[...next];syncValue();}onValueChange?.([...next],detail);if(!controlledValue)nativeCommit();return true;};
          const toggleOption=(option,event,source)=>{if(!(option instanceof HTMLElement)||option.hasAttribute('data-disabled'))return;const selected=current.includes(option.dataset.value);const wanted=new Set(current);if(selected)wanted.delete(option.dataset.value);else wanted.add(option.dataset.value);const next=options().filter(item=>wanted.has(item.dataset.value)).map(item=>item.dataset.value);selectionTransaction=true;const transaction=generation;requestValue(next,option,!selected,source,event);selectionTransaction=false;if(pendingForced){const notice=pendingForced;pendingForced=null;notifyOpen(false,notice.reason,notice.source,true);return;}if(!active||transaction!==generation||!root.isConnected)return;if(configuration.closeOnSelect)requestOpen(false,'selection',option);};
          const localeLower=value=>{const lang=root.closest('[lang]')?.getAttribute('lang')??root.ownerDocument.documentElement.lang??'';try{return lang?value.toLocaleLowerCase(lang):value.toLocaleLowerCase();}catch{return value.toLowerCase();}};
          const typeahead=event=>{const altGraph=event.getModifierState?.('AltGraph')??false;if(event.isComposing||event.ctrlKey||event.metaKey||(event.altKey&&!altGraph)||event.key.length!==1)return false;const key=localeLower(event.key);typeBuffer=typeBuffer.length===1&&typeBuffer===key?key:typeBuffer+key;if(typeTimer!==null)clearTimeout(typeTimer);typeTimer=setTimeout(()=>{typeBuffer='';typeTimer=null;},500);const enabled=enabledOptions(),index=enabled.findIndex(option=>option.dataset.value===highlightedValue),ordered=[...enabled.slice(index+1),...enabled.slice(0,index+1)],match=ordered.find(option=>localeLower(option.querySelector('[data-citry-ui-part="option-label"]')?.textContent?.trim().replace(/\s+/g,' ')??'').startsWith(typeBuffer));if(!match)return false;highlightedValue=match.dataset.value;sync();match.scrollIntoView({block:'nearest'});return true;};
          const move=direction=>{const enabled=enabledOptions();if(!enabled.length)return;const index=enabled.findIndex(option=>option.dataset.value===highlightedValue),edge=direction>0?enabled[0]:enabled.at(-1),next=index<0?edge:enabled[index+direction]??(configuration.loop?edge:enabled[index]);highlightedValue=next?.dataset.value??null;sync();next?.scrollIntoView({block:'nearest'});};
          const onClick=event=>{const path=event.composedPath();if(path.includes(trigger)){if(eligible())requestOpen(!logicalOpen,'trigger',trigger,true);return;}const option=path.find(node=>node instanceof HTMLElement&&node.getAttribute('role')==='option'&&node.closest('[role="listbox"]')===listbox);if(option)toggleOption(option,event,'pointer');};
          const onPointer=event=>{if(!logicalOpen||(event.pointerType==='pen'&&(event.buttons>0||event.pressure>0)))return;const option=event.composedPath().find(node=>node instanceof HTMLElement&&node.getAttribute('role')==='option'&&node.closest('[role="listbox"]')===listbox);if(!(option instanceof HTMLElement)||option.hasAttribute('data-disabled'))return;highlightedValue=option.dataset.value;sync();};
          const onKey=event=>{if(event.target!==trigger||!eligible())return;if(!logicalOpen){if(['Enter',' ','ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();requestOpen(true,'keyboard',trigger,true,event.key==='ArrowUp'?-1:1);}return;}if(event.key==='ArrowDown'){event.preventDefault();move(1);}else if(event.key==='ArrowUp'){event.preventDefault();move(-1);}else if(event.key==='Home'){event.preventDefault();highlightedValue=enabledOptions()[0]?.dataset.value??null;sync();}else if(event.key==='End'){event.preventDefault();highlightedValue=enabledOptions().at(-1)?.dataset.value??null;sync();}else if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleOption(optionFor(highlightedValue),event,'keyboard');}else if(event.key==='Escape'){event.preventDefault();requestOpen(false,'escape',trigger);}else if(event.key==='Tab'){tabGesture=true;setTimeout(()=>{tabGesture=false;},0);requestOpen(false,'tab',trigger);}else if(typeahead(event))event.preventDefault();};
          const onToggle=event=>{if(event.target!==popup)return;const nativeOpen=popup.matches(':popover-open');if(nativeOpen===logicalOpen)return;if(nativeOpen){if(!coordinator.mayOpen(layer)||controlledOpen){popup.hidePopover();if(controlledOpen)notifyOpen(true,'native',popup);return;}internalOpen=true;logicalOpen=true;popup.hidden=false;popup.inert=false;popup.setAttribute('data-open','');highlightedValue=chooseHighlight(1);coordinator.register(layer);sync();notifyOpen(true,'native',popup);return;}if(controlledOpen&&coordinator.mayOpen(layer)){popup.hidden=false;popup.showPopover();notifyOpen(false,'native',popup);return;}internalOpen=false;logicalOpen=false;popup.inert=true;popup.hidden=true;popup.removeAttribute('data-open');highlightedValue=null;coordinator.unregister(layer);sync();notifyOpen(false,'native',popup);};
          const onInvalid=event=>{nativeInvalid=true;syncValue();event.preventDefault();formRuntime.focus(trigger);};
          const onProxyFocus=()=>{if(root.hasAttribute('data-citry-multi-select-initialized'))formRuntime.focus(trigger);};
          const onReset=event=>{const scheduled=generation;setTimeout(()=>{if(!active||event.defaultPrevented||scheduled!==generation)return;if(!controlledValue&&!same(current,data.value)){const previous=[...current];current=[...data.value];committed=[...data.value];syncValue();onValueChange?.([...current],{value:[...current],previousValue:previous,option:null,selected:false,controlled:false,source:'reset',sourceEvent:event});}else if(controlledValue&&!same(current,data.value))onValueChange?.([...data.value],{value:[...data.value],previousValue:[...current],option:null,selected:false,controlled:true,source:'reset',sourceEvent:event});if(logicalOpen)requestOpen(false,'reset',nativeForm);},0);};
          const reconcile=()=>{if(clientValue===undefined||clientValue===null){invalidEpisodes.delete('value');if(controlledValue)committed=[...current];controlledValue=false;current=[...committed];}else{const normalized=normalize(clientValue);if(normalized===null){report('value',clientValue,'; releasing control from committed selection');if(controlledValue)committed=[...current];controlledValue=false;current=[...committed];}else{invalidEpisodes.delete('value');controlledValue=true;current=normalized;}}const existing=new Set(options().map(option=>option.dataset.value));if(current.some(value=>!existing.has(value))){const previous=[...current];const next=current.filter(value=>existing.has(value));current=next;if(!controlledValue)committed=[...next];queueMicrotask(()=>onValueChange?.([...next],{value:[...next],previousValue:previous,option:null,selected:false,controlled:controlledValue,source:'structure',sourceEvent:null}));}if(clientOpen===undefined||clientOpen===null){invalidEpisodes.delete('open');controlledOpen=false;applyOpen(internalOpen,{reason:'owner',source:trigger});}else if(typeof clientOpen==='boolean'){invalidEpisodes.delete('open');controlledOpen=true;applyOpen(clientOpen,{reason:'owner',source:trigger,focus:clientOpen});}else{report('open',clientOpen,'; releasing control from committed visibility');controlledOpen=false;applyOpen(internalOpen,{reason:'owner',source:trigger});}if((effectiveDisabled()||configuration.readonly)&&logicalOpen)forceClose('ancestor',trigger);sync();};
          listeners.add(root,'click',onClick,true);listeners.add(root,'pointerover',onPointer,true);listeners.add(trigger,'keydown',onKey,true);listeners.add(popup,'toggle',onToggle);listeners.add(nativeSelect,'invalid',onInvalid);listeners.add(nativeSelect,'focus',onProxyFocus);
          const unregisterReset=formRuntime.registerReset(root,nativeSelect,{invalidate:()=>generation+=1,reset:onReset});
          const stopFieldsets=formRuntime.watchFieldset(root,trigger,reconcile);
          const stop=effect(()=>{clientValue=props.value;clientOpen=props.open;onValueChange=typeof props.onValueChange==='function'?props.onValueChange:null;onOpenChange=typeof props.onOpenChange==='function'?props.onOpenChange:null;if(props.onValueChange!=null&&onValueChange===null)report('onValueChange',props.onValueChange);else invalidEpisodes.delete('onValueChange');if(props.onOpenChange!=null&&onOpenChange===null)report('onOpenChange',props.onOpenChange);else invalidEpisodes.delete('onOpenChange');configuration={required:field?field.required:boolean('required',data.required),disabled:field?field.disabled:(form?.disabled||boolean('disabled',data.disabled)),readonly:field?field.readonly:(form?.readonly||boolean('readonly',data.readonly)),invalid:field?field.invalid:boolean('invalid',data.invalid),loop:boolean('loop',data.loop),closeOnSelect:boolean('closeOnSelect',data.closeOnSelect),placement:choice('placement',data.placement,['bottom-start','bottom-end','top-start','top-end']),matchWidth:boolean('matchWidth',data.matchWidth),variant:choice('variant',data.variant,['outline','filled','plain']),size:choice('size',data.size,['sm','md','lg'])};reconcile();});
          const nativeMode={className:'cui-form-control__native--enhanced'};
          root.setAttribute('data-citry-multi-select-initialized','');formRuntime.enhanceNative(nativeSelect,trigger,nativeMode);reconcile();
          return()=>{active=false;generation+=1;if(typeTimer!==null)clearTimeout(typeTimer);root[multiSelectHandoffKey]={serverFingerprint,committed:[...committed],internalOpen,highlightedValue};stop?.();stopFieldsets();unregisterReset();listeners.stop();coordinator.unregister(layer,{reason:'ancestor',source:root,cascade:true});field?.setNativeInvalid(false);root.removeAttribute('data-citry-multi-select-initialized');formRuntime.enhanceNative(nativeSelect,trigger,nativeMode,false);};
        },
      })
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-multi-select) {
          --_cui-multi-select-background:var(--cui-multi-select-background,Canvas);
          --_cui-multi-select-foreground:var(--cui-multi-select-foreground,CanvasText);
          --_cui-multi-select-placeholder-color:var(--cui-multi-select-placeholder-color,light-dark(#667085,#a4a7ae));
          --_cui-multi-select-muted-color:var(--cui-multi-select-muted-color,light-dark(#667085,#a4a7ae));
          --_cui-multi-select-border-color:var(--cui-multi-select-border-color,light-dark(#d0d5dd,#535862));
          --_cui-multi-select-hover-background:var(--cui-multi-select-hover-background,color-mix(in srgb,CanvasText 7%,transparent));
          --_cui-multi-select-selected-background:var(--cui-multi-select-selected-background,light-dark(#dbeafe,#1e3a5f));
          --_cui-multi-select-selected-foreground:var(--cui-multi-select-selected-foreground,light-dark(#1849a9,#d1e9ff));
          --_cui-multi-select-chip-background:var(--cui-multi-select-chip-background,color-mix(in srgb,CanvasText 9%,Canvas));
          --_cui-multi-select-chip-foreground:var(--cui-multi-select-chip-foreground,CanvasText);
          --_cui-multi-select-focus-color:var(--cui-multi-select-focus-color,Highlight);
          --_cui-multi-select-radius:var(--cui-multi-select-radius,.625rem);
          --_cui-multi-select-control-padding:var(--cui-multi-select-control-padding,.5rem .625rem);
          --_cui-multi-select-option-padding:var(--cui-multi-select-option-padding,.5rem .625rem);
          --_cui-multi-select-max-block-size:var(--cui-multi-select-max-block-size,18rem);
          --_cui-multi-select-offset:var(--cui-multi-select-offset,.25rem);
          --_cui-multi-select-shadow:var(--cui-multi-select-shadow,0 .75rem 2rem color-mix(in srgb,CanvasText 18%,transparent));
          --_cui-multi-select-duration:var(--cui-multi-select-duration,120ms);
          box-sizing:border-box;display:grid;min-inline-size:0;color:var(--_cui-multi-select-foreground);font-family:ui-sans-serif,system-ui,sans-serif;
        }
        :where(.cui-multi-select[data-size="sm"]){font-size:.875rem;--_cui-multi-select-control-padding:.375rem .5rem;--_cui-multi-select-option-padding:.375rem .5rem}
        :where(.cui-multi-select[data-size="lg"]){font-size:1.0625rem;--_cui-multi-select-control-padding:.625rem .75rem;--_cui-multi-select-option-padding:.625rem .75rem}
        :where(.cui-multi-select:not([data-citry-multi-select-initialized]) .cui-multi-select__control),
        :where(.cui-multi-select:not([data-citry-multi-select-initialized]) .cui-multi-select__popup){display:none}
        :where(.cui-multi-select:not([data-citry-multi-select-initialized]) .cui-multi-select__native){box-sizing:border-box;inline-size:100%;min-block-size:5rem;padding:.5rem;border:1px solid var(--_cui-multi-select-border-color);border-radius:var(--_cui-multi-select-radius);background:var(--_cui-multi-select-background);color:var(--_cui-multi-select-foreground);font:inherit}
        :where(.cui-multi-select__control){box-sizing:border-box;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:.5rem;inline-size:100%;min-inline-size:0;margin:0;padding:var(--_cui-multi-select-control-padding);border:1px solid transparent;border-radius:var(--_cui-multi-select-radius);background:var(--_cui-multi-select-background);color:var(--_cui-multi-select-foreground);font:inherit;text-align:start;cursor:pointer}
        :where(.cui-multi-select[data-variant="outline"] .cui-multi-select__control){border-color:var(--_cui-multi-select-border-color)}
        :where(.cui-multi-select[data-variant="filled"] .cui-multi-select__control){background:color-mix(in srgb,CanvasText 6%,Canvas)}
        :where(.cui-multi-select[data-variant="plain"] .cui-multi-select__control){padding-inline:0}
        :where(.cui-multi-select__control:focus-visible){outline:2px solid var(--_cui-multi-select-focus-color);outline-offset:2px}
        :where(.cui-multi-select[data-disabled] .cui-multi-select__control){color:var(--_cui-multi-select-muted-color);cursor:not-allowed;opacity:.72}
        :where(.cui-multi-select[data-readonly]:not([data-disabled]) .cui-multi-select__control){cursor:default}
        :where(.cui-multi-select[data-invalid] .cui-multi-select__control){border-color:light-dark(#d92d20,#f97066)}
        :where(.cui-multi-select__values){display:flex;flex-wrap:wrap;align-items:center;gap:.25rem;min-inline-size:0;overflow-wrap:anywhere}
        :where(.cui-multi-select [data-citry-ui-part="placeholder"]){color:var(--_cui-multi-select-placeholder-color)}
        :where(.cui-multi-select__chip){display:inline-flex;max-inline-size:100%;padding:.15rem .4rem;border-radius:calc(var(--_cui-multi-select-radius) - .2rem);background:var(--_cui-multi-select-chip-background);color:var(--_cui-multi-select-chip-foreground);overflow-wrap:anywhere}
        :where(.cui-multi-select__indicator){transition:transform var(--_cui-multi-select-duration) ease-out}
        :where(.cui-multi-select[data-open] .cui-multi-select__indicator){transform:rotate(180deg)}
        :where(.cui-multi-select__popup){position:fixed;box-sizing:border-box;inline-size:min(14rem,calc(100vw - 2rem));max-inline-size:calc(100vw - 2rem);max-block-size:min(var(--_cui-multi-select-max-block-size),calc(100vh - 2rem));margin:0;padding:.25rem;overflow:auto;border:1px solid var(--_cui-multi-select-border-color);border-radius:var(--_cui-multi-select-radius);background:var(--_cui-multi-select-background);color:var(--_cui-multi-select-foreground);box-shadow:var(--_cui-multi-select-shadow);font:inherit;overscroll-behavior:contain}
        :where(.cui-multi-select__popup:not(:popover-open)){display:none}
        :where(.cui-multi-select[data-match-width] .cui-multi-select__popup){inline-size:min(anchor-size(width),calc(100vw - 2rem))}
        :where(.cui-multi-select__popup[data-placement="bottom-start"]){position-area:block-end span-inline-end;margin-block-start:var(--_cui-multi-select-offset)}
        :where(.cui-multi-select__popup[data-placement="bottom-end"]){position-area:block-end span-inline-start;margin-block-start:var(--_cui-multi-select-offset)}
        :where(.cui-multi-select__popup[data-placement="top-start"]){position-area:block-start span-inline-end;margin-block-end:var(--_cui-multi-select-offset)}
        :where(.cui-multi-select__popup[data-placement="top-end"]){position-area:block-start span-inline-start;margin-block-end:var(--_cui-multi-select-offset)}
        :where(.cui-multi-select__listbox),:where(.cui-multi-select__group){display:grid;gap:.125rem;min-inline-size:0}
        :where(.cui-multi-select__group-label){padding:.5rem .625rem .25rem;color:var(--_cui-multi-select-muted-color);font-size:.8125em;font-weight:700;overflow-wrap:anywhere}
        :where(.cui-multi-select__option){box-sizing:border-box;display:grid;grid-template-columns:1rem minmax(0,1fr);gap:.5rem;min-inline-size:0;padding:var(--_cui-multi-select-option-padding);border-radius:calc(var(--_cui-multi-select-radius) - .125rem);line-height:1.35;cursor:default}
        :where(.cui-multi-select__option[data-highlighted]:not([data-disabled])){background:var(--_cui-multi-select-hover-background);outline:2px solid var(--_cui-multi-select-focus-color);outline-offset:-2px}
        :where(.cui-multi-select__option[data-selected]){background:var(--_cui-multi-select-selected-background);color:var(--_cui-multi-select-selected-foreground)}
        :where(.cui-multi-select__option[data-disabled]){color:var(--_cui-multi-select-muted-color);opacity:.72}
        :where(.cui-multi-select__check){visibility:hidden}:where(.cui-multi-select__option[data-selected] .cui-multi-select__check){visibility:visible}
        :where(.cui-multi-select__option [data-citry-ui-part="option-label"]),:where(.cui-multi-select__option [data-citry-ui-part="option-description"]){display:block;min-inline-size:0;overflow-wrap:anywhere}
        :where(.cui-multi-select__option [data-citry-ui-part="option-description"]){color:var(--_cui-multi-select-muted-color);font-size:.875em}
        :where(.cui-multi-select__option[data-selected] [data-citry-ui-part="option-description"]){color:currentColor;opacity:.82}
        @media(prefers-reduced-motion:reduce){:where(.cui-multi-select){--_cui-multi-select-duration:0ms}}
        @media(forced-colors:active){:where(.cui-multi-select__control),:where(.cui-multi-select__popup){border-color:CanvasText}:where(.cui-multi-select__option[data-selected]){background:Highlight;color:HighlightText;forced-color-adjust:none}}
        @media print{:where(.cui-multi-select__popup){display:none!important}:where(.cui-multi-select__control){border-color:CanvasText;background:transparent;color:CanvasText;box-shadow:none}}
      }
    """


__all__ = [
    "CMultiSelect",
    "CMultiSelectChangeSource",
    "CMultiSelectOpenChangeDetail",
    "CMultiSelectOpenReason",
    "CMultiSelectOption",
    "CMultiSelectPlacement",
    "CMultiSelectSize",
    "CMultiSelectValueChangeDetail",
    "CMultiSelectVariant",
]
