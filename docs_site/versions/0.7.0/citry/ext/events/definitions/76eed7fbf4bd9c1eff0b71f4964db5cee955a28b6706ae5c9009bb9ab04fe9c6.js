(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6d5dd57f6ce194793a91da927bd3418dd400353843d7b5428c71f7c6e109ec2d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-image",
    "data-citry-ui-part": "image-root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("img", _mergeProps({ "data-citry-ui-part": "image" }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      hidden: "",
      inert: "",
      "aria-hidden": "true",
      "data-citry-ui-part": "fallback"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot3b118b957ecc918a'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot3b118b957ecc918a", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b9d6ccaea5b9cc19a71f209c7103f5b36d944e718f8d020d739dccff83424116"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-delivery" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Same-origin archive"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall99781d4233d1f319.id,
        key: _ctx.$citryPrepared.calls.citryCall99781d4233d1f319.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("p", null, "Native request policy applies before src. Citry does not proxy bytes.")
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Credential-free CORS mode"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall4f060224cf2aa5ef.id,
        key: _ctx.$citryPrepared.calls.citryCall4f060224cf2aa5ef.key
      }, {
        ['citrySlot3b118b957ecc918a']: _withCtx(() => [
          _createTextVNode("Cross-origin plate unavailable in this preview")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("p", null, "The response still needs matching server headers for CORS use.")
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "CSP and unavailable resources"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall12eb8743b6ea6000.id,
        key: _ctx.$citryPrepared.calls.citryCall12eb8743b6ea6000.key
      }, {
        ['citrySlot3b118b957ecc918a']: _withCtx(() => [
          _createTextVNode("Blocked or unavailable plate")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("p", null, "Browser CSP remains authoritative and failures settle as image error.")
    ]),
    _createElementVNode("aside", null, [
      _createElementVNode("h3", null, "Application trust boundary"),
      _createElementVNode("ul", null, [
        _createElementVNode("li", null, "Relative, HTTPS, data image, blob, raster, and SVG URLs remain consumer-owned."),
        _createElementVNode("li", null, "Do not log signed URLs, currentSrc, query strings, or response bodies."),
        _createElementVNode("li", null, "Blob lifetime, data-URL size, metadata privacy, and remote tracking are application policy.")
      ]),
      _createElementVNode("output", null, "Safe request summary: request modes configured; URLs omitted")
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1af480488376e979a8eea24706ab19773f3833ff8397dcd5f153b0589c704ec0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall99781d4233d1f319","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCall4f060224cf2aa5ef","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[],"fills":[{"name":"citrySlot3b118b957ecc918a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall12eb8743b6ea6000","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[],"fills":[{"name":"citrySlot3b118b957ecc918a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_delivery_and_security_847776c5 = _resolveComponent("citry-image-delivery-and-security-847776c5")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_delivery_and_security_847776c5, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7948b399a15a07ac.id,
      key: _ctx.$citryPrepared.calls.citryCall7948b399a15a07ac.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e0bf051798e14d9c634e1bb1208155a521a1f92bbf095de0327674d88fddb324"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7948b399a15a07ac","typeKey":"ImageDeliveryAndSecurity_28369d","componentTag":"citry-image-delivery-and-security-847776c5","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
