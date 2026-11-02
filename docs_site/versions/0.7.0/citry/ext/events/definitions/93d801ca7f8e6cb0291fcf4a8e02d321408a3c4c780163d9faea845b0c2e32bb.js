(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("span", _mergeProps({
    class: "cui-switch",
    "data-citry-ui-part": "switch"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-switch__input",
      type: "checkbox",
      role: "switch",
      "data-citry-ui-part": "input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _createElementVNode("span", { "data-citry-ui-part": "surface" }, [
      _createElementVNode("span", {
        "aria-hidden": "true",
        "data-citry-ui-part": "track"
      }, [
        _createElementVNode("span", { "data-citry-ui-part": "thumb" })
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6f155b7ef9413ee240a34cf8e0fa6512c4edca4beb1d8713d5849ef4aedc1c2d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", {
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, " * ")
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot853fef0ef19da02c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot853fef0ef19da02c", { key: 3 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5af74338e518f9e4146773956898d763682f09a14325bf9a3aa6851ad695bbde"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
    "citry-id": _ctx.$citryPrepared.calls.citryCalladc143317e88d61a.id,
    key: _ctx.$citryPrepared.calls.citryCalladc143317e88d61a.key
  }, {
    ['citrySlote2526e6f745e4169']: _withCtx(() => [
      _createTextVNode("Away mode")
    ]),
    ['citrySlot6f90e269deb4619c']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalle41880ab582803b1.id,
        key: _ctx.$citryPrepared.calls.citryCalle41880ab582803b1.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    ['citrySlote7646b39489ca911']: _withCtx(() => [
      _createTextVNode("Lower heating and pause routine lighting.")
    ]),
    ['citrySlot853fef0ef19da02c']: _withCtx(() => [
      _createTextVNode("Enable away mode before leaving.")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bf7fb899c24a11c1805f2106a72af4064f85f2d9cb6d325b48ffdf455ab49603"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle41880ab582803b1","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[]},{"localId":"citryCalladc143317e88d61a","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCalle41880ab582803b1"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot853fef0ef19da02c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_switch_field_ed6bea44 = _resolveComponent("citry-switch-field-ed6bea44")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_switch_field_ed6bea44, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1e0ee7ec9acabc51.id,
      key: _ctx.$citryPrepared.calls.citryCall1e0ee7ec9acabc51.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["36206854def336f4535af9253f64183555a98c5f597b522dee30c59ff0f75838"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1e0ee7ec9acabc51","typeKey":"SwitchField_60628a","componentTag":"citry-switch-field-ed6bea44","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
