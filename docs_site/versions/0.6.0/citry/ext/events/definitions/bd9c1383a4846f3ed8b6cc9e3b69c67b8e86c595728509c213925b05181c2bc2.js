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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["31d5684bc09c2bb77bcab5bdb19775c6f7375b842fd93d5869361b47ca3ed9d0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1e95f8251106e5ba8f604bdb1bad0d93706b4c9f0fa224d1e4c72913f02d039b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf2ba618e944b3f33","typeKey":"CDropTarget_afd2f8","componentTag":"citry-c-drop-target-302ca9ad","bindings":[{"kind":"event","name":"@change","value":"names = [...$event.target.files].map(file => file.name)","sourceStart":39,"sourceEnd":104}],"fills":[{"name":"citrySlot65cc68dfb3b08a1c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_file_drop_target_71cc32a8 = _resolveComponent("citry-file-drop-target-71cc32a8")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_file_drop_target_71cc32a8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall266e8639f0d856ec.id,
      key: _ctx.$citryPrepared.calls.citryCall266e8639f0d856ec.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["45a852f74d1cfafbc9c361da4aca9d066b562dd61ec05713d5e25cc8468a8988"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall266e8639f0d856ec","typeKey":"FileDropTarget_cec892","componentTag":"citry-file-drop-target-71cc32a8","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
