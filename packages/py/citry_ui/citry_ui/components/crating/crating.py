"""Styled exact-decimal Rating component."""

# ruff: noqa: E501 - embedded component JavaScript and CSS retain readable source lines

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from string import Formatter
from typing import Any, ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, const_value
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs
from citry_ui.components._context import FIELD_CONTEXT_KEY, FIELD_CONTROL_MARKER, FORM_CONTEXT_KEY
from citry_ui.components._form_control_runtime import (
    FORM_CONTROL_RUNTIME_DEPENDENCY,
    FORM_CONTROL_STYLE_DEPENDENCY,
)
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

CRatingExact = int | Decimal | str
CRatingSize = Literal["sm", "md", "lg"]
CRatingVariant = Literal["solid", "subtle"]
CRatingChangeSource = Literal["pointer", "keyboard", "reset"]

_PLAIN_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_RUNTIME_PREFIXES = ("data-citry-", "data-crating", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "aria-readonly",
        "data-citry-rating-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-hovering",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "id",
        "role",
        "tabindex",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-label",
        "aria-describedby",
        "aria-errormessage",
        "aria-invalid",
        FIELD_CONTROL_MARKER,
        "checked",
        "data-citry-ui-part",
        "disabled",
        "form",
        "id",
        "name",
        "required",
        "type",
        "value",
    }
)


class CRatingValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    controlled: bool
    source: CRatingChangeSource
    sourceEvent: object | None


class CRatingHoverChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    sourceEvent: object | None


def _canonical_decimal(name: str, value: object, *, optional: bool = False) -> str | None:
    value = const_value(value)
    if value is None:
        if optional:
            return None
        raise TypeError(f"CRating {name} cannot be None.")
    if type(value) is int:
        raw = str(value)
    elif type(value) is Decimal:
        decimal = cast("Decimal", value)
        if not decimal.is_finite():
            raise ValueError(f"CRating {name} must be finite.")
        raw = format(decimal, "f")
    elif type(value) is str:
        raw = cast("str", value)
        if not _PLAIN_DECIMAL.fullmatch(raw):
            raise ValueError(f"CRating {name} must use canonical plain-decimal syntax, got {raw!r}.")
    else:
        raise TypeError(f"CRating {name} must be an int, Decimal, or canonical decimal string, got {value!r}.")
    negative = raw.startswith("-")
    unsigned = raw[1:] if negative else raw
    integer, dot, fraction = unsigned.partition(".")
    integer = integer.lstrip("0") or "0"
    fraction = fraction.rstrip("0") if dot else ""
    normalized = integer + (f".{fraction}" if fraction else "")
    if negative and normalized != "0":
        normalized = f"-{normalized}"
    if sum(character.isdigit() for character in normalized) > 128:
        raise ValueError(f"CRating {name} may contain at most 128 decimal digits.")
    return normalized


def _plain(name: str, value: object) -> str:
    value = const_value(value)
    if not isinstance(value, str):
        raise TypeError(f"CRating {name} must be a string, got {value!r}.")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in normalized or "\n" in normalized or not normalized.strip():
        raise ValueError(f"CRating {name} must be one nonempty line without U+0000.")
    return normalized


def _message_pattern(value: object) -> str:
    pattern = _plain("value_label", value)
    fields: list[str] = []
    for _literal, field_name, format_spec, conversion in Formatter().parse(pattern):
        if field_name is None:
            continue
        if field_name not in {"value", "max"} or format_spec or conversion:
            raise ValueError("CRating value_label may contain only plain {value} and {max} placeholders.")
        fields.append(field_name)
    if set(fields) != {"value", "max"}:
        raise ValueError("CRating value_label must contain both {value} and {max}.")
    return pattern


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _attrs(destination: str, value: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CRating {destination} must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"CRating {destination}")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CRating {destination} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CRating {destination} cannot contain runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CRating {destination} cannot use ownership directive {key!r}.")
        if _dynamic_target(key) in owned:
            raise ValueError(f"CRating {destination} cannot dynamically bind owned attribute {key!r}.")
    return copied


def _pop_case_insensitive(attrs: dict[str, object], name: str) -> object | None:
    found: object | None = None
    for authored_name in tuple(attrs):
        if authored_name.casefold() == name:
            found = attrs.pop(authored_name)
    return found


class CRating(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        value: CRatingExact | None = None
        name: str | None = None
        form: str | None = None
        id: str | None = None
        max: int = 5
        precision: CRatingExact = 1
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        allow_clear: bool = False
        label: str | None = None
        value_label: str = "{value} out of {max}"
        variant: CRatingVariant = "solid"
        size: CRatingSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_rating_snapshot", None)
        if cached is not None:
            return cast("dict[str, Any]", cached)
        name = const_value(kwargs.name)
        form_input = const_value(kwargs.form)
        supplied_id = const_value(kwargs.id)
        if name is not None:
            validate_non_empty_string("CRating", "name", name)
        validate_html_id("CRating", supplied_id)
        validate_html_id("CRating", form_input)
        for input_name in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CRating", input_name, getattr(kwargs, input_name))
        validate_boolean("CRating", "allow_clear", kwargs.allow_clear)
        validate_optional_string("CRating", "label", kwargs.label)
        validate_choice("CRating", "variant", kwargs.variant, ("solid", "subtle"))
        validate_choice("CRating", "size", kwargs.size, ("sm", "md", "lg"))
        maximum = const_value(kwargs.max)
        if type(maximum) is not int:
            raise TypeError(f"CRating max must be an integer, got {maximum!r}.")
        if not 1 <= maximum <= 20:
            raise ValueError("CRating max must be between 1 and 20.")
        precision = cast("str", _canonical_decimal("precision", kwargs.precision))
        precision_decimal = Decimal(precision)
        if precision_decimal <= 0 or precision_decimal > 1 or Decimal(1) % precision_decimal:
            raise ValueError("CRating precision must be positive, no greater than 1, and divide 1 exactly.")
        count_decimal = Decimal(maximum) / precision_decimal
        if count_decimal != count_decimal.to_integral_value() or count_decimal > 200:
            raise ValueError("CRating max and precision must produce at most 200 exact choices.")
        count = int(count_decimal)
        value = _canonical_decimal("value", kwargs.value, optional=True)
        if value == "0":
            value = None
        if value is not None:
            value_decimal = Decimal(value)
            if value_decimal < 0 or value_decimal > maximum or value_decimal % precision_decimal:
                raise ValueError("CRating value must be zero/unrated or a bounded precision-grid value.")

        catalog_value_label = uses_catalog_default(self, "value_label")
        value_label_pattern = _message_pattern(kwargs.value_label)
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None:
            supplied = [
                input_name
                for input_name in ("required", "disabled", "readonly", "invalid")
                if getattr(kwargs, input_name) is not None
            ]
            if supplied:
                raise ValueError(f"CRating inside CField cannot set Field-owned state: {', '.join(supplied)}.")
            field.register_control("CRating")
        field_control_id = str(field.control_id) if field is not None else None
        if field_control_id is not None and supplied_id is not None and supplied_id != field_control_id:
            raise ValueError(f"CRating id {supplied_id!r} conflicts with its CField control_id {field_control_id!r}.")
        public_id = supplied_id or field_control_id or f"cui-rating-{self.id}"
        root_id = f"{public_id}-root"
        root_attrs = _attrs("attrs", kwargs.attrs, _ROOT_OWNED)
        input_attrs = _attrs("input_attrs", kwargs.input_attrs, _INPUT_OWNED)
        authored_label = _pop_case_insensitive(root_attrs, "aria-label")
        authored_labelledby = _pop_case_insensitive(root_attrs, "aria-labelledby")
        authored_describedby = _pop_case_insensitive(root_attrs, "aria-describedby")
        authored_errormessage = _pop_case_insensitive(root_attrs, "aria-errormessage")
        label = const_value(kwargs.label)
        if label is not None:
            label = _plain("label", label)
        if field is not None and label is not None:
            raise ValueError("CRating inside CField cannot also set label; use the CField label slot.")
        if field is None and label is None and authored_label is None and authored_labelledby is None:
            raise ValueError("Standalone CRating requires label or attrs aria-label/aria-labelledby.")
        if authored_label is not None and not isinstance(authored_label, str):
            raise TypeError("CRating attrs aria-label must be a string.")
        if authored_labelledby is not None and not isinstance(authored_labelledby, str):
            raise TypeError("CRating attrs aria-labelledby must be a string.")
        form_owner = get_html_form_owner(
            {"form": form_input} if form_input is not None else {},
            component_name="CRating",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CRating inside CForm cannot target a different native form owner.")
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
        group_label = str(authored_label) if authored_label is not None else label
        group_labelledby = merge_idrefs(
            field.label_id if field is not None else None,
            cast("str | None", authored_labelledby),
        )

        choices: list[dict[str, object]] = []
        for index in range(1, count + 1):
            choice_decimal = precision_decimal * index
            choice_value = cast("str", _canonical_decimal("choice", choice_decimal))
            formatted_value = (
                self.i18n.format.number(choice_decimal, format="citry-ui-rating")
                if self.i18n.configured
                else choice_value
            )
            formatted_max = (
                self.i18n.format.number(maximum, format="citry-ui-rating") if self.i18n.configured else str(maximum)
            )
            choice_label = (
                self.i18n.tr("citry-ui-rating-value", value=formatted_value, max=formatted_max)
                if catalog_value_label
                else value_label_pattern.format(value=formatted_value, max=formatted_max)
            )
            choices.append(
                {
                    "id": public_id if index == 1 else f"{public_id}-{index}",
                    "value": choice_value,
                    "checked": choice_value == value,
                    "label": choice_label,
                    "position": {
                        "inset-inline-start": f"{(index - 1) / count * 100}%",
                        "inline-size": f"{100 / count}%",
                    },
                }
            )
        ratio = (Decimal(value) / Decimal(maximum) * 100) if value is not None else Decimal(0)
        readonly_value_id = f"{public_id}-readonly-value"
        readonly_value_label = next(
            (cast("str", choice["label"]) for choice in choices if choice["value"] == value), ""
        )
        snapshot: dict[str, Any] = {
            "public_id": public_id,
            "root_id": root_id,
            "transport_id": f"{public_id}-transport",
            "readonly_value_id": readonly_value_id,
            "name": name,
            "form": form_owner,
            "value": value,
            "maximum": maximum,
            "precision": precision,
            "choices": choices,
            "stars": list(range(maximum)),
            "ratio_style": {"--_cui-rating-ratio": f"{ratio}%"},
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "allow_clear": kwargs.allow_clear,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
            "group_label": group_label,
            "group_labelledby": group_labelledby,
            "described_by": described_by,
            "readonly_described_by": merge_idrefs(
                described_by, readonly_value_id if readonly and value is not None else None
            ),
            "error_message": error_message,
            "field_control": field is not None,
            "readonly_value_label": readonly_value_label,
        }
        self._cui_rating_data = {
            "id": public_id,
            "rootId": root_id,
            "transportId": f"{public_id}-transport",
            "readonlyValueId": readonly_value_id,
            "name": name,
            "form": form_owner,
            "value": value,
            "initialValue": value,
            "max": str(maximum),
            "precision": precision,
            "values": [choice["value"] for choice in choices],
            "catalogValueLabel": catalog_value_label,
            "valueLabel": value_label_pattern,
            "disabled": disabled,
            "readonly": readonly,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "required": required,
            "invalid": invalid,
            "allowClear": kwargs.allow_clear,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "groupLabel": group_label,
            "groupLabelledby": group_labelledby,
            "describedby": described_by,
            "errormessage": error_message,
            "fieldLabelId": field.label_id if field is not None else None,
        }
        self._cui_rating_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_rating_data

    template = """
      <div
        class="cui-rating"
        role="radiogroup"
        c-id="root_id"
        c-aria-label="group_label"
        c-aria-labelledby="group_labelledby"
        c-aria-describedby="readonly_described_by if readonly else described_by"
        c-aria-errormessage="error_message"
        c-aria-invalid="'true' if invalid else None"
        c-aria-disabled="'true' if disabled else None"
        c-aria-readonly="'true' if readonly else None"
        c-tabindex="0 if readonly and not disabled else None"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-required="required"
        c-data-invalid="invalid"
        c-data-variant="variant"
        c-data-size="size"
        c-style="ratio_style"
        c-bind="root_attrs"
        data-citry-ui-part="rating"
      >
        <span aria-hidden="true" data-citry-ui-part="visual">
          <span data-citry-ui-part="empty">
            <span c-for="star in stars" data-citry-ui-part="symbol">★</span>
          </span>
          <span data-citry-ui-part="fill">
            <span data-citry-ui-part="fill-symbols">
              <span c-for="star in stars" data-citry-ui-part="symbol">★</span>
            </span>
          </span>
        </span>
        <span c-aria-hidden="'true' if readonly else None" data-citry-ui-part="choices">
          <label c-for="choice in choices" c-style="choice['position']" c-data-value="choice['value']" data-citry-ui-part="choice">
            <input
              c-id="choice['id']"
              c-name="name"
              c-form="form"
              type="radio"
              c-value="choice['value']"
              c-checked="choice['checked']"
              c-required="required"
              c-disabled="disabled or readonly"
              c-aria-describedby="described_by"
              c-aria-errormessage="error_message"
              c-aria-invalid="'true' if invalid else None"
              c-data-citry-field-control="field_control and choice['id'] == public_id"
              c-bind="input_attrs"
              data-citry-ui-part="input"
            />
            <span class="cui-rating__visually-hidden" data-citry-ui-part="choice-label">{{ choice['label'] }}</span>
          </label>
        </span>
        <span c-if="readonly and value is not None" class="cui-rating__visually-hidden" c-id="readonly_value_id" data-citry-ui-part="readonly-value">{{ readonly_value_label }}</span>
        <input
          c-id="transport_id"
          c-name="name"
          c-form="form"
          c-value="value"
          type="hidden"
          c-disabled="disabled or not readonly or name is None or value is None"
          data-citry-ui-part="readonly-transport"
        />
      </div>
    """

    js = r"""
      $component({
        props: { value: {}, required: {}, disabled: {}, readonly: {}, invalid: {}, allowClear: {}, variant: {}, size: {}, onValueChange: {}, onHoverChange: {} },
        init: ({ els, data, props, effect, inject, i18n }) => {
          const root = els[0];
          const choices = root.querySelector(':scope > [data-citry-ui-part="choices"]');
          const inputs = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"] > [data-citry-ui-part="input"]') ?? []);
          const labels = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"]') ?? []);
          const choiceLabels = Array.from(choices?.querySelectorAll(':scope > [data-citry-ui-part="choice"] > [data-citry-ui-part="choice-label"]') ?? []);
          const transport = root.querySelector(':scope > [data-citry-ui-part="readonly-transport"]');
          const readonlyValue = root.querySelector(':scope > [data-citry-ui-part="readonly-value"]');
          if (!(choices instanceof HTMLElement) || !(transport instanceof HTMLInputElement) || inputs.length !== data.values.length || inputs.some(input => !(input instanceof HTMLInputElement)) || labels.length !== inputs.length || choiceLabels.length !== inputs.length) throw new Error('[citry-ui] CRating settled anatomy is invalid.');
          const field = inject(Symbol.for('citry-ui:field'), null);
          const form = inject(Symbol.for('citry-ui:form'), null);
          const runtime = globalThis[Symbol.for('citry-ui:form-control-runtime')];
          if (runtime?.generation !== 1) throw new Error('[citry-ui] CRating form-control runtime is unavailable.');
          const resolver = runtime.resolver(root, props, 'CRating');
          const listeners = runtime.listeners();
          const mutations = runtime.mutations(root);
          const owned = mutations.owned;
          let current = data.value;
          let committed = current;
          let initialValue = data.initialValue;
          let controlled = false;
          let hovered = null;
          let configuration = null;
          let interactionSource = 'pointer';
          let bindings = [];

          const canonical = raw => {
            if (raw === null || raw === '0') return null;
            if (typeof raw !== 'string' || !data.values.includes(raw)) return undefined;
            return raw;
          };
          const resolveConfiguration = () => ({
            required: field ? field.required : resolver.boolean('required', data.required),
            disabled: field ? field.disabled : Boolean(form?.disabled) || resolver.boolean('disabled', data.disabled) || runtime.fieldsetDisabled(inputs[0]),
            readonly: field ? field.readonly : resolver.boolean('readonly', data.inheritsReadonly && form ? form.readonly : data.readonly),
            invalid: field ? field.invalid : resolver.boolean('invalid', data.invalid),
            allowClear: resolver.boolean('allowClear', data.allowClear),
            variant: resolver.choice('variant', data.variant, ['solid', 'subtle']),
            size: resolver.choice('size', data.size, ['sm', 'md', 'lg']),
          });
          const ratio = value => `${value === null ? 0 : Number(value) / Number(data.max) * 100}%`;
          const formatLabel = value => {
            const formattedValue = i18n ? i18n.format.number(value, { format: 'citry-ui-rating' }) : value;
            const formattedMax = i18n ? i18n.format.number(data.max, { format: 'citry-ui-rating' }) : data.max;
            return data.valueLabel.replaceAll('{value}', formattedValue).replaceAll('{max}', formattedMax);
          };
          const syncLabels = () => {
            bindings.forEach(binding => binding.dispose());
            bindings = [];
            inputs.forEach((input, index) => {
              if (i18n && data.catalogValueLabel) bindings.push(i18n.bind({
                message: 'citry-ui-rating-value',
                values: () => ({ value: i18n.format.number(input.value, { format: 'citry-ui-rating' }), max: i18n.format.number(data.max, { format: 'citry-ui-rating' }) }),
                onChange: text => {
                  choiceLabels[index].textContent = text;
                  if (readonlyValue && input.value === current) readonlyValue.textContent = text;
                },
              }));
              else choiceLabels[index].textContent = formatLabel(input.value);
            });
          };
          const syncRelationships = () => runtime.relationships(inputs, field, { describedby: data.describedby, errormessage: data.errormessage }, configuration.invalid);
          const apply = () => owned(() => {
            root.style.setProperty('--_cui-rating-ratio', ratio(hovered ?? current));
            root.style.setProperty('--_cui-rating-committed-ratio', ratio(current));
            root.toggleAttribute('data-hovering', hovered !== null);
            root.toggleAttribute('data-disabled', configuration.disabled);
            root.toggleAttribute('data-readonly', configuration.readonly);
            root.toggleAttribute('data-required', configuration.required);
            root.toggleAttribute('data-invalid', configuration.invalid);
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.setAttribute('aria-disabled', configuration.disabled ? 'true' : 'false');
            root.setAttribute('aria-readonly', configuration.readonly ? 'true' : 'false');
            root.setAttribute('aria-invalid', configuration.invalid ? 'true' : 'false');
            if (configuration.readonly && !configuration.disabled) root.tabIndex = 0; else root.removeAttribute('tabindex');
            choices.setAttribute('aria-hidden', configuration.readonly ? 'true' : 'false');
            inputs.forEach((input, index) => {
              input.checked = input.value === current;
              input.defaultChecked = input.value === initialValue;
              input.name = configuration.disabled || configuration.readonly ? '' : (data.name ?? '');
              input.disabled = configuration.disabled || configuration.readonly;
              input.required = configuration.required && !configuration.disabled && !configuration.readonly;
              labels[index].toggleAttribute('data-checked', input.value === current);
              labels[index].toggleAttribute('data-highlighted', hovered !== null && Number(input.value) <= Number(hovered));
            });
            transport.value = current ?? '';
            transport.name = configuration.disabled || !configuration.readonly || current === null ? '' : (data.name ?? '');
            transport.disabled = configuration.disabled || !configuration.readonly || current === null || !data.name;
            if (readonlyValue) {
              const index = inputs.findIndex(input => input.value === current);
              readonlyValue.textContent = current === null ? '' : (choiceLabels[index]?.textContent ?? formatLabel(current));
            }
            syncRelationships();
          });
          const detail = (value, previousValue, source, event) => ({ value, previousValue, controlled, source, sourceEvent: event });
          const notifyHover = (next, event) => {
            if (next === hovered) return;
            const previousValue = hovered;
            hovered = next;
            resolver.callback('onHoverChange')?.(next, { value: next, previousValue, sourceEvent: event });
            apply();
          };
          const request = (next, source, event, nativeAlreadyChanged = false) => {
            if (next === current) return false;
            const previousValue = current;
            if (!controlled) { current = next; committed = next; }
            resolver.callback('onValueChange')?.(next, detail(next, previousValue, source, event));
            apply();
            if (!controlled && !nativeAlreadyChanged) {
              const eventInput = inputs.find(input => input.value === next) ?? inputs.find(input => input.value === previousValue) ?? inputs[0];
              eventInput.dispatchEvent(new Event('input', { bubbles: true }));
              eventInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return true;
          };
          inputs.forEach(input => {
            listeners.add(input, 'pointerdown', () => { interactionSource = 'pointer'; });
            listeners.add(input, 'keydown', event => {
              interactionSource = 'keyboard';
              if (configuration.disabled || configuration.readonly) return;
              if (event.key === 'Home' || event.key === 'End') {
                event.preventDefault();
                const target = event.key === 'Home' ? inputs[0] : inputs.at(-1);
                target.focus({ preventScroll: true });
                request(target.value, 'keyboard', event);
              }
            });
            listeners.add(input, 'click', event => {
              if (configuration.disabled || configuration.readonly) { event.preventDefault(); apply(); return; }
              if (configuration.allowClear && input.value === current) {
                event.preventDefault();
                request(null, interactionSource, event);
                setTimeout(() => { if (root.isConnected) apply(); }, 0);
              }
            });
            listeners.add(input, 'change', event => {
              if (!input.checked || configuration.disabled || configuration.readonly) return;
              request(input.value, interactionSource, event, true);
            });
          });
          labels.forEach(label => {
            listeners.add(label, 'pointerenter', event => { if (!configuration.disabled && !configuration.readonly) notifyHover(label.dataset.value ?? null, event); });
          });
          listeners.add(choices, 'pointerleave', event => notifyHover(null, event));
          const reset = runtime.registerReset(root, inputs[0], {
            reset: event => {
              hovered = null;
              if (controlled) resolver.callback('onValueChange')?.(initialValue, detail(initialValue, current, 'reset', event));
              else { current = initialValue; committed = initialValue; apply(); }
            },
            invalidate: () => {},
          });
          const stopFieldset = runtime.watchFieldset(root, inputs[0], () => { configuration = resolveConfiguration(); apply(); });
          effect(() => {
            configuration = resolveConfiguration();
            const requested = props.value;
            if (requested === undefined) {
              if (controlled) { controlled = false; current = committed; }
              resolver.clear('value');
            } else {
              const normalized = canonical(requested);
              if (normalized === undefined) resolver.report('value', requested);
              else { resolver.clear('value'); controlled = true; current = normalized; }
            }
            if (configuration.disabled || configuration.readonly) hovered = null;
            apply();
          });
          if (data.fieldLabelId) {
            const fieldLabel = root.ownerDocument.getElementById(data.fieldLabelId);
            if (fieldLabel) listeners.add(fieldLabel, 'click', event => queueMicrotask(() => {
              if (!event.defaultPrevented && root.isConnected && !configuration.disabled) (configuration.readonly ? root : inputs.find(input => input.checked) ?? inputs[0]).focus({ preventScroll: true });
            }));
          }
          syncLabels();
          mutations.start(() => apply());
          root.setAttribute('data-citry-rating-initialized', '');
          apply();
          return () => {
            bindings.forEach(binding => binding.dispose());
            listeners.stop(); mutations.stop(); stopFieldset(); reset();
            root.removeAttribute('data-citry-rating-initialized');
          };
        },
      });
    """

    css_file = "runtime.min.css"

    messages = """
      # @param {str} $value - Locale-formatted exact rating choice.
      # @param {str} $max - Locale-formatted maximum rating.
      citry-ui-rating-value = { $value } out of { $max }
    """
