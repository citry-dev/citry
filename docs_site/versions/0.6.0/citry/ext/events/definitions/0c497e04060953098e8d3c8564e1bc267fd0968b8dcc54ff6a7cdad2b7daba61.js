(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "M4 5h16" }),
      _createElementVNode("path", { d: "M4 12h16" }),
      _createElementVNode("path", { d: "M4 19h16" })
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["73442fdaba2dbd32e88faf16365cbe5ef8065c255eb54c4f726af137c326e8f6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot4a88c2fdbb6f20a3'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot4a88c2fdbb6f20a3", { key: 0 })
          : _createCommentVNode("v-if", true)
      ]),
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
      _createElementVNode("header", {
        class: "cui-sidebar__header",
        "data-citry-ui-part": "header"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlota8df75f71fad2ecd'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlota8df75f71fad2ecd", { key: 1 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("div", {
        class: "cui-sidebar__content",
        "data-citry-ui-part": "content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot4f9b3c7771941819'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot4f9b3c7771941819", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a3e1879393a4a6e6e34d165126fadcd19977a85d8dcd0d0a4a9bde2501fba117"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_icon_f8b347d7 = _resolveComponent("citry-c-icon-f8b347d7")
  const _component_citry_c_sidebar_73161829 = _resolveComponent("citry-c-sidebar-73161829")
  
  return (_openBlock(), _createBlock(_component_citry_c_sidebar_73161829, {
    "citry-id": _ctx.$citryPrepared.calls.citryCalla598ea9b182ef822.id,
    key: _ctx.$citryPrepared.calls.citryCalla598ea9b182ef822.key
  }, {
    ['citrySlot4a88c2fdbb6f20a3']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall9fd178d6b4b0938e.id,
        key: _ctx.$citryPrepared.calls.citryCall9fd178d6b4b0938e.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    ['citrySlota8df75f71fad2ecd']: _withCtx(() => [
      _createElementVNode("strong", null, "Ocean lab")
    ]),
    ['citrySlot4f9b3c7771941819']: _withCtx(() => [
      _createElementVNode("p", null, "Public variables and parts customize the stable landmark.")
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["83ebadda6be548d8c96ea5786cf47ac5cbab2a7b7289a99fcc10e01d7b65df85"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9fd178d6b4b0938e","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCalla598ea9b182ef822","typeKey":"CSidebar_25c49a","componentTag":"citry-c-sidebar-73161829","bindings":[],"fills":[{"name":"citrySlot4a88c2fdbb6f20a3","localDescendants":["citryCall9fd178d6b4b0938e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4f9b3c7771941819","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlota8df75f71fad2ecd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_sidebar_customization_e46d0a3f = _resolveComponent("citry-sidebar-customization-e46d0a3f")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_sidebar_customization_e46d0a3f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle7d507d1e4ec0de9.id,
      key: _ctx.$citryPrepared.calls.citryCalle7d507d1e4ec0de9.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6f341db96ec7b33492250b4d508fc2dda6fddc3c9f82b5c7f4452ede2d1e47fa"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle7d507d1e4ec0de9","typeKey":"SidebarCustomization_4602d3","componentTag":"citry-sidebar-customization-e46d0a3f","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
