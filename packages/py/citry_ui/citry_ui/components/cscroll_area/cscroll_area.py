"""Native viewport Scroll Area component family."""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, TypedDict

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._scroll_geometry import SCROLL_GEOMETRY_RUNTIME_DEPENDENCY

CScrollAreaAxis = Literal["block", "inline", "both"]
CScrollAreaScrollbarWidth = Literal["auto", "thin"]
CScrollAreaScrollbarGutter = Literal["auto", "stable", "stable-both-edges"]
CScrollAreaOverscroll = Literal["auto", "contain", "none"]


class CScrollAreaScrollDetail(TypedDict):
    inlineOffset: float
    blockOffset: float
    source: object


class _CScrollAreaDefaultSlotData:
    pass


_AXES = ("block", "inline", "both")
_SCROLLBAR_WIDTHS = ("auto", "thin")
_SCROLLBAR_GUTTERS = ("auto", "stable", "stable-both-edges")
_OVERSCROLL_VALUES = ("auto", "contain", "none")
_ASCII_WHITESPACE = "\t\n\f\r "
_IDREF_SPLIT = re.compile(r"[\t\n\f\r ]+")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_ALLOWED_ARIA = frozenset({"aria-describedby", "aria-details", "aria-keyshortcuts"})
_ALLOWED_PLAIN = frozenset({"class", "style", "lang", "dir", "title", "translate", "spellcheck"})
_ALLOWED_EVENTS = frozenset(
    {
        "blur",
        "focus",
        "pointercancel",
        "pointerdown",
        "pointerenter",
        "pointerleave",
        "pointermove",
        "pointerup",
        "scroll",
        "scrollend",
        "touchcancel",
        "touchend",
        "touchmove",
        "touchstart",
        "wheel",
    }
)
_LIFECYCLE_DIRECTIVES = frozenset(
    {
        "$c-props",
        "c-bind",
        "c-props",
        "x-bind",
        "x-data",
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


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        suffix = " or None" if optional else ""
        raise TypeError(f"CScrollArea {name} must be a string{suffix}, got {raw!r}.")
    plain = "".join(raw)
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"CScrollArea {name} must contain non-whitespace text without U+0000.")
    return plain


def _html_id(value: object, fallback: str) -> str:
    plain = _plain("id", value, optional=True) or fallback
    if any(character in _ASCII_WHITESPACE for character in plain):
        raise ValueError("CScrollArea id cannot contain ASCII whitespace.")
    return plain


def _labelledby(value: object) -> str | None:
    plain = _plain("aria_labelledby", value, optional=True)
    if plain is None:
        return None
    tokens = [token for token in _IDREF_SPLIT.split(plain) if token]
    if len(tokens) != len(set(tokens)):
        raise ValueError("CScrollArea aria_labelledby cannot contain duplicate IDREF tokens.")
    if not tokens or any(
        "\x00" in token or any(character in _ASCII_WHITESPACE for character in token) for token in tokens
    ):
        raise ValueError("CScrollArea aria_labelledby must contain valid IDREF tokens.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        raise TypeError(f"CScrollArea {name} must be a string, got {raw!r}.")
    if raw not in allowed:
        raise ValueError(f"CScrollArea {name} must be one of {allowed!r}, got {raw!r}.")
    return raw


def _event_name(attribute: str) -> str | None:
    modifiers = attribute.split(".")[1:]
    if any(modifier in {"away", "document", "outside", "window"} for modifier in modifiers):
        return None
    if attribute.startswith("@"):
        return attribute[1:].split(".", 1)[0]
    if attribute.startswith("x-on:"):
        return attribute.removeprefix("x-on:").split(".", 1)[0]
    return None


def _copy_attrs(value: Mapping[str, object] | None) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CScrollArea attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"CScrollArea attrs require string keys, got {key!r}.")
        name = key.casefold()
        event = _event_name(name)
        if name in _ALLOWED_PLAIN or name in _ALLOWED_ARIA:
            continue
        if event in _ALLOWED_EVENTS:
            continue
        if name.startswith("data-") and not name.startswith(_RUNTIME_PREFIXES):
            continue
        if name.split(".", 1)[0] in _LIFECYCLE_DIRECTIVES or name.startswith(("x-bind:", ":", ".")):
            raise ValueError(f"CScrollArea attrs cannot use ownership directive {key!r}.")
        raise ValueError(f"CScrollArea attrs cannot contain attribute {key!r} on its owned viewport.")
    return copied


class CScrollArea(LibraryComponent):
    class Dependencies:
        js: ClassVar = [SCROLL_GEOMETRY_RUNTIME_DEPENDENCY]

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        aria_label: str | None = None
        aria_labelledby: str | None = None
        axis: CScrollAreaAxis = "block"
        scrollbar_width: CScrollAreaScrollbarWidth = "auto"
        scrollbar_gutter: CScrollAreaScrollbarGutter = "auto"
        overscroll: CScrollAreaOverscroll = "auto"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[_CScrollAreaDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_scroll_area_snapshot", None)
        if cached is not None:
            return cached
        aria_label = _plain("aria_label", kwargs.aria_label, optional=True)
        aria_labelledby = _labelledby(kwargs.aria_labelledby)
        if aria_label is not None and aria_labelledby is not None:
            raise ValueError("CScrollArea aria_label and aria_labelledby are mutually exclusive.")
        root_id = _html_id(kwargs.id, f"cui-scroll-area-{self.id}")
        axis = _choice("axis", kwargs.axis, _AXES)
        scrollbar_width = _choice("scrollbar_width", kwargs.scrollbar_width, _SCROLLBAR_WIDTHS)
        scrollbar_gutter = _choice("scrollbar_gutter", kwargs.scrollbar_gutter, _SCROLLBAR_GUTTERS)
        overscroll = _choice("overscroll", kwargs.overscroll, _OVERSCROLL_VALUES)
        owned_style: CStyleValue = {"scroll-behavior": "auto !important"}
        if kwargs.style is not None:
            owned_style = (kwargs.style, owned_style)
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "role": "region" if aria_label is not None or aria_labelledby is not None else None,
            "aria_label": aria_label,
            "aria_labelledby": aria_labelledby,
            "axis": axis,
            "scrollbar_width": scrollbar_width,
            "scrollbar_gutter": scrollbar_gutter,
            "overscroll": overscroll,
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, owned_style),
        }
        self._cui_scroll_area_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "rootId": snapshot["root_id"],
            "role": snapshot["role"],
            "ariaLabel": snapshot["aria_label"],
            "ariaLabelledby": snapshot["aria_labelledby"],
            "axis": snapshot["axis"],
            "scrollbarWidth": snapshot["scrollbar_width"],
            "scrollbarGutter": snapshot["scrollbar_gutter"],
            "overscroll": snapshot["overscroll"],
        }

    template = """
      <div
        class="cui-scroll-area"
        c-id="root_id"
        c-bind="attrs"
        tabindex="0"
        c-role="role"
        c-aria-label="aria_label"
        c-aria-labelledby="aria_labelledby"
        c-data-axis="axis"
        c-data-scrollbar-width="scrollbar_width"
        c-data-scrollbar-gutter="scrollbar_gutter"
        c-data-overscroll="overscroll"
        data-citry-ui-part="scroll-area"
      ><c-slot /></div>
    """

    js = r"""
      $component({props:{axis:{},scrollbarWidth:{},scrollbarGutter:{},overscroll:{},onScrollChange:{}},init:({els:Y,data:n,props:j,effect:Z})=>{const t=Y[0],
      c=globalThis[Symbol.for("citry-ui:scroll-geometry")];
      if(c?.generation!==1)throw new Error("[citry-ui] CScrollArea scroll geometry dependency did not load.");
      const q=Symbol.for("citry-ui:scroll-area-handoff"),z=t[q]??null,h=z?.kind==="scroll-area"&&z.rootId===n.rootId,o=h?z:{kind:"scroll-area",rootId:n.rootId},
      E=Symbol(),ce="data-citry-scroll-area-initialized";
      o.owner=E,t[q]=o,t.removeAttribute(ce);
      const ye=e=>(e.startsWith("data-citry-")&&e!=="data-citry-ui-part"&&e!==ce)||e.startsWith("data-cid")||e.startsWith("data-cev"),
      be=()=>[...t.attributes].filter(e=>ye(e.name)),he=Object.fromEntries(be().map(e=>[e.name,e.value])),ge=()=>{const e=be();
      return e.length===Object.keys(he).length&&e.every(e=>he[e.name]===e.value)};
      let T=!0,x=0,I=null,v=null,y=null,O=0,s=null,p=!0,g=null,k=[],G=!0,d=h?o.direction:getComputedStyle(t).direction,a=h?o.configuration:null;
      const u=new Set,L=h?o.resolvers:{},b=h&&o.cache?o.cache:{inline:0,block:Math.max(0,t.scrollTop)};
      o.resolvers=L,o.cache=b;
      const m=()=>T&&o.owner===E,S=(e,r)=>{u.has(e)||(u.add(e),console.error(`[citry-ui] CScrollArea ${e} received invalid client value.`,r,t))},W=(e,r)=>{const l=L[e]??{last:n[e]};
      L[e]=l;
      const i=j[e];
      return i==null?(l.last=n[e],u.delete(e),l.last):r.includes(i)?(l.last=i,u.delete(e),i):(S(e,i),l.last)},_=()=>{const e=j.onScrollChange;
      return e==null?(u.delete("onScrollChange"),o.lastCallback=null,null):typeof e=="function"?(u.delete("onScrollChange"),o.lastCallback=e,e):(S("onScrollChange",
      e),o.lastCallback??null)},R=()=>c.maximum(t.scrollWidth,t.clientWidth),N=()=>c.maximum(t.scrollHeight,t.clientHeight),A=()=>({inline:c.horizontalFromRaw(t.scrollLeft,
      R(),d==="rtl"),block:c.clamp(t.scrollTop,N())}),M=e=>({inline:a?.axis==="block"?0:c.clamp(e.inline,R()),block:a?.axis==="inline"?0:c.clamp(e.block,N())}),
      F=(e,r)=>Math.abs(e.inline-r.inline)<=1&&Math.abs(e.block-r.block)<=1,f=()=>{y=null,O=++x},ee=()=>{const e=s;
      if(v=null,!m())return;
      p&&oe(),s===e&&(s=null);
      const r=y,l=O;
      if(y=null,r&&l===x&&I&&t.hasAttribute("data-citry-scroll-area-initialized")){const i=M(A());
      Object.assign(b,i),I(Object.freeze({inlineOffset:i.inline,blockOffset:i.block,source:r}))}(s||p||y)&&w()},w=()=>{v===null&&(v=requestAnimationFrame(ee))},P=(e,r=!0)=>{if(!m()||!t.isConnected)return;
      r&&f();
      const l=M(e),i=A();
      Object.assign(b,l),!F(i,l)&&(s={...l,revision:x},t.scrollLeft=c.horizontalToRaw(l.inline,R(),d==="rtl"),t.scrollTop=l.block,w())},D=e=>{if(!m())return;
      const r=getComputedStyle(t);
      if(r.direction!==d||r.writingMode!=="horizontal-tb"||!t.hasAttribute("data-citry-scroll-area-initialized")){p=!0,w();
      return}const l=M(A());
      if(Object.assign(b,l),s){const i=s;
      if(s=null,i.revision===x&&F(l,i))return}y=e,O=x,F(l,A())||P(l,!1),w()},H=e=>e==="id"?n.rootId:e==="role"?n.role:e==="aria-label"?n.ariaLabel:e==="aria-labelledby"?n.ariaLabelledby:e==="tabindex"?"0":e==="data-citry-ui-part"?"scroll-area":e==="data-axis"?a.axis:e==="data-scrollbar-width"?a.scrollbarWidth:e==="data-scrollbar-gutter"?a.scrollbarGutter:a.overscroll,
      V="id role aria-label aria-labelledby tabindex data-citry-ui-part data-axis data-scrollbar-width data-scrollbar-gutter data-overscroll".split(" "),K="aria-hidden aria-modal aria-orientation contenteditable hidden inert is name popover slot".split(" "),
      B="aria-describedby aria-details aria-keyshortcuts aria-label aria-labelledby".split(" "),te=/^(?:@|x-on:)(?:blur|focus|pointer(?:cancel|down|enter|leave|move|up)|scroll(?:end)?|touch(?:cancel|end|move|start)|wheel)(?:\.(?!(?:away|document|outside|window)(?:\.|$))[^.]+)*$/,
      J=e=>e.startsWith("@")||e.startsWith("x-on:")?!te.test(e):e.startsWith("x-")||e.startsWith(":")||e.startsWith(".")||["$c-props","c-bind","c-props"].includes(e)||e.startsWith("on"),
      re=()=>t.getRootNode().querySelectorAll(`#${CSS.escape(n.rootId)}`).length===1,Q=()=>V.every(e=>t.getAttribute(e)===H(e))&&K.every(e=>!t.hasAttribute(e))&&[...t.attributes].every(e=>!e.name.startsWith("aria-")||B.includes(e.name))&&[...t.attributes].every(e=>!J(e.name))&&ge()&&t.style.getPropertyValue("scroll-behavior").trim()==="auto"&&t.style.getPropertyPriority("scroll-behavior")==="important",
      U=()=>{const e=[];
      let r=t.parentNode;
      for(;
      r;
      )e.push(r),r=r instanceof ShadowRoot?r.host:r.parentNode;
      return e},$=()=>{g.disconnect(),k=U(),g.observe(t,{attributes:!0}),k.forEach(e=>{const r={childList:!0};
      e instanceof Element&&(r.attributes=!0,r.attributeFilter=["dir","class","style"]),g.observe(e,r)}),o.observedAncestors=k.length},X=e=>{g.disconnect(),
      e(),m()&&t.isConnected&&$()},le=()=>X(()=>{V.forEach(e=>{const r=H(e);
      r==null?t.removeAttribute(e):t.setAttribute(e,r)}),K.forEach(e=>t.removeAttribute(e)),[...t.attributes].forEach(e=>{e.name.startsWith("aria-")&&!B.includes(e.name)&&t.removeAttribute(e.name),
      (J(e.name)||ye(e.name)&&!Object.hasOwn(he,e.name))&&t.removeAttribute(e.name)}),Object.entries(he).forEach(([e,r])=>t.setAttribute(e,r)),t.style.setProperty("scroll-behavior","auto","important")}),C=e=>t.toggleAttribute(ce,
      e&&m()),oe=()=>{if(p=!1,!m()||!t.isConnected)return;
      const e=U();
      if((e.length!==k.length||e.some((i,ne)=>i!==k[ne]))&&$(),Q()?u.delete("attributes"):(C(!1),S("attributes",be()),le(),u.delete("attributes")),!re()){C(!1),S("id",n.rootId),f();
      return}u.delete("id");
      const r=getComputedStyle(t);
      if(r.writingMode!=="horizontal-tb"){C(!1),S("writingMode",r.writingMode),f();
      return}u.delete("writingMode");
      const l=r.direction;
      l!==d&&(d=l,f()),P(b,!1),C(!0),o.direction=d},de=()=>{if(!T)return;
      T=!1,g.disconnect(),t.removeEventListener("scroll",D),v!==null&&cancelAnimationFrame(v),v=null,y=null,s=null,o.owner===E&&(o.direction=d,o.observedAncestors=0,
      t.removeAttribute(ce),o.owner=null)},se=e=>e.forEach(e=>e.addedNodes.forEach(e=>{if(!(e instanceof Element))return;
      [e,...e.querySelectorAll(`[${ce}]`)].forEach(e=>{const r=e[q];
      e.hasAttribute(ce)&&!(r?.kind==="scroll-area"&&r.owner)&&e.removeAttribute(ce)})})),ie=e=>{se(e);
      if(m()){if(!t.isConnected){de();
      return}Q()||(C(!1),f()),p=!0,w()}};
      return g=new MutationObserver(ie),$(),t.addEventListener("scroll",D,{passive:!0}),Z(()=>{const e={axis:W("axis",["block","inline","both"]),scrollbarWidth:W("scrollbarWidth",
      ["auto","thin"]),scrollbarGutter:W("scrollbarGutter",["auto","stable","stable-both-edges"]),overscroll:W("overscroll",["auto","contain","none"])};
      I=_(),f(),a=e,o.configuration=a,G&&!h&&Object.assign(b,M(A())),G=!1,X(()=>{Object.assign(t.dataset,e),t.style.setProperty("scroll-behavior","auto","important")}),
      P(b),p=!0,w()}),de}});

    """
    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="scroll-area"]) {
          --_cui-scroll-area-max-block-size: var(--cui-scroll-area-max-block-size, 20rem);
          --_cui-scroll-area-background: var(--cui-scroll-area-background, Canvas);
          --_cui-scroll-area-foreground: var(--cui-scroll-area-foreground, CanvasText);
          --_cui-scroll-area-border-color: var(
            --cui-scroll-area-border-color,
            color-mix(in srgb, currentColor 24%, transparent)
          );
          --_cui-scroll-area-border-width: var(--cui-scroll-area-border-width, 1px);
          --_cui-scroll-area-radius: var(--cui-scroll-area-radius, 0.75rem);
          --_cui-scroll-area-padding: var(--cui-scroll-area-padding, 0px);
          --_cui-scroll-area-scrollbar-color: var(--cui-scroll-area-scrollbar-color, auto);
          --_cui-scroll-area-focus-color: var(--cui-scroll-area-focus-color, #2563eb);
          --_cui-scroll-area-scroll-padding: var(--cui-scroll-area-scroll-padding, 0px);
          display: block;
          box-sizing: border-box;
          inline-size: 100%;
          min-inline-size: 0;
          max-block-size: var(--_cui-scroll-area-max-block-size);
          padding: var(--_cui-scroll-area-padding);
          border: var(--_cui-scroll-area-border-width) solid var(--_cui-scroll-area-border-color);
          border-radius: var(--_cui-scroll-area-radius);
          color: var(--_cui-scroll-area-foreground);
          background: var(--_cui-scroll-area-background);
          scrollbar-color: var(--_cui-scroll-area-scrollbar-color);
          scroll-padding: var(--_cui-scroll-area-scroll-padding);
          scroll-behavior: auto !important;
          forced-color-adjust: auto;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="block"]) {
          overflow-block: auto;
          overflow-inline: hidden;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="inline"]) {
          max-block-size: none;
          overflow-block: hidden;
          overflow-inline: auto;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="both"]) {
          overflow: auto;
        }

        :where([data-citry-ui-part="scroll-area"][data-scrollbar-width="auto"]) {
          scrollbar-width: auto;
        }

        :where([data-citry-ui-part="scroll-area"][data-scrollbar-width="thin"]) {
          scrollbar-width: thin;
        }

        :where([data-citry-ui-part="scroll-area"][data-scrollbar-gutter="auto"]) {
          scrollbar-gutter: auto;
        }

        :where([data-citry-ui-part="scroll-area"][data-scrollbar-gutter="stable"]) {
          scrollbar-gutter: stable;
        }

        :where([data-citry-ui-part="scroll-area"][data-scrollbar-gutter="stable-both-edges"]) {
          scrollbar-gutter: stable both-edges;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="block"][data-overscroll="contain"]) {
          overscroll-behavior-block: contain;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="block"][data-overscroll="none"]) {
          overscroll-behavior-block: none;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="inline"][data-overscroll="contain"]) {
          overscroll-behavior-inline: contain;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="inline"][data-overscroll="none"]) {
          overscroll-behavior-inline: none;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="both"][data-overscroll="contain"]) {
          overscroll-behavior: contain;
        }

        :where([data-citry-ui-part="scroll-area"][data-axis="both"][data-overscroll="none"]) {
          overscroll-behavior: none;
        }

        :where([data-citry-ui-part="scroll-area"]:focus-visible) {
          outline: 3px solid var(--_cui-scroll-area-focus-color);
          outline-offset: 2px;
        }

        @media (forced-colors: active) {
          :where([data-citry-ui-part="scroll-area"]) {
            border-color: CanvasText;
            scrollbar-color: auto;
          }

          :where([data-citry-ui-part="scroll-area"]:focus-visible) {
            outline-color: Highlight;
          }
        }

        @media print {
          :where([data-citry-ui-part="scroll-area"]) {
            block-size: auto !important;
            max-block-size: none !important;
            overflow: visible !important;
            border: 0;
          }
        }
      }
    """


__all__ = [
    "CScrollArea",
    "CScrollAreaAxis",
    "CScrollAreaOverscroll",
    "CScrollAreaScrollDetail",
    "CScrollAreaScrollbarGutter",
    "CScrollAreaScrollbarWidth",
]
