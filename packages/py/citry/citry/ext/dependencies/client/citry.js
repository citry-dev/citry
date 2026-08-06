/**
 * Citry's client-side dependency manager.
 *
 * The server inlines this script into pages rendered with the "document"
 * strategy (or, once a web integration is mounted, serves it at a URL). It
 * has three jobs:
 *
 * 1. Run components' per-instance JS. A component's JS registers a callback
 *    with `$component(...)` (expanded server-side to
 *    `Citry.manager.registerComponent("<classId>", ...)`); the page carries
 *    a JSON manifest naming which instances to call with which data; the
 *    manager matches the two and calls the callback with the instance's
 *    elements (the ones carrying its `data-cid-<id>` marker) and its
 *    `js_data()` result. A callback may return a cleanup function; the
 *    manager runs it before the callback fires again for the same instance
 *    through a correlated update or an explicit graph-independent call.
 *    Instead of a bare callback, `$component` also accepts a config object
 *    `{init, props}` (design events.md 5.5): `init` is the callback,
 *    and `props` declares the props it consumes. Graph-owned instances keep
 *    one lifecycle props controller that evaluates source-owned `$c-props`,
 *    validates updates, and exposes a stable read-only view to init. The
 *    Events helper remains only for legacy graph-independent calls.
 *    Other scripts (e.g. extension runtimes) can add properties to the payload
 *    object the callback receives via `Citry.manager.decorateContext(fn)`:
 *    decorators run on each instance's payload right before its callback,
 *    in registration order, mutating the payload in place (return values
 *    are ignored); a thrown error is logged and the remaining decorators
 *    and the callback still runs; the returned function unregisters the
 *    decorator.
 *
 * 2. Track which scripts/stylesheets are already on the page (by URL), so
 *    an HTML fragment inserted later does not fetch them again.
 *
 * 3. Load the scripts/stylesheets a fragment needs (`loadJs`/`loadCss` from
 *    JSON tag descriptors).
 *
 * 4. Tear an instance down when it leaves the page, and drop a class's
 *    `Component.css` when its last instance is gone. The manager tracks each
 *    instance whose callback has fired (plus any the manifest declares
 *    present for CSS only) and sweeps them against the live DOM on every DOM
 *    mutation and after each render: an instance with no `data-cid-<id>`
 *    element left has its cleanups run, and a class with no instance left has
 *    its `data-citry-css-class` sheet removed. The sheet removal is deferred
 *    to a later task and its count re-checked, so a component that re-renders
 *    in place (retiring its old id just before the new id registers) keeps
 *    its styling instead of losing it on every re-render.
 *
 * 5. Atomically normalize ownership graph revisions into typed lookup
 *    indexes, route graph-linked callbacks, and own the permanent Alpine hook
 *    broker. The broker installs Alpine's non-removable hooks once and lets
 *    Events and later graph adapters replace providers without stacking page
 *    observers, init interceptors, root selectors, magics, or startup calls.
 *
 * Manifests are JSON script tags carrying the `data-citry` attribute. JSON
 * is inert no matter how the HTML lands in the page (innerHTML included), so
 * a MutationObserver watches for inserted manifest tags and processes them;
 * manifests already in the document are processed at startup. String fields
 * inside a manifest ride as base64, so content can never break out of the
 * script tag.
 *
 * Design: docs/design/dependencies.md section 8.
 */
(function () {
  "use strict";

  /*<citry-client-graph-v1>*/
  var OWNERSHIP_COMMENT_PREFIX="citry:g1",OWNERSHIP_COMMENT_RE=/^citry:g1:([0-9a-f]{64}):([0-9]+):([ir]):([0-9]+):([se])$/,matchOwnershipComment=t=>OWNERSHIP_COMMENT_RE.exec(t.trim()),parseOwnershipComment=t=>{const e=matchOwnershipComment(t);if(e===null)return null;const[,i,c,n,s,o]=e;return{revision:i,graphId:c,kind:n,recordId:s,side:o,key:`${OWNERSHIP_COMMENT_PREFIX}:${i}:${c}:${n}:${s}`}},ProtocolValueError=class extends TypeError{constructor(t){super(t.message),this.name="ProtocolValueError",this.issue=t}},hasOwn=(t,e)=>Object.prototype.hasOwnProperty.call(t,e),pointer=(t,e)=>{const i=String(e).replace(/~/g,"~0").replace(/\//g,"~1");return t?`${t}/${i}`:`/${i}`},isPlainObject=t=>{if(t===null||typeof t!="object"||Array.isArray(t))return!1;const e=Object.getPrototypeOf(t);return e===Object.prototype||e===null},firstUnknown=(t,e)=>Object.keys(t).filter(i=>!e.has(i)).sort()[0]??null,containerIssue=(t,e)=>{if(Object.getOwnPropertySymbols(t).length)return{path:e,category:"strict_json",message:"The value contains a symbol-keyed property."};for(const i of Object.getOwnPropertyNames(t)){if(Array.isArray(t)&&i==="length")continue;const c=Object.getOwnPropertyDescriptor(t,i);if(!c?.enumerable||!("value"in c))return{path:pointer(e,i),category:"strict_json",message:"A JSON property must be an enumerable data property."}}return null},validateStrictJson=(t,e="")=>{const i=[{value:t,path:e,leaving:!1}],c=new Set;for(;i.length;){const n=i.pop(),s=n.value;if(n.leaving){c.delete(s);continue}if(s===null||typeof s=="string"||typeof s=="boolean")continue;if(typeof s=="number"){if(!Number.isFinite(s))return{path:n.path,category:"strict_json",message:"The value contains a non-finite number."};continue}if(typeof s!="object")return{path:n.path,category:"strict_json",message:"The value contains a non-JSON value."};if(!Array.isArray(s)&&!isPlainObject(s))return{path:n.path,category:"strict_json",message:"The value contains a non-JSON object."};const o=containerIssue(s,n.path);if(o)return o;if(c.has(s))return{path:n.path,category:"strict_json",message:"The value contains a cycle."};if(c.add(s),i.push({value:s,path:n.path,leaving:!0}),Array.isArray(s)){const l=Object.keys(s);if(l.length!==s.length||l.some((I,y)=>I!==String(y)))return{path:n.path,category:"strict_json",message:"A JSON array must be dense and carry no named properties."};for(let I=s.length-1;I>=0;I-=1)i.push({value:s[I],path:pointer(n.path,I),leaving:!1});continue}for(const l of Object.keys(s).sort().reverse())i.push({value:s[l],path:pointer(n.path,l),leaving:!1})}return null},PROTOCOL="citry-client-graph/1",MAX_SAFE_INTEGER=Number.MAX_SAFE_INTEGER,canonicalValue=t=>{if(t===null||typeof t=="string"||typeof t=="boolean")return JSON.stringify(t);if(typeof t=="number"){if(!Number.isSafeInteger(t)||t<0)throw new TypeError("client-graph numbers must be non-negative safe integers");return String(t)}if(Array.isArray(t))return`[${t.map(canonicalValue).join(",")}]`;if(isPlainObject(t))return`{${Object.keys(t).sort().map(e=>`${JSON.stringify(e)}:${canonicalValue(t[e])}`).join(",")}}`;throw new TypeError("unsupported client-graph JSON value")},sha256=t=>{const e=new TextEncoder().encode(t),i=Math.ceil((e.length+9)/64)*64,c=new Uint8Array(i);c.set(e),c[e.length]=128;const n=new DataView(c.buffer);n.setUint32(i-8,Math.floor(e.length/536870912),!1),n.setUint32(i-4,e.length<<3>>>0,!1);const s=new Uint32Array([1116352408,1899447441,3049323471,3921009573,961987163,1508970993,2453635748,2870763221,3624381080,310598401,607225278,1426881987,1925078388,2162078206,2614888103,3248222580,3835390401,4022224774,264347078,604807628,770255983,1249150122,1555081692,1996064986,2554220882,2821834349,2952996808,3210313671,3336571891,3584528711,113926993,338241895,666307205,773529912,1294757372,1396182291,1695183700,1986661051,2177026350,2456956037,2730485921,2820302411,3259730800,3345764771,3516065817,3600352804,4094571909,275423344,430227734,506948616,659060556,883997877,958139571,1322822218,1537002063,1747873779,1955562222,2024104815,2227730452,2361852424,2428436474,2756734187,3204031479,3329325298]),o=new Uint32Array([1779033703,3144134277,1013904242,2773480762,1359893119,2600822924,528734635,1541459225]),l=new Uint32Array(64),I=(y,p)=>y>>>p|y<<32-p;for(let y=0;y<i;y+=64){for(let m=0;m<16;m+=1)l[m]=n.getUint32(y+m*4,!1);for(let m=16;m<64;m+=1){const $=l[m-15],k=l[m-2],O=I($,7)^I($,18)^$>>>3,a=I(k,17)^I(k,19)^k>>>10;l[m]=l[m-16]+O+l[m-7]+a>>>0}let p=o[0],g=o[1],R=o[2],C=o[3],v=o[4],L=o[5],w=o[6],b=o[7];for(let m=0;m<64;m+=1){const $=I(v,6)^I(v,11)^I(v,25),k=v&L^~v&w,O=b+$+k+s[m]+l[m]>>>0,a=I(p,2)^I(p,13)^I(p,22),r=p&g^p&R^g&R,d=a+r>>>0;b=w,w=L,L=v,v=C+O>>>0,C=R,R=g,g=p,p=O+d>>>0}o[0]=o[0]+p>>>0,o[1]=o[1]+g>>>0,o[2]=o[2]+R>>>0,o[3]=o[3]+C>>>0,o[4]=o[4]+v>>>0,o[5]=o[5]+L>>>0,o[6]=o[6]+w>>>0,o[7]=o[7]+b>>>0}return Array.from(o).map(y=>y.toString(16).padStart(8,"0")).join("")},revisionFor=t=>sha256(canonicalValue(t)),revisionForManifest=t=>{const e={};for(const i of Object.keys(t))i!=="revision"&&(e[i]=t[i]);return revisionFor(e)},RENDER_ID=/^[a-z0-9_-]+$/,LOCATION_KINDS=new Set(["component-call","component-tag-client-binding","implicit-fill","named-fill","fallback-fill","slot-outlet"]),BINDING_SOURCES=new Set(["direct","server-dynamic","spread"]),FILL_KINDS=new Set(["implicit","named","fallback","python","typed-default"]),SOURCE_POLICIES=new Set(["template","python-detached","typed-default-detached"]),MORPH_MODES=new Set(["ignore"]),COMPONENT_CLASS_FIELDS=["classId","className"],COMPONENT_INSTANCE_FIELDS=["instanceId","renderId","classId","invocationId","parentRenderId","transparent"],SOURCE_LOCATION_FIELDS=["locationId","kind","ownerRenderId","ownerClassId","carrierInstanceId","origin","sourceOffset","sourcePos","mappingKey","mappingIndex"],EXPRESSION_PAYLOAD_FIELDS=["type","expression"],DOM_PAYLOAD_FIELDS=["type","classId","event","handler","args","prevent","stop","self","once","key","debounce","throttle"],POLL_PAYLOAD_FIELDS=["type","classId","handler","args","interval"],CLIENT_BINDING_FIELDS=["key","source","locationId","payload"],NESTED_COMPONENT_FIELDS=["invocationId","sourceRenderId","sourceClassId","locationId","tagName","targetClassId","morphKey","morphMode","targetRenderId","parentRegionId","clientBindings"],EXECUTION_CONSTRAINT_FIELDS=["invocationId","parentRenderId","childRenderId"],FILL_FIELDS=["fillId","kind","slotName","policy","ownerRenderId","ownerClassId","locationId","sourceInvocationId","receiverRenderId","receiverClassId","fallbackLocationId"],SLOT_REGION_FIELDS=["regionId","fillId","receiverRenderId","slotLocationId","ownerRenderId","sourceLocationId","parentRegionId","transitionFromRenderId","resultOwnerRenderId"],GRAPH_FIELDS=["graphId","componentClasses","componentInstances","sourceLocations","nestedComponents","componentExecutionOrderConstraints","fills","slotRegions"],recordIssue=(t,e,i,c,n)=>{if(n){const o=validateStrictJson(t,e);if(o)return o}if(!isPlainObject(t))return{path:e,category:"type",message:`${c} must be an object.`};for(const o of i)if(!hasOwn(t,o))return{path:pointer(e,o),category:"required",message:`${c} requires '${o}'.`};const s=firstUnknown(t,new Set(i));return s===null?null:{path:pointer(e,s),category:"unknown_field",message:`${c} has an unknown field.`}},stringIssue=(t,e,i)=>typeof t=="string"?null:{path:e,category:"type",message:`${i} must be a string.`},nullableStringIssue=(t,e,i)=>t===null||typeof t=="string"?null:{path:e,category:"type",message:`${i} must be a string or null.`},integerIssue=(t,e,i,c)=>typeof t!="number"||!Number.isInteger(t)?{path:e,category:typeof t=="number"&&!Number.isFinite(t)?"strict_json":"type",message:`${i} must be an integer.`}:!Number.isSafeInteger(t)||t<c?{path:e,category:"range",message:`${i} is outside the client-graph range.`}:null,nullableIntegerIssue=(t,e,i,c)=>t===null?null:integerIssue(t,e,i,c),enumIssue=(t,e,i,c)=>typeof t!="string"?{path:e,category:"type",message:`${c} must be a string.`}:i.has(t)?null:{path:e,category:"enum",message:`${c} is not a client-graph v1 value.`},nullableEnumIssue=(t,e,i,c)=>t===null?null:enumIssue(t,e,i,c),validateComponentClass=(t,e="",i=!0)=>{const c=recordIssue(t,e,COMPONENT_CLASS_FIELDS,"A component-class record",i);if(c)return c;const n=t;for(const s of COMPONENT_CLASS_FIELDS){const o=stringIssue(n[s],pointer(e,s),`The component ${s}`);if(o)return o}return null},validateComponentInstance=(t,e="",i=!0)=>{const c=recordIssue(t,e,COMPONENT_INSTANCE_FIELDS,"A component-instance record",i);if(c)return c;const n=t,s=[integerIssue(n.instanceId,pointer(e,"instanceId"),"The instance ID",1),stringIssue(n.renderId,pointer(e,"renderId"),"The render ID"),stringIssue(n.classId,pointer(e,"classId"),"The class ID"),nullableIntegerIssue(n.invocationId,pointer(e,"invocationId"),"The invocation ID",1),nullableStringIssue(n.parentRenderId,pointer(e,"parentRenderId"),"The parent render ID")];for(const o of s)if(o)return o;return RENDER_ID.test(n.renderId)?typeof n.transparent=="boolean"?null:{path:pointer(e,"transparent"),category:"type",message:"The transparent flag must be a boolean."}:{path:pointer(e,"renderId"),category:"pattern",message:"The component renderId is not safe for an HTML attribute name."}},validateSourceLocation=(t,e="",i=!0)=>{const c=recordIssue(t,e,SOURCE_LOCATION_FIELDS,"A source-location record",i);if(c)return c;const n=t,s=[integerIssue(n.locationId,pointer(e,"locationId"),"The location ID",1),enumIssue(n.kind,pointer(e,"kind"),LOCATION_KINDS,"The location kind"),stringIssue(n.ownerRenderId,pointer(e,"ownerRenderId"),"The location owner render ID"),stringIssue(n.ownerClassId,pointer(e,"ownerClassId"),"The location owner class ID"),integerIssue(n.carrierInstanceId,pointer(e,"carrierInstanceId"),"The carrier instance ID",1),nullableStringIssue(n.origin,pointer(e,"origin"),"The source origin")];for(const g of s)if(g)return g;const o=pointer(e,"sourceOffset");let l=recordIssue(n.sourceOffset,o,["start","end"],"A source-offset record",!1);if(l)return l;const I=n.sourceOffset;for(const g of["start","end"])if(l=integerIssue(I[g],pointer(o,g),`The source-offset ${g}`,0),l)return l;const y=pointer(e,"sourcePos");if(l=recordIssue(n.sourcePos,y,["line","column"],"A source-position record",!1),l)return l;const p=n.sourcePos;for(const g of["line","column"])if(l=integerIssue(p[g],pointer(y,g),`The source-position ${g}`,1),l)return l;return l=nullableStringIssue(n.mappingKey,pointer(e,"mappingKey"),"The mapping key"),l||nullableIntegerIssue(n.mappingIndex,pointer(e,"mappingIndex"),"The mapping index",0)},validateClientBindingPayload=(t,e="",i=!0)=>{if(i){const o=validateStrictJson(t,e);if(o)return o}if(!isPlainObject(t))return{path:e,category:"type",message:"A client-binding payload must be an object."};if(!hasOwn(t,"type"))return{path:pointer(e,"type"),category:"required",message:"A client-binding payload requires 'type'."};if(typeof t.type!="string")return{path:pointer(e,"type"),category:"type",message:"The client-binding payload type must be a string."};const c=t.type==="props"||t.type==="alpine-handler"?EXPRESSION_PAYLOAD_FIELDS:t.type==="citry-dom-event"?DOM_PAYLOAD_FIELDS:t.type==="citry-poll"?POLL_PAYLOAD_FIELDS:null;if(c===null)return{path:pointer(e,"type"),category:"enum",message:"The client-binding payload type is not a v1 value."};const n=recordIssue(t,e,c,"A client-binding payload",!1);if(n)return n;if(t.type==="props"||t.type==="alpine-handler")return stringIssue(t.expression,pointer(e,"expression"),"The Alpine expression");if(t.type==="citry-poll"){for(const l of["classId","handler"]){const I=stringIssue(t[l],pointer(e,l),`The poll ${l}`);if(I)return I}return nullableStringIssue(t.args,pointer(e,"args"),"The poll arguments")??integerIssue(t.interval,pointer(e,"interval"),"The poll interval",1)}for(const o of["classId","event","handler"]){const l=stringIssue(t[o],pointer(e,o),`The DOM-event ${o}`);if(l)return l}let s=nullableStringIssue(t.args,pointer(e,"args"),"The DOM-event args");if(s)return s;for(const o of["prevent","stop","self","once"])if(typeof t[o]!="boolean")return{path:pointer(e,o),category:"type",message:`The DOM-event ${o} flag must be a boolean.`};if(s=nullableStringIssue(t.key,pointer(e,"key"),"The DOM-event key"),s)return s;for(const o of["debounce","throttle"])if(s=nullableIntegerIssue(t[o],pointer(e,o),`The DOM-event ${o} delay`,0),s)return s;return null},validateClientBinding=(t,e="",i=!0)=>{const c=recordIssue(t,e,CLIENT_BINDING_FIELDS,"A component-tag client-binding record",i);if(c)return c;const n=t,s=[stringIssue(n.key,pointer(e,"key"),"The client-binding key"),enumIssue(n.source,pointer(e,"source"),BINDING_SOURCES,"The client-binding source"),nullableIntegerIssue(n.locationId,pointer(e,"locationId"),"The client-binding location ID",1)];for(const o of s)if(o)return o;return validateClientBindingPayload(n.payload,pointer(e,"payload"),!1)},validateNestedComponent=(t,e="",i=!0)=>{const c=recordIssue(t,e,NESTED_COMPONENT_FIELDS,"A nested-component record",i);if(c)return c;const n=t,s=[integerIssue(n.invocationId,pointer(e,"invocationId"),"The invocation ID",1),stringIssue(n.sourceRenderId,pointer(e,"sourceRenderId"),"The source render ID"),stringIssue(n.sourceClassId,pointer(e,"sourceClassId"),"The source class ID"),nullableIntegerIssue(n.locationId,pointer(e,"locationId"),"The location ID",1),stringIssue(n.tagName,pointer(e,"tagName"),"The nested-component tag name"),stringIssue(n.targetClassId,pointer(e,"targetClassId"),"The target class ID"),nullableStringIssue(n.morphKey,pointer(e,"morphKey"),"The component morph key"),nullableEnumIssue(n.morphMode,pointer(e,"morphMode"),MORPH_MODES,"The component morph mode"),stringIssue(n.targetRenderId,pointer(e,"targetRenderId"),"The target render ID"),nullableIntegerIssue(n.parentRegionId,pointer(e,"parentRegionId"),"The parent slot-region ID",1)];for(const o of s)if(o)return o;if(!Array.isArray(n.clientBindings))return{path:pointer(e,"clientBindings"),category:"type",message:"Client bindings must be an array."};for(let o=0;o<n.clientBindings.length;o+=1){const l=validateClientBinding(n.clientBindings[o],pointer(pointer(e,"clientBindings"),o),!1);if(l)return l}return null},validateExecutionConstraint=(t,e="",i=!0)=>{const c=recordIssue(t,e,EXECUTION_CONSTRAINT_FIELDS,"An execution-order constraint",i);if(c)return c;const n=t;return integerIssue(n.invocationId,pointer(e,"invocationId"),"The invocation ID",1)??stringIssue(n.parentRenderId,pointer(e,"parentRenderId"),"The parent render ID")??stringIssue(n.childRenderId,pointer(e,"childRenderId"),"The child render ID")},validateFill=(t,e="",i=!0)=>{const c=recordIssue(t,e,FILL_FIELDS,"A fill record",i);if(c)return c;const n=t;return[integerIssue(n.fillId,pointer(e,"fillId"),"The fill ID",1),enumIssue(n.kind,pointer(e,"kind"),FILL_KINDS,"The fill kind"),stringIssue(n.slotName,pointer(e,"slotName"),"The fill slot name"),enumIssue(n.policy,pointer(e,"policy"),SOURCE_POLICIES,"The fill source policy"),nullableStringIssue(n.ownerRenderId,pointer(e,"ownerRenderId"),"The fill owner render ID"),nullableStringIssue(n.ownerClassId,pointer(e,"ownerClassId"),"The fill owner class ID"),nullableIntegerIssue(n.locationId,pointer(e,"locationId"),"The fill location ID",1),nullableIntegerIssue(n.sourceInvocationId,pointer(e,"sourceInvocationId"),"The source invocation ID",1),nullableStringIssue(n.receiverRenderId,pointer(e,"receiverRenderId"),"The fill receiver render ID"),nullableStringIssue(n.receiverClassId,pointer(e,"receiverClassId"),"The fill receiver class ID"),nullableIntegerIssue(n.fallbackLocationId,pointer(e,"fallbackLocationId"),"The fallback location ID",1)].find(o=>o!==null)??null},validateSlotRegion=(t,e="",i=!0)=>{const c=recordIssue(t,e,SLOT_REGION_FIELDS,"A slot-region record",i);if(c)return c;const n=t;return[integerIssue(n.regionId,pointer(e,"regionId"),"The slot-region ID",1),integerIssue(n.fillId,pointer(e,"fillId"),"The fill ID",1),nullableStringIssue(n.receiverRenderId,pointer(e,"receiverRenderId"),"The receiver render ID"),nullableIntegerIssue(n.slotLocationId,pointer(e,"slotLocationId"),"The slot location ID",1),nullableStringIssue(n.ownerRenderId,pointer(e,"ownerRenderId"),"The owner render ID"),nullableIntegerIssue(n.sourceLocationId,pointer(e,"sourceLocationId"),"The source location ID",1),nullableIntegerIssue(n.parentRegionId,pointer(e,"parentRegionId"),"The parent slot-region ID",1),nullableStringIssue(n.transitionFromRenderId,pointer(e,"transitionFromRenderId"),"The transition source render ID"),nullableStringIssue(n.resultOwnerRenderId,pointer(e,"resultOwnerRenderId"),"The result owner render ID")].find(o=>o!==null)??null},validateGraph=(t,e="",i=!0)=>{const c=recordIssue(t,e,GRAPH_FIELDS,"A graph record",i);if(c)return c;const n=t,s=integerIssue(n.graphId,pointer(e,"graphId"),"The graph ID",0);if(s)return s;const o=[["componentClasses",validateComponentClass],["componentInstances",validateComponentInstance],["sourceLocations",validateSourceLocation],["nestedComponents",validateNestedComponent],["componentExecutionOrderConstraints",validateExecutionConstraint],["fills",validateFill],["slotRegions",validateSlotRegion]];for(const[l,I]of o){const y=n[l],p=pointer(e,l);if(!Array.isArray(y))return{path:p,category:"type",message:`The graph's ${l} must be an array.`};for(let g=0;g<y.length;g+=1){const R=I(y[g],pointer(p,g),!1);if(R)return R}}return null},cycle=t=>{const e=new Set,i=new Set;for(const c of t.keys()){let n=c;const s=[];for(;n!=null&&t.has(n)&&!i.has(n);){if(e.has(n))return!0;e.add(n),s.push(n);const o=t.get(n);if(o===void 0)break;n=o}for(const o of s)e.delete(o),i.add(o)}return!1},executionCycle=t=>{const e=new Set,i=new Set,c=Array.from(t.keys()).reverse().map(n=>[n,!1]);for(;c.length;){const[n,s]=c.pop();if(s){e.delete(n),i.add(n);continue}if(e.has(n))return!0;if(!i.has(n)){e.add(n),c.push([n,!0]);for(const o of[...t.get(n)??[]].reverse())c.push([o,!1])}}return!1},semantic=(t,e)=>({path:t,category:"semantic",message:e}),bindingKeyIssue=(t,e,i)=>{if(t.type==="props"&&e!=="$c-props")return semantic(i,"A props client binding must use the $c-props key.");if(t.type==="alpine-handler"&&!(e.startsWith("@")&&!e.startsWith("@c-")||e.startsWith("x-on:")))return semantic(i,"An Alpine-handler client binding has a non-Alpine key.");if(t.type==="citry-dom-event"){if(!e.startsWith("@c-")||e.slice(3).split(".")[0]==="poll")return semantic(i,"A Citry DOM-event client binding has a non-event key.");if(e.slice(3).split(".")[0]!==t.event)return semantic(i,"A Citry DOM-event client binding disagrees with its key.")}return t.type==="citry-poll"&&!e.startsWith("@c-poll.")?semantic(i,"A Citry poll client binding must use an @c-poll key."):null},validateRelationships=(t,e="")=>{const i=t.mode==="development",c=new Set;for(let n=0;n<t.graphs.length;n+=1){const s=t.graphs[n],o=pointer(pointer(e,"graphs"),n);if(s.graphId!==n)return semantic(pointer(o,"graphId"),`graphs[${n}].graphId is not dense and ordered.`);const l=[["componentInstances","instanceId"],["sourceLocations","locationId"],["nestedComponents","invocationId"],["fills","fillId"],["slotRegions","regionId"]],I=new Map;for(const[a,r]of l){const f=s[a].map(h=>h[r]),u=new Set(f);if(I.set(a,u),f.length!==u.size)return semantic(pointer(o,a),`graphs[${n}].${a} has duplicate ids.`)}if(!i){if(s.sourceLocations.length)return semantic(pointer(o,"sourceLocations"),`graphs[${n}] production manifest has sourceLocations.`);for(let a=0;a<s.nestedComponents.length;a+=1){const r=s.nestedComponents[a],d=pointer(pointer(o,"nestedComponents"),a);if(r.locationId!==null)return semantic(pointer(d,"locationId"),`graphs[${n}] production invocation has a location reference.`);for(let f=0;f<r.clientBindings.length;f+=1)if(r.clientBindings[f].locationId!==null){const u=pointer(pointer(d,"clientBindings"),f);return semantic(pointer(u,"locationId"),`graphs[${n}] production client binding has a location reference.`)}}for(let a=0;a<s.fills.length;a+=1){const r=s.fills[a];for(const d of["locationId","fallbackLocationId"])if(r[d]!==null)return semantic(pointer(pointer(pointer(o,"fills"),a),d),`graphs[${n}] production fill has a location reference.`)}for(let a=0;a<s.slotRegions.length;a+=1){const r=s.slotRegions[a];for(const d of["slotLocationId","sourceLocationId"])if(r[d]!==null)return semantic(pointer(pointer(pointer(o,"slotRegions"),a),d),`graphs[${n}] production slot region has a location reference.`)}}const y=new Set;for(let a=0;a<s.componentClasses.length;a+=1){const r=s.componentClasses[a].classId;if(y.has(r))return semantic(pointer(pointer(pointer(o,"componentClasses"),a),"classId"),`graphs[${n}] has duplicate class ids.`);y.add(r)}const p=new Set,g=new Map,R=new Map,C=new Map,v=[],L=new Map;for(let a=0;a<s.componentInstances.length;a+=1){const r=s.componentInstances[a],d=pointer(pointer(o,"componentInstances"),a);if(!y.has(r.classId))return semantic(pointer(d,"classId"),`graphs[${n}] component instance classId is unknown.`);if(p.has(r.renderId))return semantic(pointer(d,"renderId"),`graphs[${n}] has duplicate render ids.`);if(c.has(r.renderId))return semantic(pointer(d,"renderId"),`render id '${r.renderId}' appears in more than one graph.`);p.add(r.renderId),c.add(r.renderId),g.set(r.renderId,r.classId),R.set(r.instanceId,r.renderId),L.set(r.renderId,r.parentRenderId);const f=[r.renderId,r.parentRenderId,r.invocationId];if(v.push(f),r.invocationId!==null){const u=C.get(r.invocationId)??[];u.push(f),C.set(r.invocationId,u)}}for(let a=0;a<s.componentInstances.length;a+=1){const r=s.componentInstances[a].parentRenderId;if(r!==null&&!p.has(r))return semantic(pointer(pointer(pointer(o,"componentInstances"),a),"parentRenderId"),`graphs[${n}] component instance parentRenderId is unknown.`)}const w=new Map,b=new Map;if(i)for(let a=0;a<s.sourceLocations.length;a+=1){const r=s.sourceLocations[a],d=pointer(pointer(o,"sourceLocations"),a);if(!I.get("componentInstances").has(r.carrierInstanceId))return semantic(pointer(d,"carrierInstanceId"),`graphs[${n}] location has an unknown carrier.`);if(r.sourceOffset.start>r.sourceOffset.end)return semantic(pointer(d,"sourceOffset"),`graphs[${n}] location has a reversed byte range.`);if(!p.has(r.ownerRenderId)||g.get(r.ownerRenderId)!==r.ownerClassId)return semantic(pointer(d,"ownerRenderId"),`graphs[${n}] location owner is unknown or mismatched.`);if(R.get(r.carrierInstanceId)!==r.ownerRenderId)return semantic(pointer(d,"carrierInstanceId"),`graphs[${n}] location carrier is mismatched.`);w.set(r.locationId,[r.ownerRenderId,r.ownerClassId]),b.set(r.locationId,r.kind)}const m=new Map;for(let a=0;a<s.nestedComponents.length;a+=1){const r=s.nestedComponents[a],d=pointer(pointer(o,"nestedComponents"),a);if(!p.has(r.sourceRenderId)||g.get(r.sourceRenderId)!==r.sourceClassId)return semantic(pointer(d,"sourceRenderId"),`graphs[${n}] invocation source is unknown or mismatched.`);if(!p.has(r.targetRenderId)||g.get(r.targetRenderId)!==r.targetClassId)return semantic(pointer(d,"targetRenderId"),`graphs[${n}] invocation target is unknown or mismatched.`);if(i){if(!I.get("sourceLocations").has(r.locationId))return semantic(pointer(d,"locationId"),`graphs[${n}] invocation has an unknown location.`);const f=w.get(r.locationId);if(!f||f[0]!==r.sourceRenderId||f[1]!==r.sourceClassId)return semantic(pointer(d,"locationId"),`graphs[${n}] invocation location owner is mismatched.`);if(b.get(r.locationId)!=="component-call")return semantic(pointer(d,"locationId"),`graphs[${n}] invocation location kind is mismatched.`)}if(r.parentRegionId!==null&&!I.get("slotRegions").has(r.parentRegionId))return semantic(pointer(d,"parentRegionId"),`graphs[${n}] nested component parentRegionId references an unknown slot region.`);m.set(r.invocationId,[r.sourceRenderId,r.targetRenderId]);for(let f=0;f<r.clientBindings.length;f+=1){const u=r.clientBindings[f],h=pointer(pointer(d,"clientBindings"),f);if(i){if(!I.get("sourceLocations").has(u.locationId))return semantic(pointer(h,"locationId"),`graphs[${n}] client binding has an unknown location.`);const S=w.get(u.locationId);if(!S||S[0]!==r.sourceRenderId||S[1]!==r.sourceClassId)return semantic(pointer(h,"locationId"),`graphs[${n}] client-binding location owner is mismatched.`);if(b.get(u.locationId)!=="component-tag-client-binding")return semantic(pointer(h,"locationId"),`graphs[${n}] client-binding location kind is mismatched.`)}if((u.payload.type==="citry-dom-event"||u.payload.type==="citry-poll")&&u.payload.classId!==r.sourceClassId)return semantic(pointer(pointer(h,"payload"),"classId"),`graphs[${n}] Citry client-binding class is not its source parent.`);const T=bindingKeyIssue(u.payload,u.key,pointer(h,"key"));if(T)return T}}for(let a=0;a<s.componentInstances.length;a+=1){const r=s.componentInstances[a].invocationId;if(r!==null&&!I.get("nestedComponents").has(r))return semantic(pointer(pointer(pointer(o,"componentInstances"),a),"invocationId"),`graphs[${n}] instance has an unknown invocation.`)}for(let a=0;a<v.length;a+=1){const[r,d,f]=v[a],u=pointer(pointer(o,"componentInstances"),a);if(f===null){if(d!==null)return semantic(pointer(u,"parentRenderId"),`graphs[${n}] uninvoked instance has a parent.`);continue}const h=m.get(f);if(!h||h[0]!==d||h[1]!==r)return semantic(pointer(u,"invocationId"),`graphs[${n}] instance endpoints do not match their invocation.`)}for(let a=0;a<s.nestedComponents.length;a+=1){const r=s.nestedComponents[a].invocationId;if((C.get(r)??[]).length!==1)return semantic(pointer(pointer(pointer(o,"nestedComponents"),a),"invocationId"),`graphs[${n}] invocation does not bind exactly one target instance.`)}const $=new Map;for(let a=0;a<s.fills.length;a+=1){const r=s.fills[a],d=pointer(pointer(o,"fills"),a);if(r.ownerRenderId===null!=(r.ownerClassId===null)||r.ownerRenderId!==null&&g.get(r.ownerRenderId)!==r.ownerClassId)return semantic(pointer(d,"ownerRenderId"),`graphs[${n}] fill owner and class are mismatched.`);if(r.receiverRenderId===null!=(r.receiverClassId===null)||r.receiverRenderId!==null&&g.get(r.receiverRenderId)!==r.receiverClassId)return semantic(pointer(d,"receiverRenderId"),`graphs[${n}] fill receiver and class are mismatched.`);if(r.sourceInvocationId!==null&&!I.get("nestedComponents").has(r.sourceInvocationId))return semantic(pointer(d,"sourceInvocationId"),`graphs[${n}] fill has an unknown sourceInvocation.`);const f=r.locationId===null?void 0:b.get(r.locationId),u=r.fallbackLocationId===null?void 0:b.get(r.fallbackLocationId);if(r.policy==="template"){if(r.ownerRenderId===null||r.receiverRenderId===null||!new Set(["implicit","named","fallback"]).has(r.kind))return semantic(pointer(d,"policy"),`graphs[${n}] template fill ownership is inconsistent.`)}else if(r.policy==="python-detached"){if(r.kind!=="python"||r.ownerRenderId!==null||r.receiverRenderId===null||r.sourceInvocationId!==null||r.fallbackLocationId!==null)return semantic(pointer(d,"policy"),`graphs[${n}] detached Python fill ownership is inconsistent.`)}else if(r.kind!=="typed-default"||r.ownerRenderId!==null||r.receiverRenderId===null||r.sourceInvocationId!==null||r.fallbackLocationId!==null)return semantic(pointer(d,"policy"),`graphs[${n}] detached typed-default fill ownership is inconsistent.`);if(i){for(const[S,D]of[["locationId",r.locationId],["fallbackLocationId",r.fallbackLocationId]])if(D!==null&&!I.get("sourceLocations").has(D))return semantic(pointer(d,S),`graphs[${n}] fill has an unknown ${S}.`);const h=r.locationId===null?void 0:w.get(r.locationId),T=r.fallbackLocationId===null?void 0:w.get(r.fallbackLocationId);if(r.ownerRenderId===null!=(h===void 0))return semantic(pointer(d,"locationId"),`graphs[${n}] fill owner and source location are inconsistent.`);if(h&&(h[0]!==r.ownerRenderId||h[1]!==r.ownerClassId))return semantic(pointer(d,"locationId"),`graphs[${n}] fill source location owner is mismatched.`);if(T&&(T[0]!==r.receiverRenderId||T[1]!==r.receiverClassId))return semantic(pointer(d,"fallbackLocationId"),`graphs[${n}] fill fallback location receiver is mismatched.`)}if(r.policy==="template"){if(i){const h={implicit:"implicit-fill",named:"named-fill",fallback:"fallback-fill"}[r.kind];if(f!==h)return semantic(pointer(d,"locationId"),`graphs[${n}] template fill source location kind is mismatched.`);if(r.kind==="fallback"&&(r.fallbackLocationId===null||u!=="slot-outlet"))return semantic(pointer(d,"fallbackLocationId"),`graphs[${n}] fallback location kind is mismatched.`);if(r.kind!=="fallback"&&r.fallbackLocationId!==null)return semantic(pointer(d,"fallbackLocationId"),`graphs[${n}] supplied fill carrier is inconsistent.`)}if(r.kind==="fallback"){if(r.sourceInvocationId!==null)return semantic(pointer(d,"sourceInvocationId"),`graphs[${n}] fallback fill carrier is inconsistent.`)}else{if(r.sourceInvocationId===null)return semantic(pointer(d,"sourceInvocationId"),`graphs[${n}] supplied fill carrier is inconsistent.`);if(m.get(r.sourceInvocationId)?.[0]!==r.ownerRenderId)return semantic(pointer(d,"sourceInvocationId"),`graphs[${n}] supplied fill source invocation owner is mismatched.`)}}$.set(r.fillId,[r.ownerRenderId,r.receiverRenderId,r.locationId])}const k=new Map;for(let a=0;a<s.slotRegions.length;a+=1){const r=s.slotRegions[a],d=pointer(pointer(o,"slotRegions"),a);if(!I.get("fills").has(r.fillId))return semantic(pointer(d,"fillId"),`graphs[${n}] slot region has an unknown fill.`);if(r.parentRegionId!==null&&!I.get("slotRegions").has(r.parentRegionId))return semantic(pointer(d,"parentRegionId"),`graphs[${n}] slot region has an unknown parent.`);for(const[u,h]of Object.entries({receiverRenderId:r.receiverRenderId,ownerRenderId:r.ownerRenderId,transitionFromRenderId:r.transitionFromRenderId,resultOwnerRenderId:r.resultOwnerRenderId}))if(h!==null&&!p.has(h))return semantic(pointer(d,u),`graphs[${n}] slot region.${u} is unknown.`);if(i){for(const[h,T]of[["slotLocationId",r.slotLocationId],["sourceLocationId",r.sourceLocationId]])if(T!==null&&!I.get("sourceLocations").has(T))return semantic(pointer(d,h),`graphs[${n}] slot region has an unknown ${h}.`);const u=r.slotLocationId===null?void 0:w.get(r.slotLocationId);if(u&&u[0]!==r.receiverRenderId)return semantic(pointer(d,"slotLocationId"),`graphs[${n}] slot region slot location receiver is mismatched.`);if(r.slotLocationId!==null&&b.get(r.slotLocationId)!=="slot-outlet")return semantic(pointer(d,"slotLocationId"),`graphs[${n}] slot region slot location kind is mismatched.`)}const f=$.get(r.fillId);if(!f||f[0]!==r.ownerRenderId||f[1]!==r.receiverRenderId||f[2]!==r.sourceLocationId)return semantic(pointer(d,"fillId"),`graphs[${n}] slot region ownership does not match its fill.`);k.set(r.regionId,[r.ownerRenderId,r.receiverRenderId,r.parentRegionId,r.transitionFromRenderId])}if(cycle(new Map(Array.from(k,([a,r])=>[a,r[2]]))))return semantic(pointer(o,"slotRegions"),`graphs[${n}] slot region ancestry contains a cycle.`);for(let a=0;a<s.slotRegions.length;a+=1){const r=s.slotRegions[a],d=r.parentRegionId===null?r.receiverRenderId:k.get(r.parentRegionId)?.[0]??null;if(r.transitionFromRenderId!==d)return semantic(pointer(pointer(pointer(o,"slotRegions"),a),"transitionFromRenderId"),`graphs[${n}] slot region scope transition does not match its ancestry.`)}const O=new Map;for(let a=0;a<s.componentExecutionOrderConstraints.length;a+=1){const r=s.componentExecutionOrderConstraints[a],d=pointer(pointer(o,"componentExecutionOrderConstraints"),a),f=m.get(r.invocationId);if(!f||f[0]!==r.parentRenderId||f[1]!==r.childRenderId)return semantic(pointer(d,"invocationId"),`graphs[${n}] component execution order constraint does not match its invocation.`);const u=O.get(r.parentRenderId)??[];u.push(r.childRenderId),O.set(r.parentRenderId,u)}if(executionCycle(O))return semantic(pointer(o,"componentExecutionOrderConstraints"),`graphs[${n}] component execution order contains a cycle.`);if(cycle(L))return semantic(pointer(o,"componentInstances"),`graphs[${n}] logical instance ancestry contains a cycle.`)}return null},REVISION=/^[0-9a-f]{64}$/,MANIFEST_FIELDS=new Set(["protocol","revision","mode","graphs","delimiters"]),REQUIRED_MANIFEST_FIELDS=["protocol","revision","mode","graphs","delimiters"],DELIMITER_FIELDS=new Set(["format"]),validateManifestShape=(t,e)=>{const i=validateStrictJson(t,e);if(i)return i;if(!isPlainObject(t))return{path:e,category:"type",message:"The client-graph manifest must be an object."};for(const o of REQUIRED_MANIFEST_FIELDS)if(!hasOwn(t,o))return{path:pointer(e,o),category:"required",message:`The manifest requires '${o}'.`};const c=firstUnknown(t,MANIFEST_FIELDS);if(c!==null)return{path:pointer(e,c),category:"unknown_field",message:"The manifest has an unknown field."};if(t.protocol!==PROTOCOL)return{path:pointer(e,"protocol"),category:typeof t.protocol=="string"?"enum":"type",message:`The manifest protocol must be ${PROTOCOL}.`};if(typeof t.revision!="string")return{path:pointer(e,"revision"),category:"type",message:"The manifest revision must be a string."};if(!REVISION.test(t.revision))return{path:pointer(e,"revision"),category:"pattern",message:"The manifest revision must be lowercase SHA-256."};if(typeof t.mode!="string")return{path:pointer(e,"mode"),category:"type",message:"The manifest mode must be a string."};if(t.mode!=="production"&&t.mode!=="development")return{path:pointer(e,"mode"),category:"enum",message:"The manifest mode must be production or development."};if(!Array.isArray(t.graphs))return{path:pointer(e,"graphs"),category:"type",message:"The manifest graphs must be an array."};for(let o=0;o<t.graphs.length;o+=1){const l=validateGraph(t.graphs[o],pointer(pointer(e,"graphs"),o),!1);if(l)return l}const n=pointer(e,"delimiters");if(!isPlainObject(t.delimiters))return{path:n,category:"type",message:"The manifest delimiters must be an object."};if(!hasOwn(t.delimiters,"format"))return{path:pointer(n,"format"),category:"required",message:"The manifest delimiters require 'format'."};const s=firstUnknown(t.delimiters,DELIMITER_FIELDS);return s!==null?{path:pointer(n,s),category:"unknown_field",message:"The manifest delimiters have an unknown field."}:t.delimiters.format!==OWNERSHIP_COMMENT_PREFIX?{path:pointer(n,"format"),category:typeof t.delimiters.format=="string"?"enum":"type",message:`The ownership-comment prefix must be ${OWNERSHIP_COMMENT_PREFIX}.`}:null},validateRevision=(t,e="")=>!isPlainObject(t)||typeof t.revision!="string"||!REVISION.test(t.revision)||revisionForManifest(t)===t.revision?null:{path:pointer(e,"revision"),category:"correlation",message:"The revision does not match the canonical unsigned manifest."},validateManifest=(t,e="")=>{const i=validateManifestShape(t,e);if(i)return i;const c=validateRevision(t,e);return c||validateRelationships(t,e)},assertValidManifest=t=>{const e=validateManifest(t);if(e)throw new ProtocolValueError(e);return t},CitryClientGraphProtocol={OWNERSHIP_COMMENT_PREFIX,parseOwnershipComment,ProtocolValueError,assertValidManifest};
  /*</citry-client-graph-v1>*/

  if (globalThis.Citry && globalThis.Citry.manager) {
    return; // already loaded (e.g. both a document page and a fragment included it)
  }

  // ----- state -----

  // URLs already on the page, per type ("js" / "css").
  var loaded = { js: new Set(), css: new Set() };
  // URL -> the shared Promise for a script request that has started but has
  // not settled. Loaded-URL dedupe alone prevents a duplicate element, but
  // callers must also wait for the first request before running dependent
  // component callbacks.
  var loadingJs = new Map();
  // URL -> {element, promise, resolve}. Stylesheet requests follow the same
  // in-flight dedupe contract as scripts. Keeping the element and resolver in
  // the entry also lets class CSS collection settle a request whose link is
  // removed before its load event fires.
  var loadingCss = new Map();
  // classId -> the class's single $component registration.
  var componentRegistrations = new Map();
  // "classId:varsHash" -> the registered js_data() payload.
  var componentData = new Map();
  // "classId:varsHash" -> active call/instance owners. Data scripts are
  // content-addressed and shared. Ownership references are released after
  // the final pending call or live instance lets go; the payload itself stays
  // paired with the page-lifetime loaded-script cache.
  var componentDataReferences = new Map();
  // componentId -> the data key held by a graph-independent live instance.
  // Graph-owned instances hold the key on their lifecycle.
  var instanceDataKeys = new Map();
  // Calls whose callback or data has not arrived yet.
  var pendingCalls = [];
  // Callback-payload decorators (see decorateContext), in registration order.
  var decorators = [];
  // "classId:componentId" -> cleanup functions the instance's callback
  // returned on its last run, to call before the callback runs again.
  var cleanups = new Map();
  // componentId -> classId for every instance the manager is tracking as
  // live: one whose $component callback has fired, and one a manifest
  // declared present for CSS only (a Component.css instance with no
  // $component JS). This one set is what both the removal reconciler (run
  // an instance's cleanups when it leaves the page) and the per-class
  // Component.css cleanup count against.
  var liveInstances = new Map();
  // Whether a removal sweep is already queued, so many DOM mutations in one
  // batch coalesce into a single sweep on the next microtask.
  var sweepScheduled = false;
  // Class ids with a deferred Component.css collection already queued, so a
  // burst of retirements queues one re-check per class, not many.
  var cssGcPending = new Set();
  // revision -> fully validated, decoded ownership graph. A revision is
  // committed only after every logical reference and physical comment cap
  // passes validation.
  var ownershipGraphs = new Map();
  // revision -> dependency manifests waiting for their graph transaction.
  var graphBlockedManifests = new Map();
  // revision -> callbacks registered through ownership.whenReady().
  var graphWaiters = new Map();
  // revision -> the error that made one ownership transaction fail. A
  // dependency or Events manifest waiting on that revision must reject
  // instead of waiting forever or applying a partial transaction.
  var graphFailures = new Map();
  // Reusing one graph revision in a second dependency transaction would
  // clone concrete component IDs and caps. One revision feeds one dependency
  // manifest only.
  var consumedGraphDependencies = new Set();
  // Script-node identity must not ride a cloneable data-* marker. A moved
  // node is ignored, while cloneNode/outerHTML creates a fresh node that
  // must enter normal duplicate-revision/transaction validation.
  var processedDependencyTags = new WeakSet();
  var processedGraphTags = new WeakSet();
  // Graph tags discovered while the HTML parser is still running cannot be
  // validated until trailing physical caps have landed. Keep them iterable
  // so the Citry-owned Alpine start barrier can commit them before its first
  // DOM walk, independent of DOMContentLoaded listener registration order.
  var deferredGraphTags = new Set();
  // revision -> graph-linked Events adoption status. The Events runtime
  // explicitly acknowledges success or failure so dependency callbacks do
  // not run against a partially adopted anchor registry.
  var graphEvents = new Map();
  // Permanent page-wide Alpine broker state. The pinned Alpine bundle may
  // arrive after graph and component manifests in a fragment, so the core
  // manager owns registrations before Alpine itself exists. Alpine APIs that
  // cannot unregister are installed exactly once and dispatch through these
  // replaceable provider maps.
  var alpineOwner = null;
  var alpineReady = false;
  var alpineStarted = false;
  var alpineStarting = false;
  var alpineStartRequested = false;
  var alpineStartListenerRegistered = false;
  var alpineStartHolds = 0;
  var alpineStartError = null;
  var alpineBeforeStart = [];
  var alpineRootProviders = new Map();
  var alpinePreBoundaryProviders = new Map();
  var alpineInitProviders = new Map();
  var alpineMagicProviders = new Map();
  var alpineMutationProviders = new Map();
  var alpineStartProviders = new Map();
  var reservedAlpineMagics = new Set(["provide", "inject", "unprovide"]);
  var alpineProviderCounter = 0;
  var alpineHookCounts = { installs: 0, roots: 0, init: 0, morph: 0, starts: 0 };
  var alpineLastForeign = null;
  var alpineBoundaryRoot = null;
  // A3 keeps several live revisions at once (the document plus independent
  // fragments). These indexes route render IDs and stable anchors without a
  // page-global "current revision" shortcut.
  var ownershipStates = new Map();
  var browserAnchors = new Map();
  // Permanent replay ledger. One compact revision string is stored for
  // every graph accepted by this document so a retired fragment cannot be
  // cloned and reinserted with concrete IDs and caps that were already used.
  var seenOwnershipRevisions = new Set();
  var ownershipPruneScheduled = false;
  var scheduleOwnershipPrune = null;
  var runtimePlacementCounter = 0;
  // Stable component lifecycle is keyed by logical identity, never by the
  // per-render id. A correlated replacement therefore keeps its reactive
  // scope and live `els` array while replacing only the render invocation.
  var componentLifecycles = new Map();
  var lifecycleReconcileScheduled = false;
  var rangeMorphDepth = 0;
  var ownershipAdoptionDepth = 0;
  var rootScopeOwners = new WeakMap();
  var physicalCorruptionReports = new WeakSet();
  var expectedPhysicalRetirements = new WeakSet();
  var rootHolds = new WeakMap();
  var preBoundarySeen = new WeakSet();
  // One component boundary controller manages every client binding resolved
  // from one nested tag, such as <c-card $c-props="{ theme }" x-on:select="select()" />.
  var componentBoundariesByTarget = new Map();
  var liveComponentBoundaries = new Set();
  var fillSourceDescriptors = new Map();
  var fillRegionRoutes = new Map();
  var fillRoutesByElement = new WeakMap();
  var retiredFillRoots = new WeakSet();
  var fillReconcileScheduled = false;
  var installFillSourceDirective = null;
  var installAmbientContext = null;
  var createAmbientDirectiveControl = null;
  var runAmbientDirective = null;
  var activeAmbientDirective = null;
  var ambientDirectiveControlsByCleanup = new WeakMap();
  var ambientDirectiveEvaluatedAttributesByElement = new WeakMap();
  var ambientCloneSources = new WeakMap();
  var ambientContextRevision = null;
  var touchAmbientContext = null;
  var callWaitsForAmbientMagic = null;
  var ambientMagicFrames = new Set();
  var ambientMagicFramesByElement = new WeakMap();
  var ambientWriteCounter = 0;
  var FILL_SOURCE_FRAME = Symbol("citry-fill-source-frame");
  var FILL_SOURCE_ATTR = "x-citry-fill-source";
  var RETIRED_FILL_SCOPE = Object.freeze({});
  var flushingCalls = false;
  var flushAgain = false;
  // Assigned after graph routing is defined. Keeping the broker callback
  // here lets the embedded Alpine install before any graph exists.
  var isolateRootScope = null;

  var pointedAlpineError = function (message) {
    return new Error("[Citry] Alpine: " + message);
  };

  var rejectStructuralComponentClones = function (root) {
    if (!root || typeof root.querySelectorAll !== "function") return;
    var templates = [];
    if (
      root instanceof HTMLTemplateElement &&
      (root.hasAttribute("x-for") || root.hasAttribute("x-if") || root.hasAttribute("x-teleport"))
    ) templates.push(root);
    root.querySelectorAll("template[x-for],template[x-if],template[x-teleport]").forEach(function (template) {
      templates.push(template);
    });
    templates.forEach(function (template) {
      if (!template.content.querySelector("[data-citry-root]")) return;
      var directive = template.hasAttribute("x-for")
        ? "x-for"
        : template.hasAttribute("x-if")
        ? "x-if"
        : "x-teleport";
      throw pointedAlpineError(
        "native " + directive + " cannot clone a server-rendered client-active Citry component. " +
          "Use server <c-for> for server component lists, or keep the Alpine structural directive inside " +
          "an existing Citry component. A browser blueprint protocol must mint fresh graph, lifecycle, " +
          "source, region, and Events identity before client component instantiation can be supported."
      );
    });
    if (
      root instanceof Element && root._x_refreshXForScope &&
      (root.hasAttribute("data-citry-root") || root.querySelector("[data-citry-root]"))
    ) {
      throw pointedAlpineError(
        "native x-for cannot clone a server-rendered client-active Citry component. " +
          "Use server <c-for> for server component lists, or keep the Alpine loop inside an existing Citry " +
          "component. A browser blueprint protocol must mint fresh graph and lifecycle identity first."
      );
    }
  };

  var warnForeignAlpine = function (foreign) {
    if (!foreign || foreign === alpineOwner || foreign === alpineLastForeign) return;
    alpineLastForeign = foreign;
    console.warn(
      "[Citry] Alpine: another Alpine instance is already on this page. " +
        "Citry owns one pinned instance and restored it as globalThis.Alpine; " +
        "remove the separate Alpine include to prevent duplicate initialization."
    );
  };

  var ensureOwnedAlpineGlobal = function () {
    if (!alpineOwner) return;
    warnForeignAlpine(globalThis.Alpine);
    globalThis.Alpine = alpineOwner;
  };

  var runAlpineBeforeStart = function (callback) {
    try {
      callback(alpineOwner);
    } catch (err) {
      alpineStartError = err;
      throw err;
    }
  };

  var dispatchAlpineMutations = function (mutations) {
    if (
      ambientContextRevision && touchAmbientContext &&
      mutations.some(function (mutation) {
        if (mutation.type !== "childList") return false;
        return Array.from(mutation.addedNodes).concat(Array.from(mutation.removedNodes)).some(function (node) {
          return node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.COMMENT_NODE;
        });
      })
    ) touchAmbientContext();
    Array.from(alpineMutationProviders.values()).forEach(function (provider) {
      try {
        provider(mutations);
      } catch (err) {
        console.error("[Citry] Alpine mutation provider failed:", err);
      }
    });
  };

  var startOwnedAlpine = function () {
    if (!alpineStartRequested || alpineStarted || alpineStarting || !alpineReady || alpineStartHolds > 0) return;
    if (alpineStartError) {
      console.error("[Citry] Alpine startup was cancelled because a beforeStart callback failed:", alpineStartError);
      return;
    }
    var start = function () {
      if (alpineStarted || alpineStartHolds > 0) return;
      ensureOwnedAlpineGlobal();
      alpineStarting = true;
      try {
        flushDeferredGraphTags();
        drainClientManifests();
        Array.from(alpineStartProviders.values()).forEach(function (provider) {
          if (provider.before) provider.before();
        });
        alpineOwner.start();
        alpineStarted = true;
        flushCalls();
        alpineHookCounts.starts += 1;
        Array.from(alpineStartProviders.values()).forEach(function (provider) {
          if (provider.after) provider.after();
        });
      } catch (err) {
        alpineStartError = err;
        console.error("[Citry] Alpine startup failed:", err);
      } finally {
        alpineStarting = false;
      }
    };
    if (document.readyState === "loading") {
      if (!alpineStartListenerRegistered) {
        alpineStartListenerRegistered = true;
        document.addEventListener("DOMContentLoaded", start, { once: true });
      }
    } else {
      start();
    }
  };

  var installAlpine = function (alpine, morphPlugin) {
    if (!alpine || typeof alpine.start !== "function") {
      throw pointedAlpineError("the bundled runtime tried to install an invalid Alpine object.");
    }
    ["closestDataStack", "evaluateRaw", "reactive", "effect", "release", "cloneNode"].forEach(function (name) {
      if (typeof alpine[name] !== "function") {
        throw pointedAlpineError("the pinned runtime is missing required API Alpine." + name + ".");
      }
    });
    rejectStructuralComponentClones(document);
    if (alpineOwner) {
      if (alpineOwner !== alpine) {
        console.warn(
          "[Citry] Alpine: a second Citry Alpine bundle was evaluated. " +
            "The original runtime and all of its registrations were preserved."
        );
      }
      ensureOwnedAlpineGlobal();
      return alpineOwner === alpine;
    }
    warnForeignAlpine(globalThis.Alpine);
    alpineOwner = alpine;
    globalThis.Alpine = alpine;
    var cloneNode = alpine.cloneNode;
    alpine.cloneNode = function (from, to) {
      ambientCloneSources.set(to, from);
      return cloneNode(from, to);
    };
    alpine.plugin(morphPlugin);
    var registerOwnedMagic = alpine.magic.bind(alpine);
    if (installAmbientContext) installAmbientContext(alpine, registerOwnedMagic);
    alpine.magic = function (name, callback) {
      if (reservedAlpineMagics.has(name)) {
        throw pointedAlpineError("$" + name + " is reserved by Citry and cannot be overwritten.");
      }
      return registerOwnedMagic(name, callback);
    };
    if (installFillSourceDirective) installFillSourceDirective(alpine);
    var citryBoundaryDirective = function (el) {
      el.removeAttribute("x-citry-boundary");
      if (!preBoundarySeen.has(el)) {
        preBoundarySeen.add(el);
        Array.from(alpinePreBoundaryProviders.values()).forEach(function (provider) {
          provider(el);
        });
      }
      promoteRootHold(el);
      alpineBoundaryRoot = el;
      try {
        reconcileComponentLifecycles();
        flushCalls();
        Array.from(alpineInitProviders.values()).forEach(function (provider) {
          provider(el);
        });
      } finally {
        alpineBoundaryRoot = null;
      }
    };
    citryBoundaryDirective.inline = function (el) {
      var hold = rootHolds.get(el);
      if (hold && !hold.promoted) promoteRootHold(el);
    };
    alpine.directive("citry-boundary", citryBoundaryDirective).before("data");
    alpineHookCounts.installs += 1;
    alpine.addRootSelector(function () {
      var selectors = [];
      Array.from(alpineRootProviders.values()).forEach(function (provider) {
        var selector = provider();
        if (typeof selector === "string" && selector) selectors.push(selector);
      });
      // A selector callback must always return valid CSS, even before the
      // first provider registers.
      return selectors.length ? selectors.join(",") : "[data-citry-alpine-root]";
    });
    alpineHookCounts.roots += 1;
    alpine.interceptInit(function (el, skip) {
      rejectStructuralComponentClones(el);
      drainClientManifests();
      if (el.hasAttribute && el.hasAttribute("data-citry-root")) {
        // Alpine collects a whole initTree's directive callbacks before it
        // runs any of them. Skip descendants here, but let the root's first
        // citry-boundary handle run its inline phase. That phase promotes the
        // hold, so later root directives are not queued. The deferred boundary
        // handle then runs after already-queued ancestor directives and can
        // capture the initialized parent stack without deadlocking props.
        var hold = rootHolds.get(el);
        if (hold && !hold.promoted) {
          if (!preBoundarySeen.has(el)) el.setAttribute("x-citry-boundary", "");
          skip();
          return;
        }
        if (!preBoundarySeen.has(el)) el.setAttribute("x-citry-boundary", "");
      } else {
        Array.from(alpineInitProviders.values()).forEach(function (provider) {
          provider(el);
        });
      }
    });
    alpineHookCounts.init += 1;
    var queued = alpineBeforeStart;
    alpineBeforeStart = [];
    queued.forEach(runAlpineBeforeStart);
    return true;
  };

  var registerAlpineProvider = function (options) {
    alpineProviderCounter += 1;
    var token = alpineProviderCounter;
    if (options.root) alpineRootProviders.set(token, options.root);
    if (options.beforeBoundary) alpinePreBoundaryProviders.set(token, options.beforeBoundary);
    if (options.init) alpineInitProviders.set(token, options.init);
    if (options.mutations) alpineMutationProviders.set(token, options.mutations);
    if (options.beforeStart || options.afterStart) {
      alpineStartProviders.set(token, { before: options.beforeStart || null, after: options.afterStart || null });
    }
    return function () {
      alpineRootProviders.delete(token);
      alpinePreBoundaryProviders.delete(token);
      alpineInitProviders.delete(token);
      alpineMutationProviders.delete(token);
      alpineStartProviders.delete(token);
    };
  };

  var registerAlpineMagic = function (name, provider) {
    if (typeof name !== "string" || !name || typeof provider !== "function") {
      throw pointedAlpineError("a magic provider needs a non-empty name and a callback.");
    }
    if (reservedAlpineMagics.has(name)) {
      throw pointedAlpineError("$" + name + " is reserved by Citry and cannot be registered by an extension.");
    }
    var providers = alpineMagicProviders.get(name);
    if (!providers) {
      providers = new Map();
      alpineMagicProviders.set(name, providers);
      if (!alpineOwner) throw pointedAlpineError("the pinned runtime must install before internal magics register.");
      alpineOwner.magic(name, function (el) {
        var active = Array.from(providers.values());
        var current = active[active.length - 1];
        return current ? current(el) : undefined;
      });
    }
    alpineProviderCounter += 1;
    var token = alpineProviderCounter;
    providers.set(token, provider);
    return function () { providers.delete(token); };
  };

  // A10's deployment and performance canaries need counts from the owning
  // registries, not browser-specific heap heuristics. Keep this deliberately
  // aggregate: it exposes no author data, nodes, callbacks, or mutable
  // collections, and every number is recomputed from the current live state.
  var alpineRuntimeDebug = function () {
    var lifecycles = 0;
    var rootGroups = 0;
    var rootBindings = 0;
    var nativeListenerTargets = 0;
    var propsEffects = 0;
    var managedEffects = 0;
    var managedResources = 0;
    componentLifecycles.forEach(function (lifecycle) {
      if (!lifecycle.active) return;
      lifecycles += 1;
      if (lifecycle.rootGroup) {
        rootGroups += 1;
        lifecycle.rootGroup.bindings.forEach(function (binding) {
          rootBindings += 1;
          if (binding.targets instanceof Set) nativeListenerTargets += binding.targets.size;
        });
      }
      if (lifecycle.propsController && lifecycle.propsController.effectStop) propsEffects += 1;
      if (lifecycle.invocation && lifecycle.invocation.active) {
        managedEffects += lifecycle.invocation.effectStops.length;
        managedResources += lifecycle.invocation.resources.length;
        if (lifecycle.invocation.userCleanup) managedResources += 1;
      }
    });
    return Object.freeze({
      registrations: componentRegistrations.size,
      componentData: componentData.size,
      componentDataReferences: componentDataReferences.size,
      instanceDataOwners: instanceDataKeys.size,
      lifecycles: lifecycles,
      liveInstances: liveInstances.size,
      ownershipRevisions: ownershipGraphs.size,
      ownershipStates: ownershipStates.size,
      replayRevisions: seenOwnershipRevisions.size,
      dependencyClaims: consumedGraphDependencies.size,
      graphFailures: graphFailures.size,
      browserAnchors: browserAnchors.size,
      componentBoundaries: liveComponentBoundaries.size,
      fillSources: fillSourceDescriptors.size,
      rootGroups: rootGroups,
      rootBindings: rootBindings,
      nativeListenerTargets: nativeListenerTargets,
      propsEffects: propsEffects,
      managedEffects: managedEffects,
      managedResources: managedResources,
      ambientMagicFrames: ambientMagicFrames.size,
      pendingCalls: pendingCalls.length,
    });
  };

  var alpineApi = {
    beforeStart: function (callback) {
      if (typeof callback !== "function") throw pointedAlpineError("beforeStart(callback) needs a callback.");
      if (alpineStarted || alpineStarting || alpineStartError) {
        throw pointedAlpineError("beforeStart(callback) was called after Citry-owned startup.");
      }
      if (alpineOwner) runAlpineBeforeStart(callback);
      else alpineBeforeStart.push(callback);
    },
    _install: installAlpine,
    _ready: function () {
      if (!alpineOwner) throw pointedAlpineError("the runtime cannot become ready before Alpine installs.");
      alpineReady = true;
      flushCalls();
      startOwnedAlpine();
    },
    _start: function () {
      alpineStartRequested = true;
      startOwnedAlpine();
    },
    _holdStart: function () {
      alpineStartHolds += 1;
      var released = false;
      return function () {
        if (released) return;
        released = true;
        alpineStartHolds -= 1;
        startOwnedAlpine();
      };
    },
    _register: registerAlpineProvider,
    _magic: registerAlpineMagic,
    _runDirective: function (el, attributeName, registerCleanup, callback) {
      if (typeof runAmbientDirective !== "function") return callback();
      return runAmbientDirective(el, attributeName, registerCleanup, callback);
    },
    _morph: function (from, to, options) {
      if (!alpineOwner || typeof alpineOwner.morph !== "function") {
        throw pointedAlpineError("morph was requested before the pinned morph plugin installed.");
      }
      ensureOwnedAlpineGlobal();
      alpineHookCounts.morph += 1;
      return alpineOwner.morph(from, to, options);
    },
    _isolateScope: function (root, scope) {
      if (!alpineOwner) throw pointedAlpineError("scope attachment was requested before Alpine installed.");
      if (isolateRootScope) return isolateRootScope(root, scope);
      alpineOwner.addScopeToNode(root, scope);
      root._x_dataStack = root._x_dataStack.slice(0, 1);
    },
    _drain: function () { drainClientManifests(); },
    _isReady: function () { return alpineReady; },
    _isStarted: function () { return alpineStarted; },
    _debug: function () {
      return Object.freeze({
        installed: Boolean(alpineOwner),
        ready: alpineReady,
        started: alpineStarted,
        providers: alpineRootProviders.size,
        preBoundaryProviders: alpinePreBoundaryProviders.size,
        mutationProviders: alpineMutationProviders.size,
        magicNames: Array.from(alpineMagicProviders.keys()).sort(),
        hooks: Object.freeze(Object.assign({}, alpineHookCounts)),
        runtime: alpineRuntimeDebug(),
      });
    },
  };

  var utf8FromBinary = function (binary) {
    return decodeURIComponent(
      Array.prototype.map
        .call(binary, function (ch) {
          return "%" + ("00" + ch.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
  };

  var fromBase64 = function (value) {
    return utf8FromBinary(atob(value)); // atob alone mangles non-ASCII
  };

  var OWNERSHIP_COMMENT_PREFIX =
    CitryClientGraphProtocol.OWNERSHIP_COMMENT_PREFIX;

  var deepFreeze = function (value) {
    if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.keys(value).forEach(function (key) { deepFreeze(value[key]); });
    return Object.freeze(value);
  };

  var validatePhysicalCaps = function (revision, expected, root) {
    root = root || document;
    var revisionPrefix = OWNERSHIP_COMMENT_PREFIX + ":" + revision + ":";
    var comments = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
    var found = new Map();
    var stack = [];
    var openSlotRegionsByGraph = new Map();
    var node;
    while ((node = comments.nextNode())) {
      var text = node.data.trim();
      var ownership = CitryClientGraphProtocol.parseOwnershipComment(text);
      if (!ownership) {
        if (text.indexOf(revisionPrefix) === 0) {
          throw new TypeError("[Citry] graph: malformed physical cap.");
        }
        continue;
      }
      if (ownership.revision !== revision) continue;
      var graphId = ownership.graphId;
      var kind = ownership.kind;
      var recordId = ownership.recordId;
      var side = ownership.side;
      var key = graphId + ":" + kind + ":" + recordId;
      if (!expected.has(key)) throw new TypeError("[Citry] graph: physical cap names an unknown record " + key + ".");
      var pair = found.get(key) || {};
      if (pair[side]) throw new TypeError("[Citry] graph: duplicate physical cap " + key + ".");
      pair[side] = node;
      found.set(key, pair);
      var openSlotRegions = openSlotRegionsByGraph.get(graphId) || [];
      if (side === "s") {
        pair.parentRegion = openSlotRegions.length ? openSlotRegions[openSlotRegions.length - 1] : null;
        stack.push(key);
        if (kind === "r") {
          openSlotRegions.push(Number(recordId));
          openSlotRegionsByGraph.set(graphId, openSlotRegions);
        }
      } else {
        if (stack.pop() !== key) throw new TypeError("[Citry] graph: physical caps cross or close out of order.");
        if (kind === "r") {
          if (openSlotRegions.pop() !== Number(recordId)) {
            throw new TypeError("[Citry] graph: physical slot region caps close out of order.");
          }
          if (!openSlotRegions.length) openSlotRegionsByGraph.delete(graphId);
        }
        var implicitDocumentBody =
          root === document && pair.s && pair.s.parentNode === document && node.parentNode === document.body;
        if (!pair.s || (pair.s.parentNode !== node.parentNode && !implicitDocumentBody)) {
          throw new TypeError("[Citry] graph: physical cap endpoints must share one parent.");
        }
      }
    }
    if (stack.length) throw new TypeError("[Citry] graph: an opening physical cap is unclosed.");
    expected.forEach(function (key) {
      var pair = found.get(key);
      if (!pair || !pair.s || !pair.e) {
        throw new TypeError(
          "[Citry] graph: missing physical cap " + key + ". " +
            "Preserve Citry ownership comments beginning with " + OWNERSHIP_COMMENT_PREFIX +
            " through minification, sanitization, and client DOM updates."
        );
      }
    });
    return found;
  };

  var stageOwnershipManifest = function (manifest, capRoot) {
    var validated = CitryClientGraphProtocol.assertValidManifest(manifest);
    var expectedCaps = new Set();
    var instancesByInvocationByGraph = validated.graphs.map(function (graph, graphIndex) {
      var instancesByInvocation = new Map();
      graph.componentInstances.forEach(function (instance) {
        expectedCaps.add(graphIndex + ":i:" + instance.instanceId);
        if (instance.invocationId !== null) {
          instancesByInvocation.set(instance.invocationId, instance);
        }
      });
      graph.slotRegions.forEach(function (region) {
        expectedCaps.add(graphIndex + ":r:" + region.regionId);
      });
      return instancesByInvocation;
    });
    var caps = validatePhysicalCaps(validated.revision, expectedCaps, capRoot || document);
    validated.graphs.forEach(function (graph, graphIndex) {
      graph.slotRegions.forEach(function (region) {
        var pair = caps.get(graphIndex + ":r:" + region.regionId);
        if (!pair || pair.parentRegion !== region.parentRegionId) {
          throw new TypeError("[Citry] graph: slot region ancestry does not match physical cap nesting.");
        }
      });
      graph.nestedComponents.forEach(function (nestedComponent) {
        var target = instancesByInvocationByGraph[graphIndex].get(nestedComponent.invocationId);
        var pair = target && caps.get(graphIndex + ":i:" + target.instanceId);
        if (!pair || pair.parentRegion !== nestedComponent.parentRegionId) {
          throw new TypeError("[Citry] graph: nested component parent slot region does not match physical cap nesting.");
        }
      });
    });
    caps.forEach(Object.freeze);
    validated.graphs.forEach(deepFreeze);
    return Object.freeze({
      revision: validated.revision,
      graphs: Object.freeze(validated.graphs),
      caps: caps,
    });
  };

  // A read-only Map-shaped view. Object.freeze(new Map()) does not prevent
  // callers from mutating its entries, so committed registry indexes expose
  // snapshots through this small query-only surface instead.
  var readOnlyIndex = function (map, snapshot) {
    var expose = snapshot || function (value) { return value; };
    return Object.freeze({
      get size() { return map.size; },
      has: function (key) { return map.has(key); },
      get: function (key) {
        var value = map.get(key);
        return value === undefined ? undefined : expose(value);
      },
      keys: function () { return Array.from(map.keys()); },
      values: function () { return Array.from(map.values()).map(expose); },
      entries: function () {
        return Array.from(map.entries()).map(function (entry) { return [entry[0], expose(entry[1])]; });
      },
    });
  };

  var qualifiedGraphId = function (graphId, kind, localId) {
    return "g" + graphId + ":" + kind + ":" + localId;
  };

  var decodeClientBindingPayload = function (payload) {
    if (payload.type === "props" || payload.type === "alpine-handler") {
      return Object.freeze({ type: payload.type, expression: payload.expression });
    }
    if (payload.type === "citry-poll") {
      return Object.freeze({
        type: payload.type,
        classId: payload.classId,
        handler: payload.handler,
        args: payload.args,
        interval: payload.interval,
      });
    }
    return Object.freeze({
      type: payload.type,
      classId: payload.classId,
      event: payload.event,
      handler: payload.handler,
      args: payload.args,
      key: payload.key,
      once: payload.once,
      prevent: payload.prevent,
      self: payload.self,
      stop: payload.stop,
      debounce: payload.debounce,
      throttle: payload.throttle,
    });
  };

  var makeClientIdentity = function (revision, graphId, instanceId, renderId, classId) {
    var anchorState = {
      id: "a:" + revision + ":" + graphId + ":" + instanceId,
      active: true,
      revision: revision,
      renderId: renderId,
      classId: classId,
      logical: null,
      events: null,
      generation: 1,
    };
    var logicalState = {
      id: "l:" + revision + ":" + graphId + ":" + instanceId + ":1",
      active: true,
      revision: revision,
      renderId: renderId,
      classId: classId,
      anchor: null,
      generation: 1,
      lifecycle: null,
      scope: null,
      els: [],
      parentLogical: null,
      morphKey: null,
      morphMode: null,
      childOrder: [],
    };
    var anchor = {};
    Object.defineProperties(anchor, {
      id: { value: anchorState.id, enumerable: true },
      active: { get: function () { return anchorState.active; }, enumerable: true },
      revision: { get: function () { return anchorState.revision; }, enumerable: true },
      renderId: { get: function () { return anchorState.renderId; }, enumerable: true },
      classId: { get: function () { return anchorState.classId; }, enumerable: true },
      logicalInstance: { get: function () { return anchorState.logical; }, enumerable: true },
      events: { get: function () { return anchorState.events; }, enumerable: true },
    });
    Object.freeze(anchor);
    var logical = {};
    Object.defineProperties(logical, {
      id: { value: logicalState.id, enumerable: true },
      generation: { value: logicalState.generation, enumerable: true },
      active: { get: function () { return logicalState.active; }, enumerable: true },
      revision: { get: function () { return logicalState.revision; }, enumerable: true },
      renderId: { get: function () { return logicalState.renderId; }, enumerable: true },
      classId: { get: function () { return logicalState.classId; }, enumerable: true },
      anchor: { get: function () { return logicalState.anchor; }, enumerable: true },
    });
    Object.freeze(logical);
    anchorState.logical = logical;
    logicalState.anchor = anchor;
    return { anchor: anchor, anchorState: anchorState, logical: logical, logicalState: logicalState };
  };

  // Decode the fully validated A2 arrays into graph-qualified records and
  // query indexes. No global registry changes happen here, so a failure in a
  // later record leaves every previously committed revision untouched.
  var normalizeOwnershipRevision = function (staged) {
    var graphs = new Map();
    var componentClasses = new Map();
    var componentInstances = new Map();
    var renderIds = new Map();
    var sourceLocations = new Map();
    var nestedComponents = new Map();
    var fills = new Map();
    var slotRegions = new Map();
    var slotRegionsByFill = new Map();
    var physicalRegions = new Map();
    var physicalPlacements = new Map();
    var componentExecutionOrderConstraints = new Map();
    var anchors = new Map();
    var logicalInstances = new Map();
    var renderLinks = new Map();
    var childrenByParent = new Map();
    var executionOrderParentByChild = new Map();
    var rangeGroups = new Map();
    var rangeGroupStates = new Map();

    staged.graphs.forEach(function (graph) {
      var graphRecord = Object.freeze({ id: graph.graphId });
      graphs.set(graph.graphId, graphRecord);
      graph.componentClasses.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "c", record.classId);
        componentClasses.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          classId: record.classId,
          name: record.className,
        }));
      });
      graph.componentInstances.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "i", record.instanceId);
        var renderId = record.renderId;
        if (renderIds.has(renderId)) {
          throw new TypeError("[Citry] graph: render id '" + renderId + "' appears in more than one graph.");
        }
        var identity = makeClientIdentity(staged.revision, graph.graphId, record.instanceId, renderId, record.classId);
        var link = { active: true, anchor: identity.anchor, logical: identity.logical };
        var instance = {
          key: key,
          graphId: graph.graphId,
          instanceId: record.instanceId,
          renderId: renderId,
          classId: record.classId,
          parentRenderId: record.parentRenderId,
          invocationId: record.invocationId,
          transparent: record.transparent,
        };
        Object.defineProperties(instance, {
          active: { get: function () { return link.active; }, enumerable: true },
          anchor: { get: function () { return link.anchor; }, enumerable: true },
          logicalInstance: { get: function () { return link.logical; }, enumerable: true },
        });
        Object.freeze(instance);
        componentInstances.set(key, instance);
        renderIds.set(renderId, instance);
        anchors.set(identity.anchor.id, identity.anchor);
        logicalInstances.set(identity.logical.id, identity.logical);
        renderLinks.set(renderId, {
          record: instance,
          link: link,
          anchorState: identity.anchorState,
          logicalState: identity.logicalState,
        });
        if (instance.parentRenderId != null) {
          var children = childrenByParent.get(instance.parentRenderId) || [];
          children.push(renderId);
          childrenByParent.set(instance.parentRenderId, children);
        }
      });
      graph.sourceLocations.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "l", record.locationId);
        sourceLocations.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          locationId: record.locationId,
          kind: record.kind,
          ownerRenderId: record.ownerRenderId,
          classId: record.ownerClassId,
          carrierInstanceId: record.carrierInstanceId,
          origin: record.origin,
          start: record.sourceOffset.start,
          end: record.sourceOffset.end,
          line: record.sourcePos.line,
          column: record.sourcePos.column,
          mappingKey: record.mappingKey,
          mappingIndex: record.mappingIndex,
        }));
      });
      graph.nestedComponents.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "v", record.invocationId);
        var clientBindings = record.clientBindings.map(function (clientBinding) {
          return Object.freeze({
            key: clientBinding.key,
            locationId: clientBinding.locationId,
            source: clientBinding.source,
            payload: decodeClientBindingPayload(clientBinding.payload),
          });
        });
        nestedComponents.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          invocationId: record.invocationId,
          locationId: record.locationId,
          parentRegionId: record.parentRegionId,
          sourceRenderId: record.sourceRenderId,
          sourceClassId: record.sourceClassId,
          tag: record.tagName,
          morphKey: record.morphKey,
          morphMode: record.morphMode,
          targetRenderId: record.targetRenderId,
          targetClassId: record.targetClassId,
          clientBindings: Object.freeze(clientBindings),
        }));
        var targetLink = renderLinks.get(record.targetRenderId);
        if (targetLink) {
          targetLink.logicalState.morphKey = record.morphKey;
          targetLink.logicalState.morphMode = record.morphMode;
        }
      });
      graph.fills.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "f", record.fillId);
        fills.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          fillId: record.fillId,
          kind: record.kind,
          policy: record.policy,
          slot: record.slotName,
          ownerRenderId: record.ownerRenderId,
          ownerClassId: record.ownerClassId,
          receiverRenderId: record.receiverRenderId,
          receiverClassId: record.receiverClassId,
          sourceLocationId: record.locationId,
          sourceInvocationId: record.sourceInvocationId,
          fallbackLocationId: record.fallbackLocationId,
        }));
      });
      graph.slotRegions.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "r", record.regionId);
        var cap = staged.caps.get(graph.graphId + ":r:" + record.regionId);
        var physical = Object.freeze({
          key: key,
          graphId: graph.graphId,
          regionId: record.regionId,
          start: cap.s,
          end: cap.e,
          startMarker: cap.s.data,
          endMarker: cap.e.data,
          parentRegionId: cap.parentRegion,
          topology: cap.s.parentNode === cap.e.parentNode ? "same-parent" : "document-body",
        });
        physicalRegions.set(key, physical);
        physicalPlacements.set(key, [physical]);
        slotRegions.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          regionId: record.regionId,
          fillId: record.fillId,
          ownerRenderId: record.ownerRenderId,
          receiverRenderId: record.receiverRenderId,
          resultOwnerRenderId: record.resultOwnerRenderId,
          transitionFromRenderId: record.transitionFromRenderId,
          parentRegionId: record.parentRegionId,
          slotLocationId: record.slotLocationId,
          sourceLocationId: record.sourceLocationId,
          physical: physical,
        }));
        var fillKey = qualifiedGraphId(graph.graphId, "f", record.fillId);
        var fillSlotRegions = slotRegionsByFill.get(fillKey) || [];
        fillSlotRegions.push(slotRegions.get(key));
        slotRegionsByFill.set(fillKey, fillSlotRegions);
      });
      graph.componentInstances.forEach(function (record) {
        var cap = staged.caps.get(graph.graphId + ":i:" + record.instanceId);
        var key = qualifiedGraphId(graph.graphId, "i", record.instanceId);
        var physical = Object.freeze({
          key: key,
          graphId: graph.graphId,
          instanceId: record.instanceId,
          start: cap.s,
          end: cap.e,
          startMarker: cap.s.data,
          endMarker: cap.e.data,
          parentRegionId: cap.parentRegion,
          topology: cap.s.parentNode === cap.e.parentNode ? "same-parent" : "document-body",
        });
        physicalRegions.set(key, physical);
        physicalPlacements.set(key, [physical]);
      });
      graph.componentExecutionOrderConstraints.forEach(function (record, index) {
        var key = qualifiedGraphId(graph.graphId, "d", index + 1);
        componentExecutionOrderConstraints.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          parentRenderId: record.parentRenderId,
          childRenderId: record.childRenderId,
          invocationId: record.invocationId,
        }));
        executionOrderParentByChild.set(record.childRenderId, record.parentRenderId);
      });
    });
    childrenByParent.forEach(function (children, parentRenderId) {
      var parentLink = renderLinks.get(parentRenderId);
      if (parentLink) parentLink.logicalState.childOrder = children.slice();
    });

    renderLinks.forEach(function (link) {
      if (link.record.parentRenderId == null) return;
      var parent = renderLinks.get(link.record.parentRenderId);
      if (parent) link.logicalState.parentLogical = parent.logicalState;
    });

    fills.forEach(function (fill) {
      var key = qualifiedGraphId(fill.graphId, "f", fill.fillId);
      var groupedRegions = slotRegionsByFill.get(key) || [];
      if (!groupedRegions.length) return;
      var groupState = {
        active: true,
        retired: false,
        els: [],
        liveSlotRegions: groupedRegions.slice(),
        slotRegions: groupedRegions,
      };
      var group = {
        key: key,
        graphId: fill.graphId,
        fillId: fill.fillId,
        slotRegions: Object.freeze(groupedRegions.slice()),
        els: groupState.els,
      };
      Object.defineProperties(group, {
        active: { enumerable: true, get: function () { return groupState.active; } },
        liveSlotRegions: {
          enumerable: true,
          get: function () { return Object.freeze(groupState.liveSlotRegions.slice()); },
        },
      });
      Object.freeze(group);
      rangeGroups.set(key, group);
      rangeGroupStates.set(key, groupState);
    });

    var registry = Object.freeze({
      graphs: readOnlyIndex(graphs),
      componentClasses: readOnlyIndex(componentClasses),
      componentInstances: readOnlyIndex(componentInstances),
      renderIds: readOnlyIndex(renderIds),
      sourceLocations: readOnlyIndex(sourceLocations),
      nestedComponents: readOnlyIndex(nestedComponents),
      fills: readOnlyIndex(fills),
      slotRegions: readOnlyIndex(slotRegions),
      physicalRegions: readOnlyIndex(physicalRegions),
      physicalPlacements: readOnlyIndex(physicalPlacements, function (placements) {
        return Object.freeze(placements.slice());
      }),
      componentExecutionOrderConstraints: readOnlyIndex(componentExecutionOrderConstraints),
      anchors: readOnlyIndex(anchors),
      logicalInstances: readOnlyIndex(logicalInstances),
      rangeGroups: readOnlyIndex(rangeGroups),
    });
    var publicRevision = Object.freeze({
      revision: staged.revision,
      graphs: staged.graphs,
      caps: readOnlyIndex(staged.caps),
      registry: registry,
    });
    return {
      publicRevision: publicRevision,
      registry: registry,
      caps: staged.caps,
      physicalRegions: physicalRegions,
      physicalPlacements: physicalPlacements,
      slotRegions: slotRegions,
      renderIds: renderIds,
      renderLinks: renderLinks,
      anchors: anchors,
      logicalInstances: logicalInstances,
      childrenByParent: childrenByParent,
      executionOrderParentByChild: executionOrderParentByChild,
      rangeGroupStates: rangeGroupStates,
      graphCalls: new Map(),
      retainedPhysicalKeys: new Set(),
      provisional: false,
      adoption: null,
    };
  };

  var resolveOwnershipRoute = function (revision, renderId, classId) {
    var state = ownershipStates.get(revision);
    if (!state) {
      throw new TypeError("[Citry] graph: callback references unknown revision " + revision + ".");
    }
    var instance = state.renderIds.get(renderId);
    if (!instance || !instance.active) {
      throw new TypeError(
        "[Citry] graph: callback references inactive or unknown render id '" + renderId + "' in revision " + revision + "."
      );
    }
    if (classId != null && instance.classId !== classId) {
      throw new TypeError(
        "[Citry] graph: render id '" + renderId + "' belongs to class '" + instance.classId +
          "', not callback class '" + classId + "'."
      );
    }
    return Object.freeze({
      revision: revision,
      instance: instance,
      logicalInstance: instance.logicalInstance,
      anchor: instance.anchor,
    });
  };

  // ----- graph-owned component lifecycle and Alpine scope projection -----

  var replaceArrayContents = function (target, values) {
    target.splice.apply(target, [0, target.length].concat(values));
  };

  var routeForLifecycle = function (lifecycle) {
    if (!lifecycle.logicalState.active) return null;
    try {
      return resolveOwnershipRoute(
        lifecycle.logicalState.revision,
        lifecycle.logicalState.renderId,
        lifecycle.logicalState.classId
      );
    } catch (_err) {
      return null;
    }
  };

  var nodePrecedes = function (before, after) {
    return Boolean(before.compareDocumentPosition(after) & Node.DOCUMENT_POSITION_FOLLOWING);
  };

  var physicalRangesForKey = function (state, key) {
    var placements = state && state.physicalPlacements && state.physicalPlacements.get(key);
    if (placements) return placements;
    var physical = state && state.registry.physicalRegions.get(key);
    return physical ? [physical] : [];
  };

  var physicalRangeIsLive = function (state, physical) {
    if (!physical) return false;
    var staged = state.provisional && !physical.start.isConnected && !physical.end.isConnected;
    if (!staged && (!physical.start.isConnected || !physical.end.isConnected)) return false;
    if (physical.start.data !== physical.startMarker || physical.end.data !== physical.endMarker) return false;
    var topologyLive = staged
      ? physical.start.parentNode === physical.end.parentNode
      : physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode === physical.end.parentNode;
    if (!topologyLive || !nodePrecedes(physical.start, physical.end)) return false;
    if (physical.parentRegionId != null) {
      var parent = physical.parentPlacement || state.registry.physicalRegions.get(
        qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
      );
      if (
        !parent || !physicalRangeIsLive(state, parent) ||
        !nodePrecedes(parent.start, physical.start) || !nodePrecedes(physical.end, parent.end)
      ) return false;
    }
    return true;
  };

  var physicalRangeCorruption = function (state, physical) {
    if (!physical || !physical.start.isConnected || !physical.end.isConnected) return null;
    if (physical.start.data !== physical.startMarker || physical.end.data !== physical.endMarker) {
      return "one of its load-bearing comment caps was changed";
    }
    var topologyLive = physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode === physical.end.parentNode;
    if (!topologyLive) return "its comment caps no longer share the validated parent topology";
    if (!nodePrecedes(physical.start, physical.end)) return "its comment caps are reversed";
    if (physical.parentRegionId != null) {
      var parent = physical.parentPlacement || state.registry.physicalRegions.get(
        qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
      );
      if (
        !parent || !physicalRangeIsLive(state, parent) ||
        !nodePrecedes(parent.start, physical.start) || !nodePrecedes(physical.end, parent.end)
      ) return "it moved outside its recorded parent region";
    }
    return null;
  };

  var reportPhysicalRangeCorruption = function (state, physical) {
    var reason = physicalRangeCorruption(state, physical);
    if (!reason || expectedPhysicalRetirements.has(physical) || physicalCorruptionReports.has(physical)) return;
    physicalCorruptionReports.add(physical);
    console.error(
      "[Citry] ownership range '" + physical.key + "' was retired because " + reason +
        ". Preserve Citry ownership comments beginning with " + OWNERSHIP_COMMENT_PREFIX +
        " through minification, sanitization, and client DOM updates."
    );
  };

  var physicalRangeElements = function (physical) {
    var roots = [];
    var node = null;
    if (physical.topology === "document-body") {
      // A complete-document fragment can put the opening cap under Document
      // and the closing cap under body. Its markerless physical roots are the
      // direct body element children in the exact document-order interval.
      // This is the same narrow parser topology validated at adoption; it is
      // not a license to enumerate arbitrary marked nodes from the document.
      for (node = document.body.firstChild; node && node !== physical.end; node = node.nextSibling) {
        if (node instanceof Element && nodePrecedes(physical.start, node)) roots.push(node);
      }
      return roots;
    }
    if (physical.start.parentNode !== physical.end.parentNode) return roots;
    for (node = physical.start.nextSibling; node && node !== physical.end; node = node.nextSibling) {
      if (node instanceof Element) roots.push(node);
    }
    return roots;
  };

  var physicalRangeRoots = function (physical, renderId) {
    if (physical.topology === "same-parent") {
      var marker = "data-cid-" + renderId;
      var roots = [];
      physicalRangeElements(physical).forEach(function (topLevel) {
        if (topLevel.hasAttribute(marker)) {
          roots.push(topLevel);
          return;
        }
        // Serialization extensions may insert an unmarked visual wrapper
        // around the component's authored marked roots. Stay inside the exact
        // caps, select only the outermost matching descendants, and never
        // promote the extension wrapper into the component's public `els`.
        topLevel.querySelectorAll("[" + marker + "]").forEach(function (candidate) {
          var ancestor = candidate.parentElement;
          while (ancestor && ancestor !== topLevel) {
            if (ancestor.hasAttribute(marker)) return;
            ancestor = ancestor.parentElement;
          }
          roots.push(candidate);
        });
      });
      return roots;
    }
    // The HTML parser may place a complete-document opening cap under
    // Document and its closing cap under body. A2 validates this one narrow
    // topology, whose roots cannot be enumerated as ordinary siblings. The
    // document query is only a candidate source; both comparisons keep the
    // result inside the exact cap interval.
    return Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + renderId + "]")).filter(
      function (candidate) {
        return nodePrecedes(physical.start, candidate) && nodePrecedes(candidate, physical.end);
      }
    );
  };

  var reconcilePhysicalRangeGroups = function () {
    ownershipStates.forEach(function (state) {
      state.rangeGroupStates.forEach(function (group) {
        if (group.retired) return;
        var livePlacements = [];
        group.slotRegions.forEach(function (region) {
          physicalRangesForKey(state, region.key).forEach(function (physical) {
            var isLive = physicalRangeIsLive(state, physical);
            if (!isLive) reportPhysicalRangeCorruption(state, physical);
            if (isLive) livePlacements.push({ region: region, physical: physical });
          });
        });
        livePlacements.sort(function (left, right) {
          if (nodePrecedes(left.physical.start, right.physical.start)) return -1;
          if (nodePrecedes(right.physical.start, left.physical.start)) return 1;
          return 0;
        });
        group.liveSlotRegions = livePlacements.map(function (entry) { return entry.region; });
        replaceArrayContents(group.els, livePlacements.flatMap(function (entry) {
          return physicalRangeElements(entry.physical);
        }));
        if (livePlacements.length) return;
        group.active = false;
        group.retired = true;
      });
    });
  };

  var RANGE_ISLAND_ATTR = "data-citry-range-island";
  var rangeCapInfo = function (node) {
    if (!(node instanceof Comment)) return null;
    var ownership = CitryClientGraphProtocol.parseOwnershipComment(node.data);
    if (ownership) {
      return {
        key: ownership.key,
        revision: ownership.revision,
        recordKey: qualifiedGraphId(
          Number(ownership.graphId),
          ownership.kind,
          Number(ownership.recordId)
        ),
        side: ownership.side,
      };
    }
    var match = /^citry:p1:([0-9a-f]{64}):([A-Za-z0-9_-]+):([0-9]+):([ir]):([0-9]+):([se])$/.exec(node.data.trim());
    if (!match) return null;
    return {
      key: "citry:p1:" + match[1] + ":" + match[2] + ":" + match[3] + ":" + match[4] + ":" + match[5],
      revision: match[1],
      recordKey: qualifiedGraphId(Number(match[3]), match[4], Number(match[5])),
      side: match[6],
    };
  };

  var directRangePairs = function (parent, includeNested, boundary) {
    var stack = [];
    var pairs = [];
    var childNodes = Array.prototype.slice.call(parent.childNodes);
    if (boundary) {
      if (boundary.start.parentNode !== parent || boundary.end.parentNode !== parent) {
        throw new TypeError("[Citry] ownership range scan boundary must belong to its parent.");
      }
      var startIndex = childNodes.indexOf(boundary.start);
      var endIndex = childNodes.indexOf(boundary.end);
      if (startIndex < 0 || endIndex <= startIndex) {
        throw new TypeError("[Citry] ownership range scan boundary is disconnected or reversed.");
      }
      childNodes = childNodes.slice(startIndex + 1, endIndex);
    }
    childNodes.forEach(function (node) {
      var info = rangeCapInfo(node);
      if (!info) return;
      if (info.side === "s") {
        stack.push({ key: info.key, start: node, revision: info.revision, recordKey: info.recordKey });
        return;
      }
      var opened = stack.pop();
      if (!opened || opened.key !== info.key) {
        throw new TypeError(
          "[Citry] range morph received crossed or unmatched ownership caps near " + info.key +
            " (open cap: " + (opened ? opened.key : "none") + ")."
        );
      }
      pairs.push({
        key: info.key,
        start: opened.start,
        end: node,
        depth: stack.length,
        revision: opened.revision,
        recordKey: opened.recordKey,
      });
    });
    if (stack.length) {
      throw new TypeError("[Citry] range morph received an ownership opening cap without its closing cap.");
    }
    return includeNested ? pairs : pairs.filter(function (pair) { return pair.depth === 0; });
  };

  var collapseRangePair = function (pair, stableAnchor) {
    var placeholder = document.createElement("template");
    placeholder.setAttribute(RANGE_ISLAND_ATTR, pair.key);
    placeholder.setAttribute("key", "citry-range:" + stableAnchor);
    if (pair.topology === "document-body") {
      var firstBodyNode = document.body.firstChild;
      placeholder._citryDocumentStart = {
        nodes: [],
        next: document.documentElement,
      };
      document.body.insertBefore(placeholder, firstBodyNode);
      for (var documentNode = pair.start; documentNode && documentNode !== document.documentElement;) {
        var documentNext = documentNode.nextSibling;
        placeholder._citryDocumentStart.nodes.push(documentNode);
        placeholder.content.append(documentNode);
        documentNode = documentNext;
      }
      for (var bodyNode = firstBodyNode; bodyNode;) {
        var bodyNext = bodyNode.nextSibling;
        placeholder.content.append(bodyNode);
        if (bodyNode === pair.end) break;
        bodyNode = bodyNext;
      }
      return placeholder;
    }
    pair.start.before(placeholder);
    for (var node = pair.start; node;) {
      var next = node.nextSibling;
      placeholder.content.append(node);
      if (node === pair.end) break;
      node = next;
    }
    return placeholder;
  };

  var rangePairCanCollapse = function (pair) {
    if (pair.topology === "document-body") {
      if (pair.start.parentNode !== document || pair.end.parentNode !== document.body) return false;
      for (var node = pair.start; node && node !== document.documentElement; node = node.nextSibling) {
        if (!(node instanceof Comment)) return false;
      }
      return node === document.documentElement;
    }
    return pair.start.parentNode instanceof Element && pair.start.parentNode === pair.end.parentNode;
  };

  var assertRangePairCanCollapse = function (pair) {
    if (rangePairCanCollapse(pair)) return;
    throw new TypeError(
      "[Citry] range morph cannot protect nested ownership caps with unsupported parent topology near " +
        pair.key + "."
    );
  };

  var physicalRangeContainsNode = function (physical, node) {
    return nodePrecedes(physical.start, node) && nodePrecedes(node, physical.end);
  };

  var physicalStableAnchor = function (state, physical) {
    var instance = state.registry.componentInstances.get(physical.key);
    if (instance) return instance.logicalInstance.id;
    var region = state.registry.slotRegions.get(physical.key);
    return region ? "fill:" + region.graphId + ":" + region.fillId + ":" + region.regionId : physical.key;
  };

  var nestedPhysicalRanges = function (state, outer) {
    var candidates = [];
    ownershipStates.forEach(function (candidateState) {
      candidateState.physicalPlacements.forEach(function (placements) {
        placements.forEach(function (physical) {
        if (
          (candidateState !== state || physical !== outer) &&
          physicalRangeIsLive(candidateState, physical) &&
          physicalRangeContainsNode(outer, physical.start) &&
          physicalRangeContainsNode(outer, physical.end)
        ) candidates.push({ state: candidateState, physical: physical });
        });
      });
    });
    return candidates.filter(function (candidate) {
      return !candidates.some(function (other) {
        return other !== candidate &&
          physicalRangeContainsNode(other.physical, candidate.physical.start) &&
          physicalRangeContainsNode(other.physical, candidate.physical.end);
      });
    });
  };

  var collapseIncomingRanges = function (root, correspondence) {
    var visit = function (parent) {
      var pairs = directRangePairs(parent);
      var covered = new Set();
      pairs.forEach(function (pair) {
        for (var node = pair.start; node;) {
          covered.add(node);
          if (node === pair.end) break;
          node = node.nextSibling;
        }
        var stable = correspondence && Object.prototype.hasOwnProperty.call(correspondence, pair.key)
          ? correspondence[pair.key]
          : "incoming:" + pair.key;
        collapseRangePair(pair, stable);
      });
      Array.prototype.slice.call(parent.children).forEach(function (child) {
        if (!covered.has(child) && !child.hasAttribute(RANGE_ISLAND_ATTR)) visit(child);
      });
    };
    visit(root);
  };

  var contextualRangeContainer = function (start, end, html) {
    if (!(start.parentElement instanceof Element) || start.parentNode !== end.parentNode) {
      throw new TypeError("[Citry] range morph needs operational comment caps under one Element parent.");
    }
    var range = document.createRange();
    range.setStartAfter(start);
    range.collapse(true);
    var fragment = range.createContextualFragment(html);
    var container = start.parentElement.cloneNode(false);
    container.removeAttribute("id");
    container.append(fragment);
    return container;
  };

  var expandRangePlaceholder = function (placeholder) {
    var documentStart = placeholder._citryDocumentStart;
    if (documentStart) {
      for (var index = 0; index < documentStart.nodes.length; index += 1) {
        var expected = documentStart.nodes[index];
        if (placeholder.content.firstChild !== expected) {
          throw new TypeError("[Citry] document-body ownership island lost one of its document-level caps.");
        }
        document.insertBefore(expected, documentStart.next);
      }
    }
    placeholder.before(placeholder.content);
    placeholder.remove();
  };

  var expandRangeIslands = function (physical) {
    var placeholders = [];
    physicalRangeElements(physical).forEach(function (root) {
      if (root.hasAttribute(RANGE_ISLAND_ATTR)) placeholders.push(root);
      root.querySelectorAll("template[" + RANGE_ISLAND_ATTR + "]").forEach(function (item) {
        placeholders.push(item);
      });
    });
    placeholders.forEach(function (placeholder) {
      if (!placeholder.isConnected || !physicalRangeContainsNode(physical, placeholder)) return;
      expandRangePlaceholder(placeholder);
    });
  };

  var PLANNED_RANGE_HOLDER_ATTR = "data-citry-range-holder";
  var PLANNED_RANGE_SLOT_ATTR = "data-citry-range-slot";
  var PLANNED_RANGE_PORTABLE_ATTR = "data-citry-range-portable";
  var PLANNED_RANGE_SENTINEL_ATTR = "data-citry-range-sentinel";
  var plannedRangeSlotCounter = 0;

  var nodesInsidePair = function (pair) {
    var nodes = [];
    if (!pair.start || !pair.end || pair.start.parentNode !== pair.end.parentNode) return nodes;
    for (var node = pair.start.nextSibling; node && node !== pair.end; node = node.nextSibling) nodes.push(node);
    return nodes;
  };

  var pairContainsPair = function (outer, inner) {
    return outer !== inner && nodePrecedes(outer.start, inner.start) && nodePrecedes(inner.end, outer.end);
  };

  var rangePairsUnder = function (root, boundary) {
    var pairs = [];
    var seen = new Set();
    var visit = function (parent, window) {
      directRangePairs(parent, true, window).forEach(function (pair) {
        if (seen.has(pair.start)) return;
        if (boundary && !pairContainsPair(boundary, pair)) return;
        seen.add(pair.start);
        pairs.push(pair);
      });
      var children = window
        ? nodesInsidePair(window).filter(function (node) { return node instanceof Element; })
        : Array.prototype.slice.call(parent.children || []);
      children.forEach(function (child) { visit(child, null); });
    };
    visit(root, boundary && boundary.start.parentNode === root ? boundary : null);
    return pairs;
  };

  var pairForRecord = function (pairs, revision, recordKey) {
    return pairs.find(function (pair) {
      return pair.revision === revision && pair.recordKey === recordKey;
    }) || null;
  };

  var collapsePlannedRange = function (pair, slot, kind, match) {
    if (!pair.start || !pair.end || pair.start.parentNode !== pair.end.parentNode) {
      throw new TypeError("[Citry] planned component range has unsupported cap topology.");
    }
    var holder = document.createElement("template");
    holder.setAttribute(PLANNED_RANGE_HOLDER_ATTR, kind);
    holder.setAttribute(PLANNED_RANGE_SLOT_ATTR, slot);
    if (match) {
      holder.setAttribute(PLANNED_RANGE_PORTABLE_ATTR, slot);
      holder._citryRangeMatch = match;
    }
    pair.start.before(holder);
    for (var node = pair.start; node;) {
      var next = node.nextSibling;
      holder.content.append(node);
      if (node === pair.end) break;
      node = next;
    }
    return holder;
  };

  var insertPlannedSentinel = function (pair, slot, side, before) {
    var sentinel = document.createElement("template");
    sentinel.setAttribute(PLANNED_RANGE_SENTINEL_ATTR, side);
    sentinel.setAttribute(PLANNED_RANGE_SLOT_ATTR, slot);
    if (before) pair.start.before(sentinel);
    else pair.end.after(sentinel);
    return sentinel;
  };

  var plannedElementKey = function (element, options) {
    if (!(element instanceof Element)) return null;
    return typeof options.key === "function"
      ? options.key(element)
      : element.getAttribute("data-citry-key");
  };

  var plannedPathSegment = function (element, options, boundarySiblings) {
    var key = plannedElementKey(element, options);
    if (key !== null) return element.localName + "#" + JSON.stringify(key);
    var siblings = boundarySiblings ||
      Array.prototype.slice.call((element.parentNode && element.parentNode.childNodes) || []);
    return element.localName + "@" + siblings.indexOf(element);
  };

  var plannedParentPath = function (pair, boundary, options) {
    var boundaryParent = boundary.start ? boundary.start.parentNode : boundary;
    if (pair.start.parentNode === boundaryParent) return "";
    var boundarySiblings = boundary.start
      ? nodesInsidePair(boundary)
      : Array.prototype.slice.call(boundary.childNodes || []);
    var segments = [];
    var current = pair.start.parentElement;
    while (current && current !== boundaryParent) {
      segments.push(plannedPathSegment(
        current,
        options,
        current.parentNode === boundaryParent ? boundarySiblings : null
      ));
      current = current.parentElement;
    }
    return current === boundaryParent ? segments.reverse().join("/") : null;
  };

  var plannedWindowSignature = function (target, pairs, normalize, boundary, options) {
    var byStart = new Map();
    pairs.forEach(function (pair) {
      if (pair && pair.start.parentNode === target.start.parentNode) byStart.set(pair.start, pair);
    });
    var tokens = [];
    var boundaryParent = boundary.start ? boundary.start.parentNode : boundary;
    var boundedByPair = boundary.start && target.start.parentNode === boundaryParent;
    var stop = boundedByPair ? boundary.end : null;
    var node = boundedByPair
      ? boundary.start.nextSibling
      : target.start.parentNode === boundaryParent
        ? boundary.firstChild
        : target.start.parentNode.firstChild;
    for (; node && node !== stop;) {
      var range = byStart.get(node);
      if (range) {
        if (range === target) {
          tokens.push("TARGET");
          break;
        }
        tokens.push("RANGE:" + normalize(range));
        node = range.end.nextSibling;
        continue;
      }
      if (node instanceof Element) {
        tokens.push("ELEMENT:" + node.localName + ":" + JSON.stringify(plannedElementKey(node, options)));
      } else if (node.nodeType === Node.TEXT_NODE) {
        tokens.push("TEXT");
      } else if (node.nodeType === Node.COMMENT_NODE) {
        tokens.push("COMMENT");
      } else {
        tokens.push("NODE:" + node.nodeType + ":" + node.nodeName);
      }
      node = node.nextSibling;
    }
    return JSON.stringify(tokens);
  };

  var elementsInsidePair = function (pair, selector) {
    var result = [];
    nodesInsidePair(pair).forEach(function (node) {
      if (!(node instanceof Element)) return;
      if (node.matches(selector)) result.push(node);
      node.querySelectorAll(selector).forEach(function (element) { result.push(element); });
    });
    return result;
  };

  var expandPlannedHolders = function (pair) {
    var selector = "template[" + PLANNED_RANGE_HOLDER_ATTR + "]:not([" + PLANNED_RANGE_PORTABLE_ATTR + "])";
    while (true) {
      var holder = elementsInsidePair(pair, selector)[0];
      if (!holder) return;
      holder.before(holder.content);
      holder.remove();
    }
  };

  var removePlannedSentinels = function (pair) {
    elementsInsidePair(pair, "template[" + PLANNED_RANGE_SENTINEL_ATTR + "]").forEach(function (sentinel) {
      sentinel.remove();
    });
  };

  var plannedSentinelWindows = function (root, boundary) {
    var selector = "template[" + PLANNED_RANGE_SENTINEL_ATTR + "]";
    var sentinels = boundary
      ? elementsInsidePair(boundary, selector)
      : Array.prototype.slice.call(root.querySelectorAll(selector));
    return sentinels.filter(function (sentinel) {
      return sentinel.getAttribute(PLANNED_RANGE_SENTINEL_ATTR) === "start";
    }).map(function (start) {
      var startSlot = start.getAttribute(PLANNED_RANGE_SLOT_ATTR);
      var endSlot = startSlot && startSlot.replace(/:start$/, ":end");
      var end = sentinels.find(function (candidate) {
        return (
          candidate.parentNode === start.parentNode &&
          candidate.getAttribute(PLANNED_RANGE_SENTINEL_ATTR) === "end" &&
          candidate.getAttribute(PLANNED_RANGE_SLOT_ATTR) === endSlot &&
          nodePrecedes(start, candidate)
        );
      });
      return end ? { start: start, end: end } : null;
    }).filter(Boolean);
  };

  var pairInsidePlannedWindows = function (pair, windows) {
    return windows.some(function (window) { return pairContainsPair(window, pair); });
  };

  var elementInsidePlannedWindows = function (element, windows) {
    return windows.some(function (window) { return physicalRangeContainsNode(window, element); });
  };

  var skipPlannedSentinelWindow = function (from, to, skipUntil) {
    if (
      !(from instanceof Element) ||
      !(to instanceof Element) ||
      from.getAttribute(PLANNED_RANGE_SENTINEL_ATTR) !== "start" ||
      to.getAttribute(PLANNED_RANGE_SENTINEL_ATTR) !== "start" ||
      from.getAttribute(PLANNED_RANGE_SLOT_ATTR) !== to.getAttribute(PLANNED_RANGE_SLOT_ATTR)
    ) return false;
    var endSlot = from.getAttribute(PLANNED_RANGE_SLOT_ATTR).replace(/:start$/, ":end");
    skipUntil(function (node) {
      return node instanceof Element &&
        node.getAttribute(PLANNED_RANGE_SENTINEL_ATTR) === "end" &&
        node.getAttribute(PLANNED_RANGE_SLOT_ATTR) === endSlot;
    });
    return true;
  };

  var freshContentsForPair = function (pair, oldPair) {
    var parent = oldPair.start.parentElement;
    var container = parent ? parent.cloneNode(false) : document.createElement("div");
    if (container.removeAttribute) container.removeAttribute("id");
    nodesInsidePair(pair).forEach(function (node) { container.append(node.cloneNode(true)); });
    return container;
  };

  var rangeRecordKind = function (pair) {
    return typeof pair.recordKey === "string" ? pair.recordKey.split(":")[1] : null;
  };

  var directSlotRegionPairs = function (pairs) {
    var componentPairs = pairs.filter(function (pair) { return rangeRecordKind(pair) === "i"; });
    return pairs.filter(function (pair) {
      return (
        rangeRecordKind(pair) === "r" &&
        !componentPairs.some(function (componentPair) { return pairContainsPair(componentPair, pair); })
      );
    });
  };

  var slotRegionIdentity = function (pair, boundary, options, peerPairs) {
    var state = ownershipStates.get(pair.revision);
    var region = state && state.slotRegions.get(pair.recordKey);
    if (!state || !region) return null;
    var receiver = state.renderLinks.get(region.receiverRenderId);
    var resultOwner = state.renderLinks.get(region.resultOwnerRenderId);
    var fill = state.registry.fills.get(qualifiedGraphId(region.graphId, "f", region.fillId));
    return JSON.stringify([
      plannedParentPath(pair, boundary, options),
      plannedWindowSignature(
        pair,
        peerPairs,
        function (candidate) { return rangeRecordKind(candidate) || "unknown"; },
        boundary,
        options
      ),
      receiver ? receiver.record.classId : null,
      fill ? fill.slot : null,
      fill ? fill.kind : null,
      fill ? fill.policy : null,
      fill ? fill.ownerClassId : null,
      fill ? fill.receiverClassId : null,
      resultOwner ? resultOwner.record.classId : null,
    ]);
  };

  var morphOrdinaryRangeContents = function (oldPair, fresh, options) {
    var oldParent = oldPair.start.parentNode;
    if (!oldParent || oldParent !== oldPair.end.parentNode) {
      throw new TypeError("[Citry] correlated slot-region morph needs same-parent operational caps.");
    }
    if (oldPair.start._citryOperationalDocumentStart) {
      var boundaryWhitespace = function (node) {
        return node && node.nodeType === Node.TEXT_NODE && !node.nodeValue.trim();
      };
      var oldFirst = oldPair.start.nextSibling;
      var freshFirst = fresh.firstChild;
      if (boundaryWhitespace(freshFirst) && !boundaryWhitespace(oldFirst)) {
        while (boundaryWhitespace(freshFirst)) {
          oldParent.insertBefore(freshFirst.cloneNode(true), oldFirst);
          freshFirst = freshFirst.nextSibling;
        }
      }
      while (boundaryWhitespace(oldFirst) && !boundaryWhitespace(fresh.firstChild)) {
        var nextOld = oldFirst.nextSibling;
        oldFirst.remove();
        oldFirst = nextOld;
      }
      var oldLast = oldPair.end.previousSibling;
      var freshLast = fresh.lastChild;
      var freshTrailing = [];
      while (freshFirst && boundaryWhitespace(freshLast)) {
        freshTrailing.unshift(freshLast);
        freshLast = freshLast.previousSibling;
      }
      if (freshTrailing.length && !boundaryWhitespace(oldLast)) {
        freshTrailing.forEach(function (node) { oldParent.insertBefore(node.cloneNode(true), oldPair.end); });
      }
      while (boundaryWhitespace(oldLast) && !boundaryWhitespace(fresh.lastChild)) {
        var previousOld = oldLast.previousSibling;
        oldLast.remove();
        oldLast = previousOld;
      }
    }
    var inheritedOldWindows = plannedSentinelWindows(oldParent, oldPair);
    var inheritedFreshWindows = plannedSentinelWindows(fresh, null);
    rangePairsUnder(oldParent, oldPair)
      .filter(function (pair) { return !pairInsidePlannedWindows(pair, inheritedOldWindows); })
      .sort(function (left, right) {
        return pairContainsPair(left, right) ? 1 : pairContainsPair(right, left) ? -1 : 0;
      })
      .forEach(function (pair) {
        plannedRangeSlotCounter += 1;
        collapsePlannedRange(pair, "old:" + plannedRangeSlotCounter.toString(36), "old-unmatched", null);
      });
    rangePairsUnder(fresh, null)
      .filter(function (pair) { return !pairInsidePlannedWindows(pair, inheritedFreshWindows); })
      .sort(function (left, right) {
        return pairContainsPair(left, right) ? 1 : pairContainsPair(right, left) ? -1 : 0;
      })
      .forEach(function (pair) {
        plannedRangeSlotCounter += 1;
        collapsePlannedRange(pair, "new:" + plannedRangeSlotCounter.toString(36), "new-unmatched", null);
      });
    alpineOwner.morphBetween(oldPair.start, oldPair.end, fresh, {
      key: function (element) {
        if (
          element.hasAttribute(PLANNED_RANGE_HOLDER_ATTR) ||
          element.hasAttribute(PLANNED_RANGE_SENTINEL_ATTR)
        ) {
          return element.getAttribute(PLANNED_RANGE_SLOT_ATTR);
        }
        return typeof options.key === "function" ? options.key(element) : element.getAttribute("data-citry-key");
      },
      keyMapFilter: function (element) {
        return !elementInsidePlannedWindows(element, inheritedOldWindows);
      },
      updating: function (from, to, childrenOnly, skip, skipChildren, skipUntil) {
        if (skipPlannedSentinelWindow(from, to, skipUntil)) return;
        if (typeof options.updating === "function") {
          options.updating(from, to, childrenOnly, skip, skipChildren, skipUntil);
        }
      },
    });
    expandPlannedHolders(oldPair);
    removePlannedSentinels(oldPair);
  };

  var physicalForPlannedMatch = function (match, outer) {
    var state = ownershipStates.get(match.fromRevision);
    if (!state) return null;
    return physicalRangesForKey(state, match.fromKey).find(function (physical) {
      var operationallyLive =
        physical.start.parentNode === outer.start.parentNode &&
        physical.end.parentNode === outer.end.parentNode &&
        physical.start.data === physical.startMarker &&
        physical.end.data === physical.endMarker;
      return (
        physical.start !== outer.start &&
        (physicalRangeIsLive(state, physical) || operationallyLive) &&
        physicalRangeContainsNode(outer, physical.start) &&
        physicalRangeContainsNode(outer, physical.end)
      );
    }) || null;
  };

  var morphPlannedRangeContents = function (oldPair, fresh, currentMatch, plan, options) {
    var physicalMatches = plan.matches.concat(plan.retainedMatches || []);
    var directMatches = physicalMatches.filter(function (match) {
      return (
        match.preserveLogical &&
        match.parentFromRenderId === currentMatch.fromRenderId &&
        match.parentToRenderId === currentMatch.toRenderId
      );
    });
    var oldParent = oldPair.start.parentNode;
    if (!oldParent || oldParent !== oldPair.end.parentNode) {
      throw new TypeError("[Citry] planned range morph needs same-parent operational caps.");
    }
    var oldPairs = rangePairsUnder(oldParent, oldPair);
    var freshPairs = rangePairsUnder(fresh, null);
    var retainedIncomingRenderIds = new Set((plan.retainedCorrespondences || []).map(function (match) {
      return match.toRenderId;
    }));
    var retainedIncomingSlotKeys = new Set((plan.retainedSlotMatches || []).map(function (match) {
      return match.toKey;
    }));
    var excludedFreshPairs = freshPairs.filter(function (pair) {
      var instance = plan.state.registry.componentInstances.get(pair.recordKey);
      if (instance) {
        return plan.excludedIncomingRenderIds.has(instance.renderId) && !retainedIncomingRenderIds.has(instance.renderId);
      }
      return plan.excludedIncomingPhysicalKeys.has(pair.recordKey) && !retainedIncomingSlotKeys.has(pair.recordKey);
    }).filter(function (pair, _index, excluded) {
      return !excluded.some(function (outer) { return pairContainsPair(outer, pair); });
    });
    excludedFreshPairs.forEach(function (pair) {
      for (var node = pair.start; node;) {
        var next = node.nextSibling;
        node.remove();
        if (node === pair.end) break;
        node = next;
      }
    });
    if (excludedFreshPairs.length) freshPairs = rangePairsUnder(fresh, null);
    var inheritedOldWindows = plannedSentinelWindows(oldParent, oldPair);
    var inheritedFreshWindows = plannedSentinelWindows(fresh, null);
    var portable = [];
    var stationary = [];
    var correlatedRegions = [];

    var oldChildren = (currentMatch.oldDirectChildren || []).map(function (record) {
      var state = ownershipStates.get(record.revision);
      var pair = state && physicalRangesForKey(state, record.key).find(function (physical) {
        return (
          physicalRangeIsLive(state, physical) &&
          physicalRangeContainsNode(oldPair, physical.start) &&
          physicalRangeContainsNode(oldPair, physical.end)
        );
      });
      return pair
        ? { record: record, pair: { start: pair.start, end: pair.end, revision: record.revision, recordKey: pair.key } }
        : null;
    }).filter(Boolean);
    var newChildren = (currentMatch.newDirectChildren || []).map(function (record) {
      var pair = pairForRecord(freshPairs, record.revision, record.key);
      return pair ? { record: record, pair: pair } : null;
    }).filter(Boolean);
    var byPosition = function (left, right) {
      return nodePrecedes(left.pair.start, right.pair.start)
        ? -1
        : nodePrecedes(right.pair.start, left.pair.start)
          ? 1
          : 0;
    };
    oldChildren.sort(byPosition);
    newChildren.sort(byPosition);
    var matchByOldRange = new Map();
    physicalMatches.forEach(function (match) {
      if (!match.preserveLogical) return;
      matchByOldRange.set(match.fromRevision + "\n" + match.fromKey, match.toRevision + "\n" + match.toKey);
    });
    var normalizeOldRange = function (pair) {
      var identity = pair.revision + "\n" + pair.recordKey;
      return matchByOldRange.get(identity) || "old-only:" + identity;
    };
    var normalizeNewRange = function (pair) {
      return pair.revision + "\n" + pair.recordKey;
    };
    var insideIgnoredOldBarrier = function (pair) {
      return plan.ordinaryPairs.some(function (ordinary) {
        var element = ordinary.from;
        return element instanceof Element && element.getAttribute("data-citry-morph") === "ignore" &&
          element.contains(pair.start) && element.contains(pair.end);
      });
    };
    var intermediateRanges = function (target, pairs) {
      return pairs.filter(function (pair) { return pairContainsPair(pair, target); }).sort(function (left, right) {
        if (pairContainsPair(left, right)) return -1;
        if (pairContainsPair(right, left)) return 1;
        return 0;
      });
    };
    var normalizedIntermediateRange = function (pair, side) {
      var kind = rangeRecordKind(pair);
      if (kind === "i") {
        var identity = pair.revision + "\n" + pair.recordKey;
        var mappedIdentity = side === "old" ? matchByOldRange.get(identity) : identity;
        return mappedIdentity ? "i:" + mappedIdentity : null;
      }
      if (kind === "r") {
        var boundary = side === "old" ? oldPair : fresh;
        var peers = side === "old" ? oldPairs : freshPairs;
        var regionIdentity = slotRegionIdentity(pair, boundary, options, peers);
        return regionIdentity === null ? null : "r:" + regionIdentity;
      }
      return null;
    };
    var hasEquivalentIntermediateRanges = function (oldDirectPair, newDirectPair) {
      var oldIntermediate = intermediateRanges(oldDirectPair, oldPairs);
      var newIntermediate = intermediateRanges(newDirectPair, freshPairs);
      return oldIntermediate.length === newIntermediate.length && oldIntermediate.every(function (pair, index) {
        var oldIdentity = normalizedIntermediateRange(pair, "old");
        return oldIdentity !== null && oldIdentity === normalizedIntermediateRange(newIntermediate[index], "new");
      });
    };

    // A stationary range stays connected behind paired sentinels. A real move
    // uses portable holders so Alpine can land the new wrapper structure before
    // Citry transplants the old physical range into its new destination.
    var plannedEntries = directMatches.map(function (match) {
      var oldPhysical = physicalForPlannedMatch(match, oldPair);
      var newPair = pairForRecord(freshPairs, match.toRevision, match.toKey);
      if (!oldPhysical || !newPair) {
        throw new TypeError(
          "[Citry] planned keyed component range is absent from one physical parent range" +
            " (old=" + Boolean(oldPhysical) + ", new=" + Boolean(newPair) +
            ", fresh=" + freshPairs.map(function (pair) { return pair.recordKey; }).join(",") + ")."
        );
      }
      plannedRangeSlotCounter += 1;
      var token = "p" + plannedRangeSlotCounter.toString(36);
      var oldChildIndex = oldChildren.findIndex(function (child) {
        return child.record.revision === match.fromRevision && child.record.key === match.fromKey;
      });
      var newChildIndex = newChildren.findIndex(function (child) {
        return child.record.revision === match.toRevision && child.record.key === match.toKey;
      });
      var oldDirectPair = oldChildIndex < 0 ? null : oldChildren[oldChildIndex].pair;
      var newDirectPair = newChildIndex < 0 ? null : newChildren[newChildIndex].pair;
      var oldPath = oldDirectPair && plannedParentPath(oldDirectPair, oldPair, options);
      var newPath = newDirectPair && plannedParentPath(newDirectPair, fresh, options);
      var sameWindow = oldPath !== null && oldPath === newPath;
      var staysConnected = Boolean(
        oldDirectPair &&
        newDirectPair &&
        hasEquivalentIntermediateRanges(oldDirectPair, newDirectPair) &&
        oldChildIndex === newChildIndex &&
        sameWindow &&
        plannedWindowSignature(
          oldDirectPair,
          oldChildren.map(function (child) { return child.pair; }),
          normalizeOldRange,
          oldPair,
          options
        ) === plannedWindowSignature(
          newDirectPair,
          newChildren.map(function (child) { return child.pair; }),
          normalizeNewRange,
          fresh,
          options
        )
      );
      return {
        match: match,
        token: token,
        oldPhysical: oldPhysical,
        oldPair: oldDirectPair,
        newPair: newDirectPair,
        staysConnected: staysConnected,
      };
    }).filter(function (entry) {
      return !(entry.match.retained && insideIgnoredOldBarrier(entry.oldPhysical));
    });

    // Discover every boundary before moving any of them into template
    // fragments. Enclosing portable holders are created first, so a nested
    // holder travels with its parent and the parent destination becomes
    // reachable before the nested range is transplanted.
    plannedEntries.sort(function (left, right) {
      if (
        (left.oldPair && right.oldPair && pairContainsPair(left.oldPair, right.oldPair)) ||
        (left.newPair && right.newPair && pairContainsPair(left.newPair, right.newPair))
      ) return -1;
      if (
        (right.oldPair && left.oldPair && pairContainsPair(right.oldPair, left.oldPair)) ||
        (right.newPair && left.newPair && pairContainsPair(right.newPair, left.newPair))
      ) return 1;
      return 0;
    });
    plannedEntries.forEach(function (entry) {
      if (!entry.staysConnected) return;
      entry.staysConnected = !plannedEntries.some(function (candidate) {
        return candidate !== entry && !candidate.staysConnected && (
          (candidate.oldPair && entry.oldPair && pairContainsPair(candidate.oldPair, entry.oldPair)) ||
          (candidate.newPair && entry.newPair && pairContainsPair(candidate.newPair, entry.newPair))
        );
      });
    });
    plannedEntries.forEach(function (entry) {
      if (entry.staysConnected) {
        stationary.push({
          match: entry.match,
          token: entry.token,
          oldPair: entry.oldPair,
          newPair: entry.newPair,
        });
        return;
      }
      var oldHolder = collapsePlannedRange(
        { start: entry.oldPhysical.start, end: entry.oldPhysical.end },
        entry.token + ":old",
        "portable-old",
        entry.match
      );
      var newHolder = collapsePlannedRange(
        entry.newPair,
        entry.token + ":new",
        "portable-new",
        entry.match
      );
      portable.push({ match: entry.match, oldHolder: oldHolder, newHolder: newHolder });
    });

    // A logically direct sibling may be physically nested inside a stationary
    // range (for example through supplied-slot placement). Install every real
    // portable move first, then patch stationary ranges from the inside out.
    // Each completed inner pass gains paired sentinels, so the enclosing pass
    // can keep it connected and opaque while matching the wrapper structure.
    stationary.sort(function (left, right) {
      if (pairContainsPair(left.oldPair, right.oldPair) || pairContainsPair(left.newPair, right.newPair)) return 1;
      if (pairContainsPair(right.oldPair, left.oldPair) || pairContainsPair(right.newPair, left.newPair)) return -1;
      return 0;
    });
    stationary.forEach(function (entry) {
      if (!entry.match.retained) {
        morphPlannedRangeContents(
          entry.oldPair,
          freshContentsForPair(entry.newPair, entry.oldPair),
          entry.match,
          plan,
          options
        );
      }
      entry.oldStartSentinel = insertPlannedSentinel(entry.oldPair, entry.token + ":start", "start", true);
      entry.oldEndSentinel = insertPlannedSentinel(entry.oldPair, entry.token + ":end", "end", false);
      entry.newStartSentinel = insertPlannedSentinel(entry.newPair, entry.token + ":start", "start", true);
      entry.newEndSentinel = insertPlannedSentinel(entry.newPair, entry.token + ":end", "end", false);
    });

    // Recursive stationary-component morphs can replace slot-region caps that
    // were present in the pre-morph scan. Re-scan both sides before correlating
    // regions so identity planning never reads a detached, stale cap pair.
    oldPairs = rangePairsUnder(oldParent, oldPair);
    freshPairs = rangePairsUnder(fresh, null);
    var oldRegionsByIdentity = new Map();
    directSlotRegionPairs(oldPairs).forEach(function (pair) {
      var identity = slotRegionIdentity(pair, oldPair, options, oldPairs);
      if (identity === null) return;
      var queue = oldRegionsByIdentity.get(identity) || [];
      queue.push(pair);
      oldRegionsByIdentity.set(identity, queue);
    });
    directSlotRegionPairs(freshPairs).forEach(function (newPair) {
      var identity = slotRegionIdentity(newPair, fresh, options, freshPairs);
      var queue = identity === null ? null : oldRegionsByIdentity.get(identity);
      if (!queue || !queue.length) return;
      var oldRegionPair = queue.shift();
      var oldRegionIdentity = oldRegionPair.revision + "\n" + oldRegionPair.recordKey;
      if (plan.retainedOldPhysicalRecords.has(oldRegionIdentity) && insideIgnoredOldBarrier(oldRegionPair)) return;
      var oldState = ownershipStates.get(oldRegionPair.revision);
      var oldPhysical = oldState && physicalRangesForKey(oldState, oldRegionPair.recordKey).find(function (physical) {
        return physical.start === oldRegionPair.start && physical.end === oldRegionPair.end;
      });
      if (!oldPhysical) return;
      plannedRangeSlotCounter += 1;
      correlatedRegions.push({
        oldPair: oldRegionPair,
        newPair: newPair,
        oldPhysical: oldPhysical,
        retained: plan.retainedOldPhysicalRecords.has(oldRegionIdentity),
        token: "r" + plannedRangeSlotCounter.toString(36),
      });
    });
    correlatedRegions.sort(function (left, right) {
      if (pairContainsPair(left.oldPair, right.oldPair) || pairContainsPair(left.newPair, right.newPair)) return 1;
      if (pairContainsPair(right.oldPair, left.oldPair) || pairContainsPair(right.newPair, left.newPair)) return -1;
      return 0;
    });
    correlatedRegions.forEach(function (entry) {
      if (!entry.retained) {
        morphOrdinaryRangeContents(
          entry.oldPair,
          freshContentsForPair(entry.newPair, entry.oldPair),
          options
        );
        var transfers = plan.state.adoption.transfers.get(entry.newPair.recordKey) || [];
        if (transfers.indexOf(entry.oldPhysical) === -1) transfers.push(entry.oldPhysical);
        plan.state.adoption.transfers.set(entry.newPair.recordKey, transfers);
      }
      insertPlannedSentinel(entry.oldPair, entry.token + ":start", "start", true);
      insertPlannedSentinel(entry.oldPair, entry.token + ":end", "end", false);
      insertPlannedSentinel(entry.newPair, entry.token + ":start", "start", true);
      insertPlannedSentinel(entry.newPair, entry.token + ":end", "end", false);
      stationary.push(entry);
    });

    var insideStationary = function (pair, side) {
      var inherited = side === "old" ? inheritedOldWindows : inheritedFreshWindows;
      return pairInsidePlannedWindows(pair, inherited) || stationary.some(function (entry) {
        var boundary = side === "old" ? entry.oldPair : entry.newPair;
        return pair.start === boundary.start || pairContainsPair(boundary, pair);
      });
    };

    // Every other ownership range is an unmatched virtual node for this
    // level. Keep its comments atomic while Alpine patches ordinary DOM.
    rangePairsUnder(oldParent, oldPair)
      .filter(function (pair) { return !insideStationary(pair, "old"); })
      .sort(function (left, right) {
        return pairContainsPair(left, right) ? 1 : pairContainsPair(right, left) ? -1 : 0;
      })
      .forEach(function (pair) {
        plannedRangeSlotCounter += 1;
        collapsePlannedRange(pair, "old:" + plannedRangeSlotCounter.toString(36), "old-unmatched", null);
      });
    rangePairsUnder(fresh, null)
      .filter(function (pair) { return !insideStationary(pair, "new"); })
      .sort(function (left, right) {
        return pairContainsPair(left, right) ? 1 : pairContainsPair(right, left) ? -1 : 0;
      })
      .forEach(function (pair) {
        plannedRangeSlotCounter += 1;
        collapsePlannedRange(pair, "new:" + plannedRangeSlotCounter.toString(36), "new-unmatched", null);
      });

    alpineOwner.morphBetween(oldPair.start, oldPair.end, fresh, {
      key: function (element) {
        if (
          element.hasAttribute(PLANNED_RANGE_HOLDER_ATTR) ||
          element.hasAttribute(PLANNED_RANGE_SENTINEL_ATTR)
        ) {
          return element.getAttribute(PLANNED_RANGE_SLOT_ATTR);
        }
        return typeof options.key === "function" ? options.key(element) : element.getAttribute("data-citry-key");
      },
      // Alpine builds one keyed map from all flat element siblings before its
      // updating hook can call skipUntil. Exclude roots inside stationary cap
      // windows from that map so they cannot escape across neighboring ranges;
      // the paired sentinels still drive traversal while the live range stays
      // connected and untouched at this level.
      keyMapFilter: function (element) {
        return !elementInsidePlannedWindows(element, inheritedOldWindows) && !stationary.some(function (entry) {
          return physicalRangeContainsNode(entry.oldPair, element);
        });
      },
      updating: function (from, to, childrenOnly, skip, skipChildren, skipUntil) {
        if (skipPlannedSentinelWindow(from, to, skipUntil)) return;
        if (typeof options.updating === "function") {
          options.updating(from, to, childrenOnly, skip, skipChildren, skipUntil);
        }
      },
    });

    expandPlannedHolders(oldPair);
    portable.forEach(function (entry) {
      var selector =
        "template[" + PLANNED_RANGE_PORTABLE_ATTR + '="' + CSS.escape(entry.newHolder.getAttribute(
          PLANNED_RANGE_PORTABLE_ATTR
        )) + '"]';
      var destination = elementsInsidePair(oldPair, selector).find(function (candidate) {
        return candidate.getAttribute(PLANNED_RANGE_HOLDER_ATTR) === "portable-new";
      });
      if (!destination) {
        throw new TypeError("[Citry] keyed component range destination vanished during morph.");
      }
      var oldNested = pairForRecord(
        rangePairsUnder(entry.oldHolder.content, null),
        entry.match.fromRevision,
        entry.match.fromKey
      );
      var newNested = pairForRecord(
        rangePairsUnder(destination.content, null),
        entry.match.toRevision,
        entry.match.toKey
      );
      if (!oldNested || !newNested) {
        throw new TypeError("[Citry] keyed component holder lost one of its cap pairs.");
      }
      if (!entry.match.retained) {
        morphPlannedRangeContents(
          oldNested,
          freshContentsForPair(newNested, oldNested),
          entry.match,
          plan,
          options
        );
      }
      destination.replaceWith(entry.oldHolder);
      entry.oldHolder.before(entry.oldHolder.content);
      entry.oldHolder.remove();
    });
    removePlannedSentinels(oldPair);
  };

  var morphPlannedOwnershipRange = function (physical, html, options) {
    var plan = options.adoptionPlan;
    var rootMatch = plan && plan.matches.find(function (match) {
      return match.fromKey === physical.key && match.preserveLogical;
    });
    if (!rootMatch) return false;
    var morphStart = physical.start;
    var cursor = null;
    var operationalDocumentStarts = [];
    if (physical.topology === "document-body") {
      cursor = document.createComment("citry:range-morph-cursor");
      document.body.insertBefore(cursor, document.body.firstChild);
      morphStart = cursor;
      // Nested ranges can share the parser's split Document/body topology:
      // each opening cap precedes <html>, while its closing cap lives in
      // body. The planner operates on one sibling window, so temporarily
      // bring those nested openings behind the body cursor. Correlated caps
      // that remain at the document root are restored after the patch;
      // ranges moved into an authored wrapper keep their new same-parent
      // topology and adoption reclassifies them from the committed DOM.
      ownershipStates.forEach(function (candidateState) {
        candidateState.physicalPlacements.forEach(function (placements) {
          placements.forEach(function (candidate) {
            if (
              candidate !== physical &&
              candidate.topology === "document-body" &&
              physicalRangeIsLive(candidateState, candidate) &&
              physicalRangeContainsNode(physical, candidate.start) &&
              physicalRangeContainsNode(physical, candidate.end) &&
              operationalDocumentStarts.every(function (entry) { return entry.start !== candidate.start; })
            ) {
              operationalDocumentStarts.push({ start: candidate.start, end: candidate.end });
            }
          });
        });
      });
      operationalDocumentStarts.sort(function (left, right) {
        return nodePrecedes(left.start, right.start) ? -1 : nodePrecedes(right.start, left.start) ? 1 : 0;
      });
      var operationalTail = cursor;
      operationalDocumentStarts.forEach(function (entry) {
        entry.start._citryOperationalDocumentStart = true;
        operationalTail.after(entry.start);
        operationalTail = entry.start;
      });
    }
    try {
      var container = contextualRangeContainer(morphStart, physical.end, html);
      morphPlannedRangeContents(
        { start: morphStart, end: physical.end },
        container,
        rootMatch,
        plan,
        options
      );
    } finally {
      operationalDocumentStarts.forEach(function (entry) {
        if (
          entry.start.isConnected &&
          entry.end.isConnected &&
          entry.start.parentNode === document.body &&
          entry.end.parentNode === document.body
        ) {
          document.insertBefore(entry.start, document.documentElement);
        }
        delete entry.start._citryOperationalDocumentStart;
      });
      if (cursor && cursor.isConnected) cursor.remove();
    }
    return true;
  };

  var morphOwnershipRange = function (revision, physicalKey, html, options) {
    if (typeof revision !== "string" || typeof physicalKey !== "string" || typeof html !== "string") {
      throw new TypeError("[Citry] range morph needs a revision, physical range key, and HTML string.");
    }
    options = options || {};
    var state = ownershipStates.get(revision);
    var physical = options.physical || (state && state.registry.physicalRegions.get(physicalKey));
    if (!state || !physical || !physicalRangeIsLive(state, physical)) {
      throw new TypeError("[Citry] range morph target is unknown, retired, or corrupt.");
    }
    if (!alpineOwner || typeof alpineOwner.morphBetween !== "function") {
      throw pointedAlpineError("range morph was requested before the pinned morphBetween adapter installed.");
    }
    if (options.adoptionPlan) {
      rangeMorphDepth += 1;
      try {
        if (morphPlannedOwnershipRange(physical, html, options)) return physical;
      } finally {
        rangeMorphDepth -= 1;
        if (rangeMorphDepth === 0 && ownershipAdoptionDepth === 0) reconcileComponentLifecycles();
      }
    }
    var livePlaceholders = [];
    var nestedRanges = nestedPhysicalRanges(state, physical);
    var targetCanMorph = physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode instanceof Element && physical.start.parentNode === physical.end.parentNode;
    if (!targetCanMorph) {
      throw new TypeError("[Citry] range morph target has unsupported parent topology.");
    }
    nestedRanges.forEach(function (nested) {
      assertRangePairCanCollapse({
        key: nested.physical.startMarker.slice(0, -2),
        start: nested.physical.start,
        end: nested.physical.end,
        topology: nested.physical.topology,
      });
    });
    var morphCursor = null;
    rangeMorphDepth += 1;
    try {
      nestedRanges.forEach(function (nested) {
        livePlaceholders.push(collapseRangePair(
          {
            key: nested.physical.startMarker.slice(0, -2),
            start: nested.physical.start,
            end: nested.physical.end,
            topology: nested.physical.topology,
          },
          physicalStableAnchor(nested.state, nested.physical)
        ));
      });
      var morphStart = physical.start;
      if (physical.topology === "document-body") {
        morphCursor = document.createComment("citry:range-morph-cursor");
        document.body.insertBefore(morphCursor, document.body.firstChild);
        morphStart = morphCursor;
      }
      var container = contextualRangeContainer(morphStart, physical.end, html);
      collapseIncomingRanges(container, options.correspondence || null);
      alpineOwner.morphBetween(morphStart, physical.end, container, {
        key: function (element) {
          if (element.hasAttribute(RANGE_ISLAND_ATTR)) return element.getAttribute("key");
          if (typeof options.key === "function") return options.key(element);
          return element.getAttribute("data-citry-key") || element.getAttribute("key") || element.id;
        },
      });
    } finally {
      try {
        expandRangeIslands(physical);
        livePlaceholders.forEach(function (placeholder) {
          // A removed nested island stays detached inside its inert holder;
          // normal cap liveness retirement owns its cleanup.
          if (placeholder.isConnected) placeholder.remove();
        });
        if (morphCursor && morphCursor.isConnected) morphCursor.remove();
      } finally {
        rangeMorphDepth -= 1;
        if (rangeMorphDepth === 0 && ownershipAdoptionDepth === 0) reconcileComponentLifecycles();
      }
    }
    return physical;
  };

  var replaceOwnershipRange = function (revision, physicalKey, html, options) {
    var state = ownershipStates.get(revision);
    var physical = options && options.physical;
    if (!state || !physical || physical.key !== physicalKey || !physicalRangeIsLive(state, physical)) {
      throw new TypeError("[Citry] range replacement target is unknown, retired, or corrupt.");
    }
    var start = physical.start;
    var cursor = null;
    if (physical.topology === "document-body") {
      cursor = document.createComment("citry:range-replace-cursor");
      document.body.insertBefore(cursor, document.body.firstChild);
      start = cursor;
    }
    try {
      var container = contextualRangeContainer(start, physical.end, html);
      for (var node = start.nextSibling; node && node !== physical.end;) {
        var next = node.nextSibling;
        node.remove();
        node = next;
      }
      while (container.firstChild) physical.end.before(container.firstChild);
    } finally {
      if (cursor && cursor.isConnected) cursor.remove();
    }
    return physical;
  };

  var lifecyclePhysicalRange = function (lifecycle) {
    var route = routeForLifecycle(lifecycle);
    var state = route && ownershipStates.get(route.revision);
    var physicals = state && route ? physicalRangesForKey(state, route.instance.key) : [];
    return {
      route: route,
      state: state,
      physical: physicals.length ? physicals[0] : null,
      physicals: physicals,
    };
  };

  // A component boundary is one logical listener surface even when its
  // rendered component has several element roots. Modifier state and global
  // listeners therefore belong to this group, not to individual elements.
  var ROOT_GROUP_ENTER_LEAVE = new Set(["mouseenter", "mouseleave", "pointerenter", "pointerleave"]);

  var rootGroupUnique = function (roots) {
    var seen = new Set();
    return roots.filter(function (root) {
      if (!(root instanceof Element)) throw new TypeError("[Citry] RootGroup members must be Elements.");
      if (seen.has(root)) return false;
      seen.add(root);
      return true;
    });
  };

  var rootGroupKebab = function (value) {
    if (value === " " || value === "_") return value;
    return value.replace(/([a-z])([A-Z])/g, "$1-$2").replace(/[_\s]/, "-").toLowerCase();
  };

  var rootGroupKeyAliases = function (key) {
    if (!key) return [];
    key = rootGroupKebab(key);
    var aliases = {
      ctrl: "control", slash: "/", space: " ", spacebar: " ", cmd: "meta", esc: "escape",
      up: "arrow-up", down: "arrow-down", left: "arrow-left", right: "arrow-right",
      period: ".", comma: ",", equal: "=", minus: "-", underscore: "_",
    };
    aliases[key] = key;
    return Object.keys(aliases).filter(function (name) { return aliases[name] === key; });
  };

  var rootGroupIsKeyEvent = function (event) { return event === "keydown" || event === "keyup"; };
  var rootGroupIsClickEvent = function (event) {
    return ["contextmenu", "click", "mouse"].some(function (part) { return event.indexOf(part) !== -1; });
  };
  var rootGroupIsNumeric = function (value) { return !Array.isArray(value) && !Number.isNaN(Number(value)); };
  var rootGroupTiming = function (modifiers, name) {
    var next = modifiers[modifiers.indexOf(name) + 1] || "invalid-wait";
    return rootGroupIsNumeric(next.split("ms")[0]) ? Number(next.split("ms")[0]) : 250;
  };

  var rootGroupMissesKeyFilter = function (event, modifiers) {
    var ignored = [
      "window", "document", "prevent", "stop", "once", "capture", "self", "away", "outside",
      "passive", "preserve-scroll", "blur", "change", "lazy",
    ];
    var keys = modifiers.filter(function (item) { return ignored.indexOf(item) === -1; });
    ["debounce", "throttle"].forEach(function (timing) {
      if (keys.indexOf(timing) === -1) return;
      var index = keys.indexOf(timing);
      var next = keys[index + 1] || "invalid-wait";
      keys.splice(index, rootGroupIsNumeric(next.split("ms")[0]) ? 2 : 1);
    });
    if (!keys.length) return false;
    if (keys.length === 1 && rootGroupKeyAliases(event.key).indexOf(keys[0]) !== -1) return false;
    var system = ["ctrl", "shift", "alt", "meta", "cmd", "super"];
    var selected = system.filter(function (name) { return keys.indexOf(name) !== -1; });
    keys = keys.filter(function (name) { return selected.indexOf(name) === -1; });
    if (selected.length) {
      var active = selected.filter(function (name) {
        var property = name === "cmd" || name === "super" ? "meta" : name;
        return event[property + "Key"];
      });
      if (active.length === selected.length) {
        if (rootGroupIsClickEvent(event.type)) return false;
        if (rootGroupKeyAliases(event.key).indexOf(keys[0]) !== -1) return false;
      }
    }
    return true;
  };

  var rootGroupPathContains = function (event, root) {
    var path = typeof event.composedPath === "function" ? event.composedPath() : [];
    if (path.indexOf(root) !== -1) return true;
    return path.some(function (candidate) {
      return candidate instanceof Node && root.contains(candidate);
    });
  };

  var RootGroup = function (els, isLogicalLive) {
    this.els = els;
    this.bindings = new Set();
    this.destroyed = false;
    this.isLogicalLive = isLogicalLive;
  };
  RootGroup.prototype.setRoots = function (next) {
    if (this.destroyed) return;
    var roots = rootGroupUnique(Array.from(next || []));
    replaceArrayContents(this.els, roots);
    this.bindings.forEach(function (binding) { binding.syncRoots(); });
  };
  RootGroup.prototype.hasLive = function (root) {
    return this.isLogicalLive() && this.els.indexOf(root) !== -1 && root.isConnected;
  };
  RootGroup.prototype.firstLive = function () {
    if (!this.isLogicalLive()) return null;
    return this.els.find(function (root) { return root.isConnected; }) || null;
  };
  RootGroup.prototype.containsNode = function (node) {
    return node instanceof Node && this.els.some(function (root) { return root === node || root.contains(node); });
  };
  RootGroup.prototype.containsEvent = function (event) {
    return this.els.some(function (root) { return rootGroupPathContains(event, root); });
  };
  RootGroup.prototype.hasVisibleRoot = function () {
    return this.els.some(function (root) {
      return root.isConnected && root._x_isShown !== false && (root.offsetWidth >= 1 || root.offsetHeight >= 1);
    });
  };
  RootGroup.prototype.on = function (event, modifiers, callback, citrySpec) {
    if (this.destroyed) throw new Error("[Citry] cannot bind a destroyed RootGroup.");
    var binding = new RootGroupBinding(this, event, modifiers, callback, citrySpec || null);
    this.bindings.add(binding);
    binding.syncRoots([], this.els);
    return function () { binding.cleanup(); };
  };
  RootGroup.prototype.poll = function (interval, callback) {
    if (!(interval > 0)) throw new TypeError("[Citry] RootGroup poll intervals must be positive.");
    var group = this;
    var active = true;
    var timer = window.setInterval(function () {
      if (!active || document.hidden || !group.isLogicalLive()) return;
      callback(group.firstLive());
    }, interval);
    var binding = {
      syncRoots: function () {},
      cleanup: function () {
        if (!active) return;
        active = false;
        window.clearInterval(timer);
        group.bindings.delete(binding);
      },
    };
    this.bindings.add(binding);
    return binding.cleanup;
  };
  RootGroup.prototype.destroy = function () {
    if (this.destroyed) return;
    this.destroyed = true;
    Array.from(this.bindings).forEach(function (binding) { binding.cleanup(); });
    replaceArrayContents(this.els, []);
  };

  var RootGroupBinding = function (group, event, modifiers, callback, citrySpec) {
    this.group = group;
    this.modifiers = Array.from(modifiers || []);
    this.event = this.modifiers.indexOf("dot") !== -1
      ? event.replace(/-/g, ".")
      : this.modifiers.indexOf("camel") !== -1
        ? event.toLowerCase().replace(/-(\w)/g, function (_match, ch) { return ch.toUpperCase(); })
        : event;
    this.callback = callback;
    this.citrySpec = citrySpec;
    this.targets = new Set();
    this.cancelTimers = [];
    this.listening = true;
    this.destroyed = false;
    this.options = {};
    if (this.modifiers.indexOf("capture") !== -1) this.options.capture = true;
    if (this.modifiers.indexOf("passive") !== -1) {
      this.options.passive = this.modifiers[this.modifiers.indexOf("passive") + 1] !== "false";
    }
    var binding = this;
    this.handleEvent = function (domEvent) {
      var direct = domEvent.currentTarget instanceof Element;
      var carrier = direct ? domEvent.currentTarget : binding.group.firstLive();
      binding.handler({ event: domEvent, carrier: carrier, direct: direct });
    };
    this.handler = citrySpec ? this.buildCitryHandler() : this.buildAlpineHandler();
  };
  RootGroupBinding.prototype.targetMode = function () {
    if (this.modifiers.indexOf("away") !== -1 || this.modifiers.indexOf("outside") !== -1) return "outside";
    if (this.modifiers.indexOf("document") !== -1) return "document";
    if (this.modifiers.indexOf("window") !== -1) return "window";
    return "direct";
  };
  RootGroupBinding.prototype.eventTargets = function () {
    var mode = this.targetMode();
    if (mode === "window") return this.group.els.length ? [window] : [];
    if (mode === "document" || mode === "outside") return this.group.els.length ? [document] : [];
    return this.group.els;
  };
  RootGroupBinding.prototype.syncRoots = function () {
    if (!this.listening || this.destroyed) return;
    var binding = this;
    var expected = new Set(this.eventTargets());
    Array.from(this.targets).forEach(function (target) {
      if (expected.has(target)) return;
      target.removeEventListener(binding.event, binding.handleEvent, binding.options);
      binding.targets.delete(target);
    });
    expected.forEach(function (target) {
      if (binding.targets.has(target)) return;
      target.addEventListener(binding.event, binding.handleEvent, binding.options);
      binding.targets.add(target);
    });
  };
  RootGroupBinding.prototype.stopListening = function () {
    if (!this.listening) return;
    var binding = this;
    this.listening = false;
    this.targets.forEach(function (target) {
      target.removeEventListener(binding.event, binding.handleEvent, binding.options);
    });
    this.targets.clear();
  };
  RootGroupBinding.prototype.deliver = function (context) {
    if (this.destroyed || !this.group.isLogicalLive()) return;
    var carrier = context.carrier;
    if (context.direct) {
      if (!carrier || !this.group.hasLive(carrier)) return;
    } else if (!carrier || !this.group.hasLive(carrier)) {
      carrier = this.group.firstLive();
      if (!carrier) return;
    }
    this.callback(context.event, carrier);
  };
  RootGroupBinding.prototype.buildAlpineHandler = function () {
    var binding = this;
    var wrap = function (next, wrapper) { return function (context) { wrapper(next, context); }; };
    var handler = function (context) { binding.deliver(context); };
    if (this.modifiers.indexOf("debounce") !== -1) {
      var debounceWait = rootGroupTiming(this.modifiers, "debounce");
      var debounceTimer = 0;
      handler = (function (next) {
        return function (context) {
          window.clearTimeout(debounceTimer);
          debounceTimer = window.setTimeout(function () { debounceTimer = 0; next(context); }, debounceWait);
        };
      })(handler);
      this.cancelTimers.push(function () { window.clearTimeout(debounceTimer); });
    }
    if (this.modifiers.indexOf("throttle") !== -1) {
      var throttleWait = rootGroupTiming(this.modifiers, "throttle");
      var throttled = false;
      var throttleTimer = 0;
      handler = (function (next) {
        return function (context) {
          if (throttled) return;
          next(context);
          throttled = true;
          throttleTimer = window.setTimeout(function () { throttled = false; throttleTimer = 0; }, throttleWait);
        };
      })(handler);
      this.cancelTimers.push(function () { window.clearTimeout(throttleTimer); throttled = false; });
    }
    if (this.modifiers.indexOf("prevent") !== -1) handler = wrap(handler, function (next, c) { c.event.preventDefault(); next(c); });
    if (this.modifiers.indexOf("stop") !== -1) handler = wrap(handler, function (next, c) { c.event.stopPropagation(); next(c); });
    if (this.modifiers.indexOf("once") !== -1) handler = wrap(handler, function (next, c) { next(c); binding.stopListening(); });
    if (this.targetMode() === "outside") {
      handler = wrap(handler, function (next, c) {
        if (binding.group.containsEvent(c.event)) return;
        if (c.event.target && c.event.target.isConnected === false) return;
        if (!binding.group.hasVisibleRoot()) return;
        next(c);
      });
    }
    if (this.modifiers.indexOf("self") !== -1) {
      handler = wrap(handler, function (next, c) { if (binding.group.els.indexOf(c.event.target) !== -1) next(c); });
    }
    if (ROOT_GROUP_ENTER_LEAVE.has(this.event)) {
      handler = wrap(handler, function (next, c) {
        if (c.event.relatedTarget && binding.group.containsNode(c.event.relatedTarget)) return;
        next(c);
      });
    }
    if (this.event === "submit") {
      handler = wrap(handler, function (next, c) {
        var updates = c.event.target && c.event.target._x_pendingModelUpdates;
        if (updates) updates.forEach(function (update) { update(); });
        next(c);
      });
    }
    if (rootGroupIsKeyEvent(this.event) || rootGroupIsClickEvent(this.event)) {
      handler = wrap(handler, function (next, c) { if (!rootGroupMissesKeyFilter(c.event, binding.modifiers)) next(c); });
    }
    return handler;
  };
  RootGroupBinding.prototype.buildCitryHandler = function () {
    var binding = this;
    var exhausted = false;
    var debounceTimer = 0;
    var throttleUntil = 0;
    this.cancelTimers.push(function () { window.clearTimeout(debounceTimer); });
    return function (context) {
      var spec = binding.citrySpec;
      if (
        ROOT_GROUP_ENTER_LEAVE.has(binding.event) && context.event.relatedTarget &&
        binding.group.containsNode(context.event.relatedTarget)
      ) return;
      if (spec.key) {
        var expected = { enter: "Enter", escape: "Escape" }[spec.key];
        if (!expected || context.event.key !== expected) return;
      }
      if (spec.self === true && binding.group.els.indexOf(context.event.target) === -1) return;
      if (spec.once === true) {
        if (exhausted) return;
        exhausted = true;
        binding.stopListening();
      }
      if (spec.prevent === true) context.event.preventDefault();
      if (spec.stop === true) context.event.stopPropagation();
      var now = Date.now();
      if (spec.throttle > 0) {
        if (throttleUntil > now) return;
        throttleUntil = now + spec.throttle;
      }
      if (!(spec.debounce > 0)) {
        binding.deliver(context);
        return;
      }
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(function () { debounceTimer = 0; binding.deliver(context); }, spec.debounce);
    };
  };
  RootGroupBinding.prototype.cleanup = function () {
    if (this.destroyed) return;
    this.destroyed = true;
    this.stopListening();
    this.cancelTimers.splice(0).forEach(function (cancel) { cancel(); });
    this.group.bindings.delete(this);
  };

  var PROP_BLOCKED_KEYS = new Set(["__proto__", "prototype", "constructor"]);
  var propTypeName = function (ctor) { return typeof ctor === "function" && ctor.name ? ctor.name : String(ctor); };
  var propValueType = function (value) {
    if (Array.isArray(value)) return "an array";
    return "a " + typeof value;
  };
  var propMatchesType = function (value, ctor) {
    if (ctor === String) return typeof value === "string";
    if (ctor === Number) return typeof value === "number";
    if (ctor === Boolean) return typeof value === "boolean";
    if (ctor === Function) return typeof value === "function";
    if (ctor === Symbol) return typeof value === "symbol";
    if (ctor === BigInt) return typeof value === "bigint";
    if (ctor === Array) return Array.isArray(value);
    if (ctor === Object) return value !== null && typeof value === "object";
    return typeof ctor === "function" && value instanceof ctor;
  };
  var plainPropsObject = function (value) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
    if (typeof value.then === "function") return false;
    var prototype = Object.getPrototypeOf(value);
    return prototype === Object.prototype || prototype === null;
  };

  var createPropsController = function (lifecycle, declarations, expectsSupply) {
    var classId = lifecycle.classId;
    var declarationIsObject = declarations !== null && typeof declarations === "object" && !Array.isArray(declarations);
    var definitions = declarationIsObject ? declarations : {};
    var target = alpineOwner.reactive({});
    var defaults = {};
    var episodes = new Map();
    var declarationErrors = new Map();
    var declaredNames = Object.keys(definitions);
    var controller = {
      target: target,
      view: null,
      defaults: defaults,
      definitions: definitions,
      expectsSupply: expectsSupply,
      initialSettled: false,
      currentValid: false,
      effectStop: null,
      sourceBoundary: null,
    };

    var report = function (key, message) {
      if (episodes.get(key) === message) return;
      episodes.set(key, message);
      console.error("[Citry] component " + classId + " props for render '" + lifecycle.renderId + "': " + message);
    };
    var recover = function (failures) {
      Array.from(episodes.keys()).forEach(function (key) {
        if (!failures.has(key)) episodes.delete(key);
      });
    };

    if (!declarationIsObject) {
      declarationErrors.set("$declaration", "the props declaration must be an object.");
      declaredNames = [];
    }
    declaredNames.forEach(function (name) {
      var definition = definitions[name];
      if (PROP_BLOCKED_KEYS.has(name)) {
        declarationErrors.set(name, "prop '" + name + "' uses a prototype-sensitive key and is not allowed.");
        return;
      }
      if (definition === null || typeof definition !== "object" || Array.isArray(definition)) {
        declarationErrors.set(name, "prop '" + name + "' must be an object with type, required, and/or default.");
        return;
      }
      if (definition.required != null && typeof definition.required !== "boolean") {
        declarationErrors.set(name, "prop '" + name + "' has a non-boolean required option.");
      }
      if (definition.type != null) {
        var types = Array.isArray(definition.type) ? definition.type : [definition.type];
        if (!types.length || types.some(function (ctor) { return typeof ctor !== "function"; })) {
          declarationErrors.set(name, "prop '" + name + "' type must be a constructor or a non-empty array of constructors.");
        }
      }
      if (Object.prototype.hasOwnProperty.call(definition, "default")) {
        if (definition.default !== null && typeof definition.default === "object") {
          declarationErrors.set(name, "prop '" + name + "' has an object or array default; use a per-instance factory.");
          return;
        }
        try {
          defaults[name] = typeof definition.default === "function" ? definition.default() : definition.default;
        } catch (err) {
          declarationErrors.set(name, "prop '" + name + "' default factory threw: " + (err && err.message ? err.message : String(err)));
        }
      } else {
        defaults[name] = undefined;
      }
    });

    controller.view = new Proxy(target, {
      set: function (_object, name) {
        throw new TypeError("[Citry] props are read-only; assign child-local values to scope instead of props." + String(name));
      },
      deleteProperty: function () {
        throw new TypeError("[Citry] props are read-only; top-level prop keys cannot be deleted.");
      },
      defineProperty: function () {
        throw new TypeError("[Citry] props are read-only; top-level prop keys cannot be redefined.");
      },
    });

    controller.apply = function (supplied, supplierError) {
      var failures = new Map(declarationErrors);
      var shapeValid = supplierError == null && plainPropsObject(supplied);
      if (!shapeValid) {
        var shapeMessage = supplierError
          ? "the $c-props supplier threw: " + (supplierError.message || String(supplierError))
          : "the $c-props supplier must synchronously return a plain object; Promises, thenables, arrays, and class instances are invalid.";
        failures.set("$supplier", shapeMessage);
        declaredNames.forEach(function (name) { target[name] = undefined; });
      } else {
        Object.keys(supplied).forEach(function (name) {
          if (PROP_BLOCKED_KEYS.has(name)) {
            failures.set("unknown:" + name, "ignored prototype-sensitive supplied key '" + name + "'.");
          } else if (!Object.prototype.hasOwnProperty.call(definitions, name)) {
            failures.set("unknown:" + name, "ignored unknown supplied prop '" + name + "'.");
          }
        });
        declaredNames.forEach(function (name) {
          if (declarationErrors.has(name)) {
            target[name] = undefined;
            return;
          }
          var definition = definitions[name];
          var value = Object.prototype.hasOwnProperty.call(supplied, name) ? supplied[name] : defaults[name];
          if (value === undefined && definition.required === true) {
            failures.set(name, "prop '" + name + "' is required, but the current supply and declaration default are both undefined.");
            target[name] = undefined;
            return;
          }
          if (value !== undefined && value !== null && definition.type != null) {
            var accepted = Array.isArray(definition.type) ? definition.type : [definition.type];
            if (!accepted.some(function (ctor) { return propMatchesType(value, ctor); })) {
              failures.set(
                name,
                "prop '" + name + "' expected " + accepted.map(propTypeName).join(" or ") + ", got " + propValueType(value) + "."
              );
              target[name] = undefined;
              return;
            }
          }
          target[name] = value;
        });
      }
      recover(failures);
      failures.forEach(function (message, key) { report(key, message); });
      controller.currentValid = Array.from(failures.keys()).every(function (key) {
        return String(key).indexOf("unknown:") === 0;
      });
      if (!controller.initialSettled) controller.initialSettled = true;
      return controller.currentValid;
    };
    controller.applyNoSupply = function () { return controller.apply({}); };
    controller.destroy = function () {
      if (controller.effectStop) {
        try { controller.effectStop(); } catch (_err) {}
        controller.effectStop = null;
      }
    };
    return controller;
  };

  var lifecycleCapsAreLive = function (lifecycle) {
    // Graph-backed lifecycles use exact canonical or runtime-placement caps.
    // A compatibility render id belongs only to the legacy no-graph path; its
    // Events anchor owns retirement after the DOM liveness sweep.
    if (lifecycle.compatRenderId) return true;
    var range = lifecyclePhysicalRange(lifecycle);
    return Boolean(
      range.route && range.state && range.physicals.some(function (physical) {
        return physicalRangeIsLive(range.state, physical);
      })
    );
  };

  var rootsForRender = function (renderId) {
    return Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + renderId + "]"));
  };

  var lifecycleForRender = function (renderId) {
    var found = null;
    ownershipStates.forEach(function (state) {
      if (found) return;
      var link = state.renderLinks.get(renderId);
      if (link && link.link.active && link.logicalState.lifecycle && link.logicalState.lifecycle.active) {
        found = link.logicalState.lifecycle;
      }
    });
    if (!found) {
      componentLifecycles.forEach(function (lifecycle) {
        if (!found && lifecycle.active && lifecycle.compatRenderId === renderId) found = lifecycle;
      });
    }
    return found;
  };

  var rootsForLifecycle = function (lifecycle) {
    if (lifecycle.compatRenderId) return rootsForRender(lifecycle.compatRenderId);
    var range = lifecyclePhysicalRange(lifecycle);
    if (!range.route || !range.state) return [];
    var roots = [];
    range.physicals.forEach(function (physical) {
      if (!physicalRangeIsLive(range.state, physical)) return;
      roots = roots.concat(physicalRangeRoots(physical, range.route.instance.renderId));
    });
    roots.sort(function (left, right) {
      if (nodePrecedes(left, right)) return -1;
      if (nodePrecedes(right, left)) return 1;
      return 0;
    });
    return roots;
  };

  var lifecycleOwnsRoot = function (lifecycle, root) {
    return lifecycle.active && rootsForLifecycle(lifecycle).indexOf(root) !== -1;
  };

  var innermostLifecycleForRoot = function (root) {
    if (!root || !root.getAttribute) return null;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    for (var index = ids.length - 1; index >= 0; index -= 1) {
      var lifecycle = lifecycleForRender(ids[index]);
      if (lifecycle && lifecycleOwnsRoot(lifecycle, root)) return lifecycle;
    }
    return null;
  };

  var localAlpineLayers = function (root, previous) {
    var stack = root._x_dataStack ? root._x_dataStack.slice() : [];
    if (previous) {
      var previousIndex = stack.indexOf(previous.router);
      if (previousIndex !== -1) return stack.slice(0, previousIndex);
    }
    var parent = root.parentElement;
    while (parent && !parent._x_dataStack) parent = parent.parentElement;
    if (!parent || !parent._x_dataStack) return stack;
    var inherited = new Set(parent._x_dataStack);
    var firstInherited = stack.findIndex(function (layer) { return inherited.has(layer); });
    return firstInherited === -1 ? stack : stack.slice(0, firstInherited);
  };

  var makeScopeRouter = function (scope) {
    var owner = alpineOwner.reactive({ current: scope });
    var router = new Proxy({}, {
      ownKeys: function () { return owner.current ? Reflect.ownKeys(owner.current) : []; },
      has: function (_target, name) { return Boolean(owner.current && Reflect.has(owner.current, name)); },
      get: function (_target, name) {
        return owner.current ? Reflect.get(owner.current, name, owner.current) : undefined;
      },
      set: function (_target, name, value) {
        if (!owner.current) return true;
        return Reflect.set(owner.current, name, value, owner.current);
      },
      deleteProperty: function (_target, name) {
        if (!owner.current) return true;
        return Reflect.deleteProperty(owner.current, name);
      },
      getOwnPropertyDescriptor: function (_target, name) {
        if (!owner.current) return undefined;
        var descriptor = Reflect.getOwnPropertyDescriptor(owner.current, name);
        return descriptor ? Object.assign({}, descriptor, { configurable: true }) : undefined;
      },
    });
    return { owner: owner, router: router };
  };

  isolateRootScope = function (root, fallbackScope) {
    var lifecycle = innermostLifecycleForRoot(root);
    var scope = lifecycle && lifecycle.scope ? lifecycle.scope : fallbackScope;
    var previous = rootScopeOwners.get(root) || null;
    var fillRoute = fillRoutesByElement.get(root) || null;
    if (fillRoute && fillRoute.descriptor && fillRoute.descriptor.active) {
      var fillLocal = localAlpineLayers(root, previous);
      var fillFrameIndex = fillLocal.indexOf(fillRoute.descriptor.frame);
      fillLocal = fillFrameIndex === -1 ? [] : fillLocal.slice(0, fillFrameIndex + 1);
      if (previous) {
        try { previous.remove(); } catch (_err) {}
        rootScopeOwners.delete(root);
      }
      // A slot-only receiver can share its physical root with caller-owned
      // fill markup. That expression surface belongs wholly to the fill
      // source; the receiver router must not remain as a fallback for names
      // missing at the caller.
      root._x_dataStack = fillLocal.length ? fillLocal : [fillRoute.descriptor.frame];
      return function () {};
    }
    if (previous && root._x_dataStack && root._x_dataStack.indexOf(previous.router) !== -1) {
      previous.scope = scope;
      previous.owner.current = scope;
      return previous.remove;
    }
    var local = localAlpineLayers(root, previous);
    if (previous) {
      try { previous.remove(); } catch (_err) {}
    }
    var routed = makeScopeRouter(scope);
    var remove = alpineOwner.addScopeToNode(root, routed.router);
    // Same-root user x-data remains above the Citry layer. Inherited parent
    // layers are deliberately absent, which is the component isolation rule.
    root._x_dataStack = local.concat([routed.router]);
    var record = { scope: scope, owner: routed.owner, router: routed.router, remove: remove };
    rootScopeOwners.set(root, record);
    return remove;
  };

  // ----- graph-owned slot source projection -----

  var fillDescriptorIsLive = function (descriptor) {
    if (!descriptor.active || !descriptor.groupState || descriptor.groupState.retired) return false;
    if (!descriptor.groupState.active) return false;
    if (descriptor.ownerLifecycle && !descriptor.ownerLifecycle.active) return false;
    if (descriptor.sourceState && descriptor.sourcePhysicalKey) {
      return physicalRangesForKey(descriptor.sourceState, descriptor.sourcePhysicalKey).some(function (physical) {
        return physicalRangeIsLive(descriptor.sourceState, physical);
      });
    }
    return descriptor.detached || Boolean(descriptor.ownerLifecycle);
  };

  var fillRouteToken = function (state, localKey) {
    return state.publicRevision.revision + ":" + localKey;
  };

  var fillDescriptorStack = function (descriptor) {
    if (!fillDescriptorIsLive(descriptor)) return [];
    var stack = descriptor.sourceOrigin instanceof Element
      ? alpineOwner.closestDataStack(descriptor.sourceOrigin).slice()
      : [];
    var sourceScope = descriptor.ownerLifecycle && descriptor.ownerLifecycle.scope;
    if (sourceScope && stack.indexOf(sourceScope) === -1) stack.push(sourceScope);
    return stack;
  };

  var makeFillSourceFrame = function (descriptor) {
    descriptor.frameVersion = alpineOwner.reactive({ current: 0 });
    var liveScope = function () {
      descriptor.frameVersion.current;
      return alpineOwner.mergeProxies(fillDescriptorStack(descriptor));
    };
    return new Proxy({}, {
      ownKeys: function () {
        return Array.from(new Set([FILL_SOURCE_FRAME].concat(Reflect.ownKeys(liveScope()))));
      },
      has: function (_target, name) {
        return name === FILL_SOURCE_FRAME || Reflect.has(liveScope(), name);
      },
      get: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) return descriptor;
        return Reflect.get(liveScope(), name);
      },
      set: function (_target, name, value) {
        if (name === FILL_SOURCE_FRAME) return false;
        return Reflect.set(liveScope(), name, value);
      },
      deleteProperty: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) return false;
        return Reflect.deleteProperty(liveScope(), name);
      },
      getOwnPropertyDescriptor: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) {
          return { configurable: true, enumerable: false, value: descriptor };
        }
        if (!Reflect.has(liveScope(), name)) return undefined;
        return {
          configurable: true,
          enumerable: true,
          get: function () { return Reflect.get(liveScope(), name); },
          set: function (value) { Reflect.set(liveScope(), name, value); },
        };
      },
    });
  };

  var fillDescriptorInStack = function (el) {
    if (!alpineOwner || !(el instanceof Element)) return null;
    var stack = el._x_dataStack || alpineOwner.closestDataStack(el);
    for (var index = 0; index < stack.length; index += 1) {
      try {
        var descriptor = stack[index] && stack[index][FILL_SOURCE_FRAME];
        if (descriptor) return descriptor;
      } catch (_err) {}
    }
    return null;
  };

  var fillBacklinkOwner = function (el) {
    var current = el;
    while (current._x_teleportBack && current._x_teleportBack._x_teleport === current) {
      current = current._x_teleportBack;
    }
    return current;
  };

  var clearFillMagicCaches = function (root) {
    alpineOwner.walk(root, function (el) {
      delete el._x_refs_proxy;
      delete el._x_id;
    });
  };

  var unlinkFillRoot = function (el, descriptor) {
    descriptor.roots.delete(el);
    var currentRoute = fillRoutesByElement.get(el);
    if (currentRoute && currentRoute.descriptor !== descriptor) return;
    fillRoutesByElement.delete(el);
    var owner = el._x_citryFillBacklinkOwner;
    delete el._x_citryFillBacklinkOwner;
    if (!owner || owner._x_citryFillBacklink !== descriptor) return;
    var stillUsed = Array.from(descriptor.roots).some(function (root) {
      return root._x_citryFillBacklinkOwner === owner;
    });
    if (stillUsed) return;
    delete owner._x_citryFillBacklink;
    delete owner._x_teleportBack;
  };

  var linkFillRoot = function (el, route) {
    var descriptor = route.descriptor;
    retiredFillRoots.delete(el);
    fillRoutesByElement.set(el, route);
    descriptor.routesByRoot.set(el, route.token);
    var owner = fillBacklinkOwner(el);
    if (owner._x_teleportBack && owner._x_citryFillBacklink !== descriptor) {
      throw pointedAlpineError("a slot source cannot replace an unrelated Alpine teleport backlink.");
    }
    owner._x_citryFillBacklink = descriptor;
    owner._x_teleportBack = descriptor.carrier;
    el._x_citryFillBacklinkOwner = owner;
    descriptor.roots.add(el);
  };

  var fillRouteForDirective = function (expression) {
    var route = fillRegionRoutes.get(expression.trim());
    if (!route || !route.descriptor.active) {
      throw pointedAlpineError("a slot source directive refers to an inactive or unknown ownership region.");
    }
    return route;
  };

  installFillSourceDirective = function (alpine) {
    ["addScopeToNode", "closestDataStack", "mergeProxies", "onElRemoved", "walk", "closestRoot"].forEach(
      function (name) {
        if (typeof alpine[name] !== "function") {
          throw pointedAlpineError("the pinned runtime is missing required slot-scope API Alpine." + name + ".");
        }
      }
    );
    var emptyReference = document.createDocumentFragment();
    var handler = function (el, directive, utilities) {
      var route = fillRouteForDirective(directive.expression);
      var descriptor = route.descriptor;
      var ownStack = Object.prototype.hasOwnProperty.call(el, "_x_dataStack") ? el._x_dataStack || [] : [];
      var alreadyLinked = ownStack.some(function (layer) {
        try { return layer && layer[FILL_SOURCE_FRAME] === descriptor; } catch (_err) { return false; }
      });
      var undo = alreadyLinked
        ? function () {}
        : alpine.addScopeToNode(el, descriptor.frame, emptyReference);
      var released = false;
      var release = function () {
        if (released) return;
        released = true;
        undo();
        if (descriptor.rootReleases.get(el) === release) descriptor.rootReleases.delete(el);
        retiredFillRoots.add(el);
        unlinkFillRoot(el, descriptor);
      };
      descriptor.rootReleases.set(el, release);
      utilities.cleanup(release);
    };
    handler.inline = function (el, directive) {
      var route = fillRouteForDirective(directive.expression);
      if (
        el.tagName === "TEMPLATE" &&
        (el.hasAttribute("x-if") || el.hasAttribute("x-for") || el.hasAttribute("x-teleport"))
      ) {
        var generatedRoot = el.content.firstElementChild;
        if (!generatedRoot) {
          throw pointedAlpineError("a structural slot fill needs one element root.");
        }
        var existing = generatedRoot.getAttribute(FILL_SOURCE_ATTR);
        if (existing && existing !== directive.expression.trim()) {
          throw pointedAlpineError("one structural root cannot belong to two slot sources.");
        }
        generatedRoot.setAttribute(FILL_SOURCE_ATTR, directive.expression.trim());
      }
      linkFillRoot(el, route);
    };
    alpine.directive("citry-fill-source", handler).before("ref");

    // Stock `$root` stops at a shared receiver/fill `data-citry-root` before
    // following `_x_teleportBack`. A local x-data root remains physical; an
    // otherwise shared root follows the graph-selected lexical carrier.
    alpine.magic("root", function (el) {
      var descriptor = fillDescriptorInStack(el);
      var physical = alpine.closestRoot(el);
      if (!descriptor || !fillDescriptorIsLive(descriptor) || (physical && physical.hasAttribute("x-data"))) {
        return physical;
      }
      return alpine.closestRoot(descriptor.carrier);
    });
  };

  var fillRegionDirectElements = function (state, region) {
    var elements = [];
    physicalRangesForKey(state, region.key).forEach(function (physical) {
      if (!physicalRangeIsLive(state, physical)) return;
      var nested = [];
      state.physicalPlacements.forEach(function (placements) {
        placements.forEach(function (candidate) {
          if (
            candidate !== physical && candidate.graphId === region.graphId &&
            candidate.placementId === physical.placementId &&
            candidate.parentRegionId === region.regionId && physicalRangeIsLive(state, candidate)
          ) nested.push(candidate);
        });
      });
      physicalRangeElements(physical).forEach(function (element) {
        if (nested.some(function (candidate) { return physicalRangeContainsNode(candidate, element); })) return;
        if (element.hasAttribute("data-citry-root")) {
          var ids = (element.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
          if (region.receiverRenderId != null && ids.indexOf(region.receiverRenderId) === -1) return;
        }
        elements.push(element);
      });
    });
    return elements;
  };

  var fallbackSourceOrigin = function (state, region) {
    var cursor = region;
    while (cursor.parentRegionId != null) {
      var parent = state.registry.slotRegions.get(qualifiedGraphId(cursor.graphId, "r", cursor.parentRegionId));
      if (!parent) break;
      if (parent.transitionFromRenderId === region.ownerRenderId) {
        var parentPhysical = state.registry.physicalRegions.get(parent.key);
        return parentPhysical && parentPhysical.start.parentElement;
      }
      cursor = parent;
    }
    var physical = state.registry.physicalRegions.get(region.key);
    return physical && physical.start.parentElement;
  };

  var preflightGraphFillSources = function (state, acceptedRenderIds, excludedPhysicalKeys) {
    var plans = [];
    state.registry.fills.values().forEach(function (fill) {
      if (
        acceptedRenderIds &&
        ((fill.ownerRenderId != null && !acceptedRenderIds.has(fill.ownerRenderId)) ||
          (fill.receiverRenderId != null && !acceptedRenderIds.has(fill.receiverRenderId)))
      ) return;
      var groupState = state.rangeGroupStates.get(fill.key);
      if (!groupState || !groupState.slotRegions.length) return;
      var acceptedSlotRegions = excludedPhysicalKeys
        ? groupState.slotRegions.filter(function (region) { return !excludedPhysicalKeys.has(region.key); })
        : groupState.slotRegions.slice();
      if (!acceptedSlotRegions.length) return;
      if (acceptedSlotRegions.length !== groupState.slotRegions.length) {
        throw pointedAlpineError("a shared fill was only partially accepted by the ownership plan.");
      }
      var sourceInvocation = fill.sourceInvocationId == null
        ? null
        : state.registry.nestedComponents.get(qualifiedGraphId(fill.graphId, "v", fill.sourceInvocationId));
      var sourceInstance = sourceInvocation
        ? state.registry.renderIds.get(sourceInvocation.targetRenderId)
        : null;
      var sourcePhysical = sourceInstance && state.registry.physicalRegions.get(sourceInstance.key);
      if (fill.policy === "template" && fill.kind !== "fallback" && (!sourceInvocation || !sourcePhysical)) {
        throw pointedAlpineError("a supplied slot fill has no validated source invocation carrier.");
      }
      var plan = {
        state: state,
        fill: fill,
        groupState: groupState,
        sourceInvocation: sourceInvocation,
        sourcePhysical: sourcePhysical,
        slotRegions: acceptedSlotRegions,
      };
      plan.slotRegions.forEach(function (region) {
        fillRegionDirectElements(state, region).forEach(function (element) {
          if (alpineStarted && element._x_marker) {
            throw pointedAlpineError(
              "a delayed slot region arrived after Alpine initialized; adopt its graph and DOM atomically."
            );
          }
        });
      });
      plans.push(plan);
    });
    return plans;
  };

  // Alpine evaluators capture the data-stack frame object when their
  // directive initializes. Morph can preserve a physical fill element while
  // its graph route changes, so replacing only the element's route would
  // leave existing effects attached to a retired frame. Preserve the live
  // descriptor object and retarget its graph fields instead. The reactive
  // frame version then reruns bindings against the incoming source without
  // destroying same-root local Alpine state.
  var adoptFillSourceDescriptor = function (previous, incoming) {
    if (previous === incoming) return previous;
    var previousKey = previous.key;
    var previousRegions = previous.slotRegions.slice();
    previous.slotRegions.forEach(function (region) {
      var token = fillRouteToken(previous.state, region.key);
      var route = fillRegionRoutes.get(token);
      if (route && route.descriptor === previous) fillRegionRoutes.delete(token);
    });

    previous.key = incoming.key;
    previous.state = incoming.state;
    previous.fill = incoming.fill;
    previous.groupState = incoming.groupState;
    previous.slotRegions = incoming.slotRegions;
    previous.ownerRenderId = incoming.ownerRenderId;
    previous.ownerLifecycle = incoming.ownerLifecycle;
    previous.sourceState = incoming.sourceState;
    previous.sourcePhysical = incoming.sourcePhysical;
    previous.sourcePhysicalKey = incoming.sourcePhysicalKey;
    previous.sourceOrigin = incoming.sourceOrigin;
    previous.detached = incoming.detached;
    previous.active = true;
    if (previous.sourceOrigin instanceof Element) {
      previous.carrier._x_teleportBack = previous.sourceOrigin;
    } else {
      delete previous.carrier._x_teleportBack;
    }

    incoming.slotRegions.forEach(function (region) {
      var token = fillRouteToken(incoming.state, region.key);
      var route = fillRegionRoutes.get(token);
      if (route) route.descriptor = previous;
    });
    Array.from(previous.roots).forEach(function (root) {
      var oldToken = previous.routesByRoot.get(root);
      var oldRegion = oldToken && previousRegions.find(function (region) {
        return oldToken.slice(65) === region.key;
      });
      var oldIndex = oldRegion ? previousRegions.indexOf(oldRegion) : 0;
      var nextRegion = incoming.slotRegions[oldIndex] || incoming.slotRegions[0];
      if (!nextRegion) return;
      var token = fillRouteToken(incoming.state, nextRegion.key);
      var route = fillRegionRoutes.get(token);
      if (!route) return;
      fillRoutesByElement.set(root, route);
      previous.routesByRoot.set(root, token);
      if (root.getAttribute(FILL_SOURCE_ATTR) !== token) root.setAttribute(FILL_SOURCE_ATTR, token);
      clearFillMagicCaches(root);
    });

    previous.frameVersion.current += 1;

    incoming.active = false;
    fillSourceDescriptors.delete(previousKey);
    fillSourceDescriptors.delete(incoming.key);
    fillSourceDescriptors.set(previous.key, previous);
    return previous;
  };

  var stampFillRoutes = function () {
    Array.from(fillSourceDescriptors.values()).forEach(function (descriptor) {
      if (!descriptor.active) return;
      descriptor.slotRegions.forEach(function (region) {
        var token = fillRouteToken(descriptor.state, region.key);
        var route = fillRegionRoutes.get(token);
        fillRegionDirectElements(descriptor.state, region).forEach(function (element) {
          var previousRoute = fillRoutesByElement.get(element);
          if (
            previousRoute && previousRoute.descriptor !== descriptor &&
            previousRoute.descriptor.active && element._x_marker
          ) {
            descriptor = adoptFillSourceDescriptor(previousRoute.descriptor, descriptor);
            route.descriptor = descriptor;
          }
          fillRoutesByElement.set(element, route);
          descriptor.routesByRoot.set(element, token);
          if (element.getAttribute(FILL_SOURCE_ATTR) !== token) {
            element.setAttribute(FILL_SOURCE_ATTR, token);
          }
        });
      });
    });
  };

  var retireFillSource = function (descriptor) {
    if (!descriptor.active) return;
    descriptor.active = false;
    Array.from(descriptor.roots).forEach(function (root) {
      var currentRoute = fillRoutesByElement.get(root);
      if (currentRoute && currentRoute.descriptor !== descriptor) {
        var handedOffRelease = descriptor.rootReleases.get(root);
        if (handedOffRelease) handedOffRelease();
        descriptor.routesByRoot.delete(root);
        return;
      }
      clearFillMagicCaches(root);
      retiredFillRoots.add(root);
      var release = descriptor.rootReleases.get(root);
      if (release) release();
      // A teleported clone can outlive the source template physically. Keep
      // that retired DOM isolated instead of revealing receiver or placement
      // scopes after the live source frame is removed.
      root._x_dataStack = [RETIRED_FILL_SCOPE];
      if (root.getAttribute(FILL_SOURCE_ATTR) === descriptor.routesByRoot.get(root)) {
        root.removeAttribute(FILL_SOURCE_ATTR);
      }
      descriptor.routesByRoot.delete(root);
      unlinkFillRoot(root, descriptor);
    });
    descriptor.slotRegions.forEach(function (region) {
      fillRegionRoutes.delete(fillRouteToken(descriptor.state, region.key));
    });
    fillSourceDescriptors.delete(descriptor.key);
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var reconcileFillSources = function () {
    fillReconcileScheduled = false;
    reconcilePhysicalRangeGroups();
    fillSourceDescriptors.forEach(function (descriptor) {
      if (!fillDescriptorIsLive(descriptor)) {
        retireFillSource(descriptor);
      }
    });
    stampFillRoutes();
  };

  var scheduleFillSourceReconcile = function () {
    if (fillReconcileScheduled) return;
    fillReconcileScheduled = true;
    queueMicrotask(reconcileFillSources);
  };

  var activateGraphFillSources = function (state, plans) {
    plans.forEach(function (plan) {
      var fill = plan.fill;
      var ownerLifecycle = null;
      if (fill.ownerRenderId != null) {
        ownerLifecycle = ensureLifecycle(resolveOwnershipRoute(state.publicRevision.revision, fill.ownerRenderId, null), true);
      }
      if (fill.receiverRenderId != null) {
        ensureLifecycle(resolveOwnershipRoute(state.publicRevision.revision, fill.receiverRenderId, null), true);
      }
      var descriptor = {
        key: fillRouteToken(state, fill.key),
        state: state,
        fill: fill,
        groupState: plan.groupState,
        slotRegions: plan.slotRegions,
        ownerRenderId: fill.ownerRenderId,
        ownerLifecycle: ownerLifecycle,
        sourceState: plan.sourcePhysical ? state : null,
        sourcePhysical: plan.sourcePhysical,
        sourcePhysicalKey: plan.sourcePhysical ? plan.sourcePhysical.key : null,
        sourceOrigin: null,
        carrier: document.createElement("span"),
        frame: null,
        roots: new Set(),
        rootReleases: new Map(),
        routesByRoot: new WeakMap(),
        detached: fill.policy !== "template",
        active: true,
      };
      if (fill.policy === "template" && fill.kind === "fallback") {
        descriptor.sourceOrigin = fallbackSourceOrigin(state, plan.slotRegions[0]);
      } else if (plan.sourcePhysical) {
        descriptor.sourceOrigin = plan.sourcePhysical.start.parentElement;
      }
      descriptor.frame = makeFillSourceFrame(descriptor);
      descriptor.carrier._x_dataStack = [descriptor.frame];
      if (descriptor.sourceOrigin instanceof Element) descriptor.carrier._x_teleportBack = descriptor.sourceOrigin;
      fillSourceDescriptors.set(descriptor.key, descriptor);
      plan.slotRegions.forEach(function (region) {
        var token = fillRouteToken(state, region.key);
        fillRegionRoutes.set(token, { descriptor: descriptor, region: region, token: token });
      });
    });
    stampFillRoutes();
  };

  var refreshGraphFillSources = function (state) {
    fillSourceDescriptors.forEach(function (descriptor) {
      if (descriptor.state !== state || !descriptor.active) return;
      if (descriptor.sourcePhysicalKey) {
        var sourcePhysical = physicalRangesForKey(state, descriptor.sourcePhysicalKey).filter(function (physical) {
          return physicalRangeIsLive(state, physical);
        })[0] || null;
        descriptor.sourcePhysical = sourcePhysical;
        descriptor.sourceOrigin = sourcePhysical ? sourcePhysical.start.parentElement : null;
      } else if (descriptor.fill.policy === "template" && descriptor.fill.kind === "fallback") {
        descriptor.sourceOrigin = fallbackSourceOrigin(state, descriptor.slotRegions[0]);
      }
      if (descriptor.sourceOrigin instanceof Element) {
        descriptor.carrier._x_teleportBack = descriptor.sourceOrigin;
      } else {
        delete descriptor.carrier._x_teleportBack;
      }
    });
    stampFillRoutes();
  };

  var fillSourceOwnerForElement = function (el) {
    for (var current = el; current instanceof Element; current = current.parentElement) {
      if (retiredFillRoots.has(current)) return null;
    }
    var descriptor = fillDescriptorInStack(el);
    if (!descriptor || !fillDescriptorIsLive(descriptor)) return undefined;
    return descriptor.detached ? null : descriptor.ownerRenderId;
  };

  var holdRootForCall = function (root, call) {
    if (!root || !root.isConnected || root._x_marker || call.heldRoots.has(root)) return;
    var hold = rootHolds.get(root);
    if (!hold) {
      hold = {
        reasons: new Set(),
        ownedIgnore: !root._x_ignore,
        suppressedDescendants: [],
        promoted: false,
        releaseQueued: false,
      };
      rootHolds.set(root, hold);
    }
    hold.reasons.add(call);
    call.heldRoots.add(root);
  };

  var promoteRootHold = function (root) {
    var hold = rootHolds.get(root);
    if (!hold || hold.promoted) return;
    hold.promoted = true;
    if (hold.ownedIgnore) root._x_ignore = true;
    delete root._x_marker;
    root.querySelectorAll("*").forEach(function (descendant) {
      delete descendant._x_marker;
      if (descendant._x_ignoreSelf) return;
      descendant._x_ignoreSelf = true;
      hold.suppressedDescendants.push(descendant);
    });
  };

  var releaseRootHold = function (root, call) {
    var hold = rootHolds.get(root);
    if (!hold) return;
    hold.reasons.delete(call);
    call.heldRoots.delete(root);
    if (hold.reasons.size || hold.releaseQueued) return;
    hold.releaseQueued = true;
    queueMicrotask(function () {
      var current = rootHolds.get(root);
      if (current !== hold || current.reasons.size) {
        if (current) current.releaseQueued = false;
        return;
      }
      rootHolds.delete(root);
      if (hold.promoted && hold.ownedIgnore) delete root._x_ignore;
      hold.suppressedDescendants.forEach(function (descendant) {
        delete descendant._x_ignoreSelf;
      });
      if (alpineStarted && root.isConnected && !root._x_marker) {
        try {
          alpineOwner.initTree(root);
        } catch (err) {
          console.error("[Citry] Alpine initialization after component callback settlement failed:", err);
        }
      }
    });
  };

  var releaseCallHolds = function (call) {
    Array.from(call.heldRoots).forEach(function (root) { releaseRootHold(root, call); });
  };

  var disposeInvocation = function (lifecycle) {
    var invocation = lifecycle.invocation;
    if (!invocation || !invocation.active) return;
    invocation.active = false;
    if (invocation.ambientFrame) {
      var hadAmbientWrites = invocation.ambientFrame.writes.size > 0;
      invocation.ambientFrame.active = false;
      invocation.ambientFrame.open = false;
      invocation.ambientFrame.writes.clear();
      if (hadAmbientWrites && touchAmbientContext) touchAmbientContext();
    }
    invocation.effectStops.splice(0).forEach(function (stop) {
      try { stop(); } catch (err) {
        console.error("[Citry] managed component effect cleanup failed:", err);
      }
    });
    invocation.resources.splice(0).forEach(function (cleanup) {
      try { cleanup(); } catch (err) {
        console.error("[Citry] managed component resource cleanup failed:", err);
      }
    });
    if (invocation.userCleanup) {
      try { invocation.userCleanup(); } catch (err) {
        console.error("[Citry] component cleanup for '" + lifecycle.classId + "' failed:", err);
      }
    }
    lifecycle.invocation = null;
  };

  var destroyComponentBoundary = null;

  var cancelLifecycleCalls = function (lifecycle, reason) {
    var cancelled = false;
    Array.from(lifecycle.calls).forEach(function (call) {
      if (call.status === "settled" || call.status === "cancelled") return;
      cancelled = true;
      call.status = "cancelled";
      releaseCallHolds(call);
      releaseCallData(call);
      if (reason) {
        console.warn(
          "[Citry] cancelled component callback for retired render id '" + call.componentId + "': " + reason
        );
      }
    });
    lifecycle.calls.clear();
    if (cancelled) queueMicrotask(flushCalls);
  };

  var destroyLifecycle = function (lifecycle, reason) {
    if (!lifecycle || !lifecycle.active) return;
    lifecycle.active = false;
    cancelLifecycleCalls(lifecycle, reason || "its ownership caps left the document");
    disposeInvocation(lifecycle);
    Array.from(lifecycle.componentBoundaries || []).forEach(function (boundary) {
      if (destroyComponentBoundary) destroyComponentBoundary(boundary);
    });
    if (lifecycle.propsController) lifecycle.propsController.destroy();
    lifecycle.els.forEach(function (root) {
      var owner = rootScopeOwners.get(root);
      if (!owner || owner.scope !== lifecycle.scope) return;
      owner.scope = null;
      owner.owner.current = null;
    });
    if (lifecycle.rootGroup) lifecycle.rootGroup.destroy();
    else replaceArrayContents(lifecycle.els, []);
    releaseComponentDataKey(lifecycle.dataKey);
    lifecycle.dataKey = null;
    componentLifecycles.delete(lifecycle.logical.id);
    if (lifecycle.logicalState.lifecycle === lifecycle) lifecycle.logicalState.lifecycle = null;
    liveInstances.delete(lifecycle.renderId);
    if (lifecycle.compatRenderId) liveInstances.delete(lifecycle.compatRenderId);
    scheduleCssGc(lifecycle.classId);
    scheduleLifecycleReconcile();
  };

  var deactivateRenderLink = function (state, link) {
    if (!link || !link.link.active) return;
    link.link.active = false;
    link.anchorState.active = false;
    link.logicalState.active = false;
    browserAnchors.delete(link.anchorState.id);
    link.anchorState.revision = null;
    link.anchorState.renderId = null;
    link.logicalState.revision = null;
    link.logicalState.renderId = null;
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var ensureLifecycle = function (route, cascade, visited) {
    var state = ownershipStates.get(route.revision);
    var link = state && state.renderLinks.get(route.instance.renderId);
    if (!link || !link.link.active) return null;
    var lifecycle = link.logicalState.lifecycle;
    if (!lifecycle || !lifecycle.active) {
      lifecycle = {
        active: true,
        logical: link.link.logical,
        logicalState: link.logicalState,
        classId: route.instance.classId,
        revision: route.revision,
        renderId: route.instance.renderId,
        compatRenderId: null,
        scope: link.logicalState.scope || (alpineOwner ? alpineOwner.reactive({}) : null),
        els: link.logicalState.els,
        calls: new Set(),
        dataKey: null,
        invocation: null,
        componentBoundaries: new Set(),
        propsController: null,
        rootGroup: null,
      };
      lifecycle.rootGroup = new RootGroup(lifecycle.els, function () {
        return lifecycle.active && lifecycleCapsAreLive(lifecycle);
      });
      link.logicalState.lifecycle = lifecycle;
      link.logicalState.scope = lifecycle.scope;
      componentLifecycles.set(lifecycle.logical.id, lifecycle);
    } else {
      lifecycle.classId = route.instance.classId;
      lifecycle.revision = route.revision;
      lifecycle.renderId = route.instance.renderId;
      if (!lifecycle.scope && alpineOwner) {
        lifecycle.scope = alpineOwner.reactive({});
        link.logicalState.scope = lifecycle.scope;
      }
    }
    liveInstances.set(lifecycle.renderId, lifecycle.classId);
    if (cascade) {
      visited = visited || new Set();
      if (visited.has(route.instance.renderId)) return lifecycle;
      visited.add(route.instance.renderId);
      (state.childrenByParent.get(route.instance.renderId) || []).forEach(function (childRenderId) {
        try { ensureLifecycle(resolveOwnershipRoute(route.revision, childRenderId, null), true, visited); } catch (_err) {}
      });
    }
    scheduleLifecycleReconcile();
    return lifecycle;
  };

  var reconcileComponentLifecycles = function () {
    lifecycleReconcileScheduled = false;
    if (rangeMorphDepth > 0 || ownershipAdoptionDepth > 0) {
      scheduleLifecycleReconcile();
      return;
    }
    reconcilePhysicalRangeGroups();
    componentLifecycles.forEach(function (lifecycle) {
      if (!lifecycle.active) return;
      if (!lifecycleCapsAreLive(lifecycle)) {
        var failedRange = lifecyclePhysicalRange(lifecycle);
        var failedLink = failedRange.state && failedRange.route
          ? failedRange.state.renderLinks.get(failedRange.route.instance.renderId)
          : null;
        if (failedRange.state) reportPhysicalRangeCorruption(failedRange.state, failedRange.physical);
        destroyLifecycle(lifecycle);
        if (failedRange.state && failedLink && failedLink.logicalState === lifecycle.logicalState) {
          deactivateRenderLink(failedRange.state, failedLink);
        }
        return;
      }
      var route = routeForLifecycle(lifecycle);
      if (!route) {
        destroyLifecycle(lifecycle);
        return;
      }
      lifecycle.revision = route.revision;
      lifecycle.renderId = route.instance.renderId;
      lifecycle.classId = route.instance.classId;
      if (!lifecycle.scope && alpineOwner) lifecycle.scope = alpineOwner.reactive({});
      var roots = rootsForLifecycle(lifecycle);
      if (lifecycle.rootGroup) lifecycle.rootGroup.setRoots(roots);
      else replaceArrayContents(lifecycle.els, roots);
      lifecycle.calls.forEach(function (call) {
        if (call.status === "staged" || call.status === "waiting") {
          roots.forEach(function (root) { holdRootForCall(root, call); });
        }
      });
    });
    if (alpineOwner) {
      document.querySelectorAll("[data-citry-root]").forEach(function (root) {
        var lifecycle = innermostLifecycleForRoot(root);
        if (
          lifecycle &&
          lifecycle.scope &&
          (root === alpineBoundaryRoot || (root._x_marker && !root.hasAttribute("x-citry-boundary")))
        ) {
          isolateRootScope(root, lifecycle.scope);
        } else if (!lifecycle) {
          var owner = rootScopeOwners.get(root);
          if (owner) {
            owner.scope = null;
            owner.owner.current = null;
          }
        }
      });
    }
  };

  var scheduleLifecycleReconcile = function () {
    if (lifecycleReconcileScheduled) return;
    lifecycleReconcileScheduled = true;
    queueMicrotask(reconcileComponentLifecycles);
  };

  var boundaryIsLive = function (boundary, carrier) {
    if (boundary.destroyed || !boundary.sourceLifecycle.active || !boundary.targetLifecycle.active) return false;
    if (boundary.sourceOrigin && !boundary.sourceOrigin.isConnected) return false;
    if (!lifecycleCapsAreLive(boundary.sourceLifecycle) || !lifecycleCapsAreLive(boundary.targetLifecycle)) return false;
    if (carrier) return boundary.targetLifecycle.rootGroup.hasLive(carrier);
    return true;
  };

  var boundarySourceRenderId = function (boundary) {
    return boundary.sourceLifecycle.renderId || boundary.invocation.sourceRenderId;
  };

  var boundaryEventsScope = function (boundary, carrier) {
    var events = globalThis.Citry && globalThis.Citry.events;
    if (events && events._internal && typeof events._internal.boundaryScope === "function") {
      return events._internal.boundaryScope(
        boundarySourceRenderId(boundary),
        carrier || null,
        function () { return boundaryIsLive(boundary, carrier || null); }
      );
    }
    return {
      $state: Object.freeze({}),
      $loading: function () { return false; },
      $error: function () { return null; },
      $sendEvent: function () {
        return Promise.reject(new Error("[Citry] the source component declares no Events runtime."));
      },
      $onEvent: function () { return function () {}; },
    };
  };

  var boundaryPhysicalScope = function (boundary, event, carrier) {
    var scope = {};
    Object.defineProperties(scope, Object.getOwnPropertyDescriptors(boundaryEventsScope(boundary, carrier)));
    Object.defineProperties(scope, {
      $el: { enumerable: true, value: carrier },
      $event: { enumerable: true, value: event },
      $dispatch: {
        enumerable: true,
        value: function (name, detail, options) {
          if (!carrier) return false;
          return carrier.dispatchEvent(new CustomEvent(name, Object.assign({
            detail: detail == null ? {} : detail,
            bubbles: true,
            composed: true,
            cancelable: true,
          }, options || {})));
        },
      },
    });
    return scope;
  };

  var boundarySourceScope = function (boundary) {
    var origin = boundary.sourceOrigin;
    var scope = {};
    Object.defineProperties(scope, Object.getOwnPropertyDescriptors(boundaryEventsScope(boundary, null)));
    Object.defineProperties(scope, {
      $el: { enumerable: true, value: origin },
      $dispatch: {
        enumerable: true,
        value: function (name, detail, options) {
          if (!origin) return false;
          return origin.dispatchEvent(new CustomEvent(name, Object.assign({
            detail: detail == null ? {} : detail,
            bubbles: true,
            composed: true,
            cancelable: true,
          }, options || {})));
        },
      },
    });
    return scope;
  };

  var observeRejectedThenable = function (value, onRejected) {
    if (value === null || (typeof value !== "object" && typeof value !== "function")) return;
    var then;
    try { then = value.then; } catch (err) {
      onRejected(err);
      return;
    }
    if (typeof then !== "function") return;
    try { then.call(value, function () {}, onRejected); } catch (err) { onRejected(err); }
  };

  var evaluateBoundaryExpression = function (boundary, expression, event, carrier, physical) {
    if (!boundary.sourceCarrier || !boundaryIsLive(boundary, carrier || null)) {
      throw new Error("[Citry] a component-boundary expression was dropped because its source or target is no longer live.");
    }
    var scope = physical
      ? boundaryPhysicalScope(boundary, event, carrier)
      : boundarySourceScope(boundary);
    return alpineOwner.evaluateRaw(boundary.sourceCarrier, expression, {
      scope: scope,
      params: event ? [event] : [],
    });
  };

  var propsBoundaryForLifecycle = function (lifecycle) {
    var found = null;
    lifecycle.componentBoundaries.forEach(function (boundary) {
      if (found || boundary.targetLifecycle !== lifecycle) return;
      if (boundary.invocation.clientBindings.some(function (clientBinding) { return clientBinding.payload.type === "props"; })) found = boundary;
    });
    return found;
  };

  var lifecycleExpectsPropsSupply = function (lifecycle) {
    var route = routeForLifecycle(lifecycle);
    var state = route && ownershipStates.get(route.revision);
    var expected = false;
    if (!state) return false;
    state.registry.nestedComponents.values().forEach(function (invocation) {
      if (expected || invocation.targetRenderId !== route.instance.renderId) return;
      expected = invocation.clientBindings.some(function (clientBinding) { return clientBinding.payload.type === "props"; });
    });
    return expected;
  };

  var installPropsSupplier = function (boundary) {
    var lifecycle = boundary.targetLifecycle;
    var controller = lifecycle.propsController;
    if (!controller || controller.effectStop || !boundary.sourceCarrier) return;
    var clientBinding = boundary.invocation.clientBindings.find(function (candidate) { return candidate.payload.type === "props"; });
    if (!clientBinding) return;
    controller.sourceBoundary = boundary;
    var runner = alpineOwner.effect(function () {
      var value;
      var error = null;
      try {
        value = evaluateBoundaryExpression(boundary, clientBinding.payload.expression, null, null, false);
      } catch (err) {
        error = err;
      }
      observeRejectedThenable(value, function () {});
      controller.apply(value, error);
      flushCalls();
    });
    controller.effectStop = function () { alpineOwner.release(runner); };
  };

  var ensureLifecycleProps = function (lifecycle, entry) {
    var supplyBoundary = propsBoundaryForLifecycle(lifecycle);
    var expectsSupply = Boolean(supplyBoundary) || lifecycleExpectsPropsSupply(lifecycle);
    if (!entry.hasProps && !expectsSupply) return null;
    if (!lifecycle.propsController) {
      lifecycle.propsController = createPropsController(
        lifecycle,
        entry.hasProps ? entry.props : {},
        expectsSupply
      );
      if (!expectsSupply) lifecycle.propsController.applyNoSupply();
    }
    if (supplyBoundary) installPropsSupplier(supplyBoundary);
    return lifecycle.propsController;
  };

  var parseAlpineBoundaryKey = function (key) {
    var name = key.indexOf("x-on:") === 0 ? key.slice(5) : key.slice(1);
    var parts = name.split(".");
    return { event: parts.shift(), modifiers: parts };
  };

  var reportRootlessBoundaryHandler = function (boundary, clientBinding) {
    console.error(
      "[Citry] component boundary handler '" + clientBinding.key + "' cannot attach to render '" +
        boundary.invocation.targetRenderId + "' because the child rendered no HTML element root. " +
        "Add an element root or remove the DOM handler; $c-props, init, and @c-poll remain valid."
    );
  };

  var installBoundaryHandlers = function (boundary) {
    var group = boundary.targetLifecycle.rootGroup;
    boundary.invocation.clientBindings.forEach(function (clientBinding) {
      var payload = clientBinding.payload;
      if (payload.type === "props") return;
      if (payload.type !== "citry-poll" && group.els.length === 0) {
        reportRootlessBoundaryHandler(boundary, clientBinding);
      }
      if (payload.type === "alpine-handler") {
        var parsed = parseAlpineBoundaryKey(clientBinding.key);
        boundary.cleanups.push(group.on(parsed.event, parsed.modifiers, function (event, carrier) {
          try {
            var result = evaluateBoundaryExpression(boundary, payload.expression, event, carrier, true);
            observeRejectedThenable(result, function (err) {
              console.error("[Citry] relocated Alpine handler '" + clientBinding.key + "' failed:", err);
            });
          } catch (err) {
            console.error("[Citry] relocated Alpine handler '" + clientBinding.key + "' failed:", err);
          }
        }));
        return;
      }
      var dispatchCitry = function (event, carrier) {
        var args = null;
        try {
          if (payload.args != null) {
            args = evaluateBoundaryExpression(boundary, "(" + payload.args + ")", event, carrier, Boolean(carrier));
            if (args === null || typeof args !== "object" || Array.isArray(args) || typeof args.then === "function") {
              observeRejectedThenable(args, function () {});
              throw new TypeError("the Citry boundary argument expression must synchronously return an object.");
            }
          }
          var events = globalThis.Citry && globalThis.Citry.events;
          if (!events || !events._internal || typeof events._internal.sendBoundary !== "function") {
            throw new Error("the Events runtime is not available.");
          }
          var promise = events._internal.sendBoundary(
            boundarySourceRenderId(boundary),
            payload.handler,
            args,
            payload.type === "citry-poll"
              ? { recurring: boundary.key + ":" + clientBinding.key }
              : undefined,
            carrier || null,
            function () { return boundaryIsLive(boundary, carrier || null); },
            event || null
          );
          if (promise) promise.then(null, function () {});
        } catch (err) {
          console.error("[Citry] relocated Citry handler '" + clientBinding.key + "' failed:", err);
        }
      };
      if (payload.type === "citry-poll") {
        boundary.cleanups.push(group.poll(payload.interval, function (carrier) { dispatchCitry(null, carrier); }));
      } else {
        boundary.cleanups.push(group.on(payload.event, [], dispatchCitry, payload));
      }
    });
  };

  var captureBoundarySource = function (boundary, targetRoot, sourceOrigin) {
    if (boundary.destroyed || boundary.sourceCarrier) return;
    var sharedSourceRoot = targetRoot && (targetRoot.getAttribute("data-cid") || "")
      .trim()
      .split(/\s+/)
      .indexOf(boundarySourceRenderId(boundary)) !== -1;
    var origin = sourceOrigin || (
      targetRoot && (sharedSourceRoot ? targetRoot : targetRoot._x_teleportBack || targetRoot.parentElement || targetRoot)
    );
    if (origin && !origin.isConnected) return;
    // The target root can already carry a child-owned stack from an earlier
    // registry pass. The physical source origin is the lexical side of the
    // vanished component tag, so capture from it instead.
    var stack = origin ? alpineOwner.closestDataStack(origin).slice() : [];
    var sourceScope = boundary.sourceLifecycle.scope;
    if (sourceScope && stack.indexOf(sourceScope) === -1) stack.unshift(sourceScope);
    var carrier = document.createElement("span");
    carrier._x_dataStack = stack;
    if (origin) carrier._x_teleportBack = origin;
    boundary.sourceCarrier = carrier;
    boundary.sourceOrigin = origin;
    installBoundaryHandlers(boundary);
    installPropsSupplier(boundary);
  };

  var activateBoundariesForRoot = function (root) {
    if (!root || !root.getAttribute) return;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    ids.forEach(function (renderId) {
      (componentBoundariesByTarget.get(renderId) || []).forEach(function (boundary) {
        captureBoundarySource(boundary, root, null);
      });
    });
  };

  var activateRootlessBoundaries = function () {
    liveComponentBoundaries.forEach(function (boundary) {
      if (boundary.destroyed || boundary.sourceCarrier) return;
      if (!lifecycleCapsAreLive(boundary.targetLifecycle)) return;
      if (boundary.targetLifecycle.els.length) {
        var targetRoot = boundary.targetLifecycle.els.find(function (root) {
          return root.isConnected && root._x_marker;
        });
        if (targetRoot) captureBoundarySource(boundary, targetRoot, null);
        return;
      }
      var route = routeForLifecycle(boundary.targetLifecycle);
      var state = route && ownershipStates.get(route.revision);
      var physical = state && state.registry.physicalRegions.get(route.instance.key);
      var origin = physical && physical.start && physical.start.parentNode;
      if (origin instanceof Element) captureBoundarySource(boundary, null, origin);
      else if (physical && physical.topology === "document-body") captureBoundarySource(boundary, null, null);
    });
  };

  var adoptBoundaryEndpoint = function (state, renderId, provisionalLifecycle, adoptedLifecycle) {
    if (!state || !provisionalLifecycle || !adoptedLifecycle) return;
    Array.from(provisionalLifecycle.componentBoundaries).forEach(function (boundary) {
      if (boundary.revision !== state.publicRevision.revision) return;
      if (
        boundary.invocation.sourceRenderId === renderId &&
        boundary.sourceLifecycle === provisionalLifecycle
      ) {
        provisionalLifecycle.componentBoundaries.delete(boundary);
        boundary.sourceLifecycle = adoptedLifecycle;
        adoptedLifecycle.componentBoundaries.add(boundary);
      }
      if (
        boundary.invocation.targetRenderId === renderId &&
        boundary.targetLifecycle === provisionalLifecycle
      ) {
        provisionalLifecycle.componentBoundaries.delete(boundary);
        boundary.targetLifecycle = adoptedLifecycle;
        adoptedLifecycle.componentBoundaries.add(boundary);
      }
    });
  };

  var retireSupersededComponentBoundaries = function (state) {
    var incomingSources = new Set();
    state.renderLinks.forEach(function (link) {
      var lifecycle = link.link.active && link.logicalState.lifecycle;
      if (lifecycle) incomingSources.add(lifecycle);
    });
    Array.from(liveComponentBoundaries).forEach(function (candidate) {
      if (
        candidate.destroyed ||
        candidate.revision === state.publicRevision.revision ||
        (state.adoption.retainedOldRenderIds &&
          state.adoption.retainedOldRenderIds.has(candidate.invocation.targetRenderId)) ||
        !incomingSources.has(candidate.sourceLifecycle)
      ) return;
      var successor = null;
      state.registry.nestedComponents.values().forEach(function (invocation) {
        if (successor) return;
        var sourceLink = state.renderLinks.get(invocation.sourceRenderId);
        var targetLink = state.renderLinks.get(invocation.targetRenderId);
        if (
          sourceLink && targetLink &&
          sourceLink.link.active && targetLink.link.active &&
          sourceLink.logicalState.lifecycle === candidate.sourceLifecycle &&
          targetLink.logicalState.lifecycle === candidate.targetLifecycle
        ) successor = invocation;
      });
      var controller = candidate.targetLifecycle.propsController;
      destroyComponentBoundary(candidate);
      if (!controller) return;
      controller.sourceBoundary = null;
      controller.expectsSupply = Boolean(successor && successor.clientBindings.some(function (clientBinding) {
        return clientBinding.payload.type === "props";
      }));
      if (controller.expectsSupply) {
        controller.initialSettled = false;
        controller.currentValid = false;
      } else {
        // A compatible adoption creates its successor client binding later in the
        // same transaction. Do not emit a transient "required prop missing"
        // episode in that gap; settle no-supply only after boundary
        // reconciliation has had its microtask to attach a successor.
        queueMicrotask(function () {
          if (
            !candidate.targetLifecycle.active ||
            candidate.targetLifecycle.propsController !== controller ||
            controller.sourceBoundary ||
            propsBoundaryForLifecycle(candidate.targetLifecycle) ||
            lifecycleExpectsPropsSupply(candidate.targetLifecycle)
          ) return;
          controller.applyNoSupply();
          flushCalls();
        }, 0);
      }
    });
  };

  destroyComponentBoundary = function (boundary) {
    if (!boundary || boundary.destroyed) return;
    boundary.destroyed = true;
    boundary.cleanups.splice(0).forEach(function (cleanup) {
      try { cleanup(); } catch (_err) {}
    });
    if (
      boundary.targetLifecycle.propsController &&
      boundary.targetLifecycle.propsController.sourceBoundary === boundary
    ) {
      boundary.targetLifecycle.propsController.destroy();
    }
    boundary.sourceLifecycle.componentBoundaries.delete(boundary);
    boundary.targetLifecycle.componentBoundaries.delete(boundary);
    liveComponentBoundaries.delete(boundary);
    var targets = componentBoundariesByTarget.get(boundary.invocation.targetRenderId) || [];
    targets = targets.filter(function (candidate) { return candidate !== boundary; });
    if (targets.length) componentBoundariesByTarget.set(boundary.invocation.targetRenderId, targets);
    else componentBoundariesByTarget.delete(boundary.invocation.targetRenderId);
    boundary.sourceCarrier = null;
    boundary.sourceOrigin = null;
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var activateGraphClientBindings = function (revision, acceptedRenderIds) {
    var state = ownershipStates.get(revision);
    if (!state) return;
    state.registry.nestedComponents.values().forEach(function (invocation) {
      if (!invocation.clientBindings.length) return;
      if (
        acceptedRenderIds &&
        (!acceptedRenderIds.has(invocation.sourceRenderId) || !acceptedRenderIds.has(invocation.targetRenderId))
      ) return;
      var sourceLifecycle = null;
      var targetLifecycle = null;
      try {
        sourceLifecycle = ensureLifecycle(resolveOwnershipRoute(revision, invocation.sourceRenderId, null), true);
        targetLifecycle = ensureLifecycle(resolveOwnershipRoute(revision, invocation.targetRenderId, null), true);
      } catch (_err) {
        return;
      }
      if (!sourceLifecycle || !targetLifecycle) return;
      var boundary = {
        key: revision + ":" + invocation.key,
        revision: revision,
        invocation: invocation,
        sourceLifecycle: sourceLifecycle,
        targetLifecycle: targetLifecycle,
        sourceCarrier: null,
        sourceOrigin: null,
        cleanups: [],
        destroyed: false,
      };
      sourceLifecycle.componentBoundaries.add(boundary);
      targetLifecycle.componentBoundaries.add(boundary);
      liveComponentBoundaries.add(boundary);
      var targets = componentBoundariesByTarget.get(invocation.targetRenderId) || [];
      targets.push(boundary);
      componentBoundariesByTarget.set(invocation.targetRenderId, targets);
    });
  };

  registerAlpineProvider({
    root: function () { return "[data-citry-root]"; },
    beforeBoundary: activateBoundariesForRoot,
    init: function (el) {
      if (!el.hasAttribute || !el.hasAttribute("data-citry-root")) return;
      var lifecycle = innermostLifecycleForRoot(el);
      if (lifecycle && lifecycle.scope) isolateRootScope(el, lifecycle.scope);
    },
    mutations: function () {
      scheduleLifecycleReconcile();
      scheduleFillSourceReconcile();
      queueMicrotask(activateRootlessBoundaries);
    },
    afterStart: function () {
      reconcileComponentLifecycles();
      reconcileFillSources();
      activateRootlessBoundaries();
    },
  });

  var preflightEventsBridge = function (revision, entries) {
    return entries.map(function (entry) {
      var route = resolveOwnershipRoute(revision, entry.componentId, entry.classId);
      var link = ownershipStates.get(revision).renderLinks.get(entry.componentId);
      if (link.anchorState.events) {
        throw new TypeError("[Citry] graph: render id '" + entry.componentId + "' already has an Events anchor.");
      }
      return route;
    });
  };

  var attachEventsBridge = function (revision, renderId, classId, eventsAnchor) {
    var route = resolveOwnershipRoute(revision, renderId, classId);
    ensureLifecycle(route, true);
    var link = ownershipStates.get(revision).renderLinks.get(renderId);
    if (link.anchorState.events && link.anchorState.events !== eventsAnchor) {
      throw new TypeError("[Citry] graph: render id '" + renderId + "' already has an Events anchor.");
    }
    link.anchorState.events = eventsAnchor;
    return route.anchor;
  };

  var detachEventsBridge = function (generalAnchor, eventsAnchor) {
    if (!generalAnchor) return;
    ownershipStates.forEach(function (state) {
      state.renderLinks.forEach(function (link) {
        if (link.link.anchor === generalAnchor && link.anchorState.events === eventsAnchor) {
          link.anchorState.events = null;
        }
      });
    });
  };

  // A graph-backed adoption calls this while the incoming revision is private.
  // The explicit transaction transfers the stable anchor and, for a
  // same-class match, the logical lifecycle. The fallback below remains
  // for legacy Events responses that do not carry an ownership graph.
  var transitionEventsBridge = function (generalAnchor, renderId, classId) {
    if (!generalAnchor || typeof renderId !== "string" || typeof classId !== "string") return;
    var source = null;
    var target = null;
    ownershipStates.forEach(function (state, revision) {
      state.renderLinks.forEach(function (link) {
        if (!source && link.link.active && link.link.anchor === generalAnchor) {
          source = { revision: revision, link: link };
        }
      });
      var candidate = state.renderLinks.get(renderId);
      if (state.provisional && candidate && candidate.link.active && candidate.record.classId === classId) {
        target = { revision: revision, link: candidate };
      }
    });
    if (source && target && source.link !== target.link) {
      replaceOwnership([{
        fromRevision: source.revision,
        fromRenderId: source.link.record.renderId,
        toRevision: target.revision,
        toRenderId: target.link.record.renderId,
        preserveLogical: source.link.record.classId === target.link.record.classId,
      }]);
      return;
    }
    if (source && target && source.link === target.link) return;
    var lifecycle = null;
    ownershipStates.forEach(function (state) {
      if (lifecycle) return;
      state.renderLinks.forEach(function (link) {
        if (
          !lifecycle &&
          link.link.active &&
          link.link.anchor === generalAnchor &&
          link.logicalState.lifecycle &&
          link.logicalState.lifecycle.active
        ) {
          lifecycle = link.logicalState.lifecycle;
        }
      });
    });
    if (!lifecycle) return;
    if (lifecycle.classId !== classId) {
      destroyLifecycle(lifecycle, "an Events compatibility render changed component class");
      return;
    }
    if (lifecycle.compatRenderId) liveInstances.delete(lifecycle.compatRenderId);
    else liveInstances.delete(lifecycle.renderId);
    lifecycle.compatRenderId = renderId;
    liveInstances.set(renderId, classId);
    scheduleLifecycleReconcile();
  };

  var retireEventsBridge = function (generalAnchor) {
    if (!generalAnchor) return;
    var lifecycles = [];
    var retiredLinks = [];
    ownershipStates.forEach(function (state) {
      state.renderLinks.forEach(function (link) {
        var lifecycle = link.logicalState.lifecycle;
        if (
          link.link.active &&
          link.link.anchor === generalAnchor &&
          lifecycle &&
          lifecycle.active &&
          lifecycles.indexOf(lifecycle) === -1
        ) {
          lifecycles.push(lifecycle);
        }
        if (link.link.active && link.link.anchor === generalAnchor) retiredLinks.push({ state: state, link: link });
      });
    });
    lifecycles.forEach(function (lifecycle) {
      destroyLifecycle(lifecycle, "its Events anchor was retired");
    });
    retiredLinks.forEach(function (retired) {
      var link = retired.link;
      physicalRangesForKey(retired.state, link.record.key).forEach(function (physical) {
        if (
          physical.start.data === physical.startMarker &&
          physical.end.data === physical.endMarker
        ) {
          physical.start.remove();
          physical.end.remove();
        }
      });
      deactivateRenderLink(retired.state, link);
    });
  };

  var isOwnershipAnchorLive = function (generalAnchor) {
    if (!generalAnchor || !generalAnchor.active) return false;
    var live = false;
    ownershipStates.forEach(function (state) {
      if (live) return;
      state.renderLinks.forEach(function (link) {
        if (live || !link.link.active || link.link.anchor !== generalAnchor) return;
        var lifecycle = link.logicalState.lifecycle;
        if (
          lifecycle &&
          lifecycle.active &&
          lifecycle.compatRenderId &&
          document.querySelector("[data-cid-" + lifecycle.compatRenderId + "]")
        ) {
          live = true;
          return;
        }
        live = physicalRangesForKey(state, link.record.key).some(function (physical) {
          return physicalRangeIsLive(state, physical);
        });
      });
    });
    return live;
  };

  var livePhysicalPlacementsForAnchor = function (generalAnchor) {
    var placements = [];
    ownershipStates.forEach(function (state, revision) {
      if (!ownershipGraphs.has(revision)) return;
      state.renderLinks.forEach(function (link) {
        if (!link.link.active || link.link.anchor !== generalAnchor) return;
        physicalRangesForKey(state, link.record.key).forEach(function (physical) {
          if (!physicalRangeIsLive(state, physical)) {
            throw new TypeError(
              "[Citry] ownership transaction rejected because one physical placement of shared range '" +
                physical.key + "' is missing or corrupt."
            );
          }
          placements.push({ physical: physical, link: link });
        });
      });
    });
    return placements;
  };

  var activeCommittedLink = function (renderId) {
    var found = null;
    ownershipStates.forEach(function (state, revision) {
      if (found || !ownershipGraphs.has(revision)) return;
      var link = state.renderLinks.get(renderId);
      if (link && link.link.active) found = { revision: revision, state: state, link: link };
    });
    return found;
  };

  var componentRangeIdentity = function (link) {
    return JSON.stringify([link.record.classId, link.logicalState.morphKey]);
  };

  var ownershipPlanningMatches = function (plan) {
    var pooled = new Map();
    [plan.candidateMatches || [], plan.discoveredMatches || [], plan.matches || []].forEach(function (matches) {
      matches.forEach(function (match) {
        pooled.set(match.fromRenderId + "\n" + match.toRenderId, match);
      });
    });
    return Array.from(pooled.values());
  };

  // Historical candidates remain available only to close retention over the
  // incoming endpoint they originally corresponded with. Physical planning
  // must use the latest recomputed correspondence plus explicit retained
  // pairs; otherwise an endpoint removed by ignore closure can re-enter the
  // ordinary planner and retain descendants of a range final matching replaces.
  var physicalPlanningMatches = function (plan) {
    var pooled = new Map();
    [plan.matches || [], plan.retainedMatches || []].forEach(function (matches) {
      matches.forEach(function (match) {
        pooled.set(match.fromRenderId + "\n" + match.toRenderId, match);
      });
    });
    return Array.from(pooled.values());
  };

  var directLogicalChildren = function (parentLogical, provisionalState) {
    var found = [];
    var collect = function (state, revision) {
      state.renderLinks.forEach(function (link) {
        if (
          link.link.active &&
          link.logicalState.parentLogical === parentLogical
        ) found.push({ revision: revision, state: state, link: link });
      });
    };
    if (provisionalState) {
      collect(provisionalState, provisionalState.publicRevision.revision);
    } else {
      ownershipStates.forEach(function (state, revision) {
        if (ownershipGraphs.has(revision)) collect(state, revision);
      });
    }
    var order = [];
    var states = provisionalState
      ? [[provisionalState.publicRevision.revision, provisionalState]]
      : Array.from(ownershipStates.entries()).filter(function (entry) { return ownershipGraphs.has(entry[0]); });
    states.some(function (entry) {
      var parentLink = Array.from(entry[1].renderLinks.values()).find(function (link) {
        return link.link.active && link.link.logical === parentLogical;
      });
      if (!parentLink) return false;
      order = parentLink.logicalState.childOrder.slice();
      return true;
    });
    var orderIndex = new Map();
    order.forEach(function (renderId, index) { orderIndex.set(renderId, index); });
    found.sort(function (left, right) {
      var leftIndex = orderIndex.has(left.link.record.renderId)
        ? orderIndex.get(left.link.record.renderId)
        : Number.MAX_SAFE_INTEGER;
      var rightIndex = orderIndex.has(right.link.record.renderId)
        ? orderIndex.get(right.link.record.renderId)
        : Number.MAX_SAFE_INTEGER;
      return leftIndex - rightIndex;
    });
    return found;
  };

  // Build the complete virtual-component correspondence without mutating
  // either revision. Explicitly addressed roots correlate first. Their direct
  // logical children then match top-down by (class, non-null key); an
  // unmatched component is opaque, so its descendants never leak outward.
  var planOwnershipAdoption = function (transaction, explicitRoots, options) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    if (!Array.isArray(explicitRoots)) {
      throw new TypeError("[Citry] graph: ownership adoption roots must be an array.");
    }
    var targetState = transaction.state;
    options = options || {};
    var matches = [];
    var replacements = [];
    var usedOld = new Set();
    var usedNew = new Set();

    var addPair = function (oldEntry, newEntry, explicit, parentMatch) {
      var oldId = oldEntry.link.record.renderId;
      var newId = newEntry.link.record.renderId;
      if (usedOld.has(oldId) || usedNew.has(newId)) {
        throw new TypeError("[Citry] graph: component range correspondence repeats an endpoint.");
      }
      usedOld.add(oldId);
      usedNew.add(newId);
      var preserveLogical = oldEntry.link.record.classId === newEntry.link.record.classId;
      var preserveExternalParent = Boolean(
        explicit &&
        preserveLogical &&
        newEntry.link.record.parentRenderId == null &&
        oldEntry.link.logicalState.parentLogical
      );
      replacements.push({
        fromRevision: oldEntry.revision,
        fromRenderId: oldId,
        toRevision: transaction.revision,
        toRenderId: newId,
        preserveLogical: preserveLogical,
        preserveExternalParent: preserveExternalParent,
      });
      matches.push({
        fromRevision: oldEntry.revision,
        fromRenderId: oldId,
        fromKey: oldEntry.link.record.key,
        toRevision: transaction.revision,
        toRenderId: newId,
        toKey: newEntry.link.record.key,
        preserveLogical: preserveLogical,
        preserveExternalParent: preserveExternalParent,
        parentFromRenderId: parentMatch ? parentMatch.fromRenderId : null,
        parentToRenderId: parentMatch ? parentMatch.toRenderId : null,
      });
      var currentMatch = matches[matches.length - 1];
      if (!preserveLogical) return;

      var oldChildren = directLogicalChildren(oldEntry.link.logicalState, null);
      var newChildren = directLogicalChildren(newEntry.link.logicalState, targetState);
      // Physical morphing runs after logical transfer deactivates the source
      // endpoints. Freeze each parent's direct-child order into the read-only
      // plan so the connected-range classifier never consults mutated state.
      currentMatch.oldDirectChildren = oldChildren.map(function (child) {
        return { revision: child.revision, key: child.link.record.key };
      });
      currentMatch.newDirectChildren = newChildren.map(function (child) {
        return { revision: child.revision, key: child.link.record.key };
      });
      var oldByIdentity = new Map();
      oldChildren.forEach(function (child) {
        if (child.link.logicalState.morphKey === null) return;
        var identity = componentRangeIdentity(child.link);
        var queue = oldByIdentity.get(identity) || [];
        queue.push(child);
        oldByIdentity.set(identity, queue);
      });
      newChildren.forEach(function (child) {
        if (child.link.logicalState.morphKey === null) return;
        var identity = componentRangeIdentity(child.link);
        var queue = oldByIdentity.get(identity);
        if (!queue || !queue.length) return;
        addPair(queue.shift(), child, false, currentMatch);
      });
      var remainingOld = oldChildren.filter(function (child) {
        return !usedOld.has(child.link.record.renderId);
      });
      var remainingNew = newChildren.filter(function (child) {
        return !usedNew.has(child.link.record.renderId);
      });
      var positionalLength = Math.max(remainingOld.length, remainingNew.length);
      for (var position = 0; position < positionalLength; position += 1) {
        var oldChild = remainingOld[position];
        var newChild = remainingNew[position];
        if (!oldChild || !newChild) continue;
        if (
          oldChild.link.logicalState.morphKey === null &&
          newChild.link.logicalState.morphKey === null &&
          oldChild.link.record.classId === newChild.link.record.classId
        ) addPair(oldChild, newChild, false, currentMatch);
      }
    };

    explicitRoots.forEach(function (root, index) {
      if (!root || typeof root !== "object") {
        throw new TypeError("[Citry] graph: explicit adoption root[" + index + "] must be an object.");
      }
      var oldEntry = activeCommittedLink(root.fromRenderId);
      var newLink = targetState.renderLinks.get(root.toRenderId);
      if (!oldEntry || !newLink || !newLink.link.active) {
        throw new TypeError("[Citry] graph: explicit adoption root is unknown or inactive.");
      }
      addPair(oldEntry, { revision: transaction.revision, state: targetState, link: newLink }, true, null);
    });

    var plan = {
      transaction: transaction,
      state: targetState,
      matches: matches,
      candidateMatches: matches.slice(),
      discoveredMatches: matches.slice(),
      replacements: replacements,
      candidateReplacements: replacements.slice(),
      retainedOldRenderIds: new Set(),
      pinnedOldRenderIds: new Set(),
      unmatchedOldRenderIds: new Set(),
      unmatchedIncomingRenderIds: new Set(),
      excludedIncomingRenderIds: new Set(),
      retainedOldPhysicalRecords: new Set(),
      pinnedOldPhysicalRecords: new Set(),
      excludedIncomingPhysicalKeys: new Set(),
      candidateSlotMatches: [],
      ordinaryPairs: [],
      ordinaryAdditions: [],
      ordinaryRemovals: [],
      acceptedIncomingRenderIds: new Set(targetState.renderLinks.keys()),
      retainedRootFromRenderIds: new Set(),
      warnedDuplicateComponentKeys: new Set(),
      applied: false,
    };
    if (!options.bypassIgnore) {
      matches.forEach(function (match) {
        var oldEntry = activeCommittedLink(match.fromRenderId);
        // A nested ignored range is retained only when the ancestor-ordered
        // physical walk reaches its atom through matched ordinary ancestors.
        // Seeding it here would let a keyed atom escape a replaced wrapper.
        // The explicit root has no enclosing ordinary ancestor in this
        // planning window, so its policy is known immediately.
        if (
          match.parentFromRenderId === null &&
          match.preserveLogical &&
          oldEntry &&
          oldEntry.link.logicalState.morphMode === "ignore"
        ) {
          plan.retainedOldRenderIds.add(match.fromRenderId);
          if (match.parentFromRenderId === null) plan.retainedRootFromRenderIds.add(match.fromRenderId);
        }
      });
    }
    applyOwnershipRetentionClosure(plan, plan.retainedOldRenderIds);
    transaction.plan = plan;
    return plan;
  };

  var addIncomingSubtreeToExclusion = function (plan, renderId) {
    var queue = [renderId];
    while (queue.length) {
      var current = queue.shift();
      if (plan.excludedIncomingRenderIds.has(current)) continue;
      plan.excludedIncomingRenderIds.add(current);
      plan.acceptedIncomingRenderIds.delete(current);
      (plan.state.childrenByParent.get(current) || []).forEach(function (child) { queue.push(child); });
    }
  };

  var recomputeActiveOwnershipMatches = function (plan) {
    var matches = [];
    var replacements = [];
    var usedOld = new Set();
    var usedNew = new Set();
    var targetState = plan.state;

    var availableOld = function (entry) {
      return entry && entry.link.link.active &&
        !plan.retainedOldRenderIds.has(entry.link.record.renderId) &&
        !plan.unmatchedOldRenderIds.has(entry.link.record.renderId) &&
        !usedOld.has(entry.link.record.renderId);
    };
    var availableNew = function (entry) {
      return entry && entry.link.link.active &&
        !plan.excludedIncomingRenderIds.has(entry.link.record.renderId) &&
        !plan.unmatchedIncomingRenderIds.has(entry.link.record.renderId) &&
        !usedNew.has(entry.link.record.renderId);
    };
    var addPair = function (oldEntry, newEntry, explicit, parentMatch) {
      if (!availableOld(oldEntry) || !availableNew(newEntry)) return;
      var oldId = oldEntry.link.record.renderId;
      var newId = newEntry.link.record.renderId;
      usedOld.add(oldId);
      usedNew.add(newId);
      var preserveLogical = oldEntry.link.record.classId === newEntry.link.record.classId;
      var preserveExternalParent = Boolean(
        explicit && preserveLogical && newEntry.link.record.parentRenderId == null && oldEntry.link.logicalState.parentLogical
      );
      var match = {
        fromRevision: oldEntry.revision,
        fromRenderId: oldId,
        fromKey: oldEntry.link.record.key,
        toRevision: plan.transaction.revision,
        toRenderId: newId,
        toKey: newEntry.link.record.key,
        preserveLogical: preserveLogical,
        preserveExternalParent: preserveExternalParent,
        parentFromRenderId: parentMatch ? parentMatch.fromRenderId : null,
        parentToRenderId: parentMatch ? parentMatch.toRenderId : null,
      };
      matches.push(match);
      replacements.push({
        fromRevision: oldEntry.revision,
        fromRenderId: oldId,
        toRevision: plan.transaction.revision,
        toRenderId: newId,
        preserveLogical: preserveLogical,
        preserveExternalParent: preserveExternalParent,
      });
      if (!preserveLogical) return;

      var oldChildren = directLogicalChildren(oldEntry.link.logicalState, null);
      var newChildren = directLogicalChildren(newEntry.link.logicalState, targetState);
      match.oldDirectChildren = oldChildren.map(function (child) {
        return { revision: child.revision, key: child.link.record.key };
      });
      match.newDirectChildren = newChildren.map(function (child) {
        return { revision: child.revision, key: child.link.record.key };
      });

      var oldByIdentity = new Map();
      oldChildren.forEach(function (child) {
        if (!availableOld(child) || child.link.logicalState.morphKey === null) return;
        var identity = componentRangeIdentity(child.link);
        var queue = oldByIdentity.get(identity) || [];
        queue.push(child);
        oldByIdentity.set(identity, queue);
      });
      newChildren.forEach(function (child) {
        if (!availableNew(child) || child.link.logicalState.morphKey === null) return;
        var queue = oldByIdentity.get(componentRangeIdentity(child.link));
        if (queue && queue.length) addPair(queue.shift(), child, false, match);
      });

      var remainingOld = oldChildren.filter(availableOld);
      var remainingNew = newChildren.filter(availableNew);
      var positionalLength = Math.max(remainingOld.length, remainingNew.length);
      for (var position = 0; position < positionalLength; position += 1) {
        var oldChild = remainingOld[position];
        var newChild = remainingNew[position];
        if (!oldChild || !newChild) continue;
        if (
          oldChild.link.logicalState.morphKey === null &&
          newChild.link.logicalState.morphKey === null &&
          oldChild.link.record.classId === newChild.link.record.classId
        ) addPair(oldChild, newChild, false, match);
      }
    };

    (plan.candidateMatches || []).filter(function (match) {
      return match.parentFromRenderId === null && match.parentToRenderId === null;
    }).forEach(function (root) {
      var oldEntry = activeCommittedLink(root.fromRenderId);
      var newLink = targetState.renderLinks.get(root.toRenderId);
      if (oldEntry && newLink) {
        addPair(oldEntry, { revision: plan.transaction.revision, state: targetState, link: newLink }, true, null);
      }
    });
    matches.forEach(function (match) {
      if (!(plan.discoveredMatches || []).some(function (candidate) {
        return candidate.fromRenderId === match.fromRenderId && candidate.toRenderId === match.toRenderId;
      })) plan.discoveredMatches.push(match);
    });
    plan.matches = matches;
    plan.replacements = replacements;
  };

  var retainOldSlotGroup = function (plan, revision, key, pinned) {
    var state = ownershipStates.get(revision);
    var region = state && state.registry.slotRegions.get(key);
    if (!state || !region) return;
    var fillKey = qualifiedGraphId(region.graphId, "f", region.fillId);
    var group = state.registry.rangeGroups.get(fillKey);
    (group ? group.slotRegions : [region]).forEach(function (sharedRegion) {
      var identity = revision + "\n" + sharedRegion.key;
      plan.retainedOldPhysicalRecords.add(identity);
      if (pinned && sharedRegion.key === key) plan.pinnedOldPhysicalRecords.add(identity);
    });
  };

  var excludeIncomingSlotGroup = function (plan, key) {
    var region = plan.state.registry.slotRegions.get(key);
    if (!region) return;
    var fillKey = qualifiedGraphId(region.graphId, "f", region.fillId);
    var group = plan.state.registry.rangeGroups.get(fillKey);
    (group ? group.slotRegions : [region]).forEach(function (sharedRegion) {
      plan.excludedIncomingPhysicalKeys.add(sharedRegion.key);
    });
  };

  function applyOwnershipRetentionClosure(plan, retainedSeeds, pinnedSeeds) {
    var matchByOld = new Map();
    ownershipPlanningMatches(plan).forEach(function (match) { matchByOld.set(match.fromRenderId, match); });
    var queue = Array.from(retainedSeeds || []);
    var expanded = new Set();
    while (queue.length) {
      var renderId = queue.shift();
      if (expanded.has(renderId)) continue;
      expanded.add(renderId);
      plan.retainedOldRenderIds.add(renderId);
      if (pinnedSeeds && pinnedSeeds.has(renderId)) plan.pinnedOldRenderIds.add(renderId);
      var oldEntry = activeCommittedLink(renderId);
      if (oldEntry) {
        directLogicalChildren(oldEntry.link.logicalState, null).forEach(function (child) {
          var childId = child.link.record.renderId;
          if (plan.pinnedOldRenderIds.has(renderId)) plan.pinnedOldRenderIds.add(childId);
          if (!expanded.has(childId)) queue.push(childId);
        });
      }
      var match = matchByOld.get(renderId);
      if (match) addIncomingSubtreeToExclusion(plan, match.toRenderId);
    }
    Array.from(plan.retainedOldPhysicalRecords).forEach(function (identity) {
      var separator = identity.indexOf("\n");
      if (separator < 0) return;
      retainOldSlotGroup(plan, identity.slice(0, separator), identity.slice(separator + 1), false);
    });
    plan.retainedOldPhysicalRecords.forEach(function (identity) {
      plan.candidateSlotMatches.filter(function (candidate) {
        return candidate.fromRevision + "\n" + candidate.fromKey === identity;
      }).forEach(function (slotMatch) {
        excludeIncomingSlotGroup(plan, slotMatch.toKey);
      });
    });
    plan.retainedCorrespondences = ownershipPlanningMatches(plan).filter(function (match) {
      return (
        match.preserveLogical &&
        plan.retainedOldRenderIds.has(match.fromRenderId) &&
        plan.excludedIncomingRenderIds.has(match.toRenderId)
      );
    });
    plan.retainedMatches = plan.retainedCorrespondences.map(function (match) {
      return Object.assign({}, match, { retained: true });
    });
    plan.retainedSlotMatches = plan.candidateSlotMatches.filter(function (match) {
      return plan.retainedOldPhysicalRecords.has(match.fromRevision + "\n" + match.fromKey) &&
        plan.excludedIncomingPhysicalKeys.has(match.toKey);
    });
    recomputeActiveOwnershipMatches(plan);
    return plan;
  }

  var clonePlanningNode = function (source, planningDocument) {
    var clone;
    if (source.nodeType === Node.ELEMENT_NODE) {
      clone = planningDocument.createElementNS(source.namespaceURI, source.localName);
      Array.prototype.slice.call(source.attributes || []).forEach(function (attribute) {
        clone.setAttributeNodeNS(planningDocument.importNode(attribute, true));
      });
    } else if (source.nodeType === Node.TEXT_NODE) {
      clone = planningDocument.createTextNode(source.data);
    } else if (source.nodeType === Node.COMMENT_NODE) {
      clone = planningDocument.createComment(source.data);
    } else {
      clone = planningDocument.importNode(source, false);
    }
    clone._citryPlanningSource = source;
    if (source._x_bindings) clone._x_bindings = source._x_bindings;
    Array.prototype.slice.call(source.childNodes || []).forEach(function (child) {
      clone.appendChild(clonePlanningNode(child, planningDocument));
    });
    return clone;
  };

  var clonePlanningBoundary = function (boundary) {
    var planningDocument = document.implementation.createHTMLDocument("");
    var container = planningDocument.createElement("div");
    var nodes;
    if (boundary.topology === "document-body") {
      nodes = [];
      for (var documentNode = boundary.start.nextSibling;
        documentNode && documentNode !== document.documentElement;
        documentNode = documentNode.nextSibling) nodes.push(documentNode);
      for (var bodyNode = document.body.firstChild;
        bodyNode && bodyNode !== boundary.end;
        bodyNode = bodyNode.nextSibling) nodes.push(bodyNode);
    } else {
      nodes = boundary.start && boundary.end
        ? nodesInsidePair(boundary)
        : Array.prototype.slice.call(boundary.childNodes || []);
    }
    nodes.forEach(function (node) { container.appendChild(clonePlanningNode(node, planningDocument)); });
    return container;
  };

  var replacePlanningRange = function (pair, token) {
    if (!pair.start.parentNode || pair.start.parentNode !== pair.end.parentNode) return;
    var atom = document.createElement("template");
    atom.setAttribute("data-citry-planning-range", token);
    pair.start.before(atom);
    for (var node = pair.start; node;) {
      var next = node.nextSibling;
      node.remove();
      if (node === pair.end) break;
      node = next;
    }
  };

  var atomizePlanningRanges = function (plan, oldContainer, newContainer, options) {
    var oldPairs = rangePairsUnder(oldContainer, null);
    var newPairs = rangePairsUnder(newContainer, null);
    var oldTokens = new Map();
    var newTokens = new Map();
    var candidateMatches = physicalPlanningMatches(plan);
    var oldComponentMatches = new Map();
    var newComponentMatches = new Map();
    candidateMatches.forEach(function (match) {
      oldComponentMatches.set(match.fromRevision + "\n" + match.fromKey, match);
      newComponentMatches.set(match.toRevision + "\n" + match.toKey, match);
    });
    oldPairs.forEach(function (pair) {
      var match = oldComponentMatches.get(pair.revision + "\n" + pair.recordKey);
      if (match) oldTokens.set(pair, "component:" + match.fromRenderId + ":" + match.toRenderId);
    });
    newPairs.forEach(function (pair) {
      var match = newComponentMatches.get(pair.revision + "\n" + pair.recordKey);
      if (match) newTokens.set(pair, "component:" + match.fromRenderId + ":" + match.toRenderId);
    });

    var oldRegionsByIdentity = new Map();
    directSlotRegionPairs(oldPairs).forEach(function (pair) {
      var identity = slotRegionIdentity(pair, oldContainer, options, oldPairs);
      if (identity === null) return;
      var queue = oldRegionsByIdentity.get(identity) || [];
      queue.push(pair);
      oldRegionsByIdentity.set(identity, queue);
    });
    directSlotRegionPairs(newPairs).forEach(function (newPair) {
      var identity = slotRegionIdentity(newPair, newContainer, options, newPairs);
      var queue = identity === null ? null : oldRegionsByIdentity.get(identity);
      if (!queue || !queue.length) return;
      var oldPair = queue.shift();
      var token = "slot:" + oldPair.revision + ":" + oldPair.recordKey + ":" + newPair.recordKey;
      oldTokens.set(oldPair, token);
      newTokens.set(newPair, token);
      if (!plan.candidateSlotMatches.some(function (candidate) {
        return candidate.fromRevision === oldPair.revision &&
          candidate.fromKey === oldPair.recordKey && candidate.toKey === newPair.recordKey;
      })) {
        plan.candidateSlotMatches.push({
          fromRevision: oldPair.revision,
          fromKey: oldPair.recordKey,
          toRevision: newPair.revision,
          toKey: newPair.recordKey,
        });
      }
    });

    var replaceAll = function (pairs, tokens, side) {
      pairs.slice().sort(function (left, right) {
        return pairContainsPair(left, right) ? -1 : pairContainsPair(right, left) ? 1 : 0;
      }).forEach(function (pair) {
        replacePlanningRange(
          pair,
          tokens.get(pair) || side + ":" + pair.revision + ":" + pair.recordKey
        );
      });
    };
    replaceAll(oldPairs, oldTokens, "old");
    replaceAll(newPairs, newTokens, "new");
  };

  var collectOldBarrierRecords = function (plan, element, retainedSeeds, pinnedSeeds) {
    ownershipStates.forEach(function (state, revision) {
      if (!ownershipGraphs.has(revision)) return;
      state.physicalPlacements.forEach(function (placements, key) {
        if (!placements.some(function (physical) {
          return physicalRangeIsLive(state, physical) &&
            element.contains(physical.start) && element.contains(physical.end);
        })) return;
        var instance = state.registry.componentInstances.get(key);
        if (instance) {
          retainedSeeds.add(instance.renderId);
          pinnedSeeds.add(instance.renderId);
          return;
        }
        if (state.registry.slotRegions.get(key)) {
          retainOldSlotGroup(plan, revision, key, true);
        }
      });
    });
  };

  var collectIncomingBarrierRecords = function (plan, element) {
    rangePairsUnder(element, null).forEach(function (pair) {
      var instance = plan.state.registry.componentInstances.get(pair.recordKey);
      if (instance) {
        addIncomingSubtreeToExclusion(plan, instance.renderId);
        return;
      }
      if (plan.state.registry.slotRegions.get(pair.recordKey)) {
        excludeIncomingSlotGroup(plan, pair.recordKey);
      }
    });
  };

  var planOrdinaryBarrierPairs = function (
    plan,
    oldBoundary,
    newBoundary,
    options,
    retainedSeeds,
    pinnedSeeds
  ) {
    if (!alpineOwner || typeof alpineOwner._citryPlanBetween !== "function") {
      throw pointedAlpineError("the pinned morph planner is unavailable.");
    }
    var oldContainer = clonePlanningBoundary(oldBoundary);
    var newContainer = clonePlanningBoundary(newBoundary);
    atomizePlanningRanges(plan, oldContainer, newContainer, options);
    var ordinaryAncestorsMatched = function (from, to) {
      var oldAncestor = from.parentElement;
      var newAncestor = to.parentElement;
      while (oldAncestor !== oldContainer || newAncestor !== newContainer) {
        if (!oldAncestor || !newAncestor || oldAncestor === oldContainer || newAncestor === newContainer) {
          return false;
        }
        var oldSource = oldAncestor._citryPlanningSource || oldAncestor;
        var newSource = newAncestor._citryPlanningSource || newAncestor;
        if (!plan.ordinaryPairs.some(function (pair) {
          return pair.from === oldSource && pair.to === newSource;
        })) return false;
        oldAncestor = oldAncestor.parentElement;
        newAncestor = newAncestor.parentElement;
      }
      return true;
    };
    alpineOwner._citryPlanBetween(oldContainer, newContainer, {
      key: function (element) {
        return element.getAttribute("data-citry-planning-range") || plannedElementKey(element, options);
      },
      updating: function (from, to, _childrenOnly, skip) {
        var oldElement = from && from._citryPlanningSource;
        var incomingElement = to && to._citryPlanningSource;
        plan.ordinaryPairs.push({ from: oldElement || from, to: incomingElement || to });
        var rangeToken = from && from.getAttribute && from.getAttribute("data-citry-planning-range");
        if (rangeToken && rangeToken.indexOf("component:") === 0) {
          var rangeMatch = physicalPlanningMatches(plan).find(function (candidate) {
            return rangeToken === "component:" + candidate.fromRenderId + ":" + candidate.toRenderId;
          });
          var oldRange = rangeMatch && activeCommittedLink(rangeMatch.fromRenderId);
          if (
            rangeMatch &&
            oldRange &&
            oldRange.link.logicalState.morphMode === "ignore"
          ) {
            if (ordinaryAncestorsMatched(from, to)) {
              retainedSeeds.add(rangeMatch.fromRenderId);
              skip();
            } else {
              // An ignored range may move through matched wrappers, but an
              // unmatched ancestor replaces the complete old branch. Reserve
              // both endpoints so final rematching cannot recreate the pair.
              plan.unmatchedOldRenderIds.add(rangeMatch.fromRenderId);
              plan.unmatchedIncomingRenderIds.add(rangeMatch.toRenderId);
            }
          }
          return;
        }
        if (
          !(oldElement instanceof Element) || !(incomingElement instanceof Element) ||
          oldElement.getAttribute("data-citry-morph") !== "ignore"
        ) return;
        collectOldBarrierRecords(plan, oldElement, retainedSeeds, pinnedSeeds);
        collectIncomingBarrierRecords(plan, incomingElement);
        skip();
      },
      adding: function (node) {
        plan.ordinaryAdditions.push(node._citryPlanningSource || node);
      },
      removing: function (node) {
        plan.ordinaryRemovals.push(node._citryPlanningSource || node);
      },
    });
    physicalPlanningMatches(plan).forEach(function (rangeMatch) {
      if (rangeMatch.parentFromRenderId === null || plan.retainedOldRenderIds.has(rangeMatch.fromRenderId)) return;
      var oldRange = activeCommittedLink(rangeMatch.fromRenderId);
      if (!oldRange || oldRange.link.logicalState.morphMode !== "ignore") return;
      var oldState = ownershipStates.get(rangeMatch.fromRevision);
      var oldPhysical = oldState && physicalRangesForKey(oldState, rangeMatch.fromKey).find(function (physical) {
        return physicalRangeIsLive(oldState, physical) &&
          physicalRangeContainsNode(oldBoundary, physical.start) &&
          physicalRangeContainsNode(oldBoundary, physical.end);
      });
      if (!oldPhysical) return;
      var boundaryParent = oldBoundary.start ? oldBoundary.start.parentNode : oldBoundary;
      var oldAncestor = oldPhysical.start.parentElement;
      var unmatchedAncestor = false;
      while (oldAncestor && oldAncestor !== boundaryParent) {
        if (!plan.ordinaryPairs.some(function (pair) { return pair.from === oldAncestor; })) {
          unmatchedAncestor = true;
          break;
        }
        oldAncestor = oldAncestor.parentElement;
      }
      if (!unmatchedAncestor) return;
      plan.unmatchedOldRenderIds.add(rangeMatch.fromRenderId);
      plan.unmatchedIncomingRenderIds.add(rangeMatch.toRenderId);
    });
  };

  var selectAnchorPhysicalPlacement = function (generalAnchor, index) {
    var selected = null;
    ownershipStates.forEach(function (state, revision) {
      if (selected || !ownershipGraphs.has(revision)) return;
      state.renderLinks.forEach(function (link) {
        if (selected || !link.link.active || link.link.anchor !== generalAnchor) return;
        var placements = physicalRangesForKey(state, link.record.key).filter(function (physical) {
          return physicalRangeIsLive(state, physical);
        });
        if (placements[index]) selected = { state: state, revision: revision, link: link, physical: placements[index] };
      });
    });
    return selected;
  };

  var warnDuplicateActiveComponentKeys = function (plan) {
    (plan.matches || []).forEach(function (parentMatch) {
      if (!parentMatch.preserveLogical) return;
      var oldParent = activeCommittedLink(parentMatch.fromRenderId);
      var newParent = plan.state.renderLinks.get(parentMatch.toRenderId);
      if (!oldParent || !newParent) return;
      var oldCounts = new Map();
      var newCounts = new Map();
      directLogicalChildren(oldParent.link.logicalState, null).forEach(function (child) {
        if (
          child.link.logicalState.morphKey === null ||
          plan.retainedOldRenderIds.has(child.link.record.renderId) ||
          plan.unmatchedOldRenderIds.has(child.link.record.renderId)
        ) return;
        var identity = componentRangeIdentity(child.link);
        oldCounts.set(identity, (oldCounts.get(identity) || 0) + 1);
      });
      directLogicalChildren(newParent.logicalState, plan.state).forEach(function (child) {
        if (
          child.link.logicalState.morphKey === null ||
          plan.excludedIncomingRenderIds.has(child.link.record.renderId) ||
          plan.unmatchedIncomingRenderIds.has(child.link.record.renderId)
        ) return;
        var identity = componentRangeIdentity(child.link);
        newCounts.set(identity, (newCounts.get(identity) || 0) + 1);
      });
      oldCounts.forEach(function (oldCount, identity) {
        var newCount = newCounts.get(identity) || 0;
        if (!newCount || (oldCount < 2 && newCount < 2)) return;
        var warningKey = parentMatch.fromRenderId + "\n" + parentMatch.toRenderId + "\n" + identity;
        if (plan.warnedDuplicateComponentKeys.has(warningKey)) return;
        plan.warnedDuplicateComponentKeys.add(warningKey);
        console.warn(
          "[Citry] graph: duplicate component key " + identity +
            " among one logical parent's direct children; matched in invocation order."
        );
      });
    });
  };

  var planOwnershipPlacement = function (plan, generalAnchor, index, html, options) {
    if (!plan || !plan.transaction || plan.transaction.status !== "prepared" || plan.applied) {
      throw new TypeError("[Citry] graph: ownership adoption plan is not ready for physical planning.");
    }
    var selected = selectAnchorPhysicalPlacement(generalAnchor, index);
    if (!selected) throw new TypeError("[Citry] graph: physical planning target is not live.");
    options = options || {};
    var fresh;
    if (selected.physical.topology === "document-body") {
      var range = document.createRange();
      range.selectNodeContents(document.body);
      range.collapse(true);
      fresh = document.createElement("div");
      fresh.append(range.createContextualFragment(html));
    } else {
      fresh = contextualRangeContainer(selected.physical.start, selected.physical.end, html);
    }
    var freshPairs = rangePairsUnder(fresh, null);
    var retainedSeeds = new Set(plan.retainedOldRenderIds);
    var pinnedSeeds = new Set(plan.pinnedOldRenderIds);
    var matchSignature = function () {
      return (plan.matches || []).map(function (match) {
        return match.fromRenderId + "\n" + match.toRenderId;
      }).sort().join("\n\n");
    };
    var stable = false;
    var iterationLimit = plan.state.renderLinks.size * 2 + ownershipPlanningMatches(plan).length + 4;
    for (var iteration = 0; iteration < iterationLimit; iteration += 1) {
      var signatureBefore = matchSignature();
      var candidateMatches = physicalPlanningMatches(plan);
      var rootMatch = candidateMatches.find(function (match) {
        return match.fromRenderId === selected.link.record.renderId;
      });
      if (!rootMatch || !rootMatch.preserveLogical) return plan;
      var matchedBoundaries = [{
        match: rootMatch,
        oldBoundary: selected.physical,
        newBoundary: fresh,
      }];
      candidateMatches.forEach(function (match) {
        if (match === rootMatch || !match.preserveLogical) return;
        var oldState = ownershipStates.get(match.fromRevision);
        var oldPhysical = oldState && physicalRangesForKey(oldState, match.fromKey).find(function (physical) {
          return (
            physicalRangeIsLive(oldState, physical) &&
            physicalRangeContainsNode(selected.physical, physical.start) &&
            physicalRangeContainsNode(selected.physical, physical.end)
          );
        });
        var newPair = pairForRecord(freshPairs, match.toRevision, match.toKey);
        if (oldPhysical && newPair) {
          matchedBoundaries.push({ match: match, oldBoundary: oldPhysical, newBoundary: newPair });
        }
      });
      matchedBoundaries.sort(function (left, right) {
        return pairContainsPair(left.oldBoundary, right.oldBoundary)
          ? -1
          : pairContainsPair(right.oldBoundary, left.oldBoundary)
            ? 1
            : 0;
      });
      var correspondenceChanged = false;
      for (var boundaryIndex = 0; boundaryIndex < matchedBoundaries.length; boundaryIndex += 1) {
        var entry = matchedBoundaries[boundaryIndex];
        if (!plan.retainedOldRenderIds.has(entry.match.fromRenderId)) {
          planOrdinaryBarrierPairs(
            plan,
            entry.oldBoundary,
            entry.newBoundary,
            options,
            retainedSeeds,
            pinnedSeeds
          );
        }
        applyOwnershipRetentionClosure(plan, retainedSeeds, pinnedSeeds);
        if (matchSignature() !== signatureBefore) {
          correspondenceChanged = true;
          break;
        }
      }
      if (correspondenceChanged) continue;
      applyOwnershipRetentionClosure(plan, retainedSeeds, pinnedSeeds);
      if (matchSignature() === signatureBefore) {
        stable = true;
        break;
      }
    }
    if (!stable) {
      throw new TypeError("[Citry] graph: ownership correspondence did not stabilize during physical planning.");
    }
    warnDuplicateActiveComponentKeys(plan);
    return plan;
  };

  var applyOwnershipAdoptionPlan = function (plan) {
    if (!plan || !plan.transaction || plan.transaction.status !== "prepared" || plan.applied) {
      throw new TypeError("[Citry] graph: ownership adoption plan is not ready to apply.");
    }
    if (plan.replacements.length) replaceOwnership(plan.replacements);
    plan.state.adoption.acceptedIncomingRenderIds = new Set(plan.acceptedIncomingRenderIds);
    plan.state.adoption.retainedOldRenderIds = new Set(plan.retainedOldRenderIds);
    plan.excludedIncomingRenderIds.forEach(function (renderId) {
      var link = plan.state.renderLinks.get(renderId);
      if (!link) return;
      link.link.active = false;
      link.anchorState.active = false;
      link.logicalState.active = false;
    });
    var retainedByIncoming = new Map();
    (plan.retainedCorrespondences || plan.retainedMatches || []).forEach(function (match) {
      retainedByIncoming.set(match.toRenderId, match.fromRenderId);
    });
    plan.matches.forEach(function (match) {
      var link = plan.state.renderLinks.get(match.toRenderId);
      if (!link) return;
      link.logicalState.childOrder = link.logicalState.childOrder.map(function (renderId) {
        return retainedByIncoming.get(renderId) || renderId;
      }).filter(function (renderId) {
        return !plan.excludedIncomingRenderIds.has(renderId) || retainedByIncoming.has(renderId);
      });
    });
    plan.matches.forEach(function (match) {
      if (match.preserveExternalParent) {
        var link = plan.state.renderLinks.get(match.toRenderId);
        if (link) plan.state.adoption.externalParents.add(link.logicalState);
      }
    });
    plan.applied = true;
    return plan.matches.slice();
  };

  // A8 supplies these explicit correspondences from its atomic DOM+graph
  // transaction. The complete proposal is validated first and correspondence
  // is never guessed from class or DOM position.
  var replaceOwnership = function (replacements) {
    if (!Array.isArray(replacements) || !replacements.length) {
      throw new TypeError("[Citry] graph: replacement needs a non-empty correspondence array.");
    }
    var staged = [];
    var fromKeys = new Set();
    var toKeys = new Set();
    var fromLinks = new Set();
    var toLinks = new Set();
    replacements.forEach(function (record, index) {
      if (!record || typeof record !== "object") {
        throw new TypeError("[Citry] graph: replacement[" + index + "] must be an object.");
      }
      var fromState = ownershipStates.get(record.fromRevision);
      var from = fromState && fromState.renderLinks.get(record.fromRenderId);
      if (!from || !from.link.active) {
        throw new TypeError("[Citry] graph: replacement source is unknown or inactive.");
      }
      var fromKey = record.fromRevision + ":" + record.fromRenderId;
      if (fromKeys.has(fromKey)) throw new TypeError("[Citry] graph: replacement repeats a source render.");
      fromKeys.add(fromKey);
      fromLinks.add(from);
      var to = null;
      var toState = null;
      if (record.toRevision != null || record.toRenderId != null) {
        if (typeof record.toRevision !== "string" || typeof record.toRenderId !== "string") {
          throw new TypeError("[Citry] graph: replacement target needs both revision and render id.");
        }
        toState = ownershipStates.get(record.toRevision);
        to = toState && toState.renderLinks.get(record.toRenderId);
        if (!to || !to.link.active) throw new TypeError("[Citry] graph: replacement target is unknown or inactive.");
        var toKey = record.toRevision + ":" + record.toRenderId;
        if (toKeys.has(toKey)) throw new TypeError("[Citry] graph: replacement repeats a target render.");
        toKeys.add(toKey);
        toLinks.add(to);
        if (record.preserveLogical === true && from.record.classId !== to.record.classId) {
          throw new TypeError("[Citry] graph: logical identity can be preserved only across the same component class.");
        }
        if (to.anchorState.events) {
          throw new TypeError("[Citry] graph: replacement target already owns an Events anchor.");
        }
      } else if (record.preserveLogical === true) {
        throw new TypeError("[Citry] graph: plain retirement cannot preserve logical identity.");
      }
      staged.push({
        fromState: fromState,
        from: from,
        to: to,
        toState: toState,
        preserveLogical: record.preserveLogical === true,
        preserveExternalParent: record.preserveExternalParent === true,
      });
    });
    toLinks.forEach(function (link) {
      if (fromLinks.has(link)) {
        throw new TypeError("[Citry] graph: one replacement transaction cannot use a render as both source and target.");
      }
    });

    staged.forEach(function (record) {
      var from = record.from;
      var sourceLifecycle = from.logicalState.lifecycle;
      var sourceRoots = sourceLifecycle
        ? sourceLifecycle.els.slice()
        : physicalRangesForKey(record.fromState, from.record.key).flatMap(function (physical) {
            return physicalRangeRoots(physical, from.record.renderId);
          });
      var targetLifecycle = record.to && record.to.logicalState.lifecycle;
      var targetCall =
        record.preserveLogical && record.toState
          ? record.toState.graphCalls.get(record.to.record.renderId) || null
          : null;
      if (record.preserveLogical) {
        if (targetLifecycle && targetLifecycle !== sourceLifecycle) {
          adoptBoundaryEndpoint(
            record.toState,
            record.to.record.renderId,
            targetLifecycle,
            sourceLifecycle
          );
          destroyLifecycle(targetLifecycle, "a correlated replacement adopted the source logical identity");
        }
        if (sourceLifecycle) {
          cancelLifecycleCalls(sourceLifecycle, null);
          disposeInvocation(sourceLifecycle);
        }
      } else if (sourceLifecycle) {
        destroyLifecycle(
          sourceLifecycle,
          record.to ? "a class replacement created a fresh logical instance" : "the logical instance was retired"
        );
      }
      if (!record.to) {
        deactivateRenderLink(record.fromState, from);
        return;
      }
      from.link.active = false;
      var to = record.to;
      var provisionalAnchor = to.link.anchor;
      var provisionalAnchorState = to.anchorState;
      var provisionalLogical = to.link.logical;
      var provisionalLogicalState = to.logicalState;
      var targetRevision = provisionalAnchorState.revision;
      provisionalAnchorState.active = false;
      browserAnchors.delete(provisionalAnchor.id);
      to.link.anchor = from.link.anchor;
      to.anchorState = from.anchorState;
      from.anchorState.active = true;
      from.anchorState.revision = targetRevision;
      from.anchorState.renderId = to.record.renderId;
      from.anchorState.classId = to.record.classId;
      if (record.preserveLogical) {
        var incomingChildOrder = provisionalLogicalState.childOrder.slice();
        var incomingMorphKey = provisionalLogicalState.morphKey;
        var incomingMorphMode = provisionalLogicalState.morphMode;
        provisionalLogicalState.active = false;
        to.link.logical = from.link.logical;
        to.logicalState = from.logicalState;
        from.logicalState.active = true;
        from.logicalState.revision = from.anchorState.revision;
        from.logicalState.renderId = to.record.renderId;
        from.logicalState.childOrder = incomingChildOrder;
        if (!record.preserveExternalParent) {
          from.logicalState.morphKey = incomingMorphKey;
          from.logicalState.morphMode = incomingMorphMode;
        }
        record.toState.logicalInstances.delete(provisionalLogical.id);
        record.toState.logicalInstances.set(from.link.logical.id, from.link.logical);
        if (sourceLifecycle) {
          sourceLifecycle.active = true;
          sourceLifecycle.logical = from.link.logical;
          sourceLifecycle.logicalState = from.logicalState;
          sourceLifecycle.revision = targetRevision;
          sourceLifecycle.renderId = to.record.renderId;
          sourceLifecycle.compatRenderId = null;
          sourceLifecycle.classId = to.record.classId;
          from.logicalState.lifecycle = sourceLifecycle;
          componentLifecycles.set(sourceLifecycle.logical.id, sourceLifecycle);
          liveInstances.delete(from.record.renderId);
          liveInstances.set(to.record.renderId, to.record.classId);
          if (targetCall) {
            targetCall.lifecycle = sourceLifecycle;
            targetCall.route = resolveOwnershipRoute(targetRevision, to.record.renderId, to.record.classId);
            targetCall.status = targetCall.dependenciesReady ? "waiting" : "staged";
            targetCall.heldRoots = new Set();
            // A settled call transferred its data reference to the
            // provisional lifecycle. Destroying that lifecycle above releases
            // the reference, so retain it again before the fresh render is
            // queued against the preserved logical instance.
            retainCallData(targetCall);
            sourceLifecycle.calls.add(targetCall);
            if (pendingCalls.indexOf(targetCall) === -1) pendingCalls.push(targetCall);
          }
        }
      } else {
        from.logicalState.active = false;
        to.link.logical = to.record.logicalInstance;
        provisionalLogicalState.anchor = from.link.anchor;
        from.anchorState.logical = to.link.logical;
      }
      // Keep the target record's dynamic getters routed through the updated
      // link cell; the provisional anchor is intentionally retired.
      to.link.active = true;
      record.toState.anchors.delete(provisionalAnchor.id);
      record.toState.anchors.set(from.link.anchor.id, from.link.anchor);
      if (record.toState.adoption) {
        record.toState.adoption.transfers.set(
          to.record.key,
          physicalRangesForKey(record.fromState, from.record.key).slice()
        );
        record.toState.adoption.markerTransfers.push({
          fromRenderId: from.record.renderId,
          toRenderId: to.record.renderId,
          targetKey: to.record.key,
          roots: sourceRoots,
        });
      }
      scheduleLifecycleReconcile();
      if (targetCall && sourceLifecycle) flushCalls();
    });
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var mintRuntimePlacementId = function () {
    runtimePlacementCounter += 1;
    return "p" + runtimePlacementCounter.toString(36);
  };

  var validateRuntimePlacementCaps = function (revision, expected) {
    var prefix = "citry:p1:" + revision + ":";
    var comments = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    var placements = new Map();
    var stacks = new Map();
    var node;
    while ((node = comments.nextNode())) {
      var text = node.data.trim();
      if (text.indexOf(prefix) !== 0) continue;
      var match = /^citry:p1:([0-9a-f]{64}):([A-Za-z0-9_-]+):([0-9]+):([ir]):([0-9]+):([se])$/.exec(text);
      if (!match || match[1] !== revision) {
        throw new TypeError("[Citry] graph: malformed runtime placement cap.");
      }
      var placementId = match[2];
      var key = match[3] + ":" + match[4] + ":" + match[5];
      if (!expected.has(key)) {
        throw new TypeError("[Citry] graph: runtime placement cap names an unknown record " + key + ".");
      }
      var found = placements.get(placementId);
      if (!found) {
        found = new Map();
        placements.set(placementId, found);
      }
      var pair = found.get(key) || {};
      if (pair[match[6]]) {
        throw new TypeError("[Citry] graph: duplicate runtime placement cap " + placementId + ":" + key + ".");
      }
      pair[match[6]] = node;
      found.set(key, pair);
      var stack = stacks.get(placementId) || [];
      stacks.set(placementId, stack);
      if (match[6] === "s") {
        var graphPrefix = match[3] + ":r:";
        pair.parentRegion = null;
        for (var index = stack.length - 1; index >= 0; index -= 1) {
          if (stack[index].indexOf(graphPrefix) === 0) {
            pair.parentRegion = Number(stack[index].slice(graphPrefix.length));
            break;
          }
        }
        stack.push(key);
      } else {
        if (stack.pop() !== key) {
          throw new TypeError("[Citry] graph: runtime placement caps cross or close out of order.");
        }
        if (!pair.s || pair.s.parentNode !== node.parentNode || !nodePrecedes(pair.s, node)) {
          throw new TypeError("[Citry] graph: runtime placement cap endpoints must share one ordered parent.");
        }
      }
    }
    placements.forEach(function (found, placementId) {
      if ((stacks.get(placementId) || []).length) {
        throw new TypeError("[Citry] graph: a runtime placement opening cap is unclosed.");
      }
      expected.forEach(function (key) {
        var pair = found.get(key);
        if (!pair || !pair.s || !pair.e) {
          throw new TypeError("[Citry] graph: runtime placement '" + placementId + "' is missing cap " + key + ".");
        }
      });
    });
    return placements;
  };

  var buildPhysicalPlacementSet = function (caps, placementId) {
    var physicals = new Map();
    caps.forEach(function (pair, localKey) {
      var parts = localKey.split(":");
      var graphId = Number(parts[0]);
      var kind = parts[1];
      var localId = Number(parts[2]);
      var key = qualifiedGraphId(graphId, kind, localId);
      physicals.set(key, {
        key: key,
        graphId: graphId,
        regionId: kind === "r" ? localId : undefined,
        instanceId: kind === "i" ? localId : undefined,
        start: pair.s,
        end: pair.e,
        startMarker: pair.s.data,
        endMarker: pair.e.data,
        parentRegionId: pair.parentRegion,
        parentPlacement: null,
        placementId: placementId,
        topology: pair.s.parentNode === pair.e.parentNode ? "same-parent" : "document-body",
      });
    });
    physicals.forEach(function (physical) {
      if (physical.parentRegionId != null) {
        physical.parentPlacement = physicals.get(
          qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
        ) || null;
      }
      Object.freeze(physical);
    });
    return physicals;
  };

  var applyAdoptionTransfers = function (state) {
    state.adoption.transfers.forEach(function (candidates, key) {
      var parts = key.slice(1).split(":");
      var live = candidates.filter(function (physical) {
        return physical.start.isConnected && physical.end.isConnected;
      });
      live.forEach(function (physical, index) {
        var placementId = index === 0 ? null : physical.placementId || mintRuntimePlacementId();
        var prefix = placementId == null
          ? OWNERSHIP_COMMENT_PREFIX + ":" + state.publicRevision.revision + ":"
          : "citry:p1:" + state.publicRevision.revision + ":" + placementId + ":";
        physical.start.data = prefix + parts[0] + ":" + parts[1] + ":" + parts[2] + ":s";
        physical.end.data = prefix + parts[0] + ":" + parts[1] + ":" + parts[2] + ":e";
      });
    });
  };

  var removeExcludedAdoptionCaps = function (state, expected) {
    var known = new Set(state.caps.keys());
    var revision = state.publicRevision.revision;
    var canonicalPrefix = OWNERSHIP_COMMENT_PREFIX + ":" + revision + ":";
    var runtimePrefix = "citry:p1:" + revision + ":";
    var comments = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    var excluded = [];
    for (var node = comments.nextNode(); node; node = comments.nextNode()) {
      var text = node.data.trim();
      var key = null;
      var ownership = CitryClientGraphProtocol.parseOwnershipComment(text);
      if (ownership && ownership.revision === revision) {
        key = ownership.graphId + ":" + ownership.kind + ":" + ownership.recordId;
      } else if (text.indexOf(canonicalPrefix) === 0) {
        throw new TypeError("[Citry] graph: malformed excluded incoming physical cap.");
      } else if (text.indexOf(runtimePrefix) === 0) {
        var runtime = /^citry:p1:([0-9a-f]{64}):([A-Za-z0-9_-]+):([0-9]+):([ir]):([0-9]+):([se])$/.exec(text);
        if (!runtime || runtime[1] !== revision) {
          throw new TypeError("[Citry] graph: malformed excluded incoming runtime cap.");
        }
        key = runtime[3] + ":" + runtime[4] + ":" + runtime[5];
      }
      if (key === null || expected.has(key)) continue;
      if (!known.has(key)) {
        throw new TypeError("[Citry] graph: physical cap names an unknown record " + key + ".");
      }
      excluded.push(node);
    }
    // A stationary retained range can leave the incoming endpoints crossed
    // with its accepted parent cap even though its incoming contents never
    // land. Remove those known-excluded endpoints first; the strict scan below
    // then validates every accepted range and rejects any remaining damage.
    excluded.forEach(function (cap) { cap.remove(); });
  };

  var adoptLivePhysicalPlacements = function (state, acceptedRenderIds, plan) {
    var expected = new Set();
    var excludedPhysicalKeys = state.adoption && state.adoption.excludedIncomingPhysicalKeys;
    state.caps.forEach(function (_pair, key) {
      var parts = key.split(":");
      var recordKey = qualifiedGraphId(Number(parts[0]), parts[1], Number(parts[2]));
      if (excludedPhysicalKeys && excludedPhysicalKeys.has(recordKey)) return;
      var instance = state.registry.componentInstances.get(recordKey);
      if (instance) {
        if (!acceptedRenderIds || acceptedRenderIds.has(instance.renderId)) expected.add(key);
        return;
      }
      var region = state.registry.slotRegions.get(recordKey);
      if (!region || !acceptedRenderIds) {
        expected.add(key);
        return;
      }
      if (
        (region.ownerRenderId == null || acceptedRenderIds.has(region.ownerRenderId)) &&
        (region.receiverRenderId == null || acceptedRenderIds.has(region.receiverRenderId)) &&
        (region.resultOwnerRenderId == null || acceptedRenderIds.has(region.resultOwnerRenderId))
      ) expected.add(key);
    });
    (plan && (plan.retainedCorrespondences || plan.retainedMatches) || []).forEach(function (match) {
      var retainedState = ownershipStates.get(match.fromRevision);
      if (!retainedState) return;
      physicalRangesForKey(retainedState, match.fromKey).forEach(function (physical) {
        if (!physical.start.isConnected || !physical.end.isConnected) return;
        // Alpine's comment walk may reuse the retained Comment objects for
        // their excluded incoming counterparts. Restore the old revision's
        // exact marker text before removing any remaining incoming endpoints.
        physical.start.data = physical.startMarker;
        physical.end.data = physical.endMarker;
      });
    });
    removeExcludedAdoptionCaps(state, expected);
    var canonical = validatePhysicalCaps(state.publicRevision.revision, expected, document);
    var runtime = validateRuntimePlacementCaps(state.publicRevision.revision, expected);
    var byKey = new Map();
    var canonicalPhysical = buildPhysicalPlacementSet(canonical, null);
    canonicalPhysical.forEach(function (physical, key) {
      byKey.set(key, [physical]);
      state.physicalRegions.set(key, physical);
    });
    runtime.forEach(function (caps, placementId) {
      buildPhysicalPlacementSet(caps, placementId).forEach(function (physical, key) {
        var placements = byKey.get(key) || [];
        placements.push(physical);
        byKey.set(key, placements);
      });
    });
    state.caps.clear();
    canonical.forEach(function (pair, key) {
      Object.freeze(pair);
      state.caps.set(key, pair);
    });
    state.physicalPlacements.clear();
    byKey.forEach(function (placements, key) {
      state.physicalPlacements.set(key, placements);
    });
  };

  var prepareOwnershipAdoption = function (manifest, capRoot) {
    if (graphFailures.has(manifest.revision) || seenOwnershipRevisions.has(manifest.revision) || ownershipStates.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: incoming revision was already used.");
    }
    rejectStructuralComponentClones(capRoot);
    var staged = stageOwnershipManifest(manifest, capRoot);
    var normalized = normalizeOwnershipRevision(staged);
    normalized.renderIds.forEach(function (_instance, renderId) {
      ownershipStates.forEach(function (liveState) {
        var live = liveState.renderLinks.get(renderId);
        if (live && live.link.active) {
          throw new TypeError("[Citry] graph: live render id '" + renderId + "' appears in more than one revision.");
        }
      });
    });
    normalized.provisional = true;
    normalized.adoption = {
      transfers: new Map(),
      markerTransfers: [],
      externalParents: new Set(),
      status: "prepared",
      activated: false,
      excludedIncomingPhysicalKeys: new Set(),
    };
    ownershipStates.set(staged.revision, normalized);
    ownershipAdoptionDepth += 1;
    return {
      revision: staged.revision,
      state: normalized,
      status: "prepared",
    };
  };

  var activateOwnershipAdoption = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var state = transaction.state;
    if (state.adoption.activated) return;
    var accepted = transaction.plan && transaction.plan.acceptedIncomingRenderIds;
    if (!(accepted instanceof Set)) accepted = new Set(state.renderLinks.keys());
    accepted.forEach(function (renderId) {
      var link = state.renderLinks.get(renderId);
      if (link && link.link.active) ensureLifecycle(resolveOwnershipRoute(transaction.revision, renderId, link.record.classId), false);
    });
    var excludedPhysicalKeys = transaction.plan && transaction.plan.excludedIncomingPhysicalKeys;
    var fillPlans = preflightGraphFillSources(state, accepted, excludedPhysicalKeys);
    activateGraphFillSources(state, fillPlans);
    activateGraphClientBindings(transaction.revision, accepted);
    state.adoption.activated = true;
  };

  var adoptionRoot = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var roots = [];
    transaction.state.renderLinks.forEach(function (link) {
      if (link.record.parentRenderId == null) roots.push(link.record);
    });
    if (!roots.length) return null;
    if (roots.length !== 1) {
      throw new TypeError("[Citry] graph: an adopted component render must have one logical root instance.");
    }
    return { componentId: roots[0].renderId, classId: roots[0].classId };
  };

  var deactivateOwnershipAdoption = function (state) {
    Array.from(fillSourceDescriptors.values()).forEach(function (descriptor) {
      if (descriptor.state === state) retireFillSource(descriptor);
    });
    Array.from(liveComponentBoundaries).forEach(function (boundary) {
      if (boundary.revision === state.publicRevision.revision && destroyComponentBoundary) {
        destroyComponentBoundary(boundary);
      }
    });
  };

  var pruneInactiveOwnershipRevisions = function () {
    ownershipPruneScheduled = false;
    if (ownershipAdoptionDepth > 0 || rangeMorphDepth > 0) {
      setTimeout(scheduleOwnershipPrune, 0);
      return;
    }
    ownershipStates.forEach(function (state, revision) {
      if (state.provisional || !ownershipGraphs.has(revision)) return;
      var active = false;
      state.renderLinks.forEach(function (link) {
        if (link.link.active) active = true;
      });
      state.graphCalls.forEach(function (call) {
        if (call.status !== "settled" && call.status !== "cancelled") active = true;
      });
      fillSourceDescriptors.forEach(function (descriptor) {
        if (descriptor.active && descriptor.state === state) active = true;
      });
      liveComponentBoundaries.forEach(function (boundary) {
        if (!boundary.destroyed && boundary.revision === revision) active = true;
      });
      var eventsTransaction = graphEvents.get(revision);
      if (eventsTransaction && eventsTransaction.state === "pending") active = true;
      state.retainedPhysicalKeys.forEach(function (key) {
        var stillLive = physicalRangesForKey(state, key).some(function (physical) {
          return physicalRangeIsLive(state, physical);
        });
        if (stillLive) active = true;
        else state.retainedPhysicalKeys.delete(key);
      });
      if (active) return;
      var eventsRuntime = globalThis.Citry && globalThis.Citry.events;
      if (
        eventsRuntime &&
        typeof eventsRuntime._pruneDescriptorRevision === "function" &&
        eventsRuntime._pruneDescriptorRevision(revision, true) === false
      ) return;
      ownershipGraphs.delete(revision);
      ownershipStates.delete(revision);
      graphEvents.delete(revision);
      consumedGraphDependencies.delete(revision);
    });
  };

  scheduleOwnershipPrune = function () {
    if (ownershipPruneScheduled) return;
    ownershipPruneScheduled = true;
    queueMicrotask(pruneInactiveOwnershipRevisions);
  };

  var abortOwnershipAdoption = function (transaction, error) {
    if (!transaction || transaction.status !== "prepared") return;
    var state = transaction.state;
    var failure = error instanceof Error ? error : new Error("[Citry] graph: ownership adoption was aborted.");
    deactivateOwnershipAdoption(state);
    state.renderLinks.forEach(function (link) {
      if (link.logicalState.lifecycle) destroyLifecycle(link.logicalState.lifecycle, "an incoming transaction was aborted");
      deactivateRenderLink(state, link);
    });
    state.adoption.transfers.forEach(function (physicals) {
      physicals.forEach(function (physical) {
        if (physical.start.isConnected) physical.start.remove();
        if (physical.end.isConnected) physical.end.remove();
      });
    });
    var canonicalPrefix = OWNERSHIP_COMMENT_PREFIX + ":" + transaction.revision + ":";
    var runtimePrefix = "citry:p1:" + transaction.revision + ":";
    var comments = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    var ownedComments = [];
    for (var node = comments.nextNode(); node; node = comments.nextNode()) {
      var marker = node.data.trim();
      if (marker.indexOf(canonicalPrefix) === 0 || marker.indexOf(runtimePrefix) === 0) ownedComments.push(node);
    }
    ownedComments.forEach(function (node) { node.remove(); });
    ownershipGraphs.delete(transaction.revision);
    ownershipStates.delete(transaction.revision);
    ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
    transaction.status = "aborted";
    state.adoption.status = "aborted";
    failOwnershipManifest(transaction.revision, failure);
  };

  var discardOwnershipAdoption = function (transaction) {
    if (!transaction || transaction.status !== "prepared") return;
    var state = transaction.state;
    deactivateOwnershipAdoption(state);
    state.renderLinks.forEach(function (link) {
      if (link.logicalState.lifecycle) destroyLifecycle(link.logicalState.lifecycle, "an incoming transaction was excluded");
      link.link.active = false;
      link.anchorState.active = false;
      link.logicalState.active = false;
    });
    ownershipStates.delete(transaction.revision);
    seenOwnershipRevisions.add(transaction.revision);
    ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
    transaction.status = "discarded";
    state.adoption.status = "discarded";
    scheduleOwnershipPrune();
  };

  var forceAdoptionRootMarkers = function (state) {
    state.adoption.markerTransfers.forEach(function (transfer) {
      var physicals = physicalRangesForKey(state, transfer.targetKey);
      transfer.roots.forEach(function (root) {
        if (
          !(root instanceof Element) || !root.isConnected ||
          !root.hasAttribute("data-cid-" + transfer.fromRenderId) ||
          !physicals.some(function (physical) { return physicalRangeContainsNode(physical, root); })
        ) return;
        root.removeAttribute("data-cid-" + transfer.fromRenderId);
        root.setAttribute("data-cid-" + transfer.toRenderId, "");
        var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
        ids = ids.map(function (id) {
          return id === transfer.fromRenderId ? transfer.toRenderId : id;
        });
        if (ids.indexOf(transfer.toRenderId) === -1) ids.push(transfer.toRenderId);
        root.setAttribute("data-cid", Array.from(new Set(ids)).join(" "));
      });
    });
  };

  var commitOwnershipAdoption = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var state = transaction.state;
    if (transaction.plan) {
      state.adoption.excludedIncomingPhysicalKeys = new Set(transaction.plan.excludedIncomingPhysicalKeys);
      transaction.plan.retainedOldPhysicalRecords.forEach(function (identity) {
        var separator = identity.indexOf("\n");
        var retainedState = separator < 0 ? null : ownershipStates.get(identity.slice(0, separator));
        if (retainedState) retainedState.retainedPhysicalKeys.add(identity.slice(separator + 1));
      });
    }
    applyAdoptionTransfers(state);
    retireSupersededComponentBoundaries(state);
    state.renderLinks.forEach(function (link) {
      var parent = link.record.parentRenderId == null ? null : state.renderLinks.get(link.record.parentRenderId);
      if (parent && parent.link.active) link.logicalState.parentLogical = parent.logicalState;
      else if (!state.adoption.externalParents.has(link.logicalState)) link.logicalState.parentLogical = null;
    });
    var accepted = transaction.plan && transaction.plan.acceptedIncomingRenderIds;
    adoptLivePhysicalPlacements(state, accepted instanceof Set ? accepted : null, transaction.plan);
    forceAdoptionRootMarkers(state);
    if (!state.adoption.activated) activateOwnershipAdoption(transaction);
    ownershipGraphs.set(transaction.revision, state.publicRevision);
    seenOwnershipRevisions.add(transaction.revision);
    state.anchors.forEach(function (anchor, anchorId) {
      if (anchor.active) browserAnchors.set(anchorId, anchor);
    });
    state.provisional = false;
    state.adoption.status = "committed";
    refreshGraphFillSources(state);
    var waiters = graphWaiters.get(transaction.revision) || [];
    graphWaiters.delete(transaction.revision);
    waiters.forEach(function (waiter) { waiter.resolve(state.publicRevision); });
    transaction.status = "committed";
    ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
    scheduleLifecycleReconcile();
    scheduleFillSourceReconcile();
    queueMicrotask(activateRootlessBoundaries);
    return state.publicRevision;
  };

  var failOwnershipManifest = function (revision, error) {
    if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision) || ownershipGraphs.has(revision)) {
      return;
    }
    graphFailures.set(revision, error);
    var waiters = graphWaiters.get(revision) || [];
    graphWaiters.delete(revision);
    waiters.forEach(function (waiter) { waiter.reject(error); });
    var blocked = graphBlockedManifests.get(revision) || [];
    graphBlockedManifests.delete(revision);
    if (blocked.length) {
      console.error(
        "[Citry] discarded " + blocked.length + " dependency manifest(s) blocked on failed ownership graph " + revision + "."
      );
    }
  };

  var commitOwnershipManifest = function (manifest) {
    if (graphFailures.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: revision " + manifest.revision + " belongs to a failed transaction.");
    }
    if (seenOwnershipRevisions.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: revision " + manifest.revision + " was inserted more than once.");
    }
    var staged = stageOwnershipManifest(manifest);
    var normalized = normalizeOwnershipRevision(staged);
    var fillPlans = preflightGraphFillSources(normalized);
    normalized.renderIds.forEach(function (_instance, renderId) {
      ownershipStates.forEach(function (liveState) {
        var live = liveState.renderLinks.get(renderId);
        if (live && live.link.active) {
          throw new TypeError("[Citry] graph: live render id '" + renderId + "' appears in more than one revision.");
        }
      });
    });
    // Publication is the first global mutation. Every wire record, cap, and
    // secondary index above has already succeeded, so consumers cannot see a
    // partially normalized revision.
    ownershipStates.set(staged.revision, normalized);
    ownershipGraphs.set(staged.revision, normalized.publicRevision);
    seenOwnershipRevisions.add(staged.revision);
    normalized.anchors.forEach(function (anchor, anchorId) {
      browserAnchors.set(anchorId, anchor);
    });
    activateGraphFillSources(normalized, fillPlans);
    activateGraphClientBindings(staged.revision);
    var waiters = graphWaiters.get(staged.revision) || [];
    graphWaiters.delete(staged.revision);
    waiters.forEach(function (waiter) { waiter.resolve(normalized.publicRevision); });
    var blocked = graphBlockedManifests.get(staged.revision) || [];
    graphBlockedManifests.delete(staged.revision);
    blocked.forEach(function (dependencyManifest) {
      try {
        loadComponentScripts(dependencyManifest);
      } catch (err) {
        console.error("[Citry] failed to process graph-blocked dependency manifest:", err);
      }
    });
    return normalized.publicRevision;
  };

  // ----- loaded-URL bookkeeping -----

  var markScriptLoaded = function (type, url) {
    loaded[type].add(url);
  };

  var isScriptLoaded = function (type, url) {
    return loaded[type].has(url);
  };

  // ----- element creation from {tag, attrs, content} descriptors -----

  var createElement = function (descriptor) {
    var el = document.createElement(descriptor.tag);
    Object.keys(descriptor.attrs || {}).forEach(function (name) {
      var value = descriptor.attrs[name];
      if (value === true) el.setAttribute(name, "");
      else if (value !== false && value != null) el.setAttribute(name, String(value));
    });
    if (descriptor.content) el.textContent = descriptor.content;
    return el;
  };

  var validateDescriptorStructure = function (descriptor) {
    var validationDocument = document.implementation.createDocument("urn:citry:dependency-validation", "validation", null);
    var element = validationDocument.createElementNS("urn:citry:dependency-validation", descriptor.tag);
    Object.keys(descriptor.attrs || {}).forEach(function (name) {
      var value = descriptor.attrs[name];
      if (value === true) element.setAttribute(name, "");
      else if (value !== false && value != null) element.setAttribute(name, String(value));
    });
  };

  // Append a <script> descriptor to <body>; resolves once it has loaded.
  var loadJs = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.src;
    if (url && loadingJs.has(url)) return loadingJs.get(url);
    if (url && isScriptLoaded("js", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (!url) {
      document.body.appendChild(el); // inline scripts run synchronously
      return Promise.resolve();
    }
    var resolveLoad = null;
    var rejectLoad = null;
    var load = new Promise(function (resolve, reject) {
      resolveLoad = resolve;
      rejectLoad = reject;
    });
    loadingJs.set(url, load);
    markScriptLoaded("js", url);
    el.onload = function () {
      loadingJs.delete(url);
      resolveLoad();
    };
    el.onerror = function (event) {
      loadingJs.delete(url);
      loaded.js.delete(url);
      rejectLoad(event);
    };
    document.body.appendChild(el);
    return load;
  };

  // Append a <link rel="stylesheet"> (or inline <style>) descriptor to <head>.
  var loadCss = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.href;
    if (url && loadingCss.has(url)) return loadingCss.get(url).promise;
    if (url && isScriptLoaded("css", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (!url) {
      document.head.appendChild(el);
      return Promise.resolve();
    }
    var resolveLoad = null;
    var rejectLoad = null;
    var load = new Promise(function (resolve, reject) {
      resolveLoad = resolve;
      rejectLoad = reject;
    });
    var entry = { element: el, promise: load, resolve: resolveLoad };
    loadingCss.set(url, entry);
    markScriptLoaded("css", url);
    el.onload = function () {
      if (loadingCss.get(url) !== entry) return;
      loadingCss.delete(url);
      resolveLoad();
    };
    el.onerror = function (event) {
      if (loadingCss.get(url) !== entry) return;
      loadingCss.delete(url);
      loaded.css.delete(url);
      rejectLoad(event);
    };
    document.head.appendChild(el);
    return load;
  };

  // ----- component registrations and data -----

  var registerComponent = function (classId, definition) {
    if (componentRegistrations.has(classId)) {
      throw new Error(
        "[Citry] component '" +
          classId +
          "' is already defined; only one $component registration is allowed per class."
      );
    }
    // The registration preserves whether the config actually declared
    // `props`, including falsy invalid declarations. The
    // `$component` config form (design events.md 5.5) carries both as
    // `{init, props}`; flushCalls resolves the declaration right before
    // init runs.
    var entry;
    if (typeof definition === "function") {
      entry = { fn: definition, props: null, hasProps: false };
    } else if (definition !== null && typeof definition === "object" && typeof definition.init === "function") {
      var hasProps = Object.prototype.hasOwnProperty.call(definition, "props");
      entry = { fn: definition.init, props: hasProps ? definition.props : null, hasProps: hasProps };
    } else {
      throw new TypeError(
        "[Citry] component '" +
          classId +
          "' definition must be a callback function or a config object with an init function."
      );
    }
    componentRegistrations.set(classId, entry);
    componentLifecycles.forEach(function (lifecycle) {
      if (lifecycle.active && lifecycle.classId === classId) ensureLifecycleProps(lifecycle, entry);
    });
    flushCalls();
  };

  // Other extensions enrich the callback payload through `fn(ctx)`.
  // This is called with each instance's payload object just before its callback
  // and adds members by mutating it (its return value is ignored). Returns a
  // function that unregisters the decorator.
  var decorateContext = function (fn) {
    decorators.push(fn);
    return function () {
      var idx = decorators.indexOf(fn);
      if (idx !== -1) decorators.splice(idx, 1);
    };
  };

  var registerComponentData = function (classId, varsHash, data) {
    componentData.set(classId + ":" + varsHash, data);
    flushCalls();
  };

  var retainCallData = function (call) {
    if (call.varsHash == null || call.dataKey != null) return;
    var key = call.classId + ":" + call.varsHash;
    call.dataKey = key;
    componentDataReferences.set(key, (componentDataReferences.get(key) || 0) + 1);
  };

  var releaseComponentDataKey = function (key) {
    if (key == null) return;
    var references = componentDataReferences.get(key);
    if (references == null) return;
    if (references > 1) {
      componentDataReferences.set(key, references - 1);
      return;
    }
    componentDataReferences.delete(key);
    // The data payload has the same page lifetime as its content-addressed
    // variables-script URL in loaded.js. Keep it cached so a later fragment
    // reusing this hash can skip the script request and still settle its call.
  };

  var releaseCallData = function (call) {
    if (call.dataKey == null) return;
    releaseComponentDataKey(call.dataKey);
    call.dataKey = null;
  };

  var transferCallDataToInstance = function (call, lifecycle) {
    var previous = lifecycle ? lifecycle.dataKey : instanceDataKeys.get(call.componentId);
    releaseComponentDataKey(previous);
    if (lifecycle) lifecycle.dataKey = call.dataKey;
    else if (call.dataKey == null) instanceDataKeys.delete(call.componentId);
    else instanceDataKeys.set(call.componentId, call.dataKey);
    // The live instance now owns the reference that the call held.
    call.dataKey = null;
  };

  var callComponent = function (classId, componentId, varsHash, revision) {
    var route = revision == null ? null : resolveOwnershipRoute(revision, componentId, classId);
    var lifecycle = revision == null ? lifecycleForRender(componentId) : null;
    var call = {
      classId: classId,
      componentId: componentId,
      varsHash: varsHash,
      dataKey: null,
      revision: revision || null,
      route: route,
      status: "waiting",
      dependenciesReady: true,
      dependencyCalls: [],
      heldRoots: new Set(),
      lifecycle: lifecycle,
    };
    if (lifecycle) lifecycle.calls.add(call);
    retainCallData(call);
    pendingCalls.push(call);
    flushCalls();
  };

  var isCallReady = function (call) {
    if (call.status === "settled" || call.status === "cancelled" || call.status === "running") return false;
    if (call.revision && (!alpineReady || !call.dependenciesReady)) return false;
    if (call.revision) {
      try {
        call.route = resolveOwnershipRoute(call.revision, call.componentId, call.classId);
      } catch (_err) {
        call.status = "cancelled";
        releaseCallHolds(call);
        releaseCallData(call);
        return false;
      }
    }
    if (call.dependencyCalls.some(function (dependency) {
      return dependency.status !== "settled" && dependency.status !== "cancelled";
    })) return false;
    if (!componentRegistrations.has(call.classId)) return false;
    if (call.dataKey != null && !componentData.has(call.dataKey)) return false;
    if (call.lifecycle) {
      var props = ensureLifecycleProps(call.lifecycle, componentRegistrations.get(call.classId));
      if (props && !props.initialSettled) return false;
      if (callWaitsForAmbientMagic && callWaitsForAmbientMagic(call)) return false;
    }
    return true;
  };

  // ----- rendered ambient context -----

  var AMBIENT_BLOCKED = Symbol("citry-ambient-blocked");

  var validateAmbientKey = function (key) {
    if ((typeof key !== "string" || key.length === 0) && typeof key !== "symbol") {
      throw new TypeError("[Citry] provide/inject keys must be a non-empty string or a symbol.");
    }
    return key;
  };

  var ambientKeyLabel = function (key) {
    return typeof key === "symbol" ? String(key) : "'" + key + "'";
  };

  // Native Alpine teleports keep their authored template as the ambient
  // parent. Citry fill backlinks are lexical-scope carriers and are ignored
  // here, because ambient lookup follows the slot's rendered position.
  var ambientElementPath = function (el) {
    var path = [];
    var seen = new Set();
    var current = el;
    while (current instanceof Element && !seen.has(current)) {
      seen.add(current);
      path.push(current);
      if (!current.isConnected && ambientCloneSources.has(current)) {
        current = ambientCloneSources.get(current);
      } else if (
        current._x_teleportBack instanceof Element &&
        current._x_teleportBack._x_teleport === current
      ) {
        current = current._x_teleportBack;
      } else if (current.parentElement) {
        current = current.parentElement;
      } else if (current.parentNode instanceof ShadowRoot) {
        current = current.parentNode.host;
      } else {
        current = null;
      }
    }
    return path;
  };

  var ambientRangeContainsElement = function (physical, el) {
    return ambientElementPath(el).some(function (candidate) {
      return physicalRangeContainsNode(physical, candidate);
    });
  };

  var ambientElementContainsRange = function (el, physical) {
    var points = physicalRangeElements(physical);
    if (!points.length && physical.start.parentElement) points = [physical.start.parentElement];
    return points.length > 0 && points.every(function (point) {
      return ambientElementPath(point).indexOf(el) !== -1;
    });
  };

  var ambientRangeContainsRange = function (outer, inner) {
    return outer === inner || (
      physicalRangeContainsNode(outer, inner.start) &&
      physicalRangeContainsNode(outer, inner.end)
    );
  };

  var ambientContainerContains = function (outer, inner) {
    if (outer.kind === "range" && inner.kind === "range") {
      return ambientRangeContainsRange(outer.physical, inner.physical);
    }
    if (outer.kind === "range" && inner.kind === "element") {
      return ambientRangeContainsElement(outer.physical, inner.element);
    }
    if (outer.kind === "element" && inner.kind === "range") {
      return ambientElementContainsRange(outer.element, inner.physical);
    }
    return ambientElementPath(inner.element).indexOf(outer.element) !== -1;
  };

  var ambientElementHasRoute = function (el) {
    var found = false;
    ownershipStates.forEach(function (state) {
      if (found) return;
      state.renderLinks.forEach(function (link) {
        if (found || !link.link.active) return;
        physicalRangesForKey(state, link.record.key).forEach(function (physical) {
          if (
            !found &&
            physicalRangeIsLive(state, physical) &&
            ambientRangeContainsElement(physical, el)
          ) found = true;
        });
      });
    });
    return found;
  };

  var ambientElementDeclaresWrite = function (el) {
    return Array.from(el.attributes || []).some(function (attribute) {
      var name = attribute.name.toLowerCase();
      if (name !== "x-init" && name !== "x-effect" && name !== "x-data" && name !== "x-bind") return false;
      return /\$(?:provide|unprovide)\b/.test(attribute.value);
    });
  };

  var ambientElementHasPendingWrite = function (el) {
    var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el) || new Map();
    return Array.from(el.attributes || []).some(function (attribute) {
      var name = attribute.name.toLowerCase();
      if (name !== "x-init" && name !== "x-effect" && name !== "x-data" && name !== "x-bind") return false;
      return /\$(?:provide|unprovide)\b/.test(attribute.value) && !(evaluated.get(attribute.name) > 0);
    });
  };

  callWaitsForAmbientMagic = function (call) {
    var lifecycle = call.lifecycle;
    if (!lifecycle || !lifecycle.active) return false;
    var range = lifecyclePhysicalRange(lifecycle);
    if (!range.state) return false;
    var targetRanges = range.physicals.filter(function (physical) {
      return physicalRangeIsLive(range.state, physical);
    });
    if (!targetRanges.length) return false;
    return Array.prototype.some.call(document.querySelectorAll("[x-init],[x-effect],[x-data]"), function (element) {
      if (!ambientElementDeclaresWrite(element) || !ambientElementHasPendingWrite(element)) return false;
      return targetRanges.some(function (physical) {
        return !ambientRangeContainsElement(physical, element) && ambientElementContainsRange(element, physical);
      });
    });
  };

  var assertAmbientElementRoute = function (el) {
    if (!(el instanceof Element) || !ambientElementHasRoute(el)) {
      throw new Error(
        "[Citry] client context needs an element inside a live Citry render. " +
          "Move this expression into a Citry component template."
      );
    }
  };

  var ambientMagicValue = function (frame, key) {
    for (var index = frame.writes.length - 1; index >= 0; index -= 1) {
      if (frame.writes[index].key === key) return { present: true, value: frame.writes[index].value };
    }
    return { present: false, value: undefined };
  };

  var ambientComponentValue = function (frame, key) {
    if (!frame.writes.has(key)) return { present: false, value: undefined };
    return { present: true, value: frame.writes.get(key) };
  };

  var ambientCandidates = function (target, excludedFrame) {
    var candidates = [];
    componentLifecycles.forEach(function (lifecycle) {
      var invocation = lifecycle.invocation;
      var frame = invocation && invocation.ambientFrame;
      if (!frame || !frame.active || frame === excludedFrame || !frame.writes.size) return;
      var range = lifecyclePhysicalRange(lifecycle);
      if (!range.state) return;
      range.physicals.forEach(function (physical) {
        if (!physicalRangeIsLive(range.state, physical)) return;
        var container = { kind: "range", physical: physical };
        if (ambientContainerContains(container, target)) {
          candidates.push({ frame: frame, container: container, read: ambientComponentValue });
        }
      });
    });
    ambientMagicFrames.forEach(function (frame) {
      if (!frame.active || frame === excludedFrame || !frame.writes.length || !frame.element.isConnected) return;
      if (target.kind === "range" && ambientRangeContainsElement(target.physical, frame.element)) return;
      var container = { kind: "element", element: frame.element };
      if (ambientContainerContains(container, target)) {
        candidates.push({ frame: frame, container: container, read: ambientMagicValue });
      }
    });
    candidates.sort(function (left, right) {
      var leftContainsRight = ambientContainerContains(left.container, right.container);
      var rightContainsLeft = ambientContainerContains(right.container, left.container);
      if (leftContainsRight && !rightContainsLeft) return 1;
      if (rightContainsLeft && !leftContainsRight) return -1;
      if (leftContainsRight && rightContainsLeft && left.container.kind !== right.container.kind) {
        return left.container.kind === "element" ? -1 : 1;
      }
      return 0;
    });
    return candidates;
  };

  var ambientLookup = function (target, key, excludedFrame) {
    if (!ambientContextRevision) ambientContextRevision = alpineOwner.reactive({ value: Object.freeze({}) });
    ambientContextRevision.value;
    var candidates = ambientCandidates(target, excludedFrame);
    for (var index = 0; index < candidates.length; index += 1) {
      var entry = candidates[index].read(candidates[index].frame, key);
      if (!entry.present) continue;
      if (entry.value === AMBIENT_BLOCKED) return { found: false, blocked: true, value: undefined };
      return { found: true, blocked: false, value: entry.value };
    }
    return { found: false, blocked: false, value: undefined };
  };

  var missingAmbientInjection = function (key, owner) {
    throw new Error(
      "[Citry] " + owner + " tried to inject " + ambientKeyLabel(key) +
        ", but no rendered ancestor provided it. Add provide() or $provide() above this call."
    );
  };

  var requireAmbientInvocation = function (frame, operation, writes) {
    if (!frame.active || !frame.invocation.active) {
      throw new Error("[Citry] " + operation + "() used a component context whose invocation has been disposed.");
    }
    if (writes && !frame.open) {
      throw new Error(
        "[Citry] " + operation + "() can only be called during synchronous $component initialization. " +
          "Provide one stable reactive value when later updates are needed."
      );
    }
  };

  var ambientComponentWrite = function (frame, key, value, operation) {
    requireAmbientInvocation(frame, operation, true);
    validateAmbientKey(key);
    frame.writes.set(key, value);
    touchAmbientContext();
  };

  var ambientComponentInject = function (frame, key, hasDefault, defaultValue) {
    requireAmbientInvocation(frame, "inject", false);
    validateAmbientKey(key);
    var range = lifecyclePhysicalRange(frame.lifecycle);
    var physicals = range.state
      ? range.physicals.filter(function (physical) { return physicalRangeIsLive(range.state, physical); })
      : [];
    if (!physicals.length) {
      throw new Error("[Citry] inject() cannot resolve because this component has no live rendered placement.");
    }
    var outcomes = physicals.map(function (physical) {
      return ambientLookup({ kind: "range", physical: physical }, key, frame);
    });
    var first = outcomes[0];
    var agrees = outcomes.every(function (outcome) {
      return outcome.found === first.found && (!first.found || Object.is(outcome.value, first.value));
    });
    if (!agrees) {
      throw new Error(
        "[Citry] inject(" + ambientKeyLabel(key) + ") is ambiguous because this shared component's " +
          "rendered placements have different ancestor values. Inject at the placement with $inject(), " +
          "or make every placement inherit the same value."
      );
    }
    if (first.found) return first.value;
    if (hasDefault) return defaultValue;
    return missingAmbientInjection(key, "component '" + frame.lifecycle.classId + "'");
  };

  var ambientMagicFrame = function (el) {
    var frame = ambientMagicFramesByElement.get(el);
    if (frame && frame.active) return frame;
    frame = { active: true, element: el, writes: [] };
    ambientMagicFramesByElement.set(el, frame);
    ambientMagicFrames.add(frame);
    return frame;
  };

  var retireAmbientMagicFrameIfEmpty = function (frame) {
    if (frame.writes.length) return;
    frame.active = false;
    ambientMagicFrames.delete(frame);
    if (ambientMagicFramesByElement.get(frame.element) === frame) {
      ambientMagicFramesByElement.delete(frame.element);
    }
  };

  touchAmbientContext = function () {
    if (!ambientContextRevision) ambientContextRevision = alpineOwner.reactive({ value: Object.freeze({}) });
    ambientContextRevision.value = Object.freeze({});
  };

  createAmbientDirectiveControl = function (el, attributeName) {
    var token = {
      active: true,
      open: true,
      evaluated: false,
      element: el,
      attributeName: attributeName,
      frame: null,
    };
    var close = function () {
      token.open = false;
    };
    var control = {
      run: function (callback) {
        if (!token.active) return callback();
        var previous = activeAmbientDirective;
        activeAmbientDirective = token;
        try {
          return callback();
        } finally {
          var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el);
          if (!evaluated) {
            evaluated = new Map();
            ambientDirectiveEvaluatedAttributesByElement.set(el, evaluated);
          }
          if (!token.evaluated) {
            token.evaluated = true;
            evaluated.set(attributeName, (evaluated.get(attributeName) || 0) + 1);
          }
          activeAmbientDirective = previous;
        }
      },
      close: close,
      dispose: function () {
        if (!token.active) return;
        token.active = false;
        close();
        var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el);
        if (evaluated && token.evaluated) {
          var remaining = (evaluated.get(attributeName) || 1) - 1;
          if (remaining > 0) evaluated.set(attributeName, remaining);
          else evaluated.delete(attributeName);
          if (!evaluated.size) ambientDirectiveEvaluatedAttributesByElement.delete(el);
        }
        if (!token.frame) return;
        var frame = token.frame;
        token.frame = null;
        var priorLength = frame.writes.length;
        frame.writes = frame.writes.filter(function (write) { return write.token !== token; });
        if (frame.writes.length !== priorLength) touchAmbientContext();
        retireAmbientMagicFrameIfEmpty(frame);
      },
    };
    token.control = control;
    return Object.freeze(control);
  };

  runAmbientDirective = function (el, attributeName, registerCleanup, callback) {
    var control = ambientDirectiveControlsByCleanup.get(registerCleanup);
    if (!control) {
      var dispose = function () {
        control.dispose();
        if (ambientDirectiveControlsByCleanup.get(registerCleanup) === control) {
          ambientDirectiveControlsByCleanup.delete(registerCleanup);
        }
      };
      control = createAmbientDirectiveControl(el, attributeName);
      ambientDirectiveControlsByCleanup.set(registerCleanup, control);
      registerCleanup(dispose);
      queueMicrotask(function () {
        control.close();
        flushCalls();
      });
    }
    return control.run(callback);
  };

  var ambientMagicWrite = function (el, key, value, operation) {
    validateAmbientKey(key);
    var token = activeAmbientDirective;
    var ownerElement = token && token.active ? token.element : el;
    if (!token || !token.active || !token.open) {
      throw new Error(
        "[Citry] $" + operation + "() can only be called during a synchronous Alpine directive's " +
          "initial evaluation. Use x-init, or provide one stable reactive value for later updates."
      );
    }
    if (!ownerElement.isConnected) {
      throw new Error(
        "[Citry] $" + operation + "() cannot write while Alpine initializes a detached morph clone. " +
          "Declare the provider in x-init on the live component template."
      );
    }
    assertAmbientElementRoute(ownerElement);
    var frame = ambientMagicFrame(ownerElement);
    token.frame = frame;
    ambientWriteCounter += 1;
    frame.writes.push({ key: key, value: value, token: token, order: ambientWriteCounter });
    touchAmbientContext();
  };

  var ambientMagicInject = function (el, key, hasDefault, defaultValue) {
    validateAmbientKey(key);
    var ownerElement = el;
    assertAmbientElementRoute(ownerElement);
    var ownFrame = ambientMagicFramesByElement.get(ownerElement) || null;
    var outcome = ambientLookup({ kind: "element", element: ownerElement }, key, ownFrame);
    if (outcome.found) return outcome.value;
    if (hasDefault) return defaultValue;
    return missingAmbientInjection(key, "an Alpine expression");
  };

  installAmbientContext = function (_alpine, registerMagic) {
    registerMagic("provide", function (el) {
      return function (key, value) { ambientMagicWrite(el, key, value, "provide"); };
    });
    registerMagic("inject", function (el) {
      return function (key, defaultValue) {
        return ambientMagicInject(el, key, arguments.length > 1, defaultValue);
      };
    });
    registerMagic("unprovide", function (el) {
      return function (key) { ambientMagicWrite(el, key, AMBIENT_BLOCKED, "unprovide"); };
    });
  };

  var makeInvocation = function (lifecycle) {
    var invocation = {
      active: true,
      effectStops: [],
      resources: [],
      userCleanup: null,
      ambientFrame: null,
    };
    invocation.ambientFrame = {
      active: true,
      open: true,
      lifecycle: lifecycle,
      invocation: invocation,
      writes: new Map(),
    };
    lifecycle.invocation = invocation;
    return invocation;
  };

  var invocationControl = function (invocation) {
    return Object.freeze({
      registerCleanup: function (cleanup) {
        if (typeof cleanup !== "function") {
          throw new TypeError("[Citry] a context decorator tried to register a non-function cleanup.");
        }
        var active = true;
        var once = function () {
          if (!active) return;
          active = false;
          cleanup();
        };
        if (!invocation.active) once();
        else invocation.resources.push(once);
        return once;
      },
    });
  };

  var addLifecycleContext = function (ctx, lifecycle, invocation) {
    var ambientFrame = invocation.ambientFrame;
    ctx.scope = lifecycle.scope;
    ctx.els = lifecycle.els;
    ctx.provide = function (key, value) {
      ambientComponentWrite(ambientFrame, key, value, "provide");
    };
    ctx.inject = function (key, defaultValue) {
      return ambientComponentInject(ambientFrame, key, arguments.length > 1, defaultValue);
    };
    ctx.unprovide = function (key) {
      ambientComponentWrite(ambientFrame, key, AMBIENT_BLOCKED, "unprovide");
    };
    ctx.reactive = function (value) {
      if (!invocation.active) {
        throw new Error("[Citry] reactive() cannot be called after this component invocation was disposed.");
      }
      if (value === null || typeof value !== "object") {
        throw new TypeError("[Citry] reactive(value) needs an object or array.");
      }
      return alpineOwner.reactive(value);
    };
    ctx.effect = function (callback) {
      if (!invocation.active) {
        throw new Error("[Citry] effect() cannot be called after this component invocation was disposed.");
      }
      if (typeof callback !== "function") throw new TypeError("[Citry] effect(callback) needs a callback.");
      var active = true;
      var reference = alpineOwner.effect(function () {
        if (!active || !invocation.active) return;
        try { callback(); } catch (err) {
          console.error("[Citry] managed component effect failed:", err);
        }
      });
      var stop = function () {
        if (!active) return;
        active = false;
        alpineOwner.release(reference);
      };
      invocation.effectStops.push(stop);
      return stop;
    };
  };

  var storeCleanup = function (call, cleanup) {
    var key = call.classId + ":" + call.componentId;
    var fns = cleanups.get(key);
    if (!fns) cleanups.set(key, (fns = []));
    fns.push(cleanup);
  };

  // Run (and discard) the cleanups stored for one instance. A later
  // graph-independent call for the same id re-runs its callback, so whatever
  // it set up last time is torn down first.
  var runCleanups = function (call) {
    var fns = cleanups.get(call.classId + ":" + call.componentId);
    if (!fns) return;
    cleanups.delete(call.classId + ":" + call.componentId);
    fns.forEach(function (cleanup) {
      try {
        cleanup();
      } catch (err) {
        console.error("[Citry] component cleanup for '" + call.classId + "' failed:", err);
      }
    });
  };

  // ----- instance lifecycle: teardown on removal and Component.css cleanup -----

  // How many tracked instances of a class are still live. Counted straight
  // from liveInstances every time, so the number can never drift from the set
  // of instances actually tracked.
  var classLiveCount = function (classId) {
    var n = 0;
    liveInstances.forEach(function (cls) {
      if (cls === classId) n += 1;
    });
    return n;
  };

  // Remove a class-level Component.css sheet, the one the server tags with
  // data-citry-css-class. A sheet whose class has no live instance left has
  // nothing to style, so it is dropped.
  var removeClassCss = function (classId) {
    document.querySelectorAll('[data-citry-css-class="' + classId + '"]').forEach(function (el) {
      var url = el.getAttribute("href");
      if (url) {
        loaded.css.delete(url);
        var loading = loadingCss.get(url);
        if (loading && loading.element === el) {
          loadingCss.delete(url);
          loading.resolve();
        }
      }
      el.remove();
    });
  };

  // Collect a class's Component.css, but on a later task, not now. A component
  // that re-renders in place retires its old instance id before it registers
  // the fresh one, so at the moment of retirement a class's only instance can
  // momentarily look like its last even though a same-class render is about
  // to land. Dropping the sheet right then would remove it on every such
  // re-render, and a sheet served from a URL is recorded as loaded (so it is
  // not fetched again), which would lose the class's styling for good. So the
  // check is deferred and the live count re-read then: a fresh same-class
  // instance that arrived in the meantime cancels the collection, while a
  // class that is genuinely gone still has its sheet removed. One re-check is
  // queued per class so a burst of retirements does not pile up timers.
  var scheduleCssGc = function (classId) {
    if (cssGcPending.has(classId)) return;
    cssGcPending.add(classId);
    setTimeout(function () {
      cssGcPending.delete(classId);
      if (classLiveCount(classId) === 0) removeClassCss(classId);
    }, 0);
  };

  // Run the teardown for every tracked instance whose last element has left
  // the DOM (a real node removal, or the same node's data-cid-<id> swapped
  // for a new one in place), then forget it. When that empties a class, the
  // class's Component.css is queued for the deferred collection above.
  var sweepRemovedInstances = function () {
    sweepScheduled = false;
    reconcileComponentLifecycles();
    liveInstances.forEach(function (classId, componentId) {
      var lifecycle = lifecycleForRender(componentId);
      if (lifecycle && lifecycleCapsAreLive(lifecycle)) return;
      if (document.querySelector("[data-cid-" + componentId + "]")) return;
      liveInstances.delete(componentId);
      var dataKey = instanceDataKeys.get(componentId);
      instanceDataKeys.delete(componentId);
      releaseComponentDataKey(dataKey);
      // A CSS-only instance has no stored cleanups, so runCleanups is a no-op
      // for it; a JS instance's cleanups run here exactly once.
      runCleanups({ classId: classId, componentId: componentId });
      if (classLiveCount(classId) === 0) scheduleCssGc(classId);
    });
  };

  // Queue a removal sweep for the next microtask. Debounced so a morph's
  // remove-then-add churn within one mutation batch is seen whole: an id
  // removed and re-added in the same batch is present again when the sweep
  // runs, so it is not misread as a removal.
  var scheduleSweep = function () {
    if (sweepScheduled) return;
    sweepScheduled = true;
    Promise.resolve().then(sweepRemovedInstances);
  };

  // Record an instance the manifest declared present for CSS only (a
  // Component.css instance with no $component JS), so its class counts as
  // live even though nothing calls it. See the cssInstances note in
  // loadComponentScripts for the manifest shape WP10 emits.
  var trackCssInstance = function (classId, componentId) {
    liveInstances.set(componentId, classId);
  };

  // Run every pending call whose callback and data have both arrived. Calls
  // stay queued (in order) until they are ready, so the manifest, the
  // component's JS, and the data script may arrive in any order.
  var flushCalls = function () {
    if (flushingCalls) {
      flushAgain = true;
      return;
    }
    flushingCalls = true;
    try {
      do {
        flushAgain = false;
        var batch = pendingCalls;
        pendingCalls = [];
        var progressed = false;
        batch.forEach(function (call) {
          if (call.status === "cancelled" || call.status === "settled") return;
          if (!isCallReady(call)) {
            if (call.status !== "cancelled") pendingCalls.push(call);
            return;
          }
          progressed = true;
          call.status = "running";
          var lifecycle = call.lifecycle;
          var invocation = null;
          var control = null;
          if (lifecycle) {
            disposeInvocation(lifecycle);
            reconcileComponentLifecycles();
            invocation = makeInvocation(lifecycle);
            control = invocationControl(invocation);
          } else {
            runCleanups(call);
          }

          var data = call.dataKey == null ? null : componentData.get(call.dataKey);
          var els = lifecycle ? lifecycle.els : rootsForRender(call.componentId);
          var ctx = { id: call.componentId, els: els, data: data };
          if (call.route) ctx.graph = call.route;
          if (lifecycle) addLifecycleContext(ctx, lifecycle, invocation);
          decorators.slice().forEach(function (decorate) {
            try {
              decorate(ctx, control);
            } catch (err) {
              console.error("[Citry] context decorator failed (calling '" + call.classId + "'):", err);
            }
          });
          var entry = componentRegistrations.get(call.classId);
          var runCallback = true;
          var lifecycleProps = lifecycle ? ensureLifecycleProps(lifecycle, entry) : null;
          if (lifecycleProps) {
            ctx.props = lifecycleProps.view;
            if (!lifecycleProps.currentValid) runCallback = false;
          } else if (entry.hasProps) {
            var events = globalThis.Citry.events;
            if (!events || typeof events._resolveProps !== "function") {
              console.error(
                "[Citry] component callback for '" + call.classId +
                  "' declares props, which need the events extension's client runtime;" +
                  " the runtime is not loaded, so the callback was skipped."
              );
              runCallback = false;
            } else {
              try {
                ctx.props = events._resolveProps(call.classId, entry.props);
              } catch (err) {
                console.error(
                  "[Citry] component callback for '" + call.classId + "' skipped, its props failed validation:",
                  err
                );
                runCallback = false;
              }
            }
          }
          if (runCallback) {
            try {
              var cleanup = entry.fn(ctx);
              if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
              if (typeof cleanup === "function") {
                if (invocation) invocation.userCleanup = cleanup;
                else storeCleanup(call, cleanup);
              } else if (cleanup && typeof cleanup.then === "function") {
                console.error(
                  "[Citry] component callback for '" + call.classId +
                    "' returned a Promise. Async component init is unsupported; the init DAG settled synchronously."
                );
                Promise.resolve(cleanup).catch(function (err) {
                  console.error("[Citry] unsupported async component callback for '" + call.classId + "' rejected:", err);
                });
              }
            } catch (err) {
              if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
              console.error("[Citry] component callback for '" + call.classId + "' failed:", err);
              if (lifecycle) disposeInvocation(lifecycle);
            }
          } else if (lifecycle) {
            if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
            disposeInvocation(lifecycle);
          }
          call.status = "settled";
          releaseCallHolds(call);
          if (lifecycle) lifecycle.calls.delete(call);
          transferCallDataToInstance(call, lifecycle);
          liveInstances.set(call.componentId, call.classId);
        });
        if (progressed && pendingCalls.length) flushAgain = true;
      } while (flushAgain);
    } finally {
      flushingCalls = false;
    }
    scheduleSweep();
  };

  // ----- manifests -----

  // Process one manifest object (already JSON-parsed; string fields base64):
  //   markLoaded: {js: [url...], css: [url...]}   already on the page
  //   fetch:      {js: [tag descriptor JSON...], css: [...]}   load now
  //   calls:      [[classId, componentId, varsHash | null], ...]
  var stageManifestCalls = function (manifest, revision) {
    var calls = (manifest.calls || []).map(function (call) {
      var staged = {
        classId: fromBase64(call[0]),
        componentId: fromBase64(call[1]),
        varsHash: call[2] == null ? null : fromBase64(call[2]),
        dataKey: null,
        revision: revision || null,
        route: null,
        status: revision ? "staged" : "waiting",
        dependenciesReady: !revision,
        dependencyCalls: [],
        heldRoots: new Set(),
        lifecycle: null,
      };
      if (revision) staged.route = resolveOwnershipRoute(revision, staged.componentId, staged.classId);
      return staged;
    });
    if (!revision) {
      calls.forEach(function (call) {
        call.lifecycle = lifecycleForRender(call.componentId);
        if (call.lifecycle) call.lifecycle.calls.add(call);
        retainCallData(call);
      });
      return calls;
    }

    var state = ownershipStates.get(revision);
    var local = new Map();
    calls.forEach(function (call) {
      if (local.has(call.componentId) || state.graphCalls.has(call.componentId)) {
        throw new TypeError(
          "[Citry] graph-linked dependency manifest repeats callback render id '" + call.componentId + "'."
        );
      }
      local.set(call.componentId, call);
    });
    calls.forEach(function (call) {
      call.lifecycle = ensureLifecycle(call.route, true);
      if (!call.lifecycle) {
        throw new TypeError("[Citry] graph-linked callback could not activate its logical instance.");
      }
    });
    calls.forEach(function (call) {
      var parentRenderId = state.executionOrderParentByChild.get(call.componentId);
      var visited = new Set();
      while (parentRenderId != null && !visited.has(parentRenderId)) {
        visited.add(parentRenderId);
        var parentCall = local.get(parentRenderId) || state.graphCalls.get(parentRenderId);
        if (parentCall) {
          call.dependencyCalls.push(parentCall);
          break;
        }
        var parentLink = state.renderLinks.get(parentRenderId);
        parentRenderId =
          state.executionOrderParentByChild.get(parentRenderId) ||
          (parentLink ? parentLink.record.parentRenderId : null);
      }
      state.graphCalls.set(call.componentId, call);
      call.lifecycle.calls.add(call);
      retainCallData(call);
      pendingCalls.push(call);
    });
    calls.forEach(function (call) {
      var childRange = lifecyclePhysicalRange(call.lifecycle);
      if (!childRange.state) return;
      calls.forEach(function (candidate) {
        if (candidate === call || call.dependencyCalls.indexOf(candidate) !== -1) return;
        var parentRange = lifecyclePhysicalRange(candidate.lifecycle);
        if (!parentRange.state) return;
        var parentContainsChild = childRange.physicals.length > 0 && childRange.physicals.every(
          function (childPhysical) {
            return parentRange.physicals.some(function (parentPhysical) {
              return ambientRangeContainsRange(parentPhysical, childPhysical);
            });
          }
        );
        if (!parentContainsChild) return;
        var childContainsParent = parentRange.physicals.length > 0 && parentRange.physicals.every(
          function (parentPhysical) {
            return childRange.physicals.some(function (childPhysical) {
              return ambientRangeContainsRange(childPhysical, parentPhysical);
            });
          }
        );
        if (!childContainsParent) call.dependencyCalls.push(candidate);
      });
    });
    // This synchronous pass is what places per-root Alpine holds before the
    // owned Alpine MutationObserver sees a just-inserted fragment.
    reconcileComponentLifecycles();
    return calls;
  };

  var cancelStagedCalls = function (calls, reason) {
    calls.forEach(function (call) {
      if (call.status === "settled" || call.status === "cancelled") return;
      call.status = "cancelled";
      releaseCallHolds(call);
      releaseCallData(call);
      if (call.lifecycle) call.lifecycle.calls.delete(call);
    });
    flushCalls();
    if (reason) console.error("[Citry] component callback branch was cancelled because an asset failed:", reason);
  };

  var prepareComponentAssets = function (manifest) {
    var markLoaded = manifest.markLoaded || {};
    (markLoaded.js || []).forEach(function (url) {
      markScriptLoaded("js", fromBase64(url));
    });
    (markLoaded.css || []).forEach(function (url) {
      markScriptLoaded("css", fromBase64(url));
    });

    var fetch = manifest.fetch || {};
    var hasAsyncAssets = false;
    var styles = (fetch.css || []).map(function (encoded) {
      var descriptor = JSON.parse(fromBase64(encoded));
      if (descriptor.attrs && descriptor.attrs.href) hasAsyncAssets = true;
      return loadCss(descriptor);
    });
    var scripts = (fetch.js || []).map(function (encoded) {
      var descriptor = JSON.parse(fromBase64(encoded));
      if (descriptor.attrs && descriptor.attrs.src) hasAsyncAssets = true;
      return descriptor;
    });
    return {
      styles: styles,
      scripts: scripts,
      hasAsyncAssets: hasAsyncAssets,
    };
  };

  var applyStagedManifest = function (manifest, calls) {
    calls.forEach(function (call) {
      if (!call.revision) pendingCalls.push(call);
      else {
        call.dependenciesReady = true;
        if (call.status === "staged") call.status = "waiting";
      }
    });
    flushCalls();

    // Instances the manifest declares present for CSS only: a Component.css
    // instance with no $component JS, which nothing else would register, so
    // a class made only of such instances is still counted as live for the
    // Component.css cleanup. Shape (the contract WP10 emits): a `cssInstances`
    // list of [classId, componentId] pairs, base64-armored like `calls`.
    (manifest.cssInstances || []).forEach(function (entry) {
      trackCssInstance(fromBase64(entry[0]), fromBase64(entry[1]));
    });
  };

  var applyComponentScripts = function (manifest) {
    var calls = stageManifestCalls(manifest, null);
    var assets = prepareComponentAssets(manifest);
    // Preserve the graph-independent inline-manifest contract: inline styles
    // and scripts execute, and their callbacks flush, before this private
    // manager call returns. URL assets necessarily use the asynchronous path.
    if (!assets.hasAsyncAssets) {
      assets.scripts.forEach(loadJs);
      applyStagedManifest(manifest, calls);
      return Promise.resolve();
    }
    var chain = Promise.all(assets.styles);
    assets.scripts.forEach(function (descriptor) {
      chain = chain.then(function () { return loadJs(descriptor); });
    });
    return chain.then(
      function () {
        applyStagedManifest(manifest, calls);
      },
      function (err) {
        cancelStagedCalls(calls, err);
        throw err;
      }
    );
  };

  var applyGraphComponentScripts = function (manifest, calls) {
    var assets = prepareComponentAssets(manifest);
    var hasAssets = assets.styles.length || assets.scripts.length;
    var releaseStart = hasAssets ? alpineApi._holdStart() : function () {};
    var chain = Promise.all(assets.styles);
    assets.scripts.forEach(function (descriptor) {
      chain = chain.then(function () { return loadJs(descriptor); });
    });
    return chain.then(
      function () {
        releaseStart();
        return whenGraphEventsReady(manifest.graph);
      },
      function (err) {
        releaseStart();
        cancelStagedCalls(calls, err);
        throw err;
      }
    ).then(function () {
      applyStagedManifest(manifest, calls);
    });
  };

  var preflightAdoptionDependency = function (manifest, revision) {
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest) || manifest.graph !== revision) {
      throw new TypeError("[Citry] dependency manifest does not match its prepared ownership revision.");
    }
    var requireArray = function (value, label) {
      if (value == null) return [];
      if (!Array.isArray(value)) throw new TypeError("[Citry] dependency manifest field '" + label + "' must be an array.");
      return value;
    };
    var requireObject = function (value, label) {
      if (value == null) return {};
      if (typeof value !== "object" || Array.isArray(value)) {
        throw new TypeError("[Citry] dependency manifest field '" + label + "' must be an object.");
      }
      return value;
    };
    var decode = function (value, label) {
      if (typeof value !== "string") {
        throw new TypeError("[Citry] dependency manifest field '" + label + "' must contain base64 strings.");
      }
      return fromBase64(value);
    };
    var decodeDescriptor = function (encoded, label) {
      var descriptor = JSON.parse(decode(encoded, label));
      if (
        !descriptor || typeof descriptor !== "object" || Array.isArray(descriptor) ||
        typeof descriptor.tag !== "string" ||
        (descriptor.attrs != null && (typeof descriptor.attrs !== "object" || Array.isArray(descriptor.attrs))) ||
        (descriptor.content != null && typeof descriptor.content !== "string")
      ) {
        throw new TypeError("[Citry] dependency asset descriptor is invalid.");
      }
      // Prove tag and attribute names in a non-HTML namespace. An HTML
      // custom-element constructor can run at document.createElement time,
      // before ownership adoption has committed, even while detached.
      validateDescriptorStructure(descriptor);
      return descriptor;
    };
    var state = ownershipStates.get(revision);
    if (!state) throw new TypeError("[Citry] dependency manifest refers to an unknown prepared graph.");
    var seen = new Set();
    requireArray(manifest.calls, "calls").forEach(function (call) {
      if (!Array.isArray(call) || call.length !== 3) {
        throw new TypeError("[Citry] graph-linked dependency call must be a three-item tuple.");
      }
      var classId = decode(call[0], "calls");
      var renderId = decode(call[1], "calls");
      if (seen.has(renderId)) {
        throw new TypeError("[Citry] graph-linked dependency manifest repeats callback render id '" + renderId + "'.");
      }
      seen.add(renderId);
      resolveOwnershipRoute(revision, renderId, classId);
      if (call[2] != null) decode(call[2], "calls");
    });

    requireArray(manifest.cssInstances, "cssInstances").forEach(function (entry) {
      if (!Array.isArray(entry) || entry.length !== 2) {
        throw new TypeError("[Citry] graph-linked css instance must be a two-item tuple.");
      }
      var classId = decode(entry[0], "cssInstances");
      var renderId = decode(entry[1], "cssInstances");
      resolveOwnershipRoute(revision, renderId, classId);
    });

    var markLoaded = requireObject(manifest.markLoaded, "markLoaded");
    ["css", "js"].forEach(function (kind) {
      requireArray(markLoaded[kind], "markLoaded." + kind).forEach(function (encoded) {
        decode(encoded, "markLoaded." + kind);
      });
    });

    var fetch = requireObject(manifest.fetch, "fetch");
    var preparedFetch = { css: [], js: [] };
    ["css", "js"].forEach(function (kind) {
      requireArray(fetch[kind], "fetch." + kind).forEach(function (entry) {
        if (!Array.isArray(entry) || entry.length !== 2) {
          throw new TypeError("[Citry] graph-linked dependency fetch must be a two-item tuple.");
        }
        var encoded = entry[0];
        var descriptor = decodeDescriptor(encoded, "fetch." + kind);
        var owners = entry[1];
        var decodedOwners = null;
        if (owners !== null) {
          if (!Array.isArray(owners) || !owners.length) {
            throw new TypeError("[Citry] graph-linked dependency owners must be null or a non-empty array.");
          }
          decodedOwners = owners.map(function (owner) { return decode(owner, "fetch." + kind + ".owners"); });
          var priorOwner = null;
          decodedOwners.forEach(function (owner) {
            if (!state.renderLinks.has(owner)) {
              throw new TypeError("[Citry] graph-linked dependency owner '" + owner + "' is absent from its graph.");
            }
            if (priorOwner !== null && owner <= priorOwner) {
              throw new TypeError("[Citry] graph-linked dependency owners must be unique and sorted.");
            }
            priorOwner = owner;
          });
        }
        preparedFetch[kind].push({ encoded: encoded, descriptor: descriptor, owners: decodedOwners });
      });
    });
    if (!Array.isArray(manifest.beforeManifest)) {
      throw new TypeError("[Citry] graph-linked dependency field 'beforeManifest' must be an array.");
    }
    var preparedBeforeManifest = manifest.beforeManifest.map(function (encoded) {
      return decodeDescriptor(encoded, "beforeManifest");
    });
    return {
      graph: revision,
      markLoaded: manifest.markLoaded,
      fetch: preparedFetch,
      calls: manifest.calls,
      cssInstances: manifest.cssInstances,
      beforeManifest: preparedBeforeManifest,
    };
  };

  var acceptedDependencyManifest = function (transaction, prepared) {
    var accepted = transaction.plan && transaction.plan.acceptedIncomingRenderIds;
    if (!(accepted instanceof Set)) accepted = new Set(transaction.state.renderLinks.keys());
    var hasAccepted = accepted.size > 0;
    var keepOwned = function (entry) {
      if (entry.owners === null) return hasAccepted;
      return entry.owners.some(function (owner) { return accepted.has(owner); });
    };
    var keepRenderTuple = function (entry) {
      return Array.isArray(entry) && typeof entry[1] === "string" && accepted.has(fromBase64(entry[1]));
    };
    return {
      graph: prepared.graph,
      markLoaded: hasAccepted ? prepared.markLoaded : { js: [], css: [] },
      fetch: {
        js: prepared.fetch.js.filter(keepOwned).map(function (entry) { return entry.encoded; }),
        css: prepared.fetch.css.filter(keepOwned).map(function (entry) { return entry.encoded; }),
      },
      calls: prepared.calls.filter(keepRenderTuple),
      cssInstances: prepared.cssInstances.filter(keepRenderTuple),
      beforeManifest: hasAccepted ? prepared.beforeManifest : [],
    };
  };

  var activateBeforeManifest = function (descriptors, tag) {
    descriptors.forEach(function (descriptor) {
      var element = createElement(descriptor);
      if (tag && tag.parentNode) tag.parentNode.insertBefore(element, tag);
      else document.body.appendChild(element);
    });
  };

  var applyAdoptionDependency = function (transaction, manifest, tag) {
    if (!transaction || transaction.status !== "committed" || manifest.graph !== transaction.revision) {
      return Promise.reject(new TypeError("[Citry] dependency adoption requires a committed matching graph."));
    }
    if (consumedGraphDependencies.has(transaction.revision)) {
      return Promise.reject(new TypeError("[Citry] dependency manifest repeats ownership graph " + transaction.revision + "."));
    }
    if (tag) {
      processedDependencyTags.add(tag);
      tag.dataset.citryProcessed = "";
    }
    consumedGraphDependencies.add(transaction.revision);
    var acceptedManifest = acceptedDependencyManifest(transaction, manifest);
    var calls = stageManifestCalls(acceptedManifest, transaction.revision);
    activateBeforeManifest(acceptedManifest.beforeManifest, tag);
    return applyGraphComponentScripts(acceptedManifest, calls);
  };

  var beginGraphEvents = function (revision) {
    if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision)) {
      throw new TypeError("[Citry] Events manifest carries an invalid graph revision.");
    }
    if (graphEvents.has(revision)) {
      throw new TypeError("[Citry] ownership graph " + revision + " already has an Events transaction.");
    }
    var transaction = {
      state: "pending",
      error: null,
      waiters: [],
      releaseStart: alpineApi._holdStart(),
    };
    graphEvents.set(revision, transaction);
  };

  var finishGraphEvents = function (revision, error) {
    var transaction = graphEvents.get(revision);
    if (!transaction || transaction.state !== "pending") {
      throw new TypeError("[Citry] ownership graph " + revision + " has no pending Events transaction.");
    }
    transaction.state = error == null ? "ready" : "failed";
    transaction.error = error;
    transaction.waiters.forEach(function (waiter) {
      if (error == null) waiter.resolve();
      else waiter.reject(error);
    });
    transaction.waiters = [];
    transaction.releaseStart();
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var whenGraphEventsReady = function (revision) {
    var transaction = graphEvents.get(revision);
    // No Events manifest was claimed for this graph. Components without
    // Events still use graph-linked dependency callbacks.
    if (!transaction) return Promise.resolve();
    if (transaction.state === "ready") return Promise.resolve();
    if (transaction.state === "failed") return Promise.reject(transaction.error);
    return new Promise(function (resolve, reject) {
      transaction.waiters.push({ resolve: resolve, reject: reject });
    });
  };

  var loadComponentScripts = function (manifest) {
    if (manifest.graph != null) {
      if (typeof manifest.graph !== "string" || !/^[0-9a-f]{64}$/.test(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest carries an invalid graph revision.");
      }
      if (graphFailures.has(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest requires a failed ownership graph " + manifest.graph + ".");
      }
      if (!ownershipGraphs.has(manifest.graph)) {
        var blocked = graphBlockedManifests.get(manifest.graph) || [];
        blocked.push(manifest);
        graphBlockedManifests.set(manifest.graph, blocked);
        return;
      }
      if (consumedGraphDependencies.has(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest repeats ownership graph " + manifest.graph + ".");
      }
      var graphFetch = manifest.fetch;
      var hasOwnerAwareFetch = graphFetch && typeof graphFetch === "object" && ["js", "css"].some(function (kind) {
        return Array.isArray(graphFetch[kind]) && graphFetch[kind].some(Array.isArray);
      });
      var isTransactionalDependency = hasOwnerAwareFetch || Object.prototype.hasOwnProperty.call(manifest, "beforeManifest");
      var acceptedManifest = manifest;
      if (isTransactionalDependency) {
        var prepared = preflightAdoptionDependency(manifest, manifest.graph);
        acceptedManifest = acceptedDependencyManifest({
          plan: null,
          state: ownershipStates.get(manifest.graph),
        }, prepared);
      }
      consumedGraphDependencies.add(manifest.graph);
      // Activate and hold every callback branch in this observer turn. The
      // actual assets and Events adoption may settle in later tasks.
      var calls;
      try {
        calls = stageManifestCalls(acceptedManifest, manifest.graph);
        if (isTransactionalDependency) activateBeforeManifest(acceptedManifest.beforeManifest, null);
      } catch (err) {
        console.error("[Citry] discarded graph-linked dependency manifest:", err);
        return;
      }
      // Let the Events manifest observer adopt this graph-linked transaction
      // before component callbacks can run. Mutation observers and graph
      // waiter promise jobs finish before this next task. Keeping dependency
      // script injection out of the insertion microtask also lets the host's
      // fragment-insertion promise settle normally.
      setTimeout(function () {
        Promise.resolve().then(function () {
          return applyGraphComponentScripts(acceptedManifest, calls);
        }).then(
          function () {},
          function (err) {
            cancelStagedCalls(calls, err);
            console.error("[Citry] discarded graph-linked dependency manifest:", err);
          }
        );
      }, 0);
      return;
    }
    applyComponentScripts(manifest).catch(function (err) {
      console.error("[Citry] discarded dependency manifest:", err);
    });
  };

  var processManifestTag = function (el) {
    if (processedDependencyTags.has(el)) return;
    processedDependencyTags.add(el);
    // Kept as an observable diagnostic marker only. Identity comes from the
    // WeakSet above, so a clone that copies this attribute is still processed.
    el.dataset.citryProcessed = "";
    try {
      loadComponentScripts(JSON.parse(el.textContent));
    } catch (err) {
      console.error("[Citry] failed to process dependency manifest:", err);
    }
  };

  var commitGraphTag = function (el) {
    var manifest = null;
    try {
      rejectStructuralComponentClones(document);
      manifest = JSON.parse(el.textContent);
      commitOwnershipManifest(manifest);
    } catch (err) {
      failOwnershipManifest(manifest && manifest.revision, err);
      var reason = err && err.message ? err.message : String(err);
      console.error("[Citry] failed to process ownership graph manifest: " + reason);
    }
  };

  var commitDeferredGraphTag = function (el) {
    if (!deferredGraphTags.delete(el)) return;
    commitGraphTag(el);
  };

  var flushDeferredGraphTags = function () {
    Array.from(deferredGraphTags).forEach(commitDeferredGraphTag);
  };

  var processGraphTag = function (el) {
    if (processedGraphTags.has(el)) return;
    processedGraphTags.add(el);
    el.dataset.citryGraphProcessed = "";
    // A document can place <c-js> inside the component it closes. During HTML
    // parsing the graph tag then appears before that outer instance's closing
    // cap. Fragments arrive as complete DOM insertions, but parser-created
    // documents must wait until all trailing caps have landed.
    if (document.readyState === "loading") {
      deferredGraphTags.add(el);
      document.addEventListener("DOMContentLoaded", function () { commitDeferredGraphTag(el); }, { once: true });
      return;
    }
    commitGraphTag(el);
  };

  var manifestSelector = 'script[type="application/json"][data-citry]';
  var graphSelector = 'script[type="application/json"][data-citry-graph]';

  var processInsertedGraphs = function (node) {
    if (node.matches && node.matches(graphSelector)) processGraphTag(node);
    else if (node.querySelectorAll) node.querySelectorAll(graphSelector).forEach(processGraphTag);
  };

  var processInsertedDependencies = function (node) {
    if (node.matches && node.matches(manifestSelector)) processManifestTag(node);
    else if (node.querySelectorAll) node.querySelectorAll(manifestSelector).forEach(processManifestTag);
  };

  new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        processInsertedGraphs(node);
      });
    });
    // Extension consumers, including Events, see the batch after every graph
    // tag has staged and before any graph-linked dependency manifest runs.
    dispatchAlpineMutations(mutations);
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        processInsertedDependencies(node);
      });
    });
    // Any DOM change may have removed an instance's last element, or swapped a
    // persisting node's data-cid-<id> for a new one; reconcile on the next
    // microtask. Watching attributes is what makes the in-place id swap
    // visible: the attribute name carries the id, so it cannot be named in an
    // attributeFilter ahead of time.
    scheduleSweep();
  }).observe(document, { childList: true, subtree: true, attributes: true, characterData: true });

  // ----- public surface -----

  globalThis.Citry = globalThis.Citry || {};
  globalThis.Citry.alpine = alpineApi;
  globalThis.Citry.manager = {
    registerComponent: registerComponent,
    registerComponentData: registerComponentData,
    callComponent: callComponent,
    decorateContext: decorateContext,
    loadJs: loadJs,
    loadCss: loadCss,
    markScriptLoaded: markScriptLoaded,
    isScriptLoaded: isScriptLoaded,
    ownership: {
      has: function (revision) { return ownershipGraphs.has(revision); },
      get: function (revision) { return ownershipGraphs.get(revision) || null; },
      whenReady: function (revision) {
        if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision)) {
          return Promise.reject(new TypeError("[Citry] graph: whenReady needs a lowercase SHA-256 revision."));
        }
        if (ownershipGraphs.has(revision)) return Promise.resolve(ownershipGraphs.get(revision));
        if (graphFailures.has(revision)) return Promise.reject(graphFailures.get(revision));
        if (seenOwnershipRevisions.has(revision)) {
          return Promise.reject(new TypeError("[Citry] graph: ownership revision " + revision + " is retired."));
        }
        return new Promise(function (resolve, reject) {
          var waiters = graphWaiters.get(revision) || [];
          waiters.push({ resolve: resolve, reject: reject });
          graphWaiters.set(revision, waiters);
        });
      },
      revisions: function () { return Array.from(ownershipGraphs.keys()); },
      forRender: function (revision, renderId) {
        if (!ownershipGraphs.has(revision)) return null;
        try {
          return resolveOwnershipRoute(revision, renderId, null);
        } catch (_err) {
          return null;
        }
      },
      anchors: function () { return Array.from(browserAnchors.values()); },
      _ownerForElement: fillSourceOwnerForElement,
      _replace: replaceOwnership,
      _morphRange: morphOwnershipRange,
      _prepareAdoption: prepareOwnershipAdoption,
      _adoptionRoot: adoptionRoot,
      _planAdoption: planOwnershipAdoption,
      _planPlacement: planOwnershipPlacement,
      _applyAdoptionPlan: applyOwnershipAdoptionPlan,
      _activateAdoption: activateOwnershipAdoption,
      _commitAdoption: commitOwnershipAdoption,
      _abortAdoption: abortOwnershipAdoption,
      _discardAdoption: discardOwnershipAdoption,
      _rejectAdoption: failOwnershipManifest,
      _mintPlacement: mintRuntimePlacementId,
      _placementIds: function (generalAnchor) {
        return livePhysicalPlacementsForAnchor(generalAnchor).map(function (entry) {
          return entry.physical.placementId;
        });
      },
      _placementRoots: function (generalAnchor) {
        return livePhysicalPlacementsForAnchor(generalAnchor).map(function (entry) {
          return physicalRangeRoots(entry.physical, entry.link.record.renderId);
        });
      },
      _hasPlacements: function (generalAnchor) {
        return this._placementIds(generalAnchor).length > 0;
      },
      _relatedEvents: function (generalAnchor) {
        var source = null;
        ownershipStates.forEach(function (state) {
          state.renderLinks.forEach(function (link) {
            if (!source && link.link.active && link.link.anchor === generalAnchor) source = link.logicalState;
          });
        });
        if (!source) return [];
        var isAncestor = function (ancestor, child) {
          for (var current = child; current; current = current.parentLogical) {
            if (current === ancestor) return true;
          }
          return false;
        };
        var related = [];
        ownershipStates.forEach(function (state) {
          state.renderLinks.forEach(function (link) {
            if (!link.link.active || !link.anchorState.events) return;
            if (
              link.logicalState === source ||
              isAncestor(source, link.logicalState) ||
              isAncestor(link.logicalState, source)
            ) related.push(link.anchorState.events);
          });
        });
        return related;
      },
      _morphPlacement: function (generalAnchor, index, html, options) {
        var selected = null;
        ownershipStates.forEach(function (state, revision) {
          if (selected || !ownershipGraphs.has(revision)) return;
          state.renderLinks.forEach(function (link) {
            if (selected || link.link.anchor !== generalAnchor) return;
            var placements = physicalRangesForKey(state, link.record.key).filter(function (physical) {
              return physicalRangeIsLive(state, physical);
            });
            if (placements[index]) {
              selected = { state: state, revision: revision, link: link, physical: placements[index] };
            }
          });
        });
        if (!selected) throw new TypeError("[Citry] graph: runtime placement morph target is not live.");
        options = options || {};
        options.physical = selected.physical;
        alpineHookCounts.morph += 1;
        var physical = morphOwnershipRange(selected.revision, selected.link.record.key, html, options);
        return { end: physical.end, roots: physicalRangeElements(physical) };
      },
      _replacePlacement: function (generalAnchor, index, html) {
        var selected = null;
        ownershipStates.forEach(function (state, revision) {
          if (selected || !ownershipGraphs.has(revision)) return;
          state.renderLinks.forEach(function (link) {
            if (selected || link.link.anchor !== generalAnchor) return;
            var placements = physicalRangesForKey(state, link.record.key).filter(function (physical) {
              return physicalRangeIsLive(state, physical);
            });
            if (placements[index]) {
              selected = { state: state, revision: revision, link: link, physical: placements[index] };
            }
          });
        });
        if (!selected) throw new TypeError("[Citry] graph: runtime placement replacement target is not live.");
        var physical = replaceOwnershipRange(selected.revision, selected.link.record.key, html, {
          physical: selected.physical,
        });
        return { end: physical.end, roots: physicalRangeElements(physical) };
      },
      _expectRetirement: function (renderIds) {
        var wanted = new Set(Array.isArray(renderIds) ? renderIds : []);
        ownershipStates.forEach(function (state, revision) {
          if (!ownershipGraphs.has(revision)) return;
          wanted.forEach(function (renderId) {
            var link = state.renderLinks.get(renderId);
            if (!link) return;
            physicalRangesForKey(state, link.record.key).forEach(function (physical) {
              expectedPhysicalRetirements.add(physical);
              ownershipStates.forEach(function (candidateState) {
                candidateState.physicalPlacements.forEach(function (placements) {
                  placements.forEach(function (candidate) {
                    if (
                      candidate !== physical &&
                      physicalRangeContainsNode(physical, candidate.start) &&
                      physicalRangeContainsNode(physical, candidate.end)
                    ) expectedPhysicalRetirements.add(candidate);
                  });
                });
              });
            });
          });
        });
      },
      _claimTag: function (el) {
        if (!el || !el.matches) return;
        if (el.matches(graphSelector)) processedGraphTags.add(el);
        if (el.matches(manifestSelector)) processedDependencyTags.add(el);
      },
      _preflightDependency: preflightAdoptionDependency,
      _applyDependency: applyAdoptionDependency,
      _preflightEvents: preflightEventsBridge,
      _attachEvents: attachEventsBridge,
      _detachEvents: detachEventsBridge,
      _transitionEvents: transitionEventsBridge,
      _retireEvents: retireEventsBridge,
      _isLive: isOwnershipAnchorLive,
      _beginEvents: beginGraphEvents,
      _finishEvents: finishGraphEvents,
      _schedulePrune: scheduleOwnershipPrune,
    },
    _loadComponentScripts: loadComponentScripts,
    _stageOwnershipManifest: stageOwnershipManifest,
  };

  // Manifests that were already in the document before this script ran.
  var drainClientManifests = function () {
    document.querySelectorAll(graphSelector).forEach(processGraphTag);
    // A provider's empty-batch path drains its own already-present manifest
    // tags. This is what lets the one Alpine init interceptor close a late
    // fragment race synchronously.
    dispatchAlpineMutations([]);
    document.querySelectorAll(manifestSelector).forEach(processManifestTag);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", drainClientManifests);
  } else {
    drainClientManifests();
  }
})();
