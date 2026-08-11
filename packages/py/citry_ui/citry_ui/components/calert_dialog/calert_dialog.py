"""Urgent modal AlertDialog built on the shared native Dialog runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, SlotInput
from citry.ext.dependencies import Style
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
)
from citry_ui.components.cdialog.cdialog import CDialog

CAlertDialogSize = Literal["sm", "md", "lg"]
CAlertDialogScroll = Literal["body", "dialog"]

_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_OWNED_ATTRS = frozenset(
    {
        "aria-describedby",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-modal",
        "closedby",
        "contenteditable",
        "data-citry-ui-part",
        "data-open",
        "data-scroll",
        "data-size",
        "hidden",
        "id",
        "inert",
        "open",
        "popover",
        "role",
        "tabindex",
    }
)


class CAlertDialogActivatorSlotData:
    activator_attrs: dict[str, object]
    activator_type: Literal["button"]


class CAlertDialogTitleSlotData:
    pass


class CAlertDialogDescriptionSlotData:
    pass


class CAlertDialogDefaultSlotData:
    pass


class CAlertDialogCancelSlotData:
    cancel_attrs: dict[str, object]
    cancel_type: Literal["button"]


class CAlertDialogActionSlotData:
    action_attrs: dict[str, object]
    action_type: Literal["button"]


class CAlertDialogOpenChangeDetail(TypedDict):
    reason: Literal["trigger", "escape", "action", "native"]
    controlled: bool
    source: object | None
    returnValue: str


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"CAlertDialog attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CAlertDialog attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CAlertDialog attrs cannot contain reserved Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"CAlertDialog attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in _OWNED_ATTRS:
            raise ValueError(f"CAlertDialog attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CAlertDialog(LibraryComponent):
    class Dependencies:
        css = (Style(content=CDialog.css),)

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        close_on_escape: bool = True
        size: CAlertDialogSize = "sm"
        scroll: CAlertDialogScroll = "body"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CAlertDialogTitleSlotData]
        description: SlotInput[CAlertDialogDescriptionSlotData]
        cancel: SlotInput[CAlertDialogCancelSlotData]
        action: SlotInput[CAlertDialogActionSlotData]
        activator: SlotInput[CAlertDialogActivatorSlotData] | None = None
        default: SlotInput[CAlertDialogDefaultSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_html_id("CAlertDialog", kwargs.id)
        if kwargs.id is not None and "\x00" in kwargs.id:
            raise ValueError("CAlertDialog id cannot contain U+0000.")
        validate_boolean("CAlertDialog", "open", kwargs.open)
        validate_boolean("CAlertDialog", "close_on_escape", kwargs.close_on_escape)
        validate_choice("CAlertDialog", "size", kwargs.size, ("sm", "md", "lg"))
        validate_choice("CAlertDialog", "scroll", kwargs.scroll, ("body", "dialog"))
        dialog_id = kwargs.id or f"cui-alert-dialog-{self.id}"
        title_id = f"{dialog_id}-title"
        description_id = f"{dialog_id}-description"
        return {
            "dialog_id": dialog_id,
            "title_id": title_id,
            "description_id": description_id,
            "open": bool(kwargs.open),
            "size": kwargs.size,
            "scroll": kwargs.scroll,
            "has_activator": "activator" in self.raw_slots,
            "has_body": "default" in self.raw_slots,
            "activator_attrs": {
                "aria-haspopup": "dialog",
                "aria-controls": dialog_id,
                "aria-expanded": "true" if kwargs.open else "false",
                "data-citry-dialog-trigger": "",
            },
            "button_type": "button",
            "cancel_attrs": {
                "autofocus": True,
                "data-citry-dialog-close": "",
                "value": "cancel",
            },
            "action_attrs": {
                "data-citry-dialog-close": "",
                "value": "action",
            },
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "open": bool(kwargs.open),
            "dismissible": True,
            "closeOnEscape": bool(kwargs.close_on_escape),
            "closeOnOutside": False,
            "initialFocus": "auto",
            "size": kwargs.size,
            "scroll": kwargs.scroll,
        }

    template = """
      <div class="cui-dialog-host cui-alert-dialog-host" data-citry-dialog-host>
        <c-if cond="has_activator">
          <c-slot
            name="activator"
            c-activator_attrs="activator_attrs"
            c-activator_type="button_type"
          />
        </c-if>
        <dialog
          class="cui-dialog cui-alert-dialog"
          c-id="dialog_id"
          c-open="open"
          role="alertdialog"
          aria-modal="true"
          c-aria-labelledby="title_id"
          c-aria-describedby="description_id"
          c-data-open="open"
          c-data-size="size"
          c-data-scroll="scroll"
          c-bind="attrs"
          data-citry-dialog-surface
          data-citry-ui-part="alert-dialog"
        >
          <div class="cui-dialog__surface" data-citry-ui-part="surface">
            <header class="cui-dialog__header" data-citry-ui-part="header">
              <h2 class="cui-dialog__title" c-id="title_id" data-citry-ui-part="title">
                <c-slot name="title" required />
              </h2>
            </header>
            <div
              class="cui-dialog__description"
              c-id="description_id"
              data-citry-ui-part="description"
            ><c-slot name="description" required /></div>
            <c-if cond="has_body">
              <div class="cui-dialog__body" data-citry-ui-part="body"><c-slot /></div>
            </c-if>
            <footer class="cui-dialog__actions" data-citry-ui-part="actions">
              <c-slot
                name="cancel"
                c-cancel_attrs="cancel_attrs"
                c-cancel_type="button_type"
                required
              />
              <c-slot
                name="action"
                c-action_attrs="action_attrs"
                c-action_type="button_type"
                required
              />
            </footer>
          </div>
        </dialog>
      </div>
    """

    js = CDialog.js
    css = """
      @layer citry-ui.theme {
        :where(.cui-alert-dialog) {
          --_cui-alert-dialog-backdrop: var(
            --cui-alert-dialog-backdrop,
            rgb(15 23 42 / 58%)
          );
          --_cui-alert-dialog-background: var(
            --cui-alert-dialog-background,
            Canvas
          );
          --_cui-alert-dialog-foreground: var(
            --cui-alert-dialog-foreground,
            CanvasText
          );
          --_cui-alert-dialog-border-color: var(
            --cui-alert-dialog-border-color,
            color-mix(in srgb, CanvasText 16%, transparent)
          );
          --_cui-alert-dialog-radius: var(
            --cui-alert-dialog-radius,
            0.875rem
          );
          --_cui-alert-dialog-shadow: var(
            --cui-alert-dialog-shadow,
            0 1.5rem 4rem rgb(15 23 42 / 28%)
          );
          --_cui-alert-dialog-inline-size: var(
            --cui-alert-dialog-inline-size,
            26rem
          );
          --_cui-alert-dialog-max-block-size: var(
            --cui-alert-dialog-max-block-size,
            calc(100dvb - 2rem)
          );
          --_cui-alert-dialog-padding: var(
            --cui-alert-dialog-padding,
            1.25rem
          );
          --_cui-alert-dialog-gap: var(
            --cui-alert-dialog-gap,
            1rem
          );

          --_cui-dialog-backdrop: var(--_cui-alert-dialog-backdrop);
          --_cui-dialog-background: var(--_cui-alert-dialog-background);
          --_cui-dialog-foreground: var(--_cui-alert-dialog-foreground);
          --_cui-dialog-border-color: var(--_cui-alert-dialog-border-color);
          --_cui-dialog-radius: var(--_cui-alert-dialog-radius);
          --_cui-dialog-shadow: var(--_cui-alert-dialog-shadow);
          --_cui-dialog-inline-size: var(--_cui-alert-dialog-inline-size);
          --_cui-dialog-max-block-size: var(--_cui-alert-dialog-max-block-size);
          --_cui-dialog-padding: var(--_cui-alert-dialog-padding);
          --_cui-dialog-gap: var(--_cui-alert-dialog-gap);
        }

        :where(.cui-alert-dialog[data-size="sm"]) {
          --_cui-alert-dialog-inline-size: var(
            --cui-alert-dialog-inline-size,
            26rem
          );
        }

        :where(.cui-alert-dialog[data-size="md"]) {
          --_cui-alert-dialog-inline-size: var(
            --cui-alert-dialog-inline-size,
            36rem
          );
        }

        :where(.cui-alert-dialog[data-size="lg"]) {
          --_cui-alert-dialog-inline-size: var(
            --cui-alert-dialog-inline-size,
            52rem
          );
        }
      }
    """


__all__ = [
    "CAlertDialog",
    "CAlertDialogActionSlotData",
    "CAlertDialogActivatorSlotData",
    "CAlertDialogCancelSlotData",
    "CAlertDialogDefaultSlotData",
    "CAlertDialogDescriptionSlotData",
    "CAlertDialogOpenChangeDetail",
    "CAlertDialogScroll",
    "CAlertDialogSize",
    "CAlertDialogTitleSlotData",
]
