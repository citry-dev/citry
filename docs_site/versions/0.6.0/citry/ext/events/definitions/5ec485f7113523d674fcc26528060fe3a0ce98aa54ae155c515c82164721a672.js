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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["813ec2839f8e22774ea60a3aa5cce40ee2536816a8098ddc85050f9af752f01c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      (_ctx.$citryPrepared.selectedSlots['citrySlot20df656fe6df3687'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot20df656fe6df3687", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["86483c86ad7fb6b00b213b70cbda3f82fdfbee3d7200b8b7d88fb0ed3125dfbc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-delivery" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Same-origin archive"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall535693469417acac.id,
        key: _ctx.$citryPrepared.calls.citryCall535693469417acac.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("p", null, "Native request policy applies before src. Citry does not proxy bytes.")
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Credential-free CORS mode"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalled9ff7c7982a159b.id,
        key: _ctx.$citryPrepared.calls.citryCalled9ff7c7982a159b.key
      }, {
        ['citrySlot20df656fe6df3687']: _withCtx(() => [
          _createTextVNode("Cross-origin plate unavailable in this preview")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("p", null, "The response still needs matching server headers for CORS use.")
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "CSP and unavailable resources"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalle928bd5f2a3988b0.id,
        key: _ctx.$citryPrepared.calls.citryCalle928bd5f2a3988b0.key
      }, {
        ['citrySlot20df656fe6df3687']: _withCtx(() => [
          _createTextVNode("Blocked or unavailable plate")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("p", null, "Browser CSP remains authoritative and failures settle as image error.")
    ]),
    _createElementVNode("aside", null, [
      _createElementVNode("h3", null, "Application trust boundary"),
      _createElementVNode("ul", null, [
        _createElementVNode("li", null, "Relative, HTTPS, data, blob, raster, and SVG URLs remain consumer-owned."),
        _createElementVNode("li", null, "Do not log signed URLs, currentSrc, query strings, or response bodies."),
        _createElementVNode("li", null, "Blob lifetime, data-URL size, metadata privacy, and remote tracking are application policy.")
      ]),
      _createElementVNode("output", null, "Safe request summary: request modes configured; URLs omitted")
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ebce3e7ed1418f96a8aac6e1f89271e13add7c836770bfceafeba974154380ab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall535693469417acac","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCalled9ff7c7982a159b","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[],"fills":[{"name":"citrySlot20df656fe6df3687","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle928bd5f2a3988b0","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[],"fills":[{"name":"citrySlot20df656fe6df3687","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_delivery_and_security_c3c10618 = _resolveComponent("citry-image-delivery-and-security-c3c10618")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_delivery_and_security_c3c10618, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0d40f8dfca1ef3c5.id,
      key: _ctx.$citryPrepared.calls.citryCall0d40f8dfca1ef3c5.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["0b864f1834c8286b64a73ee146b36ed45e46e639bce8d0757b0cb3a9e33eeceb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0d40f8dfca1ef3c5","typeKey":"ImageDeliveryAndSecurity_c75620","componentTag":"citry-image-delivery-and-security-c3c10618","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
