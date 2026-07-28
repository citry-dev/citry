"""Styled and headless Button component definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput

CButtonType = Literal["button", "submit", "reset"]


class CButtonHeadlessDefaultSlotData:
    attrs: dict[str, str | bool | None]
    disabled: bool
    loading: bool


class CButtonHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        loading: bool = False
        disabled: bool = False
        type: CButtonType = "button"

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        disabled = kwargs.disabled or kwargs.loading
        return {
            "slot_data": {
                "attrs": {
                    "type": kwargs.type,
                    "disabled": disabled,
                    "aria-busy": "true" if kwargs.loading else None,
                    "data-loading": kwargs.loading,
                },
                "disabled": disabled,
                "loading": kwargs.loading,
            }
        }

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CButtonDefaultSlotData:
    pass


class CButton(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CButtonHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonDefaultSlotData]

    template = """
      <c-CButtonHeadless
        c-loading="loading"
        c-disabled="disabled"
        c-type="type"
      >
        <c-fill name="default" data="data">
          <button
            class="cui-button"
            c-bind="data.attrs"
            data-citry-ui-part="button"
          >
            <c-if cond="data.loading">
              <span data-citry-ui-part="loading-indicator">
                Loading
              </span>
            </c-if>
            <span data-citry-ui-part="content">
              <c-slot />
            </span>
          </button>
        </c-fill>
      </c-CButtonHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-button) {
          --cui-button-background: #175cd3;
          --cui-button-foreground: #ffffff;
          --cui-button-radius: 0.375rem;

          appearance: none;
          border: 0;
          border-radius: var(--cui-button-radius);
          background: var(--cui-button-background);
          color: var(--cui-button-foreground);
          cursor: pointer;
          font: inherit;
          padding-block: 0.5rem;
          padding-inline: 0.875rem;
        }

        :where(.cui-button:focus-visible) {
          outline: 0.1875rem solid CanvasText;
          outline-offset: 0.1875rem;
        }
      }
    """


__all__ = [
    "CButton",
    "CButtonDefaultSlotData",
    "CButtonHeadless",
    "CButtonHeadlessDefaultSlotData",
    "CButtonType",
]
