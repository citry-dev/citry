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
window.__citryRuntimeDefinitions["e9353d70b32d3f839458b5dd563e573f6aa54a77ce091bd051043a727d230424"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall84ae91bac95194c8","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallea898a6e180f130c","typeKey":"CToggle_5d9b5a","componentTag":"citry-c-toggle-134d0afe","bindings":[],"fills":[{"name":"citrySlot61a887458dd1621f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1bdda6ab87bf2b0e","typeKey":"CToggleGroup_81ba63","componentTag":"citry-c-toggle-group-8c174217","bindings":[{"kind":"prop","name":":value","value":"view","sourceStart":99,"sourceEnd":112},{"kind":"prop","name":":onValueChange","value":"(next) => view = next","sourceStart":113,"sourceEnd":151}],"fills":[{"name":"citrySlot00531573a6c1f4c4","localDescendants":["citryCall84ae91bac95194c8","citryCallea898a6e180f130c"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_toggle_ced718dd = _resolveComponent("citry-controlled-toggle-ced718dd")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_toggle_ced718dd, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall29bd27d763337f7e.id,
      key: _ctx.$citryPrepared.calls.citryCall29bd27d763337f7e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["00b2288bd5a5d855a0f6a8c0eed4f9b4572fb37e986c678d1e71705e35d30708"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall29bd27d763337f7e","typeKey":"ControlledToggle_31f6d6","componentTag":"citry-controlled-toggle-ced718dd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
