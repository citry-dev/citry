"""Context Menu adapter over Citry UI's one Menu model."""

# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._anchored_layer import ANCHORED_LAYER_RUNTIME_DEPENDENCY
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import validate_boolean
from citry_ui.components.cmenu.cmenu import (
    _CMENU_SHARED_ASSETS,
    CMenuSize,
    _build_menu_root_snapshot,
)


class CContextMenuTargetSlotData:
    target_attrs: dict[str, object]


class CContextMenuMenuSlotData:
    pass


class CContextMenuOpenChangeDetail(TypedDict):
    reason: Literal[
        "contextmenu",
        "keyboard",
        "long-press",
        "escape",
        "outside",
        "focus-outside",
        "tab",
        "action",
        "native",
        "disabled",
        "ancestor",
    ]
    controlled: bool
    forced: bool
    source: object | None
    clientX: float
    clientY: float


_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
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
_ROOT_ATTRS = frozenset({"class", "dir", "lang", "style"})
_ROOT_RESERVED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-controls",
        "aria-expanded",
        "aria-disabled",
        "contenteditable",
        "data-disabled",
        "data-invocation",
        "data-open",
        "data-size",
        "disabled",
        "hidden",
        "id",
        "inert",
        "is",
        "popover",
        "role",
        "tabindex",
        "data-citry-ui-part",
    }
)
_TARGET_RESERVED = frozenset(
    {
        "aria-controls",
        "aria-expanded",
        "disabled",
        "hidden",
        "id",
        "inert",
        "is",
        "popover",
        "role",
        "data-citry-context-menu-target",
    }
)
_OWNED_EVENTS = frozenset(
    {
        "blur",
        "contextmenu",
        "focusin",
        "keydown",
        "pointercancel",
        "pointerdown",
        "pointermove",
        "pointerup",
        "scroll",
        "visibilitychange",
    }
)


def _plain_id(value: object, render_id: str) -> str:
    if value is None:
        return f"cui-context-menu-{render_id}"
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CContextMenu id must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CContextMenu id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CContextMenu id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_label(value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CContextMenu aria_label must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain.strip():
        msg = "CContextMenu aria_label must contain non-whitespace text."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CContextMenu aria_label cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _dynamic_target(name: str) -> str | None:
    if name.startswith("x-bind:"):
        return name.removeprefix("x-bind:").split(".", 1)[0]
    if name.startswith((":", ".")):
        return name[1:].split(".", 1)[0]
    return None


def _event_target(name: str) -> str | None:
    if name.startswith("x-on:"):
        return name.removeprefix("x-on:").split(".", 1)[0]
    if name.startswith("@"):
        return name[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    input_name: str,
    value: Mapping[str, object] | None,
    *,
    reserved: frozenset[str],
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        msg = f"CContextMenu {input_name} must be a mapping or None, got {value!r}."
        raise TypeError(msg)
    attrs = dict(value)
    allowed = _ROOT_ATTRS if input_name == "attrs" else None
    seen: set[str] = set()
    for key in attrs:
        if not isinstance(key, str):
            msg = f"CContextMenu {input_name} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized in seen:
            msg = f"CContextMenu {input_name} cannot contain duplicate case variants of {key!r}."
            raise ValueError(msg)
        seen.add(normalized)
        native_marker = input_name == "target_attrs" and normalized == "data-citry-context-menu-native"
        root_aria = input_name == "attrs" and normalized.startswith("aria-")
        if (root_aria or normalized.startswith(_RUNTIME_PREFIXES) or normalized in reserved) and not native_marker:
            msg = f"CContextMenu {input_name} cannot override owned attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"CContextMenu {input_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        event = _event_target(normalized)
        if event is not None:
            if event in _OWNED_EVENTS:
                msg = f"CContextMenu {input_name} cannot override owned event {event!r}."
                raise ValueError(msg)
            continue
        if normalized.startswith("on"):
            msg = f"CContextMenu {input_name} cannot use raw event attribute {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target is not None:
            native_target = input_name == "target_attrs" and target == "data-citry-context-menu-native"
            if (
                (input_name == "attrs" and target.startswith("aria-"))
                or target in reserved
                or target.startswith(_RUNTIME_PREFIXES)
            ) and not native_target:
                msg = f"CContextMenu {input_name} cannot dynamically bind attribute {target!r}."
                raise ValueError(msg)
            if allowed is not None and target not in allowed and not target.startswith(("aria-", "data-")):
                msg = f"CContextMenu {input_name} does not allow attribute {target!r}."
                raise ValueError(msg)
            continue
        if allowed is not None and normalized not in allowed and not normalized.startswith(("aria-", "data-")):
            msg = f"CContextMenu {input_name} does not allow attribute {key!r}."
            raise ValueError(msg)
    return attrs


def _adapt_python_target_slot(
    component: CContextMenu,
    slots: CContextMenu.Slots,
) -> None:
    """Give this family's Python target callback its frozen direct-data shape."""
    target = component.raw_slots.get("target")
    if target is None or target.extra.get("cui_context_target_adapter"):
        return
    content = target.content_func
    if getattr(content, "__module__", "").startswith("citry."):
        return

    adapted = Slot(
        target.contents,
        content_func=lambda context: content(context.data),
        component_name=target.component_name,
        slot_name=target.slot_name,
        source_position=target.source_position,
        extra={**target.extra, "cui_context_target_adapter": True},
    )
    component.raw_slots["target"] = adapted
    slots.target = adapted


@dataclass(slots=True)
class _MenuRootInputs:
    id: str
    open: bool
    disabled: bool
    loop: bool
    placement: Literal["bottom-start"]
    match_width: bool
    close_on_select: bool
    size: CMenuSize
    class_: None
    style: None
    attrs: None


class CContextMenu(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        aria_label: str
        id: str | None = None
        open: bool = False
        disabled: bool = False
        loop: bool = True
        close_on_select: bool = True
        size: CMenuSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        target_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        target: SlotInput[CContextMenuTargetSlotData]
        menu: SlotInput[CContextMenuMenuSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_context_menu_snapshot", None)
        if cached is not None:
            return cached
        base_id = _plain_id(kwargs.id, self.id)
        aria_label = _plain_label(kwargs.aria_label)
        validate_boolean("CContextMenu", "open", kwargs.open)
        validate_boolean("CContextMenu", "disabled", kwargs.disabled)
        validate_boolean("CContextMenu", "loop", kwargs.loop)
        validate_boolean("CContextMenu", "close_on_select", kwargs.close_on_select)
        size = const_value(kwargs.size)
        if size not in _SIZES:
            msg = f"CContextMenu size must be one of {_SIZES!r}, got {size!r}."
            raise ValueError(msg)
        root_attrs = _copy_attrs("attrs", kwargs.attrs, reserved=_ROOT_RESERVED)
        target_input_attrs = _copy_attrs(
            "target_attrs",
            kwargs.target_attrs,
            reserved=_TARGET_RESERVED,
        )
        surface_id = f"{base_id}-menu"
        menu = _build_menu_root_snapshot(
            self,
            _MenuRootInputs(
                id=surface_id,
                open=kwargs.open,
                disabled=kwargs.disabled,
                loop=kwargs.loop,
                placement="bottom-start",
                match_width=False,
                close_on_select=kwargs.close_on_select,
                size=size,
                class_=None,
                style=None,
                attrs=None,
            ),
            declaration_slot="menu",
            surface_aria_label=aria_label,
            allow_nested_owner=True,
        )
        activator_attrs = cast("dict[str, object]", menu["activator_attrs"])
        activator_style = cast("dict[str, object]", activator_attrs["style"])
        anchor_name = cast("str", activator_style["anchor-name"])
        target_id = f"{base_id}-target"
        point_id = f"{base_id}-point"
        target_attrs = dict(target_input_attrs)
        target_attrs.update(
            {
                "id": target_id,
                "data-citry-context-menu-target": "",
            }
        )
        point_attrs = {
            "id": point_id,
            "style": {
                "anchor-name": anchor_name,
            },
        }
        snapshot = {
            "root_id": base_id,
            "target_id": target_id,
            "point_id": point_id,
            "surface_id": surface_id,
            "aria_label": aria_label,
            "open": bool(kwargs.open) and not bool(kwargs.disabled),
            "disabled": bool(kwargs.disabled),
            "loop": bool(kwargs.loop),
            "close_on_select": bool(kwargs.close_on_select),
            "size": size,
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "target_attrs": target_attrs,
            "point_attrs": point_attrs,
            "point_anchor_name": anchor_name,
            "menu_surface": menu["menu_surface"],
        }
        self._cui_context_menu_snapshot = snapshot
        return snapshot

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        _adapt_python_target_slot(self, slots)
        return self._snapshot(kwargs)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        _adapt_python_target_slot(self, slots)
        snapshot = self._snapshot(kwargs)
        return {
            "rootId": snapshot["root_id"],
            "targetId": snapshot["target_id"],
            "pointId": snapshot["point_id"],
            "surfaceId": snapshot["surface_id"],
            "ariaLabel": snapshot["aria_label"],
            "open": snapshot["open"],
            "disabled": snapshot["disabled"],
            "loop": snapshot["loop"],
            "closeOnSelect": snapshot["close_on_select"],
            "size": snapshot["size"],
            "pointAnchorName": snapshot["point_anchor_name"],
        }

    template = """
      <div
        class="cui-context-menu-host"
        c-id="root_id"
        c-data-open="open"
        c-data-disabled="disabled"
        c-data-size="size"
        c-bind="root_attrs"
        data-citry-context-menu-host
        data-citry-ui-part="context-menu"
      >
        <c-slot
          name="target"
          c-target_attrs="target_attrs"
          required
        />
        <span
          c-bind="point_attrs"
          aria-hidden="true"
          popover="manual"
          data-citry-context-menu-point
        ></span>
        <c-CInternalMenuSurface c-surface="menu_surface">
          <c-slot name="menu" required />
        </c-CInternalMenuSurface>
      </div>
    """

    js = r"""
      const menuKey=Symbol.for("citry-ui:menu-root-runtime"),menuRuntime=globalThis[menuKey]
      ;if(1!==menuRuntime?.generation||1!==menuRuntime.helpers?.externalActivationVersion||"function"!=typeof menuRuntime.helpers?.hideNativePopover)throw new Error("[citry-ui] CContextMenu requires the compatible external Menu controller.")
      ;const mutationScopes=globalThis[Symbol.for("citry-ui:context-menu-mutations")]??=new WeakMap,watchMutations=(root,ready,owner,callback)=>{let scope,manager,active=!0;const entry={notify:callback}
      ;const attach=()=>{scope=root.getRootNode(),manager=mutationScopes.get(scope);if(!manager){const entries=new Map,observer=new MutationObserver(records=>{
      for(const record of records)for(const node of record.addedNodes)if(node instanceof Element)for(const candidate of[node,...node.querySelectorAll(`[${ready}]`)])candidate.hasAttribute(ready)&&!candidate[owner]?.active&&candidate.removeAttribute(ready)
      ;for(const[element,record]of entries)records.some(change=>change.target===element||element.contains(change.target)||[...change.addedNodes,...change.removedNodes].some(node=>node===element||node.contains?.(element)))&&record.notify(records)
      });observer.observe(scope instanceof Document?scope.documentElement:scope,{subtree:!0,childList:!0,attributes:!0}),manager={entries,observer},mutationScopes.set(scope,manager)}manager.entries.set(root,entry)}
      ;const detach=()=>{if(manager.entries.get(root)===entry){manager.entries.delete(root);if(0===manager.entries.size)manager.observer.disconnect(),mutationScopes.delete(scope)}}
      ;attach();return{refresh(){if(active&&root.getRootNode()!==scope)detach(),attach()},cleanup(){active=!1,detach()}}}
      ;$component({props:{open:{},disabled:{},loop:{},closeOnSelect:{},size:{},onOpenChange:{},onAction:{}},init:e=>{
      const{els:t,data:n,props:o,effect:r}=e,i=t[0],a=[...i.children],s=a[0],l=a[1],c=a[2],u="data-citry-context-menu-initialized",d=Symbol.for("citry-ui:context-menu-owner"),p=Symbol.for("citry-ui:context-menu-handoff"),f={
      active:!0};i.removeAttribute(u),i[d]=f;let m=!0,v=null,h=!1,g=!1,b=null,y=null,x=0,w=null,He=null,Ge=()=>{},Pt=()=>{},it=!1,at=!1,ot=!1,st=!1,pt=!1,ct=!1,vt=!1,mt=!1,yt=!1,Ft=null,It=!1,Ot=null,capInvalid=!1,St=null,Xt=[],E={disabled:n.disabled,
      loop:n.loop,closeOnSelect:n.closeOnSelect,size:n.size},O=null,R=null,N=null,A=null,L=null,k=null,C=null,S=null,I=null
      ;const T=new Set,M=new Set,tt=new Set;let z=i.getRootNode()
      ;const P=i.ownerDocument,q=P.defaultView,Zt=()=>{const e=(e,t)=>e instanceof Element?[...e.attributes].filter(e=>!t.includes(e.name)&&!e.name.startsWith("data-cid")&&!e.name.startsWith("data-cev")&&!["data-has-alpine-state","x-citry-fill-source"].includes(e.name)).map(e=>[e.name,e.value]).sort():null
      ;return JSON.stringify([e(i,[u,"id","data-open","data-disabled","data-size","data-invocation","data-citry-context-menu-host","data-citry-ui-part"]),e(s,["id","data-citry-context-menu-target"])])},F=JSON.stringify([n.rootId,n.targetId,n.pointId,n.surfaceId,n.ariaLabel,n.open,n.disabled,n.loop,n.closeOnSelect,n.size,Zt()]),D=i[p]??null,Ht=menuRuntime.helpers.hideNativePopover,Dt=e=>{const t=e?.surface??c,n=e?.point??l,o=e?.root??i;null!=e?.provisionalAbort&&(clearTimeout(e.provisionalAbort),e.provisionalAbort=null),Ht(t),t.inert=!0,t.removeAttribute("data-open"),t.removeAttribute("data-citry-menu-initialized"),Ht(n),o.removeAttribute("data-open"),o.removeAttribute("data-invocation"),delete t.__citryUiMenuRuntime,e&&(e.invocation=null,e.provisional=!1)},bt=Boolean(D?.provisional),X=Boolean(D&&D.fingerprint===F&&D.actualRoot===i.getRootNode()&&D.root===i&&D.target===s&&D.point===l&&D.surface===c);null!=D?.provisionalAbort&&(clearTimeout(D.provisionalAbort),D.provisionalAbort=null),D?.provisional&&!X&&Dt(D);if(!(s instanceof Element&&l instanceof Element&&c instanceof Element))return console.error("[citry-ui] CContextMenu requires one target, point, and Menu surface.",i),f.active=!1,i[d]===f&&(i[d]=null),()=>{};const Y=X?D:{
      fingerprint:F,actualRoot:i.getRootNode(),root:i,target:s,point:l,surface:c,invocation:null,menuSignature:null};Y.provisional=!1,Y.owner=f,i[p]=Y,mt=X&&Boolean(Y.invocation)
      ;const W=()=>m&&f.active&&i[d]===f&&Y.owner===f,$=(e,t=0)=>{const n=setTimeout(()=>{T.delete(n),W()&&e()},t)
      ;return T.add(n),n},rt=e=>{null!=e&&(clearTimeout(e),T.delete(e))},V=(e,t,n="")=>{
      M.has(e)||(M.add(e),console.error(`[citry-ui] CContextMenu ${e} received an invalid ${null===t?"null":typeof t}${n}.`,i))},B=e=>{
      const t=void 0===o[e]?n[e]:o[e];return"boolean"==typeof t?(M.delete(e),t):(V(e,t,"; using the server fallback"),n[e])
      },j=()=>{const e=void 0===o.size?n.size:o.size;return["sm","md","lg"].includes(e)?(M.delete("size"),
      e):(V("size",e,"; using the server fallback"),n.size)},U=()=>{let e=P.activeElement
      ;for(;e?.shadowRoot?.activeElement;)e=e.shadowRoot.activeElement;return e},H=()=>{
      const e=q?.visualViewport,t=e?.offsetLeft??0,n=e?.offsetTop??0;return{left:t,top:n,right:t+(e?.width??q.innerWidth),
      bottom:n+(e?.height??q.innerHeight)}},K=(e,t)=>{const n=H();return{x:Math.max(n.left,Math.min(n.right-1,e)),
      y:Math.max(n.top,Math.min(n.bottom-1,t))}},J=(e,t)=>{try{const n=i.getRootNode().querySelectorAll(`#${CSS.escape(e)}`)
      ;return 1===n.length&&n[0]===t}catch{return!1}
      },At=()=>{const e=i.getRootNode();return i.ownerDocument===P&&(e===P||e instanceof ShadowRoot&&"open"===e.mode&&e.host.shadowRoot===e&&e.host.ownerDocument===P)},G=()=>At()&&3===a.length&&3===[...i.children].length&&i.children[0]===s&&i.children[1]===l&&i.children[2]===c&&s instanceof HTMLElement&&!(s instanceof HTMLUnknownElement)&&!s.localName.includes("-")&&!s.hasAttribute("is")&&!s.shadowRoot&&s.getRootNode()===i.getRootNode()&&l.getRootNode()===i.getRootNode()&&c.getRootNode()===i.getRootNode(),Q=()=>G()&&s.id===n.targetId&&s.hasAttribute("data-citry-context-menu-target")&&l instanceof HTMLSpanElement&&l.id===n.pointId&&"manual"===l.getAttribute("popover")&&"true"===l.getAttribute("aria-hidden")&&l.hasAttribute("data-citry-context-menu-point")&&!l.hasAttribute("inert")&&0===l.childNodes.length&&[...l.attributes].every(e=>["id","popover","aria-hidden","data-citry-context-menu-point","style"].includes(e.name))&&l.style.getPropertyValue("anchor-name")===n.pointAnchorName&&[...l.style].every(e=>["anchor-name","left","top"].includes(e))&&c instanceof HTMLDivElement&&c.id===n.surfaceId&&"menu"===c.getAttribute("role")&&c.getAttribute("aria-label")===n.ariaLabel&&"manual"===c.getAttribute("popover")&&"menu"===c.dataset.citryUiPart&&i.id===n.rootId&&"context-menu"===i.dataset.citryUiPart&&i.hasAttribute("data-citry-context-menu-host")&&J(n.rootId,i)&&J(n.targetId,s)&&J(n.pointId,l)&&J(n.surfaceId,c),Z=()=>globalThis[menuKey]===menuRuntime&&"function"==typeof l.showPopover&&"function"==typeof l.hidePopover&&"function"==typeof c.showPopover&&"function"==typeof c.hidePopover&&CSS.supports("anchor-name: --cui-context-probe")&&CSS.supports("position-anchor: --cui-context-probe"),_=()=>E.disabled||s.matches?.(":disabled"),ee=()=>W()&&i.isConnected&&Q()&&Z()&&!_(),te=()=>{
      Ht(l)},ne=e=>{h=Boolean(e&&W()&&Q()&&Z()),h&&(vt=!0),i.toggleAttribute(u,h)
      },oe=()=>{O=null,R=null,Y.invocation=null,i.removeAttribute("data-invocation")},ge=()=>{A&&(v?.cancelOpenRequest(A.request),rt(A.task)),A=null,L=null,rt(k?.task),k=null,C=null,rt(S?.task),S=null,rt(I?.task),I=null,rt(Ot),Ot=null,It=!1,tt.clear(),x+=1,Ge();return x},be=(e,t=!1)=>{if(!(e instanceof Element&&e.isConnected&&!e.matches(":disabled")&&(!t||e.tabIndex>=0)&&e.getClientRects().length>0&&"hidden"!==getComputedStyle(e).visibility))return!1
      ;for(let n=e;n;n=n.parentElement??n.getRootNode()?.host)if(n.hasAttribute?.("hidden")||n.hasAttribute?.("inert"))return!1;return!0},re=(e="external",t=null,p=null)=>{
      const n=H(),o=U(),r=t instanceof Element&&s.contains(t)&&be(t)?t:o instanceof Element&&s.contains(o)&&be(o)?o:be(s)?s:null;if(!r)return null;const i=r.getBoundingClientRect(),a=Math.max(n.left,i.left),l=Math.min(n.right,i.right),u=Math.max(n.top,i.top),d=Math.min(n.bottom,i.bottom)
      ;let f=a,m=l,v=u,h=d;for(let e=r.parentElement;e;e=e.parentElement??e.getRootNode()?.host){const t=getComputedStyle(e),n=e.getBoundingClientRect(),o=n.width/(e.offsetWidth||n.width||1),i=n.height/(e.offsetHeight||n.height||1),a=n.left+e.clientLeft*o,l=a+e.clientWidth*o,u=n.top+e.clientTop*i,d=u+e.clientHeight*i;/(auto|scroll|hidden|clip)/.test(t.overflowX)&&(f=Math.max(f,a),m=Math.min(m,l)),/(auto|scroll|hidden|clip)/.test(t.overflowY)&&(v=Math.max(v,u),h=Math.min(h,d))}
      ;if(m<=f||h<=v)return null;const y=[],x=r.getRootNode(),w=x.elementsFromPoint?.bind(x)??P.elementsFromPoint.bind(P),A="none"===getComputedStyle(r).pointerEvents?{present:r.hasAttribute("style"),value:r.getAttribute("style")}:null,g="rtl"===getComputedStyle(c).direction,E=e=>w(e.x+.5,e.y+.5).some(e=>e===r||r.contains(e)),D={x:g?m-1:f,y:h-1};A&&r.style.setProperty("pointer-events","auto","important");try{if(E(D))y.push(D);else for(let e=0;e<9;e+=1)for(let t=0;t<9;t+=1){const n={x:f+(e+.5)*(m-f)/9-.5,y:v+(t+.5)*(h-v)/9-.5};E(n)&&y.push(n)}}finally{A&&(A.present?r.setAttribute("style",A.value??""):(r.style.removeProperty("pointer-events"),r.removeAttribute("style")))}if(!y.length)return null;y.sort((e,t)=>t.y-e.y||(g?t.x-e.x:e.x-t.x));const j=y[0];return{generation:p?.generation??ge(),kind:e,x:j.x,y:j.y,
      viewportX:j.x-n.left,viewportY:j.y-n.top,source:p?.source??t??r,returnFocus:p?.returnFocus??r,pointerId:p?.pointerId??null,pointerType:p?.pointerType??null}
      },ie=(e,t,n,o,r=null)=>{const i=H(),a=K(n+i.left,o+i.top),l=U();return{generation:ge(),kind:e,x:a.x,y:a.y,viewportX:a.x-i.left,
      viewportY:a.y-i.top,source:t,returnFocus:be(t,!0)?t:s.contains(l)&&be(l)?l:t,pointerId:r?.pointerId??null,
      pointerType:r?.pointerType??null}},ae=e=>{if(!(e&&W()&&Q()&&Z()))return!1;l.style.left=`${e.x}px`,l.style.top=`${e.y}px`,ct=!0
      ;try{l.matches(":popover-open")||l.showPopover()}catch(e){return te(),V("point",e,"; native Popover entry failed"),!1}finally{ct=!1}
      const t=l.getBoundingClientRect()
      ;const n=l.matches(":popover-open")&&Math.abs(t.left-e.x)<=1&&Math.abs(t.top-e.y)<=1&&t.width>0&&t.height>0;return n||te(),n},se=e=>{rt(Ot),Ot=null,O=e,N=null,
      R=null,Y.invocation={...e,source:null,returnFocus:e.returnFocus},i.dataset.invocation=e.kind},le=(e,t)=>{const n=e?R:O??N,r="disabled"===t.reason?s:t.source,d=Object.freeze({reason:t.reason,controlled:t.controlled,
      forced:t.forced,source:r,clientX:n?.x??0,clientY:n?.y??0}),a=U();e||(It=!0,rt(Ot),Ot=null);try{return w?.(e,d)}finally{!e&&t.controlled&&U()!==a&&(Ft=U()),e||(rt(A?.task),A=null,N=null,It=!1)}},ce=new Proxy(o,{
      get:(e,t)=>"onOpenChange"===t?le:Reflect.get(e,t)}),ue={...e,data:{...n,placement:"bottom-start",matchWidth:!1},props:ce
      },dt=new Set(["x-data","x-init","x-effect","x-id","x-if","x-for","x-show","x-ignore","x-teleport","x-html","x-text"]),et=new Set(["blur","contextmenu","focusin","keydown","pointercancel","pointerdown","pointermove","pointerup","scroll","visibilitychange"]),dn=e=>e.startsWith("x-bind:")?e.slice(7).split(".",1)[0]:e.startsWith(":")||e.startsWith(".")?e.slice(1).split(".",1)[0]:null,en=e=>e.startsWith("x-on:")?e.slice(5).split(".",1)[0]:e.startsWith("@")?e.slice(1).split(".",1)[0]:null,tn=s.getAttribute("role"),targetComponent=s.hasAttribute("data-citry-root")&&(s.getAttribute("data-cid")??"").split(/\s+/).some(e=>e&&s.hasAttribute(`data-cid-${e}`)),Tr=Object.fromEntries([...s.attributes].filter(e=>e.name.startsWith("data-cid")||e.name.startsWith("data-cev")||targetComponent&&e.name.startsWith("data-citry-")&&!["data-citry-context-menu-target","data-citry-context-menu-native"].includes(e.name)).map(e=>[e.name,e.value])),Pe=Object.fromEntries([...i.attributes].filter(e=>e.name.startsWith("data-cid")||e.name.startsWith("data-cev")||e.name.startsWith("data-citry-")&&!["data-citry-context-menu-host","data-citry-ui-part",u].includes(e.name)).map(e=>[e.name,e.value])),targetReady=targetComponent&&s.dataset.citryUiPart?`data-citry-${s.dataset.citryUiPart}-initialized`:null,ye=()=>{
      for(const e of s.attributes){const t=e.name,n=t.split(".",1)[0],o=dn(t),r=en(t)
      ;if("role"===t&&e.value!==tn||["aria-controls","aria-expanded","hidden","inert","is","popover"].includes(t)||dt.has(n)||r&&et.has(r)||o&&(["aria-controls","aria-expanded","hidden","inert","is","popover","role","disabled"].includes(o)||o.startsWith("data-citry-")&&"data-citry-context-menu-native"!==o))return!1
      ;if(t.startsWith("data-citry-")&&!["data-citry-context-menu-target","data-citry-context-menu-native"].includes(t)&&Tr[t]!==e.value){if(!vt&&t===targetReady&&""===e.value&&s._x_dataStack?.length)Tr[t]=e.value;else return!1}
      ;if((t.startsWith("data-cid")||t.startsWith("data-cev"))&&Tr[t]!==e.value)return!1}
      return s.getAttribute("role")===tn&&Object.entries(Tr).every(([e,t])=>s.getAttribute(e)===t)},qe=()=>{
      for(const e of i.attributes){const t=e.name,n=t.split(".",1)[0],o=dn(t),r=en(t)
      ;if(t.startsWith("aria-")||["role","tabindex","contenteditable","disabled","hidden","inert","is","popover"].includes(t)||dt.has(n)||r&&et.has(r)||o&&(o.startsWith("aria-")||["role","tabindex","contenteditable","disabled","hidden","inert","is","popover"].includes(o)))return!1
      ;if(t.startsWith("data-citry-")&&!["data-citry-context-menu-host","data-citry-ui-part",u].includes(t)&&Pe[t]!==e.value)return!1
      ;if((t.startsWith("data-cid")||t.startsWith("data-cev"))&&Pe[t]!==e.value)return!1}return Object.entries(Pe).every(([e,t])=>i.getAttribute(e)===t)},de=()=>{x+=1,N=null,rt(A?.task),A=null,L=null,rt(k?.task),k=null,C=null,rt(S?.task),S=null,rt(I?.task),I=null,rt(Ot),Ot=null,It=!1,tt.clear(),Ge()
      },pe=()=>Q()&&Z()&&qe()&&ye();if(!pe())return bt&&X&&Dt(Y),V("anatomy","invalid","; leaving the server fallback unchanged"),f.active=!1,
      i[d]===f&&(i[d]=null),()=>{};try{l.matches(":popover-open")||(l.showPopover(),l.hidePopover())}catch(e){
      return bt&&X&&Dt(Y),V("capability",e,"; leaving the server fallback unchanged"),f.active=!1,i[d]===f&&(i[d]=null),()=>{}}
      X&&Y.invocation&&(O=Y.invocation,i.dataset.invocation=O.kind);v=menuRuntime.mount(ue,{activationMode:"external",
      controller:!0,host:i,componentName:"CContextMenu",surface:c,trigger:l,disabledElement:s,insideElements:[s],
      ownerDisabled:_,validateOwner:pe,prepareOpen:()=>{if(!W()||!Q()||_())return!1
      ;if(O&&!R)return!(!l.matches(":popover-open")&&!ae(O))&&ee();if(l.matches(":popover-open")&&R)return!0
      ;const e=re("external");return!(!e||!ae(e))&&(se(e),ee())},focusReturnTarget:()=>be(O?.returnFocus)?O.returnFocus:be(O?.source)?O.source:be(s,!0)?s:null,
      shouldRestoreFocus:(e,t)=>Ft&&U()===Ft?(Ft=null,!1):(Ft=null,"escape"===e||"action"===e&&!(t instanceof HTMLAnchorElement)),committedOpen:e=>{W()&&(i.toggleAttribute("data-open",e),e&&O&&(i.dataset.invocation=O.kind),Ge())},closed:()=>{if(W()&&!mt){N=O;const e=N;te(),
      oe(),Ge(),$(()=>{N===e&&(N=null)})}},readyChanged:e=>{if(!W())return;if(!e&&mt){const e=Y.owner;$(()=>{Y.owner===e&&(mt=!1)})}if(e&&v){const e=v.declarationSignature();if(X&&null!==Y.menuSignature&&Y.menuSignature!==e){const e=w;w=null;try{v.forceClose("ancestor",s)}finally{w=e,O=null,Y.invocation=null,te()}}Y.menuSignature=e,mt=!1}!e||pe()?ne(e):ne(!1),e&&!yt&&(yt=!0,$(()=>Pt()))},disabledChanged(){W()&&(i.toggleAttribute("data-disabled",_()),
      _()&&de())}})
      ;const Qt=()=>i.hasAttribute(u)===h&&i.hasAttribute("data-open")===v.isOpen()&&i.hasAttribute("data-disabled")===_()&&i.dataset.size===E.size&&(v.isOpen()&&O?i.dataset.invocation===O.kind:!i.hasAttribute("data-invocation")),fe=e=>(e=>e.composedPath().find(e=>e instanceof Element&&e.hasAttribute("data-citry-context-menu-target")))(e)===s,me=e=>e.composedPath().find(e=>e instanceof Element)??s,ve=e=>{
      try{return e.intersectsNode(s)}catch{return!1}},he=()=>{const e=P.getSelection();if(!e)return!1
      ;if(z instanceof ShadowRoot){if("function"==typeof e.getComposedRanges)try{return e.getComposedRanges({shadowRoots:[z]}).some(e=>{
      const t=P.createRange();return t.setStart(e.startContainer,e.startOffset),t.setEnd(e.endContainer,e.endOffset),!t.collapsed&&Boolean(t.toString())&&ve(t)
      })}catch{const t=z.getSelection?.()??e;return Boolean(t.toString()||e.toString())}const t=z.getSelection?.()??e
      ;return Boolean(t.toString()||e.toString())}if(e.isCollapsed||!e.toString())return!1
      ;for(let t=0;t<e.rangeCount;t+=1)if(ve(e.getRangeAt(t)))return!0;return!1},xe=(e,t=!0)=>{if(t&&he())return!0
      for(const t of e.composedPath())if(t instanceof Element){
      if(t.hasAttribute("data-citry-context-menu-native")||t.isContentEditable||t.localName.includes("-")||t.hasAttribute("is")||t.shadowRoot||t.matches("a[href], input, textarea, select, option, [contenteditable]:not([contenteditable='false']), img, audio, video, iframe, embed, object"))return!0
      ;if(t===s)break}return!1},we=e=>{v.isOpen()&&v.forceClose("native",e)},Ee=e=>{
      if(W()&&A===e)if(!0===o.open&&v.isOpen())A=null;else{if(!0===o.open&&!e.awaitedReconcile)return e.awaitedReconcile=!0,
      void(e.task=$(()=>Ee(e)))
      ;A=null,v.cancelOpenRequest(e.request),oe(),te(),V("controlled-open",o.open,"; the synchronous true claim was not committed")
      }},De=e=>{const t=w;w=null;try{v.forceClose("ancestor",e)}catch{}finally{w=t,R=null,oe(),te()}},Oe=(e,t,n=null)=>{if(!ee()||!ae(e))return!1;R=e;let o;try{o=v.requestOpen(!0,t,e.source,null)}catch(t){De(e.source);throw t}
      ;if(o.same)return ee()?(se(e),v.focusRoot("first"),n?.preventDefault(),!0):(De(e.source),!1);if(o.controlled){
      if(!o.accepted||!0!==o.callbackResult||R!==e)return v.cancelOpenRequest(o.request),De(e.source),!1;if(!ee())return V("anatomy","invalid","; external owner structure is invalid after onOpenChange"),v.cancelOpenRequest(o.request),De(e.source),!1;se(e);const t={
      request:o.request,generation:e.generation,task:null,awaitedReconcile:!1};return A=t,t.task=$(()=>Ee(t)),
      n?.preventDefault(),!0}return o.accepted&&ee()&&v.isOpen()?(se(e),v.focusRoot("first"),n?.preventDefault(),!0):(R=null,
      De(e.source),!1)},Re=e=>{if(!e.isTrusted||!fe(e)||!Qe())return;const t=me(e);if(e.shiftKey)return void we(t);if(L){const t=L
      ;return L=null,void(t.accepted&&t.generation===x&&e.preventDefault())}const n=k?.selection??!0;k&&(rt(k.task),k=null),Le();if(xe(e,n)||_())return void we(t)
      ;const o=e.pointerType??"",r=["touch","pen"].includes(o)?"long-press":e.button<0?"keyboard":"contextmenu"
      ;if(I&&"long-press"===r&&I.generation===x&&(!(e.pointerId>0)||e.pointerId===I.pointerId)&&e.pointerType===I.pointerType&&e.composedPath().includes(I.source)&&Math.hypot(e.clientX-I.x,e.clientY-I.y)<=10)return void(v.isOpen()&&e.preventDefault())
      ;const i="keyboard"===r?re("keyboard",t):ie("long-press"===r?"long-press":"pointer",t,e.clientX,e.clientY,e)
      ;if(i&&Oe(i,r,e)&&"keyboard"!==r){const e=i.generation;Ot=$(()=>{
      Ot=null,v.isOpen()&&O?.generation===e&&v.focusRoot("first")})}},Ae=e=>{
      if(!e.isTrusted||e.repeat||e.isComposing||e.altKey||e.ctrlKey||e.metaKey||!fe(e)||!Qe()||!("ContextMenu"===e.key&&!e.shiftKey||"F10"===e.key&&e.shiftKey))return;const t=U()
      ;if(!(t instanceof Element&&s.contains(t)))return;if(xe(e)||_())return;const n=re("keyboard",t);if(!n)return;const o={
      accepted:Oe(n,"keyboard",e),generation:x};L=o,$(()=>{L===o&&(L=null)})},Le=()=>{rt(S?.task),S=null,Ge()
      },Ke=()=>{rt(I?.task),I=null,Ge()},je=()=>{Le(),Ke(),rt(k?.task),k=null,tt.clear(),Ge()
      },ke=e=>{if(!e.isTrusted||!fe(e)||!Qe())return;Ke();const t=me(e),n=["touch","pen"].includes(e.pointerType)
      ;if(n&&(tt.add(e.pointerId),Ge(),tt.size>1))return void Le();if(2===e.button){Le(),rt(k?.task);const n={pointerId:e.pointerId,selection:he(),
      focusSource:null,generation:x,task:null};return k=n,n.task=$(()=>{k===n&&(k=null,n.focusSource&&v.isOpen()&&v.requestOpen(!1,"focus-outside",n.focusSource,null),Ge())},1500),Ge(),
      void(e.shiftKey&&we(t))}
      if(0===e.button&&v.isOpen()){const e={generation:x};C=e,v.requestOpen(!1,"outside",t,null),$(()=>{C===e&&(C=null)})}
      if(0!==e.button||!n||!e.isPrimary||xe(e)||_())return;Le();const o={pointerId:e.pointerId,
      pointerType:e.pointerType,button:e.button,source:t,x:e.clientX,y:e.clientY,task:null};o.task=$(()=>(e=>{if(S!==e)return
      ;if(S=null,Ge(),!W()||!ee()||he())return;const t=ie("long-press",e.source,e.x,e.y,e);if(!Oe(t,"long-press"))return;const n={
      generation:t.generation,pointerId:e.pointerId,pointerType:e.pointerType,button:e.button,source:e.source,x:e.x,y:e.y,
      expires:performance.now()+1e4,task:null};I=n,n.task=$(()=>{I===n&&Ke()},1e4),Ge()})(o),700),S=o,Ge()},Ce=e=>{
      Qe()&&S&&e.pointerId===S.pointerId&&Math.hypot(e.clientX-S.x,e.clientY-S.y)>10&&Le()},Se=e=>{if(!Qe())return
      if(k?.pointerId===e.pointerId){const t=k;rt(t.task),k=null,t.focusSource&&v.isOpen()&&$(()=>{t.generation===x&&v.isOpen()&&v.requestOpen(!1,"focus-outside",t.focusSource,null)})}if(tt.delete(e.pointerId),S?.pointerId===e.pointerId&&Le(),"pointercancel"===e.type)return Ke(),void Ge()
      ;if(I?.pointerId===e.pointerId&&I.pointerType===e.pointerType){I.expires=Math.min(I.expires,performance.now()+1500)
      ;const e=I;rt(e.task),e.task=$(()=>{I===e&&Ke()},Math.max(0,e.expires-performance.now()))}Ge()},Ie=e=>{if(!Qe())return
      I&&e.isTrusted&&fe(e)&&I.generation===x&&e.pointerId===I.pointerId&&e.pointerType===I.pointerType&&e.button===I.button&&performance.now()<=I.expires&&e.composedPath().includes(I.source)&&Math.hypot(e.clientX-I.x,e.clientY-I.y)<=10&&(Ke(),
      e.preventDefault(),e.stopImmediatePropagation())},Ne=e=>{if(!Qe())return
      ;fe(e)&&v.isOpen()&&!It&&(k?k.focusSource=me(e):C||v.requestOpen(!1,"focus-outside",me(e),null))},Te=()=>{if(y=null,
      !Qe())return
      ;if(
      !W()||!v.isOpen()||!O)return;let e;if(["pointer","long-press"].includes(O.kind)){
      const t=H(),n=K(t.left+O.viewportX,t.top+O.viewportY);e={...O,...n}}else e=re(O.kind,O.source,O);e&&ae(e)?(O=e,
      Y.invocation=e):v.forceClose("ancestor",s)},Me=()=>{null===y&&(y=requestAnimationFrame(Te))},ze=()=>{P.hidden&&je()
      },Ue=()=>{Le(),v.isOpen()&&Me()},Gt=()=>{S&&he()&&Le()},Jt=e=>{e.isTrusted&&(S&&Le(),I&&Ke())};Ge=()=>{const e=Boolean(k||S||I||tt.size),t=Boolean(I),n=e||v.isOpen(),o=v.isOpen(),r=Boolean(S||I)
      ;if(e!==it){it=e;const t=e?"addEventListener":"removeEventListener";P[t]("pointermove",Ce,!0),P[t]("pointerup",Se,!0),P[t]("pointercancel",Se,!0),q[t]("blur",je),P[t]("visibilitychange",ze),P[t]("selectionchange",Gt)}
      if(t!==at){at=t,i[t?"addEventListener":"removeEventListener"]("click",Ie,!0)}if(n!==ot){ot=n;const e=n?"addEventListener":"removeEventListener";q[e]("scroll",Ue,!0),q.visualViewport?.[e]("scroll",Ue)}
      St&&(!n||St!==z)&&(St.removeEventListener("scroll",Ue,!0),St=null),n&&!St&&(St=z,St.addEventListener("scroll",Ue,!0))
      ;const a=[];if(n)for(let e=s.parentElement;e;e=e.parentElement??e.getRootNode()?.host)e!==i&&a.push(e)
      ;(a.length!==Xt.length||a.some((e,t)=>e!==Xt[t]))&&(Xt.forEach(e=>e.removeEventListener("scroll",Ue,!0)),Xt=a,Xt.forEach(e=>e.addEventListener("scroll",Ue,!0)))
      if(o!==st){st=o;const e=o?"addEventListener":"removeEventListener";q[e]("resize",Me),q.visualViewport?.[e]("resize",Me)}if(r!==pt)pt=r,P[r?"addEventListener":"removeEventListener"]("pointerdown",Jt,!0)}
      ;const Fe=()=>{if(W()){const e=!Z();if(!qe()||!ye()||!G()||e){if(e&&capInvalid)return;return capInvalid=e,ne(!1),de(),v.isOpen()?void v.forceClose("ancestor",s.isConnected?s:null):(Ht(c),te(),oe(),void i.removeAttribute("data-open"))}capInvalid=!1,g=!0,i.id=n.rootId,i.dataset.citryUiPart="context-menu",
      i.setAttribute("data-citry-context-menu-host",""),i.dataset.size=E.size,i.toggleAttribute("data-disabled",_()),
      i.toggleAttribute("data-open",v.isOpen()),v.isOpen()&&O?i.dataset.invocation=O.kind:i.removeAttribute("data-invocation"),
      s.id=n.targetId,s.setAttribute("data-citry-context-menu-target",""),l.id=n.pointId,l.setAttribute("popover","manual"),
      l.setAttribute("aria-hidden","true"),l.setAttribute("data-citry-context-menu-point",""),l.removeAttribute("inert"),
      [...l.style].filter(e=>!["anchor-name","left","top"].includes(e)).forEach(e=>l.style.removeProperty(e)),l.style.setProperty("anchor-name",n.pointAnchorName),
      R??(v.isOpen()?O:null)?ae(R??O):(l.style.removeProperty("left"),l.style.removeProperty("top")),
      c.id=n.surfaceId,c.setAttribute("popover","manual"),c.setAttribute("role","menu"),
      c.setAttribute("aria-label",n.ariaLabel),c.dataset.citryUiPart="menu",z=i.getRootNode(),v.repairOwned(),
      v.refreshRootScope(),g=!1,ne(c.hasAttribute("data-citry-menu-initialized"))}},Qe=()=>{if(capInvalid){if(!Z())return!1;capInvalid=!1,Fe()}if(!Q()||!qe()||!ye()||!Z())return Fe(),!1;return(!Qt()||!h&&c.hasAttribute("data-citry-menu-initialized"))&&Fe(),Qt()&&h}
      ;He=watchMutations(i,u,d,()=>{S&&Le();if(W()&&!g)if(i.isConnected){if(capInvalid){if(!Z())return;return capInvalid=!1,null===b&&(b=$(()=>{b=null,Fe()})),void 0}if(Q()&&qe()&&ye()&&Z())return(!Qt()||!h&&vt&&c.hasAttribute("data-citry-menu-initialized"))&&Fe(),z=i.getRootNode(),v.refreshRootScope(),Ge(),void He.refresh();ne(!1),Le(),
      null===b&&(b=$(()=>{b=null,Fe()}))}else We()}),i.addEventListener("contextmenu",Re,!0),i.addEventListener("keydown",Ae,!0),
      i.addEventListener("pointerdown",ke,!0),i.addEventListener("focusin",Ne,!0),Ge();const Be=e=>{if(e.target!==l||!W())return;if("closed"===e.oldState&&"open"===e.newState&&!ct&&!v.isOpen()&&!R)return void e.preventDefault();"open"===e.oldState&&"closed"===e.newState&&v.isOpen()&&(Ht(c),ne(!1),v.forceClose("ancestor",l))},Ye=()=>{
      if(!W())return;const e=l.matches(":popover-open");e&&!ct&&!v.isOpen()&&!R?te():v.isOpen()&&!e&&(ne(!1),v.forceClose("ancestor",l))};l.addEventListener("toggle",Ye),
      l.addEventListener("beforetoggle",Be),Pt=()=>{if(!Qe())return;E={disabled:B("disabled"),loop:B("loop"),closeOnSelect:B("closeOnSelect"),size:j()},w=(()=>{
      const e=o.onOpenChange;return null==e?(M.delete("onOpenChange"),null):"function"==typeof e?(M.delete("onOpenChange"),
      e):(V("onOpenChange",e,"; ignoring the callback"),null)})(),i.dataset.size=E.size,
      i.toggleAttribute("data-disabled",_()),_()&&de(),A&&!0!==o.open&&v.cancelOpenRequest(A.request),$(()=>Fe())},r(()=>{void o.open,void o.disabled,void o.loop,void o.closeOnSelect,void o.size,void o.onOpenChange,void o.onAction,Pt()})
      ;const We=()=>{if(m){m=!1,f.active=!1,N=null,He.cleanup(),i.removeEventListener("contextmenu",Re,!0),
      i.removeEventListener("keydown",Ae,!0),i.removeEventListener("pointerdown",ke,!0),
      P.removeEventListener("pointermove",Ce,!0),P.removeEventListener("pointerup",Se,!0),
      P.removeEventListener("pointercancel",Se,!0),P.removeEventListener("pointerdown",Jt,!0),i.removeEventListener("click",Ie,!0),
      i.removeEventListener("focusin",Ne,!0),q.removeEventListener("scroll",Ue,!0),St?.removeEventListener("scroll",Ue,!0),Xt.forEach(e=>e.removeEventListener("scroll",Ue,!0)),Xt=[],q.removeEventListener("resize",Me),
      q.removeEventListener("blur",je),q.visualViewport?.removeEventListener("scroll",Ue),
      q.visualViewport?.removeEventListener("resize",Me),P.removeEventListener("visibilitychange",ze),P.removeEventListener("selectionchange",Gt),
      l.removeEventListener("toggle",Ye),l.removeEventListener("beforetoggle",Be);for(const e of T)clearTimeout(e)
      ;T.clear(),null!==b&&clearTimeout(b),null!==y&&cancelAnimationFrame(y);const e=Y.owner===f,t=Y.root===i&&Y.target===s&&Y.point===l&&Y.surface===c,a=e&&i.isConnected&&pe(),o=!e&&t
      ;a&&(Y.invocation=O,Y.provisional=!0),v.cleanup({handoff:a||o}),e&&(a||(te(),Y.invocation=null),Y.owner=null),a&&(Y.provisionalAbort=setTimeout(()=>{i[p]===Y&&Y.provisional&&!Y.owner&&Dt(Y)},1e3)),i[d]===f&&(i.removeAttribute(u),i[d]=null)} }
      ;return We}});
    """
    css = """
      @layer citry-ui.theme {
        :where(.cui-context-menu-host) {
          display: contents;
        }

        :where([data-citry-context-menu-point]) {
          position: fixed;
          inset: auto;
          width: 1px;
          height: 1px;
          margin: 0;
          padding: 0;
          border: 0;
          background: transparent;
          overflow: visible;
          pointer-events: none;
        }

        @media print {
          :where([data-citry-context-menu-point]) {
            display: none !important;
          }
        }
      }
    """


class _CContextMenuDependencies:
    js: ClassVar = [ANCHORED_LAYER_RUNTIME_DEPENDENCY, _CMENU_SHARED_ASSETS.runtime]
    css: ClassVar = [_CMENU_SHARED_ASSETS.style]


CContextMenu.Dependencies = _CContextMenuDependencies


__all__ = [
    "CContextMenu",
    "CContextMenuMenuSlotData",
    "CContextMenuOpenChangeDetail",
    "CContextMenuTargetSlotData",
]
