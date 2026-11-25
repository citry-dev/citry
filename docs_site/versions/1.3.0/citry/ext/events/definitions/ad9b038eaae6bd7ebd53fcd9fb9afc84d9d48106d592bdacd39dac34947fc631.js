(function(Vue){
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-8bc33b5d2375a1c7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotb8dc4e41a0c17789'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotb8dc4e41a0c17789", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3ebb802e10c9e747aee17a3d30b27b12124e60cdf20d71ae31530b47904707e9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-8bc33b5d2375a1c7","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-8bc33b5d2375a1c7","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_grid_80d6d79a = _resolveComponent("citry-c-grid-80d6d79a")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "grid-columns",
    "aria-labelledby": "grid-columns-title"
  }, [
    _createElementVNode("h2", { id: "grid-columns-title" }, "Crystal systems"),
    _createElementVNode("p", null, "Resize the preview to watch one column become two, then four."),
    (_openBlock(), _createBlock(_component_citry_c_grid_80d6d79a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall29ef1d5057be8cec.id,
      key: _ctx.$citryPrepared.calls.citryCall29ef1d5057be8cec.key
    }, {
      ['citrySlotb8dc4e41a0c17789']: _withCtx(() => [
        _createElementVNode("div", { class: "grid-columns__cell" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
        _createElementVNode("div", { class: "grid-columns__cell" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
        _createElementVNode("div", { class: "grid-columns__cell" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
        _createElementVNode("div", { class: "grid-columns__cell" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("h3", null, "Fixed three-column index"),
    (_openBlock(), _createBlock(_component_citry_c_grid_80d6d79a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall08a7faa3c16fcfbd.id,
      key: _ctx.$citryPrepared.calls.citryCall08a7faa3c16fcfbd.key
    }, {
      ['citrySlotb8dc4e41a0c17789']: _withCtx(() => [
        _createElementVNode("div", { class: "grid-columns__cell grid-columns__cell--quiet" }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
        _createElementVNode("div", { class: "grid-columns__cell grid-columns__cell--quiet" }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */),
        _createElementVNode("div", { class: "grid-columns__cell grid-columns__cell--quiet" }, _toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["42181c2173a2050ec8721b25fb22dd858dbfc78a9bdff9eeb9f01b011beec605"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall29ef1d5057be8cec","typeKey":"CGrid_4b2c8c","componentTag":"citry-c-grid-80d6d79a","bindings":[],"fills":[{"name":"citrySlotb8dc4e41a0c17789","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall08a7faa3c16fcfbd","typeKey":"CGrid_4b2c8c","componentTag":"citry-c-grid-80d6d79a","bindings":[],"fills":[{"name":"citrySlotb8dc4e41a0c17789","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_grid_responsive_columns_de255de2 = _resolveComponent("citry-grid-responsive-columns-de255de2")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_grid_responsive_columns_de255de2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2f20f02d6fde6729.id,
      key: _ctx.$citryPrepared.calls.citryCall2f20f02d6fde6729.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0612d5814986c6b7deadbcb68160df40239be6c245d9376bf494342b5ae3971a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2f20f02d6fde6729","typeKey":"GridResponsiveColumns_b30a6b","componentTag":"citry-grid-responsive-columns-de255de2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
