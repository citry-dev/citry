"""Styled and headless Field and Input component definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, SlotInput

CFieldOrientation = Literal["vertical", "horizontal"]
CFieldDensity = Literal["comfortable", "compact"]
CInputType = Literal["text", "email", "password", "search", "tel", "url"]

_FIELD_CONTEXT_KEY = "citry_ui_field"


class CFieldHeadlessDefaultSlotData:
    root_attrs: dict[str, object]
    label_attrs: dict[str, object]
    control_attrs: dict[str, object]
    description_attrs: dict[str, object]
    error_attrs: dict[str, object]
    control_id: str
    label_id: str
    description_id: str
    error_id: str
    is_required: bool
    is_disabled: bool
    is_invalid: bool
    has_description: bool
    has_error: bool


class CFieldHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        control_id: str | None = None
        required: bool = False
        disabled: bool = False
        invalid: bool = False
        has_description: bool = False
        has_error: bool = False
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CFieldHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CFieldHeadless.Kwargs,
        slots: CFieldHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        control_id = kwargs.control_id or f"cui-field-{self.id}-control"
        label_id = f"{control_id}-label"
        description_id = f"{control_id}-description"
        error_id = f"{control_id}-error"
        described_by = " ".join(
            item
            for item, present in (
                (description_id, kwargs.has_description),
                (error_id, kwargs.invalid and kwargs.has_error),
            )
            if present
        )
        root_attrs: dict[str, object] = {
            **(kwargs.attrs or {}),
            "data-disabled": kwargs.disabled,
            "data-invalid": kwargs.invalid,
            "data-required": kwargs.required,
        }
        control_attrs: dict[str, object] = {
            "id": control_id,
            "required": kwargs.required,
            "disabled": kwargs.disabled,
            "aria-invalid": "true" if kwargs.invalid else None,
            "aria-describedby": described_by or None,
            "aria-errormessage": error_id if kwargs.invalid and kwargs.has_error else None,
        }
        slot_data = {
            "root_attrs": root_attrs,
            "label_attrs": {"id": label_id, "for": control_id},
            "control_attrs": control_attrs,
            "description_attrs": {"id": description_id},
            "error_attrs": {"id": error_id, "aria-live": "polite"},
            "control_id": control_id,
            "label_id": label_id,
            "description_id": description_id,
            "error_id": error_id,
            "is_required": kwargs.required,
            "is_disabled": kwargs.disabled,
            "is_invalid": kwargs.invalid,
            "has_description": kwargs.has_description,
            "has_error": kwargs.has_error,
        }
        self.provide(
            _FIELD_CONTEXT_KEY,
            control_attrs=control_attrs,
            required=kwargs.required,
            disabled=kwargs.disabled,
            invalid=kwargs.invalid,
            description_id=description_id,
            error_id=error_id,
            has_error=kwargs.has_error,
        )
        return {"slot_data": slot_data}

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CFieldLabelSlotData:
    pass


class CFieldDefaultSlotData:
    control_attrs: dict[str, object]
    control_id: str
    label_id: str
    description_id: str
    error_id: str
    is_required: bool
    is_disabled: bool
    is_invalid: bool


class CFieldDescriptionSlotData:
    pass


class CFieldErrorSlotData:
    pass


class CField(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        control_id: str | None = None
        required: bool = False
        disabled: bool = False
        invalid: bool = False
        orientation: CFieldOrientation = "vertical"
        density: CFieldDensity = "comfortable"
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        label: SlotInput[CFieldLabelSlotData]
        default: SlotInput[CFieldDefaultSlotData]
        description: SlotInput[CFieldDescriptionSlotData] | None = None
        error: SlotInput[CFieldErrorSlotData] | None = None

    def template_data(
        self,
        kwargs: CField.Kwargs,
        slots: CField.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "control_id": kwargs.control_id,
            "required": kwargs.required,
            "disabled": kwargs.disabled,
            "invalid": kwargs.invalid,
            "orientation": kwargs.orientation,
            "density": kwargs.density,
            "field_class": f"cui-field cui-field--{kwargs.orientation} cui-field--{kwargs.density}",
            "attrs": kwargs.attrs,
            "has_description": "description" in self.raw_slots,
            "has_error": "error" in self.raw_slots,
        }

    template = """
      <c-CFieldHeadless
        c-control_id="control_id"
        c-required="required"
        c-disabled="disabled"
        c-invalid="invalid"
        c-has_description="has_description"
        c-has_error="has_error"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <div
            c-class="field_class"
            c-bind="data.root_attrs"
            data-citry-ui-part="field"
          >
            <label
              c-bind="data.label_attrs"
              data-citry-ui-part="label"
            >
              <c-slot name="label" required />
            </label>
            <div data-citry-ui-part="control">
              <c-slot
                c-control_attrs="data.control_attrs"
                c-control_id="data.control_id"
                c-label_id="data.label_id"
                c-description_id="data.description_id"
                c-error_id="data.error_id"
                c-is_required="data.is_required"
                c-is_disabled="data.is_disabled"
                c-is_invalid="data.is_invalid"
                required
              />
            </div>
            <c-if cond="data.has_description">
              <div
                c-bind="data.description_attrs"
                data-citry-ui-part="description"
              >
                <c-slot name="description" />
              </div>
            </c-if>
            <div
              c-bind="data.error_attrs"
              data-citry-ui-part="error"
            >
              <c-if cond="data.has_error">
                <c-slot name="error" />
              </c-if>
            </div>
          </div>
        </c-fill>
      </c-CFieldHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-field) {
          display: grid;
          gap: 0.375rem;
        }

        :where(.cui-field--horizontal) {
          grid-template-columns: minmax(8rem, 0.35fr) minmax(0, 1fr);
          align-items: start;
        }

        :where(.cui-field--compact) {
          gap: 0.25rem;
        }

        :where(.cui-field [data-citry-ui-part="label"]) {
          font-weight: 600;
        }

        :where(.cui-field [data-citry-ui-part="description"]) {
          color: #475467;
        }

        :where(.cui-field [data-citry-ui-part="error"]) {
          color: #b42318;
          min-height: 1.25em;
        }
      }
    """


def _idrefs(value: object) -> list[str]:
    """Normalize a user-provided ARIA ID-reference list."""
    if value is None or value is False:
        return []
    if not isinstance(value, str):
        msg = f"ARIA relationship attributes must be strings, got {value!r}."
        raise TypeError(msg)
    return value.split()


def _merge_idrefs(*values: object) -> str | None:
    """Merge ARIA ID references in order without emitting duplicates."""
    merged = dict.fromkeys(token for value in values for token in _idrefs(value))
    return " ".join(merged) or None


class CInputHeadlessDefaultSlotData:
    input_attrs: dict[str, object]
    is_required: bool
    is_disabled: bool
    is_invalid: bool


def _input_template_data(
    component: CInputHeadless,
    kwargs: CInputHeadless.Kwargs,
) -> dict[str, object]:
    field = component.inject(_FIELD_CONTEXT_KEY, None)
    inherited_attrs = dict(field.control_attrs) if field is not None else {}
    field_control_id = cast("str | None", inherited_attrs.get("id"))
    if field_control_id is not None and kwargs.id is not None and kwargs.id != field_control_id:
        msg = (
            f"Input id {kwargs.id!r} conflicts with its Field control_id {field_control_id!r}; "
            "set the same value on Field.control_id and Input.id."
        )
        raise ValueError(msg)

    required = kwargs.required if kwargs.required is not None else bool(field.required) if field is not None else False
    disabled = kwargs.disabled if kwargs.disabled is not None else bool(field.disabled) if field is not None else False
    invalid = kwargs.invalid if kwargs.invalid is not None else bool(field.invalid) if field is not None else False
    input_id = kwargs.id or field_control_id
    caller_attrs = dict(kwargs.attrs or {})

    inherited_described_by = _idrefs(inherited_attrs.pop("aria-describedby", None))
    if field is not None:
        if invalid and field.has_error:
            inherited_described_by.append(field.error_id)
        elif not invalid:
            inherited_described_by = [token for token in inherited_described_by if token != field.error_id]
    described_by = _merge_idrefs(
        " ".join(inherited_described_by),
        caller_attrs.pop("aria-describedby", None),
    )

    if invalid:
        error_message = _merge_idrefs(
            inherited_attrs.pop("aria-errormessage", None),
            field.error_id if field is not None and field.has_error else None,
            caller_attrs.pop("aria-errormessage", None),
        )
    else:
        inherited_attrs.pop("aria-errormessage", None)
        caller_attrs.pop("aria-errormessage", None)
        error_message = None

    input_attrs = {
        **inherited_attrs,
        **caller_attrs,
        "id": input_id,
        "name": kwargs.name,
        "type": kwargs.type,
        "value": kwargs.value,
        "required": required,
        "disabled": disabled,
        "readonly": kwargs.readonly,
        "aria-invalid": "true" if invalid else None,
        "aria-describedby": described_by,
        "aria-errormessage": error_message,
        "autocomplete": kwargs.autocomplete,
        "inputmode": kwargs.inputmode,
        "placeholder": kwargs.placeholder,
    }
    return {
        "input_attrs": input_attrs,
        "is_required": required,
        "is_disabled": disabled,
        "is_invalid": invalid,
    }


class CInputHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        name: str
        type: CInputType = "text"
        id: str | None = None
        value: str | None = None
        required: bool | None = None
        disabled: bool | None = None
        readonly: bool = False
        invalid: bool | None = None
        autocomplete: str | None = None
        inputmode: str | None = None
        placeholder: str | None = None
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CInputHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CInputHeadless.Kwargs,
        slots: CInputHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {"slot_data": _input_template_data(self, kwargs)}

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CInput(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CInputHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        pass

    template = """
      <c-CInputHeadless
        c-name="name"
        c-type="type"
        c-id="id"
        c-value="value"
        c-required="required"
        c-disabled="disabled"
        c-readonly="readonly"
        c-invalid="invalid"
        c-autocomplete="autocomplete"
        c-inputmode="inputmode"
        c-placeholder="placeholder"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <input
            class="cui-input"
            c-bind="data.input_attrs"
            data-citry-ui-part="input"
          />
        </c-fill>
      </c-CInputHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-input) {
          box-sizing: border-box;
          width: 100%;
          border: 1px solid #98a2b3;
          border-radius: 0.375rem;
          background: Canvas;
          color: CanvasText;
          font: inherit;
          padding: 0.5rem 0.625rem;
        }

        :where(.cui-input[aria-invalid="true"]) {
          border-color: #d92d20;
        }

        :where(.cui-input:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: 0.125rem;
        }
      }
    """


__all__ = [
    "CField",
    "CFieldDefaultSlotData",
    "CFieldDensity",
    "CFieldDescriptionSlotData",
    "CFieldErrorSlotData",
    "CFieldHeadless",
    "CFieldHeadlessDefaultSlotData",
    "CFieldLabelSlotData",
    "CFieldOrientation",
    "CInput",
    "CInputHeadless",
    "CInputHeadlessDefaultSlotData",
    "CInputType",
]
