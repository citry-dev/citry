"""Progressively enhanced requests for another server-owned result page."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CInfiniteScrollReason = Literal["button", "intersection", "retry"]

_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-busy",
        "aria-label",
        "contenteditable",
        "data-auto",
        "data-citry-infinite-scroll-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-end",
        "data-error",
        "data-loading",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CInfiniteScrollDefaultSlotData:
    pass


class CInfiniteScrollLoadDetail(TypedDict):
    reason: CInfiniteScrollReason
    sourceEvent: object | None


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000.")
    return plain


def _threshold(value: object) -> float:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise TypeError(f"CInfiniteScroll threshold must be a number, got {raw!r}.")
    result = float(raw)
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise ValueError(f"CInfiniteScroll threshold must be finite and between 0 and 1, got {raw!r}.")
    return result


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    attrs: Mapping[str, object] | None, class_: CClassValue | None, style: CStyleValue | None
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"CInfiniteScroll attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _ROOT_OWNED, "CInfiniteScroll attrs")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CInfiniteScroll attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CInfiniteScroll attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"CInfiniteScroll attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in _ROOT_OWNED:
            raise ValueError(f"CInfiniteScroll attrs cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


class CInfiniteScroll(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        aria_label: str | None = None
        has_more: bool = True
        loading: bool = False
        error: bool = False
        disabled: bool = False
        auto: bool = True
        root_margin: str = "0px 0px 240px 0px"
        threshold: float = 0
        action_name: str | None = None
        action_value: str = "load-more"
        load_more_label: str = "Load more"
        retry_label: str = "Try again"
        loading_label: str = "Loading more results"
        error_label: str = "More results could not be loaded"
        end_label: str = "No more results"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CInfiniteScrollDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_infinite_scroll_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        validate_html_id("CInfiniteScroll", kwargs.id)
        for name in ("has_more", "loading", "error", "disabled", "auto"):
            validate_boolean("CInfiniteScroll", name, getattr(kwargs, name))
        catalog = {
            key: uses_catalog_default(self, f"{key}_label")
            for key in ("load_more", "retry", "loading", "error", "end")
        }
        message_ids = {
            "load_more": "citry-ui-infinite-scroll-load-more",
            "retry": "citry-ui-infinite-scroll-retry",
            "loading": "citry-ui-infinite-scroll-loading",
            "error": "citry-ui-infinite-scroll-error",
            "end": "citry-ui-infinite-scroll-end",
        }
        labels = {}
        for key, message_id in message_ids.items():
            value = self.i18n.tr(message_id) if catalog[key] else getattr(kwargs, f"{key}_label")
            labels[key] = cast("str", _plain(f"CInfiniteScroll {key}_label", value))
        snapshot: dict[str, object] = {
            "root_id": kwargs.id or f"cui-infinite-scroll-{self.id}",
            "aria_label": cast("str | None", _plain("CInfiniteScroll aria_label", kwargs.aria_label, optional=True)),
            "has_more": bool(kwargs.has_more),
            "loading": bool(kwargs.loading),
            "error": bool(kwargs.error),
            "disabled": bool(kwargs.disabled),
            "auto": bool(kwargs.auto),
            "root_margin": cast("str", _plain("CInfiniteScroll root_margin", kwargs.root_margin)),
            "threshold": _threshold(kwargs.threshold),
            "action_name": cast(
                "str | None", _plain("CInfiniteScroll action_name", kwargs.action_name, optional=True)
            ),
            "action_value": cast("str", _plain("CInfiniteScroll action_value", kwargs.action_value)),
            "catalog": catalog,
            "labels": labels,
            "attrs": _attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }
        self._cui_infinite_scroll_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        snapshot = self._snapshot(kwargs)
        has_more = cast("bool", snapshot["has_more"])
        loading = cast("bool", snapshot["loading"])
        error = cast("bool", snapshot["error"])
        disabled = cast("bool", snapshot["disabled"])
        auto = cast("bool", snapshot["auto"])
        return {
            **snapshot,
            "content": (
                cast("Slot[CInfiniteScrollDefaultSlotData]", slots.default)({}) if "default" in self.raw_slots else ""
            ),
            "root_attrs": {
                **cast("dict[str, object]", snapshot["attrs"]),
                "aria-label": snapshot["aria_label"],
                "data-auto": True if auto else None,
                "data-disabled": True if disabled else None,
                "data-end": True if not has_more and not loading and not error else None,
                "data-error": True if error and not loading else None,
                "data-loading": True if loading else None,
                "role": "region" if snapshot["aria_label"] is not None else None,
            },
            "content_busy": "true" if loading else "false",
            "show_action": has_more and not loading,
            "show_loading": loading,
            "show_error": error and not loading,
            "show_end": not has_more and not loading and not error,
            "button_disabled": disabled,
            "button_type": "submit" if snapshot["action_name"] is not None else "button",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            key: snapshot[key]
            for key in ("has_more", "loading", "error", "disabled", "auto", "root_margin", "threshold")
        }

    template = """
      <div class="cui-infinite-scroll" c-id="root_id" c-bind="root_attrs" data-citry-ui-part="infinite-scroll">
        <div c-aria-busy="content_busy" data-citry-ui-part="content">{{ content }}</div>
        <div data-citry-ui-part="status" role="status" aria-live="polite" aria-atomic="true">
          <span c-hidden="not show_loading" c-$c-tr:citry-ui-infinite-scroll-loading="True if catalog['loading'] else None">{{ tr('citry-ui-infinite-scroll-loading') if catalog['loading'] else labels['loading'] }}</span>
          <span c-hidden="not show_error" c-$c-tr:citry-ui-infinite-scroll-error="True if catalog['error'] else None">{{ tr('citry-ui-infinite-scroll-error') if catalog['error'] else labels['error'] }}</span>
          <span c-hidden="not show_end" c-$c-tr:citry-ui-infinite-scroll-end="True if catalog['end'] else None">{{ tr('citry-ui-infinite-scroll-end') if catalog['end'] else labels['end'] }}</span>
        </div>
        <button c-type="button_type" c-name="action_name" c-value="action_value" c-disabled="button_disabled"
          c-hidden="not show_action" c-formnovalidate="True if action_name is not None else None"
          data-citry-infinite-scroll-action data-citry-ui-part="action">
          <span c-hidden="error" c-$c-tr:citry-ui-infinite-scroll-load-more="True if catalog['load_more'] else None">{{ tr('citry-ui-infinite-scroll-load-more') if catalog['load_more'] else labels['load_more'] }}</span>
          <span c-hidden="not error" c-$c-tr:citry-ui-infinite-scroll-retry="True if catalog['retry'] else None">{{ tr('citry-ui-infinite-scroll-retry') if catalog['retry'] else labels['retry'] }}</span>
        </button>
        <span data-citry-infinite-scroll-sentinel data-citry-ui-part="sentinel" aria-hidden="true"></span>
      </div>
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      citry-ui-infinite-scroll-load-more = Load more
      citry-ui-infinite-scroll-retry = Try again
      citry-ui-infinite-scroll-loading = Loading more results
      citry-ui-infinite-scroll-error = More results could not be loaded
      citry-ui-infinite-scroll-end = No more results
    """


__all__ = ["CInfiniteScroll", "CInfiniteScrollDefaultSlotData", "CInfiniteScrollLoadDetail", "CInfiniteScrollReason"]
