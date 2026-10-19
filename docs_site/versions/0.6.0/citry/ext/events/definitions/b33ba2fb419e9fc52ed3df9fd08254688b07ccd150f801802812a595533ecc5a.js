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
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_hover_card_44054f9b = _resolveComponent("citry-c-hover-card-44054f9b")
  const _component_citry_c_row_d2dc488a = _resolveComponent("citry-c-row-d2dc488a")
  
  return (_openBlock(), _createBlock(_component_citry_c_row_d2dc488a, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall23458fe6a107a034.id,
    key: _ctx.$citryPrepared.calls.citryCall23458fe6a107a034.key
  }, {
    ['citrySlotb13ff7dbfcd5f34a']: _withCtx(() => [
      _createElementVNode("div", { style: "color-scheme:light;background:Canvas;color:CanvasText;padding:2rem" }, [
        (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallb83f00f5c9e32c99.id,
          key: _ctx.$citryPrepared.calls.citryCallb83f00f5c9e32c99.key
        }, {
          ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
            _createElementVNode("a", _mergeProps({ href: "#day" }, _ctx.$citryPrepared.citryAttrs0), "Day profile", 16 /* FULL_PROPS */)
          ]),
          ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
            _createElementVNode("strong", null, "Light scheme"),
            _createElementVNode("p", null, "Follows its anchor context.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _createElementVNode("div", { style: "color-scheme:dark;background:Canvas;color:CanvasText;padding:2rem" }, [
        (_openBlock(), _createBlock(_component_citry_c_hover_card_44054f9b, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallbd9a25e551cdd26c.id,
          key: _ctx.$citryPrepared.calls.citryCallbd9a25e551cdd26c.key
        }, {
          ['citrySlot5acfa23a00dd4e44']: _withCtx(() => [
            _createElementVNode("a", _mergeProps({ href: "#night" }, _ctx.$citryPrepared.citryAttrs1), "Night profile", 16 /* FULL_PROPS */)
          ]),
          ['citrySlot3f4ff818ad71f2c3']: _withCtx(() => [
            _createElementVNode("strong", null, "Dark scheme"),
            _createElementVNode("p", null, "Follows its anchor context.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2197b9fa3142786966c297ffca52c357278b756ee2f8b16abfb87e3fd18226fd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb83f00f5c9e32c99","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbd9a25e551cdd26c","typeKey":"CHoverCard_27dc84","componentTag":"citry-c-hover-card-44054f9b","bindings":[],"fills":[{"name":"citrySlot3f4ff818ad71f2c3","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot5acfa23a00dd4e44","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall23458fe6a107a034","typeKey":"CRow_c22819","componentTag":"citry-c-row-d2dc488a","bindings":[],"fills":[{"name":"citrySlotb13ff7dbfcd5f34a","localDescendants":["citryCallb83f00f5c9e32c99","citryCallbd9a25e551cdd26c"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_hover_card_themes_244c55a1 = _resolveComponent("citry-hover-card-themes-244c55a1")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_hover_card_themes_244c55a1, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall379f11e85391988b.id,
      key: _ctx.$citryPrepared.calls.citryCall379f11e85391988b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["622b3887a2310ddf7efc50f49de108d19c068b6ce837ad8301d71d1eecc8294c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall379f11e85391988b","typeKey":"HoverCardThemes_70f0a9","componentTag":"citry-hover-card-themes-244c55a1","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
