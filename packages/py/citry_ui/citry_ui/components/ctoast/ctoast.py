"""Persistent Toast queue, viewport, timers, focus access, and announcers."""

# ruff: noqa: E501 - Citry template expressions stay on their owning attribute lines.

from __future__ import annotations

import json
import string
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import inline_translation_value, uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CToastIntent = Literal["neutral", "info", "success", "warn", "error"]
CToastPlacement = Literal[
    "block-start-start",
    "block-start-end",
    "block-end-start",
    "block-end-end",
]
CToastPriority = Literal["polite", "assertive"]

_INTENTS = ("neutral", "info", "success", "warn", "error")
_PLACEMENTS = (
    "block-start-start",
    "block-start-end",
    "block-end-start",
    "block-end-end",
)
_PRIORITIES = ("polite", "assertive")
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
        "aria-label",
        "aria-labelledby",
        "aria-live",
        "contenteditable",
        "data-citry-toast-initialized",
        "data-citry-ui-part",
        "data-paused",
        "data-placement",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


@dataclass(frozen=True, slots=True)
class CToastMessage:
    """One plain-text message supplied to a CToastRegion queue."""

    id: str
    title: str
    description: str | None = None
    intent: CToastIntent = "neutral"
    priority: CToastPriority = "polite"
    duration_ms: int | None = None
    action_label: str | None = None
    close_on_action: bool = True
    dismissible: bool = True


@dataclass(frozen=True, slots=True)
class CToastMessages:
    """Optional caller-owned patterns for text created by the Toast runtime."""

    dismiss_label: str | None = None
    action_announcement: str | None = None


def _plain_text(
    input_name: str,
    value: object,
    *,
    optional: bool = False,
    identity: bool = False,
) -> str | None:
    if value is None and optional:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"CToastRegion {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if type(plain) is not str:
        msg = f"CToastRegion could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if "\0" in plain:
        msg = f"CToastRegion {input_name} cannot contain U+0000."
        raise ValueError(msg)
    if not plain.strip():
        msg = f"CToastRegion {input_name} must contain non-whitespace text."
        raise ValueError(msg)
    if identity and any(character in "\t\n\f\r " for character in plain):
        msg = f"CToastRegion {input_name} cannot contain ASCII whitespace."
        raise ValueError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_text(input_name, value)
    if plain is None:  # pragma: no cover - nonoptional normalization rejects None
        msg = f"CToastRegion {input_name} must be a string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CToastRegion {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _duration(input_name: str, value: object, *, optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        expected = "an integer or None" if optional else "an integer"
        msg = f"CToastRegion {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    if raw != 0 and not 1000 <= raw <= 120_000:
        msg = f"CToastRegion {input_name} must be 0 or between 1000 and 120000 milliseconds."
        raise ValueError(msg)
    return raw


def _message_pattern(name: str, value: object, *, required: str) -> str:
    pattern = _plain_text(f"messages.{name}", value)
    assert pattern is not None  # noqa: S101 - nonoptional normalization
    fields: list[str] = []
    try:
        parsed = tuple(string.Formatter().parse(pattern))
    except ValueError as error:
        raise ValueError(f"CToastRegion messages.{name} is not a valid message pattern.") from error
    for _text, field, format_spec, conversion in parsed:
        if field is None:
            continue
        if field != required or format_spec or conversion:
            raise ValueError(f"CToastRegion messages.{name} contains an unsupported placeholder.")
        fields.append(field)
    if required not in fields:
        raise ValueError(f"CToastRegion messages.{name} must contain {{{required}}}.")
    return pattern


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CToastRegion attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(attrs: dict[str, object]) -> None:
    reject_owned_attrs(attrs, _ROOT_OWNED_ATTRS, "CToastRegion attrs")
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CToastRegion attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CToastRegion attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _ROOT_OWNED_ATTRS:
            msg = f"CToastRegion attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _normalize_message(message: object, index: int) -> dict[str, object]:
    if not isinstance(message, CToastMessage):
        msg = f"CToastRegion items[{index}] must be CToastMessage, got {message!r}."
        raise TypeError(msg)
    message_id = _plain_text(f"items[{index}].id", message.id, identity=True)
    title = _plain_text(f"items[{index}].title", message.title)
    description = _plain_text(f"items[{index}].description", message.description, optional=True)
    action_label = _plain_text(f"items[{index}].action_label", message.action_label, optional=True)
    intent = _plain_choice(f"items[{index}].intent", message.intent, _INTENTS)
    priority = _plain_choice(f"items[{index}].priority", message.priority, _PRIORITIES)
    duration_ms = _duration(f"items[{index}].duration_ms", message.duration_ms, optional=True)
    validate_boolean("CToastRegion", f"items[{index}].close_on_action", message.close_on_action)
    validate_boolean("CToastRegion", f"items[{index}].dismissible", message.dismissible)
    return {
        "id": message_id,
        "title": title,
        "description": description,
        "intent": intent,
        "priority": priority,
        "durationMs": duration_ms,
        "actionLabel": action_label,
        "closeOnAction": message.close_on_action,
        "dismissible": message.dismissible,
    }


class CToastRegion(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        items: Sequence[CToastMessage] = ()
        id: str | None = None
        label: str = "Notifications"
        messages: CToastMessages | None = None
        placement: CToastPlacement = "block-end-end"
        limit: int = 3
        duration_ms: int = 8000
        pause_on_hover: bool = True
        pause_on_focus: bool = True
        pause_on_hidden: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_html_id("CToastRegion", kwargs.id)
        if kwargs.id is not None and "\0" in kwargs.id:
            msg = "CToastRegion id cannot contain U+0000."
            raise ValueError(msg)
        catalog_label = uses_catalog_default(self, "label")
        label = _plain_text(
            "label",
            self.i18n.tr("citry-ui-toast-region") if catalog_label else kwargs.label,
        )
        if kwargs.messages is not None and not isinstance(kwargs.messages, CToastMessages):
            raise TypeError(f"CToastRegion messages must be CToastMessages or None, got {kwargs.messages!r}.")
        overrides = kwargs.messages or CToastMessages()
        catalog_dismiss = overrides.dismiss_label is None
        catalog_action_announcement = overrides.action_announcement is None
        dismiss_pattern = _message_pattern(
            "dismiss_label",
            overrides.dismiss_label
            if overrides.dismiss_label is not None
            else self.i18n.tr("citry-ui-toast-dismiss", title="{title}"),
            required="title",
        )
        action_pattern = _message_pattern(
            "action_announcement",
            overrides.action_announcement
            if overrides.action_announcement is not None
            else self.i18n.tr("citry-ui-toast-action-available", action_label="{action_label}"),
            required="action_label",
        )
        placement = _plain_choice("placement", kwargs.placement, _PLACEMENTS)
        if isinstance(kwargs.limit, bool) or not isinstance(kwargs.limit, int):
            msg = f"CToastRegion limit must be an integer, got {kwargs.limit!r}."
            raise TypeError(msg)
        if not 1 <= kwargs.limit <= 10:
            msg = "CToastRegion limit must be between 1 and 10."
            raise ValueError(msg)
        _duration("duration_ms", kwargs.duration_ms)
        validate_boolean("CToastRegion", "pause_on_hover", kwargs.pause_on_hover)
        validate_boolean("CToastRegion", "pause_on_focus", kwargs.pause_on_focus)
        validate_boolean("CToastRegion", "pause_on_hidden", kwargs.pause_on_hidden)
        if isinstance(kwargs.items, (str, bytes)) or not isinstance(kwargs.items, Sequence):
            msg = f"CToastRegion items must be a sequence of CToastMessage, got {kwargs.items!r}."
            raise TypeError(msg)
        normalized = tuple(_normalize_message(message, index) for index, message in enumerate(tuple(kwargs.items)))
        messages = tuple(
            {
                **message,
                "dismissLabel": self.i18n.tr(
                    "citry-ui-toast-dismiss",
                    title=inline_translation_value(cast("str", message["title"])),
                )
                if catalog_dismiss
                else dismiss_pattern.format(title=message["title"]),
                "actionAnnouncement": self.i18n.tr(
                    "citry-ui-toast-action-available",
                    action_label=inline_translation_value(cast("str", message["actionLabel"])),
                )
                if catalog_action_announcement and message["actionLabel"] is not None
                else action_pattern.format(action_label=message["actionLabel"])
                if message["actionLabel"] is not None
                else None,
            }
            for message in normalized
        )
        # Template HTML and the initializer consume one snapshot even when a
        # caller supplies a mutable or side-effecting public Sequence.
        self._toast_messages = messages
        self._toast_i18n_data = {
            "catalogDismiss": catalog_dismiss,
            "catalogActionAnnouncement": catalog_action_announcement,
            "dismissPattern": dismiss_pattern,
            "actionAnnouncementPattern": action_pattern,
        }
        ids = [message["id"] for message in messages]
        if len(ids) != len(set(ids)):
            msg = "CToastRegion items require unique canonical ids."
            raise ValueError(msg)
        attrs = _copy_attrs(kwargs.attrs)
        _validate_attrs(attrs)
        region_id = kwargs.id or f"cui-toast-region-{self.id}"
        visible_messages = tuple(
            {
                **message,
                "titleId": f"{region_id}-title-{index}",
                "descriptionId": f"{region_id}-description-{index}",
                "translationTitle": inline_translation_value(cast("str", message["title"])),
                "dismissValuesExpression": "{ title: "
                + json.dumps(
                    inline_translation_value(cast("str", message["title"])),
                    ensure_ascii=False,
                )
                + " }",
            }
            for index, message in enumerate(messages[: kwargs.limit])
        )
        return {
            "region_id": region_id,
            "label": label,
            "catalog_label": catalog_label,
            "catalog_dismiss": catalog_dismiss,
            "placement": placement,
            "visible_messages": visible_messages,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        messages = self._toast_messages
        return {
            "items": messages,
            "placement": _plain_choice("placement", kwargs.placement, _PLACEMENTS),
            "limit": kwargs.limit,
            "durationMs": kwargs.duration_ms,
            "pauseOnHover": kwargs.pause_on_hover,
            "pauseOnFocus": kwargs.pause_on_focus,
            "pauseOnHidden": kwargs.pause_on_hidden,
            **self._toast_i18n_data,
        }

    template = """
      <section
        class="cui-toast-region"
        c-id="region_id"
        c-bind="attrs"
        c-aria-label="tr('citry-ui-toast-region') if catalog_label else label"
        c-$c-tr:citry-ui-toast-region[aria-label]="True if catalog_label else None"
        c-data-placement="placement"
        role="region"
        tabindex="-1"
        data-citry-ui-part="region"
      >
        <div
          class="cui-toast-region__announcer"
          aria-live="polite"
          aria-atomic="true"
          data-citry-ui-part="announcer-polite"
        ></div>
        <div
          class="cui-toast-region__announcer"
          aria-live="assertive"
          aria-atomic="true"
          data-citry-ui-part="announcer-assertive"
        ></div>
        <div class="cui-toast-region__list" data-citry-toast-list>
          <c-for each="message in visible_messages">
            <div
              class="cui-toast"
              role="group"
              tabindex="0"
              c-aria-labelledby="message['titleId']"
              c-aria-describedby="message['descriptionId'] if message['description'] else None"
              c-data-intent="message['intent']"
              c-data-priority="message['priority']"
              c-data-citry-toast-id="message['id']"
              data-citry-ui-part="toast"
            >
              <div class="cui-toast__content" data-citry-ui-part="content">
                <div c-id="message['titleId']" class="cui-toast__title" data-citry-ui-part="title">
                  {{ message['title'] }}
                </div>
                <c-if cond="message['description']">
                  <div
                    c-id="message['descriptionId']"
                    class="cui-toast__description"
                    data-citry-ui-part="description"
                  >{{ message['description'] }}</div>
                </c-if>
              </div>
              <c-if cond="message['actionLabel'] or message['dismissible']">
                <div class="cui-toast__actions" data-citry-ui-part="actions">
                  <c-if cond="message['actionLabel']">
                    <button type="button" data-citry-toast-action data-citry-ui-part="action">
                      {{ message['actionLabel'] }}
                    </button>
                  </c-if>
                  <c-if cond="message['dismissible']">
                    <button
                      type="button"
                      c-aria-label="tr('citry-ui-toast-dismiss', title=message['translationTitle']) if catalog_dismiss else message['dismissLabel']"
                      c-$c-tr:citry-ui-toast-dismiss[aria-label]="message['dismissValuesExpression'] if catalog_dismiss else None"
                      data-citry-toast-dismiss
                      data-citry-ui-part="dismiss"
                    >&times;</button>
                  </c-if>
                </div>
              </c-if>
            </div>
          </c-for>
        </div>
      </section>
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-toast-region = Notifications
      # @param {str} $title - Toast title.
      citry-ui-toast-dismiss = Dismiss { $title }
      # @param {str} $action_label - Visible toast action label.
      citry-ui-toast-action-available = Action available: { $action_label }.
    """


__all__ = [
    "CToastIntent",
    "CToastMessage",
    "CToastMessages",
    "CToastPlacement",
    "CToastPriority",
    "CToastRegion",
]
