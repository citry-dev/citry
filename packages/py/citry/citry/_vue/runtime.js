/* Citry interactive runtime. GENERATED FILE, do not edit: Vue runtime, prepared coordinator, then Events bridge. */
(function (global) {
if (!global.CitryStable) {
/* Citry Vue runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-vue.ts (pnpm run build there). Bundles Vue 3.5.42 runtime-only (MIT). */
var Vue=(()=>{var fr=Object.defineProperty;var Vc=Object.getOwnPropertyDescriptor;var xc=Object.getOwnPropertyNames;var Ac=Object.prototype.hasOwnProperty;var Rc=(e,t)=>{for(var n in t)fr(e,n,{get:t[n],enumerable:!0})},Pc=(e,t,n,s)=>{if(t&&typeof t=="object"||typeof t=="function")for(let r of xc(t))!Ac.call(e,r)&&r!==n&&fr(e,r,{get:()=>t[r],enumerable:!(s=Vc(t,r))||s.enumerable});return e};var kc=e=>Pc(fr({},"__esModule",{value:!0}),e);var _p={};Rc(_p,{BaseTransition:()=>Xr,BaseTransitionPropsValidators:()=>Ys,Comment:()=>pe,DeprecationTypes:()=>wf,EffectScope:()=>Mt,ErrorCodes:()=>ma,ErrorTypeStrings:()=>mf,Fragment:()=>ve,KeepAlive:()=>nu,ReactiveEffect:()=>ct,Static:()=>ft,Suspense:()=>qu,Teleport:()=>Pa,Text:()=>Ot,TrackOpTypes:()=>pi,Transition:()=>Cf,TransitionGroup:()=>ep,TriggerOpTypes:()=>di,VueElement:()=>or,assertNumber:()=>_a,callWithAsyncErrorHandling:()=>Ie,callWithErrorHandling:()=>zt,camelize:()=>ae,capitalize:()=>Et,cloneVNode:()=>st,compatUtils:()=>Of,compile:()=>gp,computed:()=>Rl,createApp:()=>vo,createBlock:()=>Fs,createCommentVNode:()=>Ol,createElementBlock:()=>tf,createElementVNode:()=>ao,createHydrationRenderer:()=>lo,createPropsRestProxy:()=>wu,createRenderer:()=>io,createSSRApp:()=>wc,createSlots:()=>au,createStaticVNode:()=>of,createTextVNode:()=>uo,createVNode:()=>ce,customRef:()=>Ns,defineAsyncComponent:()=>eu,defineComponent:()=>Gs,defineCustomElement:()=>fc,defineEmits:()=>hu,defineExpose:()=>gu,defineModel:()=>Eu,defineOptions:()=>_u,defineProps:()=>du,defineSSRCustomElement:()=>zf,defineSlots:()=>mu,devtools:()=>Ef,effect:()=>qo,effectScope:()=>jo,getCurrentInstance:()=>Ce,getCurrentScope:()=>Vr,getCurrentWatcher:()=>hi,getTransitionRawChildren:()=>qn,guardReactiveProps:()=>bl,h:()=>fo,handleError:()=>qt,hasInjectionContext:()=>Da,hydrate:()=>dp,hydrateOnIdle:()=>za,hydrateOnInteraction:()=>Za,hydrateOnMediaQuery:()=>Xa,hydrateOnVisible:()=>Ja,initCustomFormatter:()=>gf,initDirectivesForSSR:()=>hp,inject:()=>Fn,isMemoSame:()=>Pl,isProxy:()=>$t,isReactive:()=>Ue,isReadonly:()=>Pe,isRef:()=>ue,isRuntimeOnly:()=>Cl,isShallow:()=>Ee,isVNode:()=>dt,markRaw:()=>ys,mergeDefaults:()=>bu,mergeModels:()=>Ou,mergeProps:()=>wl,nextTick:()=>Gn,nodeOps:()=>sc,normalizeClass:()=>Pt,normalizeProps:()=>Mo,normalizeStyle:()=>Rt,onActivated:()=>Wi,onBeforeMount:()=>zi,onBeforeUnmount:()=>Js,onBeforeUpdate:()=>qs,onDeactivated:()=>Yi,onErrorCaptured:()=>Zi,onMounted:()=>gn,onRenderTracked:()=>Xi,onRenderTriggered:()=>Ji,onScopeDispose:()=>Bo,onServerPrefetch:()=>qi,onUnmounted:()=>_n,onUpdated:()=>Xn,onWatcherCleanup:()=>Pr,openBlock:()=>Kn,patchProp:()=>uc,popScopeId:()=>Oa,provide:()=>Ii,proxyRefs:()=>Pn,pushScopeId:()=>ba,queuePostFlushCb:()=>hn,reactive:()=>on,readonly:()=>An,ref:()=>Ft,registerRuntimeCompiler:()=>uf,render:()=>Oc,renderList:()=>cu,renderSlot:()=>uu,resolveComponent:()=>ou,resolveDirective:()=>lu,resolveDynamicComponent:()=>iu,resolveFilter:()=>bf,resolveTransitionHooks:()=>Wt,setBlockTracking:()=>Wn,setDevtoolsHook:()=>yf,setTransitionHooks:()=>nt,shallowReactive:()=>ms,shallowReadonly:()=>ri,shallowRef:()=>vs,ssrContextKey:()=>$i,ssrUtils:()=>Nf,stop:()=>Jo,toDisplayString:()=>gr,toHandlerKey:()=>At,toHandlers:()=>fu,toRaw:()=>z,toRef:()=>ai,toRefs:()=>ci,toValue:()=>li,transformVNodeArgs:()=>sf,triggerRef:()=>ii,unref:()=>Lt,useAttrs:()=>Nu,useCssModule:()=>Xf,useCssVars:()=>Pf,useHost:()=>pc,useId:()=>Ma,useModel:()=>Pu,useSSRContext:()=>Fi,useShadowRoot:()=>Jf,useSlots:()=>vu,useTemplateRef:()=>Ia,useTransitionState:()=>Ws,vModelCheckbox:()=>bo,vModelDynamic:()=>Ec,vModelRadio:()=>Oo,vModelSelect:()=>_c,vModelText:()=>lr,vShow:()=>cc,version:()=>kl,warn:()=>Ml,watch:()=>Bt,watchEffect:()=>Sa,watchPostEffect:()=>Ca,watchSyncEffect:()=>Li,withAsyncContext:()=>Tu,withCtx:()=>Jr,withDefaults:()=>yu,withDirectives:()=>Ta,withKeys:()=>pp,withMemo:()=>_f,withModifiers:()=>up,withScopeId:()=>wa});/**
* @vue/shared v3.5.42
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/function Ct(e){let t=Object.create(null);for(let n of e.split(","))t[n]=1;return n=>n in t}var J={},Vt=[],Te=()=>{},dr=()=>!1,xt=e=>e.charCodeAt(0)===111&&e.charCodeAt(1)===110&&(e.charCodeAt(2)>122||e.charCodeAt(2)<97),Zt=e=>e.startsWith("onUpdate:"),Q=Object.assign,bn=(e,t)=>{let n=e.indexOf(t);n>-1&&e.splice(n,1)},Mc=Object.prototype.hasOwnProperty,ee=(e,t)=>Mc.call(e,t),F=Array.isArray,it=e=>Qt(e)==="[object Map]",He=e=>Qt(e)==="[object Set]",Vo=e=>Qt(e)==="[object Date]",Ro=e=>Qt(e)==="[object RegExp]",B=e=>typeof e=="function",se=e=>typeof e=="string",we=e=>typeof e=="symbol",Z=e=>e!==null&&typeof e=="object",rs=e=>(Z(e)||B(e))&&B(e.then)&&B(e.catch),Po=Object.prototype.toString,Qt=e=>Po.call(e),hr=e=>Qt(e).slice(8,-1),en=e=>Qt(e)==="[object Object]",On=e=>se(e)&&e!=="NaN"&&e[0]!=="-"&&""+parseInt(e,10)===e,mt=Ct(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted");var os=e=>{let t=Object.create(null);return(n=>t[n]||(t[n]=e(n)))},Ic=/-\w/g,ae=os(e=>e.replace(Ic,t=>t.slice(1).toUpperCase())),$c=/\B([A-Z])/g,De=os(e=>e.replace($c,"-$1").toLowerCase()),Et=os(e=>e.charAt(0).toUpperCase()+e.slice(1)),At=os(e=>e?`on${Et(e)}`:""),he=(e,t)=>!Object.is(e,t),yt=(e,...t)=>{for(let n=0;n<e.length;n++)e[n](...t)},is=(e,t,n,s=!1)=>{Object.defineProperty(e,t,{configurable:!0,enumerable:!1,writable:s,value:n})},tn=e=>{let t=parseFloat(e);return isNaN(t)?e:t},nn=e=>{let t=se(e)?Number(e):NaN;return isNaN(t)?e:t},xo,wn=()=>xo||(xo=typeof globalThis<"u"?globalThis:typeof self<"u"?self:typeof window<"u"?window:typeof global<"u"?global:{});var Fc="Infinity,undefined,NaN,isFinite,isNaN,parseFloat,parseInt,decodeURI,decodeURIComponent,encodeURI,encodeURIComponent,Math,Number,Date,Array,Object,Boolean,String,RegExp,Map,Set,JSON,Intl,BigInt,console,Error,Symbol",ko=Ct(Fc);function Rt(e){if(F(e)){let t={};for(let n=0;n<e.length;n++){let s=e[n],r=se(s)?jc(s):Rt(s);if(r)for(let o in r)t[o]=r[o]}return t}else if(se(e)||Z(e))return e}var Lc=/;(?![^(]*\))/g,Hc=/:([^]+)/,Uc=/\/\*[^]*?\*\//g;function jc(e){let t={};return e.replace(Uc,"").split(Lc).forEach(n=>{if(n){let s=n.split(Hc);s.length>1&&(t[s[0].trim()]=s[1].trim())}}),t}function Pt(e){let t="";if(se(e))t=e;else if(F(e))for(let n=0;n<e.length;n++){let s=Pt(e[n]);s&&(t+=s+" ")}else if(Z(e))for(let n in e)e[n]&&(t+=n+" ");return t.trim()}function Mo(e){if(!e)return null;let{class:t,style:n}=e;return t&&!se(t)&&(e.class=Pt(t)),n&&(e.style=Rt(n)),e}var Io="itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly",$o=Ct(Io),Bc=Ct(Io+",async,autofocus,autoplay,controls,default,defer,disabled,inert,loop,open,required,reversed,scoped,seamless,checked,muted,multiple,selected");function ls(e){return!!e||e===""}function Kc(e,t){if(e.length!==t.length)return!1;let n=!0;for(let s=0;n&&s<e.length;s++)n=Re(e[s],t[s]);return n}function Ao(e,t){if(e.size!==t.size)return!1;let n=Array.from(t),s=new Uint8Array(n.length);for(let r of e){let o=-1;for(let i=0;i<n.length;i++)if(!s[i]&&Re(r,n[i])){o=i;break}if(o<0)return!1;s[o]=1}return!0}function Re(e,t){if(e===t)return!0;let n=Vo(e),s=Vo(t);if(n||s)return n&&s?e.getTime()===t.getTime():!1;if(n=we(e),s=we(t),n||s)return e===t;if(n=F(e),s=F(t),n||s)return n&&s?Kc(e,t):!1;if(n=Z(e),s=Z(t),n||s){if(!n||!s)return!1;if(n=it(e),s=it(t),n||s||(n=He(e),s=He(t),n||s))return n&&s?Ao(e,t):!1;let r=Object.keys(e).length,o=Object.keys(t).length;if(r!==o)return!1;for(let i in e){let l=e.hasOwnProperty(i),c=t.hasOwnProperty(i);if(l&&!c||!l&&c||!Re(e[i],t[i]))return!1}}return String(e)===String(t)}function Tn(e,t){return e.findIndex(n=>Re(n,t))}var Fo=e=>!!(e&&e.__v_isRef===!0),gr=e=>se(e)?e:e==null?"":F(e)||Z(e)&&(e.toString===Po||!B(e.toString))?Fo(e)?gr(e.value):JSON.stringify(e,Lo,2):String(e),Lo=(e,t)=>Fo(t)?Lo(e,t.value):it(t)?{[`Map(${t.size})`]:[...t.entries()].reduce((n,[s,r],o)=>(n[pr(s,o)+" =>"]=r,n),{})}:He(t)?{[`Set(${t.size})`]:[...t.values()].map(n=>pr(n))}:we(t)?pr(t):Z(t)&&!F(t)&&!en(t)?String(t):t,pr=(e,t="")=>{var n;return we(e)?`Symbol(${(n=e.description)!=null?n:t})`:e};function _r(e){return e==null?"initial":typeof e=="string"?e===""?" ":e:(typeof e!="number"||Number.isFinite(e),String(e))}/**
* @vue/reactivity v3.5.42
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/function Wc(e,...t){console.warn(`[Vue warn] ${e}`,...t)}var me,Mt=class{constructor(t=!1){this.detached=t,this._active=!0,this._on=0,this.effects=[],this.cleanups=[],this._isPaused=!1,this._warnOnRun=!0,this.__v_skip=!0,!t&&me&&(me.active?(this.parent=me,this.index=(me.scopes||(me.scopes=[])).push(this)-1):(this._active=!1,this._warnOnRun=!1))}get active(){return this._active}pause(){if(this._active){this._isPaused=!0;let t,n;if(this.scopes){let s=this.scopes.slice();for(t=0,n=s.length;t<n;t++)s[t].pause()}for(t=0,n=this.effects.length;t<n;t++)this.effects[t].pause()}}resume(){if(this._active&&this._isPaused){this._isPaused=!1;let t,n;if(this.scopes){let r=this.scopes.slice();for(t=0,n=r.length;t<n;t++)r[t].resume()}let s=this.effects.slice();for(t=0,n=s.length;t<n;t++)s[t].resume()}}run(t){if(this._active){let n=me;try{return me=this,t()}finally{me=n}}}on(){++this._on===1&&(this.prevScope=me,me=this)}off(){if(this._on>0&&--this._on===0){if(me===this)me=this.prevScope;else{let t=me;for(;t;){if(t.prevScope===this){t.prevScope=this.prevScope;break}t=t.prevScope}}this.prevScope=void 0}}stop(t){if(this._active){this._active=!1;let n,s;for(n=0,s=this.effects.length;n<s;n++)this.effects[n].stop();for(this.effects.length=0,n=0,s=this.cleanups.length;n<s;n++)this.cleanups[n]();if(this.cleanups.length=0,this.scopes){let r=this.scopes.slice();for(n=0,s=r.length;n<s;n++)r[n].stop(!0);this.scopes.length=0}if(!this.detached&&this.parent&&!t){let r=this.parent.scopes.pop();r&&r!==this&&(this.parent.scopes[this.index]=r,r.index=this.index)}this.parent=void 0}}};function jo(e){return new Mt(e)}function Vr(){return me}function Bo(e,t=!1){me&&me.cleanups.push(e)}var ie;var mr=new WeakSet,ct=class{constructor(t){this.fn=t,this.deps=void 0,this.depsTail=void 0,this.flags=5,this.next=void 0,this.cleanup=void 0,this.scheduler=void 0,me&&(me.active?me.effects.push(this):this.flags&=-2)}pause(){this.flags|=64}resume(){this.flags&64&&(this.flags&=-65,mr.has(this)&&(mr.delete(this),this.trigger()))}notify(){this.flags&2&&!(this.flags&32)||this.flags&8||Wo(this)}run(){if(!(this.flags&1))return this.fn();this.flags|=2,Ho(this),Yo(this);let t=ie,n=ze;ie=this,ze=!0;try{return this.fn()}finally{Go(this),ie=t,ze=n,this.flags&=-3}}stop(){if(this.flags&1){for(let t=this.deps;t;t=t.nextDep)Rr(t);this.deps=this.depsTail=void 0,Ho(this),this.onStop&&this.onStop(),this.flags&=-2}}trigger(){this.flags&64?mr.add(this):this.scheduler?this.scheduler():this.runIfDirty()}runIfDirty(){vr(this)&&this.run()}get dirty(){return vr(this)}},Ko=0,Sn,Cn;function Wo(e,t=!1){if(e.flags|=8,t){e.next=Cn,Cn=e;return}e.next=Sn,Sn=e}function xr(){Ko++}function Ar(){if(--Ko>0)return;if(Cn){let t=Cn;for(Cn=void 0;t;){let n=t.next;t.next=void 0,t.flags&=-9,t=n}}let e;for(;Sn;){let t=Sn;for(Sn=void 0;t;){let n=t.next;if(t.next=void 0,t.flags&=-9,t.flags&1)try{t.trigger()}catch(s){e||(e=s)}t=n}}if(e)throw e}function Yo(e){for(let t=e.deps;t;t=t.nextDep)t.version=-1,t.prevActiveLink=t.dep.activeLink,t.dep.activeLink=t}function Go(e){let t,n=e.depsTail,s=n;for(;s;){let r=s.prevDep;s.version===-1?(s===n&&(n=r),Rr(s),Yc(s)):t=s,s.dep.activeLink=s.prevActiveLink,s.prevActiveLink=void 0,s=r}e.deps=t,e.depsTail=n}function vr(e){for(let t=e.deps;t;t=t.nextDep)if(t.dep.version!==t.version||t.dep.computed&&(zo(t.dep.computed)||t.dep.version!==t.version))return!0;return!!e._dirty}function zo(e){if(e.flags&4&&!(e.flags&16)||(e.flags&=-17,e.globalVersion===Vn)||(e.globalVersion=Vn,!e.isSSR&&e.flags&128&&(!e.deps&&!e._dirty||!vr(e))))return;e.flags|=2;let t=e.dep,n=ie,s=ze;ie=e,ze=!0;try{Yo(e);let r=e.fn(e._value);(t.version===0||he(r,e._value))&&(e.flags|=128,e._value=r,t.version++)}catch(r){throw t.version++,r}finally{ie=n,ze=s,Go(e),e.flags&=-3}}function Rr(e,t=!1){let{dep:n,prevSub:s,nextSub:r}=e;if(s&&(s.nextSub=r,e.prevSub=void 0),r&&(r.prevSub=s,e.nextSub=void 0),n.subs===e&&(n.subs=s,!s&&n.computed)){n.computed.flags&=-5;for(let o=n.computed.deps;o;o=o.nextDep)Rr(o,!0)}!t&&!--n.sc&&n.map&&n.map.delete(n.key)}function Yc(e){let{prevDep:t,nextDep:n}=e;t&&(t.nextDep=n,e.prevDep=void 0),n&&(n.prevDep=t,e.nextDep=void 0)}function qo(e,t){e.effect instanceof ct&&(e=e.effect.fn);let n=new ct(e);t&&Q(n,t);try{n.run()}catch(r){throw n.stop(),r}let s=n.run.bind(n);return s.effect=n,s}function Jo(e){e.effect.stop()}var ze=!0,Xo=[];function Be(){Xo.push(ze),ze=!1}function Ke(){let e=Xo.pop();ze=e===void 0?!0:e}function Ho(e){let{cleanup:t}=e;if(e.cleanup=void 0,t){let n=ie;ie=void 0;try{t()}finally{ie=n}}}var Vn=0,Nr=class{constructor(t,n){this.sub=t,this.dep=n,this.version=n.version,this.nextDep=this.prevDep=this.nextSub=this.prevSub=this.prevActiveLink=void 0}},rn=class{constructor(t){this.computed=t,this.version=0,this.activeLink=void 0,this.subs=void 0,this.map=void 0,this.key=void 0,this.sc=0,this.__v_skip=!0}track(t){if(!ie||!ze||ie===this.computed)return;let n=this.activeLink;if(n===void 0||n.sub!==ie)n=this.activeLink=new Nr(ie,this),ie.deps?(n.prevDep=ie.depsTail,ie.depsTail.nextDep=n,ie.depsTail=n):ie.deps=ie.depsTail=n,Zo(n);else if(n.version===-1&&(n.version=this.version,n.nextDep)){let s=n.nextDep;s.prevDep=n.prevDep,n.prevDep&&(n.prevDep.nextDep=s),n.prevDep=ie.depsTail,n.nextDep=void 0,ie.depsTail.nextDep=n,ie.depsTail=n,ie.deps===n&&(ie.deps=s)}return n}trigger(t){this.version++,Vn++,this.notify(t)}notify(t){xr();try{for(let n=this.subs;n;n=n.prevSub)n.sub.notify()&&n.sub.dep.notify()}finally{Ar()}}};function Zo(e){if(e.dep.sc++,e.sub.flags&4){let t=e.dep.computed;if(t&&!e.dep.subs){t.flags|=20;for(let s=t.deps;s;s=s.nextDep)Zo(s)}let n=e.dep.subs;n!==e&&(e.prevSub=n,n&&(n.nextSub=e)),e.dep.subs=e}}var fs=new WeakMap,kt=Symbol(""),br=Symbol(""),xn=Symbol("");function Ne(e,t,n){if(ze&&ie){let s=fs.get(e);s||fs.set(e,s=new Map);let r=s.get(n);r||(s.set(n,r=new rn),r.map=s,r.key=n),r.track()}}function Ze(e,t,n,s,r,o){let i=fs.get(e);if(!i){Vn++;return}let l=c=>{c&&c.trigger()};if(xr(),t==="clear")i.forEach(l);else{let c=F(e),u=c&&On(n);if(c&&n==="length"){let f=Number(s);i.forEach((a,_)=>{(_==="length"||_===xn||!we(_)&&_>=f)&&l(a)})}else switch((n!==void 0||i.has(void 0))&&l(i.get(n)),u&&l(i.get(xn)),t){case"add":c?u&&l(i.get("length")):(l(i.get(kt)),it(e)&&l(i.get(br)));break;case"delete":c||(l(i.get(kt)),it(e)&&l(i.get(br)));break;case"set":it(e)&&l(i.get(kt));break}}Ar()}function Gc(e,t){let n=fs.get(e);return n&&n.get(t)}function sn(e){let t=z(e);return t===e?t:(Ne(t,"iterate",xn),Ee(e)?t:t.map(je))}function Rn(e){return Ne(e=z(e),"iterate",xn),e}function Xe(e,t){return Pe(e)?It(Ue(e)?je(t):t):je(t)}var zc={__proto__:null,[Symbol.iterator](){return Er(this,Symbol.iterator,e=>Xe(this,e))},concat(...e){return sn(this).concat(...e.map(t=>F(t)?sn(t):t))},entries(){return Er(this,"entries",e=>(e[1]=Xe(this,e[1]),e))},every(e,t){return lt(this,"every",e,t,void 0,arguments)},filter(e,t){return lt(this,"filter",e,t,n=>n.map(s=>Xe(this,s)),arguments)},find(e,t){return lt(this,"find",e,t,n=>Xe(this,n),arguments)},findIndex(e,t){return lt(this,"findIndex",e,t,void 0,arguments)},findLast(e,t){return lt(this,"findLast",e,t,n=>Xe(this,n),arguments)},findLastIndex(e,t){return lt(this,"findLastIndex",e,t,void 0,arguments)},forEach(e,t){return lt(this,"forEach",e,t,void 0,arguments)},includes(...e){return yr(this,"includes",e)},indexOf(...e){return yr(this,"indexOf",e)},join(e){return sn(this).join(e)},lastIndexOf(...e){return yr(this,"lastIndexOf",e)},map(e,t){return lt(this,"map",e,t,void 0,arguments)},pop(){return Dn(this,"pop")},push(...e){return Dn(this,"push",e)},reduce(e,...t){return Uo(this,"reduce",e,t)},reduceRight(e,...t){return Uo(this,"reduceRight",e,t)},shift(){return Dn(this,"shift")},some(e,t){return lt(this,"some",e,t,void 0,arguments)},splice(...e){return Dn(this,"splice",e)},toReversed(){return sn(this).toReversed()},toSorted(e){return sn(this).toSorted(e)},toSpliced(...e){return sn(this).toSpliced(...e)},unshift(...e){return Dn(this,"unshift",e)},values(){return Er(this,"values",e=>Xe(this,e))}};function Er(e,t,n){let s=Rn(e),r=s[t]();return s!==e&&!Ee(e)&&(r._next=r.next,r.next=()=>{let o=r._next();return o.done||(o.value=n(o.value)),o}),r}var qc=Array.prototype;function lt(e,t,n,s,r,o){let i=Rn(e),l=i!==e&&!Ee(e),c=i[t];if(c!==qc[t]){let a=c.apply(e,o);return l?je(a):a}let u=n;i!==e&&(l?u=function(a,_){return n.call(this,Xe(e,a),_,e)}:n.length>2&&(u=function(a,_){return n.call(this,a,_,e)}));let f=c.call(i,u,s);return l&&r?r(f):f}function Uo(e,t,n,s){let r=Rn(e),o=r!==e&&!Ee(e),i=n,l=!1;r!==e&&(o?(l=s.length===0,i=function(u,f,a){return l&&(l=!1,u=Xe(e,u)),n.call(this,u,Xe(e,f),a,e)}):n.length>3&&(i=function(u,f,a){return n.call(this,u,f,a,e)}));let c=r[t](i,...s);return l?Xe(e,c):c}function yr(e,t,n){let s=z(e);Ne(s,"iterate",xn);let r=s[t](...n);return(r===-1||r===!1)&&$t(n[0])?(n[0]=z(n[0]),s[t](...n)):r}function Dn(e,t,n=[]){Be(),xr();let s=z(e)[t].apply(e,n);return Ar(),Ke(),s}var Jc=Ct("__proto__,__v_isRef,__isVue"),Qo=new Set(Object.getOwnPropertyNames(Symbol).filter(e=>e!=="arguments"&&e!=="caller").map(e=>Symbol[e]).filter(we));function Xc(e){we(e)||(e=String(e));let t=z(this);return Ne(t,"has",e),t.hasOwnProperty(e)}var ps=class{constructor(t=!1,n=!1){this._isReadonly=t,this._isShallow=n}get(t,n,s){if(n==="__v_skip")return t.__v_skip;let r=this._isReadonly,o=this._isShallow;if(n==="__v_isReactive")return!r;if(n==="__v_isReadonly")return r;if(n==="__v_isShallow")return o;if(n==="__v_raw")return s===(r?o?si:ni:o?ti:ei).get(t)||Object.getPrototypeOf(t)===Object.getPrototypeOf(s)?t:void 0;let i=F(t);if(!r){let c;if(i&&(c=zc[n]))return c;if(n==="hasOwnProperty")return Xc}let l=Reflect.get(t,n,ue(t)?t:s);if((we(n)?Qo.has(n):Jc(n))||(r||Ne(t,"get",n),o))return l;if(ue(l)){let c=i&&On(n)?l:l.value;return r&&Z(c)?An(c):c}return Z(l)?r?An(l):on(l):l}},ds=class extends ps{constructor(t=!1){super(!1,t)}set(t,n,s,r){let o=t[n],i=F(t)&&On(n);if(!this._isShallow){let u=Pe(o);if(!Ee(s)&&!Pe(s)&&(o=z(o),s=z(s)),!i&&ue(o)&&!ue(s))return u||(o.value=s),!0}let l=i?Number(n)<t.length:ee(t,n),c=Reflect.set(t,n,s,ue(t)?t:r);return t===z(r)&&c&&(l?he(s,o)&&Ze(t,"set",n,s,o):Ze(t,"add",n,s)),c}deleteProperty(t,n){let s=ee(t,n),r=t[n],o=Reflect.deleteProperty(t,n);return o&&s&&Ze(t,"delete",n,void 0,r),o}has(t,n){let s=Reflect.has(t,n);return(!we(n)||!Qo.has(n))&&Ne(t,"has",n),s}ownKeys(t){return Ne(t,"iterate",F(t)?"length":kt),Reflect.ownKeys(t)}},hs=class extends ps{constructor(t=!1){super(!0,t)}set(t,n){return!0}deleteProperty(t,n){return!0}},Zc=new ds,Qc=new hs,ea=new ds(!0),ta=new hs(!0),Or=e=>e,cs=e=>Reflect.getPrototypeOf(e);function na(e,t,n){return function(...s){let r=this.__v_raw,o=z(r),i=it(o),l=e==="entries"||e===Symbol.iterator&&i,c=e==="keys"&&i,u=r[e](...s),f=n?Or:t?It:je;return!t&&Ne(o,"iterate",c?br:kt),Q(Object.create(u),{next(){let{value:a,done:_}=u.next();return _?{value:a,done:_}:{value:l?[f(a[0]),f(a[1])]:f(a),done:_}}})}}function as(e){return function(...t){return e==="delete"?!1:e==="clear"?void 0:this}}function sa(e,t){let n={get(r){let o=this.__v_raw,i=z(o),l=z(r);e||(he(r,l)&&Ne(i,"get",r),Ne(i,"get",l));let{has:c}=cs(i),u=t?Or:e?It:je;if(c.call(i,r))return u(o.get(r));if(c.call(i,l))return u(o.get(l));o!==i&&o.get(r)},get size(){let r=this.__v_raw;return!e&&Ne(z(r),"iterate",kt),r.size},has(r){let o=this.__v_raw,i=z(o),l=z(r);return e||(he(r,l)&&Ne(i,"has",r),Ne(i,"has",l)),r===l?o.has(r):o.has(r)||o.has(l)},forEach(r,o){let i=this,l=i.__v_raw,c=z(l),u=t?Or:e?It:je;return!e&&Ne(c,"iterate",kt),l.forEach((f,a)=>r.call(o,u(f),u(a),i))}};return Q(n,e?{add:as("add"),set:as("set"),delete:as("delete"),clear:as("clear")}:{add(r){let o=z(this),i=cs(o),l=z(r),c=!t&&!Ee(r)&&!Pe(r)?l:r;return i.has.call(o,c)||he(r,c)&&i.has.call(o,r)||he(l,c)&&i.has.call(o,l)||(o.add(c),Ze(o,"add",c,c)),this},set(r,o){!t&&!Ee(o)&&!Pe(o)&&(o=z(o));let i=z(this),{has:l,get:c}=cs(i),u=l.call(i,r);u||(r=z(r),u=l.call(i,r));let f=c.call(i,r);return i.set(r,o),u?he(o,f)&&Ze(i,"set",r,o,f):Ze(i,"add",r,o),this},delete(r){let o=z(this),{has:i,get:l}=cs(o),c=i.call(o,r);c||(r=z(r),c=i.call(o,r));let u=l?l.call(o,r):void 0,f=o.delete(r);return c&&Ze(o,"delete",r,void 0,u),f},clear(){let r=z(this),o=r.size!==0,i=void 0,l=r.clear();return o&&Ze(r,"clear",void 0,void 0,i),l}}),["keys","values","entries",Symbol.iterator].forEach(r=>{n[r]=na(r,e,t)}),n}function _s(e,t){let n=sa(e,t);return(s,r,o)=>r==="__v_isReactive"?!e:r==="__v_isReadonly"?e:r==="__v_raw"?s:Reflect.get(ee(n,r)&&r in s?n:s,r,o)}var ra={get:_s(!1,!1)},oa={get:_s(!1,!0)},ia={get:_s(!0,!1)},la={get:_s(!0,!0)};var ei=new WeakMap,ti=new WeakMap,ni=new WeakMap,si=new WeakMap;function ca(e){switch(e){case"Object":case"Array":return 1;case"Map":case"Set":case"WeakMap":case"WeakSet":return 2;default:return 0}}function on(e){return Pe(e)?e:Es(e,!1,Zc,ra,ei)}function ms(e){return Es(e,!1,ea,oa,ti)}function An(e){return Es(e,!0,Qc,ia,ni)}function ri(e){return Es(e,!0,ta,la,si)}function Es(e,t,n,s,r){if(!Z(e)||e.__v_raw&&!(t&&e.__v_isReactive)||e.__v_skip||!Object.isExtensible(e))return e;let o=r.get(e);if(o)return o;let i=ca(hr(e));if(i===0)return e;let l=new Proxy(e,i===2?s:n);return r.set(e,l),l}function Ue(e){return Pe(e)?Ue(e.__v_raw):!!(e&&e.__v_isReactive)}function Pe(e){return!!(e&&e.__v_isReadonly)}function Ee(e){return!!(e&&e.__v_isShallow)}function $t(e){return e?!!e.__v_raw:!1}function z(e){let t=e&&e.__v_raw;return t?z(t):e}function ys(e){return!ee(e,"__v_skip")&&Object.isExtensible(e)&&is(e,"__v_skip",!0),e}var je=e=>Z(e)?on(e):e,It=e=>Z(e)?An(e):e;function ue(e){return e?e.__v_isRef===!0:!1}function Ft(e){return oi(e,!1)}function vs(e){return oi(e,!0)}function oi(e,t){return ue(e)?e:new wr(e,t)}var wr=class{constructor(t,n){this.dep=new rn,this.__v_isRef=!0,this.__v_isShallow=!1,this._rawValue=n?t:z(t),this._value=n?t:je(t),this.__v_isShallow=n}get value(){return this.dep.track(),this._value}set value(t){let n=this._rawValue,s=this.__v_isShallow||Ee(t)||Pe(t);t=s?t:z(t),he(t,n)&&(this._rawValue=t,this._value=s?t:je(t),this.dep.trigger())}};function ii(e){e.dep&&e.dep.trigger()}function Lt(e){return ue(e)?e.value:e}function li(e){return B(e)?e():Lt(e)}var aa={get:(e,t,n)=>t==="__v_raw"?e:Lt(Reflect.get(e,t,n)),set:(e,t,n,s)=>{let r=e[t];return ue(r)&&!ue(n)?(r.value=n,!0):Reflect.set(e,t,n,s)}};function Pn(e){return Ue(e)?e:new Proxy(e,aa)}var Tr=class{constructor(t){this.__v_isRef=!0,this._value=void 0;let n=this.dep=new rn,{get:s,set:r}=t(n.track.bind(n),n.trigger.bind(n));this._get=s,this._set=r}get value(){return this._value=this._get()}set value(t){this._set(t)}};function Ns(e){return new Tr(e)}function ci(e){let t=F(e)?new Array(e.length):{};for(let n in e)t[n]=ui(e,n);return t}var Dr=class{constructor(t,n,s){this._object=t,this._defaultValue=s,this.__v_isRef=!0,this._value=void 0,this._key=we(n)?n:String(n),this._raw=z(t);let r=!0,o=t;if(!F(t)||we(this._key)||!On(this._key))do r=!$t(o)||Ee(o);while(r&&(o=o.__v_raw));this._shallow=r}get value(){let t=this._object[this._key];return this._shallow&&(t=Lt(t)),this._value=t===void 0?this._defaultValue:t}set value(t){if(this._shallow&&ue(this._raw[this._key])){let n=this._object[this._key];if(ue(n)){n.value=t;return}}this._object[this._key]=t}get dep(){return Gc(this._raw,this._key)}},Sr=class{constructor(t){this._getter=t,this.__v_isRef=!0,this.__v_isReadonly=!0,this._value=void 0}get value(){return this._value=this._getter()}};function ai(e,t,n){return ue(e)?e:B(e)?new Sr(e):Z(e)&&arguments.length>1?ui(e,t,n):Ft(e)}function ui(e,t,n){return new Dr(e,t,n)}var Cr=class{constructor(t,n,s){this.fn=t,this.setter=n,this._value=void 0,this.dep=new rn(this),this.__v_isRef=!0,this.deps=void 0,this.depsTail=void 0,this.flags=16,this.globalVersion=Vn-1,this.next=void 0,this.effect=this,this.__v_isReadonly=!n,this.isSSR=s}notify(){if(this.flags|=16,!(this.flags&8)&&ie!==this)return Wo(this,!0),!0}get value(){let t=this.dep.track();return zo(this),t&&(t.version=this.dep.version),this._value}set value(t){this.setter&&this.setter(t)}};function fi(e,t,n=!1){let s,r;return B(e)?s=e:(s=e.get,r=e.set),new Cr(s,r,n)}var pi={GET:"get",HAS:"has",ITERATE:"iterate"},di={SET:"set",ADD:"add",DELETE:"delete",CLEAR:"clear"};var us={},gs=new WeakMap,vt;function hi(){return vt}function Pr(e,t=!1,n=vt){if(n){let s=gs.get(n);s||gs.set(n,s=[]),s.push(e)}}function gi(e,t,n=J){let{immediate:s,deep:r,once:o,scheduler:i,augmentJob:l,call:c}=n,u=g=>{(n.onWarn||Wc)("Invalid watch source: ",g,"A watch source can only be a getter/effect function, a ref, a reactive object, or an array of these types.")},f=g=>r?g:Ee(g)||r===!1||r===0?Qe(g,1):Qe(g),a,_,E,v,N=!1,L=!1;if(ue(e)?(_=()=>e.value,N=Ee(e)):Ue(e)?(_=()=>f(e),N=!0):F(e)?(L=!0,N=e.some(g=>Ue(g)||Ee(g)),_=()=>e.map(g=>{if(ue(g))return g.value;if(Ue(g))return f(g);if(B(g))return c?c(g,2):g()})):B(e)?t?_=c?()=>c(e,2):e:_=()=>{if(E){Be();try{E()}finally{Ke()}}let g=vt;vt=a;try{return c?c(e,3,[v]):e(v)}finally{vt=g}}:_=Te,t&&r){let g=_,C=r===!0?1/0:r;_=()=>Qe(g(),C)}let H=Vr(),b=()=>{a.stop(),H&&H.active&&bn(H.effects,a)};if(o&&t){let g=t;t=(...C)=>{let x=g(...C);return b(),x}}let h=L?new Array(e.length).fill(us):us,m=g=>{if(!(!(a.flags&1)||!a.dirty&&!g))if(t){let C=a.run();if(g||r||N||(L?C.some((x,I)=>he(x,h[I])):he(C,h))){E&&E();let x=vt;vt=a;try{let I=[C,h===us?void 0:L&&h[0]===us?[]:h,v];h=C,c?c(t,3,I):t(...I)}finally{vt=x}}}else a.run()};return l&&l(m),a=new ct(_),a.scheduler=i?()=>i(m,!1):m,v=g=>Pr(g,!1,a),E=a.onStop=()=>{let g=gs.get(a);if(g){if(c)c(g,4);else for(let C of g)C();gs.delete(a)}},t?s?m(!0):h=a.run():i?i(m.bind(null,!0),!0):a.run(),b.pause=a.pause.bind(a),b.resume=a.resume.bind(a),b.stop=b,b}function Qe(e,t=1/0,n){if(t<=0||!Z(e)||e.__v_skip||(n=n||new Map,(n.get(e)||0)>=t))return e;if(n.set(e,t),t--,ue(e))Qe(e.value,t,n);else if(F(e))for(let s=0;s<e.length;s++)Qe(e[s],t,n);else if(He(e)||it(e))e.forEach(s=>{Qe(s,t,n)});else if(en(e)){for(let s in e)Qe(e[s],t,n);for(let s of Object.getOwnPropertySymbols(e))Object.prototype.propertyIsEnumerable.call(e,s)&&Qe(e[s],t,n)}return e}/**
* @vue/runtime-core v3.5.42
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/var jt=[];function ua(e){jt.push(e)}function fa(){jt.pop()}var kr=!1;function _i(e,...t){if(kr)return;kr=!0,Be();let n=jt.length?jt[jt.length-1].component:null,s=n&&n.appContext.config.warnHandler,r=pa();if(s)zt(s,n,11,[e+t.map(o=>{var i,l;return(l=(i=o.toString)==null?void 0:i.call(o))!=null?l:JSON.stringify(o)}).join(""),n&&n.proxy,r.map(({vnode:o})=>`at <${Al(n,o.type)}>`).join(`
`),r]);else{let o=[`[Vue warn]: ${e}`,...t];r.length&&o.push(`
`,...da(r)),console.warn(...o)}Ke(),kr=!1}function pa(){let e=jt[jt.length-1];if(!e)return[];let t=[];for(;e;){let n=t[0];n&&n.vnode===e?n.recurseCount++:t.push({vnode:e,recurseCount:0});let s=e.component&&e.component.parent;e=s&&s.vnode}return t}function da(e){let t=[];return e.forEach((n,s)=>{t.push(...s===0?[]:[`
`],...ha(n))}),t}function ha({vnode:e,recurseCount:t}){let n=t>0?`... (${t} recursive calls)`:"",s=e.component?e.component.parent==null:!1,r=` at <${Al(e.component,e.type,s)}`,o=">"+n;return e.props?[r,...ga(e.props),o]:[r+o]}function ga(e){let t=[],n=Object.keys(e);return n.slice(0,3).forEach(s=>{t.push(...Ai(s,e[s]))}),n.length>3&&t.push(" ..."),t}function Ai(e,t,n){return se(t)?(t=JSON.stringify(t),n?t:[`${e}=${t}`]):typeof t=="number"||typeof t=="boolean"||t==null?n?t:[`${e}=${t}`]:ue(t)?(t=Ai(e,z(t.value),!0),n?t:[`${e}=Ref<`,t,">"]):B(t)?[`${e}=fn${t.name?`<${t.name}>`:""}`]:(t=z(t),n?t:[`${e}=`,t])}function _a(e,t){}var ma={SETUP_FUNCTION:0,0:"SETUP_FUNCTION",RENDER_FUNCTION:1,1:"RENDER_FUNCTION",NATIVE_EVENT_HANDLER:5,5:"NATIVE_EVENT_HANDLER",COMPONENT_EVENT_HANDLER:6,6:"COMPONENT_EVENT_HANDLER",VNODE_HOOK:7,7:"VNODE_HOOK",DIRECTIVE_HOOK:8,8:"DIRECTIVE_HOOK",TRANSITION_HOOK:9,9:"TRANSITION_HOOK",APP_ERROR_HANDLER:10,10:"APP_ERROR_HANDLER",APP_WARN_HANDLER:11,11:"APP_WARN_HANDLER",FUNCTION_REF:12,12:"FUNCTION_REF",ASYNC_COMPONENT_LOADER:13,13:"ASYNC_COMPONENT_LOADER",SCHEDULER:14,14:"SCHEDULER",COMPONENT_UPDATE:15,15:"COMPONENT_UPDATE",APP_UNMOUNT_CLEANUP:16,16:"APP_UNMOUNT_CLEANUP"},Ea={sp:"serverPrefetch hook",bc:"beforeCreate hook",c:"created hook",bm:"beforeMount hook",m:"mounted hook",bu:"beforeUpdate hook",u:"updated",bum:"beforeUnmount hook",um:"unmounted hook",a:"activated hook",da:"deactivated hook",ec:"errorCaptured hook",rtc:"renderTracked hook",rtg:"renderTriggered hook",0:"setup function",1:"render function",2:"watcher getter",3:"watcher callback",4:"watcher cleanup function",5:"native event handler",6:"component event handler",7:"vnode hook",8:"directive hook",9:"transition hook",10:"app errorHandler",11:"app warnHandler",12:"ref function",13:"async component loader",14:"scheduler flush",15:"component update",16:"app unmount cleanup function"};function zt(e,t,n,s){try{return s?e(...s):e()}catch(r){qt(r,t,n)}}function Ie(e,t,n,s){if(B(e)){let r=zt(e,t,n,s);return r&&rs(r)&&r.catch(o=>{qt(o,t,n)}),r}if(F(e)){let r=[];for(let o=0;o<e.length;o++)r.push(Ie(e[o],t,n,s));return r}}function qt(e,t,n,s=!0){let r=t?t.vnode:null,{errorHandler:o,throwUnhandledErrorInProduction:i}=t&&t.appContext.config||J;if(t){let l=t.parent,c=t.proxy,u=`https://vuejs.org/error-reference/#runtime-${n}`;for(;l;){let f=l.ec;if(f){for(let a=0;a<f.length;a++)if(f[a](e,c,u)===!1)return}l=l.parent}if(o){Be(),zt(o,null,10,[e,c,u]),Ke();return}}ya(e,n,r,s,i)}function ya(e,t,n,s=!0,r=!1){if(r)throw e;console.error(e)}var Ae=[],et=-1,fn=[],bt=null,cn=0,Ri=Promise.resolve(),xs=null;function Gn(e){let t=xs||Ri;return e?t.then(this?e.bind(this):e):t}function va(e){let t=et+1,n=Ae.length;for(;t<n;){let s=t+n>>>1,r=Ae[s],o=Hn(r);o<e||o===e&&r.flags&2?t=s+1:n=s}return t}function qr(e){if(!(e.flags&1)){let t=Hn(e),n=Ae[Ae.length-1];!n||!(e.flags&2)&&t>=Hn(n)?Ae.push(e):Ae.splice(va(t),0,e),e.flags|=1,Pi()}}function Pi(){xs||(xs=Ri.then(ki))}function hn(e){if(!F(e))bt&&e.id===-1?bt.splice(cn+1,0,e):e.flags&1||(fn.push(e),e.flags|=1);else for(let t=0;t<e.length;t++)fn.push(e[t]);Pi()}function mi(e,t,n=et+1){for(;n<Ae.length;n++){let s=Ae[n];if(s&&s.flags&2){if(e&&s.id!==e.uid)continue;Ae.splice(n,1),n--,s.flags&4&&(s.flags&=-2),s(),s.flags&4||(s.flags&=-2)}}}function As(e){if(fn.length){let t=[...new Set(fn)].sort((n,s)=>Hn(n)-Hn(s));if(fn.length=0,bt){for(let n=0;n<t.length;n++)bt.push(t[n]);return}for(bt=t,cn=0;cn<bt.length;cn++){let n=bt[cn];n.flags&4&&(n.flags&=-2),n.flags&8||n(),n.flags&=-2}bt=null,cn=0}}var Hn=e=>e.id==null?e.flags&2?-1:1/0:e.id;function ki(e){let t=Te;try{for(et=0;et<Ae.length;et++){let n=Ae[et];n&&!(n.flags&8)&&(n.flags&4&&(n.flags&=-2),zt(n,n.i,n.i?15:14),n.flags&4||(n.flags&=-2))}}finally{for(;et<Ae.length;et++){let n=Ae[et];n&&(n.flags&=-2)}et=-1,Ae.length=0,As(e),xs=null,(Ae.length||fn.length)&&ki(e)}}var Na=!1;var an,bs=[],Ei=!1;function Mi(e,t){var n,s;an=e,an?(an.enabled=!0,bs.forEach(({event:r,args:o})=>an.emit(r,...o)),bs=[]):typeof window<"u"&&window.HTMLElement&&!((s=(n=window.navigator)==null?void 0:n.userAgent)!=null&&s.includes("jsdom"))?((t.__VUE_DEVTOOLS_HOOK_REPLAY__=t.__VUE_DEVTOOLS_HOOK_REPLAY__||[]).push(o=>{Mi(o,t)}),setTimeout(()=>{an||(t.__VUE_DEVTOOLS_HOOK_REPLAY__=null,Ei=!0,bs=[])},3e3)):(Ei=!0,bs=[])}var Oe=null,Bs=null;function Un(e){let t=Oe;return Oe=e,Bs=e&&e.type.__scopeId||null,t}function ba(e){Bs=e}function Oa(){Bs=null}var wa=e=>Jr;function Jr(e,t=Oe,n){if(!t||e._n)return e;let s=(...r)=>{s._d&&Wn(-1);let o=Un(t),i=pt.length,l;try{l=e(...r)}finally{for(let c=pt.length;c>i;c--)Qs();Un(o),s._d&&Wn(1)}return l};return s._n=!0,s._c=!0,s._d=!0,s}function Ta(e,t){if(Oe===null)return e;let n=Zn(Oe),s=e.dirs||(e.dirs=[]);for(let r=0;r<t.length;r++){let[o,i,l,c=J]=t[r];o&&(B(o)&&(o={mounted:o,updated:o}),o.deep&&Qe(i),s.push({dir:o,instance:n,value:i,oldValue:void 0,arg:l,modifiers:c}))}return e}function tt(e,t,n,s){let r=e.dirs,o=t&&t.dirs;for(let i=0;i<r.length;i++){let l=r[i];o&&(l.oldValue=o[i].value);let c=l.dir[s];c&&(Be(),Ie(c,n,8,[e.el,l,e,t]),Ke())}}function Ii(e,t){if(be){let n=be.provides,s=be.parent&&be.parent.provides;s===n&&(n=be.provides=Object.create(s)),n[e]=t}}function Fn(e,t,n=!1){let s=Ce();if(s||Kt){let r=Kt?Kt._context.provides:s?s.parent==null||s.ce?s.vnode.appContext&&s.vnode.appContext.provides:s.parent.provides:void 0;if(r&&e in r)return r[e];if(arguments.length>1)return n&&B(t)?t.call(s&&s.proxy):t}}function Da(){return!!(Ce()||Kt)}var $i=Symbol.for("v-scx"),Fi=()=>{{let e=Fn($i);return e}};function Sa(e,t){return zn(e,null,t)}function Ca(e,t){return zn(e,null,{flush:"post"})}function Li(e,t){return zn(e,null,{flush:"sync"})}function Bt(e,t,n){return zn(e,t,n)}function zn(e,t,n=J){let{immediate:s,deep:r,flush:o,once:i}=n,l=Q({},n),c=t&&s||!t&&o!=="post",u;if(Gt){if(o==="sync"){let E=Fi();u=E.__watcherHandles||(E.__watcherHandles=[])}else if(!c){let E=()=>{};return E.stop=Te,E.resume=Te,E.pause=Te,E}}let f=be;l.call=(E,v,N)=>Ie(E,f,v,N);let a=!1;o==="post"?l.scheduler=E=>{ge(E,f&&f.suspense)}:o!=="sync"&&(a=!0,l.scheduler=(E,v)=>{v?E():qr(E)}),l.augmentJob=E=>{t&&(E.flags|=4),a&&(E.flags|=2,f&&(E.id=f.uid,E.i=f))};let _=gi(e,t,l);return Gt&&(u?u.push(_):c&&_()),_}function Va(e,t,n){let s=this.proxy,r=se(e)?e.includes(".")?Hi(s,e):()=>s[e]:e.bind(s,s),o;B(t)?o=t:(o=t.handler,n=t);let i=mn(this),l=zn(r,o.bind(s),n);return i(),l}function Hi(e,t){let n=t.split(".");return()=>{let s=e;for(let r=0;r<n.length&&s;r++)s=s[n[r]];return s}}var Nt=new WeakMap,Ui=Symbol("_vte"),Ks=e=>e.__isTeleport,Ut=e=>e&&(e.disabled||e.disabled===""),xa=e=>e&&(e.defer||e.defer===""),yi=e=>typeof SVGElement<"u"&&e instanceof SVGElement,vi=e=>typeof MathMLElement=="function"&&e instanceof MathMLElement,Lr=(e,t)=>{let n=e&&e.to;return se(n)?t?t(n):null:n},Aa={name:"Teleport",__isTeleport:!0,process(e,t,n,s,r,o,i,l,c,u){let{mc:f,pc:a,pbc:_,o:{insert:E,querySelector:v,createText:N,createComment:L,parentNode:H}}=u,b=Ut(t.props),{dynamicChildren:h}=t,m=(x,I,w)=>{x.shapeFlag&16&&f(x.children,I,w,r,o,i,l,c)},g=(x=t)=>{let I=Ut(x.props),w=x.target=Lr(x.props,v),P=Hr(w,x,N,E);w&&(i!=="svg"&&yi(w)?i="svg":i!=="mathml"&&vi(w)&&(i="mathml"),r&&r.isCE&&(r.ce._teleportTargets||(r.ce._teleportTargets=new Set)).add(w),I||(m(x,w,P),Mn(x,!1)))},C=x=>{let I=()=>{if(Nt.get(x)===I){if(Nt.delete(x),Ut(x.props)){let w=H(x.el)||n;m(x,w,x.anchor),Mn(x,!0)}g(x)}};Nt.set(x,I),ge(I,o)};if(e==null){let x=t.el=N(""),I=t.anchor=N("");if(E(x,n,s),E(I,n,s),xa(t.props)||o&&o.pendingBranch){C(t);return}b&&(m(t,n,I),Mn(t,!0)),g()}else{t.el=e.el;let x=t.anchor=e.anchor,I=Nt.get(e);if(I){I.flags|=8,Nt.delete(e),C(t);return}t.targetStart=e.targetStart;let w=t.target=e.target,P=t.targetAnchor=e.targetAnchor,M=Ut(e.props),V=M?n:w,K=M?x:P;if(i==="svg"||yi(w)?i="svg":(i==="mathml"||vi(w))&&(i="mathml"),h?(_(e.dynamicChildren,h,V,r,o,i,l),co(e,t,!0)):c||a(e,t,V,K,r,o,i,l,!1),b)M?t.props&&e.props&&t.props.to!==e.props.to&&(t.props.to=e.props.to):Os(t,n,x,u,1);else if((t.props&&t.props.to)!==(e.props&&e.props.to)){let q=Lr(t.props,v);q&&(t.target=q,Os(t,q,null,u,0))}else M&&Os(t,w,P,u,1);Mn(t,b)}},remove(e,t,n,{um:s,o:{remove:r}},o){let{shapeFlag:i,children:l,anchor:c,targetStart:u,targetAnchor:f,target:a,props:_}=e,E=Ut(_),v=o||!E,N=Nt.get(e);if(N&&(N.flags|=8,Nt.delete(e)),a&&(r(u),r(f)),o&&r(c),!N&&(E||a)&&i&16)for(let L=0;L<l.length;L++){let H=l[L];s(H,t,n,v,!!H.dynamicChildren)}},move:Os,hydrate:Ra};function Os(e,t,n,{o:{insert:s},m:r},o=2){o===0&&s(e.targetAnchor,t,n);let{el:i,anchor:l,shapeFlag:c,children:u,props:f}=e,a=o===2;if(a&&s(i,t,n),!Nt.has(e)&&(!a||Ut(f))&&c&16)for(let _=0;_<u.length;_++)r(u[_],t,n,2);a&&s(l,t,n)}function Ra(e,t,n,s,r,o,{o:{nextSibling:i,parentNode:l,querySelector:c,insert:u,createText:f}},a){function _(L,H){let b=H;for(;b;){if(b&&b.nodeType===8){if(b.data==="teleport start anchor")t.targetStart=b;else if(b.data==="teleport anchor"){t.targetAnchor=b,L._lpa=t.targetAnchor&&i(t.targetAnchor);break}}b=i(b)}}function E(L,H){H.anchor=a(i(L),H,l(L),n,s,r,o)}let v=t.target=Lr(t.props,c),N=Ut(t.props);if(v){let L=v._lpa||v.firstChild;t.shapeFlag&16&&(N?(E(e,t),_(v,L),t.targetAnchor||Hr(v,t,f,u,l(e)===v?e:null)):(t.anchor=i(e),_(v,L),t.targetAnchor||Hr(v,t,f,u),a(L&&i(L),t,v,n,s,r,o))),Mn(t,N)}else N&&t.shapeFlag&16&&(E(e,t),t.targetStart=e,t.targetAnchor=i(e));return t.anchor&&i(t.anchor)}var Pa=Aa;function Mn(e,t){let n=e.ctx;if(n&&n.ut){let s,r;for(t?(s=e.el,r=e.anchor):(s=e.targetStart,r=e.targetAnchor);s&&s!==r;)s.nodeType===1&&s.setAttribute("data-v-owner",n.uid),s=s.nextSibling;n.ut()}}function Hr(e,t,n,s,r=null){let o=t.targetStart=n(""),i=t.targetAnchor=n("");return o[Ui]=i,e&&(s(o,e,r),s(i,e,r)),i}var Ye=Symbol("_leaveCb"),kn=Symbol("_enterCb");function Ws(){let e={isMounted:!1,isLeaving:!1,isUnmounting:!1,leavingVNodes:new Map};return gn(()=>{e.isMounted=!0}),Js(()=>{e.isUnmounting=!0}),e}var We=[Function,Array],Ys={mode:String,appear:Boolean,persisted:Boolean,onBeforeEnter:We,onEnter:We,onAfterEnter:We,onEnterCancelled:We,onBeforeLeave:We,onLeave:We,onAfterLeave:We,onLeaveCancelled:We,onBeforeAppear:We,onAppear:We,onAfterAppear:We,onAppearCancelled:We},ji=e=>{let t=e.subTree;return t.component?ji(t.component):t},ka={name:"BaseTransition",props:Ys,setup(e,{slots:t}){let n=Ce(),s=Ws();return()=>{let r=t.default&&qn(t.default(),!0),o=r&&r.length?Bi(r):n.subTree?Ol():void 0;if(!o)return;let i=z(e),{mode:l}=i;if(s.isLeaving)return Mr(o);let c=Rs(o);if(!c)return Mr(o);let u=Wt(c,i,s,n,a=>u=a);c.type!==pe&&nt(c,u);let f=n.subTree&&Rs(n.subTree);if(f&&f.type!==pe&&!qe(f,c)&&ji(n).type!==pe){let a=Wt(f,i,s,n);if(nt(f,a),l==="out-in"&&c.type!==pe)return s.isLeaving=!0,a.afterLeave=()=>{s.isLeaving=!1,n.job.flags&8||n.update(),delete a.afterLeave,f=void 0},Mr(o);l==="in-out"&&c.type!==pe?a.delayLeave=(_,E,v)=>{let N=Ki(s,f);N[String(f.key)]=f,_[Ye]=()=>{E(),_[Ye]=void 0,delete u.delayedLeave,f=void 0},u.delayedLeave=()=>{v(),delete u.delayedLeave,f=void 0}}:f=void 0}else f&&(f=void 0);return o}}};function Bi(e){let t=e[0];if(e.length>1){let n=!1;for(let s of e)if(s.type!==pe){t=s,n=!0;break}}return t}var Xr=ka;function Ki(e,t){let{leavingVNodes:n}=e,s=n.get(t.type);return s||(s=Object.create(null),n.set(t.type,s)),s}function Wt(e,t,n,s,r){let{appear:o,mode:i,persisted:l=!1,onBeforeEnter:c,onEnter:u,onAfterEnter:f,onEnterCancelled:a,onBeforeLeave:_,onLeave:E,onAfterLeave:v,onLeaveCancelled:N,onBeforeAppear:L,onAppear:H,onAfterAppear:b,onAppearCancelled:h}=t,m=String(e.key),g=Ki(n,e),C=(w,P)=>{w&&Ie(w,s,9,P)},x=(w,P)=>{let M=P[1];C(w,P),F(w)?w.every(V=>V.length<=1)&&M():w.length<=1&&M()},I={mode:i,persisted:l,beforeEnter(w){let P=c;if(!n.isMounted)if(o)P=L||c;else return;w[Ye]&&w[Ye](!0);let M=g[m];M&&qe(e,M)&&M.el[Ye]&&M.el[Ye](),C(P,[w])},enter(w){if(!Na&&g[m]===e)return;let P=u,M=f,V=a;if(!n.isMounted)if(o)P=H||u,M=b||f,V=h||a;else return;let K=!1;w[kn]=ne=>{K||(K=!0,ne?C(V,[w]):C(M,[w]),I.delayedLeave&&I.delayedLeave(),w[kn]=void 0)};let q=w[kn].bind(null,!1);P?x(P,[w,q]):q()},leave(w,P){let M=String(e.key);if(w[kn]&&w[kn](!0),n.isUnmounting)return P();C(_,[w]);let V=!1;w[Ye]=q=>{V||(V=!0,P(),q?C(N,[w]):C(v,[w]),w[Ye]=void 0,g[M]===e&&delete g[M])};let K=w[Ye].bind(null,!1);g[M]=e,E?x(E,[w,K]):K()},clone(w){let P=Wt(w,t,n,s,r);return r&&r(P),P}};return I}function Mr(e){if(Jn(e))return e=st(e),e.children=null,e}function Rs(e){if(!Jn(e))return Ks(e.type)&&e.children?Bi(e.children):e;if(e.component)return e.component.subTree;let{shapeFlag:t,children:n}=e;if(n){if(t&16)return n[0];if(t&32&&B(n.default))return n.default()}}function nt(e,t){if(e.shapeFlag&6&&e.component){e.transition=t;let n=e.component.subTree;nt(Ks(n.type)&&Rs(n)||n,t)}else e.shapeFlag&128?(e.ssContent.transition=t.clone(e.ssContent),e.ssFallback.transition=t.clone(e.ssFallback)):e.transition=t}function qn(e,t=!1,n){let s=[],r=0;for(let o=0;o<e.length;o++){let i=e[o],l=n==null?i.key:String(n)+String(i.key!=null?i.key:o);i.type===ve?(i.patchFlag&128&&r++,s=s.concat(qn(i.children,t,l))):(t||i.type!==pe)&&s.push(l!=null?st(i,{key:l}):i)}if(r>1)for(let o=0;o<s.length;o++)s[o].patchFlag=-2;return s}function Gs(e,t){return B(e)?Q({name:e.name},t,{setup:e}):e}function Ma(){let e=Ce();return e?(e.appContext.config.idPrefix||"v")+"-"+e.ids[0]+e.ids[1]++:""}function Zr(e){e.ids=[e.ids[0]+e.ids[2]+++"-",0,0]}function Ia(e){let t=Ce(),n=vs(null);if(t){let r=t.refs===J?t.refs={}:t.refs;Object.defineProperty(r,e,{enumerable:!0,get:()=>n.value,set:o=>n.value=o})}return n}function Ni(e,t){let n;return!!((n=Object.getOwnPropertyDescriptor(e,t))&&!n.configurable)}var Ps=new WeakMap;function pn(e,t,n,s,r=!1){if(F(e)){e.forEach((N,L)=>pn(N,t&&(F(t)?t[L]:t),n,s,r));return}if(ut(s)&&!r){s.shapeFlag&512&&s.type.__asyncResolved&&s.component.subTree.component&&pn(e,t,n,s.component.subTree);return}let o=s.shapeFlag&4?Zn(s.component):s.el,i=r?null:o,{i:l,r:c}=e,u=t&&t.r,f=l.refs===J?l.refs={}:l.refs,a=l.setupState,_=z(a),E=a===J?dr:N=>Ni(f,N)?!1:ee(_,N),v=(N,L)=>!(L&&Ni(f,L));if(u!=null&&u!==c){if(bi(t),se(u))f[u]=null,E(u)&&(a[u]=null);else if(ue(u)){let N=t;v(u,N.k)&&(u.value=null),N.k&&(f[N.k]=null)}}if(B(c))zt(c,l,12,[i,f]);else{let N=se(c),L=ue(c);if(N||L){let H=()=>{if(e.f){let b=N?E(c)?a[c]:f[c]:v(c)||!e.k?c.value:f[e.k];if(r)F(b)&&bn(b,o);else if(F(b))b.includes(o)||b.push(o);else if(N)f[c]=[o],E(c)&&(a[c]=f[c]);else{let h=[o];v(c,e.k)&&(c.value=h),e.k&&(f[e.k]=h)}}else N?(f[c]=i,E(c)&&(a[c]=i)):L&&(v(c,e.k)&&(c.value=i),e.k&&(f[e.k]=i))};if(i){let b=()=>{H(),Ps.delete(e)};b.id=-1,Ps.set(e,b),ge(b,n)}else bi(e),H()}}}function bi(e){let t=Ps.get(e);t&&(t.flags|=8,Ps.delete(e))}var Oi=!1,ln=()=>{Oi||(console.error("Hydration completed but contains mismatches."),Oi=!0)},$a=e=>e.namespaceURI.includes("svg")&&e.tagName!=="foreignObject",Fa=e=>e.namespaceURI.includes("MathML"),ws=e=>{if(e.nodeType===1){if($a(e))return"svg";if(Fa(e))return"mathml"}},un=e=>e.nodeType===8;function La(e){let{mt:t,p:n,o:{patchProp:s,createText:r,nextSibling:o,parentNode:i,remove:l,insert:c,createComment:u}}=e,f=(h,m)=>{if(!m.hasChildNodes()){n(null,h,m),As(),m._vnode=h;return}a(m.firstChild,h,null,null,null),As(),m._vnode=h},a=(h,m,g,C,x,I=!1)=>{I=I||!!m.dynamicChildren;let w=un(h)&&h.data==="[",P=()=>N(h,m,g,C,x,w),{type:M,ref:V,shapeFlag:K,patchFlag:q}=m,ne=h.nodeType;m.el=h,q===-2&&(I=!1,m.dynamicChildren=null);let U=null;switch(M){case Ot:ne!==3?m.children===""?(c(m.el=r(""),i(h),h),U=h):U=P():(h.data!==m.children&&(ln(),h.data=m.children),U=o(h));break;case pe:b(h)?(U=o(h),H(m.el=h.content.firstChild,h,g)):ne!==8||w?U=P():U=o(h);break;case ft:if(w&&(h=o(h),ne=h.nodeType),ne===1||ne===3){U=h;let X=!m.children.length;for(let Y=0;Y<m.staticCount;Y++)X&&(m.children+=U.nodeType===1?U.outerHTML:U.data),Y===m.staticCount-1&&(m.anchor=U),U=o(U);return w?o(U):U}else P();break;case ve:w?U=v(h,m,g,C,x,I):U=P();break;default:if(K&1)(ne!==1||m.type.toLowerCase()!==h.tagName.toLowerCase())&&!b(h)?U=P():U=_(h,m,g,C,x,I);else if(K&6){m.slotScopeIds=x;let X=i(h);if(w?U=L(h):un(h)&&h.data==="teleport start"?U=L(h,h.data,"teleport end"):U=o(h),t(m,X,null,g,C,ws(X),I),ut(m)&&!m.component.subTree){let Y;w?(Y=ce(ft),Y.anchor=U?U.previousSibling:X.lastChild):Y=h.nodeType===3?uo(""):ce("div"),Y.el=h,m.component.subTree=Y}}else K&64?ne!==8?U=P():U=m.type.hydrate(h,m,g,C,x,I,e,E):K&128&&(U=m.type.hydrate(h,m,g,C,ws(i(h)),x,I,e,a))}return V!=null&&pn(V,null,C,m),U},_=(h,m,g,C,x,I)=>{I=I||!!m.dynamicChildren;let{type:w,dynamicProps:P,props:M,patchFlag:V,shapeFlag:K,dirs:q,transition:ne}=m,U=w==="input"||w==="option",X=!!P;if(U||X||V!==-1){q&&tt(m,null,g,"created");let Y=!1;if(b(h)){Y=gl(null,ne)&&g&&g.vnode.props&&g.vnode.props.appear;let le=h.content.firstChild;if(Y){let Ve=le.getAttribute("class");Ve&&(le.$cls=Ve),ne.beforeEnter(le)}H(le,h,g),m.el=h=le}if(K&16&&!(M&&(M.innerHTML||M.textContent))){let le=E(h.firstChild,m,h,g,C,x,I);for(le&&!Ss(h,1)&&ln();le;){let Ve=le;le=le.nextSibling,l(Ve)}}else if(K&8){let le=m.children;le[0]===`
`&&(h.tagName==="PRE"||h.tagName==="TEXTAREA")&&(le=le.slice(1));let{textContent:Ve}=h;Ve!==le&&Ve!==le.replace(/\r\n|\r/g,`
`)&&(Ss(h,0)||ln(),h.textContent=m.children)}if(M){if(U||X||!I||V&48){let le=h.tagName.includes("-"),Ve=h.namespaceURI.includes("svg")?"svg":h.namespaceURI.includes("MathML")?"mathml":void 0;for(let ye in M)if(U&&(ye.endsWith("value")||ye==="indeterminate")||xt(ye)&&!mt(ye)||ye[0]==="."||le&&!mt(ye)||P&&P.includes(ye)){if(Ua(h,ye,M[ye]))continue;s(h,ye,null,M[ye],Ve,g)}}else if(M.onClick)s(h,"onClick",null,M.onClick,void 0,g);else if(V&4&&Ue(M.style))for(let le in M.style)M.style[le]}let fe;(fe=M&&M.onVnodeBeforeMount)&&ke(fe,g,m),q&&tt(m,null,g,"beforeMount"),((fe=M&&M.onVnodeMounted)||q||Y)&&yl(()=>{fe&&ke(fe,g,m),Y&&ne.enter(h),q&&tt(m,null,g,"mounted")},C)}return h.nextSibling},E=(h,m,g,C,x,I,w)=>{w=w||!!m.dynamicChildren;let P=m.children,M=P.length,V=!1;for(let K=0;K<M;K++){let q=w?P[K]:P[K]=Me(P[K]),ne=q.type===Ot;h?(ne&&!w&&K+1<M&&Me(P[K+1]).type===Ot&&(c(r(h.data.slice(q.children.length)),g,o(h)),h.data=q.children),h=a(h,q,C,x,I,w)):ne&&!q.children?c(q.el=r(""),g):(V||(V=!0,Ss(g,1)||ln()),n(null,q,g,null,C,x,ws(g),I))}return h},v=(h,m,g,C,x,I)=>{let{slotScopeIds:w}=m;w&&(x=x?x.concat(w):w);let P=i(h),M=E(o(h),m,P,g,C,x,I);return M&&un(M)&&M.data==="]"?o(m.anchor=M):(ln(),c(m.anchor=u("]"),P,M),M)},N=(h,m,g,C,x,I)=>{if(Ba(h,m)||ln(),m.el=null,I){let M=L(h);for(;;){let V=o(h);if(V&&V!==M)l(V);else break}}let w=o(h),P=i(h);return l(h),n(null,m,P,w,g,C,ws(P),x),g&&(g.vnode.el=m.el,Zs(g,m.el)),w},L=(h,m="[",g="]")=>{let C=0;for(;h;)if(h=o(h),h&&un(h)&&(h.data===m&&C++,h.data===g)){if(C===0)return o(h);C--}return h},H=(h,m,g)=>{let C=m.parentNode;C&&C.replaceChild(h,m);let x=g;for(;x;)x.vnode.el===m&&(x.vnode.el=x.subTree.el=h),x=x.parent},b=h=>h.nodeType===1&&h.tagName==="TEMPLATE";return[f,a]}var Ha=new Set(["src","srcset","href","poster"]);function Ua(e,t,n){return Ha.has(t)?e.getAttribute(t)===(n==null?null:`${n}`):!1}var ks="data-allow-mismatch",ja={0:"text",1:"children",2:"class",3:"style",4:"attribute"};function Ss(e,t){if(t===0||t===1)for(;e&&!e.hasAttribute(ks);)e=e.parentElement;return Qr(e&&e.getAttribute(ks),t)}function Qr(e,t){if(e==null)return!1;if(e==="")return!0;{let n=e.split(",");return t===0&&n.includes("children")?!0:n.includes(ja[t])}}function Ba(e,t){return Ss(e.parentElement,1)||Ka(e)||Wa(t)}function Ka(e){return e.nodeType===1&&Qr(e.getAttribute(ks),1)}function Wa({props:e}){let t=e&&e[ks];return typeof t=="string"&&Qr(t,1)}var Ya=wn().requestIdleCallback||(e=>setTimeout(e,1)),Ga=wn().cancelIdleCallback||(e=>clearTimeout(e)),za=(e=1e4)=>t=>{let n=Ya(t,{timeout:e});return()=>Ga(n)};function qa(e){let{top:t,left:n,bottom:s,right:r}=e.getBoundingClientRect(),{innerHeight:o,innerWidth:i}=window;return(t>0&&t<o||s>0&&s<o)&&(n>0&&n<i||r>0&&r<i)}var Ja=e=>(t,n)=>{let s=new IntersectionObserver(r=>{for(let o of r)if(o.isIntersecting){s.disconnect(),t();break}},e);return n(r=>{if(r instanceof Element){if(qa(r))return t(),s.disconnect(),!1;s.observe(r)}}),()=>s.disconnect()},Xa=e=>t=>{if(e){let n=matchMedia(e);if(n.matches)t();else return n.addEventListener("change",t,{once:!0}),()=>n.removeEventListener("change",t)}},Za=(e=[])=>(t,n)=>{se(e)&&(e=[e]);let s=!1,r=i=>{s||(s=!0,o(),t(),i.target.dispatchEvent(new i.constructor(i.type,i)))},o=()=>{n(i=>{for(let l of e)i.removeEventListener(l,r)})};return n(i=>{for(let l of e)i.addEventListener(l,r,{once:!0})}),o};function Qa(e,t){if(un(e)&&e.data==="["){let n=1,s=e.nextSibling;for(;s;){if(s.nodeType===1){if(t(s)===!1)break}else if(un(s))if(s.data==="]"){if(--n===0)break}else s.data==="["&&n++;s=s.nextSibling}}else t(e)}var ut=e=>!!e.type.__asyncLoader;function eu(e){B(e)&&(e={loader:e});let{loader:t,loadingComponent:n,errorComponent:s,delay:r=200,hydrate:o,timeout:i,suspensible:l=!0,onError:c}=e,u=null,f,a=0,_=()=>(a++,u=null,E()),E=()=>{let v;return u||(v=u=t().catch(N=>{if(N=N instanceof Error?N:new Error(String(N)),c)return new Promise((L,H)=>{c(N,()=>L(_()),()=>H(N),a+1)});throw N}).then(N=>v!==u&&u?u:(N&&(N.__esModule||N[Symbol.toStringTag]==="Module")&&(N=N.default),f=N,N)))};return Gs({name:"AsyncComponentWrapper",__asyncLoader:E,__asyncHydrate(v,N,L){let H=v.isConnected,b=!1;(N.bu||(N.bu=[])).push(()=>b=!0);let h=()=>{b||!v.parentNode||H&&!v.isConnected||L()},m=o?()=>{let g=o(h,C=>Qa(v,C));g&&(N.bum||(N.bum=[])).push(g)}:h;f?m():E().then(()=>!N.isUnmounted&&m())},get __asyncResolved(){return f},setup(){let v=be;if(Zr(v),f)return()=>Ts(f,v);let N=g=>{u=null,qt(g,v,13,!s)};if(l&&v.suspense||Gt)return E().then(g=>()=>Ts(g,v)).catch(g=>(N(g),()=>s?ce(s,{error:g}):null));let L=Ft(!1),H=Ft(),b=Ft(!!r),h,m;return _n(()=>{h!=null&&clearTimeout(h),m!=null&&clearTimeout(m)}),r&&(m=setTimeout(()=>{v.isUnmounted||(b.value=!1)},r)),i!=null&&(h=setTimeout(()=>{if(!v.isUnmounted&&!L.value&&!H.value){let g=new Error(`Async component timed out after ${i}ms.`);N(g),H.value=g}},i)),E().then(()=>{v.isUnmounted||(L.value=!0,v.parent&&Jn(v.parent.vnode)&&v.parent.update())}).catch(g=>{if(v.isUnmounted){u=null;return}N(g),H.value=g}),()=>{if(L.value&&f)return Ts(f,v);if(H.value&&s)return ce(s,{error:H.value});if(n&&!b.value)return Ts(n,v)}}})}function Ts(e,t){let{ref:n,props:s,children:r,ce:o}=t.vnode,i=ce(e,s,r);return i.ref=n,i.ce=o,delete t.vnode.ce,i}var Jn=e=>e.type.__isKeepAlive,tu={name:"KeepAlive",__isKeepAlive:!0,props:{include:[String,RegExp,Array],exclude:[String,RegExp,Array],max:[String,Number]},setup(e,{slots:t}){let n=Ce(),s=n.ctx;if(!s.renderer)return()=>{let b=t.default&&t.default();return b&&b.length===1?b[0]:b};let r=new Map,o=new Set,i=null,l=n.suspense,{renderer:{p:c,m:u,um:f,o:{createElement:a}}}=s,_=a("div");s.activate=(b,h,m,g,C)=>{let x=b.component;u(b,h,m,0,l),c(x.vnode,b,h,m,x,l,g,b.slotScopeIds,C),ge(()=>{x.isDeactivated=!1,x.a&&yt(x.a);let I=b.props&&b.props.onVnodeMounted;I&&ke(I,x.parent,b)},l)},s.deactivate=b=>{let h=b.component;Is(h.m),Is(h.a),u(b,_,null,1,l),ge(()=>{h.da&&yt(h.da);let m=b.props&&b.props.onVnodeUnmounted;m&&ke(m,h.parent,b),h.isDeactivated=!0},l)};function E(b){Ir(b),f(b,n,l,!0)}function v(b){r.forEach((h,m)=>{let g=js(ut(h)?h.type.__asyncResolved||{}:h.type);g&&!b(g)&&N(m)})}function N(b){let h=r.get(b);h&&(!i||!qe(h,i))?E(h):i&&Ir(i),r.delete(b),o.delete(b)}Bt(()=>[e.include,e.exclude],([b,h])=>{b&&v(m=>In(b,m)),h&&v(m=>!In(h,m))},{flush:"post",deep:!0});let L=null,H=()=>{L!=null&&($s(n.subTree.type)?ge(()=>{let b=Ds(n.subTree);b.component&&r.set(L,b)},n.subTree.suspense):r.set(L,Ds(n.subTree)))};return gn(H),Xn(H),Js(()=>{r.forEach(b=>{let{subTree:h,suspense:m}=n,g=Ds(h);if(b.type===g.type&&b.key===g.key){Ir(g);let C=g.component.da;C&&ge(C,m);return}E(b)})}),()=>{if(L=null,!t.default)return i=null;let b=t.default(),h=b[0];if(b.length>1)return i=null,b;if(!dt(h)||!(h.shapeFlag&4)&&!(h.shapeFlag&128))return i=null,h;let m=Ds(h);if(m.type===pe)return i=null,m;let g=m.type,C=js(ut(m)?m.type.__asyncResolved||{}:g),{include:x,exclude:I,max:w}=e;if(x&&(!C||!In(x,C))||I&&C&&In(I,C))return m.shapeFlag&=-257,i=m,h;let P=m.key==null?g:m.key,M=r.get(P);return m.el&&(m=st(m),h.shapeFlag&128&&(h.ssContent=m)),L=P,M?(m.el=M.el,m.component=M.component,m.transition&&nt(m,m.transition),m.shapeFlag|=512,o.delete(P),o.add(P)):(o.add(P),w&&o.size>parseInt(w,10)&&N(o.values().next().value)),m.shapeFlag|=256,i=m,$s(h.type)?h:m}}},nu=tu;function In(e,t){return F(e)?e.some(n=>In(n,t)):se(e)?e.split(",").includes(t):Ro(e)?(e.lastIndex=0,e.test(t)):!1}function Wi(e,t){Gi(e,"a",t)}function Yi(e,t){Gi(e,"da",t)}function Gi(e,t,n=be){let s=e.__wdc||(e.__wdc=()=>{let r=n;for(;r;){if(r.isDeactivated)return;r=r.parent}return e()});if(zs(t,s,n),n){let r=n.parent;for(;r&&r.parent;)Jn(r.parent.vnode)&&su(s,t,n,r),r=r.parent}}function su(e,t,n,s){let r=zs(t,e,s,!0);_n(()=>{bn(s[t],r)},n)}function Ir(e){e.shapeFlag&=-257,e.shapeFlag&=-513}function Ds(e){return e.shapeFlag&128?e.ssContent:e}function zs(e,t,n=be,s=!1){if(n){let r=n[e]||(n[e]=[]),o=t.__weh||(t.__weh=(...i)=>{Be();let l=mn(n),c=Ie(t,n,e,i);return l(),Ke(),c});return s?r.unshift(o):r.push(o),o}}var ht=e=>(t,n=be)=>{(!Gt||e==="sp")&&zs(e,(...s)=>t(...s),n)},zi=ht("bm"),gn=ht("m"),qs=ht("bu"),Xn=ht("u"),Js=ht("bum"),_n=ht("um"),qi=ht("sp"),Ji=ht("rtg"),Xi=ht("rtc");function Zi(e,t=be){zs("ec",e,t)}var eo="components",ru="directives";function ou(e,t){return to(eo,e,!0,t)||e}var Qi=Symbol.for("v-ndc");function iu(e){return se(e)?to(eo,e,!1)||e:e||Qi}function lu(e){return to(ru,e)}function to(e,t,n=!0,s=!1){let r=Oe||be;if(r){let o=r.type;if(e===eo){let l=js(o,!1);if(l&&(l===t||l===ae(t)||l===Et(ae(t))))return o}let i=wi(r[e]||o[e],t)||wi(r.appContext[e],t);return!i&&s?o:i}}function wi(e,t){return e&&(e[t]||e[ae(t)]||e[Et(ae(t))])}function cu(e,t,n,s){let r,o=n&&n[s],i=F(e);if(i||se(e)){let l=i&&Ue(e),c=!1,u=!1;l&&(c=!Ee(e),u=Pe(e),e=Rn(e)),r=new Array(e.length);for(let f=0,a=e.length;f<a;f++)r[f]=t(c?u?It(je(e[f])):je(e[f]):e[f],f,void 0,o&&o[f])}else if(typeof e=="number"){r=new Array(e);for(let l=0;l<e;l++)r[l]=t(l+1,l,void 0,o&&o[l])}else if(Z(e))if(e[Symbol.iterator])r=Array.from(e,(l,c)=>t(l,c,void 0,o&&o[c]));else{let l=Object.keys(e);r=new Array(l.length);for(let c=0,u=l.length;c<u;c++){let f=l[c];r[c]=t(e[f],f,c,o&&o[c])}}else r=[];return n&&(n[s]=r),r}function au(e,t){for(let n=0;n<t.length;n++){let s=t[n];if(F(s))for(let r=0;r<s.length;r++)e[s[r].name]=s[r].fn;else s&&(e[s.name]=s.key?(...r)=>{let o=s.fn(...r);return o&&(o.key=s.key),o}:s.fn)}return e}function uu(e,t,n,s,r,o){if(n==null&&(n={}),Oe.ce||Oe.parent&&ut(Oe.parent)&&Oe.parent.ce){let u=o!=null&&n.key==null?Q({},n,{key:o}):n,f=Object.keys(u).length>0;return t!=="default"&&(u.name=t),Kn(),Fs(ve,null,[ce("slot",u,s&&s())],f?-2:64)}let i=e[t];i&&i._c&&(i._d=!1);let l=pt.length;Kn();let c;try{let u=i&&no(i(n)),f=n.key||o||u&&u.key;c=Fs(ve,{key:(f&&!we(f)?f:`_${t}`)+(!u&&s?"_fb":"")},u||(s?s():[]),u&&e._===1?64:-2)}catch(u){for(let f=pt.length;f>l;f--)Qs();throw u}finally{i&&i._c&&(i._d=!0)}return!r&&c.scopeId&&(c.slotScopeIds=[c.scopeId+"-s"]),c}function no(e){return e.some(t=>dt(t)?!(t.type===pe||t.type===ve&&!no(t.children)):!0)?e:null}function fu(e,t){let n={};for(let s in e)n[t&&/[A-Z]/.test(s)?`on:${s}`:At(s)]=e[s];return n}var Ur=e=>e?Dl(e)?Zn(e):Ur(e.parent):null;var Ln=Q(Object.create(null),{$:e=>e,$el:e=>e.vnode.el,$data:e=>e.data,$props:e=>e.props,$attrs:e=>e.attrs,$slots:e=>e.slots,$refs:e=>e.refs,$parent:e=>Ur(e.parent),$root:e=>Ur(e.root),$host:e=>e.ce,$emit:e=>e.emit,$options:e=>so(e),$forceUpdate:e=>e.f||(e.f=()=>{qr(e.update)}),$nextTick:e=>e.n||(e.n=Gn.bind(e.proxy)),$watch:e=>Va.bind(e)});var $r=(e,t)=>e!==J&&!e.__isScriptSetup&&ee(e,t),jr={get({_:e},t){if(t==="__v_skip")return!0;let{ctx:n,setupState:s,data:r,props:o,accessCache:i,type:l,appContext:c}=e;if(t[0]!=="$"){let _=i[t];if(_!==void 0)switch(_){case 1:return s[t];case 2:return r[t];case 4:return n[t];case 3:return o[t]}else{if($r(s,t))return i[t]=1,s[t];if(r!==J&&ee(r,t))return i[t]=2,r[t];if(ee(o,t))return i[t]=3,o[t];if(n!==J&&ee(n,t))return i[t]=4,n[t];Br&&(i[t]=0)}}let u=Ln[t],f,a;if(u)return t==="$attrs"&&Ne(e.attrs,"get",""),u(e);if((f=l.__cssModules)&&(f=f[t]))return f;if(n!==J&&ee(n,t))return i[t]=4,n[t];if(a=c.config.globalProperties,ee(a,t))return a[t]},set({_:e},t,n){let{data:s,setupState:r,ctx:o}=e;return $r(r,t)?(r[t]=n,!0):s!==J&&ee(s,t)?(s[t]=n,!0):ee(e.props,t)||t[0]==="$"&&t.slice(1)in e?!1:(o[t]=n,!0)},has({_:{data:e,setupState:t,accessCache:n,ctx:s,appContext:r,props:o,type:i}},l){let c;return!!(n[l]||e!==J&&l[0]!=="$"&&ee(e,l)||$r(t,l)||ee(o,l)||ee(s,l)||ee(Ln,l)||ee(r.config.globalProperties,l)||(c=i.__cssModules)&&c[l])},defineProperty(e,t,n){return n.get!=null?e._.accessCache[t]=0:ee(n,"value")&&this.set(e,t,n.value,null),Reflect.defineProperty(e,t,n)}},pu=Q({},jr,{get(e,t){if(t!==Symbol.unscopables)return jr.get(e,t,e)},has(e,t){return t[0]!=="_"&&!ko(t)}});function du(){return null}function hu(){return null}function gu(e){}function _u(e){}function mu(){return null}function Eu(){}function yu(e,t){return null}function vu(){return el("useSlots").slots}function Nu(){return el("useAttrs").attrs}function el(e){let t=Ce();return t.setupContext||(t.setupContext=xl(t))}function jn(e){return F(e)?e.reduce((t,n)=>(t[n]=null,t),{}):e}function bu(e,t){let n=jn(e);for(let s in t){if(s.startsWith("__skip"))continue;let r=n[s];r?F(r)||B(r)?r=n[s]={type:r,default:t[s]}:r.default=t[s]:r===null&&(r=n[s]={default:t[s]}),r&&t[`__skip_${s}`]&&(r.skipFactory=!0)}return n}function Ou(e,t){return!e||!t?e||t:F(e)&&F(t)?e.concat(t):Q({},jn(e),jn(t))}function wu(e,t){let n={};for(let s in e)t.includes(s)||Object.defineProperty(n,s,{enumerable:!0,get:()=>e[s]});return n}function Tu(e){let t=Ce(),n=Gt,s=e();Yn(),n&&wt(!1);let r=()=>{mn(t),n&&wt(!0)},o=()=>{Ce()!==t&&t.scope.off(),Yn(),n&&wt(!1)};return rs(s)&&(s=s.catch(i=>{throw r(),Promise.resolve().then(()=>Promise.resolve().then(o)),i})),[s,()=>{r(),Promise.resolve().then(o)}]}var Br=!0;function Du(e){let t=so(e),n=e.proxy,s=e.ctx;Br=!1,t.beforeCreate&&Ti(t.beforeCreate,e,"bc");let{data:r,computed:o,methods:i,watch:l,provide:c,inject:u,created:f,beforeMount:a,mounted:_,beforeUpdate:E,updated:v,activated:N,deactivated:L,beforeDestroy:H,beforeUnmount:b,destroyed:h,unmounted:m,render:g,renderTracked:C,renderTriggered:x,errorCaptured:I,serverPrefetch:w,expose:P,inheritAttrs:M,components:V,directives:K,filters:q}=t;if(u&&Su(u,s,null),i)for(let X in i){let Y=i[X];B(Y)&&(s[X]=Y.bind(n))}if(r){let X=r.call(n,n);Z(X)&&(e.data=on(X))}if(Br=!0,o)for(let X in o){let Y=o[X],fe=B(Y)?Y.bind(n,n):B(Y.get)?Y.get.bind(n,n):Te,le=!B(Y)&&B(Y.set)?Y.set.bind(n):Te,Ve=Rl({get:fe,set:le});Object.defineProperty(s,X,{enumerable:!0,configurable:!0,get:()=>Ve.value,set:ye=>Ve.value=ye})}if(l)for(let X in l)tl(l[X],s,n,X);if(c){let X=B(c)?c.call(n):c;Reflect.ownKeys(X).forEach(Y=>{Ii(Y,X[Y])})}f&&Ti(f,e,"c");function U(X,Y){F(Y)?Y.forEach(fe=>X(fe.bind(n))):Y&&X(Y.bind(n))}if(U(zi,a),U(gn,_),U(qs,E),U(Xn,v),U(Wi,N),U(Yi,L),U(Zi,I),U(Xi,C),U(Ji,x),U(Js,b),U(_n,m),U(qi,w),F(P))if(P.length){let X=e.exposed||(e.exposed={});P.forEach(Y=>{Object.defineProperty(X,Y,{get:()=>n[Y],set:fe=>n[Y]=fe,enumerable:!0})})}else e.exposed||(e.exposed={});g&&e.render===Te&&(e.render=g),M!=null&&(e.inheritAttrs=M),V&&(e.components=V),K&&(e.directives=K),w&&Zr(e)}function Su(e,t,n=Te){F(e)&&(e=Kr(e));for(let s in e){let r=e[s],o;Z(r)?"default"in r?o=Fn(r.from||s,r.default,!0):o=Fn(r.from||s):o=Fn(r),ue(o)?Object.defineProperty(t,s,{enumerable:!0,configurable:!0,get:()=>o.value,set:i=>o.value=i}):t[s]=o}}function Ti(e,t,n){Ie(F(e)?e.map(s=>s.bind(t.proxy)):e.bind(t.proxy),t,n)}function tl(e,t,n,s){let r=s.includes(".")?Hi(n,s):()=>n[s];if(se(e)){let o=t[e];B(o)&&Bt(r,o)}else if(B(e))Bt(r,e.bind(n));else if(Z(e))if(F(e))e.forEach(o=>tl(o,t,n,s));else{let o=B(e.handler)?e.handler.bind(n):t[e.handler];B(o)&&Bt(r,o,e)}}function so(e){let t=e.type,{mixins:n,extends:s}=t,{mixins:r,optionsCache:o,config:{optionMergeStrategies:i}}=e.appContext,l=o.get(t),c;return l?c=l:!r.length&&!n&&!s?c=t:(c={},r.length&&r.forEach(u=>Ms(c,u,i,!0)),Ms(c,t,i)),Z(t)&&o.set(t,c),c}function Ms(e,t,n,s=!1){let{mixins:r,extends:o}=t;o&&Ms(e,o,n,!0),r&&r.forEach(i=>Ms(e,i,n,!0));for(let i in t)if(!(s&&i==="expose")){let l=Cu[i]||n&&n[i];e[i]=l?l(e[i],t[i]):t[i]}return e}var Cu={data:Di,props:Si,emits:Si,methods:$n,computed:$n,beforeCreate:xe,created:xe,beforeMount:xe,mounted:xe,beforeUpdate:xe,updated:xe,beforeDestroy:xe,beforeUnmount:xe,destroyed:xe,unmounted:xe,activated:xe,deactivated:xe,errorCaptured:xe,serverPrefetch:xe,components:$n,directives:$n,watch:xu,provide:Di,inject:Vu};function Di(e,t){return t?e?function(){return Q(B(e)?e.call(this,this):e,B(t)?t.call(this,this):t)}:t:e}function Vu(e,t){return $n(Kr(e),Kr(t))}function Kr(e){if(F(e)){let t={};for(let n=0;n<e.length;n++)t[e[n]]=e[n];return t}return e}function xe(e,t){return e?[...new Set([].concat(e,t))]:t}function $n(e,t){return e?Q(Object.create(null),e,t):t}function Si(e,t){return e?F(e)&&F(t)?[...new Set([...e,...t])]:Q(Object.create(null),jn(e),jn(t??{})):t}function xu(e,t){if(!e)return t;if(!t)return e;let n=Q(Object.create(null),e);for(let s in t)n[s]=xe(e[s],t[s]);return n}function nl(){return{app:null,config:{isNativeTag:dr,performance:!1,globalProperties:{},optionMergeStrategies:{},errorHandler:void 0,warnHandler:void 0,compilerOptions:{}},mixins:[],components:{},directives:{},provides:Object.create(null),optionsCache:new WeakMap,propsCache:new WeakMap,emitsCache:new WeakMap}}var Au=0;function Ru(e,t){return function(s,r=null){B(s)||(s=Q({},s)),r!=null&&!Z(r)&&(r=null);let o=nl(),i=new WeakSet,l=[],c=!1,u=o.app={_uid:Au++,_component:s,_props:r,_container:null,_context:o,_instance:null,version:kl,get config(){return o.config},set config(f){},use(f,...a){return i.has(f)||(f&&B(f.install)?(i.add(f),f.install(u,...a)):B(f)&&(i.add(f),f(u,...a))),u},mixin(f){return o.mixins.includes(f)||o.mixins.push(f),u},component(f,a){return a?(o.components[f]=a,u):o.components[f]},directive(f,a){return a?(o.directives[f]=a,u):o.directives[f]},mount(f,a,_){if(!c){let E=u._ceVNode||ce(s,r);return E.appContext=o,_===!0?_="svg":_===!1&&(_=void 0),a&&t?t(E,f):e(E,f,_),c=!0,u._container=f,f.__vue_app__=u,Zn(E.component)}},onUnmount(f){l.push(f)},unmount(){c&&(Ie(l,u._instance,16),e(null,u._container),delete u._container.__vue_app__)},provide(f,a){return o.provides[f]=a,u},runWithContext(f){let a=Kt;Kt=u;try{return f()}finally{Kt=a}}};return u}}var Kt=null;function Pu(e,t,n=J){let s=Ce(),r=ae(t),o=De(t),i=sl(e,r),l=Ns((c,u)=>{let f,a=J,_;return Li(()=>{let E=e[r];he(f,E)&&(f=E,u())}),{get(){return c(),n.get?n.get(f):f},set(E){let v=n.set?n.set(E):E;if(!he(v,f)&&!(a!==J&&he(E,a)))return;let N=s.vnode.props,L=!!(N&&(t in N||r in N||o in N)&&(`onUpdate:${t}`in N||`onUpdate:${r}`in N||`onUpdate:${o}`in N));L||(f=E,u()),s.emit(`update:${t}`,v),he(E,a)&&(he(E,v)&&!he(v,_)||L&&a!==J&&!he(v,f))&&u(),a=E,_=v}}});return l[Symbol.iterator]=()=>{let c=0;return{next(){return c<2?{value:c++?i||J:l,done:!1}:{done:!0}}}},l}var sl=(e,t)=>t==="modelValue"||t==="model-value"?e.modelModifiers:e[`${t}Modifiers`]||e[`${ae(t)}Modifiers`]||e[`${De(t)}Modifiers`];function ku(e,t,...n){if(e.isUnmounted)return;let s=e.vnode.props||J,r=n,o=t.startsWith("update:"),i=o&&sl(s,t.slice(7));i&&(i.trim&&(r=n.map(f=>se(f)?f.trim():f)),i.number&&(r=r.map(tn)));let l,c=s[l=At(t)]||s[l=At(ae(t))];!c&&o&&(c=s[l=At(De(t))]),c&&Ie(c,e,6,r);let u=s[l+"Once"];if(u){if(!e.emitted)e.emitted={};else if(e.emitted[l])return;e.emitted[l]=!0,Ie(u,e,6,r)}}var Mu=new WeakMap;function rl(e,t,n=!1){let s=n?Mu:t.emitsCache,r=s.get(e);if(r!==void 0)return r;let o=e.emits,i={},l=!1;if(!B(e)){let c=u=>{let f=rl(u,t,!0);f&&(l=!0,Q(i,f))};!n&&t.mixins.length&&t.mixins.forEach(c),e.extends&&c(e.extends),e.mixins&&e.mixins.forEach(c)}return!o&&!l?(Z(e)&&s.set(e,null),null):(F(o)?o.forEach(c=>i[c]=null):Q(i,o),Z(e)&&s.set(e,i),i)}function Xs(e,t){return!e||!xt(t)?!1:(t=t.slice(2),t=t==="Once"?t:t.replace(/Once$/,""),ee(e,t[0].toLowerCase()+t.slice(1))||ee(e,De(t))||ee(e,t))}function Cs(e){let{type:t,vnode:n,proxy:s,withProxy:r,propsOptions:[o],slots:i,attrs:l,emit:c,render:u,renderCache:f,props:a,data:_,setupState:E,ctx:v,inheritAttrs:N}=e,L=Un(e),H,b;try{if(n.shapeFlag&4){let g=r||s,C=g;H=Me(u.call(C,g,f,a,E,_,v)),b=l}else{let g=t;H=Me(g.length>1?g(a,{attrs:l,slots:i,emit:c}):g(a,null)),b=t.props?l:$u(l)}}catch(g){pt.length=0,qt(g,e,1),H=ce(pe)}let h=H,m;if(b&&N!==!1){let g=Object.keys(b),{shapeFlag:C}=h;g.length&&C&7&&(o&&g.some(Zt)&&(b=Fu(b,o)),h=st(h,b,!1,!0))}if(n.dirs&&(h=st(h,null,!1,!0),h.dirs=h.dirs?h.dirs.concat(n.dirs):n.dirs),n.transition){let g=Ks(h.type)&&Rs(h)||h;nt(g,n.transition)}return H=h,Un(L),H}function Iu(e,t=!0){let n;for(let s=0;s<e.length;s++){let r=e[s];if(dt(r)){if(r.type!==pe||r.children==="v-if"){if(n)return;n=r}}else return}return n}var $u=e=>{let t;for(let n in e)(n==="class"||n==="style"||xt(n))&&((t||(t={}))[n]=e[n]);return t},Fu=(e,t)=>{let n={};for(let s in e)(!Zt(s)||!(s.slice(9)in t))&&(n[s]=e[s]);return n};function Lu(e,t,n){let{props:s,children:r,component:o}=e,{props:i,children:l,patchFlag:c}=t,u=o.emitsOptions;if(t.dirs||t.transition)return!0;if(n&&c>=0){if(c&1024)return!0;if(c&16)return s?Ci(s,i,u):!!i;if(c&8){let f=t.dynamicProps;for(let a=0;a<f.length;a++){let _=f[a];if(ol(i,s,_)&&!Xs(u,_))return!0}}}else return(r||l)&&(!l||!l.$stable)?!0:s===i?!1:s?i?Ci(s,i,u):!0:!!i;return!1}function Ci(e,t,n){let s=Object.keys(t);if(s.length!==Object.keys(e).length)return!0;for(let r=0;r<s.length;r++){let o=s[r];if(ol(t,e,o)&&!Xs(n,o))return!0}return!1}function ol(e,t,n){let s=e[n],r=t[n];return n==="style"&&Z(s)&&Z(r)?!Re(s,r):s!==r}function Zs({vnode:e,parent:t,suspense:n},s){for(;t;){let r=t.subTree;if(r.suspense&&r.suspense.activeBranch===e&&(r.suspense.vnode.el=r.el=s,e=r),r===e)(e=t.vnode).el=s,t=t.parent;else break}n&&n.activeBranch===e&&(n.vnode.el=s)}var il={},ll=()=>Object.create(il),cl=e=>Object.getPrototypeOf(e)===il;function Hu(e,t,n,s=!1){let r={},o=ll();e.propsDefaults=Object.create(null),al(e,t,r,o);for(let i in e.propsOptions[0])i in r||(r[i]=void 0);n?e.props=s?r:ms(r):e.type.props?e.props=r:e.props=o,e.attrs=o}function Uu(e,t,n,s){let{props:r,attrs:o,vnode:{patchFlag:i}}=e,l=z(r),[c]=e.propsOptions,u=!1;if((s||i>0)&&!(i&16)){if(i&8){let f=e.vnode.dynamicProps;for(let a=0;a<f.length;a++){let _=f[a];if(Xs(e.emitsOptions,_))continue;let E=t[_];if(c)if(ee(o,_))E!==o[_]&&(o[_]=E,u=!0);else{let v=ae(_);r[v]=Wr(c,l,v,E,e,!1)}else E!==o[_]&&(o[_]=E,u=!0)}}}else{al(e,t,r,o)&&(u=!0);let f;for(let a in l)(!t||!ee(t,a)&&((f=De(a))===a||!ee(t,f)))&&(c?n&&(n[a]!==void 0||n[f]!==void 0)&&(r[a]=Wr(c,l,a,void 0,e,!0)):delete r[a]);if(o!==l)for(let a in o)(!t||!ee(t,a))&&(delete o[a],u=!0)}u&&Ze(e.attrs,"set","")}function al(e,t,n,s){let[r,o]=e.propsOptions,i=!1,l;if(t)for(let c in t){if(mt(c))continue;let u=t[c],f;r&&ee(r,f=ae(c))?!o||!o.includes(f)?n[f]=u:(l||(l={}))[f]=u:Xs(e.emitsOptions,c)||(!(c in s)||u!==s[c])&&(s[c]=u,i=!0)}if(o){let c=z(n),u=l||J;for(let f=0;f<o.length;f++){let a=o[f];n[a]=Wr(r,c,a,u[a],e,!ee(u,a))}}return i}function Wr(e,t,n,s,r,o){let i=e[n];if(i!=null){let l=ee(i,"default");if(l&&s===void 0){let c=i.default;if(i.type!==Function&&!i.skipFactory&&B(c)){let{propsDefaults:u}=r;if(n in u)s=u[n];else{let f=mn(r);s=u[n]=c.call(null,t),f()}}else s=c;r.ce&&r.ce._setProp(n,s)}i[0]&&(o&&!l?s=!1:i[1]&&(s===""||s===De(n))&&(s=!0))}return s}var ju=new WeakMap;function ul(e,t,n=!1){let s=n?ju:t.propsCache,r=s.get(e);if(r)return r;let o=e.props,i={},l=[],c=!1;if(!B(e)){let f=a=>{c=!0;let[_,E]=ul(a,t,!0);Q(i,_),E&&l.push(...E)};!n&&t.mixins.length&&t.mixins.forEach(f),e.extends&&f(e.extends),e.mixins&&e.mixins.forEach(f)}if(!o&&!c)return Z(e)&&s.set(e,Vt),Vt;if(F(o))for(let f=0;f<o.length;f++){let a=ae(o[f]);Vi(a)&&(i[a]=J)}else if(o)for(let f in o){let a=ae(f);if(Vi(a)){let _=o[f],E=i[a]=F(_)||B(_)?{type:_}:Q({},_),v=E.type,N=!1,L=!0;if(F(v))for(let H=0;H<v.length;++H){let b=v[H],h=B(b)&&b.name;if(h==="Boolean"){N=!0;break}else h==="String"&&(L=!1)}else N=B(v)&&v.name==="Boolean";E[0]=N,E[1]=L,(N||ee(E,"default"))&&l.push(a)}}let u=[i,l];return Z(e)&&s.set(e,u),u}function Vi(e){return e[0]!=="$"&&!mt(e)}var ro=e=>e==="_"||e==="_ctx"||e==="$stable",oo=e=>F(e)?e.map(Me):[Me(e)],Bu=(e,t,n)=>{if(t._n)return t;let s=Jr((...r)=>oo(t(...r)),n);return s._c=!1,s},fl=(e,t,n)=>{let s=e._ctx;for(let r in e){if(ro(r))continue;let o=e[r];if(B(o))t[r]=Bu(r,o,s);else if(o!=null){let i=oo(o);t[r]=()=>i}}},pl=(e,t)=>{let n=oo(t);e.slots.default=()=>n},dl=(e,t,n)=>{for(let s in t)(n||!ro(s))&&(e[s]=t[s])},Ku=(e,t,n)=>{let s=e.slots=ll();if(e.vnode.shapeFlag&32){let r=t._;r?(dl(s,t,n),n&&is(s,"_",r,!0)):fl(t,s)}else t&&pl(e,t)},Wu=(e,t,n)=>{let{vnode:s,slots:r}=e,o=!0,i=J;if(s.shapeFlag&32){let l=t._;l?n&&l===1?o=!1:dl(r,t,n):(o=!t.$stable,fl(t,r)),i=t}else t&&(pl(e,t),i={default:1});if(o)for(let l in r)!ro(l)&&i[l]==null&&delete r[l]};function Yu(){let e=[]}var ge=yl;function io(e){return hl(e)}function lo(e){return hl(e,La)}function hl(e,t){Yu();let n=wn();n.__VUE__=!0;let{insert:s,remove:r,patchProp:o,createElement:i,createText:l,createComment:c,setText:u,setElementText:f,parentNode:a,nextSibling:_,setScopeId:E=Te,insertStaticContent:v}=e,N=(p,d,y,S=null,O=null,T=null,k=void 0,R=null,A=!!d.dynamicChildren)=>{if(p===d)return;p&&!qe(p,d)&&(S=ss(p),ot(p,O,T,!0),p=null),d.patchFlag===-2&&(A=!1,d.dynamicChildren=null);let{type:D,ref:W,shapeFlag:$}=d;switch(D){case Ot:L(p,d,y,S);break;case pe:H(p,d,y,S);break;case ft:p==null&&b(d,y,S,k);break;case ve:K(p,d,y,S,O,T,k,R,A);break;default:$&1?C(p,d,y,S,O,T,k,R,A):$&6?q(p,d,y,S,O,T,k,R,A):($&64||$&128)&&D.process(p,d,y,S,O,T,k,R,A,Xt)}W!=null&&O?pn(W,p&&p.ref,T,d||p,!d):W==null&&p&&p.ref!=null&&pn(p.ref,null,T,p,!0)},L=(p,d,y,S)=>{if(p==null)s(d.el=l(d.children),y,S);else{let O=d.el=p.el;d.children!==p.children&&u(O,d.children)}},H=(p,d,y,S)=>{p==null?s(d.el=c(d.children||""),y,S):d.el=p.el},b=(p,d,y,S)=>{[p.el,p.anchor]=v(p.children,d,y,S,p.el,p.anchor)},h=(p,d,y,S)=>{if(d.children!==p.children){let O=_(p.anchor);g(p),[d.el,d.anchor]=v(d.children,y,O,S)}else d.el=p.el,d.anchor=p.anchor},m=({el:p,anchor:d},y,S)=>{let O;for(;p&&p!==d;)O=_(p),s(p,y,S),p=O;s(d,y,S)},g=({el:p,anchor:d})=>{let y;for(;p&&p!==d;)y=_(p),r(p),p=y;r(d)},C=(p,d,y,S,O,T,k,R,A)=>{if(d.type==="svg"?k="svg":d.type==="math"&&(k="mathml"),p==null)x(d,y,S,O,T,k,R,A);else{let D=p.el&&p.el._isVueCE?p.el:null;try{D&&D._beginPatch(),P(p,d,O,T,k,R,A)}finally{D&&D._endPatch()}}},x=(p,d,y,S,O,T,k,R)=>{let A,D,{props:W,shapeFlag:$,transition:j,dirs:G}=p;if(A=p.el=i(p.type,T,W&&W.is,W),$&8?f(A,p.children):$&16&&w(p.children,A,null,S,O,Fr(p,T),k,R),G&&tt(p,null,S,"created"),I(A,p,p.scopeId,k,S),W){for(let oe in W)oe!=="value"&&!mt(oe)&&o(A,oe,null,W[oe],T,S);"value"in W&&o(A,"value",null,W.value,T),(D=W.onVnodeBeforeMount)&&ke(D,S,p)}G&&tt(p,null,S,"beforeMount");let te=gl(O,j);te&&j.beforeEnter(A),s(A,d,y),((D=W&&W.onVnodeMounted)||te||G)&&ge(()=>{let re;D&&ke(D,S,p),te&&j.enter(A),G&&tt(p,null,S,"mounted")},O)},I=(p,d,y,S,O)=>{if(y&&E(p,y),S)for(let T=0;T<S.length;T++)E(p,S[T]);if(O){let T=O.subTree;if(d===T||$s(T.type)&&(T.ssContent===d||T.ssFallback===d)){let k=O.vnode;I(p,k,k.scopeId,k.slotScopeIds,O.parent)}}},w=(p,d,y,S,O,T,k,R,A=0)=>{for(let D=A;D<p.length;D++){let W=p[D]=R?at(p[D]):Me(p[D]);N(null,W,d,y,S,O,T,k,R)}},P=(p,d,y,S,O,T,k)=>{let R=d.el=p.el,{patchFlag:A,dynamicChildren:D,dirs:W}=d;A|=p.patchFlag&16;let $=p.props||J,j=d.props||J,G;if(y&&Ht(y,!1),(G=j.onVnodeBeforeUpdate)&&ke(G,y,d,p),W&&tt(d,p,y,"beforeUpdate"),y&&Ht(y,!0),D&&(!p.dynamicChildren||p.dynamicChildren.length!==D.length)&&(A=0,k=!1,D=null),($.innerHTML&&j.innerHTML==null||$.textContent&&j.textContent==null)&&f(R,""),D?M(p.dynamicChildren,D,R,y,S,Fr(d,O),T):k||fe(p,d,R,null,y,S,Fr(d,O),T,!1),A>0){if(A&16)V(R,$,j,y,O);else if(A&2&&$.class!==j.class&&o(R,"class",null,j.class,O),A&4&&o(R,"style",$.style,j.style,O),A&8){let te=d.dynamicProps;for(let oe=0;oe<te.length;oe++){let re=te[oe],de=$[re],_e=j[re];(_e!==de||re==="value")&&o(R,re,de,_e,O,y)}}A&1&&p.children!==d.children&&f(R,d.children)}else!k&&D==null&&V(R,$,j,y,O);((G=j.onVnodeUpdated)||W)&&ge(()=>{G&&ke(G,y,d,p),W&&tt(d,p,y,"updated")},S)},M=(p,d,y,S,O,T,k)=>{for(let R=0;R<d.length;R++){let A=p[R],D=d[R],W=A.el&&(A.type===ve||!qe(A,D)||A.shapeFlag&198)?a(A.el):y;N(A,D,W,null,S,O,T,k,!0)}},V=(p,d,y,S,O)=>{if(d!==y){if(d!==J)for(let T in d)!mt(T)&&!(T in y)&&o(p,T,d[T],null,O,S);for(let T in y){if(mt(T))continue;let k=y[T],R=d[T];k!==R&&T!=="value"&&o(p,T,R,k,O,S)}"value"in y&&o(p,"value",d.value,y.value,O)}},K=(p,d,y,S,O,T,k,R,A)=>{let D=d.el=p?p.el:l(""),W=d.anchor=p?p.anchor:l(""),{patchFlag:$,dynamicChildren:j,slotScopeIds:G}=d;G&&(R=R?R.concat(G):G),p==null?(s(D,y,S),s(W,y,S),w(d.children||[],y,W,O,T,k,R,A)):$>0&&$&64&&j&&p.dynamicChildren&&p.dynamicChildren.length===j.length?(M(p.dynamicChildren,j,y,O,T,k,R),(d.key!=null||O&&d===O.subTree)&&co(p,d,!0)):fe(p,d,y,W,O,T,k,R,A)},q=(p,d,y,S,O,T,k,R,A)=>{d.slotScopeIds=R,p==null?d.shapeFlag&512?O.ctx.activate(d,y,S,k,A):ne(d,y,S,O,T,k,A):U(p,d,A)},ne=(p,d,y,S,O,T,k)=>{let R=p.component=Tl(p,S,O);if(Jn(p)&&(R.ctx.renderer=Xt),Sl(R,!1,k),R.asyncDep){if(O&&O.registerDep(R,X,k),!p.el){let A=R.subTree=ce(pe);H(null,A,d,y),p.placeholder=A.el}}else X(R,p,d,y,O,T,k)},U=(p,d,y)=>{let S=d.component=p.component;if(Lu(p,d,y))if(S.asyncDep&&!S.asyncResolved){Y(S,d,y);return}else S.next=d,S.update();else d.el=p.el,S.vnode=d},X=(p,d,y,S,O,T,k)=>{let R=()=>{if(p.isMounted){let{next:$,bu:j,u:G,parent:te,vnode:oe}=p;{let $e=_l(p);if($e){$&&($.el=oe.el,Y(p,$,k)),$e.asyncDep.then(()=>{ge(()=>{p.isUnmounted||D()},O)});return}}let re=$,de;Ht(p,!1),$?($.el=oe.el,Y(p,$,k)):$=oe,j&&yt(j),(de=$.props&&$.props.onVnodeBeforeUpdate)&&ke(de,te,$,oe),Ht(p,!0);let _e=Cs(p),Ge=p.subTree;p.subTree=_e,N(Ge,_e,a(Ge.el),ss(Ge),p,O,T),$.el=_e.el,re===null&&Zs(p,_e.el),G&&ge(G,O),(de=$.props&&$.props.onVnodeUpdated)&&ge(()=>ke(de,te,$,oe),O)}else{let $,{el:j,props:G}=d,{bm:te,m:oe,parent:re,root:de,type:_e}=p,Ge=ut(d);if(Ht(p,!1),te&&yt(te),!Ge&&($=G&&G.onVnodeBeforeMount)&&ke($,re,d),Ht(p,!0),j&&ur){let $e=()=>{p.subTree=Cs(p),ur(j,p.subTree,p,O,null)};Ge&&_e.__asyncHydrate?_e.__asyncHydrate(j,p,$e):$e()}else{de.ce&&de.ce._hasShadowRoot()&&de.ce._injectChildStyle(_e,p.parent?p.parent.type:void 0);let $e=p.subTree=Cs(p);N(null,$e,y,S,p,O,T),d.el=$e.el}if(oe&&ge(oe,O),!Ge&&($=G&&G.onVnodeMounted)){let $e=d;ge(()=>ke($,re,$e),O)}(d.shapeFlag&256||re&&ut(re.vnode)&&re.vnode.shapeFlag&256)&&p.a&&ge(p.a,O),p.isMounted=!0,d=y=S=null}};p.scope.on();let A=p.effect=new ct(R);p.scope.off();let D=p.update=A.run.bind(A),W=p.job=A.runIfDirty.bind(A);W.i=p,W.id=p.uid,A.scheduler=()=>qr(W),Ht(p,!0),D()},Y=(p,d,y)=>{d.component=p;let S=p.vnode.props;p.vnode=d,p.next=null,Uu(p,d.props,S,y),Wu(p,d.children,y),Be(),mi(p),Ke()},fe=(p,d,y,S,O,T,k,R,A=!1)=>{let D=p&&p.children,W=p?p.shapeFlag:0,$=d.children,{patchFlag:j,shapeFlag:G}=d;if(j>0){if(j&128){Ve(D,$,y,S,O,T,k,R,A);return}else if(j&256){le(D,$,y,S,O,T,k,R,A);return}}G&8?(W&16&&vn(D,O,T),$!==D&&f(y,$)):W&16?G&16?Ve(D,$,y,S,O,T,k,R,A):vn(D,O,T,!0):(W&8&&f(y,""),G&16&&w($,y,S,O,T,k,R,A))},le=(p,d,y,S,O,T,k,R,A)=>{p=p||Vt,d=d||Vt;let D=p.length,W=d.length,$=Math.min(D,W),j;for(j=0;j<$;j++){let G=d[j]=A?at(d[j]):Me(d[j]);N(p[j],G,y,null,O,T,k,R,A)}D>W?vn(p,O,T,!0,!1,$):w(d,y,S,O,T,k,R,A,$)},Ve=(p,d,y,S,O,T,k,R,A)=>{let D=0,W=d.length,$=p.length-1,j=W-1;for(;D<=$&&D<=j;){let G=p[D],te=d[D]=A?at(d[D]):Me(d[D]);if(qe(G,te))N(G,te,y,null,O,T,k,R,A);else break;D++}for(;D<=$&&D<=j;){let G=p[$],te=d[j]=A?at(d[j]):Me(d[j]);if(qe(G,te))N(G,te,y,null,O,T,k,R,A);else break;$--,j--}if(D>$){if(D<=j){let G=j+1,te=G<W?d[G].el:S;for(;D<=j;)N(null,d[D]=A?at(d[D]):Me(d[D]),y,te,O,T,k,R,A),D++}}else if(D>j)for(;D<=$;)ot(p[D],O,T,!0),D++;else{let G=D,te=D,oe=new Map;for(D=te;D<=j;D++){let Fe=d[D]=A?at(d[D]):Me(d[D]);Fe.key!=null&&oe.set(Fe.key,D)}let re,de=0,_e=j-te+1,Ge=!1,$e=0,Nn=new Array(_e);for(D=0;D<_e;D++)Nn[D]=0;for(D=G;D<=$;D++){let Fe=p[D];if(de>=_e){ot(Fe,O,T,!0);continue}let Je;if(Fe.key!=null)Je=oe.get(Fe.key);else for(re=te;re<=j;re++)if(Nn[re-te]===0&&qe(Fe,d[re])){Je=re;break}Je===void 0?ot(Fe,O,T,!0):(Nn[Je-te]=D+1,Je>=$e?$e=Je:Ge=!0,N(Fe,d[Je],y,null,O,T,k,R,A),de++)}let Do=Ge?Gu(Nn):Vt;for(re=Do.length-1,D=_e-1;D>=0;D--){let Fe=te+D,Je=d[Fe],So=d[Fe+1],Co=Fe+1<W?So.el||ml(So):S;Nn[D]===0?N(null,Je,y,Co,O,T,k,R,A):Ge&&(re<0||D!==Do[re]?ye(Je,y,Co,2):re--)}}},ye=(p,d,y,S,O=null)=>{let{el:T,type:k,transition:R,children:A,shapeFlag:D}=p;if(D&6){ye(p.component.subTree,d,y,S);return}if(D&128){p.suspense.move(d,y,S);return}if(D&64){k.move(p,d,y,Xt);return}if(k===ve){s(T,d,y);for(let $=0;$<A.length;$++)ye(A[$],d,y,S);s(p.anchor,d,y);return}if(k===ft){m(p,d,y);return}if(S!==2&&D&1&&R)if(S===0)R.persisted&&!T[Ye]?s(T,d,y):(R.beforeEnter(T),s(T,d,y),ge(()=>R.enter(T),O));else{let{leave:$,delayLeave:j,afterLeave:G}=R,te=()=>{p.ctx.isUnmounted?r(T):s(T,d,y)},oe=()=>{let re=T._isLeaving||!!T[Ye];T._isLeaving&&T[Ye](!0),R.persisted&&!re?te():$(T,()=>{te(),G&&G()})};j?j(T,te,oe):oe()}else s(T,d,y)},ot=(p,d,y,S=!1,O=!1)=>{let{type:T,props:k,ref:R,children:A,dynamicChildren:D,shapeFlag:W,patchFlag:$,dirs:j,cacheIndex:G,memo:te}=p;if($===-2&&(O=!1),R!=null&&(Be(),pn(R,null,y,p,!0),Ke()),G!=null&&(d.renderCache[G]=void 0),W&256){d.ctx.deactivate(p);return}let oe=W&1&&j,re=!ut(p),de;if(re&&(de=k&&k.onVnodeBeforeUnmount)&&ke(de,d,p),W&6)Cc(p.component,y,S);else{if(W&128){p.suspense.unmount(y,S);return}oe&&tt(p,null,d,"beforeUnmount"),W&64?p.type.remove(p,d,y,Xt,S):D&&!D.hasOnce&&(T!==ve||$>0&&$&64)?vn(D,d,y,!1,!0):(T===ve&&$&384||!O&&W&16)&&vn(A,d,y),S&&wo(p)}let _e=te!=null&&G==null;(re&&(de=k&&k.onVnodeUnmounted)||oe||_e)&&ge(()=>{de&&ke(de,d,p),oe&&tt(p,null,d,"unmounted"),_e&&(p.el=null)},y)},wo=p=>{let{type:d,el:y,anchor:S,transition:O}=p;if(d===ve){Sc(y,S);return}if(d===ft){g(p);return}let T=()=>{r(y),O&&!O.persisted&&O.afterLeave&&O.afterLeave()};if(p.shapeFlag&1&&O&&!O.persisted){let{leave:k,delayLeave:R}=O,A=()=>k(y,T);R?R(p.el,T,A):A()}else T()},Sc=(p,d)=>{let y;for(;p!==d;)y=_(p),r(p),p=y;r(d)},Cc=(p,d,y)=>{let{bum:S,scope:O,job:T,subTree:k,um:R,m:A,a:D}=p;Is(A),Is(D),S&&yt(S),O.stop(),T&&(T.flags|=8,ot(k,p,d,y)),R&&ge(R,d),ge(()=>{p.isUnmounted=!0},d)},vn=(p,d,y,S=!1,O=!1,T=0)=>{for(let k=T;k<p.length;k++)ot(p[k],d,y,S,O)},ss=p=>{if(p.shapeFlag&6)return ss(p.component.subTree);if(p.shapeFlag&128)return p.suspense.next();let d=_(p.anchor||p.el),y=d&&d[Ui];return y?_(y):d},cr=!1,To=(p,d,y)=>{let S;p==null?d._vnode&&(ot(d._vnode,null,null,!0),S=d._vnode.component):N(d._vnode||null,p,d,null,null,null,y),d._vnode=p,cr||(cr=!0,mi(S),As(),cr=!1)},Xt={p:N,um:ot,m:ye,r:wo,mt:ne,mc:w,pc:fe,pbc:M,n:ss,o:e},ar,ur;return t&&([ar,ur]=t(Xt)),{render:To,hydrate:ar,createApp:Ru(To,ar)}}function Fr({type:e,props:t},n){return n==="svg"&&e==="foreignObject"||n==="mathml"&&e==="annotation-xml"&&t&&t.encoding&&t.encoding.includes("html")?void 0:n}function Ht({effect:e,job:t},n){n?(e.flags|=32,t.flags|=4):(e.flags&=-33,t.flags&=-5)}function gl(e,t){return(!e||e&&!e.pendingBranch)&&t&&!t.persisted}function co(e,t,n=!1){let s=e.children,r=t.children;if(F(s)&&F(r))for(let o=0;o<s.length;o++){let i=s[o],l=r[o];l.shapeFlag&1&&!l.dynamicChildren&&((l.patchFlag<=0||l.patchFlag===32)&&(l=r[o]=at(r[o]),l.el=i.el),!n&&l.patchFlag!==-2&&co(i,l)),l.type===Ot&&(l.patchFlag===-1&&(l=r[o]=at(l)),l.el=i.el),l.type===pe&&!l.el&&(l.el=i.el)}}function Gu(e){let t=e.slice(),n=[0],s,r,o,i,l,c=e.length;for(s=0;s<c;s++){let u=e[s];if(u!==0){if(r=n[n.length-1],e[r]<u){t[s]=r,n.push(s);continue}for(o=0,i=n.length-1;o<i;)l=o+i>>1,e[n[l]]<u?o=l+1:i=l;u<e[n[o]]&&(o>0&&(t[s]=n[o-1]),n[o]=s)}}for(o=n.length,i=n[o-1];o-- >0;)n[o]=i,i=t[i];return n}function _l(e){let t=e.subTree.component;if(t)return t.asyncDep&&!t.asyncResolved?t:_l(t)}function Is(e){if(e)for(let t=0;t<e.length;t++)e[t].flags|=8}function ml(e){if(e.placeholder)return e.placeholder;let t=e.component;return t?ml(t.subTree):null}var $s=e=>e.__isSuspense,Yr=0,zu={name:"Suspense",__isSuspense:!0,process(e,t,n,s,r,o,i,l,c,u){if(e==null)Ju(t,n,s,r,o,i,l,c,u);else{if(o&&o.deps>0&&!e.suspense.isInFallback){t.suspense=e.suspense,t.suspense.vnode=t,t.el=e.el;return}Xu(e,t,n,s,r,i,l,c,u)}},hydrate:Zu,normalize:Qu},qu=zu;function Bn(e,t){let n=e.props&&e.props[t];B(n)&&n()}function Ju(e,t,n,s,r,o,i,l,c){let{p:u,o:{createElement:f}}=c,a=f("div"),_=e.suspense=El(e,r,s,t,a,n,o,i,l,c);u(null,_.pendingBranch=e.ssContent,a,null,s,_,o,i),_.deps>0?(Bn(e,"onPending"),Bn(e,"onFallback"),u(null,e.ssFallback,t,n,s,null,o,i),dn(_,e.ssFallback)):_.resolve(!1,!0)}function Xu(e,t,n,s,r,o,i,l,{p:c,um:u,o:{createElement:f}}){let a=t.suspense=e.suspense;a.vnode=t,t.el=e.el;let _=t.ssContent,E=t.ssFallback,{activeBranch:v,pendingBranch:N,isInFallback:L,isHydrating:H}=a;if(N)a.pendingBranch=_,qe(N,_)?(c(N,_,a.hiddenContainer,null,r,a,o,i,l),a.deps<=0?a.resolve():L&&!H&&!a.isFallbackMountPending&&(c(v,E,n,s,r,null,o,i,l),dn(a,E))):(a.pendingId=Yr++,H?(a.isHydrating=!1,a.activeBranch=N):u(N,r,a),a.deps=0,a.effects.length=0,a.hiddenContainer=f("div"),L?(c(null,_,a.hiddenContainer,null,r,a,o,i,l),a.deps<=0?a.resolve():a.isFallbackMountPending||(c(v,E,n,s,r,null,o,i,l),dn(a,E))):v&&qe(v,_)?(c(v,_,n,s,r,a,o,i,l),a.resolve(!0)):(c(null,_,a.hiddenContainer,null,r,a,o,i,l),a.deps<=0&&a.resolve()));else if(v&&qe(v,_))c(v,_,n,s,r,a,o,i,l),dn(a,_);else if(Bn(t,"onPending"),a.pendingBranch=_,_.shapeFlag&512?a.pendingId=_.component.suspenseId:a.pendingId=Yr++,c(null,_,a.hiddenContainer,null,r,a,o,i,l),a.deps<=0)a.resolve();else{let{timeout:b,pendingId:h}=a;b>0?setTimeout(()=>{a.pendingId===h&&a.fallback(E)},b):b===0&&a.fallback(E)}}function El(e,t,n,s,r,o,i,l,c,u,f=!1){let{p:a,m:_,um:E,n:v,o:{parentNode:N,remove:L}}=u,H,b=ef(e);b&&t&&t.pendingBranch&&(H=t.pendingId,t.deps++);let h=e.props?nn(e.props.timeout):void 0,m=o,g={vnode:e,parent:t,parentComponent:n,namespace:i,container:s,hiddenContainer:r,deps:0,pendingId:Yr++,timeout:typeof h=="number"?h:-1,activeBranch:null,isFallbackMountPending:!1,pendingBranch:null,isInFallback:!f,isHydrating:f,isUnmounted:!1,effects:[],resolve(C=!1,x=!1){let{vnode:I,activeBranch:w,pendingBranch:P,pendingId:M,effects:V,parentComponent:K,container:q,isInFallback:ne}=g,U=!1;if(g.isHydrating)g.isHydrating=!1;else if(!C){U=w&&P.transition&&P.transition.mode==="out-in";let fe=!1;U&&(w.transition.afterLeave=()=>{M===g.pendingId&&(_(P,q,o===m&&!fe?v(w):o,0),hn(V),ne&&I.ssFallback&&(I.ssFallback.el=null))}),w&&!g.isFallbackMountPending&&(N(w.el)===q&&(o=v(w),fe=!0),E(w,K,g,!0),!U&&ne&&I.ssFallback&&ge(()=>I.ssFallback.el=null,g)),U||_(P,q,o,0)}g.isFallbackMountPending=!1,dn(g,P),g.pendingBranch=null,g.isInFallback=!1;let X=g.parent,Y=!1;for(;X;){if(X.pendingBranch){for(let fe=0;fe<V.length;fe++)X.effects.push(V[fe]);Y=!0;break}X=X.parent}!Y&&!U&&hn(V),g.effects=[],b&&t&&t.pendingBranch&&H===t.pendingId&&(t.deps--,t.deps===0&&!x&&t.resolve()),Bn(I,"onResolve")},fallback(C){if(!g.pendingBranch)return;let{vnode:x,activeBranch:I,parentComponent:w,container:P,namespace:M}=g;Bn(x,"onFallback");let V=v(I),K=()=>{if(g.isFallbackMountPending=!1,!g.isInFallback)return;let ne=g.vnode.ssFallback;a(null,ne,P,V,w,null,M,l,c),dn(g,ne)},q=C.transition&&C.transition.mode==="out-in";q&&(g.isFallbackMountPending=!0,I.transition.afterLeave=K),g.isInFallback=!0,E(I,w,null,!0),q||K()},move(C,x,I){g.activeBranch&&_(g.activeBranch,C,x,I),g.container=C},next(){return g.activeBranch&&v(g.activeBranch)},registerDep(C,x,I){let w=!!g.pendingBranch;w&&g.deps++;let P=C.vnode.el;C.asyncDep.catch(M=>{qt(M,C,0)}).then(M=>{if(C.isUnmounted||g.isUnmounted||g.pendingId!==C.suspenseId)return;Yn(),C.asyncResolved=!0;let{vnode:V}=C;Gr(C,M,!1),P&&(V.el=P);let K=!P&&C.subTree.el;x(C,V,N(P||C.subTree.el),P?null:v(C.subTree),g,i,I),K&&(V.placeholder=null,L(K)),Zs(C,V.el),w&&--g.deps===0&&g.resolve()})},unmount(C,x){g.isUnmounted=!0,g.activeBranch&&E(g.activeBranch,n,C,x),g.pendingBranch&&E(g.pendingBranch,n,C,x)}};return g}function Zu(e,t,n,s,r,o,i,l,c){let u=t.suspense=El(t,s,n,e.parentNode,document.createElement("div"),null,r,o,i,l,!0),f=c(e,u.pendingBranch=t.ssContent,n,u,o,i);return u.deps===0&&u.resolve(!1,!0),f}function Qu(e){let{shapeFlag:t,children:n}=e,s=t&32;e.ssContent=xi(s?n.default:n),e.ssFallback=s?xi(n.fallback):ce(pe)}function xi(e){let t;if(B(e)){let n=Yt&&e._c;n&&(e._d=!1,Kn()),e=e(),n&&(e._d=!0,t=Se,Qs())}return F(e)&&(e=Iu(e)),e=Me(e),t&&!e.dynamicChildren&&(e.dynamicChildren=t.filter(n=>n!==e)),e}function yl(e,t){t&&t.pendingBranch?F(e)?t.effects.push(...e):t.effects.push(e):hn(e)}function dn(e,t){e.activeBranch=t;let{vnode:n,parentComponent:s}=e,r=t.el;for(;!r&&t.component;)t=t.component.subTree,r=t.el;n.el=r,s&&s.subTree===n&&(s.vnode.el=r,Zs(s,r))}function ef(e){let t=e.props&&e.props.suspensible;return t!=null&&t!==!1}var ve=Symbol.for("v-fgt"),Ot=Symbol.for("v-txt"),pe=Symbol.for("v-cmt"),ft=Symbol.for("v-stc"),pt=[],Se=null;function Kn(e=!1){pt.push(Se=e?null:[])}function Qs(){pt.pop(),Se=pt[pt.length-1]||null}var Yt=1;function Wn(e,t=!1){Yt+=e,e<0&&Se&&t&&(Se.hasOnce=!0)}function vl(e){return e.dynamicChildren=Yt>0?Se||Vt:null,Qs(),Yt>0&&Se&&Se.push(e),e}function tf(e,t,n,s,r,o){return vl(ao(e,t,n,s,r,o,!0))}function Fs(e,t,n,s,r){return vl(ce(e,t,n,s,r,!0))}function dt(e){return e?e.__v_isVNode===!0:!1}function qe(e,t){return e.type===t.type&&e.key===t.key}var nf;function sf(e){nf=e}var Nl=({key:e})=>e??null,Vs=({ref:e,ref_key:t,ref_for:n})=>(typeof e=="number"&&(e=""+e),e!=null?se(e)||ue(e)||B(e)?{i:Oe,r:e,k:t,f:!!n}:e:null);function ao(e,t=null,n=null,s=0,r=null,o=e===ve?0:1,i=!1,l=!1){let c={__v_isVNode:!0,__v_skip:!0,type:e,props:t,key:t&&Nl(t),ref:t&&Vs(t),scopeId:Bs,slotScopeIds:null,children:n,component:null,suspense:null,ssContent:null,ssFallback:null,dirs:null,transition:null,el:null,anchor:null,target:null,targetStart:null,targetAnchor:null,staticCount:0,shapeFlag:o,patchFlag:s,dynamicProps:r,dynamicChildren:null,appContext:null,ctx:Oe};return l?(Ls(c,n),o&128&&e.normalize(c)):n&&(c.shapeFlag|=se(n)?8:16),Yt>0&&!i&&Se&&(c.patchFlag>0||o&6)&&c.patchFlag!==32&&Se.push(c),c}var ce=rf;function rf(e,t=null,n=null,s=0,r=null,o=!1){if((!e||e===Qi)&&(e=pe),dt(e)){let l=st(e,t,!0);return n&&Ls(l,n),Yt>0&&!o&&Se&&(l.shapeFlag&6?Se[Se.indexOf(e)]=l:Se.push(l)),l.patchFlag=-2,l}if(hf(e)&&(e=e.__vccOpts),t){t=bl(t);let{class:l,style:c}=t;l&&!se(l)&&(t.class=Pt(l)),Z(c)&&($t(c)&&!F(c)&&(c=Q({},c)),t.style=Rt(c))}let i=se(e)?1:$s(e)?128:Ks(e)?64:Z(e)?4:B(e)?2:0;return ao(e,t,n,s,r,i,o,!0)}function bl(e){return e?$t(e)||cl(e)?Q({},e):e:null}function st(e,t,n=!1,s=!1){let{props:r,ref:o,patchFlag:i,children:l,transition:c}=e,u=t?wl(r||{},t):r,f={__v_isVNode:!0,__v_skip:!0,type:e.type,props:u,key:u&&Nl(u),ref:t&&t.ref?n&&o?F(o)?o.concat(Vs(t)):[o,Vs(t)]:Vs(t):o,scopeId:e.scopeId,slotScopeIds:e.slotScopeIds,children:l,target:e.target,targetStart:e.targetStart,targetAnchor:e.targetAnchor,staticCount:e.staticCount,shapeFlag:e.shapeFlag,patchFlag:t&&e.type!==ve?i===-1?16:i|16:i,dynamicProps:e.dynamicProps,dynamicChildren:e.dynamicChildren,appContext:e.appContext,dirs:e.dirs,transition:c,component:e.component,suspense:e.suspense,ssContent:e.ssContent&&st(e.ssContent),ssFallback:e.ssFallback&&st(e.ssFallback),placeholder:e.placeholder,el:e.el,anchor:e.anchor,ctx:e.ctx,ce:e.ce};return c&&s&&nt(f,c.clone(f)),f}function uo(e=" ",t=0){return ce(Ot,null,e,t)}function of(e,t){let n=ce(ft,null,e);return n.staticCount=t,n}function Ol(e="",t=!1){return t?(Kn(),Fs(pe,null,e)):ce(pe,null,e)}function Me(e){return e==null||typeof e=="boolean"?ce(pe):F(e)?ce(ve,null,e.slice()):dt(e)?at(e):ce(Ot,null,String(e))}function at(e){return e.el===null&&e.patchFlag!==-1||e.memo?e:st(e)}function Ls(e,t){let n=0,{shapeFlag:s}=e;if(t==null)t=null;else if(F(t))n=16;else if(typeof t=="object")if(s&65){let r=t.default;r&&(r._c&&(r._d=!1),Ls(e,r()),r._c&&(r._d=!0));return}else{n=32;let r=t._;!r&&!cl(t)?t._ctx=Oe:r===3&&Oe&&(Oe.slots._===1?t._=1:(t._=2,e.patchFlag|=1024))}else if(B(t)){if(s&65){Ls(e,{default:t});return}t={default:t,_ctx:Oe},n=32}else t=String(t),s&64?(n=16,t=[uo(t)]):n=8;e.children=t,e.shapeFlag|=n}function wl(...e){let t={};for(let n=0;n<e.length;n++){let s=e[n];for(let r in s)if(r==="class")t.class!==s.class&&(t.class=Pt([t.class,s.class]));else if(r==="style")t.style=Rt([t.style,s.style]);else if(xt(r)){let o=t[r],i=s[r];i&&o!==i&&!(F(o)&&o.includes(i))?t[r]=o?[].concat(o,i):i:i==null&&o==null&&!Zt(r)&&(t[r]=i)}else r!==""&&(t[r]=s[r])}return t}function ke(e,t,n,s=null){Ie(e,t,7,[n,s])}var lf=nl(),cf=0;function Tl(e,t,n){let s=e.type,r=(t?t.appContext:e.appContext)||lf,o={uid:cf++,vnode:e,type:s,parent:t,appContext:r,root:null,next:null,subTree:null,effect:null,update:null,job:null,scope:new Mt(!0),render:null,proxy:null,exposed:null,exposeProxy:null,withProxy:null,provides:t?t.provides:Object.create(r.provides),ids:t?t.ids:["",0,0],accessCache:null,renderCache:[],components:null,directives:null,propsOptions:ul(s,r),emitsOptions:rl(s,r),emit:null,emitted:null,propsDefaults:J,inheritAttrs:s.inheritAttrs,ctx:J,data:J,props:J,attrs:J,slots:J,refs:J,setupState:J,setupContext:null,suspense:n,suspenseId:n?n.pendingId:0,asyncDep:null,asyncResolved:!1,isMounted:!1,isUnmounted:!1,isDeactivated:!1,bc:null,c:null,bm:null,m:null,bu:null,u:null,um:null,bum:null,da:null,a:null,rtg:null,rtc:null,ec:null,sp:null};return o.ctx={_:o},o.root=t?t.root:o,o.emit=ku.bind(null,o),e.ce&&e.ce(o),o}var be=null,Ce=()=>be||Oe,Hs,wt;{let e=wn(),t=(n,s)=>{let r;return(r=e[n])||(r=e[n]=[]),r.push(s),o=>{r.length>1?r.forEach(i=>i(o)):r[0](o)}};Hs=t("__VUE_INSTANCE_SETTERS__",n=>be=n),wt=t("__VUE_SSR_SETTERS__",n=>Gt=n)}var mn=e=>{let t=be;return Hs(e),e.scope.on(),()=>{e.scope.off(),Hs(t)}},Yn=()=>{be&&be.scope.off(),Hs(null)};function Dl(e){return e.vnode.shapeFlag&4}var Gt=!1;function Sl(e,t=!1,n=!1){t&&wt(t);let{props:s,children:r}=e.vnode,o=Dl(e);Hu(e,s,o,t),Ku(e,r,n||t);let i=o?af(e,t):void 0;return t&&wt(!1),i}function af(e,t){let n=e.type;e.accessCache=Object.create(null),e.proxy=new Proxy(e.ctx,jr);let{setup:s}=n;if(s){Be();let r=e.setupContext=s.length>1?xl(e):null,o=mn(e),i=zt(s,e,0,[e.props,r]),l=rs(i);if(Ke(),o(),(l||e.sp)&&!ut(e)&&Zr(e),l){if(i.then(Yn,Yn),t)return i.then(c=>{wt(!0);try{Gr(e,c,t)}finally{wt(!1)}}).catch(c=>{qt(c,e,0)});e.asyncDep=i}else Gr(e,i,t)}else Vl(e,t)}function Gr(e,t,n){B(t)?e.type.__ssrInlineRender?e.ssrRender=t:e.render=t:Z(t)&&(e.setupState=Pn(t)),Vl(e,n)}var Us,zr;function uf(e){Us=e,zr=t=>{t.render._rc&&(t.withProxy=new Proxy(t.ctx,pu))}}var Cl=()=>!Us;function Vl(e,t,n){let s=e.type;if(!e.render){if(!t&&Us&&!s.render){let r=s.template||so(e).template;if(r){let{isCustomElement:o,compilerOptions:i}=e.appContext.config,{delimiters:l,compilerOptions:c}=s,u=Q(Q({isCustomElement:o,delimiters:l},i),c);s.render=Us(r,u)}}e.render=s.render||Te,zr&&zr(e)}{let r=mn(e);Be();try{Du(e)}finally{Ke(),r()}}}var ff={get(e,t){return Ne(e,"get",""),e[t]}};function xl(e){let t=n=>{e.exposed=n||{}};return{attrs:new Proxy(e.attrs,ff),slots:e.slots,emit:e.emit,expose:t}}function Zn(e){return e.exposed?e.exposeProxy||(e.exposeProxy=new Proxy(Pn(ys(e.exposed)),{get(t,n){if(n in t)return t[n];if(n in Ln)return Ln[n](e)},has(t,n){return n in t||n in Ln}})):e.proxy}var pf=/(?:^|[-_])\w/g,df=e=>e.replace(pf,t=>t.toUpperCase()).replace(/[-_]/g,"");function js(e,t=!0){return B(e)?e.displayName||e.name:e.name||t&&e.__name}function Al(e,t,n=!1){let s=js(t);if(!s&&t.__file){let r=t.__file.match(/([^/\\]+)\.\w+$/);r&&(s=r[1])}if(!s&&e){let r=o=>{for(let i in o)if(o[i]===t)return i};s=r(e.components)||e.parent&&r(e.parent.type.components)||r(e.appContext.components)}return s?df(s):n?"App":"Anonymous"}function hf(e){return B(e)&&"__vccOpts"in e}var Rl=(e,t)=>fi(e,t,Gt);function fo(e,t,n){try{Wn(-1);let s=arguments.length;return s===2?Z(t)&&!F(t)?dt(t)?ce(e,null,[t]):ce(e,t):ce(e,null,t):(s>3?n=Array.prototype.slice.call(arguments,2):s===3&&dt(n)&&(n=[n]),ce(e,t,n))}finally{Wn(1)}}function gf(){return;function o(a){let _=[];a.type.props&&a.props&&_.push(i("props",z(a.props))),a.setupState!==J&&_.push(i("setup",a.setupState)),a.data!==J&&_.push(i("data",z(a.data)));let E=c(a,"computed");E&&_.push(i("computed",E));let v=c(a,"inject");return v&&_.push(i("injected",v)),_.push(["div",{},["span",{style:s.style+";opacity:0.66"},"$ (internal): "],["object",{object:a}]]),_}function i(a,_){return _=Q({},_),Object.keys(_).length?["div",{style:"line-height:1.25em;margin-bottom:0.6em"},["div",{style:"color:#476582"},a],["div",{style:"padding-left:1.25em"},...Object.keys(_).map(E=>["div",{},["span",s,E+": "],l(_[E],!1)])]]:["span",{}]}function l(a,_=!0){return typeof a=="number"?["span",t,a]:typeof a=="string"?["span",n,JSON.stringify(a)]:typeof a=="boolean"?["span",s,a]:Z(a)?["object",{object:_?z(a):a}]:["span",n,String(a)]}function c(a,_){let E=a.type;if(B(E))return;let v={};for(let N in a.ctx)u(E,N,_)&&(v[N]=a.ctx[N]);return v}function u(a,_,E){let v=a[E];if(F(v)&&v.includes(_)||Z(v)&&_ in v||a.extends&&u(a.extends,_,E)||a.mixins&&a.mixins.some(N=>u(N,_,E)))return!0}function f(a){return Ee(a)?"ShallowRef":a.effect?"ComputedRef":"Ref"}}function _f(e,t,n,s){let r=n[s];if(r&&Pl(r,e))return r;let o=t();return o.memo=e.slice(),o.cacheIndex=s,n[s]=o}function Pl(e,t){let n=e.memo;if(n.length!=t.length)return!1;for(let s=0;s<n.length;s++)if(he(n[s],t[s]))return!1;return Yt>0&&Se&&Se.push(e),!0}var kl="3.5.42",Ml=Te,mf=Ea,Ef=an,yf=Mi,vf={createComponentInstance:Tl,setupComponent:Sl,renderComponentRoot:Cs,setCurrentRenderingInstance:Un,isVNode:dt,normalizeVNode:Me,getComponentPublicInstance:Zn,ensureValidVNode:no,pushWarningContext:ua,popWarningContext:fa},Nf=vf,bf=null,Of=null,wf=null;/**
* @vue/runtime-dom v3.5.42
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/var mo,Il=typeof window<"u"&&window.trustedTypes;if(Il)try{mo=Il.createPolicy("vue",{createHTML:e=>e})}catch{}var nc=mo?e=>mo.createHTML(e):e=>e,Tf="http://www.w3.org/2000/svg",Df="http://www.w3.org/1998/Math/MathML",gt=typeof document<"u"?document:null,$l=gt&&gt.createElement("template"),sc={insert:(e,t,n)=>{t.insertBefore(e,n||null)},remove:e=>{let t=e.parentNode;t&&t.removeChild(e)},createElement:(e,t,n,s)=>{let r=t==="svg"?gt.createElementNS(Tf,e):t==="mathml"?gt.createElementNS(Df,e):n?gt.createElement(e,{is:n}):gt.createElement(e);return e==="select"&&s&&s.multiple!=null&&r.setAttribute("multiple",s.multiple),r},createText:e=>gt.createTextNode(e),createComment:e=>gt.createComment(e),setText:(e,t)=>{e.nodeValue=t},setElementText:(e,t)=>{e.textContent=t},parentNode:e=>e.parentNode,nextSibling:e=>e.nextSibling,querySelector:e=>gt.querySelector(e),setScopeId(e,t){e.setAttribute(t,"")},insertStaticContent(e,t,n,s,r,o){let i=n?n.previousSibling:t.lastChild;if(r&&(r===o||r.nextSibling))for(;t.insertBefore(r.cloneNode(!0),n),!(r===o||!(r=r.nextSibling)););else{$l.innerHTML=nc(s==="svg"?`<svg>${e}</svg>`:s==="mathml"?`<math>${e}</math>`:e);let l=$l.content;if(s==="svg"||s==="mathml"){let c=l.firstChild;for(;c.firstChild;)l.appendChild(c.firstChild);l.removeChild(c)}t.insertBefore(l,n)}return[i?i.nextSibling:t.firstChild,n?n.previousSibling:t.lastChild]}},Tt="transition",Qn="animation",En=Symbol("_vtc"),rc={name:String,type:String,css:{type:Boolean,default:!0},duration:[String,Number,Object],enterFromClass:String,enterActiveClass:String,enterToClass:String,appearFromClass:String,appearActiveClass:String,appearToClass:String,leaveFromClass:String,leaveActiveClass:String,leaveToClass:String},oc=Q({},Ys,rc),Sf=e=>(e.displayName="Transition",e.props=oc,e),Cf=Sf((e,{slots:t})=>fo(Xr,ic(e),t)),Jt=(e,t=[])=>{F(e)?e.forEach(n=>n(...t)):e&&e(...t)},Fl=e=>e?F(e)?e.some(t=>t.length>1):e.length>1:!1;function ic(e){let t={};for(let V in e)V in rc||(t[V]=e[V]);if(e.css===!1)return t;let{name:n="v",type:s,duration:r,enterFromClass:o=`${n}-enter-from`,enterActiveClass:i=`${n}-enter-active`,enterToClass:l=`${n}-enter-to`,appearFromClass:c=o,appearActiveClass:u=i,appearToClass:f=l,leaveFromClass:a=`${n}-leave-from`,leaveActiveClass:_=`${n}-leave-active`,leaveToClass:E=`${n}-leave-to`}=e,v=Vf(r),N=v&&v[0],L=v&&v[1],{onBeforeEnter:H,onEnter:b,onEnterCancelled:h,onLeave:m,onLeaveCancelled:g,onBeforeAppear:C=H,onAppear:x=b,onAppearCancelled:I=h}=t,w=(V,K,q,ne)=>{V._enterCancelled=ne,Dt(V,K?f:l),Dt(V,K?u:i),q&&q()},P=(V,K)=>{V._isLeaving=!1,Dt(V,a),Dt(V,E),Dt(V,_),K&&K()},M=V=>(K,q)=>{let ne=V?x:b,U=()=>w(K,V,q);Jt(ne,[K,U]),Ll(()=>{Dt(K,V?c:o),rt(K,V?f:l),Fl(ne)||Hl(K,s,N,U)})};return Q(t,{onBeforeEnter(V){Jt(H,[V]),rt(V,o),rt(V,i)},onBeforeAppear(V){Jt(C,[V]),rt(V,c),rt(V,u)},onEnter:M(!1),onAppear:M(!0),onLeave(V,K){V._isLeaving=!0;let q=()=>P(V,K);rt(V,a),V._enterCancelled?(rt(V,_),Eo(V)):(Eo(V),rt(V,_)),Ll(()=>{V._isLeaving&&(Dt(V,a),rt(V,E),Fl(m)||Hl(V,s,L,q))}),Jt(m,[V,q])},onEnterCancelled(V){w(V,!1,void 0,!0),Jt(h,[V])},onAppearCancelled(V){w(V,!0,void 0,!0),Jt(I,[V])},onLeaveCancelled(V){P(V),Jt(g,[V])}})}function Vf(e){if(e==null)return null;if(Z(e))return[po(e.enter),po(e.leave)];{let t=po(e);return[t,t]}}function po(e){return nn(e)}function rt(e,t){t.split(/\s+/).forEach(n=>n&&e.classList.add(n)),(e[En]||(e[En]=new Set)).add(t)}function Dt(e,t){t.split(/\s+/).forEach(s=>s&&e.classList.remove(s));let n=e[En];n&&(n.delete(t),n.size||(e[En]=void 0))}function Ll(e){requestAnimationFrame(()=>{requestAnimationFrame(e)})}var xf=0;function Hl(e,t,n,s){let r=e._endId=++xf,o=()=>{r===e._endId&&s()};if(n!=null)return setTimeout(o,n);let{type:i,timeout:l,propCount:c}=lc(e,t);if(!i)return s();let u=i+"end",f=0,a=()=>{e.removeEventListener(u,_),o()},_=E=>{E.target===e&&++f>=c&&a()};setTimeout(()=>{f<c&&a()},l+1),e.addEventListener(u,_)}function lc(e,t){let n=window.getComputedStyle(e),s=v=>(n[v]||"").split(", "),r=s(`${Tt}Delay`),o=s(`${Tt}Duration`),i=Ul(r,o),l=s(`${Qn}Delay`),c=s(`${Qn}Duration`),u=Ul(l,c),f=null,a=0,_=0;t===Tt?i>0&&(f=Tt,a=i,_=o.length):t===Qn?u>0&&(f=Qn,a=u,_=c.length):(a=Math.max(i,u),f=a>0?i>u?Tt:Qn:null,_=f?f===Tt?o.length:c.length:0);let E=f===Tt&&/\b(?:transform|all)(?:,|$)/.test(s(`${Tt}Property`).toString());return{type:f,timeout:a,propCount:_,hasTransform:E}}function Ul(e,t){for(;e.length<t.length;)e=e.concat(e);return Math.max(...t.map((n,s)=>jl(n)+jl(e[s])))}function jl(e){return e==="auto"?0:Number(e.slice(0,-1).replace(",","."))*1e3}function Eo(e){return(e?e.ownerDocument:document).body.offsetHeight}function Af(e,t,n){let s=e[En];s&&(t=(t?[t,...s]:[...s]).join(" ")),t==null?e.removeAttribute("class"):n?e.setAttribute("class",t):e.className=t}var sr=Symbol("_vod"),No=Symbol("_vsh"),cc={name:"show",beforeMount(e,{value:t},{transition:n}){e[sr]=e.style.display==="none"?"":e.style.display,n&&t?n.beforeEnter(e):es(e,t)},mounted(e,{value:t},{transition:n}){n&&t&&n.enter(e)},updated(e,{value:t,oldValue:n},{transition:s}){!t!=!n&&(s?t?(s.beforeEnter(e),es(e,!0),s.enter(e)):s.leave(e,()=>{es(e,!1)}):es(e,t))},beforeUnmount(e,{value:t}){es(e,t)}};function es(e,t){e.style.display=t?e[sr]:"none",e[No]=!t}function Rf(){cc.getSSRProps=({value:e})=>{if(!e)return{style:{display:"none"}}}}var ac=Symbol("");function Pf(e){let t=Ce();if(!t)return;let n=t.ut=(r=e(t.proxy))=>{Array.from(document.querySelectorAll(`[data-v-owner="${t.uid}"]`)).forEach(o=>rr(o,r))},s=()=>{let r=e(t.proxy);t.ce?rr(t.ce,r):yo(t.subTree,r),n(r)};qs(()=>{hn(s)}),gn(()=>{Bt(s,Te,{flush:"post"});let r=new MutationObserver(s);r.observe(t.subTree.el.parentNode,{childList:!0}),_n(()=>r.disconnect())})}function yo(e,t){if(e.shapeFlag&128){let n=e.suspense;e=n.activeBranch,n.pendingBranch&&!n.isHydrating&&n.effects.push(()=>{yo(n.activeBranch,t)})}for(;e.component;)e=e.component.subTree;if(e.shapeFlag&1&&e.el)rr(e.el,t);else if(e.type===ve)e.children.forEach(n=>yo(n,t));else if(e.type===ft){let{el:n,anchor:s}=e;for(;n&&(rr(n,t),n!==s);)n=n.nextSibling}}function rr(e,t){if(e.nodeType===1){let n=e.style,s="";for(let r in t){let o=_r(t[r]);n.setProperty(`--${r}`,o),s+=`--${r}: ${o};`}n[ac]=s}}var kf=/(?:^|;)\s*display\s*:/;function Mf(e,t,n){let s=e.style,r=se(n),o=!1;if(n&&!r){if(t)if(se(t))for(let i of t.split(";")){let l=i.slice(0,i.indexOf(":")).trim();n[l]==null&&ts(s,l,"")}else for(let i in t)n[i]==null&&ts(s,i,"");for(let i in n){i==="display"&&(o=!0);let l=n[i];l!=null?$f(e,i,!se(t)&&t?t[i]:void 0,l)||ts(s,i,l):ts(s,i,"")}}else if(r){if(t!==n){let i=s[ac];i&&(n+=";"+i),s.cssText=n,o=kf.test(n)}}else t&&e.removeAttribute("style");sr in e&&(e[sr]=o?s.display:"",e[No]&&(s.display="none"))}var er=/\s*!important$/;function ts(e,t,n){if(F(n))n.forEach(s=>ts(e,t,s));else if(n==null&&(n=""),t.startsWith("--"))er.test(n)?e.setProperty(t,n.replace(er,""),"important"):e.setProperty(t,n);else{let s=If(e,t);er.test(n)?e.setProperty(De(s),n.replace(er,""),"important"):e[s]=n}}var Bl=["Webkit","Moz","ms"],ho={};function If(e,t){let n=ho[t];if(n)return n;let s=ae(t);if(s!=="filter"&&s in e)return ho[t]=s;s=Et(s);for(let r=0;r<Bl.length;r++){let o=Bl[r]+s;if(o in e)return ho[t]=o}return t}function $f(e,t,n,s){return e.tagName==="TEXTAREA"&&(t==="width"||t==="height")&&se(s)&&n===s}var Kl="http://www.w3.org/1999/xlink";function Wl(e,t,n,s,r,o=$o(t)){s&&t.startsWith("xlink:")?n==null?e.removeAttributeNS(Kl,t.slice(6,t.length)):e.setAttributeNS(Kl,t,n):n==null||o&&!ls(n)?e.removeAttribute(t):e.setAttribute(t,o?"":we(n)?String(n):n)}function Yl(e,t,n,s,r){if(t==="innerHTML"||t==="textContent"){n!=null&&(e[t]=t==="innerHTML"?nc(n):n);return}let o=e.tagName;if(t==="value"&&o!=="PROGRESS"&&!o.includes("-")){let l=o==="OPTION"?e.getAttribute("value")||"":e.value,c=n==null?e.type==="checkbox"?"on":"":String(n);(l!==c||!("_value"in e))&&(e.value=c),n==null&&e.removeAttribute(t),e._value=n;return}let i=!1;if(n===""||n==null){let l=typeof e[t];l==="boolean"?n=ls(n):n==null&&l==="string"?(n="",i=!0):l==="number"&&(n=0,i=!0)}try{e[t]=n}catch{}i&&e.removeAttribute(r||t)}function _t(e,t,n,s){e.addEventListener(t,n,s)}function Ff(e,t,n,s){e.removeEventListener(t,n,s)}var Gl=Symbol("_vei");function Lf(e,t,n,s,r=null){let o=e[Gl]||(e[Gl]={}),i=o[t];if(s&&i)i.value=s;else{let[l,c]=jf(t);if(s){let u=o[t]=Wf(s,r);_t(e,l,u,c)}else i&&(Ff(e,l,i,c),o[t]=void 0)}}var Hf=/(Once|Passive|Capture)$/,Uf=/^on:?(?:Once|Passive|Capture)$/;function jf(e){let t,n;for(;(n=e.match(Hf))&&!Uf.test(e);)t||(t={}),e=e.slice(0,e.length-n[1].length),t[n[1].toLowerCase()]=!0;return[e[2]===":"?e.slice(3):De(e.slice(2)),t]}var go=0,Bf=Promise.resolve(),Kf=()=>go||(Bf.then(()=>go=0),go=Date.now());function Wf(e,t){let n=s=>{if(!s._vts)s._vts=Date.now();else if(s._vts<=n.attached)return;let r=n.value;if(F(r)){let o=s.stopImmediatePropagation;s.stopImmediatePropagation=()=>{o.call(s),s._stopped=!0};let i=r.slice(),l=[s];for(let c=0;c<i.length&&!s._stopped;c++){let u=i[c];u&&Ie(u,t,5,l)}}else Ie(r,t,5,[s])};return n.value=e,n.attached=Kf(),n}var zl=e=>e.charCodeAt(0)===111&&e.charCodeAt(1)===110&&e.charCodeAt(2)>96&&e.charCodeAt(2)<123,uc=(e,t,n,s,r,o)=>{let i=r==="svg";t==="class"?Af(e,s,i):t==="style"?Mf(e,n,s):xt(t)?Zt(t)||Lf(e,t,n,s,o):(t[0]==="."?(t=t.slice(1),!0):t[0]==="^"?(t=t.slice(1),!1):Yf(e,t,s,i))?(Yl(e,t,s),!e.tagName.includes("-")&&(t==="value"||t==="checked"||t==="selected")&&Wl(e,t,s,i,o,t!=="value")):e._isVueCE&&(Gf(e,t)||e._def.__asyncLoader&&(/[A-Z]/.test(t)||!se(s)))?Yl(e,ae(t),s,o,t):(t==="true-value"?e._trueValue=s:t==="false-value"&&(e._falseValue=s),Wl(e,t,s,i))};function Yf(e,t,n,s){if(s)return!!(t==="innerHTML"||t==="textContent"||t in e&&zl(t)&&B(n));if(t==="spellcheck"||t==="draggable"||t==="translate"||t==="autocorrect"||t==="sandbox"&&e.tagName==="IFRAME"||t==="form"||t==="list"&&e.tagName==="INPUT"||t==="type"&&e.tagName==="TEXTAREA")return!1;if(t==="width"||t==="height"){let r=e.tagName;if(r==="IMG"||r==="VIDEO"||r==="CANVAS"||r==="SOURCE")return!1}return zl(t)&&se(n)?!1:t in e}function Gf(e,t){let n=e._def.props;if(!n)return!1;let s=ae(t);return Array.isArray(n)?n.some(r=>ae(r)===s):Object.keys(n).some(r=>ae(r)===s)}var ql={};function fc(e,t,n){let s=Gs(e,t);en(s)&&(s=Q({},s,t));class r extends or{constructor(i){super(s,i,n)}}return r.def=s,r}var zf=((e,t)=>fc(e,t,wc)),qf=typeof HTMLElement<"u"?HTMLElement:class{},or=class e extends qf{constructor(t,n={},s=vo){super(),this._def=t,this._props=n,this._createApp=s,this._isVueCE=!0,this._instance=null,this._app=null,this._nonce=this._def.nonce,this._connected=!1,this._resolved=!1,this._patching=!1,this._dirty=!1,this._numberProps=null,this._styleChildren=new WeakSet,this._styleAnchors=new WeakMap,this._ob=null,this.shadowRoot&&s!==vo?this._root=this.shadowRoot:t.shadowRoot!==!1?(this.attachShadow(Q({},t.shadowRootOptions,{mode:"open"})),this._root=this.shadowRoot):this._root=this}connectedCallback(){if(!this.isConnected)return;!this.shadowRoot&&!this._resolved&&this._parseSlots(),this._connected=!0;let t=this;for(;t=t&&(t.assignedSlot||t.parentNode||t.host);)if(t instanceof e){this._parent=t;break}this._instance||(this._resolved?this._mount(this._def):t&&t._pendingResolve?this._pendingResolve=t._pendingResolve.then(()=>{if(this._pendingResolve=void 0,this.isConnected)return this._resolveDef()}):this._resolveDef())}_setParent(t=this._parent){t&&(this._instance.parent=t._instance,this._inheritParentContext(t))}_inheritParentContext(t=this._parent){t&&this._app&&Object.setPrototypeOf(this._app._context.provides,t._instance.provides)}disconnectedCallback(){this._connected=!1,Gn(()=>{this._connected||(this._ob&&(this._ob.disconnect(),this._ob=null),this._app&&this._app.unmount(),this._instance&&(this._instance.ce=void 0),this._app=this._instance=null,this._teleportTargets&&(this._teleportTargets.clear(),this._teleportTargets=void 0))})}_processMutations(t){for(let n of t)this._setAttr(n.attributeName)}_resolveDef(){if(this._pendingResolve)return this._pendingResolve;for(let s=0;s<this.attributes.length;s++)this._setAttr(this.attributes[s].name);this._ob=new MutationObserver(this._processMutations.bind(this)),this._ob.observe(this,{attributes:!0});let t=(s,r=!1)=>{this._resolved=!0,this._pendingResolve=void 0;let{props:o,styles:i}=s,l;if(o&&!F(o))for(let c in o){let u=o[c];(u===Number||u&&u.type===Number)&&(c in this._props&&(this._props[c]=nn(this._props[c])),(l||(l=Object.create(null)))[ae(c)]=!0)}this._numberProps=l,this._resolveProps(s),this.shadowRoot&&this._applyStyles(i),this._mount(s)},n=this._def.__asyncLoader;if(n)return this._pendingResolve=n().then(s=>{s.configureApp=this._def.configureApp,t(this._def=s,!0)}),this._pendingResolve;t(this._def)}_mount(t){this._app=this._createApp(t),this._inheritParentContext(),t.configureApp&&t.configureApp(this._app),this._app._ceVNode=this._createVNode(),this._app.mount(this._root);let n=this._instance&&this._instance.exposed;if(n)for(let s in n)ee(this,s)||Object.defineProperty(this,s,{get:()=>Lt(n[s])})}_resolveProps(t){let{props:n}=t,s=F(n)?n:Object.keys(n||{});for(let r of Object.keys(this))r[0]!=="_"&&s.includes(r)&&this._setProp(r,this[r]);for(let r of s.map(ae))Object.defineProperty(this,r,{get(){return this._getProp(r)},set(o){this._setProp(r,o,!0,!this._patching)}})}_setAttr(t){if(t.startsWith("data-v-"))return;let n=this.hasAttribute(t),s=n?this.getAttribute(t):ql,r=ae(t);n&&this._numberProps&&this._numberProps[r]&&(s=nn(s)),this._setProp(r,s,!1,!0)}_getProp(t){return this._props[t]}_setProp(t,n,s=!0,r=!1){if(n!==this._props[t]&&(this._dirty=!0,n===ql?delete this._props[t]:(this._props[t]=n,t==="key"&&this._app&&(this._app._ceVNode.key=n)),r&&this._instance&&this._update(),s)){let o=this._ob;o&&(this._processMutations(o.takeRecords()),o.disconnect()),n===!0?this.setAttribute(De(t),""):typeof n=="string"||typeof n=="number"?this.setAttribute(De(t),n+""):n||this.removeAttribute(De(t)),o&&o.observe(this,{attributes:!0})}}_update(){let t=this._createVNode();this._app&&(t.appContext=this._app._context),Oc(t,this._root)}_createVNode(){let t={};this.shadowRoot||(t.onVnodeMounted=t.onVnodeUpdated=this._renderSlots.bind(this));let n=ce(this._def,Q(t,this._props));return this._instance||(n.ce=s=>{this._instance=s,s.ce=this,s.isCE=!0;let r=(o,i)=>{this.dispatchEvent(new CustomEvent(o,en(i[0])?Q({detail:i},i[0]):{detail:i}))};s.emit=(o,...i)=>{r(o,i),De(o)!==o&&r(De(o),i)},this._setParent()}),n}_applyStyles(t,n,s){if(!t)return;if(n){if(n===this._def||this._styleChildren.has(n))return;this._styleChildren.add(n)}let r=this._nonce,o=this.shadowRoot,i=s?this._getStyleAnchor(s)||this._getStyleAnchor(this._def):this._getRootStyleInsertionAnchor(o),l=null;for(let c=t.length-1;c>=0;c--){let u=document.createElement("style");r&&u.setAttribute("nonce",r),u.textContent=t[c],o.insertBefore(u,l||i),l=u,c===0&&(s||this._styleAnchors.set(this._def,u),n&&this._styleAnchors.set(n,u))}}_getStyleAnchor(t){if(!t)return null;let n=this._styleAnchors.get(t);return n&&n.parentNode===this.shadowRoot?n:(n&&this._styleAnchors.delete(t),null)}_getRootStyleInsertionAnchor(t){for(let n=0;n<t.childNodes.length;n++){let s=t.childNodes[n];if(!(s instanceof HTMLStyleElement))return s}return null}_parseSlots(){let t=this._slots={},n;for(;n=this.firstChild;){let s=n.nodeType===1&&n.getAttribute("slot")||"default";(t[s]||(t[s]=[])).push(n),this.removeChild(n)}}_renderSlots(){let t=this._getSlots(),n=this._instance.type.__scopeId;for(let s=0;s<t.length;s++){let r=t[s],o=r.getAttribute("name")||"default",i=this._slots[o],l=r.parentNode;if(i)for(let c of i){if(n&&c.nodeType===1){let u=n+"-s",f=document.createTreeWalker(c,1);c.setAttribute(u,"");let a;for(;a=f.nextNode();)a.setAttribute(u,"")}l.insertBefore(c,r)}else for(;r.firstChild;)l.insertBefore(r.firstChild,r);l.removeChild(r)}}_getSlots(){let t=[this];this._teleportTargets&&t.push(...this._teleportTargets);let n=new Set;for(let s of t){let r=s.querySelectorAll("slot");for(let o=0;o<r.length;o++)n.add(r[o])}return Array.from(n)}_injectChildStyle(t,n){this._applyStyles(t.styles,t,n)}_beginPatch(){this._patching=!0,this._dirty=!1}_endPatch(){this._patching=!1,this._dirty&&this._instance&&this._update()}_hasShadowRoot(){return this._def.shadowRoot!==!1}_removeChildStyle(t){}};function pc(e){let t=Ce(),n=t&&t.ce;return n||null}function Jf(){let e=pc();return e&&e.shadowRoot}function Xf(e="$style"){{let t=Ce();if(!t)return J;let n=t.type.__cssModules;if(!n)return J;let s=n[e];return s||J}}var dc=new WeakMap,hc=new WeakMap,ir=Symbol("_moveCb"),Jl=Symbol("_enterCb"),Zf=e=>(delete e.props.mode,e),Qf=Zf({name:"TransitionGroup",props:Q({},oc,{tag:String,moveClass:String}),setup(e,{slots:t}){let n=Ce(),s=Ws(),r,o;return Xn(()=>{if(!r.length)return;let i=e.moveClass||`${e.name||"v"}-move`;if(!rp(r[0].el,n.vnode.el,i)){r=[];return}r.forEach(tp),r.forEach(np);let l=r.filter(sp);Eo(n.vnode.el),l.forEach(c=>{let u=c.el,f=u.style;rt(u,i),f.transform=f.webkitTransform=f.transitionDuration="";let a=u[ir]=_=>{_&&_.target!==u||(!_||_.propertyName.endsWith("transform"))&&(u.removeEventListener("transitionend",a),u[ir]=null,Dt(u,i))};u.addEventListener("transitionend",a)}),r=[]}),()=>{let i=z(e),l=ic(i),c=i.tag||ve;if(r=[],o)for(let u=0;u<o.length;u++){let f=o[u];f.el&&f.el instanceof Element&&!f.el[No]&&(r.push(f),nt(f,Wt(f,l,s,n)),dc.set(f,gc(f.el)))}o=t.default?qn(t.default()):[];for(let u=0;u<o.length;u++){let f=o[u];f.key!=null&&nt(f,Wt(f,l,s,n))}return ce(c,null,o)}}}),ep=Qf;function tp(e){let t=e.el;t[ir]&&t[ir](),t[Jl]&&t[Jl]()}function np(e){hc.set(e,gc(e.el))}function sp(e){let t=dc.get(e),n=hc.get(e),s=t.left-n.left,r=t.top-n.top;if(s||r){let o=e.el,i=o.style,l=o.getBoundingClientRect(),c=1,u=1;return o.offsetWidth&&(c=l.width/o.offsetWidth),o.offsetHeight&&(u=l.height/o.offsetHeight),(!Number.isFinite(c)||c===0)&&(c=1),(!Number.isFinite(u)||u===0)&&(u=1),Math.abs(c-1)<.01&&(c=1),Math.abs(u-1)<.01&&(u=1),i.transform=i.webkitTransform=`translate(${s/c}px,${r/u}px)`,i.transitionDuration="0s",e}}function gc(e){let t=e.getBoundingClientRect();return{left:t.left,top:t.top}}function rp(e,t,n){let s=e.cloneNode(),r=e[En];r&&r.forEach(l=>{l.split(/\s+/).forEach(c=>c&&s.classList.remove(c))}),n.split(/\s+/).forEach(l=>l&&s.classList.add(l)),s.style.display="none";let o=t.nodeType===1?t:t.parentNode;o.appendChild(s);let{hasTransform:i}=lc(s);return o.removeChild(s),i}var St=e=>{let t=e.props["onUpdate:modelValue"]||!1;return F(t)?n=>yt(t,n):t};function op(e){e.target.composing=!0}function Xl(e){let t=e.target;t.composing&&(t.composing=!1,t.dispatchEvent(new Event("input")))}var Le=Symbol("_assign"),tr=Symbol("_initialValue");function _o(e,t,n){return t&&(e=e.trim()),n&&(e=tn(e)),e}var lr={created(e,{modifiers:{lazy:t,trim:n,number:s}},r){e.parentNode&&(e.type==="text"?e[tr]=e.defaultValue.replace(/[\r\n]/g,""):e.type==="textarea"&&(e[tr]=e.defaultValue.replace(/\r\n?/g,`
`))),e[Le]=St(r);let o=s||r.props&&r.props.type==="number";_t(e,t?"change":"input",i=>{i.target.composing||e[Le](_o(e.value,n,o))}),(n||o)&&_t(e,"change",()=>{e.value=_o(e.value,n,o)}),t||(_t(e,"compositionstart",op),_t(e,"compositionend",Xl),_t(e,"change",Xl))},mounted(e,{value:t,modifiers:{trim:n,number:s}}){let r=t??"",o=e[tr];delete e[tr],o!==void 0&&(e.type==="text"||e.type==="textarea")&&e.value!==o?e[Le](_o(e.value,n,s)):e.value=r},beforeUpdate(e,{value:t,oldValue:n,modifiers:{lazy:s,trim:r,number:o}},i){if(e[Le]=St(i),e.composing)return;let l=(o||e.type==="number")&&!/^0\d/.test(e.value)?tn(e.value):e.value,c=t??"";if(l===c)return;let u=e.getRootNode();(u instanceof Document||u instanceof ShadowRoot)&&u.activeElement===e&&e.type!=="range"&&(s&&t===n||r&&e.value.trim()===c)||(e.value=c)}},bo={deep:!0,created(e,t,n){e[Le]=St(n),_t(e,"change",()=>{let s=e._modelValue,r=yn(e),o=e.checked,i=e[Le];if(F(s)){let l=Tn(s,r),c=l!==-1;if(o&&!c)i(s.concat(r));else if(!o&&c){let u=[...s];u.splice(l,1),i(u)}}else if(He(s)){let l=new Set(s);o?l.add(r):l.delete(r),i(l)}else i(mc(e,o))})},mounted:Zl,beforeUpdate(e,t,n){e[Le]=St(n),Zl(e,t,n)}};function Zl(e,{value:t,oldValue:n},s){e._modelValue=t;let r;if(F(t))r=Tn(t,s.props.value)>-1;else if(He(t))r=t.has(s.props.value);else{if(t===n)return;r=Re(t,mc(e,!0))}e.checked!==r&&(e.checked=r)}var Oo={created(e,{value:t},n){e.checked=Re(t,n.props.value),e[Le]=St(n),_t(e,"change",()=>{e[Le](yn(e))})},beforeUpdate(e,{value:t,oldValue:n},s){e[Le]=St(s),t!==n&&(e.checked=Re(t,s.props.value))}},_c={deep:!0,created(e,{value:t,modifiers:{number:n}},s){e._modelValue=t,_t(e,"change",()=>{let r=Array.prototype.filter.call(e.options,c=>c.selected).map(c=>n?tn(yn(c)):yn(c)),o=e.multiple,i=o?He(e._modelValue)?new Set(r):r:r[0],l=e._pendingValue=[o,o?F(i)?r.slice():r:i];try{e[Le](i)}finally{Gn(()=>{e._pendingValue===l&&(e._pendingValue=void 0)})}}),e[Le]=St(s)},mounted(e,{value:t}){Ql(e,t)},beforeUpdate(e,{value:t},n){e._modelValue=t,e[Le]=St(n)},updated(e,{value:t}){let n=e._pendingValue;e._pendingValue=void 0,(!n||n[0]!==e.multiple||!ip(t,n[1],n[0]))&&Ql(e,t)}};function ip(e,t,n){if(!n)return Re(e,t);if(F(e))return Re(e,t);if(He(e)){if(e.size!==t.length)return!1;for(let s of t)if(!e.has(s))return!1;return!0}return!1}function Ql(e,t){let n=e.multiple,s=F(t);if(!(n&&!s&&!He(t))){for(let r=0,o=e.options.length;r<o;r++){let i=e.options[r],l=yn(i);if(n)if(s){let c=typeof l;c==="string"||c==="number"?i.selected=t.some(u=>String(u)===String(l)):i.selected=Tn(t,l)>-1}else i.selected=t.has(l);else if(Re(yn(i),t)){e.selectedIndex!==r&&(e.selectedIndex=r);return}}!n&&e.selectedIndex!==-1&&(e.selectedIndex=-1)}}function yn(e){return"_value"in e?e._value:e.value}function mc(e,t){let n=t?"_trueValue":"_falseValue";return n in e?e[n]:t}var Ec={created(e,t,n){nr(e,t,n,null,"created")},mounted(e,t,n){nr(e,t,n,null,"mounted")},beforeUpdate(e,t,n,s){nr(e,t,n,s,"beforeUpdate")},updated(e,t,n,s){nr(e,t,n,s,"updated")}};function yc(e,t){switch(e){case"SELECT":return _c;case"TEXTAREA":return lr;default:switch(t){case"checkbox":return bo;case"radio":return Oo;default:return lr}}}function nr(e,t,n,s,r){let i=yc(e.tagName,n.props&&n.props.type)[r];i&&i(e,t,n,s)}function lp(){lr.getSSRProps=({value:e})=>({value:e}),Oo.getSSRProps=({value:e},t)=>{if(t.props&&Re(t.props.value,e))return{checked:!0}},bo.getSSRProps=({value:e},t)=>{if(F(e)){if(t.props&&Tn(e,t.props.value)>-1)return{checked:!0}}else if(He(e)){if(t.props&&e.has(t.props.value))return{checked:!0}}else if(e)return{checked:!0}},Ec.getSSRProps=(e,t)=>{if(typeof t.type!="string")return;let n=yc(t.type.toUpperCase(),t.props&&t.props.type);if(n.getSSRProps)return n.getSSRProps(e,t)}}var cp=["ctrl","shift","alt","meta"],ap={stop:e=>e.stopPropagation(),prevent:e=>e.preventDefault(),self:e=>e.target!==e.currentTarget,ctrl:e=>!e.ctrlKey,shift:e=>!e.shiftKey,alt:e=>!e.altKey,meta:e=>!e.metaKey,left:e=>"button"in e&&e.button!==0,middle:e=>"button"in e&&e.button!==1,right:e=>"button"in e&&e.button!==2,exact:(e,t)=>cp.some(n=>e[`${n}Key`]&&!t.includes(n))},up=(e,t)=>{if(!e)return e;let n=e._withMods||(e._withMods={}),s=t.join(".");return n[s]||(n[s]=((r,...o)=>{for(let i=0;i<t.length;i++){let l=ap[t[i]];if(l&&l(r,t))return}return e(r,...o)}))},fp={esc:"escape",space:" ",up:"arrow-up",left:"arrow-left",right:"arrow-right",down:"arrow-down",delete:"backspace"},pp=(e,t)=>{let n=e._withKeys||(e._withKeys={}),s=t.join(".");return n[s]||(n[s]=(r=>{if(!("key"in r))return;let o=De(r.key);if(t.some(i=>i===o||fp[i]===o))return e(r)}))},vc=Q({patchProp:uc},sc),ns,ec=!1;function Nc(){return ns||(ns=io(vc))}function bc(){return ns=ec?ns:lo(vc),ec=!0,ns}var Oc=((...e)=>{Nc().render(...e)}),dp=((...e)=>{bc().hydrate(...e)}),vo=((...e)=>{let t=Nc().createApp(...e),{mount:n}=t;return t.mount=s=>{let r=Dc(s);if(!r)return;let o=t._component;!B(o)&&!o.render&&!o.template&&(o.template=r.innerHTML),r.nodeType===1&&(r.textContent="");let i=n(r,!1,Tc(r));return r instanceof Element&&(r.removeAttribute("v-cloak"),r.setAttribute("data-v-app","")),i},t}),wc=((...e)=>{let t=bc().createApp(...e),{mount:n}=t;return t.mount=s=>{let r=Dc(s);if(r)return n(r,!0,Tc(r))},t});function Tc(e){if(e instanceof SVGElement)return"svg";if(typeof MathMLElement=="function"&&e instanceof MathMLElement)return"mathml"}function Dc(e){return se(e)?document.querySelector(e):e}var tc=!1,hp=()=>{tc||(tc=!0,lp(),Rf())};/**
* vue v3.5.42
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/var gp=()=>{};return kc(_p);})();

global.Vue = Vue;
/* Citry Vue fragment manager. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-fragments.ts (pnpm run build there). */
var CitryVueFragments=(()=>{var __defProp=Object.defineProperty;var __getOwnPropDesc=Object.getOwnPropertyDescriptor;var __getOwnPropNames=Object.getOwnPropertyNames;var __hasOwnProp=Object.prototype.hasOwnProperty;var __export=(target,all)=>{for(var name in all)__defProp(target,name,{get:all[name],enumerable:true})};var __copyProps=(to,from,except,desc)=>{if(from&&typeof from==="object"||typeof from==="function"){for(let key of __getOwnPropNames(from))if(!__hasOwnProp.call(to,key)&&key!==except)__defProp(to,key,{get:()=>from[key],enumerable:!(desc=__getOwnPropDesc(from,key))||desc.enumerable})}return to};var __toCommonJS=mod=>__copyProps(__defProp({},"__esModule",{value:true}),mod);var citry_fragments_exports={};__export(citry_fragments_exports,{installFragmentManager:()=>installFragmentManager});function installFragmentManager(publicApi,isManagedDescendant,startPrepared,documentNonce=""){const processed=new WeakMap;const reservedHosts=new Set;const pendingHosts=new Map;const trackedHosts=new Map;let pendingAttributeObserver=null;let pendingGuardQueued=false;const queuePendingGuards=()=>{if(pendingGuardQueued)return;pendingGuardQueued=true;queueMicrotask(()=>{pendingGuardQueued=false;for(const pending of pendingHosts.values()){try{pending.guard()}catch(error){pending.abort.abort(error)}}})};const updatePendingAttributeObserver=()=>{if(pendingHosts.size>0&&pendingAttributeObserver===null){pendingAttributeObserver=new MutationObserver(queuePendingGuards);pendingAttributeObserver.observe(document,{attributes:true,subtree:true})}else if(pendingHosts.size===0&&pendingAttributeObserver!==null){pendingAttributeObserver.disconnect();pendingAttributeObserver=null}};const load=async(raw,tag)=>{if(!raw||typeof raw!=="object"||Array.isArray(raw))throw new TypeError("[Citry] fragment manifest is not an object.");const manifest=raw;if(Object.keys(manifest).some(key=>key!=="vue"))throw new TypeError("[Citry] Vue fragments cannot carry legacy dependency state.");const vue=manifest.vue;if(!vue||vue.protocol!=="citry-vue-fragment/1"||typeof vue.appId!=="string"||!vue.appId||typeof vue.host!=="string"||!vue.host||!vue.prepared||typeof vue.prepared!=="object"||vue.prepared.host!==vue.host||vue.prepared.manifest?.appId!==vue.appId)throw new TypeError("[Citry] fragment manifest has no valid bound Vue mount descriptor.");const hosts=document.querySelectorAll(vue.host);if(hosts.length!==1||!document.body.contains(hosts[0]))throw new TypeError("[Citry] Vue fragment host must resolve once inside the document body.");const host=hosts[0];const initialParent=host.parentNode;const initialTagParent=tag?.parentNode??null;if(reservedHosts.has(host))throw new TypeError("[Citry] Vue fragment host is already mounting.");if(tag&&isManagedDescendant(tag)||isManagedDescendant(host))throw new TypeError("[Citry] a Vue fragment cannot be inserted inside a managed Vue host.");const guard=()=>{const current=document.querySelectorAll(vue.host);if(current.length!==1||current[0]!==host||!document.body.contains(host)||host.parentNode!==initialParent||tag!==void 0&&(!document.body.contains(tag)||tag.parentNode!==initialTagParent)||isManagedDescendant(host,vue.appId))throw new TypeError("[Citry] Vue fragment host changed while mounting.")};reservedHosts.add(host);const abort=new AbortController;pendingHosts.set(host,{abort,guard});updatePendingAttributeObserver();let mounted=null;try{guard();mounted=await startPrepared(vue.prepared,{guard,nonce:documentNonce,signal:abort.signal});guard();trackedHosts.set(host,{appId:mounted.appId,dispose:()=>mounted?.app.unmount()})}catch(error){try{mounted?.app.unmount()}catch(cleanupError){console.error("[Citry] failed to dispose a rejected Vue fragment:",cleanupError)}throw error}finally{pendingHosts.delete(host);updatePendingAttributeObserver();reservedHosts.delete(host)}};const manager={load(raw,tag){if(tag){const prior=processed.get(tag);if(prior)return prior;tag.dataset.citryProcessed="";const promise=load(raw,tag);processed.set(tag,promise);return promise}return load(raw,tag)}};publicApi.fragments=manager;const process=tag=>{if(processed.has(tag)||!tag.textContent.trim())return;let manifest;try{manifest=JSON.parse(tag.textContent)}catch(error){console.error("[Citry] failed to parse Vue fragment manifest:",error);return}void manager.load(manifest,tag).catch(error=>console.error("[Citry] discarded Vue fragment:",error))};const scan=node=>{if(!(node instanceof Element))return;if(node.matches('script[type="application/json"][data-citry-vue-fragment]'))process(node);node.querySelectorAll('script[type="application/json"][data-citry-vue-fragment]').forEach(process)};let connectivityQueued=false;new MutationObserver(records=>{records.forEach(record=>{record.addedNodes.forEach(scan)});if(!connectivityQueued&&(pendingHosts.size||trackedHosts.size)){connectivityQueued=true;queueMicrotask(()=>{connectivityQueued=false;queuePendingGuards();for(const[host,tracked]of trackedHosts){if(host.isConnected)continue;trackedHosts.delete(host);try{tracked.dispose()}catch(error){console.error("[Citry] failed to dispose a removed Vue fragment:",error)}}})}}).observe(document,{childList:true,subtree:true});document.querySelectorAll('script[type="application/json"][data-citry-vue-fragment]').forEach(process);return manager}return __toCommonJS(citry_fragments_exports);})();

global.CitryVueFragments = CitryVueFragments;
/* Experimental private Citry/Vue runtime. Not a public package API. */
(function (global) {
  "use strict";
  const V = global.Vue;
  if (!V) throw new Error("Vue runtime must load before Citry's private Vue client");
  const citryNamespace = global.Citry === undefined ? {} : global.Citry;
  if ((typeof citryNamespace !== "object" || citryNamespace === null) && typeof citryNamespace !== "function")
    throw new TypeError("the global Citry namespace must be an object");
  if (Object.prototype.hasOwnProperty.call(citryNamespace, "vue")) {
    if (citryNamespace.vue !== V) throw new Error("the global Citry.vue namespace uses a different Vue runtime");
  } else {
    Object.defineProperty(citryNamespace, "vue", {value: V, enumerable: true, configurable: false, writable: false});
  }
  if (global.Citry === undefined) global.Citry = citryNamespace;
  const HELPER_CONTRACT = "f30a03c6ab842434ce11a1b4b6eac1d98ecc9d88a33207f373b88d974da3613e";
  if (global.CitryStable) {
    if (global.CitryStable.compilerRuntime?.helperContract !== HELPER_CONTRACT)
      throw new Error("an incompatible Citry Vue runtime is already loaded");
    return;
  }

  const apps = new Map();
  const registeredTypeOptions = new Map();
  const browserPluginFactories = new Map();
  const instanceRecords = new WeakMap();
  const publicEventsConfig = Object.create(null);
  const publicEventTransports = new Map();
  const publicTargetMatches = target => {
    const matches = [];
    for (const app of apps.values()) {
      const source = app.resolvePublicTarget?.(target);
      if (source) matches.push({app, source});
    }
    return matches;
  };
  let publicSend = (target, name, args, opts) => {
    const matches = publicTargetMatches(target);
    if (matches.length === 0)
      return Promise.reject(new Error("Citry.events.send found no current mounted prepared Vue component for its target."));
    if (matches.length > 1)
      return Promise.reject(new Error("Citry.events.send found multiple current mounted prepared Vue components for its target."));
    return matches[0].app.publicSend?.(matches[0].source, name, args, opts);
  };
  let publicApplyActions = actions => {
    let checked;
    try {
      checked = snapshotPublicActions(actions);
    } catch (error) {
      return Promise.reject(error);
    }
    const targets = checked.map(action => {
      if (!action || typeof action !== "object") return null;
      if (action.action === "state") return `render:${action.targetRenderId}`;
      return action.action === "render" || action.action === "event" ? action.target : null;
    }).filter(target => typeof target === "string");
    const owners = [];
    for (const target of targets) {
      // A marker is caller-relative: its first segment identifies the
      // component whose render response owns the marker.
      const marker = /^mark:([^:]+):/.exec(target);
      const lookup = marker ? `render:${marker[1]}` : target;
      const matches = publicTargetMatches(lookup);
      if (matches.length === 0)
        return Promise.reject(new Error(`Citry.events.applyActions target '${target}' is stale or retired.`));
      if (matches.length > 1)
        return Promise.reject(new Error(`Citry.events.applyActions target '${target}' matches multiple mounted prepared Vue components.`));
      owners.push(matches[0]);
    }
    if (owners.length) {
      const app = owners[0].app;
      if (owners.some(owner => owner.app !== app))
        return Promise.reject(new Error("Citry.events.applyActions cannot combine targets from different Vue apps."));
      return app.publicApplyActions?.(checked, owners[0].source);
    }
    return applyPublicActionsWithoutApp(checked);
  };
  const publicEvents = {
    send(target, name, args, opts) {
      return publicSend(target, name, args, opts);
    },
    on(name, callback) {
      if (typeof name !== "string" || name.length === 0) throw new TypeError("Citry.events.on needs a non-empty event name");
      if (typeof callback !== "function") throw new TypeError("Citry.events.on needs a callback function");
      const listener = event => callback(event.detail);
      document.addEventListener(name, listener);
      return () => document.removeEventListener(name, listener);
    },
    configure(options = {}) {
      plain(options, "Citry.events.configure options");
      if (options.csrf !== undefined) plain(options.csrf, "Citry.events.configure csrf");
      Object.assign(publicEventsConfig, options);
      if (options.csrf !== undefined)
        publicEventsConfig.csrf = {...options.csrf};
    },
    registerTransport(name, implementation) {
      if (typeof name !== "string" || name.length === 0) throw new TypeError("Citry.events.registerTransport needs a non-empty name");
      if (!implementation || typeof implementation.send !== "function")
        throw new TypeError("Citry.events.registerTransport needs an implementation with send(envelope)");
      publicEventTransports.set(name, implementation);
    },
    applyActions(actions) {
      return publicApplyActions(actions);
    },
  };
  if (Object.prototype.hasOwnProperty.call(citryNamespace, "events") && citryNamespace.events !== undefined) {
    if (!citryNamespace.events || typeof citryNamespace.events !== "object")
      throw new TypeError("the global Citry.events namespace must be an object");
    Object.assign(citryNamespace.events, publicEvents);
  } else {
    Object.defineProperty(citryNamespace, "events", {value: publicEvents, enumerable: true, configurable: true, writable: true});
  }
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const plain = (value, name) => {
    if (!value || Object.getPrototypeOf(value) !== Object.prototype) throw new TypeError(name + " must be a plain object");
    return value;
  };
  const has = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const knownActionKinds = new Set(["render", "data", "state", "event", "redirect", "url"]);
  const knownSwaps = new Set(["morph", "replace", "inner", "append", "prepend", "remove", "none"]);
  const knownRenderers = new Set(["html-fragment/1", "vue-prepared/1"]);
  const safeRenderId = value => typeof value === "string" && /^[a-z0-9_-]+$/.test(value);
  const strictPublicJson = (value, path = "", ancestors = new Set()) => {
    if (value === null || typeof value === "string" || typeof value === "boolean") return;
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new TypeError(`Citry.events.applyActions received non-finite JSON at ${path || "/"}`);
      return;
    }
    if (typeof value !== "object") throw new TypeError(`Citry.events.applyActions received non-JSON data at ${path || "/"}`);
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null && !Array.isArray(value))
      throw new TypeError(`Citry.events.applyActions received a non-JSON object at ${path || "/"}`);
    if (Object.getOwnPropertySymbols(value).length)
      throw new TypeError(`Citry.events.applyActions received symbol-keyed data at ${path || "/"}`);
    if (ancestors.has(value)) throw new TypeError(`Citry.events.applyActions received cyclic data at ${path || "/"}`);
    for (const name of Object.getOwnPropertyNames(value)) {
      if (Array.isArray(value) && name === "length") continue;
      const descriptor = Object.getOwnPropertyDescriptor(value, name);
      if (!descriptor?.enumerable || !("value" in descriptor))
        throw new TypeError(`Citry.events.applyActions received accessor or non-enumerable data at ${path || "/"}`);
    }
    if (Array.isArray(value)) {
      const names = Object.keys(value);
      if (names.length !== value.length || names.some((name, index) => name !== String(index)))
        throw new TypeError(`Citry.events.applyActions received a sparse or named array at ${path || "/"}`);
    }
    ancestors.add(value);
    for (const [key, child] of Object.entries(value)) strictPublicJson(child, `${path}/${key}`, ancestors);
    ancestors.delete(value);
  };
  const publicTarget = (value, path) => {
    if (typeof value !== "string" || value.length === 0)
      throw new TypeError(`Citry.events.applyActions needs a non-empty target at ${path}`);
    if (value.startsWith("render:") && !safeRenderId(value.slice(7)))
      throw new TypeError(`Citry.events.applyActions needs a valid render target at ${path}`);
  };
  const publicTiming = (action, path) => {
    if (has(action, "delay") && (typeof action.delay !== "number" || !Number.isFinite(action.delay) || action.delay < 0))
      throw new TypeError(`Citry.events.applyActions needs a finite non-negative delay at ${path}/delay`);
    if (has(action, "wait") && action.wait !== false)
      throw new TypeError(`Citry.events.applyActions requires wait=false at ${path}/wait`);
  };
  const assertPublicActionList = actions => {
    if (!Array.isArray(actions)) throw new TypeError("Citry.events.applyActions needs an action array");
    strictPublicJson(actions);
    let dataActions = 0;
    for (let index = 0; index < actions.length; index += 1) {
      const action = actions[index];
      const path = `/actions/${index}`;
      if (!action || Array.isArray(action) || (Object.getPrototypeOf(action) !== Object.prototype && Object.getPrototypeOf(action) !== null))
        throw new TypeError(`Citry.events.applyActions received an invalid action at ${path}`);
      if (typeof action.action !== "string" || !knownActionKinds.has(action.action))
        throw new TypeError(`Citry.events.applyActions received an invalid action kind at ${path}`);
      const required = {
        render: ["target", "swap"],
        data: ["value"],
        state: ["targetRenderId", "stateToken"],
        event: ["eventName"],
        redirect: ["url"],
        url: ["url", "mode"],
      }[action.action];
      for (const name of required) if (!has(action, name)) throw new TypeError(`Citry.events.applyActions is missing ${path}/${name}`);
      const fields = {
        render: ["action", "target", "swap", "renderer", "html", "prepared", "delay", "wait"],
        data: ["action", "value", "delay"],
        state: ["action", "targetRenderId", "stateToken", "delay", "wait"],
        event: ["action", "eventName", "detail", "target", "delay", "wait"],
        redirect: ["action", "url", "delay", "wait"],
        url: ["action", "url", "mode", "delay", "wait"],
      }[action.action];
      for (const name of Object.keys(action)) if (!fields.includes(name)) throw new TypeError(`Citry.events.applyActions found an unknown field at ${path}/${name}`);
      if (action.action === "render") {
        publicTarget(action.target, `${path}/target`);
        if (!knownSwaps.has(action.swap)) throw new TypeError(`Citry.events.applyActions received an invalid render swap at ${path}/swap`);
        const renderer = has(action, "renderer") ? action.renderer : "html-fragment/1";
        if (!knownRenderers.has(renderer)) throw new TypeError(`Citry.events.applyActions received an invalid renderer at ${path}/renderer`);
        const content = renderer === "html-fragment/1" ? "html" : "prepared";
        const other = content === "html" ? "prepared" : "html";
        if (!has(action, content) || has(action, other)) throw new TypeError(`Citry.events.applyActions received invalid render content at ${path}`);
        if (content === "html" && typeof action.html !== "string") throw new TypeError(`Citry.events.applyActions needs string HTML at ${path}/html`);
        if (content === "prepared" && (!action.prepared || Array.isArray(action.prepared) || (Object.getPrototypeOf(action.prepared) !== Object.prototype && Object.getPrototypeOf(action.prepared) !== null)))
          throw new TypeError(`Citry.events.applyActions needs prepared object data at ${path}/prepared`);
      } else if (action.action === "data") {
        dataActions += 1;
      } else if (action.action === "state") {
        if (typeof action.targetRenderId !== "string" || !safeRenderId(action.targetRenderId)) throw new TypeError(`Citry.events.applyActions needs a valid state target at ${path}/targetRenderId`);
        if (typeof action.stateToken !== "string" || action.stateToken.length === 0) throw new TypeError(`Citry.events.applyActions needs a state token at ${path}/stateToken`);
      } else if (action.action === "event") {
        if (typeof action.eventName !== "string" || action.eventName.length === 0 || action.eventName.startsWith("citry:")) throw new TypeError(`Citry.events.applyActions needs a public event name at ${path}/eventName`);
        if (has(action, "target")) publicTarget(action.target, `${path}/target`);
      } else if (action.action === "redirect") {
        if (typeof action.url !== "string" || action.url.length === 0) throw new TypeError(`Citry.events.applyActions needs a redirect URL at ${path}/url`);
      } else {
        if (typeof action.url !== "string" || action.url.length === 0 || (action.mode !== "push" && action.mode !== "replace")) throw new TypeError(`Citry.events.applyActions needs a URL and mode at ${path}`);
      }
      publicTiming(action, path);
    }
    if (dataActions > 1) throw new TypeError("Citry.events.applyActions accepts at most one data action");
    return actions;
  };
  const snapshotPublicActions = actions => {
    const protocolValidator = global.CitryVueEvents?.assertValidActionList;
    if (typeof protocolValidator === "function") protocolValidator(actions);
    else assertPublicActionList(actions);
    return structuredClone(actions);
  };
  async function applyPublicActionsWithoutApp(actions) {
    let data;
    const apply = async action => {
      if (!action || typeof action !== "object" || typeof action.action !== "string")
        throw new TypeError("Citry.events.applyActions received an invalid action");
      if (typeof action.delay === "number" && action.delay > 0)
        await new Promise(resolve => setTimeout(resolve, action.delay * 1000));
      if (action.action === "data") data = action.value;
      else if (action.action === "redirect") global.location.assign(action.url);
      else if (action.action === "url") global.history[action.mode === "push" ? "pushState" : "replaceState"](global.history.state, "", action.url);
      else if (action.action === "event") {
        if (action.target !== undefined) throw new Error("Citry.events.applyActions needs a mounted component for targeted Event actions.");
        document.dispatchEvent(new CustomEvent(action.eventName, {detail: action.detail, bubbles: true}));
      } else throw new Error("Citry.events.applyActions needs a mounted component for Render and State actions.");
    };
    for (const action of actions) {
      if (action?.wait === false) void apply(action).catch(error => console.error("[Citry] applying a public action failed:", error));
      else await apply(action);
    }
    return data;
  }
  const clone = value => structuredClone(value);
  const freezeDetached = value => {
    if (value && typeof value === "object" && !Object.isFrozen(value)) {
      for (const child of Array.isArray(value) ? value : Object.values(value)) freezeDetached(child);
      Object.freeze(value);
    }
    return value;
  };
  const detached = value => freezeDetached(clone(value));
  const RESERVED_TEMPLATE_CONTEXT_NAMES = new Set([
    "$attrs", "$citryEvents", "$data", "$el", "$emit", "$error", "$event", "$forceUpdate", "$loading",
    "$nextTick", "$onEvent", "$options", "$parent", "$props", "$refs", "$root", "$sendEvent", "$slots", "$state", "$watch",
  ]);
  function templateContextNames(value, label) {
    if (!Array.isArray(value) || value.some(item => typeof item !== "string" || !/^\$[A-Za-z][A-Za-z0-9_]*$/.test(item) ||
        RESERVED_TEMPLATE_CONTEXT_NAMES.has(item)) ||
        new Set(value).size !== value.length || [...value].sort().some((item, index) => item !== value[index]))
      throw new TypeError(label + " must be a sorted unique array of public $ names");
    return Object.freeze([...value]);
  }
  function registerBrowserPlugin(name, schemaVersion, factory, contextNames = []) {
    if (typeof name !== "string" || !/^[a-z][a-z0-9_]*$/.test(name) ||
        !Number.isInteger(schemaVersion) || schemaVersion <= 0 || typeof factory !== "function")
      throw new TypeError("invalid Citry browser plugin registration");
    const normalizedNames = templateContextNames(contextNames, "browser plugin template context names");
    const prior = browserPluginFactories.get(name);
    if (prior && (prior.schemaVersion !== schemaVersion || prior.factory !== factory ||
        JSON.stringify(prior.templateContextNames) !== JSON.stringify(normalizedNames)))
      throw new Error("Citry browser plugin registration collision: " + name);
    browserPluginFactories.set(name, Object.freeze({schemaVersion, factory, templateContextNames: normalizedNames}));
  }
  function extensionEntries(value) {
    plain(value, "prepared extensions");
    return Object.keys(value).sort().map(name => {
      if (!/^[a-z][a-z0-9_]*$/.test(name)) throw new Error("invalid prepared extension name");
      const item = plain(value[name], "prepared extension");
      if (Object.keys(item).sort().join(",") !== "payload,schemaVersion,templateContextNames" ||
          !Number.isInteger(item.schemaVersion) || item.schemaVersion <= 0)
        throw new Error("invalid prepared extension wrapper");
      plain(item.payload, "prepared extension payload");
      return [name, {...item, templateContextNames: templateContextNames(item.templateContextNames, "extension template context names")}];
    });
  }
  const ORDINARY_TARGET = "ordinary-vnodes/1";
  const INPUT_MODEL_SITE = "__citryInputModelSite";
  let nextInputModelIdentity = 0;
  const inputModelObjectIds = new WeakMap();
  const inputModelSymbolIds = (() => {
    try {
      const values = new WeakMap(), probe = Symbol();
      values.set(probe, 0);
      return values;
    } catch {
      return null;
    }
  })();
  const inputModelFallbackSymbolIds = new WeakMap();
  const inputModelIdentityId = (values, value) => {
    let id = values.get(value);
    if (id === undefined) values.set(value, id = ++nextInputModelIdentity);
    return id;
  };
  const inputModelToken = (instance, value) => {
    if (value === undefined) return ["undefined"];
    if (value === null) return ["null"];
    if (typeof value === "string") return ["string", value];
    if (typeof value === "boolean") return ["boolean", value];
    if (typeof value === "number") return ["number", Number.isNaN(value) ? "NaN" : String(value)];
    if (typeof value === "bigint") return ["bigint", String(value)];
    if (typeof value === "symbol") {
      const registered = Symbol.keyFor(value);
      if (registered !== undefined) return ["registered-symbol", registered];
      if (inputModelSymbolIds) return ["symbol", inputModelIdentityId(inputModelSymbolIds, value)];
      let fallback = inputModelFallbackSymbolIds.get(instance);
      if (!fallback) inputModelFallbackSymbolIds.set(instance, fallback = new Map());
      return ["symbol", inputModelIdentityId(fallback, value)];
    }
    return ["object", inputModelIdentityId(inputModelObjectIds, value)];
  };
  const inputModelKey = (instance, site, type, authoredKey) => {
    return JSON.stringify([
      "\u0000citry-input-model",
      inputModelToken(instance, site),
      inputModelToken(instance, type),
      inputModelToken(instance, authoredKey),
    ]);
  };
  const vnodeProps = props => {
    if (props === null || props === undefined || !own(props, INPUT_MODEL_SITE)) return props;
    const site = props[INPUT_MODEL_SITE];
    if (typeof site !== "string" || site.length === 0) throw new Error("invalid input model lifecycle site");
    const prepared = {...props};
    delete prepared[INPUT_MODEL_SITE];
    const instance = V.getCurrentInstance();
    if (!instance) throw new Error("input model lifecycle key requires an active Vue render");
    const type = prepared.type === null || prepared.type === undefined ? "text" : prepared.type;
    prepared.key = inputModelKey(instance, site, type, prepared.key);
    return prepared;
  };
  const compilerRuntime = Object.create(V);
  Object.defineProperty(compilerRuntime, "openBlock", {value: () => null, enumerable: true});
  for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"]) {
    Object.defineProperty(compilerRuntime, name, {
      value: (type, props, children) => V.createVNode(type, vnodeProps(props), children),
      enumerable: true,
    });
  }
  Object.defineProperty(compilerRuntime, "createTextVNode", {
    value: text => V.createTextVNode(text),
    enumerable: true,
  });
  for (const name of ["resolveDirective", "vModelCheckbox", "vModelDynamic", "vModelRadio", "vModelSelect", "vModelText"]) {
    if (V[name] === undefined) throw new Error("Vue runtime lacks required compiler helper: " + name);
    Object.defineProperty(compilerRuntime, name, {value: V[name], enumerable: true});
  }
  function runtimeForDynamicElements(entries) {
    if (!Array.isArray(entries)) throw new TypeError("dynamicElements must be an array");
    if (entries.length === 0) return compilerRuntime;
    const aliases = new Map();
    for (const entry of entries) {
      plain(entry, "dynamic element entry");
      if (Object.keys(entry).sort().join(",") !== "alias,sourceEnd,sourceStart,tag" ||
          typeof entry.alias !== "string" || !/^citry-dynamic-[0-9a-f]{16}$/.test(entry.alias) ||
          typeof entry.tag !== "string" || !/^[A-Za-z][A-Za-z0-9_.-]*$/.test(entry.tag) ||
          ["script", "style", "template"].includes(entry.tag.toLowerCase()) ||
          !Number.isInteger(entry.sourceStart) || !Number.isInteger(entry.sourceEnd) ||
          entry.sourceStart < 0 || entry.sourceEnd <= entry.sourceStart || aliases.has(entry.alias))
        throw new TypeError("invalid dynamic element entry");
      aliases.set(entry.alias, entry.tag);
    }
    const runtime = Object.create(compilerRuntime);
    for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"])
      Object.defineProperty(runtime, name, {enumerable: true, value(type, props, children) {
        if (typeof type === "string" && type.startsWith("citry-dynamic-")) {
          if (!aliases.has(type)) throw new Error("unknown prepared dynamic element alias: " + type);
          type = aliases.get(type);
        }
        return V.createVNode(type, vnodeProps(props), children);
      }});
    return Object.freeze(runtime);
  }
  Object.defineProperty(compilerRuntime, "runtimeForDynamicElements", {
    value: runtimeForDynamicElements,
    enumerable: false,
  });
  Object.defineProperty(compilerRuntime, "helperContract", {value: HELPER_CONTRACT, enumerable: true});

  const opaqueHtmlComponent = Object.freeze({
    name: "CitryOpaqueHtml",
    props: {record: {type: Object, required: true}},
    setup(props) {
      return () => {
        const record = plain(props.record, "opaque HTML record");
        if (Object.keys(record).join(",") !== "html" || typeof record.html !== "string")
          throw new TypeError("invalid opaque HTML record");
        if (record.html === "") return V.h(V.Fragment, {key: record.html}, []);
        const vnode = V.createStaticVNode(record.html, 0);
        vnode.key = record.html;
        return vnode;
      };
    },
  });

  function normalizeDirectiveSignature(value) {
    if (!Array.isArray(value)) throw new TypeError("directiveSignature must be an array");
    const result = value.map(item => {
      plain(item, "directive signature entry");
      if (typeof item.siteId !== "string" || typeof item.name !== "string" || (item.arg !== null && typeof item.arg !== "string") || !Array.isArray(item.modifiers) || item.modifiers.some(x => typeof x !== "string")) throw new TypeError("invalid directive signature entry");
      const modifiers = [...item.modifiers];
      if (new Set(modifiers).size !== modifiers.length || modifiers.some((x, i) => i && modifiers[i - 1] > x)) throw new Error("directive modifiers must be unique and sorted");
      return Object.freeze({siteId: item.siteId, name: item.name, arg: item.arg, modifiers: Object.freeze(modifiers)});
    });
    const sites = new Set();
    for (const item of result) { if (sites.has(item.siteId)) throw new Error("duplicate directive site"); sites.add(item.siteId); }
    return Object.freeze(result);
  }
  const signatureKey = value => JSON.stringify(value);
  function normalizeReplacementSites(value) {
    if (!Array.isArray(value)) throw new TypeError("replacementSites must be an array");
    let prior = "";
    return Object.freeze(value.map(item => {
      plain(item, "replacement site");
      const key = item.replacementKey ?? item.key;
      const descendants = item.localDescendants ?? [];
      const descendantRuns = item.localDescendantRuns ?? [];
      if (typeof item.siteId !== "string" || typeof key !== "string" ||
          !Array.isArray(descendants) || descendants.some(id => typeof id !== "string") ||
          signatureKey(descendants) !== signatureKey([...new Set(descendants)].sort()) ||
          !Array.isArray(descendantRuns) || descendantRuns.some(id => typeof id !== "string") ||
          new Set(descendantRuns).size !== descendantRuns.length || item.siteId <= prior)
        throw new Error("replacement sites must be sorted and unique");
      prior = item.siteId;
      return Object.freeze({siteId: item.siteId, key, localDescendants: Object.freeze([...descendants]), localDescendantRuns: Object.freeze([...descendantRuns])});
    }));
  }

  function normalizeLocalCallRuns(value) {
    if (!Array.isArray(value)) throw new TypeError("localCallRuns must be an array");
    const ids = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "local call run");
      const strings = ["runId", "typeKey", "componentTag", "collectionExpression", "idExpression", "keyExpression"];
      const offsets = ["sourceStart", "sourceEnd", "loopSourceStart", "loopSourceEnd"];
      if (Object.keys(item).length !== strings.length + offsets.length ||
          [...strings, ...offsets].some(key => !own(item, key)) || strings.some(key => typeof item[key] !== "string") ||
          offsets.some(key => !Number.isInteger(item[key]) || item[key] < 0) ||
          item.sourceEnd < item.sourceStart || item.loopSourceEnd < item.loopSourceStart ||
          ids.has(item.runId)) throw new TypeError("invalid local call run");
      ids.add(item.runId);
      return Object.freeze(Object.fromEntries([...strings, ...offsets].map(key => [key, item[key]])));
    }));
  }

  function normalizeLocalCalls(value) {
    if (!Array.isArray(value)) throw new TypeError("localCalls must be an array");
    const ids = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "local call declaration");
      if (typeof item.localId !== "string" || typeof item.typeKey !== "string" ||
          typeof item.componentTag !== "string" || !Array.isArray(item.bindings) ||
          Object.keys(item).sort().join(",") !== "bindings,componentTag,localId,typeKey" ||
          ids.has(item.localId)) throw new TypeError("invalid local call declaration");
      const bindings = Object.freeze(item.bindings.map(binding => {
        plain(binding, "component call binding");
        if (Object.keys(binding).sort().join(",") !== "kind,name,sourceEnd,sourceStart,value" ||
            !["prop", "props-object", "events-object", "event", "ref-static", "ref-expression"].includes(binding.kind) ||
            typeof binding.name !== "string" || typeof binding.value !== "string" ||
            !Number.isInteger(binding.sourceStart) || !Number.isInteger(binding.sourceEnd) ||
            binding.sourceStart < 0 || binding.sourceEnd <= binding.sourceStart)
          throw new TypeError("invalid component call binding");
        return Object.freeze({
          kind: binding.kind,
          name: binding.name,
          value: binding.value,
          sourceStart: binding.sourceStart,
          sourceEnd: binding.sourceEnd,
        });
      }));
      ids.add(item.localId);
      return Object.freeze({localId: item.localId, typeKey: item.typeKey, componentTag: item.componentTag, bindings});
    }));
  }

  function normalizeDynamicElements(value) {
    if (!Array.isArray(value)) throw new TypeError("dynamicElements must be an array");
    const aliases = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "dynamic element entry");
      if (Object.keys(item).sort().join(",") !== "alias,sourceEnd,sourceStart,tag" ||
          typeof item.alias !== "string" || !/^citry-dynamic-[0-9a-f]{16}$/.test(item.alias) ||
          typeof item.tag !== "string" || !/^[A-Za-z][A-Za-z0-9_.-]*$/.test(item.tag) ||
          ["script", "style", "template"].includes(item.tag.toLowerCase()) || aliases.has(item.alias) ||
          !Number.isInteger(item.sourceStart) || !Number.isInteger(item.sourceEnd) ||
          item.sourceStart < 0 || item.sourceEnd <= item.sourceStart)
        throw new TypeError("invalid dynamic element entry");
      aliases.add(item.alias);
      return Object.freeze({
        alias: item.alias,
        tag: item.tag,
        sourceStart: item.sourceStart,
        sourceEnd: item.sourceEnd,
      });
    }));
  }

  function normalizeOpaqueHtmlSites(value) {
    if (!Array.isArray(value)) throw new TypeError("opaqueHtmlSites must be an array");
    const keys = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "opaque HTML site");
      if (Object.keys(item).sort().join(",") !== "key,origin,sourceEnd,sourceStart" ||
          typeof item.key !== "string" || !/^citryOpaque[0-9A-Za-z]+$/.test(item.key) || keys.has(item.key) ||
          !["raw", "markup"].includes(item.origin) || !Number.isInteger(item.sourceStart) ||
          !Number.isInteger(item.sourceEnd) || item.sourceStart < 0 || item.sourceEnd <= item.sourceStart)
        throw new TypeError("invalid opaque HTML site");
      keys.add(item.key);
      return Object.freeze({
        key: item.key,
        sourceStart: item.sourceStart,
        sourceEnd: item.sourceEnd,
        origin: item.origin,
      });
    }));
  }
  function normalizeRuntimeEventSites(value) {
    if (!Array.isArray(value)) throw new TypeError("runtimeEventSites must be an array");
    const seen = new Set(), seenRoutes = new Set();
    return Object.freeze(value.map(site => {
      plain(site, "runtime event site");
      if (Object.keys(site).sort().join(",") !== "bindingKey,siteId,steps" ||
          typeof site.siteId !== "string" || !/^citryDirective[0-9a-f]+D[0-9]+$/.test(site.siteId) ||
          seen.has(site.siteId) ||
          typeof site.bindingKey !== "string" || !/^citryRuntimeEvents[0-9A-Za-z]+$/.test(site.bindingKey) ||
          !Array.isArray(site.steps)) throw new TypeError("runtime event site is invalid or duplicated");
      seen.add(site.siteId);
      const steps = site.steps.map(step => {
        plain(step, "runtime event site step");
        const keys = Object.keys(step).sort().join(",");
        if (step.kind === "branch" && keys === "index,key,kind" && typeof step.key === "string" &&
            /^citryIf[0-9]+$/.test(step.key) &&
            Number.isSafeInteger(step.index) && step.index >= 0)
          return Object.freeze({kind: step.kind, key: step.key, index: step.index});
        if ((step.kind === "each" || step.kind === "empty") && keys === "key,kind" &&
            typeof step.key === "string" && /^citryLoop[0-9]+$/.test(step.key))
          return Object.freeze({kind: step.kind, key: step.key});
        throw new TypeError("runtime event site step is invalid");
      });
      const routeKey = JSON.stringify([site.bindingKey,
        steps.map(step => [step.kind, step.key, step.kind === "branch" ? step.index : null])]);
      if (seenRoutes.has(routeKey)) throw new TypeError("runtime event site route and binding key are duplicated");
      seenRoutes.add(routeKey);
      return Object.freeze({siteId:site.siteId, bindingKey:site.bindingKey, steps:Object.freeze(steps)});
    }));
  }

  function validateRuntimeEventSiteDeclarations(directiveSignature, runtimeEventSites) {
    const runtimeDirectives = directiveSignature.filter(item => item.name === "v-citry-runtime-events");
    if (runtimeDirectives.some(item => item.arg !== null || item.modifiers.length !== 0))
      throw new Error("runtime event directive declaration has arguments or modifiers");
    const directiveIds = new Set(runtimeDirectives.map(item => item.siteId));
    const siteIds = new Set(runtimeEventSites.map(item => item.siteId));
    if (directiveIds.size !== siteIds.size || [...directiveIds].some(id => !siteIds.has(id)))
      throw new Error("runtime event sites do not exactly match runtime directive declarations");
  }

  function normalizeDefinitionAsset(asset) {
    plain(asset, "prepared definition asset");
    const keys = ["directiveSignature", "dynamicElements", "helperContract", "id", "localCallRuns",
      "localCalls", "opaqueHtmlSites", "replacementSites", "runtimeEventSites", "sha256", "target", "url"];
    if (Object.keys(asset).sort().join(",") !== [...keys].sort().join(",") ||
        typeof asset.id !== "string" || typeof asset.url !== "string" ||
        asset.target !== ORDINARY_TARGET || asset.helperContract !== HELPER_CONTRACT)
      throw new Error("invalid prepared definition asset");
    sriFromHex(asset.sha256);
    const directiveSignature = normalizeDirectiveSignature(asset.directiveSignature);
    const runtimeEventSites = normalizeRuntimeEventSites(asset.runtimeEventSites);
    validateRuntimeEventSiteDeclarations(directiveSignature, runtimeEventSites);
    return Object.freeze({
      id: asset.id, url: asset.url, sha256: asset.sha256, target: asset.target,
      helperContract: asset.helperContract,
      dynamicElements: normalizeDynamicElements(asset.dynamicElements),
      directiveSignature,
      replacementSites: normalizeReplacementSites(asset.replacementSites),
      localCalls: normalizeLocalCalls(asset.localCalls),
      localCallRuns: normalizeLocalCallRuns(asset.localCallRuns),
      opaqueHtmlSites: normalizeOpaqueHtmlSites(asset.opaqueHtmlSites),
      runtimeEventSites,
    });
  }

  function definitionMetadataKey(definition) {
    return signatureKey({target: definition.target, helperContract: definition.helperContract,
      dynamicElements: definition.dynamicElements, directiveSignature: definition.directiveSignature,
      replacementSites: definition.replacementSites, localCalls: definition.localCalls,
      localCallRuns: definition.localCallRuns, opaqueHtmlSites: definition.opaqueHtmlSites,
      runtimeEventSites: definition.runtimeEventSites});
  }

  function validateRuntimeEventSpec(id, spec, occurrence) {
    plain(spec, "runtime event binding");
    const timing = value => value === null || Number.isSafeInteger(value) && value >= 0;
    const descriptor = occurrence.eventContext?.descriptor;
    if (!/^citryRuntimeEvent[0-9a-f]+$/.test(id) ||
        Object.keys(spec).sort().join(",") !== "args,debounce,event,handler,id,key,once,prevent,self,stop,throttle" ||
        spec.id !== id || typeof spec.event !== "string" || spec.event === "" ||
        typeof spec.handler !== "string" || spec.handler === "" || spec.args !== null ||
        ![spec.prevent, spec.stop, spec.self, spec.once].every(value => typeof value === "boolean") ||
        spec.key !== null && (typeof spec.key !== "string" || spec.key === "") ||
        !timing(spec.debounce) || !timing(spec.throttle) || !descriptor ||
        !own(descriptor.eventHandlers, spec.handler))
      throw new Error("runtime event binding is missing, stale, or invalid");
  }

  function validateRuntimePollSpec(id, spec, occurrence) {
    plain(spec, "runtime poll binding");
    const descriptor = occurrence.eventContext?.descriptor;
    if (!/^citryRuntimePoll[0-9a-f]+$/.test(id) ||
        Object.keys(spec).sort().join(",") !== "args,handler,id,interval" ||
        spec.id !== id || typeof spec.handler !== "string" || spec.handler === "" ||
        spec.args !== null || !Number.isSafeInteger(spec.interval) || spec.interval <= 0 ||
        !descriptor || !own(descriptor.eventHandlers, spec.handler))
      throw new Error("runtime poll binding is missing, stale, or invalid");
  }

  function validateOccurrenceRuntimeEvents(occurrence, definition) {
    const referenced = new Set();
    const visit = (site, index, scope) => {
      if (index === site.steps.length) {
        if (!own(scope, site.bindingKey) || typeof scope[site.bindingKey] !== "string")
          throw new Error("runtime event site terminal is missing or invalid");
        const ids = scope[site.bindingKey] === "" ? [] : scope[site.bindingKey].split(",");
        if (new Set(ids).size !== ids.length || ids.some(id =>
          !/^citryRuntime(?:Event|Poll)[0-9a-f]+$/.test(id)))
          throw new Error("runtime event site references invalid or duplicate ids");
        for (const id of ids) referenced.add(id);
        return;
      }
      const step = site.steps[index];
      if (step.kind === "branch") {
        if (!own(scope, step.key) || !Number.isSafeInteger(scope[step.key]))
          throw new Error("runtime event branch selector is invalid");
        if (scope[step.key] === step.index) visit(site, index + 1, scope);
        return;
      }
      if (!own(scope, step.key) || !Array.isArray(scope[step.key]))
        throw new Error("runtime event loop selector is invalid");
      if (step.kind === "each") {
        for (const row of scope[step.key]) visit(site, index + 1, plain(row, "runtime event loop row"));
      } else if (scope[step.key].length === 0) visit(site, index + 1, scope);
    };
    for (const site of definition.runtimeEventSites) visit(site, 0, occurrence.preparedData);
    const eventTable = own(occurrence.preparedData, "eventBindings")
      ? plain(occurrence.preparedData.eventBindings, "preparedData.eventBindings") : {};
    const pollTable = own(occurrence.preparedData, "pollBindings")
      ? plain(occurrence.preparedData.pollBindings, "preparedData.pollBindings") : {};
    const runtimeEventIds = Object.keys(eventTable).filter(id => id.startsWith("citryRuntimeEvent"));
    const runtimePollIds = Object.keys(pollTable).filter(id => id.startsWith("citryRuntimePoll"));
    const eventRuntimeIds = Object.keys(eventTable).filter(id => id.startsWith("citryRuntime"));
    const pollRuntimeIds = Object.keys(pollTable).filter(id => id.startsWith("citryRuntime"));
    const runtimeIds = [...runtimeEventIds, ...runtimePollIds];
    if (eventRuntimeIds.length !== runtimeEventIds.length || pollRuntimeIds.length !== runtimePollIds.length ||
        runtimeIds.length !== referenced.size || runtimeIds.some(id => !referenced.has(id)))
      throw new Error("runtime event references do not match definition sites");
    for (const id of referenced) {
      if (/^citryRuntimeEvent[0-9a-f]+$/.test(id) && own(eventTable, id) && !own(pollTable, id))
        validateRuntimeEventSpec(id, eventTable[id], occurrence);
      else if (/^citryRuntimePoll[0-9a-f]+$/.test(id) && own(pollTable, id) && !own(eventTable, id))
        validateRuntimePollSpec(id, pollTable[id], occurrence);
      else throw new Error("runtime event site references a missing or swapped binding table entry");
    }
  }

  function preflightDefinitions(app, assets, occurrences, rootId) {
    const declared = new Map();
    for (const asset of assets) {
      const normalized = normalizeDefinitionAsset(asset);
      if (declared.has(normalized.id)) throw new Error("duplicate prepared definition asset");
      const prior = app.definitions.get(normalized.id);
      if (prior && definitionMetadataKey(prior) !== definitionMetadataKey(normalized))
        throw new Error("prepared definition metadata collision");
      declared.set(normalized.id, prior || normalized);
    }
    const occurrenceMap = new Map(occurrences.map(item => [item.id, item]));
    for (const occurrence of occurrences) {
      const definition = declared.get(occurrence.definitionId) || app.definitions.get(occurrence.definitionId);
      if (!definition) throw new Error("unknown prepared definition metadata");
      validateOccurrenceCallRuns(occurrenceMap, occurrence, definition);
      validateOccurrenceRuntimeEvents(occurrence, definition);
      const opaque = own(occurrence.preparedData, "opaqueHtml")
        ? plain(occurrence.preparedData.opaqueHtml, "preparedData.opaqueHtml") : {};
      const declaredOpaque = new Set(definition.opaqueHtmlSites.map(site => site.key));
      if (Object.keys(opaque).length !== declaredOpaque.size || Object.keys(opaque).some(key => !declaredOpaque.has(key)))
        throw new Error("prepared opaque HTML does not match definition declarations");
      for (const key of declaredOpaque) {
        const record = plain(opaque[key], "opaque HTML record");
        if (Object.keys(record).join(",") !== "html" || typeof record.html !== "string")
          throw new TypeError("invalid opaque HTML record");
      }
    }
    validateGraph(occurrenceMap, rootId);
    return declared;
  }

  function validateOccurrenceCallRuns(occurrences, occurrence, definition) {
    const calls = plain(occurrence.preparedData.calls, "preparedData.calls");
    const declarations = new Map(definition.localCallRuns.map(run => [run.runId, run]));
    const values = own(occurrence.preparedData, "callRuns")
      ? plain(occurrence.preparedData.callRuns, "preparedData.callRuns")
      : declarations.size === 0 ? {} : (() => { throw new Error("prepared call runs do not match definition declarations"); })();
    if (Object.keys(values).some(runId => !declarations.has(runId)) ||
        [...declarations.keys()].some(runId => !own(values, runId)))
      throw new Error("prepared call runs do not match definition declarations");
    if (Object.keys(calls).length !== definition.localCalls.length)
      throw new Error("prepared ordinary calls do not match definition declarations");
    const covered = new Set();
    for (const declaration of definition.localCalls) {
      if (!own(calls, declaration.localId))
        throw new Error("prepared ordinary local call does not match its declaration");
      const binding = calls[declaration.localId];
      const child = occurrences.get(binding.id);
      if (!child || child.parentId !== binding.parentId || child.typeKey !== declaration.typeKey || covered.has(child.id))
        throw new Error("prepared ordinary local call stable-type mismatch");
      covered.add(child.id);
    }
    for (const [runId, ids] of Object.entries(values)) {
      if (!Array.isArray(ids) || new Set(ids).size !== ids.length || ids.some(id => typeof id !== "string"))
        throw new TypeError("invalid prepared call run values");
      const declaration = declarations.get(runId);
      for (const id of ids) {
        const child = occurrences.get(id);
        if (!child || child.parentId !== occurrence.id || child.typeKey !== declaration.typeKey || covered.has(id))
          throw new Error("prepared local call run stable-type or ownership mismatch");
        covered.add(id);
      }
    }
  }

  function validateDefinitionCallRuns(app, definition) {
    const declared = new Set(definition.localCallRuns.map(run => run.runId));
    for (const site of definition.replacementSites) {
      if (site.localDescendantRuns.some(runId => !declared.has(runId)))
        throw new Error("replacement site references an unknown local call run");
    }
    const stagedTags = new Map(app.callRunTags);
    for (const run of [...definition.localCalls, ...definition.localCallRuns]) {
      const prior = stagedTags.get(run.componentTag);
      if (prior && prior !== run.typeKey) throw new Error("local call component tag stable-type mismatch");
      stagedTags.set(run.componentTag, run.typeKey);
    }
  }

  function validateGraph(occurrences, rootId) {
    if (typeof rootId !== "string" || !occurrences.has(rootId) || occurrences.get(rootId).parentId !== null || occurrences.get(rootId).placementKey !== null) throw new Error("invalid prepared root");
    let roots = 0;
    const placements = new Set();
    for (const item of occurrences.values()) {
      if (item.parentId === null) roots += 1;
      else {
        if (!occurrences.has(item.parentId)) throw new Error("unknown occurrence parent");
        if (typeof item.placementKey !== "string" || item.placementKey.length === 0) throw new Error("invalid occurrence placement key");
        const placement = JSON.stringify([item.parentId, item.placementKey]);
        if (placements.has(placement)) throw new Error("duplicate occurrence placement key within one parent");
        placements.add(placement);
      }
      const seen = new Set([item.id]); let cursor = item.parentId;
      while (cursor !== null) { if (seen.has(cursor)) throw new Error("cyclic occurrence graph"); seen.add(cursor); cursor = occurrences.get(cursor).parentId; }
    }
    if (roots !== 1) throw new Error("prepared graph must have exactly one root");
    const directCalls = [...occurrences.values()].some(item => own(item.preparedData, "calls"));
    if (directCalls) {
      const referenced = new Set();
      for (const owner of occurrences.values()) {
        plain(owner.preparedData.calls, "preparedData.calls");
        for (const binding of Object.values(owner.preparedData.calls)) {
          plain(binding, "prepared local call binding");
          if (Object.keys(binding).sort().join(",") !== "id,key,parentId" ||
              typeof binding.id !== "string" || typeof binding.key !== "string" ||
              typeof binding.parentId !== "string")
            throw new Error("invalid prepared local call binding");
          const child = occurrences.get(binding.id);
          if (!child || child.parentId !== binding.parentId || referenced.has(binding.id))
            throw new Error("prepared local call does not match occurrence placement");
          referenced.add(binding.id);
        }
        if (own(owner.preparedData, "callRuns")) {
          const runs = plain(owner.preparedData.callRuns, "preparedData.callRuns");
          for (const ids of Object.values(runs)) {
            if (!Array.isArray(ids) || ids.some(id => typeof id !== "string"))
              throw new Error("invalid prepared local call run values");
            for (const id of ids) {
              const child = occurrences.get(id);
              if (!child || child.parentId !== owner.id || referenced.has(id))
                throw new Error("prepared local call run does not match occurrence placement");
              referenced.add(id);
            }
          }
        }
      }
      for (const id of occurrences.keys()) {
        if (id !== rootId && !referenced.has(id)) throw new Error("prepared occurrence has no local call binding");
      }
    }
  }

  function definitionRegistry(appId) {
    const app = apps.get(appId);
    if (!app) throw new Error("unknown Citry Vue app: " + appId);
    return app;
  }

  const MARK_NAME = /^[A-Za-z][A-Za-z0-9_-]*$/;
  function normalizeMarkers(values, occurrences) {
    if (!Array.isArray(values)) throw new TypeError("prepared markers must be an array");
    if (values.length === 0) return new Map();
    const markers = new Map(), physical = new Set();
    let prior = null;
    for (const value of values) {
      plain(value, "prepared marker");
      if (Object.keys(value).sort().join(",") !== "name,occurrenceId,ownerId" ||
          typeof value.ownerId !== "string" || !occurrences.has(value.ownerId) ||
          typeof value.occurrenceId !== "string" || !occurrences.has(value.occurrenceId) ||
          typeof value.name !== "string" || !MARK_NAME.test(value.name))
        throw new Error("prepared marker metadata is invalid");
      const key = value.ownerId + "\0" + value.name;
      const order = key + "\0" + value.occurrenceId;
      if (markers.has(key) || physical.has(value.occurrenceId) || prior !== null && order <= prior)
        throw new Error("prepared marker metadata is duplicated or unsorted");
      markers.set(key, Object.freeze({...value}));
      physical.add(value.occurrenceId); prior = order;
    }
    return markers;
  }

  function configure(bootstrap, startAttempt = null) {
    plain(bootstrap, "bootstrap");
    if (bootstrap.protocol !== "citry-vue-prepared/1" || typeof bootstrap.appId !== "string" || !Number.isInteger(bootstrap.revision) || !Array.isArray(bootstrap.occurrences)) throw new TypeError("invalid bootstrap");
    if (apps.has(bootstrap.appId)) throw new Error("duplicate Citry Vue app");
    const occurrences = new Map();
    for (const item of bootstrap.occurrences) {
      plain(item, "occurrence");
      if (typeof item.id !== "string" || typeof item.typeKey !== "string" || typeof item.definitionId !== "string" || (item.parentId !== null && typeof item.parentId !== "string") || (item.placementKey !== null && typeof item.placementKey !== "string")) throw new TypeError("invalid occurrence identity");
      plain(item.serverData, "serverData");
      plain(item.preparedData, "preparedData");
      if (occurrences.has(item.id)) throw new Error("duplicate occurrence id");
      occurrences.set(item.id, Object.freeze({...clone(item), serverData: clone(item.serverData)}));
    }
    validateGraph(occurrences, bootstrap.rootId);
    const markers = normalizeMarkers(bootstrap.markers, occurrences);
    const initialLive = new Map([...occurrences].map(([id,item]) => [id, {...item, serverData: V.reactive(clone(item.serverData))}]));
    const definitionTypes = new Map();
    for (const item of occurrences.values()) { const prior = definitionTypes.get(item.definitionId); if (prior && prior !== item.typeKey) throw new Error("definition used by multiple stable types"); definitionTypes.set(item.definitionId, item.typeKey); }
    const app = {id: bootstrap.appId, startAttempt, rootId: bootstrap.rootId, revision: bootstrap.revision, occurrences, markers, snapshot: V.shallowRef(initialLive), definitions: new Map(), definitionTypes, callRunTags: new Map(), typeTags: new Map(), types: new Map(), browserPlugins: [], templateContextNames: [], initialPluginStages: [], vueApp: null, hostElement: null, mounted: new Map(), nextMountGeneration: 0, preparedHost: null, eventDispatch: null, eventDispatchComponent: null, initialTasks: new Set(), initialError: null, transaction: null, busy: false, terminal: false};
    apps.set(app.id, app);
    return app;
  }

  function registerDefinition(appId, definitionId, definition, expected = null) {
    plain(definition, "render definition");
    if (typeof definitionId !== "string" || typeof definition.render !== "function" || definition.target !== ORDINARY_TARGET || definition.helperContract !== HELPER_CONTRACT) throw new TypeError("invalid render definition");
    const normalized = Object.freeze({render: definition.render, target: definition.target, helperContract: definition.helperContract, dynamicElements:normalizeDynamicElements(definition.dynamicElements || []),directiveSignature: normalizeDirectiveSignature(definition.directiveSignature),replacementSites:normalizeReplacementSites(definition.replacementSites),localCalls:normalizeLocalCalls(definition.localCalls),localCallRuns:normalizeLocalCallRuns(definition.localCallRuns),opaqueHtmlSites:normalizeOpaqueHtmlSites(definition.opaqueHtmlSites),runtimeEventSites:normalizeRuntimeEventSites(definition.runtimeEventSites || [])});
    validateRuntimeEventSiteDeclarations(normalized.directiveSignature, normalized.runtimeEventSites);
    if (expected && definitionMetadataKey(expected) !== definitionMetadataKey(normalized))
      throw new Error("loaded definition metadata does not match its prepared declaration");
    const app = definitionRegistry(appId);
    validateDefinitionCallRuns(app, normalized);
    const prior = app.definitions.get(definitionId);
    if (prior && (prior.render !== normalized.render || prior.target !== normalized.target || prior.helperContract !== normalized.helperContract || signatureKey(prior.dynamicElements) !== signatureKey(normalized.dynamicElements) || signatureKey(prior.directiveSignature) !== signatureKey(normalized.directiveSignature)||signatureKey(prior.replacementSites)!==signatureKey(normalized.replacementSites)||signatureKey(prior.localCalls)!==signatureKey(normalized.localCalls)||signatureKey(prior.localCallRuns)!==signatureKey(normalized.localCallRuns)||signatureKey(prior.opaqueHtmlSites)!==signatureKey(normalized.opaqueHtmlSites)||signatureKey(prior.runtimeEventSites)!==signatureKey(normalized.runtimeEventSites))) throw new Error("definition id collision");
    for (const occurrence of app.occurrences.values()) if (occurrence.definitionId === definitionId)
      validateOccurrenceCallRuns(app.occurrences, occurrence, normalized);
    if (!prior) {
      app.definitions.set(definitionId, normalized);
      for (const call of [...normalized.localCalls, ...normalized.localCallRuns])
        app.callRunTags.set(call.componentTag, call.typeKey);
    }
  }

  function attachVueApp(appId, vueApp) {
    const app = definitionRegistry(appId), prior = vueApp.config.errorHandler;
    for (const occurrence of app.occurrences.values()) {
      const definition = app.definitions.get(occurrence.definitionId);
      if (!definition) throw new Error("missing render definition before Vue app attachment");
      validateOccurrenceCallRuns(app.occurrences, occurrence, definition);
    }
    app.vueApp = vueApp;
    vueApp.config.errorHandler = (error, instance, info) => {
      app.terminal = true;
      stopAppPolling(app);
      if (prior) prior(error, instance, info);
      else queueMicrotask(() => { throw error; });
    };
  }

  function attachPreparedHost(appId, host) {
    plain(host, "prepared host");
    if (
      typeof host.onOccurrenceMounted !== "function" ||
      typeof host.onOccurrenceUnmounted !== "function" ||
      typeof host.beforeServerCallbacks !== "function"
    ) throw new TypeError("invalid prepared host");
    const app = definitionRegistry(appId);
    if (app.preparedHost) throw new Error("prepared host is already attached");
    app.preparedHost = Object.freeze({onOccurrenceMounted: host.onOccurrenceMounted, onOccurrenceUnmounted: host.onOccurrenceUnmounted, beforeServerCallbacks: host.beforeServerCallbacks});
  }

  function installServerKey(instance, record, key) {
    if (key.startsWith("$") || key.startsWith("_")) throw new Error("reserved js_data key: " + key);
    Object.defineProperty(instance, key, {enumerable: true, configurable: true,
      get() { return record.live.value?.serverData[key]; },
      set(value) { record.live.value.serverData[key] = value; }});
  }

  function eventDescriptor(record) {
    return record.events.descriptor;
  }

  function requireEventHandler(record, name) {
    const descriptor = eventDescriptor(record);
    if (typeof name !== "string" || !descriptor || !own(descriptor.eventHandlers, name))
      throw new Error("Unknown event handler '" + String(name) + "'.");
    return name;
  }

  function cloneJsonValue(value, label) {
    const ancestors = new Set();
    const copy = item => {
      if (item === null || typeof item === "string" || typeof item === "boolean") return item;
      if (typeof item === "number" && Number.isFinite(item)) return item;
      if (!item || typeof item !== "object") throw new TypeError(label + " must contain only strict JSON");
      const raw = V.toRaw(item);
      if (!Array.isArray(raw) && Object.getPrototypeOf(raw) !== Object.prototype && Object.getPrototypeOf(raw) !== null ||
          ancestors.has(raw) || Object.getOwnPropertySymbols(raw).length)
        throw new TypeError(label + " must contain only strict JSON");
      const names = Object.getOwnPropertyNames(raw);
      if (Array.isArray(raw) && (Object.keys(raw).length !== raw.length ||
          Object.keys(raw).some((key, index) => key !== String(index))))
        throw new TypeError(label + " must contain only dense JSON arrays");
      for (const name of names) {
        if (Array.isArray(raw) && name === "length") continue;
        const descriptor = Object.getOwnPropertyDescriptor(raw, name);
        if (!descriptor?.enumerable || !("value" in descriptor))
          throw new TypeError(label + " must contain only strict JSON");
      }
      ancestors.add(raw);
      const result = Array.isArray(raw) ? [] : {};
      for (const key of Object.keys(raw)) {
        Object.defineProperty(result, key, {
          value: copy(raw[key]), enumerable: true, configurable: true, writable: true,
        });
      }
      ancestors.delete(raw);
      return result;
    };
    return copy(value);
  }
  const cloneStateValue = value => cloneJsonValue(value, "$state values");

  function writableStateFields(descriptor, publicState) {
    return new Set(own(descriptor, "writableStateFields") ? descriptor.writableStateFields : Object.keys(publicState));
  }

  function createStateFacade(record, initialContext) {
    const state = {values: null, pending: null, writable: null, current: true, nestedViews: null, contractEpoch: 0};
    const requireCurrent = key => {
      if (!state.current || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events State source is stale or retired");
      if (typeof key !== "string" || !state.values || !own(state.values, key))
        throw new Error("Unknown $state field '" + String(key) + "'.");
      if (!state.writable.has(key)) throw new Error("$state field '" + key + "' is not client-writable.");
    };
    const nested = value => {
      const existing = state.nestedViews.get(value);
      if (existing) return existing;
      const epoch = state.contractEpoch;
      const proxy = new Proxy(value, {
      get(target, key) {
        if (!state.current || epoch !== state.contractEpoch)
          throw new Error("Citry Events State source is stale or retired");
        const child = Reflect.get(target, key);
        return child && typeof child === "object" ? nested(child) : child;
      },
      getOwnPropertyDescriptor(target, key) {
        const descriptor = Reflect.getOwnPropertyDescriptor(target, key);
        if (!descriptor || !descriptor.configurable || !("value" in descriptor) ||
            !descriptor.value || typeof descriptor.value !== "object") return descriptor;
        return {...descriptor, value: nested(descriptor.value)};
      },
      set() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      deleteProperty() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      defineProperty() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      preventExtensions() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      setPrototypeOf() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      });
      state.nestedViews.set(value, proxy);
      return proxy;
    };
    state.facade = new Proxy(Object.create(null), {
      get(_target, key) {
        if (!state.current) throw new Error("Citry Events State source is stale or retired");
        const value = state.values && own(state.values, key) ? state.values[key] : undefined;
        return value && typeof value === "object" ? nested(value) : value;
      },
      set(_target, key, value) {
        requireCurrent(key);
        const copied = cloneStateValue(value);
        const pending = cloneStateValue(copied);
        state.values[key] = copied;
        state.pending[key] = pending;
        return true;
      },
      deleteProperty() { throw new Error("State fields cannot be deleted through $state."); },
      defineProperty() { throw new Error("State fields cannot be defined through $state."); },
      preventExtensions() { throw new Error("State fields cannot be frozen, sealed, or made non-extensible."); },
      setPrototypeOf() { throw new Error("State prototypes cannot be changed through $state."); },
      has(_target, key) { return Boolean(state.values && own(state.values, key)); },
      ownKeys() { return state.values ? Reflect.ownKeys(state.values) : []; },
      getOwnPropertyDescriptor(_target, key) {
        return state.values && own(state.values, key)
          ? {configurable: true, enumerable: true, writable: true,
            value: state.values[key] && typeof state.values[key] === "object" ? nested(state.values[key]) : state.values[key]}
          : undefined;
      },
    });
    state.adopt = context => {
      if (!context) {
        state.contractEpoch += 1;
        state.values = null; state.pending = null; state.writable = null; state.nestedViews = null;
        return;
      }
      const incoming = context?.publicState || {};
      if (!state.values) {
        state.contractEpoch += 1;
        state.values = V.reactive(Object.assign(Object.create(null), clone(incoming)));
        state.pending = Object.create(null);
        state.nestedViews = new WeakMap();
      }
      state.writable = writableStateFields(context?.descriptor || {writableStateFields: []}, incoming);
      for (const key of Object.keys(state.pending)) if (!state.writable.has(key)) delete state.pending[key];
      for (const key of Object.keys(state.values)) if (!own(incoming, key) && !own(state.pending, key)) delete state.values[key];
      for (const [key, value] of Object.entries(incoming)) if (!own(state.pending, key)) state.values[key] = clone(value);
    };
    state.retire = () => {
      state.current = false; state.contractEpoch += 1;
      state.values = null; state.pending = null; state.writable = null; state.nestedViews = null;
    };
    state.adopt(initialContext);
    return state;
  }

  const controlLifetimes = new WeakMap();
  // Vue-owned native state is private runtime metadata. Keep it out of the
  // DOM so application code cannot accidentally forge ownership by assigning
  // an expando with the same name.
  const vueOwnedNativeProperties = new WeakMap();
  // Uncontrolled native values need a per-element snapshot when Vue patches a
  // surrounding component. The private ownership directive is present on each
  // prepared native control, so this avoids scanning an entire app on every
  // reactive update.
  const nativeControlUpdateSnapshots = new WeakMap();
  const eventTimingLifetimes = new WeakMap();
  const eventTimingDirectives = new WeakMap();
  const runtimeEventTimingDirectives = new WeakMap();
  const MAX_TIMER_DELAY = 2_147_483_647;
  function scheduleDelay(lifetime, milliseconds, callback) {
    let remaining = milliseconds;
    const schedule = () => {
      const chunk = Math.min(remaining, MAX_TIMER_DELAY);
      const started = performance.now();
      lifetime.timer = setTimeout(() => {
        lifetime.timer = 0;
        remaining -= Math.max(0, performance.now() - started);
        if (remaining <= 0) callback();
        else schedule();
      }, chunk);
    };
    schedule();
  }
  function releaseEventTiming(lifetime) {
    if (lifetime.timer) clearTimeout(lifetime.timer);
    lifetime.timer = 0;
    const byBinding = eventTimingLifetimes.get(lifetime.element);
    if (byBinding?.get(lifetime.bindingId) === lifetime) {
      byBinding.delete(lifetime.bindingId);
      if (byBinding.size === 0) eventTimingLifetimes.delete(lifetime.element);
    }
    lifetime.record.eventTimingLifetimes?.delete(lifetime);
    if (lifetime.kind === "poll") {
      const polling = lifetime.record.app.polling;
      polling?.lifetimes.delete(lifetime);
      if (polling?.lifetimes.size === 0) {
        document.removeEventListener("visibilitychange", polling.onVisibility);
        lifetime.record.app.polling = undefined;
      }
    }
  }
  function finishEventTiming(lifetime, value) {
    releaseEventTiming(lifetime);
    lifetime.resolve?.(value);
    lifetime.resolve = undefined;
  }
  function disposeEventTimings(record) {
    const lifetimes = record.eventTimingLifetimes;
    if (!lifetimes || lifetimes.size === 0) return;
    for (const lifetime of lifetimes) finishEventTiming(lifetime, undefined);
  }
  function stopAppPolling(app) {
    const polling = app.polling;
    if (!polling) return;
    for (const lifetime of polling.lifetimes) finishEventTiming(lifetime, undefined);
  }
  function eventTimingLifetime(record, element, bindingId, binding) {
    let byBinding = eventTimingLifetimes.get(element);
    if (!byBinding) {
      byBinding = new Map();
      eventTimingLifetimes.set(element, byBinding);
    }
    let lifetime = byBinding.get(bindingId);
    if (lifetime && (lifetime.record !== record || lifetime.binding !== binding)) {
      finishEventTiming(lifetime, undefined);
      lifetime = undefined;
      byBinding = eventTimingLifetimes.get(element);
      if (!byBinding) {
        byBinding = new Map();
        eventTimingLifetimes.set(element, byBinding);
      }
    }
    if (!lifetime) {
      lifetime = {record, element, bindingId, binding, timer: 0, last: -Infinity, resolve: undefined};
      byBinding.set(bindingId, lifetime);
      (record.eventTimingLifetimes ||= new Set()).add(lifetime);
    }
    return lifetime;
  }
  function disposeElementEventTimings(element, handles) {
    const byBinding = eventTimingLifetimes.get(element);
    if (byBinding) for (const handle of handles || []) {
      const lifetime = byBinding.get(handle.id);
      if (lifetime?.record === handle.record) finishEventTiming(lifetime, undefined);
    }
  }
  const timingDirectiveOwns = (element, record, bindingId, binding) =>
    [eventTimingDirectives.get(element), runtimeEventTimingDirectives.get(element)].some(handles =>
      handles?.some(handle => handle.record === record && handle.id === bindingId && handle.spec === binding),
    );
  const timedBindingIsCurrent = (record, element, bindingId, binding) =>
    record.app.mounted.get(record.occurrenceId)?.record === record && element.isConnected &&
    record.live.value?.preparedData?.eventBindings?.[bindingId] === binding;
  const pollBindingIsCurrent = lifetime =>
    !lifetime.record.app.terminal &&
    apps.get(lifetime.record.app.id) === lifetime.record.app &&
    lifetime.record.app.mounted.get(lifetime.record.occurrenceId)?.record === lifetime.record &&
    lifetime.element.isConnected &&
    eventTimingLifetimes.get(lifetime.element)?.get(lifetime.bindingId) === lifetime &&
    timingDirectiveOwns(lifetime.element, lifetime.record, lifetime.bindingId, lifetime.binding) &&
    lifetime.record.live.value?.preparedData?.pollBindings?.[lifetime.bindingId] === lifetime.binding;
  function reportPollFailure(lifetime, error) {
    const app = lifetime.record.app;
    const mounted = lifetime.record.app.mounted.get(lifetime.record.occurrenceId);
    finishEventTiming(lifetime, undefined);
    stopAppPolling(app);
    app.vueApp.config.errorHandler(error, mounted?.component, "Citry @c-poll");
  }
  function schedulePoll(lifetime) {
    if (lifetime.timer) clearTimeout(lifetime.timer);
    if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
    if (document.hidden) return;
    lifetime.pending = false;
    scheduleDelay(lifetime, lifetime.binding.interval, () => {
      if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
      if (document.hidden) return;
      // A slow request must not create a chain of already-expired timers. If
      // its deadline passes, restart the interval when the request settles.
      if (lifetime.inFlight) { lifetime.pending = true; return; }
      schedulePoll(lifetime);
      let args;
      try {
        args = lifetime.args === undefined ? {} : lifetime.args();
        plain(args, "Citry polling arguments");
        args = cloneJsonValue(args, "Citry polling arguments");
      } catch (error) {
        reportPollFailure(lifetime, error);
        return;
      }
      if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
      lifetime.inFlight = true;
      Promise.resolve().then(() => {
        if (document.hidden) return undefined;
        if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return undefined; }
        return lifetime.record.app.eventPoll(lifetime.record, lifetime.bindingId, args);
      })
        .catch(error => { if (!lifetime.record.app.terminal) reportPollFailure(lifetime, error); })
        .finally(() => {
          lifetime.inFlight = false;
          if (lifetime.pending) schedulePoll(lifetime);
        });
    });
  }
  function registerPoll(element, handle) {
    const lifetime = eventTimingLifetime(handle.record, element, handle.id, handle.spec);
    lifetime.kind = "poll";
    lifetime.args = handle.args;
    lifetime.inFlight = false;
    let polling = handle.record.app.polling;
    if (!polling) {
      polling = {lifetimes: new Set(), onVisibility: undefined};
      polling.onVisibility = () => {
        for (const current of polling.lifetimes) {
          if (document.hidden) {
            if (current.timer) clearTimeout(current.timer);
            current.timer = 0;
          } else schedulePoll(current);
        }
      };
      handle.record.app.polling = polling;
      document.addEventListener("visibilitychange", polling.onVisibility);
    }
    polling.lifetimes.add(lifetime);
    schedulePoll(lifetime);
  }
  const eventTimingSignature = handle => {
    const spec = handle.spec;
    return JSON.stringify([handle.record.occurrenceId, handle.record.generation, handle.id,
      spec.event, spec.handler, spec.args, spec.prevent, spec.stop, spec.self, spec.once,
      spec.key, spec.debounce, spec.throttle]);
  };
  function reconcileEventTimings(element, handles) {
    const prior = eventTimingDirectives.get(element) || [];
    const currentByKey = new Map(handles.map(handle => [handle.kind + ":" + handle.id, handle]));
    for (const old of prior) {
      const current = currentByKey.get(old.kind + ":" + old.id);
      if (current && current.record === old.record &&
          eventTimingSignature(current) === eventTimingSignature(old)) {
        const lifetime = eventTimingLifetimes.get(element)?.get(old.id);
        if (lifetime?.record === old.record && lifetime.binding === old.spec)
          lifetime.binding = current.spec;
        continue;
      }
      disposeElementEventTimings(element, [old]);
    }
    eventTimingDirectives.set(element, handles);
    const byBinding = eventTimingLifetimes.get(element);
    for (const handle of handles) {
      if (handle.kind !== "poll") continue;
      const old = prior.find(candidate => candidate.kind === "poll" && candidate.id === handle.id &&
        candidate.record === handle.record && candidate.spec === handle.spec);
      const lifetime = byBinding?.get(handle.id);
      if (old && lifetime?.record === handle.record && lifetime.binding === handle.spec) lifetime.args = handle.args;
      else registerPoll(element, handle);
    }
  }
  const textualInputTypes = new Set(["text","search","email","url","tel","password","date","datetime-local","month","time","week","color"]);
  const actionInputTypes = new Set(["button","submit","reset","image","file"]);
  function classifyControl(element, spec) {
    const tag = element.tagName.toLowerCase();
    if (tag === "input") {
      const raw = element.getAttribute("type");
      const type = raw == null || raw === "" ? "text" : raw.toLowerCase();
      if (type === "hidden") { if (spec.binding_mode !== "one-way") throw new Error("hidden controls support one-way State bindings only"); }
      else if (!textualInputTypes.has(type) && !["checkbox","radio","number","range"].includes(type))
        throw new Error(actionInputTypes.has(type) ? "action controls cannot be bound to State" : "unrecognized input type");
      if (spec.lazy && ["checkbox","radio"].includes(type)) throw new Error(".lazy has no effect on change controls");
      return {draft:["checkbox","radio"].includes(type)?"change":"input", flush:spec.on || (["checkbox","radio"].includes(type)||spec.lazy?"change":"input")};
    }
    if (tag === "select") { if (spec.lazy) throw new Error(".lazy has no effect on select controls"); return {draft:"change",flush:spec.on||"change"}; }
    if (tag === "textarea") return {draft:"input",flush:spec.on||(spec.lazy?"change":"input")};
    if (tag.includes("-")) {
      if (spec.binding_mode === "two-way" && !spec.on) throw new Error("two-way custom controls require .on:<event>");
      if (!customElements.get(tag)) return null;
      if (!("value" in element)) throw new Error("custom control has no value property");
      return {draft:spec.on,flush:spec.on};
    }
    throw new Error("element holds no value to bind");
  }
  function controlSignature(element, handles) {
    const tag = element.tagName.toLowerCase();
    const shape = tag === "input" ? element.getAttribute("type") || "text"
      : tag === "select" ? String(element.multiple) : tag;
    return shape + ":" + handles.map(handle => JSON.stringify(handle.spec)).join("|");
  }
  function controlEventName(element, spec) {
    if (spec.on) return spec.on;
    if (spec.lazy) return "change";
    const tag = element.tagName.toLowerCase();
    if (tag === "select" || tag === "input" && ["checkbox", "radio"].includes(element.type)) return "change";
    return "input";
  }
  function controlRead(element) {
    const tag = element.tagName.toLowerCase();
    if (tag === "select" && element.multiple)
      return [...element.selectedOptions].map(option => option.value);
    if (tag === "input" && element.type === "checkbox") return element.checked;
    if (tag === "input" && element.type === "radio") return element.checked;
    if (tag === "input" && ["number","range"].includes(element.type))
      return Number.isFinite(element.valueAsNumber) ? element.valueAsNumber : element.value;
    return element.value;
  }
  function controlWrite(element, value) {
    const tag = element.tagName.toLowerCase();
    const lifetime = controlLifetimes.get(element);
    if (lifetime) lifetime.writing = true;
    try {
    if (tag.includes("-")) { element.value = value; return; }
    if (tag === "input" && ["checkbox","radio"].includes(element.type)) {
      if (typeof value !== "boolean") throw new TypeError("checkbox and radio State values must be boolean");
      element.checked = value; return;
    }
    if (tag === "select" && element.multiple) {
      const selected = new Set(Array.isArray(value) && value.every(item => typeof item === "string") ? value : []);
      for (const option of element.options) option.selected = selected.has(option.value);
      return;
    }
    element.value = value == null ? "" : value;
    } finally { if (lifetime) lifetime.writing = false; }
  }
  function applyControlValue(element, value) {
    try { controlWrite(element, value); return true; }
    catch (error) { console.error("[Citry] could not apply State value to control:", error); return false; }
  }
  const controlReadFailures = new WeakMap();
  function adoptControlValue(element, record, field) {
    try {
      const value = controlRead(element);
      if (value === undefined) throw new TypeError("control value is unavailable");
      record.state.facade[field] = value;
      controlReadFailures.get(element)?.delete(field);
      return true;
    } catch (error) {
      let fields = controlReadFailures.get(element);
      if (!fields) { fields = new Set(); controlReadFailures.set(element, fields); }
      if (!fields.has(field)) {
        fields.add(field);
        console.error("[Citry] could not adopt control value into State:", error);
      }
      return false;
    }
  }
  function disposeControl(element) {
    const aggregate = controlLifetimes.get(element);
    if (!aggregate) return;
    aggregate.active = false;
    for (const token of aggregate.pending) { token.element = null; token.handles = null; token.aggregate = null; }
    aggregate.pending.clear();
    for (const lifetime of aggregate.children) {
      if (lifetime.listener) element.removeEventListener(lifetime.event, lifetime.listener);
      if (lifetime.draftListener) element.removeEventListener(lifetime.draftEvent, lifetime.draftListener);
      if (lifetime.timer) clearTimeout(lifetime.timer);
    }
    controlLifetimes.delete(element);
  }
  function installControl(element, handle, aggregate) {
    if (!handle || !handle.record || !handle.spec) throw new Error("Citry control binding is missing or stale");
    const {record, spec} = handle;
    let classification;
    try { classification = classifyControl(element, spec); }
    catch (error) { console.error("[Citry] invalid State control binding:", error); return; }
    if (classification === null) {
      const name = element.tagName.toLowerCase();
      const token = {element, handles:aggregate.handles, aggregate};
      aggregate.pending.add(token);
      customElements.whenDefined(name).then(() => {
        const target = token.element, handles = token.handles, owner = token.aggregate;
        token.element = null; token.handles = null; token.aggregate = null; owner?.pending.delete(token);
        if (target && handles && owner?.active && controlLifetimes.get(target) === owner && target.isConnected)
          installControls(target, handles);
      }, error => console.error("[Citry] custom control definition failed:", error));
      return;
    }
    const field = spec.field;
    applyControlValue(element, record.state.facade[field]);
    if (spec.binding_mode === "one-way") return;
    const event = classification.flush;
    const lifetime = {event, draftEvent:classification.draft, timer: 0, last: -Infinity, listener: null, draftListener:null, handle};
    aggregate.children.push(lifetime);
    const send = () => { void record.app.eventSend(record, spec.handler, {}).catch(() => {}); };
    const listener = domEvent => {
      if (aggregate.writing) return;
      if (spec.key && String(domEvent.key || "").toLowerCase() !== spec.key) return;
      if (!adoptControlValue(element, record, field)) return;
      if (spec.throttle !== null) {
        const now = performance.now();
        if (now - lifetime.last < spec.throttle) return;
        lifetime.last = now;
      }
      if (spec.debounce !== null) {
        if (lifetime.timer) clearTimeout(lifetime.timer);
        scheduleDelay(lifetime, spec.debounce, () => send());
      } else send();
    };
    lifetime.listener = listener;
    element.addEventListener(event, listener);
    if (classification.draft && classification.draft !== event) {
      lifetime.draftListener = () => {
        adoptControlValue(element, record, field);
      };
      element.addEventListener(classification.draft, lifetime.draftListener);
    }
  }
  function installControls(element, handles) {
    disposeControl(element);
    if (!Array.isArray(handles) || handles.length === 0) throw new Error("Citry control bindings are missing or stale");
    const aggregate = {handles,children:[],active:true,writing:false,signature:controlSignature(element, handles),pending:new Set()};
    controlLifetimes.set(element, aggregate);
    for (const handle of handles) installControl(element, handle, aggregate);
  }

  function setVueOwnedNativeProperties(element, value) {
    const values = Array.isArray(value) ? value : [value];
    const properties = values.filter(property =>
      property === "value" || property === "checked" || property === "selected");
    if (properties.length === 0) {
      vueOwnedNativeProperties.delete(element);
      return;
    }
    vueOwnedNativeProperties.set(element, Object.freeze([...new Set(properties)]));
  }

  function createEventActivity(record, descriptor = null) {
    const view = V.reactive({
      total: 0,
      loading: Object.create(null),
      errors: Object.create(null),
      errorOrder: Object.create(null),
      nextStarted: 0,
      nextError: 0,
    });
    const activity = {
      descriptor,
      view,
      listeners: new Map(),
      loading(name) {
        if (name === undefined) return view.total > 0;
        return (view.loading[requireEventHandler(record, name)] ?? 0) > 0;
      },
      error(name) {
        if (name !== undefined) return view.errors[requireEventHandler(record, name)] || null;
        let selected = null, selectedOrder = -1;
        for (const [handler, error] of Object.entries(view.errors)) {
          const order = view.errorOrder[handler] ?? 0;
          if (order > selectedOrder) { selected = error; selectedOrder = order; }
        }
        return selected;
      },
      enqueue(handler) {
        requireEventHandler(record, handler);
        view.total += 1;
        view.loading[handler] = (view.loading[handler] ?? 0) + 1;
        return {handler, started: 0};
      },
      start(intent) {
        intent.started = ++view.nextStarted;
        activity.latestStarted[intent.handler] = intent.started;
      },
      succeed(intent) {
        if (activity.latestStarted[intent.handler] !== intent.started) return;
        delete view.errors[intent.handler];
        delete view.errorOrder[intent.handler];
      },
      fail(intent, error) {
        if (activity.latestStarted[intent.handler] !== intent.started) return;
        view.errors[intent.handler] = detached(error);
        view.errorOrder[intent.handler] = ++view.nextError;
      },
      finish(intent) {
        view.total = Math.max(0, view.total - 1);
        const count = (view.loading[intent.handler] ?? 0) - 1;
        if (count > 0) view.loading[intent.handler] = count;
        else delete view.loading[intent.handler];
      },
      subscribe(name, callback) {
        if (typeof name !== "string" || name.length === 0) throw new TypeError("$onEvent needs a non-empty event name");
        if (typeof callback !== "function") throw new TypeError("$onEvent needs a callback function");
        const listeners = activity.listeners.get(name) || new Set();
        listeners.add(callback);
        activity.listeners.set(name, listeners);
        let active = true;
        return () => {
          if (!active) return;
          active = false;
          listeners.delete(callback);
          if (!listeners.size) activity.listeners.delete(name);
        };
      },
      dispatch(name, detail) {
        const listeners = activity.listeners.get(name);
        if (!listeners) return;
        for (const callback of [...listeners]) {
          try { callback(detail); }
          catch (error) { queueMicrotask(() => { throw error; }); }
        }
      },
      dispose() {
        activity.listeners.clear();
      },
      latestStarted: Object.create(null),
    };
    return activity;
  }

  function typeOptions(appId, typeKey, userOptions) {
    userOptions = userOptions || {};
    if (userOptions.mixins || userOptions.extends) throw new Error("mixins and extends are unsupported by the js_data collision proof");
    const callback = userOptions.onServerRender;
    const userData = userOptions.data;
    const userSetup = userOptions.setup;
    const userBeforeCreate = userOptions.beforeCreate;
    const userCreated = userOptions.created;
    const userMounted = userOptions.mounted;
    const userBeforeUnmount = userOptions.beforeUnmount;
    const props = Array.isArray(userOptions.props) ? [...userOptions.props, "citryId"] : {...(userOptions.props || {}), citryId: {type: String, required: true}};
    const injectIsObject = userOptions.inject !== null && typeof userOptions.inject === "object" &&
      Object.getPrototypeOf(userOptions.inject) === Object.prototype;
    const injectedKeys = Array.isArray(userOptions.inject) ? userOptions.inject : injectIsObject ? Object.keys(userOptions.inject) : [];
    if (userOptions.inject !== undefined && (!Array.isArray(userOptions.inject) && !injectIsObject ||
        injectedKeys.some(key => typeof key !== "string")))
      throw new TypeError("inject must be a Vue array or plain object with string local names");
    const pluginContextNames = definitionRegistry(appId).templateContextNames;
    const propsKeys = Array.isArray(userOptions.props) ? userOptions.props : Object.keys(userOptions.props || {});
    const eventPublicNames = ["$loading", "$error", "$state", "$sendEvent", "$onEvent"];
    for (const name of eventPublicNames) if (propsKeys.includes(name) || injectedKeys.includes(name) ||
        own(userOptions.methods || {}, name) || own(userOptions.computed || {}, name))
      throw new Error("reserved Events public name collision: " + name);
    for (const name of pluginContextNames) {
      if (propsKeys.includes(name) || injectedKeys.includes(name) || own(userOptions.methods || {}, name) ||
          own(userOptions.computed || {}, name)) throw new Error("browser plugin template context collision: " + name);
    }
    const reservedOptionKeys = new Set([
      ...Object.keys(userOptions.methods || {}), ...Object.keys(userOptions.computed || {}), ...injectedKeys,
      ...pluginContextNames,
    ]);
    const reservedPublicNames = new Set(["preparedData", "$citryEvents", ...eventPublicNames, ...pluginContextNames]);
    const options = {...userOptions, name: userOptions.name || "CitryStable_" + typeKey, props};
    delete options.onServerRender;
    options.data = function () {
      const app = definitionRegistry(appId), occurrence = app.occurrences.get(this.citryId);
      if (!occurrence || occurrence.typeKey !== typeKey) throw new Error("unknown or wrong-type occurrence");
      const value = userData ? userData.call(this) : {};
      plain(value, "data() result");
      for (const key of Object.keys(value)) if (reservedPublicNames.has(key))
        throw new Error("reserved public data() collision: " + key);
      for (const key of Object.keys(occurrence.serverData)) if (own(value, key) || reservedOptionKeys.has(key)) throw new Error("js_data/local collision: " + key);
      return value;
    };
    if (userSetup) options.setup = function (props, context) {
      const value = userSetup(props, context);
      if (value === undefined) return undefined;
      if (typeof value === "function" || value instanceof Promise)
        throw new TypeError("setup must synchronously return a plain bindings object or undefined");
      plain(value, "setup() result");
      for (const key of Object.keys(value)) if (reservedPublicNames.has(key))
        throw new Error("reserved public setup() collision: " + key);
      return value;
    };
    options.beforeCreate = function () {
      const app = definitionRegistry(appId), occurrence = app.occurrences.get(this.citryId);
      if (!occurrence || occurrence.typeKey !== typeKey || app.mounted.has(occurrence.id)) throw new Error("invalid mounted occurrence");
      const generation = ++app.nextMountGeneration;
      const initialLive = app.snapshot.value.get(occurrence.id);
      const record = {app, occurrenceId: occurrence.id, parentId: occurrence.parentId, generation, live: V.shallowRef(initialLive), serverKeys: new Set(Object.keys(occurrence.serverData)), definition: V.shallowRef({id: occurrence.definitionId, render: null, cache: []}), callbackScope: undefined, callbackCleanup: undefined, callbackSubscriptions: undefined, applying: false, failed: false, events: null, state: null, controlHandles: new Map()};
      record.events = createEventActivity(record, occurrence.eventContext?.descriptor || null);
      record.state = createStateFacade(record, occurrence.eventContext);
      instanceRecords.set(this, record);
      const currentInstance = V.getCurrentInstance?.();
      if (currentInstance?.proxy) instanceRecords.set(currentInstance.proxy, record);
      if (currentInstance?.ctx) instanceRecords.set(currentInstance.ctx, record);
      for (const key of record.serverKeys) {
        if (reservedOptionKeys.has(key) || key in this) throw new Error("js_data/public instance collision: " + key);
        installServerKey(this, record, key);
      }
      if (reservedOptionKeys.has("preparedData") || "preparedData" in this) throw new Error("preparedData/public instance collision");
      Object.defineProperty(this, "preparedData", {enumerable: true, configurable: true, get() { return record.live.value?.preparedData || {}; }});
      Object.defineProperty(this, "$loading", {enumerable: false, configurable: true, value: record.events.loading});
      Object.defineProperty(this, "$error", {enumerable: false, configurable: true, value: record.events.error});
      Object.defineProperty(this, "$state", {enumerable: false, configurable: true, value: record.state.facade});
      Object.defineProperty(this, "$sendEvent", {enumerable: false, configurable: true, value: (name, args, opts) => {
        requireEventHandler(record, name);
        return record.app.eventSend(record, name, args, opts);
      }});
      Object.defineProperty(this, "$onEvent", {enumerable: false, configurable: true, value: (name, callback) => {
        if (!record.events?.descriptor)
          throw new Error("this component declares no Events class; $onEvent needs a component Events declaration");
        if (!record.events?.subscribe) throw new Error("Citry Events subscriptions are unavailable");
        return subscribeRecordEvent(record, name, callback);
      }});
      if (reservedOptionKeys.has("$citryEvents") || "$citryEvents" in this) throw new Error("$citryEvents/public instance collision");
      Object.defineProperty(this, "$citryEvents", {enumerable: false, configurable: true, value: Object.freeze({
        dispatch(bindingId, event, authoredArgs) {
          if (typeof record.app.eventDispatch !== "function") throw new Error("Citry Events bridge is unavailable");
          return record.app.eventDispatch(record, bindingId, event, authoredArgs);
        },
        dispatchComponent(bindingId, emittedValue, authoredArgs) {
          if (typeof record.app.eventDispatchComponent !== "function")
            throw new Error("Citry Events bridge is unavailable");
          return record.app.eventDispatchComponent(record, bindingId, emittedValue, authoredArgs);
        },
        componentRoot(childId) {
          if (typeof record.app.componentRoot !== "function")
            throw new Error("Citry Events component-root bridge is unavailable");
          return record.app.componentRoot(record, childId);
        },
        controls(bindingIds) {
          if (bindingIds === "") return Object.freeze([]);
          if (typeof bindingIds !== "string") throw new TypeError("Citry control binding ids must be a string");
          const bindings = record.live.value?.preparedData?.controlBindings;
          const ids = bindingIds.split(",");
          const specs = ids.map(id => bindings && bindings[id]);
          if (specs.some(spec => !spec)) throw new Error("Citry control binding is missing or stale");
          const prior = record.controlHandles.get(bindingIds);
          if (prior && prior.every((handle, index) => handle.spec === specs[index])) return prior;
          const handles = Object.freeze(specs.map(spec => Object.freeze({record, spec})));
          record.controlHandles.set(bindingIds, handles);
          return handles;
        },
        runtimeEvents(bindingIds) {
          if (bindingIds === "") return Object.freeze([]);
          if (typeof bindingIds !== "string") throw new TypeError("Citry runtime event binding ids must be a string");
          const ids = bindingIds.split(",");
          if (new Set(ids).size !== ids.length) throw new Error("Citry runtime event binding ids are duplicated");
          const eventBindings = record.live.value?.preparedData?.eventBindings;
          const pollBindings = record.live.value?.preparedData?.pollBindings;
          const resolved = ids.map(id => {
            if (/^citryRuntimeEvent[0-9a-f]+$/.test(id)) {
              const spec = eventBindings && eventBindings[id];
              validateRuntimeEventSpec(id, spec, {eventContext:{descriptor:record.events.descriptor}});
              return {kind:"event", spec};
            }
            if (/^citryRuntimePoll[0-9a-f]+$/.test(id)) {
              const spec = pollBindings && pollBindings[id];
              validateRuntimePollSpec(id, spec, {eventContext:{descriptor:record.events.descriptor}});
              return {kind:"poll", spec};
            }
            throw new Error("Citry runtime binding id has an invalid kind");
          });
          return Object.freeze(ids.map((id, index) => Object.freeze({
            kind: resolved[index].kind,
            record,
            id,
            spec: resolved[index].spec,
            args: undefined,
          })));
        },
        timings(bindingIds, pollEntries) {
          if (typeof bindingIds !== "string") throw new TypeError("Citry event timing ids must be a string");
          if (pollEntries !== undefined && !Array.isArray(pollEntries))
            throw new TypeError("Citry poll timing entries must be an array");
          if (bindingIds === "" && (pollEntries === undefined || pollEntries.length === 0))
            throw new TypeError("Citry timing requires an event or poll binding");
          const bindings = record.live.value?.preparedData?.eventBindings;
          const ids = bindingIds === "" ? [] : bindingIds.split(",");
          if (new Set(ids).size !== ids.length) throw new Error("Citry event timing ids are duplicated");
          const specs = ids.map(id => bindings && bindings[id]);
          if (specs.some(spec => !spec || spec.debounce === null && spec.throttle === null))
            throw new Error("Citry event timing binding is missing, stale, or untimed");
          const prior = record.eventTimingHandles?.get(bindingIds);
          const eventHandles = prior && prior.every((handle, index) => handle.spec === specs[index])
            ? prior
            : Object.freeze(ids.map((id, index) => Object.freeze({kind:"event", record, id, spec: specs[index]})));
          if (eventHandles !== prior) (record.eventTimingHandles ||= new Map()).set(bindingIds, eventHandles);
          if (pollEntries === undefined || pollEntries.length === 0) return eventHandles;
          const polls = record.live.value?.preparedData?.pollBindings;
          const seenPolls = new Set();
          const pollHandles = pollEntries.map(entry => {
            plain(entry, "Citry poll timing entry");
            if (Object.keys(entry).sort().join(",") !== "args,id" || typeof entry.id !== "string" ||
                !/^citryPoll[0-9a-f]+$/.test(entry.id) ||
                entry.args !== undefined && typeof entry.args !== "function" || seenPolls.has(entry.id))
              throw new TypeError("Citry poll timing entry is invalid or duplicated");
            seenPolls.add(entry.id);
            const spec = polls && polls[entry.id];
            if (!spec || Object.keys(spec).sort().join(",") !== "args,handler,id,interval" ||
                spec.id !== entry.id || typeof spec.handler !== "string" || spec.handler === "" ||
                spec.args !== null && typeof spec.args !== "string" ||
                !Number.isSafeInteger(spec.interval) || spec.interval <= 0)
              throw new Error("Citry poll timing binding is missing, stale, or invalid");
            return Object.freeze({kind:"poll", record, id:entry.id, spec, args:entry.args});
          });
          return pollHandles.length === 0 ? eventHandles : Object.freeze([...eventHandles, ...pollHandles]);
        },
      })});
      if (userBeforeCreate) userBeforeCreate.call(this);
    };
    options.created = function () {
      const record = instanceRecords.get(this), definition = record.app.definitions.get(record.definition.value.id);
      if (!definition) throw new Error("missing initial render definition: " + record.definition.value.id);
      record.definition.value = {id: record.definition.value.id, render: definition.render, cache: []};
      record.app.mounted.set(record.occurrenceId, {component: this, record});
      if (userCreated) userCreated.call(this);
    };
    options.render = function (...args) {
      const record = instanceRecords.get(this), definition = record.definition.value;
      if (!definition.render) throw new Error("render definition is unavailable");
      args[1] = definition.cache;
      return definition.render.apply(this, args);
    };
    options.mounted = function () {
      const record = instanceRecords.get(this);
      if (userMounted) userMounted.call(this);
      const transaction = record.app.transaction;
      if (transaction) {
        const generations = transaction.newMounts.get(record.occurrenceId) || [];
        generations.push(record.generation);
        transaction.newMounts.set(record.occurrenceId, generations);
      } else {
        const occurrence = record.app.occurrences.get(record.occurrenceId);
        const mounted = {stableId: record.occurrenceId, generation: record.generation, occurrence};
        const task = Promise.resolve(record.app.preparedHost?.onOccurrenceMounted(mounted))
          .then(() => runCallback(this, record, callback, record.app.revision))
          .catch(error => {
            record.app.terminal = true;
            record.app.initialError = error;
          })
          .finally(() => {
            record.app.initialTasks.delete(task);
          });
        record.app.initialTasks.add(task);
      }
    };
    options.beforeUnmount = function () {
      const record = instanceRecords.get(this);
      let error;
      if (record) {
        record.state.retire();
        try { dispose(record); }
        catch (caught) { error = caught; }
        finally {
          try {
            const transaction = record.app.transaction;
            const acceptedTransaction = transaction?.acceptedRetirementIds.has(record.occurrenceId) &&
              transaction.oldAcceptedRecords.get(record.occurrenceId)?.record === record
              ? transaction.acceptedTransaction : undefined;
            record.app.preparedHost?.onOccurrenceUnmounted({
              stableId: record.occurrenceId,
              generation: record.generation,
              acceptedTransaction,
            });
          } catch (caught) {
            if (error === undefined) error = caught;
            else console.error("[Citry] occurrence unmount failed:", caught);
          }
          if (record.app.mounted.get(record.occurrenceId)?.record === record) record.app.mounted.delete(record.occurrenceId);
          instanceRecords.delete(this);
        }
      }
      try { if (userBeforeUnmount) userBeforeUnmount.call(this); }
      catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] beforeUnmount failed:", caught); }
      if (error !== undefined) throw error;
    };
    return options;
  }

  function defineType(appId, typeKey, userOptions) {
    const app = definitionRegistry(appId);
    if (typeof typeKey !== "string" || app.types.has(typeKey)) throw new Error("invalid or duplicate stable type");
    if (userOptions === undefined) userOptions = registeredTypeOptions.get(typeKey)?.options || {};
    const options = V.defineComponent(typeOptions(appId, typeKey, userOptions));
    app.types.set(typeKey, options);
    return options;
  }

  function registerTypeOptions(typeKey, sourceHash, options) {
    if (typeof typeKey !== "string" || typeof sourceHash !== "string" || !/^[0-9a-f]{64}$/.test(sourceHash))
      throw new Error("invalid Vue type options identity");
    if (typeof options === "function") options = {onServerRender: options};
    plain(options, "Vue type options");
    const prior = registeredTypeOptions.get(typeKey);
    if (prior) {
      if (prior.sourceHash !== sourceHash) throw new Error("Vue type options identity collision");
      return;
    }
    registeredTypeOptions.set(typeKey, Object.freeze({options, sourceHash}));
  }

  const loadedDefinitionUrls = new Map();
  const loadedScriptUrls = new Map();
  const loadedStyleUrls = new Map();
  function sriFromHex(value) {
    if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) throw new Error("invalid definition digest");
    return "sha256-" + btoa(String.fromCharCode(...value.match(/../g).map(part => parseInt(part, 16))));
  }
  function canApplyOwnedIntegrity() {
    // A sandboxed iframe without allow-same-origin has an opaque origin.  Its
    // requests are cross-origin even when the URL points back to the hosting
    // site, so browsers require CORS before they can validate SRI.  Explicit
    // integrity supplied for an external asset is retained below.
    return global.origin !== "null";
  }
  function loadDefinition(asset, nonce) {
    if (global.CitryStableDefinitions?.[asset.id]) return Promise.resolve();
    const prior = loadedDefinitionUrls.get(asset.url);
    if (prior) return prior;
    const promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = asset.url;
      if (canApplyOwnedIntegrity()) script.integrity = sriFromHex(asset.sha256);
      if (nonce) script.nonce = nonce;
      const finish = callback => {
        script.onload = null;
        script.onerror = null;
        script.remove();
        callback();
      };
      script.onload = () => finish(() => resolve());
      script.onerror = () => finish(() => {
        loadedDefinitionUrls.delete(asset.url);
        reject(new Error("Citry Vue definition failed to load: " + asset.url));
      });
      document.head.append(script);
    });
    loadedDefinitionUrls.set(asset.url, promise);
    return promise;
  }
  function normalizeStyleAsset(asset, occurrenceTypes) {
    plain(asset, "prepared style asset");
    if (Object.keys(asset).sort().join(",") !== "lazyAllowed,owner,source" ||
        typeof asset.lazyAllowed !== "boolean")
      throw new Error("invalid prepared style asset");
    plain(asset.owner, "prepared style owner"); plain(asset.source, "prepared style source");
    if (asset.owner.kind === "component") {
      if (Object.keys(asset.owner).sort().join(",") !== "kind,occurrenceIds,typeKey" ||
          typeof asset.owner.typeKey !== "string" || !Array.isArray(asset.owner.occurrenceIds) ||
          !asset.owner.occurrenceIds.length || asset.owner.occurrenceIds.some(id => typeof id !== "string" ||
            (occurrenceTypes && occurrenceTypes.get(id) !== asset.owner.typeKey)) ||
          new Set(asset.owner.occurrenceIds).size !== asset.owner.occurrenceIds.length ||
          [...asset.owner.occurrenceIds].sort().some((id, index) => id !== asset.owner.occurrenceIds[index]))
        throw new Error("invalid prepared style asset");
    } else if (asset.owner.kind !== "extension" || Object.keys(asset.owner).sort().join(",") !== "extensionName,kind" ||
        typeof asset.owner.extensionName !== "string") throw new Error("invalid prepared style asset");
    normalizeAssetSource(asset.source, "style");
    return asset;
  }
  function normalizeScriptAsset(asset) {
    plain(asset, "prepared script asset");
    if (Object.keys(asset).sort().join(",") !== "lazyAllowed,owner,registersOptions,source" ||
        typeof asset.lazyAllowed !== "boolean" || typeof asset.registersOptions !== "boolean")
      throw new Error("invalid prepared script asset");
    plain(asset.owner, "prepared script owner");
    if (asset.owner.kind === "component") {
      if (Object.keys(asset.owner).sort().join(",") !== "kind,typeKey" || typeof asset.owner.typeKey !== "string")
        throw new Error("invalid prepared script asset");
    } else if (asset.owner.kind !== "extension" || Object.keys(asset.owner).sort().join(",") !== "extensionName,kind" ||
        typeof asset.owner.extensionName !== "string" || asset.registersOptions)
      throw new Error("invalid prepared script asset");
    normalizeAssetSource(asset.source, "script");
    return asset;
  }
  function normalizeAssetSource(source, elementKind) {
    if (source.kind === "owned") {
      if (typeof source.url !== "string" || typeof source.sha256 !== "string" ||
          !["kind,sha256,url", "attrs,kind,sha256,url"].includes(Object.keys(source).sort().join(",")))
        throw new Error("invalid prepared asset source");
      sriFromHex(source.sha256);
    } else if (source.kind === "external") {
      if (Object.keys(source).sort().join(",") !== "attrs,kind,url" || typeof source.url !== "string" || !plain(source.attrs, "prepared external asset attrs"))
        throw new Error("invalid prepared asset source");
    } else throw new Error("invalid prepared asset source");
    const attrs = source.attrs || {};
    const forbidden = elementKind === "script"
      ? new Set(["src", "nonce", "async", "defer", "nomodule"])
      : new Set(["href", "nonce"]);
    if (Object.entries(attrs).some(([name, value]) => typeof name !== "string" || !name ||
        (typeof value !== "string" && typeof value !== "boolean") || forbidden.has(name.toLowerCase())) ||
        (attrs.integrity !== undefined && (typeof attrs.integrity !== "string" || !validIntegrity(attrs.integrity))))
      throw new Error("invalid prepared asset source attributes");
    const aliases = name => Object.keys(attrs).filter(key => key.toLowerCase() === name);
    if (elementKind === "script") {
      const types = aliases("type");
      const classicTypes = new Set(["text/javascript", "application/javascript", "application/ecmascript",
        "application/x-ecmascript", "application/x-javascript", "text/ecmascript", "text/javascript1.0",
        "text/javascript1.1", "text/javascript1.2", "text/javascript1.3", "text/javascript1.4",
        "text/javascript1.5", "text/jscript", "text/livescript", "text/x-ecmascript", "text/x-javascript"]);
      if (types.length > 1 || types.length === 1 && (typeof attrs[types[0]] !== "string" ||
          !classicTypes.has(attrs[types[0]].trim().toLowerCase().split(";", 1)[0].trimEnd())))
        throw new Error("prepared scripts must use one classic JavaScript MIME type");
    } else {
      const rels = aliases("rel");
      if (rels.length > 1 || rels.length === 1 && (rels[0] !== "rel" || attrs.rel !== "stylesheet"))
        throw new Error("prepared stylesheets must retain canonical rel metadata");
    }
    return source;
  }
  function validIntegrity(value) {
    const tokens = value.trim().split(/\s+/).filter(Boolean), lengths = {sha256: 32, sha384: 48, sha512: 64};
    if (!tokens.length) return false;
    return tokens.every(token => {
      const separator = token.indexOf("-"), algorithm = token.slice(0, separator), encoded = token.slice(separator + 1);
      if (separator < 1 || !(algorithm in lengths) || !encoded || encoded.includes("?")) return false;
      const normalized = encoded.replaceAll("-", "+").replaceAll("_", "/");
      const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
      try {
        const decoded = atob(padded);
        if (decoded.length !== lengths[algorithm]) return false;
        const canonical = btoa(decoded), urlsafe = canonical.replaceAll("+", "-").replaceAll("/", "_");
        return [canonical, canonical.replace(/=+$/, ""), urlsafe, urlsafe.replace(/=+$/, "")].includes(encoded);
      } catch { return false; }
    });
  }
  function assetIdentity(asset) {
    const source = asset.source;
    return JSON.stringify([source.kind, source.url, source.sha256 || null, Object.entries(source.attrs || {}).sort()]);
  }
  function assetRefs(asset) {
    return asset.owner.kind === "component" ? new Set(asset.owner.occurrenceIds) : new Set(["extension:" + asset.owner.extensionName]);
  }
  function applyAssetSource(element, source, nonce) {
    const attrs = source.attrs || {};
    for (const [name, value] of Object.entries(attrs)) {
      if (name.toLowerCase() === "nonce") throw new Error("prepared assets cannot replace the bootstrap nonce");
      if (value === true) element.setAttribute(name, ""); else if (value !== false) element.setAttribute(name, value);
    }
    if (source.kind === "owned" && canApplyOwnedIntegrity() &&
        !Object.keys(attrs).some(name => name.toLowerCase() === "integrity"))
      element.integrity = sriFromHex(source.sha256);
    if (nonce) element.nonce = nonce;
  }
  function styleRecordKey(appId, url) {
    return JSON.stringify([appId, url]);
  }
  function scriptRecordKey(appId, asset) {
    return asset.owner.kind === "extension" ? JSON.stringify([appId, asset.source.url]) : asset.source.url;
  }
  function existingStyleElement(appId, url) {
    return [...document.querySelectorAll('[data-citry-vue-style-app][data-citry-css-url]')]
      .find(element => element.getAttribute("data-citry-vue-style-app") === appId &&
        element.getAttribute("data-citry-css-url") === url) || null;
  }
  function retireUnusedStyles() {
    for (const [key, record] of loadedStyleUrls) if (!record.refs.size && !record.stages.size) {
      record.element?.remove();
      loadedStyleUrls.delete(key);
    }
  }
  function abortStyleStage(stage) {
    if (!stage) return;
    for (const record of loadedStyleUrls.values()) record.stages.delete(stage.token);
    retireUnusedStyles();
  }
  function commitStyleStage(appId, stage) {
    for (const record of loadedStyleUrls.values()) {
      const prior = record.refs.get(appId);
      if (prior) {
        for (const id of stage.replacedIds) prior.delete(id);
        if (!prior.size) record.refs.delete(appId);
      }
      record.stages.delete(stage.token);
    }
    for (const [url, ids] of stage.refs) {
      const record = loadedStyleUrls.get(styleRecordKey(appId, url));
      if (!record) throw new Error("prepared stylesheet disappeared before commit");
      const refs = record.refs.get(appId) || new Set();
      for (const id of ids) refs.add(id);
      record.refs.set(appId, refs);
    }
    retireUnusedStyles();
  }
  function releaseAppStyles(appId) {
    for (const record of loadedStyleUrls.values()) record.refs.delete(appId);
    retireUnusedStyles();
  }
  function releaseAppScripts(appId) {
    for (const [key, record] of loadedScriptUrls) {
      if (record.appId === appId) loadedScriptUrls.delete(key);
    }
  }
  function loadStyle(appId, asset, nonce, stage, knownInitial = false) {
    const key = styleRecordKey(appId, asset.source.url);
    const prior = loadedStyleUrls.get(key);
    if (prior) {
      if (prior.identity !== assetIdentity(asset))
        throw new Error("prepared stylesheet URL identity collision");
      if (stage) prior.stages.add(stage.token);
      return prior.promise;
    }
    if (!knownInitial && !asset.lazyAllowed)
      throw new Error("lazy stylesheet loading is unsupported after custom dependency hooks");
    const link = document.createElement("link");
    const record = {element: link, refs: new Map(), stages: new Set(stage ? [stage.token] : []),
      identity: assetIdentity(asset)};
    record.promise = new Promise((resolve, reject) => {
      link.rel = "stylesheet";
      link.href = asset.source.url;
      link.setAttribute("data-citry-vue-style-app", appId);
      link.setAttribute("data-citry-css-url", asset.source.url);
      applyAssetSource(link, asset.source, nonce);
      link.onload = resolve;
      link.onerror = () => {
        reject(new Error("Citry Vue stylesheet failed to load: " + asset.source.url));
        if (loadedStyleUrls.get(key) === record) {
          loadedStyleUrls.delete(key);
          link.remove();
        }
      };
      document.head.append(link);
    });
    loadedStyleUrls.set(key, record);
    return record.promise;
  }
  function loadTypeScript(appId, asset, nonce, knownInitial = false) {
    normalizeScriptAsset(asset);
    const key = scriptRecordKey(appId, asset), prior = loadedScriptUrls.get(key);
    const identity = assetIdentity(asset);
    if (prior) {
      if (prior.identity !== identity) throw new Error("prepared script URL identity collision");
      return prior.promise;
    }
    if (!knownInitial && !asset.lazyAllowed)
      throw new Error("lazy type script loading is unsupported after custom dependency hooks");
    const record = {appId: asset.owner.kind === "extension" ? appId : null, identity, promise: null};
    record.promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = asset.source.url;
      applyAssetSource(script, asset.source, nonce);
      const finish = callback => {
        script.onload = null;
        script.onerror = null;
        script.remove();
        callback();
      };
      script.onload = () => finish(() => {
        if (asset.registersOptions && (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey))) {
          if (loadedScriptUrls.get(key) === record) loadedScriptUrls.delete(key);
          reject(new Error("Citry Vue type script did not register its declared Options"));
        } else resolve();
      });
      script.onerror = () => finish(() => {
        if (loadedScriptUrls.get(key) === record) loadedScriptUrls.delete(key);
        reject(new Error("Citry Vue type script failed to load: " + asset.source.url));
      });
      document.head.append(script);
    });
    loadedScriptUrls.set(key, record);
    return record.promise;
  }

  function waitForStartup(value, lifecycle) {
    if (!lifecycle?.signal) return value;
    lifecycle.guard();
    if (lifecycle.signal.aborted)
      return Promise.reject(lifecycle.signal.reason || new Error("Citry Vue startup was cancelled"));
    return new Promise((resolve, reject) => {
      let signal = lifecycle.signal;
      const release = () => {
        signal?.removeEventListener("abort", cancelled);
        signal = null;
      };
      const cancelled = () => {
        const reason = signal?.reason;
        release();
        reject(reason || new Error("Citry Vue startup was cancelled"));
      };
      signal.addEventListener("abort", cancelled, {once: true});
      Promise.resolve(value).then(
        result => { release(); resolve(result); },
        error => { release(); reject(error); },
      );
    });
  }

  function validateCandidateAssets(appId, scripts, styles, occurrenceTypes, extensionNames, configuration,
      enforceLazy) {
    const normalizedScripts = scripts.map(asset => normalizeScriptAsset(asset));
    const normalizedStyles = styles.map(asset => normalizeStyleAsset(asset, occurrenceTypes));
    const candidates = [
      [normalizedScripts, loadedScriptUrls, asset => scriptRecordKey(appId, asset), "script"],
      [normalizedStyles, loadedStyleUrls, asset => styleRecordKey(appId, asset.source.url), "stylesheet"],
    ];
    for (const [assets, live, keyFor, label] of candidates) {
      const seen = new Map();
      for (const asset of assets) {
        if (asset.owner.kind === "extension" && !extensionNames.has(asset.owner.extensionName))
          throw new Error("prepared asset references an uninstalled browser extension");
        const key = keyFor(asset), prior = seen.get(key) || live.get(key);
        if (prior && prior.identity !== assetIdentity(asset))
          throw new Error(`prepared ${label} URL identity collision`);
        seen.set(key, {identity: assetIdentity(asset)});
        if (enforceLazy && !live.has(key)) {
          if (asset.lazyAllowed !== true) throw new Error(`prepared unseen ${label} asset disallows lazy loading`);
          if (asset.owner.kind === "component" && configuration.allowLazyTypeAssets !== true)
            throw new Error("lazy type assets are unsupported by this dependency or JavaScript policy");
        }
      }
    }
    return {scripts: normalizedScripts, styles: normalizedStyles};
  }

  async function primeInitialAssets(manifest, configuration, extensionNames, lifecycle) {
    if (!Array.isArray(manifest.scripts) || !Array.isArray(manifest.styles) || !Array.isArray(manifest.typePolicies))
      throw new Error("prepared manifest dependency assets must be arrays");
    normalizeTypePolicies(manifest.typePolicies);
    const initialTypes = new Map(manifest.occurrences.map(item => [item.id, item.typeKey]));
    const {scripts: normalizedScripts, styles: normalizedStyles} = validateCandidateAssets(
      manifest.appId, manifest.scripts, manifest.styles, initialTypes, extensionNames, configuration, false);
    const initialStyleStage = configuration.loadInitialAssets === true ? {
      token: Symbol("initial-style-stage"),
      refs: new Map(),
      replacedIds: new Set(),
    } : null;
    try {
    if (configuration.loadInitialAssets !== true) {
      for (const asset of normalizedScripts) if (asset.registersOptions &&
          (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey)))
        throw new Error("initial Citry Vue type Options were not emitted before bootstrap");
      for (const asset of normalizedStyles) {
        const key = styleRecordKey(manifest.appId, asset.source.url);
        if (!loadedStyleUrls.has(key) && !existingStyleElement(manifest.appId, asset.source.url))
          throw new Error("initial Citry Vue stylesheet was not emitted before bootstrap");
      }
    }
    if (configuration.loadInitialAssets === true) {
      await waitForStartup(
        Promise.all(normalizedStyles.map(asset =>
          loadStyle(manifest.appId, asset, configuration.nonce, initialStyleStage, true))),
        lifecycle,
      );
      lifecycle?.guard();
      for (const asset of normalizedScripts) {
        await waitForStartup(loadTypeScript(manifest.appId, asset, configuration.nonce, true), lifecycle);
        lifecycle?.guard();
      }
    }
    for (const [assets, loaded, name] of [[manifest.scripts, loadedScriptUrls, "script"]]) {
      for (const asset of assets) {
        if (name === "script" && asset.registersOptions &&
            (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey)))
          throw new Error("initial Citry Vue type Options were not emitted before bootstrap");
        const key = scriptRecordKey(manifest.appId, asset);
        const prior = loaded.get(key), identity = assetIdentity(asset);
        if (prior && prior.identity !== identity) throw new Error("prepared script URL identity collision");
        if (!prior) loaded.set(key, {
          appId: asset.owner.kind === "extension" ? manifest.appId : null,
          identity,
          promise: Promise.resolve(),
        });
      }
    }
    for (const rawAsset of manifest.styles) {
      const asset = normalizeStyleAsset(rawAsset, initialTypes);
      if (asset.owner.kind === "extension" && !extensionNames.has(asset.owner.extensionName))
        throw new Error("prepared asset references an uninstalled browser extension");
      const key = styleRecordKey(manifest.appId, asset.source.url);
      let record = loadedStyleUrls.get(key);
      if (!record) {
        const element = existingStyleElement(manifest.appId, asset.source.url);
        if (!element) throw new Error("initial Citry Vue stylesheet was not emitted before bootstrap");
        record = {element, refs: new Map(), stages: new Set(), promise: Promise.resolve(),
          identity: assetIdentity(asset)};
        loadedStyleUrls.set(key, record);
      } else if (record.identity !== assetIdentity(asset)) {
        throw new Error("prepared stylesheet URL identity collision");
      }
      const refs = record.refs.get(manifest.appId) || new Set();
      for (const id of assetRefs(asset)) refs.add(id);
      record.refs.set(manifest.appId, refs);
    }
    } finally {
      abortStyleStage(initialStyleStage);
    }
  }

  function normalizeTypePolicies(values) {
    const policies = new Map();
    for (const value of values) {
      plain(value, "prepared type policy");
      if (typeof value.typeKey !== "string" || typeof value.lazyAllowed !== "boolean" ||
          Object.keys(value).sort().join(",") !== "lazyAllowed,typeKey" || policies.has(value.typeKey))
        throw new Error("invalid prepared type policy");
      policies.set(value.typeKey, value.lazyAllowed);
    }
    return policies;
  }

  async function startPreparedOwned(configuration, lifecycle, startAttempt) {
    if (lifecycle) configuration = {...configuration, nonce: lifecycle.nonce};
    plain(configuration, "prepared bootstrap");
    const manifest = plain(configuration.manifest, "prepared manifest");
    const hostElement = typeof configuration.host === "string" ? document.querySelector(configuration.host) : configuration.host;
    if (!(hostElement instanceof Element) || !plain(configuration.tags, "component tags"))
      throw new Error("prepared bootstrap needs one host element and component tags");
    const appId = manifest.appId, registered = new Set(), contexts = new Map(), sources = new Map();
    const pluginEntries = extensionEntries(manifest.extensions || {}), plugins = new Map();
    let staged = null;
    if (!Array.isArray(manifest.definitions) || !Array.isArray(manifest.occurrences))
      throw new Error("prepared manifest lacks definitions or occurrences");
    const declaredDefinitions = preflightDefinitions(
      {definitions: new Map()}, manifest.definitions, manifest.occurrences, manifest.rootId);
    configure(manifest, startAttempt);
    definitionRegistry(appId).hostElement = hostElement;
    const claimedContextNames = new Set();
    for (const [, item] of pluginEntries) for (const name of item.templateContextNames) {
      if (claimedContextNames.has(name)) throw new Error("duplicate browser plugin template context claim: " + name);
      claimedContextNames.add(name);
    }
    definitionRegistry(appId).templateContextNames = Object.freeze([...claimedContextNames].sort());
    await waitForStartup(
      primeInitialAssets(manifest, configuration, new Set(pluginEntries.map(([name]) => name)), lifecycle),
      lifecycle,
    );
    lifecycle?.guard();
    for (const asset of manifest.definitions) {
      await waitForStartup(loadDefinition(asset, configuration.nonce), lifecycle);
      lifecycle?.guard();
    }
    for (const asset of manifest.definitions) {
      registerDefinition(appId, asset.id, global.CitryStableDefinitions?.[asset.id], declaredDefinitions.get(asset.id));
      registered.add(asset.id);
    }
    const componentTypes = {};
    const initialTypeTags = new Map(Object.entries(configuration.tags));
    for (const definition of definitionRegistry(appId).definitions.values()) {
      for (const call of [...definition.localCalls, ...definition.localCallRuns]) {
        const prior = initialTypeTags.get(call.typeKey);
        if (prior && prior !== call.componentTag) throw new Error("prepared stable type has conflicting component tags");
        initialTypeTags.set(call.typeKey, call.componentTag);
      }
    }
    const pluginHost = Object.freeze({
      appId,
      vue: V,
      occurrenceId(component) {
        const record = instanceRecords.get(component);
        return record?.app.id === appId ? record.occurrenceId : null;
      },
      occurrence(id) { return definitionRegistry(appId).occurrences.get(id) || null; },
      revision() { return definitionRegistry(appId).revision; },
    });
    const cleanupPluginStages = (values, method) => {
      for (const item of [...values].reverse()) {
        try { item.plugin[method](item.stage); }
        catch (error) { console.error("[Citry] browser plugin " + method + " failed:", error); }
      }
    };
    const activatedInitialPlugins = [];
    try {
      for (const [name, item] of pluginEntries) {
        const registration = browserPluginFactories.get(name);
        if (!registration || registration.schemaVersion !== item.schemaVersion ||
            JSON.stringify(registration.templateContextNames) !== JSON.stringify(item.templateContextNames))
          throw new Error("missing or incompatible Citry browser plugin: " + name);
        const plugin = registration.factory(pluginHost);
        if (!plugin || typeof plugin.install !== "function" || typeof plugin.prepareRevision !== "function" ||
            typeof plugin.activateRevision !== "function" || typeof plugin.commitRevision !== "function" ||
            typeof plugin.abortRevision !== "function" || typeof plugin.rollbackRevision !== "function" ||
            typeof plugin.dispose !== "function")
          throw new Error("invalid Citry browser plugin factory result: " + name);
        plugins.set(name, {plugin, stage: null});
        const stage = await waitForStartup(plugin.prepareRevision(detached(item.payload), detached(manifest)), lifecycle);
        lifecycle?.guard();
        plugins.set(name, {plugin, stage});
      }
      lifecycle?.guard();
      for (const item of plugins.values()) {
        activatedInitialPlugins.push(item);
        item.plugin.activateRevision(item.stage);
      }
    } catch (error) {
      cleanupPluginStages(activatedInitialPlugins, "rollbackRevision");
      const activated = new Set(activatedInitialPlugins);
      cleanupPluginStages([...plugins.values()].filter(item => item.stage !== null && !activated.has(item)), "abortRevision");
      releaseAppStyles(appId);
      releaseAppScripts(appId);
      apps.delete(appId);
      for (const {plugin} of plugins.values()) {
        try { plugin.dispose(); } catch (disposeError) { console.error("[Citry] browser plugin dispose failed:", disposeError); }
      }
      throw error;
    }
    definitionRegistry(appId).browserPlugins = [...plugins.values()].map(item => item.plugin);
    definitionRegistry(appId).initialPluginStages = [...plugins.values()];
    const ownedApp = definitionRegistry(appId);
    const firstLiveElement = (vnode, seen = new Set()) => {
      if (!vnode || typeof vnode !== "object" || seen.has(vnode)) return null;
      seen.add(vnode);
      const nested = vnode.component?.subTree;
      if (nested) {
        const element = firstLiveElement(nested, seen);
        if (element) return element;
      }
      if (vnode.type === V.Static && vnode.el instanceof Node && vnode.anchor instanceof Node) {
        let node = vnode.el;
        while (node) {
          if (node instanceof Element && node.isConnected) return node;
          if (node === vnode.anchor) break;
          node = node.nextSibling;
        }
      }
      if (vnode.el instanceof Element && vnode.el.isConnected) return vnode.el;
      if (Array.isArray(vnode.children)) for (const child of vnode.children) {
        const element = firstLiveElement(child, seen);
        if (element) return element;
      }
      return null;
    };
    const liveComponentCarrier = component => {
      const element = firstLiveElement(component?.$?.subTree);
      if (element) return element;
      const root = component?.$el;
      if (typeof Node === "function" && root instanceof Node && root.isConnected) return root;
      throw new Error("Citry Events component has no live DOM root");
    };
    const dispatchCarrier = source => {
      if (!source || sources.get(source.stableId)?.generation !== source.generation)
        throw new Error("Citry Events dispatch source is stale or retired");
      const mounted = ownedApp.mounted.get(source.stableId);
      if (!mounted || mounted.record.generation !== source.generation)
        throw new Error("Citry Events dispatch source is stale or retired");
      return liveComponentCarrier(mounted.component);
    };
    const liveRootElements = (component, seen = new Set(), output = []) => {
      const visit = vnode => {
        if (!vnode || typeof vnode !== "object" || seen.has(vnode)) return;
        seen.add(vnode);
        if (vnode.component?.subTree) { visit(vnode.component.subTree); return; }
        if (vnode.type === V.Fragment && Array.isArray(vnode.children)) {
          for (const child of vnode.children) visit(child);
          return;
        }
        if (typeof Element === "function" && vnode.el instanceof Element && vnode.el.isConnected) {
          if (!output.includes(vnode.el)) output.push(vnode.el);
          return;
        }
        if (Array.isArray(vnode.children)) for (const child of vnode.children) visit(child);
      };
      visit(component?.$?.subTree);
      if (!output.length && typeof Element === "function" && component?.$el instanceof Element && component.$el.isConnected)
        output.push(component.$el);
      return output;
    };
    const componentContains = (component, element) =>
      liveRootElements(component).some(root => root === element || root.contains(element));
    ownedApp.componentRoot = (record, childId) => {
      if (record?.app !== ownedApp || ownedApp.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry component event source is stale or retired");
      if (typeof childId !== "string" || childId.length === 0)
        throw new TypeError("Citry component event child id must be a non-empty string");
      const child = ownedApp.occurrences.get(childId);
      if (!child)
        throw new Error("Citry component event child is not a descendant of its source");
      let cursor = child.parentId;
      while (cursor !== null && cursor !== record.occurrenceId)
        cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
      if (cursor !== record.occurrenceId)
        throw new Error("Citry component event child is not a descendant of its source");
      const mounted = ownedApp.mounted.get(childId);
      if (!mounted || mounted.record.app !== ownedApp || mounted.record.occurrenceId !== childId)
        throw new Error("Citry component event child is stale or retired");
      return liveComponentCarrier(mounted.component);
    };
    const sourceForElement = element => {
      if (typeof Element !== "function" || !(element instanceof Element) || !element.isConnected) return null;
      const candidates = [];
      for (const [id, mounted] of ownedApp.mounted) {
        if (!componentContains(mounted.component, element)) continue;
        let depth = 0, cursor = id;
        while (ownedApp.occurrences.get(cursor)?.parentId !== null) {
          depth += 1;
          cursor = ownedApp.occurrences.get(cursor).parentId;
        }
        const source = sources.get(id);
        if (source?.generation === mounted.record.generation) candidates.push({source, depth});
      }
      candidates.sort((left, right) => right.depth - left.depth);
      return candidates[0]?.source || null;
    };
    const sourceForTarget = target => {
      if (typeof target === "string") {
        const renderId = target.startsWith("render:") ? target.slice("render:".length) : target;
        for (const occurrence of ownedApp.occurrences.values()) {
          if (occurrence.renderId !== renderId) continue;
          const mounted = ownedApp.mounted.get(occurrence.id), source = sources.get(occurrence.id);
          if (mounted && source?.generation === mounted.record.generation) return source;
          return null;
        }
        return null;
      }
      return sourceForElement(target);
    };
    for (const typeKey of new Set(manifest.occurrences.map(item => item.typeKey))) {
      let options = registeredTypeOptions.get(typeKey)?.options || {};
      for (const plugin of definitionRegistry(appId).browserPlugins) if (typeof plugin.decorateTypeOptions === "function")
        options = plugin.decorateTypeOptions(typeKey, options);
      componentTypes[typeKey] = defineTypeWithCallback(appId, typeKey, options);
    }
    const cleanupEventAttempt = (attempt, reason = new Error("prepared Events render was cancelled")) => {
      if (!attempt || attempt.cleaned || attempt.published) return;
      attempt.aborted = true;
      attempt.abortReason ||= reason;
      attempt.rejectCancellation?.(attempt.abortReason);
      abortStyleStage(attempt.styleStage);
      for (const item of attempt.pluginStages || []) {
        if (item.cleaned || !item.hasStage) continue;
        item.cleaned = true;
        try { item.plugin[item.attempted ? "rollbackRevision" : "abortRevision"](item.stage); }
        catch (error) { console.error("[Citry] Events plugin stage cleanup failed:", error); }
      }
      attempt.cleaned = true;
      if (staged === attempt) staged = null;
    };
    const validateAddresses = (values, requireAddresses) => {
      const byRender = new Map();
      const addressed = values.filter(item => own(item, "renderId"));
      if ((requireAddresses && addressed.length !== values.length) ||
          (addressed.length !== 0 && addressed.length !== values.length))
        throw new Error("prepared Events occurrence addresses are incomplete");
      for (const occurrence of addressed) {
        if (typeof occurrence.renderId !== "string" || !/^[a-z0-9_-]+$/.test(occurrence.renderId) ||
            byRender.has(occurrence.renderId))
          throw new Error("prepared Events occurrence address is invalid or duplicated");
        if (occurrence.eventContext && occurrence.eventContext.serverRenderId !== occurrence.renderId)
          throw new Error("prepared Events occurrence address disagrees with its event context");
        byRender.set(occurrence.renderId, occurrence);
      }
      return byRender;
    };
    const addressSnapshot = (requireAddresses = false) =>
      validateAddresses([...ownedApp.occurrences.values()], requireAddresses);
    const translateTargetEnvelope = (rawEnvelope, target, allocator) => {
      const envelope = clone(rawEnvelope), incoming = new Map(envelope.occurrences.map(item => [item.id, item]));
      if (incoming.size !== envelope.occurrences.length || !incoming.has(envelope.rootId))
        throw new Error("invalid isolated prepared target snapshot");
      for (const item of incoming.values()) if (typeof item.id !== "string" ||
          !/^citryOccurrence[0-9A-Za-z]+$/.test(item.id))
        throw new Error("prepared Events incoming occurrence ID is invalid");
      validateGraph(incoming, envelope.rootId);
      normalizeMarkers(envelope.markers, incoming);
      const existingChildren = new Map();
      for (const item of ownedApp.occurrences.values()) {
        const key = item.parentId;
        if (!existingChildren.has(key)) existingChildren.set(key, []);
        existingChildren.get(key).push(item);
      }
      const incomingChildren = new Map();
      for (const item of incoming.values()) {
        if (!incomingChildren.has(item.parentId)) incomingChildren.set(item.parentId, []);
        incomingChildren.get(item.parentId).push(item);
      }
      const occupied = allocator.occupied;
      const reserved = allocator.reserved;
      const claimedExisting = allocator.claimedExisting;
      const mapped = new Map([[envelope.rootId, target.id]]);
      claimedExisting.add(target.id);
      const visit = oldParent => {
        const newParent = mapped.get(oldParent);
        const candidates = existingChildren.get(newParent) || [];
        for (const child of incomingChildren.get(oldParent) || []) {
          const match = candidates.find(item => !claimedExisting.has(item.id) &&
            item.placementKey === child.placementKey && item.typeKey === child.typeKey);
          let id;
          if (match) id = match.id;
          else {
            if (!occupied.has(child.id)) id = child.id;
            if (!id) {
              do id = `citryOccurrenceTranslated${envelope.revision}${allocator.ordinal++}`;
              while (reserved.has(id));
            }
            reserved.add(id);
            occupied.add(id);
          }
          claimedExisting.add(id);
          mapped.set(child.id, id); visit(child.id);
        }
      };
      visit(envelope.rootId);
      const resolve = id => {
        if (typeof id !== "string" || !mapped.has(id)) throw new Error("prepared target references an unknown incoming occurrence");
        return mapped.get(id);
      };
      const translatePreparedData = value => {
        const prepared = clone(value);
        for (const call of Object.values(prepared.calls || {})) {
          if (call.key !== call.id) throw new Error("prepared component call key must equal its occurrence id");
          call.id = resolve(call.id); call.key = call.id;
          if (typeof call.parentId === "string") call.parentId = resolve(call.parentId);
        }
        for (const ids of Object.values(prepared.callRuns || {})) for (let index = 0; index < ids.length; index += 1)
          ids[index] = resolve(ids[index]);
        return prepared;
      };
      envelope.rootId = resolve(envelope.rootId);
      envelope.updatedIds = envelope.updatedIds.map(resolve).sort();
      envelope.occurrences = envelope.occurrences.map(item => ({...item, id: resolve(item.id),
        parentId: item.parentId === null ? null : resolve(item.parentId), preparedData: translatePreparedData(item.preparedData)}));
      envelope.markers = envelope.markers.map(item => ({...item,
        ownerId: resolve(item.ownerId), occurrenceId: resolve(item.occurrenceId)})).sort((a,b) => {
        const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
        const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
        return left < right ? -1 : left > right ? 1 : 0;
      });
      envelope.replacements = envelope.replacements.map(item => ({...item, ownerId: resolve(item.ownerId),
        expectedRemountIds: item.expectedRemountIds.map(resolve).sort()})).sort((a,b) => {
        const left = `${a.ownerId}\0${a.siteId}`, right = `${b.ownerId}\0${b.siteId}`;
        return left < right ? -1 : left > right ? 1 : 0;
      });
      for (const style of envelope.styles || []) if (style.owner?.kind === "component" && Array.isArray(style.owner.occurrenceIds))
        style.owner.occurrenceIds = style.owner.occurrenceIds.map(resolve).sort();
      for (const [name, extension] of extensionEntries(envelope.extensions || {})) {
        const plugin = plugins.get(name)?.plugin;
        if ([...mapped].some(([before, after]) => before !== after)) {
          if (typeof plugin?.translateRevision !== "function") throw new Error("browser plugin cannot translate occurrence identities: " + name);
          const translated = plugin.translateRevision(detached(extension.payload), resolve);
          if (translated && typeof translated.then === "function") throw new Error("browser plugin occurrence translation must be synchronous: " + name);
          envelope.extensions[name] = {...extension, payload: detached(translated)};
        }
      }
      return envelope;
    };
    const host = {
      appId(source) { return sources.get(source.stableId)?.generation === source.generation ? appId : ""; },
      resolve(source) { return sources.get(source.stableId)?.generation === source.generation ? contexts.get(source.stableId) || null : null; },
      revision(source) { return sources.get(source.stableId)?.generation === source.generation ? definitionRegistry(appId).revision : -1; },
      resolveTarget(target) { return sourceForTarget(target); },
      preflightResult(result, source) {
        const renders = result.ok ? result.actions.filter(action => action.action === "render") : [];
        if (!renders.length) return {result};
        if (renders.length > 1) {
          const indexes = renders.map(action => result.actions.indexOf(action));
          if (indexes.some((index, ordinal) => index !== indexes[0] + ordinal) ||
              renders.some(action => action.wait === false || typeof action.delay === "number" && action.delay > 0))
            throw new Error("multiple prepared Render actions must be one immediate blocking contiguous group");
        }
        const byRender = addressSnapshot();
        const allIncomingIds = new Set();
        for (const action of renders) for (const occurrence of action.prepared?.occurrences || []) {
          if (typeof occurrence.id !== "string") throw new Error("prepared Events incoming occurrence ID is invalid");
          allIncomingIds.add(occurrence.id);
        }
        const allocator = {occupied: new Set(ownedApp.occurrences.keys()),
          reserved: new Set([...ownedApp.occurrences.keys(), ...allIncomingIds]), claimedExisting: new Set(), ordinal: 0};
        const handles = [], entries = [], targetIds = new Set();
        let combined = null;
        const canonical = value => {
          if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
          if (value && typeof value === "object") return `{${Object.keys(value).sort()
            .map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
          return JSON.stringify(value);
        };
        const merged = (name, identity) => {
          const values = [], seen = new Map();
          for (const entry of entries) for (const value of entry.envelope[name] || []) {
            const key = identity(value), prior = seen.get(key);
            if (prior && canonical(prior) !== canonical(value))
              throw new Error(`prepared ${name} identity conflicts across Render targets`);
            if (!prior) { seen.set(key, value); values.push(value); }
          }
          return values;
        };
        const mergedStyles = () => {
          const values = [], seen = new Map();
          for (const entry of entries) for (const raw of entry.envelope.styles || []) {
            const value = clone(raw);
            const key = canonical([value.source?.url, value.owner?.kind,
              value.owner?.typeKey || value.owner?.extensionName]);
            const prior = seen.get(key);
            if (!prior) { seen.set(key, value); values.push(value); continue; }
            const priorComparable = clone(prior), valueComparable = clone(value);
            if (priorComparable.owner?.kind === "component") priorComparable.owner.occurrenceIds = [];
            if (valueComparable.owner?.kind === "component") valueComparable.owner.occurrenceIds = [];
            if (canonical(priorComparable) !== canonical(valueComparable))
              throw new Error("prepared styles identity conflicts across Render targets");
            if (prior.owner.kind === "component") prior.owner.occurrenceIds =
              [...new Set([...prior.owner.occurrenceIds, ...value.owner.occurrenceIds])].sort();
          }
          return values;
        };
        for (const action of renders) {
          if (action.renderer !== "vue-prepared/1" || action.swap !== "morph" || typeof action.target !== "string")
            throw new Error("cross-component Vue rendering requires a render target, morph, and vue-prepared/1");
          let target, selectedMarker = null;
          if (action.target.startsWith("render:")) target = byRender.get(action.target.slice(7));
          else {
            const match = /^mark:([a-z0-9_-]+):([A-Za-z][A-Za-z0-9_-]*)$/.exec(action.target);
            if (!match) throw new Error("prepared Events marker target syntax is invalid");
            const caller = byRender.get(match[1]);
            if (!caller || caller.id !== source.stableId)
              throw new Error("prepared Events marker caller is stale or does not match the event source");
            selectedMarker = ownedApp.markers.get(caller.id + "\0" + match[2]);
            target = selectedMarker && ownedApp.occurrences.get(selectedMarker.occurrenceId);
          }
          if (!target) throw new Error("prepared Events Render target is stale or unknown");
          if (targetIds.has(target.id)) throw new Error("multiple prepared Render actions target the same occurrence");
          for (const other of targetIds) {
            let cursor = target.id;
            while (cursor !== null && cursor !== other) cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
            let reverse = other;
            while (reverse !== null && reverse !== target.id) reverse = ownedApp.occurrences.get(reverse)?.parentId ?? null;
            if (cursor === other || reverse === target.id) throw new Error("prepared Render targets overlap");
          }
          targetIds.add(target.id);
          const mounted = ownedApp.mounted.get(target.id);
          if (!mounted) throw new Error("prepared Events Render target is not mounted");
          validateIsolatedEnvelope(ownedApp, action.prepared);
          let sourceCursor = source.stableId, strictAncestor = false;
          while (sourceCursor !== null) {
            if (sourceCursor === target.id) { strictAncestor = target.id !== source.stableId; break; }
            sourceCursor = ownedApp.occurrences.get(sourceCursor)?.parentId ?? null;
          }
          if (strictAncestor) {
            const renderIndex = result.actions.indexOf(action);
            const sourceRenderId = ownedApp.occurrences.get(source.stableId)?.renderId;
            result.actions.forEach((candidate, index) => {
              const sourceBound = candidate.action === "state" ||
                (candidate.action === "event" &&
                  (candidate.target === undefined || candidate.target === `render:${sourceRenderId}`));
              if (sourceBound && (index > renderIndex || (index < renderIndex &&
                  (candidate.wait === false || typeof candidate.delay === "number" && candidate.delay > 0))))
                throw new Error("ancestor Render cannot be combined with deferred or later source-bound actions");
            });
          }
          const root = action.prepared?.occurrences?.find(item => item.id === action.prepared.rootId);
          if (!root || root.typeKey !== target.typeKey) throw new Error("prepared Events Render target changed component type");
          const extensions = new Map(extensionEntries(action.prepared.extensions || {}));
          for (const name of plugins.keys()) if (!extensions.has(name)) throw new Error("prepared revision omitted installed browser plugin: " + name);
          for (const [name, incoming] of extensions) {
            const registration = browserPluginFactories.get(name);
            if (!plugins.has(name)) throw new Error("prepared revision introduced an uninstalled browser plugin: " + name);
            if (!registration || incoming.schemaVersion !== registration.schemaVersion ||
                JSON.stringify(incoming.templateContextNames) !== JSON.stringify(registration.templateContextNames))
              throw new Error("prepared revision changed browser plugin schema: " + name);
            if (renders.length > 1 && typeof plugins.get(name).plugin.prepareRevisionBatch !== "function")
              throw new Error("browser plugin does not support multiple prepared Render targets: " + name);
          }
          const translated = translateTargetEnvelope(action.prepared, target, allocator);
          validateIsolatedEnvelope(ownedApp, translated, target.id);
          entries.push({envelope: translated, targetId: target.id,
            extensions: new Map(extensionEntries(translated.extensions || {}))});
          handles.push(Object.freeze({app: ownedApp, id: target.id, generation: mounted.record.generation,
            renderId: target.renderId, typeKey: target.typeKey, revision: ownedApp.revision,
            markerOwnerId: selectedMarker?.ownerId || null, markerName: selectedMarker?.name || null}));
        }
        const removed = new Set();
        for (const id of ownedApp.occurrences.keys()) for (const rootId of targetIds) {
          let cursor = id;
          while (cursor !== null && cursor !== rootId) cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
          if (cursor === rootId) { removed.add(id); break; }
        }
        // A nontransparent parent can own the VNode for a child projected
        // through a marker. Replacing that marker removes the child from the
        // target subtree, while the parent's prepared call table still has to
        // satisfy its unchanged render definition. Keep those ancestor-owned
        // call chains in the composed graph; the replacement definition does
        // not consume the projected slot, and the replaced-root style stage
        // still retires their assets.
        const preserve = new Set();
        const preserveCalls = owner => {
          const prepared = owner.preparedData || {};
          for (const binding of Object.values(prepared.calls || {})) {
            if (removed.has(binding.id) && !targetIds.has(binding.id)) preserve.add(binding.id);
          }
          for (const ids of Object.values(prepared.callRuns || {})) {
            for (const id of ids) if (removed.has(id) && !targetIds.has(id)) preserve.add(id);
          }
        };
        for (const owner of ownedApp.occurrences.values()) if (!removed.has(owner.id)) preserveCalls(owner);
        for (const id of [...preserve]) {
          const queue = [id];
          while (queue.length) {
            const current = queue.pop();
            const owner = ownedApp.occurrences.get(current);
            if (!owner) continue;
            const before = preserve.size;
            preserveCalls(owner);
            if (preserve.size === before) continue;
            for (const child of preserve) if (!queue.includes(child)) queue.push(child);
          }
        }
        for (const id of preserve) removed.delete(id);
        const occurrences = new Map([...ownedApp.occurrences].filter(([id]) => !removed.has(id)));
        for (const entry of entries) {
          const existingTarget = ownedApp.occurrences.get(entry.targetId);
          for (const item of entry.envelope.occurrences) {
            if (occurrences.has(item.id)) throw new Error("subtree occurrence collides outside its target group");
            occurrences.set(item.id, item.id === entry.targetId ? {...item,
              parentId: existingTarget.parentId, placementKey: existingTarget.placementKey} : item);
          }
        }
        const compareMarker = (a, b) => {
          const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
          const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
          return left < right ? -1 : left > right ? 1 : 0;
        };
        const markers = [
          ...[...ownedApp.markers.values()].filter(item => targetIds.has(item.occurrenceId) || !removed.has(item.occurrenceId)),
          ...entries.flatMap(entry => entry.envelope.markers.filter(item => item.occurrenceId !== entry.targetId)),
        ].sort(compareMarker);
        normalizeMarkers(markers, occurrences);
        combined = {...entries[0].envelope, rootId: ownedApp.rootId,
          occurrences: [...occurrences.values()], markers};
        combined = {...combined,
          definitions: merged("definitions", value => value.id),
          scripts: merged("scripts", value => canonical([value.owner, value.source?.url])),
          styles: mergedStyles(),
          typePolicies: merged("typePolicies", value => value.typeKey),
          updatedIds: [...new Set(entries.flatMap(entry => entry.envelope.updatedIds))].sort(),
          replacements: entries.flatMap(entry => entry.envelope.replacements).sort((a,b) => {
            const left = `${a.ownerId}\0${a.siteId}`, right = `${b.ownerId}\0${b.siteId}`;
            return left < right ? -1 : left > right ? 1 : 0;
          }),
        };
        const incomingTypes = new Map(combined.occurrences.map(item => [item.id, item.typeKey]));
        const policies = normalizeTypePolicies(combined.typePolicies);
        validateCandidateAssets(appId, combined.scripts, combined.styles, incomingTypes,
          new Set(plugins.keys()), configuration, true);
        for (const typeKey of incomingTypes.values()) if (!ownedApp.types.has(typeKey) &&
            (configuration.allowLazyTypeAssets !== true || policies.get(typeKey) !== true))
          throw new Error("lazy component types are unsupported by this dependency or JavaScript policy");
        const declared = preflightDefinitions(ownedApp, combined.definitions, combined.occurrences, combined.rootId);
        const shadow = {...ownedApp, definitions: new Map(ownedApp.definitions)};
        for (const [id, definition] of declared) shadow.definitions.set(id, definition);
        validateCombinedActions(shadow, clone(combined));
        validateAddresses(combined.occurrences, true);
        const firstIndex = result.actions.indexOf(renders[0]);
        const transformed = renders.length === 1 ? result : {...result, actions: [
          ...result.actions.slice(0, firstIndex), {...renders[0], prepared: combined},
          ...result.actions.slice(firstIndex + renders.length),
        ]};
        return {result: transformed, renderPlan: Object.freeze({handles: Object.freeze(handles), envelope: combined,
          entries: Object.freeze(entries), replacedRootIds: Object.freeze([...targetIds])})};
      },
      async prepareRender(action, source, signal, renderPlan) {
        if (signal?.aborted) throw new Error("prepared Events render was cancelled");
        if (staged) throw new Error("a prepared Events transaction is already staged");
        let rejectCancellation;
        const cancellation = new Promise((_, reject) => { rejectCancellation = reject; });
        cancellation.catch(() => undefined);
        const attempt = {
          preparing: true,
          aborted: false,
          abortReason: null,
          cleaned: false,
          published: false,
          styleStage: null,
          pluginStages: [],
          rejectCancellation,
        };
        const cancel = () => cleanupEventAttempt(attempt);
        signal?.addEventListener("abort", cancel, {once: true});
        const guardHandles = () => {
          if (!source || sources.get(source.stableId)?.generation !== source.generation)
            throw new Error("prepared Events source became stale while rendering");
          for (const handle of renderPlan?.handles || []) if (handle && (handle.app !== ownedApp || ownedApp.revision !== handle.revision ||
              ownedApp.mounted.get(handle.id)?.record.generation !== handle.generation ||
              ownedApp.occurrences.get(handle.id)?.renderId !== handle.renderId ||
              ownedApp.occurrences.get(handle.id)?.typeKey !== handle.typeKey ||
              handle.markerOwnerId !== null && ownedApp.markers.get(handle.markerOwnerId + "\0" + handle.markerName)?.occurrenceId !== handle.id))
            throw new Error("prepared Events Render target became stale while rendering");
        };
        const wait = async promise => {
          const value = await Promise.race([promise, cancellation]);
          if (attempt.aborted || signal?.aborted) throw attempt.abortReason || new Error("prepared Events render was cancelled");
          guardHandles();
          return value;
        };
        staged = attempt;
        try {
        const envelope = renderPlan?.envelope || action.prepared;
        const handles = renderPlan?.handles || [];
        const replacedRootIds = renderPlan?.replacedRootIds || [source.stableId];
        if (!envelope || envelope.appId !== appId || !Array.isArray(envelope.definitions) || !Array.isArray(envelope.scripts) || !Array.isArray(envelope.styles) || !Array.isArray(envelope.typePolicies)) throw new Error("invalid prepared Events envelope");
        const incomingExtensions = new Map(extensionEntries(envelope.extensions || {}));
        for (const name of incomingExtensions.keys()) if (!plugins.has(name))
          throw new Error("prepared revision introduced an uninstalled browser plugin: " + name);
        for (const name of plugins.keys()) if (!incomingExtensions.has(name))
          throw new Error("prepared revision omitted installed browser plugin: " + name);
        normalizeTypePolicies(envelope.typePolicies);
        for (const [name, installed] of plugins) {
          const incoming = incomingExtensions.get(name), registration = browserPluginFactories.get(name);
          if (!registration || incoming.schemaVersion !== registration.schemaVersion ||
              JSON.stringify(incoming.templateContextNames) !== JSON.stringify(registration.templateContextNames))
            throw new Error("prepared revision changed browser plugin schema: " + name);
        }
        const incomingOccurrenceTypes = new Map(envelope.occurrences.map(item => [item.id, item.typeKey]));
        const normalizedAssets = validateCandidateAssets(appId, envelope.scripts, envelope.styles,
          incomingOccurrenceTypes, new Set(incomingExtensions.keys()), configuration, true);
        const replacedStyleIds = new Set();
        for (const id of definitionRegistry(appId).occurrences.keys()) {
          for (const rootId of replacedRootIds) {
            let cursor = id;
            while (cursor !== null && cursor !== rootId)
              cursor = definitionRegistry(appId).occurrences.get(cursor)?.parentId ?? null;
            if (cursor === rootId) { replacedStyleIds.add(id); break; }
          }
        }
        const suppliedLiveOccurrenceIds = renderPlan?.entries?.length
          ? new Set(renderPlan.entries.flatMap(entry => entry.envelope.occurrences.map(item => item.id)))
          : null;
        attempt.styleStage = {
          token: Object.freeze({appId, revision: envelope.revision}),
          replacedIds: replacedStyleIds,
          refs: new Map(),
        };
        for (const asset of normalizedAssets.styles) {
          const refs = attempt.styleStage.refs.get(asset.source.url) || new Set();
          for (const id of assetRefs(asset)) {
            if (suppliedLiveOccurrenceIds && replacedStyleIds.has(id) && !suppliedLiveOccurrenceIds.has(id)) continue;
            refs.add(id);
          }
          attempt.styleStage.refs.set(asset.source.url, refs);
        }
        if (!source || sources.get(source.stableId)?.generation !== source.generation)
          throw new Error("prepared Events source is stale before render preflight");
        guardHandles();
        const declaredDefinitions = preflightDefinitions(
          definitionRegistry(appId), envelope.definitions, envelope.occurrences, envelope.rootId);
        const shadow = {...definitionRegistry(appId), definitions: new Map(definitionRegistry(appId).definitions)};
        for (const [id, definition] of declaredDefinitions) shadow.definitions.set(id, definition);
        validateCombinedActions(shadow, clone(envelope));
        const declaredDefinitionIds = new Set(declaredDefinitions.keys());
        const priorDefinitionKeys = new Set(Object.keys(global.CitryStableDefinitions || {}));
        for (const asset of envelope.definitions) await wait(loadDefinition(asset, configuration.nonce));
        for (const id of Object.keys(global.CitryStableDefinitions || {}))
          if (!priorDefinitionKeys.has(id) && !declaredDefinitionIds.has(id))
            throw new Error("prepared definition asset registered an undeclared definition");
        for (const asset of envelope.definitions) if (!registered.has(asset.id)) {
          registerDefinition(
            appId, asset.id, global.CitryStableDefinitions?.[asset.id], declaredDefinitions.get(asset.id));
          registered.add(asset.id);
        }
        validateCombinedActions(definitionRegistry(appId), clone(envelope));
        const declaredOptionTypes = new Set(normalizedAssets.scripts.filter(asset => asset.registersOptions).map(asset => asset.owner.typeKey));
        const priorOptionTypes = new Set(registeredTypeOptions.keys());
        for (const asset of normalizedAssets.scripts)
          await wait(loadTypeScript(appId, asset, configuration.nonce));
        await wait(Promise.all(normalizedAssets.styles.map(asset =>
          loadStyle(appId, asset, configuration.nonce, attempt.styleStage))));
        for (const typeKey of registeredTypeOptions.keys())
          if (!priorOptionTypes.has(typeKey) && !declaredOptionTypes.has(typeKey))
            throw new Error("prepared type asset registered undeclared Vue Options");
        try {
          for (const [name, installed] of plugins) {
            const incoming = incomingExtensions.get(name);
            const item = {
              name, plugin: installed.plugin, attempted: false, cleaned: false, hasStage: false, stage: undefined,
            };
            attempt.pluginStages.push(item);
            const entries = renderPlan?.entries;
            const pending = Promise.resolve(entries?.length > 1
              ? installed.plugin.prepareRevisionBatch(entries.map(entry => ({
                  payload: detached(entry.extensions.get(name).payload), rootId: entry.targetId,
                })), detached(envelope))
              : entries?.length === 1
                ? installed.plugin.prepareRevision(detached(entries[0].extensions.get(name).payload),
                    detached(entries[0].envelope))
                : installed.plugin.prepareRevision(detached(incoming.payload), detached(envelope)));
            pending.then(stage => {
              item.stage = stage;
              item.hasStage = true;
              if (attempt.aborted && !item.cleaned) {
                item.cleaned = true;
                try { item.plugin.abortRevision(stage); }
                catch (error) { console.error("[Citry] late Events plugin stage cleanup failed:", error); }
              }
            }, () => undefined);
            await wait(pending);
          }
        } catch (error) {
          cleanupEventAttempt(attempt, error);
          throw error;
        }
        if (attempt.aborted || signal?.aborted) throw attempt.abortReason || new Error("prepared Events render was cancelled");
        attempt.preparing = false;
        attempt.envelope = envelope;
        attempt.replacedRootIds = replacedRootIds;
        attempt.targetHandles = handles;
        attempt.callbackOwnerIds = new Set(handles.map(handle => handle.markerOwnerId).filter(Boolean));
        return {transaction: attempt};
        } catch (error) {
          cleanupEventAttempt(attempt, error);
          throw error;
        } finally {
          signal?.removeEventListener("abort", cancel);
        }
      },
      abortRender(prepared) {
        const transaction = prepared?.transaction;
        if (!transaction) {
          if (staged?.preparing) cleanupEventAttempt(staged);
          return;
        }
        if (staged === transaction) cleanupEventAttempt(transaction);
      },
      async commitRender(prepared, source) {
        if (apps.get(appId) !== ownedApp || ownedApp.terminal || !staged || prepared.transaction !== staged)
          throw new Error("prepared Events transaction is stale");
        const transaction = staged;
        try {
          if (!source || sources.get(source.stableId)?.generation !== source.generation)
            throw new Error("prepared Events source became stale before publication");
          for (const handle of transaction.targetHandles || []) if (handle && (handle.app !== ownedApp || ownedApp.revision !== handle.revision ||
              ownedApp.mounted.get(handle.id)?.record.generation !== handle.generation ||
              ownedApp.occurrences.get(handle.id)?.renderId !== handle.renderId ||
              ownedApp.occurrences.get(handle.id)?.typeKey !== handle.typeKey ||
              handle.markerOwnerId !== null && ownedApp.markers.get(handle.markerOwnerId + "\0" + handle.markerName)?.occurrenceId !== handle.id))
            throw new Error("prepared Events Render target became stale before publication");
          await applyEnvelope(appId, transaction.envelope, transaction.replacedRootIds[0] || source.stableId, {
            combined: true,
            acceptedTransaction: transaction,
            callbackOwnerIds: transaction.callbackOwnerIds,
            activate() { for (const item of transaction.pluginStages) {
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before activation");
              item.attempted = true;
              item.plugin.activateRevision(item.stage);
            } },
            commit() {
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before publication");
              for (const item of transaction.pluginStages) {
                item.plugin.commitRevision(item.stage);
                if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                  throw new Error("prepared Events transaction was disposed during plugin publication");
              }
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before style publication");
              commitStyleStage(appId, transaction.styleStage);
              transaction.published = true;
            },
          });
          if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
            throw new Error("prepared Events transaction became stale after publication");
        } catch (error) {
          cleanupEventAttempt(transaction, error);
          throw error;
        } finally {
          if (staged === transaction) staged = null;
        }
      },
      commitState(serverRenderId, stateToken) {
        for (const [id, value] of contexts) if (value.serverRenderId === serverRenderId)
          contexts.set(id, {...value, stateToken});
      },
      dispatchEvent(name, detail, source) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation)
          throw new Error("Citry Events dispatch source is stale or retired");
        mounted.record.events.dispatch(name, detail);
        dispatchCarrier(source).dispatchEvent(new CustomEvent(name, {detail, bubbles: true}));
      },
      dispatchEventGlobal(name, detail) {
        document.dispatchEvent(new CustomEvent(name, {detail, bubbles: true}));
      },
      lifecycle(kind, source, event, extra = {}) {
        // A committed self-render may retire the sender and mount its
        // replacement before the bridge emits `swapped`/`after`. Those
        // notifications describe the committed instance, so follow the
        // stable occurrence identity for post-commit hooks while keeping
        // cancellation/error checks bound to the original generation.
        const effectiveSource = kind === "swapped" || kind === "after"
          ? sources.get(source.stableId) || source
          : source;
        const context = contexts.get(effectiveSource.stableId);
        const mounted = ownedApp.mounted.get(effectiveSource.stableId);
        if (!context || !mounted || mounted.record.generation !== effectiveSource.generation) return true;
        const details = {
          instance: context.serverRenderId,
          class: context.componentClassId,
          event,
          ...extra,
        };
        if (kind === "swapped") details.els = liveRootElements(mounted.component);
        const roots = liveRootElements(mounted.component);
        const carrier = roots[0] || document;
        return carrier.dispatchEvent(new CustomEvent(`citry:events:${kind}`, {
          detail: details,
          bubbles: true,
          cancelable: kind === "before",
        }));
      },
      redirect(url) { global.location.assign(url); },
      updateUrl(url, mode) { global.history[mode === "push" ? "pushState" : "replaceState"]({}, "", url); },
      takePendingState(source, handlerName) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation) return undefined;
        const descriptor = mounted.record.events.descriptor;
        if (descriptor?.eventHandlers?.[handlerName]?.httpMethod === "GET") return undefined;
        if (!mounted.record.state.pending) return undefined;
        const keys = Object.keys(mounted.record.state.pending);
        if (!keys.length) return undefined;
        const snapshot = cloneStateValue(mounted.record.state.pending);
        mounted.record.state.pending = Object.create(null);
        return snapshot;
      },
      restorePendingState(source, updates) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation || !mounted.record.state.current ||
            !mounted.record.state.writable || !mounted.record.state.pending) return;
        for (const [key, value] of Object.entries(updates))
          if (mounted.record.state.writable.has(key) && !own(mounted.record.state.pending, key))
            mounted.record.state.pending[key] = cloneStateValue(value);
      },
    };
    const cookieToken = () => {
      const match = document.cookie.split(";").map(value => value.trim()).find(value => value.startsWith("csrftoken="));
      return match ? decodeURIComponent(match.slice("csrftoken=".length)) : "";
    };
    const hasEvents = manifest.occurrences.some(occurrence => occurrence.eventContext);
    if (manifest.occurrences.some(occurrence => own(occurrence, "renderId"))) addressSnapshot();
    let bridge = null;
    const ensureEventsBridge = () => {
      addressSnapshot(true);
      if (bridge) return bridge;
      if (!global.CitryVueEvents || typeof configuration.endpoint !== "string")
        throw new Error("prepared Events components require the Events bridge and endpoint");
      bridge = global.CitryVueEvents.createVueEventsBridge({
        endpoint: configuration.endpoint,
        eventBaseUrl: configuration.eventBaseUrl,
        host,
        csrf: configuration.csrf || {token: cookieToken},
        runtimeConfig: () => publicEventsConfig,
        transport: () => {
          const name = typeof publicEventsConfig.transport === "string" && publicEventsConfig.transport
            ? publicEventsConfig.transport : "fetch";
          const implementation = publicEventTransports.get(name);
          if (implementation) return implementation;
          if (name === "fetch") return null;
          throw new Error("Citry Events transport is not registered: " + name);
        },
        activity(source, descriptor) {
          const mounted = ownedApp.mounted.get(source.stableId);
          if (!mounted || mounted.record.generation !== source.generation)
            throw new Error("Citry Events activity source is stale or retired");
          mounted.record.events.descriptor = descriptor;
          return mounted.record.events;
        },
      });
      return bridge;
    };
    if (hasEvents) ensureEventsBridge();
    async function sendDeclarativeEvent(record, binding, source, args) {
      const eventsBridge = ensureEventsBridge();
      let result;
      try {
        result = await eventsBridge.send({source, handler: binding.handler, args});
      } catch (error) {
        if (!ownedApp.terminal && eventsBridge.isDeclarativeFailureHandled(error)) return undefined;
        throw error;
      }
      document.dispatchEvent(new CustomEvent("citry:rendered", {detail: {appId, revision: definitionRegistry(appId).revision}}));
      return result;
    }
    const resolveDeclarativeEvent = (record, bindingId) => {
      if (record.app !== definitionRegistry(appId) || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events source is stale or retired");
      const bindings = record.live.value?.preparedData?.eventBindings;
      const binding = bindings && bindings[bindingId];
      if (!binding) throw new Error("Citry Events binding is missing or stale");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry Events binding has no mounted Vue owner");
      return {binding, source};
    };
    const declarativeEventArgs = (value, authoredArgs) => {
      let args = authoredArgs;
      if (args === undefined) {
        const isEvent = typeof global.Event === "function" && value instanceof global.Event;
        const form = isEvent && value.target instanceof HTMLFormElement
          ? value.target
          : isEvent && value.currentTarget instanceof HTMLFormElement ? value.currentTarget : null;
        args = form
          ? global.CitryVueEvents.collectFormArgs(form, new Set())
          : {};
      }
      plain(args, "Citry Events arguments");
      return args;
    };
    definitionRegistry(appId).eventDispatch = async (record, bindingId, event, authoredArgs) => {
      const {binding, source} = resolveDeclarativeEvent(record, bindingId);
      if (binding.event !== event.type) throw new Error("Citry Events binding is missing or stale");
      const args = declarativeEventArgs(event, authoredArgs);
      if (binding.debounce === null && binding.throttle === null)
        return sendDeclarativeEvent(record, binding, source, args);
      const element = event.currentTarget;
      if (!(element instanceof Element)) throw new Error("timed component-boundary Events bindings are not supported");
      if (!timingDirectiveOwns(element, record, bindingId, binding))
        throw new Error("Citry timed Events binding has no authenticated element lifecycle");
      const capturedArgs = cloneJsonValue(args, "Citry Events arguments");
      const lifetime = eventTimingLifetime(record, element, bindingId, binding);
      if (binding.throttle !== null) {
        const now = performance.now();
        if (now - lifetime.last < binding.throttle) return undefined;
        lifetime.last = now;
      }
      if (binding.debounce !== null) {
        if (lifetime.timer) clearTimeout(lifetime.timer);
        lifetime.resolve?.(undefined);
        return await new Promise((resolve, reject) => {
          lifetime.resolve = resolve;
          scheduleDelay(lifetime, binding.debounce, () => {
            const currentBinding = lifetime.binding;
            lifetime.resolve = undefined;
            if (!timedBindingIsCurrent(record, element, bindingId, currentBinding)) {
              releaseEventTiming(lifetime);
              resolve(undefined);
              return;
            }
            const remainingThrottle = currentBinding.throttle === null
              ? 0 : currentBinding.throttle - (performance.now() - lifetime.last);
            if (remainingThrottle > 0)
              scheduleDelay(lifetime, remainingThrottle, () => releaseEventTiming(lifetime));
            else releaseEventTiming(lifetime);
            void sendDeclarativeEvent(record, currentBinding, source, capturedArgs).then(resolve, reject);
          });
        });
      }
      if (!timedBindingIsCurrent(record, element, bindingId, binding)) {
        finishEventTiming(lifetime, undefined);
        return undefined;
      }
      if (lifetime.timer) {
        clearTimeout(lifetime.timer);
        lifetime.timer = 0;
      }
      scheduleDelay(lifetime, binding.throttle, () => releaseEventTiming(lifetime));
      return sendDeclarativeEvent(record, binding, source, capturedArgs);
    };
    definitionRegistry(appId).eventDispatchComponent = async (record, bindingId, emittedValue, authoredArgs) => {
      const {binding, source} = resolveDeclarativeEvent(record, bindingId);
      const args = declarativeEventArgs(emittedValue, authoredArgs);
      if (binding.debounce !== null || binding.throttle !== null)
        throw new Error("timed component-boundary Events bindings are not supported");
      return sendDeclarativeEvent(record, binding, source, args);
    };
    definitionRegistry(appId).eventPoll = async (record, bindingId, args) => {
      if (record.app !== definitionRegistry(appId) || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry polling source is stale or retired");
      const binding = record.live.value?.preparedData?.pollBindings?.[bindingId];
      if (!binding) throw new Error("Citry polling binding is missing or stale");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry polling binding has no mounted Vue owner");
      return sendDeclarativeEvent(record, binding, source, args);
    };
    definitionRegistry(appId).eventSend = async (record, handler, args, opts) => {
      if (record.app !== ownedApp || ownedApp.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events source is stale or retired");
      const checkedArgs = args === undefined ? {} : args;
      plain(checkedArgs, "Citry Events arguments");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry Events call has no mounted Vue owner");
      const options = opts === undefined ? undefined : opts && typeof opts === "object" ? {timeout: opts.timeout} : opts;
      return ensureEventsBridge().send({source, handler, args: checkedArgs, options});
    };
    ownedApp.resolvePublicTarget = sourceForTarget;
    ownedApp.publicSend = (source, handler, args, opts) => {
      const mounted = ownedApp.mounted.get(source.stableId);
      if (!mounted || mounted.record.generation !== source.generation)
        return Promise.reject(new Error("Citry.events.send target is stale or retired."));
      requireEventHandler(mounted.record, handler);
      const checkedArgs = args === undefined ? {} : args;
      plain(checkedArgs, "Citry Events arguments");
      const options = opts === undefined ? undefined : opts && typeof opts === "object" ? {timeout: opts.timeout} : opts;
      return ensureEventsBridge().send({source, handler, args: checkedArgs, options});
    };
    ownedApp.publicApplyActions = (actions, source) => ensureEventsBridge().applyActions(actions, source);
    attachPreparedHost(appId, {
      onOccurrenceMounted({stableId, generation, occurrence}) {
        sources.set(stableId, {stableId, generation});
        const mounted = ownedApp.mounted.get(stableId);
        if (mounted?.record.generation === generation)
          { mounted.record.events.descriptor = occurrence.eventContext?.descriptor || null;
            mounted.record.state.adopt(occurrence.eventContext); }
        if (occurrence.eventContext) contexts.set(stableId, occurrence.eventContext);
      },
      onOccurrenceUnmounted({stableId, generation, acceptedTransaction}) {
        const source = sources.get(stableId);
        if (!source || source.generation !== generation) return;
        bridge?.retire(source, acceptedTransaction);
        sources.delete(stableId);
        contexts.delete(stableId);
      },
      beforeServerCallbacks({mounted}) {
        if ([...ownedApp.occurrences.values()].some(occurrence => occurrence.eventContext)) ensureEventsBridge();
        for (const id of sources.keys()) if (!definitionRegistry(appId).occurrences.has(id)) { sources.delete(id); contexts.delete(id); }
        for (const {stableId, generation, occurrence, adoptContext = true} of mounted) {
          sources.set(stableId, {stableId, generation});
          const current = ownedApp.mounted.get(stableId);
          if (adoptContext && current?.record.generation === generation)
            { current.record.events.descriptor = occurrence.eventContext?.descriptor || null;
              current.record.state.adopt(occurrence.eventContext); }
          if (adoptContext) {
            if (occurrence.eventContext) contexts.set(stableId, occurrence.eventContext);
            else contexts.delete(stableId);
          }
        }
      },
    });
    const root = manifest.occurrences.find(item => item.id === manifest.rootId);
    const vueApp = V.createApp(componentTypes[root.typeKey], {citryId: root.id});
    vueApp.component("citry-opaque-html", opaqueHtmlComponent);
    vueApp.directive("citry-control", {
      mounted(element, binding) {
        if (binding.value.length) installControls(element, binding.value);
      },
      updated(element, binding) {
        if (!binding.value.length) { disposeControl(element); return; }
        const lifetime = controlLifetimes.get(element);
        if (!lifetime || lifetime.handles !== binding.value || lifetime.signature !== controlSignature(element, binding.value))
          installControls(element, binding.value);
        else for (const handle of binding.value) applyControlValue(element, handle.record.state.facade[handle.spec.field]);
      },
      beforeUnmount(element) { disposeControl(element); },
    });
    vueApp.directive("citry-vue-owned", {
      mounted(element, binding) { setVueOwnedNativeProperties(element, binding.value); },
      beforeUpdate(element, binding) {
        if (Array.isArray(binding.value) && binding.value.length === 0) {
          const snapshot = captureNativeControlState(element);
          if (snapshot.length) nativeControlUpdateSnapshots.set(element, snapshot);
        }
      },
      updated(element, binding) {
        setVueOwnedNativeProperties(element, binding.value);
        const snapshot = nativeControlUpdateSnapshots.get(element);
        nativeControlUpdateSnapshots.delete(element);
        if (snapshot) restoreNativeControlState(snapshot);
      },
      beforeUnmount(element) { vueOwnedNativeProperties.delete(element); },
    });
    const runtimeEventLifetimes = new WeakMap();
    const disposeRuntimeEvents = element => {
      const lifetime = runtimeEventLifetimes.get(element);
      if (!lifetime) return;
      for (const item of lifetime.values()) element.removeEventListener(item.event, item.listener);
      const timed = runtimeEventTimingDirectives.get(element);
      disposeElementEventTimings(element, timed);
      runtimeEventTimingDirectives.delete(element);
      runtimeEventLifetimes.delete(element);
    };
    const runtimeEventSignature = eventTimingSignature;
    const runtimeTimingSignature = handle => {
      if (handle.kind === "event") return "event:" + runtimeEventSignature(handle);
      const spec = handle.spec;
      return JSON.stringify([
        "poll",
        handle.record.occurrenceId,
        handle.record.generation,
        handle.id,
        spec.handler,
        spec.args,
        spec.interval,
      ]);
    };
    const reconcileRuntimeEventTimings = (element, handles) => {
      const prior = runtimeEventTimingDirectives.get(element) || [];
      const current = Object.freeze(handles);
      runtimeEventTimingDirectives.set(element, current);
      const currentByKey = new Map(current.map(handle => [handle.kind + ":" + handle.id, handle]));
      const retained = new Set();
      for (const old of prior) {
        const replacement = currentByKey.get(old.kind + ":" + old.id);
        if (replacement && replacement.record === old.record &&
            runtimeTimingSignature(replacement) === runtimeTimingSignature(old)) {
          const lifetime = eventTimingLifetimes.get(element)?.get(old.id);
          if (lifetime?.record === old.record && lifetime.binding === old.spec) {
            lifetime.binding = replacement.spec;
            lifetime.args = replacement.args;
            retained.add(replacement);
          } else if (old.kind === "event") {
            retained.add(replacement);
          }
          continue;
        }
        disposeElementEventTimings(element, [old]);
      }
      for (const handle of current) {
        if (handle.kind === "poll" && !retained.has(handle)) registerPoll(element, handle);
      }
    };
    const installRuntimeEvents = (element, handles) => {
      const prior = runtimeEventLifetimes.get(element) || new Map();
      const current = new Map();
      for (const handle of handles.filter(handle => handle.kind === "event")) {
        const spec = handle.spec;
        const signature = runtimeEventSignature(handle);
        const retained = prior.get(handle.id);
        if (retained?.signature === signature) { current.set(handle.id, retained); continue; }
        if (retained) element.removeEventListener(retained.event, retained.listener);
        let listener = event => {
          let dispatched;
          try { dispatched = handle.record.app.eventDispatch(handle.record, handle.id, event, undefined); }
          catch (error) {
            handle.record.app.vueApp.config.errorHandler(error, handle.record.app.mounted.get(handle.record.occurrenceId)?.component, "Citry runtime event");
            return;
          }
          Promise.resolve(dispatched).catch(error => handle.record.app.vueApp.config.errorHandler(
            error, handle.record.app.mounted.get(handle.record.occurrenceId)?.component, "Citry runtime event"));
        };
        const modifiers = ["prevent", "stop", "self"].filter(name => spec[name] === true);
        if (modifiers.length) listener = V.withModifiers(listener, modifiers);
        if (spec.key !== null) listener = V.withKeys(listener, [spec.key]);
        element.addEventListener(spec.event, listener, spec.once === true ? {once:true} : undefined);
        current.set(handle.id, {event:spec.event, listener, signature});
      }
      for (const [id, item] of prior) if (!current.has(id)) element.removeEventListener(item.event, item.listener);
      const timed = handles.filter(handle => handle.kind === "poll" ||
        handle.spec.debounce !== null || handle.spec.throttle !== null);
      reconcileRuntimeEventTimings(element, timed);
      runtimeEventLifetimes.set(element, current);
    };
    vueApp.directive("citry-runtime-events", {
      mounted(element, binding) { installRuntimeEvents(element, binding.value); },
      updated(element, binding) { installRuntimeEvents(element, binding.value); },
      beforeUnmount(element) { disposeRuntimeEvents(element); },
    });
    vueApp.directive("citry-event-timing", {
      mounted(element, binding) { reconcileEventTimings(element, binding.value); },
      updated(element, binding) { reconcileEventTimings(element, binding.value); },
      beforeUnmount(element) {
        const handles = eventTimingDirectives.get(element);
        disposeElementEventTimings(element, handles);
        eventTimingDirectives.delete(element);
      },
    });
    vueApp.config.globalProperties.$loading = function (name) {
      const current = V.getCurrentInstance?.();
      const record = instanceRecords.get(this) || instanceRecords.get(this?.$?.proxy) ||
        instanceRecords.get(current?.proxy) || instanceRecords.get(current?.ctx);
      if (!record) throw new Error("$loading is unavailable outside a Citry Vue component");
      return record.events.loading(name);
    };
    vueApp.config.globalProperties.$error = function (name) {
      const current = V.getCurrentInstance?.();
      const record = instanceRecords.get(this) || instanceRecords.get(this?.$?.proxy) ||
        instanceRecords.get(current?.proxy) || instanceRecords.get(current?.ctx);
      if (!record) throw new Error("$error is unavailable outside a Citry Vue component");
      return record.events.error(name);
    };
    let initialPublished = false;
    try {
      lifecycle?.guard();
      for (const {plugin} of plugins.values()) vueApp.use(plugin);
      for (const [typeKey, type] of Object.entries(componentTypes)) {
        const tag = initialTypeTags.get(typeKey);
        if (typeof tag !== "string") throw new Error("prepared component type has no registered tag");
        definitionRegistry(appId).typeTags.set(typeKey, tag);
        vueApp.component(tag, type);
      }
      attachVueApp(appId, vueApp);
      lifecycle?.guard();
      vueApp.mount(hostElement);
      await waitForStartup(whenReady(appId), lifecycle);
      initialPublished = true;
      for (const {plugin, stage} of plugins.values()) plugin.commitRevision(stage);
      definitionRegistry(appId).initialPluginStages = [];
    } catch (error) {
      ownedApp.terminal = true;
      cleanupEventAttempt(staged, error);
      bridge?.dispose?.();
      if (!initialPublished) cleanupPluginStages(plugins.values(), "rollbackRevision");
      definitionRegistry(appId).initialPluginStages = [];
      try { vueApp.unmount(); } catch (unmountError) {
        console.error("[Citry] failed to dispose a rejected Vue app:", unmountError);
      }
      for (const {plugin} of plugins.values()) {
        try { plugin.dispose(); } catch (disposeError) { console.error("[Citry] browser plugin dispose failed:", disposeError); }
      }
      releaseAppStyles(appId);
      releaseAppScripts(appId);
      apps.delete(appId);
      throw error;
    }
    document.dispatchEvent(new CustomEvent("citry:ready", {detail: {appId, revision: definitionRegistry(appId).revision}}));
    const nativeUnmount = vueApp.unmount.bind(vueApp);
    let disposed = false;
    vueApp.unmount = () => {
      if (disposed) return;
      disposed = true;
      ownedApp.terminal = true;
      cleanupEventAttempt(staged, new Error("Vue app was disposed"));
      bridge?.dispose?.();
      try { nativeUnmount(); }
      finally {
        const current = apps.get(appId);
        if (current?.vueApp === vueApp) current.mounted.clear();
        for (const {plugin} of plugins.values()) {
          try { plugin.dispose(); } catch (error) { console.error("[Citry] browser plugin dispose failed:", error); }
        }
        if (apps.get(appId) === ownedApp) {
          releaseAppStyles(appId);
          releaseAppScripts(appId);
          apps.delete(appId);
        }
      }
    };
    return Object.freeze({appId, app: vueApp});
  }

  async function startPrepared(configuration, lifecycle) {
    const candidateId = configuration && typeof configuration === "object" && configuration.manifest &&
      typeof configuration.manifest === "object" ? configuration.manifest.appId : null;
    const startAttempt = Object.freeze({});
    try {
      return await startPreparedOwned(configuration, lifecycle, startAttempt);
    } catch (error) {
      const created = typeof candidateId === "string" ? apps.get(candidateId) : undefined;
      if (created?.startAttempt === startAttempt) {
        for (const item of [...(created.initialPluginStages || [])].reverse()) {
          try { item.plugin.rollbackRevision(item.stage); }
          catch (rollbackError) { console.error("[Citry] browser plugin rollbackRevision failed:", rollbackError); }
        }
        created.initialPluginStages = [];
        try { created.vueApp?.unmount(); } catch (unmountError) {
          console.error("[Citry] rejected Vue app disposal failed:", unmountError);
        }
        for (const plugin of created.browserPlugins) {
          try { plugin.dispose(); } catch (disposeError) {
            console.error("[Citry] rejected browser plugin disposal failed:", disposeError);
          }
        }
        if (apps.get(candidateId) === created) apps.delete(candidateId);
        releaseAppStyles(candidateId);
        releaseAppScripts(candidateId);
      }
      throw error;
    }
  }

  function disposeCallbacks(record, options = {}) {
    const scope = record.callbackScope, cleanup = record.callbackCleanup;
    const subscriptions = record.callbackSubscriptions;
    record.callbackScope = undefined; record.callbackCleanup = undefined; record.callbackSubscriptions = undefined;
    let error;
    try { scope?.stop(); } catch (caught) { error = caught; }
    for (const unsubscribe of subscriptions || []) {
      try { unsubscribe(); }
      catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] callback event cleanup failed:", caught); }
    }
    try {
      if (cleanup) {
        if (options.handoff === true && cleanup.supportsHandoff === true) cleanup(options);
        else cleanup();
      }
    }
    catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] callback cleanup failed:", caught); }
    if (error !== undefined) throw error;
  }
  function subscribeRecordEvent(record, name, handler) {
    const unsubscribe = record.events.subscribe(name, handler);
    const subscriptions = record.callbackSubscriptions;
    if (!subscriptions) return unsubscribe;
    let active = true;
    const off = () => {
      if (!active) return;
      active = false;
      subscriptions.delete(off);
      unsubscribe();
    };
    subscriptions.add(off);
    return off;
  }
  function dispose(record) {
    disposeEventTimings(record);
    record.events?.dispose?.();
    disposeCallbacks(record);
  }
  async function runCallback(component, record, callback, revision) {
    if (!callback) return;
    const scope = V.effectScope(true);
    const subscriptions = new Set();
    record.callbackScope = scope;
    record.callbackSubscriptions = subscriptions;
    try {
      const cleanup = scope.run(() => callback({
        component,
        revision,
        onEvent: (name, handler) => subscribeRecordEvent(record, name, handler),
      }));
      if (cleanup !== undefined && typeof cleanup !== "function") throw new TypeError("onServerRender must return a function or undefined");
      record.callbackCleanup = cleanup;
    } catch (error) {
      scope.stop();
      for (const unsubscribe of subscriptions) unsubscribe();
      record.callbackScope = undefined;
      record.callbackCleanup = undefined;
      record.callbackSubscriptions = undefined;
      throw error;
    }
  }

  async function whenReady(appId) {
    const app = definitionRegistry(appId);
    await V.nextTick();
    while (app.initialTasks.size) {
      await Promise.all([...app.initialTasks]);
      await V.nextTick();
    }
    if (app.terminal) throw app.initialError || new Error("Citry Vue app failed during initialization");
    validateMountedParents(app);
    return app;
  }

  function validateMountedParents(app) {
    for (const [id, mounted] of app.mounted) {
      let parent = mounted.component.$parent;
      while (parent && !instanceRecords.has(parent)) parent = parent.$parent;
      const actualParentId = parent ? instanceRecords.get(parent).occurrenceId : null;
      if (actualParentId !== app.occurrences.get(id)?.parentId) {
        throw new Error("mounted Vue parent does not match prepared occurrence parent: " + id);
      }
    }
  }

  function validateIsolatedEnvelope(app, envelope, expectedRootId = null) {
    plain(envelope, "envelope");
    if (envelope.protocol !== "citry-vue-prepared/1" || envelope.appId !== app.id ||
        envelope.baseRevision !== app.revision || envelope.revision !== app.revision + 1 ||
        typeof envelope.rootId !== "string" || expectedRootId !== null && envelope.rootId !== expectedRootId ||
        !Array.isArray(envelope.definitions) || !Array.isArray(envelope.scripts) ||
        !Array.isArray(envelope.styles) || !Array.isArray(envelope.typePolicies) ||
        !Array.isArray(envelope.occurrences) || !Array.isArray(envelope.updatedIds) ||
        !Array.isArray(envelope.replacements) || !Array.isArray(envelope.markers) ||
        own(envelope, "topologyChanges")) throw new Error("stale or malformed envelope");
    const subtree = new Map();
    for (const item of envelope.occurrences) {
      plain(item, "subtree occurrence");
      if (typeof item.id !== "string" || subtree.has(item.id)) throw new Error("invalid or duplicate subtree occurrence");
      subtree.set(item.id, item);
    }
    validateGraph(subtree, envelope.rootId);
    const declaredUpdates = new Set(envelope.updatedIds);
    if (envelope.updatedIds.some(id => typeof id !== "string") ||
        declaredUpdates.size !== envelope.updatedIds.length || declaredUpdates.size !== subtree.size ||
        [...subtree.keys()].some(id => !declaredUpdates.has(id)))
      throw new Error("subtree update ids must exactly cover its snapshot");
    if (envelope.replacements.some(item => !item || !subtree.has(item.ownerId)))
      throw new Error("subtree replacement owner lies outside its snapshot");
    normalizeMarkers(envelope.markers, subtree);
    return subtree;
  }

  function expandSubtreeEnvelope(app, envelope, targetId) {
    const subtree = validateIsolatedEnvelope(app, envelope, targetId);
    if (!app.occurrences.has(targetId)) throw new Error("stale or malformed envelope");
    const removed = new Set();
    for (const id of app.occurrences.keys()) {
      let cursor = id;
      while (cursor !== null && cursor !== targetId) cursor = app.occurrences.get(cursor)?.parentId ?? null;
      if (cursor === targetId) removed.add(id);
    }
    const combined = new Map([...app.occurrences].filter(([id]) => !removed.has(id)));
    for (const id of subtree.keys()) if (combined.has(id)) throw new Error("subtree occurrence collides outside its target");
    const existingTarget = app.occurrences.get(targetId);
    for (const [id, item] of subtree) combined.set(id, id === targetId ? {
      ...item, parentId: existingTarget.parentId, placementKey: existingTarget.placementKey,
    } : item);
    const markers = [
      ...[...app.markers.values()].filter(item => item.occurrenceId === targetId || !removed.has(item.occurrenceId)),
      ...envelope.markers.filter(item => item.occurrenceId !== targetId),
    ].sort((a,b) => {
      const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
      const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
      return left < right ? -1 : left > right ? 1 : 0;
    });
    normalizeMarkers(markers, combined);
    return {...envelope, rootId: app.rootId, occurrences: [...combined.values()], markers};
  }

  function validateActions(app, envelope, targetId) {
    return validateCombinedActions(app, expandSubtreeEnvelope(app, envelope, targetId));
  }

  function validateCombinedActions(app, envelope) {
    plain(envelope, "combined envelope");
    if (envelope.protocol !== "citry-vue-prepared/1" || envelope.appId !== app.id ||
        envelope.baseRevision !== app.revision || envelope.revision !== app.revision + 1 ||
        envelope.rootId !== app.rootId || !Array.isArray(envelope.definitions) ||
        !Array.isArray(envelope.scripts) || !Array.isArray(envelope.styles) ||
        !Array.isArray(envelope.typePolicies) || !Array.isArray(envelope.occurrences) ||
        !Array.isArray(envelope.updatedIds) || !Array.isArray(envelope.replacements) ||
        !Array.isArray(envelope.markers) || own(envelope, "topologyChanges"))
      throw new Error("stale or malformed combined envelope");
    const incoming = new Map(envelope.occurrences.map(item => [item.id, item]));
    normalizeMarkers(envelope.markers, incoming);
    const staged = [], ids = new Set(), updatedIds = new Set(), nextDefinitionTypes = new Map(app.definitionTypes);
    for (const id of envelope.updatedIds) { if (typeof id !== "string" || updatedIds.has(id)) throw new Error("invalid updated occurrence ids"); updatedIds.add(id); }
    for (const action of envelope.occurrences) {
      plain(action, "occurrence action");
      if (typeof action.id !== "string" || typeof action.typeKey !== "string" || typeof action.definitionId !== "string" || (action.parentId !== null && typeof action.parentId !== "string") || (action.placementKey !== null && typeof action.placementKey !== "string") || !own(action, "serverData")) throw new TypeError("invalid occurrence action");
      plain(action.serverData, "serverData");
      plain(action.preparedData, "preparedData");
      if (ids.has(action.id)) throw new Error("duplicate occurrence action"); ids.add(action.id);
      const mounted = app.mounted.get(action.id), prepared = app.occurrences.get(action.id), nextDefinition = app.definitions.get(action.definitionId);
      const added = !prepared;
      if ((prepared && (prepared.typeKey !== action.typeKey || prepared.parentId !== action.parentId || prepared.placementKey !== action.placementKey)) || !nextDefinition) throw new Error("unknown occurrence or definition");
      const boundType = nextDefinitionTypes.get(action.definitionId);
      if (boundType && boundType !== action.typeKey) throw new Error("render definition stable-type mismatch");
      nextDefinitionTypes.set(action.definitionId, action.typeKey);
      const definitionChanged = !prepared || prepared.definitionId !== action.definitionId;
      validateOccurrenceCallRuns(incoming, action, nextDefinition);
      if (definitionChanged) {
        const priorDefinition = prepared && app.definitions.get(prepared.definitionId);
        if (!updatedIds.has(action.id) || nextDefinition.target !== ORDINARY_TARGET ||
            (prepared && (!priorDefinition || priorDefinition.target !== ORDINARY_TARGET)))
          throw new Error("incompatible retained render definition");
      }
      const nextKeys = new Set(Object.keys(action.serverData));
      const serverShapeChanged = mounted ? signatureKey([...nextKeys].sort()) !==
        signatureKey([...mounted.record.serverKeys].sort()) : false;
      if (mounted) for (const key of nextKeys) if (!mounted.record.serverKeys.has(key) && (key in mounted.component || key.startsWith("$") || key.startsWith("_"))) throw new Error("later js_data/public collision: " + key);
      const payloadChanged = added || JSON.stringify(prepared.serverData) !== JSON.stringify(action.serverData) || JSON.stringify(prepared.preparedData) !== JSON.stringify(action.preparedData);
      if (payloadChanged && !updatedIds.has(action.id)) throw new Error("changed occurrence missing from updatedIds");
      if (updatedIds.has(action.id)) staged.push({action: clone(action), ...(mounted || {}), nextKeys,
        serverShapeChanged, definitionChanged, nextDefinition, added});
    }
    validateGraph(incoming, app.rootId);
    for (const id of updatedIds) if (!ids.has(id)) throw new Error("unknown explicitly updated occurrence");
    const removed = [];
    for (const id of app.occurrences.keys()) if (!incoming.has(id)) {
      removed.push(id);
    }
    const addedIds = new Set([...incoming.keys()].filter(id => !app.occurrences.has(id)));
    // The browser owns the only authoritative accepted baseline. Derive keyed
    // replacement declarations from that baseline and the incoming occurrence
    // graph instead of relying on process-local server revision history. A
    // server may still send declarations for older clients, but they must
    // exactly agree with this derivation.
    const derivedReplacements = [];
    for (const item of staged.filter(item => item.definitionChanged && !item.added)) {
      const priorOccurrence = app.occurrences.get(item.action.id);
      const priorDefinition = app.definitions.get(priorOccurrence.definitionId);
      if (!priorDefinition) throw new Error("retained occurrence has no prior render definition");
      const before = new Map(priorDefinition.replacementSites.map(site => [site.siteId, site]));
      const after = new Map(item.nextDefinition.replacementSites.map(site => [site.siteId, site]));
      const changed = [...new Set([...before.keys(), ...after.keys()])]
        .filter(id => before.get(id)?.key !== after.get(id)?.key).sort();
      const siteRecords = [];
      for (const siteId of changed) {
        const expectedForSite = new Set();
        const coveredBySite = new Set();
        for (const [site, occurrence] of [[before.get(siteId), priorOccurrence],
          [after.get(siteId), incoming.get(item.action.id)]]) {
          if (!site) continue;
          for (const localId of site.localDescendants) {
            const call = occurrence.preparedData.calls[localId];
            if (!call) throw new Error("replacement site references an absent ordinary local call");
            coveredBySite.add(call.id);
            if (incoming.has(call.id) && app.mounted.has(call.id)) expectedForSite.add(call.id);
          }
          for (const runId of site.localDescendantRuns) {
            for (const id of occurrence.preparedData.callRuns[runId]) {
              coveredBySite.add(id);
              if (incoming.has(id) && app.mounted.has(id)) expectedForSite.add(id);
            }
          }
        }
        siteRecords.push({ownerId: item.action.id, siteId, coveredBySite, expectedForSite});
      }
      // A lifecycle directive can be nested inside another changed directive
      // in one definition.  Both metadata records then mention the same
      // mounted component, but one remount must account for it only once.  A
      // larger local coverage identifies the enclosing site; equal coverage
      // falls back to the stable site order because the wire format carries
      // no source path.
      const assigned = new Map();
      for (const record of siteRecords) {
        for (const id of record.expectedForSite) {
          const candidates = siteRecords.filter(candidate => candidate.expectedForSite.has(id));
          candidates.sort((left, right) => right.coveredBySite.size - left.coveredBySite.size ||
            (left.siteId < right.siteId ? -1 : left.siteId > right.siteId ? 1 : 0));
          const owner = candidates[0];
          if (!assigned.has(owner.siteId)) assigned.set(owner.siteId, new Set());
          assigned.get(owner.siteId).add(id);
        }
      }
      for (const record of siteRecords) {
        derivedReplacements.push({ownerId: record.ownerId, siteId: record.siteId,
          expectedRemountIds: [...(assigned.get(record.siteId) || [])].sort()});
      }
    }
    const replacementSortKey = value => value && typeof value === "object" && !Array.isArray(value)
      ? [typeof value.ownerId === "string" ? value.ownerId : "", typeof value.siteId === "string" ? value.siteId : ""]
      : ["", ""];
    const compareReplacementDeclarations = (left, right) => {
      const [leftOwner, leftSite] = replacementSortKey(left), [rightOwner, rightSite] = replacementSortKey(right);
      if (leftOwner !== rightOwner) return leftOwner < rightOwner ? -1 : 1;
      if (leftSite !== rightSite) return leftSite < rightSite ? -1 : 1;
      return 0;
    };
    // The generated declarations follow occurrence traversal order, which is
    // not a protocol ordering guarantee.  Keep the derived effective list in
    // the same strict order required of supplied declarations.
    derivedReplacements.sort(compareReplacementDeclarations);
    const suppliedReplacements = envelope.replacements;
    // Compatibility is set-like with respect to declaration order, while the
    // effective supplied list remains ordered and is checked below.  This lets
    // an older server send the same valid declarations in a different
    // traversal order without weakening the wire-order invariant.
    const replacementSignature = values => signatureKey(values.map(value => value && typeof value === "object" && !Array.isArray(value)
      ? {ownerId: value.ownerId, siteId: value.siteId, expectedRemountIds: value.expectedRemountIds}
      : value).sort(compareReplacementDeclarations));
    if (suppliedReplacements.length !== 0 &&
        replacementSignature(suppliedReplacements) !== replacementSignature(derivedReplacements))
      throw new Error("replacement metadata does not match client derivation");
    const replacements = suppliedReplacements.length === 0 ? derivedReplacements : suppliedReplacements;
    const derivedReplacementByKey = new Map(derivedReplacements.map(replacement =>
      [JSON.stringify([replacement.ownerId, replacement.siteId]), replacement]));
    const expectedRemountIds = new Set(), replacementSites = new Set();
    let priorReplacementOwner, priorReplacementSite;
    for (const replacement of replacements) {
      plain(replacement, "replacement");
      if (Object.keys(replacement).sort().join(",") !== "expectedRemountIds,ownerId,siteId" ||
          typeof replacement.ownerId !== "string" || typeof replacement.siteId !== "string" || !Array.isArray(replacement.expectedRemountIds))
        throw new Error("invalid replacement metadata");
      const siteKey = JSON.stringify([replacement.ownerId, replacement.siteId]);
      if (replacementSites.has(siteKey)) throw new Error("duplicate replacement site");
      replacementSites.add(siteKey);
      if (priorReplacementOwner !== undefined && (replacement.ownerId < priorReplacementOwner ||
          (replacement.ownerId === priorReplacementOwner && replacement.siteId <= priorReplacementSite)))
        throw new Error("replacement sites must be sorted");
      priorReplacementOwner = replacement.ownerId;
      priorReplacementSite = replacement.siteId;
      const ownerStage = staged.find(item => item.action.id === replacement.ownerId);
      if (!ownerStage?.definitionChanged) throw new Error("replacement owner must have a changed definition");
      const declaredSite = ownerStage.nextDefinition.replacementSites.find(item => item.siteId === replacement.siteId);
      const priorSite = app.definitions.get(app.occurrences.get(replacement.ownerId).definitionId)
        .replacementSites.find(item => item.siteId === replacement.siteId);
      if (!declaredSite && !priorSite) throw new Error("replacement site is absent from both definitions");
      const derivedReplacement = derivedReplacementByKey.get(siteKey);
      if (!derivedReplacement || signatureKey(replacement.expectedRemountIds) !==
          signatureKey(derivedReplacement.expectedRemountIds))
        throw new Error("expected remount ids do not match replacement descendant runs");
      let priorRemountId = "";
      for (const id of replacement.expectedRemountIds) {
        if (typeof id !== "string" || expectedRemountIds.has(id) || !incoming.has(id) || id === replacement.ownerId)
          throw new Error("invalid expected remount id");
        if (priorRemountId && id < priorRemountId) throw new Error("expected remount ids must be sorted");
        priorRemountId = id;
        let cursor = incoming.get(id).parentId, descendant = false;
        while (cursor !== null) {
          if (cursor === replacement.ownerId) { descendant = true; break; }
          cursor = incoming.get(cursor).parentId;
        }
        if (!descendant || !app.mounted.has(id)) throw new Error("expected remount is not a mounted descendant");
        expectedRemountIds.add(id);
      }
    }
    for (const item of staged.filter(item => item.definitionChanged && !item.added)) {
      const prior = app.definitions.get(app.occurrences.get(item.action.id).definitionId);
      const before = new Map(prior.replacementSites.map(site => [site.siteId, site.key]));
      const after = new Map(item.nextDefinition.replacementSites.map(site => [site.siteId, site.key]));
      const changed = [...new Set([...before.keys(), ...after.keys()])].filter(id => before.get(id) !== after.get(id)).sort();
      const declared = replacements.filter(entry => entry.ownerId === item.action.id).map(entry => entry.siteId).sort();
      if (signatureKey(changed) !== signatureKey(declared))
        throw new Error("replacement metadata does not match changed definition sites: " + item.action.id);
      const beforeDirectives = new Map(prior.directiveSignature.map(value => [value.siteId, signatureKey(value)]));
      const afterDirectives = new Map(item.nextDefinition.directiveSignature.map(value => [value.siteId, signatureKey(value)]));
      const changedDirectives = [...new Set([...beforeDirectives.keys(), ...afterDirectives.keys()])]
        .filter(id => beforeDirectives.get(id) !== afterDirectives.get(id));
      if (changedDirectives.some(id => !declared.some(site => id.startsWith(site + "D"))))
        throw new Error("runtime directive change is outside a declared keyed replacement site");
    }
    const expectedNewIds = addedIds;
    return {snapshot: envelope, staged, removed, nextDefinitionTypes, expectedRemountIds, expectedNewIds};
  }

  function registerIncomingTypes(app, snapshot) {
    const incomingTypes = new Set(snapshot.occurrences.map(item => item.typeKey));
    const pending = [];
    for (const typeKey of incomingTypes) {
      if (app.types.has(typeKey)) continue;
      if (!app.vueApp) throw new Error("new prepared component type requires an attached Vue app");
      const tags = new Set();
      for (const definition of app.definitions.values()) {
        for (const call of [...definition.localCalls, ...definition.localCallRuns])
          if (call.typeKey === typeKey) tags.add(call.componentTag);
      }
      if (tags.size !== 1) throw new Error("new prepared component type has no unique component tag");
      const tag = [...tags][0];
      const priorType = [...app.typeTags].find(([, value]) => value === tag)?.[0];
      if (priorType && priorType !== typeKey) throw new Error("prepared component tag is already registered to another type");
      pending.push({typeKey, tag});
    }
    const prepared = [];
    for (const {typeKey, tag} of pending) {
      let options = registeredTypeOptions.get(typeKey)?.options || {};
      for (const plugin of app.browserPlugins) if (typeof plugin.decorateTypeOptions === "function")
        options = plugin.decorateTypeOptions(typeKey, options);
      const callback = options.onServerRender;
      const type = V.defineComponent(typeOptions(app.id, typeKey, options));
      type.__citryCallback = callback;
      prepared.push({typeKey, tag, type});
    }
    for (const {typeKey, tag, type} of prepared) {
      app.types.set(typeKey, type);
      app.typeTags.set(typeKey, tag);
      app.vueApp.component(tag, type);
    }
  }

  function isNativeControl(value) {
    return typeof HTMLInputElement === "function" && value instanceof HTMLInputElement ||
      typeof HTMLTextAreaElement === "function" && value instanceof HTMLTextAreaElement ||
      typeof HTMLSelectElement === "function" && value instanceof HTMLSelectElement;
  }

  function nativeControlElements(root) {
    if (typeof Element !== "function" || !(root instanceof Element)) return [];
    const elements = [];
    if (isNativeControl(root)) elements.push(root);
    elements.push(...root.querySelectorAll("input,textarea,select"));
    return elements;
  }

  function nativeOwnedProperties(element) {
    const properties = new Set(vueOwnedNativeProperties.get(element) || []);
    const tag = element.tagName.toLowerCase();
    if (controlLifetimes.has(element)) {
      if (tag === "select") properties.add("selected");
      else if (tag === "textarea") properties.add("value");
      else if (tag === "input") {
        const type = element.type.toLowerCase();
        properties.add(type === "checkbox" || type === "radio" ? "checked" : "value");
      }
    }
    if (tag === "select" && properties.has("selected") === false) {
      for (const option of element.options) {
        const owned = vueOwnedNativeProperties.get(option) || [];
        if (owned.includes("selected") || owned.includes("value")) {
          properties.add("selected");
          break;
        }
      }
    }
    return properties;
  }

  function captureNativeControlState(root) {
    const snapshots = [];
    for (const element of nativeControlElements(root)) {
      const owned = nativeOwnedProperties(element);
      if (typeof HTMLInputElement === "function" && element instanceof HTMLInputElement) {
        const type = element.type.toLowerCase();
        if (type === "file") continue;
        if ((type === "checkbox" || type === "radio") && !owned.has("checked") &&
            element.checked !== element.defaultChecked) {
          snapshots.push({root, element, kind: "checked", baseline: element.defaultChecked, value: element.checked});
        }
        if (!owned.has("value") && element.value !== element.defaultValue)
          snapshots.push({root, element, kind: "value", baseline: element.defaultValue, value: element.value});
        continue;
      }
      if (typeof HTMLTextAreaElement === "function" && element instanceof HTMLTextAreaElement) {
        if (!owned.has("value") && element.value !== element.defaultValue)
          snapshots.push({root, element, kind: "value", baseline: element.defaultValue, value: element.value});
        continue;
      }
      if (owned.has("selected")) continue;
      const options = [...element.options];
      const values = options.map(option => option.value);
      const selected = options.map(option => option.selected);
      const defaults = options.map(option => option.defaultSelected);
      if (selected.some((value, index) => value !== defaults[index]))
        snapshots.push({root, element, kind: "selected", values, defaults, selected});
    }
    return snapshots;
  }

  function restoreNativeControlState(snapshots) {
    for (const snapshot of snapshots || []) {
      const {root, element} = snapshot;
      if (typeof Element !== "function" || !(root instanceof Element) || !root.isConnected ||
          !element.isConnected || !root.contains(element)) continue;
      const owned = nativeOwnedProperties(element);
      if (owned.has(snapshot.kind)) continue;
      if (snapshot.kind === "value" && "value" in element) {
        element.value = element.defaultValue === snapshot.baseline ? snapshot.value : element.defaultValue;
      }
      else if (snapshot.kind === "checked" && "checked" in element) {
        element.checked = element.defaultChecked === snapshot.baseline ? snapshot.value : element.defaultChecked;
      }
      else if (snapshot.kind === "selected" && typeof HTMLSelectElement === "function" &&
          element instanceof HTMLSelectElement) {
        const options = [...element.options];
        const unchanged = options.length === snapshot.values.length &&
          !options.some((option, index) => option.value !== snapshot.values[index] ||
            option.defaultSelected !== snapshot.defaults[index]);
        options.forEach((option, index) => {
          option.selected = unchanged ? snapshot.selected[index] : option.defaultSelected;
        });
      }
    }
  }

  function captureFocusForPublication() {
    const element = document.activeElement;
    // Body/document focus is the browser's unfocused sentinel, so only retain a user control.
    if (typeof HTMLElement !== "function" || !(element instanceof HTMLElement) ||
        element === document.body || element === document.documentElement)
      return null;
    const isTextControl = (typeof HTMLInputElement === "function" && element instanceof HTMLInputElement) ||
      (typeof HTMLTextAreaElement === "function" && element instanceof HTMLTextAreaElement);
    if (!isTextControl) return null;
    const snapshot = {element, selection: null};
    if (isTextControl) {
      // Keyed moves can clear an active control's range while Vue temporarily detaches it.
      const start = element.selectionStart, end = element.selectionEnd;
      if (Number.isInteger(start) && Number.isInteger(end)) {
        snapshot.selection = {
          start,
          end,
          direction: typeof element.selectionDirection === "string" ? element.selectionDirection : null,
        };
      }
    }
    return snapshot;
  }

  function restoreFocusAfterPublication(snapshot) {
    const element = snapshot?.element;
    if (!element?.isConnected) return;
    const current = document.activeElement;
    const focusWasLost = current === null || current === document || current === document.body ||
      current === document.documentElement;
    // A move to another connected element wins over the focus captured for this render.
    if (!focusWasLost && current !== element) return;
    if (current !== element) {
      try { element.focus({preventScroll: true}); }
      catch (_) { return; }
    }
    const selection = snapshot.selection;
    if (!selection || typeof element.setSelectionRange !== "function") return;
    // Server data may shorten the value, so keep the old range inside its new bounds.
    const length = typeof element.value === "string" ? element.value.length : 0;
    const start = Math.min(selection.start, length), end = Math.min(selection.end, length);
    try {
      if (selection.direction === null) element.setSelectionRange(start, end);
      else element.setSelectionRange(start, end, selection.direction);
    } catch (_) {
      // A control whose type changed during the render no longer accepts text ranges.
    }
  }

  async function applyEnvelope(appId, envelope, targetId = envelope.rootId, pluginTransaction = null) {
    const app = definitionRegistry(appId);
    if (app.busy) throw new Error("concurrent server render rejected");
    if (app.terminal) throw new Error("Citry Vue app lifecycle is terminal");
    const incoming = clone(envelope);
    if (!Array.isArray(incoming.definitions) || !Array.isArray(incoming.occurrences))
      throw new Error("prepared envelope lacks definitions or occurrences");
    preflightDefinitions(app, incoming.definitions, incoming.occurrences, incoming.rootId);
    const {snapshot, staged, removed, nextDefinitionTypes, expectedRemountIds, expectedNewIds} =
      pluginTransaction?.combined ? validateCombinedActions(app, incoming) : validateActions(app, incoming, targetId);
    app.busy = true;
    const priorMounted = new Map(app.mounted);
    const acceptedRetirementIds = new Set([...expectedRemountIds, ...removed]);
    const oldAcceptedRecords = new Map([...acceptedRetirementIds].map(id => [id, app.mounted.get(id)]));
    app.transaction = {
      expectedRemountIds,
      expectedNewIds,
      acceptedRetirementIds,
      oldAcceptedRecords,
      acceptedTransaction: pluginTransaction?.acceptedTransaction,
      newMounts: new Map(),
    };
    try {
      pluginTransaction?.activate();
      registerIncomingTypes(app, snapshot);
    } catch (error) {
      app.transaction = null;
      app.busy = false;
      throw error;
    }
    try {
      const callbackCleanupRecords = new Set();
      for (const item of staged) if (item.record && !item.added && !expectedRemountIds.has(item.action.id))
        callbackCleanupRecords.add(item.record);
      for (const callbackOwnerId of pluginTransaction?.callbackOwnerIds || []) {
        if (acceptedRetirementIds.has(callbackOwnerId)) continue;
        const owner = app.mounted.get(callbackOwnerId)?.record;
        if (owner) callbackCleanupRecords.add(owner);
      }
      for (const record of callbackCleanupRecords) disposeCallbacks(record, {handoff: true});
      for (const id of removed) { const mounted = app.mounted.get(id); if (mounted) dispose(mounted.record); }
      for (const {action, component, record, nextKeys, added} of staged) {
        if (!record || added || expectedRemountIds.has(action.id)) continue;
        for (const key of record.serverKeys) if (!nextKeys.has(key)) delete component[key];
        for (const key of nextKeys) if (!record.serverKeys.has(key)) installServerKey(component, record, key);
        record.serverKeys = nextKeys;
      }
      for (const item of staged) if (item.record && item.definitionChanged && !item.added && !expectedRemountIds.has(item.action.id)) item.record.definition.value = {id: item.action.definitionId, render: item.nextDefinition.render, cache: []};
      app.occurrences = new Map(snapshot.occurrences.map(item => [item.id, Object.freeze({...clone(item), serverData: clone(item.serverData)})]));
      app.markers = normalizeMarkers(snapshot.markers, app.occurrences);
      app.definitionTypes = nextDefinitionTypes;
      const changedIds = new Set(staged.map(item => item.action.id)), priorLive = app.snapshot.value;
      const nextLive = new Map([...app.occurrences].map(([id,item]) => [id, changedIds.has(id) || expectedRemountIds.has(id) ? {...item, serverData: V.reactive(clone(item.serverData))} : priorLive.get(id)]));
      // Removed instances keep their prior server data until Vue runs beforeUnmount in this flush.
      for (const id of removed) if (priorLive.has(id)) nextLive.set(id, priorLive.get(id));
      const focusSnapshot = captureFocusForPublication();
      const nativeControlSnapshot = captureNativeControlState(app.hostElement);
      app.snapshot.value = nextLive;
      for (const item of staged) if (item.record && !item.added && !expectedRemountIds.has(item.action.id)) item.record.live.value = nextLive.get(item.action.id);
      for (const item of staged) if (item.record && item.serverShapeChanged && !item.added &&
          !expectedRemountIds.has(item.action.id)) item.component.$forceUpdate();
      await V.nextTick();
      restoreNativeControlState(nativeControlSnapshot);
      restoreFocusAfterPublication(focusSnapshot);
      if (app.terminal) throw new Error("render failed after prepared revision publication");
      if (!app.mounted.has(app.rootId) || [...app.mounted.keys()].some(id => !app.occurrences.has(id)) ||
          removed.some(id => app.mounted.has(id))) throw new Error("rendered occurrence set does not match prepared snapshot");
      validateMountedParents(app);
      for (const id of app.mounted.keys())
        if (!expectedRemountIds.has(id) && !expectedNewIds.has(id) && app.mounted.get(id)?.record !== priorMounted.get(id)?.record)
          throw new Error("unexpected descendant remount");
      for (const id of expectedRemountIds) {
        const mounted = app.mounted.get(id), old = oldAcceptedRecords.get(id);
        const observed = app.transaction.newMounts.get(id);
        if (mounted && (mounted.record === old.record || mounted.record.generation <= old.record.generation ||
            !observed || observed.length !== 1 || observed[0] !== mounted.record.generation))
          throw new Error("expected descendant remount did not occur");
      }
      for (const id of expectedNewIds) {
        const mounted = app.mounted.get(id), observed = app.transaction.newMounts.get(id);
        if (mounted && (!observed || observed.length !== 1 || observed[0] !== mounted.record.generation))
          throw new Error("new occurrence mount generation is invalid");
      }
      const expectedMounted = new Set([...expectedRemountIds, ...expectedNewIds]);
      if ([...app.transaction.newMounts.keys()].some(id => !expectedMounted.has(id)))
        throw new Error("unexpected descendant remount occurred");
      if (removed.length) app.snapshot.value = new Map([...app.snapshot.value].filter(([id]) => app.occurrences.has(id)));
      const callbackIds = new Set([...staged.map(item => item.action.id), ...expectedRemountIds,
        ...(pluginTransaction?.callbackOwnerIds || [])]
        .filter(id => app.mounted.has(id)));
      app.revision = snapshot.revision;
      pluginTransaction?.commit();
      if (app.preparedHost) {
        const stagedCallbackIds = new Set([...staged.map(item => item.action.id), ...expectedRemountIds]);
        const mounted = [...callbackIds].map(id => {
          const current = app.mounted.get(id);
          if (!current) throw new Error("prepared callback target is not mounted");
          return {
            stableId: id,
            generation: current.record.generation,
            occurrence: app.occurrences.get(id),
            adoptContext: stagedCallbackIds.has(id),
          };
        });
        await app.preparedHost.beforeServerCallbacks({revision: app.revision, mounted});
      }
      for (const id of callbackIds) {
        const mounted = app.mounted.get(id);
        await runCallback(mounted.component, mounted.record, mounted.component.$options.__citryCallback, app.revision);
      }
      await V.nextTick();
      if (app.terminal) throw new Error("render failed during onServerRender flush");
    } catch (error) {
      app.terminal = true;
      try { app.vueApp?.unmount(); } catch (unmountError) { console.error("[Citry] terminal Vue disposal failed:", unmountError); }
      throw error;
    }
    finally { app.transaction = null; app.busy = false; }
  }

  // Kept private on the stable options so the coordinator invokes the exact type callback.
  const originalDefineType = defineType;
  function defineTypeWithCallback(appId, typeKey, userOptions) {
    const resolvedOptions = userOptions === undefined ? registeredTypeOptions.get(typeKey)?.options || {} : userOptions;
    const callback = resolvedOptions.onServerRender;
    const result = originalDefineType(appId, typeKey, resolvedOptions);
    result.__citryCallback = callback;
    return result;
  }

  global.CitryStable = {configure, registerDefinition, registerTypeOptions, registerBrowserPlugin, defineType: defineTypeWithCallback, startPrepared, attachVueApp, attachPreparedHost, whenReady, applyEnvelope, compilerRuntime, _apps: apps};
  if (!global.CitryVueFragments?.installFragmentManager)
    throw new Error("Citry Vue fragment support is unavailable");
  const fragmentDocumentNonce = document.currentScript?.nonce || document.currentScript?.getAttribute("nonce") || "";
  global.CitryVueFragments.installFragmentManager(
    global.Citry ||= {},
    (node, exceptAppId) => [...apps.values()].some(app => app.id !== exceptAppId &&
      app.hostElement instanceof Element && app.hostElement.contains(node)),
    startPrepared,
    fragmentDocumentNonce,
  );
})(window);

} else {
  if (global.CitryStable.compilerRuntime?.helperContract !== "f30a03c6ab842434ce11a1b4b6eac1d98ecc9d88a33207f373b88d974da3613e") throw new Error("an incompatible Citry Vue runtime is already loaded");
  if (!global.Vue) throw new Error("the existing Citry Vue runtime has no Vue namespace");
}
if (!global.CitryVueEvents) {
/* Citry Vue Events bridge. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events-vue.ts (pnpm run build there). */
var CitryVueEvents=(()=>{var __defProp=Object.defineProperty;var __getOwnPropDesc=Object.getOwnPropertyDescriptor;var __getOwnPropNames=Object.getOwnPropertyNames;var __hasOwnProp=Object.prototype.hasOwnProperty;var __defNormalProp=(obj,key,value)=>key in obj?__defProp(obj,key,{enumerable:true,configurable:true,writable:true,value}):obj[key]=value;var __export=(target,all)=>{for(var name in all)__defProp(target,name,{get:all[name],enumerable:true})};var __copyProps=(to,from,except,desc)=>{if(from&&typeof from==="object"||typeof from==="function"){for(let key of __getOwnPropNames(from))if(!__hasOwnProp.call(to,key)&&key!==except)__defProp(to,key,{get:()=>from[key],enumerable:!(desc=__getOwnPropDesc(from,key))||desc.enumerable})}return to};var __toCommonJS=mod=>__copyProps(__defProp({},"__esModule",{value:true}),mod);var __publicField=(obj,key,value)=>__defNormalProp(obj,typeof key!=="symbol"?key+"":key,value);var citry_events_vue_exports={};__export(citry_events_vue_exports,{assertValidActionList:()=>assertValidActionList2,collectFormArgs:()=>collectFormArgs,createVueEventsBridge:()=>createVueEventsBridge});var ProtocolValueError=class extends TypeError{constructor(issue){super(issue.message);__publicField(this,"issue");this.name="ProtocolValueError";this.issue=issue}};var hasOwn=(value,key)=>Object.prototype.hasOwnProperty.call(value,key);var pointer=(parent,member)=>{const escaped=String(member).replace(/~/g,"~0").replace(/\//g,"~1");return parent?`${parent}/${escaped}`:`/${escaped}`};var isPlainObject=value=>{if(value===null||typeof value!=="object"||Array.isArray(value))return false;const prototype=Object.getPrototypeOf(value);return prototype===Object.prototype||prototype===null};var firstUnknown=(value,allowed)=>Object.keys(value).filter(key=>!allowed.has(key)).sort()[0]??null;var containerIssue=(value,path)=>{if(Object.getOwnPropertySymbols(value).length){return{path,category:"strict_json",message:"The value contains a symbol-keyed property."}}for(const name of Object.getOwnPropertyNames(value)){if(Array.isArray(value)&&name==="length")continue;const descriptor=Object.getOwnPropertyDescriptor(value,name);if(!descriptor?.enumerable||!("value"in descriptor)){return{path:pointer(path,name),category:"strict_json",message:"A JSON property must be an enumerable data property."}}}return null};var validateStrictJson=(value,path="")=>{const stack=[{value,path,leaving:false}];const ancestors=new Set;while(stack.length){const frame=stack.pop();const current=frame.value;if(frame.leaving){ancestors.delete(current);continue}if(current===null||typeof current==="string"||typeof current==="boolean"){continue}if(typeof current==="number"){if(!Number.isFinite(current)){return{path:frame.path,category:"strict_json",message:"The value contains a non-finite number."}}continue}if(typeof current!=="object"){return{path:frame.path,category:"strict_json",message:"The value contains a non-JSON value."}}if(!Array.isArray(current)&&!isPlainObject(current)){return{path:frame.path,category:"strict_json",message:"The value contains a non-JSON object."}}const ownIssue=containerIssue(current,frame.path);if(ownIssue)return ownIssue;if(ancestors.has(current)){return{path:frame.path,category:"strict_json",message:"The value contains a cycle."}}ancestors.add(current);stack.push({value:current,path:frame.path,leaving:true});if(Array.isArray(current)){const names=Object.keys(current);if(names.length!==current.length||names.some((name,index)=>name!==String(index))){return{path:frame.path,category:"strict_json",message:"A JSON array must be dense and carry no named properties."}}for(let index=current.length-1;index>=0;index-=1){stack.push({value:current[index],path:pointer(frame.path,index),leaving:false})}continue}const keys=Object.keys(current).sort().reverse();for(const key of keys){stack.push({value:current[key],path:pointer(frame.path,key),leaving:false})}}return null};var copyJson=value=>{const issue=validateStrictJson(value);if(issue)throw new ProtocolValueError(issue);if(value===null||typeof value!=="object")return value;const copied=Array.isArray(value)?new Array(value.length):{};const stack=[{source:value,target:copied}];while(stack.length){const{source,target}=stack.pop();for(const key of Object.keys(source)){const item=source[key];if(item!==null&&typeof item==="object"){const child=Array.isArray(item)?new Array(item.length):{};Object.defineProperty(target,key,{configurable:true,enumerable:true,value:child,writable:true});stack.push({source:item,target:child})}else{Object.defineProperty(target,key,{configurable:true,enumerable:true,value:item,writable:true})}}}return copied};var PROTOCOL="citry-events/1";var CALLS_LIMIT=16;var ACTION_KINDS=["render","data","state","event","redirect","url"];var SWAPS=["morph","replace","inner","append","prepend","remove","none"];var RENDERERS=["html-fragment/1","vue-prepared/1"];var CAPABILITIES_BASELINE_V1={swaps:["replace","inner","append","prepend","remove","none"],actions:ACTION_KINDS,renderers:["html-fragment/1"]};var ENVELOPE_FIELDS=new Set(["protocol","requestId","capabilities","calls"]);var CALL_FIELDS=new Set(["componentClassId","handlerName","callerRenderId","args","stateToken","stateUpdates","sendSequence"]);var isSafeRenderId=value=>typeof value==="string"&&/^[a-z0-9_-]+$/.test(value);var nonEmptyStringIssue=(value,path,message)=>{if(typeof value!=="string")return{path,category:"type",message};if(!value)return{path,category:"range",message};return null};var integerIssue=(value,path,message)=>{if(typeof value!=="number"||!Number.isInteger(value)){if(typeof value==="number"&&!Number.isFinite(value)){return{path,category:"strict_json",message}}return{path,category:"type",message}}if(value<0)return{path,category:"range",message};return null};var validateCall=(value,path="")=>{const jsonIssue=validateStrictJson(value,path);if(jsonIssue)return jsonIssue;if(!isPlainObject(value)){return{path,category:"type",message:"Each entry of 'calls' must be a call object."}}for(const required of["componentClassId","handlerName","args"]){if(!hasOwn(value,required)){return{path:pointer(path,required),category:"required",message:`The call is missing required field '${required}'.`}}}const unknown=firstUnknown(value,CALL_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:`The call carries unknown field '${unknown}'.`}}for(const field of["componentClassId","handlerName"]){const issue=nonEmptyStringIssue(value[field],pointer(path,field),`The call's '${field}' must be a non-empty string.`);if(issue)return issue}if(hasOwn(value,"callerRenderId")){const issue=nonEmptyStringIssue(value.callerRenderId,pointer(path,"callerRenderId"),"The call's 'callerRenderId' must be a non-empty string.");if(issue)return issue;if(!isSafeRenderId(value.callerRenderId)){return{path:pointer(path,"callerRenderId"),category:"pattern",message:"The call's 'callerRenderId' must use only lowercase ASCII letters, digits, hyphens, and underscores."}}}if(!isPlainObject(value.args)){return{path:pointer(path,"args"),category:"type",message:"The call's 'args' must be an object."}}const argsIssue=validateStrictJson(value.args);if(argsIssue){return{path:pointer(path,"args")+argsIssue.path,category:"strict_json",message:"The call's 'args' must contain only strict JSON values under string keys."}}if(hasOwn(value,"stateToken")){const issue=nonEmptyStringIssue(value.stateToken,pointer(path,"stateToken"),"The call's 'stateToken' must be a non-empty string.");if(issue)return issue}if(hasOwn(value,"stateUpdates")){if(!isPlainObject(value.stateUpdates)){return{path:pointer(path,"stateUpdates"),category:"type",message:"The call's 'stateUpdates' must be an object."}}const stateIssue=validateStrictJson(value.stateUpdates);if(stateIssue){return{path:pointer(path,"stateUpdates")+stateIssue.path,category:"strict_json",message:"The call's 'stateUpdates' must contain only strict JSON values under string keys."}}}if(hasOwn(value,"sendSequence")){return integerIssue(value.sendSequence,pointer(path,"sendSequence"),"The call's 'sendSequence' must be an integer of at least 0.")}return null};var validateCapabilities=(value,path="/capabilities")=>{const jsonIssue=validateStrictJson(value,path);if(jsonIssue)return jsonIssue;const message="The envelope's 'capabilities' must contain only 'swaps', 'actions', and 'renderers'; each value must be a duplicate-free array of known v1 names.";if(!isPlainObject(value))return{path,category:"type",message};const unknown=firstUnknown(value,new Set(["swaps","actions","renderers"]));if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message}}for(const[name,known]of[["swaps",SWAPS],["actions",ACTION_KINDS],["renderers",RENDERERS]]){if(!hasOwn(value,name))continue;const items=value[name];const itemPath=pointer(path,name);if(!Array.isArray(items))return{path:itemPath,category:"type",message};for(let index=0;index<items.length;index+=1){if(typeof items[index]!=="string"){return{path:pointer(itemPath,index),category:"type",message}}if(!known.includes(items[index])){return{path:pointer(itemPath,index),category:"enum",message}}}if(new Set(items).size!==items.length){return{path:itemPath,category:"semantic",message}}}return null};var validateCallEnvelope=value=>{const jsonIssue=validateStrictJson(value);if(jsonIssue)return jsonIssue;if(!isPlainObject(value)){return{path:"",category:"type",message:"The request body is not a call envelope object."}}for(const required of["protocol","requestId","calls"]){if(!hasOwn(value,required)){return{path:pointer("",required),category:"required",message:`The envelope requires '${required}'.`}}}const unknown=firstUnknown(value,ENVELOPE_FIELDS);if(unknown!==null){return{path:pointer("",unknown),category:"unknown_field",message:`The envelope carries unknown field '${unknown}'.`}}if(value.protocol!==PROTOCOL){return{path:"/protocol",category:typeof value.protocol==="string"?"enum":"type",message:"The envelope protocol must be citry-events/1."}}const requestIssue=nonEmptyStringIssue(value.requestId,"/requestId","The envelope carries no 'requestId' string.");if(requestIssue)return requestIssue;if(hasOwn(value,"capabilities")){const issue=validateCapabilities(value.capabilities);if(issue)return issue}if(!Array.isArray(value.calls)){return{path:"/calls",category:"type",message:"The envelope calls must be an array."}}if(!value.calls.length||value.calls.length>CALLS_LIMIT){return{path:"/calls",category:"range",message:`The envelope must carry 1 to ${CALLS_LIMIT} calls.`}}for(let index=0;index<value.calls.length;index+=1){const issue=validateCall(value.calls[index],`/calls/${index}`);if(issue)return issue}return null};var buildCall=input=>{const call={componentClassId:input.componentClassId,handlerName:input.handlerName,args:copyJson(input.args)};for(const field of["callerRenderId","stateToken","sendSequence"]){if(input[field]!==void 0)call[field]=input[field]}if(input.stateUpdates!==void 0){call.stateUpdates=copyJson(input.stateUpdates)}const issue=validateCall(call);if(issue)throw new ProtocolValueError(issue);return call};var buildCallEnvelope=(requestId,calls,capabilities)=>{const envelope={protocol:PROTOCOL,requestId,calls:copyJson(calls)};if(capabilities!==void 0)envelope.capabilities=copyJson(capabilities);const issue=validateCallEnvelope(envelope);if(issue)throw new ProtocolValueError(issue);return envelope};var HTTP_METHOD=/^[!#$%&'*+.^_`|~0-9A-Z-]+$/;var DESCRIPTOR_FIELDS=new Set(["componentClassId","eventHandlers","writableStateFields"]);var HANDLER_FIELDS=new Set(["httpMethod","usesState","debounceMilliseconds","throttleMilliseconds","latestCallWins","allowBatching"]);var nonNegativeIntegerIssue=(value,path,name)=>{if(typeof value!=="number"||!Number.isInteger(value)){return{path,category:typeof value==="number"&&!Number.isFinite(value)?"strict_json":"type",message:`The ${name} hint must be an integer.`}}if(value<0){return{path,category:"range",message:`The ${name} hint must be at least 0.`}}return null};var validateHandlerDescriptor=(value,path="")=>{const jsonIssue=validateStrictJson(value,path);if(jsonIssue)return jsonIssue;if(!isPlainObject(value)){return{path,category:"type",message:"Event-handler hints must be an object."}}if(!hasOwn(value,"httpMethod")){return{path:pointer(path,"httpMethod"),category:"required",message:"Handler hints require 'httpMethod'."}}const unknown=firstUnknown(value,HANDLER_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:"Handler hints have an unknown field."}}if(typeof value.httpMethod!=="string"){return{path:pointer(path,"httpMethod"),category:"type",message:"The HTTP method must be a string."}}if(!HTTP_METHOD.test(value.httpMethod)){return{path:pointer(path,"httpMethod"),category:"pattern",message:"The HTTP method must be an uppercase token."}}if(hasOwn(value,"usesState")&&value.usesState!==true){return{path:pointer(path,"usesState"),category:"enum",message:"The usesState hint has its non-default literal value."}}for(const name of["debounceMilliseconds","throttleMilliseconds"]){if(!hasOwn(value,name))continue;const issue=nonNegativeIntegerIssue(value[name],pointer(path,name),name);if(issue)return issue}if(hasOwn(value,"latestCallWins")&&value.latestCallWins!==true){return{path:pointer(path,"latestCallWins"),category:"enum",message:"The latestCallWins hint has its non-default literal value."}}if(hasOwn(value,"allowBatching")&&value.allowBatching!==false){return{path:pointer(path,"allowBatching"),category:"enum",message:"The allowBatching hint has its non-default literal value."}}return null};var validateDescriptor=(value,path="")=>{const jsonIssue=validateStrictJson(value,path);if(jsonIssue)return jsonIssue;if(!isPlainObject(value)){return{path,category:"type",message:"A component descriptor must be an object."}}for(const required of["componentClassId","eventHandlers"]){if(!hasOwn(value,required)){return{path:pointer(path,required),category:"required",message:`The descriptor requires '${required}'.`}}}const unknown=firstUnknown(value,DESCRIPTOR_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:"The descriptor has an unknown field."}}if(typeof value.componentClassId!=="string"){return{path:pointer(path,"componentClassId"),category:"type",message:"The component class ID must be a string."}}if(!value.componentClassId){return{path:pointer(path,"componentClassId"),category:"range",message:"The component class ID must not be empty."}}if(!isPlainObject(value.eventHandlers)){return{path:pointer(path,"eventHandlers"),category:"type",message:"Event handlers must be an object."}}for(const name of Object.keys(value.eventHandlers).sort()){if(!name){return{path:pointer(path,"eventHandlers"),category:"range",message:"A handler name must not be empty."}}const issue=validateHandlerDescriptor(value.eventHandlers[name],pointer(pointer(path,"eventHandlers"),name));if(issue)return issue}if(hasOwn(value,"writableStateFields")){const fields=value.writableStateFields;const fieldPath=pointer(path,"writableStateFields");if(!Array.isArray(fields)){return{path:fieldPath,category:"type",message:"Writable State fields must be an array."}}const seen=new Set;for(let index=0;index<fields.length;index+=1){const field=fields[index];if(typeof field!=="string"){return{path:pointer(fieldPath,index),category:"type",message:"A writable State field must be a string."}}if(!field){return{path:pointer(fieldPath,index),category:"range",message:"A writable State field must not be empty."}}if(seen.has(field)){return{path:fieldPath,category:"semantic",message:"Writable State fields must be unique."}}seen.add(field)}}return null};var ERROR_STATUS_BY_CODE={invalid_args:422,invalid_state:403,stale_state:409,unknown_event:404,unknown_component:404,forbidden:403,not_found:404,conflict:409,error:null,csrf_failed:403,payload_too_large:413,protocol_mismatch:400,handler_error:500};var RESULT_ENVELOPE_FIELDS=new Set(["protocol","requestId","results"]);var OK_RESULT_FIELDS=new Set(["ok","sendSequence","actions"]);var ERROR_RESULT_FIELDS=new Set(["ok","sendSequence","error"]);var ERROR_FIELDS=new Set(["status","code","message","fieldErrors"]);var ACTION_FIELDS={render:new Set(["action","target","swap","renderer","html","prepared","delay","wait"]),data:new Set(["action","value","delay"]),state:new Set(["action","targetRenderId","stateToken","delay","wait"]),event:new Set(["action","eventName","detail","target","delay","wait"]),redirect:new Set(["action","url","delay","wait"]),url:new Set(["action","url","mode","delay","wait"])};var ACTION_REQUIRED={render:["action","target","swap"],data:["action","value"],state:["action","targetRenderId","stateToken"],event:["action","eventName"],redirect:["action","url"],url:["action","url","mode"]};var validateNonNegativeInteger=(value,path,message)=>{if(typeof value!=="number"||!Number.isInteger(value)){return{path,category:typeof value==="number"&&!Number.isFinite(value)?"strict_json":"type",message}}if(value<0)return{path,category:"range",message};return null};var validateTiming=(value,path)=>{if(hasOwn(value,"delay")){const delay=value.delay;if(typeof delay!=="number"){return{path:pointer(path,"delay"),category:"type",message:"The action delay must be a finite number."}}if(!Number.isFinite(delay)){return{path:pointer(path,"delay"),category:"strict_json",message:"The action delay must be finite."}}if(delay<0){return{path:pointer(path,"delay"),category:"range",message:"The action delay must be at least 0."}}}if(hasOwn(value,"wait")&&value.wait!==false){return{path:pointer(path,"wait"),category:"enum",message:"The action wait flag, when present, must be false."}}return null};var validateTarget=(value,path)=>{if(typeof value!=="string"){return{path,category:"type",message:"An action target must be a non-empty string."}}if(!value){return{path,category:"range",message:"An action target must be a non-empty string."}}if(value.startsWith("render:")&&!isSafeRenderId(value.slice(7))){return{path,category:"pattern",message:"A render target must contain a valid render ID."}}return null};var validateActionShape=(value,path="")=>{if(!isPlainObject(value)){return{path,category:"type",message:"An action must be an object."}}if(!hasOwn(value,"action")){return{path:pointer(path,"action"),category:"required",message:"The action kind is required."}}if(typeof value.action!=="string"){return{path:pointer(path,"action"),category:"type",message:"The action kind must be a string."}}if(!ACTION_KINDS.includes(value.action)){return{path:pointer(path,"action"),category:"enum",message:`Unknown action kind '${value.action}'.`}}const kind=value.action;for(const required of ACTION_REQUIRED[kind]){if(!hasOwn(value,required)){return{path:pointer(path,required),category:"required",message:`The ${kind} action requires '${required}'.`}}}const unknown=firstUnknown(value,ACTION_FIELDS[kind]);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:`The ${kind} action has an unknown field.`}}if(kind==="render"){const targetIssue=validateTarget(value.target,pointer(path,"target"));if(targetIssue)return targetIssue;if(!SWAPS.includes(value.swap)){return{path:pointer(path,"swap"),category:typeof value.swap==="string"?"enum":"type",message:"The render swap is not a v1 swap."}}const renderer=hasOwn(value,"renderer")?value.renderer:"html-fragment/1";if(typeof renderer!=="string"){return{path:pointer(path,"renderer"),category:"type",message:"The render renderer must be a string."}}if(!RENDERERS.includes(renderer)){return{path:pointer(path,"renderer"),category:"enum",message:"The render renderer is not a v1 renderer."}}const content=renderer==="html-fragment/1"?"html":"prepared";const other=content==="html"?"prepared":"html";if(!hasOwn(value,content)){return{path:pointer(path,content),category:"required",message:`The ${renderer} render requires '${content}'.`}}if(hasOwn(value,other)){return{path:pointer(path,other),category:"semantic",message:"A render action must carry exactly one content representation."}}if(content==="html"&&typeof value.html!=="string"){return{path:pointer(path,"html"),category:"type",message:"The render HTML must be a string."}}if(content==="prepared"&&!isPlainObject(value.prepared)){return{path:pointer(path,"prepared"),category:"type",message:"The prepared render content must be a JSON object."}}}else if(kind==="data"){}else if(kind==="state"){if(typeof value.targetRenderId!=="string"){return{path:pointer(path,"targetRenderId"),category:"type",message:"The state target must be a render ID."}}if(!isSafeRenderId(value.targetRenderId)){return{path:pointer(path,"targetRenderId"),category:"pattern",message:"The state target must be a valid render ID."}}if(typeof value.stateToken!=="string"){return{path:pointer(path,"stateToken"),category:"type",message:"The state token must be a string."}}if(!value.stateToken){return{path:pointer(path,"stateToken"),category:"range",message:"The state token must not be empty."}}}else if(kind==="event"){if(typeof value.eventName!=="string"){return{path:pointer(path,"eventName"),category:"type",message:"The event name must be a string."}}if(!value.eventName){return{path:pointer(path,"eventName"),category:"range",message:"The event name must not be empty."}}if(value.eventName.startsWith("citry:")){return{path:pointer(path,"eventName"),category:"pattern",message:"The event name is reserved."}}if(hasOwn(value,"target")){const issue=validateTarget(value.target,pointer(path,"target"));if(issue)return issue}}else if(kind==="redirect"){if(typeof value.url!=="string"){return{path:pointer(path,"url"),category:"type",message:"The redirect URL must be a string."}}if(!value.url){return{path:pointer(path,"url"),category:"range",message:"The redirect URL must not be empty."}}}else{if(typeof value.url!=="string"){return{path:pointer(path,"url"),category:"type",message:"The URL action URL must be a string."}}if(!value.url){return{path:pointer(path,"url"),category:"range",message:"The URL action URL must not be empty."}}if(value.mode!=="push"&&value.mode!=="replace"){return{path:pointer(path,"mode"),category:typeof value.mode==="string"?"enum":"type",message:"The URL action mode must be push or replace."}}}return validateTiming(value,path)};var validateErrorShape=(value,path="")=>{if(!isPlainObject(value)){return{path,category:"type",message:"The result error must be an object."}}for(const required of["status","code","message"]){if(!hasOwn(value,required)){return{path:pointer(path,required),category:"required",message:`The error requires '${required}'.`}}}const unknown=firstUnknown(value,ERROR_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:"The result error has an unknown field."}}if(typeof value.status!=="number"||!Number.isInteger(value.status)){return{path:pointer(path,"status"),category:typeof value.status==="number"&&!Number.isFinite(value.status)?"strict_json":"type",message:"The error status must be an integer."}}if(value.status<400||value.status>599){return{path:pointer(path,"status"),category:"range",message:"The error status must be from 400 to 599."}}if(typeof value.code!=="string"){return{path:pointer(path,"code"),category:"type",message:"The error code must be a string."}}if(!hasOwn(ERROR_STATUS_BY_CODE,value.code)){return{path:pointer(path,"code"),category:"enum",message:"The error code is not a v1 code."}}if(typeof value.message!=="string"){return{path:pointer(path,"message"),category:"type",message:"The error message must be a string."}}if(!value.message){return{path:pointer(path,"message"),category:"range",message:"The error message must not be empty."}}if(hasOwn(value,"fieldErrors")){if(!isPlainObject(value.fieldErrors)){return{path:pointer(path,"fieldErrors"),category:"type",message:"Field errors must be an object."}}for(const name of Object.keys(value.fieldErrors).sort()){if(typeof value.fieldErrors[name]!=="string"){return{path:pointer(pointer(path,"fieldErrors"),name),category:"type",message:"Field errors map strings."}}}}const expected=ERROR_STATUS_BY_CODE[value.code];if(expected!==null&&value.status!==expected){return{path:pointer(path,"status"),category:"semantic",message:"The error status does not match its code."}}return null};var validateResultShape=(value,path="")=>{if(!isPlainObject(value)){return{path,category:"type",message:"A result must be an object."}}if(!hasOwn(value,"ok")){return{path:pointer(path,"ok"),category:"required",message:"The result requires 'ok'."}}if(typeof value.ok!=="boolean"){return{path:pointer(path,"ok"),category:"type",message:"The result's 'ok' field must be a boolean."}}const required=value.ok?["ok","actions"]:["ok","error"];for(const field of required){if(!hasOwn(value,field)){return{path:pointer(path,field),category:"required",message:`The result requires '${field}'.`}}}const unknown=firstUnknown(value,value.ok?OK_RESULT_FIELDS:ERROR_RESULT_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:"The result has an unknown field."}}if(hasOwn(value,"sendSequence")){const issue=validateNonNegativeInteger(value.sendSequence,pointer(path,"sendSequence"),"The send sequence must be an integer.");if(issue)return issue}if(!value.ok)return validateErrorShape(value.error,pointer(path,"error"));if(!Array.isArray(value.actions)){return{path:pointer(path,"actions"),category:"type",message:"The result actions must be an array."}}for(let index=0;index<value.actions.length;index+=1){const issue=validateActionShape(value.actions[index],pointer(pointer(path,"actions"),index));if(issue)return issue}if(value.actions.filter(action=>isPlainObject(action)&&action.action==="data").length>1){return{path:pointer(path,"actions"),category:"semantic",message:"Each result may carry at most one data action."}}return null};var validateResult=(value,path="")=>{const jsonIssue=validateStrictJson(value,path);return jsonIssue??validateResultShape(value,path)};var validateResultEnvelopeShape=(value,path="")=>{if(!isPlainObject(value)){return{path,category:"type",message:"The result envelope must be an object."}}for(const required of["protocol","requestId","results"]){if(!hasOwn(value,required)){return{path:pointer(path,required),category:"required",message:`The result envelope requires '${required}'.`}}}const unknown=firstUnknown(value,RESULT_ENVELOPE_FIELDS);if(unknown!==null){return{path:pointer(path,unknown),category:"unknown_field",message:"The result envelope has an unknown field."}}if(value.protocol!==PROTOCOL){return{path:pointer(path,"protocol"),category:typeof value.protocol==="string"?"enum":"type",message:"The result protocol must be citry-events/1."}}if(value.requestId!==null&&typeof value.requestId!=="string"){return{path:pointer(path,"requestId"),category:"type",message:"The result request ID must be a string or null."}}if(value.requestId===""){return{path:pointer(path,"requestId"),category:"range",message:"The result request ID must not be empty."}}if(!Array.isArray(value.results)){return{path:pointer(path,"results"),category:"type",message:"The results must be an array."}}if(!value.results.length){return{path:pointer(path,"results"),category:"range",message:"The results array must not be empty."}}for(let index=0;index<value.results.length;index+=1){const issue=validateResultShape(value.results[index],pointer(pointer(path,"results"),index));if(issue)return issue}if(value.requestId===null){if(value.results.length!==1){return{path:pointer(path,"results"),category:"correlation",message:"An edge error has exactly one result."}}const result=value.results[0];const error=result.error;if(result.ok!==false||hasOwn(result,"sendSequence")||error.code!=="protocol_mismatch"&&error.code!=="payload_too_large"||hasOwn(error,"fieldErrors")){return{path:pointer(path,"results"),category:"correlation",message:"A null request ID is only for one transport-edge error."}}}return null};var validateResultEnvelope=(value,path="")=>{const jsonIssue=validateStrictJson(value,path);return jsonIssue??validateResultEnvelopeShape(value,path)};var validateExchangeAfterValidatedEnvelope=(callEnvelope,resultEnvelope)=>{const result=resultEnvelope;if(result.requestId!==callEnvelope.requestId){return{path:"/requestId",category:"correlation",message:"The result request ID does not match the call."}}if(result.results.length!==callEnvelope.calls.length){return{path:"/results",category:"correlation",message:"The result count does not match the call count."}}const advertised=callEnvelope.capabilities??{};const actions=new Set(advertised.actions??CAPABILITIES_BASELINE_V1.actions);const swaps=new Set(advertised.swaps??CAPABILITIES_BASELINE_V1.swaps);const renderers=new Set(advertised.renderers??CAPABILITIES_BASELINE_V1.renderers);for(let index=0;index<result.results.length;index+=1){const call=callEnvelope.calls[index];const answer=result.results[index];if(answer.sendSequence!==call.sendSequence||hasOwn(answer,"sendSequence")!==hasOwn(call,"sendSequence")){return{path:`/results/${index}/sendSequence`,category:"correlation",message:"The result does not echo the call's send sequence."}}if(!answer.ok)continue;for(let actionIndex=0;actionIndex<answer.actions.length;actionIndex+=1){const action=answer.actions[actionIndex];if(!actions.has(action.action)){return{path:`/results/${index}/actions/${actionIndex}/action`,category:"capability",message:"The result uses an action the caller did not advertise."}}if(action.action==="render"&&!swaps.has(action.swap)){return{path:`/results/${index}/actions/${actionIndex}/swap`,category:"capability",message:"The result uses a swap the caller did not advertise."}}if(action.action==="render"){const renderer="renderer"in action?action.renderer:"html-fragment/1";if(!renderers.has(renderer)){return{path:`/results/${index}/actions/${actionIndex}/renderer`,category:"capability",message:"The result uses a renderer the caller did not advertise."}}}}}return null};var validateActionList=actions=>validateResult({ok:true,actions});var buildOkResult=(actions,sendSequence)=>{const result={ok:true,actions:copyJson(actions)};if(sendSequence!==void 0)result.sendSequence=sendSequence;const issue=validateResult(result);if(issue)throw new ProtocolValueError(issue);return result};var resultIndex=path=>{const match=/^\/results\/(\d+)(?:\/|$)/.exec(path);return match?Number(match[1]):null};var preflightResultEnvelope=(reply,sent)=>{const structural=validateResultEnvelope(reply);if(structural){const edge=isPlainObject(reply)&&reply.requestId===null;const index=resultIndex(structural.path);return{ok:false,issue:structural,reason:edge&&structural.path.startsWith("/results")?"edge":index===null?"header":`result ${index}`}}const envelope=reply;if(envelope.requestId===null){const edge=envelope.results[0];return{ok:true,results:sent.calls.map(()=>edge)}}const relationship=validateExchangeAfterValidatedEnvelope(sent,envelope);if(relationship){const index=resultIndex(relationship.path);return{ok:false,issue:relationship,reason:relationship.path==="/requestId"||relationship.path==="/results"&&relationship.category==="correlation"?"correlation":`result ${index??0}`}}return{ok:true,results:envelope.results}};var assertValidActionList=actions=>{const issue=validateActionList(actions);if(issue)throw new ProtocolValueError(issue);return actions};var collectFormArgs=(form,reservedFields)=>{const entries=new Map;new FormData(form).forEach((value,name)=>{if(reservedFields.has(name)||typeof value!=="string")return;const bucket=entries.get(name)??[];bucket.push(value);entries.set(name,bucket)});const output={};entries.forEach((values,name)=>{const control=form.elements.namedItem(name);const input=control instanceof HTMLInputElement?control:null;const numeric=input&&(input.type==="number"||input.type==="range")?input.valueAsNumber:Number.NaN;output[name]=values.length===1?Number.isFinite(numeric)?numeric:values[0]:values.slice()});return output};var assertValidActionList2=actions=>assertValidActionList(actions);var validContext=value=>value!==null&&typeof value==="object"&&Object.keys(value).sort().join("|")==="componentClassId|descriptor|publicState|serverRenderId|stateToken"&&validateStrictJson(value)===null&&typeof value.serverRenderId==="string"&&value.serverRenderId.length>0&&(value.stateToken===null||typeof value.stateToken==="string"&&value.stateToken.length>0)&&typeof value.componentClassId==="string"&&value.componentClassId.length>0&&validateDescriptor(value.descriptor)===null&&value.descriptor.componentClassId===value.componentClassId;var VueEventCancellation=class extends Error{};var VueEventStale=class extends VueEventCancellation{constructor(reason){super(reason==="disposed"?"The Vue Events bridge was disposed; the source is stale or retired.":reason==="superseded"?"The Vue event call was superseded by a newer call.":"The Vue event source is stale or retired.");__publicField(this,"reason");this.reason=reason}};var stale=(reason="retired")=>new VueEventStale(reason);var activityError=error=>{if(error!==null&&typeof error==="object"&&"status"in error&&typeof error.status==="number"&&"code"in error&&typeof error.code==="string"&&"message"in error&&typeof error.message==="string")return error;const message=error instanceof Error?error.message:"The Vue event request failed.";return{status:0,code:message==="The Vue event request timed out."?"timeout":"transport",message}};var eventUrl=(base,context,handler)=>{if(typeof base!=="string"||!base.endsWith("/")||base.includes("?")||base.includes("#")){throw new Error("Vue Events eventBaseUrl must be a path ending in '/'.")}return`${base}${encodeURIComponent(context.componentClassId)}/${encodeURIComponent(handler)}`};var configuredEventRoutes=(url,endpoint,eventBaseUrl)=>{if(typeof url!=="string"||url.length===0)return{endpoint,eventBaseUrl};if(url.includes("?")||url.includes("#"))throw new Error("Citry Events url must not contain a query or fragment.");const normalized=url.endsWith("/")?url:`${url}/`;if(normalized.endsWith("/call/")){return{endpoint:normalized.slice(0,-1),eventBaseUrl:`${normalized.slice(0,-5)}e/`}}if(normalized.endsWith("/e/")){return{endpoint:`${normalized.slice(0,-2)}call`,eventBaseUrl:normalized}}return{endpoint:`${normalized}call`,eventBaseUrl:`${normalized}e/`}};var readCookie=name=>{if(typeof document==="undefined"||typeof document.cookie!=="string")return"";const item=document.cookie.split(";").map(value=>value.trim()).find(value=>value.startsWith(`${name}=`));return item?decodeURIComponent(item.slice(name.length+1)):""};var isWellFormedUtf16=value=>{for(let index=0;index<value.length;index+=1){const unit=value.charCodeAt(index);if(unit>=55296&&unit<=56319){const next=value.charCodeAt(index+1);if(!(next>=56320&&next<=57343))return false;index+=1}else if(unit>=56320&&unit<=57343)return false}return true};var flatQuery=args=>{const query=new URLSearchParams;const append=(key,value)=>{if(typeof value==="string"){if(!isWellFormedUtf16(value))throw new Error(`Event argument '${key}' is not well-formed UTF-16.`);query.append(key,value)}else if(typeof value==="boolean")query.append(key,String(value));else if(typeof value==="number"&&Number.isFinite(value))query.append(key,String(value));else throw new Error(`Event argument '${key}' has no flat GET query representation.`)};for(const[key,value]of Object.entries(args)){if(!isWellFormedUtf16(key))throw new Error("Event argument name is not well-formed UTF-16.");if(key.startsWith("_citry_"))throw new Error(`Event argument '${key}' uses a reserved GET query name.`);if(Array.isArray(value)){if(value.length===0)throw new Error(`Event argument '${key}' has no flat GET query representation.`);for(const item of value)append(key,item)}else append(key,value)}return query};var attachmentFilename=value=>{const extended=/(?:^|;)\s*filename\*\s*=\s*([^;]+)/i.exec(value)?.[1]?.trim();if(extended!==void 0){const encoded=/^UTF-8''(.+)$/i.exec(extended)?.[1];if(!encoded)throw new Error("The attachment response has an unsupported encoded filename.");try{return decodeURIComponent(encoded)}catch{throw new Error("The attachment response has an invalid encoded filename.")}}const quoted=/(?:^|;)\s*filename\s*=\s*"((?:\\.|[^"\\])*)"/i.exec(value)?.[1];if(quoted!==void 0)return quoted.replace(/\\(.)/g,"$1")||"download";const token=/(?:^|;)\s*filename\s*=\s*([!#$%&'*+.^_`|~0-9A-Za-z-]+)/i.exec(value)?.[1];return token||"download"};var saveAttachment=(blob,filename)=>{const url=URL.createObjectURL(blob);const anchor=document.createElement("a");try{anchor.href=url;anchor.download=filename;anchor.style.display="none";document.body.append(anchor);anchor.click()}finally{anchor.remove();URL.revokeObjectURL(url)}};var createVueEventsBridge=options=>{const reportableFailures=new WeakSet;const handledFailures=new WeakSet;const fetchImpl=options.fetch??globalThis.fetch.bind(globalThis);let correlation=0;const owners=new Map;const queue=[];let active=null;let running=false;let disposed=false;const supersedeEarlier=input=>{const error=stale("superseded");for(let index=queue.length-1;index>=0;index-=1){const job=queue[index];if(job.input.source.stableId===input.source.stableId&&job.input.source.generation===input.source.generation&&job.input.handler===input.handler){queue.splice(index,1);lifecycle("stale",job.input.source,job.input.handler,{reason:"superseded"});job.cancel(error)}}if(active&&active.input.source.stableId===input.source.stableId&&active.input.source.generation===input.source.generation&&active.input.handler===input.handler)active.cancel(error)};const lifecycle=(kind,source,event,detail)=>{try{return options.host.lifecycle?.(kind,source,event,detail)!==false}catch(error){console.error(`[Citry] citry:events:${kind} listener failed:`,error);return true}};const ownerState=source=>{const existing=owners.get(source.stableId);if(existing?.generation===source.generation)return existing;const state={generation:source.generation,sendSequence:0,acceptedEpoch:0,retired:false,timers:new Map};owners.set(source.stableId,state);return state};const current=source=>{const context=options.host.resolve(source);if(context===null||!validContext(context))throw stale("retired");return context};const stillCurrent=(source,state,epoch)=>{if(state.retired||owners.get(source.stableId)!==state||state.generation!==source.generation||epoch!==void 0&&epoch!==state.acceptedEpoch){throw stale(state.retired?"retired":"epoch")}current(source)};const delay=(milliseconds,state)=>new Promise((resolve,reject)=>{if(state.retired||disposed){reject(stale(state.retired?"retired":"disposed"));return}const timer=globalThis.setTimeout(()=>{state.timers.delete(timer);resolve()},milliseconds);state.timers.set(timer,reject)});const continuationCurrent=(source,state,epoch,job)=>{if(disposed||epoch!==state.acceptedEpoch){throw stale(disposed?"disposed":"epoch")}if(!job.acceptedRemount)stillCurrent(source,state,epoch)};const validateTargets=(result,source,serverRenderId)=>{if(!result.ok)return;const componentTarget=`render:${serverRenderId}`;for(const action of result.actions){if(action.action==="render"&&!options.host.preflightResult&&action.target!==componentTarget){throw new Error("Vue Events accepts the current component target; marker targets are not implemented.")}if(action.action==="event"&&action.target!==void 0&&action.target!==componentTarget){throw new Error("Vue Events accepts the current component Event target; marker targets are not implemented.")}}current(source)};const applyOne=async(action,source,state,epoch,onData,job,renderPlan)=>{if(action.action==="data"){if(!job.external)continuationCurrent(source,state,epoch,job);onData(action.value);return}if(action.action==="render"){stillCurrent(source,state,epoch);const context=current(source);if(!renderPlan&&action.target!==`render:${context.serverRenderId}`){throw new Error("The experimental Vue Events bridge accepts only its current root Render target.")}if(!("renderer"in action)||action.renderer!=="vue-prepared/1"){throw new Error("The Vue Events bridge requires a vue-prepared/1 Render action.")}const preparing=options.host.prepareRender(action,source,job.controller?.signal??new AbortController().signal,renderPlan);let prepared;try{prepared=await Promise.race([preparing,job.cancelled]);stillCurrent(source,state,epoch)}catch(error){try{options.host.abortRender(void 0,source)}catch(cleanupError){console.error("[Citry] aborting a prepared Vue render failed:",cleanupError)}void preparing.then(value=>{try{options.host.abortRender(value,source)}catch(cleanupError){console.error("[Citry] aborting a late prepared Vue render failed:",cleanupError)}},()=>void 0);throw error}job.committingTransaction=prepared.transaction;try{await Promise.race([options.host.commitRender(prepared,source),job.cancelled]);lifecycle("swapped",source,job.input.handler,{els:[]})}finally{job.committingTransaction=void 0}}else if(action.action==="state"){stillCurrent(source,state,epoch);options.host.commitState(action.targetRenderId,action.stateToken,source)}else if(action.action==="event"){stillCurrent(source,state,epoch);const rootTarget=`render:${current(source).serverRenderId}`;const callerTarget=job.callerRenderId===void 0?void 0:`render:${job.callerRenderId}`;if(action.target!==void 0&&action.target!==rootTarget&&action.target!==callerTarget){throw new Error("The experimental Vue Events bridge accepts only its current root Event target.")}if(job.external&&action.target===void 0&&options.host.dispatchEventGlobal)options.host.dispatchEventGlobal(action.eventName,action.detail);else options.host.dispatchEvent(action.eventName,action.detail,source)}else if(action.action==="redirect"){if(!job.external)continuationCurrent(source,state,epoch,job);options.host.redirect(action.url)}else{if(!job.external)continuationCurrent(source,state,epoch,job);options.host.updateUrl(action.url,action.mode)}};const applyActions=async(result,source,state,epoch,job,renderPlan)=>{if(!result.ok){reportableFailures.add(result.error);throw result.error}let data;const hoisted=new Set;result.actions.forEach((action,index)=>{if(action.action==="state"&&!(typeof action.delay==="number"&&action.delay>0)&&action.wait!==false){stillCurrent(source,state,epoch);options.host.commitState(action.targetRenderId,action.stateToken,source);hoisted.add(index)}});for(const[index,action]of result.actions.entries()){if(hoisted.has(index))continue;const run=async()=>{if(typeof action.delay==="number"&&action.delay>0)await delay(action.delay*1e3,state);await applyOne(action,source,state,epoch,value=>{data=value},job,action.action==="render"?renderPlan:void 0)};if("wait"in action&&action.wait===false){void run().catch(error=>{if(error instanceof VueEventStale){lifecycle("stale",source,job.input.handler,{reason:error.reason})}else if(!(error instanceof VueEventCancellation)){lifecycle("error",source,job.input.handler,{error:activityError(error)})}console.error("[Citry] applying a detached Vue event action failed:",error)})}else await run()}return data};const sendNow=async job=>{const input=job.input;if(disposed)throw stale("disposed");const context=current(input.source);const state=ownerState(input.source);job.owner=state;const appId=options.host.appId(input.source);if(typeof appId!=="string"||appId.length===0)throw stale("retired");const committedRevision=options.host.revision(input.source);if(!Number.isInteger(committedRevision)||committedRevision<0)throw stale("retired");if(!Object.prototype.hasOwnProperty.call(context.descriptor.eventHandlers,input.handler))throw new Error(`Unknown event handler '${input.handler}'.`);const handlerOptions=context.descriptor.eventHandlers[input.handler];job.callerRenderId=context.serverRenderId;job.lifecycleStarted=true;if(!lifecycle("before",input.source,input.handler))throw new VueEventCancellation(`Citry Events send '${input.handler}' was cancelled by citry:events:before.`);const useGet=handlerOptions.httpMethod==="GET";const runtimeConfig=options.runtimeConfig?.()??{};const configuredEndpoint=typeof options.endpoint==="function"&&!useGet?options.endpoint(context,input.handler):typeof options.endpoint==="string"?options.endpoint:"";const routes=configuredEventRoutes(runtimeConfig.url??"",configuredEndpoint,options.eventBaseUrl);if(useGet&&input.stateUpdates!==void 0)throw new Error("GET events cannot send pending State updates.");const taken=useGet?void 0:input.stateUpdates??options.host.takePendingState?.(input.source,input.handler);job.stateUpdates=taken===void 0?void 0:structuredClone(taken);state.sendSequence+=1;correlation+=1;const call=buildCall({componentClassId:context.componentClassId,handlerName:input.handler,callerRenderId:context.serverRenderId,args:input.args??{},stateToken:context.stateToken??void 0,stateUpdates:job.stateUpdates,sendSequence:state.sendSequence});const envelope=buildCallEnvelope(`vue_${correlation}`,[call],{actions:["render","data","state","event","redirect","url"],swaps:["morph"],renderers:["vue-prepared/1"]});const headers={"Content-Type":"application/citry-events+json","X-Citry-Events":"1","X-Citry-Vue-App":appId,"X-Citry-Vue-Occurrence":input.source.stableId,"X-Citry-Vue-Revision":String(committedRevision)};const selectedTransport=options.transport?.()??null;const csrf=selectedTransport?void 0:runtimeConfig.csrf??options.csrf;if(!useGet&&csrf){const token=csrf.token?typeof csrf.token==="function"?csrf.token():csrf.token:readCookie(csrf.cookie??"csrftoken");if(token)headers[csrf.header??"X-CSRFToken"]=token}const isolated=useGet||handlerOptions.allowBatching===false;const endpoint=isolated?eventUrl(routes.eventBaseUrl??"",context,input.handler):routes.endpoint;const callTimeout=input.options?.timeout;const timeoutMs=callTimeout??runtimeConfig.timeout??options.timeoutMs??3e4;if(!Number.isFinite(timeoutMs)||timeoutMs<=0)throw new Error("Vue Events timeoutMs must be positive.");const controller=new AbortController;job.controller=controller;const operation=(async()=>{if(selectedTransport){try{return{raw:await selectedTransport.send(envelope)}}catch(error){if(error!==null&&typeof error==="object")reportableFailures.add(error);throw error}}let requestUrl=endpoint;if(useGet){const query=flatQuery(input.args??{});query.append("_citry_protocol",envelope.protocol);query.append("_citry_request_id",envelope.requestId);query.append("_citry_capabilities",JSON.stringify(envelope.capabilities));query.append("_citry_caller_render_id",call.callerRenderId??"");query.append("_citry_send_sequence",String(call.sendSequence));if(handlerOptions.usesState===true&&call.stateToken!==void 0)query.append("_citry_state_token",call.stateToken);requestUrl+=`?${query.toString()}`}const requestHeaders=useGet?Object.fromEntries(Object.entries(headers).filter(([name])=>name!=="Content-Type")):headers;const requestInit={method:isolated?handlerOptions.httpMethod:"POST",credentials:"same-origin",headers:requestHeaders,...useGet?{}:{body:JSON.stringify(envelope)},signal:controller.signal};let response;try{response=await fetchImpl(requestUrl,requestInit)}catch(error){if(error!==null&&typeof error==="object")reportableFailures.add(error);throw error}const disposition=response.headers?.get?.("Content-Disposition")??null;if(response.ok&&disposition&&/^\s*attachment(?:;|$)/i.test(disposition)){return{attachment:await response.blob(),filename:attachmentFilename(disposition)}}try{const raw2=await response.json();return{raw:raw2}}catch(error){if(response.ok)throw new Error("A successful raw Event response must be an attachment.");throw error}})();let timeoutId=0;const received=await Promise.race([operation,job.cancelled,new Promise((_resolve,reject)=>{timeoutId=globalThis.setTimeout(()=>{controller.abort();const error=new Error("The Vue event request timed out.");reportableFailures.add(error);reject(error)},timeoutMs)})]).finally(()=>globalThis.clearTimeout(timeoutId));if("attachment"in received){stillCurrent(input.source,state);state.acceptedEpoch+=1;continuationCurrent(input.source,state,state.acceptedEpoch,job);saveAttachment(received.attachment,received.filename);return void 0}const raw=received.raw;const checked=preflightResultEnvelope(raw,envelope);if(!checked.ok)throw new Error(`Invalid Events response: ${checked.issue.message}`);stillCurrent(input.source,state);validateTargets(checked.results[0],input.source,context.serverRenderId);const preparedResult=options.host.preflightResult?.(checked.results[0],input.source)??{result:checked.results[0]};state.acceptedEpoch+=1;if(preparedResult.result.ok)job.stateAccepted=true;return applyActions(preparedResult.result,input.source,state,state.acceptedEpoch,job,preparedResult.renderPlan)};const runQueue=async()=>{if(running)return;running=true;try{while(queue.length>0){const job=queue.shift();if(!job||job.settled)continue;active=job;try{job.activity?.start(job.intent);const value=await sendNow(job);job.stateAccepted=true;job.activity?.succeed(job.intent);if(job.lifecycleStarted)lifecycle("after",job.input.source,job.input.handler,{ok:true});job.resolve(value)}catch(error){if(!job.stateAccepted&&job.stateUpdates!==void 0)options.host.restorePendingState?.(job.input.source,job.stateUpdates);if(job.lifecycleStarted){if(error instanceof VueEventStale){lifecycle("stale",job.input.source,job.input.handler,{reason:error.reason})}else if(!(error instanceof VueEventCancellation)){lifecycle("error",job.input.source,job.input.handler,{error:activityError(error)})}lifecycle("after",job.input.source,job.input.handler,{ok:false})}if(!(error instanceof VueEventCancellation)){job.activity?.fail(job.intent,activityError(error));if(job.activity&&error!==null&&typeof error==="object"&&reportableFailures.has(error))handledFailures.add(error)}job.reject(error)}finally{if(!job.activityFinished){job.activityFinished=true;job.activity?.finish(job.intent)}active=null}}}finally{running=false}};const unsupportedBrowserMethods=new Set(["HEAD","OPTIONS","CONNECT","TRACE","TRACK"]);const send=input=>{if(disposed)return Promise.reject(stale("disposed"));let activity;let intent;try{if(input.options?.timeout!==void 0&&(!Number.isFinite(input.options.timeout)||input.options.timeout<=0))throw new Error("Citry Events timeout must be a positive finite number.");const context=current(input.source);if(!Object.prototype.hasOwnProperty.call(context.descriptor.eventHandlers,input.handler))throw new Error(`Unknown event handler '${input.handler}'.`);const method=context.descriptor.eventHandlers[input.handler].httpMethod;if(unsupportedBrowserMethods.has(method))throw new Error(`Event handler '${input.handler}' uses HTTP ${method}, which is server-transport-only and cannot be sent by the browser bridge.`);activity=options.activity?.(input.source,context.descriptor);intent=activity?.enqueue(input.handler);if(context.descriptor.eventHandlers[input.handler].latestCallWins===true)supersedeEarlier(input)}catch(error){return Promise.reject(error)}let resolvePromise;let rejectPromise;let cancelPromise;const promise=new Promise((resolve,reject)=>{resolvePromise=resolve;rejectPromise=reject});const cancelled=new Promise((_resolve,reject)=>{cancelPromise=reject});void cancelled.catch(()=>void 0);const job={input,acceptedRemount:false,activity,intent,activityFinished:false,lifecycleStarted:false,external:false,stateAccepted:false,settled:false,cancelled,cancel(error){if(job.settled)return;job.controller?.abort();cancelPromise(error);if(!job.activityFinished){job.activityFinished=true;job.activity?.finish(job.intent)}job.reject(error)},resolve(value){if(job.settled)return;job.settled=true;resolvePromise(value)},reject(error){if(job.settled)return;job.settled=true;rejectPromise(error)}};queue.push(job);void runQueue();return promise};const applyActionsExternally=async(actions,source)=>{const result=buildOkResult(actions);if(!source){let data;for(const action of result.actions){if(typeof action.delay==="number"&&action.delay>0){const delay2=action.delay;await new Promise(resolve=>globalThis.setTimeout(resolve,delay2*1e3))}if(action.action==="data")data=action.value;else if(action.action==="redirect")options.host.redirect(action.url);else if(action.action==="url")options.host.updateUrl(action.url,action.mode);else if(action.action==="event"){if(action.target!==void 0||!options.host.dispatchEventGlobal)throw new Error("Citry.events.applyActions needs a mounted component for targeted Event actions.");options.host.dispatchEventGlobal(action.eventName,action.detail)}else{throw new Error("Citry.events.applyActions needs a mounted component for Render and State actions.")}}return data}const externalContext=current(source);const state=ownerState(source);state.acceptedEpoch+=1;const cancelled=new Promise(()=>void 0);const job={input:{source,handler:"__external__"},acceptedRemount:false,activityFinished:true,lifecycleStarted:true,external:true,callerRenderId:externalContext.serverRenderId,stateAccepted:true,settled:true,cancelled,cancel(){},resolve(){},reject(){}};const prepared=options.host.preflightResult?.(result,source)??{result};if(!lifecycle("before",source,job.input.handler)){const error=new VueEventCancellation("Citry Events applyActions was cancelled by citry:events:before.");lifecycle("after",source,job.input.handler,{ok:false});throw error}try{const value=await applyActions(prepared.result,source,state,state.acceptedEpoch,job,prepared.renderPlan);lifecycle("after",source,job.input.handler,{ok:true});return value}catch(error){if(error instanceof VueEventStale){lifecycle("stale",source,job.input.handler,{reason:error.reason})}else if(!(error instanceof VueEventCancellation)){lifecycle("error",source,job.input.handler,{error:activityError(error)})}lifecycle("after",source,job.input.handler,{ok:false});throw error}};const retire=(source,acceptedTransaction)=>{const state=owners.get(source.stableId);if(state?.generation===source.generation){state.retired=true;for(const[timer,reject]of state.timers){globalThis.clearTimeout(timer);reject(stale("retired"))}state.timers.clear();owners.delete(source.stableId)}const error=new VueEventStale("retired");for(let index=queue.length-1;index>=0;index-=1){const job=queue[index];if(job.input.source.stableId===source.stableId&&job.input.source.generation===source.generation){queue.splice(index,1);lifecycle("stale",source,job.input.handler,{reason:"retired"});job.cancel(error)}}if(active?.input.source.stableId===source.stableId&&active.input.source.generation===source.generation&&acceptedTransaction!==void 0&&active.committingTransaction===acceptedTransaction){active.acceptedRemount=true}else if(active?.input.source.stableId===source.stableId&&active.input.source.generation===source.generation)active.cancel(error)};const dispose=()=>{if(disposed)return;disposed=true;for(const state of owners.values()){state.retired=true;for(const[timer,reject]of state.timers){globalThis.clearTimeout(timer);reject(stale("disposed"))}state.timers.clear()}owners.clear();const error=new VueEventStale("disposed");for(const job of queue.splice(0)){lifecycle("stale",job.input.source,job.input.handler,{reason:"disposed"});job.cancel(error)}active?.cancel(error)};const isDeclarativeFailureHandled=error=>error instanceof VueEventCancellation||error!==null&&typeof error==="object"&&handledFailures.has(error);return{send,applyActions:applyActionsExternally,retire,dispose,isDeclarativeFailureHandled}};return __toCommonJS(citry_events_vue_exports);})();

global.CitryVueEvents = CitryVueEvents;
}

})(globalThis);
