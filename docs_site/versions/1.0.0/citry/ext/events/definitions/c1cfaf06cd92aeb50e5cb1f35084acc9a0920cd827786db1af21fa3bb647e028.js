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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_image_dbf87ebd = _resolveComponent("citry-c-image-dbf87ebd")
  
  return (_openBlock(), _createElementBlock("section", { class: "image-priority" }, [
    _createElementVNode("article", null, [
      _createElementVNode("p", { class: "image-priority__eyebrow" }, "Above the fold"),
      _createElementVNode("h3", null, "Tonight's featured field"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall81bc58fb6511171f.id,
        key: _ctx.$citryPrepared.calls.citryCall81bc58fb6511171f.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("p", null, "Reserve high priority for the small number of likely LCP images.")
    ]),
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (_ctx.$refs.archive.scrollIntoView({behavior:'auto'}))
    }, "Scroll to the archive image", 8 /* PROPS */, ["onClick"]),
    _createElementVNode("div", {
      class: "image-priority__spacer",
      "aria-hidden": "true"
    }),
    _createElementVNode("article", {
      ref: "archive",
      id: "image-priority-archive"
    }, [
      _createElementVNode("p", { class: "image-priority__eyebrow" }, "Below the fold"),
      _createElementVNode("h3", null, "Archive plate"),
      (_openBlock(), _createBlock(_component_citry_c_image_dbf87ebd, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalla520f96f5a5b46b7.id,
        key: _ctx.$citryPrepared.calls.citryCalla520f96f5a5b46b7.key
      }, null, 8 /* PROPS */, ["citry-id"])),
      _createElementVNode("p", null, "Lazy loading remains a native hint and needs no data-src indirection.")
    ], 512 /* NEED_PATCH */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d6ceaaa440e7b96dc3ace87ee657b72ec381182dc6ae129b4647687f00c8fed4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall81bc58fb6511171f","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]},{"localId":"citryCalla520f96f5a5b46b7","typeKey":"CImage_2a7af5","componentTag":"citry-c-image-dbf87ebd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_image_loading_priority_6a2a8f30 = _resolveComponent("citry-image-loading-priority-6a2a8f30")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_image_loading_priority_6a2a8f30, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall678ad41f25f87fbe.id,
      key: _ctx.$citryPrepared.calls.citryCall678ad41f25f87fbe.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["41f6125ce7117ba329ff83e7b13a09fb1e437b288f42814dfcf98a8466abef70"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall678ad41f25f87fbe","typeKey":"ImageLoadingPriority_8eea0a","componentTag":"citry-image-loading-priority-6a2a8f30","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
