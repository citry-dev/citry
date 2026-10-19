(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

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
      _createElementVNode("header", {
        class: "cui-sidebar__header",
        "data-citry-ui-part": "header"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlota8df75f71fad2ecd'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlota8df75f71fad2ecd", { key: 0 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("div", {
        class: "cui-sidebar__content",
        "data-citry-ui-part": "content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot4f9b3c7771941819'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot4f9b3c7771941819", { key: 1 })
          : _createCommentVNode("v-if", true)
      ]),
      _createElementVNode("footer", {
        class: "cui-sidebar__footer",
        "data-citry-ui-part": "footer"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotd4ecec09845391b2'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotd4ecec09845391b2", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c5ec9d205ab3a2e22103bd8ea98f80ec1d86c227b0d64a5dd52eea6b3db8895b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f1aec00fd68548f2","tag":"aside","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_sidebar_73161829 = _resolveComponent("citry-c-sidebar-73161829")
  
  return (_openBlock(), _createBlock(_component_citry_c_sidebar_73161829, {
    "citry-id": _ctx.$citryPrepared.calls.citryCall714599dc372b65cf.id,
    key: _ctx.$citryPrepared.calls.citryCall714599dc372b65cf.key
  }, {
    ['citrySlota8df75f71fad2ecd']: _withCtx(() => [
      _createElementVNode("strong", null, "Inspector")
    ]),
    ['citrySlot4f9b3c7771941819']: _withCtx(() => [
      _createElementVNode("p", null, "Long tool content scrolls independently between fixed regions."),
      _createElementVNode("p", null, "Keep adding contextual controls here.")
    ]),
    ['citrySlotd4ecec09845391b2']: _withCtx(() => [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        "citry-id": _ctx.$citryPrepared.calls.citryCalldb651a5d7edb9ff7.id,
        key: _ctx.$citryPrepared.calls.citryCalldb651a5d7edb9ff7.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode("Apply")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _: 2 /* DYNAMIC */
  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["71af6af988f24b4b22add494002acd8a5d9c148cc113db2f6733e6a504ebbd14"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldb651a5d7edb9ff7","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall714599dc372b65cf","typeKey":"CSidebar_25c49a","componentTag":"citry-c-sidebar-73161829","bindings":[],"fills":[{"name":"citrySlot4f9b3c7771941819","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlota8df75f71fad2ecd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd4ecec09845391b2","localDescendants":["citryCalldb651a5d7edb9ff7"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_sidebar_presentation_02e0aabc = _resolveComponent("citry-sidebar-presentation-02e0aabc")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_sidebar_presentation_02e0aabc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallf4b237c3394b4127.id,
      key: _ctx.$citryPrepared.calls.citryCallf4b237c3394b4127.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2f5647c2aff1113b79c125c8362ba78b8a13325c87f2c5b27b3e572bff2c3990"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf4b237c3394b4127","typeKey":"SidebarPresentation_b05da2","componentTag":"citry-sidebar-presentation-02e0aabc","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
