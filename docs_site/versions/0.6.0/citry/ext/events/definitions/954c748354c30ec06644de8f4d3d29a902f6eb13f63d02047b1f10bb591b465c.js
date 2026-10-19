(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f1aec00fd68548f2", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("button", _mergeProps({
      class: "cui-sidebar__toggle",
      type: "button",
      "data-citry-ui-part": "toggle"
    }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("span", {
        class: "cui-sidebar__toggle-icon",
        "aria-hidden": "true",
        "data-citry-ui-part": "toggle-icon"
      }, " ≡ "),
      _createElementVNode("span", _mergeProps({
        class: "cui-sidebar__toggle-label",
        "data-citry-ui-part": "toggle-label"
      }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
      _createElementVNode("span", {
        class: "cui-sidebar__toggle-label",
        "data-citry-ui-part": "toggle-label"
      }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      class: "cui-sidebar__panel",
      "data-citry-ui-part": "panel"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("div", {
        class: "cui-sidebar__content",
        "data-citry-ui-part": "content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1bc155a4b10baf50'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1bc155a4b10baf50", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["70dc1790eaf3d9490cca0948e47b7d6170172d897789e694ffc103d8b2a6e5a7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_sidebar_73161829 = _resolveComponent("citry-c-sidebar-73161829")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.last)
      }, "No request yet", 8 /* PROPS */, ["textContent"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_sidebar_73161829, {
      collapsed: _ctx.collapsed,
      "on-collapsed-change": _ctx.change,
      "citry-id": _ctx.$citryPrepared.calls.citryCallcd1d1cdaee3ccc66.id,
      key: _ctx.$citryPrepared.calls.citryCallcd1d1cdaee3ccc66.key
    }, {
      ['citrySlot1bc155a4b10baf50']: _withCtx(() => [
        _createElementVNode("strong", null, "Controlled Sidebar content")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["collapsed", "on-collapsed-change", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["506234750f014e3e3d1cb1fa604040fb4678ec37fe597ab78fa2f7722b11b4ff"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcd1d1cdaee3ccc66","typeKey":"CSidebar_25c49a","componentTag":"citry-c-sidebar-73161829","bindings":[{"kind":"prop","name":":collapsed","value":"collapsed","sourceStart":94,"sourceEnd":116},{"kind":"prop","name":":on-collapsed-change","value":"change","sourceStart":117,"sourceEnd":146}],"fills":[{"name":"citrySlot1bc155a4b10baf50","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_sidebar_controlled_dd5bf2e4 = _resolveComponent("citry-sidebar-controlled-dd5bf2e4")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_sidebar_controlled_dd5bf2e4, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalldff1293e30c2e604.id,
      key: _ctx.$citryPrepared.calls.citryCalldff1293e30c2e604.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["575f1e7050ce86c6a6ad85f59f21c4c9639f793f2cfef5038b9f65eecaf720c4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldff1293e30c2e604","typeKey":"SidebarControlled_b83d65","componentTag":"citry-sidebar-controlled-dd5bf2e4","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
