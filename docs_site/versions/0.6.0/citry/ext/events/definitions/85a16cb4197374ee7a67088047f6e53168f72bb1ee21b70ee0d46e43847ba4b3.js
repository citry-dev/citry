(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("input", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), null, 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, ['checked','value']]
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9a4826fdbd426eba9635a88233d6dc82dc0ff0dafbd32a4471d49ff7954ef1bf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-3bed3ea0af7a1780", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotb13ff7dbfcd5f34a'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotb13ff7dbfcd5f34a", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["129018bdb62ddf7d3004fd2406c69ecf845810b4574aabc6e73eddfb2027f47e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_date_input_0233fc63 = _resolveComponent("citry-c-date-input-0233fc63")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createElementBlock("section", { class: "date-input-demo-stack" }, [
    (_openBlock(), _createBlock(_component_citry_c_date_input_0233fc63, {
      value: _ctx.day,
      onInput: $event => (_ctx.last=$event.currentTarget.value),
      "citry-id": _ctx.$citryPrepared.calls.citryCall51d270ad4cb2d2f5.id,
      key: _ctx.$citryPrepared.calls.citryCall51d270ad4cb2d2f5.key
    }, null, 8 /* PROPS */, ["value", "onInput", "citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld4ebc6e966261426.id,
      key: _ctx.$citryPrepared.calls.citryCalld4ebc6e966261426.key
    }, {
      ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
        _createElementVNode("button", {
          type: "button",
          onClick: $event => (_ctx.day='2026-08-22')
        }, "Set 22 August", 8 /* PROPS */, ["onClick"]),
        _createElementVNode("button", {
          type: "button",
          onClick: $event => (_ctx.day=null)
        }, "Clear", 8 /* PROPS */, ["onClick"])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.last)
    }, "No native input yet", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c9e3081322c7134570545649d46ea5d87861900c184bee57b6aea7b91e71432a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall51d270ad4cb2d2f5","typeKey":"CDateInput_135afc","componentTag":"citry-c-date-input-0233fc63","bindings":[{"kind":"prop","name":":value","value":"day","sourceStart":72,"sourceEnd":84},{"kind":"event","name":"@input","value":"last=$event.currentTarget.value","sourceStart":85,"sourceEnd":125}]},{"localId":"citryCalld4ebc6e966261426","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_date_input_c884fcf8 = _resolveComponent("citry-controlled-date-input-c884fcf8")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_date_input_c884fcf8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfb1d7758ab49dfdc.id,
      key: _ctx.$citryPrepared.calls.citryCallfb1d7758ab49dfdc.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f72d4053a18fd804fe2017b7e494c93a5851e28a427ef2bf85613697105f6b2a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfb1d7758ab49dfdc","typeKey":"ControlledDateInput_102e67","componentTag":"citry-controlled-date-input-c884fcf8","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
