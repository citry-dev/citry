"""Styled progressive-enhancement single-value Select family."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
    ANCHORED_LAYER_RUNTIME_JS,
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

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      const selectHandoffKey = Symbol.for("citry-ui:select-handoff");

      $component({
        props: {
          value: {}, open: {}, required: {}, disabled: {}, readonly: {}, invalid: {},
          loop: {}, placement: {}, matchWidth: {}, variant: {}, size: {},
          onValueChange: {}, onOpenChange: {},
        },
        init: ({els, data, props, effect, inject}) => {
          const root = els[0];
          const trigger = root.querySelector(':scope > [data-citry-ui-part="control"]');
          const nativeSelect = root.querySelector(':scope > [data-cui-select-native]');
          const readonlyInput = root.querySelector(':scope > [data-cui-select-readonly-value]');
          const popup = root.querySelector(':scope > [data-citry-ui-part="popup"]');
          const listbox = popup?.querySelector(':scope > [data-citry-ui-part="listbox"]');
          if (
            !(trigger instanceof HTMLButtonElement)
            || !(nativeSelect instanceof HTMLSelectElement)
            || !(readonlyInput instanceof HTMLInputElement)
            || !(popup instanceof HTMLElement)
            || !(listbox instanceof HTMLElement)
          ) {
            throw new Error("[citry-ui] CSelect settled anatomy is invalid.");
          }
          const field = inject(Symbol.for("citry-ui:field"), null);
          const form = inject(Symbol.for("citry-ui:form"), null);
          const nativeForm = nativeSelect.form;
          const coordinator = anchoredLayerRuntime.coordinatorFor(popup);
          const invalidEpisodes = new Set();
          const options = () => [...listbox.querySelectorAll('[role="option"]')]
            .filter((option) => option.closest('[role="listbox"]') === listbox);
          const optionFor = (value) => options().find((option) => option.dataset.value === value) ?? null;
          const enabledOptions = () => options().filter((option) => !option.hasAttribute('data-disabled'));
          const canonicalString = (value) => (
            typeof value === 'string' && value.length > 0 && !value.includes('\0')
              ? value.replace(/\r\n?/g, '\n')
              : null
          );
          const report = (name, value, suffix = '') => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CSelect ${name} received invalid client value${suffix}`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
            report(name, supplied, '; using the server fallback');
            return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'string' && allowed.includes(supplied)) {
              invalidEpisodes.delete(name); return supplied;
            }
            report(name, supplied, '; using the server fallback');
            return fallback;
          };
          const prior = root[selectHandoffKey];
          delete root[selectHandoffKey];
          const serverFingerprint = JSON.stringify(data.value);
          let committedValue = prior?.serverFingerprint === serverFingerprint
            ? prior.committedValue
            : data.value;
          let currentValue = committedValue;
          let internalOpen = prior?.serverFingerprint === serverFingerprint
            ? Boolean(prior.internalOpen)
            : data.open;
          let logicalOpen = false;
          let highlightedValue = prior?.highlightedValue ?? null;
          let controlledValue = false;
          let controlledOpen = false;
          let clientValue;
          let clientOpen;
          let onValueChange = null;
          let onOpenChange = null;
          let nativeInvalid = false;
          let active = true;
          let generation = 0;
          let typeBuffer = '';
          let typeTimer = null;
          let tabGesture = false;
          let pendingOpenDirection = 1;
          let selectionTransaction = false;
          let pendingForcedNotice = null;
          let pendingStructure = prior?.pendingStructure ?? null;
          let configuration = {
            required:data.required,
            disabled:data.disabled,
            readonly:data.readonly,
            invalid:data.invalid,
            loop:data.loop,
            placement:data.placement,
            matchWidth:data.matchWidth,
            variant:data.variant,
            size:data.size,
          };

          const anchorName = data.anchorName;
          if (!anchorName.startsWith('--')) {
            throw new Error('[citry-ui] CSelect could not resolve its CSS anchor name.');
          }
          trigger.style.setProperty('anchor-name', anchorName);
          popup.style.setProperty('position-anchor', anchorName);

          const idrefs = (...values) => {
            const output = [];
            values.forEach((value) => {
              if (typeof value !== 'string') return;
              value.split(/\s+/).filter(Boolean).forEach((token) => {
                if (!output.includes(token)) output.push(token);
              });
            });
            return output.join(' ') || null;
          };
          const effectiveDisabled = () => configuration.disabled || trigger.matches(':disabled');
          const eligible = () => !effectiveDisabled() && !configuration.readonly;
          const selectedOption = () => optionFor(currentValue);
          const labelFor = (value) => data.options.find((option) => option.value === value)?.label ?? null;
          const actualOpen = () => active && logicalOpen;
          const layer = {
            trigger,
            surface:popup,
            isOpen:actualOpen,
            isEligible:eligible,
            requestDismiss:(reason, source) => {
              if (tabGesture && reason === 'focus-outside') return;
              requestOpen(false, reason, source);
            },
            forceClose:(reason, source) => forceClose(reason === 'modal' ? 'ancestor' : reason, source),
          };
          const notifyOpen = (next, reason, source, forced = false) => {
            onOpenChange?.(next, {open:next, reason, controlled:controlledOpen, forced, source});
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
            if (describedBy) trigger.setAttribute('aria-describedby', describedBy);
            else trigger.removeAttribute('aria-describedby');
            if (errorMessage) trigger.setAttribute('aria-errormessage', errorMessage);
            else trigger.removeAttribute('aria-errormessage');
          };
          const syncValue = () => {
            const selected = selectedOption();
            const empty = selected === null;
            root.toggleAttribute('data-empty', empty);
            root.querySelector('[data-citry-ui-part="value"]').textContent = selected?.querySelector(
              '[data-citry-ui-part="option-label"]',
            )?.textContent ?? data.placeholder;
            options().forEach((option) => {
              const chosen = option === selected;
              option.setAttribute('aria-selected', chosen ? 'true' : 'false');
              option.toggleAttribute('data-selected', chosen);
              option.toggleAttribute('data-highlighted', logicalOpen && option.dataset.value === highlightedValue);
            });
            nativeSelect.value = currentValue ?? '';
            readonlyInput.value = currentValue ?? '';
            const readonlySubmission = configuration.readonly && !effectiveDisabled() && Boolean(data.name);
            nativeSelect.name = readonlySubmission ? '' : (data.name ?? '');
            nativeSelect.disabled = effectiveDisabled() || configuration.readonly;
            nativeSelect.required = configuration.required && !configuration.readonly && !effectiveDisabled();
            readonlyInput.name = readonlySubmission ? data.name : '';
            readonlyInput.disabled = !readonlySubmission;
            if (currentValue !== null) nativeInvalid = false;
            const invalid = configuration.invalid || nativeInvalid;
            root.toggleAttribute('data-invalid', invalid);
            if (invalid) trigger.setAttribute('aria-invalid', 'true');
            else trigger.removeAttribute('aria-invalid');
            syncRelationships(invalid);
            field?.setNativeInvalid(nativeInvalid);
          };
          const syncPresentation = () => {
            const disabled = effectiveDisabled();
            root.toggleAttribute('data-open', logicalOpen);
            root.toggleAttribute('data-required', configuration.required);
            root.toggleAttribute('data-disabled', disabled);
            root.toggleAttribute('data-readonly', configuration.readonly);
            root.toggleAttribute('data-match-width', configuration.matchWidth);
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            popup.dataset.placement = configuration.placement;
            trigger.disabled = configuration.disabled;
            trigger.setAttribute('aria-expanded', logicalOpen ? 'true' : 'false');
            if (configuration.required) trigger.setAttribute('aria-required', 'true');
            else trigger.removeAttribute('aria-required');
            if (disabled) trigger.setAttribute('aria-disabled', 'true');
            else trigger.removeAttribute('aria-disabled');
            if (configuration.readonly) trigger.setAttribute('aria-readonly', 'true');
            else trigger.removeAttribute('aria-readonly');
            if (logicalOpen && highlightedValue !== null) {
              trigger.setAttribute('aria-activedescendant', optionFor(highlightedValue)?.id ?? '');
            } else trigger.removeAttribute('aria-activedescendant');
            syncValue();
          };
          const chooseHighlight = (direction = 1) => {
            const enabled = enabledOptions();
            const selected = selectedOption();
            if (selected && !selected.hasAttribute('data-disabled')) return selected.dataset.value;
            return (direction < 0 ? enabled.at(-1) : enabled[0])?.dataset.value ?? null;
          };
          const applyOpen = (next, {reason = null, source = null, focus = false} = {}) => {
            if (next === logicalOpen) {
              if (next && !coordinator.register(layer)) forceClose('ancestor', popup);
              return;
            }
            generation += 1;
            const currentGeneration = generation;
            if (next) {
              if (!eligible() || !coordinator.mayOpen(layer)) {
                internalOpen = false;
                logicalOpen = false;
                popup.hidden = true;
                popup.inert = true;
                syncPresentation();
                return;
              }
              highlightedValue = chooseHighlight(pendingOpenDirection);
              pendingOpenDirection = 1;
              popup.hidden = false;
              popup.inert = false;
              try {
                if (!popup.matches(':popover-open')) popup.showPopover();
              } catch (error) {
                console.error('[citry-ui] CSelect could not open its popup:', error, popup);
                popup.hidden = true;
                popup.inert = true;
                internalOpen = false;
                logicalOpen = false;
                syncPresentation();
                return;
              }
              logicalOpen = true;
              popup.setAttribute('data-open', '');
              if (!coordinator.register(layer)) {
                logicalOpen = false;
                popup.hidePopover();
                popup.hidden = true;
                popup.inert = true;
                popup.removeAttribute('data-open');
                syncPresentation();
                return;
              }
              syncPresentation();
              if (focus) trigger.focus({preventScroll:true});
              const rawDuration = getComputedStyle(popup)
                .getPropertyValue('--_cui-select-duration')
                .trim();
              const milliseconds = rawDuration.endsWith('ms')
                ? Math.max(0, Number.parseFloat(rawDuration) || 0)
                : rawDuration.endsWith('s')
                  ? Math.max(0, (Number.parseFloat(rawDuration) || 0) * 1000)
                  : Math.max(0, Number.parseFloat(rawDuration) || 0);
              if (milliseconds > 0) {
                popup.animate(
                  [{opacity:0, transform:'translateY(-0.2rem) scale(0.98)'}, {opacity:1, transform:'none'}],
                  {duration:milliseconds, easing:'ease-out'},
                ).finished.catch(() => {});
              }
              optionFor(highlightedValue)?.scrollIntoView({block:'nearest'});
              return;
            }
            logicalOpen = false;
            highlightedValue = null;
            popup.inert = true;
            popup.removeAttribute('data-open');
            coordinator.unregister(layer);
            if (popup.matches(':popover-open')) popup.hidePopover();
            popup.hidden = true;
            syncPresentation();
            if (
              reason !== 'outside'
              && reason !== 'focus-outside'
              && reason !== 'tab'
              && reason !== 'ancestor'
              && anchoredLayerRuntime.composedContains(popup, coordinator.deepActiveElement())
              && trigger.isConnected
              && !effectiveDisabled()
            ) trigger.focus({preventScroll:true});
            if (currentGeneration !== generation) return;
            void source;
          };
          const requestOpen = (next, reason, source, focus = false, direction = 1) => {
            if (next === logicalOpen) return;
            if (next) {
              pendingOpenDirection = direction;
              coordinator.clearSuppression(layer);
            }
            if (controlledOpen) {
              notifyOpen(next, reason, source);
              return;
            }
            internalOpen = next;
            applyOpen(next, {reason, source, focus});
            notifyOpen(next, reason, source);
          };
          const forceClose = (reason, source) => {
            if (!logicalOpen) { internalOpen = false; return; }
            internalOpen = false;
            applyOpen(false, {reason, source});
            if (selectionTransaction) pendingForcedNotice = {reason, source};
            else notifyOpen(false, reason, source, true);
          };
          const emitNativeCommit = () => {
            nativeSelect.dispatchEvent(new Event('input', {bubbles:true}));
            nativeSelect.dispatchEvent(new Event('change', {bubbles:true}));
          };
          const requestValue = (next, option, source, sourceEvent) => {
            if (next === currentValue || option?.hasAttribute('data-disabled')) return false;
            const previousValue = currentValue;
            const detail = {
              value:next,
              previousValue,
              option,
              controlled:controlledValue,
              source,
              sourceEvent,
            };
            if (!controlledValue) {
              currentValue = next;
              committedValue = next;
              syncValue();
            }
            onValueChange?.(next, detail);
            if (!controlledValue) emitNativeCommit();
            return true;
          };
          const selectOption = (option, event, source) => {
            if (!(option instanceof HTMLElement) || option.hasAttribute('data-disabled')) return;
            selectionTransaction = true;
            const transactionGeneration = generation;
            requestValue(option.dataset.value, option, source, event);
            selectionTransaction = false;
            if (pendingForcedNotice) {
              const notice = pendingForcedNotice;
              pendingForcedNotice = null;
              notifyOpen(false, notice.reason, notice.source, true);
              return;
            }
            if (!active || transactionGeneration !== generation || !root.isConnected) return;
            requestOpen(false, 'selection', option);
          };
          const localeLower = (value) => {
            const lang = root.closest('[lang]')?.getAttribute('lang')
              ?? root.ownerDocument.documentElement.lang
              ?? '';
            try { return lang ? value.toLocaleLowerCase(lang) : value.toLocaleLowerCase(); }
            catch { return value.toLowerCase(); }
          };
          const typeahead = (event) => {
            const altGraph = event.getModifierState?.('AltGraph') ?? false;
            if (
              event.isComposing || event.ctrlKey || event.metaKey
              || (event.altKey && !altGraph) || event.key.length !== 1
            ) return false;
            const key = localeLower(event.key);
            typeBuffer = typeBuffer.length === 1 && typeBuffer === key ? key : typeBuffer + key;
            if (typeTimer !== null) clearTimeout(typeTimer);
            typeTimer = setTimeout(() => { typeBuffer=''; typeTimer=null; }, 500);
            const enabled = enabledOptions();
            const startValue = logicalOpen ? highlightedValue : currentValue;
            const index = enabled.findIndex((option) => option.dataset.value === startValue);
            const ordered = [...enabled.slice(index + 1), ...enabled.slice(0, index + 1)];
            const match = ordered.find((option) => {
              const label = option.querySelector('[data-citry-ui-part="option-label"]')?.textContent ?? '';
              return localeLower(label.trim().replace(/\s+/g, ' ')).startsWith(typeBuffer);
            });
            if (!match) return false;
            if (logicalOpen) {
              highlightedValue = match.dataset.value;
              syncPresentation();
              match.scrollIntoView({block:'nearest'});
            } else requestValue(match.dataset.value, match, 'keyboard', event);
            return true;
          };
          const onClick = (event) => {
            const path = event.composedPath();
            if (path.includes(trigger)) {
              if (!eligible()) return;
              requestOpen(!logicalOpen, 'trigger', trigger, true);
              return;
            }
            const option = path.find((node) => (
              node instanceof HTMLElement
              && node.getAttribute('role') === 'option'
              && node.closest('[role="listbox"]') === listbox
            ));
            if (option) selectOption(option, event, 'pointer');
          };
          const onPointerOver = (event) => {
            if (!logicalOpen || (event.pointerType === 'pen' && (event.buttons > 0 || event.pressure > 0))) return;
            const option = event.composedPath().find((node) => (
              node instanceof HTMLElement
              && node.getAttribute('role') === 'option'
              && node.closest('[role="listbox"]') === listbox
            ));
            if (!(option instanceof HTMLElement) || option.hasAttribute('data-disabled')) return;
            highlightedValue = option.dataset.value;
            syncPresentation();
          };
          const moveHighlight = (direction) => {
            const enabled = enabledOptions();
            if (!enabled.length) return;
            const index = enabled.findIndex((option) => option.dataset.value === highlightedValue);
            const initial = direction > 0 ? enabled[0] : enabled.at(-1);
            const next = index < 0
              ? initial
              : enabled[index + direction]
                ?? (configuration.loop ? initial : enabled[index]);
            highlightedValue = next?.dataset.value ?? null;
            syncPresentation();
            next?.scrollIntoView({block:'nearest'});
          };
          const onKeyDown = (event) => {
            if (event.target !== trigger || !eligible()) return;
            if (!logicalOpen) {
              if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                requestOpen(true, 'keyboard', trigger, true, event.key === 'ArrowUp' ? -1 : 1);
                return;
              }
              if (typeahead(event)) event.preventDefault();
              return;
            }
            if (event.key === 'ArrowDown') { event.preventDefault(); moveHighlight(1); }
            else if (event.key === 'ArrowUp') { event.preventDefault(); moveHighlight(-1); }
            else if (event.key === 'Home') {
              event.preventDefault();
              highlightedValue = enabledOptions()[0]?.dataset.value ?? null;
              syncPresentation();
            } else if (event.key === 'End') {
              event.preventDefault();
              highlightedValue = enabledOptions().at(-1)?.dataset.value ?? null;
              syncPresentation();
            } else if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              selectOption(optionFor(highlightedValue), event, 'keyboard');
            } else if (event.key === 'Escape') {
              event.preventDefault();
              requestOpen(false, 'escape', trigger);
            } else if (event.key === 'Tab') {
              tabGesture = true;
              setTimeout(() => { tabGesture=false; }, 0);
              requestOpen(false, 'tab', trigger);
            } else if (typeahead(event)) event.preventDefault();
          };
          const onToggle = (event) => {
            if (event.target !== popup) return;
            const nativeOpen = popup.matches(':popover-open');
            if (nativeOpen === logicalOpen) return;
            if (nativeOpen) {
              if (!coordinator.mayOpen(layer) || controlledOpen) {
                popup.hidePopover();
                if (controlledOpen) notifyOpen(true, 'native', popup);
                return;
              }
              internalOpen = true;
              logicalOpen = true;
              popup.hidden = false;
              popup.inert = false;
              popup.setAttribute('data-open', '');
              highlightedValue = chooseHighlight();
              coordinator.register(layer);
              syncPresentation();
              notifyOpen(true, 'native', popup);
              return;
            }
            if (controlledOpen && coordinator.mayOpen(layer)) {
              popup.hidden = false;
              popup.showPopover();
              notifyOpen(false, 'native', popup);
              return;
            }
            internalOpen = false;
            logicalOpen = false;
            popup.inert = true;
            popup.hidden = true;
            popup.removeAttribute('data-open');
            highlightedValue = null;
            coordinator.unregister(layer);
            syncPresentation();
            notifyOpen(false, 'native', popup);
          };
          const onInvalid = (event) => {
            nativeInvalid = true;
            syncValue();
            event.preventDefault();
            trigger.focus({preventScroll:true});
          };
          const onProxyFocus = () => {
            if (root.hasAttribute('data-citry-select-initialized')) trigger.focus({preventScroll:true});
          };
          const onReset = (event) => {
            const scheduled = generation;
            setTimeout(() => {
              if (!active || event.defaultPrevented || scheduled !== generation) return;
              if (!controlledValue && currentValue !== data.value) {
                const previousValue = currentValue;
                currentValue = data.value;
                committedValue = data.value;
                syncValue();
                onValueChange?.(currentValue, {
                  value:currentValue, previousValue, option:selectedOption(), controlled:false,
                  source:'reset', sourceEvent:event,
                });
              }
              if (logicalOpen) requestOpen(false, 'reset', nativeForm);
            }, 0);
          };
          const reconcileControlled = () => {
            if (clientValue === undefined) {
              invalidEpisodes.delete('value');
              if (controlledValue) committedValue = currentValue;
              controlledValue = false;
              currentValue = committedValue;
            } else if (clientValue === null) {
              invalidEpisodes.delete('value');
              controlledValue = true;
              currentValue = null;
              pendingStructure = null;
            } else {
              const normalized = canonicalString(clientValue);
              if (normalized === null) {
                report('value', clientValue, '; releasing control from the committed value');
                if (controlledValue) committedValue = currentValue;
                controlledValue = false;
                currentValue = committedValue;
              } else if (!optionFor(normalized)) {
                controlledValue = true;
                currentValue = null;
                report('value', clientValue, '; the settled collection does not contain this value');
                if (pendingStructure !== normalized) {
                  pendingStructure = normalized;
                  const scheduled = generation;
                  queueMicrotask(() => {
                    if (active && scheduled === generation && pendingStructure === normalized) {
                      onValueChange?.(null, {
                        value:null, previousValue:normalized, option:null, controlled:true,
                        source:'structure', sourceEvent:null,
                      });
                    }
                  });
                }
              } else {
                invalidEpisodes.delete('value');
                pendingStructure = null;
                controlledValue = true;
                currentValue = normalized;
              }
            }
            if (currentValue !== null && !optionFor(currentValue)) {
              const previousValue = currentValue;
              currentValue = null;
              committedValue = null;
              if (pendingStructure !== previousValue) {
                pendingStructure = previousValue;
                queueMicrotask(() => onValueChange?.(null, {
                  value:null, previousValue, option:null, controlled:false,
                  source:'structure', sourceEvent:null,
                }));
              }
            }
            if (clientOpen === undefined || clientOpen === null) {
              invalidEpisodes.delete('open');
              controlledOpen = false;
              applyOpen(internalOpen, {reason:'owner', source:trigger});
            } else if (typeof clientOpen === 'boolean') {
              invalidEpisodes.delete('open');
              controlledOpen = true;
              applyOpen(clientOpen, {reason:'owner', source:trigger, focus:clientOpen});
            } else {
              report('open', clientOpen, '; releasing control from committed visibility');
              controlledOpen = false;
              applyOpen(internalOpen, {reason:'owner', source:trigger});
            }
            if ((effectiveDisabled() || configuration.readonly) && logicalOpen) {
              forceClose('ancestor', trigger);
            }
            syncPresentation();
          };

          root.addEventListener('click', onClick, true);
          root.addEventListener('pointerover', onPointerOver, true);
          trigger.addEventListener('keydown', onKeyDown, true);
          popup.addEventListener('toggle', onToggle);
          nativeSelect.addEventListener('invalid', onInvalid);
          nativeSelect.addEventListener('focus', onProxyFocus);
          nativeForm?.addEventListener('reset', onReset);

          const fieldsetObservers = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const observer = new MutationObserver(reconcileControlled);
            observer.observe(ancestor, {attributes:true, childList:true, attributeFilter:['disabled']});
            fieldsetObservers.push(observer);
          }
          const stop = effect(() => {
            clientValue = props.value;
            clientOpen = props.open;
            onValueChange = typeof props.onValueChange === 'function' ? props.onValueChange : null;
            onOpenChange = typeof props.onOpenChange === 'function' ? props.onOpenChange : null;
            if (props.onValueChange != null && onValueChange === null) report('onValueChange', props.onValueChange);
            else invalidEpisodes.delete('onValueChange');
            if (props.onOpenChange != null && onOpenChange === null) report('onOpenChange', props.onOpenChange);
            else invalidEpisodes.delete('onOpenChange');
            configuration = {
              required:field ? field.required : resolveBoolean('required', data.required),
              disabled:field
                ? field.disabled
                : (form?.disabled || resolveBoolean('disabled', data.disabled)),
              readonly:field
                ? field.readonly
                : (form?.readonly || resolveBoolean('readonly', data.readonly)),
              invalid:field ? field.invalid : resolveBoolean('invalid', data.invalid),
              loop:resolveBoolean('loop', data.loop),
              placement:resolveChoice('placement', data.placement, [
                'bottom-start','bottom-end','top-start','top-end',
              ]),
              matchWidth:resolveBoolean('matchWidth', data.matchWidth),
              variant:resolveChoice('variant', data.variant, ['outline','filled','plain']),
              size:resolveChoice('size', data.size, ['sm','md','lg']),
            };
            reconcileControlled();
          });
          root.setAttribute('data-citry-select-initialized', '');
          nativeSelect.tabIndex = -1;
          nativeSelect.setAttribute('aria-hidden', 'true');
          reconcileControlled();

          return () => {
            active = false;
            generation += 1;
            if (typeTimer !== null) clearTimeout(typeTimer);
            root[selectHandoffKey] = {
              serverFingerprint,
              committedValue,
              internalOpen,
              highlightedValue,
              pendingStructure,
            };
            stop?.();
            fieldsetObservers.forEach((observer) => observer.disconnect());
            root.removeEventListener('click', onClick, true);
            root.removeEventListener('pointerover', onPointerOver, true);
            trigger.removeEventListener('keydown', onKeyDown, true);
            popup.removeEventListener('toggle', onToggle);
            nativeSelect.removeEventListener('invalid', onInvalid);
            nativeSelect.removeEventListener('focus', onProxyFocus);
            nativeForm?.removeEventListener('reset', onReset);
            coordinator.unregister(layer, {reason:'ancestor', source:root, cascade:true});
            field?.setNativeInvalid(false);
            root.removeAttribute('data-citry-select-initialized');
            nativeSelect.removeAttribute('tabindex');
            nativeSelect.removeAttribute('aria-hidden');
          };
        },
      })
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-select) {
          --_cui-select-anchor: --_cui-select-unresolved;
          --_cui-select-background: var(--cui-select-background, Canvas);
          --_cui-select-foreground: var(--cui-select-foreground, CanvasText);
          --_cui-select-placeholder-color: var(
            --cui-select-placeholder-color,
            light-dark(#667085, #a4a7ae)
          );
          --_cui-select-muted-color: var(--cui-select-muted-color, light-dark(#667085, #a4a7ae));
          --_cui-select-border-color: var(--cui-select-border-color, light-dark(#d0d5dd, #535862));
          --_cui-select-hover-background: var(
            --cui-select-hover-background,
            color-mix(in srgb, CanvasText 7%, transparent)
          );
          --_cui-select-selected-background: var(
            --cui-select-selected-background,
            light-dark(#dbeafe, #1e3a5f)
          );
          --_cui-select-selected-foreground: var(
            --cui-select-selected-foreground,
            light-dark(#1849a9, #d1e9ff)
          );
          --_cui-select-focus-color: var(--cui-select-focus-color, Highlight);
          --_cui-select-radius: var(--cui-select-radius, 0.625rem);
          --_cui-select-control-padding: var(--cui-select-control-padding, 0.625rem 0.75rem);
          --_cui-select-option-padding: var(--cui-select-option-padding, 0.5rem 0.625rem);
          --_cui-select-max-block-size: var(--cui-select-max-block-size, 18rem);
          --_cui-select-offset: var(--cui-select-offset, 0.25rem);
          --_cui-select-shadow: var(
            --cui-select-shadow,
            0 0.75rem 2rem color-mix(in srgb, CanvasText 18%, transparent)
          );
          --_cui-select-duration: var(--cui-select-duration, 120ms);
          box-sizing: border-box;
          display: grid;
          min-inline-size: 0;
          color: var(--_cui-select-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
        }
        :where(.cui-select[data-size="sm"]) {
          --_cui-select-control-padding: var(--cui-select-control-padding, 0.45rem 0.625rem);
          --_cui-select-option-padding: var(--cui-select-option-padding, 0.375rem 0.5rem);
          font-size: 0.875rem;
        }
        :where(.cui-select[data-size="lg"]) {
          --_cui-select-control-padding: var(--cui-select-control-padding, 0.75rem 0.875rem);
          --_cui-select-option-padding: var(--cui-select-option-padding, 0.625rem 0.75rem);
          font-size: 1.0625rem;
        }
        :where(.cui-select:not([data-citry-select-initialized]) .cui-select__control),
        :where(.cui-select:not([data-citry-select-initialized]) .cui-select__popup) {
          display: none;
        }
        :where(.cui-select:not([data-citry-select-initialized]) .cui-select__native) {
          box-sizing: border-box;
          inline-size: 100%;
          min-block-size: 2.5rem;
          padding: 0.5rem 0.625rem;
          border: 1px solid var(--_cui-select-border-color);
          border-radius: var(--_cui-select-radius);
          background: var(--_cui-select-background);
          color: var(--_cui-select-foreground);
          font: inherit;
        }
        :where(.cui-select[data-citry-select-initialized] .cui-select__native) {
          position: absolute;
          inline-size: 1px;
          block-size: 1px;
          margin: -1px;
          padding: 0;
          overflow: hidden;
          clip-path: inset(50%);
          white-space: nowrap;
          border: 0;
        }
        :where(.cui-select__control) {
          box-sizing: border-box;
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: 0.625rem;
          inline-size: 100%;
          min-inline-size: 0;
          margin: 0;
          padding: var(--_cui-select-control-padding);
          border: 1px solid transparent;
          border-radius: var(--_cui-select-radius);
          background: var(--_cui-select-background);
          color: var(--_cui-select-foreground);
          font: inherit;
          line-height: 1.35;
          text-align: start;
          cursor: pointer;
        }
        :where(.cui-select[data-variant="outline"] .cui-select__control) {
          border-color: var(--_cui-select-border-color);
        }
        :where(.cui-select[data-variant="filled"] .cui-select__control) {
          background: color-mix(in srgb, CanvasText 6%, Canvas);
        }
        :where(.cui-select[data-variant="plain"] .cui-select__control) {
          padding-inline: 0;
        }
        :where(.cui-select__control:focus-visible) {
          outline: 2px solid var(--_cui-select-focus-color);
          outline-offset: 2px;
        }
        :where(.cui-select[data-empty] .cui-select__control) {
          color: var(--_cui-select-placeholder-color);
        }
        :where(.cui-select[data-disabled] .cui-select__control) {
          color: var(--_cui-select-muted-color);
          cursor: not-allowed;
          opacity: 0.72;
        }
        :where(.cui-select[data-readonly]:not([data-disabled]) .cui-select__control) {
          cursor: default;
        }
        :where(.cui-select[data-invalid] .cui-select__control) {
          border-color: light-dark(#d92d20, #f97066);
        }
        :where(.cui-select [data-citry-ui-part="value"]) {
          min-inline-size: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        :where(.cui-select__indicator) {
          transition: transform var(--_cui-select-duration) ease-out;
        }
        :where(.cui-select[data-open] .cui-select__indicator) { transform: rotate(180deg); }
        :where(.cui-select__popup) {
          position: fixed;
          position-anchor: var(--_cui-select-anchor);
          box-sizing: border-box;
          inline-size: min(14rem, calc(100vw - 2rem));
          max-inline-size: calc(100vw - 2rem);
          max-block-size: min(var(--_cui-select-max-block-size), calc(100vh - 2rem));
          margin: 0;
          padding: 0.25rem;
          overflow: auto;
          border: 1px solid var(--_cui-select-border-color);
          border-radius: var(--_cui-select-radius);
          background: var(--_cui-select-background);
          color: var(--_cui-select-foreground);
          box-shadow: var(--_cui-select-shadow);
          font: inherit;
          overscroll-behavior: contain;
        }
        :where(.cui-select__popup:not(:popover-open)) { display: none; }
        :where(.cui-select[data-match-width] .cui-select__popup) {
          inline-size: min(anchor-size(width), calc(100vw - 2rem));
        }
        :where(.cui-select__popup[data-placement="bottom-start"]) {
          position-area: block-end span-inline-end;
          margin-block-start: var(--_cui-select-offset);
        }
        :where(.cui-select__popup[data-placement="bottom-end"]) {
          position-area: block-end span-inline-start;
          margin-block-start: var(--_cui-select-offset);
        }
        :where(.cui-select__popup[data-placement="top-start"]) {
          position-area: block-start span-inline-end;
          margin-block-end: var(--_cui-select-offset);
        }
        :where(.cui-select__popup[data-placement="top-end"]) {
          position-area: block-start span-inline-start;
          margin-block-end: var(--_cui-select-offset);
        }
        :where(.cui-select__listbox),
        :where(.cui-select__group) {
          display: grid;
          gap: 0.125rem;
          min-inline-size: 0;
        }
        :where(.cui-select__group-label) {
          padding: 0.5rem 0.625rem 0.25rem;
          color: var(--_cui-select-muted-color);
          font-size: 0.8125em;
          font-weight: 700;
          line-height: 1.3;
          overflow-wrap: anywhere;
        }
        :where(.cui-select__option) {
          box-sizing: border-box;
          display: grid;
          gap: 0.125rem;
          min-inline-size: 0;
          padding: var(--_cui-select-option-padding);
          border-radius: calc(var(--_cui-select-radius) - 0.125rem);
          line-height: 1.35;
          cursor: default;
        }
        :where(.cui-select__option[data-highlighted]:not([data-disabled])) {
          background: var(--_cui-select-hover-background);
          outline: 2px solid var(--_cui-select-focus-color);
          outline-offset: -2px;
        }
        :where(.cui-select__option[data-selected]) {
          background: var(--_cui-select-selected-background);
          color: var(--_cui-select-selected-foreground);
        }
        :where(.cui-select__option[data-disabled]) {
          color: var(--_cui-select-muted-color);
          cursor: not-allowed;
          opacity: 0.72;
        }
        :where(.cui-select__option [data-citry-ui-part="option-label"]),
        :where(.cui-select__option [data-citry-ui-part="option-description"]) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where(.cui-select__option [data-citry-ui-part="option-description"]) {
          color: var(--_cui-select-muted-color);
          font-size: 0.875em;
        }
        :where(.cui-select__option[data-selected] [data-citry-ui-part="option-description"]) {
          color: currentColor;
          opacity: 0.82;
        }
        @media (prefers-reduced-motion: reduce) {
          :where(.cui-select) { --_cui-select-duration: 0ms; }
        }
        @media (forced-colors: active) {
          :where(.cui-select__control), :where(.cui-select__popup) { border-color: CanvasText; }
          :where(.cui-select__option[data-selected]) {
            background: Highlight;
            color: HighlightText;
            forced-color-adjust: none;
          }
          :where(.cui-select__option[data-highlighted]) { outline-color: Highlight; }
        }
        @media print {
          :where(.cui-select__popup) { display: none !important; }
          :where(.cui-select__control) {
            border-color: CanvasText;
            background: transparent;
            color: CanvasText;
            box-shadow: none;
          }
        }
      }
    """


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
