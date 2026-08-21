"""Styled persistent Alert component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean
from citry_ui.components.cicon import CIconName  # noqa: TC001 - runtime type hints
from citry_ui.components.cicon.cicon import _resolve_registered_icon

if TYPE_CHECKING:
    from citry_ui.components.cicon.cicon import _RegisteredIconGlyph

CAlertIntent = Literal["info", "success", "warn", "error"]
CAlertVariant = Literal["soft", "solid", "outline"]
CAlertSize = Literal["sm", "md", "lg"]
CAlertAnnounce = Literal["off", "polite", "assertive"]

_INTENTS = ("info", "success", "warn", "error")
_VARIANTS = ("soft", "solid", "outline")
_SIZES = ("sm", "md", "lg")
_ANNOUNCEMENTS = ("off", "polite", "assertive")
_AUTOMATIC_ICON_NAMES = {
    "info": "info",
    "success": "success",
    "warn": "warn",
    "error": "danger",
}
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
        "x-teleport",
        "x-text",
    }
)
_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-atomic",
        "aria-hidden",
        "aria-live",
        "contenteditable",
        "data-announce",
        "data-citry-alert-initialized",
        "data-citry-ui-part",
        "data-icon",
        "data-intent",
        "data-size",
        "data-variant",
        "role",
        "tabindex",
    }
)
_ACTIONS_OWNED_ATTRS = frozenset(
    {
        "aria-atomic",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-live",
        "contenteditable",
        "data-citry-ui-part",
        "role",
        "tabindex",
    }
)


class CAlertTitleSlotData:
    pass


class CAlertDefaultSlotData:
    pass


class CAlertActionsSlotData:
    pass


@dataclass(frozen=True, slots=True)
class _AlertGlyph:
    intent: str
    icon: _RegisteredIconGlyph


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CAlert {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CAlert could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        msg = f"CAlert {input_name} must be a string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CAlert {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _plain_actions_label(value: object) -> str | None:
    plain = _plain_optional_string("actions_label", value)
    if plain is None:
        return None
    normalized = plain.replace("\r\n", "\n").replace("\r", "\n")
    if "\0" in normalized:
        msg = "CAlert actions_label cannot contain U+0000."
        raise ValueError(msg)
    if not normalized.strip():
        msg = "CAlert actions_label must contain non-whitespace text when supplied."
        raise ValueError(msg)
    return normalized


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CAlert {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(
    input_name: str,
    attrs: dict[str, object],
    owned: frozenset[str],
) -> None:
    component_name = f"CAlert {input_name}"
    reject_owned_attrs(attrs, owned, component_name)
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"{component_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


class CAlert(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        intent: CAlertIntent = "info"
        variant: CAlertVariant = "soft"
        size: CAlertSize = "md"
        announce: CAlertAnnounce = "off"
        icon: bool = True
        icon_name: CIconName | None = None
        actions_label: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        actions_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CAlertTitleSlotData] | None = None
        default: SlotInput[CAlertDefaultSlotData] | None = None
        actions: SlotInput[CAlertActionsSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        intent = _plain_choice("intent", kwargs.intent, _INTENTS)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        announce = _plain_choice("announce", kwargs.announce, _ANNOUNCEMENTS)
        validate_boolean("CAlert", "icon", kwargs.icon)
        actions_label = _plain_actions_label(kwargs.actions_label)

        fixed_icon = (
            None if kwargs.icon_name is None else _resolve_registered_icon(kwargs.icon_name, "CAlert icon_name")
        )
        automatic_icons = (
            tuple(
                _AlertGlyph(
                    intent=automatic_intent,
                    icon=_resolve_registered_icon(icon_name, "CAlert automatic icon"),
                )
                for automatic_intent, icon_name in _AUTOMATIC_ICON_NAMES.items()
            )
            if fixed_icon is None
            else ()
        )

        has_title = "title" in self.raw_slots
        has_message = "default" in self.raw_slots
        has_actions = "actions" in self.raw_slots
        if not has_title and not has_message:
            msg = "CAlert requires a title or default message slot."
            raise ValueError(msg)

        attrs = _copy_attrs("attrs", kwargs.attrs)
        actions_attrs = _copy_attrs("actions_attrs", kwargs.actions_attrs)
        _validate_attrs("attrs", attrs, _ROOT_OWNED_ATTRS)
        _validate_attrs("actions_attrs", actions_attrs, _ACTIONS_OWNED_ATTRS)
        if actions_attrs and not has_actions:
            msg = "CAlert actions_attrs requires the actions slot."
            raise ValueError(msg)
        if actions_label is not None and not has_actions:
            msg = "CAlert actions_label requires the actions slot."
            raise ValueError(msg)

        role = {"off": None, "polite": "status", "assertive": "alert"}[announce]
        return {
            "intent": intent,
            "variant": variant,
            "size": size,
            "announce": announce,
            "icon": bool(kwargs.icon),
            "fixed_icon": fixed_icon,
            "automatic_icons": automatic_icons,
            "role": role,
            "actions_label": actions_label,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "actions_attrs": actions_attrs,
            "has_title": has_title,
            "has_message": has_message,
            "has_actions": has_actions,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        validate_boolean("CAlert", "icon", kwargs.icon)
        return {
            "intent": _plain_choice("intent", kwargs.intent, _INTENTS),
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "announce": _plain_choice("announce", kwargs.announce, _ANNOUNCEMENTS),
            "icon": bool(kwargs.icon),
        }

    template = """
      <div
        class="cui-alert"
        c-data-intent="intent"
        c-data-variant="variant"
        c-data-size="size"
        c-data-announce="announce"
        c-data-icon="icon"
        c-bind="attrs"
        data-citry-ui-part="alert"
      >
        <div
          class="cui-alert__indicator"
          aria-hidden="true"
          c-hidden="not icon"
          data-citry-ui-part="indicator"
        >
          <svg
            class="cui-alert__icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            focusable="false"
            aria-hidden="true"
          >
            <c-if cond="fixed_icon is not None">
              <g
                c-class="[
                  'cui-alert__glyph',
                  {'cui-alert__glyph--logical': fixed_icon.logical},
                ]"
              >
                {{ fixed_icon.markup }}
              </g>
            </c-if>
            <c-else>
              <g
                c-for="glyph in automatic_icons"
                class="cui-alert__glyph"
                c-data-cui-alert-intent="glyph.intent"
                c-data-cui-alert-hidden="glyph.intent != intent"
              >
                {{ glyph.icon.markup }}
              </g>
            </c-else>
          </svg>
        </div>
        <div
          class="cui-alert__content"
          c-role="role"
          data-citry-ui-part="content"
        >
          <c-if cond="has_title">
            <div
              class="cui-alert__title"
              data-citry-ui-part="title"
            >
              <c-slot name="title" />
            </div>
          </c-if>
          <c-if cond="has_message">
            <div
              class="cui-alert__message"
              data-citry-ui-part="message"
            >
              <c-slot />
            </div>
          </c-if>
        </div>
        <c-if cond="has_actions">
          <div
            class="cui-alert__actions"
            c-role="'group' if actions_label is not None else None"
            c-aria-label="actions_label"
            c-bind="actions_attrs"
            data-citry-ui-part="actions"
          >
            <c-slot name="actions" />
          </div>
        </c-if>
      </div>
    """

    js = """
      $component({
        props: {
          intent: {},
          variant: {},
          size: {},
          announce: {},
          icon: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const indicator = root.querySelector('[data-citry-ui-part="indicator"]');
          const content = root.querySelector('[data-citry-ui-part="content"]');
          const automaticGlyphs = Array.from(
            indicator.querySelectorAll("[data-cui-alert-intent]"),
          );
          const allowedValues = {
            intent: ["info", "success", "warn", "error"],
            variant: ["soft", "solid", "outline"],
            size: ["sm", "md", "lg"],
            announce: ["off", "polite", "assertive"],
          };
          const invalidEpisodes = new Set();

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            const describedValue = describeValue(value);
            console.error(
              `[citry-ui] CAlert ${name} received invalid client value ${describedValue}; `
                + "using the server-rendered fallback.",
              root,
            );
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
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const setData = (name, value) => {
            if (root.dataset[name] !== value) {
              root.dataset[name] = value;
            }
          };
          const setRole = (announce) => {
            const role = announce === "polite"
              ? "status"
              : announce === "assertive"
                ? "alert"
                : null;
            if (role === null) {
              content.removeAttribute("role");
            } else if (content.getAttribute("role") !== role) {
              content.setAttribute("role", role);
            }
          };

          effect(() => {
            const next = {
              intent: resolveChoice("intent"),
              variant: resolveChoice("variant"),
              size: resolveChoice("size"),
              announce: resolveChoice("announce"),
              icon: resolveBoolean("icon"),
            };
            setData("intent", next.intent);
            setData("variant", next.variant);
            setData("size", next.size);
            setData("announce", next.announce);
            root.toggleAttribute("data-icon", next.icon);
            if (indicator.hidden === next.icon) {
              indicator.hidden = !next.icon;
            }
            for (const glyph of automaticGlyphs) {
              const hidden = glyph.dataset.cuiAlertIntent !== next.intent;
              if (glyph.hasAttribute("data-cui-alert-hidden") !== hidden) {
                glyph.toggleAttribute("data-cui-alert-hidden", hidden);
              }
            }
            setRole(next.announce);
          });
          root.setAttribute("data-citry-alert-initialized", "");

          return () => {
            root.removeAttribute("data-citry-alert-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = [
    "CAlert",
    "CAlertActionsSlotData",
    "CAlertAnnounce",
    "CAlertDefaultSlotData",
    "CAlertIntent",
    "CAlertSize",
    "CAlertTitleSlotData",
    "CAlertVariant",
]
