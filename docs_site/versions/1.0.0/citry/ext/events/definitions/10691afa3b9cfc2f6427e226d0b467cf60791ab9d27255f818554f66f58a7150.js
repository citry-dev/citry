(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("label", _mergeProps({
    class: "cui-drop-target",
    "data-citry-ui-part": "drop-target"
  }, _ctx.$citryPrepared.citryAttrs0), [
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
window.__citryRuntimeDefinitions["dce45bf475e215f443432db6da425463c3adf7638949bf615c616a0f0c3c64b1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_drop_target_302ca9ad = _resolveComponent("citry-c-drop-target-302ca9ad")
  
  return (_openBlock(), _createElementBlock("div", null, [
    (_openBlock(), _createBlock(_component_citry_c_drop_target_302ca9ad, {
      onChange: $event => (_ctx.names = [...$event.target.files].map(file => file.name)),
      "citry-id": _ctx.$citryPrepared.calls.citryCallf2ba618e944b3f33.id,
      key: _ctx.$citryPrepared.calls.citryCallf2ba618e944b3f33.key
    }, {
      ['citrySlot65cc68dfb3b08a1c']: _withCtx(() => [
        _createTextVNode(" PDF or image files ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onChange", "citry-id"])),
    _createElementVNode("p", {
      textContent: _toDisplayString(_ctx.names.join(', '))
    }, null, 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2d10624aac16b3f4118386bf8303ca8e7e8b3188f5e5c204cf67cf12a00bbcc8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf2ba618e944b3f33","typeKey":"CDropTarget_afd2f8","componentTag":"citry-c-drop-target-302ca9ad","bindings":[{"kind":"event","name":"@change","value":"names = [...$event.target.files].map(file => file.name)","sourceStart":39,"sourceEnd":104}],"fills":[{"name":"citrySlot65cc68dfb3b08a1c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_file_drop_target_3dd18812 = _resolveComponent("citry-file-drop-target-3dd18812")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_file_drop_target_3dd18812, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb1e996a102b3f209.id,
      key: _ctx.$citryPrepared.calls.citryCallb1e996a102b3f209.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9896ff56534b88c41ca4c4458e654935b78464fdea0c55576e6272b86f3a5859"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb1e996a102b3f209","typeKey":"FileDropTarget_c3a06b","componentTag":"citry-file-drop-target-3dd18812","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
