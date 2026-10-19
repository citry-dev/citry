(function() {

__citryRuntime.registerTypeOptions.bind(null, "CScrollArea_a799e7", "df07d4d6d56fa3e7f0e0c657475fa466cef0691c41dfc54da95611830615af43")({props:{axis:{},scrollbarWidth:{},scrollbarGutter:{},overscroll:{},onScrollChange:{}},onServerRender:({component:Y})=>{const t=Y.$el,n={rootId:Y.rootId,role:Y.role,ariaLabel:Y.ariaLabel,ariaLabelledby:Y.ariaLabelledby,...Y.serverDefaults},j=Y.$props,Z=Citry.vue.watchEffect,
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
if(r.direction!==d||r.writingMode!=="horizontal-tb"||!t.hasAttribute("data-citry-scroll-area-initialized")||ae()){p=!0,w();
return}const l=M(A());
if(Object.assign(b,l),s){const i=s;
if(s=null,i.revision===x&&F(l,i))return}y=e,O=x,F(l,A())||P(l,!1),w()},H=e=>e==="id"?n.rootId:e==="role"?n.role:e==="aria-label"?n.ariaLabel:e==="aria-labelledby"?n.ariaLabelledby:e==="tabindex"?"0":e==="data-citry-ui-part"?"scroll-area":e==="data-axis"?a.axis:e==="data-scrollbar-width"?a.scrollbarWidth:e==="data-scrollbar-gutter"?a.scrollbarGutter:a.overscroll,
V="id role aria-label aria-labelledby tabindex data-citry-ui-part data-axis data-scrollbar-width data-scrollbar-gutter data-overscroll".split(" "),K="aria-hidden aria-modal aria-orientation contenteditable hidden inert is name popover slot".split(" "),
B="aria-describedby aria-details aria-keyshortcuts aria-label aria-labelledby".split(" "),J=e=>e.startsWith("@")||e.startsWith(":")||e.startsWith(".")||e==="c-bind"||e.startsWith("on"),
re=()=>/** @type {Document|DocumentFragment|Element} */(t.getRootNode()).querySelectorAll(`#${CSS.escape(n.rootId)}`).length===1,Q=()=>V.every(e=>t.getAttribute(e)===H(e))&&K.every(e=>!t.hasAttribute(e))&&[...t.attributes].every(e=>!e.name.startsWith("aria-")||B.includes(e.name))&&[...t.attributes].every(e=>!J(e.name))&&ge()&&t.style.getPropertyValue("scroll-behavior").trim()==="auto"&&t.style.getPropertyPriority("scroll-behavior")==="important",
U=()=>{const e=[];
let r=t.parentNode;
for(;
r;
)e.push(r),r=r instanceof ShadowRoot?r.host:r.parentNode;
return e},ae=()=>{const e=U();
return e.length!==k.length||e.some((r,l)=>r!==k[l])},$=()=>{g.disconnect(),k=U(),g.observe(t,{attributes:!0}),k.forEach(e=>{const r={childList:!0};
e instanceof Element&&(r.attributes=!0,r.attributeFilter=["dir","class","style"]),g.observe(e,r)}),o.observedAncestors=k.length},X=e=>{g.disconnect(),
e(),m()&&t.isConnected&&$()},le=()=>X(()=>{V.forEach(e=>{const r=H(e);
r==null?t.removeAttribute(e):t.setAttribute(e,r)}),K.forEach(e=>t.removeAttribute(e)),[...t.attributes].forEach(e=>{e.name.startsWith("aria-")&&!B.includes(e.name)&&t.removeAttribute(e.name),
(J(e.name)||ye(e.name)&&!Object.hasOwn(he,e.name))&&t.removeAttribute(e.name)}),Object.entries(he).forEach(([e,r])=>t.setAttribute(e,r)),t.style.setProperty("scroll-behavior","auto","important")}),C=e=>t.toggleAttribute(ce,
e&&m()),oe=()=>{if(p=!1,!m()||!t.isConnected)return;
if(ae()&&$(),Q()?u.delete("attributes"):(C(!1),S("attributes",be()),le(),u.delete("attributes")),!re()){C(!1),S("id",n.rootId),f();
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


})();