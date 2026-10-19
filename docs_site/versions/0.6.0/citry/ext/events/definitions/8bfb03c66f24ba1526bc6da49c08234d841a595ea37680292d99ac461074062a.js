(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-hover-card-host",
    "data-citry-hover-card-host": "",
    "data-citry-ui-part": "host"
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot5acfa23a00dd4e44'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot5acfa23a00dd4e44", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-hover-card",
      popover: "manual",
      "aria-hidden": "true",
      "data-citry-ui-part": "hover-card"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", { "data-citry-ui-part": "content" }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot3f4ff818ad71f2c3'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot3f4ff818ad71f2c3", { key: 1 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("span", {
        "aria-hidden": "true",
        "data-citry-ui-part": "arrow"
      })
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c3385dbb74ed2db91946b18174dacfb90567ddc2a21c3c8ffa75ea8c44b0b108"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_hover_card_44054f9b = _resolveComponent("citry-c-hover-card-44054f9b")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall4751f0e944c2ff78.id,
    key: _ctx.$citryPrepared.calls.citryCall4751f0e944c2ff78.key
  }, {
    ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallecf2a46022077cac.id,
        key: _ctx.$citryPrepared.calls.citryCallecf2a46022077cac.key
      }, {
        ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
          _createElementVNode("a", _mergeProps({ href: "#instant" }, _ctx.$citryPrepared.citryAttrs0), "Instant", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
          _createTextVNode("No opening or closing delay.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7a5f521aee4b26a9.id,
        key: _ctx.$citryPrepared.calls.citryCall7a5f521aee4b26a9.key
      }, {
        ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
          _createElementVNode("a", _mergeProps({ href: "#deliberate" }, _ctx.$citryPrepared.citryAttrs1), "Deliberate", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
          _createTextVNode("A slower, forgiving preview.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["08b0570a67e2ef1542a86a69bbdf364d0110e1e691f522fa614182fcf79e5ada"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallecf2a46022077cac","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7a5f521aee4b26a9","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4751f0e944c2ff78","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":["citryCall7a5f521aee4b26a9","citryCallecf2a46022077cac"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_hover_card_delays_2d12df62 = _resolveComponent("citry-hover-card-delays-2d12df62")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_hover_card_delays_2d12df62, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallc78c15c6aee2d047.id,
      key: _ctx.$citryPrepared.calls.citryCallc78c15c6aee2d047.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6894affc6cdeec834850f41378e4892fec594af80bc92b27b46ec14b23346c60"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallc78c15c6aee2d047","typeKey":"HoverCardDelays_0f22e5","componentTag":"citry-hover-card-delays-2d12df62","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
