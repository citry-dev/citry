"""Finite native-link or client-owned Pagination navigation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CPaginationVariant = Literal["soft", "outline", "plain"]
CPaginationSize = Literal["sm", "md", "lg"]

_VARIANTS = ("soft", "outline", "plain")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-size",
        "data-variant",
        "role",
        "tabindex",
    }
)


class CPaginationChangeDetail(TypedDict):
    page: int
    previousPage: int
    kind: Literal["page", "previous", "next", "first", "last"]
    sourceEvent: object


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        msg = f"CPagination {name} must be a string{' or None' if optional else ''}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain.strip() or "\x00" in plain:
        msg = f"CPagination {name} must be nonempty and cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in allowed:
        raise ValueError(f"CPagination {name} must be one of {allowed!r}, got {plain!r}.")
    return plain


def _integer(name: str, value: object, *, minimum: int, maximum: int | None = None) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"CPagination {name} must be an integer, got {raw!r}.")
    if raw < minimum or (maximum is not None and raw > maximum):
        bound = f"between {minimum} and {maximum}" if maximum is not None else f"at least {minimum}"
        raise ValueError(f"CPagination {name} must be {bound}, got {raw!r}.")
    return raw


def _range(pages: int, page: int, siblings: int, boundaries: int) -> tuple[int | str, ...]:
    visible = set(range(1, min(boundaries, pages) + 1))
    visible.update(range(max(1, pages - boundaries + 1), pages + 1))
    visible.update(range(max(1, page - siblings), min(pages, page + siblings) + 1))
    ordered = sorted(visible)
    result: list[int | str] = []
    for item in ordered:
        if result and isinstance(result[-1], int):
            gap = item - result[-1]
            if gap == 2:
                result.append(item - 1)
            elif gap > 2:
                result.append("ellipsis")
        result.append(item)
    return tuple(result)


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"CPagination attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED, "CPagination attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"CPagination attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"CPagination attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in _OWNED:
            raise ValueError(f"CPagination attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CPagination(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        pages: int
        page: int = 1
        href: str | None = None
        siblings: int = 1
        boundaries: int = 1
        show_controls: bool = True
        show_edges: bool = False
        disabled: bool = False
        variant: CPaginationVariant = "soft"
        size: CPaginationSize = "md"
        label: str = "Pagination"
        page_label: str = "Page {page}"
        previous_label: str = "Previous page"
        next_label: str = "Next page"
        first_label: str = "First page"
        last_label: str = "Last page"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        pages = _integer("pages", kwargs.pages, minimum=1)
        page = _integer("page", kwargs.page, minimum=1, maximum=pages)
        siblings = _integer("siblings", kwargs.siblings, minimum=0, maximum=10)
        boundaries = _integer("boundaries", kwargs.boundaries, minimum=0, maximum=10)
        href = _plain("href", kwargs.href, optional=True)
        if href is not None and "{page}" not in href:
            raise ValueError("CPagination href must contain the literal {page} placeholder.")
        validate_boolean("CPagination", "show_controls", kwargs.show_controls)
        validate_boolean("CPagination", "show_edges", kwargs.show_edges)
        validate_boolean("CPagination", "disabled", kwargs.disabled)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        labels = {
            name: _plain(name, value)
            for name, value in (
                ("label", kwargs.label),
                ("page_label", kwargs.page_label),
                ("previous_label", kwargs.previous_label),
                ("next_label", kwargs.next_label),
                ("first_label", kwargs.first_label),
                ("last_label", kwargs.last_label),
            )
        }
        if "{page}" not in str(labels["page_label"]):
            raise ValueError("CPagination page_label must contain {page}.")
        items: list[dict[str, object]] = []
        if kwargs.show_edges:
            items.append(self._control("first", 1, page, pages, href, str(labels["first_label"]), kwargs.disabled))
        if kwargs.show_controls:
            items.append(
                self._control(
                    "previous",
                    max(1, page - 1),
                    page,
                    pages,
                    href,
                    str(labels["previous_label"]),
                    kwargs.disabled,
                )
            )
        for range_item in _range(pages, page, siblings, boundaries):
            if isinstance(range_item, str):
                items.append({"kind": "ellipsis"})
            else:
                items.append(
                    self._control(
                        "page",
                        range_item,
                        page,
                        pages,
                        href,
                        str(labels["page_label"]).replace("{page}", str(range_item)),
                        kwargs.disabled,
                    )
                )
        if kwargs.show_controls:
            items.append(
                self._control(
                    "next",
                    min(pages, page + 1),
                    page,
                    pages,
                    href,
                    str(labels["next_label"]),
                    kwargs.disabled,
                )
            )
        if kwargs.show_edges:
            items.append(self._control("last", pages, page, pages, href, str(labels["last_label"]), kwargs.disabled))
        self._pagination_data: dict[str, object] = {
            "pages": pages,
            "page": page,
            "href": href,
            "siblings": siblings,
            "boundaries": boundaries,
            "showControls": bool(kwargs.show_controls),
            "showEdges": bool(kwargs.show_edges),
            "disabled": bool(kwargs.disabled),
            "variant": variant,
            "size": size,
            **labels,
        }
        return {
            "items": items,
            "disabled": bool(kwargs.disabled),
            "variant": variant,
            "size": size,
            "label": labels["label"],
            "attrs": merge_root_attrs(_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
        }

    @staticmethod
    def _control(
        kind: str,
        target: int,
        page: int,
        pages: int,
        href: str | None,
        label: str,
        disabled: bool,
    ) -> dict[str, object]:
        unavailable = (
            disabled or (kind in ("first", "previous") and page == 1) or (kind in ("next", "last") and page == pages)
        )
        texts = {"first": "«", "previous": "\u2039", "next": "\u203a", "last": "»"}
        control: dict[str, object] = {
            "kind": kind,
            "page": target,
            "label": label,
            "text": str(target) if kind == "page" else texts[kind],
            "current": kind == "page" and target == page,
            "disabled": unavailable,
            "href": href.replace("{page}", str(target)) if href is not None and not unavailable else None,
        }
        return control

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return self._pagination_data

    template = """
      <nav
        class="cui-pagination"
        c-bind="attrs"
        data-citry-ui-part="pagination"
        c-data-disabled="disabled"
        c-data-variant="variant"
        c-data-size="size"
        c-aria-label="label"
      >
        <ul data-citry-ui-part="list">
          <c-for each="item in items">
            <li>
              <c-if cond="item['kind'] == 'ellipsis'">
                <span data-citry-ui-part="ellipsis" aria-hidden="true">…</span>
              </c-if>
              <c-elif cond="item['href'] is not None">
                <a
                  c-href="item['href']"
                  c-aria-label="item['label']"
                  c-aria-current="'page' if item['current'] else None"
                  c-data-page="item['page']"
                  c-data-kind="item['kind']"
                  c-data-current="item['current']"
                  data-citry-ui-part="control"
                >{{ item['text'] }}</a>
              </c-elif>
              <c-else>
                <button
                  type="button"
                  c-aria-label="item['label']"
                  c-aria-current="'page' if item['current'] else None"
                  c-data-page="item['page']"
                  c-data-kind="item['kind']"
                  c-data-current="item['current']"
                  c-disabled="item['disabled']"
                  data-citry-ui-part="control"
                >{{ item['text'] }}</button>
              </c-else>
            </li>
          </c-for>
        </ul>
      </nav>
    """

    js = r"""
      $component({
        props: {page: {}, disabled: {}, variant: {}, size: {}, onPageChange: {}},
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const list = root.querySelector('[data-citry-ui-part="list"]');
          let current = data.page;
          let callback = null;
          let effectiveDisabled = data.disabled;
          let effectiveVariant = data.variant;
          let effectiveSize = data.size;
          const invalid = new Set();
          const report = (name, value) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(`[citry-ui] CPagination ${name} received invalid client value`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalid.delete(name); return fallback; }
            if (typeof supplied === "boolean") { invalid.delete(name); return supplied; }
            report(name, supplied);
            return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalid.delete(name); return fallback; }
            if (typeof supplied === "string" && allowed.includes(supplied)) {
              invalid.delete(name);
              return supplied;
            }
            report(name, supplied);
            return fallback;
          };
          const range = (page) => {
            const values = new Set();
            for (let n = 1; n <= Math.min(data.boundaries, data.pages); n += 1) values.add(n);
            for (let n = Math.max(1, data.pages - data.boundaries + 1); n <= data.pages; n += 1) values.add(n);
            for (let n = Math.max(1, page - data.siblings);
                n <= Math.min(data.pages, page + data.siblings); n += 1) values.add(n);
            const ordered = [...values].sort((a, b) => a - b);
            const result = [];
            ordered.forEach((value) => {
              const previous = result[result.length - 1];
              if (typeof previous === "number" && value - previous === 2) result.push(value - 1);
              else if (typeof previous === "number" && value - previous > 2) result.push("ellipsis");
              result.push(value);
            });
            return result;
          };
          const label = (kind, page) => kind === "page"
            ? data.page_label.replace("{page}", String(page))
            : data[`${kind}_label`];
          const render = () => {
            const items = [];
            if (data.showEdges) items.push(["first", 1]);
            if (data.showControls) items.push(["previous", Math.max(1, current - 1)]);
            range(current).forEach((value) => items.push(value === "ellipsis" ? ["ellipsis", null] : ["page", value]));
            if (data.showControls) items.push(["next", Math.min(data.pages, current + 1)]);
            if (data.showEdges) items.push(["last", data.pages]);
            list.replaceChildren(...items.map(([kind, page]) => {
              const li = document.createElement("li");
              if (kind === "ellipsis") {
                const span = document.createElement("span");
                span.dataset.citryUiPart = "ellipsis";
                span.setAttribute("aria-hidden", "true");
                span.textContent = "…";
                li.append(span);
                return li;
              }
              const unavailable = effectiveDisabled
                || (["first", "previous"].includes(kind) && current === 1)
                || (["next", "last"].includes(kind) && current === data.pages);
              const href = data.href && !unavailable ? data.href.replace("{page}", String(page)) : null;
              const control = document.createElement(href ? "a" : "button");
              if (href) control.href = href;
              else { control.type = "button"; control.disabled = unavailable; }
              control.dataset.citryUiPart = "control";
              control.dataset.page = String(page);
              control.dataset.kind = kind;
              control.setAttribute("aria-label", label(kind, page));
              control.textContent = kind === "page" ? String(page)
                : ({first: "«", previous: "\u2039", next: "\u203a", last: "»"})[kind];
              if (kind === "page" && page === current) {
                control.setAttribute("aria-current", "page");
                control.setAttribute("data-current", "");
              }
              li.append(control);
              return li;
            }));
            root.toggleAttribute("data-disabled", effectiveDisabled);
          };
          const reconcile = () => {
            callback = typeof props.onPageChange === "function" ? props.onPageChange : null;
            if (props.page === undefined) invalid.delete("page");
            else if (Number.isInteger(props.page) && props.page >= 1 && props.page <= data.pages) {
              invalid.delete("page");
              current = props.page;
            } else report("page", props.page);
            effectiveDisabled = resolveBoolean("disabled", data.disabled);
            effectiveVariant = resolveChoice("variant", data.variant, ["soft", "outline", "plain"]);
            effectiveSize = resolveChoice("size", data.size, ["sm", "md", "lg"]);
            root.dataset.variant = effectiveVariant;
            root.dataset.size = effectiveSize;
            render();
          };
          const onClick = (event) => {
            const control = event.target.closest?.('[data-citry-ui-part="control"]');
            if (!control || control.closest('[data-citry-ui-part="pagination"]') !== root || control.disabled) return;
            const page = Number(control.dataset.page);
            if (page === current) return;
            const previousPage = current;
            callback?.(page, {page, previousPage, kind: control.dataset.kind, sourceEvent: event});
            if (!control.href) event.preventDefault();
            if (props.page === undefined && (!control.href || event.defaultPrevented)) { current = page; render(); }
            else if (props.page !== undefined) setTimeout(reconcile, 0);
          };
          root.addEventListener("click", onClick);
          const stop = effect(reconcile);
          root.setAttribute("data-citry-pagination-initialized", "");
          return () => {
            stop?.();
            root.removeEventListener("click", onClick);
            root.removeAttribute("data-citry-pagination-initialized");
          };
        },
      })
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="pagination"]) {
          --_cui-pagination-gap: var(--cui-pagination-gap, 0.35rem);
          --_cui-pagination-control-size: var(--cui-pagination-control-size, 2.35rem);
          --_cui-pagination-radius: var(--cui-pagination-radius, 0.55rem);
          --_cui-pagination-foreground: var(--cui-pagination-foreground, CanvasText);
          --_cui-pagination-background: var(--cui-pagination-background, transparent);
          --_cui-pagination-border-color: var(--cui-pagination-border-color, light-dark(#d6d3d1, #57534e));
          --_cui-pagination-current-background: var(--cui-pagination-current-background, light-dark(#175cd3, #93c5fd));
          --_cui-pagination-current-foreground: var(--cui-pagination-current-foreground, light-dark(white, #172554));
          --_cui-pagination-disabled-opacity: var(--cui-pagination-disabled-opacity, 0.5);
          --_cui-pagination-focus-ring: var(--cui-pagination-focus-ring, Highlight);
          max-inline-size: 100%;
        }
        :where([data-citry-ui-part="pagination"] > [data-citry-ui-part="list"]) {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--_cui-pagination-gap);
          margin: 0;
          padding: 0;
          list-style: none;
        }
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"]),
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="ellipsis"]) {
          box-sizing: border-box;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-inline-size: var(--_cui-pagination-control-size);
          min-block-size: var(--_cui-pagination-control-size);
          padding: 0.35rem;
          border: 1px solid transparent;
          border-radius: var(--_cui-pagination-radius);
          color: var(--_cui-pagination-foreground);
          background: var(--_cui-pagination-background);
          font: inherit;
          line-height: 1;
          text-decoration: none;
        }
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"]) {
          cursor: pointer;
        }
        :where([data-citry-ui-part="pagination"][data-variant="outline"] [data-citry-ui-part="control"]) {
          border-color: var(--_cui-pagination-border-color);
        }
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"][data-current]) {
          color: var(--_cui-pagination-current-foreground);
          background: var(--_cui-pagination-current-background);
          border-color: var(--_cui-pagination-current-background);
          font-weight: 700;
        }
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"]:disabled) {
          opacity: var(--_cui-pagination-disabled-opacity);
          cursor: not-allowed;
        }
        :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"]:focus-visible) {
          outline: 3px solid var(--_cui-pagination-focus-ring);
          outline-offset: 2px;
        }
        :where([data-citry-ui-part="pagination"]:dir(rtl)
          [data-citry-ui-part="control"]:not([data-kind="page"])) {
          transform: rotate(180deg);
        }
        :where([data-citry-ui-part="pagination"][data-size="sm"]) {
          --_cui-pagination-control-size: 2rem;
          font-size: 0.875rem;
        }
        :where([data-citry-ui-part="pagination"][data-size="lg"]) {
          --_cui-pagination-control-size: 2.75rem;
          font-size: 1.0625rem;
        }
        @media (forced-colors: active) {
          :where([data-citry-ui-part="pagination"] [data-citry-ui-part="control"][data-current]) {
            color: HighlightText;
            background: Highlight;
            border-color: Highlight;
          }
        }
      }
    """


__all__ = ["CPagination", "CPaginationChangeDetail", "CPaginationSize", "CPaginationVariant"]
