(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("button", _mergeProps({
    class: "cui-toggle",
    "data-citry-ui-part": "toggle",
    type: "button"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot61a887458dd1621f'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot61a887458dd1621f", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ed0463b80606a79c6acdca34a41d8880fd015ae3a9bb295ded405b159b372d32"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_toggle_134d0afe = _resolveComponent("citry-c-toggle-134d0afe")
  
  return (_openBlock(), _createBlock(_component_citry_c_toggle_134d0afe, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall3bf1ed56e2e86ff7.id,
    key: _ctx.$citryPrepared.calls.citryCall3bf1ed56e2e86ff7.key
  }, {
    ['citrySlot61a887458dd1621f']: _withCtx(() => [
      _createTextVNode("Pin observation")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1df49e00963fa3d143029a1c40a41e1a25794d1d0d50ad2960c1d88f652a2164"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3bf1ed56e2e86ff7","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_standalone_toggle_2a783d93 = _resolveComponent("citry-standalone-toggle-2a783d93")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_standalone_toggle_2a783d93, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1959706ec738c898.id,
      key: _ctx.$citryPrepared.calls.citryCall1959706ec738c898.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6bce13530dcef6d7dbf65d29f64b7cfc77684c082a014cde687538809283cdc8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1959706ec738c898","typeKey":"StandaloneToggle_b45a68","componentTag":"citry-standalone-toggle-2a783d93","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
