"""Styled Button component family."""

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
)

CButtonType = Literal["button", "submit", "reset"]
CButtonVariant = Literal["solid", "outline", "ghost"]
CButtonIntent = Literal["primary", "neutral", "success", "warn", "danger"]
CButtonSize = Literal["sm", "md", "lg"]
CButtonLoadingPos = Literal["start", "center", "end"]


class CButtonDefaultSlotData:
    pass


class CButtonStartSlotData:
    pass


class CButtonEndSlotData:
    pass


class CButtonLoadingSlotData:
    pass


_LINK_FORM_ATTRS = {
    "form",
    "formaction",
    "formenctype",
    "formmethod",
    "formnovalidate",
    "formtarget",
    "name",
    "value",
}


def _reject_link_form_attrs(attrs: Mapping[str, object] | None) -> None:
    incompatible = sorted(key for key in attrs or {} if key.lower() in _LINK_FORM_ATTRS)
    if incompatible:
        names = ", ".join(repr(name) for name in incompatible)
        msg = f"CButton attrs {names} apply only to action buttons and cannot be used when href is set."
        raise ValueError(msg)


def _pop_case_insensitive(attrs: dict[str, object], name: str) -> object | None:
    value: object | None = None
    for authored_name in tuple(attrs):
        if authored_name.lower() == name:
            value = attrs.pop(authored_name)
    return value


def _get_case_insensitive(attrs: Mapping[str, object] | None, name: str) -> object | None:
    value: object | None = None
    for authored_name, authored_value in (attrs or {}).items():
        if authored_name.lower() == name:
            value = authored_value
    return value


class CButton(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        type: CButtonType = "button"
        href: str | None = None
        disabled: bool = False
        loading: bool = False
        variant: CButtonVariant = "solid"
        intent: CButtonIntent = "primary"
        size: CButtonSize = "md"
        block: bool = False
        loading_pos: CButtonLoadingPos = "center"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonDefaultSlotData]
        start: SlotInput[CButtonStartSlotData] | None = None
        end: SlotInput[CButtonEndSlotData] | None = None
        loading: SlotInput[CButtonLoadingSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        validate_choice("CButton", "type", kwargs.type, ("button", "submit", "reset"))
        validate_choice("CButton", "variant", kwargs.variant, ("solid", "outline", "ghost"))
        validate_choice(
            "CButton",
            "intent",
            kwargs.intent,
            ("primary", "neutral", "success", "warn", "danger"),
        )
        validate_choice("CButton", "size", kwargs.size, ("sm", "md", "lg"))
        validate_choice(
            "CButton",
            "loading_pos",
            kwargs.loading_pos,
            ("start", "center", "end"),
        )
        if kwargs.href is not None and not isinstance(kwargs.href, str):
            msg = f"CButton href must be a string or None, got {kwargs.href!r}."
            raise TypeError(msg)
        if kwargs.href is not None and kwargs.type != "button":
            msg = "CButton type applies only to action buttons and must remain 'button' when href is set."
            raise ValueError(msg)
        validate_boolean("CButton", "disabled", kwargs.disabled)
        validate_boolean("CButton", "loading", kwargs.loading)
        validate_boolean("CButton", "block", kwargs.block)
        reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-busy",
                "aria-disabled",
                "data-block",
                "data-citry-button-has-end",
                "data-citry-button-has-start",
                "data-citry-button-initialized",
                "data-citry-ui-part",
                "data-disabled",
                "data-intent",
                "data-loading",
                "data-loading-position",
                "data-size",
                "data-variant",
                "disabled",
                "href",
                "type",
            },
            "CButton",
        )
        if kwargs.href is not None:
            _reject_link_form_attrs(kwargs.attrs)

        form = self.inject(FORM_CONTEXT_KEY, None)
        disabled = (bool(form.disabled) if form is not None else False) or kwargs.disabled
        is_link = kwargs.href is not None
        unavailable = disabled or kwargs.loading
        attrs = merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style)
        authored_tabindex = _pop_case_insensitive(attrs, "tabindex")
        if not is_link:
            tabindex_without_js = authored_tabindex
        elif disabled:
            tabindex_without_js = -1
        elif kwargs.loading:
            tabindex_without_js = authored_tabindex if authored_tabindex is not None else 0
        else:
            tabindex_without_js = authored_tabindex
        return {
            "root_tag": "a" if is_link else "button",
            "type_without_js": None if is_link else kwargs.type,
            "href_without_js": None if unavailable else kwargs.href,
            "disabled_without_js": unavailable if not is_link else None,
            "tabindex_without_js": tabindex_without_js,
            "aria_busy": "true" if kwargs.loading else None,
            "aria_disabled": "true" if unavailable else None,
            "disabled": disabled,
            "loading": kwargs.loading,
            "variant": kwargs.variant,
            "intent": kwargs.intent,
            "size": kwargs.size,
            "block": kwargs.block,
            "loading_pos": kwargs.loading_pos,
            "attrs": attrs,
            "has_start": "start" in self.raw_slots,
            "has_end": "end" in self.raw_slots,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "href": kwargs.href,
            "tabIndex": _get_case_insensitive(kwargs.attrs, "tabindex"),
            "disabled": kwargs.disabled,
            "loading": kwargs.loading,
            "variant": kwargs.variant,
            "intent": kwargs.intent,
            "size": kwargs.size,
            "block": kwargs.block,
            "loadingPosition": kwargs.loading_pos,
        }

    template = """
      <c-element
        c-is="root_tag"
        class="cui-button"
        c-type="type_without_js"
        c-href="href_without_js"
        c-disabled="disabled_without_js"
        c-tabindex="tabindex_without_js"
        c-aria-busy="aria_busy"
        c-aria-disabled="aria_disabled"
        c-data-loading="loading"
        c-data-disabled="disabled"
        c-data-variant="variant"
        c-data-intent="intent"
        c-data-size="size"
        c-data-block="block"
        c-data-loading-position="loading_pos"
        c-data-citry-button-has-start="has_start"
        c-data-citry-button-has-end="has_end"
        c-bind="attrs"
        data-citry-ui-part="button"
      >
        <span
          class="cui-button__loading"
          aria-hidden="true"
          c-hidden="not loading"
          data-citry-ui-part="loading-indicator"
        >
          <c-slot name="loading">
            <span class="cui-button__spinner"></span>
          </c-slot>
        </span>
        <c-if cond="has_start">
          <span
            class="cui-button__decoration"
            data-citry-ui-part="start"
          >
            <c-slot name="start" />
          </span>
        </c-if>
        <span
          class="cui-button__content"
          data-citry-ui-part="content"
        >
          <c-slot required />
        </span>
        <c-if cond="has_end">
          <span
            class="cui-button__decoration"
            data-citry-ui-part="end"
          >
            <c-slot name="end" />
          </span>
        </c-if>
      </c-element>
    """

    js = """
      $component({
        props: {
          disabled: {},
          loading: {},
          variant: {},
          intent: {},
          size: {},
          block: {},
          loadingPosition: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const indicator = root.querySelector('[data-citry-ui-part="loading-indicator"]');
          const formContext = inject(Symbol.for("citry-ui:form"), null);
          const isLink = root.localName === "a";
          const allowedValues = {
            variant: ["solid", "outline", "ghost"],
            intent: ["primary", "neutral", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
            loadingPosition: ["start", "center", "end"],
          };
          const invalidEpisodes = new Map();
          let configuration = {
            disabled: data.disabled,
            loading: data.loading,
            variant: data.variant,
            intent: data.intent,
            size: data.size,
            block: data.block,
            loadingPosition: data.loadingPosition,
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
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CButton ${name} received invalid client value ${describedValue}; `
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
          const applyConfiguration = (next) => {
            configuration = next;
            if (isLink) {
              if (next.disabled || next.loading) {
                root.removeAttribute("href");
              } else {
                root.setAttribute("href", data.href);
              }
              const tabIndex = next.disabled
                ? -1
                : next.loading
                  ? (data.tabIndex ?? 0)
                  : data.tabIndex;
              if (tabIndex === null || tabIndex === undefined) {
                root.removeAttribute("tabindex");
              } else {
                root.setAttribute("tabindex", String(tabIndex));
              }
            } else {
              root.disabled = next.disabled;
            }
            root.toggleAttribute("data-disabled", next.disabled);
            root.toggleAttribute("data-loading", next.loading);
            root.toggleAttribute("data-block", next.block);
            root.dataset.variant = next.variant;
            root.dataset.intent = next.intent;
            root.dataset.size = next.size;
            root.dataset.loadingPosition = next.loadingPosition;
            if (next.loading) {
              root.setAttribute("aria-busy", "true");
            } else {
              root.removeAttribute("aria-busy");
            }
            if (next.disabled || next.loading) {
              root.setAttribute("aria-disabled", "true");
            } else {
              root.removeAttribute("aria-disabled");
            }
            indicator.hidden = !next.loading;
          };
          const blockUnavailableActivation = (event) => {
            if (!configuration.loading && !(isLink && configuration.disabled)) {
              return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
          };
          const blockLoadingSubmitter = (event) => {
            if (!configuration.loading || event.submitter !== root) {
              return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
          };
          const nativeForm = isLink ? null : root.form;

          root.addEventListener("click", blockUnavailableActivation, true);
          nativeForm?.addEventListener("submit", blockLoadingSubmitter, true);
          effect(() => {
            const localDisabled = resolveBoolean("disabled");
            applyConfiguration({
              disabled: Boolean(formContext?.disabled) || localDisabled,
              loading: resolveBoolean("loading"),
              variant: resolveChoice("variant"),
              intent: resolveChoice("intent"),
              size: resolveChoice("size"),
              block: resolveBoolean("block"),
              loadingPosition: resolveChoice("loadingPosition"),
            });
          });
          root.setAttribute("data-citry-button-initialized", "");

          return () => {
            root.removeEventListener("click", blockUnavailableActivation, true);
            nativeForm?.removeEventListener("submit", blockLoadingSubmitter, true);
            root.removeAttribute("data-citry-button-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-button) {
          --_cui-button-tone: LinkText;
          --_cui-button-on-tone: Canvas;
          --_cui-button-background-default: var(--_cui-button-tone);
          --_cui-button-foreground-default: var(--_cui-button-on-tone);
          --_cui-button-border-default: transparent;
          --_cui-button-hover-default: color-mix(
            in srgb,
            var(--_cui-button-tone),
            CanvasText 12%
          );
          --_cui-button-active-default: color-mix(
            in srgb,
            var(--_cui-button-tone),
            CanvasText 22%
          );
          --_cui-button-background: var(
            --cui-button-background,
            var(--_cui-button-background-default)
          );
          --_cui-button-foreground: var(
            --cui-button-foreground,
            var(--_cui-button-foreground-default)
          );
          --_cui-button-border-color: var(
            --cui-button-border-color,
            var(--_cui-button-border-default)
          );
          --_cui-button-hover-background: var(
            --cui-button-hover-background,
            var(--_cui-button-hover-default)
          );
          --_cui-button-active-background: var(
            --cui-button-active-background,
            var(--_cui-button-active-default)
          );
          --_cui-button-focus-color: var(--cui-button-focus-color, Highlight);
          --_cui-button-radius: var(--cui-button-radius, 0.5rem);
          --_cui-button-font-weight: var(--cui-button-font-weight, 600);
          --_cui-button-gap: var(--cui-button-gap, 0.5rem);
          --_cui-button-disabled-opacity: var(--cui-button-disabled-opacity, 0.48);
          --_cui-button-height: var(--cui-button-height, 2.5rem);
          --_cui-button-inline-padding: var(--cui-button-inline-padding, 1rem);
          --_cui-button-block-padding: var(--cui-button-block-padding, 0.5rem);
          --_cui-button-font-size: var(--cui-button-font-size, 0.9375rem);

          position: relative;
          display: inline-flex;
          box-sizing: border-box;
          align-items: center;
          justify-content: center;
          gap: var(--_cui-button-gap);
          min-block-size: var(--_cui-button-height);
          margin: 0;
          padding-block: var(--_cui-button-block-padding);
          padding-inline: var(--_cui-button-inline-padding);
          border: 1px solid var(--_cui-button-border-color);
          border-radius: var(--_cui-button-radius);
          background: var(--_cui-button-background);
          color: var(--_cui-button-foreground);
          font: inherit;
          font-size: var(--_cui-button-font-size);
          font-weight: var(--_cui-button-font-weight);
          line-height: 1.25;
          text-align: center;
          text-decoration: none;
          vertical-align: middle;
          cursor: pointer;
          isolation: isolate;
          -webkit-tap-highlight-color: transparent;
        }

        :where(.cui-button[data-intent="neutral"]) {
          --_cui-button-tone: CanvasText;
          --_cui-button-on-tone: Canvas;
        }

        :where(.cui-button[data-intent="success"]) {
          --_cui-button-tone: light-dark(#067647, #75e0a7);
          --_cui-button-on-tone: light-dark(#ffffff, #102a1d);
        }

        :where(.cui-button[data-intent="warn"]) {
          --_cui-button-tone: light-dark(#b54708, #fec84b);
          --_cui-button-on-tone: light-dark(#ffffff, #1d2939);
        }

        :where(.cui-button[data-intent="danger"]) {
          --_cui-button-tone: light-dark(#b42318, #fda29b);
          --_cui-button-on-tone: light-dark(#ffffff, #3f0e0a);
        }

        :where(.cui-button[data-variant="outline"]) {
          --_cui-button-background-default: transparent;
          --_cui-button-foreground-default: var(--_cui-button-tone);
          --_cui-button-border-default: var(--_cui-button-tone);
          --_cui-button-hover-default: color-mix(
            in srgb,
            var(--_cui-button-tone) 10%,
            transparent
          );
          --_cui-button-active-default: color-mix(
            in srgb,
            var(--_cui-button-tone) 18%,
            transparent
          );
        }

        :where(.cui-button[data-variant="ghost"]) {
          --_cui-button-background-default: transparent;
          --_cui-button-foreground-default: var(--_cui-button-tone);
          --_cui-button-border-default: transparent;
          --_cui-button-hover-default: color-mix(
            in srgb,
            var(--_cui-button-tone) 10%,
            transparent
          );
          --_cui-button-active-default: color-mix(
            in srgb,
            var(--_cui-button-tone) 18%,
            transparent
          );
        }

        :where(.cui-button[data-size="sm"]) {
          --_cui-button-height: var(--cui-button-height, 2.25rem);
          --_cui-button-inline-padding: var(--cui-button-inline-padding, 0.75rem);
          --_cui-button-block-padding: var(--cui-button-block-padding, 0.375rem);
          --_cui-button-font-size: var(--cui-button-font-size, 0.875rem);
        }

        :where(.cui-button[data-size="lg"]) {
          --_cui-button-height: var(--cui-button-height, 2.75rem);
          --_cui-button-inline-padding: var(--cui-button-inline-padding, 1.25rem);
          --_cui-button-block-padding: var(--cui-button-block-padding, 0.625rem);
          --_cui-button-font-size: var(--cui-button-font-size, 1rem);
        }

        :where(.cui-button[data-block]) {
          display: flex;
          inline-size: 100%;
        }

        @media (hover: hover) {
          :where(
            .cui-button:not(:disabled):not([data-disabled]):not([data-loading]):hover
          ) {
            background: var(--_cui-button-hover-background);
          }
        }

        :where(
          .cui-button:not(:disabled):not([data-disabled]):not([data-loading]):active
        ) {
          background: var(--_cui-button-active-background);
        }

        :where(.cui-button:focus-visible) {
          outline: 0.1875rem solid var(--_cui-button-focus-color);
          outline-offset: 0.1875rem;
        }

        :where(
          .cui-button:disabled,
          .cui-button[data-disabled],
          .cui-button[data-loading]
        ) {
          cursor: not-allowed;
        }

        :where(.cui-button:disabled, .cui-button[data-disabled]) {
          opacity: var(--_cui-button-disabled-opacity);
        }

        :where(.cui-button__content) {
          min-inline-size: 0;
        }

        :where(.cui-button__decoration, .cui-button__loading) {
          display: inline-flex;
          flex: 0 0 auto;
          align-items: center;
          justify-content: center;
          inline-size: 1em;
          block-size: 1em;
        }

        :where(.cui-button__loading) {
          position: absolute;
          inset-block-start: 50%;
          translate: 0 -50%;
        }

        :where(.cui-button__loading[hidden]) {
          display: none;
        }

        :where(.cui-button[data-loading-position="start"] .cui-button__loading) {
          inset-inline-start: var(--_cui-button-inline-padding);
        }

        :where(.cui-button[data-loading-position="center"] .cui-button__loading) {
          inset-inline-start: 50%;
          translate: -50% -50%;
        }

        :where(.cui-button[data-loading-position="end"] .cui-button__loading) {
          inset-inline-end: var(--_cui-button-inline-padding);
        }

        :where(
          .cui-button[data-loading][data-loading-position="center"]
          .cui-button__decoration
        ),
        :where(
          .cui-button[data-loading][data-loading-position="center"]
          .cui-button__content
        ),
        :where(
          .cui-button[data-loading][data-loading-position="start"]
          [data-citry-ui-part="start"]
        ),
        :where(
          .cui-button[data-loading][data-loading-position="end"]
          [data-citry-ui-part="end"]
        ) {
          opacity: 0;
        }

        :where(
          .cui-button[data-loading][data-loading-position="start"]:not(
            [data-citry-button-has-start]
          )
          .cui-button__content
        ) {
          margin-inline-start: calc(1em + var(--_cui-button-gap));
        }

        :where(
          .cui-button[data-loading][data-loading-position="end"]:not(
            [data-citry-button-has-end]
          )
          .cui-button__content
        ) {
          margin-inline-end: calc(1em + var(--_cui-button-gap));
        }

        :where(.cui-button__spinner) {
          display: block;
          box-sizing: border-box;
          inline-size: 1em;
          block-size: 1em;
          border: 0.125em solid currentColor;
          border-inline-end-color: transparent;
          border-radius: 50%;
          animation: cui-button-spin 700ms linear infinite;
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-button__spinner) {
            border-inline-end-color: currentColor;
            border-block-start-color: transparent;
            animation: none;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-button) {
            border-color: ButtonText;
          }

          :where(.cui-button:disabled, .cui-button[data-disabled]) {
            border-color: GrayText;
            color: GrayText;
            opacity: 1;
          }
        }

        @keyframes cui-button-spin {
          to {
            rotate: 1turn;
          }
        }
      }
    """


__all__ = [
    "CButton",
    "CButtonDefaultSlotData",
    "CButtonEndSlotData",
    "CButtonIntent",
    "CButtonLoadingPos",
    "CButtonLoadingSlotData",
    "CButtonSize",
    "CButtonStartSlotData",
    "CButtonType",
    "CButtonVariant",
]
