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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3fbcabab908f3f069c568a4ccc040fcd9ddb0be09f10391b6271af0e24fd413f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-toggle-group",
    "data-citry-ui-part": "toggle-group",
    role: "group"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot00531573a6c1f4c4'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot00531573a6c1f4c4", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a8089d3a74e8f830e5a5d8108f2ad07a25e440d680274508501c083626fbed43"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_toggle_134d0afe = _resolveComponent("citry-c-toggle-134d0afe")
  const _component_citry_c_toggle_group_8c174217 = _resolveComponent("citry-c-toggle-group-8c174217")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createTextVNode("Current view: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.view)
      }, null, 8 /* PROPS */, ["textContent"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_toggle_group_8c174217, {
      value: _ctx.view,
      onValueChange: (next) => _ctx.view = next,
      "citry-id": _ctx.$citryPrepared.calls.citryCallcd0547d729734fd6.id,
      key: _ctx.$citryPrepared.calls.citryCallcd0547d729734fd6.key
    }, {
      ['citrySlot00531573a6c1f4c4']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_toggle_134d0afe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall664b8565e1a5f846.id,
          key: _ctx.$citryPrepared.calls.citryCall664b8565e1a5f846.key
        }, {
          ['citrySlot61a887458dd1621f']: _withCtx(() => [
            _createTextVNode("Sky")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_toggle_134d0afe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall873fbefa63d1cb78.id,
          key: _ctx.$citryPrepared.calls.citryCall873fbefa63d1cb78.key
        }, {
          ['citrySlot61a887458dd1621f']: _withCtx(() => [
            _createTextVNode("Spectrum")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["value", "onValueChange", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["83d4c6fd65ce8a630bcfe847350da3a8ae7c92d355fb9e1f7a99810541cfaa6a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall664b8565e1a5f846","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall873fbefa63d1cb78","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcd0547d729734fd6","typeKey":"CToggleGroup_81ba63","componentTag":"citry-c-toggle-group-8c174217","bindings":[{"kind":"prop","name":":value","value":"view","sourceStart":99,"sourceEnd":112},{"kind":"prop","name":":onValueChange","value":"(next) => view = next","sourceStart":113,"sourceEnd":151}],"fills":[{"name":"citrySlot00531573a6c1f4c4","localDescendants":["citryCall664b8565e1a5f846","citryCall873fbefa63d1cb78"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_toggle_97a61a51 = _resolveComponent("citry-controlled-toggle-97a61a51")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_toggle_97a61a51, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle1ea4401dda29a8a.id,
      key: _ctx.$citryPrepared.calls.citryCalle1ea4401dda29a8a.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5173f6de0d85f4f26a4d4e7622110062eecbd485671738fa5330f618ebbf065f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle1ea4401dda29a8a","typeKey":"ControlledToggle_e66dc6","componentTag":"citry-controlled-toggle-97a61a51","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
