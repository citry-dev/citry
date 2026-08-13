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

    js = r"""
      const toastRegistryKey = Symbol.for("citry-ui:toast-region-runtime");
      const toastRegistry = globalThis[toastRegistryKey] ?? new WeakMap();
      globalThis[toastRegistryKey] = toastRegistry;

      $component({
        props: {
          items: {}, placement: {}, limit: {}, durationMs: {}, pauseOnHover: {},
          pauseOnFocus: {}, pauseOnHidden: {}, onDismiss: {}, onAction: {},
        },
        init: ({ els, data, props, effect, i18n }) => {
          const region = els[0];
          const scope = region.getRootNode();
          const ownerDocument = region.ownerDocument;
          const existing = toastRegistry.get(scope);
          if (existing?.isConnected && existing !== region) {
            console.error("[citry-ui] CToastRegion permits only one initialized Region per root.", region);
            region.inert = true;
            return;
          }
          toastRegistry.set(scope, region);

          const list = region.querySelector("[data-citry-toast-list]");
          const polite = region.querySelector('[data-citry-ui-part="announcer-polite"]');
          const assertive = region.querySelector('[data-citry-ui-part="announcer-assertive"]');
          if (!list || !polite || !assertive) {
            console.error("[citry-ui] CToastRegion could not resolve its owned anatomy.", region);
            toastRegistry.delete(scope);
            return;
          }
          // A retained Region can be reinitialized while the previous
          // generation's short live-region dwell is still active. Its cleanup
          // cancels that generation's clear task, so normalize inherited text
          // before rebuilding the queue rather than leaving it live forever.
          polite.textContent = "";
          assertive.textContent = "";

          const placements = [
            "block-start-start", "block-start-end", "block-end-start", "block-end-end",
          ];
          const intents = ["neutral", "info", "success", "warn", "error"];
          const priorities = ["polite", "assertive"];
          const runtimeState = region.__citryUiToastRuntime ?? {
            entries: [], suppressedIds: [], timers: {}, focusReturn: null,
            focusedId: null, focusedPart: null, nodeCounter: 0,
            announcedFingerprints: new Map(),
          };
          region.__citryUiToastRuntime = runtimeState;
          const invalidEpisodes = new Set();
          const suppressedIds = new Set(runtimeState.suppressedIds ?? []);
          const announcedFingerprints = runtimeState.announcedFingerprints instanceof Map
            ? new Map(runtimeState.announcedFingerprints)
            : new Map();
          const nodes = new Map();
          const timerRecords = new Map(
            Object.entries(runtimeState.timers ?? {}).map(([id, record]) => [
              id, { remaining: record.remaining, started: 0, handle: null },
            ]),
          );
          const taskHandles = new Set();
          const modalObserver = new MutationObserver((records) => {
            const relevant = records.some((record) => record.type === "attributes"
              || [...record.addedNodes, ...record.removedNodes].some((node) => node instanceof Element
                && (node.matches("dialog") || node.querySelector("dialog") || node.shadowRoot)));
            if (relevant) refreshModalState();
          });
          let entries = (runtimeState.entries ?? []).map((entry) => ({
            message: { ...entry.message },
            announcePending: announcedFingerprints.get(entry.message.id)
              !== entry.message.fingerprint,
          }));
          let config = {
            placement: data.placement,
            limit: data.limit,
            durationMs: data.durationMs,
            pauseOnHover: data.pauseOnHover,
            pauseOnFocus: data.pauseOnFocus,
            pauseOnHidden: data.pauseOnHidden,
          };
          let onDismiss = null;
          let onAction = null;
          let hovering = false;
          let focusWithin = false;
          let modalPaused = false;
          let focusReturn = runtimeState.focusReturn?.isConnected ? runtimeState.focusReturn : null;
          let pendingFocusId = runtimeState.focusedId ?? null;
          let pendingFocusPart = runtimeState.focusedPart ?? null;
          let generation = 0;
          let disposed = false;
          let announcementQueue = [];
          let announcementRunning = false;
          let nodeCounter = runtimeState.nodeCounter ?? 0;

          const composedParent = (node) => {
            if (node?.parentNode) return node.parentNode;
            const root = node?.getRootNode?.();
            return root instanceof ShadowRoot ? root.host : null;
          };
          const composedContains = (ancestor, node) => {
            for (let current = node; current; current = composedParent(current)) {
              if (current === ancestor) return true;
            }
            return false;
          };
          const deepActiveElement = () => {
            let active = ownerDocument.activeElement;
            while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
            return active;
          };
          const isFocusable = (element) => element instanceof HTMLElement
            && element.isConnected
            && !element.hidden
            && !element.matches(":disabled,[inert]")
            && !element.closest("[inert]")
            && element.getClientRects().length > 0;
          const focusBody = () => {
            const body = ownerDocument.body;
            if (!body) return;
            const hadTabIndex = body.hasAttribute("tabindex");
            const previousTabIndex = body.getAttribute("tabindex");
            if (!hadTabIndex) body.tabIndex = -1;
            body.focus({ preventScroll: true });
            if (!hadTabIndex) body.removeAttribute("tabindex");
            else if (previousTabIndex !== null) body.setAttribute("tabindex", previousTabIndex);
          };
          const publicMessage = (message) => ({
            id: message.id,
            title: message.title,
            description: message.description,
            intent: message.intent,
            priority: message.priority,
            durationMs: message.durationMs,
            actionLabel: message.actionLabel,
            closeOnAction: message.closeOnAction,
            dismissible: message.dismissible,
          });
          const persistRuntimeState = () => {
            const now = performance.now();
            const active = deepActiveElement();
            const focusedRoot = active?.closest?.("[data-citry-toast-id]");
            runtimeState.entries = entries.map((entry) => ({
              message: { ...entry.message, fingerprint: entry.message.fingerprint },
            }));
            runtimeState.suppressedIds = [...suppressedIds];
            runtimeState.announcedFingerprints = new Map(announcedFingerprints);
            runtimeState.timers = Object.fromEntries(
              [...timerRecords].map(([id, record]) => [id, {
                remaining: record.handle === null
                  ? record.remaining
                  : Math.max(0, record.remaining - (now - record.started)),
              }]),
            );
            runtimeState.focusReturn = focusReturn?.isConnected ? focusReturn : null;
            runtimeState.focusedId = focusedRoot?.dataset.citryToastId ?? null;
            runtimeState.focusedPart = active?.matches?.("[data-citry-toast-action]")
              ? "action"
              : active?.matches?.("[data-citry-toast-dismiss]") ? "dismiss" : "toast";
            runtimeState.nodeCounter = nodeCounter;
          };
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            let shown;
            try { shown = JSON.stringify(value) ?? String(value); } catch { shown = String(value); }
            console.error(
              `[citry-ui] CToastRegion ${name} received invalid client value ${shown}; retaining its fallback.`,
              region,
            );
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") { invalidEpisodes.delete(name); return value; }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveInteger = (name, fallback, valid) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (Number.isInteger(value) && valid(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveCallback = (name) => {
            const value = props[name];
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete(name);
              return value ?? null;
            }
            reportInvalid(name, value);
            return null;
          };
          const text = (name, value, { optional = false, identity = false } = {}) => {
            if (value === null && optional) return null;
            if (typeof value !== "string") throw new TypeError(`${name} must be a string.`);
            const normalized = value.replace(/\r\n?/g, "\n");
            if (normalized.includes("\0")) throw new TypeError(`${name} cannot contain U+0000.`);
            if (!normalized.trim()) throw new TypeError(`${name} cannot be blank.`);
            if (identity && /[\t\n\f\r ]/.test(normalized)) {
              throw new TypeError(`${name} cannot contain ASCII whitespace.`);
            }
            return normalized;
          };
          const formatPattern = (pattern, name, value) => pattern.split(`{${name}}`).join(value);
          const inlineTranslationValue = (value) => value
            .replace(/[\n\r\u001c-\u001e\u0085\u2029]/gu, " ")
            .replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/gu, "");
          const normalizeMessage = (raw, index) => {
            if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
              throw new TypeError(`items[${index}] must be an object.`);
            }
            const duration = raw.durationMs === undefined || raw.durationMs === null
              ? null : raw.durationMs;
            if (duration !== null && (!Number.isInteger(duration)
              || (duration !== 0 && (duration < 1000 || duration > 120000)))) {
              throw new TypeError(`items[${index}].durationMs is invalid.`);
            }
            const intent = raw.intent ?? "neutral";
            const priority = raw.priority ?? "polite";
            if (!intents.includes(intent) || !priorities.includes(priority)) {
              throw new TypeError(`items[${index}] intent or priority is invalid.`);
            }
            const closeOnAction = raw.closeOnAction ?? true;
            const dismissible = raw.dismissible ?? true;
            if (typeof closeOnAction !== "boolean" || typeof dismissible !== "boolean") {
              throw new TypeError(`items[${index}] Boolean field is invalid.`);
            }
            const value = {
              id: text(`items[${index}].id`, raw.id, { identity: true }),
              title: text(`items[${index}].title`, raw.title),
              description: raw.description === undefined
                ? null : text(`items[${index}].description`, raw.description, { optional: true }),
              intent,
              priority,
              durationMs: duration,
              actionLabel: raw.actionLabel === undefined
                ? null : text(`items[${index}].actionLabel`, raw.actionLabel, { optional: true }),
              closeOnAction,
              dismissible,
              dismissLabel: raw.dismissLabel === undefined
                ? null : text(`items[${index}].dismissLabel`, raw.dismissLabel, { optional: true }),
              actionAnnouncement: raw.actionAnnouncement === undefined
                ? null : text(
                    `items[${index}].actionAnnouncement`,
                    raw.actionAnnouncement,
                    { optional: true },
                  ),
            };
            value.fingerprint = JSON.stringify(value);
            return value;
          };
          const normalizeItems = (raw) => {
            if (!Array.isArray(raw)) throw new TypeError("items must be an Array.");
            const seen = new Set();
            const result = raw.map((item, index) => {
              const normalized = normalizeMessage(item, index);
              if (seen.has(normalized.id)) throw new TypeError("items require unique ids.");
              seen.add(normalized.id);
              return normalized;
            });
            invalidEpisodes.delete("items");
            return result;
          };
          const activeEntries = () => entries.slice(0, config.limit);
          const effectiveDuration = (entry) => entry.message.durationMs ?? config.durationMs;
          const timersPaused = () => modalPaused
            || (config.pauseOnHover && hovering)
            || (config.pauseOnFocus && focusWithin)
            || (config.pauseOnHidden && ownerDocument.hidden);
          const stopTimer = (entry) => {
            const record = timerRecords.get(entry.message.id);
            if (!record) return;
            if (record.handle !== null) {
              clearTimeout(record.handle);
              taskHandles.delete(record.handle);
              record.remaining = Math.max(0, record.remaining - (performance.now() - record.started));
              record.handle = null;
            }
          };
          const dismiss = (entry, reason, source) => {
            if (disposed || !entries.includes(entry)) return;
            const active = deepActiveElement();
            const node = nodes.get(entry.message.id)?.root;
            const focused = node && composedContains(node, active);
            const oldActive = activeEntries();
            const oldIndex = oldActive.indexOf(entry);
            suppressedIds.add(entry.message.id);
            entries = entries.filter((candidate) => candidate !== entry);
            announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
            stopTimer(entry);
            timerRecords.delete(entry.message.id);
            syncVisible();
            if (focused && (active === deepActiveElement() || !isFocusable(deepActiveElement()))) {
              const survivors = activeEntries();
              const next = survivors[oldIndex] ?? survivors[oldIndex - 1];
              if (next) nodes.get(next.message.id)?.root.focus({ preventScroll: true });
              else if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
              else focusBody();
            }
            onDismiss?.(entry.message.id, { reason, source, message: publicMessage(entry.message) });
          };
          const scheduleTimer = (entry) => {
            if (!activeEntries().includes(entry) || timersPaused()) return;
            const duration = effectiveDuration(entry);
            if (duration === 0) return;
            let record = timerRecords.get(entry.message.id);
            if (!record) {
              record = { remaining: duration, started: 0, handle: null };
              timerRecords.set(entry.message.id, record);
            }
            if (record.handle !== null) return;
            if (record.remaining <= 0) { dismiss(entry, "timeout", region); return; }
            record.started = performance.now();
            record.handle = setTimeout(() => {
              taskHandles.delete(record.handle);
              record.handle = null;
              record.remaining = 0;
              dismiss(entry, "timeout", region);
            }, record.remaining);
            taskHandles.add(record.handle);
          };
          const syncTimers = () => {
            const active = new Set(activeEntries());
            for (const entry of entries) {
              if (!active.has(entry) || timersPaused()) stopTimer(entry);
              else scheduleTimer(entry);
            }
          };
          const actionAnnouncement = (message) => {
            if (!message.actionLabel) return null;
            if (data.catalogActionAnnouncement) {
              return i18n
                ? i18n.tr("citry-ui-toast-action-available", {
                    action_label: inlineTranslationValue(message.actionLabel),
                  })
                : formatPattern(
                    data.actionAnnouncementPattern,
                    "action_label",
                    inlineTranslationValue(message.actionLabel),
                  );
            }
            return formatPattern(data.actionAnnouncementPattern, "action_label", message.actionLabel);
          };
          const announcementText = (message) => [
            message.title,
            message.description,
            actionAnnouncement(message),
          ].filter(Boolean).join(" ");
          const drainAnnouncements = () => {
            if (announcementRunning || disposed || modalPaused
              || (config.pauseOnHidden && ownerDocument.hidden) || announcementQueue.length === 0) return;
            announcementRunning = true;
            const item = announcementQueue.shift();
            const target = item.priority === "assertive" ? assertive : polite;
            target.textContent = "";
            const token = generation;
            const commitHandle = setTimeout(() => {
              taskHandles.delete(commitHandle);
              const current = entries.find((entry) => entry.message.id === item.id);
              if (disposed || token !== generation
                || !current || current.message.fingerprint !== item.fingerprint) {
                announcementRunning = false;
                drainAnnouncements();
                return;
              }
              if (modalPaused || (config.pauseOnHidden && ownerDocument.hidden)) {
                announcementQueue.unshift(item);
                announcementRunning = false;
                return;
              }
              target.textContent = item.text;
              announcedFingerprints.set(item.id, item.fingerprint);
              persistRuntimeState();
              const nextHandle = setTimeout(() => {
                taskHandles.delete(nextHandle);
                target.textContent = "";
                announcementRunning = false;
                drainAnnouncements();
              }, 250);
              taskHandles.add(nextHandle);
            }, 20);
            taskHandles.add(commitHandle);
          };
          const queueAnnouncement = (entry) => {
            announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
            announcementQueue.push({
              id: entry.message.id,
              fingerprint: entry.message.fingerprint,
              priority: entry.message.priority,
              text: announcementText(entry.message),
            });
            drainAnnouncements();
          };
          const createNode = (entry) => {
            nodeCounter += 1;
            const root = ownerDocument.createElement("div");
            const content = ownerDocument.createElement("div");
            const title = ownerDocument.createElement("div");
            const description = ownerDocument.createElement("div");
            const actions = ownerDocument.createElement("div");
            const action = ownerDocument.createElement("button");
            const dismissButton = ownerDocument.createElement("button");
            const titleId = `${region.id}-title-client-${nodeCounter}`;
            const descriptionId = `${region.id}-description-client-${nodeCounter}`;
            root.className = "cui-toast";
            root.setAttribute("role", "group");
            root.tabIndex = 0;
            root.setAttribute("aria-labelledby", titleId);
            root.setAttribute("data-citry-ui-part", "toast");
            root.setAttribute("data-citry-toast-id", entry.message.id);
            content.className = "cui-toast__content";
            content.setAttribute("data-citry-ui-part", "content");
            title.id = titleId;
            title.className = "cui-toast__title";
            title.setAttribute("data-citry-ui-part", "title");
            description.id = descriptionId;
            description.className = "cui-toast__description";
            description.setAttribute("data-citry-ui-part", "description");
            actions.className = "cui-toast__actions";
            actions.setAttribute("data-citry-ui-part", "actions");
            action.type = "button";
            action.setAttribute("data-citry-toast-action", "");
            action.setAttribute("data-citry-ui-part", "action");
            dismissButton.type = "button";
            dismissButton.textContent = "\u00d7";
            dismissButton.setAttribute("data-citry-toast-dismiss", "");
            dismissButton.setAttribute("data-citry-ui-part", "dismiss");
            content.append(title, description);
            actions.append(action, dismissButton);
            root.append(content, actions);
            const value = {
              root, title, description, actions, action, dismissButton, descriptionId,
              dismissBinding: null,
            };
            nodes.set(entry.message.id, value);
            return value;
          };
          const updateNode = (entry) => {
            const value = nodes.get(entry.message.id) ?? createNode(entry);
            const message = entry.message;
            value.root.dataset.intent = message.intent;
            value.root.dataset.priority = message.priority;
            value.title.textContent = message.title;
            value.description.textContent = message.description ?? "";
            value.description.hidden = message.description === null;
            if (message.description) value.root.setAttribute("aria-describedby", value.descriptionId);
            else value.root.removeAttribute("aria-describedby");
            value.action.textContent = message.actionLabel ?? "";
            value.action.hidden = message.actionLabel === null;
            value.dismissButton.hidden = !message.dismissible;
            if (data.catalogDismiss && i18n) {
              if (value.dismissBinding === null) {
                value.dismissBinding = i18n.bind({
                  message: "citry-ui-toast-dismiss",
                  values: () => ({title: inlineTranslationValue(entry.message.title)}),
                  onChange: (text) => value.dismissButton.setAttribute("aria-label", text),
                });
              } else {
                value.dismissBinding.refresh();
              }
            } else if (data.catalogDismiss) {
              value.dismissButton.setAttribute(
                "aria-label",
                formatPattern(
                  data.dismissPattern,
                  "title",
                  inlineTranslationValue(message.title),
                ),
              );
            } else {
              value.dismissButton.setAttribute(
                "aria-label",
                formatPattern(data.dismissPattern, "title", inlineTranslationValue(message.title)),
              );
            }
            value.actions.hidden = message.actionLabel === null && !message.dismissible;
            return value;
          };
          const recoverFocusAfterSync = (oldActive, focusedId) => {
            if (!focusedId || nodes.has(focusedId)) return;
            const oldIndex = oldActive.findIndex((entry) => entry.message.id === focusedId);
            const candidates = activeEntries();
            const nextId = (candidates[oldIndex] ?? candidates[oldIndex - 1])?.message.id ?? null;
            const token = generation;
            const handle = setTimeout(() => {
              taskHandles.delete(handle);
              if (disposed || token !== generation) return;
              const active = deepActiveElement();
              if (active !== ownerDocument.body && isFocusable(active)) return;
              const next = nextId ? nodes.get(nextId)?.root : null;
              if (isFocusable(next)) next.focus({ preventScroll: true });
              else if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
              else focusBody();
            }, 0);
            taskHandles.add(handle);
          };
          function syncVisible() {
            const oldActive = [...nodes.keys()];
            const activeElement = deepActiveElement();
            const focusedId = oldActive.find((id) => composedContains(nodes.get(id).root, activeElement));
            const active = activeEntries();
            const activeIds = new Set(active.map((entry) => entry.message.id));
            for (const [id, value] of nodes) {
              if (activeIds.has(id)) continue;
              value.dismissBinding?.dispose();
              value.root.remove();
              nodes.delete(id);
            }
            for (const entry of active) {
              const value = updateNode(entry);
              list.append(value.root);
              if (entry.announcePending) {
                entry.announcePending = false;
                queueAnnouncement(entry);
              }
            }
            recoverFocusAfterSync(
              oldActive.map((id) => ({ message: { id } })),
              focusedId,
            );
            if (pendingFocusId && nodes.has(pendingFocusId)) {
              const pendingId = pendingFocusId;
              const pendingPart = pendingFocusPart;
              pendingFocusId = null;
              pendingFocusPart = null;
              const token = generation;
              const handle = setTimeout(() => {
                taskHandles.delete(handle);
                if (disposed || token !== generation) return;
                const value = nodes.get(pendingId);
                if (!value) return;
                const target = pendingPart === "action" ? value.action
                  : pendingPart === "dismiss" ? value.dismissButton : value.root;
                if (isFocusable(target)) target.focus({ preventScroll: true });
              }, 0);
              taskHandles.add(handle);
            }
            syncTimers();
            persistRuntimeState();
          }
          const reconcileItems = (incoming) => {
            const previous = new Map(entries.map((entry) => [entry.message.id, entry]));
            const incomingIds = new Set(incoming.map((message) => message.id));
            for (const id of [...suppressedIds]) {
              if (incomingIds.has(id)) continue;
              suppressedIds.delete(id);
              announcedFingerprints.delete(id);
            }
            const next = [];
            for (const message of incoming) {
              if (suppressedIds.has(message.id)) continue;
              const retained = previous.get(message.id);
              if (retained && retained.message.fingerprint === message.fingerprint) {
                next.push(retained);
                continue;
              }
              if (retained) {
                stopTimer(retained);
                timerRecords.delete(message.id);
                retained.message = message;
                retained.announcePending = true;
                next.push(retained);
              } else {
                next.push({
                  message,
                  announcePending: announcedFingerprints.get(message.id) !== message.fingerprint,
                });
              }
            }
            for (const entry of entries) {
              if (next.includes(entry)) continue;
              stopTimer(entry);
              timerRecords.delete(entry.message.id);
              announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
              if (!incomingIds.has(entry.message.id)) announcedFingerprints.delete(entry.message.id);
            }
            entries = next;
            syncVisible();
          };
          const openRoots = () => {
            const roots = [ownerDocument];
            for (let index = 0; index < roots.length; index += 1) {
              for (const element of roots[index].querySelectorAll("*")) {
                if (element.shadowRoot) roots.push(element.shadowRoot);
              }
            }
            return roots;
          };
          const observeModalRoots = () => {
            modalObserver.disconnect();
            for (const root of openRoots()) {
              modalObserver.observe(root, {
                subtree: true, childList: true, attributes: true, attributeFilter: ["open"],
              });
            }
          };
          function refreshModalState() {
            observeModalRoots();
            const next = openRoots().flatMap((root) => [...root.querySelectorAll("dialog:modal")])
              .some((modal) => !composedContains(modal, region));
            if (next === modalPaused) return;
            modalPaused = next;
            region.toggleAttribute("data-citry-toast-modal-paused", modalPaused);
            region.inert = modalPaused;
            syncPausedState();
            if (!modalPaused) drainAnnouncements();
          }
          const syncPausedState = () => {
            region.toggleAttribute("data-paused", timersPaused());
            syncTimers();
            persistRuntimeState();
          };
          const onPointerEnter = () => { hovering = true; syncPausedState(); };
          const onPointerLeave = () => { hovering = false; syncPausedState(); };
          const onFocusIn = () => { focusWithin = true; syncPausedState(); persistRuntimeState(); };
          const onFocusOut = () => {
            queueMicrotask(() => {
              if (disposed) return;
              focusWithin = composedContains(region, deepActiveElement());
              syncPausedState();
              persistRuntimeState();
            });
          };
          const onVisibilityChange = () => { syncPausedState(); if (!ownerDocument.hidden) drainAnnouncements(); };
          const onClick = (event) => {
            const toast = event.target.closest?.("[data-citry-toast-id]");
            if (!toast || !composedContains(region, toast)) return;
            const entry = entries.find((candidate) => candidate.message.id === toast.dataset.citryToastId);
            if (!entry) return;
            if (event.target.closest("[data-citry-toast-dismiss]")) {
              dismiss(entry, "dismiss", event.target);
              return;
            }
            if (!event.target.closest("[data-citry-toast-action]")) return;
            const token = generation;
            onAction?.(entry.message.id, { source: event.target, message: publicMessage(entry.message) });
            if (disposed || token !== generation || !region.isConnected) return;
            if (entry.message.closeOnAction) dismiss(entry, "action", event.target);
          };
          const onKeyDown = (event) => {
            if (event.defaultPrevented || event.key !== "F6" || event.altKey || event.ctrlKey || event.metaKey) return;
            const active = deepActiveElement();
            if (composedContains(region, active)) {
              event.preventDefault();
              if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
              else focusBody();
              persistRuntimeState();
              return;
            }
            const first = activeEntries()[0];
            const node = first && nodes.get(first.message.id)?.root;
            if (!node || modalPaused) return;
            event.preventDefault();
            focusReturn = active;
            node.focus({ preventScroll: true });
            persistRuntimeState();
          };

          list.replaceChildren();
          region.addEventListener("pointerenter", onPointerEnter);
          region.addEventListener("pointerleave", onPointerLeave);
          region.addEventListener("focusin", onFocusIn);
          region.addEventListener("focusout", onFocusOut);
          region.addEventListener("click", onClick);
          scope.addEventListener("keydown", onKeyDown, true);
          ownerDocument.addEventListener("visibilitychange", onVisibilityChange);
          refreshModalState();

          effect(() => {
            const placement = props.placement === undefined ? data.placement : props.placement;
            if (placements.includes(placement)) {
              config.placement = placement;
              invalidEpisodes.delete("placement");
            } else reportInvalid("placement", placement);
            config.limit = resolveInteger("limit", data.limit, (value) => value >= 1 && value <= 10);
            const nextDuration = resolveInteger(
              "durationMs", data.durationMs,
              (value) => value === 0 || (value >= 1000 && value <= 120000),
            );
            if (nextDuration !== config.durationMs) {
              config.durationMs = nextDuration;
              for (const entry of entries) {
                if (entry.message.durationMs !== null) continue;
                stopTimer(entry);
                timerRecords.delete(entry.message.id);
              }
            }
            config.pauseOnHover = resolveBoolean("pauseOnHover");
            config.pauseOnFocus = resolveBoolean("pauseOnFocus");
            config.pauseOnHidden = resolveBoolean("pauseOnHidden");
            onDismiss = resolveCallback("onDismiss");
            onAction = resolveCallback("onAction");
            region.dataset.placement = config.placement;
            const supplied = props.items === undefined ? data.items : props.items;
            try { reconcileItems(normalizeItems(supplied)); }
            catch (error) { reportInvalid("items", supplied); }
            syncPausedState();
            persistRuntimeState();
          });
          region.setAttribute("data-citry-toast-initialized", "");

          return () => {
            for (const entry of entries) stopTimer(entry);
            persistRuntimeState();
            disposed = true;
            generation += 1;
            modalObserver.disconnect();
            for (const handle of taskHandles) clearTimeout(handle);
            taskHandles.clear();
            timerRecords.clear();
            for (const value of nodes.values()) value.dismissBinding?.dispose();
            region.removeEventListener("pointerenter", onPointerEnter);
            region.removeEventListener("pointerleave", onPointerLeave);
            region.removeEventListener("focusin", onFocusIn);
            region.removeEventListener("focusout", onFocusOut);
            region.removeEventListener("click", onClick);
            scope.removeEventListener("keydown", onKeyDown, true);
            ownerDocument.removeEventListener("visibilitychange", onVisibilityChange);
            if (toastRegistry.get(scope) === region) toastRegistry.delete(scope);
            region.removeAttribute("data-citry-toast-initialized");
          };
        },
      });
    """

    css = r"""
      @layer citry-ui.theme {
        :where(.cui-toast-region) {
          --_cui-toast-inline-offset: var(--cui-toast-inline-offset, 1rem);
          --_cui-toast-block-offset: var(--cui-toast-block-offset, 1rem);
          --_cui-toast-gap: var(--cui-toast-gap, 0.75rem);
          --_cui-toast-width: var(--cui-toast-width, 22rem);
          --_cui-toast-background: var(--cui-toast-background, Canvas);
          --_cui-toast-foreground: var(--cui-toast-foreground, CanvasText);
          --_cui-toast-border-color: var(
            --cui-toast-border-color,
            color-mix(in srgb, CanvasText 18%, transparent)
          );
          --_cui-toast-shadow: var(--cui-toast-shadow, 0 1rem 3rem rgb(15 23 42 / 22%));
          --_cui-toast-radius: var(--cui-toast-radius, 0.75rem);
          --_cui-toast-padding: var(--cui-toast-padding, 1rem);
          --_cui-toast-accent: var(--cui-toast-accent, currentColor);
          --_cui-toast-z-index: var(--cui-toast-z-index, 1000);

          position: fixed;
          z-index: var(--_cui-toast-z-index);
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          gap: var(--_cui-toast-gap);
          inline-size: min(
            var(--_cui-toast-width),
            calc(100dvi - 2 * var(--_cui-toast-inline-offset))
          );
          max-block-size: calc(100dvb - 2 * var(--_cui-toast-block-offset));
          padding: 0;
          overflow: auto;
          overscroll-behavior: contain;
          pointer-events: none;
        }
        :where(.cui-toast-region[data-placement^="block-start"]) {
          inset-block-start: max(var(--_cui-toast-block-offset), env(safe-area-inset-top));
          inset-block-end: auto;
        }
        :where(.cui-toast-region[data-placement^="block-end"]) {
          inset-block-start: auto;
          inset-block-end: max(var(--_cui-toast-block-offset), env(safe-area-inset-bottom));
        }
        :where(.cui-toast-region[data-placement$="-start"]) {
          inset-inline-start: max(
            var(--_cui-toast-inline-offset),
            env(safe-area-inset-left),
            env(safe-area-inset-right)
          );
          inset-inline-end: auto;
        }
        :where(.cui-toast-region[data-placement$="-end"]) {
          inset-inline-start: auto;
          inset-inline-end: max(
            var(--_cui-toast-inline-offset),
            env(safe-area-inset-left),
            env(safe-area-inset-right)
          );
        }
        :where(.cui-toast-region[data-citry-toast-modal-paused]) {
          visibility: hidden;
        }
        :where(.cui-toast-region__announcer) {
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
        :where(.cui-toast-region__list) {
          display: contents;
        }
        :where(.cui-toast) {
          --_cui-toast-item-accent: var(--_cui-toast-accent);
          box-sizing: border-box;
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 0.75rem;
          align-items: start;
          inline-size: 100%;
          min-inline-size: 0;
          padding: var(--_cui-toast-padding);
          border: 1px solid var(--_cui-toast-border-color);
          border-inline-start: 0.25rem solid var(--_cui-toast-item-accent);
          border-radius: var(--_cui-toast-radius);
          background: var(--_cui-toast-background);
          color: var(--_cui-toast-foreground);
          box-shadow: var(--_cui-toast-shadow);
          pointer-events: auto;
        }
        :where(.cui-toast[data-intent="info"]) {
          --_cui-toast-item-accent: light-dark(#175cd3, #84adff);
        }
        :where(.cui-toast[data-intent="success"]) {
          --_cui-toast-item-accent: light-dark(#087443, #75e0a7);
        }
        :where(.cui-toast[data-intent="warn"]) {
          --_cui-toast-item-accent: light-dark(#b54708, #fec84b);
        }
        :where(.cui-toast[data-intent="error"]) {
          --_cui-toast-item-accent: light-dark(#b42318, #fda29b);
        }
        :where(.cui-toast__content) {
          display: grid;
          gap: 0.25rem;
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where(.cui-toast__title) {
          font-weight: 700;
          line-height: 1.35;
        }
        :where(.cui-toast__description) {
          color: color-mix(in srgb, currentColor 76%, transparent);
          line-height: 1.45;
        }
        :where(.cui-toast__description[hidden]) { display: none; }
        :where(.cui-toast__actions) {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          align-items: center;
          min-inline-size: 0;
        }
        :where(.cui-toast__actions[hidden]) { display: none; }
        :where(.cui-toast__actions button) {
          min-block-size: 2.75rem;
          padding: 0.5rem 0.75rem;
          border: 1px solid currentColor;
          border-radius: 0.5rem;
          background: transparent;
          color: inherit;
          font: inherit;
          overflow-wrap: anywhere;
          cursor: pointer;
        }
        :where(.cui-toast__actions [data-citry-toast-dismiss]) {
          inline-size: 2.75rem;
          padding: 0;
          font-size: 1.35rem;
          line-height: 1;
        }
        :where(.cui-toast__actions button[hidden]) { display: none; }
        :where(.cui-toast:focus-visible, .cui-toast__actions button:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: 0.125rem;
        }
        @media (forced-colors: active) {
          :where(.cui-toast) {
            border-color: CanvasText;
            border-inline-start-width: 0.375rem;
          }
        }
        @media print {
          :where(.cui-toast-region) { display: none; }
        }
      }
    """

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
