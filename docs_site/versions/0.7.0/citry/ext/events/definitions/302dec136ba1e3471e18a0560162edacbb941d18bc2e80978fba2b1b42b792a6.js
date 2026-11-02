(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

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
      ]),
      _createElementVNode("span", { "data-citry-ui-part": "body" }, [
        _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs2), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot68b9ec6d1edbf23f'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot68b9ec6d1edbf23f", { key: 0 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot748d23fb9d69de3c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot748d23fb9d69de3c", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b4fa3a1da54482c36a9d18ca6a6bfd1c80c7c2c1ba534524c41e8c045c8c8abd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-4db931dd4fd5ad47", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot0d2ecfee87db4621'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot0d2ecfee87db4621", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["182ced09199ba5a266177a942bdbb3353b37ffbb805fe4ca6238a3f0cb46353f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-4db931dd4fd5ad47","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-4db931dd4fd5ad47","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_switch_42d828ec = _resolveComponent("citry-c-switch-42d828ec")
  const _component_citry_c_col_37f35bc5 = _resolveComponent("citry-c-col-37f35bc5")
  
  return (_openBlock(), _createBlock(_component_citry_c_col_37f35bc5, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallea34ceab160d7235.id,
    key: _ctx.$citryPrepared.calls.citryCallea34ceab160d7235.key
  }, {
    ['citrySlot0d2ecfee87db4621']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall206a78e00a054b84.id,
        key: _ctx.$citryPrepared.calls.citryCall206a78e00a054b84.key
      }, {
        ['citrySlot68b9ec6d1edbf23f']: _withCtx(() => [
          _createTextVNode("Air purifier")
        ]),
        ['citrySlot748d23fb9d69de3c']: _withCtx(() => [
          _createTextVNode("Runs quietly until the room reaches clean-air target.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_switch_42d828ec, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallae64b121320de09d.id,
        key: _ctx.$citryPrepared.calls.citryCallae64b121320de09d.key
      }, {
        ['citrySlot68b9ec6d1edbf23f']: _withCtx(() => [
          _createTextVNode("Fireplace fan")
        ]),
        ['citrySlot748d23fb9d69de3c']: _withCtx(() => [
          _createTextVNode("Available while the fireplace is warm.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["232cf42d8c286d1a028e7bfd712f318d0876aa2b1c8d1e6559fd127f650f13ab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall206a78e00a054b84","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot68b9ec6d1edbf23f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot748d23fb9d69de3c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallae64b121320de09d","typeKey":"CSwitch_fa49a4","componentTag":"citry-c-switch-42d828ec","bindings":[],"fills":[{"name":"citrySlot68b9ec6d1edbf23f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot748d23fb9d69de3c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallea34ceab160d7235","typeKey":"CCol_a23ecf","componentTag":"citry-c-col-37f35bc5","bindings":[],"fills":[{"name":"citrySlot0d2ecfee87db4621","localDescendants":["citryCall206a78e00a054b84","citryCallae64b121320de09d"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_described_switches_fa631604 = _resolveComponent("citry-described-switches-fa631604")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_described_switches_fa631604, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9cedfb200f592073.id,
      key: _ctx.$citryPrepared.calls.citryCall9cedfb200f592073.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ab49e8d29a8276e180467404f5801e587763108d3c960953547273530198c001"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9cedfb200f592073","typeKey":"DescribedSwitches_587e5d","componentTag":"citry-described-switches-fa631604","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
