"""Image and fallback Avatar component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CAvatarVariant = Literal["soft", "solid", "outline"]
CAvatarSize = Literal["sm", "md", "lg"]
CAvatarShape = Literal["circle", "rounded", "square"]
CAvatarStatus = Literal["fallback", "loading", "loaded", "error"]

_VARIANTS = ("soft", "solid", "outline")
_SIZES = ("sm", "md", "lg")
_SHAPES = ("circle", "rounded", "square")
_EMPTY_IMAGE_SRC = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
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
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "contenteditable",
        "data-citry-ui-part",
        "data-shape",
        "data-size",
        "data-status",
        "data-variant",
        "role",
        "tabindex",
    }
)
_IMAGE_OWNED_ATTRS = frozenset(
    {
        "alt",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "data-citry-ui-part",
        "hidden",
        "onerror",
        "onload",
        "role",
        "sizes",
        "src",
        "srcset",
        "tabindex",
    }
)


class CAvatarDefaultSlotData:
    pass


def _plain_string(
    input_name: str,
    value: object,
    *,
    optional: bool = False,
    empty: bool = True,
) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"CAvatar {input_name} must be {expected}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CAvatar could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if "\x00" in plain:
        msg = f"CAvatar {input_name} cannot contain U+0000."
        raise ValueError(msg)
    if not empty and not plain:
        msg = f"CAvatar {input_name} must be non-empty when supplied."
        raise ValueError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = cast("str", _plain_string(input_name, value))
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CAvatar {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    attrs: Mapping[str, object] | None,
    *,
    destination: str,
    owned: frozenset[str],
    inert_only: bool = False,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CAvatar {destination} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"CAvatar {destination}")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CAvatar {destination} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CAvatar {destination} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if inert_only and normalized.startswith(("x-", "@", "on", ":", ".")):
            msg = f"CAvatar {destination} accepts inert image attributes only, got {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"CAvatar {destination} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CAvatar(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        src: str | None = None
        alt: str = ""
        variant: CAvatarVariant = "soft"
        size: CAvatarSize = "md"
        shape: CAvatarShape = "circle"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        img_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CAvatarDefaultSlotData] | None = None

    def _normalized(self, kwargs: Kwargs) -> dict[str, object]:
        return {
            "src": _plain_string("src", kwargs.src, optional=True, empty=False),
            "alt": _plain_string("alt", kwargs.alt),
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "shape": _plain_choice("shape", kwargs.shape, _SHAPES),
        }

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        data = self._normalized(kwargs)
        alt = cast("str", data["alt"])
        src = cast("str | None", data["src"])
        data.update(
            {
                "role": "img" if alt else None,
                "status": "loading" if src is not None else "fallback",
                "image_src": src or _EMPTY_IMAGE_SRC,
                "has_fallback": "default" in self.raw_slots,
                "attrs": merge_root_attrs(
                    _copy_attrs(
                        kwargs.attrs,
                        destination="attrs",
                        owned=_ROOT_OWNED_ATTRS,
                    ),
                    kwargs.class_,
                    kwargs.style,
                ),
                "img_attrs": _copy_attrs(
                    kwargs.img_attrs,
                    destination="img_attrs",
                    owned=_IMAGE_OWNED_ATTRS,
                    inert_only=True,
                ),
            }
        )
        return data

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        data = self._normalized(kwargs)
        data["empty_image_src"] = _EMPTY_IMAGE_SRC
        return data

    template = """
      <span
        class="cui-avatar"
        c-bind="attrs"
        data-citry-ui-part="avatar"
        c-data-variant="variant"
        c-data-size="size"
        c-data-shape="shape"
        c-data-status="status"
        c-role="role"
        c-aria-label="alt or None"
      >
        <span
          class="cui-avatar__fallback"
          aria-hidden="true"
          data-citry-ui-part="fallback"
        >
          <c-if cond="has_fallback">
            <c-slot />
          </c-if>
          <c-else>
            <svg
              class="cui-avatar__placeholder"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              focusable="false"
              aria-hidden="true"
            >
              <circle cx="12" cy="8" r="3.25"></circle>
              <path d="M5.75 19c.8-3.35 3.05-5 6.25-5s5.45 1.65 6.25 5"></path>
            </svg>
          </c-else>
        </span>
        <img
          class="cui-avatar__image"
          c-bind="img_attrs"
          data-citry-ui-part="image"
          alt=""
          c-src="image_src"
          c-hidden="src is None"
        />
      </span>
    """

    js = """
      $component({
        props: {
          src: {},
          alt: {},
          variant: {},
          size: {},
          shape: {},
          onStatusChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const image = root.querySelector('[data-citry-ui-part="image"]');
          const allowedValues = {
            variant: ["soft", "solid", "outline"],
            size: ["sm", "md", "lg"],
            shape: ["circle", "rounded", "square"],
          };
          const invalidEpisodes = new Set();
          let currentSource = data.src;
          let currentStatus = root.dataset.status;
          let sourceGeneration = 0;

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
            console.error(
              `[citry-ui] CAvatar ${name} received invalid client value `
                + `${describeValue(value)}; using the server-rendered fallback.`,
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
          const resolveText = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "string" && !value.includes("\\u0000")) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveSource = () => {
            const value = props.src === undefined ? data.src : props.src;
            if (value === null || (typeof value === "string" && value && !value.includes("\\u0000"))) {
              invalidEpisodes.delete("src");
              return value;
            }
            reportInvalid("src", value);
            return data.src;
          };
          const notifyStatus = (status, source) => {
            const callback = props.onStatusChange;
            if (callback === undefined || callback === null) {
              invalidEpisodes.delete("onStatusChange");
              return;
            }
            if (typeof callback !== "function") {
              reportInvalid("onStatusChange", callback);
              return;
            }
            invalidEpisodes.delete("onStatusChange");
            callback({status, src: source});
          };
          const setStatus = (status, source, notify = true) => {
            if (currentStatus === status && root.dataset.status === status) {
              return;
            }
            currentStatus = status;
            root.dataset.status = status;
            if (notify) {
              notifyStatus(status, source);
            }
          };
          const settleCurrentImage = (generation) => {
            if (generation !== sourceGeneration || currentSource === null) {
              return;
            }
            if (!image.complete) {
              return;
            }
            if (image.naturalWidth > 0) {
              image.hidden = false;
              setStatus("loaded", currentSource);
            } else {
              image.hidden = true;
              setStatus("error", currentSource);
            }
          };
          const onLoad = () => {
            if (currentSource === null) {
              return;
            }
            image.hidden = false;
            setStatus("loaded", currentSource);
          };
          const onError = () => {
            if (currentSource === null) {
              return;
            }
            image.hidden = true;
            setStatus("error", currentSource);
          };

          image.addEventListener("load", onLoad);
          image.addEventListener("error", onError);

          effect(() => {
            const source = resolveSource();
            const alt = resolveText("alt");
            const variant = resolveChoice("variant");
            const size = resolveChoice("size");
            const shape = resolveChoice("shape");

            root.dataset.variant = variant;
            root.dataset.size = size;
            root.dataset.shape = shape;
            if (alt) {
              root.setAttribute("role", "img");
              root.setAttribute("aria-label", alt);
            } else {
              root.removeAttribute("role");
              root.removeAttribute("aria-label");
            }

            if (source !== currentSource) {
              currentSource = source;
              sourceGeneration += 1;
              if (source === null) {
                image.setAttribute("src", data.empty_image_src);
                image.hidden = true;
                setStatus("fallback", null);
              } else {
                image.hidden = false;
                image.setAttribute("src", source);
                setStatus("loading", source);
                const generation = sourceGeneration;
                queueMicrotask(() => settleCurrentImage(generation));
              }
            } else {
              settleCurrentImage(sourceGeneration);
            }
          });

          root.dataset.citryAvatarInitialized = "";
          return () => {
            sourceGeneration += 1;
            image.removeEventListener("load", onLoad);
            image.removeEventListener("error", onError);
            delete root.dataset.citryAvatarInitialized;
          };
        },
      });
    """

    css_file = "runtime.min.css"
