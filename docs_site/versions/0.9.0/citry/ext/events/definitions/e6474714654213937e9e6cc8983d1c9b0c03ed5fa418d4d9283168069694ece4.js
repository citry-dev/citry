(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("label", _mergeProps({ "data-citry-ui-part": "drop-target" }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-drop-target__input",
      type: "file",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", {
      class: "cui-drop-target__label",
      "data-citry-ui-part": "label"
    }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
    _createElementVNode("span", {
      class: "cui-drop-target__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot65cc68dfb3b08a1c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot65cc68dfb3b08a1c", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0f4a3244b3710432e36adfad0d72a1797d63253a09a11f2483933af5ca175429"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_drop_target_302ca9ad = _resolveComponent("citry-c-drop-target-302ca9ad")
  
  return (_openBlock(), _createBlock(_component_citry_c_drop_target_302ca9ad, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall22ec2949bb27ff58.id,
    key: _ctx.$citryPrepared.calls.citryCall22ec2949bb27ff58.key
  }, {
    ['citrySlot65cc68dfb3b08a1c']: _withCtx(() => [
      _createTextVNode(" CSV, PDF, or field images ")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["490e782a79900966f3102918345300700c7a15cf5c88dd7a0a92fb0364a1af8e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall22ec2949bb27ff58","typeKey":"CDropTarget_afd2f8","componentTag":"citry-c-drop-target-302ca9ad","bindings":[],"fills":[{"name":"citrySlot65cc68dfb3b08a1c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_customized_files_2ff55bfe = _resolveComponent("citry-customized-files-2ff55bfe")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_customized_files_2ff55bfe, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall48b66b0f4cf50cd7.id,
      key: _ctx.$citryPrepared.calls.citryCall48b66b0f4cf50cd7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["24fa42b4fbb5cbc36797bca9f60e0936bc73f05c77b73e79db3304fba0ef3ae0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall48b66b0f4cf50cd7","typeKey":"CustomizedFiles_e045e1","componentTag":"citry-customized-files-2ff55bfe","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
