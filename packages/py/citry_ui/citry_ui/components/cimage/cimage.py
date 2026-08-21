"""Native-first responsive Image component."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, ClassVar, Literal, cast

from citry import LibraryComponent, SlotInput, const_value, merge_attrs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs

CImageFit = Literal["contain", "cover", "fill", "none", "scale-down"]
CImageLoading = Literal["eager", "lazy"]
CImageDecoding = Literal["auto", "sync", "async"]
CImageFetchPriority = Literal["auto", "high", "low"]
CImageCrossOrigin = Literal["anonymous", "use-credentials"]
CImageReferrerPolicy = Literal[
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
]
CImageStatus = Literal["loading", "loaded", "error"]

_FITS = ("contain", "cover", "fill", "none", "scale-down")
_LOADINGS = ("eager", "lazy")
_DECODINGS = ("auto", "sync", "async")
_FETCH_PRIORITIES = ("auto", "high", "low")
_CROSS_ORIGINS = ("anonymous", "use-credentials")
_REFERRER_POLICIES = (
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
)
_RUNTIME_PREFIXES = (
    "data-citry-",
    "data-cev",
    "data-cid",
    "data-has-alpine-state",
    "x-citry-",
)
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-data",
        "x-bind",
        "x-effect",
        "x-for",
        "x-html",
        "x-id",
        "x-if",
        "x-ignore",
        "x-init",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_ROOT_OWNED = frozenset(
    {
        "data-citry-ui-part",
        "data-citry-image-initialized",
        "data-fit",
        "data-has-fallback",
        "data-has-placeholder",
        "data-status",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_IMAGE_OWNED = frozenset(
    {
        "alt",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "contenteditable",
        "crossorigin",
        "data-citry-ui-part",
        "decoding",
        "draggable",
        "fetchpriority",
        "height",
        "hidden",
        "inert",
        "ismap",
        "loading",
        "popover",
        "referrerpolicy",
        "role",
        "sizes",
        "src",
        "srcset",
        "tabindex",
        "usemap",
        "width",
    }
)
_MIME_ESSENCE = re.compile(r"image/[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_WIDTH_DESCRIPTOR = re.compile(r"(?:^|,)\s*[^,]+\s+[1-9][0-9]*w\s*(?=,|$)")


@dataclass(frozen=True, slots=True)
class CImageSource:
    """Describe one ordered native ``picture`` source."""

    srcset: str
    media: str | None = None
    type: str | None = None
    sizes: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True, slots=True)
class CImageStatusChangeDetail:
    """Describe one normalized native image settlement."""

    status: CImageStatus
    src: str
    current_src: str
    natural_width: int
    natural_height: int


class _CImageVisualSlotData:
    pass


class _CImageVisualParser(HTMLParser):
    _VOID: ClassVar[set[str]] = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.visual_depth = 0
        self.invalid = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if self.visual_depth == 0:
            if values.get("data-citry-ui-part") in {"placeholder", "fallback"}:
                self.visual_depth = 1
            return
        if tag not in self._VOID:
            self.visual_depth += 1
        if (
            tag
            in {
                "button",
                "details",
                "embed",
                "iframe",
                "img",
                "input",
                "label",
                "object",
                "select",
                "textarea",
                "summary",
            }
            or (tag == "a" and "href" in values)
            or (tag == "area" and "href" in values)
            or (tag in {"audio", "video"} and "controls" in values)
            or "tabindex" in values
            or ("contenteditable" in values and (values["contenteditable"] or "").casefold() != "false")
        ):
            self.invalid = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        before = self.visual_depth
        self.handle_starttag(tag, attrs)
        self.visual_depth = before

    def handle_endtag(self, tag: str) -> None:  # noqa: ARG002
        if self.visual_depth:
            self.visual_depth -= 1


def _plain_string(
    name: str,
    value: object,
    *,
    optional: bool = False,
    empty: bool = False,
) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        expected = "a string or None" if optional else "a string"
        msg = f"CImage {name} must be {expected}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CImage could not normalize {name}."
        raise TypeError(msg)
    if any(ord(character) < 32 or ord(character) == 127 for character in plain):
        msg = f"CImage {name} cannot contain ASCII controls."
        raise ValueError(msg)
    if not empty and not plain:
        msg = f"CImage {name} must be non-empty."
        raise ValueError(msg)
    return plain


def _plain_url(name: str, value: object) -> str:
    plain = cast("str", _plain_string(name, value))
    normalized = plain.lstrip(" ").casefold()
    if normalized.startswith(("javascript:", "vbscript:")):
        msg = f"CImage {name} cannot use an active URL scheme."
        raise ValueError(msg)
    return plain


def _plain_srcset(name: str, value: object, *, optional: bool = False) -> str | None:
    plain = _plain_string(name, value, optional=optional)
    if plain is not None and any(
        candidate.casefold().startswith(("javascript:", "vbscript:")) for candidate in _srcset_urls(plain)
    ):
        msg = f"CImage {name} cannot use an active URL scheme."
        raise ValueError(msg)
    return plain


def _srcset_urls(value: str) -> tuple[str, ...]:
    urls: list[str] = []
    index = 0
    while index < len(value):
        while index < len(value) and (value[index].isspace() or value[index] == ","):
            index += 1
        start = index
        while index < len(value) and not value[index].isspace():
            index += 1
        candidate = value[start:index].rstrip(",")
        if candidate:
            urls.append(candidate)
        if index > start and value[index - 1] == ",":
            continue
        depth = 0
        while index < len(value):
            character = value[index]
            index += 1
            if character == "(":
                depth += 1
            elif character == ")" and depth:
                depth -= 1
            elif character == "," and depth == 0:
                break
    return tuple(urls)


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = cast("str", _plain_string(name, value))
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CImage {name} must be one of {expected}."
        raise ValueError(msg)
    return plain


def _positive_dimension(name: str, value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = f"CImage {name} must be a positive integer."
        raise TypeError(msg)
    if raw <= 0:
        msg = f"CImage {name} must be greater than zero."
        raise ValueError(msg)
    return raw


def _optional_dimension(name: str, value: object) -> int | None:
    raw = const_value(value)
    return None if raw is None else _positive_dimension(name, raw)


def _boolean(name: str, value: object) -> bool:
    raw = const_value(value)
    if not isinstance(raw, bool):
        msg = f"CImage {name} must be a bool."
        raise TypeError(msg)
    return bool(raw)


def _uses_width_descriptor(srcset: str | None) -> bool:
    return srcset is not None and _WIDTH_DESCRIPTOR.search(srcset) is not None


def _uses_auto_sizes(sizes: str | None) -> bool:
    if sizes is None:
        return False
    normalized = sizes.strip().casefold()
    return normalized == "auto" or normalized.startswith("auto,")


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    value: Mapping[str, object] | None,
    *,
    destination: str,
    owned: frozenset[str],
    reject_all_aria: bool,
) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        msg = f"CImage {destination} must be a mapping or None."
        raise TypeError(msg)
    copied = dict(value or {})
    for key in copied:
        if not isinstance(key, str):
            msg = f"CImage {destination} requires string attribute names."
            raise TypeError(msg)
        normalized = key.casefold()
        target = _dynamic_target(normalized)
        if (
            normalized in owned
            or (reject_all_aria and normalized.startswith("aria-"))
            or normalized.startswith(_RUNTIME_PREFIXES)
        ):
            msg = f"CImage {destination} cannot override owned attribute {key!r}."
            raise ValueError(msg)
        if normalized.startswith("on"):
            msg = f"CImage {destination} cannot use raw event attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CImage {destination} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if target in owned or (reject_all_aria and target is not None and target.startswith("aria-")):
            msg = f"CImage {destination} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


def _normalize_sources(
    value: Sequence[CImageSource],
    *,
    image_srcset: str | None,
    image_sizes: str | None,
    loading: str,
) -> tuple[dict[str, object], ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        msg = "CImage sources must be a sequence of CImageSource values."
        raise TypeError(msg)
    snapshot = tuple(value)
    if len(snapshot) > 32:
        msg = "CImage sources accepts at most 32 records."
        raise ValueError(msg)
    resolved: list[dict[str, object]] = []
    for index, source in enumerate(snapshot):
        if not isinstance(source, CImageSource):
            msg = f"CImage sources[{index}] must be CImageSource."
            raise TypeError(msg)
        srcset = _plain_srcset(f"sources[{index}].srcset", source.srcset)
        media = _plain_string(f"sources[{index}].media", source.media, optional=True)
        if media is not None and not media.strip(" \t\n\f\r"):
            msg = f"CImage sources[{index}].media must be non-empty."
            raise ValueError(msg)
        source_type = _plain_string(f"sources[{index}].type", source.type, optional=True)
        sizes = _plain_string(f"sources[{index}].sizes", source.sizes, optional=True)
        width = _optional_dimension(f"sources[{index}].width", source.width)
        height = _optional_dimension(f"sources[{index}].height", source.height)
        if (width is None) != (height is None):
            msg = f"CImage sources[{index}] width and height must be supplied together."
            raise ValueError(msg)
        if source_type is not None and _MIME_ESSENCE.fullmatch(source_type) is None:
            msg = f"CImage sources[{index}].type must be an image MIME essence."
            raise ValueError(msg)
        has_following_selector = index + 1 < len(snapshot) or image_srcset is not None
        useful_media = media is not None and media.strip().casefold() != "all"
        if has_following_selector and source_type is None and not useful_media:
            msg = f"CImage sources[{index}] requires type or a nontrivial media discriminator."
            raise ValueError(msg)
        if _uses_width_descriptor(cast("str", srcset)) and sizes is None:
            msg = f"CImage sources[{index}] width descriptors require sizes."
            raise ValueError(msg)
        if _uses_auto_sizes(sizes) and (loading != "lazy" or not _uses_auto_sizes(image_sizes)):
            msg = f"CImage sources[{index}] auto sizes requires a lazy image with auto sizes."
            raise ValueError(msg)
        resolved.append(
            {
                "srcset": srcset,
                "media": media,
                "type": source_type,
                "sizes": sizes,
                "width": width,
                "height": height,
            }
        )
    return tuple(resolved)


class CImage(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        src: str
        alt: str
        width: int
        height: int
        srcset: str | None = None
        sizes: str | None = None
        sources: Sequence[CImageSource] = ()
        loading: CImageLoading = "eager"
        decoding: CImageDecoding = "auto"
        fetch_priority: CImageFetchPriority = "auto"
        cross_origin: CImageCrossOrigin | None = None
        referrer_policy: CImageReferrerPolicy | None = None
        fit: CImageFit = "contain"
        position: str = "50% 50%"
        draggable: bool = False
        onStatusChange: Any | None = None  # noqa: N815 - public browser callback spelling
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        img_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        placeholder: SlotInput[_CImageVisualSlotData] | None = None
        fallback: SlotInput[_CImageVisualSlotData] | None = None

    def _normalized(self, kwargs: Kwargs) -> dict[str, object]:
        src = _plain_url("src", kwargs.src)
        alt = cast("str", _plain_string("alt", kwargs.alt, empty=True))
        width = _positive_dimension("width", kwargs.width)
        height = _positive_dimension("height", kwargs.height)
        srcset = _plain_srcset("srcset", kwargs.srcset, optional=True)
        sizes = cast("str | None", _plain_string("sizes", kwargs.sizes, optional=True))
        loading = _choice("loading", kwargs.loading, _LOADINGS)
        decoding = _choice("decoding", kwargs.decoding, _DECODINGS)
        fetch_priority = _choice("fetch_priority", kwargs.fetch_priority, _FETCH_PRIORITIES)
        cross_origin = (
            None if kwargs.cross_origin is None else _choice("cross_origin", kwargs.cross_origin, _CROSS_ORIGINS)
        )
        referrer_policy = (
            None
            if kwargs.referrer_policy is None
            else _choice("referrer_policy", kwargs.referrer_policy, _REFERRER_POLICIES)
        )
        fit = _choice("fit", kwargs.fit, _FITS)
        position = cast("str", _plain_string("position", kwargs.position))
        if any(character in position for character in ";{}\\"):
            msg = "CImage position cannot contain declaration-breaking characters."
            raise ValueError(msg)
        draggable = _boolean("draggable", kwargs.draggable)
        if _uses_width_descriptor(srcset) and sizes is None:
            msg = "CImage width-descriptor srcset requires sizes."
            raise ValueError(msg)
        if _uses_auto_sizes(sizes) and loading != "lazy":
            msg = "CImage auto sizes requires loading='lazy'."
            raise ValueError(msg)
        sources = _normalize_sources(
            kwargs.sources,
            image_srcset=srcset,
            image_sizes=sizes,
            loading=loading,
        )
        return {
            "src": src,
            "alt": alt,
            "width": width,
            "height": height,
            "srcset": srcset,
            "sizes": sizes,
            "sources": sources,
            "loading": loading,
            "decoding": decoding,
            "fetch_priority": fetch_priority,
            "cross_origin": cross_origin,
            "referrer_policy": referrer_policy,
            "fit": fit,
            "position": position,
            "draggable": draggable,
        }

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_image_snapshot", None)
        if cached is None:
            cached = self._normalized(kwargs)
            self._cui_image_snapshot = cached
        return cast("dict[str, object]", cached)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        data = dict(self._snapshot(kwargs))
        has_placeholder = "placeholder" in self.raw_slots
        has_fallback = "fallback" in self.raw_slots
        root_attrs = merge_root_attrs(
            _copy_attrs(
                kwargs.attrs,
                destination="attrs",
                owned=_ROOT_OWNED,
                reject_all_aria=True,
            ),
            kwargs.class_,
            kwargs.style,
        )
        root_attrs = merge_attrs(
            root_attrs,
            {
                "style": {
                    "--_cui-image-input-fit": data["fit"],
                    "--_cui-image-input-position": data["position"],
                }
            },
        )
        image_attrs = _copy_attrs(
            kwargs.img_attrs,
            destination="img_attrs",
            owned=_IMAGE_OWNED,
            reject_all_aria=False,
        )
        image_attrs.update(
            {
                "src": data["src"],
                "srcset": data["srcset"],
                "sizes": data["sizes"],
                "alt": data["alt"],
                "width": data["width"],
                "height": data["height"],
                "loading": data["loading"],
                "decoding": data["decoding"],
                "fetchpriority": data["fetch_priority"],
                "crossorigin": data["cross_origin"],
                "referrerpolicy": data["referrer_policy"],
                "draggable": "true" if data["draggable"] else "false",
            }
        )
        data.update(
            {
                "attrs": root_attrs,
                "image_attrs": image_attrs,
                "has_sources": bool(data["sources"]),
                "has_placeholder": has_placeholder,
                "has_fallback": has_fallback,
            }
        )
        return cast("dict[str, Any]", data)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        data = self._snapshot(kwargs)
        return {
            "src": data["src"],
            "alt": data["alt"],
            "width": data["width"],
            "height": data["height"],
            "srcset": data["srcset"],
            "sizes": data["sizes"],
            "sources": data["sources"],
            "loading": data["loading"],
            "decoding": data["decoding"],
            "fetchPriority": data["fetch_priority"],
            "crossOrigin": data["cross_origin"],
            "referrerPolicy": data["referrer_policy"],
            "fit": data["fit"],
            "position": data["position"],
            "draggable": data["draggable"],
            "hasPlaceholder": "placeholder" in self.raw_slots,
            "hasFallback": "fallback" in self.raw_slots,
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CImage completed without a render result.")
        parser = _CImageVisualParser()
        parser.feed(rendered.serialize(deps_strategy="ignore"))
        parser.close()
        if parser.invalid:
            raise ValueError("CImage placeholder and fallback slots cannot contain interactive or image content.")

    template = """
      <span
        class="cui-image"
        c-bind="attrs"
        data-citry-ui-part="image-root"
        c-data-fit="fit"
        c-data-has-placeholder="has_placeholder"
        c-data-has-fallback="has_fallback"
      >
        <c-if cond="has_sources">
          <picture data-citry-ui-part="picture">
            <source c-for="source in sources" c-bind="source" />
            <img c-bind="image_attrs" data-citry-ui-part="image" />
          </picture>
        </c-if>
        <c-else>
          <img c-bind="image_attrs" data-citry-ui-part="image" />
        </c-else>
        <c-if cond="has_placeholder">
          <span
            hidden
            inert
            aria-hidden="true"
            data-citry-ui-part="placeholder"
          >
            <c-slot name="placeholder" />
          </span>
        </c-if>
        <c-if cond="has_fallback">
          <span
            hidden
            inert
            aria-hidden="true"
            data-citry-ui-part="fallback"
          >
            <c-slot name="fallback" />
          </span>
        </c-if>
      </span>
    """

    js = """
      const imageReady = "data-citry-image-initialized";
      const imageOwner = Symbol.for("citry-ui:image-owner");
      const imageScopes = globalThis[Symbol.for("citry-ui:image-mutation-scopes")] ??= new WeakMap();
      const watchImage = (root, entry) => {
        let scope;
        let manager;
        let active = true;
        const detach = () => {
          if (manager?.entries.get(root) !== entry) return;
          manager.entries.delete(root);
          if (manager.entries.size === 0) {
            manager.observer.disconnect();
            imageScopes.delete(scope);
          }
        };
        const attach = () => {
          scope = root.getRootNode();
          manager = imageScopes.get(scope);
          if (!manager) {
            const entries = new Map();
            const observer = new MutationObserver((records) => {
              for (const record of records) {
                for (const node of record.addedNodes) {
                  if (!(node instanceof Element)) continue;
                  const candidates = node.hasAttribute(imageReady)
                    ? [node, ...node.querySelectorAll(`[${imageReady}]`)]
                    : [...node.querySelectorAll(`[${imageReady}]`)];
                  for (const candidate of candidates) {
                    if (!candidate[imageOwner]?.active) {
                      candidate.removeAttribute(imageReady);
                      candidate.removeAttribute("data-status");
                      for (const visual of candidate.querySelectorAll(
                        ':scope > [data-citry-ui-part="placeholder"], :scope > [data-citry-ui-part="fallback"]',
                      )) visual.hidden = true;
                    }
                  }
                }
              }
              for (const [candidate, registration] of [...entries]) {
                if (records.some((record) => record.target === candidate
                  || candidate.contains(record.target)
                  || [...record.addedNodes, ...record.removedNodes].some((node) =>
                    node === candidate || node.contains?.(candidate)))) registration.notify();
              }
            });
            observer.observe(scope instanceof Document ? scope.documentElement : scope, {
              subtree: true, childList: true, attributes: true,
            });
            manager = { entries, observer };
            imageScopes.set(scope, manager);
          }
          manager.entries.set(root, entry);
        };
        attach();
        return {
          refresh() {
            if (active && root.getRootNode() !== scope) {
              detach();
              attach();
            }
          },
          cleanup() {
            active = false;
            detach();
          },
        };
      };
      $component({
        props: {
          src: {}, alt: {}, width: {}, height: {}, srcset: {}, sizes: {},
          loading: {}, decoding: {}, fetchPriority: {}, crossOrigin: {},
          referrerPolicy: {}, fit: {}, position: {}, draggable: {},
          onStatusChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const handoffKey = Symbol.for("citry-ui:image-handoff");
          const previous = root?.[handoffKey] ?? null;
          if (previous?.abort !== null && previous?.abort !== undefined) clearTimeout(previous.abort);
          if (!previous) {
            root?.removeAttribute(imageReady);
            root?.removeAttribute("data-status");
          }
          const abortHandoff = (record) => {
            if (!record) return;
            if (record.abort !== null) clearTimeout(record.abort);
            record.root.removeAttribute(imageReady);
            record.root.removeAttribute("data-status");
            if (record.placeholder) record.placeholder.hidden = true;
            if (record.fallback) record.fallback.hidden = true;
            if (record.root[handoffKey] === record) delete record.root[handoffKey];
          };
          const picture = root.firstElementChild?.matches('[data-citry-ui-part="picture"]')
            ? root.firstElementChild : null;
          const image = picture
            ? picture.querySelector(':scope > [data-citry-ui-part="image"]')
            : root.querySelector(':scope > [data-citry-ui-part="image"]');
          const sourceElements = picture ? [...picture.children].slice(0, -1) : [];
          const placeholder = root.querySelector(':scope > [data-citry-ui-part="placeholder"]');
          const fallback = root.querySelector(':scope > [data-citry-ui-part="fallback"]');
          if (!(root instanceof HTMLSpanElement) || !(image instanceof HTMLImageElement)) {
            abortHandoff(previous);
            console.error("[citry-ui] CImage requires one native image and root.");
            return () => {};
          }
          const ownedElements = [root, picture, ...sourceElements, image, placeholder, fallback]
            .filter(Boolean);
          const frameworkMarker = (attribute) => attribute.name === "data-citry-root"
            || attribute.name === "data-has-alpine-state"
            || attribute.name.startsWith("data-cid")
            || attribute.name.startsWith("data-cev")
            || attribute.name.startsWith("x-citry-");
          const correlationValid = () => {
            const identifiers = (root.getAttribute("data-cid") ?? "").split(/\\s+/).filter(Boolean);
            const markers = [...root.attributes]
              .filter((attribute) => attribute.name.startsWith("data-cid-"))
              .map((attribute) => attribute.name.slice(9));
            const fillOwners = [root, placeholder, fallback].filter(Boolean);
            return root.getAttribute("data-citry-root") === ""
              && (!root.hasAttribute("data-has-alpine-state")
                || root.getAttribute("data-has-alpine-state") === "true")
              && (!root.hasAttribute("x-citry-boundary")
                || root.getAttribute("x-citry-boundary") === "")
              && identifiers.length === 1
              && markers.length === 1
              && markers[0] === identifiers[0]
              && ownedElements.slice(1).every((element) =>
                ![...element.attributes].some((attribute) => attribute.name.startsWith("data-cid"))
                && !element.hasAttribute("data-citry-root")
                && !element.hasAttribute("data-has-alpine-state")
                && !element.hasAttribute("x-citry-boundary"))
              && ownedElements.every((element) =>
                ![...element.attributes].some((attribute) => attribute.name.startsWith("data-cev")))
              && ownedElements.every((element) => [...element.attributes].every((attribute) =>
                !attribute.name.startsWith("x-citry-")
                || attribute.name === "x-citry-boundary"
                || (attribute.name === "x-citry-fill-source"
                  && fillOwners.includes(element)
                  && /^[0-9a-f]{64}:.+$/u.test(attribute.value))));
          };
          const frameworkBaseline = ownedElements.map((element) => JSON.stringify(
            [...element.attributes]
              .filter(frameworkMarker)
              .map((attribute) => [attribute.name, attribute.value])
              .sort(([left], [right]) => left.localeCompare(right)),
          ));
          const token = Symbol();
          const owner = { active: true, token };
          const documentOwner = root.ownerDocument;
          const invalid = new Set();
          const tasks = new Set();
          let active = true;
          let callback = null;
          let configuration = null;
          let generation = 0;
          let status = null;
          let settled = null;
          let decodeToken = null;
          let started = false;
          let watcher = null;

          const queue = (work) => {
            const marker = {};
            tasks.add(marker);
            queueMicrotask(() => {
              if (!tasks.delete(marker) || !active || root[imageOwner] !== owner) return;
              work();
            });
          };
          const describe = (value) => value === null ? "null" : typeof value;
          const report = (name, value) => {
            if (invalid.has(name)) return;
            invalid.add(name);
            console.error(
              `[citry-ui] CImage ${name} received an invalid ${describe(value)}; retaining the last valid value.`,
            );
          };
          const text = (name, optional = false, empty = false) => {
            const supplied = props[name];
            const value = supplied === undefined || (supplied === null && !optional) ? data[name] : supplied;
            if (
              (optional && value === null)
              || (typeof value === "string" && (empty || value.length > 0) && !/[\\u0000-\\u001f\\u007f]/.test(value))
            ) {
              invalid.delete(name);
              return value;
            }
            report(name, value);
            return configuration?.[name] ?? data[name];
          };
          const choice = (name, allowed, optional = false) => {
            const supplied = props[name];
            const value = supplied === undefined || (supplied === null && !optional) ? data[name] : supplied;
            if ((optional && value === null) || allowed.includes(value)) {
              invalid.delete(name);
              return value;
            }
            report(name, value);
            return configuration?.[name] ?? data[name];
          };
          const dimension = (name) => {
            const value = props[name] === undefined || props[name] === null ? data[name] : props[name];
            if (Number.isInteger(value) && value > 0) {
              invalid.delete(name);
              return value;
            }
            report(name, value);
            return configuration?.[name] ?? data[name];
          };
          const bool = (name) => {
            const value = props[name] === undefined || props[name] === null ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalid.delete(name);
              return value;
            }
            report(name, value);
            return configuration?.[name] ?? data[name];
          };
          const resolveCallback = () => {
            const value = props.onStatusChange;
            if (value === undefined || value === null || typeof value === "function") {
              invalid.delete("onStatusChange");
              return value ?? null;
            }
            report("onStatusChange", value);
            return callback;
          };
          const resolve = () => {
            const next = {
              src: text("src"),
              alt: text("alt", false, true),
              width: dimension("width"),
              height: dimension("height"),
              srcset: text("srcset", true),
              sizes: text("sizes", true),
              loading: choice("loading", ["eager", "lazy"]),
              decoding: choice("decoding", ["auto", "sync", "async"]),
              fetchPriority: choice("fetchPriority", ["auto", "high", "low"]),
              crossOrigin: choice("crossOrigin", ["anonymous", "use-credentials"], true),
              referrerPolicy: choice("referrerPolicy", [
                "no-referrer", "no-referrer-when-downgrade", "origin",
                "origin-when-cross-origin", "same-origin", "strict-origin",
                "strict-origin-when-cross-origin", "unsafe-url",
              ], true),
              fit: choice("fit", ["contain", "cover", "fill", "none", "scale-down"]),
              position: text("position"),
              draggable: bool("draggable"),
            };
            const activeSource = (value) => typeof value === "string"
              && /^\\s*(?:javascript|vbscript)\\s*:/i.test(value);
            const activeSet = (value) => {
              if (typeof value !== "string") return false;
              let index = 0;
              while (index < value.length) {
                while (index < value.length && (/[\\s,]/.test(value[index]))) index += 1;
                const start = index;
                while (index < value.length && !/\\s/.test(value[index])) index += 1;
                const candidate = value.slice(start, index).replace(/,+$/, "");
                if (/^(?:javascript|vbscript)\\s*:/i.test(candidate)) return true;
                if (index > start && value[index - 1] === ",") continue;
                let depth = 0;
                while (index < value.length) {
                  const character = value[index++];
                  if (character === "(") depth += 1;
                  else if (character === ")" && depth) depth -= 1;
                  else if (character === "," && depth === 0) break;
                }
              }
              return false;
            };
            if (activeSource(next.src)) {
              report("src", next.src);
              next.src = configuration?.src ?? data.src;
            }
            if (activeSet(next.srcset)) {
              report("srcset", next.srcset);
              next.srcset = configuration?.srcset ?? data.srcset;
            }
            const widthCandidates = typeof next.srcset === "string"
              && /(?:^|,)\\s*[^,]+\\s+[1-9][0-9]*w\\s*(?=,|$)/.test(next.srcset);
            const autoSizes = typeof next.sizes === "string"
              && /^auto(?:\\s*,|\\s*$)/i.test(next.sizes.trim());
            const sourceAutoSizes = data.sources.some((source) => typeof source.sizes === "string"
              && /^auto(?:\\s*,|\\s*$)/i.test(source.sizes.trim()));
            if (
              (widthCandidates && !next.sizes)
              || (autoSizes && next.loading !== "lazy")
              || (sourceAutoSizes && (next.loading !== "lazy" || !autoSizes))
            ) {
              report("responsive source", next.srcset);
              next.loading = configuration?.loading ?? data.loading;
              next.srcset = configuration?.srcset ?? data.srcset;
              next.sizes = configuration?.sizes ?? data.sizes;
            }
            if (/[;{}]/.test(next.position) || next.position.includes(String.fromCharCode(92))) {
              report("position", next.position);
              next.position = configuration?.position ?? data.position;
            }
            return next;
          };
          const fingerprint = (value) => JSON.stringify([
            value.src, value.srcset, value.sizes, value.width, data.sources,
            value.crossOrigin, value.referrerPolicy,
          ]);
          const sameAttribute = (element, name, value) => value === null
            ? !element.hasAttribute(name)
            : element.getAttribute(name) === String(value);
          const runtimeAttributesValid = (element, allowed) => [...element.attributes].every((attribute) =>
            !attribute.name.startsWith("data-citry-") || allowed.includes(attribute.name));
          const frameworkMarkersValid = () => ownedElements.every((element, index) => JSON.stringify(
            [...element.attributes]
              .filter(frameworkMarker)
              .map((attribute) => [attribute.name, attribute.value])
              .sort(([left], [right]) => left.localeCompare(right)),
          ) === frameworkBaseline[index]);
          const hasForbidden = (element, names, allAria = false) => [...element.attributes].some(
            (attribute) => names.includes(attribute.name)
              || (allAria && attribute.name.startsWith("aria-")),
          );
          const sourceValid = (element, value) => element instanceof HTMLSourceElement
            && ["srcset", "media", "type", "sizes", "width", "height"].every((name) =>
              sameAttribute(element, name, value[name]))
            && [...element.attributes].every((attribute) =>
              ["srcset", "media", "type", "sizes", "width", "height"].includes(attribute.name)
              || frameworkMarker(attribute));
          const serverImageValid = () => [
            ["src", data.src], ["srcset", data.srcset], ["sizes", data.sizes], ["alt", data.alt],
            ["width", data.width], ["height", data.height], ["loading", data.loading],
            ["decoding", data.decoding], ["fetchpriority", data.fetchPriority],
            ["crossorigin", data.crossOrigin], ["referrerpolicy", data.referrerPolicy],
            ["draggable", data.draggable ? "true" : "false"],
          ].every(([name, value]) => sameAttribute(image, name, value));
          const scopeValid = () => {
            const actual = root.getRootNode();
            return root.ownerDocument === documentOwner && (actual === documentOwner
              || (actual instanceof ShadowRoot
                && actual.host.ownerDocument === documentOwner
                && actual.host.shadowRoot === actual));
          };
          const anatomyValid = (requireReady = true) => {
            const first = picture ?? image;
            const expected = [first];
            if (data.hasPlaceholder) expected.push(placeholder);
            if (data.hasFallback) expected.push(fallback);
            const children = [...root.children];
            if (!scopeValid() || !correlationValid() || !frameworkMarkersValid()
              || children.length !== expected.length
              || children.some((child, index) => child !== expected[index])
              || root.dataset.citryUiPart !== "image-root"
              || Boolean(picture) !== Boolean(data.sources.length)
              || Boolean(placeholder) !== data.hasPlaceholder
              || Boolean(fallback) !== data.hasFallback
              || root.hasAttribute("data-has-placeholder") !== data.hasPlaceholder
              || root.hasAttribute("data-has-fallback") !== data.hasFallback
              || (!configuration && !serverImageValid())
              || !runtimeAttributesValid(root, ["data-citry-ui-part", "data-citry-root", imageReady])
              || !runtimeAttributesValid(image, ["data-citry-ui-part"])
              || hasForbidden(root, ["role", "tabindex", "hidden", "inert", "popover"], true)
              || hasForbidden(image, [
                "role", "tabindex", "hidden", "inert", "popover", "aria-hidden", "aria-label",
                "aria-labelledby", "contenteditable", "usemap", "ismap",
              ])
              || image.dataset.citryUiPart !== "image"
              || (requireReady && !root.hasAttribute(imageReady))) return false;
            if (picture) {
              if (picture.dataset.citryUiPart !== "picture"
                || !runtimeAttributesValid(picture, ["data-citry-ui-part"])
                || [...picture.attributes].some((attribute) => !(
                  attribute.name === "data-citry-ui-part"
                  || frameworkMarker(attribute)
                ))
                || picture.children.length !== data.sources.length + 1
                || picture.lastElementChild !== image
                || sourceElements.length !== data.sources.length
                || sourceElements.some((source, index) => !sourceValid(source, data.sources[index]))) return false;
            }
            for (const [visual, part] of [[placeholder, "placeholder"], [fallback, "fallback"]]) {
              if (visual && (visual.parentElement !== root || visual.dataset.citryUiPart !== part
                || visual.getAttribute("aria-hidden") !== "true" || !visual.hasAttribute("inert")
                || (!started && !previous && !visual.hidden)
                || visual.querySelector(
                  "a[href],area[href],button,details,embed,iframe,img,input,label,object,select,textarea,summary,[contenteditable]:not([contenteditable='false']),[tabindex],audio[controls],video[controls]",
                )
                || !runtimeAttributesValid(visual, ["data-citry-ui-part"])
                || [...visual.attributes].some((attribute) => !(
                  ["data-citry-ui-part", "hidden", "inert", "aria-hidden"].includes(attribute.name)
                  || frameworkMarker(attribute)
                )))) return false;
            }
            if (configuration && (
              !sameAttribute(image, "src", configuration.src)
              || !sameAttribute(image, "srcset", configuration.srcset)
              || !sameAttribute(image, "sizes", configuration.sizes)
              || !sameAttribute(image, "alt", configuration.alt)
              || !sameAttribute(image, "width", configuration.width)
              || !sameAttribute(image, "height", configuration.height)
              || !sameAttribute(image, "loading", configuration.loading)
              || !sameAttribute(image, "decoding", configuration.decoding)
              || !sameAttribute(image, "fetchpriority", configuration.fetchPriority)
              || !sameAttribute(image, "crossorigin", configuration.crossOrigin)
              || !sameAttribute(image, "referrerpolicy", configuration.referrerPolicy)
              || !sameAttribute(image, "draggable", configuration.draggable ? "true" : "false")
              || root.dataset.fit !== configuration.fit
              || root.style.getPropertyValue("--_cui-image-input-fit") !== configuration.fit
              || root.style.getPropertyValue("--_cui-image-input-position") !== configuration.position
              || root.dataset.status !== status
              || (placeholder && placeholder.hidden !== (status !== "loading"))
              || (fallback && fallback.hidden !== (status !== "error"))
            )) return false;
            return true;
          };
          const setAttribute = (name, value) => {
            if (value === null) image.removeAttribute(name);
            else if (image.getAttribute(name) !== String(value)) image.setAttribute(name, String(value));
          };
          const apply = (next) => {
            setAttribute("alt", next.alt);
            setAttribute("width", next.width);
            setAttribute("height", next.height);
            setAttribute("loading", next.loading);
            setAttribute("decoding", next.decoding);
            setAttribute("fetchpriority", next.fetchPriority);
            setAttribute("crossorigin", next.crossOrigin);
            setAttribute("referrerpolicy", next.referrerPolicy);
            setAttribute("draggable", next.draggable ? "true" : "false");
            setAttribute("srcset", next.srcset);
            setAttribute("sizes", next.sizes);
            setAttribute("src", next.src);
            root.dataset.fit = next.fit;
            root.style.setProperty("--_cui-image-input-fit", next.fit);
            root.style.setProperty("--_cui-image-input-position", next.position);
          };
          const detail = (nextStatus) => ({
            status: nextStatus,
            src: configuration.src,
            current_src: image.currentSrc || "",
            natural_width: image.naturalWidth,
            natural_height: image.naturalHeight,
          });
          const syncVisuals = () => {
            if (placeholder) placeholder.hidden = !(status === "loading");
            if (fallback) fallback.hidden = !(status === "error");
          };
          const notify = (nextStatus, currentGeneration) => {
            const snapshot = detail(nextStatus);
            queue(() => {
              if (currentGeneration !== generation) return;
              callback?.(snapshot);
            });
          };
          const setStatus = (nextStatus, currentGeneration, force = false) => {
            if (!force && status === nextStatus && settled
              && settled.currentSrc === image.currentSrc
              && settled.width === image.naturalWidth
              && settled.height === image.naturalHeight) return;
            status = nextStatus;
            settled = {
              currentSrc: image.currentSrc,
              width: image.naturalWidth,
              height: image.naturalHeight,
            };
            root.dataset.status = nextStatus;
            syncVisuals();
            notify(nextStatus, currentGeneration);
          };
          const accept = (nextStatus, currentGeneration, currentSrc) => {
            queue(() => {
              if (
                currentGeneration !== generation
                || image.currentSrc !== currentSrc
                || root[imageOwner] !== owner
              ) return;
              setStatus(nextStatus, currentGeneration);
            });
          };
          const reconcileComplete = (currentGeneration) => {
            if (currentGeneration !== generation || !image.complete || !image.currentSrc) return;
            const currentSrc = image.currentSrc;
            if (image.naturalWidth > 0) {
              accept("loaded", currentGeneration, currentSrc);
              return;
            }
            const probe = {};
            decodeToken = probe;
            if (typeof image.decode !== "function") {
              teardown(true);
              return;
            }
            try {
              const decoding = image.decode();
              const then = decoding?.then;
              if (typeof then !== "function") {
                teardown(true);
                return;
              }
              then.call(
                decoding,
                () => {
                  if (decodeToken === probe) accept("loaded", currentGeneration, currentSrc);
                },
                () => {
                  if (
                    decodeToken === probe
                    && image.complete
                    && image.currentSrc === currentSrc
                  ) accept("error", currentGeneration, currentSrc);
                },
              );
            } catch {
              teardown(true);
            }
          };
          const onLoad = (event) => {
            if (!event.isTrusted) return;
            const currentSrc = image.currentSrc;
            if (!currentSrc) return;
            decodeToken = null;
            accept("loaded", generation, currentSrc);
          };
          const onError = (event) => {
            if (!event.isTrusted) return;
            decodeToken = null;
            accept("error", generation, image.currentSrc);
          };
          if (!anatomyValid(false)) {
            abortHandoff(previous);
            console.error(
              "[citry-ui] CImage received invalid native anatomy; leaving the server fallback unchanged.",
            );
            return () => {};
          }
          const retained = Boolean(previous
            && previous.root === root
            && previous.documentOwner === documentOwner
            && previous.picture === picture
            && previous.image === image
            && previous.sourceElements.length === sourceElements.length
            && sourceElements.every((source, index) => source === previous.sourceElements[index]));
          if (previous && !retained) abortHandoff(previous);
          if (retained) delete root[handoffKey];
          image.addEventListener("load", onLoad);
          image.addEventListener("error", onError);
          root[imageOwner] = owner;

          const teardown = (diagnose = false) => {
            if (!active) return;
            active = false;
            owner.active = false;
            generation += 1;
            decodeToken = null;
            tasks.clear();
            image.removeEventListener("load", onLoad);
            image.removeEventListener("error", onError);
            watcher?.cleanup();
            if (root[imageOwner] === owner) {
              delete root[imageOwner];
              root.removeAttribute(imageReady);
              root.removeAttribute("data-status");
              if (placeholder) placeholder.hidden = true;
              if (fallback) fallback.hidden = true;
            }
            if (diagnose) console.error(
              "[citry-ui] CImage lost its owned native anatomy; component behavior was removed.",
            );
          };
          const registration = {
            notify() {
              if (!active) return;
              if (configuration) {
                if (root.style.getPropertyValue("--_cui-image-input-fit") !== configuration.fit) {
                  root.style.setProperty("--_cui-image-input-fit", configuration.fit);
                }
                if (root.style.getPropertyValue("--_cui-image-input-position") !== configuration.position) {
                  root.style.setProperty("--_cui-image-input-position", configuration.position);
                }
              }
              if (!root.isConnected) {
                teardown();
                return;
              }
              if (!anatomyValid()) {
                teardown(true);
                return;
              }
              watcher.refresh();
            },
          };
          watcher = watchImage(root, registration);

          effect(() => {
            if (!active) return;
            callback = resolveCallback();
            const next = resolve();
            const nextFingerprint = fingerprint(next);
            if (!started && retained && previous.fingerprint === nextFingerprint) {
              configuration = next;
              generation = previous.generation;
              status = previous.status;
              settled = previous.settled;
              started = true;
              apply(next);
              root.dataset.status = status;
              syncVisuals();
              root.setAttribute(imageReady, "");
              return;
            }
            if (!started && retained) generation = previous.generation;
            const changed = configuration === null || fingerprint(configuration) !== nextFingerprint;
            configuration = next;
            apply(next);
            if (!started || changed) {
              started = true;
              generation += 1;
              decodeToken = null;
              setStatus("loading", generation, true);
              const currentGeneration = generation;
              queue(() => reconcileComplete(currentGeneration));
            }
            root.setAttribute(imageReady, "");
          });

          return () => {
            if (!active) return;
            const ownsRoot = root[imageOwner] === owner;
            const canHandoff = ownsRoot && root.isConnected && anatomyValid();
            const record = canHandoff ? {
              root, picture, image, sourceElements: [...sourceElements], placeholder, fallback,
              documentOwner,
              fingerprint: fingerprint(configuration), configuration, generation,
              status, settled, abort: null,
            } : null;
            active = false;
            owner.active = false;
            generation += 1;
            decodeToken = null;
            tasks.clear();
            image.removeEventListener("load", onLoad);
            image.removeEventListener("error", onError);
            watcher?.cleanup();
            if (!ownsRoot) return;
            delete root[imageOwner];
            if (record) {
              root[handoffKey] = record;
              record.abort = setTimeout(() => {
                if (root[handoffKey] === record && !root[imageOwner]?.active) abortHandoff(record);
              }, 1000);
              return;
            }
            root.removeAttribute(imageReady);
            root.removeAttribute("data-status");
            if (placeholder) placeholder.hidden = true;
            if (fallback) fallback.hidden = true;
            delete root[handoffKey];
          };
        },
      });
    """

    css_file = "runtime.min.css"


__all__ = [
    "CImage",
    "CImageCrossOrigin",
    "CImageDecoding",
    "CImageFetchPriority",
    "CImageFit",
    "CImageLoading",
    "CImageReferrerPolicy",
    "CImageSource",
    "CImageStatus",
    "CImageStatusChangeDetail",
]
