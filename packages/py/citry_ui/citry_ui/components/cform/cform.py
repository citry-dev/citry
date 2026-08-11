"""Styled native Form component family."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_optional_string,
)

CFormMethod = Literal["get", "post", "dialog"]
CFormEnctype = Literal[
    "application/x-www-form-urlencoded",
    "multipart/form-data",
    "text/plain",
]
CFormAutocomplete = Literal["on", "off"]


class CFormDefaultSlotData:
    pass


class CForm(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        action: str | None = None
        method: CFormMethod | None = None
        enctype: CFormEnctype | None = None
        target: str | None = None
        autocomplete: CFormAutocomplete | None = None
        disabled: bool = False
        readonly: bool = False
        submitting: bool = False
        novalidate: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CFormDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if self.inject(FORM_CONTEXT_KEY, None) is not None:
            msg = "CForm cannot be nested inside another CForm."
            raise ValueError(msg)
        validate_html_id("CForm", kwargs.id)
        validate_optional_string("CForm", "action", kwargs.action)
        if kwargs.method is not None:
            validate_choice("CForm", "method", kwargs.method, ("get", "post", "dialog"))
        if kwargs.enctype is not None:
            validate_choice(
                "CForm",
                "enctype",
                kwargs.enctype,
                (
                    "application/x-www-form-urlencoded",
                    "multipart/form-data",
                    "text/plain",
                ),
            )
        validate_optional_string("CForm", "target", kwargs.target)
        if kwargs.autocomplete is not None:
            validate_choice("CForm", "autocomplete", kwargs.autocomplete, ("on", "off"))
        validate_boolean("CForm", "disabled", kwargs.disabled)
        validate_boolean("CForm", "readonly", kwargs.readonly)
        validate_boolean("CForm", "submitting", kwargs.submitting)
        validate_boolean("CForm", "novalidate", kwargs.novalidate)
        reject_owned_attrs(
            kwargs.attrs,
            {
                "action",
                "aria-busy",
                "autocomplete",
                "data-citry-form-initialized",
                "data-citry-ui-part",
                "data-disabled",
                "data-readonly",
                "data-submitting",
                "data-validation-attempted",
                "enctype",
                "id",
                "method",
                "novalidate",
                "target",
            },
            "CForm",
        )
        form_id = kwargs.id or f"cui-form-{self.id}"
        self.provide(
            FORM_CONTEXT_KEY,
            form_id=form_id,
            disabled=kwargs.disabled,
            readonly=kwargs.readonly,
        )
        return {
            "form_id": form_id,
            "action": kwargs.action,
            "method": kwargs.method,
            "enctype": kwargs.enctype,
            "target": kwargs.target,
            "autocomplete": kwargs.autocomplete,
            "disabled": kwargs.disabled,
            "readonly": kwargs.readonly,
            "submitting": kwargs.submitting,
            "novalidate": kwargs.novalidate,
            "aria_busy": "true" if kwargs.submitting else None,
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "disabled": kwargs.disabled,
            "readonly": kwargs.readonly,
            "submitting": kwargs.submitting,
            "colors": ["red", "green", "blue"],
        }

    template = """
      <form
        class="cui-form"
        c-id="form_id"
        c-action="action"
        c-method="method"
        c-enctype="enctype"
        c-target="target"
        c-autocomplete="autocomplete"
        c-novalidate="novalidate"
        c-aria-busy="aria_busy"
        c-data-disabled="disabled"
        c-data-readonly="readonly"
        c-data-submitting="submitting"
        c-bind="attrs"
        data-citry-ui-part="form"
      >
        <fieldset
          class="cui-form__fieldset"
          c-disabled="disabled"
          data-citry-ui-part="fieldset"
        >
          <legend hidden aria-hidden="true"></legend>
          <c-slot required />
        </fieldset>
      </form>
    """

    js = """
      $component({
        props: {
          disabled: {},
          readonly: {},
          submitting: {},
        },
        init: ({ els, data, scope, props, effect, reactive, provide }) => {
          const form = els[0];
          const fieldset = form.querySelector('[data-citry-ui-part="fieldset"]');
          const invalidEpisodes = new Set();
          const resetTimers = new Set();
          let invalidGeneration = 0;
          let configuration = {
            disabled: data.disabled,
            readonly: data.readonly,
            submitting: data.submitting,
          };

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            const describedValue = describeValue(value);
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CForm ${name} received invalid client value ${describedValue}; `
                + "using the server-rendered fallback.",
              form,
            );
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const context = reactive({
            form,
            disabled: configuration.disabled,
            readonly: configuration.readonly,
          });
          provide(Symbol.for("citry-ui:form"), context);

          const applyConfiguration = (next) => {
            configuration = next;
            context.disabled = next.disabled;
            context.readonly = next.readonly;
            fieldset.disabled = next.disabled;
            form.toggleAttribute("data-disabled", next.disabled);
            form.toggleAttribute("data-readonly", next.readonly);
            form.toggleAttribute("data-submitting", next.submitting);
            if (next.submitting) {
              form.setAttribute("aria-busy", "true");
            } else {
              form.removeAttribute("aria-busy");
            }
          };
          const onInvalid = () => {
            invalidGeneration += 1;
            form.setAttribute("data-validation-attempted", "");
          };
          const onReset = (event) => {
            // Reset is cancelable. Wait until every listener has run before
            // clearing Form-owned attempted-validation presentation.
            // Keep one task per event: a later canceled reset must not erase
            // the outcome of an earlier uncanceled reset in the same turn.
            const resetInvalidGeneration = invalidGeneration;
            const timer = setTimeout(() => {
              resetTimers.delete(timer);
              if (event.defaultPrevented || invalidGeneration !== resetInvalidGeneration) {
                return;
              }
              form.removeAttribute("data-validation-attempted");
            }, 0);
            resetTimers.add(timer);
          };
          const onSubmit = (event) => {
            if (!configuration.submitting) {
              return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
          };

          form.addEventListener("invalid", onInvalid, true);
          form.addEventListener("reset", onReset);
          form.addEventListener("submit", onSubmit, true);
          effect(() => {
            applyConfiguration({
              disabled: resolveBoolean("disabled"),
              readonly: resolveBoolean("readonly"),
              submitting: resolveBoolean("submitting"),
            });
          });
          form.setAttribute("data-citry-form-initialized", "");

          return () => {
            form.removeEventListener("invalid", onInvalid, true);
            form.removeEventListener("reset", onReset);
            form.removeEventListener("submit", onSubmit, true);
            for (const timer of resetTimers) {
              clearTimeout(timer);
            }
            resetTimers.clear();
            form.removeAttribute("data-citry-form-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-form) {
          --_cui-form-gap: var(--cui-form-gap, 1rem);

          display: block;
          min-inline-size: 0;
        }

        :where(.cui-form__fieldset) {
          display: grid;
          min-inline-size: 0;
          margin: 0;
          padding: 0;
          border: 0;
          gap: var(--_cui-form-gap);
        }
      }
    """


__all__ = [
    "CForm",
    "CFormAutocomplete",
    "CFormDefaultSlotData",
    "CFormEnctype",
    "CFormMethod",
]
