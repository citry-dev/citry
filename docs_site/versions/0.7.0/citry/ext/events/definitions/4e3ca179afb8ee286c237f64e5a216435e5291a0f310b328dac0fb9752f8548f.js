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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["afcbb64cd3e879dce639ead8238a1058fed0e999b8c67c1b97121a90061dc209"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0adfeb1903c9250150e0a3d058316d216477a18bf78a56c396d8635da8b31dce"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-3bed3ea0af7a1780","tag":"div","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_hover_card_44054f9b = _resolveComponent("citry-c-hover-card-44054f9b")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
    "citry-id": _ctx.$citryPrepared.calls.citryCalle659534041dbb56a.id,
    key: _ctx.$citryPrepared.calls.citryCalle659534041dbb56a.key
  }, {
    ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall3207829cf8c6c789.id,
        key: _ctx.$citryPrepared.calls.citryCall3207829cf8c6c789.key
      }, {
        ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
          _createElementVNode("a", _mergeProps({ href: "#top" }, _ctx.$citryPrepared.citryAttrs0), "Top start", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
          _createTextVNode("Collision-aware top preview.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall58ac5cb7361d769f.id,
        key: _ctx.$citryPrepared.calls.citryCall58ac5cb7361d769f.key
      }, {
        ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
          _createElementVNode("a", _mergeProps({ href: "#bottom" }, _ctx.$citryPrepared.citryAttrs1), "Bottom end", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
          _createTextVNode("Collision-aware bottom preview.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6e70951c35fcd5a725c614db546bcd829071497460be336f216d4380264b3832"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3207829cf8c6c789","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall58ac5cb7361d769f","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle659534041dbb56a","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":["citryCall3207829cf8c6c789","citryCall58ac5cb7361d769f"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_hover_card_placements_31045ba6 = _resolveComponent("citry-hover-card-placements-31045ba6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_hover_card_placements_31045ba6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall3fdd4e0271b00d44.id,
      key: _ctx.$citryPrepared.calls.citryCall3fdd4e0271b00d44.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["82603b55233b1331dec3c78825e62c419856947713837d058e5783e2faebfddf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3fdd4e0271b00d44","typeKey":"HoverCardPlacements_ac13d0","componentTag":"citry-hover-card-placements-31045ba6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
