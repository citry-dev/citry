"""Progressively enhanced free-form TagsInput component."""

# ruff: noqa: E501

from __future__ import annotations

import json
import string
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, ClassVar, Literal, TypedDict, cast, overload

from citry import LibraryComponent, const_value, is_const
from citry_ui.components._aria import merge_idrefs
from citry_ui.components._attrs import CClassValue, CStyleValue, get_html_form_owner, merge_root_attrs, pop_html_attr
from citry_ui.components._context import FIELD_CONTEXT_KEY, FORM_CONTEXT_KEY
from citry_ui.components._form_control_runtime import FORM_CONTROL_RUNTIME_DEPENDENCY, FORM_CONTROL_STYLE_DEPENDENCY
from citry_ui.components._validation import validate_optional_boolean

CTagsInputVariant = Literal["outline", "filled", "plain"]
CTagsInputSize = Literal["sm", "md", "lg"]
CTagsInputChangeSource = Literal[
    "input",
    "enter",
    "delimiter",
    "paste",
    "backspace",
    "delete",
    "remove",
    "reset",
]
CTagsInputInvalidReason = Literal["empty", "duplicate", "maximum", "delimiter", "invalid-value"]


@dataclass(frozen=True, slots=True)
class CTagsInputMessages:
    remove_label: str | None = None
    added_message: str | None = None
    removed_message: str | None = None
    selected_message: str | None = None
    duplicate_message: str | None = None
    maximum_message: str | None = None
    empty_message: str | None = None
    invalid_message: str | None = None
    uncommitted_message: str | None = None


class CTagsInputValueChangeDetail(TypedDict):
    source: CTagsInputChangeSource
    added: list[str]
    removed: list[str]
    candidates: list[str]
    previousValue: list[str]
    nextInputValue: str
    controlled: bool


class CTagsInputInputValueChangeDetail(TypedDict):
    source: CTagsInputChangeSource
    previousValue: str
    nextValue: str
    controlled: bool
    composing: bool


class CTagsInputInvalidDetail(TypedDict):
    source: CTagsInputChangeSource
    candidate: str | None
    candidates: list[str]
    value: list[str]
    inputValue: str
    maxTags: int | None
    controlled: bool


@dataclass(frozen=True, slots=True)
class _ResolvedTag:
    value: str
    remove_label: str
    values_expression: str


_VARIANTS = ("outline", "filled", "plain")
_SIZES = ("sm", "md", "lg")
_ASCII_WHITESPACE = "\t\n\f\r "
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")


def _fingerprint(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "$c-props",
        "c-bind",
        "c-props",
        "x-bind",
        "x-data",
        "x-effect",
        "x-for",
        "x-html",
        "x-id",
        "x-if",
        "x-ignore",
        "x-init",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_ROOT_OWNED = frozenset(
    {
        "aria-activedescendant",
        "aria-atomic",
        "aria-controls",
        "aria-disabled",
        "aria-errormessage",
        "aria-expanded",
        "aria-haspopup",
        "aria-hidden",
        "aria-invalid",
        "aria-label",
        "aria-labelledby",
        "aria-live",
        "aria-readonly",
        "aria-required",
        "contenteditable",
        "data-at-max",
        "data-citry-tags-input-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-empty",
        "data-focused",
        "data-invalid",
        "data-readonly",
        "data-required",
        "data-size",
        "data-variant",
        "disabled",
        "form",
        "hidden",
        "id",
        "inert",
        "is",
        "multiple",
        "name",
        "part",
        "popover",
        "readonly",
        "required",
        "role",
        "tabindex",
        "type",
        "value",
    }
)
_INPUT_OWNED = frozenset(
    {
        "aria-activedescendant",
        "aria-controls",
        "aria-disabled",
        "aria-errormessage",
        "aria-invalid",
        "aria-labelledby",
        "aria-readonly",
        "aria-required",
        "autocomplete",
        "data-citry-field-control",
        "data-citry-ui-part",
        "defaultvalue",
        "disabled",
        "form",
        "hidden",
        "id",
        "inert",
        "inputmode",
        "is",
        "list",
        "maxlength",
        "minlength",
        "multiple",
        "name",
        "part",
        "pattern",
        "placeholder",
        "popover",
        "readonly",
        "required",
        "role",
        "tabindex",
        "type",
        "value",
    }
)


@overload
def _plain(name: str, value: object, *, optional: Literal[False] = False) -> str: ...


@overload
def _plain(name: str, value: object, *, optional: Literal[True]) -> str | None: ...


@overload
def _plain(name: str, value: object, *, optional: bool) -> str | None: ...


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    value = const_value(value)
    if value is None and optional:
        return None
    if not isinstance(value, str):
        expected = "a string or None" if optional else "a string"
        raise TypeError(f"CTagsInput {name} must be {expected}, got {value!r}.")
    plain = "".join(value)
    if type(plain) is not str:
        raise TypeError(f"CTagsInput could not convert {name} to a plain string.")
    return plain


def _id(name: str, value: object, *, optional: bool = True) -> str | None:
    plain = _plain(name, value, optional=optional)
    if plain is not None and (not plain or any(character in _ASCII_WHITESPACE for character in plain)):
        raise ValueError(f"CTagsInput {name} must be non-empty and cannot contain ASCII whitespace.")
    return plain


def _canonical_value(value: object, delimiters: tuple[str, ...], *, name: str = "value") -> str:
    plain = _plain(name, value)
    normalized = plain.replace("\r\n", "\n").replace("\r", "\n")
    canonical = normalized.strip(_ASCII_WHITESPACE)
    if "\0" in normalized or "\n" in normalized or canonical != plain or not canonical:
        raise ValueError(f"CTagsInput {name} items must be nonempty canonical single-line strings, got {plain!r}.")
    if any(delimiter in plain for delimiter in delimiters):
        raise ValueError(f"CTagsInput {name} item {plain!r} cannot contain a configured delimiter.")
    return plain


def _values(value: object, delimiters: tuple[str, ...]) -> tuple[str, ...]:
    value = const_value(value)
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(value, Sequence):
        raise TypeError(f"CTagsInput value must be a sequence of strings, got {value!r}.")
    resolved = tuple(_canonical_value(item, delimiters) for item in value)
    if len(set(resolved)) != len(resolved):
        raise ValueError("CTagsInput value items must be unique under exact code-point equality.")
    return resolved


def _delimiters(value: object) -> tuple[str, ...]:
    value = const_value(value)
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(value, Sequence):
        raise TypeError(f"CTagsInput delimiters must be a sequence of strings, got {value!r}.")
    resolved: list[str] = []
    for item in value:
        delimiter = _plain("delimiters", item)
        valid_scalar = len(delimiter) == 1 and not 0xD800 <= ord(delimiter) <= 0xDFFF
        if (
            not valid_scalar
            or delimiter.isspace()
            or unicodedata.category(delimiter).startswith("C")
            or delimiter in "\0\r\n"
        ):
            raise ValueError(
                f"CTagsInput delimiters require non-whitespace, non-control Unicode scalars, got {delimiter!r}."
            )
        resolved.append(delimiter)
    if not resolved:
        raise ValueError("CTagsInput delimiters must contain at least one delimiter.")
    if len(set(resolved)) != len(resolved):
        raise ValueError("CTagsInput delimiters must be unique.")
    return tuple(resolved)


def _positive_integer(name: str, value: object) -> int | None:
    raw = const_value(value)
    if raw is None:
        return None
    if is_const(value) and isinstance(raw, str) and raw.isascii() and raw.isdecimal():
        value = int(raw)
    else:
        value = raw
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"CTagsInput {name} must be a positive integer or None, got {value!r}.")
    if value <= 0:
        raise ValueError(f"CTagsInput {name} must be a positive integer, got {value!r}.")
    return value


def _choice(name: str, value: object, choices: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in choices:
        expected = ", ".join(repr(item) for item in choices)
        raise ValueError(f"CTagsInput {name} must be one of {expected}, got {plain!r}.")
    return plain


def _validate_messages(messages: object) -> CTagsInputMessages:
    if messages is None:
        messages = CTagsInputMessages()
    if not isinstance(messages, CTagsInputMessages):
        raise TypeError(f"CTagsInput messages must be CTagsInputMessages or None, got {messages!r}.")
    allowed = {
        "remove_label": "value",
        "added_message": "value",
        "removed_message": "value",
        "selected_message": "value",
        "duplicate_message": "value",
        "maximum_message": "max",
        "empty_message": None,
        "invalid_message": None,
        "uncommitted_message": None,
    }
    formatter = string.Formatter()
    for name, required in allowed.items():
        template = _plain(f"messages.{name}", getattr(messages, name))
        if not template:
            raise ValueError(f"CTagsInput messages.{name} must be nonempty.")
        fields: list[str] = []
        try:
            parsed = tuple(formatter.parse(template))
        except ValueError as exc:
            raise ValueError(f"CTagsInput messages.{name} is not a valid message template.") from exc
        for _, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            if field_name not in ({required} if required else set()) or format_spec or conversion:
                raise ValueError(f"CTagsInput messages.{name} contains an unsupported placeholder.")
            fields.append(field_name)
        if required is not None and required not in fields:
            raise ValueError(f"CTagsInput messages.{name} must contain {{{required}}}.")
    return messages


def _dynamic_target(key: str) -> str | None:
    normalized = key.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _destination_attrs(
    destination: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"CTagsInput {destination} must be a mapping or None, got {attrs!r}.")
    copied: dict[str, object] = {}
    for key, value in (attrs or {}).items():
        if not isinstance(key, str):
            raise TypeError(f"CTagsInput {destination} requires string keys, got {key!r}.")
        normalized = key.casefold()
        target = _dynamic_target(key)
        if (
            normalized in owned
            or normalized in _OWNERSHIP_DIRECTIVES
            or target in owned
            or normalized.startswith(_RUNTIME_PREFIXES)
        ):
            raise ValueError(f"CTagsInput {destination} cannot override owned attribute {key!r}.")
        copied[key] = value
    return copied


class CTagsInput(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = (FORM_CONTROL_RUNTIME_DEPENDENCY,)
        css: ClassVar = (FORM_CONTROL_STYLE_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        name: str | None = None
        form: str | None = None
        id: str | None = None
        value: Sequence[str] = ()
        input_value: str = ""
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool | None = None
        invalid: bool | None = None
        placeholder: str | None = None
        delimiters: Sequence[str] = (",",)
        max_tags: int | None = None
        autocomplete: str | None = None
        inputmode: str | None = None
        variant: CTagsInputVariant = "outline"
        size: CTagsInputSize = "md"
        messages: CTagsInputMessages | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        input_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def _localized_messages(self, value: CTagsInputMessages | None) -> tuple[CTagsInputMessages, dict[str, bool]]:
        if value is not None and not isinstance(value, CTagsInputMessages):
            raise TypeError(f"CTagsInput messages must be CTagsInputMessages or None, got {value!r}.")
        overrides = value or CTagsInputMessages()
        names = (
            "remove_label",
            "added_message",
            "removed_message",
            "selected_message",
            "duplicate_message",
            "maximum_message",
            "empty_message",
            "invalid_message",
            "uncommitted_message",
        )
        catalog = {name: getattr(overrides, name) is None for name in names}
        resolved = {
            "remove_label": overrides.remove_label
            if overrides.remove_label is not None
            else self.i18n.tr("citry-ui-tags-input-remove", value="{value}"),
            "added_message": overrides.added_message
            if overrides.added_message is not None
            else self.i18n.tr("citry-ui-tags-input-added", value="{value}"),
            "removed_message": overrides.removed_message
            if overrides.removed_message is not None
            else self.i18n.tr("citry-ui-tags-input-removed", value="{value}"),
            "selected_message": overrides.selected_message
            if overrides.selected_message is not None
            else self.i18n.tr("citry-ui-tags-input-selected", value="{value}"),
            "duplicate_message": overrides.duplicate_message
            if overrides.duplicate_message is not None
            else self.i18n.tr("citry-ui-tags-input-duplicate", value="{value}"),
            "maximum_message": overrides.maximum_message
            if overrides.maximum_message is not None
            else self.i18n.tr("citry-ui-tags-input-maximum", max="{max}"),
            "empty_message": overrides.empty_message
            if overrides.empty_message is not None
            else self.i18n.tr("citry-ui-tags-input-required"),
            "invalid_message": overrides.invalid_message
            if overrides.invalid_message is not None
            else self.i18n.tr("citry-ui-tags-input-invalid"),
            "uncommitted_message": overrides.uncommitted_message
            if overrides.uncommitted_message is not None
            else self.i18n.tr("citry-ui-tags-input-unfinished"),
        }
        messages = CTagsInputMessages(**resolved)
        return _validate_messages(messages), catalog

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_tags_input_snapshot", None)
        if cached is not None:
            return cached
        name = _plain("name", kwargs.name, optional=True)
        if name == "":
            raise ValueError("CTagsInput name must be nonempty when supplied.")
        supplied_id = _id("id", kwargs.id)
        form_id = _id("form", kwargs.form)
        delimiters = _delimiters(kwargs.delimiters)
        values = _values(kwargs.value, delimiters)
        draft = _plain("input_value", kwargs.input_value)
        if any(character in draft for character in "\0\r\n"):
            raise ValueError("CTagsInput input_value cannot contain NUL, CR, or LF.")
        max_tags = _positive_integer("max_tags", kwargs.max_tags)
        if max_tags is not None and len(values) > max_tags:
            raise ValueError("CTagsInput initial value cannot exceed max_tags.")
        for state in ("required", "disabled", "readonly", "invalid"):
            validate_optional_boolean("CTagsInput", state, getattr(kwargs, state))
        placeholder = _plain("placeholder", kwargs.placeholder, optional=True)
        autocomplete = _plain("autocomplete", kwargs.autocomplete, optional=True)
        inputmode = _plain("inputmode", kwargs.inputmode, optional=True)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        messages, catalog_messages = self._localized_messages(kwargs.messages)
        root_attrs = _destination_attrs("attrs", kwargs.attrs, _ROOT_OWNED)
        input_attrs = _destination_attrs("input_attrs", kwargs.input_attrs, _INPUT_OWNED)
        consumer_label = pop_html_attr(input_attrs, "aria-label", component_name="CTagsInput input_attrs")
        consumer_description = pop_html_attr(
            input_attrs,
            "aria-describedby",
            component_name="CTagsInput input_attrs",
        )
        field = self.inject(FIELD_CONTEXT_KEY, None)
        form = self.inject(FORM_CONTEXT_KEY, None)
        if field is not None:
            conflicts = [
                state
                for state in ("required", "disabled", "readonly", "invalid")
                if getattr(kwargs, state) is not None
            ]
            if conflicts:
                raise ValueError(f"CTagsInput inside CField cannot set Field-owned state: {', '.join(conflicts)}.")
            if supplied_id is not None and supplied_id != str(field.control_id):
                raise ValueError(
                    f"CTagsInput id {supplied_id!r} conflicts with its CField control_id {field.control_id!r}."
                )
            if consumer_label is not None or consumer_description is not None:
                raise ValueError("CTagsInput inside CField cannot override Field-owned ARIA naming or description.")
            field.register_control("CTagsInput")
        else:
            if not isinstance(consumer_label, str):
                raise ValueError("Standalone CTagsInput requires a static aria-label in input_attrs.")
            plain_label = "".join(consumer_label)
            if any(character in plain_label for character in "\0\r\n") or not any(
                not character.isspace() for character in plain_label
            ):
                raise ValueError("Standalone CTagsInput aria-label must contain non-whitespace accessible text.")
            consumer_label = plain_label
        form_owner = get_html_form_owner(
            {"form": form_id} if form_id is not None else {},
            component_name="CTagsInput",
            default=form.form_id if form is not None else None,
        )
        if form is not None and form_owner != form.form_id:
            raise ValueError("CTagsInput inside CForm cannot target a different native form owner.")
        if field is not None:
            required = bool(field.required)
            disabled = bool(field.disabled)
            readonly = bool(field.readonly)
            invalid = bool(field.invalid)
        else:
            required = bool(kwargs.required)
            disabled = bool(form.disabled) if form is not None else False
            disabled = disabled or bool(kwargs.disabled)
            readonly = (
                bool(kwargs.readonly)
                if kwargs.readonly is not None
                else bool(form.readonly)
                if form is not None
                else False
            )
            invalid = bool(kwargs.invalid)
        public_id = supplied_id or (str(field.control_id) if field is not None else f"cui-tags-input-{self.id}")
        editor_id = f"{public_id}-input"
        native_id = f"{public_id}-native"
        described_by = merge_idrefs(
            field.description_id if field is not None and field.has_description else None,
            field.error_id if field is not None and field.has_error and invalid else None,
            consumer_description,
        )
        error_message = field.error_id if field is not None and field.has_error and invalid else None
        label_id = field.label_id if field is not None else None
        options = values
        tags = tuple(
            _ResolvedTag(
                value=value,
                remove_label=self.i18n.tr("citry-ui-tags-input-remove", value=value)
                if catalog_messages["remove_label"]
                else cast("str", messages.remove_label).format(value=value),
                values_expression="{ value: " + json.dumps(value, ensure_ascii=False) + " }",
            )
            for value in values
        )
        messages_data = asdict(messages)
        structure_fingerprint = _fingerprint(
            {
                "ids": [public_id, editor_id, native_id],
                "name": name,
                "form": form_owner,
                "delimiters": delimiters,
                "messages": messages_data,
                "variant": variant,
                "size": size,
                "maxTags": max_tags,
                "fieldOwned": field is not None,
            }
        )
        value_fingerprint = _fingerprint(values)
        draft_fingerprint = _fingerprint(draft)
        data = {
            "publicId": public_id,
            "editorId": editor_id,
            "nativeId": native_id,
            "name": name,
            "form": form_owner,
            "value": list(values),
            "inputValue": draft,
            "required": required,
            "disabled": disabled,
            "readonly": readonly,
            "invalid": invalid,
            "inheritsReadonly": field is None and kwargs.readonly is None,
            "placeholder": placeholder,
            "delimiters": list(delimiters),
            "maxTags": max_tags,
            "autocomplete": autocomplete,
            "inputmode": inputmode,
            "variant": variant,
            "size": size,
            "messages": messages_data,
            "fieldOwned": field is not None,
            "ariaLabel": consumer_label,
            "ariaLabelledby": label_id,
            "ariaDescribedby": described_by,
            "ariaErrormessage": error_message,
            "structureFingerprint": structure_fingerprint,
            "valueFingerprint": value_fingerprint,
            "draftFingerprint": draft_fingerprint,
            "serverFingerprint": _fingerprint([structure_fingerprint, value_fingerprint, draft_fingerprint]),
        }
        snapshot = {
            **data,
            "native_name": None if readonly else name,
            "native_disabled": disabled or readonly,
            "aria_required": "true" if required else None,
            "aria_disabled": "true" if disabled else None,
            "aria_readonly": "true" if readonly else None,
            "aria_invalid": "true" if invalid else None,
            "field_control": "" if field is not None else None,
            "empty": not values,
            "at_max": max_tags is not None and len(values) >= max_tags,
            "options": options,
            "tags": tags,
            "catalog_remove_label": catalog_messages["remove_label"],
            "readonly_values": values if readonly and not disabled and name else (),
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "input_attrs": input_attrs,
        }
        self._cui_tags_input_snapshot = snapshot
        self._cui_tags_input_data = {
            "p": public_id,
            "e": editor_id,
            "n": native_id,
            "N": name,
            "f": form_owner,
            "v": list(values),
            "i": draft,
            "q": required,
            "d": disabled,
            "r": readonly,
            "x": invalid,
            "h": field is None and kwargs.readonly is None,
            "P": placeholder,
            "l": list(delimiters),
            "m": max_tags,
            "a": autocomplete,
            "o": inputmode,
            "t": variant,
            "s": size,
            "g": {
                "r": messages.remove_label,
                "a": messages.added_message,
                "d": messages.removed_message,
                "s": messages.selected_message,
                "e": messages.empty_message,
                "u": messages.duplicate_message,
                "m": messages.maximum_message,
                "i": messages.invalid_message,
                "c": messages.uncommitted_message,
            },
            "G": {
                "r": catalog_messages["remove_label"],
                "a": catalog_messages["added_message"],
                "d": catalog_messages["removed_message"],
                "s": catalog_messages["selected_message"],
                "u": catalog_messages["duplicate_message"],
                "m": catalog_messages["maximum_message"],
                "e": catalog_messages["empty_message"],
                "i": catalog_messages["invalid_message"],
                "c": catalog_messages["uncommitted_message"],
            },
            "K": {tag.value: tag.remove_label for tag in tags},
            "L": consumer_label,
            "B": label_id,
            "C": described_by,
            "R": error_message,
            "S": structure_fingerprint,
            "V": value_fingerprint,
            "D": draft_fingerprint,
            "Z": data["serverFingerprint"],
        }
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        self._snapshot(kwargs)
        return self._cui_tags_input_data

    template = """
      <div
        class="cui-tags-input"
        c-data-empty="empty"
        c-data-required="required"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-invalid="invalid"
        c-data-at-max="at_max"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="root_attrs"
        data-citry-ui-part="tags-input"
      >
        <select
          class="cui-tags-input__native"
          c-id="publicId"
          c-name="native_name"
          c-form="form"
          c-required="required and not readonly"
          c-disabled="native_disabled"
          c-aria-label="ariaLabel"
          c-aria-labelledby="ariaLabelledby"
          c-aria-describedby="ariaDescribedby"
          c-aria-errormessage="ariaErrormessage"
          c-aria-invalid="aria_invalid"
          multiple
          data-citry-tags-input-native
        >
          <option c-for="option in options" c-value="option" selected>{{ option }}</option>
        </select>
        <div
          class="cui-tags-input__control"
          hidden
          data-citry-ui-part="control"
        >
          <span class="cui-tags-input__tag-list" data-citry-ui-part="tag-list">
            <span
              c-for="tag in tags"
              class="cui-tags-input__tag"
              c-data-value="tag.value"
              data-citry-ui-part="tag"
            >
              <span data-citry-ui-part="tag-label">{{ tag.value }}</span>
              <button
                c-aria-label="tr('citry-ui-tags-input-remove', value=tag.value) if catalog_remove_label else tag.remove_label"
                c-$c-tr:citry-ui-tags-input-remove[aria-label]="tag.values_expression if catalog_remove_label else None"
                c-data-value="tag.value"
                c-disabled="disabled or readonly"
                type="button"
                tabindex="-1"
                data-citry-ui-part="remove"
              >&#215;</button>
            </span>
          </span>
          <input
            class="cui-tags-input__input"
            c-id="editorId"
            type="text"
            c-value="inputValue"
            c-disabled="disabled"
            c-readonly="readonly"
            c-placeholder="placeholder"
            c-autocomplete="autocomplete"
            c-inputmode="inputmode"
            c-aria-label="ariaLabel"
            c-aria-labelledby="ariaLabelledby"
            c-aria-describedby="ariaDescribedby"
            c-aria-errormessage="ariaErrormessage"
            c-aria-required="aria_required"
            c-aria-disabled="aria_disabled"
            c-aria-readonly="aria_readonly"
            c-aria-invalid="aria_invalid"
            c-data-citry-field-control="field_control"
            c-bind="input_attrs"
            data-citry-ui-part="input"
          />
        </div>
        <span hidden data-citry-tags-input-readonly-values>
          <input
            c-for="readonly_value in readonly_values"
            c-name="name"
            c-form="form"
            c-value="readonly_value"
            type="hidden"
          />
        </span>
        <span
          class="cui-tags-input__status cui-form-control__status"
          role="status"
          aria-live="polite"
          aria-atomic="true"
          data-citry-ui-part="status"
        ></span>
      </div>
    """

    js = r"""
$component({props:{value:{},inputValue:{},required:{},disabled:{},readonly:{},invalid:{},placeholder:{},maxTags:{},autocomplete:{},inputmode:{},variant:{},size:{},onValueChange:{},onInputValueChange:{},onValueInvalid:{}},init:({els:e,data:t,props:n,effect:a,inject:l,i18n:Z0})=>{const i=e[0],r=i.querySelector(":scope > [data-citry-tags-input-native]"),u=i.querySelector(':scope > [data-citry-ui-part="control"]'),o=u?.querySelector(':scope > [data-citry-ui-part="tag-list"]'),d=u?.querySelector(':scope > [data-citry-ui-part="input"]'),s=i.querySelector(":scope > [data-citry-tags-input-readonly-values]"),c=i.querySelector(':scope > [data-citry-ui-part="status"]');if(!(r instanceof HTMLSelectElement&&u instanceof HTMLElement&&o instanceof HTMLElement&&d instanceof HTMLInputElement&&s instanceof HTMLElement&&c instanceof HTMLElement))throw Error("[citry-ui] CTagsInput settled anatomy is invalid.");const p=l(Symbol.for("citry-ui:field"),null),m=l(Symbol.for("citry-ui:form"),null),v=globalThis[Symbol.for("citry-ui:form-control-runtime")];if(1!==v?.generation)throw Error("[citry-ui] CTagsInput form-control runtime dependency did not load.");const f=v.resolver(i,n,"CTagsInput"),{describe:y,report:g,clear:b,callback:V}=f,h=[t.S,t.V,t.D,t.Z,t.v,t.i],x=v.tokenHandoff(i,Symbol.for("citry-ui:tags-input-runtime"),h,d,"CTagsInput");let[,,,,I,T,C,E,w,q,,,L]=x,M=!1,H=!1,k=0,S=0,z=null,A=null,D=0,N=!1,_=!1,G=0,TB=[];const R=v.listeners(),j=v.mutations(i),B=e=>v.canonical(e,t.l,!0),F=(e,t)=>p&&["required","disabled","readonly","invalid"].includes(e)?(void 0!==n[e]?g(e,n[e],"ignoring Field-owned state"):b(e),!!p[e]):f.boolean(e,t),P=(e,t)=>f.string(e,t),$=(e,t,n)=>f.choice(e,t,n),J=()=>{const e=!!m?.disabled||F("disabled",t.d)||v.fieldsetDisabled(d),n=F("readonly",t.h&&m?m.readonly:t.r);return{required:F("required",t.q),disabled:e,readonly:n,I:F("invalid",t.x),maxTags:f.maximum("maxTags",t.m),placeholder:P("placeholder",t.P),autocomplete:P("autocomplete",t.a),inputmode:P("inputmode",t.o),variant:$("variant",t.t,["outline","filled","plain"]),size:$("size",t.s,["sm","md","lg"])}},K=j.owned,{attr:O}=v,Q=(e,n,a,l)=>{if(!t.G?.[l])return v.format(e,n,a);if(Z0)switch(l){case"r":return Z0.tr("citry-ui-tags-input-remove",{value:a});case"a":return Z0.tr("citry-ui-tags-input-added",{value:a});case"d":return Z0.tr("citry-ui-tags-input-removed",{value:a});case"s":return Z0.tr("citry-ui-tags-input-selected",{value:a});case"u":return Z0.tr("citry-ui-tags-input-duplicate",{value:a});case"m":return Z0.tr("citry-ui-tags-input-maximum",{max:Z0.format.number(a,{format:"citry-ui-tags-input-maximum"})});case"e":return Z0.tr("citry-ui-tags-input-required");case"i":return Z0.tr("citry-ui-tags-input-invalid");case"c":return Z0.tr("citry-ui-tags-input-unfinished")}return"r"===l?t.K?.[a]??String(a):n?String(a):e},P0=e=>Q(t.g[e],null,null,e),U=v.status(i,c),W=U.announce,X={publicId:t.p,nativeId:t.n,visibleId:t.e,className:"cui-form-control__native--enhanced"},Y=(e=J())=>K(()=>{TB.forEach(e=>e.dispose()),TB=[],v.syncOptions(r,I,!0),v.renderTokens(o,I,{className:"cui-tags-input__tag",part:"tag",labelPart:"tag-label",active:e=>e===w,removeLabel:e=>Q(t.g.r,"value",e,"r"),removeDisabled:e.disabled||e.readonly}),Z0&&t.G.r&&o.querySelectorAll(':scope > [data-citry-ui-part="tag"] > [data-citry-ui-part="remove"]').forEach(e=>{TB.push(Z0.bind({message:"citry-ui-tags-input-remove",values:()=>({value:e.dataset.value??""}),onChange:t=>e.setAttribute("aria-label",t)}))})}),Z=(e,{clear:n=!1,input:a=(q||_?d.value:T)}={})=>{n&&(L=!1,p?.setNativeInvalid(!1)),r.setCustomValidity(e.disabled||e.readonly||!a.length?"":P0("c"));const l=e.I||L;i.toggleAttribute("data-invalid",l),((e,n)=>{v.relationships([d,r],p,{label:t.L,labelledby:t.B,describedby:t.C,errormessage:t.R,control:d,required:e.required,disabled:e.disabled,readonly:e.readonly},n)})(e,l)},ee=v.blockedTransition(()=>{++S,++G,z=null,q=!1,_=!1,N=!1,++D,L=!1,p?.setNativeInvalid(!1)}),te=(e=J())=>K(()=>{ee(e),d.disabled=e.disabled,d.readOnly=e.readonly,q||_||(d.value=T),O(d,"placeholder",e.placeholder||null),O(d,"autocomplete",e.autocomplete||null),O(d,"inputmode",e.inputmode||null),v.syncTransport(r,s,I,{name:t.N,form:t.f,required:e.required,readonly:e.readonly,disabled:e.disabled}),v.states(i,{empty:!I.length,required:e.required,disabled:e.disabled,readonly:e.readonly,"at-max":null!==e.maxTags&&I.length>=e.maxTags}),v.disableRemovals(o,e.disabled||e.readonly),i.dataset.variant=e.variant,i.dataset.size=e.size,Z(e)}),ne=()=>K(()=>{i.removeAttribute("data-citry-tags-input-initialized"),u.hidden=!0,v.enhanceNative(r,d,X,!1)}),ae=()=>{i.isConnected&&(v.exactAnatomy([[i,"[data-citry-tags-input-native]",r],[i,'[data-citry-ui-part="control"]',u],[u,'[data-citry-ui-part="tag-list"]',o],[u,'[data-citry-ui-part="input"]',d],[i,"[data-citry-tags-input-readonly-values]",s],[i,'[data-citry-ui-part="status"]',c]])||(ne(),K(()=>i.replaceChildren(r,u,s,c))),K(()=>{v.sanitizeFormControl(i,d),i.dataset.citryUiPart="tags-input",u.dataset.citryUiPart="control",o.dataset.citryUiPart="tag-list",d.dataset.citryUiPart="input",c.dataset.citryUiPart="status"}),Y(),te(),K(()=>{v.enhanceNative(r,d,X),u.hidden=!1,i.setAttribute("data-citry-tags-input-initialized","")}))},le=e=>{w=I.includes(e)?e:null,v.highlight(o,':scope > [data-citry-ui-part="tag"]',w),w&&W(Q(t.g.s,"value",w,"s"))},ie=(e,n,a,l=null)=>{const i=J();if(i.disabled||i.readonly)return;L=!0,p?.setNativeInvalid(!0),Z(i);const r={empty:P0("e"),duplicate:Q(t.g.u,"value",l??"","u"),maximum:Q(t.g.m,"max",i.maxTags??"","m"),delimiter:P0("i"),"invalid-value":P0("i")};W(r[e]),V("onValueInvalid")?.(e,{source:n,candidate:l,candidates:[...a],value:[...I],inputValue:T,maxTags:i.maxTags,controlled:M})},re=(e,t,n=!1,a=V("onInputValueChange"))=>{if(e===T)return;const l=T,r=++S,u=H;u||(T=e,E=e,d.value=e,Z(J())),a?.(e,{source:t,previousValue:l,nextValue:e,controlled:u,composing:n}),u&&i.isConnected&&r===S&&(d.value=T,Z(J()))},ue=(e,n,a)=>{const l=((e,n)=>{const a=J(),l=v.stringList(I,e,B,a.maxTags);return l.reason?(ie("invalid-value"===l.reason&&t.l.some(e=>l.candidate.includes(e))?"delimiter":l.reason,n,e,l.candidate),null):a})(e,a);if(!l)return!1;z=null;const u=[...I],o=[...I,...e],d=++k,s=++S,c=M,p=V("onValueChange"),m=V("onInputValueChange");return c||(I=o,C=[...o],Y(),te(l)),p?.([...o],{source:a,added:[...e],removed:[],candidates:[...e],previousValue:u,nextInputValue:n,controlled:c}),!(!i.isConnected||d!==k||(c?(z={next:o,added:[...e],removed:[],T:n,source:a,M:s,H:m},0):(r.dispatchEvent(new Event("input",{bubbles:!0})),!i.isConnected||d!==k||(r.dispatchEvent(new Event("change",{bubbles:!0})),S===s&&re(n,a,!1,m),W(e.map(e=>Q(t.g.a,"value",e,"a")).join(" ")),Z(J(),{clear:!0}),0))))},oe=(e,n)=>{const a=J();if(a.disabled||a.readonly)return;const l=I.indexOf(e);if(l<0)return;z=null,++S;const u=[...I],o=I.filter(t=>t!==e),s=++k;if(M||(I=o,C=[...o],Y(),te(a)),V("onValueChange")?.([...o],{source:n,added:[],removed:[e],candidates:[],previousValue:u,nextInputValue:T,controlled:M}),!i.isConnected||s!==k)return;M?z={next:o,added:[],removed:[e],T,source:n,M:S,H:null}:(v.commit(r),W(Q(t.g.d,"value",e,"d")));const c=o[l]??o[l-1]??null;le(c),v.focus(d)},de=(e,n,a=null)=>{const l=v.split(e,t.l);return!!l.candidates.length&&(l.candidates.some(e=>""===e)?(ie("empty",n,l.candidates,""),a&&a(),!0):(!ue(l.candidates,l.draft,n)&&a&&a(),!0))},se=v.registerReset(i,r,{reset:()=>{const e=k,a=S;L=!1,p?.setNativeInvalid(!1);const l=V("onValueChange"),r=V("onInputValueChange"),u=n.value,o=n.inputValue;M?l?.([...t.v],{source:"reset",added:[],removed:[],candidates:[],previousValue:[...I],nextInputValue:t.i,controlled:!0}):(I=[...t.v],C=[...t.v],Y());const s=()=>{i.isConnected&&k===e&&S===a&&n.value===u&&n.inputValue===o&&(H?r?.(t.i,{source:"reset",previousValue:T,nextValue:t.i,controlled:!0,composing:!1}):(T=t.i,E=t.i,d.value=T),w=null,te(J()))};M&&l?queueMicrotask(s):s()},invalidate:()=>{++k,++S,++G,++D,q=!1,_=!1,N=!1,z=null,U.invalidate()}}),ce=v.watchFieldset(i,d,()=>te(J()));return R.add(d,"beforeinput",()=>{A={value:d.value,start:d.selectionStart,end:d.selectionEnd}}),R.add(d,"input",e=>{if(le(null),++S,z=null,L&&(L=!1,p?.setNativeInvalid(!1),Z(J())),q||e.isComposing){e.isComposing&&!q&&(_=!0,++D);const t=T;return H||(T=d.value,E=d.value),Z(J()),void V("onInputValueChange")?.(d.value,{source:"input",previousValue:t,nextValue:d.value,controlled:H,composing:!0})}_&&(_=!1,++D),N&&(N=!1,++D);const n=A;if(t.l.some(e=>d.value.includes(e))){const e=()=>{d.value=H?T:n?.value??T;const e=n?.start??d.value.length,t=n?.end??e;d.setSelectionRange(e,t)};return void de(d.value,"delimiter",e)}re(d.value,"input")}),R.add(d,"paste",e=>{if(q||e.isComposing)return;const n=e.clipboardData?.getData("text/plain")??"";if(!t.l.some(e=>n.includes(e))&&!/[\r\n]/.test(n))return;e.preventDefault();const a=d.selectionStart??d.value.length,l=d.selectionEnd??a,i=d.value.slice(0,a)+n+d.value.slice(l);de(i,"paste")}),R.add(d,"keydown",e=>{if(q||e.isComposing||229===e.keyCode)return;const t=J();if(t.disabled||t.readonly)return;if("Enter"===e.key){if(!d.value)return;return e.preventDefault(),void ue([v.trim(d.value)],"","enter")}const n=0===d.selectionStart&&0===d.selectionEnd;if("Backspace"===e.key&&n)return void(w?(e.preventDefault(),oe(w,"backspace")):I.length&&(e.preventDefault(),le(I.at(-1))));if("Delete"===e.key&&w)return e.preventDefault(),void oe(w,"delete");if("Escape"===e.key&&w)return e.preventDefault(),void le(null);if(("Home"===e.key||"End"===e.key)&&w)return e.preventDefault(),void le("Home"===e.key?I[0]:I.at(-1));const a="rtl"===getComputedStyle(i).direction;if(n&&(!a&&"ArrowLeft"===e.key||a&&"ArrowRight"===e.key)){e.preventDefault();const t=w?I.indexOf(w):I.length;return void le(I[Math.max(0,t-1)])}if(w&&(!a&&"ArrowRight"===e.key||a&&"ArrowLeft"===e.key)){e.preventDefault();const t=I.indexOf(w)+1;return void le(t<I.length?I[t]:null)}w&&1===e.key.length&&le(null)}),R.add(d,"compositionstart",()=>{_=!1,q=!0,N=!1,++D}),R.add(d,"compositionend",()=>{q=!1,_=!1,N=!0;const e=++D;queueMicrotask(()=>{e===D&&N&&i.isConnected&&(N=!1,t.l.some(e=>d.value.includes(e))?de(d.value,"delimiter"):re(d.value,"input"))})}),R.add(d,"focus",()=>K(()=>i.toggleAttribute("data-focused",!0))),R.add(d,"blur",()=>K(()=>i.removeAttribute("data-focused"))),R.add(u,"click",e=>{const t=e.target.closest('[data-citry-ui-part="remove"]');t&&t.closest('[data-citry-ui-part="tags-input"]')===i?(e.preventDefault(),oe(t.dataset.value,"remove")):u.contains(e.target)&&v.focus(d)}),R.add(r,"invalid",e=>{e.preventDefault(),L=!0,p?.setNativeInvalid(!0),Z(J()),W(r.validationMessage);const t=++G;v.invalidFocus(i,d,()=>t===G)},!0),j.start(ae),a(()=>{const e=J();ee(e);const a=n.inputValue;null!=a?"string"!=typeof a||/[\0\r\n]/.test(a)?g("inputValue",a):(b("inputValue"),H=!0,T!==a&&(T=a,++S,z?.added.length&&(z=null))):(H&&(T=E,++S,z?.added.length&&(z=null)),H=!1,b("inputValue"));const l=n.value;if(null!=l)if(!Array.isArray(i=l)||v.stringList([],i,B).reason)g("value",l);else if(null!==e.maxTags&&l.length>e.maxTags&&y(l)!==y(I))g("value",l);else{b("value");const e=y(I)!==y(l);if(I=[...l],M=!0,e){const e=z;z=null,e&&y(l)===y(e.next)&&(e.added.length?(S===e.M&&re(e.T,e.source,!1,e.H),W(e.added.map(e=>Q(t.g.a,"value",e,"a")).join(" "))):e.removed.length&&W(e.removed.map(e=>Q(t.g.d,"value",e,"d")).join(" ")))}}else M&&(I=[...C],++k,z=null),M=!1,b("value");var i;Y(),te(e)}),ae(),v.restoreTokenHandoff(x,d,c,K),()=>{const e=v.saveTokenHandoff(x,h,d,[I,C,T,E,w,q||_,L,c.textContent??""]);++k,++S,++G,++D,U.invalidate(),TB.forEach(e=>e.dispose()),j.stop(),ce(),se(),e&&p?.setNativeInvalid(!1),R.stop(),e&&ne()}}});
    """

    css = """
      @layer citry-ui.theme{:where(.cui-tags-input){--_cui-tags-input-background:var(--cui-tags-input-background,Canvas);--_cui-tags-input-foreground:var(--cui-tags-input-foreground,CanvasText);--_cui-tags-input-border-color:var(--cui-tags-input-border-color,color-mix(in srgb,CanvasText 28%,transparent));--_cui-tags-input-hover-border-color:var(--cui-tags-input-hover-border-color,color-mix(in srgb,CanvasText 55%,transparent));--_cui-tags-input-focus-color:var(--cui-tags-input-focus-color,Highlight);--_cui-tags-input-invalid-border-color:var(--cui-tags-input-invalid-border-color,light-dark(#b42318,#fda29b));--_cui-tags-input-disabled-background:var(--cui-tags-input-disabled-background,color-mix(in srgb,CanvasText 6%,Canvas));--_cui-tags-input-tag-background:var(--cui-tags-input-tag-background,color-mix(in srgb,CanvasText 8%,Canvas));--_cui-tags-input-tag-foreground:var(--cui-tags-input-tag-foreground,CanvasText);--_cui-tags-input-tag-border-color:var(--cui-tags-input-tag-border-color,color-mix(in srgb,CanvasText 18%,transparent));--_cui-tags-input-tag-highlighted-background:var(--cui-tags-input-tag-highlighted-background,light-dark(#dbeafe,#19376d));--_cui-tags-input-tag-highlighted-border-color:var(--cui-tags-input-tag-highlighted-border-color,Highlight);--_cui-tags-input-radius:var(--cui-tags-input-radius,.5rem);--_cui-tags-input-min-height:var(--cui-tags-input-min-height,2.5rem);--_cui-tags-input-padding:var(--cui-tags-input-padding,.375rem .5rem);--_cui-tags-input-gap:var(--cui-tags-input-gap,.375rem);--_cui-tags-input-tag-gap:var(--cui-tags-input-tag-gap,.25rem);--_cui-tags-input-font-size:var(--cui-tags-input-font-size,1rem);min-inline-size:0;color:var(--_cui-tags-input-foreground);font:var(--_cui-tags-input-font-size)/1.25 ui-sans-serif,system-ui,sans-serif;}:where(.cui-tags-input__control){display:flex;align-items:center;flex-wrap:wrap;gap:var(--_cui-tags-input-gap);min-block-size:var(--_cui-tags-input-min-height);padding:var(--_cui-tags-input-padding);box-sizing:border-box;border:1px solid var(--_cui-tags-input-border-color);border-radius:var(--_cui-tags-input-radius);background:var(--_cui-tags-input-background);}:where(.cui-tags-input__control:hover){border-color:var(--_cui-tags-input-hover-border-color);}:where(.cui-tags-input[data-focused] .cui-tags-input__control){outline:2px solid var(--_cui-tags-input-focus-color);outline-offset:2px;}:where(.cui-tags-input[data-invalid] .cui-tags-input__control){border-color:var(--_cui-tags-input-invalid-border-color);}:where(.cui-tags-input[data-disabled] .cui-tags-input__control){background:var(--_cui-tags-input-disabled-background);opacity:.65;}:where(.cui-tags-input[data-variant="filled"] .cui-tags-input__control){background:var(--_cui-tags-input-tag-background);}:where(.cui-tags-input[data-variant="plain"] .cui-tags-input__control){border-color:transparent;background:transparent;}:where(.cui-tags-input[data-size="sm"]){--_cui-tags-input-min-height:2rem;--_cui-tags-input-font-size:.875rem;}:where(.cui-tags-input[data-size="lg"]){--_cui-tags-input-min-height:3rem;--_cui-tags-input-font-size:1.125rem;}:where(.cui-tags-input__tag-list){display:contents;}:where(.cui-tags-input__tag){display:inline-flex;align-items:center;gap:var(--_cui-tags-input-tag-gap);max-inline-size:100%;border:1px solid var(--_cui-tags-input-tag-border-color);border-radius:var(--_cui-tags-input-radius);background:var(--_cui-tags-input-tag-background);color:var(--_cui-tags-input-tag-foreground);padding-inline-start:.5em;overflow-wrap:anywhere;}:where(.cui-tags-input__tag[data-highlighted]){background:var(--_cui-tags-input-tag-highlighted-background);border-color:var(--_cui-tags-input-tag-highlighted-border-color);}:where(.cui-tags-input__tag [data-citry-ui-part="remove"]){display:inline-grid;place-items:center;min-inline-size:44px;min-block-size:44px;border:0;background:transparent;color:inherit;cursor:pointer;}:where(.cui-tags-input__input){flex:1 1 8ch;min-inline-size:4ch;border:0;outline:0;background:transparent;color:inherit;font:inherit;}@media (forced-colors:active){:where(.cui-tags-input__control,.cui-tags-input__tag){border-color:CanvasText}:where(.cui-tags-input[data-focused] .cui-tags-input__control,.cui-tags-input__tag[data-highlighted]){outline-color:Highlight}}@media print{:where(.cui-tags-input__input,.cui-tags-input__tag [data-citry-ui-part="remove"],.cui-tags-input__native){display:none!important}:where(.cui-tags-input__control){border:0;padding:0}}}
    """

    messages = """
      # @param {str} $value - Visible tag label.
      citry-ui-tags-input-remove = Remove { $value }
      # @param {str} $value - Visible tag label.
      citry-ui-tags-input-added = Added { $value }
      # @param {str} $value - Visible tag label.
      citry-ui-tags-input-removed = Removed { $value }
      # @param {str} $value - Visible tag label.
      citry-ui-tags-input-selected = Selected { $value }
      # @param {str} $value - Visible tag label.
      citry-ui-tags-input-duplicate = { $value } is already added
      # @param {str} $max - Locale-formatted maximum number of tags.
      citry-ui-tags-input-maximum = Add at most { $max } tags
      citry-ui-tags-input-required = Tags cannot be empty
      citry-ui-tags-input-invalid = That tag is invalid
      citry-ui-tags-input-unfinished = Add or clear the unfinished tag before submitting
    """


__all__ = [
    "CTagsInput",
    "CTagsInputChangeSource",
    "CTagsInputInputValueChangeDetail",
    "CTagsInputInvalidDetail",
    "CTagsInputInvalidReason",
    "CTagsInputMessages",
    "CTagsInputSize",
    "CTagsInputValueChangeDetail",
    "CTagsInputVariant",
]
