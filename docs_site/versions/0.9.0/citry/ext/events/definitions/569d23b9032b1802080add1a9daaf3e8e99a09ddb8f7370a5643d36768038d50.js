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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c67bc57972168e164de760592b1472311a4d7373958c708da1be9beb4a144fb4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      "citry-id": _ctx.$citryPrepared.calls.citryCall1bdda6ab87bf2b0e.id,
      key: _ctx.$citryPrepared.calls.citryCall1bdda6ab87bf2b0e.key
    }, {
      ['citrySlot00531573a6c1f4c4']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_toggle_134d0afe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall84ae91bac95194c8.id,
          key: _ctx.$citryPrepared.calls.citryCall84ae91bac95194c8.key
        }, {
          ['citrySlot61a887458dd1621f']: _withCtx(() => [
            _createTextVNode("Sky")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_toggle_134d0afe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallea898a6e180f130c.id,
          key: _ctx.$citryPrepared.calls.citryCallea898a6e180f130c.key
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b1ac6256ae803c07e39b06bfb32b329b1f4784b97f694de62c5ab72fabe63850"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall84ae91bac95194c8","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallea898a6e180f130c","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1bdda6ab87bf2b0e","typeKey":"CToggleGroup_81ba63","componentTag":"citry-c-toggle-group-8c174217","bindings":[{"kind":"prop","name":":value","value":"view","sourceStart":99,"sourceEnd":112},{"kind":"prop","name":":onValueChange","value":"(next) => view = next","sourceStart":113,"sourceEnd":151}],"fills":[{"name":"citrySlot00531573a6c1f4c4","localDescendants":["citryCall84ae91bac95194c8","citryCallea898a6e180f130c"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_toggle_a32facea = _resolveComponent("citry-controlled-toggle-a32facea")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_toggle_a32facea, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla9088c0d96b1bd02.id,
      key: _ctx.$citryPrepared.calls.citryCalla9088c0d96b1bd02.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["06b95246f60431885acaf539d846cbbd0c6ed9d8f08410d9008550432f0847dd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla9088c0d96b1bd02","typeKey":"ControlledToggle_eadc7a","componentTag":"citry-controlled-toggle-a32facea","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
